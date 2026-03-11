"""Unified book configuration for the entire pipeline.

Consolidates 7 separate config dicts from 7 scripts into one BookConfig dataclass.
All file paths are derived from the canonical book ID — no hardcoded paths.
"""

from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
WEB_DATA_DIR = PROJECT_ROOT / "web" / "public" / "data"
SERVER_DATA_DIR = PROJECT_ROOT / "web" / "server-data"

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
    has_original_text: bool = False
    original_script: str = ""  # e.g., "Devanagari", "Bengali", "Tamil"

    # ── Book type ────────────────────────────────────────────────────────
    type: str = "book"  # "book" or "anthology"

    # ── Verse detection ───────────────────────────────────────────────────
    verse_detection: bool = False  # Mark numbered verses vs prose commentary

    # ── Section markers ──────────────────────────────────────────────────
    has_sections: bool = False
    section_pattern: str = ""  # regex with capture group for section number

    # ── Character portraits ──────────────────────────────────────────────
    num_character_portraits: int = 6  # Number of character portraits to generate

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

    # Server-data paths (for Next.js server-side reads)
    @property
    def server_book_dir(self) -> Path:
        return SERVER_DATA_DIR / "books" / self.id

    @property
    def server_chapters_json(self) -> Path:
        return self.server_book_dir / "chapters.json"

    @property
    def server_original_chapters_json(self) -> Path:
        return self.server_book_dir / "chapters_original.json"


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

# ── Devdas ──────────────────────────────────────────────────────────────

