"""Generate character portrait images for the top 6 characters in each Feluda story-book.

Usage:
    uv run python -m pipeline.generate_feluda_characters
    uv run python -m pipeline.generate_feluda_characters --force

Reads anthology.json for story-book IDs, then for each book with annotations.json:
  1. Finds top 6 characters by chapter frequency
  2. Generates portrait prompts via GPT-4.1 (OpenRouter)
  3. Generates 1:1 square images via Nano Banana 2 (Gemini)
  4. Saves PNG + WebP, updates annotations.json with image paths
"""

import argparse
import os
import re
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types
from openai import OpenAI
from PIL import Image
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WEB_DATA_DIR = PROJECT_ROOT / "web" / "public" / "data"
WEB_CHAR_DIR = WEB_DATA_DIR / "images" / "characters"

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
IMAGE_MODEL = "gemini-3.1-flash-image-preview"
TEXT_MODEL = "openai/gpt-4.1"

text_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

STYLE_PREFIX = (
    "Generate an image in the style of Satyajit Ray's own illustrations — "
    "clean line work with watercolor washes, warm earth tones, "
    "amber, sepia, deep green. Atmospheric, cinematic character portrait. "
    "No text, no lettering, no words anywhere in the image. "
    "Indian setting, 1960s-1990s.\n\n"
)

PORTRAIT_PREFIX = (
    "A character portrait, head and upper body, facing slightly to the side. "
    "The subject is centered. Edge-to-edge, no border, no frame, no margin. "
    "No text.\n\n"
)

CHECKPOINT_PATH = PROJECT_ROOT / "data" / "feluda_character_images_checkpoint.json"
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


def get_story_book_ids():
    anthology_path = WEB_DATA_DIR / "books" / "feluda" / "anthology.json"
    data = load_json(str(anthology_path))
    return data["storyBookIds"]


def get_top_characters(book_id, n=6):
    ann_path = WEB_DATA_DIR / "books" / book_id / "annotations.json"
    ch_path = WEB_DATA_DIR / "books" / book_id / "chapters.json"

    if not ann_path.exists() or not ch_path.exists():
        return []

    annotations = load_json(str(ann_path))
    chapters_data = load_json(str(ch_path))
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


def get_first_paragraphs(book_id, character_name, n_paragraphs=3):
    ann_path = WEB_DATA_DIR / "books" / book_id / "annotations.json"
    ch_path = WEB_DATA_DIR / "books" / book_id / "chapters.json"

    if not ann_path.exists() or not ch_path.exists():
        return []

    annotations = load_json(str(ann_path))
    chapters_data = load_json(str(ch_path))
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


def generate_single_image(book_id, slug, prompt_text, retries=3):
    client = genai.Client(api_key=GEMINI_API_KEY)

    full_prompt = PORTRAIT_PREFIX + STYLE_PREFIX + prompt_text

    web_book_dir = WEB_CHAR_DIR / book_id
    os.makedirs(str(web_book_dir), exist_ok=True)
    png_path = web_book_dir / f"{slug}.png"
    webp_path = web_book_dir / f"{slug}.webp"

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
                    img.save(str(png_path))

                    # Convert to WebP with PIL
                    pil_img = Image.open(str(png_path))
                    pil_img.save(str(webp_path), "WEBP", quality=90)
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


def generate_character_portrait(book_id, char, key, state):
    """Single task: generate prompt (or use cached) + generate image for one character."""
    slug = slugify(char["name"])

    # Step 1: Get or generate prompt
    with checkpoint_lock:
        cached_prompt = state.get("prompts", {}).get(key)

    if cached_prompt:
        prompt_text = cached_prompt
    else:
        prompt_text = build_portrait_prompt(book_id, char)
        with checkpoint_lock:
            state.setdefault("prompts", {})[key] = prompt_text
            save_json(str(CHECKPOINT_PATH), state)

    # Step 2: Generate image
    generate_single_image(book_id, slug, prompt_text)

    with checkpoint_lock:
        state["completed"].append(key)
        save_json(str(CHECKPOINT_PATH), state)

    return key


def update_annotations(book_id, characters):
    ann_path = WEB_DATA_DIR / "books" / book_id / "annotations.json"
    if not ann_path.exists():
        return

    annotations = load_json(str(ann_path))
    updated = False

    for char in characters:
        name = char["name"]
        slug = slugify(name)
        webp_path = WEB_CHAR_DIR / book_id / f"{slug}.webp"
        if webp_path.exists() and name in annotations["glossary"]:
            annotations["glossary"][name]["image"] = f"/data/images/characters/{book_id}/{slug}.webp"
            updated = True

    if updated:
        save_json(str(ann_path), annotations)


def main():
    parser = argparse.ArgumentParser(description="Generate Feluda character portraits")
    parser.add_argument("--force", action="store_true", help="Force re-generation")
    args = parser.parse_args()

    story_book_ids = get_story_book_ids()
    print(f"Found {len(story_book_ids)} Feluda story-books")

    # Load checkpoint
    os.makedirs(str(CHECKPOINT_PATH.parent), exist_ok=True)
    if CHECKPOINT_PATH.exists():
        state = load_json(str(CHECKPOINT_PATH))
    else:
        state = {"completed": [], "prompts": {}}

    # Collect all tasks across ALL books at once
    all_tasks = []
    books_chars = {}  # book_id -> chars list, for annotation update
    for book_id in story_book_ids:
        ann_path = WEB_DATA_DIR / "books" / book_id / "annotations.json"
        if not ann_path.exists():
            continue

        chars = get_top_characters(book_id, n=6)
        if not chars:
            continue

        books_chars[book_id] = chars
        print(f"\n[{book_id}] Top characters:")
        for c in chars:
            print(f"  {c['name']} ({c['count']} chapters)")

        for c in chars:
            key = f"{book_id}/{slugify(c['name'])}"
            if key in state["completed"] and not args.force:
                continue
            all_tasks.append((book_id, c, key))

    if not all_tasks:
        print("\nAll character images already generated!")
        for book_id, chars in books_chars.items():
            update_annotations(book_id, chars)
        return

    total = len(all_tasks)
    print(f"\n--- Generating {total} character portraits (15 workers, prompt+image per task) ---")

    done_count = [0]
    count_lock = threading.Lock()

    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {}
        for book_id, char, key in all_tasks:
            f = executor.submit(generate_character_portrait, book_id, char, key, state)
            futures[f] = (book_id, char["name"], key)

        for future in as_completed(futures):
            book_id, name, key = futures[future]
            with count_lock:
                done_count[0] += 1
                n = done_count[0]
            try:
                future.result()
                print(f"  [{n}/{total}] {key}: OK")
            except Exception as e:
                print(f"  [{n}/{total}] {key}: FAILED ({e})")

    print(f"\n--- Updating annotations ---")
    for book_id, chars in books_chars.items():
        update_annotations(book_id, chars)
        print(f"  Updated {book_id}")

    print("\nDone!")


if __name__ == "__main__":
    main()
