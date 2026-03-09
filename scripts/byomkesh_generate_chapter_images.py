"""Step 3: Generate chapter images for split Byomkesh stories.

Usage:
    uv run python scripts/byomkesh_generate_chapter_images.py

For each new chapter across all split stories, generates a 16:9 landscape
scene image via Gemini, saves as PNG + WebP, and updates chapters.json.
"""

import json
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types
from openai import OpenAI
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

WEB_DATA = "web/public/data/books"
WEB_IMAGES = "web/public/data/images/chapters"

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
IMAGE_MODEL = "gemini-3.1-flash-image-preview"
TEXT_MODEL = "google/gemini-3-flash-preview"

text_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

IMAGE_STYLE = (
    "Generate an image in the style of 1930s-1940s Bengali book illustration — "
    "noir-influenced, moody ink washes with deep sepia, charcoal grey, "
    "muted amber, and flashes of deep crimson. "
    "The composition should feel like a classic pulp detective cover — "
    "atmospheric, shadowy, with dramatic chiaroscuro lighting. "
    "No text, no lettering, no words anywhere in the image. "
    "1930s-1960s Calcutta setting. "
)

# Rate limiting for Gemini
gemini_lock = threading.Lock()
last_gemini_call = [0.0]
GEMINI_DELAY = 1.5  # seconds between image gen calls


def generate_scene_prompt(chapter: dict, story_title: str) -> str:
    """Use Gemini Flash to create a scene description for image gen."""
    text = "\n\n".join(chapter["paragraphs"][:5])
    excerpt = text[:1500] + "..." if len(text) > 1500 else text

    response = text_client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are creating vivid scene descriptions for AI image generation of book chapter illustrations. "
                    "Given a chapter excerpt, write a 3-5 sentence scene description. "
                    "Focus on: visual setting, character positioning, lighting/mood, key action. "
                    "Do NOT include any text/lettering instructions. "
                    "Use neutral language — avoid words like 'desperate', 'tears', 'blood', 'death', 'kill'. "
                    "Output ONLY the scene description, nothing else."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Story: \"{story_title}\"\n"
                    f"Chapter {chapter['number']}: \"{chapter['title']}\"\n\n"
                    f"Chapter excerpt:\n{excerpt}"
                ),
            },
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def generate_image(output_path: str, prompt_text: str, retries=3) -> bool:
    """Generate a 16:9 image via Gemini."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    full_prompt = (
        "Edge-to-edge illustration filling the entire frame. "
        "No border, no frame, no margin, no vignette, no white space. "
        "The artwork must extend to all edges. "
        + IMAGE_STYLE + prompt_text
    )

    for attempt in range(retries):
        # Rate limit
        with gemini_lock:
            elapsed = time.time() - last_gemini_call[0]
            if elapsed < GEMINI_DELAY:
                time.sleep(GEMINI_DELAY - elapsed)
            last_gemini_call[0] = time.time()

        try:
            response = client.models.generate_content(
                model=IMAGE_MODEL,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                    image_config=types.ImageConfig(aspect_ratio="16:9"),
                ),
            )
            if response.parts is None:
                if attempt < retries - 1:
                    time.sleep(3)
                    continue
                print(f"    WARN: Safety filter blocked image for {output_path}")
                return False

            for part in response.parts:
                if part.inline_data is not None:
                    img = part.as_image()
                    img.save(output_path)
                    return True

            if attempt < retries - 1:
                time.sleep(3)
                continue
            return False
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(3)
                continue
            print(f"    ERROR generating {output_path}: {e}")
            return False


def png_to_webp(png_path: str) -> str:
    """Convert PNG to WebP, return WebP path."""
    webp_path = png_path.replace(".png", ".webp")
    img = Image.open(png_path)
    img.save(webp_path, "WEBP", quality=85)
    return webp_path


def process_story(story_id: str) -> int:
    """Generate images for all chapters of a story. Returns count generated."""
    chapters_path = f"{WEB_DATA}/{story_id}/chapters.json"
    images_dir = f"{WEB_IMAGES}/{story_id}"
    os.makedirs(images_dir, exist_ok=True)

    with open(chapters_path) as f:
        data = json.load(f)

    # Get story title from meta
    meta_path = f"{WEB_DATA}/{story_id}/meta.json"
    with open(meta_path) as f:
        meta = json.load(f)
    story_title = meta["title"]

    generated = 0
    updated = False

    for chapter in data["chapters"]:
        part = chapter.get("part")
        num = chapter["number"]
        img_name = f"p{part}_chapter_{num}"
        png_path = f"{images_dir}/{img_name}.png"
        webp_path = f"{images_dir}/{img_name}.webp"
        web_ref = f"/data/images/chapters/{story_id}/{img_name}.webp"

        # Skip if already has image
        if chapter.get("image") and os.path.exists(webp_path):
            continue

        print(f"  [{story_id}] Chapter {num}: generating prompt...")
        prompt = generate_scene_prompt(chapter, story_title)

        print(f"  [{story_id}] Chapter {num}: generating image...")
        success = generate_image(png_path, prompt)

        if success:
            png_to_webp(png_path)
            chapter["image"] = web_ref
            generated += 1
            updated = True
            print(f"  [{story_id}] Chapter {num}: done")
        else:
            print(f"  [{story_id}] Chapter {num}: FAILED")

    if updated:
        with open(chapters_path, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return generated


def main():
    # Find all split stories (totalChapters > 1 in meta.json)
    stories = []
    for entry in sorted(os.listdir(WEB_DATA)):
        if not entry.startswith("byomkesh-"):
            continue
        meta_path = f"{WEB_DATA}/{entry}/meta.json"
        if not os.path.exists(meta_path):
            continue
        with open(meta_path) as f:
            meta = json.load(f)
        if meta.get("totalChapters", 1) > 1:
            stories.append(entry)

    if not stories:
        print("No split stories found. Run Step 2 first.")
        return

    print(f"Generating chapter images for {len(stories)} stories...\n")

    total = 0
    # Process stories in parallel (4 at a time, rate-limited by gemini_lock)
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(process_story, sid): sid for sid in stories}
        for future in as_completed(futures):
            sid = futures[future]
            try:
                n = future.result()
                total += n
                print(f"  [{sid}] Generated {n} images")
            except Exception as e:
                print(f"  [{sid}] ERROR: {e}")

    print(f"\nDone! Generated {total} chapter images across {len(stories)} stories.")


if __name__ == "__main__":
    main()
