"""
Generate chapter header images for 'Barrister Parvatishan' by Mokkapati Narasimha Shastri
using Gemini image generation.

Two images per chapter:
  - A5 portrait (148:210) for the typeset PDF book
  - Landscape (16:9) for the web reader

Consistent aesthetic: vintage Indian watercolor illustration, 1920s setting,
warm sepia/ochre/indigo palette, mixing rural Andhra and Edwardian England scenes.
"""

import os
import json
import re
import time
from google import genai
from google.genai import types
from PIL import Image

from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
TRANSLATION_FILE = "data/barrister_english.txt"
OUTPUT_DIR = "barrister_images"
CHECKPOINT_FILE = "data/barrister_images_checkpoint.json"
PROMPT_CACHE_FILE = "data/barrister_image_prompts.json"
IMAGE_MODEL = "gemini-3-pro-image-preview"
TEXT_MODEL = "gemini-2.0-flash"

client = genai.Client(api_key=GEMINI_API_KEY)
os.makedirs(OUTPUT_DIR, exist_ok=True)

A5_RATIO = 148 / 210
LANDSCAPE_RATIO = 16 / 9

# ── Consistent style prefix ──
STYLE_PREFIX = (
    "Generate an image in the style of a vintage Indian watercolor illustration "
    "from the 1920s. Warm sepia, ochre, and cream tones with accents of deep "
    "indigo blue and vermillion red. Soft brushstrokes and gentle washes. "
    "The composition should feel like an illustration from a classic Indian "
    "literary magazine of the colonial era — elegant, slightly whimsical, with "
    "period-accurate clothing and architecture. Detailed but not photorealistic. "
    "No text, no lettering, no words anywhere in the image. "
    "\n\nScene: "
)

# ── Character descriptions ──
PARVATISHAN = "a thin, earnest young Telugu Brahmin man in his 20s with a shaved head and tuft, wearing traditional dhoti, later in ill-fitting English suit"
NARRATOR = "the author Mokkapati Narasimha Shastri, a genial Telugu gentleman with spectacles"
RAJU = "Parvatishan's Indian friend in England, more worldly and confident"
LANDLADY = "a kind middle-aged English woman running a boarding house"

# ── Chapter definitions ──
# Part 1: Parvatisham's Origins (pages 10-135)
# Part 2: England Adventures (pages 136-339)
# Part 3: Return Home (pages 346-543)

