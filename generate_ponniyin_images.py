"""
Generate chapter header images for Ponniyin Selvan by Kalki Krishnamurthy
using ONLY Gemini (nano-banana-pro-preview).

Two images per chapter:
  - A5 portrait (148:210) for the typeset PDF book
  - Landscape (16:9) for the web reader

Single-stage: Gemini generates images directly from style prefix + chapter-derived
scene descriptions. No OpenAI involved.

Consistent aesthetic: Chola dynasty Tanjore painting style — rich gold, deep
crimson, emerald green, lapis blue.
"""

import os
import sys
import json
import time
from google import genai
from google.genai import types
from PIL import Image

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, "scripts")
from parse_ponniyin_chapters import extract_chapters

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
TRANSLATION_FILE = "data/ponniyin_english.txt"
OUTPUT_DIR = "ponniyin_images"
CHECKPOINT_FILE = "data/ponniyin_images_checkpoint.json"
PROMPT_CACHE_FILE = "data/ponniyin_image_prompts.json"
IMAGE_MODEL = "gemini-3-pro-image-preview"
TEXT_MODEL = "gemini-2.0-flash"  # fast model for text-only prompt generation

client = genai.Client(api_key=GEMINI_API_KEY)
os.makedirs(OUTPUT_DIR, exist_ok=True)

A5_RATIO = 148 / 210
LANDSCAPE_RATIO = 16 / 9

# ── Consistent style prefix ──
STYLE_PREFIX = (
    "Generate an image in the style of a classic Tanjore painting (Thanjavur art) "
    "from South India. RICH, VIBRANT colors: deep gold leaf, crimson red, emerald "
    "green, lapis lazuli blue, and warm bronze tones. Fine detailed ornamentation "
    "with semi-precious stone inlay effects. The composition should feel like a "
    "luxury illustrated manuscript of the Chola dynasty era — ornate borders, "
    "detailed figures with traditional Chola jewelry, silk garments, and temple "
    "architecture. Tropical South Indian landscape with palm trees, lotus ponds, "
    "and Kaveri river when outdoors. "
    "No text, no lettering, no words anywhere in the image. "
    "10th century Chola empire setting.\n\nScene: "
)

# ── Character descriptions ──
VANDIYATHEVAN = "a handsome young Vaanar warrior (25), athletic, turban, sword, charming roguish smile"
KUNDAVAI = "a beautiful Chola princess (22), regal, ornate gold jewelry, silk sari, commanding eyes"
ARULMOZHI = "a radiant young Chola prince, divine face, simple warrior garb, compassionate"
NANDINI = "a stunningly beautiful young woman, heavy gold jewelry, mysterious dark eyes"
AZHVARKADIYAN = "a Vaishnavite pilgrim, shaved head with tuft, sacred marks, shrewd eyes, staff"
PAZHUVETTARAYAR = "an aged powerful commander, massive build, fierce, heavy armor, white mustache"
SUNDARA_CHOLA = "an aging emperor, gaunt noble face, royal silks, golden crown"
VANATHI = "a shy delicate princess, gentle face, soft silk garments"
POONGUZHALI = "a wild free-spirited boatwoman, windswept hair, simple clothes, by the sea"


def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False)


def make_key(ch):
    """Create unique key like p1_chapter_3."""
    return f"p{ch['part']}_chapter_{ch['number']}"


def generate_scene_prompt(ch, prompt_cache):
    """Use Gemini text mode to generate a scene description."""
    key = make_key(ch)
    if key in prompt_cache:
        return prompt_cache[key]

    body = ch["body"][:1500] + "..." if len(ch["body"]) > 1500 else ch["body"]

    prompt = f"""You are creating a vivid scene description for a Tanjore painting illustration of a chapter from "Ponniyin Selvan" set in 10th century Chola empire South India.

Key characters:
- Vandiyathevan: {VANDIYATHEVAN}
- Kundavai: {KUNDAVAI}
- Arulmozhi Varman: {ARULMOZHI}
- Nandini: {NANDINI}
- Azhvarkadiyan: {AZHVARKADIYAN}
- Pazhuvettarayar: {PAZHUVETTARAYAR}
- Sundara Chola: {SUNDARA_CHOLA}
- Vanathi: {VANATHI}
- Poonguzhali: {POONGUZHALI}

Write ONE scene description (3-5 sentences) for the most vivid moment. Include: characters present, setting, mood, lighting, visual details.
Use NEUTRAL language — no "desperate", "tears", "blood", "death", "kill", "murder", "poison", "corpse", "stab", "suicide". Use alternatives like "tense", "confrontation", "fallen warrior".
Output ONLY the scene description.

Chapter {ch['number']} (Part {ch['part']} — {ch['partName']}): {ch['title']}

{body}"""

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=TEXT_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT"],
                    temperature=0.7,
                ),
            )
            if response.text:
                scene = response.text.strip()
                prompt_cache[key] = scene
                save_json(PROMPT_CACHE_FILE, prompt_cache)
                return scene
        except Exception as e:
            if attempt < 2:
                time.sleep(3)
                continue
            print(f"prompt gen failed: {e}")
            return None
    return None


def crop_to_ratio(path, target_ratio):
    """Center-crop image to target aspect ratio (w/h)."""
    img = Image.open(path)
    w, h = img.size
    if abs(w / h - target_ratio) < 0.02:
        return
    if w / h > target_ratio:
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    else:
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))
    img.save(path)


