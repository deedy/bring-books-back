"""Generate an epic hero banner for the Mahabharata."""
import os, io, shutil
from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai import types
from PIL import Image

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

prompt = (
    "Edge-to-edge cinematic wide landscape illustration filling the entire frame. "
    "No border, no frame, no margin, no vignette, no white space. "
    "An EPIC, dramatic cinematic panorama of THE MAHABHARATA — "
    "the greatest war epic ever told. "
    "Style: hyper-detailed classical Indian art meets modern cinematic concept art. "
    "Rich jewel tones, gold leaf accents, dramatic chiaroscuro lighting. "
    "A sweeping wide-angle view of the Kurukshetra battlefield at the golden hour of dawn. "
    "In the center-distance: Arjuna's divine chariot with Krishna as charioteer, "
    "silhouetted against a blazing golden-crimson sky. "
    "Two VAST armies stretching across the entire horizon — "
    "war elephants with golden howdahs, thousands of chariots with streaming banners, "
    "cavalry and infantry formations, dust clouds rising. "
    "Divine weapons and astras streaking across the dramatic sky "
    "painted in deep crimsons, burnt oranges, and royal purples. "
    "A glowing divine discus like a second sun in the sky. "
    "Foreground: scattered arrows, conch shells, war drums, lotus flowers in blood-red earth. "
    "The overall feel should be MONUMENTAL, SACRED, and AWE-INSPIRING — "
    "like a Peter Jackson aerial battle shot meets Rajput miniature painting. "
    "Extremely detailed, painterly, luminous, vast scale. "
    "16:9 cinematic widescreen landscape composition. "
    "No text, no lettering, no words anywhere in the image."
)

print("Generating epic hero banner...")
for attempt in range(3):
    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
                image_config=types.ImageConfig(aspect_ratio="16:9"),
            ),
        )
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    img = Image.open(io.BytesIO(part.inline_data.data))
                    img.save("web/public/data/images/heroes/mahabharata.png")
                    img.save("web/public/data/images/heroes/mahabharata.webp", "WEBP", quality=85)
                    print(f"  Saved hero banner: {img.size}")
                    break
            else:
                print(f"  Attempt {attempt+1}: no image in response")
                continue
            break
        else:
            print(f"  Attempt {attempt+1}: no candidates")
    except Exception as e:
        print(f"  Attempt {attempt+1} error: {e}")

print("Done!")
