"""
Regenerate chapter images for Mrinalini and Baeesween Sadi (22nd Century)
in both A5 portrait and 16:9 landscape (web) formats.

Aggressive parallelization: 4 concurrent workers per book using ThreadPoolExecutor.
Uses Gemini image generation with book-specific style prefixes.
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

A5_RATIO = 148 / 210
LANDSCAPE_RATIO = 16 / 9

# Thread-safe checkpoint lock
checkpoint_lock = threading.Lock()


def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False)


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


def generate_image(client, output_path, style_prefix, prompt_text, orientation, retries=3):
    if orientation == "portrait":
        aspect_note = "Portrait orientation, taller than wide (A5 book page ratio). "
    else:
        aspect_note = "Wide landscape orientation (16:9 ratio, cinematic banner). "

    full_prompt = aspect_note + style_prefix + prompt_text

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
                    target = A5_RATIO if orientation == "portrait" else LANDSCAPE_RATIO
                    crop_to_ratio(output_path, target)
                    return output_path

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


def process_chapter(client, book_config, key, prompt_text, state, state_path):
    """Generate A5 + web images for one chapter."""
    output_dir = book_config["output_dir"]
    style_prefix = book_config["style_prefix"]
    a5_key = f"{key}_a5"
    web_key = f"{key}_web"

    results = []

    # A5 portrait
    if a5_key not in state["completed"]:
        a5_path = os.path.join(output_dir, f"{key}.png")
        try:
            generate_image(client, a5_path, style_prefix, prompt_text, "portrait")
            with checkpoint_lock:
                state["completed"].append(a5_key)
                save_json(state_path, state)
            results.append(f"{key} A5: OK")
        except Exception as e:
            results.append(f"{key} A5: FAILED ({e})")
        time.sleep(0.5)
    else:
        results.append(f"{key} A5: cached")

    # Landscape web
    if web_key not in state["completed"]:
        web_path = os.path.join(output_dir, f"{key}_web.png")
        try:
            generate_image(client, web_path, style_prefix, prompt_text, "landscape")
            with checkpoint_lock:
                state["completed"].append(web_key)
                save_json(state_path, state)
            results.append(f"{key} web: OK")
        except Exception as e:
            results.append(f"{key} web: FAILED ({e})")
        time.sleep(0.5)
    else:
        results.append(f"{key} web: cached")

    return results


# ═══════════════════════════════════════════════════════════════════
# MRINALINI — Bankim Chandra Chattopadhyay
# ═══════════════════════════════════════════════════════════════════

MRINALINI_STYLE = (
    "Generate an image in the style of a vintage Bengali miniature painting "
    "from the 19th century. Monochromatic warm sepia and brown tones with fine "
    "crosshatch engraving lines, like a classic book illustration. "
    "A single accent color of deep vermilion red used sparingly for emphasis. "
    "The composition should feel like a woodblock print from a 19th century "
    "Bengali literary journal — detailed, contemplative, with strong chiaroscuro. "
    "No text, no lettering, no words anywhere in the image. "
    "13th century Bengal setting with Hindu and Muslim architectural elements.\n\nScene: "
)

HEMCHANDRA = "a young handsome Hindu warrior prince with turban, armor, bow and quiver"
MRINALINI_CHAR = "a beautiful young Bengali woman in a white sari with delicate features"
MADHAVACHARYA = "a tall elderly Brahmin sage with white beard, lean body, sacred ash on forehead"
MANORAMA = "a graceful mature woman with serene, goddess-like beauty in white garments"
PASHUPATI = "a powerful 35-year-old Brahmin minister with intelligent, ambitious eyes"
GIRIJAYA = "a dark-skinned 16-year-old beggar girl with wild hair and bright eyes"

MRINALINI_PROMPTS = {
    "cover": (
        f"A sweeping panoramic composition showing 13th century Bengal — "
        f"the sacred Ganges flowing through ancient Navadwip with Hindu temples "
        f"and palm trees. In the foreground, {HEMCHANDRA} and {MRINALINI_CHAR} "
        f"stand facing each other across a moonlit lake. In the background, "
        f"distant smoke rises from a burning city. The mood is epic romance "
        f"against the backdrop of historical upheaval. Dramatic twilight sky."
    ),
    "1_1": (
        f"At the sacred confluence of Prayag where the Ganga and Yamuna meet, "
        f"monsoon evening. {HEMCHANDRA} steps ashore from a small boat and "
        f"approaches a hermitage. Inside a small hut, {MADHAVACHARYA} sits on "
        f"sacred grass in prayer. Swollen rivers and golden clouds in the western sky."
    ),
    "1_2": (
        f"Two young women in an intimate chamber — {MRINALINI_CHAR} and her friend "
        f"Manimalini paint designs on walls. Mrinalini is melancholic, like "
        f"a caged bird. Soft lamplight, artistic implements scattered around. "
        f"The mood is feminine domesticity tinged with longing."
    ),
    "1_3": (
        f"{GIRIJAYA} enters a wealthy household singing devotional songs about "
        f"Krishna. She carries a bundle and has wildflowers in her hair. "
        f"{MRINALINI_CHAR} listens, enchanted. The contrast between the beggar girl's "
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
        f"{MRINALINI_CHAR} holds a letter while {GIRIJAYA} holds an oil lamp. "
        f"They read the letter together by warm lamplight. Moonlight illuminates "
        f"the stone wall behind them. The mood is anticipation and hope."
    ),
    "1_6": (
        f"An elderly Brahmin householder confronts {MRINALINI_CHAR} in her bedchamber, "
        f"pointing accusingly. She stands with bowed head. Her friend Manimalini "
        f"weeps in the corner. Dramatic rejection scene — emotional turmoil. "
        f"Interior with overturned furniture suggesting confrontation."
    ),
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
        f"{MRINALINI_CHAR} and {GIRIJAYA} sit in a small dinghy on the Ganges at "
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
        f"{PASHUPATI} meets an informant in a dark corridor at night. The informant whispers "
        f"intelligence about Turkish army movements. Flickering torchlight "
        f"casts dramatic shadows. The mood is secret political intrigue. "
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
        f"{MANORAMA} gestures for him to follow. A guard lurks with "
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
        f"{HEMCHANDRA} on horseback galloping across open plains, wounded on his "
        f"shoulder from an arrow. Three horsemen pursue him with bows drawn. "
        f"Dust rises from the horses' hooves. Dawn light breaks on the horizon. "
        f"Dynamic action scene of fleeing warrior."
    ),
    "3_1": (
        f"Dawn at a boatman's cottage by the river. {MRINALINI_CHAR} and {GIRIJAYA} "
        f"discover {HEMCHANDRA} sleeping beneath a great banyan tree, his body "
        f"covered in wounds. Surprise recognition on their faces. "
        f"Humble rural setting with thatched roof and fishing nets."
    ),
    "3_2": (
        f"{MANORAMA} tends to {HEMCHANDRA}'s wounds, washing and "
        f"applying herbal medicine. {MRINALINI_CHAR} watches from behind a curtain, "
        f"her face showing jealousy and pain. Intimate interior scene. "
        f"Bandages, water basin, medicinal herbs."
    ),
    "3_3": (
        f"{GIRIJAYA} sits beneath an open window, her head tilted, listening to "
        f"voices inside. Through the window, she sees {HEMCHANDRA} and {MANORAMA} "
        f"together. Her expression is anxious and worried. Garden flowers "
        f"frame the window. The mood is surveillance and unease."
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
        f"{GIRIJAYA} returns to {MRINALINI_CHAR} with devastating news. Mrinalini "
        f"sits by a window, turning her face away in heartbreak. Girijaya "
        f"kneels beside her. Evening light fades. The mood is betrayal and "
        f"sorrow. Wilting flowers in a vase nearby."
    ),
    "3_8": (
        f"A young woman ({MRINALINI_CHAR}) sits at a wooden writing desk by warm "
        f"lamplight, composing a letter with a quill pen. An ink pot and "
        f"rolled parchment are visible on the desk. Her friend stands nearby "
        f"ready to deliver the letter. The mood is thoughtful correspondence. "
        f"Evening light through a window."
    ),
    "3_9": (
        f"{HEMCHANDRA} lies alone on a bed, face buried in a pillow, in anguish. "
        f"A crumpled letter lies on the floor beside him. Moonlight streams "
        f"through the window. A warrior brought low by emotional torment. "
        f"The mood is vulnerability and inner conflict."
    ),
    "3_10": (
        f"{MRINALINI_CHAR} and {HEMCHANDRA} stand face to face by a moonlit lake "
        f"surrounded by trees. They embrace after long separation. Ripples "
        f"spread across the silvery water. Fireflies dot the darkness. "
        f"The mood is magical reunion and romantic fulfillment."
    ),
    "4_1": (
        f"{PASHUPATI} sits in midnight darkness, a single candle illuminating "
        f"his stern face. His servant Shantashil kneels before him. "
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
        f"his long-lost wife. His face shows shock. The temple door closes. "
        f"Dramatic revelation — closed doors, flickering lamps, emotional "
        f"confrontation between husband and wife."
    ),
    "4_4": (
        f"Seventeen Turkish horsemen on magnificent steeds ride down the royal "
        f"road of Navadwip. They wear turbans and carry curved swords and spears. "
        f"Palace gates loom ahead. Citizens watch with concern. The mood is conquest "
        f"and imperial presence. Dust clouds, military banners."
    ),
    "4_5": (
        f"{PASHUPATI} faces Bakhtiyar Khilji — a fierce Turkish general — in "
        f"the palace hall. The general demands submission. Pashupati stands "
        f"defiant. Guards line the walls. The mood is tense negotiation and "
        f"the clash of civilizations. Power and confrontation."
    ),
    "4_6": (
        f"{MANORAMA} climbs out of a high window using the branches of a mango tree. "
        f"Her sari catches on branches as she leaps to freedom. Nighttime escape — "
        f"moonlight, brave action. The mansion walls tower behind her. "
        f"The mood is daring feminine courage."
    ),
    "4_7": (
        f"Turkish army enters Navadwip at night — chaos everywhere. Burning "
        f"houses light the sky orange. Fallen warriors lie in the streets. Soldiers with "
        f"torches and swords. Civilians flee. The mood is dramatic destruction. "
        f"A great Hindu temple burns in the background."
    ),
    "4_8": (
        f"{MRINALINI_CHAR} and {GIRIJAYA} sit by a tranquil lakeside at dawn. "
        f"Mrinalini stares blankly at the water, unresponsive, in shock. "
        f"Girijaya watches over her protectively. Lotus flowers float on "
        f"the water. The mood is profound grief and gentle companionship."
    ),
    "4_9": (
        f"{MRINALINI_CHAR} lies asleep, dreaming — shown through translucent vision "
        f"above her of {HEMCHANDRA} riding victorious on a white horse, sword "
        f"raised. She awakens to find him actually standing before her. "
        f"The dream dissolving into reality. Mystical, hopeful mood."
    ),
    "4_10": (
        f"{HEMCHANDRA} and {MRINALINI_CHAR} embrace in a moonlit garden pavilion. "
        f"Joy on their faces. In the background, {GIRIJAYA} and "
        f"a man (Digvijay) watch with smiles. Flowering vines wrap the pillars. "
        f"The mood is joyous romantic reunion."
    ),
    "4_11": (
        f"{MRINALINI_CHAR} and {GIRIJAYA} sit together in a domestic interior. "
        f"Mrinalini narrates her past — visualized as a ghostly scene behind "
        f"them of a young woman in a river during a storm, rescued "
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
        f"{PASHUPATI} walks through a devastated city — fallen warriors and ruin on "
        f"the streets, burning buildings. He sees his own mansion ablaze. "
        f"In anguish, he runs into the burning temple to embrace the goddess idol. "
        f"Inferno, tragic heroism. Flames consuming everything."
    ),
    "4_15": (
        f"A funeral pyre burns by the sacred Ganges at dawn. {MANORAMA}, "
        f"disheveled but serene-faced, walks toward the flames. Brahmins chant "
        f"nearby. The river flows peacefully beyond. The mood is tragic dignity "
        f"and sacrifice. Sacred fire and sacred water together."
    ),
}


# ═══════════════════════════════════════════════════════════════════
# BAEESWEEN SADI — Rahul Sankrityayan (22nd Century)
# ═══════════════════════════════════════════════════════════════════

BAEESWEEN_STYLE = (
    "Generate an image in the style of a vintage Indian woodblock print. "
    "Monochromatic warm sepia and brown tones with fine crosshatch engraving lines. "
    "A single accent color of deep saffron orange used sparingly for emphasis. "
    "The composition should feel like a classic book illustration — detailed, "
    "contemplative, with strong chiaroscuro. No text, no lettering, no words "
    "anywhere in the image.\n\nScene: "
)

BAEESWEEN_PROMPTS = {
    "chapter_1": (
        "An elderly bearded Indian sage in simple robes sits at the mouth of a "
        "mountain cave high in the Himalayas, gazing out at a vast transformed "
        "landscape below — towering unfamiliar trees, a distant receded river, "
        "waterfalls. He is waking from a centuries-long sleep. The mood is wonder "
        "and disorientation. Dawn light filters through the cave entrance."
    ),
    "chapter_2": (
        "A lush terraced orchard on a Himalayan mountainside — enormous apple "
        "and orange trees heavy with impossibly large, perfect fruit. Neat irrigation "
        "channels and copper pipes wind through the grove. In the distance, workers "
        "in clean simple clothing pick fruit into baskets. The old sage walks among "
        "them in leaf-clothes, a stranger from another time."
    ),
    "chapter_3": (
        "A panoramic vista of a futuristic yet pastoral Indian landscape — "
        "gleaming low buildings nestled among trees, electric wires strung between "
        "mountains, clean wide paths. A group of well-dressed men and women of "
        "different backgrounds sit in a circle on a veranda, engaged in animated "
        "discussion. Books and scrolls are visible. The mood is intellectual vitality."
    ),
    "chapter_4": (
        "The grand facade of a reimagined Nalanda University — a magnificent "
        "campus with classical Indian architectural elements blended with clean "
        "modern lines. Students of all ages walk through columned walkways. "
        "A vast library building rises in the background. Gardens and fountains "
        "surround the structures. The mood is reverence for knowledge."
    ),
    "chapter_5": (
        "A split composition: the left half shows the inequality of "
        "early 20th century India — cramped streets, barefoot workers, smoke — "
        "while the right half shows the clean, egalitarian future — open spaces, "
        "healthy people in simple dignified clothing, trees. A thin vertical line "
        "of saffron divides the two worlds. The mood is contrast and reflection."
    ),
    "chapter_6": (
        "A prosperous Indian village of the future — clean communal houses with "
        "gardens, shared dining halls, children playing in open spaces. A man and "
        "woman work side by side tending a vegetable garden. The village is surrounded "
        "by orchards and connected by smooth paths. Copper pipes bring water. "
        "The mood is community and contentment."
    ),
    "chapter_7": (
        "A sunlit nursery and children's garden — young children of diverse "
        "backgrounds play together, some singing, some examining plants and insects "
        "with magnifying lenses. A gentle teacher sits among them. Toys and "
        "educational objects are scattered on soft ground. Flowering vines frame "
        "the scene. The mood is innocence and discovery."
    ),
    "chapter_8": (
        "A sleek electric train races along tracks through dramatic Himalayan "
        "foothills — dense sal and teak forests on both sides, terraced orchards "
        "climbing the hills, tunnels carved through mountains. Inside a window, "
        "passengers read and converse. The landscape blurs with speed. "
        "The mood is progress and movement through nature."
    ),
    "chapter_9": (
        "A ceremonial welcome at the gates of Nalanda — garlands of flowers, "
        "crowds of scholars in simple white clothing, the ancient university "
        "buildings restored to glory in the background. The old sage, now in "
        "clean robes, receives a flower garland. Lamps and banners line the path. "
        "The mood is celebration and homecoming."
    ),
    "chapter_10": (
        "Tiny children in a bright classroom without walls — open to nature. "
        "They sit in a circle on the ground, some building with blocks, others "
        "listening to a story. A teacher demonstrates something with her hands. "
        "Birds and butterflies pass through. The floor transitions seamlessly "
        "into a garden. The mood is gentle learning."
    ),
    "chapter_11": (
        "Older children (around 10-12) in an open-air workshop — some are "
        "examining botanical specimens, others peer through telescopes or "
        "work with mechanical models. Maps and globes are visible. A child "
        "debates animatedly with a teacher. The setting blends workshop, "
        "laboratory, and garden. The mood is curiosity and empowerment."
    ),
    "chapter_12": (
        "Young adults in a sophisticated university setting — a grand amphitheater "
        "where a lecturer demonstrates a scientific apparatus. Students take notes "
        "on tablets. Through arched windows, a botanical garden and observatory "
        "dome are visible. Chemical apparatus and astronomical instruments line "
        "the walls. The mood is intellectual ambition."
    ),
    "chapter_13": (
        "A democratic assembly in session — representatives from across India "
        "sit in concentric semicircles in an open-air parliament pavilion. "
        "A speaker stands at the center. The architecture combines classical "
        "Indian pillars with clean modernist lines. Sunlight streams through. "
        "No guards, no ornate thrones — just equals deliberating. "
        "The mood is governance through reason."
    ),
    "chapter_14": (
        "A farewell scene at a train station — the sage stands by a modern "
        "locomotive, looking back at Nalanda's spires in the distance. "
        "Friends wave from the platform. Mango orchards line the tracks ahead. "
        "The sun is setting, casting long warm shadows. Luggage and flower "
        "garlands rest on the platform. The mood is bittersweet departure."
    ),
    "chapter_15": (
        "A bird's-eye view of the Indian subcontinent reimagined — interconnected "
        "villages and cities linked by rail lines and roads, each settlement "
        "surrounded by forests and orchards. Rivers flow clean. Small democratic "
        "assemblies are visible in each village. The whole forms a network, "
        "like a living organism. The mood is unity in diversity."
    ),
    "chapter_16": (
        "A symbolic still-life composition — objects from the old world (coins, "
        "weapons, chains, ornate crowns) lie discarded "
        "and crumbling on the left. On the right, simple objects of the new world "
        "(books, farming tools, a compass, a telescope, a child's toy) glow with "
        "warm light. Vines grow over the old objects. The mood is quiet triumph."
    ),
}


def run_book(book_name, book_config, prompts, max_workers=4):
    """Process all chapters for one book with thread parallelization."""
    output_dir = book_config["output_dir"]
    state_path = book_config["checkpoint"]
    os.makedirs(output_dir, exist_ok=True)

    state = load_json(state_path, {"completed": []})
    total = len(prompts)

    # Count remaining work
    remaining = []
    for key, prompt in prompts.items():
        a5_key = f"{key}_a5"
        web_key = f"{key}_web"
        if a5_key not in state["completed"] or web_key not in state["completed"]:
            remaining.append((key, prompt))

    if not remaining:
        print(f"\n[{book_name}] All {total} chapters complete!")
        return

    print(f"\n[{book_name}] {len(remaining)} chapters remaining (of {total}), {max_workers} workers")

    # Each thread gets its own client to avoid connection issues
    def make_worker(key, prompt):
        thread_client = genai.Client(api_key=GEMINI_API_KEY)
        return process_chapter(thread_client, book_config, key, prompt, state, state_path)

    done = total - len(remaining)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(make_worker, key, prompt): key
            for key, prompt in remaining
        }
        for future in as_completed(futures):
            key = futures[future]
            done += 1
            try:
                results = future.result()
                for r in results:
                    print(f"  [{book_name}] [{done}/{total}] {r}")
            except Exception as e:
                print(f"  [{book_name}] [{done}/{total}] {key}: ERROR {e}")

    a5_done = len([k for k in state["completed"] if k.endswith("_a5")])
    web_done = len([k for k in state["completed"] if k.endswith("_web")])
    print(f"\n[{book_name}] Done: {a5_done}/{total} A5 + {web_done}/{total} web in {output_dir}/")


def main():
    mrinalini_config = {
        "output_dir": "mrinalini_images_v2",
        "checkpoint": "data/mrinalini_v2_checkpoint.json",
        "style_prefix": MRINALINI_STYLE,
    }

    baeesween_config = {
        "output_dir": "baeesween_images_v2",
        "checkpoint": "data/baeesween_v2_checkpoint.json",
        "style_prefix": BAEESWEEN_STYLE,
    }

    # Run both books in parallel with their own thread pools
    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(run_book, "Mrinalini", mrinalini_config, MRINALINI_PROMPTS, max_workers=4)
        f2 = executor.submit(run_book, "Baeesween Sadi", baeesween_config, BAEESWEEN_PROMPTS, max_workers=4)
        f1.result()
        f2.result()

    print("\n=== All done! ===")


if __name__ == "__main__":
    main()
