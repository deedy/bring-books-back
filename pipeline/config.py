"""Unified book configuration for the entire pipeline.

Consolidates 7 separate config dicts from 7 scripts into one BookConfig dataclass.
All file paths are derived from the canonical book ID — no hardcoded paths.
"""

from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
WEB_DATA_DIR = PROJECT_ROOT / "web" / "public" / "data"

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


@dataclass
class BookConfig:
    # ── Identity ──────────────────────────────────────────────────────────
    id: str
    title: str
    transliterated_title: str
    original_title: str
    author_id: str
    author_name: str
    author_years: str
    original_language: str
    original_year: int
    genre: list[str]
    accent_color: str
    style_context: str

    # ── Translation ───────────────────────────────────────────────────────
    translation_prompt: str = ""

    # ── Chapter detection ─────────────────────────────────────────────────
    chapter_context: str = ""

    # ── Annotation ────────────────────────────────────────────────────────
    annotation_prompt: str = ""

    # ── Image generation ──────────────────────────────────────────────────
    image_style_prefix: str = ""
    characters_description: str = ""

    # ── Character portraits ───────────────────────────────────────────────
    character_style_prefix: str = ""

    # ── Hero banner ───────────────────────────────────────────────────────
    hero_prompt: str = ""

    # ── Original text ──────────────────────────────────────────────────
    original_script: str = ""  # e.g., "Devanagari", "Bengali", "Tamil"

    # ── Book type ────────────────────────────────────────────────────────
    type: str = "book"  # "book" or "anthology"

    # ── Derived paths ─────────────────────────────────────────────────────
    @property
    def book_dir(self) -> Path:
        return DATA_DIR / self.id

    @property
    def source_pdf(self) -> Path:
        return self.book_dir / "source.pdf"

    @property
    def ocr_txt(self) -> Path:
        return self.book_dir / "ocr.txt"

    @property
    def english_raw_txt(self) -> Path:
        return self.book_dir / "english_raw.txt"

    @property
    def english_txt(self) -> Path:
        return self.book_dir / "english.txt"

    @property
    def chapters_def_json(self) -> Path:
        return self.book_dir / "chapters_def.json"

    @property
    def image_prompts_json(self) -> Path:
        return self.book_dir / "image_prompts.json"

    @property
    def images_dir(self) -> Path:
        return self.book_dir / "images"

    # Checkpoints
    @property
    def ocr_checkpoint(self) -> Path:
        return self.book_dir / "ocr_checkpoint.json"

    @property
    def translate_checkpoint(self) -> Path:
        return self.book_dir / "translate_checkpoint.json"

    @property
    def images_checkpoint(self) -> Path:
        return self.book_dir / "images_checkpoint.json"

    # Web output paths
    @property
    def web_book_dir(self) -> Path:
        return WEB_DATA_DIR / "books" / self.id

    @property
    def web_chapters_json(self) -> Path:
        return self.web_book_dir / "chapters.json"

    @property
    def web_original_chapters_json(self) -> Path:
        return self.web_book_dir / "chapters_original.json"

    @property
    def web_annotations_json(self) -> Path:
        return self.web_book_dir / "annotations.json"

    @property
    def web_chapter_images_dir(self) -> Path:
        return WEB_DATA_DIR / "images" / "chapters" / self.id

    @property
    def web_cover_path(self) -> Path:
        return WEB_DATA_DIR / "images" / "covers" / f"{self.id}.png"


# ══════════════════════════════════════════════════════════════════════════
# Book definitions
# ══════════════════════════════════════════════════════════════════════════

BOOKS: dict[str, BookConfig] = {}


def _register(cfg: BookConfig):
    BOOKS[cfg.id] = cfg


def get_book(book_id: str) -> BookConfig:
    if book_id not in BOOKS:
        raise ValueError(f"Unknown book: {book_id}. Available: {', '.join(BOOKS.keys())}")
    return BOOKS[book_id]


# ── Ponniyin Selvan ───────────────────────────────────────────────────────

