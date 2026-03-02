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


def get_top_characters(book_id, n=6):
    cfg = get_book(book_id)
    ann_path = str(cfg.web_annotations_json)
    ch_path = str(cfg.web_chapters_json)

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
        first_chapter_idx = None
        for i, ch_id in enumerate(chapter_ids):
            ch_terms = annotations.get("chapters", {}).get(ch_id, [])
            if name in ch_terms:
                count += 1
                if first_chapter_idx is None:
                    first_chapter_idx = i
        characters.append({
            "name": name,
            "description": entry["description"],
            "count": count,
            "first_chapter_idx": first_chapter_idx if first_chapter_idx is not None else len(chapter_ids),
        })

    characters.sort(key=lambda x: (-x["count"], x["name"]))
    return characters[:n]


def get_first_paragraphs(book_id, character_name, n_paragraphs=3):
    cfg = get_book(book_id)
    ann_path = str(cfg.web_annotations_json)
    ch_path = str(cfg.web_chapters_json)

    if not os.path.exists(ann_path) or not os.path.exists(ch_path):
        return []

    annotations = load_json(ann_path)
    chapters_data = load_json(ch_path)
    for ch in chapters_data["chapters"]:
        ch_terms = annotations.get("chapters", {}).get(ch["id"], [])
        if character_name in ch_terms:
            return ch["paragraphs"][:n_paragraphs]
    return []


def build_portrait_prompt(book_id, character):
    name = character["name"]
    description = character["description"]
    paragraphs = get_first_paragraphs(book_id, name)
    context_text = "\n".join(paragraphs) if paragraphs else ""

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


def build_all_prompts(tasks, state):
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
            f = executor.submit(build_portrait_prompt, book_id, char)
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


def generate_single_image(book_id, slug, prompt_text, retries=3):
    cfg = get_book(book_id)
    client = genai.Client(api_key=GEMINI_API_KEY)
    style_prefix = cfg.character_style_prefix

    full_prompt = (
        "A character portrait, head and upper body, facing slightly to the side. "
        "The subject is centered. Square composition (1:1 ratio). No text.\n\n"
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
                    crop_to_square(output_path)

                    web_book_dir = os.path.join(WEB_DIR, book_id)
                    os.makedirs(web_book_dir, exist_ok=True)
                    shutil.copy2(output_path, os.path.join(web_book_dir, f"{slug}.png"))
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


def generate_all_images(tasks, prompts, state):
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
            f = executor.submit(generate_single_image, book_id, slug, prompts[key])
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

    for char in characters:
        name = char["name"]
        slug = slugify(name)
        web_path = os.path.join(WEB_DIR, book_id, f"{slug}.png")
        if os.path.exists(web_path) and name in annotations["glossary"]:
            annotations["glossary"][name]["image"] = f"/data/images/characters/{book_id}/{slug}.png"

    save_json(ann_path, annotations)
    print(f"  Updated annotations for {book_id}")


def run(book_id, force=False):
    """Run character image generation for a single book. Returns True on success."""
    cfg = get_book(book_id)
    if not cfg.character_style_prefix:
        print(f"[{book_id}] No character style prefix configured")
        return False

    os.makedirs(os.path.dirname(CHECKPOINT_PATH), exist_ok=True)
    if os.path.exists(CHECKPOINT_PATH):
        state = load_json(CHECKPOINT_PATH)
    else:
        state = {"completed": [], "prompts": {}}

    chars = get_top_characters(book_id, n=6)
    if not chars:
        print(f"[{book_id}] No characters found (annotations missing?)")
        return False

    print(f"\n[{book_id}] Top 6 characters:")
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
