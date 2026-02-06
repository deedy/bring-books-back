"""
Generate chapter header images for 'The Twenty-Second Century'
using Gemini's image generation.

Consistent aesthetic: vintage Indian woodblock print,
monochromatic warm sepia with single deep saffron accent.
"""

import os
import json
import time
from google import genai
from google.genai import types

from dotenv import load_dotenv
load_dotenv()

API_KEY = os.environ["GEMINI_API_KEY"]
OUTPUT_DIR = "chapter_images"
CHECKPOINT_FILE = "data/chapter_images_checkpoint.json"
MODEL = "gemini-3-pro-image-preview"

client = genai.Client(api_key=API_KEY)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Consistent style prefix applied to every prompt
STYLE_PREFIX = (
    "Generate an image in the style of a vintage Indian woodblock print. "
    "Monochromatic warm sepia and brown tones with fine crosshatch engraving lines. "
    "A single accent color of deep saffron orange used sparingly for emphasis. "
    "The composition should feel like a classic book illustration — detailed, "
    "contemplative, with strong chiaroscuro. No text, no lettering, no words "
    "anywhere in the image. Portrait orientation.\n\nScene: "
)

CHAPTER_PROMPTS = {
    "1": (
        "An elderly bearded Indian sage in simple robes sits at the mouth of a "
        "mountain cave high in the Himalayas, gazing out at a vast transformed "
        "landscape below — towering unfamiliar trees, a distant receded river, "
        "waterfalls. He is waking from a centuries-long sleep. The mood is wonder "
        "and disorientation. Dawn light filters through the cave entrance."
    ),
    "2": (
        "A lush terraced orchard on a Himalayan mountainside — enormous apple "
        "and orange trees heavy with impossibly large, perfect fruit. Neat irrigation "
        "channels and copper pipes wind through the grove. In the distance, workers "
        "in clean simple clothing pick fruit into baskets. The old sage walks among "
        "them in leaf-clothes, a stranger from another time."
    ),
    "3": (
        "A panoramic vista of a futuristic yet pastoral Indian landscape — "
        "gleaming low buildings nestled among trees, electric wires strung between "
        "mountains, clean wide paths. A group of well-dressed men and women of "
        "different backgrounds sit in a circle on a veranda, engaged in animated "
        "discussion. Books and scrolls are visible. The mood is intellectual vitality."
    ),
    "4": (
        "The grand facade of a reimagined Nalanda University — a magnificent "
        "campus with classical Indian architectural elements blended with clean "
        "modern lines. Students of all ages walk through columned walkways. "
        "A vast library building rises in the background. Gardens and fountains "
        "surround the structures. The mood is reverence for knowledge."
    ),
    "5": (
        "A split composition: the left half shows the squalor and inequality of "
        "early 20th century India — cramped streets, barefoot workers, smoke — "
        "while the right half shows the clean, egalitarian future — open spaces, "
        "healthy people in simple dignified clothing, trees. A thin vertical line "
        "of saffron divides the two worlds. The mood is contrast and reflection."
    ),
    "6": (
        "A prosperous Indian village of the future — clean communal houses with "
        "gardens, shared dining halls, children playing in open spaces. A man and "
        "woman work side by side tending a vegetable garden. The village is surrounded "
        "by orchards and connected by smooth paths. Copper pipes bring water. "
        "The mood is community and contentment."
    ),
    "7": (
        "A sunlit nursery and children's garden — young children of diverse "
        "backgrounds play together, some singing, some examining plants and insects "
        "with magnifying lenses. A gentle teacher sits among them. Toys and "
        "educational objects are scattered on soft ground. Flowering vines frame "
        "the scene. The mood is innocence and discovery."
    ),
    "8": (
        "A sleek electric train races along tracks through dramatic Himalayan "
        "foothills — dense sal and teak forests on both sides, terraced orchards "
        "climbing the hills, tunnels carved through mountains. Inside a window, "
        "passengers read and converse. The landscape blurs with speed. "
        "The mood is progress and movement through nature."
    ),
    "9": (
        "A ceremonial welcome at the gates of Nalanda — garlands of flowers, "
        "crowds of scholars in simple white clothing, the ancient university "
        "buildings restored to glory in the background. The old sage, now in "
        "clean robes, receives a flower garland. Lamps and banners line the path. "
        "The mood is celebration and homecoming."
    ),
    "10": (
        "Tiny children in a bright classroom without walls — open to nature. "
        "They sit in a circle on the ground, some building with blocks, others "
        "listening to a story. A teacher demonstrates something with her hands. "
        "Birds and butterflies pass through. The floor transitions seamlessly "
        "into a garden. The mood is gentle learning."
    ),
    "11": (
        "Older children (around 10-12) in an open-air workshop — some are "
        "examining botanical specimens, others peer through telescopes or "
        "work with mechanical models. Maps and globes are visible. A child "
        "debates animatedly with a teacher. The setting blends workshop, "
        "laboratory, and garden. The mood is curiosity and empowerment."
    ),
    "12": (
        "Young adults in a sophisticated university setting — a grand amphitheater "
        "where a lecturer demonstrates a scientific apparatus. Students take notes "
        "on tablets. Through arched windows, a botanical garden and observatory "
        "dome are visible. Chemical apparatus and astronomical instruments line "
        "the walls. The mood is intellectual ambition."
    ),
    "13": (
        "A democratic assembly in session — representatives from across India "
        "sit in concentric semicircles in an open-air parliament pavilion. "
        "A speaker stands at the center. The architecture combines classical "
        "Indian pillars with clean modernist lines. Sunlight streams through. "
        "No guards, no ornate thrones — just equals deliberating. "
        "The mood is governance through reason."
    ),
    "14": (
        "A farewell scene at a train station — the sage stands by a modern "
        "locomotive, looking back at Nalanda's spires in the distance. "
        "Friends wave from the platform. Mango orchards line the tracks ahead. "
        "The sun is setting, casting long warm shadows. Luggage and flower "
        "garlands rest on the platform. The mood is bittersweet departure."
    ),
    "15": (
        "A bird's-eye view of the Indian subcontinent reimagined — interconnected "
        "villages and cities linked by rail lines and roads, each settlement "
        "surrounded by forests and orchards. Rivers flow clean. Small democratic "
        "assemblies are visible in each village. The whole forms a network, "
        "like a living organism. The mood is unity in diversity."
    ),
    "16": (
        "A symbolic still-life composition — objects from the old world (coins, "
        "weapons, prison chains, ornate crowns, religious idols) lie discarded "
        "and crumbling on the left. On the right, simple objects of the new world "
        "(books, farming tools, a compass, a telescope, a child's toy) glow with "
        "warm light. Vines grow over the old objects. The mood is quiet triumph."
    ),
}