_register(BookConfig(
    id="ponniyin-selvan",
    title="Ponniyin Selvan",
    transliterated_title="Ponniyin Selvan",
    original_title="பொன்னியின் செல்வன்",
    author_id="kalki-krishnamurthy",
    author_name="Kalki Krishnamurthy",
    author_years="1899–1954",
    original_language="Tamil",
    original_script="Tamil",
    original_year=1955,
    genre=["Historical Fiction", "Epic"],
    accent_color="#8B6914",
    style_context="Epic historical novel set in the 10th-century Chola dynasty",
    annotation_prompt=(
        'You are a literary analyst helping annotate an English translation of "Ponniyin Selvan" (1955), '
        "an epic historical novel set in 10th-century Chola dynasty India by Kalki Krishnamurthy. "
        "The translation preserves many Tamil proper nouns, historical terms, and cultural vocabulary.\n\n"
        "For the given chapter text, extract three categories of terms that a modern English reader might want explained:\n\n"
        '1. **Characters** — Recurring named people. Give a 1-2 sentence description of who they are and their role in the Chola court/story.\n'
        '2. **Proper nouns** — Place names (cities, temples, rivers), kingdom names, dynasty references, cultural terms, religious terms, festival names, etc. Give a brief explanation.\n'
        '3. **Vocabulary** — Archaic, vernacular, or culturally-specific words/phrases (e.g., "palanquin", "thambiran", "kumkum") that might be unfamiliar. Give a brief definition.\n\n'
        "Rules:\n"
        "- Only extract terms that actually appear in the chapter text (exact spelling match).\n"
        '- For character names, use the exact form that appears in the text (e.g., "Vandiyathevan" not "Vallavaraiyan").\n'
        "- Keep descriptions concise: 1-2 sentences max.\n"
        "- Do NOT extract common English words.\n"
        "- Focus on terms that are clearly Tamil/Indian in origin, or specific to the Chola dynasty period.\n"
        "- Return valid JSON only, no markdown fences."
    ),
    image_style_prefix=(
        "Generate an image in the style of a Tanjore painting — "
        "rich gold leaf accents, vibrant jewel tones (deep red, emerald green, royal blue), "
        "ornate decorative borders. "
        "The composition should feel like a traditional South Indian temple painting — "
        "warm golden lighting, detailed ornamentation. "
        "No text, no lettering, no words anywhere in the image. "
        "10th century Chola dynasty South India setting.\n\nScene: "
    ),
    characters_description=(
        "Key characters:\n"
        "- Vandiyathevan: a dashing young warrior, charming, athletic build, light armor and flowing cape\n"
        "- Arulmozhivarman (Ponniyin Selvan): a noble prince, serene, regal bearing, royal Chola attire\n"
        "- Kundavai: an intelligent, regal princess, elaborate silk sari, gold jewelry\n"
        "- Nandini: a stunningly beautiful woman, seductive, ornate dark silk, mysterious aura\n"
        "- Aditya Karikalan: a fierce warrior prince, muscular, battle-scarred, crown prince attire\n"
    ),
    character_style_prefix=(
        "Generate an image in the style of a Tanjore painting — rich gold leaf accents, "
        "vibrant jewel tones (deep red, emerald green, royal blue), ornate decorative borders. "
        "The style should feel like a traditional South Indian temple painting with warm "
        "golden lighting and detailed ornamentation. "
        "No text, no lettering, no words anywhere in the image. "
        "10th century Chola dynasty South India setting.\n\n"
    ),
    hero_prompt=(
        "Generate an edge-to-edge illustration in Tanjore painting style "
        "with gold, crimson, emerald, and lapis lazuli palette. "
        "The Chola empire at its peak: the grand Brihadeeswarar temple towering over the scene, "
        "the Kaveri river flowing through lush palm groves, warriors on elephants, "
        "a magnificent sunset casting golden light over the ancient kingdom. "
        "Bright, vivid, saturated colors. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
))


# ── Baeesween Sadi ───────────────────────────────────────────────────────

_register(BookConfig(
    id="baeesween-sadi",
    title="The Twenty-Second Century",
    transliterated_title="Baeesween Sadi",
    original_title="बाईसवीं सदी",
    author_id="rahul-sankrityayan",
    author_name="Rahul Sankrityayan",
    author_years="1893–1963",
    original_language="Hindi",
    original_script="Devanagari",
    original_year=1924,
    genre=["Science Fiction", "Utopian Fiction"],
    accent_color="#4B0082",
    style_context="Hindi science fiction novel about a utopian 22nd century India",
    image_style_prefix=(
        "Scene in the style of a vintage Indian woodblock print with saffron, indigo, and gold palette. "
        "Monochromatic warm tones with fine crosshatch engraving lines and a single accent of deep saffron orange. "
        "Futuristic 22nd-century Indian setting with advanced technology blended with traditional aesthetics. "
        "No text, no lettering. Scene: "
    ),
    annotation_prompt=(
        'You are a literary analyst helping annotate an English translation of "Baeesween Sadi" '
        "(The Twenty-Second Century, 1924), a Hindi science fiction novel by Rahul Sankrityayan. "
        "The translation preserves many Hindi proper nouns, cultural terms, and futuristic vocabulary.\n\n"
        "For the given chapter text, extract three categories of terms that a modern English reader might want explained:\n\n"
        '1. **Characters** — Recurring named people. Give a 1-2 sentence description of who they are and their role.\n'
        '2. **Proper nouns** — Place names, cultural terms, historical references, Hindi/Sanskrit terms, scientific concepts, geographical references, etc. Give a brief explanation.\n'
        '3. **Vocabulary** — Archaic, vernacular, or culturally-specific words/phrases (e.g., "kos", "vimana", "ashram") that might be unfamiliar. Give a brief definition.\n\n'
        "Rules:\n"
        "- Only extract terms that actually appear in the chapter text (exact spelling match).\n"
        "- For character names, use the exact form that appears in the text.\n"
        "- Keep descriptions concise: 1-2 sentences max.\n"
        "- Do NOT extract common English words.\n"
        "- Focus on terms that are clearly Hindi/Sanskrit/Indian in origin, or specific to the futuristic setting.\n"
        "- Return valid JSON only, no markdown fences."
    ),
    character_style_prefix=(
        "Generate an image in the style of a vintage Indian woodblock print. "
        "Monochromatic warm sepia and brown tones with fine crosshatch engraving lines. "
        "A single accent color of deep saffron orange used sparingly for emphasis. "
        "The composition should feel like a classic book illustration — detailed, "
        "contemplative, with strong chiaroscuro. "
        "No text, no lettering, no words anywhere in the image.\n\n"
    ),
    hero_prompt=(
        "Generate an edge-to-edge illustration in vintage Indian woodblock print style "
        "with saffron, indigo, and gold palette. "
        "A panoramic vision of 22nd-century India: a futuristic city nestled in mountains, "
        "lush orchards with enormous fruits, flying machines in the sky, advanced irrigation channels, "
        "radiant sunrise casting golden light across the landscape. "
        "Bright, vivid, saturated colors. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
))


# ── Mrinalini ─────────────────────────────────────────────────────────────

_register(BookConfig(
    id="mrinalini",
    title="Mrinalini",
    transliterated_title="Mrinalini",
    original_title="মৃণালিনী",
    author_id="bankim-chandra-chattopadhyay",
    author_name="Bankim Chandra Chattopadhyay",
    author_years="1838–1894",
    original_language="Bengali",
    original_script="Bengali",
    original_year=1882,
    genre=["Historical Romance", "Adventure"],
    accent_color="#800020",
    style_context="Bengali historical romance set in 13th-century Bengal during the Bakhtiyar Khilji invasion",
    annotation_prompt=(
        'You are a literary analyst helping annotate an English translation of "Mrinalini" (1882), '
        "a historical romance set in 13th-century Bengal by Bankim Chandra Chattopadhyay. "
        "The translation preserves many Bengali proper nouns, historical terms, and cultural vocabulary.\n\n"
        "For the given chapter text, extract three categories of terms that a modern English reader might want explained:\n\n"
        '1. **Characters** — Recurring named people. Give a 1-2 sentence description of who they are and their role.\n'
        '2. **Proper nouns** — Place names, kingdoms, battles, cultural terms, historical references, caste names, religious terms, etc. Give a brief explanation.\n'
        '3. **Vocabulary** — Archaic, vernacular, or culturally-specific words/phrases (e.g., "Yavan", "sannyasi", "ghat") that might be unfamiliar. Give a brief definition.\n\n'
        "Rules:\n"
        "- Only extract terms that actually appear in the chapter text (exact spelling match).\n"
        "- For character names, use the exact form that appears in the text.\n"
        "- Keep descriptions concise: 1-2 sentences max.\n"
        "- Do NOT extract common English words.\n"
        "- Focus on terms that are clearly Bengali/Indian in origin, or specific historical references to the Bakhtiyar Khilji invasion period.\n"
        "- Return valid JSON only, no markdown fences."
    ),
    character_style_prefix=(
        "Generate an image in the style of a vintage Bengali miniature painting "
        "from the 19th century. Monochromatic warm sepia and brown tones with fine "
        "crosshatch engraving lines, like a classic book illustration. "
        "A single accent color of deep vermilion red used sparingly for emphasis. "
        "The composition should feel like a woodblock print from a 19th century "
        "Bengali literary journal — detailed, contemplative, with strong chiaroscuro. "
        "No text, no lettering, no words anywhere in the image. "
        "13th century Bengal setting with Hindu and Muslim architectural elements.\n\n"
    ),
    hero_prompt=(
        "Generate an edge-to-edge illustration in Bengali miniature painting style "
        "with vermilion, purple, emerald, and gold palette. "
        "A wide panoramic landscape of 13th-century Bengal: "
        "a serene lotus pond in the foreground, ancient temples of Navadwip with ornate spires "
        "rising across the midground, the Ganges river shimmering at twilight under a magenta sky. "
        "Boats on the river, birds in flight, lush tropical vegetation. "
        "NO people, NO figures. Pure landscape scenery. "
        "Bright, vivid, saturated colors. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
))


# ── Alaler Gharer Dulal ──────────────────────────────────────────────────

_register(BookConfig(
    id="alaler-gharer-dulal",
    title="The Spoilt Child",
    transliterated_title="Alaler Gharer Dulal",
    original_title="আলালের ঘরের দুলাল",
    author_id="peary-chand-mitra",
    author_name="Peary Chand Mitra",
    author_years="1814–1883",
    original_language="Bengali",
    original_script="Bengali",
    original_year=1858,
    genre=["Social Satire", "Realist Fiction"],
    accent_color="#2F4F4F",
    style_context="First Bengali novel — social satire of 19th-century colonial Calcutta",
    annotation_prompt=(
        'You are a literary analyst helping annotate an English translation of "Alaler Gharer Dulal" '
        "(1858), a social satire set in 19th-century colonial Calcutta by Peary Chand Mitra. "
        "The translation preserves many Bengali proper nouns and cultural vocabulary.\n\n"
        "For the given chapter text, extract three categories of terms that a modern English reader might want explained:\n\n"
        '1. **Characters** — Recurring named people. Give a 1-2 sentence description of who they are and their role.\n'
        '2. **Proper nouns** — Place names, cultural terms, historical references, caste names, etc. Give a brief explanation.\n'
        '3. **Vocabulary** — Archaic, vernacular, or culturally-specific words/phrases that might be unfamiliar. Give a brief definition.\n\n'
        "Rules:\n"
        "- Only extract terms that actually appear in the chapter text (exact spelling match).\n"
        "- For character names, use the exact form that appears in the text.\n"
        "- Keep descriptions concise: 1-2 sentences max.\n"
        "- Do NOT extract common English words.\n"
        "- Focus on terms that are clearly Bengali/Indian in origin, or specific to 19th century colonial Calcutta.\n"
        "- Return valid JSON only, no markdown fences."
    ),
    character_style_prefix=(
        "Generate an image in the style of a Bengali woodblock print from the 1850s. "
        "Monochromatic warm sepia tones with fine crosshatch engraving lines. "
        "A single accent color of deep indigo blue used sparingly for emphasis. "
        "The composition should feel like an illustration from the first Bengali novels — "
        "detailed, satirical, with strong contrast. "
        "No text, no lettering, no words anywhere in the image. "
        "19th century colonial Calcutta setting.\n\n"
    ),
    hero_prompt=(
        "Generate an edge-to-edge illustration in colonial Calcutta watercolor style "
        "with sepia, indigo, and ochre palette. "
        "1850s Calcutta: a wealthy Bengali mansion with ornate columns and arches, "
        "a bustling courtyard filled with servants and visitors, colonial architecture visible, "
        "the Hooghly river and boats in the distance, warm afternoon light. "
        "Bright, vivid, saturated colors. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
))


# ── Barrister Parvateesam ────────────────────────────────────────────────

_register(BookConfig(
    id="barrister-parvateesam",
    title="Barrister Parvateesam",
    transliterated_title="Barrister Parvateesam",
    original_title="బారిస్టర్ పార్వతీశం",
    author_id="mokkapati-narasimha-shastri",
    author_name="Mokkapati Narasimha Shastri",
    author_years="1892–1975",
    original_language="Telugu",
    original_script="Telugu",
    original_year=1924,
    genre=["Humor", "Picaresque"],
    accent_color="#8B4513",
    style_context="Humorous Telugu novel about a naive Brahmin's misadventures traveling to England",
    annotation_prompt=(
        'You are a literary analyst helping annotate an English translation of "Barrister Parvateesam" (1924), '
        "a humorous Telugu novel by Mokkapati Narasimha Shastri about a naive young Brahmin's misadventures "
        "traveling to England. The translation preserves many Telugu proper nouns, cultural terms, and period vocabulary.\n\n"
        "For the given chapter text, extract three categories of terms that a modern English reader might want explained:\n\n"
        '1. **Characters** — Recurring named people. Give a 1-2 sentence description of who they are and their role.\n'
        '2. **Proper nouns** — Place names, cultural terms, historical references, caste references, religious terms, British/Indian colonial terms, etc. Give a brief explanation.\n'
        '3. **Vocabulary** — Archaic, vernacular, or culturally-specific words/phrases (e.g., "dhoti", "munshi", "tiffin") that might be unfamiliar. Give a brief definition.\n\n'
        "Rules:\n"
        "- Only extract terms that actually appear in the chapter text (exact spelling match).\n"
        "- For character names, use the exact form that appears in the text.\n"
        "- Keep descriptions concise: 1-2 sentences max.\n"
        "- Do NOT extract common English words.\n"
        "- Focus on terms that are clearly Telugu/Indian in origin, or specific to early 20th century colonial India/England.\n"
        "- Return valid JSON only, no markdown fences."
    ),
    character_style_prefix=(
        "Generate an image in the style of a 1920s Indian watercolor illustration. "
        "Soft sepia base with hand-tinted accents of indigo and vermilion. "
        "The style should feel like an illustration from an early 20th century "
        "Indian literary magazine — warm, humorous, detailed character study. "
        "No text, no lettering, no words anywhere in the image. "
        "Early 20th century India / Edwardian England setting.\n\n"
    ),
    hero_prompt=(
        "Generate an edge-to-edge illustration in 1920s Indian watercolor style "
        "with warm, humorous tones. "
        "A wide panoramic scene: a grand English port with a large steamship docked, "
        "fog rolling over Victorian buildings and lampposts on the left, "
        "Indian architectural motifs and warm golden colors blending in on the right. "
        "Luggage and trunks on the dock, seagulls overhead, two cultures colliding in architecture. "
        "NO people, NO figures. Pure landscape/architecture scenery. "
        "Bright, vivid, saturated colors. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
))


# ── Chandrakanta ──────────────────────────────────────────────────────────

_register(BookConfig(
    id="chandrakanta",
    title="Chandrakanta",
    transliterated_title="Chandrakanta",
    original_title="चंद्रकांता",
    author_id="devaki-nandan-khatri",
    author_name="Devaki Nandan Khatri",
    author_years="1861–1913",
    original_language="Hindi",
    original_script="Devanagari",
    original_year=1888,
    genre=["Fantasy", "Romance", "Adventure"],
    accent_color="#8B0000",
    style_context="Hindi fantasy novel with tilism (magical realms)",
    translation_prompt=(
        "You are translating a Hindi fantasy/romance novel titled 'Chandrakanta' "
        "(चंद्रकांता) by Devaki Nandan Khatri, first published in 1888. "
        "This is one of the most popular Hindi novels ever written — a tale of "
        "love, adventure, and magic set in the tilism (magical realms) of rival "
        "kingdoms. The story follows Prince Virendra Singh and Princess Chandrakanta "
        "through underground labyrinths, enchanted fortresses, and political intrigue. "
        "Preserve Hindi proper nouns (character names, place names, tilism terms). "
        "Translate into fluent, literary English. Preserve paragraph breaks and the "
        "original adventurous, romantic tone. Do NOT skip or summarize any content. "
        "Do not add commentary — output only the English translation."
    ),
    chapter_context=(
        "Hindi fantasy/romance novel with tilism (magical realms), underground labyrinths. "
        "May have parts/sections."
    ),
    annotation_prompt=(
        'You are a literary analyst helping annotate an English translation of "Chandrakanta" (1888), '
        "a Hindi fantasy/romance novel by Devaki Nandan Khatri. This is one of the most popular Hindi "
        "novels ever written, featuring tilism (magical realms), underground labyrinths, aiyyars "
        "(spies/magicians), and rival kingdoms. The translation preserves many Hindi proper nouns and "
        "fantasy vocabulary.\n\n"
        "For the given chapter text, extract three categories of terms that a modern English reader might want explained:\n\n"
        '1. **Characters** — Recurring named people. Give a 1-2 sentence description of who they are and their role.\n'
        '2. **Proper nouns** — Place names, kingdom names, tilism names, cultural terms, Hindi/Urdu terms, etc. Give a brief explanation.\n'
        '3. **Vocabulary** — Archaic, vernacular, or culturally-specific words/phrases (e.g., "tilism", "aiyyar", "kotwal") that might be unfamiliar. Give a brief definition.\n\n'
        "Rules:\n"
        "- Only extract terms that actually appear in the chapter text (exact spelling match).\n"
        "- For character names, use the exact form that appears in the text.\n"
        "- Keep descriptions concise: 1-2 sentences max.\n"
        "- Do NOT extract common English words.\n"
        "- Focus on terms that are clearly Hindi/Urdu/Indian in origin, or specific to the fantasy setting.\n"
        "- Return valid JSON only, no markdown fences."
    ),
    image_style_prefix=(
        "Generate an image in the style of a Mughal miniature painting — "
        "rich gold leaf, deep crimson, emerald green, intricate geometric patterns. "
        "The composition should feel like a luxury illustrated manuscript from "
        "the Mughal court era — ornate borders, detailed architectural elements, "
        "elaborate costumes with jewels and fine fabrics. "
        "No text, no lettering, no words anywhere in the image. "
        "19th century North Indian fantasy kingdom setting with magical elements.\n\nScene: "
    ),
    characters_description=(
        "Key characters:\n"
        "- Virendra Singh: a handsome young Rajput prince, brave, strong build, ornate armor and turban\n"
        "- Chandrakanta: a stunningly beautiful princess, delicate features, ornate jewelry, silk garments\n"
        "- Krur Singh: a menacing warrior, dark, heavy-set, scheming expression\n"
        "- Shivdutt: an elderly aiyar (spy/magician), mysterious, magical robes\n"
    ),
    character_style_prefix=(
        "Generate an image in the style of a Mughal miniature painting — "
        "rich gold leaf, deep crimson, emerald green, intricate geometric patterns. "
        "The style should feel like a luxury illustrated manuscript from "
        "the Mughal court era — ornate, detailed character study. "
        "No text, no lettering, no words anywhere in the image. "
        "19th century North Indian fantasy kingdom setting.\n\n"
    ),
    hero_prompt=(
        "Generate an edge-to-edge illustration in Mughal miniature painting style "
        "with gold, crimson, and emerald palette. "
        "Grand ornate palaces with domes and minarets, a magical tilism labyrinth "
        "with glowing pathways, a moonlit scene with ornate Rajput architecture, "
        "mystery and enchantment in the air, starlit sky. "
        "Bright, vivid, saturated colors. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
))


# ── Matira Manisha ────────────────────────────────────────────────────────

_register(BookConfig(
    id="matira-manisha",
    title="Man of the Soil",
    transliterated_title="Matira Manisha",
    original_title="ମାଟିର ମଣିଷ",
    author_id="kalindi-charan-panigrahi",
    author_name="Kalindi Charan Panigrahi",
    author_years="1901–1991",
    original_language="Odia",
    original_script="Odia",
    original_year=1929,
    genre=["Realist Fiction", "Rural Life"],
    accent_color="#B8860B",
    style_context="Odia realist novel about farmers",
    translation_prompt=(
        "You are translating an Odia realist novel titled 'Matira Manisha' "
        "(ମାଟିର ମଣିଷ) by Kalindi Charan Panigrahi, first published in 1929. "
        "This is a landmark Odia novel about farmers and rural life in Odisha. "
        "It portrays the struggles of peasant communities against feudal oppression "
        "with deep empathy and realism. Preserve Odia proper nouns and rural vocabulary. "
        "Translate into fluent, literary English. Preserve paragraph breaks and the "
        "original earthy, emotional tone. Do NOT skip or summarize any content. "
        "Do not add commentary — output only the English translation."
    ),
    chapter_context="Odia realist novel about farmers and rural life. May have simple chapter divisions.",
    annotation_prompt=(
        'You are a literary analyst helping annotate an English translation of "Matira Manisha" (1929), '
        "an Odia realist novel by Kalindi Charan Panigrahi about farmers and rural life in Odisha. "
        "The translation preserves many Odia proper nouns and rural vocabulary.\n\n"
        "For the given chapter text, extract three categories of terms that a modern English reader might want explained:\n\n"
        '1. **Characters** — Recurring named people. Give a 1-2 sentence description of who they are and their role.\n'
        '2. **Proper nouns** — Place names, village names, cultural terms, caste references, festival names, etc. Give a brief explanation.\n'
        '3. **Vocabulary** — Archaic, vernacular, or culturally-specific words/phrases (e.g., "zamindar", "bigha", "panchayat") that might be unfamiliar. Give a brief definition.\n\n'
        "Rules:\n"
        "- Only extract terms that actually appear in the chapter text (exact spelling match).\n"
        "- For character names, use the exact form that appears in the text.\n"
        "- Keep descriptions concise: 1-2 sentences max.\n"
        "- Do NOT extract common English words.\n"
        "- Focus on terms that are clearly Odia/Indian in origin, or specific to rural Odisha.\n"
        "- Return valid JSON only, no markdown fences."
    ),
    image_style_prefix=(
        "Generate an image in the style of Pattachitra folk art from Odisha — "
        "earthy ochre, terracotta red, indigo blue, natural pigment colors. "
        "The composition should feel like a traditional Odia scroll painting — "
        "folk art style with bold outlines, flat perspective, decorative borders. "
        "No text, no lettering, no words anywhere in the image. "
        "1920s rural Odisha setting with rice paddies, village huts, and farmland.\n\nScene: "
    ),
    characters_description=(
        "Key characters:\n"
        "- Saria: a poor but dignified farmer, weathered face, simple dhoti, strong hands\n"
        "- Bana: a farmer, friend and neighbor, earthy rural appearance\n"
    ),
    character_style_prefix=(
        "Generate an image in the style of Pattachitra folk art from Odisha — "
        "earthy ochre, terracotta red, indigo blue, natural pigment colors. "
        "The style should feel like a traditional Odia scroll painting — "
        "folk art, bold outlines, detailed character study. "
        "No text, no lettering, no words anywhere in the image. "
        "1920s rural Odisha setting.\n\n"
    ),
    hero_prompt=(
        "Generate an edge-to-edge illustration in Pattachitra folk art style from Odisha "
        "with ochre, terracotta, and indigo palette. "
        "Rural Odisha: expansive rice paddies stretching to the horizon, "
        "a thatched farmhouse with a courtyard, farmers working in the fields, "
        "a dramatic monsoon sky with billowing clouds, lush green vegetation. "
        "Bright, vivid, saturated colors. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
))


# ── Shyamchi Aai ──────────────────────────────────────────────────────────

_register(BookConfig(
    id="shyamchi-aai",
    title="Shyam's Mother",
    transliterated_title="Shyamchi Aai",
    original_title="श्यामची आई",
    author_id="sane-guruji",
    author_name="Sane Guruji",
    author_years="1899–1950",
    original_language="Marathi",
    original_script="Devanagari",
    original_year=1935,
    genre=["Autobiography", "Coming of Age"],
    accent_color="#D2691E",
    style_context="Marathi autobiography about mother-son bond",
    translation_prompt=(
        "You are translating a Marathi autobiography titled 'Shyamchi Aai' "
        "(श्यामची आई) by Sane Guruji (Pandurang Sadashiv Sane), first published in 1935. "
        "This is one of the most beloved Marathi books — a deeply moving account of "
        "the bond between a mother (Aai) and her son Shyam. Written while the author "
        "was in prison, it recounts childhood memories of his mother's love, sacrifice, "
        "and moral teachings in rural Maharashtra. Preserve Marathi proper nouns and "
        "cultural terms. Translate into fluent, literary English with warmth and emotion. "
        "Preserve paragraph breaks and the original tender, nostalgic tone. "
        "Do NOT skip or summarize any content. "
        "Do not add commentary — output only the English translation."
    ),
    chapter_context=(
        "Marathi autobiography about mother-son bond. Written as a series of "
        "stories/episodes told at night."
    ),
    annotation_prompt=(
        'You are a literary analyst helping annotate an English translation of "Shyamchi Aai" (1935), '
        "a Marathi autobiography by Sane Guruji about the bond between a mother and her son Shyam. "
        "The translation preserves many Marathi proper nouns and cultural vocabulary.\n\n"
        "For the given chapter text, extract three categories of terms that a modern English reader might want explained:\n\n"
        '1. **Characters** — Recurring named people. Give a 1-2 sentence description of who they are and their role.\n'
        '2. **Proper nouns** — Place names, cultural terms, festival names, religious terms, etc. Give a brief explanation.\n'
        '3. **Vocabulary** — Archaic, vernacular, or culturally-specific words/phrases (e.g., "aai", "tulsi", "rangoli") that might be unfamiliar. Give a brief definition.\n\n'
        "Rules:\n"
        "- Only extract terms that actually appear in the chapter text (exact spelling match).\n"
        "- For character names, use the exact form that appears in the text.\n"
        "- Keep descriptions concise: 1-2 sentences max.\n"
        "- Do NOT extract common English words.\n"
        "- Focus on terms that are clearly Marathi/Indian in origin, or specific to rural Maharashtra culture.\n"
        "- Return valid JSON only, no markdown fences."
    ),
    image_style_prefix=(
        "Generate an image in the style of Warli tribal art combined with Marathi folk painting — "
        "warm sepia tones, saffron orange accents, simple geometric shapes. "
        "The composition should feel like an illustration from a beloved children's book — "
        "warm, emotional, nostalgic, with folk art sensibility. "
        "No text, no lettering, no words anywhere in the image. "
        "1920s-1930s rural Maharashtra setting with simple houses, fields, and village life.\n\nScene: "
    ),
    characters_description=(
        "Key characters:\n"
        "- Shyam: a young boy (8-12), thin, bright-eyed, simple village clothes\n"
        "- Aai (Mother): a gentle, loving woman in a simple cotton sari, kind face, strong hands from work\n"
    ),
    character_style_prefix=(
        "Generate an image in the style of Warli tribal art combined with Marathi folk painting — "
        "warm sepia tones, saffron orange accents, simple geometric shapes. "
        "The style should feel warm, emotional, nostalgic — a character study. "
        "No text, no lettering, no words anywhere in the image. "
        "1920s-1930s rural Maharashtra setting.\n\n"
    ),
    hero_prompt=(
        "Generate an edge-to-edge illustration in Warli tribal art combined with Marathi folk painting style "
        "with saffron, ochre, and green palette. "
        "A mother and young son sitting together on a village porch, "
        "Konkan fields stretching behind them, a golden sunset sky, "
        "a mango tree laden with fruit, wildflowers in the foreground. "
        "Bright, vivid, saturated colors. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
))


# ── Kayar ─────────────────────────────────────────────────────────────────

_register(BookConfig(
    id="kayar",
    title="Coir",
    transliterated_title="Kayar",
    original_title="கயர்",
    author_id="thakazhi-sivasankara-pillai",
    author_name="Thakazhi Sivasankara Pillai",
    author_years="1912–1999",
    original_language="Malayalam",
    original_script="Malayalam",
    original_year=1978,
    genre=["Epic Fiction", "Social Realism"],
    accent_color="#2E8B57",
    style_context="Epic novel about coir workers in Kerala",
    translation_prompt=(
        "You are translating a Tamil translation of the Malayalam novel 'Kayar' (Coir) "
        "originally by Thakazhi Sivasankara Pillai, first published in 1978. "
        "This epic novel chronicles the lives of coir workers in the Alleppey region "
        "of Kerala across several generations. It portrays the social upheavals, "
        "caste conflicts, labor movements, and human relationships in the backwater "
        "communities of Kerala. Preserve local terms (Malayalam/Tamil place names, "
        "caste names, occupational terms). Translate into fluent, literary English. "
        "Preserve paragraph breaks and the original sweeping, realist tone. "
        "Do NOT skip or summarize any content. "
        "Do not add commentary — output only the English translation."
    ),
    chapter_context="Epic novel about coir workers in Kerala across generations. May have parts and chapters.",
    annotation_prompt=(
        'You are a literary analyst helping annotate an English translation of "Kayar" (Coir, 1978), '
        "an epic novel by Thakazhi Sivasankara Pillai about coir workers in Kerala. "
        "The translation preserves many Malayalam/Tamil terms and local vocabulary.\n\n"
        "For the given chapter text, extract three categories of terms that a modern English reader might want explained:\n\n"
        '1. **Characters** — Recurring named people. Give a 1-2 sentence description of who they are and their role.\n'
        '2. **Proper nouns** — Place names, caste names, festival names, cultural terms, etc. Give a brief explanation.\n'
        '3. **Vocabulary** — Archaic, vernacular, or culturally-specific words/phrases (e.g., "coir", "toddy", "backwater") that might be unfamiliar. Give a brief definition.\n\n'
        "Rules:\n"
        "- Only extract terms that actually appear in the chapter text (exact spelling match).\n"
        "- For character names, use the exact form that appears in the text.\n"
        "- Keep descriptions concise: 1-2 sentences max.\n"
        "- Do NOT extract common English words.\n"
        "- Focus on terms that are clearly Malayalam/Tamil/Indian in origin, or specific to Kerala backwater communities.\n"
        "- Return valid JSON only, no markdown fences."
    ),
    image_style_prefix=(
        "Generate an image in the style of a Kerala mural painting — "
        "deep green, rich gold, warm ochre, temple painting style. "
        "The composition should feel like a traditional Kerala wall painting — "
        "detailed figures, lush tropical vegetation, flowing water. "
        "No text, no lettering, no words anywhere in the image. "
        "Kerala backwaters setting with coconut palms, coir workers, houseboats, and lush greenery.\n\nScene: "
    ),
    characters_description=(
        "Key characters:\n"
        "- Common people: coir workers, fishermen, and farming families of the Kerala backwaters\n"
        "- Setting features: coconut groves, coir-making huts, backwater canals, rice paddies\n"
    ),
    character_style_prefix=(
        "Generate an image in the style of a Kerala mural painting — "
        "deep green, rich gold, warm ochre, temple painting style. "
        "The style should feel like a traditional Kerala wall painting — "
        "detailed character study with tropical elements. "
        "No text, no lettering, no words anywhere in the image. "
        "Kerala backwaters setting.\n\n"
    ),
    hero_prompt=(
        "Generate an edge-to-edge illustration in Kerala mural painting style "
        "with deep green, gold, and ochre palette. "
        "Kerala backwaters: tall coconut palms swaying over calm canals, "
        "coir workers spinning rope on the shore, traditional houseboats (kettuvallam), "
        "lush tropical greenery, warm golden light filtering through the palms. "
        "Bright, vivid, saturated colors. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
))


# ── Ghare Baire ───────────────────────────────────────────────────────────

_register(BookConfig(
    id="ghare-baire",
    title="The Home and the World",
    transliterated_title="Ghare Baire",
    original_title="ঘরে বাইরে",
    author_id="rabindranath-tagore",
    author_name="Rabindranath Tagore",
    author_years="1861–1941",
    original_language="Bengali",
    original_script="Bengali",
    original_year=1916,
    genre=["Literary Fiction", "Political Novel"],
    accent_color="#8B4513",
    style_context="Bengali novel about Swadeshi movement, nationalism vs. personal relationships",
    translation_prompt=(
        "You are translating a Bengali novel titled 'Ghare Baire' "
        "(ঘরে বাইরে, The Home and the World) by Rabindranath Tagore, first published in 1916. "
        "This is one of Tagore's most celebrated novels, set during the Swadeshi movement "
        "in early 20th-century Bengal. It explores the triangle between the idealistic "
        "landlord Nikhilesh, the fiery nationalist Sandip, and Nikhilesh's wife Bimala, "
        "who is drawn between domestic life and the intoxication of the political movement. "
        "The novel is narrated in turns by all three characters. "
        "Preserve Bengali proper nouns (character names, place names, cultural terms). "
        "Translate into fluent, literary English. Preserve paragraph breaks and the "
        "original introspective, philosophical tone. Do NOT skip or summarize any content. "
        "Do not add commentary — output only the English translation."
    ),
    chapter_context=(
        "Bengali novel set during the Swadeshi movement. Three narrators: landlord Nikhilesh, "
        "nationalist Sandip, and Bimala. May have parts organized by narrator POV "
        "(Bimala's Story, Nikhilesh's Story, Sandip's Story) and numbered chapters within each."
    ),
    annotation_prompt=(
        'You are a literary analyst helping annotate an English translation of "Ghare Baire" '
        "(The Home and the World, 1916), a Bengali novel by Rabindranath Tagore set during the "
        "Swadeshi movement. The story is narrated by three characters: the idealistic landlord "
        "Nikhilesh, the fiery nationalist Sandip, and Nikhilesh's wife Bimala. The translation "
        "preserves many Bengali proper nouns, Swadeshi-era terms, and cultural vocabulary.\n\n"
        "For the given chapter text, extract three categories of terms that a modern English reader might want explained:\n\n"
        '1. **Characters** — Recurring named people. Give a 1-2 sentence description of who they are and their role.\n'
        '2. **Proper nouns** — Place names, cultural terms, historical references, Swadeshi movement terms, religious terms, etc. Give a brief explanation.\n'
        '3. **Vocabulary** — Archaic, vernacular, or culturally-specific words/phrases (e.g., "Bande Mataram", "swadeshi", "zenana") that might be unfamiliar. Give a brief definition.\n\n'
        "Rules:\n"
        "- Only extract terms that actually appear in the chapter text (exact spelling match).\n"
        "- For character names, use the exact form that appears in the text.\n"
        "- Keep descriptions concise: 1-2 sentences max.\n"
        "- Do NOT extract common English words.\n"
        "- Focus on terms that are clearly Bengali/Indian in origin, or specific to the Swadeshi movement and early 20th century Bengal.\n"
        "- Return valid JSON only, no markdown fences."
    ),
    image_style_prefix=(
        "Generate an image in the style of a Bengal School painting — "
        "soft watercolor washes, warm amber and sepia tones, touches of vermilion and gold. "
        "The composition should feel like an Abanindranath Tagore or Nandalal Bose painting — "
        "dreamlike, emotional, with flowing lines and lyrical beauty. "
        "No text, no lettering, no words anywhere in the image. "
        "Early 20th century Bengal setting: grand zamindar mansion, Swadeshi movement era, "
        "rural estates, political gatherings, intimate domestic spaces.\n\nScene: "
    ),
    characters_description=(
        "Key characters:\n"
        "- Nikhilesh: a gentle, idealistic Bengali zamindar (landlord), refined features, simple elegant clothing\n"
        "- Bimala: a beautiful young Bengali woman, Nikhilesh's wife, traditional sari, expressive eyes\n"
        "- Sandip: a charismatic, fiery Swadeshi leader, intense gaze, dramatic gestures, political orator\n"
    ),
    character_style_prefix=(
        "Generate an image in the style of a Bengal School painting — "
        "soft watercolor washes, warm amber and sepia tones, touches of vermilion and gold. "
        "The style should feel like an Abanindranath Tagore painting — "
        "dreamlike, emotional, detailed character study with lyrical beauty. "
        "No text, no lettering, no words anywhere in the image. "
        "Early 20th century Bengal setting.\n\n"
    ),
    hero_prompt=(
        "Generate an edge-to-edge illustration in Bengal School watercolor style "
        "with warm amber, sepia, vermilion, and gold palette. "
        "Early 20th century Bengal: a grand zamindar mansion with ornate balconies "
        "and courtyards, the Swadeshi movement unfurling — flags and banners in the distance, "
        "a serene river flowing past, lush Bengali countryside with palm trees and rice fields, "
        "warm golden afternoon light, clouds gathering on the horizon. "
        "NO people, NO figures. Pure landscape/architecture scenery. "
        "Bright, vivid, saturated colors. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
))


# ── Malegalalli Madumagalu ────────────────────────────────────────────────

_register(BookConfig(
    id="malegalalli-madumagalu",
    title="Malegalalli Madumagalu",
    transliterated_title="Malegalalli Madumagalu",
    original_title="ಮಲೆಗಳಲ್ಲಿ ಮದುಮಗಳು",
    author_id="kuvempu",
    author_name="Kuvempu",
    author_years="1904–1994",
    original_language="Kannada",
    original_script="Kannada",
    original_year=1967,
    genre=["Literary Fiction", "Nature Writing"],
    accent_color="#556B2F",
    style_context="Kannada novel set in the Western Ghats",
    translation_prompt=(
        "You are translating a Kannada novel titled 'Malegalalli Madumagalu' "
        "(ಮಲೆಗಳಲ್ಲಿ ಮದುಮಗಳು) by Kuvempu (K. V. Puttappa), first published in 1967. "
        "This is a masterpiece of Kannada literature set in the lush Western Ghats "
        "of Karnataka. It tells the story of a young bride in a remote coffee "
        "plantation community, exploring themes of nature, tradition, love, and "
        "social change. The novel is known for its vivid descriptions of the "
        "Western Ghats landscape. Preserve Kannada proper nouns and nature vocabulary. "
        "Translate into fluent, literary English. Preserve paragraph breaks and the "
        "original lyrical, nature-rich tone. Do NOT skip or summarize any content. "
        "Do not add commentary — output only the English translation."
    ),
    chapter_context="Kannada novel set in Western Ghats. Story of a bride in a coffee plantation community.",
    annotation_prompt="",  # Not yet processed
    image_style_prefix=(
        "Generate an image in the style of a Mysore painting — "
        "rich gold leaf, deep green, royal purple, ornate traditional South Indian style. "
        "The composition should feel like a classic Mysore illustration — "
        "detailed, elegant, with lush natural elements and fine ornamentation. "
        "No text, no lettering, no words anywhere in the image. "
        "Western Ghats of Karnataka setting with dense forests, coffee plantations, misty mountains.\n\nScene: "
    ),
    characters_description=(
        "Key characters:\n"
        "- A young bride adjusting to life in a remote Western Ghats community\n"
        "- Coffee plantation families, forest dwellers\n"
        "- Setting features: dense forests, coffee estates, mountain streams, mist-covered peaks\n"
    ),
    character_style_prefix=(
        "Generate an image in the style of a Mysore painting — "
        "rich gold leaf, deep green, royal purple, ornate traditional South Indian style. "
        "The style should feel like a classic Mysore illustration — "
        "elegant, detailed character study. "
        "No text, no lettering, no words anywhere in the image. "
        "Western Ghats of Karnataka setting.\n\n"
    ),
    hero_prompt="",  # Not yet processed
))

# Note: malegalalli-madumagalu is partially processed (OCR only), so some prompts are empty.


# ── Maitreyi ─────────────────────────────────────────────────────────────

_register(BookConfig(
    id="maitreyi",
    title="Bengal Nights",
    transliterated_title="Maitreyi",
    original_title="Maitreyi",
    author_id="mircea-eliade",
    author_name="Mircea Eliade",
    author_years="1907–1986",
    original_language="Romanian",
    original_script="Latin",
    original_year=1933,
    genre=["Autobiographical Fiction", "Romance"],
    accent_color="#8B4513",
    style_context="Semi-autobiographical novel about a forbidden love affair in 1930s colonial Calcutta",
    translation_prompt=(
        "You are translating a Romanian novel titled 'Maitreyi' (Bengal Nights) by Mircea Eliade, "
        "first published in 1933. This semi-autobiographical novel follows a young European scholar "
        "living in 1930s Calcutta who falls in love with the daughter of his Indian host, "
        "an engineer named Narendra Sen. The story explores the clash of cultures, forbidden love, "
        "and the exoticism of colonial India through European eyes. "
        "Preserve Romanian and Bengali proper nouns (character names, place names, Indian terms). "
        "Translate into fluent, literary English. Preserve paragraph breaks and the original "
        "introspective, lyrical tone. Do NOT skip or summarize any content. "
        "Do not add commentary — output only the English translation."
    ),
    chapter_context="Romanian autobiographical novel set in 1930s Calcutta. Chapters are numbered with Roman numerals (I, II, III, etc.).",
    annotation_prompt=(
        'You are a literary analyst helping annotate an English translation of "Maitreyi" (Bengal Nights, 1933), '
        "a semi-autobiographical novel by Mircea Eliade about a forbidden love affair in colonial Calcutta. "
        "The translation preserves many Romanian, Bengali, and Hindi terms.\n\n"
        "For the given chapter text, extract three categories of terms that a modern English reader might want explained:\n\n"
        '1. **Characters** — Recurring named people. Give a 1-2 sentence description of who they are and their role.\n'
        '2. **Proper nouns** — Place names, cultural terms, religious references, Bengali/Indian customs, etc. Give a brief explanation.\n'
        '3. **Vocabulary** — Archaic, vernacular, or culturally-specific words/phrases (e.g., "sahib", "dhoti", "puja") that might be unfamiliar. Give a brief definition.\n\n'
        "Rules:\n"
        "- Only extract terms that actually appear in the chapter text (exact spelling match).\n"
        "- For character names, use the exact form that appears in the text.\n"
        "- Keep descriptions concise: 1-2 sentences max.\n"
        "- Do NOT extract common English words.\n"
        "- Focus on terms that are clearly Romanian, Bengali, Hindi, or Sanskrit in origin, or specific to 1930s colonial Calcutta.\n"
        "- Return valid JSON only, no markdown fences."
    ),
    image_style_prefix=(
        "Generate an image in the style of Bengal School of Art — "
        "warm sepia tones, soft gold, muted indigo, and earthy browns. "
        "The composition should feel like a Nandalal Bose or Abanindranath Tagore painting — "
        "dreamy, atmospheric, with soft edges and rich textures. "
        "No text, no lettering, no words anywhere in the image. "
        "1930s colonial Calcutta setting with grand Bengali homes, tropical gardens, and monsoon light.\n\nScene: "
    ),
    characters_description=(
        "Key characters:\n"
        "- Allan (Alain): Young European man in his early 20s, lean build, light skin, Western clothing (linen suits, open collar), intellectual demeanor\n"
        "- Maitreyi: Beautiful young Bengali woman, dark eyes, long black hair, wears traditional saris, graceful and poetic\n"
        "- Narendra Sen: Middle-aged Bengali engineer, dignified, wears both Western suits and traditional dhoti-kurta, scholarly bearing\n"
        "- Chabu: Maitreyi's younger sister, small and curious, traditional Bengali girl's clothing\n"
        "- Lucien: French journalist, stocky, animated, always carrying a notebook or camera\n"
    ),
    character_style_prefix=(
        "Generate an image in the style of Bengal School of Art — "
        "warm sepia tones, soft gold, muted indigo, and earthy browns. "
        "The style should feel like a Nandalal Bose or Abanindranath Tagore painting — "
        "dreamy character portrait with atmospheric background. "
        "No text, no lettering, no words anywhere in the image. "
        "1930s colonial Calcutta setting.\n\n"
    ),
    hero_prompt=(
        "Generate an edge-to-edge illustration in Bengal School of Art style "
        "with warm sepia, soft gold, muted indigo, and earthy brown palette. "
        "A sweeping view of 1930s Calcutta: grand colonial-era Bengali mansion with pillared verandah, "
        "lush tropical garden with jasmine and bougainvillea, tall palms silhouetted against a monsoon sky, "
        "the Hooghly River visible in the distance with boats. "
        "NO people, NO figures. Pure landscape scenery. "
        "Bright, vivid, saturated colors. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
))


# ── Na Hanyate ──────────────────────────────────────────────────────────

_register(BookConfig(
    id="na-hanyate",
    title="It Does Not Die",
    transliterated_title="Na Hanyate",
    original_title="ন হন্যতে",
    author_id="maitreyi-devi",
    author_name="Maitreyi Devi",
    author_years="1914–1990",
    original_language="Bengali",
    original_script="Bengali",
    original_year=1974,
    genre=["Autobiographical Fiction", "Memoir"],
    accent_color="#722F37",
    style_context=(
        "Bengali autobiographical memoir, a response to Mircea Eliade's 'Bengal Nights'. "
        "Written in 1974, it recounts Maitreyi Devi's memories of her forbidden love affair "
        "with Romanian scholar Mircea Eliade in 1930s Calcutta, and their reunion in 1972. "
        "Dual timeline: 1972 present-day reflections and 1930 memories. "
        "Sahitya Akademi Award winner (1976)."
    ),
    translation_prompt=(
        "You are translating a Bengali memoir titled 'Na Hanyate' "
        "(ন হন্যতে, It Does Not Die) by Maitreyi Devi, first published in 1974. "
        "This is a Sahitya Akademi Award-winning autobiographical novel, written as a response "
        "to Mircea Eliade's 'Maitreyi' (Bengal Nights). The narrator is Maitreyi herself, "
        "looking back from 1972 on her forbidden love with the Romanian scholar Mircea "
        "in 1930s Calcutta. The book alternates between present-day (1972) reflections "
        "and vivid memories of her youth. Key characters: Maitreyi (narrator), Mircea "
        "(the Romanian scholar), Surendranath Dasgupta (her philosopher father), "
        "Shanti/Ma (her mother), and various family members. "
        "The pages have watermark text from 'www.MurchOna.org' and "
        "'suman_ahm@yahoo.com' — IGNORE and DO NOT translate these watermarks. "
        "Also ignore any lines of tildes (~~~~~~). "
        "Preserve Bengali proper nouns (character names, place names, cultural terms). "
        "Translate into fluent, literary English. Preserve paragraph breaks and the "
        "original intimate, reflective, emotionally rich tone. Do NOT skip or summarize any content. "
        "Do not add commentary — output only the English translation."
    ),
    chapter_context=(
        "Bengali autobiographical memoir with a dual timeline (1972 present, 1930s past). "
        "The book is a continuous narrative without explicit chapter divisions. "
        "Look for natural thematic breaks, time shifts (between 1930s and 1972), "
        "or significant scene changes to divide into chapters. "
        "The memoir begins on 1st September 1972 and moves between past and present."
    ),
    annotation_prompt=(
        'You are a literary analyst helping annotate an English translation of "Na Hanyate" '
        "(It Does Not Die, 1974), a Bengali autobiographical memoir by Maitreyi Devi about "
        "her forbidden love with Romanian scholar Mircea Eliade in 1930s Calcutta. "
        "The translation preserves many Bengali, Sanskrit, and Hindi terms.\n\n"
        "For the given chapter text, extract three categories of terms that a modern English reader might want explained:\n\n"
        '1. **Characters** — Recurring named people. Give a 1-2 sentence description of who they are and their role.\n'
        '2. **Proper nouns** — Place names, cultural terms, religious references, Bengali customs, literary references, etc. Give a brief explanation.\n'
        '3. **Vocabulary** — Archaic, vernacular, or culturally-specific words/phrases (e.g., "sannyasi", "ashram", "puja") that might be unfamiliar. Give a brief definition.\n\n'
        "Rules:\n"
        "- Only extract terms that actually appear in the chapter text (exact spelling match).\n"
        "- For character names, use the exact form that appears in the text.\n"
        "- Keep descriptions concise: 1-2 sentences max.\n"
        "- Do NOT extract common English words.\n"
        "- Focus on terms that are clearly Bengali, Sanskrit, Hindi, or Romanian in origin, or specific to 1930s Calcutta and Bengali culture.\n"
        "- Return valid JSON only, no markdown fences."
    ),
    image_style_prefix=(
        "Generate an image in the style of Bengal School of Art — "
        "soft watercolor washes with deep rose, warm ochre, twilight indigo, and muted gold tones. "
        "The composition should feel like an intimate Nandalal Bose painting — "
        "emotionally rich, contemplative, with flowing lines and poetic atmosphere. "
        "No text, no lettering, no words anywhere in the image. "
        "Settings alternate between 1930s colonial Calcutta (grand Bengali homes, gardens, verandahs) "
        "and 1970s scenes (university halls, European cities, airports).\n\nScene: "
    ),
    characters_description=(
        "Key characters:\n"
        "- Maitreyi (Amrita): Bengali woman, narrator — in 1930s: young, beautiful, dark eyes, long black hair, traditional saris; in 1970s: mature, dignified, still graceful\n"
        "- Mircea: Romanian scholar — in 1930s: young European man, lean, light skin, Western clothing; in 1970s: elderly, distinguished professor\n"
        "- Surendranath Dasgupta (Baba): Maitreyi's father, middle-aged Bengali philosopher, stern, scholarly, traditional dhoti-kurta\n"
        "- Shanti (Ma): Maitreyi's mother, gentle Bengali woman, traditional white sari\n"
    ),
    character_style_prefix=(
        "Generate an image in the style of Bengal School of Art — "
        "soft watercolor washes with deep rose, warm ochre, twilight indigo, and muted gold. "
        "The style should feel like an intimate Nandalal Bose painting — "
        "emotionally rich, contemplative character portrait. "
        "No text, no lettering, no words anywhere in the image. "
        "Bengali setting, 1930s or 1970s.\n\n"
    ),
    hero_prompt=(
        "Generate an edge-to-edge illustration in Bengal School of Art style "
        "with deep rose, warm ochre, twilight indigo, and muted gold palette. "
        "A Bengali mansion verandah at twilight — ornate wooden railings draped with jasmine vines, "
        "terracotta floor tiles, a writing desk with scattered papers and an old fountain pen, "
        "oil lamp casting warm glow, through the arches a garden with flowering krishnachura trees, "
        "evening sky with first stars appearing over distant Calcutta rooftops. "
        "NO people, NO figures. Pure interior/landscape scenery. "
        "Bright, vivid, saturated colors. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
))


# ── Byomkesh ──────────────────────────────────────────────────────────

_register(BookConfig(
    id="byomkesh",
    title="The Adventures of Byomkesh Bakshi",
    transliterated_title="Byomkesh Samagra",
    original_title="ব্যোমকেশ সমগ্র",
    author_id="sharadindu-bandyopadhyay",
    author_name="Sharadindu Bandyopadhyay",
    author_years="1899–1970",
    original_language="Bengali",
    original_script="Bengali",
    original_year=1932,
    genre=["Detective Fiction", "Mystery"],
    accent_color="#4A3728",
    style_context=(
        "Bengali detective fiction anthology — 32 stories featuring truth-seeker "
        "Byomkesh Bakshi and his friend/narrator Ajit Bandyopadhyay. Stories span "
        "1932–1970, set in colonial and post-independence Calcutta. "
        "Known for atmospheric mysteries, psychological insight, and vivid depictions "
        "of Bengali society across four decades."
    ),
    type="anthology",
    translation_prompt=(
        "You are translating a Bengali detective fiction anthology — 'Byomkesh Bakshi' stories "
        "by Sharadindu Bandyopadhyay. These are classic Bengali mystery stories set in colonial "
        "and post-independence Calcutta. The narrator is Ajit Bandyopadhyay, Byomkesh's friend. "
        "Translate the given Bengali OCR text into fluent, literary English. "
        "Preserve Bengali proper nouns, honorifics, and cultural terms. "
        "Maintain the narrator's first-person voice and period-appropriate tone. "
        "Output ONLY the English translation, no commentary."
    ),
    annotation_prompt=(
        'You are a literary analyst helping annotate an English translation of '
        '"The Adventures of Byomkesh Bakshi", '
        "a Bengali detective fiction anthology by Sharadindu Bandyopadhyay featuring "
        "truth-seeker Byomkesh Bakshi and his friend/narrator Ajit.\n\n"
        "For the given chapter text, extract three categories of terms:\n\n"
        '1. **Characters** — Recurring named people. 1-2 sentence description.\n'
        '2. **Proper nouns** — Place names, cultural terms, historical references. Brief explanation.\n'
        '3. **Vocabulary** — Culturally-specific words/phrases. Brief definition.\n\n'
        "Rules:\n"
        "- Only extract terms that actually appear in the chapter text (exact spelling match).\n"
        "- Keep descriptions concise: 1-2 sentences max.\n"
        "- Do NOT extract common English words.\n"
        "- Focus on Bengali, Hindi, or Indian-origin terms.\n"
        "- Return valid JSON only, no markdown fences."
    ),
    image_style_prefix=(
        "Generate an image in the style of 1930s–1940s Bengali book illustration — "
        "noir-influenced, moody ink washes with deep sepia, charcoal grey, "
        "muted amber, and flashes of deep crimson. "
        "The composition should feel like a classic pulp detective cover — "
        "atmospheric, shadowy, with dramatic chiaroscuro lighting. "
        "No text, no lettering, no words anywhere in the image. "
        "1930s–1960s Calcutta setting with narrow lanes, boarding houses, "
        "dim kerosene lamps, and colonial architecture.\n\nScene: "
    ),
    characters_description=(
        "Key characters:\n"
        "- Byomkesh Bakshi: young Bengali man in his 20s-30s, lean, sharp intelligent eyes, "
        "wears white dhoti-kurta, sometimes a shawl, cigarette smoker, contemplative demeanor\n"
        "- Ajit Bandyopadhyay: Byomkesh's close friend and narrator, similar age, "
        "loyal, observant, also wears dhoti-kurta, slightly stockier build\n"
        "- Satyabati: Byomkesh's wife (from later stories), beautiful Bengali woman, "
        "intelligent, wears traditional sari, strong-willed\n"
    ),
    character_style_prefix=(
        "Generate an image in the style of 1930s–1940s Bengali book illustration — "
        "noir-influenced, moody ink washes with deep sepia, charcoal grey, and muted amber. "
        "Atmospheric, shadowy character portrait with dramatic chiaroscuro. "
        "No text, no lettering, no words anywhere in the image. "
        "1930s–1960s Calcutta setting.\n\n"
    ),
    hero_prompt=(
        "Generate an edge-to-edge illustration in the style of 1930s–1940s Bengali book illustration — "
        "noir-influenced, moody ink washes with deep sepia, charcoal grey, muted amber, deep crimson. "
        "A moody 1940s Calcutta rooftop at dusk — terracotta terraces, clotheslines, "
        "chimney smoke, a kerosene lamp on a weathered table beside an open notebook, "
        "narrow lanes below with dim streetlights, colonial-era buildings silhouetted against darkening sky. "
        "NO people, NO figures. Pure atmospheric scenery. "
        "Bright, vivid, saturated colors. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
))

# ── Feluda ─────────────────────────────────────────────────────────────

_register(BookConfig(
    id="feluda",
    title="The Adventures of Feluda",
    transliterated_title="Feluda Samagra",
    original_title="ফেলুদা সমগ্র",
    author_id="satyajit-ray",
    author_name="Satyajit Ray",
    author_years="1921–1992",
    original_language="Bengali",
    original_script="Bengali",
    original_year=1965,
    genre=["Detective Fiction", "Mystery"],
    accent_color="#2E5A3C",
    style_context=(
        "Bengali detective fiction anthology — 31 stories featuring private investigator "
        "Prodosh C. Mitter (Feluda), his cousin Tapesh (Topshe), and thriller writer "
        "Lalmohan Ganguly (Jatayu). Stories span 1965–1992, set in Calcutta, Darjeeling, "
        "Lucknow, Varanasi, Rajasthan, London, Kathmandu, and other locations. "
        "Known for cerebral puzzles, witty banter, and vivid Indian settings."
    ),
    type="anthology",
    annotation_prompt=(
        'You are a literary analyst helping annotate an English translation of '
        '"The Adventures of Feluda", '
        "a Bengali detective fiction anthology by Satyajit Ray featuring private investigator "
        "Prodosh C. Mitter (Feluda), his cousin Tapesh (Topshe), and thriller writer "
        "Lalmohan Ganguly (Jatayu).\n\n"
        "For the given chapter text, extract three categories of terms:\n\n"
        '1. **Characters** — Recurring named people. 1-2 sentence description.\n'
        '2. **Proper nouns** — Place names, cultural terms, historical references. Brief explanation.\n'
        '3. **Vocabulary** — Culturally-specific words/phrases. Brief definition.\n\n'
        "Rules:\n"
        "- Only extract terms that actually appear in the chapter text (exact spelling match).\n"
        "- Keep descriptions concise: 1-2 sentences max.\n"
        "- Do NOT extract common English words.\n"
        "- Focus on Bengali, Hindi, or Indian-origin terms.\n"
        "- Return valid JSON only, no markdown fences."
    ),
    image_style_prefix=(
        "Generate an image in the style of Satyajit Ray's own illustrations — "
        "clean line work with watercolor washes, warm earth tones, "
        "amber, sepia, deep green, and dusty rose. "
        "The composition should feel like a classic mystery book illustration — "
        "atmospheric, cinematic, with dramatic lighting. "
        "No text, no lettering, no words anywhere in the image. "
        "Indian settings from the 1960s-1990s.\n\nScene: "
    ),
    characters_description=(
        "Key characters:\n"
        "- Feluda (Prodosh C. Mitter): tall, lean Bengali detective in his 30s, sharp features, "
        "intelligent eyes, typically wears kurta-pajama or safari suit\n"
        "- Topshe (Tapesh Ranjan Mitter): teenage boy, Feluda's cousin and narrator, "
        "earnest, curious expression\n"
        "- Jatayu (Lalmohan Ganguly): middle-aged, portly Bengali man, friendly round face, "
        "bespectacled, comic thriller writer\n"
    ),
    character_style_prefix=(
        "Generate an image in the style of Satyajit Ray's own illustrations — "
        "clean line work with watercolor washes, warm earth tones, "
        "amber, sepia, deep green. "
        "Atmospheric, cinematic character portrait. "
        "No text, no lettering, no words anywhere in the image. "
        "Indian setting, 1960s-1990s.\n\n"
    ),
    hero_prompt=(
        "Generate an edge-to-edge illustration in the style of Satyajit Ray's artwork — "
        "clean line work with watercolor washes, warm amber, sepia, and deep green palette. "
        "A moody Calcutta street scene at dusk — colonial-era buildings with ornate balconies, "
        "a yellow Ambassador taxi, old bookshops, narrow lanes with long shadows, "
        "a magnifying glass resting on a stack of old notebooks on a wooden desk in the foreground. "
        "NO people, NO figures. Pure atmospheric scenery. "
        "Bright, vivid, saturated colors. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
))


# ── Samskara ──────────────────────────────────────────────────────────

_register(BookConfig(
    id="samskara",
    title="Samskara",
    transliterated_title="Samskara",
    original_title="ಸಂಸ್ಕಾರ",
    author_id="u-r-ananthamurthy",
    author_name="U.R. Ananthamurthy",
    author_years="1932–2014",
    original_language="Kannada",
    original_script="Kannada",
    original_year=1965,
    genre=["Literary Fiction", "Social Criticism"],
    accent_color="#8B4513",
    style_context=(
        "A groundbreaking Kannada novel about Praneshacharya, a devout Brahmin scholar "
        "in an agrahara (Brahmin settlement) in rural Karnataka. When Naranappa, a rebellious "
        "Brahmin who defied caste norms, dies, the community faces a crisis — no one will "
        "perform his funeral rites (samskara). Praneshacharya's quest for an answer unravels "
        "his own beliefs. A searing critique of orthodoxy, caste, and moral hypocrisy. "
        "Considered a masterpiece of the Navya literary movement."
    ),
    translation_prompt=(
        "You are translating a Kannada novel 'Samskara' (1965) by U.R. Ananthamurthy. "
        "This is a landmark of modern Indian literature about a Brahmin community's moral "
        "crisis when a rebellious member dies. The novel explores caste rigidity, religious "
        "orthodoxy, and individual conscience in a South Indian agrahara (Brahmin settlement). "
        "Preserve Kannada/Sanskrit proper nouns, honorifics, and cultural/religious terms "
        "(agrahara, samskara, acharya, etc.). Translate into fluent, literary English. "
        "Maintain the introspective, philosophical tone. "
        "Output ONLY the English translation, no commentary."
    ),
    chapter_context=(
        "Novel about a Brahmin community's crisis in rural Karnataka. "
        "May have numbered chapters or sections."
    ),
    annotation_prompt=(
        'You are a literary analyst helping annotate an English translation of "Samskara" (1965), '
        "a Kannada novel by U.R. Ananthamurthy about a Brahmin community's moral crisis.\n\n"
        "For the given chapter text, extract three categories of terms:\n\n"
        '1. **Characters** — Recurring named people. 1-2 sentence description.\n'
        '2. **Proper nouns** — Place names, religious terms, caste terms, cultural references. Brief explanation.\n'
        '3. **Vocabulary** — Kannada/Sanskrit words, religious/ritual terms, archaic terms. Brief definition.\n\n'
        "Rules:\n"
        "- Only extract terms that actually appear in the chapter text (exact spelling match).\n"
        "- Keep descriptions concise: 1-2 sentences max.\n"
        "- Do NOT extract common English words.\n"
        "- Focus on Kannada, Sanskrit, or Indian-origin terms specific to Brahminical and South Indian culture.\n"
        "- Return valid JSON only, no markdown fences."
    ),
    image_style_prefix=(
        "Generate an image in the style of Mysore traditional painting — "
        "rich gold, deep red, earthy brown, temple art aesthetic. "
        "The composition should feel like a classical South Indian painting — "
        "detailed, ornate, atmospheric. "
        "No text, no lettering, no words anywhere in the image. "
        "Rural Karnataka setting — agrahara, temple, coconut groves, Western Ghats.\n\nScene: "
    ),
    characters_description=(
        "Key characters:\n"
        "- Praneshacharya: devout Brahmin scholar, middle-aged, ascetic appearance\n"
        "- Naranappa: rebellious Brahmin who defied caste norms, now deceased\n"
        "- Chandri: Naranappa's low-caste companion, beautiful and devoted\n"
    ),
    character_style_prefix=(
        "Generate an image in the style of Mysore traditional painting — "
        "rich gold, deep red, earthy brown, temple art aesthetic. "
        "Atmospheric character portrait in classical South Indian style. "
        "No text, no lettering, no words anywhere in the image. "
        "Rural Karnataka setting.\n\n"
    ),
    hero_prompt=(
        "Generate an edge-to-edge illustration in Mysore traditional painting style — "
        "rich gold, deep red, earthy brown palette. "
        "A South Indian agrahara (Brahmin settlement) at dawn — "
        "tiled-roof houses along a river, a stone temple with gopuram, "
        "coconut palms, morning mist over the Western Ghats, "
        "brass oil lamps glowing, sacred tulsi plant in a courtyard. "
        "NO people, NO figures. Pure atmospheric scenery. "
        "Bright, vivid, saturated colors. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
))

# ── Godan ────────────────────────────────────────────────────────────────

_register(BookConfig(
    id="godan",
    title="Godan",
    transliterated_title="Godan",
    original_title="गोदान",
    author_id="premchand",
    author_name="Munshi Premchand",
    author_years="1880–1936",
    original_language="Hindi",
    original_script="Devanagari",
    original_year=1936,
    genre=["Literary Fiction", "Social Realism"],
    accent_color="#B8860B",
    style_context=(
        "Premchand's magnum opus about Hori, a poor peasant farmer in colonial-era "
        "rural India, whose lifelong dream is to own a cow (godan means 'gift of a cow'). "
        "The novel paints a vivid portrait of village life — caste oppression, debt bondage, "
        "zamindari exploitation, and the dignity of the rural poor. Parallel urban plotlines "
        "follow educated characters like Mehta and Malti. Considered the greatest Hindi novel "
        "ever written, it is a searing critique of colonial and feudal India."
    ),
    translation_prompt=(
        "You are translating a Hindi novel 'Godan' (1936) by Munshi Premchand. "
        "This is the greatest Hindi novel — about Hori, a poor peasant farmer in colonial "
        "India whose lifelong dream is to own a cow. The novel depicts village life, caste "
        "oppression, zamindari exploitation, debt bondage, and the dignity of the rural poor. "
        "Preserve Hindi/Urdu proper nouns, honorifics, caste terms, and cultural references "
        "(zamindar, mahajan, panchayat, godan, etc.). Translate into fluent, literary English. "
        "Maintain Premchand's empathetic, realistic tone. "
        "Output ONLY the English translation, no commentary."
    ),
    chapter_context=(
        "Novel about peasant life in colonial India. "
        "Has numbered chapters (likely 30+). No parts."
    ),
    annotation_prompt=(
        'You are a literary analyst helping annotate an English translation of "Godan" (1936), '
        "a Hindi novel by Munshi Premchand about peasant life in colonial India.\n\n"
        "For the given chapter text, extract three categories of terms:\n\n"
        '1. **Characters** — Recurring named people. 1-2 sentence description.\n'
        '2. **Proper nouns** — Place names, caste terms, colonial-era references, cultural terms. Brief explanation.\n'
        '3. **Vocabulary** — Hindi/Urdu words, agricultural terms, feudal terms, archaic terms. Brief definition.\n\n'
        "Rules:\n"
        "- Only extract terms that actually appear in the chapter text (exact spelling match).\n"
        "- Keep descriptions concise: 1-2 sentences max.\n"
        "- Do NOT extract common English words.\n"
        "- Focus on Hindi, Urdu, or Indian-origin terms specific to rural and colonial Indian culture.\n"
        "- Return valid JSON only, no markdown fences."
    ),
    image_style_prefix=(
        "Generate an image in the style of Indian miniature painting meets Bengal School — "
        "warm earth tones, ochre, terracotta, golden wheat fields. "
        "The composition should feel like a classic Indian realist painting — "
        "detailed, emotive, atmospheric. "
        "No text, no lettering, no words anywhere in the image. "
        "Rural North India setting — thatched huts, bullock carts, fields, village lanes.\n\nScene: "
    ),
    characters_description=(
        "Key characters:\n"
        "- Hori: poor peasant farmer, weathered, dignified, middle-aged\n"
        "- Dhania: Hori's wife, strong-willed village woman\n"
        "- Gobar: Hori's son, young, restless, ambitious\n"
    ),
    character_style_prefix=(
        "Generate an image in the style of Indian miniature painting meets Bengal School — "
        "warm earth tones, ochre, terracotta, golden wheat. "
        "Atmospheric character portrait in classical Indian realist style. "
        "No text, no lettering, no words anywhere in the image. "
        "Rural North India setting.\n\n"
    ),
    hero_prompt=(
        "Generate an edge-to-edge illustration in Indian miniature painting meets Bengal School style — "
        "warm earth tones, ochre, terracotta, golden wheat palette. "
        "A North Indian village at dawn — "
        "thatched mud huts, a well, bullock carts, golden wheat fields stretching to the horizon, "
        "a neem tree in the foreground, distant smoke from cooking fires, "
        "a cow grazing peacefully in the morning light. "
        "NO people, NO figures. Pure atmospheric scenery. "
        "Bright, vivid, saturated colors. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
))
