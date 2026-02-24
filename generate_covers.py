"""Generate beautiful, colorful cover images for both books."""

import os
import time
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ["GEMINI_API_KEY"]
MODEL = "gemini-3-pro-image-preview"
client = genai.Client(api_key=API_KEY)

ASPECT_NOTE = (
    "IMPORTANT: The image MUST have an aspect ratio of exactly 148:210 (width:height), "
    "matching A5 paper proportions. This means width is about 70.5% of height. "
    "For example 1050x1488 pixels. "
)

COVERS = {
    "chapter_images/cover.png": (
        ASPECT_NOTE +
        "Generate a stunning book cover illustration in the style of a vintage Indian "
        "woodblock print, but with RICH, VIBRANT colors. Deep saffron orange, royal indigo blue, "
        "warm gold, and earthy brown tones with fine crosshatch engraving textures. "
        "No text, no lettering, no words anywhere in the image. Portrait orientation.\n\n"
        "Scene: A sweeping panoramic vision of 22nd century India as imagined from the 1920s. "
        "In the foreground, an elderly bearded sage in simple robes stands at the mouth of "
        "a Himalayan cave, gazing down at a transformed landscape below. In the valley, "
        "a gleaming futuristic city nestles among lush orchards and gardens — clean white "
        "buildings with classical Indian architecture, electric trains threading through "
        "mountains, wide tree-lined avenues. The sky is a magnificent sunrise with layers "
        "of deep saffron, gold, and indigo. Waterfalls cascade from snow-capped peaks. "
        "Flying machines shaped like mythical birds dot the distant sky. The mood is "
        "wonder, utopian beauty, and the awakening of a visionary dream. Rich warm palette "
        "with jewel-like colors — this should be the most visually striking image in the book."
    ),
    "mrinalini_images/cover.png": (
        ASPECT_NOTE +
        "Generate a stunning book cover illustration in the style of a vintage Bengali "
        "miniature painting, but with RICH, VIBRANT colors. Deep vermilion red, royal "
        "purple, emerald green, warm gold, and ivory white with fine crosshatch engraving "
        "textures. No text, no lettering, no words anywhere in the image. Portrait orientation.\n\n"
        "Scene: 13th century Bengal during the golden age before the Muslim conquest. "
        "In the foreground, a young Hindu warrior prince in ornate armor stands beside "
        "a beautiful Bengali woman in an elegant red and gold sari — they face each other "
        "across a sacred lotus pond under a full moon. Behind them, the magnificent temples "
        "and palaces of Navadwip rise against a dramatic twilight sky of deep purple and "
        "gold. The Ganges river flows in the background, reflecting moonlight. On one side, "
        "lush mango orchards and flowering gardens in rich greens; on the other, the distant "
        "silhouette of approaching horsemen suggesting the coming invasion. Sacred flames "
        "from temple lamps cast warm golden light. The mood is epic romance against the "
        "backdrop of a civilization at a turning point. Jewel-toned, luminous, deeply "
        "colorful — this should be the most visually striking image in the book."
    ),
}


def generate_cover(output_path, prompt, retries=3):
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )
            if response.parts is None:
                if attempt < retries - 1:
                    print(f"  (no parts, retry {attempt+1})...", end=" ", flush=True)
                    time.sleep(3)
                    continue
                raise RuntimeError("No parts returned after retries")

            for part in response.parts:
                if part.inline_data is not None:
                    img = part.as_image()
                    img.save(output_path)
                    return output_path

            if attempt < retries - 1:
                print(f"  (no image, retry {attempt+1})...", end=" ", flush=True)
                time.sleep(3)
                continue
            raise RuntimeError("No image in response after retries")
        except RuntimeError:
            raise
        except Exception as e:
            if attempt < retries - 1:
                print(f"  (error: {e}, retry {attempt+1})...", end=" ", flush=True)
                time.sleep(3)
                continue
            raise RuntimeError(f"API error after retries: {e}")


A5_RATIO = 148 / 210  # width / height = 0.7048


def crop_to_a5(path):
    """Center-crop an image to A5 aspect ratio."""
    img = Image.open(path)
    w, h = img.size
    current_ratio = w / h

    if abs(current_ratio - A5_RATIO) < 0.01:
        print(f"(already A5)", end=" ")
        return

    if current_ratio > A5_RATIO:
        # Too wide — crop width
        new_w = int(h * A5_RATIO)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    else:
        # Too tall — crop height
        new_h = int(w / A5_RATIO)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))

    img.save(path)
    print(f"(cropped to {img.size[0]}x{img.size[1]})", end=" ")


def main():
    for path, prompt in COVERS.items():
        book = "Baeesween Sadi" if "chapter" in path else "Mrinalini"
        print(f"Generating {book} cover...", end=" ", flush=True)
        result = generate_cover(path, prompt)
        crop_to_a5(result)
        print(f"OK -> {result}")
        time.sleep(2)

    print("\nBoth covers generated!")


if __name__ == "__main__":
    main()
