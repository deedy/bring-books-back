"""
Generate chapter header images for 'Mrinalini' by Bankim Chandra Chattopadhyay
using Gemini's image generation.

Consistent aesthetic: vintage Bengali miniature painting style,
monochromatic warm sepia with single deep vermilion accent.
"""

import os
import json
import time
from google import genai
from google.genai import types

from dotenv import load_dotenv
load_dotenv()

API_KEY = os.environ["GEMINI_API_KEY"]
OUTPUT_DIR = "mrinalini_images"
CHECKPOINT_FILE = "data/mrinalini_images_checkpoint.json"
MODEL = "gemini-3-pro-image-preview"

client = genai.Client(api_key=API_KEY)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Consistent style prefix applied to every prompt
STYLE_PREFIX = (
    "Generate an image in the style of a vintage Bengali miniature painting "
    "from the 19th century. Monochromatic warm sepia and brown tones with fine "
    "crosshatch engraving lines, like a classic book illustration. "
    "A single accent color of deep vermilion red used sparingly for emphasis. "
    "The composition should feel like a woodblock print from a 19th century "
    "Bengali literary journal — detailed, contemplative, with strong chiaroscuro. "
    "No text, no lettering, no words anywhere in the image. Portrait orientation. "
    "13th century Bengal setting with Hindu and Muslim architectural elements.\n\nScene: "
)

# Key character descriptions for consistency
HEMCHANDRA = "a young handsome Hindu warrior prince with turban, armor, bow and quiver"
MRINALINI = "a beautiful young Bengali woman in a white sari with delicate features"
MADHAVACHARYA = "a tall elderly Brahmin sage with white beard, lean body, sacred ash on forehead"
MANORAMA = "a graceful mature woman with serene, goddess-like beauty in white garments"
PASHUPATI = "a powerful 35-year-old Brahmin minister with intelligent, ambitious eyes"
GIRIJAYA = "a dark-skinned 16-year-old beggar girl with wild hair and bright eyes"

