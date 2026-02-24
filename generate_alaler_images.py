"""
Generate chapter header images for 'Alaler Gharer Dulal' (The Spoilt Child)
by Peary Chand Mitra using Gemini's image generation.

Consistent aesthetic: vintage Bengali woodblock print from mid-19th century,
warm sepia and ochre tones with deep indigo accent.
"""

import os
import json
import time
from google import genai
from google.genai import types

from dotenv import load_dotenv
load_dotenv()

API_KEY = os.environ["GEMINI_API_KEY"]
OUTPUT_DIR = "alaler_images"
CHECKPOINT_FILE = "data/alaler_images_checkpoint.json"
MODEL = "gemini-3-pro-image-preview"

client = genai.Client(api_key=API_KEY)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Consistent style prefix applied to every prompt
STYLE_PREFIX = (
    "Generate an image in the style of a vintage Bengali woodblock print "
    "from the mid-19th century. Warm sepia and ochre tones with fine "
    "crosshatch engraving lines, like illustrations from an 1850s Calcutta "
    "literary journal. A single accent color of deep indigo blue used sparingly. "
    "The composition should feel like a period illustration — detailed domestic "
    "scenes of colonial-era Bengali life, with strong chiaroscuro. "
    "No text, no lettering, no words anywhere in the image. "
    "1850s colonial Calcutta setting.\n\nScene: "
)

# Key character descriptions
BABURAM = "a wealthy, stout Bengali gentleman in his 50s with a turban and fine dhoti"
MOTILAL = "a handsome but dissolute young Bengali man in his 20s, spoiled and reckless"
BENI = "a thin, wise Bengali gentleman with spectacles and a shawl"
BECHARAM = "a good-natured, rotund Bengali gentleman, a loyal friend"
THAKCHACHA = "a cunning, sly older man with shifty eyes, always scheming"
BORDA = "a dignified, elderly Bengali gentleman of great integrity and simplicity"
MOTHER = "a gentle, sorrowful Bengali woman in a white sari, Motilal's long-suffering mother"