CHAPTERS = [
    # Part 1: Origins
    {"part": 1, "number": 1, "start_page": 10, "end_page": 26,
     "title": "Parvatisham's Origins"},
    {"part": 1, "number": 2, "start_page": 27, "end_page": 31,
     "title": "Childhood Mischief"},
    {"part": 1, "number": 3, "start_page": 32, "end_page": 34,
     "title": "School Days"},
    {"part": 1, "number": 4, "start_page": 35, "end_page": 39,
     "title": "The Decision"},
    {"part": 1, "number": 5, "start_page": 40, "end_page": 45,
     "title": "Wedding and Departure"},
    {"part": 1, "number": 6, "start_page": 46, "end_page": 47,
     "title": "Farewell"},
    {"part": 1, "number": 7, "start_page": 48, "end_page": 50,
     "title": "The Journey Begins"},
    {"part": 1, "number": 8, "start_page": 51, "end_page": 135,
     "title": "Voyage to England"},
    # Part 2: England
    {"part": 2, "number": 1, "start_page": 136, "end_page": 159,
     "title": "Arrival in England"},
    {"part": 2, "number": 5, "start_page": 160, "end_page": 166,
     "title": "First Acquaintances"},
    {"part": 2, "number": 6, "start_page": 167, "end_page": 173,
     "title": "Culture Shocks"},
    {"part": 2, "number": 7, "start_page": 174, "end_page": 179,
     "title": "Lodgings"},
    {"part": 2, "number": 8, "start_page": 180, "end_page": 182,
     "title": "The Boarding House"},
    {"part": 2, "number": 9, "start_page": 183, "end_page": 190,
     "title": "New Routines"},
    {"part": 2, "number": 10, "start_page": 191, "end_page": 200,
     "title": "English Lessons"},
    {"part": 2, "number": 11, "start_page": 201, "end_page": 208,
     "title": "Social Life"},
    {"part": 2, "number": 12, "start_page": 209, "end_page": 213,
     "title": "Indian Friends"},
    {"part": 2, "number": 13, "start_page": 214, "end_page": 220,
     "title": "Raju's Absence"},
    {"part": 2, "number": 14, "start_page": 221, "end_page": 224,
     "title": "Growing Fame"},
    {"part": 2, "number": 15, "start_page": 225, "end_page": 231,
     "title": "Edinburgh"},
    {"part": 2, "number": 16, "start_page": 232, "end_page": 242,
     "title": "Studies"},
    {"part": 2, "number": 17, "start_page": 243, "end_page": 254,
     "title": "Amusements"},
    {"part": 2, "number": 18, "start_page": 255, "end_page": 263,
     "title": "Theatre and Music"},
    {"part": 2, "number": 19, "start_page": 264, "end_page": 273,
     "title": "The Landlady's Daughter"},
    {"part": 2, "number": 20, "start_page": 274, "end_page": 280,
     "title": "New Lodgings"},
    {"part": 2, "number": 21, "start_page": 281, "end_page": 284,
     "title": "Wartime England"},
    {"part": 2, "number": 22, "start_page": 285, "end_page": 295,
     "title": "The Great War"},
    {"part": 2, "number": 23, "start_page": 296, "end_page": 308,
     "title": "Examinations"},
    {"part": 2, "number": 24, "start_page": 309, "end_page": 328,
     "title": "Farewell to England"},
    {"part": 2, "number": 26, "start_page": 329, "end_page": 339,
     "title": "The Voyage Home"},
    # Part 3: Return Home
    {"part": 3, "number": 1, "start_page": 346, "end_page": 352,
     "title": "Homecoming"},
    {"part": 3, "number": 2, "start_page": 353, "end_page": 358,
     "title": "The Train Home"},
    {"part": 3, "number": 3, "start_page": 359, "end_page": 367,
     "title": "Arrival in the Village"},
    {"part": 3, "number": 4, "start_page": 368, "end_page": 381,
     "title": "Family Reunion"},
    {"part": 3, "number": 6, "start_page": 385, "end_page": 398,
     "title": "Public Reception"},
    {"part": 3, "number": 7, "start_page": 399, "end_page": 401,
     "title": "The Speech"},
    {"part": 3, "number": 8, "start_page": 402, "end_page": 408,
     "title": "Train Journey"},
    {"part": 3, "number": 9, "start_page": 409, "end_page": 428,
     "title": "Starting Practice"},
    {"part": 3, "number": 11, "start_page": 429, "end_page": 439,
     "title": "Marriage Proposal"},
    {"part": 3, "number": 12, "start_page": 440, "end_page": 444,
     "title": "Wedding Preparations"},
    {"part": 3, "number": 13, "start_page": 445, "end_page": 452,
     "title": "The Wedding"},
    {"part": 3, "number": 14, "start_page": 453, "end_page": 461,
     "title": "Married Life"},
    {"part": 3, "number": 15, "start_page": 462, "end_page": 469,
     "title": "Return to Practice"},
    {"part": 3, "number": 16, "start_page": 470, "end_page": 476,
     "title": "Court Cases"},
    {"part": 3, "number": 17, "start_page": 477, "end_page": 488,
     "title": "Building a Reputation"},
    {"part": 3, "number": 18, "start_page": 489, "end_page": 499,
     "title": "Legal Career"},
    {"part": 3, "number": 19, "start_page": 500, "end_page": 509,
     "title": "A Turning Point"},
    {"part": 3, "number": 20, "start_page": 510, "end_page": 516,
     "title": "Public Life"},
    {"part": 3, "number": 21, "start_page": 517, "end_page": 526,
     "title": "Politics"},
    {"part": 3, "number": 22, "start_page": 527, "end_page": 543,
     "title": "Final Chapter"},
]


def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False)


def load_pages():
    with open(TRANSLATION_FILE) as f:
        text = f.read()
    parts = re.split(r"--- Page (\d+) ---\n", text)
    pages = {}
    i = 1
    while i < len(parts):
        page_num = int(parts[i])
        body = parts[i + 1] if i + 1 < len(parts) else ""
        pages[page_num] = body.strip()
        i += 2
    return pages


def get_chapter_text(ch, pages):
    """Get first ~1500 chars of a chapter's text."""
    text_parts = []
    for pn in range(ch["start_page"], min(ch["end_page"] + 1, ch["start_page"] + 5)):
        if pn in pages:
            text_parts.append(pages[pn])
    full = "\n".join(text_parts)
    return full[:1500] + "..." if len(full) > 1500 else full


def make_key(ch):
    return f"p{ch['part']}_chapter_{ch['number']}"


def generate_scene_prompt(ch, body_text, prompt_cache):
    key = make_key(ch)
    if key in prompt_cache:
        return prompt_cache[key]

    setting = "rural Andhra Pradesh village" if ch["part"] != 2 else "Edwardian England"
    era = "1920s India" if ch["part"] != 2 else "1910s-1920s England"

    prompt = f"""You are creating a vivid scene description for a watercolor illustration of a chapter from "Barrister Parvatishan", a humorous Telugu novel set in {era}.

Key characters:
- Parvatishan: {PARVATISHAN}
- Narrator: {NARRATOR}
- Raju: {RAJU}

Write ONE scene description (3-5 sentences) for the most vivid or humorous moment in this chapter. Include: characters present, setting ({setting}), mood (usually humorous/whimsical), lighting, visual details.
Use NEUTRAL language — avoid words like "desperate", "tears", "blood", "death", "kill". Use cheerful, comic alternatives.
Output ONLY the scene description, nothing else.

Chapter {ch['number']} (Part {ch['part']}): {ch['title']}

{body_text}"""

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=TEXT_MODEL,
                contents=prompt,
            )
            desc = response.text.strip()
            prompt_cache[key] = desc
            save_json(PROMPT_CACHE_FILE, prompt_cache)
            return desc
        except Exception as e:
            if attempt < 2:
                time.sleep(3)
                continue
            raise RuntimeError(f"Prompt generation failed: {e}")