CHAPTER_PROMPTS = {
    # COVER
    "cover": (
        f"A sweeping panoramic composition showing 13th century Bengal — "
        f"the sacred Ganges flowing through ancient Navadwip with Hindu temples "
        f"and palm trees. In the foreground, {HEMCHANDRA} and {MRINALINI} "
        f"stand facing each other across a moonlit lake. In the background, "
        f"distant smoke rises from a burning city. The mood is epic romance "
        f"against the backdrop of historical upheaval. Dramatic twilight sky."
    ),
    # VOLUME ONE
    "1_1": (
        f"At the sacred confluence of Prayag where the Ganga and Yamuna meet, "
        f"monsoon evening. {HEMCHANDRA} steps ashore from a small boat and "
        f"approaches a hermitage. Inside a small hut, {MADHAVACHARYA} sits on "
        f"sacred grass in prayer. Swollen rivers and golden clouds in the western sky."
    ),
    "1_2": (
        f"Two young women in an intimate chamber — {MRINALINI} and her friend "
        f"Manimalini paint designs on walls. Mrinalini is melancholic, like "
        f"a caged bird. Soft lamplight, artistic implements scattered around. "
        f"The mood is feminine domesticity tinged with longing."
    ),
    "1_3": (
        f"{GIRIJAYA} enters a wealthy household singing devotional songs about "
        f"Krishna. She carries a bundle and has wildflowers in her hair. "
        f"{MRINALINI} listens, enchanted. The contrast between the beggar girl's "
        f"freedom and the noble woman's confinement. Musical, spiritual mood."
    ),
    "1_4": (
        f"{HEMCHANDRA} sits beneath a flowering Ashoka tree in a merchant's "
        f"courtyard, cutting flower branches. He meets {GIRIJAYA} who brings "
        f"a message. Dappled afternoon light, urban marketplace in the background. "
        f"The mood is melancholic anticipation and longing."
    ),
    "1_5": (
        f"Two women friends meet by the wall of a garden at evening. "
        f"{MRINALINI} holds a letter while {GIRIJAYA} holds an oil lamp. "
        f"They read the letter together by warm lamplight. Moonlight illuminates "
        f"the stone wall behind them. The mood is anticipation and hope."
    ),
    "1_6": (
        f"An elderly Brahmin householder confronts {MRINALINI} in her bedchamber, "
        f"pointing accusingly. She stands with bowed head. Her friend Manimalini "
        f"weeps in the corner. Dramatic rejection scene — emotional turmoil. "
        f"Interior with overturned furniture suggesting confrontation."
    ),
    # PART TWO
    "2_1": (
        f"A grand royal court of 13th century Bengal — an aged king sits on "
        f"a jeweled throne beneath a ceremonial canopy. Brahmins and courtiers "
        f"are seated in rows. {MADHAVACHARYA} stands before the king, speaking "
        f"urgently. Majestic palace interior with pillars and hanging lamps."
    ),
    "2_2": (
        f"{HEMCHANDRA} meets {MANORAMA} for the first time in a garden house. "
        f"An elderly deaf Brahmin sits nearby. Manorama is ethereally beautiful, "
        f"surrounded by flowering plants. Delicate, innocent encounter. "
        f"Soft light filtering through garden foliage."
    ),
    "2_3": (
        f"{MRINALINI} and {GIRIJAYA} sit in a small dinghy on the Ganges at "
        f"twilight. The evening sky transitions from crimson to dusky purple. "
        f"River waves and foam surround the boat. Two women adrift — "
        f"melancholic, contemplative mood. Vast water and vast sky."
    ),
    "2_4": (
        f"{HEMCHANDRA} lies on a couch gazing out an open window at the moonlit "
        f"Ganges. Suddenly a turbaned face appears at the window — shock and "
        f"suspicion. Moonlit bedroom interior with river view beyond. "
        f"The mood is peaceful rest shattered by danger."
    ),
    "2_5": (
        f"Nighttime scene by a sacred tank surrounded by dark trees. {HEMCHANDRA} "
        f"discovers {MANORAMA} sitting alone by the water's edge in white. "
        f"Mysterious, supernatural atmosphere. Her reflection shimmers in "
        f"the dark pool. The mood is enchantment and wonder."
    ),
    "2_6": (
        f"{PASHUPATI} sits alone in a lamplit chamber in a grand mansion, "
        f"deep in thought. Maps and scrolls surround him. His face shows "
        f"intelligence and ambition. Opulent interior with carved pillars "
        f"and heavy curtains. The mood is scheming solitude."
    ),
    "2_7": (
        f"{PASHUPATI} meets a spy in a dark corridor at night. The spy whispers "
        f"intelligence about Turkish army movements. Flickering torchlight "
        f"casts dramatic shadows. The mood is clandestine political intrigue. "
        f"Both figures are partially obscured by shadow."
    ),
    "2_8": (
        f"{MANORAMA} appears at the doorway of a goddess temple, illuminated by "
        f"jeweled oil lamps. Her extraordinary beauty seems divine, goddess-like. "
        f"{PASHUPATI} gazes at her from the shadows, mesmerized. Temple interior "
        f"with sacred images and flower offerings."
    ),
    "2_9": (
        f"{PASHUPATI} gazes at {MANORAMA} in the temple with insatiable eyes. "
        f"She has a mature, goddess-like expression contrasting with delicate form. "
        f"The sacred fire burns between them. Internal spiritual conflict "
        f"expressed through visual tension. Incense smoke drifts upward."
    ),
    "2_10": (
        f"{HEMCHANDRA} crouches behind a large tree near {PASHUPATI}'s mansion. "
        f"{MANORAMA} gestures for him to follow. A thief-catcher lurks with "
        f"chains near a doorway. Nighttime stealth and deception — tense, dark "
        f"scene with moonlight and shadows around grand architecture."
    ),
    "2_11": (
        f"{MANORAMA} unlocks a heavy wooden door of a picture gallery where "
        f"{HEMCHANDRA} is imprisoned. She holds a key and a lamp, guiding him "
        f"through dark corridors. Tense, secretive escape by moonlight. "
        f"Long shadows, stone walls, sense of urgency."
    ),
    "2_12": (
        f"{HEMCHANDRA} on horseback galloping across open plains, blood on his "
        f"shoulder from an arrow wound. Three horsemen pursue him with bows drawn. "
        f"Dust rises from the horses' hooves. Dawn light breaks on the horizon. "
        f"Dynamic, violent action scene of fleeing warrior."
    ),
    # PART THREE
    "3_1": (
        f"Dawn at a boatman's cottage by the river. {MRINALINI} and {GIRIJAYA} "
        f"discover {HEMCHANDRA} sleeping beneath a great banyan tree, his body "
        f"covered in blood and wounds. Surprise recognition on their faces. "
        f"Humble rural setting with thatched roof and fishing nets."
    ),
    "3_2": (
        f"{MANORAMA} tends to {HEMCHANDRA}'s wounds, washing blood from his body "
        f"and applying herbal medicine. {MRINALINI} watches from behind a curtain, "
        f"her face showing jealousy and pain. Intimate interior scene. "
        f"Bandages, water basin, medicinal herbs."
    ),
    "3_3": (
        f"{GIRIJAYA} sits beneath an open window, her head tilted, listening to "
        f"voices inside. Through the window, she sees {HEMCHANDRA} and {MANORAMA} "
        f"together. Her expression is anxious and worried. Garden flowers "
        f"frame the window. The mood is surveillance and dread."
    ),
    "3_4": (
        f"{GIRIJAYA} sits outside at dusk, singing a plaintive devotional song. "
        f"{HEMCHANDRA} emerges from the house, drawn by her voice. Oil lamps "
        f"flicker in the breeze. The mood is musical melancholy. "
        f"Stars beginning to appear in the evening sky."
    ),
    "3_5": (
        f"{MADHAVACHARYA} arrives at the house and sits with {HEMCHANDRA} in "
        f"earnest counsel. The guru's face is grave. They discuss war preparations. "
        f"Simple hermitage interior with scrolls and sacred items. "
        f"The mood is duty and spiritual guidance."
    ),
    "3_6": (
        f"{MANORAMA} and {HEMCHANDRA} sit across from each other in a chamber. "
        f"She is solemn and philosophical, he is conflicted. Between them, "
        f"a single flame burns steadily. The mood is deep emotional reckoning. "
        f"Shadows play on their faces."
    ),
    "3_7": (
        f"{GIRIJAYA} returns to {MRINALINI} with devastating news. Mrinalini "
        f"sits by a window, turning her face away in heartbreak. Girijaya "
        f"kneels beside her. Evening light fades. The mood is betrayal and "
        f"sorrow. Wilting flowers in a vase nearby."
    ),
    "3_8": (
        f"A young woman ({MRINALINI}) sits at a wooden writing desk by warm "
        f"lamplight, composing a letter with a quill pen. An ink pot and "
        f"rolled parchment are visible on the desk. Her friend stands nearby "
        f"ready to deliver the letter. The mood is thoughtful correspondence. "
        f"Evening light through a window."
    ),
    "3_9": (
        f"{HEMCHANDRA} lies alone on a bed, face buried in a pillow, weeping. "
        f"A crumpled letter lies on the floor beside him. Moonlight streams "
        f"through the window. A warrior brought low by emotional torment. "
        f"The mood is vulnerability and inner conflict."
    ),
    "3_10": (
        f"{MRINALINI} and {HEMCHANDRA} stand face to face by a moonlit lake "
        f"surrounded by trees. They embrace after long separation. Ripples "
        f"spread across the silvery water. Fireflies dot the darkness. "
        f"The mood is magical reunion and romantic fulfillment."
    ),
    # PART FOUR
    "4_1": (
        f"{PASHUPATI} sits in midnight darkness, a single candle illuminating "
        f"his stern face. His thief-catcher Shantashil kneels before him. "
        f"Political plotting in shadows. Palace chamber with heavy darkness. "
        f"The mood is menace and calculation."
    ),
    "4_2": (
        f"{MANORAMA} sits inside a goddess temple, stringing a garland of flowers. "
        f"She creates a necklace from her own hair — symbol of devotion and sacrifice. "
        f"Sacred idol in the background. Soft lamplight and flower petals "
        f"scattered on the stone floor."
    ),
    "4_3": (
        f"{PASHUPATI} confronts {MANORAMA} in the temple. She reveals herself as "
        f"his long-lost wife. His face shows shock. The temple door slams shut. "
        f"Dramatic revelation — locked doors, flickering lamps, emotional "
        f"confrontation between husband and wife."
    ),
    "4_4": (
        f"Seventeen Turkish horsemen on magnificent steeds ride down the royal "
        f"road of Navadwip. They wear turbans and carry curved swords and spears. "
        f"Palace gates loom ahead. Citizens watch in fear. The mood is conquest "
        f"and imperial menace. Dust clouds, military banners."
    ),
    "4_5": (
        f"{PASHUPATI} faces Bakhtiyar Khilji — a fierce Turkish general — in "
        f"the palace hall. The Yavana demands submission. Pashupati stands "
        f"defiant. Guards line the walls. The mood is tense negotiation and "
        f"the clash of civilizations. Power and oppression."
    ),
    "4_6": (
        f"{MANORAMA} climbs out of a high window using the branches of a mango tree. "
        f"Her sari catches on branches as she leaps to freedom. Nighttime escape — "
        f"moonlight, desperate brave action. The mansion walls tower behind her. "
        f"The mood is daring feminine courage."
    ),
    "4_7": (
        f"Turkish army invades Navadwip at night — chaos everywhere. Burning "
        f"houses light the sky orange. Bodies lie in the streets. Soldiers with "
        f"torches and swords. Civilians flee. The mood is apocalyptic destruction. "
        f"A great Hindu temple burns in the background."
    ),
    "4_8": (
        f"{MRINALINI} and {GIRIJAYA} sit by a tranquil lakeside at dawn. "
        f"Mrinalini stares blankly at the water, unresponsive, traumatized. "
        f"Girijaya watches over her protectively. Lotus flowers float on "
        f"the water. The mood is profound grief and gentle companionship."
    ),
    "4_9": (
        f"{MRINALINI} lies asleep, dreaming — shown through translucent vision "
        f"above her of {HEMCHANDRA} riding victorious on a white horse, sword "
        f"raised. She awakens to find him actually standing before her. "
        f"The dream dissolving into reality. Mystical, hopeful mood."
    ),
    "4_10": (
        f"{HEMCHANDRA} and {MRINALINI} embrace in a moonlit garden pavilion. "
        f"Tears of joy on their faces. In the background, {GIRIJAYA} and "
        f"a man (Digvijay) watch with smiles. Flowering vines wrap the pillars. "
        f"The mood is joyous romantic reunion."
    ),
    "4_11": (
        f"{MRINALINI} and {GIRIJAYA} sit together in a domestic interior. "
        f"Mrinalini narrates her past — visualized as a ghostly scene behind "
        f"them of a young woman drowning in a river during a storm, rescued "
        f"by a prince on horseback. Storytelling and memory."
    ),
    "4_12": (
        f"{HEMCHANDRA} kneels before {MADHAVACHARYA} who places a hand on "
        f"his head in blessing. The guru's face shows warmth and approval. "
        f"A sacred fire burns between them. The mood is spiritual communion, "
        f"blessing, and acceptance. Simple hermitage setting."
    ),
    "4_13": (
        f"A nighttime scene at a massive stone gate — the Lion Gate. A Muslim "
        f"guard (Muhammad Ali) secretly unlocks the gate to free {PASHUPATI}. "
        f"Moonlight on stone. The mood is redemption and unlikely mercy. "
        f"Heavy iron chains and keys."
    ),
    "4_14": (
        f"{PASHUPATI} walks through a devastated city — corpses and blood on "
        f"the streets, burning buildings. He sees his own mansion ablaze. "
        f"In despair, he runs into the burning temple to embrace the goddess idol. "
        f"Apocalyptic inferno, tragic heroism. Flames consuming everything."
    ),
    "4_15": (
        f"A funeral pyre burns by the sacred Ganges at dawn. {MANORAMA}, "
        f"disheveled but serene-faced, walks toward the flames. Brahmins chant "
        f"nearby. The river flows peacefully beyond. The mood is tragic dignity "
        f"and sacrifice. Sacred fire and sacred water together."
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


def generate_image(key, prompt_text, retries=3):
    full_prompt = STYLE_PREFIX + prompt_text
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=MODEL,
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
                raise RuntimeError("No parts returned by API after retries")

            for part in response.parts:
                if part.inline_data is not None:
                    img = part.as_image()
                    path = os.path.join(OUTPUT_DIR, f"{key}.png")
                    img.save(path)
                    return path

            if attempt < retries - 1:
                print(f"(no image, retry {attempt+1})...", end=" ", flush=True)
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
            raise RuntimeError(f"API error after retries: {e}")


def main():
    state = load_checkpoint()
    total = len(CHAPTER_PROMPTS)
    done = 0

    # Process in order: cover first, then chapters
    keys = ["cover"] + [k for k in CHAPTER_PROMPTS if k != "cover"]
    keys = sorted(keys, key=lambda k: (0 if k == "cover" else 1, k))

    for key in keys:
        if key in state["completed"]:
            print(f"  {key}: cached, skipping")
            done += 1
            continue

        print(f"  {key} ({done+1}/{total}): generating...", end=" ", flush=True)
        try:
            path = generate_image(key, CHAPTER_PROMPTS[key])
            state["completed"].append(key)
            save_checkpoint(state)
            print(f"OK -> {path}")
            done += 1
        except Exception as e:
            save_checkpoint(state)
            print(f"\n*** STOPPED at {key}: {e}")
            print("*** Checkpoint saved. Re-run to resume.")
            break

        time.sleep(1)  # rate limit courtesy

    print(f"\nGenerated {done}/{total} images in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
