"""
Generate character portrait images for the top 6 most-frequent characters per book.

Phase 1: Build all 30 portrait prompts in parallel (Gemini Flash — fast).
Phase 2: Generate all 30 images in parallel (Gemini Pro image — slow, 15 workers).

Checkpoint-based: safe to interrupt and resume.
"""

import os
import re
import json
import time
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types
from PIL import Image

from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
IMAGE_MODEL = "gemini-3-pro-image-preview"
TEXT_MODEL = "gemini-2.0-flash"

CHECKPOINT_PATH = "data/character_images_checkpoint.json"
OUTPUT_DIR = "character_images"
WEB_DIR = "web/public/data/images/characters"

checkpoint_lock = threading.Lock()

BOOK_IDS = [
    "ponniyin-selvan",
    "mrinalini",
    "alaler-gharer-dulal",
    "baeesween-sadi",
    "barrister-parvatishan",
]

STYLE_PREFIXES = {
    "ponniyin-selvan": (
        "Generate an image in the style of a Tanjore painting — rich gold leaf accents, "
        "vibrant jewel tones (deep red, emerald green, royal blue), ornate decorative borders. "
        "The style should feel like a traditional South Indian temple painting with warm "
        "golden lighting and detailed ornamentation. "
        "No text, no lettering, no words anywhere in the image. "
        "10th century Chola dynasty South India setting.\n\n"
    ),
    "mrinalini": (
        "Generate an image in the style of a vintage Bengali miniature painting "
        "from the 19th century. Monochromatic warm sepia and brown tones with fine "
        "crosshatch engraving lines, like a classic book illustration. "
        "A single accent color of deep vermilion red used sparingly for emphasis. "
        "The composition should feel like a woodblock print from a 19th century "
        "Bengali literary journal — detailed, contemplative, with strong chiaroscuro. "
        "No text, no lettering, no words anywhere in the image. "
        "13th century Bengal setting with Hindu and Muslim architectural elements.\n\n"
    ),
    "alaler-gharer-dulal": (
        "Generate an image in the style of a Bengali woodblock print from the 1850s. "
        "Monochromatic warm sepia tones with fine crosshatch engraving lines. "
        "A single accent color of deep indigo blue used sparingly for emphasis. "
        "The composition should feel like an illustration from the first Bengali novels — "
        "detailed, satirical, with strong contrast. "
        "No text, no lettering, no words anywhere in the image. "
        "19th century colonial Calcutta setting.\n\n"
    ),
    "baeesween-sadi": (
        "Generate an image in the style of a vintage Indian woodblock print. "
        "Monochromatic warm sepia and brown tones with fine crosshatch engraving lines. "
        "A single accent color of deep saffron orange used sparingly for emphasis. "
        "The composition should feel like a classic book illustration — detailed, "
        "contemplative, with strong chiaroscuro. "
        "No text, no lettering, no words anywhere in the image.\n\n"
    ),
    "barrister-parvatishan": (
        "Generate an image in the style of a 1920s Indian watercolor illustration. "
        "Soft sepia base with hand-tinted accents of indigo and vermilion. "
        "The style should feel like an illustration from an early 20th century "
        "Indian literary magazine — warm, humorous, detailed character study. "
        "No text, no lettering, no words anywhere in the image. "
        "Early 20th century India / Edwardian England setting.\n\n"
    ),
}


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
    annotations = load_json(f"web/public/data/books/{book_id}/annotations.json")
    chapters_data = load_json(f"web/public/data/books/{book_id}/chapters.json")
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
    annotations = load_json(f"web/public/data/books/{book_id}/annotations.json")
    chapters_data = load_json(f"web/public/data/books/{book_id}/chapters.json")
    for ch in chapters_data["chapters"]:
        ch_terms = annotations.get("chapters", {}).get(ch["id"], [])
        if character_name in ch_terms:
            return ch["paragraphs"][:n_paragraphs]
    return []


# ─── Phase 1: Text prompt generation (parallel, fast) ────────────────────

