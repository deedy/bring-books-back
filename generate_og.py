"""Generate an OG image (1200x630) for Grand Old Books social sharing."""
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

PROMPT = (
    "Create a wide banner image (1200x630 pixels, 1.9:1 aspect ratio) for 'Grand Old Books' — "
    "a website that revives forgotten literary classics from India using AI. "
    "Show a warm, inviting composition: a few elegant antique books with golden spines "
    "arranged on a dark surface, with subtle warm light illuminating them. "
    "Include the text 'Grand Old Books' in an elegant serif font, centered. "
    "Below it in smaller text: 'Reviving forgotten literary treasures with AI'. "
    "Color palette: warm golds, deep charcoal (#0a0a0a) background, cream accents. "
    "Modern, premium feel. Clean and readable at small sizes."
)

print("Generating OG image...", end=" ", flush=True)
response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=PROMPT,
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
    ),
)
if response.parts:
    for part in response.parts:
        if part.inline_data is not None:
            img = part.as_image()
            path = "web/public/og.png"
            img.save(path)
            print(f"OK -> {path}")
            break
    else:
        print("No image in response")
else:
    print("BLOCKED")
