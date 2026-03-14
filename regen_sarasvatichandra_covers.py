"""Regenerate Sarasvatichandra covers — matching chapter image style."""

import os, json, time
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
IMAGE_MODEL = "gemini-3.1-flash-image-preview"
client = genai.Client(api_key=GEMINI_API_KEY)

WEB = "web/public/data/images/covers"

# Match exactly the image_style_prefix from config.py
BASE_STYLE = (
    "Edge-to-edge illustration filling the entire frame. "
    "No border, no frame, no margin. "
    "A bright, colorful, vibrant book cover illustration. "
    "Style: late 19th-century Indian miniature painting blended with Victorian-era illustration — "
    "ornate Rajput court scenes, lush Gujarati landscapes, intricate textile patterns. "
    "Warm golden light, rich jewel tones, detailed architectural interiors of princely palaces. "
    "The SETTING and ENVIRONMENT should be the dominant visual element — "
    "architecture, landscape, interiors should fill 60-70% of the composition. "
    "Characters should be present but integrated into the scene, not dominating it. "
    "No text, no lettering, no words anywhere. "
)

COVERS = [
    {
        "id": "sarasvatichandra-buddhidhan-s-administration",
        "prompt": (
            BASE_STYLE +
            "A grand ornate darbar hall of the princely state of Suvarnapur — "
            "carved sandstone pillars, painted ceilings with floral motifs, "
            "silk curtains in gold and crimson, oil lamps casting warm light. "
            "In the middle distance, a young man in elegant white clothing walks through the hall, "
            "small against the grand architecture. "
            "Through arched windows, a riverside town glows at sunset. "
            "A mood of political intrigue and grandeur."
        ),
    },
    {
        "id": "sarasvatichandra-gunasundari-s-abode",
        "prompt": (
            BASE_STYLE +
            "A moonlit forest path winding between ancient banyan trees, "
            "dense foliage creating a canopy overhead, fireflies glowing in the darkness. "
            "In the distance, a small village with oil lamps visible through the trees. "
            "A woman in a silk sari walks the path, seen from behind at mid-distance, "
            "her figure dwarfed by the towering trees. "
            "A bullock cart waits on the road. Stars visible through gaps in the canopy. "
            "A mood of courage, departure, and the unknown."
        ),
    },
    {
        "id": "sarasvatichandra-ratnanagari-s-rajkaran",
        "prompt": (
            BASE_STYLE +
            "A sweeping view of a mountainous princely kingdom at sunset — "
            "a grand hilltop palace with ornate jharokha balconies and domed towers "
            "overlooking a vast valley with a winding river, terraced fields, and distant hills. "
            "On a palace balcony in the lower third, a king in royal robes looks out "
            "over his kingdom, small against the panoramic landscape. "
            "Golden sunset light bathes everything. Clouds gather on the horizon. "
            "A mood of fading power and the weight of kingship."
        ),
    },
    {
        "id": "sarasvatichandra-sarasvatichandra",
        "prompt": (
            BASE_STYLE +
            "A sacred mountain ashram at dawn — stone hermitages nestled among pine trees, "
            "prayer flags fluttering, a winding stone staircase leading up to a meditation platform. "
            "The vast landscape of India spreads below: rivers, forests, distant palace spires of a kingdom. "
            "A figure in saffron robes sits in meditation on the platform, "
            "seen from a distance, part of the landscape rather than dominating it. "
            "Golden sunrise light breaking over the peaks. "
            "A mood of spiritual awakening and panoramic vision."
        ),
    },
    {
        "id": "sarasvatichandra",
        "prompt": (
            BASE_STYLE +
            "A sweeping panoramic view of princely Gujarat — "
            "an ornate palace terrace in the foreground with carved pillars and flowering vines, "
            "overlooking a vast landscape: a riverside town, pleasure gardens with fountains, "
            "forested hills, and distant mountains where an ashram sits. "
            "Two small figures — a man in white and a woman in gold — stand at the terrace railing, "
            "looking out at the world together. "
            "Golden hour light, the entire landscape bathed in warm tones. "
            "A mood of epic romance spanning kingdoms and destinies."
        ),
    },
]

for cover in COVERS:
    png_path = f"{WEB}/{cover['id']}.png"
    webp_path = f"{WEB}/{cover['id']}.webp"
    print(f"Generating: {cover['id']}...")

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=IMAGE_MODEL,
                contents=cover["prompt"],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                    image_config=types.ImageConfig(aspect_ratio="3:4"),
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