def build_portrait_prompt(book_id, character):
    """Use Gemini Flash to build a portrait prompt from character info + context."""
    client = genai.Client(api_key=GEMINI_API_KEY)
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

    response = client.models.generate_content(
        model=TEXT_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.7,
        ),
    )
    return response.text.strip()


def build_all_prompts(tasks, state):
    """Build text prompts for all characters in parallel (15 workers, Flash is fast)."""
    prompts = {}  # key -> prompt string

    # Reuse cached prompts from checkpoint
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
    prompt_lock = threading.Lock()

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
                # Save to checkpoint
                with checkpoint_lock:
                    state.setdefault("prompts", {})[key] = prompt_text
                    save_json(CHECKPOINT_PATH, state)
                print(f"    [{done}/{len(tasks)}] {key}: prompt OK")
            except Exception as e:
                print(f"    [{done}/{len(tasks)}] {key}: prompt FAILED ({e})")

    return prompts


# ─── Phase 2: Image generation (parallel, slow) ──────────────────────────

def generate_single_image(book_id, slug, prompt_text, retries=3):
    """Generate one portrait image. Each call creates its own client."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    style_prefix = STYLE_PREFIXES[book_id]

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

                    # Copy to web dir
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
    """Generate all portrait images in parallel (15 workers)."""
    need_images = []
    for book_id, char in tasks:
        key = f"{book_id}/{slugify(char['name'])}"
        if key in state["completed"]:
            continue
        if key not in prompts:
            continue  # prompt failed
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


# ─── Annotations update ──────────────────────────────────────────────────

def update_annotations(book_id, characters):
    ann_path = f"web/public/data/books/{book_id}/annotations.json"
    annotations = load_json(ann_path)

    for char in characters:
        name = char["name"]
        slug = slugify(name)
        web_path = os.path.join(WEB_DIR, book_id, f"{slug}.png")
        if os.path.exists(web_path) and name in annotations["glossary"]:
            annotations["glossary"][name]["image"] = f"/data/images/characters/{book_id}/{slug}.png"

    save_json(ann_path, annotations)
    print(f"  Updated annotations for {book_id}")


# ─── Main ─────────────────────────────────────────────────────────────────

def main():
    os.makedirs(os.path.dirname(CHECKPOINT_PATH), exist_ok=True)
    if os.path.exists(CHECKPOINT_PATH):
        state = load_json(CHECKPOINT_PATH)
    else:
        state = {"completed": [], "prompts": {}}

    # Gather all character tasks
    all_tasks = []
    for book_id in BOOK_IDS:
        chars = get_top_characters(book_id, n=6)
        print(f"\n[{book_id}] Top 6 characters:")
        for c in chars:
            print(f"  {c['name']} ({c['count']} chapters)")
        all_tasks.extend([(book_id, c) for c in chars])

    remaining = [
        (bid, c) for bid, c in all_tasks
        if f"{bid}/{slugify(c['name'])}" not in state["completed"]
    ]
    print(f"\n{'='*60}")
    print(f"Total: {len(all_tasks)} characters, {len(remaining)} remaining")
    print(f"{'='*60}")

    # Phase 1: Build all text prompts in parallel
    print(f"\n--- Phase 1: Text prompts ---")
    prompts = build_all_prompts(all_tasks, state)

    # Phase 2: Generate all images in parallel
    print(f"\n--- Phase 2: Image generation ---")
    generate_all_images(all_tasks, prompts, state)

    # Phase 3: Update annotations
    print(f"\n--- Phase 3: Update annotations ---")
    for book_id in BOOK_IDS:
        chars = get_top_characters(book_id, n=6)
        update_annotations(book_id, chars)

    # Summary
    print(f"\n{'='*60}")
    total_images = 0
    for book_id in BOOK_IDS:
        web_book_dir = os.path.join(WEB_DIR, book_id)
        if os.path.exists(web_book_dir):
            count = len([f for f in os.listdir(web_book_dir) if f.endswith(".png")])
            total_images += count
            print(f"  {book_id}: {count} portraits")
    print(f"  Total: {total_images} portrait images")
    print("Done!")


if __name__ == "__main__":
    main()
