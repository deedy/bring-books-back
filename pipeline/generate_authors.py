"""Generate author portrait images.

Usage (standalone):
    uv run python -m pipeline.generate_authors --book chandrakanta
    uv run python -m pipeline.generate_authors --all
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
OUTPUT_DIR = str(WEB_DATA_DIR / "images" / "authors")


def generate_author_image(author_id, prompt, max_retries=5):
    client = genai.Client(api_key=GEMINI_API_KEY)

    for attempt in range(max_retries):
        try:
            print(f"  [{author_id}] Attempt {attempt + 1}...")
            full_prompt = (
                "Edge-to-edge portrait filling the entire frame. "
                "No border, no frame, no margin, no white space. "
                + prompt
            )
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

            if not response.candidates or not response.candidates[0].content.parts:
                print(f"  [{author_id}] No parts in response, retrying...")
                time.sleep(5)
                continue

            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    img = Image.open(io.BytesIO(part.inline_data.data))

                    png_path = os.path.join(OUTPUT_DIR, f"{author_id}.png")
                    img.save(png_path, "PNG")

                    webp_path = os.path.join(OUTPUT_DIR, f"{author_id}.webp")
                    img.save(webp_path, "WEBP", quality=90)

                    print(f"  [{author_id}] Saved {img.size[0]}x{img.size[1]} -> {webp_path}")
                    return True

            print(f"  [{author_id}] No image in response parts, retrying...")
            time.sleep(5)

        except Exception as e:
            print(f"  [{author_id}] Error: {e}")
            time.sleep(10)

    print(f"  [{author_id}] FAILED after {max_retries} attempts")
    return False


def _build_author_prompt(cfg):
    """Build an image generation prompt for an author portrait."""
    return (
        f"A dignified portrait of {cfg.author_name} ({cfg.author_years}), "
        f"the renowned author of \"{cfg.title}\". "
        f"{cfg.style_context}. "
        f"{cfg.character_style_prefix}"
        "Historically accurate attire and appearance for the era and region. "
        "Warm, respectful, literary portrait style. "
        "No text, no lettering, no words anywhere in the image."
    )


def run(book_id, force=False):
    """Run author portrait generation for a book. Returns True on success."""
    cfg = get_book(book_id)
    author_id = cfg.author_id

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    webp_path = os.path.join(OUTPUT_DIR, f"{author_id}.webp")
    if not force and os.path.exists(webp_path):
        print(f"[{author_id}] Author image already exists, skipping (use --force to regenerate)")
        return True

    prompt = _build_author_prompt(cfg)
    return generate_author_image(author_id, prompt)


def run_all(force=False):
    """Run author portraits for all books."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Deduplicate by author_id (multiple books can share an author)
    targets = {}
    for book_id, cfg in BOOKS.items():
        author_id = cfg.author_id
        webp_path = os.path.join(OUTPUT_DIR, f"{author_id}.webp")
        if not force and os.path.exists(webp_path):
            print(f"[{author_id}] Already exists, skipping")
        elif author_id not in targets:
            targets[author_id] = _build_author_prompt(cfg)

    if not targets:
        print("Nothing to generate!")
        return

    print(f"Generating author images for {len(targets)} author(s) in parallel...\n")

    with ThreadPoolExecutor(max_workers=min(len(targets), 4)) as executor:
        futures = {
            executor.submit(generate_author_image, aid, prompt): aid
            for aid, prompt in targets.items()
        }
        for future in as_completed(futures):
            aid = futures[future]
            try:
                success = future.result()
                print(f"[{aid}] {'Done!' if success else 'Failed!'}")
            except Exception as e:
                print(f"[{aid}] Exception: {e}")

    print("\nAll done!")


def main():
    parser = argparse.ArgumentParser(description="Generate author portraits")
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
