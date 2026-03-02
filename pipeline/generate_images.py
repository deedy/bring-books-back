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


def generate_scene_prompt(chapter, cfg, prompt_cache):
    key = f"p{chapter['part']}_chapter_{chapter['number']}"
    if key in prompt_cache:
        return prompt_cache[key]

    text = "\n\n".join(chapter["paragraphs"][:5])
    excerpt = text[:1500] + "..." if len(text) > 1500 else text

    system = (
        "You are creating vivid scene descriptions for AI image generation of book chapter illustrations. "
        "Given a chapter excerpt and character info, write a 3-5 sentence scene description. "
        "Focus on: visual setting, character positioning, lighting/mood, key action. "
        "Do NOT include any text/lettering instructions. "
        "Use neutral language — avoid words like 'desperate', 'tears', 'blood', 'death', 'kill'. "
        "Output ONLY the scene description, nothing else."
    )

    user_prompt = (
        f"Chapter {chapter['number']}: \"{chapter['title']}\"\n\n"
        f"{cfg.characters_description}\n"
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

    cover_prompt = (
        "Edge-to-edge illustration filling the entire frame. "
        "No border, no frame, no margin, no vignette, no white space. "
        "A bright, colorful, vibrant book cover illustration. "
        + cfg.image_style_prefix.replace("Scene: ", "")
        + "A sweeping panoramic scene that captures the essence of the entire story. "
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


def process_chapter(chapter, cfg, state, prompt_cache, book_id):
    key = f"p{chapter['part']}_chapter_{chapter['number']}"
    web_key = f"{key}_web"

    if web_key in state.get("completed", []):
        return f"{key}: cached"

    output_dir = str(cfg.images_dir)
    os.makedirs(output_dir, exist_ok=True)

    try:
        prompt_text = generate_scene_prompt(chapter, cfg, prompt_cache)
    except Exception as e:
        return f"{key}: prompt FAILED ({e})"

    with checkpoint_lock:
        save_json(str(cfg.image_prompts_json), prompt_cache)

    web_path = os.path.join(output_dir, f"{key}_web.png")
    try:
        generate_image(web_path, cfg.image_style_prefix, prompt_text)
        with checkpoint_lock:
            state.setdefault("completed", []).append(web_key)
            save_json(str(cfg.images_checkpoint), state)
        return f"{key}: OK"
    except Exception as e:
        return f"{key}: FAILED ({e})"


def run(book_id, force=False):
    """Run image generation for a book. Returns True on success."""
    cfg = get_book(book_id)
    chapters_path = str(cfg.web_chapters_json)

    if not cfg.image_style_prefix:
        print(f"[{book_id}] No image style prefix configured")
        return False

    if not os.path.exists(chapters_path):
        print(f"[{book_id}] chapters.json not found at {chapters_path}, skipping")
        return False

    with open(chapters_path) as f:
        chapters_data = json.load(f)["chapters"]

    state = load_json(str(cfg.images_checkpoint), {"completed": []})
    if force:
        state = {"completed": []}
    prompt_cache = load_json(str(cfg.image_prompts_json), {})
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
        generate_cover(book_id, cfg)

        done = total - len(remaining)
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(process_chapter, ch, cfg, state, prompt_cache, book_id): ch
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
    web_img_dir = str(cfg.web_chapter_images_dir)
    os.makedirs(web_img_dir, exist_ok=True)
    count = 0
    images_dir = str(cfg.images_dir)
    if os.path.exists(images_dir):
        for fname in os.listdir(images_dir):
            if fname.endswith("_web.png") and fname.startswith("p"):
                src = os.path.join(images_dir, fname)
                dst_name = fname.replace("_web.png", ".png")
                dst = os.path.join(web_img_dir, dst_name)
                shutil.copy2(src, dst)
                count += 1
    print(f"  [{book_id}] Copied {count} chapter images -> {web_img_dir}")

    # Copy cover
    cover_src = os.path.join(images_dir, "cover.png")
    if os.path.exists(cover_src):
        cover_dst = str(cfg.web_cover_path)
        os.makedirs(os.path.dirname(cover_dst), exist_ok=True)
        shutil.copy2(cover_src, cover_dst)

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
