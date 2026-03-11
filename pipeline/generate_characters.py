"""Generate character portrait images for the top 6 most-frequent characters per book.

Usage (standalone):
    uv run python -m pipeline.generate_characters --book chandrakanta
    uv run python -m pipeline.generate_characters --all

Phase 1: Build portrait prompts in parallel (Gemini Flash).
Phase 2: Generate images in parallel (Gemini Pro image).
Checkpoint-based, resumable.
"""

import argparse
import os
import re
import json
import time
import shutil
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

CHECKPOINT_PATH = "data/character_images_checkpoint.json"
OUTPUT_DIR = "character_images"
WEB_DIR = str(WEB_DATA_DIR / "images" / "characters")

checkpoint_lock = threading.Lock()


def load_json(path):
    with open(path) as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def slugify(name):
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def crop_to_square(path):
    img = Image.open(path)
    w, h = img.size
    if abs(w - h) < 5:
        return
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))
    img.save(path)


def _build_alias_map(glossary):
    """Build a mapping from chapter-level term → canonical glossary name.

    Handles aliases like "Alyosha" mapping to "Alexey Fyodorovitch Karamazov".
    Strategy:
      1. Exact glossary name match.
      2. Individual words (≥3 chars) of the glossary name.
      3. Names/aliases mentioned in the character description (e.g. "also known as Alyosha").
      4. Multi-word subsets of the glossary name (e.g. "Alexey Fyodorovitch").
    When multiple glossary names match, pick the longest (most specific) one.
    """
    char_names = {name for name, entry in glossary.items() if entry.get("type") == "character"}
    alias_map = {}  # term -> canonical name

    def _set_alias(term, canon):
        """Set alias only if not already claimed by a more specific name."""
        if term not in alias_map or len(canon) > len(alias_map[term]):
            alias_map[term] = canon

    for canon in char_names:
        alias_map[canon] = canon  # exact match always works
        parts = canon.split()

        # Map individual name parts
        for part in parts:
            if len(part) < 3 or part.lower() in ("the", "and", "von", "van", "de"):
                continue
            _set_alias(part, canon)

        # Map contiguous multi-word subsets (e.g. "Alexey Fyodorovitch" from
        # "Alexey Fyodorovitch Karamazov")
        for start in range(len(parts)):
            for end in range(start + 2, len(parts) + 1):
                subset = " ".join(parts[start:end])
                if subset != canon:
                    _set_alias(subset, canon)

        # Use explicit aliases field if present
        entry = glossary[canon]
        for alias in entry.get("aliases", []):
            _set_alias(alias, canon)

        # Extract aliases/diminutives from the description text.
        desc = entry.get("description", "")
        import re
        # Parenthetical aliases in the glossary name itself or description
        paren_names = re.findall(r'\(([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\)', canon + " " + desc)
        for alias in paren_names:
            _set_alias(alias, canon)
        # "also known as X", "called X", "nicknamed X"
        for pattern in [r'(?:also )?(?:known|called|nicknamed) (?:as )?([A-Z][a-z]+)',
                        r'diminutive[:\s]+([A-Z][a-z]+)']:
            for match in re.finditer(pattern, desc):
                _set_alias(match.group(1), canon)

    return alias_map


def get_top_characters(book_id, n=6):
    cfg = get_book(book_id)
    ann_path = str(cfg.web_annotations_json)
    ch_path = str(cfg.web_chapters_json)

    if not os.path.exists(ann_path) or not os.path.exists(ch_path):
        return []

    annotations = load_json(ann_path)
    chapters_data = load_json(ch_path)
    chapter_ids = [ch["id"] for ch in chapters_data["chapters"]]

    glossary = annotations.get("glossary", {})
    alias_map = _build_alias_map(glossary)

    # Collect all unique chapter terms and try to resolve unmatched ones
    all_chapter_terms = set()
    for ch_id in chapter_ids:
        all_chapter_terms.update(annotations.get("chapters", {}).get(ch_id, []))

    char_names = {name for name, entry in glossary.items() if entry.get("type") == "character"}

    # Count chapters per canonical character name
    char_counts = {}  # canonical name -> {count, first_chapter_idx}
    for i, ch_id in enumerate(chapter_ids):
        ch_terms = annotations.get("chapters", {}).get(ch_id, [])
        seen_in_chapter = set()  # avoid double-counting aliases in same chapter
        for term in ch_terms:
            canon = alias_map.get(term)
            if not canon or canon not in char_names:
                continue
            if canon in seen_in_chapter:
                continue
            seen_in_chapter.add(canon)
            if canon not in char_counts:
                char_counts[canon] = {"count": 0, "first_chapter_idx": i}
            char_counts[canon]["count"] += 1

    characters = []
    for name, info in char_counts.items():
        characters.append({
            "name": name,
            "description": glossary[name]["description"],
            "count": info["count"],
            "first_chapter_idx": info["first_chapter_idx"],
        })

    characters.sort(key=lambda x: (-x["count"], x["name"]))
    return characters[:n]


