"""Generate missing chapter images — massively parallel."""

import json
import os
import sys
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
    "atmospheric, shadowy, dramatic chiaroscuro lighting. "
    "No text, no lettering. 1930s-1960s Calcutta setting. "
)


def generate_one(story_id, chapter, story_title):
    """Generate prompt + image for one chapter."""
    num = chapter["number"]
    img_dir = f"{WEB_IMAGES}/{story_id}"
    os.makedirs(img_dir, exist_ok=True)
    img_name = f"pNone_chapter_{num}"
    png_path = f"{img_dir}/{img_name}.png"
    webp_path = f"{img_dir}/{img_name}.webp"

    # Generate scene prompt
    text = "\n\n".join(chapter["paragraphs"][:5])
    excerpt = text[:1500] + "..." if len(text) > 1500 else text

    resp = text_client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Create a vivid scene description for AI image generation. "
                    "3-5 sentences. Focus on setting, lighting, mood, action. "
                    "No text instructions. Use neutral language. Output ONLY the description."
                ),
            },
            {
                "role": "user",
                "content": f'Story: "{story_title}"\nChapter {num}: "{chapter["title"]}"\n\nExcerpt:\n{excerpt}',
            },
        ],
        temperature=0.7,
    )
    prompt = resp.choices[0].message.content.strip()

    # Generate image
    client = genai.Client(api_key=GEMINI_API_KEY)
    full_prompt = (
        "Edge-to-edge illustration filling the entire frame. "
        "No border, no frame, no margin. " + IMAGE_STYLE + prompt
    )

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=IMAGE_MODEL,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                    image_config=types.ImageConfig(aspect_ratio="16:9"),
                ),
            )
            if response.parts:
                for part in response.parts:
                    if part.inline_data is not None:
                        img = part.as_image()
                        img.save(png_path)
                        img = Image.open(png_path)
                        img.save(webp_path, "WEBP", quality=85)
                        web_ref = f"/data/images/chapters/{story_id}/{img_name}.webp"
                        print(f"  DONE: {story_id} ch {num}", flush=True)
                        return story_id, num, web_ref
        except Exception as e:
            print(f"  RETRY {attempt+1}: {story_id} ch {num}: {e}", flush=True)

    print(f"  FAIL: {story_id} ch {num}", flush=True)
    return story_id, num, None


def main():
    # Find all missing images
    import glob

    tasks = []
    for meta_path in sorted(glob.glob(f"{WEB_DATA}/byomkesh-*/meta.json")):
        sid = os.path.basename(os.path.dirname(meta_path))
        with open(meta_path) as f:
            meta = json.load(f)
        tc = meta.get("totalChapters", 1)
        if tc <= 1:
            continue

        chapters_path = f"{WEB_DATA}/{sid}/chapters.json"
        with open(chapters_path) as f:
            data = json.load(f)

        for ch in data["chapters"]:
            num = ch["number"]
            webp = f"{WEB_IMAGES}/{sid}/pNone_chapter_{num}.webp"
            if not os.path.exists(webp):
                tasks.append((sid, ch, meta["title"]))

    if not tasks:
        print("All images present!")
        return

    print(f"Generating {len(tasks)} missing images with {min(len(tasks), 8)} workers...", flush=True)

    # All in parallel — no rate limiting, let the API handle it
    results = []
    with ThreadPoolExecutor(max_workers=min(len(tasks), 8)) as pool:
        futures = {pool.submit(generate_one, sid, ch, title): (sid, ch["number"]) for sid, ch, title in tasks}
        for future in as_completed(futures):
            results.append(future.result())

    # Update chapters.json for each story
    updated_stories = {}
    for sid, num, web_ref in results:
        if web_ref:
            if sid not in updated_stories:
                updated_stories[sid] = {}
            updated_stories[sid][num] = web_ref

    for sid, refs in updated_stories.items():
        chapters_path = f"{WEB_DATA}/{sid}/chapters.json"
        with open(chapters_path) as f:
            data = json.load(f)
        for ch in data["chapters"]:
            if ch["number"] in refs:
                ch["image"] = refs[ch["number"]]
        with open(chapters_path, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    success = sum(1 for _, _, r in results if r)
    print(f"\nDone! {success}/{len(tasks)} images generated.", flush=True)


if __name__ == "__main__":
    main()
