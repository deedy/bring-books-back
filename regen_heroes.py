"""Generate 16:9 landscape hero banners for all 9 books.

Usage:
    uv run python regen_heroes.py
    uv run python regen_heroes.py --book ponniyin-selvan
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

load_dotenv()

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
IMAGE_MODEL = "gemini-3-pro-image-preview"
LANDSCAPE_RATIO = 16 / 9
OUTPUT_DIR = "web/public/data/images/heroes"

HERO_PROMPTS = {
    "baeesween-sadi": (
        "Generate an edge-to-edge illustration in vintage Indian woodblock print style "
        "with saffron, indigo, and gold palette. "
        "A panoramic vision of 22nd-century India: a futuristic city nestled in mountains, "
        "lush orchards with enormous fruits, flying machines in the sky, advanced irrigation channels, "
        "radiant sunrise casting golden light across the landscape. "
        "Bright, vivid, saturated colors. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
    "mrinalini": (
        "Generate an edge-to-edge illustration in Bengali miniature painting style "
        "with vermilion, purple, emerald, and gold palette. "
        "A wide panoramic landscape of 13th-century Bengal: "
        "a serene lotus pond in the foreground, ancient temples of Navadwip with ornate spires "
        "rising across the midground, the Ganges river shimmering at twilight under a magenta sky. "
        "Boats on the river, birds in flight, lush tropical vegetation. "
        "NO people, NO figures. Pure landscape scenery. "
        "Bright, vivid, saturated colors. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
    "alaler-gharer-dulal": (
        "Generate an edge-to-edge illustration in colonial Calcutta watercolor style "
        "with sepia, indigo, and ochre palette. "
        "1850s Calcutta: a wealthy Bengali mansion with ornate columns and arches, "
        "a bustling courtyard filled with servants and visitors, colonial architecture visible, "
        "the Hooghly river and boats in the distance, warm afternoon light. "
        "Bright, vivid, saturated colors. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
    "ponniyin-selvan": (
        "Generate an edge-to-edge illustration in Tanjore painting style "
        "with gold, crimson, emerald, and lapis lazuli palette. "
        "The Chola empire at its peak: the grand Brihadeeswarar temple towering over the scene, "
        "the Kaveri river flowing through lush palm groves, warriors on elephants, "
        "a magnificent sunset casting golden light over the ancient kingdom. "
        "Bright, vivid, saturated colors. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
    "barrister-parvatishan": (
        "Generate an edge-to-edge illustration in 1920s Indian watercolor style "
        "with warm, humorous tones. "
        "A wide panoramic scene: a grand English port with a large steamship docked, "
        "fog rolling over Victorian buildings and lampposts on the left, "
        "Indian architectural motifs and warm golden colors blending in on the right. "
        "Luggage and trunks on the dock, seagulls overhead, two cultures colliding in architecture. "
        "NO people, NO figures. Pure landscape/architecture scenery. "
        "Bright, vivid, saturated colors. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
    "matira-manisha": (
        "Generate an edge-to-edge illustration in Pattachitra folk art style from Odisha "
        "with ochre, terracotta, and indigo palette. "
        "Rural Odisha: expansive rice paddies stretching to the horizon, "
        "a thatched farmhouse with a courtyard, farmers working in the fields, "
        "a dramatic monsoon sky with billowing clouds, lush green vegetation. "
        "Bright, vivid, saturated colors. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
    "shyamchi-aai": (
        "Generate an edge-to-edge illustration in Warli tribal art combined with Marathi folk painting style "
        "with saffron, ochre, and green palette. "
        "A mother and young son sitting together on a village porch, "
        "Konkan fields stretching behind them, a golden sunset sky, "
        "a mango tree laden with fruit, wildflowers in the foreground. "
        "Bright, vivid, saturated colors. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
    "chandrakanta": (
        "Generate an edge-to-edge illustration in Mughal miniature painting style "
        "with gold, crimson, and emerald palette. "
        "Grand ornate palaces with domes and minarets, a magical tilism labyrinth "
        "with glowing pathways, a moonlit scene with ornate Rajput architecture, "
        "mystery and enchantment in the air, starlit sky. "
        "Bright, vivid, saturated colors. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
    "kayar": (
        "Generate an edge-to-edge illustration in Kerala mural painting style "
        "with deep green, gold, and ochre palette. "
        "Kerala backwaters: tall coconut palms swaying over calm canals, "
        "coir workers spinning rope on the shore, traditional houseboats (kettuvallam), "
        "lush tropical greenery, warm golden light filtering through the palms. "
        "Bright, vivid, saturated colors. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
}


def crop_to_landscape(img: Image.Image) -> Image.Image:
    """Center-crop image to exactly 16:9."""
    w, h = img.size
    target_h = int(w / LANDSCAPE_RATIO)
    if target_h <= h:
        top = (h - target_h) // 2
        return img.crop((0, top, w, top + target_h))
    else:
        target_w = int(h * LANDSCAPE_RATIO)
        left = (w - target_w) // 2
        return img.crop((left, 0, left + target_w, h))


def generate_hero(book_id: str, prompt: str, max_retries: int = 5):
    """Generate a single hero image with retries."""
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

                    # Save PNG
                    png_path = os.path.join(OUTPUT_DIR, f"{book_id}.png")
                    img.save(png_path, "PNG")

                    # Save WebP
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--book", default="all", help="Book ID or 'all'")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if args.book == "all":
        targets = HERO_PROMPTS
    else:
        if args.book not in HERO_PROMPTS:
            print(f"Unknown book: {args.book}")
            print(f"Available: {', '.join(HERO_PROMPTS.keys())}")
            return
        targets = {args.book: HERO_PROMPTS[args.book]}

    # Filter out already-existing
    to_generate = {}
    for book_id, prompt in targets.items():
        webp_path = os.path.join(OUTPUT_DIR, f"{book_id}.webp")
        if os.path.exists(webp_path):
            print(f"[{book_id}] Already exists, skipping (delete to regenerate)")
        else:
            to_generate[book_id] = prompt

    if not to_generate:
        print("Nothing to generate!")
        return

    print(f"Generating hero images for {len(to_generate)} book(s) in parallel...\n")

    with ThreadPoolExecutor(max_workers=len(to_generate)) as executor:
        futures = {
            executor.submit(generate_hero, book_id, prompt): book_id
            for book_id, prompt in to_generate.items()
        }
        for future in as_completed(futures):
            book_id = futures[future]
            try:
                success = future.result()
                if success:
                    print(f"[{book_id}] Done!")
                else:
                    print(f"[{book_id}] Failed!")
            except Exception as e:
                print(f"[{book_id}] Exception: {e}")

    print("\nAll done!")


if __name__ == "__main__":
    main()
