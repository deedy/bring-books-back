"""
Regenerate ONLY the web (16:9 landscape) images for Mrinalini and Baeesween Sadi.
Overwrites existing _web.png files. Skips A5 portraits.
"""

import os
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types
from PIL import Image

from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
IMAGE_MODEL = "gemini-3-pro-image-preview"
LANDSCAPE_RATIO = 16 / 9

lock = threading.Lock()
progress = {"done": 0, "total": 0}


def crop_to_ratio(path, target_ratio):
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


def generate_web_image(client, output_path, style_prefix, prompt_text, retries=3):
    full_prompt = (
        "Wide landscape orientation (16:9 ratio, cinematic banner). "
        + style_prefix + prompt_text
    )
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
                    crop_to_ratio(output_path, LANDSCAPE_RATIO)
                    return True
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


def process_one(book_name, output_dir, style_prefix, key, prompt_text):
    client = genai.Client(api_key=GEMINI_API_KEY)
    web_path = os.path.join(output_dir, f"{key}_web.png")
    try:
        generate_web_image(client, web_path, style_prefix, prompt_text)
        with lock:
            progress["done"] += 1
            print(f"  [{progress['done']}/{progress['total']}] [{book_name}] {key}_web: OK")
    except Exception as e:
        with lock:
            progress["done"] += 1
            print(f"  [{progress['done']}/{progress['total']}] [{book_name}] {key}_web: FAILED ({e})")
    time.sleep(0.3)


# ── Import prompts from regenerate_images.py ──
from regenerate_images import (
    MRINALINI_STYLE, MRINALINI_PROMPTS,
    BAEESWEEN_STYLE, BAEESWEEN_PROMPTS,
)

JOBS = []
for key, prompt in MRINALINI_PROMPTS.items():
    JOBS.append(("Mrinalini", "mrinalini_images_v2", MRINALINI_STYLE, key, prompt))
for key, prompt in BAEESWEEN_PROMPTS.items():
    JOBS.append(("Baeesween", "baeesween_images_v2", BAEESWEEN_STYLE, key, prompt))

progress["total"] = len(JOBS)
print(f"Regenerating {len(JOBS)} web images (16:9) with 8 workers\n")

with ThreadPoolExecutor(max_workers=8) as executor:
    futures = [
        executor.submit(process_one, book, outdir, style, key, prompt)
        for book, outdir, style, key, prompt in JOBS
    ]
    for f in as_completed(futures):
        f.result()  # raise exceptions

print(f"\nDone! {progress['done']}/{progress['total']} web images regenerated.")