def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE) as f:
            return json.load(f)
    return {"completed": []}


def save_checkpoint(state):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(state, f)


def generate_image(chapter_num, prompt_text):
    full_prompt = STYLE_PREFIX + prompt_text
    response = client.models.generate_content(
        model=MODEL,
        contents=full_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )

    for part in response.parts:
        if part.inline_data is not None:
            img = part.as_image()
            path = os.path.join(OUTPUT_DIR, f"chapter_{chapter_num}.png")
            img.save(path)
            return path
    raise RuntimeError("No image returned by API")


def main():
    state = load_checkpoint()
    total = len(CHAPTER_PROMPTS)
    done = 0

    for ch_num in sorted(CHAPTER_PROMPTS.keys(), key=int):
        if ch_num in state["completed"]:
            print(f"Chapter {ch_num}/{total}: cached, skipping")
            done += 1
            continue

        print(f"Chapter {ch_num}/{total}: generating...", end=" ", flush=True)
        try:
            path = generate_image(ch_num, CHAPTER_PROMPTS[ch_num])
            state["completed"].append(ch_num)
            save_checkpoint(state)
            print(f"OK -> {path}")
            done += 1
        except Exception as e:
            save_checkpoint(state)
            print(f"\n*** STOPPED at chapter {ch_num}: {e}")
            print("*** Checkpoint saved. Re-run to resume.")
            break

        time.sleep(1)  # rate limit courtesy

    print(f"\nGenerated {done}/{total} chapter images in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
