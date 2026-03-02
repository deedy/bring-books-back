"""Generate 16:9 landscape hero banners for multi-chapter Feluda story-books."""

import json
import os
import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types
from openai import OpenAI
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
IMAGE_MODEL = "gemini-3.1-flash-image-preview"
OUTPUT_DIR = "web/public/data/images/heroes"
CATALOG_PATH = "web/public/data/catalog.json"
ANTHOLOGY_PATH = "web/public/data/books/feluda/anthology.json"

STYLE_PREFIX = (
    "Generate an image in the style of Satyajit Ray's own illustrations — "
    "clean line work with watercolor washes, warm earth tones, amber, sepia, "
    "deep green, and dusty rose. The composition should feel like a classic "
    "mystery book illustration — atmospheric, cinematic, with dramatic lighting. "
    "No text, no lettering, no words anywhere in the image. "
    "Indian settings from the 1960s-1990s.\n\nScene: "
)


def get_multi_chapter_books():
    """Return list of (book_id, title, summary) for multi-chapter feluda story-books."""
    with open(ANTHOLOGY_PATH) as f:
        story_ids = set(json.load(f)["storyBookIds"])

    with open(CATALOG_PATH) as f:
        catalog = json.load(f)

    results = []
    for book in catalog["books"]:
        bid = book["id"]
        if bid in story_ids and book.get("totalChapters", 0) > 1:
            webp_path = os.path.join(OUTPUT_DIR, f"{bid}.webp")
            if not os.path.exists(webp_path):
                results.append((bid, book["title"], book.get("summary", "")))
    return results


def generate_scene_prompt(title, summary):
    """Use GPT-4.1 to create a hero banner scene prompt."""
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )
    response = client.chat.completions.create(
        model="openai/gpt-4.1",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an art director creating hero banner prompts for detective story pages. "
                    "Given a story title and summary, write a 2-3 sentence landscape scene prompt. "
                    "Focus on the key LOCATION and ATMOSPHERE of the story — wide establishing shot, "
                    "cinematic lighting, moody atmosphere. NO people, NO figures, NO faces. "
                    'Return JSON: {"prompt": "..."}'
                ),
            },
            {
                "role": "user",
                "content": f"Title: {title}\nSummary: {summary}",
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
    )
    data = json.loads(response.choices[0].message.content)
    return data["prompt"]


def generate_hero_image(book_id, prompt, max_retries=5):
    """Generate hero banner using Gemini."""
    client = genai.Client(api_key=GEMINI_API_KEY)

    for attempt in range(max_retries):
        try:
            print(f"  [{book_id}] Image attempt {attempt + 1}...")
            full_prompt = (
                "Edge-to-edge illustration filling the entire frame. "
                "No border, no frame, no margin, no vignette, no white space. "
                + STYLE_PREFIX + prompt
            )
            response = client.models.generate_content(
                model=IMAGE_MODEL,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                    image_config=types.ImageConfig(aspect_ratio="16:9"),
                ),
            )

            if not response.candidates or not response.candidates[0].content.parts:
                print(f"  [{book_id}] No parts in response, retrying...")
                time.sleep(5)
                continue

            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    img = Image.open(io.BytesIO(part.inline_data.data))

                    png_path = os.path.join(OUTPUT_DIR, f"{book_id}.png")
                    img.save(png_path, "PNG")

                    webp_path = os.path.join(OUTPUT_DIR, f"{book_id}.webp")
                    img.save(webp_path, "WEBP", quality=90)

                    print(f"  [{book_id}] Saved {img.size[0]}x{img.size[1]}")
                    return True

            print(f"  [{book_id}] No image in parts, retrying...")
            time.sleep(5)

        except Exception as e:
            print(f"  [{book_id}] Error: {e}")
            time.sleep(10)

    print(f"  [{book_id}] FAILED after {max_retries} attempts")
    return False


def process_book(book_id, title, summary):
    """Generate prompt then image for one book."""
    try:
        print(f"[{book_id}] Generating scene prompt...")
        prompt = generate_scene_prompt(title, summary)
        print(f"[{book_id}] Prompt: {prompt[:100]}...")
        success = generate_hero_image(book_id, prompt)
        return book_id, success
    except Exception as e:
        print(f"[{book_id}] Exception: {e}")
        return book_id, False


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    books = get_multi_chapter_books()
    if not books:
        print("No books need hero banners!")
        return

    print(f"Generating hero banners for {len(books)} books:\n")
    for bid, title, _ in books:
        print(f"  - {bid}: {title}")
    print()

    results = {}
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {
            executor.submit(process_book, bid, title, summary): bid
            for bid, title, summary in books
        }
        for future in as_completed(futures):
            bid = futures[future]
            try:
                _, success = future.result()
                results[bid] = success
                status = "Done" if success else "FAILED"
                print(f"[{bid}] {status}")
            except Exception as e:
                results[bid] = False
                print(f"[{bid}] Exception: {e}")

    succeeded = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    print(f"\nAll done! {succeeded} succeeded, {failed} failed.")

    if failed:
        print("Failed books:")
        for bid, ok in results.items():
            if not ok:
                print(f"  - {bid}")


if __name__ == "__main__":
    main()