def generate_image(output_path, prompt_text, orientation, retries=3):
    """Generate image with Gemini."""
    if orientation == "portrait":
        aspect_note = "Portrait orientation, taller than wide (A5 book page ratio). "
    else:
        aspect_note = "Wide landscape orientation (16:9 ratio, cinematic banner). "

    full_prompt = aspect_note + STYLE_PREFIX + prompt_text

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
                raise RuntimeError("No parts returned")

            for part in response.parts:
                if part.inline_data is not None:
                    img = part.as_image()
                    img.save(output_path)
                    target = A5_RATIO if orientation == "portrait" else LANDSCAPE_RATIO
                    crop_to_ratio(output_path, target)
                    return output_path

            if attempt < retries - 1:
                time.sleep(3)
                continue
            raise RuntimeError("No image in response")
        except RuntimeError:
            raise
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(3)
                continue
            raise RuntimeError(f"API error: {e}")


def generate_cover(state):
    """Generate cover images (A5 + landscape)."""
    cover_scene = (
        "An epic panoramic composition of the 10th century Chola empire at its zenith. "
        f"In the center foreground, {ARULMOZHI} stands tall "
        "on the banks of the river Kaveri, golden armor gleaming in sunset. Beside him, "
        f"{KUNDAVAI} in a crimson and gold silk sari adorned with "
        "temple jewelry gazes across the river. Behind them rises the magnificent Brihadeeswarar "
        "temple of Thanjavur, its towering gopuram reaching into a spectacular sunset sky of "
        "deep saffron, gold, and violet. The Kaveri river flows in the middle ground, dotted "
        "with ornate boats. Lush palm groves and rice paddies stretch to the horizon. "
        "Elephants with gold caparisons and mounted warriors. "
        "Lotus flowers bloom in the foreground. Majestic golden-age splendor."
    )
    for orient, name in [("portrait", "cover"), ("landscape", "cover_web")]:
        if name in state["completed"]:
            print(f"  {name}: cached")
            continue
        path = os.path.join(OUTPUT_DIR, f"{name}.png")
        print(f"  {name}: generating...", end=" ", flush=True)
        try:
            generate_image(path, cover_scene, orient)
            state["completed"].append(name)
            save_json(CHECKPOINT_FILE, state)
            print(f"OK -> {path}")
        except Exception as e:
            print(f"FAILED: {e}")
        time.sleep(1.5)


def main():
    state = load_json(CHECKPOINT_FILE, {"completed": []})

    # Phase 0: Covers
    print("Covers:")
    generate_cover(state)

    # Phase 1: Load chapters
    if not os.path.exists(TRANSLATION_FILE):
        print(f"ERROR: {TRANSLATION_FILE} not found.")
        return
    text = open(TRANSLATION_FILE).read()
    chapters = extract_chapters(text)
    total = len(chapters)
    print(f"\nFound {total} chapters across 5 parts")

    prompt_cache = load_json(PROMPT_CACHE_FILE, {})
    cached_prompts = len([ch for ch in chapters if make_key(ch) in prompt_cache])
    print(f"Scene prompts: {cached_prompts} cached")

    # Process each chapter end-to-end: prompt → A5 → web (images start immediately)
    for i, ch in enumerate(chapters):
        key = make_key(ch)
        a5_key = f"{key}_a5"
        web_key = f"{key}_web"

        # Skip if both images already done
        if a5_key in state["completed"] and web_key in state["completed"]:
            continue

        # Step 1: Get or generate scene prompt
        scene = prompt_cache.get(key)
        if not scene:
            scene = generate_scene_prompt(ch, prompt_cache)
            if scene:
                print(f"  [{i+1}/{total}] P{ch['part']} Ch{ch['number']} prompt: {scene[:60]}...")
            else:
                print(f"  [{i+1}/{total}] P{ch['part']} Ch{ch['number']} prompt FAILED, skipping")
                continue

        # Step 2: A5 portrait image
        if a5_key not in state["completed"]:
            a5_path = os.path.join(OUTPUT_DIR, f"{key}.png")
            print(f"  [{i+1}/{total}] {key} A5: generating...", end=" ", flush=True)
            try:
                generate_image(a5_path, scene, "portrait")
                state["completed"].append(a5_key)
                save_json(CHECKPOINT_FILE, state)
                print("OK")
            except Exception as e:
                print(f"FAILED: {e}")
            time.sleep(1.5)

        # Step 3: Landscape web image
        if web_key not in state["completed"]:
            web_path = os.path.join(OUTPUT_DIR, f"{key}_web.png")
            print(f"  [{i+1}/{total}] {key} web: generating...", end=" ", flush=True)
            try:
                generate_image(web_path, scene, "landscape")
                state["completed"].append(web_key)
                save_json(CHECKPOINT_FILE, state)
                print("OK")
            except Exception as e:
                print(f"FAILED: {e}")
            time.sleep(1.5)

    a5_done = len([k for k in state["completed"] if k.endswith("_a5")])
    web_done = len([k for k in state["completed"] if k.endswith("_web")])
    print(f"\nDone: {a5_done}/{total} A5 + {web_done}/{total} web images in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
