"""Generate web-only (16:9 landscape) chapter images + cover for books.

Usage (standalone):
    uv run python -m pipeline.generate_images --book chandrakanta

Two-phase per chapter:
  1. Auto-generate scene prompt via Gemini Flash (text model)
  2. Generate image via Gemini Pro (image model)

Checkpoint-based, resumable. 4 workers per book.
"""

import argparse
import os
import json
import shutil
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types
from openai import OpenAI
from PIL import Image
from dotenv import load_dotenv

from pipeline.config import get_book, BOOKS, WEB_DATA_DIR, OPENROUTER_BASE_URL

load_dotenv()

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
IMAGE_MODEL = "gemini-3.1-flash-image-preview"
TEXT_MODEL = "google/gemini-3-flash-preview"

text_client = OpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=os.environ["OPENROUTER_API_KEY"],
)

LANDSCAPE_RATIO = 16 / 9
MAX_WORKERS = 4

checkpoint_lock = threading.Lock()


def load_json(path, default=None):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default if default is not None else {}


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _save_webp(png_path):
    """Convert a PNG file to WebP alongside it (same name, .webp extension)."""
    webp_path = png_path.rsplit(".", 1)[0] + ".webp"
    Image.open(png_path).save(webp_path, "WEBP", quality=85)
    return webp_path


def crop_to_ratio(path, target_ratio):
    img = Image.open(path)
    w, h = img.size
    if abs(w / h - target_ratio) < 0.02:
        return
    if w / h > target_ratio:
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    else:
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))
    img.save(path)


_CHAR_ALIAS_MAP = {"Krishna": ["Blessed Lord"], "Arjuna": ["Partha", "Dhananjaya"]}


def _extract_char_aliases(line):
    """Extract character name + common aliases from a character description line like '- Lord Krishna: ...'"""
    name_part = line.strip().lstrip("- ").split(":")[0].strip()
    aliases = [name_part]
    # Add individual words as aliases (e.g. "Lord Krishna" -> also match "Krishna")
    words = name_part.split()
    if len(words) > 1:
        aliases.extend(words)
    # Common aliases
    for key, extras in _CHAR_ALIAS_MAP.items():
        if key in name_part:
            aliases.extend(extras)
    return aliases


def generate_scene_prompt(chapter, cfg, prompt_cache):
    key = f"p{chapter['part']}_chapter_{chapter['number']}"
    if key in prompt_cache:
        return prompt_cache[key]

    text = "\n\n".join(p["text"] if isinstance(p, dict) else p for p in chapter["paragraphs"][:5])
    excerpt = text[:1500] + "..." if len(text) > 1500 else text

    # Filter characters_description to only include characters mentioned in this chapter
    char_block = cfg.characters_description
    if char_block:
        lines = char_block.strip().split("\n")
        header_lines = [l for l in lines if not l.strip().startswith("- ")]
        char_lines = [l for l in lines if l.strip().startswith("- ")]
        text_lower = excerpt.lower()
        matched = [l for l in char_lines if any(
            alias.lower() in text_lower
            for alias in _extract_char_aliases(l)
        )]
        if matched:
            char_block = "\n".join(header_lines + matched)
        # If no matches, fall back to full list

    system = (
        "You are creating vivid scene descriptions for AI image generation of book chapter illustrations. "
        "Given a chapter excerpt and character info, write a 3-5 sentence scene description. "
        "Focus on: visual setting, character positioning, lighting/mood, key action. "
        "Create a UNIQUE scene specific to this chapter's content. DO NOT repeat generic scenes. "
        "Focus on what actually happens and is discussed in THIS chapter. "
        "Do NOT include any text/lettering instructions. "
        "Do NOT use frame-within-frame, inset panels, or picture-in-picture compositions. "
        "Use neutral language — avoid words like 'desperate', 'tears', 'blood', 'death', 'kill'. "
        "Output ONLY the scene description, nothing else."
    )

    user_prompt = (
        f"Chapter {chapter['number']}: \"{chapter['title']}\"\n\n"
        f"{char_block}\n"
        f"Chapter excerpt:\n{excerpt}"
    )

    response = text_client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
    )
    prompt_text = response.choices[0].message.content.strip()
    prompt_cache[key] = prompt_text
    return prompt_text


