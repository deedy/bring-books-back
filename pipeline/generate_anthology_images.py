"""Generate cover images for anthology story-books + hero banner for the anthology.

Usage:
    uv run python -m pipeline.generate_anthology_images --book feluda
    uv run python -m pipeline.generate_anthology_images --book feluda --heroes-only
    uv run python -m pipeline.generate_anthology_images --book feluda --covers-only
"""

import argparse
import io
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types
from openai import OpenAI
from PIL import Image
from dotenv import load_dotenv

from pipeline.config import get_book, WEB_DATA_DIR, OPENROUTER_BASE_URL

load_dotenv()

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
IMAGE_MODEL = "gemini-3.1-flash-image-preview"

text_client = OpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=os.environ["OPENROUTER_API_KEY"],
)

COVERS_DIR = str(WEB_DATA_DIR / "images" / "covers")
HEROES_DIR = str(WEB_DATA_DIR / "images" / "heroes")


def generate_image(prompt, output_path, aspect_ratio="2:3", max_retries=5):
    """Generate a single image with Nano Banana 2."""
    client = genai.Client(api_key=GEMINI_API_KEY)

    for attempt in range(max_retries):
        try:
            full_prompt = (
                "Edge-to-edge illustration filling the entire frame. "
                "No border, no frame, no margin, no vignette, no white space. "
                + prompt
            )
            response = client.models.generate_content(
                model=IMAGE_MODEL,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                    image_config=types.ImageConfig(
                        aspect_ratio=aspect_ratio,
                    ),
                ),
            )

            if not response.candidates or not response.candidates[0].content.parts:
                print(f"    Attempt {attempt + 1}: No parts, retrying...")
                time.sleep(5)
                continue

            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    img = Image.open(io.BytesIO(part.inline_data.data))

                    png_path = output_path.replace(".webp", ".png")
                    img.save(png_path, "PNG")
                    img.save(output_path, "WEBP", quality=90)

                    print(f"    Saved {img.size[0]}x{img.size[1]} -> {output_path}")
                    return True

            print(f"    Attempt {attempt + 1}: No image in parts, retrying...")
            time.sleep(5)

        except Exception as e:
            print(f"    Attempt {attempt + 1}: Error: {e}")
            time.sleep(10)

    print(f"    FAILED after {max_retries} attempts")
    return False


def generate_cover_prompt(story_title, story_summary, cfg):
    """Generate a scene prompt for a story cover using GPT."""
    response = text_client.chat.completions.create(
        model="openai/gpt-4.1",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an art director creating cover image prompts for detective stories. "
                    "Given a story title and summary, write a single vivid scene prompt (2-3 sentences) "
                    "that captures the mood and setting of the story. "
                    "The scene should be atmospheric and cinematic — NO people, NO faces, NO figures. "
                    "Focus on key objects, locations, and mood. "
                    "Do NOT include any text or lettering in the scene. "
                    'Return JSON: {"prompt": "..."}'
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Story: {story_title}\n"
                    f"Author: {cfg.author_name}\n"
                    f"Genre: {', '.join(cfg.genre)}\n"
                    f"Summary: {story_summary}\n"
                ),
            },
        ],
        temperature=0.7,
        response_format={"type": "json_object"},
    )
    result = json.loads(response.choices[0].message.content)
    return result["prompt"]


def run(book_id, force=False, covers_only=False, heroes_only=False):
    cfg = get_book(book_id)
    if cfg.type != "anthology":
        print(f"[{book_id}] Not an anthology")
        return

    os.makedirs(COVERS_DIR, exist_ok=True)
    os.makedirs(HEROES_DIR, exist_ok=True)

    # Load anthology data
    anthology_path = str(cfg.web_book_dir / "anthology.json")
    with open(anthology_path) as f:
        anthology = json.load(f)

    # Load catalog for story summaries
    catalog_path = str(WEB_DATA_DIR / "catalog.json")
    with open(catalog_path) as f:
        catalog = json.load(f)

    tasks = []

    # Hero banner for the anthology itself
    if not covers_only:
        hero_path = os.path.join(HEROES_DIR, f"{book_id}.webp")
        if force or not os.path.exists(hero_path):
            tasks.append({
                "id": book_id,
                "type": "hero",
                "prompt": cfg.hero_prompt,
                "output": hero_path,
                "aspect_ratio": "16:9",
            })
        else:
            print(f"[{book_id}] Hero already exists, skipping")

    # Cover images for each story-book
    if not heroes_only:
        for story_book_id in anthology["storyBookIds"]:
            cover_path = os.path.join(COVERS_DIR, f"{story_book_id}.webp")
            if not force and os.path.exists(cover_path):
                print(f"[{story_book_id}] Cover already exists, skipping")
                continue

            story_entry = next((b for b in catalog["books"] if b["id"] == story_book_id), None)
            if not story_entry:
                print(f"[{story_book_id}] Not found in catalog, skipping")
                continue

            tasks.append({
                "id": story_book_id,
                "type": "cover",
                "title": story_entry["title"],
                "summary": story_entry["summary"],
                "output": cover_path,
                "aspect_ratio": "2:3",
            })

    if not tasks:
        print("Nothing to generate!")
        return

    print(f"\nGenerating {len(tasks)} images in parallel...\n")

    def process_task(task):
        task_id = task["id"]
        task_type = task["type"]

        if task_type == "cover":
            print(f"[{task_id}] Generating cover prompt...")
            scene_prompt = generate_cover_prompt(task["title"], task["summary"], cfg)
            full_prompt = cfg.image_style_prefix + scene_prompt
        else:
            full_prompt = task["prompt"]

        print(f"[{task_id}] Generating {task_type} image...")
        return generate_image(full_prompt, task["output"], aspect_ratio=task["aspect_ratio"])

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(process_task, task): task["id"]
            for task in tasks
        }
        done = 0
        for future in as_completed(futures):
            task_id = futures[future]
            done += 1
            try:
                success = future.result()
                print(f"[{task_id}] {'Done' if success else 'FAILED'} ({done}/{len(tasks)})")
            except Exception as e:
                print(f"[{task_id}] Exception: {e} ({done}/{len(tasks)})")

    # Update catalog: point each story-book to its own cover
    with open(catalog_path) as f:
        catalog = json.load(f)

    updated = 0
    for book in catalog["books"]:
        if book.get("anthologyId") == book_id:
            story_cover = f"/data/images/covers/{book['id']}.webp"
            cover_file = os.path.join(COVERS_DIR, f"{book['id']}.webp")
            if os.path.exists(cover_file):
                book["coverImage"] = story_cover
                updated += 1
                # Also update meta.json
                meta_path = str(WEB_DATA_DIR / "books" / book["id"] / "meta.json")
                if os.path.exists(meta_path):
                    with open(meta_path) as f:
                        meta = json.load(f)
                    meta["coverImage"] = story_cover
                    with open(meta_path, "w") as f:
                        json.dump(meta, f, ensure_ascii=False, indent=2)

    with open(catalog_path, "w") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    print(f"\nUpdated {updated} cover references in catalog.json")
    print("All done!")


def main():
    parser = argparse.ArgumentParser(description="Generate anthology cover + hero images")
    parser.add_argument("--book", required=True, help="Anthology book ID")
    parser.add_argument("--force", action="store_true", help="Force re-run")
    parser.add_argument("--covers-only", action="store_true", help="Only generate covers")
    parser.add_argument("--heroes-only", action="store_true", help="Only generate hero banner")
    args = parser.parse_args()

    run(args.book, force=args.force, covers_only=args.covers_only, heroes_only=args.heroes_only)


if __name__ == "__main__":
    main()