_register(BookConfig(
    id="devdas",
    title="Devdas",
    transliterated_title="Devdas",
    original_title="দেবদাস",
    author_id="sarat-chandra-chattopadhyay",
    author_name="Sarat Chandra Chattopadhyay",
    author_years="1876–1938",
    original_language="Bengali",
    original_script="Bengali",
    original_year=1917,
    genre=["Literary Fiction", "Romance", "Tragedy"],
    accent_color="#8B0000",
    style_context=(
        "Sarat Chandra Chattopadhyay's classic Bengali novella about Devdas, a young man from "
        "a wealthy rural Bengali family who is in love with his childhood friend Parvati (Paro). "
        "When his family refuses the match due to caste differences, Devdas spirals into "
        "alcoholism and self-destruction. He befriends Chandramukhi, a courtesan with a heart "
        "of gold. The story is a tragic meditation on love, class, and self-destructive pride. "
        "Set in early 20th century rural and urban Bengal."
    ),
    translation_prompt=(
        "You are translating a Bengali novella 'Devdas' (1917) by Sarat Chandra Chattopadhyay. "
        "This is a classic tragic love story about Devdas, a wealthy young man, and his childhood "
        "love Parvati (Paro). The story follows his descent into alcoholism after family opposes "
        "the match. Preserve Bengali proper nouns, honorifics, and cultural references "
        "(babu, didi, thakur, zamindar, etc.). Translate into fluent, literary English. "
        "Maintain the melancholic, introspective tone. "
        "Output ONLY the English translation, no commentary."
    ),
    chapter_context=(
        "Short Bengali novella about tragic love. "
        "Has numbered chapters (likely 10-15 short chapters). No parts."
    ),
    annotation_prompt=(
        'You are a literary analyst helping annotate an English translation of "Devdas" (1917), '
        "a Bengali novella by Sarat Chandra Chattopadhyay about tragic love and self-destruction.\n\n"
        "For the given chapter text, extract three categories of terms:\n\n"
        '1. **Characters** — Recurring named people. 1-2 sentence description.\n'
        '2. **Proper nouns** — Place names, Bengali cultural terms, colonial-era references. Brief explanation.\n'
        '3. **Vocabulary** — Bengali words, honorifics, cultural terms, archaic terms. Brief definition.\n\n'
        "Rules:\n"
        "- Only extract terms that actually appear in the chapter text (exact spelling match).\n"
        "- Keep descriptions concise: 1-2 sentences max.\n"
        "- Do NOT extract common English words.\n"
        "- Focus on Bengali or Indian-origin terms specific to the cultural setting.\n"
        "- Return valid JSON only, no markdown fences."
    ),
    image_style_prefix=(
        "Generate an image in the style of Bengal School watercolor painting — "
        "soft washes, muted earth tones, sepia undertones, atmospheric and melancholic. "
        "Evokes the work of Abanindranath Tagore and Nandalal Bose. "
        "No text, no lettering, no words anywhere in the image. "
        "Early 20th century Bengal setting — colonial mansions, village paths, monsoon skies.\n\nScene: "
    ),
    characters_description=(
        "Key characters:\n"
        "- Devdas: handsome young Bengali man from wealthy zamindar family, brooding, self-destructive\n"
        "- Parvati (Paro): beautiful, spirited village girl, Devdas's childhood love\n"
        "- Chandramukhi: courtesan, compassionate, devoted to Devdas\n"
    ),
    character_style_prefix=(
        "A Bengal School watercolor portrait — soft washes, muted earth tones, "
        "sepia undertones, atmospheric and melancholic. "
        "Evokes early 20th century Bengali art tradition. "
        "No text, no lettering, no words anywhere in the image.\n\n"
    ),
    hero_prompt=(
        "Generate an edge-to-edge illustration in Bengal School watercolor style — "
        "soft washes, muted earth tones, sepia and indigo palette. "
        "A Bengal village at dusk — "
        "a colonial-era mansion with pillared veranda, a path lined with palm trees, "
        "monsoon clouds gathering over rice paddies, a river in the distance, "
        "oil lamps glowing in the twilight, fireflies in the evening air. "
        "NO people, NO figures. Pure atmospheric scenery. "
        "Moody, melancholic, romantic atmosphere. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
))

# ── Autobiography of a Yogi ─────────────────────────────────────────────

_register(BookConfig(
    id="autobiography-of-a-yogi",
    title="Autobiography of a Yogi",
    transliterated_title="Autobiography of a Yogi",
    original_title="Autobiography of a Yogi",
    author_id="paramahansa-yogananda",
    author_name="Paramahansa Yogananda",
    author_years="1893–1952",
    original_language="English",
    original_script="Latin",
    original_year=1946,
    genre=["Spiritual", "Autobiography", "Philosophy"],
    accent_color="#C77D2A",
    style_context=(
        "A spiritual classic by Paramahansa Yogananda, founder of Self-Realization Fellowship. "
        "Chronicles his life from childhood in India through his years with his guru Sri Yukteswar, "
        "encounters with saints and yogis, founding of yoga schools, and his mission to bring "
        "yoga and meditation to the West. Blends personal narrative with Hindu philosophy, "
        "miracles, and the science of Kriya Yoga. One of the most influential spiritual books "
        "of the 20th century."
    ),
    translation_prompt="",
    chapter_context=(
        "Spiritual autobiography with 48 numbered chapters. "
        "Chapters have descriptive titles."
    ),
    annotation_prompt=(
        'You are a literary analyst helping annotate "Autobiography of a Yogi" (1946), '
        "a spiritual autobiography by Paramahansa Yogananda.\n\n"
        "For the given chapter text, extract three categories of terms:\n\n"
        '1. **Characters** — Recurring named people (saints, gurus, historical figures). 1-2 sentence description.\n'
        '2. **Proper nouns** — Places, ashrams, organizations, scriptures, spiritual concepts. Brief explanation.\n'
        '3. **Vocabulary** — Sanskrit/Hindi/Bengali spiritual terms, yoga terminology. Brief definition.\n\n'
        "Rules:\n"
        "- Only extract terms that actually appear in the chapter text (exact spelling match).\n"
        "- Keep descriptions concise: 1-2 sentences max.\n"
        "- Do NOT extract common English words.\n"
        "- Focus on Indian spiritual, philosophical, and yogic terms.\n"
        "- Return valid JSON only, no markdown fences."
    ),
    image_style_prefix=(
        "Generate an image in the style of classical Indian spiritual art — "
        "soft golden light, warm saffron and ochre tones, ethereal atmosphere. "
        "The composition should feel serene, mystical, and transcendent. "
        "No text, no lettering, no words anywhere in the image. "
        "Settings: Indian ashrams, Himalayan landscapes, meditation halls, temples.\n\nScene: "
    ),
    characters_description=(
        "Key characters:\n"
        "- Paramahansa Yogananda: young Indian spiritual seeker, later a monk with long dark hair\n"
        "- Sri Yukteswar: Yogananda's guru, elderly Bengali sage with serene expression\n"
        "- Lahiri Mahasaya: revered 19th century yogi, householder-saint\n"
    ),
    character_style_prefix=(
        "Generate an image in the style of classical Indian spiritual art — "
        "soft golden light, warm saffron and ochre tones, ethereal atmosphere. "
        "Serene character portrait with mystical quality. "
        "No text, no lettering, no words anywhere in the image.\n\n"
    ),
    hero_prompt=(
        "Generate an edge-to-edge illustration in classical Indian spiritual art style — "
        "soft golden light, warm saffron, ochre, and deep blue palette. "
        "A peaceful Indian ashram at sunrise — "
        "whitewashed buildings with arched doorways, a meditation garden with lotus pond, "
        "Himalayan peaks in the distance, morning mist, sacred banyan tree, "
        "oil lamps glowing softly, marigold garlands. "
        "NO people, NO figures. Pure atmospheric scenery. "
        "Ethereal, mystical, serene. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
))

# ── The Discovery of India ────────────────────────────────────────────────

_register(BookConfig(
    id="discovery-of-india",
    title="The Discovery of India",
    transliterated_title="The Discovery of India",
    original_title="The Discovery of India",
    author_id="jawaharlal-nehru",
    author_name="Jawaharlal Nehru",
    author_years="1889–1964",
    original_language="English",
    original_script="Latin",
    original_year=1946,
    genre=["History", "Philosophy", "Autobiography"],
    accent_color="#2E5A4C",
    style_context=(
        "A sweeping historical and philosophical work written by Jawaharlal Nehru "
        "during his imprisonment at Ahmadnagar Fort (1942–1946). The book traces India's "
        "history from the Indus Valley Civilization through the struggle for independence, "
        "weaving together personal memoir, political philosophy, cultural analysis, and "
        "historical narrative. Nehru explores Indian civilization, its continuity and change, "
        "its encounters with other cultures, and the rise of the nationalist movement. "
        "Written in elegant, reflective English prose."
    ),
    translation_prompt="",
    chapter_context=(
        "Historical-philosophical work with 10 numbered chapters, each with many sub-sections. "
        "Chapters have titles like 'Ahmadnagar Fort', 'The Discovery of India', 'Through the Ages'. "
        "Sub-sections within chapters cover specific topics (e.g., 'The Indus Valley Civilization', "
        "'The Vedas', 'Buddha's Teaching'). Written in prison during 1942-1946."
    ),
    annotation_prompt=(
        'You are a literary analyst helping annotate "The Discovery of India" (1946), '
        "a historical and philosophical work by Jawaharlal Nehru.\n\n"
        "For the given chapter text, extract three categories of terms:\n\n"
        '1. **Characters** — Historical figures, political leaders, scholars mentioned. 1-2 sentence description.\n'
        '2. **Proper nouns** — Places, kingdoms, empires, texts, cultural concepts, political movements. Brief explanation.\n'
        '3. **Vocabulary** — Sanskrit/Hindi/Urdu terms, historical terminology, philosophical concepts. Brief definition.\n\n'
        "Rules:\n"
        "- Only extract terms that actually appear in the chapter text (exact spelling match).\n"
        "- Keep descriptions concise: 1-2 sentences max.\n"
        "- Do NOT extract common English words.\n"
        "- Focus on Indian historical, cultural, philosophical, and political terms.\n"
        "- Return valid JSON only, no markdown fences."
    ),
    image_style_prefix=(
        "Generate an image in the style of Indian modernist art — "
        "reminiscent of Amrita Sher-Gil and Nandalal Bose, with warm earth tones, "
        "deep saffron, terracotta, forest green, and indigo. "
        "The composition should feel historically evocative, dignified, and contemplative. "
        "No text, no lettering, no words anywhere in the image. "
        "Settings: ancient Indian cities, Mughal courts, temples, prison cells, "
        "freedom struggle scenes, village life, landscapes of India.\n\nScene: "
    ),
    characters_description=(
        "Key characters:\n"
        "- Jawaharlal Nehru: the narrator, Indian freedom fighter and intellectual, middle-aged, refined, in prison garb or Indian formal wear\n"
        "- Mahatma Gandhi: elderly Indian leader, thin, bald, in white dhoti, iconic round spectacles\n"
        "- Kamala Nehru: Nehru's wife, young Indian woman, delicate features, traditional sari\n"
        "- Indira: Nehru's daughter, young Indian woman\n"
    ),
    character_style_prefix=(
        "Generate an image in the style of Indian modernist art — "
        "warm earth tones, deep saffron, terracotta, forest green, and indigo. "
        "Dignified, historically evocative character portrait. "
        "No text, no lettering, no words anywhere in the image.\n\n"
    ),
    hero_prompt=(
        "Generate an edge-to-edge illustration in Indian modernist art style — "
        "warm earth tones, deep saffron, terracotta, forest green, and indigo palette. "
        "Ahmadnagar Fort at twilight — massive stone walls and battlements, "
        "a writing desk by a barred window overlooking vast Indian plains, "
        "scattered books and manuscripts, an oil lamp casting warm light, "
        "distant view of ancient temples and village silhouettes against a dramatic sunset sky. "
        "NO people, NO figures. Pure interior/landscape scenery. "
        "Historically evocative, contemplative, dignified. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
))


# ── Bhagavad Gita (Chinmayananda) ────────────────────────────────────────

_register(BookConfig(
    id="bhagavad-gita",
    title="Bhagavad Gita",
    transliterated_title="Bhagavad Gita",
    original_title="The Holy Geeta",
    author_id="swami-chinmayananda",
    author_name="Swami Chinmayananda",
    author_years="1916–1993",
    original_language="Sanskrit",
    original_script="Devanagari",
    original_year=1969,
    genre=["Philosophy", "Spirituality", "Commentary"],
    accent_color="#B8860B",
    verse_detection=True,
    style_context=(
        "A comprehensive commentary on the Bhagavad Gita by Swami Chinmayananda, "
        "one of the most influential Vedanta teachers of the 20th century. "
        "The text alternates between translated Sanskrit verses of the Gita and "
        "extensive philosophical commentary explaining each verse. "
        "Set on the battlefield of Kurukshetra, the dialogue between Lord Krishna "
        "and the warrior Arjuna covers duty, devotion, knowledge, and liberation."
    ),
    translation_prompt="",
    chapter_context=(
        "The Bhagavad Gita has 18 chapters, each called a 'Yoga'. "
        "Chapter titles include: Arjuna Vishada Yoga, Sankhya Yoga, Karma Yoga, "
        "Jnana Karma Sanyasa Yoga, etc. Each chapter contains numbered verses "
        "with speaker attributions (The Blessed Lord said, Arjuna said, Sanjaya said) "
        "followed by philosophical commentary."
    ),
    annotation_prompt=(
        'You are a literary analyst helping annotate "The Holy Geeta" (1969), '
        "a commentary on the Bhagavad Gita by Swami Chinmayananda.\n\n"
        "For the given chapter text, extract three categories of terms:\n\n"
        '1. **Characters** — Figures from the Mahabharata mentioned (Krishna, Arjuna, Dhritarashtra, etc.). 1-2 sentence description.\n'
        '2. **Proper nouns** — Places, texts, philosophical schools, dynasties. Brief explanation.\n'
        '3. **Vocabulary** — Sanskrit philosophical terms (dharma, karma, yoga, atman, brahman, etc.) and other Indian terms. Brief definition.\n\n'
        "Rules:\n"
        "- Only extract terms that actually appear in the chapter text (exact spelling match).\n"
        "- Keep descriptions concise: 1-2 sentences max.\n"
        "- Do NOT extract common English words.\n"
        "- Focus on Sanskrit, Vedantic, and Indian philosophical terminology.\n"
        "- Return valid JSON only, no markdown fences."
    ),
    image_style_prefix=(
        "A fusion of Japanese ukiyo-e woodblock print aesthetics with Rajput painting — "
        "dramatic flat color planes, strong compositional diagonals, stylized clouds and waves "
        "reimagined as Indian motifs, bold outlines with subtle color gradients, theatrical staging "
        "of mythological figures. No text. No frame-within-frame, no inset panels, single unified scene only."
        "\n\nScene: "
    ),
    characters_description=(
        "Key characters:\n"
        "- Lord Krishna: blue-skinned, wearing golden crown and yellow robes, serene and wise\n"
        "- Arjuna: warrior prince, athletic, wielding the Gandiva bow\n"
        "- Sanjaya: royal narrator, elderly, dignified\n"
        "- Dhritarashtra: blind old king, white-haired, anxious expression\n"
    ),
    character_style_prefix=(
        "A fusion of Japanese ukiyo-e woodblock print aesthetics with Rajput painting — "
        "dramatic flat color planes, bold outlines with subtle color gradients. "
        "Ornate, devotional character portrait. "
        "No text, no lettering, no words anywhere in the image.\n\n"
    ),
    hero_prompt=(
        "A fusion of Japanese ukiyo-e woodblock print aesthetics with Rajput painting — "
        "dramatic flat color planes, strong compositional diagonals, bold outlines with subtle color gradients. "
        "A sweeping panoramic view of the battlefield of Kurukshetra at dawn — "
        "two vast armies facing each other across a wide plain, elephants and warriors in formation, "
        "golden sunrise illuminating the scene with dramatic rays of light, "
        "distant mountains and a sacred river, divine cosmic energy in the sky. "
        "NO text, NO border, NO frame. 16:9 cinematic landscape ratio."
    ),
))

# ── Panchatantra ─────────────────────────────────────────────────────────

_register(BookConfig(
    id="panchatantra",
    title="The Panchatantra",
    transliterated_title="Panchatantra",
    original_title="पञ्चतन्त्र",
    author_id="vishnu-sharma",
    author_name="Vishnu Sharma",
    author_years="c. 300 BCE",
    original_language="Sanskrit",
    original_year=-300,
    genre=["Fables", "Philosophy", "Folklore"],
    accent_color="#C4872F",
    style_context=(
        "Ancient Indian fable anthology — 87 animal fables and moral tales across five books, "
        "attributed to the scholar Vishnu Sharma. The stories use nested narratives with talking "
        "animals to teach political wisdom (niti) and practical conduct. Arthur Ryder's 1925 "
        "English verse-and-prose translation."
    ),
    type="anthology",
    annotation_prompt=(
        'You are a literary analyst helping annotate an English translation of '
        '"The Panchatantra", an ancient Sanskrit collection of animal fables '
        "attributed to Vishnu Sharma (c. 300 BCE). Arthur Ryder's translation.\n\n"
        "For the given chapter text, extract three categories of terms:\n\n"
        '1. **Characters** — Named characters (animals or humans). 1-2 sentence description.\n'
        '2. **Proper nouns** — Place names, kingdom names, Sanskrit terms, Indian cultural references. Brief explanation.\n'
        '3. **Vocabulary** — Archaic English, Sanskrit-origin, or culturally-specific words/phrases. Brief definition.\n\n'
        "Rules:\n"
        "- Only extract terms that actually appear in the chapter text (exact spelling match).\n"
        "- Keep descriptions concise: 1-2 sentences max.\n"
        "- Do NOT extract common English words.\n"
        "- Focus on Sanskrit, Indian-origin, or archaic terms.\n"
        "- Return valid JSON only, no markdown fences."
    ),
    image_style_prefix=(
        "Generate an image in the style of a traditional Indian miniature painting — "
        "vivid jewel-toned gouache colors, gold accents, intricate patterning, "
        "flat perspective with layered composition. "
        "Lush Indian forest and palace settings with ornate architectural details. "
        "Animals should be expressive and anthropomorphized in the Indian folk art tradition. "
        "No text, no lettering, no words anywhere in the image. "
        "Ancient India setting with tropical forests, lotus ponds, and sandstone palaces.\n\nScene: "
    ),
    characters_description=(
        "Key recurring characters (vary by story):\n"
        "- Various talking animals: lions, jackals, crows, owls, mice, turtles, deer, monkeys\n"
        "- Brahmans: traditional Indian scholars in white dhoti, sacred thread\n"
        "- Kings: ornate Indian royal attire, crowns, seated on thrones\n"
        "- Merchants: prosperous Indian traders in fine cotton garments\n"
    ),
    character_style_prefix=(
        "A traditional Indian miniature painting portrait — "
        "vivid jewel-toned gouache, gold leaf accents, ornate decorative border. "
        "Expressive character portrait in the Rajput/Mughal miniature tradition. "
        "No text, no lettering, no words anywhere in the image.\n\n"
    ),
    hero_prompt=(
        "A traditional Indian miniature painting — vivid jewel-toned gouache colors, "
        "gold leaf accents, intricate floral borders. "
        "A sweeping panoramic scene of an ancient Indian forest clearing — "
        "a wise old Brahman scholar seated under a grand banyan tree, surrounded by "
        "attentive animal listeners: a lion, a jackal, a crow, a turtle, and a deer. "
        "Lush tropical vegetation, lotus pond, distant sandstone palace. "
        "Warm golden light filtering through the canopy. "
        "NO text, NO border, NO frame. 16:9 cinematic landscape ratio."
    ),
))


# ── Pather Panchali (Bibhutibhushan Bandyopadhyay) ──────────────────────
_register(BookConfig(
    id="pather-panchali",
    title="Pather Panchali",
    transliterated_title="Pather Panchali",
    original_title="পথের পাঁচালী",
    author_id="bibhutibhushan-bandyopadhyay",
    author_name="Bibhutibhushan Bandyopadhyay",
    author_years="1894–1950",
    original_language="Bengali",
    original_script="Bengali",
    original_year=1929,
    genre=["Novel", "Coming-of-age", "Literary Fiction"],
    accent_color="#4A7C59",
    style_context=(
        "A Bengali novel set in rural Bengal in the early 20th century. "
        "The story follows young Apu and his family — his sister Durga, his mother Sarbajaya, "
        "and his father Horihor, a poor Brahmin priest — through their daily struggles, "
        "joys, and sorrows in the village of Nishchindipur. Rich in nature imagery, "
        "childhood wonder, and the textures of village life. "
        "Made iconic by Satyajit Ray's 1955 film adaptation."
    ),
    translation_prompt=(
        "Translate from Bengali to English. Maintain the lyrical, evocative prose style "
        "of the original. Preserve the sense of childhood wonder, the vivid descriptions "
        "of rural Bengal's nature and seasons. Keep Bengali terms of address "
        "(didi, dada, mashi, etc.) and cultural terms with brief context where needed. "
        "Do NOT omit, summarize, or merge any content."
    ),
    chapter_context=(
        "Bengali novel with 35 chapters (পরিচ্ছেদ). Chapters are numbered in Bengali ordinals: "
        "প্রথম পরিচ্ছেদ (1st chapter), দ্বিতীয় পরিচ্ছেদ (2nd), etc. "
        "The novel is divided into three parts: "
        "বল্লালী-বালাই (Ballali Balai — childhood/Durga's section), "
        "আম-আঁটির ভেঁপু (Aam Aantir Bhenpu — Apu's section), "
        "and অক্রূর সংবাদ (Akrur Sambad — departure)."
    ),
    annotation_prompt=(
        'You are a literary analyst helping annotate "Pather Panchali" (1929), '
        "a Bengali novel by Bibhutibhushan Bandyopadhyay.\n\n"
        "For the given chapter text, extract three categories of terms:\n\n"
        '1. **Characters** — People mentioned (Apu, Durga, Sarbajaya, Horihor, Indir Thakrun, etc.). 1-2 sentence description.\n'
        '2. **Proper nouns** — Villages, rivers, places, festivals, texts mentioned. Brief explanation.\n'
        '3. **Vocabulary** — Bengali cultural terms, food items, plants, rituals, kinship terms. Brief definition.\n\n'
        "Rules:\n"
        "- Only extract terms that actually appear in the chapter text (exact spelling match).\n"
        "- Keep descriptions concise: 1-2 sentences max.\n"
        "- Do NOT extract common English words.\n"
        "- Focus on Bengali cultural, social, and natural world terms.\n"
        "- Return valid JSON only, no markdown fences."
    ),
    image_style_prefix=(
        "Generate a warm, hand-drawn watercolor-style illustration. "
        "Soft colored pencil and ink wash look with earthy greens, warm ochres, "
        "terracotta browns, and gentle sky blues. "
        "Lush Bengal countryside setting — thatched huts, bamboo groves, "
        "ponds, rice paddies, banana trees, and wild flowers. "
        "Evocative, nostalgic, storybook quality. NOT photorealistic, NOT black-and-white. "
        "No text, no lettering, no words anywhere in the image. "
        "Edge-to-edge, no border, no frame, no margin.\n\nScene: "
    ),
    characters_description=(
        "Key characters:\n"
        "- Apu (Apurba): young Bengali boy, curious wide eyes, thin, wearing simple dhoti, eager innocent face\n"
        "- Durga: Apu's older sister, wild-haired Bengali girl, mischievous smile, thin, wearing simple sari\n"
        "- Sarbajaya: their mother, careworn Bengali woman, thin face, in white cotton sari, stern but loving\n"
        "- Horihor: their father, gentle Bengali Brahmin, thin, sacred thread, simple dhoti-kurta, kind eyes\n"
        "- Indir Thakrun: elderly great-aunt, very old and frail, hunched, in tattered white sari\n"
    ),
    character_style_prefix=(
        "Generate an image in the style of Satyajit Ray's cinema — "
        "soft natural light, earthy tones, contemplative mood. "
        "Realistic character portrait set in rural Bengal. "
        "No text, no lettering, no words anywhere in the image.\n\n"
    ),
    hero_prompt=(
        "Generate an edge-to-edge illustration in the style of Satyajit Ray's Pather Panchali — "
        "soft golden afternoon light filtering through a bamboo grove in rural Bengal. "
        "A narrow dirt path winds through lush green vegetation — banana trees, "
        "wild flowers, a shimmering pond with water lilies in the background. "
        "Thatched mud huts visible through the trees. Monsoon clouds gathering. "
        "The textures of village Bengal — earthy, verdant, alive with nature. "
        "NO people, NO figures. Pure landscape/setting. "
        "Poetic, contemplative, nostalgic. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
))

# ── Crime and Punishment ─────────────────────────────────────────────────

_register(BookConfig(
    id="crime-and-punishment",
    title="Crime and Punishment",
    transliterated_title="Crime and Punishment",
    original_title="Преступление и наказание",
    author_id="fyodor-dostoevsky",
    author_name="Fyodor Dostoevsky",
    author_years="1821–1881",
    original_language="Russian",
    original_year=1866,
    genre=["Psychological Fiction", "Novel"],
    accent_color="#4A3728",
    style_context=(
        "A psychological novel set in 1860s St. Petersburg, Russia. Follows impoverished ex-student "
        "Raskolnikov who commits murder and grapples with guilt, morality, and redemption. "
        "Constance Garnett English translation. Dense psychological prose, Russian names and patronymics."
    ),
    annotation_prompt=(
        'You are a literary analyst helping annotate an English translation of "Crime and Punishment" (1866) '
        "by Fyodor Dostoevsky, translated by Constance Garnett.\n\n"
        "For the given chapter text, extract three categories of terms that a modern English reader might want explained:\n\n"
        '1. **Characters** — Recurring named people. Give a 1-2 sentence description of who they are and their role. '
        'Note: Russian characters have multiple name forms (full name, patronymic, diminutive). Group these together.\n'
        '2. **Proper nouns** — Place names (streets, bridges, cities), institutions, Russian cultural terms, legal terms, etc. Brief explanation.\n'
        '3. **Vocabulary** — Russian/archaic/culturally-specific words or phrases (e.g., "samovar", "kopeck", "verst") that might be unfamiliar. Brief definition.\n\n'
        "Rules:\n"
        "- Only extract terms that actually appear in the chapter text (exact spelling match).\n"
        "- Keep descriptions concise: 1-2 sentences max.\n"
        "- Do NOT extract common English words.\n"
        "- Focus on Russian names, places, currency, social customs, and 19th-century terms.\n"
        "- Return valid JSON only, no markdown fences."
    ),
    image_style_prefix=(
        "Generate an image in the style of 19th-century Russian realist painting — "
        "dark, moody atmosphere, muted earth tones, dramatic chiaroscuro lighting. "
        "Settings: cramped St. Petersburg rooms, foggy streets, dim taverns, bridges over canals. "
        "No text, no lettering, no words anywhere in the image. "
        "Edge-to-edge, no border, no frame, no margin.\n\nScene: "
    ),
    characters_description=(
        "Key characters:\n"
        "- Raskolnikov (Rodion Romanovich): gaunt young Russian man, pale, dark eyes, shabby student clothes, intense brooding expression\n"
        "- Sonia (Sofya Semyonovna Marmeladov): young woman, thin, fair hair, gentle suffering face, modest simple dress\n"
        "- Porfiry Petrovitch: middle-aged Russian detective, round face, shrewd intelligent eyes, slightly overweight\n"
        "- Svidrigailov (Arkady Ivanovich): well-dressed older man, handsome but unsettling, cold blue eyes\n"
        "- Razumihin (Dmitri Prokofych): tall strong young man, earnest open face, student clothes, warm-hearted\n"
        "- Dounia (Avdotya Romanovna): Raskolnikov's sister, beautiful dark-haired young woman, proud bearing\n"
    ),
    character_style_prefix=(
        "Generate an image in the style of 19th-century Russian realist painting — "
        "dark moody atmosphere, muted earth tones, dramatic lighting. "
        "Realistic character portrait set in 1860s St. Petersburg. "
        "No text, no lettering, no words anywhere in the image.\n\n"
    ),
    hero_prompt=(
        "Generate an edge-to-edge illustration in 19th-century Russian realist painting style — "
        "a moody view of 1860s St. Petersburg at dusk. "
        "Narrow cobblestone streets, tall yellow-grey apartment buildings with peeling facades, "
        "a canal with an arched stone bridge, gaslight lamps casting dim pools of light, "
        "fog rolling in from the Neva river, grey overcast sky with hints of sunset. "
        "Oppressive urban atmosphere, cramped and claustrophobic. "
        "NO people, NO figures. Pure atmospheric cityscape. "
        "Dark, brooding, intense. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
))

# ── The Brothers Karamazov ───────────────────────────────────────────────

# ── Ramayana ──────────────────────────────────────────────────────────────

_register(BookConfig(
    id="ramayana",
    title="Ramayana",
    transliterated_title="Ramayana",
    original_title="रामायण",
    author_id="valmiki",
    author_name="Valmiki",
    author_years="c. 5th century BCE",
    original_language="Sanskrit",
    original_year=-500,
    genre=["Epic Poetry", "Mythology"],
    accent_color="#D4451A",
    has_sections=True,
    section_pattern=r"^SECTION\s+([IVXLCDM]+)\.?$",
    style_context=(
        "The Ramayana is an ancient Indian epic poem attributed to the sage Valmiki. "
        "It narrates the life of Prince Rama of Ayodhya — his exile to the forest, "
        "the abduction of his wife Sita by the demon king Ravana, and the great war to rescue her. "
        "This is the Ralph T.H. Griffith English verse translation (1870-1874). "
        "Seven Kandas (books): Bālakāndam, Ayodhyākāndam, Āranyakāndam, Kishkindhākāndam, "
        "Sundarakāndam, Yuddhakāndam, Uttarakāndam. 656 sections total. "
        "Archaic Victorian English verse, Sanskrit names and terms throughout."
    ),
    annotation_prompt=(
        'You are a literary analyst helping annotate an English translation of the Ramayana, '
        "the ancient Sanskrit epic by Valmiki, translated into English verse by Ralph T.H. Griffith.\n\n"
        "For the given chapter text, extract three categories of terms that a modern English reader might want explained:\n\n"
        '1. **Characters** — Named people, gods, demons, sages, animals. Give a 1-2 sentence description of who they are and their role.\n'
        '2. **Proper nouns** — Place names, kingdoms, weapons, celestial objects, mythological references. Brief explanation.\n'
        '3. **Vocabulary** — Sanskrit terms, archaic English words, Vedic/Hindu religious terms that might be unfamiliar. Brief definition.\n\n'
        "Rules:\n"
        "- Only extract terms that actually appear in the chapter text (exact spelling match).\n"
        "- Keep descriptions concise: 1-2 sentences max.\n"
        "- Do NOT extract common English words.\n"
        "- Focus on Sanskrit names, mythological references, weapons, places, and archaic terms.\n"
        "- Return valid JSON only, no markdown fences."
    ),
    image_style_prefix=(
        "Generate an image blending classical Indian miniature painting with epic cinematic grandeur — "
        "rich jewel tones (deep royal blue, burnished gold, fiery orange-red, emerald green), "
        "gold leaf accents, ornate architecture, lush tropical landscapes. "
        "Dramatic cinematic lighting with god-rays, volumetric light, and epic scale. "
        "Hyper-detailed, mythological, awe-inspiring — like a scene from a massive blockbuster epic. "
        "Settings: royal palaces, dense forests, mythological battlefields, sacred rivers, celestial realms. "
        "No text, no lettering, no words anywhere in the image. "
        "Edge-to-edge, no border, no frame, no margin.\n\nScene: "
    ),
    characters_description=(
        "Key characters:\n"
        "- Rama: Prince of Ayodhya, dark-skinned, noble bearing, carries divine bow, wears royal garments and crown\n"
        "- Sita: Rama's wife, beautiful, graceful, traditional Indian jewelry and silk garments\n"
        "- Lakshmana: Rama's loyal younger brother, fair-skinned, warrior build, always by Rama's side\n"
        "- Hanuman: Vanara (monkey) warrior, powerful muscular build, devoted to Rama, carries mace\n"
        "- Ravana: Demon king of Lanka, ten heads, twenty arms, dark imposing figure, ornate demonic crown\n"
        "- Dasaratha: King of Ayodhya, Rama's father, elderly, regal, white beard, royal robes\n"
        "- Sugriva: Vanara king, golden-furred monkey warrior\n"
        "- Vibhishana: Ravana's righteous brother, noble demon, joins Rama's side\n"
    ),
    character_style_prefix=(
        "Generate an image in the style of classical Indian miniature painting — "
        "rich jewel tones, gold accents, ornate details. "
        "Realistic character portrait from the ancient Indian epic Ramayana. "
        "No text, no lettering, no words anywhere in the image.\n\n"
    ),
    hero_prompt=(
        "Generate an edge-to-edge illustration in classical Indian miniature painting style — "
        "a majestic view of the ancient city of Ayodhya at golden hour. "
        "Grand white marble palaces with golden domes, ornate pillars, "
        "the sacred Sarayu river flowing past, lush tropical gardens, "
        "distant mountains, warm golden sky with dramatic clouds. "
        "Atmospheric, mythological, vast Indian landscape. "
        "NO people, NO figures. Pure atmospheric landscape. "
        "Rich, jewel-toned, sacred. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
    type="book",
    verse_detection=True,
    num_character_portraits=14,
))


_register(BookConfig(
    id="brothers-karamazov",
    title="The Brothers Karamazov",
    transliterated_title="The Brothers Karamazov",
    original_title="Братья Карамазовы",
    author_id="fyodor-dostoevsky",
    author_name="Fyodor Dostoevsky",
    author_years="1821–1881",
    original_language="Russian",
    original_year=1880,
    has_original_text=True,
    original_script="Cyrillic",
    genre=["Philosophical Fiction", "Novel"],
    accent_color="#3B2F2F",
    style_context=(
        "A philosophical novel set in a provincial Russian town in the 1870s. "
        "Three brothers — the passionate Dmitri, the intellectual Ivan, and the spiritual Alyosha — "
        "are entangled in a murder mystery involving their dissolute father Fyodor Pavlovitch. "
        "Constance Garnett English translation. Dense dialogues, Russian names and patronymics, "
        "philosophical and theological debates."
    ),
    annotation_prompt=(
        'You are a literary analyst helping annotate an English translation of "The Brothers Karamazov" (1880) '
        "by Fyodor Dostoevsky, translated by Constance Garnett.\n\n"
        "For the given chapter text, extract three categories of terms that a modern English reader might want explained:\n\n"
        '1. **Characters** — Recurring named people. Give a 1-2 sentence description of who they are and their role. '
        'Note: Russian characters have multiple name forms (full name, patronymic, diminutive). Group these together.\n'
        '2. **Proper nouns** — Place names, institutions, Russian cultural terms, religious terms (monks, elders, monastery customs), legal terms, etc. Brief explanation.\n'
        '3. **Vocabulary** — Russian/archaic/culturally-specific words or phrases that might be unfamiliar. Brief definition.\n\n'
        "Rules:\n"
        "- Only extract terms that actually appear in the chapter text (exact spelling match).\n"
        "- Keep descriptions concise: 1-2 sentences max.\n"
        "- Do NOT extract common English words.\n"
        "- Focus on Russian names, places, currency, religious customs, and 19th-century terms.\n"
        "- Return valid JSON only, no markdown fences."
    ),
    image_style_prefix=(
        "Generate an image in the style of 19th-century Russian realist painting — "
        "warm but somber atmosphere, muted earth tones and deep shadows. "
        "Settings: Russian provincial town, monastery cells, grand drawing rooms, muddy country roads, taverns. "
        "No text, no lettering, no words anywhere in the image. "
        "Edge-to-edge, no border, no frame, no margin.\n\nScene: "
    ),
    characters_description=(
        "Key characters:\n"
        "- Fyodor Pavlovitch Karamazov: old dissolute Russian landowner, coarse features, thin lips, small shrewd eyes, buffoonish\n"
        "- Dmitri (Mitya) Karamazov: eldest son, 28, strong athletic build, dark-haired, passionate wild eyes, military bearing\n"
        "- Ivan Karamazov: second son, 24, tall lean intellectual, pale, dark brooding eyes, well-dressed\n"
        "- Alexey (Alyosha) Karamazov: youngest son, 20, handsome gentle face, dark eyes, modest monastic dress\n"
        "- Smerdyakov: illegitimate son/servant, pale sickly face, thin lips, cunning calculating expression\n"
        "- Grushenka (Agrafena Alexandrovna): beautiful young woman, full figure, dark curly hair, seductive eyes\n"
        "- Katerina Ivanovna: proud beautiful woman, dark hair, fierce determined expression, elegant dress\n"
        "- Father Zossima: elderly monk/elder, thin frail body, gentle wise eyes, monk's robes\n"
    ),
    character_style_prefix=(
        "Generate an image in the style of 19th-century Russian realist painting — "
        "warm somber atmosphere, muted earth tones, dramatic lighting. "
        "Realistic character portrait set in a 1870s Russian provincial town. "
        "No text, no lettering, no words anywhere in the image.\n\n"
    ),
    hero_prompt=(
        "Generate an edge-to-edge illustration in 19th-century Russian realist painting style — "
        "a moody view of a Russian provincial monastery at dusk. "
        "White stone walls, golden onion domes, old wooden buildings nearby, "
        "birch trees with golden autumn leaves, a muddy road leading to the monastery gate, "
        "grey overcast sky with hints of sunset, a few dim lanterns. "
        "Atmospheric, contemplative, vast Russian landscape. "
        "NO people, NO figures. Pure atmospheric landscape. "
        "Dark, brooding, spiritual. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
))


# ── The Mahabharata ──────────────────────────────────────────────────────

_register(BookConfig(
    id="mahabharata",
    title="Mahabharata",
    transliterated_title="Mahabharata",
    original_title="महाभारत",
    author_id="vyasa",
    author_name="Vyasa (tr. Kisari Mohan Ganguli)",
    author_years="c. 4th century BCE",
    original_language="Sanskrit",
    original_year=-400,
    genre=["Epic Poetry", "Mythology"],
    accent_color="#8B4513",
    has_sections=True,
    section_pattern=r"^Section\s+(\d+)$",
    style_context=(
        "The Mahabharata is the longest epic poem ever written, attributed to the sage Vyasa. "
        "It narrates the great Kurukshetra war between the Pandavas and Kauravas, "
        "encompassing vast philosophical, religious, and moral teachings. "
        "This is Kisari Mohan Ganguli's English prose translation (1883-1896). "
        "18 Parvas (books): Adi, Sabha, Vana, Virata, Udyoga, Bhishma, Drona, Karna, Shalya, "
        "Sauptika, Stri, Santi, Anusasana, Aswamedha, Asramavasika, Mausala, Mahaprasthanika, "
        "Svargarohanika. ~2.5 million words. Victorian-era English prose, Sanskrit names and terms throughout."
    ),
    annotation_prompt=(
        'You are a literary analyst helping annotate an English translation of the Mahabharata, '
        "the ancient Sanskrit epic by Vyasa, translated into English prose by Kisari Mohan Ganguli.\n\n"
        "For the given chapter text, extract three categories of terms that a modern English reader might want explained:\n\n"
        '1. **Characters** — Named people, gods, demons, sages, warriors. Give a 1-2 sentence description of who they are and their role.\n'
        '2. **Proper nouns** — Place names, kingdoms, weapons (astras), celestial objects, mythological references. Brief explanation.\n'
        '3. **Vocabulary** — Sanskrit terms, archaic English words, Vedic/Hindu religious terms that might be unfamiliar. Brief definition.\n\n'
        "Rules:\n"
        "- Only extract terms that actually appear in the chapter text (exact spelling match).\n"
        "- Keep descriptions concise: 1-2 sentences max.\n"
        "- Do NOT extract common English words.\n"
        "- Focus on Sanskrit names, mythological references, weapons, places, and archaic terms.\n"
        "- Return valid JSON only, no markdown fences."
    ),
    image_style_prefix=(
        "Generate an image in the style of classical Indian miniature painting — "
        "rich jewel tones, gold accents, epic battle scenes, ornate palaces, sacred rivers. "
        "Settings: royal courts, vast battlefields, forest hermitages, divine realms. "
        "No text, no lettering, no words anywhere in the image. "
        "Edge-to-edge, no border, no frame, no margin.\n\nScene: "
    ),
    characters_description=(
        "Key characters:\n"
        "- Krishna: Divine charioteer and guide, dark-skinned, peacock feather crown, yellow silk garments, serene smile\n"
        "- Arjuna: Greatest warrior among the Pandavas, handsome, athletic, divine bow Gandiva, royal armor\n"
        "- Bhima: Strongest of the Pandavas, massive powerful build, fierce expression, carries a mace\n"
        "- Yudhishthira: Eldest Pandava, calm dignified bearing, white robes, embodiment of dharma\n"
        "- Draupadi: Queen of the Pandavas, strikingly beautiful, dark hair, regal bearing, ornate jewelry\n"
        "- Duryodhana: Crown prince of the Kauravas, arrogant bearing, heavy golden armor, mace warrior\n"
        "- Bhishma: Grand patriarch, elderly but powerful, white hair and beard, celestial armor, carries a bow\n"
        "- Karna: Tragic hero, golden earrings and armor (kavach-kundal), noble bearing, sun-like radiance\n"
    ),
    character_style_prefix=(
        "Generate an image in the style of classical Indian miniature painting — "
        "rich jewel tones, gold accents, ornate details. "
        "Realistic character portrait from the ancient Indian epic Mahabharata. "
        "No text, no lettering, no words anywhere in the image.\n\n"
    ),
    hero_prompt=(
        "Generate an edge-to-edge illustration in classical Indian miniature painting style — "
        "a majestic panoramic view of the Kurukshetra battlefield at dawn. "
        "Vast plains stretching to the horizon, two massive armies facing each other, "
        "war elephants, chariots with fluttering banners, golden morning light, "
        "dramatic clouds in an orange-purple sky, distant mountains. "
        "Atmospheric, mythological, vast Indian epic landscape. "
        "NO people in foreground, NO close-up figures. Pure atmospheric landscape. "
        "Rich, jewel-toned, epic. 16:9 cinematic landscape ratio. "
        "NO text, NO border, NO frame."
    ),
    type="book",
    num_character_portraits=12,
))