def generate_image(output_path, style_prefix, prompt_text, retries=3):
    client = genai.Client(api_key=GEMINI_API_KEY)
    full_prompt = (
        "Edge-to-edge illustration filling the entire frame. "
        "No border, no frame, no margin, no vignette, no white space. "
        "The artwork must extend to all edges. "
        + style_prefix + prompt_text
    )

    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=IMAGE_MODEL,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                    image_config=types.ImageConfig(
                        aspect_ratio="16:9",
                    ),
                ),
            )
            if response.parts is None:
                if attempt < retries - 1:
                    time.sleep(3)
                    continue
                raise RuntimeError("No parts returned (safety filter?)")

            for part in response.parts:
                if part.inline_data is not None:
                    img = part.as_image()
                    img.save(output_path)
                    return True

            if attempt < retries - 1:
                time.sleep(3)
                continue
            raise RuntimeError("No image in response")
        except RuntimeError:
            if attempt == retries - 1:
                raise
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(3)
                continue
            raise RuntimeError(f"API error: {e}")


def generate_cover(book_id, cfg, retries=3):
    client = genai.Client(api_key=GEMINI_API_KEY)
    output_dir = str(cfg.images_dir)
    os.makedirs(output_dir, exist_ok=True)
    cover_path = os.path.join(output_dir, "cover.png")

    if os.path.exists(cover_path):
        print(f"  [{book_id}] Cover already exists")
        return

    # Include character descriptions so covers feature recognizable figures
    character_info = ""
    if cfg.characters_description:
        character_info = (
            "Feature one or more of the story's main characters prominently in the scene. "
            + cfg.characters_description + "\n"
        )

    cover_prompt = (
        "Edge-to-edge illustration filling the entire frame. "
        "No border, no frame, no margin, no vignette, no white space. "
        "A bright, colorful, vibrant book cover illustration. "
        + cfg.image_style_prefix.replace("Scene: ", "")
        + character_info
        + f'Title: "{cfg.title}". {cfg.style_context}\n'
        "A sweeping panoramic scene that captures the essence of the entire story, "
        "with a central character figure. "
        "Bright, inviting colors. No text, no lettering."
    )

    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=IMAGE_MODEL,
                contents=cover_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                    image_config=types.ImageConfig(
                        aspect_ratio="3:4",
                    ),
                ),
            )
            if response.parts is None:
                if attempt < retries - 1:
                    time.sleep(3)
                    continue
                print(f"  [{book_id}] Cover generation blocked by safety filter")
                return

            for part in response.parts:
                if part.inline_data is not None:
                    img = part.as_image()
                    img.save(cover_path)
                    print(f"  [{book_id}] Cover generated -> {cover_path}")
                    return
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(3)
                continue
            print(f"  [{book_id}] Cover FAILED: {e}")


def process_chapter(chapter, cfg, state, prompt_cache, book_id, overrides=None):
    key = f"p{chapter['part']}_chapter_{chapter['number']}"
    web_key = f"{key}_web"

    if web_key in state.get("completed", []):
        return f"{key}: cached"

    output_dir = overrides.get("images_dir", str(cfg.images_dir)) if overrides else str(cfg.images_dir)
    os.makedirs(output_dir, exist_ok=True)

    try:
        prompt_text = generate_scene_prompt(chapter, cfg, prompt_cache)
    except Exception as e:
        return f"{key}: prompt FAILED ({e})"

    prompts_path = overrides.get("prompts_path", str(cfg.image_prompts_json)) if overrides else str(cfg.image_prompts_json)
    with checkpoint_lock:
        save_json(prompts_path, prompt_cache)

    web_path = os.path.join(output_dir, f"{key}_web.png")
    checkpoint_path = overrides.get("checkpoint_path", str(cfg.images_checkpoint)) if overrides else str(cfg.images_checkpoint)
    try:
        generate_image(web_path, cfg.image_style_prefix, prompt_text)
        with checkpoint_lock:
            state.setdefault("completed", []).append(web_key)
            save_json(checkpoint_path, state)
        return f"{key}: OK"
    except Exception as e:
        return f"{key}: FAILED ({e})"