def get_first_paragraphs(book_id, character_name, n_paragraphs=3, ann_path=None, ch_path=None):
    if ann_path is None or ch_path is None:
        cfg = get_book(book_id)
        ann_path = ann_path or str(cfg.web_annotations_json)
        ch_path = ch_path or str(cfg.web_chapters_json)

    if not os.path.exists(ann_path) or not os.path.exists(ch_path):
        return []

    annotations = load_json(ann_path)
    chapters_data = load_json(ch_path)
    for ch in chapters_data["chapters"]:
        ch_terms = annotations.get("chapters", {}).get(ch["id"], [])
        if character_name in ch_terms:
            return ch["paragraphs"][:n_paragraphs]
    return []


def build_portrait_prompt(book_id, character, ann_path=None, ch_path=None):
    name = character["name"]
    description = character["description"]
    paragraphs = get_first_paragraphs(book_id, name, ann_path=ann_path, ch_path=ch_path)
    context_text = "\n".join(p["text"] if isinstance(p, dict) else p for p in paragraphs) if paragraphs else ""

    system_prompt = (
        "You are an art director creating portrait image prompts for AI image generation. "
        "Given a character's name, description, and some text from their first appearance, "
        "write a concise visual portrait prompt (2-3 sentences max). Focus on:\n"
        "- Physical appearance (age, build, clothing, distinctive features)\n"
        "- Expression and mood\n"
        "- Any props or accessories they might have\n"
        "Do NOT include any background or setting details. "
        "Do NOT include the character's name in the prompt. "
        "Output ONLY the portrait description, nothing else."
    )

    user_prompt = f"Character: {name}\nDescription: {description}"
    if context_text:
        user_prompt += f"\n\nFirst appearance context:\n{context_text[:2000]}"

    response = text_client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def build_all_prompts(tasks, state, path_overrides=None):
    """Build portrait prompts. path_overrides: dict of book_id -> (ann_path, ch_path)."""
    prompts = {}

    need_prompts = []
    for book_id, char in tasks:
        key = f"{book_id}/{slugify(char['name'])}"
        if key in state.get("prompts", {}):
            prompts[key] = state["prompts"][key]
        else:
            need_prompts.append((book_id, char, key))

    if not need_prompts:
        print(f"  All {len(tasks)} prompts cached")
        return prompts

    print(f"  Generating {len(need_prompts)} text prompts (15 workers)...")

    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {}
        for book_id, char, key in need_prompts:
            kwargs = {}
            if path_overrides and book_id in path_overrides:
                kwargs["ann_path"], kwargs["ch_path"] = path_overrides[book_id]
            f = executor.submit(build_portrait_prompt, book_id, char, **kwargs)
            futures[f] = (book_id, char["name"], key)

        done = len(tasks) - len(need_prompts)
        for future in as_completed(futures):
            done += 1
            book_id, name, key = futures[future]
            try:
                prompt_text = future.result()
                prompts[key] = prompt_text
                with checkpoint_lock:
                    state.setdefault("prompts", {})[key] = prompt_text
                    save_json(CHECKPOINT_PATH, state)
                print(f"    [{done}/{len(tasks)}] {key}: prompt OK")
            except Exception as e:
                print(f"    [{done}/{len(tasks)}] {key}: prompt FAILED ({e})")

    return prompts