def generate_image(key, scene_desc, aspect="portrait", retries=3):
    if aspect == "portrait":
        ratio_text = "The image MUST be in PORTRAIT orientation, taller than wide (A5 ratio, roughly 148mm wide by 210mm tall)."
    else:
        ratio_text = "The image MUST be in LANDSCAPE orientation, wider than tall (16:9 ratio)."

    full_prompt = STYLE_PREFIX + scene_desc + "\n\n" + ratio_text

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
                    print(f"(no parts, retry {attempt+1})...", end=" ", flush=True)
                    time.sleep(3)
                    continue
                raise RuntimeError("No parts returned after retries")

            for part in response.parts:
                if part.inline_data is not None:
                    img = part.as_image()
                    suffix = "_web" if aspect == "landscape" else ""
                    path = os.path.join(OUTPUT_DIR, f"{key}{suffix}.png")
                    img.save(path)
                    return path

            if attempt < retries - 1:
                time.sleep(3)
                continue
            raise RuntimeError("No image in response after retries")
        except RuntimeError:
            raise
        except Exception as e:
            if attempt < retries - 1:
                print(f"(error: {e}, retry {attempt+1})...", end=" ", flush=True)
                time.sleep(3)
                continue
            raise RuntimeError(f"API error: {e}")


import threading
import concurrent.futures

checkpoint_lock = threading.Lock()
prompt_lock = threading.Lock()
MAX_WORKERS = 5


def process_chapter(ch, pages, prompt_cache, state, total):
    key = make_key(ch)

    with checkpoint_lock:
        if key in state["completed"]:
            return key, True

    body_text = get_chapter_text(ch, pages)

    # Step 1: Generate scene prompt (needs lock for shared cache)
    try:
        with prompt_lock:
            scene_desc = generate_scene_prompt(ch, body_text, prompt_cache)
    except Exception as e:
        print(f"  {key}: prompt FAILED — {e}", flush=True)
        return key, False

    # Step 2: Generate portrait image (for PDF)
    try:
        generate_image(key, scene_desc, aspect="portrait")
    except Exception as e:
        print(f"  {key}: portrait FAILED — {e}", flush=True)
        return key, False

    # Step 3: Generate landscape image (for web)
    try:
        generate_image(key, scene_desc, aspect="landscape")
    except Exception as e:
        print(f"  {key}: web FAILED (portrait OK) — {e}", flush=True)

    with checkpoint_lock:
        state["completed"].append(key)
        save_json(CHECKPOINT_FILE, state)
        done = len(state["completed"])
    print(f"  {key} OK ({done}/{total})", flush=True)
    return key, True


def main():
    pages = load_pages()
    prompt_cache = load_json(PROMPT_CACHE_FILE, {})
    state = load_json(CHECKPOINT_FILE, {"completed": []})

    total = len(CHAPTERS)
    remaining = [ch for ch in CHAPTERS if make_key(ch) not in state["completed"]]
    print(f"Total: {total}, Already done: {total - len(remaining)}, Remaining: {len(remaining)}")
    print(f"Starting with {MAX_WORKERS} concurrent workers...")

    # First, generate all scene prompts sequentially (fast, uses text model)
    print("Generating scene prompts...")
    for ch in remaining:
        key = make_key(ch)
        if key not in prompt_cache:
            body_text = get_chapter_text(ch, pages)
            try:
                generate_scene_prompt(ch, body_text, prompt_cache)
                print(f"  {key}: prompt OK", flush=True)
            except Exception as e:
                print(f"  {key}: prompt FAILED — {e}", flush=True)
    print(f"All prompts ready. Generating images with {MAX_WORKERS} workers...")

    # Then generate images in parallel
    failed = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(process_chapter, ch, pages, prompt_cache, state, total): make_key(ch)
            for ch in remaining
        }
        for future in concurrent.futures.as_completed(futures):
            key = futures[future]
            try:
                _, ok = future.result()
                if not ok:
                    failed.append(key)
            except Exception as e:
                print(f"  {key}: EXCEPTION — {e}", flush=True)
                failed.append(key)

    done = len(state["completed"])
    print(f"\nGenerated {done}/{total} chapter images in {OUTPUT_DIR}/")
    if failed:
        print(f"Failed: {failed}. Re-run to retry.")


if __name__ == "__main__":
    main()