CHAPTER_PROMPTS = {
    # COVER
    "cover": (
        f"A sweeping composition showing 1850s colonial Calcutta — "
        f"a grand Bengali mansion (rajbari) with ornate columns and courtyards. "
        f"In the foreground, {MOTILAL} lounges on a divan surrounded by hookah "
        f"pipes and scattered coins, while servants attend him. "
        f"Through a window, the bustling Calcutta streets are visible with "
        f"horse carriages and markets. The mood is opulent decadence. "
        f"Dramatic lighting from oil lamps."
    ),
    # Chapter 1: Introduction to Baburam Babu
    "chapter_1": (
        f"Interior of a grand Bengali household in 1850s Calcutta. "
        f"{BABURAM} sits on a bolster in his drawing room, smoking a hookah. "
        f"A young boy (Motilal as a child) plays at his feet. "
        f"The room has ornate furniture, hanging oil lamps, and a courtyard "
        f"visible through arched doorways. Domestic prosperity."
    ),
    # Chapter 2: The Spoilt Child
    "chapter_2": (
        f"A young boy (Motilal as a child) throwing a tantrum in a Bengali "
        f"household. Servants rush to pacify him with sweets and toys. "
        f"His doting father watches indulgently from a doorway. "
        f"Scattered toys and broken objects on the floor. "
        f"The mood is comic indulgence and spoiling."
    ),
    # Chapter 3: Motilal arrives in Bali
    "chapter_3": (
        f"A young man ({MOTILAL}) stepping off a boat at a river ghat "
        f"in rural Bengal. Behind him, a small town with thatched roofs "
        f"and palm trees. Other passengers carry bundles. "
        f"The mood is a new arrival in the countryside."
    ),
    # Chapter 4: English Education in Calcutta
    "chapter_4": (
        f"A classroom scene in 1850s Calcutta. Young Bengali students sit "
        f"on wooden benches before an English schoolmaster. Slates, books, "
        f"and writing implements are scattered about. Through the window, "
        f"Calcutta rooftops are visible. The mood is colonial education."
    ),
    # Chapter 5: Baburam sends a messenger
    "chapter_5": (
        f"Early dawn in 1850s Calcutta. A messenger walks through narrow "
        f"lanes past shuttered shops and sleeping dogs. In the background, "
        f"the first light illuminates minarets and temple spires. "
        f"Oil lamps still flicker in windows. The mood is a city awakening."
    ),
    # Chapter 6: Mother's worries, conversation between sisters
    "chapter_6": (
        f"Two Bengali women sit in an inner courtyard of a traditional house. "
        f"{MOTHER} looks worried, hands clasped. Her sister consoles her. "
        f"Drying clothes hang on a line, cooking pots are visible nearby. "
        f"Soft afternoon light. The mood is domestic anxiety and sisterly bond."
    ),
    # Chapter 7: Early history of Calcutta, police
    "chapter_7": (
        f"A busy street scene in colonial Calcutta. A British magistrate's "
        f"court building with columns stands at the center. Bengali men in "
        f"dhotis and English-educated babus in coats mill about. "
        f"A police constable in uniform stands guard. Horse carriages pass. "
        f"The mood is bustling colonial administration."
    ),
    # Chapter 8: The lawyer's office
    "chapter_8": (
        f"Interior of a British lawyer's office in 1850s Calcutta. "
        f"A sahib sits behind a large desk piled with legal papers. "
        f"Bengali clerks work at side desks. Heavy curtains, a ceiling fan "
        f"worked by a punkah-wallah. The mood is colonial legal bureaucracy."
    ),
    # Chapter 9: Motilal's decline, becomes a full babu
    "chapter_9": (
        f"{MOTILAL} in extravagant attire, surrounded by a rowdy group of "
        f"young men. They drink and smoke hookah in a garden pavilion. "
        f"Musicians play in the background. Scattered bottles and playing "
        f"cards. The mood is youthful dissipation and revelry."
    ),
    # Chapter 10: The market at Baidyabati
    "chapter_10": (
        f"A bustling village market (haat) at Baidyabati. Vendors sell fish, "
        f"vegetables, and rice from woven baskets. Oil lamps illuminate "
        f"the evening scene. Women shop while children play. "
        f"A river is visible in the background. The mood is vibrant village life."
    ),
    # Chapter 11: Motilal's wedding, poetry
    "chapter_11": (
        f"A traditional Bengali wedding scene. A bride and groom sit under "
        f"a decorated canopy (mandap) with a sacred fire between them. "
        f"Brahmins chant while musicians play shehnai. Guests in fine "
        f"clothes watch. Garlands of marigolds. The mood is festive celebration."
    ),
    # Chapter 12: Benibabu visits Becharam
    "chapter_12": (
        f"{BENI} and {BECHARAM} sit facing each other on a verandah, "
        f"deep in conversation. Tea and sweets are laid out between them. "
        f"A garden with potted plants surrounds the verandah. "
        f"Evening light. The mood is thoughtful friendship."
    ),
    # Chapter 13: Bardaprasad's advice and wisdom
    "chapter_13": (
        f"{BORDA} sits in a simple room, speaking earnestly to a young man "
        f"(Ramlal). Sacred texts and an oil lamp are on a low table. "
        f"The elder's face shows kindness and gravity. "
        f"The mood is moral instruction and spiritual guidance."
    ),
    # Chapter 14: Motilal's gang pranks a Kaviraj
    "chapter_14": (
        f"A group of young Bengali men surround an elderly Kaviraj (ayurvedic "
        f"doctor) on a village road, playing a prank on him. The Kaviraj "
        f"looks bewildered, his medicine bag upset. The young men laugh. "
        f"Rural Bengal setting with trees and a pond. Comic mischief."
    ),
    # Chapter 15: Hooghly Magistrate's court
    "chapter_15": (
        f"Interior of a colonial magistrate's court in Hooghly. A British "
        f"judge sits elevated. Bengali lawyers argue before him. "
        f"Accused men stand in the dock. Clerks scribble notes. "
        f"The room has high ceilings and heavy wooden furniture. "
        f"The mood is tense legal proceedings."
    ),
    # Chapter 16: Thakchacha's house
    "chapter_16": (
        f"{THAKCHACHA} and his wife sit in their modest but cluttered home. "
        f"He leans forward conspiratorially while she listens with folded arms. "
        f"Cooking utensils and household items crowd the space. "
        f"A single oil lamp casts dramatic shadows. Scheming atmosphere."
    ),
    # Chapter 17: The barber and his wife
    "chapter_17": (
        f"A village barber's shop in 1850s Bengal. The barber sits cross-legged "
        f"with his tools while his wife prepares betel leaves nearby. "
        f"Neighbors gather to gossip. A mirror and razors hang on the wall. "
        f"The mood is village gossip and domestic comedy."
    ),
    # Chapter 18: Motilal's gang meets old Majumdar
    "chapter_18": (
        f"A group of rowdy young men confront an elderly gentleman on a "
        f"village road at dusk. The old man holds a walking stick, standing "
        f"his ground with dignity. The young men look belligerent. "
        f"Village houses and a banyan tree in the background."
    ),
    # Chapter 19: Becharam visits Beni, Baburam's illness
    "chapter_19": (
        f"A sick room scene. {BABURAM} lies on a bed, attended by family. "
        f"An ayurvedic doctor checks his pulse. Women weep softly nearby. "
        f"Medicine bottles and herbal preparations on a side table. "
        f"Oil lamps cast a warm glow. The mood is illness and family concern."
    ),
    # Chapter 20: Baburam's death, funeral rites
    "chapter_20": (
        f"A solemn funeral scene by the banks of the Ganges. A funeral pyre "
        f"burns at the ghat. Brahmins perform rituals while mourners stand "
        f"in white. The river flows quietly beyond. "
        f"Dawn light breaks over the water. The mood is grief and ritual."
    ),
    # Chapter 21: Motilal inherits, mistreats mother
    "chapter_21": (
        f"{MOTILAL} sits arrogantly on his father's seat in the grand house. "
        f"{MOTHER} stands before him with bowed head, being turned away. "
        f"A younger woman (sister) weeps behind her. "
        f"The opulent room contrasts with the women's distress. "
        f"The mood is cruelty and family dissolution."
    ),
    # Chapter 22: Motilal tries trade
    "chapter_22": (
        f"A scene at the Ganges riverbank. {MOTILAL} and his entourage board "
        f"a laden trading boat. Goods and crates are being loaded. "
        f"Boatmen pull ropes. Other boats dot the river. "
        f"The mood is commercial enterprise and departure."
    ),
    # Chapter 23: Trading venture fails
    "chapter_23": (
        f"{MOTILAL} and his companions in disarray at a trading post. "
        f"Goods are scattered, accounts in disorder. A holy man they've "
        f"insulted walks away with dignity. The young men look worried. "
        f"The mood is comic failure and just consequences."
    ),
    # Chapter 24: Thakchacha's forged warrant
    "chapter_24": (
        f"{THAKCHACHA} examines a document by candlelight with a magnifying "
        f"glass. Behind him, stacks of papers and legal documents. "
        f"His expression is calculating. Through a window, the night sky. "
        f"The mood is forgery and deception in shadows."
    ),
    # Chapter 25: Motilal goes to Jessore estate
    "chapter_25": (
        f"A procession of palanquins and bullock carts on a muddy rural road "
        f"through Bengal. {MOTILAL} rides in the lead palanquin. "
        f"Rice paddies and palm trees stretch to the horizon. "
        f"Peasants watch from the roadside. The mood is a rural journey."
    ),
    # Chapter 26: Thakchacha reveals secrets in his sleep
    "chapter_26": (
        f"{THAKCHACHA} asleep on a prison cot, talking in his sleep. "
        f"Other prisoners listen with wide eyes. A guard holds a lantern. "
        f"The lock-up is dim and cramped. The mood is comic revelation "
        f"and poetic justice."
    ),
    # Chapter 27: Badar's tenants, arrest
    "chapter_27": (
        f"A rural Bengal scene with peasant farmers being confronted by "
        f"a revenue collector. A man lies injured on the ground after being "
        f"run over by a horse carriage. Villagers gather around in alarm. "
        f"The mood is rural oppression and injustice."
    ),
    # Chapter 28: Borda Babu's honesty revealed
    "chapter_28": (
        f"{BORDA} sits humbly in a simple room while {BENI} and {BECHARAM} "
        f"listen with admiration. His threadbare but clean clothes contrast "
        f"with the others' finery. A single flower in a clay pot. "
        f"The mood is quiet virtue recognized."
    ),
    # Chapter 29: Seizing the house, family evicted
    "chapter_29": (
        f"A Bengali family being evicted from their ancestral home. "
        f"{MOTHER} and children stand outside with their belongings in "
        f"bundles. Moneylenders and officials enter the grand house. "
        f"Neighbors watch sympathetically. The mood is loss and injustice."
    ),
    # Chapter 30: Motilal's journey to Benares, redemption
    "chapter_30": (
        f"{MOTILAL}, now older and humbled, sits on the steps of a Benares "
        f"ghat at sunrise. The sacred Ganges flows before him. Temple "
        f"spires rise behind. He looks reflective and penitent. "
        f"A holy man sits nearby. The mood is spiritual awakening and redemption."
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
