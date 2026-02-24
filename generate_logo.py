"""Generate a modern logo for Grand Old Books using Gemini."""
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

PROMPT = (
    "Design a modern, minimal logo icon for 'Grand Old Books' — a website that "
    "revives forgotten literary classics from India using AI translation. "
    "The logo should be a clean, elegant symbol (no text/lettering) that evokes: "
    "an open book combined with a subtle vintage/antique feel. "
    "Use a warm color palette: muted gold, cream, and deep charcoal. "
    "Flat design, suitable for use as a favicon and header logo. "
    "Square aspect ratio, transparent or dark background (#0a0a0a). "
    "Modern tech-meets-literary aesthetic. Think: a premium book publisher's mark."
)

for name, size_note in [("logo", "256x256 pixels, square"), ("favicon", "64x64 pixels, tiny square icon, extremely simple")]:
    print(f"Generating {name}...", end=" ", flush=True)
    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=f"{size_note}. {PROMPT}",
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )
    if response.parts:
        for part in response.parts:
            if part.inline_data is not None:
                img = part.as_image()
                path = f"web/public/{name}.png"
                img.save(path)
                print(f"OK -> {path}")
                break
        else:
            print("No image in response")
    else:
        print("BLOCKED")

print("Done!")