def _run_single_book(book_id, cfg, chapters_path, images_dir, web_img_dir, force=False,
                     checkpoint_path=None, prompts_path=None, skip_cover=False):
    """Run image generation for a single book/sub-book."""
    with open(chapters_path) as f:
        chapters_data = json.load(f)["chapters"]

    checkpoint_path = checkpoint_path or str(cfg.images_checkpoint)
    prompts_path = prompts_path or str(cfg.image_prompts_json)
    state = load_json(checkpoint_path, {"completed": []})
    if force:
        state = {"completed": []}
    prompt_cache = load_json(prompts_path, {})
    total = len(chapters_data)

    remaining = []
    for ch in chapters_data:
        key = f"p{ch['part']}_chapter_{ch['number']}_web"
        if key not in state.get("completed", []):
            remaining.append(ch)

    print(f"\n[{book_id}] {len(remaining)} remaining (of {total}), {MAX_WORKERS} workers")

    if not remaining:
        print(f"[{book_id}] All chapters complete!")
    else:
        if not skip_cover:
            generate_cover(book_id, cfg)

        done = total - len(remaining)
        overrides = {"images_dir": images_dir, "checkpoint_path": checkpoint_path, "prompts_path": prompts_path}
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(process_chapter, ch, cfg, state, prompt_cache, book_id, overrides): ch
                for ch in remaining
            }
            for future in as_completed(futures):
                done += 1
                try:
                    result = future.result()
                    print(f"  [{book_id}] [{done}/{total}] {result}")
                except Exception as e:
                    print(f"  [{book_id}] [{done}/{total}] ERROR: {e}")

    # Copy images to web directory
    os.makedirs(web_img_dir, exist_ok=True)
    count = 0
    if os.path.exists(images_dir):
        for fname in os.listdir(images_dir):
            if fname.endswith("_web.png") and fname.startswith("p"):
                src = os.path.join(images_dir, fname)
                dst_name = fname.replace("_web.png", ".png")
                dst = os.path.join(web_img_dir, dst_name)
                shutil.copy2(src, dst)
                _save_webp(dst)
                count += 1
    print(f"  [{book_id}] Copied {count} chapter images (PNG+WebP) -> {web_img_dir}")

    # Update chapters.json with image paths (both public and server-data)
    if count > 0:
        with open(chapters_path) as f:
            ch_data = json.load(f)
        existing_webps = set(os.listdir(web_img_dir)) if os.path.exists(web_img_dir) else set()
        updated = 0
        for ch in ch_data["chapters"]:
            fname = f"p{ch['part']}_chapter_{ch['number']}.webp"
            if fname in existing_webps and not ch.get("image"):
                ch["image"] = f"/data/images/chapters/{book_id}/{fname}"
                updated += 1
        if updated:
            with open(chapters_path, "w") as f:
                json.dump(ch_data, f, ensure_ascii=False)
            # Also update server-data copy
            from pipeline.config import SERVER_DATA_DIR
            server_path = str(SERVER_DATA_DIR / "books" / book_id / "chapters.json")
            if os.path.exists(server_path):
                with open(server_path, "w") as f:
                    json.dump(ch_data, f, ensure_ascii=False)
            print(f"  [{book_id}] Linked {updated} chapter images in chapters.json")

    # Copy cover
    cover_src = os.path.join(images_dir, "cover.png")
    if os.path.exists(cover_src):
        cover_dst = str(cfg.web_cover_path)
        os.makedirs(os.path.dirname(cover_dst), exist_ok=True)
        shutil.copy2(cover_src, cover_dst)
        _save_webp(cover_dst)


def run(book_id, force=False):
    """Run image generation for a book. For anthologies, iterates sub-books."""
    cfg = get_book(book_id)

    if not cfg.image_style_prefix:
        print(f"[{book_id}] No image style prefix configured")
        return False

    if cfg.type == "anthology":
        return _run_anthology_images(book_id, cfg, force)

    chapters_path = str(cfg.web_chapters_json)
    if not os.path.exists(chapters_path):
        print(f"[{book_id}] chapters.json not found at {chapters_path}, skipping")
        return False

    _run_single_book(
        book_id, cfg, chapters_path,
        str(cfg.images_dir), str(cfg.web_chapter_images_dir), force
    )
    return True


