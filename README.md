# Grand Old Books

AI pipeline for bringing classical Indian literature to life: scanned PDFs of books in Hindi, Bengali, Tamil, and Telugu are OCR'd, translated to English, illustrated with AI art, typeset into beautiful PDFs, and published as an interactive web reader.

**Live site:** [grandoldbooks.com](https://grandoldbooks.com)

## Books

| Book | Author | Language | Year | Chapters | Words |
|------|--------|----------|------|----------|-------|
| Baeesween Sadi (22nd Century) | Rahul Sankrityayan | Hindi | 1924 | 16 | 41k |
| Mrinalini | Bankim Chandra Chattopadhyay | Bengali | 1882 | 43 | 39k |
| Alaler Gharer Dulal | Peary Chand Mitra | Bengali | 1858 | 30 | 54k |
| Ponniyin Selvan | Kalki Krishnamurthy | Tamil | 1955 | 293 | 672k |

## Pipeline Overview

```
Scanned PDF
    |
    v
1. OCR (Sarvam AI Vision)        -> data/{book}_ocr.txt
    |
    v
2. Translation (GPT-4.1)         -> data/{book}_english.txt
    |
    v
3. Image Generation (Gemini 3)   -> {book}_images/*.png
    |
    +---> 4a. PDF Typesetting (ReportLab) -> data/{book}_book.pdf
    |
    +---> 4b. Web JSON Generation         -> web/public/data/books/{book-id}/
    |         |
    |         v
    |     5. Annotation Generation (GPT-4.1) -> annotations.json
    |         |
    |         v
    |     6. Character Portraits (Gemini)    -> characters/{book-id}/*.png
    |         |
    |         v
    |     7. WebP Conversion + Deploy        -> *.webp
    |
    v
  Done
```

## Environment Setup

```bash
# Python (use uv)
uv venv && source .venv/bin/activate
uv pip install google-genai openai python-dotenv Pillow reportlab pymupdf

# API keys in .env
SARVAM_KEY=...          # Sarvam AI Vision (OCR)
OPENAI_API_KEY=...      # OpenAI GPT-4.1 (translation + annotations)
OPENAI_API_KEY_2=...    # Optional second key for 2x translation throughput
GEMINI_API_KEY=...      # Google Gemini (image generation)

# Web app
cd web && npm install
```

---

## Step 1: OCR (Sarvam AI Vision)

**Scripts:** `ocr_mrinalini.py`, `ocr_alaler.py`, `ocr_ponniyin.py`, `ocr_barrister.py`

Converts scanned PDF pages to text using Sarvam AI's vision endpoint. Works for Hindi, Bengali, Tamil, and Telugu.

```bash
uv run python ocr_mrinalini.py
```

**API call:**
```python
requests.post(
    "https://api.sarvam.ai/vision",
    headers={"API-Subscription-Key": api_key},
    files={"file": ("page.png", file_bytes, "image/png")},
    data={"prompt_type": "default_ocr"},
    timeout=60,
)
```

**Parallelization:** For large books (190+ pages), uses 3 API keys round-robin across 3 threads. Each thread needs its own `fitz.Document` instance and unique temp file paths (`/tmp/sarvam_{book}_t{thread_id}_{page}.png`) to avoid race conditions.

**Error handling:**
- 60s HTTP timeout to prevent hangs
- 5 retries with 10s sleep on 502/503/504 errors
- Skip-and-continue: failed pages tracked in a `skipped` list, retried after main loop
- 0.3s sleep between calls for rate limiting
- HTTP 402/429 = credits exhausted, skip that API key

**Checkpoint:** `data/{book}_ocr_checkpoint.json` — tracks completed pages, allows resume on crash.

**Output:** `data/{book}_ocr.txt` with `--- Page N ---` markers between pages.

---

## Step 2: Translation (GPT-4.1)

**Scripts:** `translate_mrinalini.py`, `translate_alaler.py`, `translate_ponniyin.py`, `translate_barrister.py`

```bash
uv run python translate_mrinalini.py
```

**CRITICAL: Must translate page-by-page**, not in chunks. Chunking causes GPT to silently drop/merge pages (lost 56/121 pages on first attempt with Baeesween Sadi). Always verify page count after translation:

```bash
grep -c "^--- Page" data/{book}_english.txt
```

**Model:** `gpt-4.1`, temperature 0.3

**Parallelization:** Up to 20 concurrent workers via `ThreadPoolExecutor`. Multiple API keys round-robin with `itertools.cycle`.

**System prompt pattern:**
```
You are translating '{TITLE}' ({YEAR}) by {AUTHOR}.
{CONTEXT ABOUT THE BOOK AND GENRE}
Translate into fluent, literary English.
Preserve paragraph breaks and {SPECIFIC TONE}.
Do NOT skip or summarize any content.
```

**Error handling:** 3 retries with exponential backoff (5s, 10s, 15s). Continue on failure, save checkpoint.

**Checkpoint:** `data/{book}_translate_checkpoint.json`

**Output:** `data/{book}_english.txt` with same `--- Page N ---` markers.

---

## Step 3: Image Generation (Gemini)

**Scripts:** `generate_ponniyin_images.py`, `generate_mrinalini_images.py`, `generate_chapter_images.py`, `regenerate_images.py`

Generates two images per chapter:
- **A5 portrait** (148:210 ratio) for PDF typesetting
- **16:9 landscape** for the web reader

```bash
uv run python generate_ponniyin_images.py
# Or batch regeneration for multiple books:
uv run python regenerate_images.py
```

**Models:**
- Image generation: `gemini-3-pro-image-preview` (aka `nano-banana-pro-preview`)
- Scene prompt generation: `gemini-2.0-flash` (text-only, for auto-generated prompts)

**Two approaches for prompts:**

1. **Hardcoded prompts** (Mrinalini, Baeesween Sadi): Hand-written scene descriptions per chapter in a `CHAPTER_PROMPTS` dict.

2. **Auto-generated prompts** (Ponniyin, Barrister, Alaler): Text model reads chapter excerpts (first 1500 chars) + character descriptions, generates 3-5 sentence scene description. Cached in `data/{book}_image_prompts.json`.

**Style prefixes** (per-book aesthetic):

| Book | Style |
|------|-------|
| Ponniyin Selvan | Tanjore painting — gold leaf, crimson, emerald, lapis blue |
| Mrinalini | Bengali miniature — sepia crosshatch with vermilion accent |
| Baeesween Sadi | Indian woodblock print — sepia with saffron accent |
| Barrister | 1920s watercolor — sepia, ochre, indigo with vermillion |

**Character descriptions** are defined as constants and injected into every prompt for visual consistency across chapters.

**Safety filters:** Gemini silently blocks prompts with certain words (returns `response.parts = None`). Use neutral alternatives:

| Blocked | Alternative |
|---------|-------------|
| desperate | determined |
| tears | saddened |
| blood | wounded |
| death, kill, murder | fallen warrior, confrontation |
| poison, corpse, stab | peril, sacrifice |
| clandestine | secret |

Retry up to 3 times with 3s delay when blocked.

**Config (always required):**
```python
config=types.GenerateContentConfig(
    response_modalities=["IMAGE", "TEXT"],  # MUST include both
)
```

**Aspect ratio enforcement:** Post-generation center-crop via PIL to exact target ratio.

**Parallelization:** `regenerate_images.py` uses `ThreadPoolExecutor` — 4 workers per book, multiple books concurrently. Each thread creates its own `genai.Client` instance.

**Checkpoint:** `data/{book}_images_checkpoint.json` — tracks `{key}_a5` and `{key}_web` entries.

**Output:** `{book}_images/` with `{key}.png` (A5) and `{key}_web.png` (landscape) pairs.

### Character Portraits

**Script:** `generate_character_images.py`

Generates square portrait images for the top 6 most-frequent characters per book (30 total across 5 books). Two-phase pipeline for maximum throughput:

```bash
uv run python generate_character_images.py
```

**Phase 1 — Prompt generation (15 parallel workers):** For each character, uses `gemini-2.0-flash` to build a portrait prompt from:
- Character name + description from `annotations.json`
- First 3 paragraphs from the first chapter where the character appears (from `chapters.json`)
- System prompt constraining output to physical appearance only (no background/setting)

**Phase 2 — Image generation (15 parallel workers):** Fires all 30 image requests concurrently using `gemini-3-pro-image-preview`. Each request wraps the portrait prompt with:
- Portrait instruction: "head and upper body, facing slightly to the side, centered, square 1:1"
- Book-specific style prefix (same as chapter images)

**Character selection:** Top 6 characters per book by chapter appearance count (same ranking logic as the book detail page).

**Slug generation:** `slugify()` — lowercase, spaces→hyphens, strip non-alphanumeric (e.g. "Baburam Babu" → "baburam-babu").

**Post-processing:** Center-crop to exact 1:1 square via PIL.

**Output:**
- Raw PNGs: `character_images/{book-id}_{slug}.png`
- Web copies: `web/public/data/images/characters/{book-id}/{slug}.png`
- Updates each book's `annotations.json` to add `"image": "/data/images/characters/{book-id}/{slug}.png"` to character entries

**Checkpoint:** `data/character_images_checkpoint.json` — tracks completed keys and cached prompts for resume.

**Web integration:** Character portraits appear in:
- Book detail page — 56px avatar in character cards
- Reader hover cards — 48px avatar next to character name
- Glossary page — 64px avatar next to character entries

---

## Step 4a: PDF Typesetting (ReportLab)

**Scripts:** `generate_ponniyin_pdf.py`, `generate_mrinalini_pdf.py`, etc.

```bash
uv run python generate_ponniyin_pdf.py
```

**Page setup:** A5 (148mm x 210mm), margins 20/24/16mm, warm parchment background (#FFFCF5).

**Fonts:**
- Headings: Inter Display (Bold, SemiBold, Medium)
- Body: Source Serif 4 — 10.5pt, leading 14.85pt (sqrt(2) ratio)
- Navigation: Inter (Regular, Light, Italic)
- Source Serif 4: download from Adobe GitHub **releases ZIP**, not raw URLs (which return HTML)

**Key gotchas:**
- `SimpleDocTemplate` adds 6pt internal frame padding
- Full-bleed images need offset: `-(MARGIN_LEFT + 6), -(MARGIN_BOTTOM + 6)`
- Shadow text over images: multi-layer dark shadow + white foreground (better than gradients)
- Page number suppression: use a `SuppressPageNum` flowable rather than predicting page numbers (pagination overflow makes prediction unreliable)

**Chapter extraction:** Page-range based assignment is more reliable than header detection when GPT translation produces inconsistent chapter header formats.

**Document structure:** Cover -> Title -> Half-title -> TOC -> Part dividers -> Chapter images -> Chapter text -> Colophon

**Output:** `data/{book}_book.pdf`

---

## Step 4b: Web JSON Generation

**Scripts:** `generate_ponniyin_json.py`, `generate_barrister_json.py`, `scripts/process_books.py`

```bash
uv run python generate_ponniyin_json.py
```

**Outputs per book:**
- `web/public/data/books/{book-id}/meta.json` — book metadata
- `web/public/data/books/{book-id}/chapters.json` — all chapters with paragraphs

**Global:**
- `web/public/data/catalog.json` — master list of all books + authors

**chapters.json structure:**
```json
{
  "chapters": [{
    "id": "ch-1",
    "number": 1,
    "title": "The Wealthy Patriarch",
    "part": null,
    "partName": null,
    "image": "/data/images/chapters/alaler-gharer-dulal/chapter_1.webp",
    "wordCount": 1850,
    "paragraphs": ["First paragraph...", "Second paragraph..."]
  }]
}
```

**Image deployment:** Only `_web.png` (landscape) versions are copied to the web directory, with the `_web` suffix stripped:
```
mrinalini_images_v2/1_1_web.png -> web/public/data/images/chapters/mrinalini/1_1.png
```

---

## Step 5: Annotation Generation (GPT-4.1)

**Script:** `generate_annotations.py`

Creates a glossary of characters, places, and vocabulary for each book.

```bash
uv run python generate_annotations.py
```

**Architecture:** Async MapReduce with `asyncio` + OpenAI async client.

**Phase 1 (Map):** Sends each chapter to GPT-4.1 in parallel (semaphore = 10 concurrent). Extracts:
- **Characters** — named people with 1-2 sentence descriptions
- **Proper nouns** — places, cultural terms, historical references
- **Vocabulary** — archaic or culturally-specific terms

**Phase 2 (Reduce):** Merges results — first description wins for duplicates, verifies each term actually appears in chapter text (exact match), removes unused entries.

**Output:** `web/public/data/books/{book-id}/annotations.json`
```json
{
  "glossary": {
    "Baburam Babu": { "type": "character", "description": "..." },
    "Baidyabati": { "type": "proper_noun", "description": "..." },
    "dhoti": { "type": "vocabulary", "description": "..." }
  },
  "chapters": {
    "ch-1": ["Baburam Babu", "Baidyabati", "dhoti"],
    "ch-2": ["..."]
  }
}
```

---

## Step 6: WebP Conversion

**Script:** `scripts/convert_webp.sh`

```bash
bash scripts/convert_webp.sh
```

1. Converts all PNGs in `web/public/data/images/` to WebP (`cwebp -q 80`) — 74% size reduction
2. Updates all JSON files: `.png"` -> `.webp"`

---

## Web App

Next.js 15 app in `web/` with static site generation (SSG).

```bash
cd web
npm run dev       # Local development
npm run build     # Production build
```

### Routes

| Route | Description |
|-------|-------------|
| `/` | Homepage — book grid |
| `/books/[id]` | Book detail — summary, characters, vocabulary, preview |
| `/books/[id]/glossary` | Full glossary — filterable by type, sortable |
| `/authors/[id]` | Author bio + their books |
| `/read/[id]` | Reader — loads saved progress |
| `/read/[id]/[...path]` | Reader — specific chapter |

### Reader Features

- **Two scroll modes:** Paginated (single chapter, arrow keys) and Infinite Scroll (all chapters, IntersectionObserver)
- **Dark/light mode** toggle
- **Font size** adjustment (small/medium/large)
- **Reading progress** persisted to localStorage via Zustand
- **Chapter picker** drawer with read/unread indicators + glossary link
- **Annotated terms** highlighted inline with popover definitions
- **Glossary** page with type filters (Characters, Places & Terms, Vocabulary) and sort (Most Frequent, Chronological)
- **Progress bars:** book-level (top) and chapter-level (bottom)
- **Continue Reading** on book page shows text from where you left off

### Key Components

| Component | Purpose |
|-----------|---------|
| `ReaderView.tsx` | Main reader — scroll modes, navigation, progress tracking |
| `ChapterContent.tsx` | Renders chapter text with annotation highlights |
| `AnnotatedTerm.tsx` | Popover for term definitions |
| `ChapterPicker.tsx` | TOC drawer with glossary link pinned at bottom |
| `ChapterImage.tsx` | Lazy-loaded chapter illustration |
| `ReaderLoader.tsx` | Client-side data fetcher |
| `BookPreview.tsx` | "Continue Reading" preview on book detail page |
| `GlossaryContent.tsx` | Filterable, sortable glossary |

### Data Layer (`web/lib/data.ts`)

```typescript
getCatalog()                 // catalog.json
getBookMeta(bookId)          // meta.json
getChapters(bookId)          // chapters.json
getAnnotations(bookId)       // annotations.json (null if missing)
```

### State (`web/lib/store.ts`)

Zustand with localStorage persistence:
```typescript
updateProgress(bookId, { currentChapter })  // 0-based index
getProgress(bookId)                          // ReadingProgress | null
setScrollMode("paginated" | "infinite")
```

---

## File Structure

```
sarvam/
├── data/                           # Pipeline intermediates
│   ├── {book}_ocr.txt             # OCR output
│   ├── {book}_english.txt         # Translated text
│   ├── {book}_book.pdf            # Typeset PDF
│   ├── {book}_image_prompts.json  # Cached scene descriptions
│   └── {book}_*_checkpoint.json   # Resume checkpoints
├── {book}_images*/                 # Generated illustrations (A5 + web)
├── fonts/                          # Inter, Source Serif 4
├── scripts/
│   ├── process_books.py           # JSON generation
│   ├── parse_ponniyin_chapters.py # Chapter parser for Ponniyin
│   └── convert_webp.sh           # PNG -> WebP batch conversion
├── web/                           # Next.js 15 app
│   ├── app/(browse)/             # Browse pages (books, authors, glossary)
│   ├── app/read/                 # Reader route
│   ├── components/reader/        # Reader components
│   ├── components/               # Shared components
│   ├── lib/                      # Types, store, utils, data layer
│   └── public/data/              # Static JSON + images (WebP)
├── ocr_*.py                      # Per-book OCR scripts
├── translate_*.py                # Per-book translation scripts
├── generate_*_images.py          # Per-book illustration generation
├── generate_*_pdf.py             # Per-book PDF typesetting
├── generate_*_json.py            # Per-book web JSON generation
├── generate_annotations.py       # Glossary generation (async MapReduce)
├── generate_character_images.py  # Character portrait generation (30 portraits)
├── regenerate_images.py          # Batch image regen (parallel, multi-book)
└── .env                          # API keys (SARVAM_KEY, OPENAI_API_KEY, GEMINI_API_KEY)
```

## Credits

- **OCR**: [Sarvam AI](https://sarvam.ai) Vision API
- **Translation**: OpenAI GPT-4.1
- **Illustrations**: Google Gemini 3 Pro
- **Typography**: [Source Serif 4](https://github.com/adobe-fonts/source-serif) (Adobe) & [Inter](https://rsms.me/inter/) (Rasmus Andersson)
- **Typesetting**: [ReportLab](https://www.reportlab.com/)
- **Web**: Next.js 15, React 19, Tailwind CSS, Zustand
