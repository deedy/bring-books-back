"""Generate 16:9 landscape hero banners for books.

Usage (standalone):
    uv run python -m pipeline.generate_heroes --book chandrakanta
    uv run python -m pipeline.generate_heroes --all
"""

import argparse
import os
import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv

from pipeline.config import get_book, BOOKS, WEB_DATA_DIR

load_dotenv()

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
IMAGE_MODEL = "gemini-3.1-flash-image-preview"
LANDSCAPE_RATIO = 16 / 9
OUTPUT_DIR = str(WEB_DATA_DIR / "images" / "heroes")


def crop_to_landscape(img):
    w, h = img.size
    target_h = int(w / LANDSCAPE_RATIO)
    if target_h <= h:
        top = (h - target_h) // 2
        return img.crop((0, top, w, top + target_h))
    else:
        target_w = int(h * LANDSCAPE_RATIO)
        left = (w - target_w) // 2
        return img.crop((left, 0, left + target_w, h))


def generate_hero(book_id, prompt, max_retries=5):
    client = genai.Client(api_key=GEMINI_API_KEY)

    for attempt in range(max_retries):
        try:
            print(f"  [{book_id}] Attempt {attempt + 1}...")
            response = client.models.generate_content(
                model=IMAGE_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )

            if not response.candidates or not response.candidates[0].content.parts:
                print(f"  [{book_id}] No parts in response, retrying...")
                time.sleep(5)
                continue

            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    img = Image.open(io.BytesIO(part.inline_data.data))
                    img = crop_to_landscape(img)

                    png_path = os.path.join(OUTPUT_DIR, f"{book_id}.png")
                    img.save(png_path, "PNG")

                    webp_path = os.path.join(OUTPUT_DIR, f"{book_id}.webp")
                    img.save(webp_path, "WEBP", quality=90)

                    print(f"  [{book_id}] Saved {img.size[0]}x{img.size[1]} -> {webp_path}")
                    return True

            print(f"  [{book_id}] No image in response parts, retrying...")
            time.sleep(5)

        except Exception as e:
            print(f"  [{book_id}] Error: {e}")
            time.sleep(10)

    print(f"  [{book_id}] FAILED after {max_retries} attempts")
    return False


def run(book_id, force=False):
    """Run hero banner generation for a book. Returns True on success."""
    cfg = get_book(book_id)

    if not cfg.hero_prompt:
        print(f"[{book_id}] No hero prompt configured")
        return False

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    webp_path = os.path.join(OUTPUT_DIR, f"{book_id}.webp")
    if not force and os.path.exists(webp_path):
        print(f"[{book_id}] Hero already exists, skipping (use --force to regenerate)")
        return True

    return generate_hero(book_id, cfg.hero_prompt)


def run_all(force=False):
    """Run hero banners for all books with prompts."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    targets = {}
    for book_id, cfg in BOOKS.items():
        if not cfg.hero_prompt:
            continue
        webp_path = os.path.join(OUTPUT_DIR, f"{book_id}.webp")
        if not force and os.path.exists(webp_path):
            print(f"[{book_id}] Already exists, skipping")
        else:
            targets[book_id] = cfg.hero_prompt

    if not targets:
        print("Nothing to generate!")
        return

    print(f"Generating hero images for {len(targets)} book(s) in parallel...\n")

    with ThreadPoolExecutor(max_workers=len(targets)) as executor:
        futures = {
            executor.submit(generate_hero, book_id, prompt): book_id
            for book_id, prompt in targets.items()
        }
        for future in as_completed(futures):
            book_id = futures[future]
            try:
                success = future.result()
                print(f"[{book_id}] {'Done!' if success else 'Failed!'}")
            except Exception as e:
                print(f"[{book_id}] Exception: {e}")

    print("\nAll done!")


def main():
    parser = argparse.ArgumentParser(description="Generate hero banners")
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