def _run_anthology_images(book_id, cfg, force=False):
    """Run image generation for each sub-book in an anthology."""
    from pipeline.config import WEB_DATA_DIR
    anthology_path = cfg.web_book_dir / "anthology.json"
    if not anthology_path.exists():
        print(f"[{book_id}] anthology.json not found")
        return False
    with open(anthology_path) as f:
        anthology = json.load(f)
    story_ids = anthology.get("storyBookIds", [])
    print(f"[{book_id}] Anthology with {len(story_ids)} story-books")

    # Generate cover for the anthology itself
    generate_cover(book_id, cfg)
    cover_src = os.path.join(str(cfg.images_dir), "cover.png")
    if os.path.exists(cover_src):
        cover_dst = str(cfg.web_cover_path)
        os.makedirs(os.path.dirname(cover_dst), exist_ok=True)
        shutil.copy2(cover_src, cover_dst)
        _save_webp(cover_dst)

    for story_id in story_ids:
        story_dir = WEB_DATA_DIR / "books" / story_id
        chapters_path = str(story_dir / "chapters.json")
        if not os.path.exists(chapters_path):
            print(f"  [{story_id}] chapters.json not found, skipping")
            continue
        web_img_dir = str(WEB_DATA_DIR / "images" / "chapters" / story_id)
        images_dir = str(cfg.images_dir / story_id)
        os.makedirs(images_dir, exist_ok=True)

        # Per-sub-book checkpoint and prompts to avoid collisions
        checkpoint_path = os.path.join(images_dir, "images_checkpoint.json")
        prompts_path = os.path.join(images_dir, "image_prompts.json")
        _run_single_book(story_id, cfg, chapters_path, images_dir, web_img_dir, force,
                         checkpoint_path=checkpoint_path, prompts_path=prompts_path,
                         skip_cover=True)

        # Generate a cover for this sub-book
        story_cover_dst = str(WEB_DATA_DIR / "images" / "covers" / f"{story_id}.png")
        if not os.path.exists(story_cover_dst):
            # Read meta.json to get the story title for the cover prompt
            meta_path = story_dir / "meta.json"
            story_title = story_id
            story_summary = ""
            if meta_path.exists():
                with open(meta_path) as f:
                    meta = json.load(f)
                story_title = meta.get("title", story_id)
                story_summary = meta.get("summary", "")
            cover_prompt = (
                "Edge-to-edge illustration filling the entire frame. "
                "No border, no frame, no margin, no vignette, no white space. "
                "A bright, colorful, vibrant book cover illustration. "
                + cfg.image_style_prefix.replace("Scene: ", "")
                + (cfg.characters_description + "\n" if cfg.characters_description else "")
                + f'Title: "{story_title}". {story_summary}\n'
                "A sweeping panoramic scene that captures the essence of the story. "
                "Bright, inviting colors. No text, no lettering."
            )
            client = genai.Client(api_key=GEMINI_API_KEY)
            for attempt in range(3):
                try:
                    response = client.models.generate_content(
                        model=IMAGE_MODEL,
                        contents=cover_prompt,
                        config=types.GenerateContentConfig(
                            response_modalities=["IMAGE", "TEXT"],
                            image_config=types.ImageConfig(aspect_ratio="3:4"),
                        ),
                    )
                    if response.parts:
                        for part in response.parts:
                            if part.inline_data is not None:
                                img = part.as_image()
                                os.makedirs(os.path.dirname(story_cover_dst), exist_ok=True)
                                img.save(story_cover_dst)
                                _save_webp(story_cover_dst)
                                print(f"  [{story_id}] Cover generated -> {story_cover_dst}")
                                break
                        break
                except Exception as e:
                    if attempt < 2:
                        time.sleep(3)
                    else:
                        print(f"  [{story_id}] Cover FAILED: {e}")

    return True


def main():
    parser = argparse.ArgumentParser(description="Generate chapter images for books")
    parser.add_argument("--book", required=True, help="Book ID or 'all'")
    parser.add_argument("--force", action="store_true", help="Force re-run")
    args = parser.parse_args()

    if args.book == "all":
        books = list(BOOKS.keys())
        with ThreadPoolExecutor(max_workers=len(books)) as executor:
            futures = {executor.submit(run, bid, args.force): bid for bid in books}
            for future in as_completed(futures):
                bid = futures[future]
                try:
                    future.result()
                except Exception as e:
                    print(f"[{bid}] BOOK ERROR: {e}")
    else:
        run(args.book, force=args.force)

    print("\n=== All done! ===")


if __name__ == "__main__":
    main()