def generate_single_image(book_id, slug, prompt_text, retries=3, style_prefix=None):
    if style_prefix is None:
        cfg = get_book(book_id)
        style_prefix = cfg.character_style_prefix
    client = genai.Client(api_key=GEMINI_API_KEY)

    full_prompt = (
        "A character portrait, head and upper body, facing slightly to the side. "
        "The subject is centered. Edge-to-edge, no border, no frame, no margin. "
        "No text.\n\n"
        + style_prefix
        + prompt_text
    )

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"{book_id}_{slug}.png")

    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=IMAGE_MODEL,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                    image_config=types.ImageConfig(
                        aspect_ratio="1:1",
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

                    web_book_dir = os.path.join(WEB_DIR, book_id)
                    os.makedirs(web_book_dir, exist_ok=True)
                    png_dst = os.path.join(web_book_dir, f"{slug}.png")
                    shutil.copy2(output_path, png_dst)
                    webp_dst = os.path.join(web_book_dir, f"{slug}.webp")
                    Image.open(png_dst).save(webp_dst, "WEBP", quality=85)
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


def generate_all_images(tasks, prompts, state, style_prefix=None):
    need_images = []
    for book_id, char in tasks:
        key = f"{book_id}/{slugify(char['name'])}"
        if key in state["completed"]:
            continue
        if key not in prompts:
            continue
        need_images.append((book_id, char, key))

    if not need_images:
        print(f"  All images cached")
        return

    print(f"  Generating {len(need_images)} images (15 workers)...")

    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {}
        for book_id, char, key in need_images:
            slug = slugify(char["name"])
            f = executor.submit(generate_single_image, book_id, slug, prompts[key],
                                style_prefix=style_prefix)
            futures[f] = (book_id, char["name"], key)

        done = len(tasks) - len(need_images)
        for future in as_completed(futures):
            done += 1
            book_id, name, key = futures[future]
            try:
                future.result()
                with checkpoint_lock:
                    state["completed"].append(key)
                    save_json(CHECKPOINT_PATH, state)
                print(f"    [{done}/{len(tasks)}] {key}: image OK")
            except Exception as e:
                print(f"    [{done}/{len(tasks)}] {key}: image FAILED ({e})")


def update_annotations(book_id, characters):
    cfg = get_book(book_id)
    ann_path = str(cfg.web_annotations_json)
    if not os.path.exists(ann_path):
        return
    annotations = load_json(ann_path)

    # Clear all existing character images first to remove stale references
    char_names_in_batch = {c["name"] for c in characters}
    for name, entry in annotations["glossary"].items():
        if entry.get("type") == "character" and "image" in entry:
            if name not in char_names_in_batch:
                del entry["image"]

    # Set images for the current batch
    for char in characters:
        name = char["name"]
        slug = slugify(name)
        web_path_webp = os.path.join(WEB_DIR, book_id, f"{slug}.webp")
        web_path_png = os.path.join(WEB_DIR, book_id, f"{slug}.png")
        has_webp = os.path.exists(web_path_webp)
        has_png = os.path.exists(web_path_png)
        if name in annotations["glossary"] and (has_webp or has_png):
            ext = "webp" if has_webp else "png"
            annotations["glossary"][name]["image"] = f"/data/images/characters/{book_id}/{slug}.{ext}"

    save_json(ann_path, annotations)
    print(f"  Updated annotations for {book_id}")


def _run_for_book(book_id, force=False):
    """Run character image generation for a single book (non-anthology)."""
    cfg = get_book(book_id)

    os.makedirs(os.path.dirname(CHECKPOINT_PATH), exist_ok=True)
    if os.path.exists(CHECKPOINT_PATH):
        state = load_json(CHECKPOINT_PATH)
    else:
        state = {"completed": [], "prompts": {}}

    n_chars = getattr(cfg, 'num_character_portraits', 6)
    chars = get_top_characters(book_id, n=n_chars)
    if not chars:
        print(f"[{book_id}] No characters found (annotations missing?)")
        return False

    print(f"\n[{book_id}] Top {n_chars} characters:")
    for c in chars:
        print(f"  {c['name']} ({c['count']} chapters)")

    tasks = [(book_id, c) for c in chars]

    remaining = [
        (bid, c) for bid, c in tasks
        if f"{bid}/{slugify(c['name'])}" not in state["completed"]
    ]

    if not remaining and not force:
        print(f"[{book_id}] All character images complete!")
    else:
        print(f"\n--- Phase 1: Text prompts ---")
        prompts = build_all_prompts(tasks, state)

        print(f"\n--- Phase 2: Image generation ---")
        generate_all_images(tasks, prompts, state)

    print(f"\n--- Phase 3: Update annotations ---")
    update_annotations(book_id, chars)

    return True


def _get_top_characters_from_paths(ann_path, ch_path, n=6):
    """Get top characters from explicit annotation/chapter paths."""
    if not os.path.exists(ann_path) or not os.path.exists(ch_path):
        return []
    annotations = load_json(ann_path)
    chapters_data = load_json(ch_path)
    chapter_ids = [ch["id"] for ch in chapters_data["chapters"]]
    characters = []
    for name, entry in annotations["glossary"].items():
        if entry["type"] != "character":
            continue
        count = 0
        for ch_id in chapter_ids:
            ch_terms = annotations.get("chapters", {}).get(ch_id, [])
            if name in ch_terms:
                count += 1
        characters.append({
            "name": name,
            "description": entry["description"],
            "count": count,
        })
    characters.sort(key=lambda x: (-x["count"], x["name"]))
    return characters[:n]


def run(book_id, force=False):
    """Run character image generation for a single book. Returns True on success."""
    cfg = get_book(book_id)
    if not cfg.character_style_prefix:
        print(f"[{book_id}] No character style prefix configured")
        return False

    if cfg.type == "anthology":
        return _run_anthology_characters(book_id, cfg, force)
    return _run_for_book(book_id, force)


def _run_anthology_characters(book_id, cfg, force=False):
    """Run character images for each sub-book in an anthology."""
    from pipeline.config import WEB_DATA_DIR
    anthology_path = cfg.web_book_dir / "anthology.json"
    if not anthology_path.exists():
        print(f"[{book_id}] anthology.json not found")
        return False
    with open(anthology_path) as f:
        anthology = json.load(f)
    story_ids = anthology.get("storyBookIds", [])
    print(f"[{book_id}] Generating characters for {len(story_ids)} story-books")

    os.makedirs(os.path.dirname(CHECKPOINT_PATH), exist_ok=True)
    if os.path.exists(CHECKPOINT_PATH):
        state = load_json(CHECKPOINT_PATH)
    else:
        state = {"completed": [], "prompts": {}}

    for story_id in story_ids:
        story_dir = WEB_DATA_DIR / "books" / story_id
        ann_path = str(story_dir / "annotations.json")
        ch_path = str(story_dir / "chapters.json")

        chars = _get_top_characters_from_paths(ann_path, ch_path, n=6)
        if not chars:
            print(f"  [{story_id}] No characters found, skipping")
            continue

        print(f"\n  [{story_id}] Top characters: {', '.join(c['name'] for c in chars)}")
        tasks = [(story_id, c) for c in chars]

        remaining = [
            (bid, c) for bid, c in tasks
            if f"{bid}/{slugify(c['name'])}" not in state["completed"]
        ]

        if not remaining and not force:
            print(f"  [{story_id}] All character images complete!")
        else:
            path_overrides = {story_id: (ann_path, ch_path)}
            prompts = build_all_prompts(tasks, state, path_overrides=path_overrides)
            generate_all_images(tasks, prompts, state, style_prefix=cfg.character_style_prefix)

        # Update annotations for this sub-book
        annotations = load_json(ann_path)
        for char in chars:
            name = char["name"]
            slug = slugify(name)
            web_path_webp = os.path.join(WEB_DIR, story_id, f"{slug}.webp")
            web_path_png = os.path.join(WEB_DIR, story_id, f"{slug}.png")
            has_webp = os.path.exists(web_path_webp)
            has_png = os.path.exists(web_path_png)
            if name in annotations["glossary"] and (has_webp or has_png):
                ext = "webp" if has_webp else "png"
                annotations["glossary"][name]["image"] = f"/data/images/characters/{story_id}/{slug}.{ext}"
        save_json(ann_path, annotations)
        print(f"  [{story_id}] Updated annotations")

    return True


def run_all(force=False):
    """Run character images for all books."""
    for book_id in BOOKS:
        run(book_id, force=force)
    print("Done!")


def main():
    parser = argparse.ArgumentParser(description="Generate character portraits")
    parser.add_argument("--book", default=None, help="Book ID (omit for all)")
    parser.add_argument("--all", action="store_true", help="Process all books")
    parser.add_argument("--force", action="store_true", help="Force re-run")
    args = parser.parse_args()

    if args.all or args.book is None:
        run_all(force=args.force)
    else:
        run(args.book, force=args.force)


if __name__ == "__main__":
    main()
