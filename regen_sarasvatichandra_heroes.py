"""Generate hero banners for Sarasvatichandra sub-books."""

import os, time
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
IMAGE_MODEL = "gemini-3.1-flash-image-preview"
client = genai.Client(api_key=GEMINI_API_KEY)

WEB = "web/public/data/images/heroes"

BASE_STYLE = (
    "Edge-to-edge illustration filling the entire frame. "
    "No border, no frame, no margin. "
    "Late 19th-century Indian miniature painting blended with Victorian-era illustration. "
    "Warm golden light, rich jewel tones, detailed architecture. "
    "NO people in focus, NO close-up figures. Pure atmospheric landscape. "
    "16:9 cinematic landscape ratio. "
    "No text, no lettering, no words anywhere. "
)

HEROES = [
    {
        "id": "sarasvatichandra-buddhidhan-s-administration",
        "prompt": (
            BASE_STYLE +
            "A grand darbar hall of a princely state in Gujarat — "
            "carved sandstone pillars receding into depth, painted ceilings with floral motifs, "
            "silk curtains in gold and crimson, oil lamps casting warm amber light, "
            "polished marble floors reflecting the lamplight. "
            "Through arched windows, a riverside town glimmers at sunset. "
            "Political intrigue and grandeur."
        ),
    },
    {
        "id": "sarasvatichandra-gunasundari-s-abode",
        "prompt": (
            BASE_STYLE +
            "A vast moonlit forest in Gujarat — ancient banyan trees with aerial roots, "
            "a winding path disappearing into darkness, fireflies glowing among dense foliage. "
            "In the far distance, oil lamps of a small village flicker through the trees. "
            "A bullock cart rests on the road. Stars visible through canopy gaps. "
            "Atmosphere of courage, departure, and the unknown."
        ),
    },
    {
        "id": "sarasvatichandra-ratnanagari-s-rajkaran",
        "prompt": (
            BASE_STYLE +
            "A sweeping panoramic view of a mountainous princely kingdom at sunset — "
            "a grand hilltop palace with ornate jharokha balconies and domed towers "
            "overlooking a vast valley with a winding river, terraced fields, and distant hills. "
            "Golden sunset light bathes everything. Clouds gather on the horizon. "
            "Atmosphere of fading power and the weight of kingship."
        ),
    },
    {
        "id": "sarasvatichandra-sarasvatichandra",
        "prompt": (
            BASE_STYLE +
            "A sacred mountain ashram at dawn — stone hermitages nestled among pine trees, "
            "prayer flags fluttering, a winding stone staircase leading to a meditation platform. "
            "The vast landscape of India spreads below: rivers, forests, distant palace spires. "
            "Golden sunrise light breaking over the peaks. "
            "Atmosphere of spiritual awakening and panoramic vision."
        ),
    },
]

for hero in HEROES:
    png_path = f"{WEB}/{hero['id']}.png"
    webp_path = f"{WEB}/{hero['id']}.webp"
    print(f"Generating: {hero['id']}...")

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=IMAGE_MODEL,
                contents=hero["prompt"],
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
                        from PIL import Image as PILImage
                        pil_img = PILImage.open(png_path)
                        pil_img.save(webp_path, "WEBP", quality=85)
                        print(f"  Saved {pil_img.size[0]}x{pil_img.size[1]}")
                        break
                break
            else:
                print(f"  Attempt {attempt+1}: no image returned, retrying...")
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            time.sleep(2)

print("Done!")
