"""
Extract text from Sarasvatichandra PDFs (4 parts) into english.txt + chapters_def.json.

Each PDF has:
  - Front matter pages (skipped)
  - Chapter pages with running headers:
    - Odd pages: chapter title as header
    - Even pages: "Sarasvatichandra Part N" as header + page number
  - Chapter start pages: title as first line, then epigraph/content (NOT a page number on line 2)

Cleans:
  - InDesign metadata lines (e.g. "02 All Chapters.indd   5")
  - Timestamps (e.g. "7/22/2015   12:23:55 PM")
  - Publisher watermarks ("Orient BlackSwan", "For Review")
  - Bare page numbers
  - Footnotes extracted via font-size detection and stored separately;
    inline superscript refs replaced with ⟨fn:N⟩ markers

Usage:
    uv run python extract_sarasvatichandra.py
"""

import json
import os
import re
import unicodedata

import fitz  # PyMuPDF

# ── Configuration ──────────────────────────────────────────────────────────────

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data", "sarasvatichandra")
ENGLISH_TXT = os.path.join(OUTPUT_DIR, "english.txt")
CHAPTERS_JSON = os.path.join(OUTPUT_DIR, "chapters_def.json")
FOOTNOTES_JSON = os.path.join(OUTPUT_DIR, "footnotes.json")

PARTS = [
    {
        "pdf": os.path.expanduser("~/Downloads/Sarasvatichandra1.pdf"),
        "part": 1,
        "part_name": "Buddhidhan's Administration",
        "content_start_page": 63,  # 1-indexed PDF page where chapter 1 begins
        "chapters": [
            "The Guest of Suvarnapur",
            "Buddhidhan's Family",
            "Buddhidhan",
            "Buddhidhan (Continued)",
            "Buddhidhan (Conclusion)",
            "Intrigues in Rajeshwar",
            "Pleasure Garden",
            "At the Counsellor's House",
            "The Consequences of Intoxication",
            "Instruments of Intrigue and the Warcraft of Karbharis",
            "In Readiness for Court",
            "The King, Palace and Administration",
            "On the Way",
            "Destiny Fulfilled",
            "Sarasvatichandra",
            "Buddhidhan and Saubhagya Devi",
            "Pramaddhan and Kumud Sundari",
            "The Karbhari and his Administration",
            "Night Life: The Rising Curtain and the Ordeal by Fire",
            "Leave Taking",
            "Walking Away",
        ],
    },
    {
        "pdf": os.path.expanduser("~/Downloads/Sarasvatichandra2.pdf"),
        "part": 2,
        "part_name": "Gunasundari's Abode",
        "content_start_page": 67,
        "chapters": [
            "On the Outskirts of Manoharpuri",
            "The Outlaws",
            "The Injured Man",
            "Gunasundari",
            "Gunasundari (Continued)",
            "A Night in Manoharpuri",
            "Forest, Dark Night and Sarasvatichandra",
            "Kumud Sundari Leaves Suvarnapur",
            "Preparations for the Morning",
            "An Encounter with the Outlaws",
            "Smouldering Embers",
        ],
    },
    {
        "pdf": os.path.expanduser("~/Downloads/Sarasvatichandra3.pdf"),
        "part": 3,
        "part_name": "Ratnanagari's Rajkaran",
        "content_start_page": 75,
        "chapters": [
            "Sundargiri",
            "Maniraj and Vidya Chatura's Family in Manoharpuri",
            "News from Bombay: Dhurtalal's Machinations",
            "News from Suvarnapur: The Guilty Son of the Karbhari",
            "In the Presence of Vishnudas",
            "A Discourse on the Philosophy of the Manifest and the Unmanifest: Dream, Awakening, Dream",
            "Kings and Ministers of Ratnanagari",
            "Mallaraj and His Jewels",
            "Mallaraj's Concerns",
            "Mallaraj's Mani and His Initiation into Statecraft",
            "The First Surge of Foreign Rule",
            "New Chapters and New Histories",
            "Mallaraj's Retirement and Maniraj's Youthful Reign",
            "Maniraj's Sorrow and the Vision of His Father",
            "A Look Back at Sarasvatichandra and Kumud",
        ],
    },
    {
        "pdf": os.path.expanduser("~/Downloads/Sarasvatichandra4.pdf"),
        "part": 4,
        "part_name": "Sarasvatichandra",
        "content_start_page": 83,
        "chapters": [
            "Subhadra",
            "Sarasvatichandra's Initiation",
            "The Garden of Beauty and Kusum's Coming of Age",
            "Do We Need Native States? An Acrimonious Debate between State Officials and Visitors from Bombay",
            "A New Night",
            "Sarasvatichandra's Anguish",
            "Twin Sisters: The Spinster and the Widow",
            "Flora and Kusum",
            "Saubhagya Devi's Auspicious Death",
            "Kusum's Cloister",
            "Malla Mahabhavan or the Political Observatory of Ratnanagari and the Discourse on Mahabharata",
            "Chandrakant's Confusions",
            "Starry-eyed",
            "Pilgrimage to Surgram",
            "Kusum's Penance",
            "The Moon and the Moonstone",
            "Prison",
            "Passions Unseen and Palpable Vows",
            "Sweet Concerns for Sweeter Madhuri",
            "Companion",
            "Diagnosis and Remedy",
            "Subtle Desires of a Subtle Body",
            "Sarasvatichandra and Chandravali",
            "Vishnudas' Authority or Ways of Attaining Fulfillment of Sarasvatichandra's Subtle Body",
            "Sanatan Dharma or the Five Elementary Sacrifices of Ascetics",
            "Moonrise on Chiranjiv Shrunga",
            "On the Other Side of the Bridge",
            "Songs of Desire",
            "Hearts Revealed",
            "A Journey through the World of Immortals and their Blessings or A Dream of Pure Love",
            "Reflections of Indian Society in Pitamahpur and the Benediction of the Gems",
            "Host or Guest? Or the Authority of Selfless Intellect in Considerations of Virtue and Vice",
            "The Social Aspects of Subtle Love",
            "Arjun's Chariot and the Forest Fires",
            "The Immortals of Kurukshetra and the Future of India",
            "The Final Blow on the Sandalwood Tree",
            "Friend or Lover?",
            "A Woman's Heart and her Power",
            "The Dream World of Duties towards the Country",
            "The Power of Justice and the Delicacy of Social Affection",
            "Dust-covered Gems",
            "A Searing Heart",
            "Summons from Court",
            "Uncertainties",
            "Some Decisions and a Resolve",
            "Blowing of the Conch in the Temple of the Unmanifest and the Fulfillment of Life",
            "Mohini Maiya's Right",
            "A Curtain Breached",
            "Daughter",
            "Ganga-Yamuna",
            "Return to Source",
            "Aarti",
        ],
    },
]


# ── Junk-line patterns ────────────────────────────────────────────────────────

# InDesign metadata:  "02 All Chapters.indd   5"
_INDD_RE = re.compile(r"^\d+\s+All\s+Chapters\.indd\s+\d+\s*$")
# Timestamps:  "7/22/2015   12:23:55 PM"
_TIMESTAMP_RE = re.compile(r"^\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+[AP]M\s*$")
# Publisher watermarks
_WATERMARK_RE = re.compile(r"^(Orient\s+BlackSwan|For\s+Review)\s*$", re.IGNORECASE)
# Bare page numbers (1-4 digits only)
_BARE_PAGE_NUM_RE = re.compile(r"^\d{1,4}\s*$")

# Font size thresholds
_BODY_MIN_SIZE = 10.0       # Body text is 11.0, verse/epigraph is 10.0
_FOOTNOTE_SIZE = 9.0        # Footnote text
_HEADER_SIZE = 8.5          # Running headers
_SUPERSCRIPT_MAX = 6.5      # Superscript footnote refs (5.2–6.4)
_JUNK_SIZE = 6.0            # InDesign metadata, timestamps

# Footnote start: number + 2+ whitespace
_FOOTNOTE_START_RE = re.compile(r"^(\d{1,2})\s{2,}(.+)$")
# Dagger footnote start
_DAGGER_FN_RE = re.compile(r"^[†‡]\s+(.+)$")


# ── Helpers ────────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    """Normalize text for fuzzy matching: lowercase, collapse whitespace, strip punctuation."""
    text = unicodedata.normalize("NFKD", text)
    text = text.lower().strip()
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = re.sub(r"[^a-z0-9' ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def slug_keywords(title: str, n: int = 4) -> list[str]:
    """Return first N significant words from a slugified title."""
    stop = {"a", "an", "the", "of", "and", "in", "or", "on", "to", "for", "its"}
    words = slugify(title).split()
    significant = [w for w in words if w not in stop]
    if len(significant) < 2:
        significant = words
    return significant[:n]


def is_book_header(line: str) -> bool:
    """Check if a line is the even-page running header like 'Sarasvatichandra Part I'."""
    return bool(re.match(r"^Sarasvatichandra\s+Part\s+(I|II|III|IV|V)$", line.strip()))


def _is_junk(text: str) -> bool:
    """Check if a line is InDesign metadata, timestamp, or watermark."""
    s = text.strip()
    return bool(_INDD_RE.match(s) or _TIMESTAMP_RE.match(s) or _WATERMARK_RE.match(s))


def extract_page_structured(page, global_fn_counter: int) -> dict:
    """
    Extract structured text from a PDF page using font-size-based classification.

    Returns a dict with:
      - 'body_text': body text with superscript refs replaced by ⟨fn:N⟩ markers
      - 'footnotes': list of (global_fn_num, footnote_text) tuples
      - 'next_fn_counter': updated global footnote counter
      - 'raw_text': plain text for chapter detection (no fn markers)
    """
    blocks = page.get_text("dict")["blocks"]

    body_lines = []
    footnote_lines = []  # raw footnote lines (size 9.0)

    # For chapter detection, use plain get_text() which preserves the original
    # text order that the chapter detection logic was tuned for
    raw_text_for_detection = page.get_text()

    # Track superscript refs found on this page (in body text)
    # These will be replaced with ⟨fn:N⟩ after we know the global mapping
    superscript_refs = []  # list of ref numbers (strings) in order

    for b in blocks:
        if b["type"] != 0:  # skip image blocks
            continue
        for line_obj in b["lines"]:
            spans = line_obj["spans"]
            if not spans:
                continue

            # Determine the dominant font size for this line
            sized_spans = [(round(s["size"], 1), s["text"]) for s in spans if s["text"].strip()]
            if not sized_spans:
                continue

            sizes = [s[0] for s in sized_spans]
            main_size = max(set(sizes), key=sizes.count) if sizes else 0

            # Skip junk (InDesign metadata, timestamps) — size 6.0 at bottom
            full_text = "".join(s["text"] for s in spans)
            if _is_junk(full_text):
                continue

            # Skip bare page numbers at any font size
            text_stripped = full_text.strip()
            if _BARE_PAGE_NUM_RE.match(text_stripped) and main_size != 11.0:
                # Bare page number — skip (but not if it's body-sized, as it
                # could be a paragraph starting with a number)
                continue

            # Classify by main font size
            if main_size >= _BODY_MIN_SIZE:
                # Body or verse text — may contain superscript refs
                # Build text, replacing superscript digit spans with ⟨fn:N⟩ placeholders
                body_text = ""
                for span in spans:
                    sz = round(span["size"], 1)
                    t = span["text"]
                    if sz <= _SUPERSCRIPT_MAX and t.strip() and re.match(r"^\d+$", t.strip()):
                        # This is a superscript footnote reference
                        ref_num = t.strip()
                        superscript_refs.append(ref_num)
                        body_text += f"\u27E8fn:__PLACEHOLDER_{ref_num}__\u27E9"
                    elif sz <= _SUPERSCRIPT_MAX and t.strip() in ("†", "‡"):
                        # Dagger/double-dagger superscript ref
                        superscript_refs.append(t.strip())
                        body_text += f"\u27E8fn:__PLACEHOLDER_{t.strip()}__\u27E9"
                    else:
                        body_text += t
                body_lines.append(body_text)

            elif _FOOTNOTE_SIZE - 0.1 <= main_size <= _FOOTNOTE_SIZE + 0.6:
                # Footnote text: 9.0 (Part 1) or 9.5 (Parts 2-4)
                text = full_text.strip()
                if _BARE_PAGE_NUM_RE.match(text):
                    # Bare page number — skip
                    continue
                footnote_lines.append(text)

            elif main_size == _HEADER_SIZE:
                # Running header — include in body_lines (will be stripped by strip_headers)
                body_lines.append(full_text)

            else:
                # Other sizes — include as body text
                body_lines.append(full_text)

    # Parse footnote lines into (number, text) tuples
    footnotes = []
    current_num = None
    current_symbol = None
    current_parts = []

    for fn_line in footnote_lines:
        m = _FOOTNOTE_START_RE.match(fn_line)
        m_dag = _DAGGER_FN_RE.match(fn_line)
        if m:
            # Save previous footnote
            if current_num is not None or current_symbol is not None:
                key = current_symbol if current_symbol else str(current_num)
                footnotes.append((key, " ".join(current_parts)))
            current_num = int(m.group(1))
            current_symbol = None
            current_parts = [m.group(2)]
        elif m_dag:
            if current_num is not None or current_symbol is not None:
                key = current_symbol if current_symbol else str(current_num)
                footnotes.append((key, " ".join(current_parts)))
            current_num = None
            current_symbol = fn_line[0]  # † or ‡
            current_parts = [m_dag.group(1)]
        elif current_num is not None or current_symbol is not None:
            # Continuation of current footnote
            current_parts.append(fn_line)

    # Save last footnote
    if current_num is not None or current_symbol is not None:
        key = current_symbol if current_symbol else str(current_num)
        footnotes.append((key, " ".join(current_parts)))

    # ── Fix drop caps ──
    # Decorative initial capitals appear as a single uppercase letter on its
    # own line, followed by a line starting with a lowercase letter.  Merge them.
    merged_body = []
    for bl in body_lines:
        if (merged_body
                and re.match(r"^[A-Z]$", merged_body[-1].strip())
                and bl.strip()
                and bl.strip()[0].islower()):
            # Merge drop cap with following line (no space — it's the same word)
            merged_body[-1] = merged_body[-1].strip() + bl
        else:
            merged_body.append(bl)
    body_lines = merged_body

    # Now assign global footnote numbers
    # Build mapping: local ref (string) -> global number
    local_to_global = {}
    fn_counter = global_fn_counter
    for local_key, fn_text in footnotes:
        fn_counter += 1
        local_to_global[local_key] = fn_counter

    # Replace placeholders in body text with actual global fn numbers
    body_text = "\n".join(body_lines)
    for local_key, global_num in local_to_global.items():
        placeholder = f"\u27E8fn:__PLACEHOLDER_{local_key}__\u27E9"
        replacement = f"\u27E8fn:{global_num}\u27E9"
        body_text = body_text.replace(placeholder, replacement)

    # Clean up any remaining placeholders (refs without matching footnotes)
    body_text = re.sub(r"\u27E8fn:__PLACEHOLDER_.*?__\u27E9", "", body_text)

    # Build the footnotes list with global numbers
    global_footnotes = []
    for local_key, fn_text in footnotes:
        global_num = local_to_global[local_key]
        global_footnotes.append((global_num, fn_text))

    return {
        "body_text": body_text,
        "footnotes": global_footnotes,
        "next_fn_counter": fn_counter,
        "raw_text": raw_text_for_detection,
    }


def is_chapter_start(page_text: str, chapter_title: str) -> bool:
    """
    Detect whether this page is the START of the given chapter.
    Uses raw_text which includes headers for detection.
    """
    lines = [l.strip() for l in page_text.split("\n") if l.strip()]
    if len(lines) < 2:
        return False

    keywords = slug_keywords(chapter_title, n=4)

    matched = False
    title_end_line = 0
    for num_lines in range(1, min(5, len(lines))):
        candidate = slugify(" ".join(lines[:num_lines]))
        if all(kw in candidate for kw in keywords):
            matched = True
            title_end_line = num_lines
            break

    if not matched:
        return False

    # The line AFTER the title should NOT be a bare page number
    if title_end_line < len(lines):
        next_line = lines[title_end_line].strip()
        if re.match(r"^\d{1,4}$", next_line):
            return False

    return True


def strip_headers(page_text: str, chapter_title: str, is_start: bool) -> str:
    """
    Remove running headers and page numbers from page text.
    """
    lines = page_text.split("\n")

    non_empty_count = 0
    skip_count = 0
    result_lines = []
    header_done = False

    for line in lines:
        s = line.strip()
        if not s and not header_done:
            result_lines.append(line)
            continue

        if header_done:
            result_lines.append(line)
            continue

        non_empty_count += 1

        if non_empty_count == 1:
            if is_book_header(s):
                skip_count += 1
                continue
            elif not is_start:
                kw = slug_keywords(chapter_title, n=3)
                if all(k in slugify(s) for k in kw):
                    skip_count += 1
                    continue
            header_done = True
            result_lines.append(line)
        elif non_empty_count == 2:
            if re.match(r"^\d{1,4}$", s) and skip_count > 0:
                header_done = True
                continue
            else:
                header_done = True
                result_lines.append(line)
        else:
            header_done = True
            result_lines.append(line)

    return "\n".join(result_lines)


# ── Main extraction ───────────────────────────────────────────────────────────

def extract():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_pages: list[str] = []
    chapters_def: list[dict] = []
    global_page = 0
    global_fn_counter = 0
    all_footnotes: dict[str, str] = {}

    for part_info in PARTS:
        pdf_path = part_info["pdf"]
        part_num = part_info["part"]
        part_name = part_info["part_name"]
        chapter_titles = part_info["chapters"]
        content_start = part_info["content_start_page"]

        print(f"\n{'='*60}")
        print(f"Processing Part {part_num}: {part_name}")
        print(f"  PDF: {pdf_path}")

        doc = fitz.open(pdf_path)
        total_pdf_pages = doc.page_count
        print(f"  Total PDF pages: {total_pdf_pages}, content starts at page {content_start}")

        current_chapter_idx = -1
        current_chapter_start_global = -1

        for pdf_page_num in range(content_start - 1, total_pdf_pages):
            page = doc[pdf_page_num]

            # Extract structured text with font-size-based classification
            result = extract_page_structured(page, global_fn_counter)
            body_text = result["body_text"]
            raw_text = result["raw_text"]
            page_footnotes = result["footnotes"]
            global_fn_counter = result["next_fn_counter"]

            # Store footnotes
            for fn_num, fn_text in page_footnotes:
                all_footnotes[str(fn_num)] = fn_text

            # Check if this page starts a new chapter (using raw text for detection)
            found_chapter = False
            next_chapter_idx = current_chapter_idx + 1

            if next_chapter_idx < len(chapter_titles):
                candidate_title = chapter_titles[next_chapter_idx]
                if is_chapter_start(raw_text, candidate_title):
                    found_chapter = True

                    # Close previous chapter
                    if current_chapter_idx >= 0:
                        ch_end = global_page
                        chapters_def[-1]["end_page"] = ch_end
                        page_count = ch_end - chapters_def[-1]["start_page"] + 1
                        print(f"    -> {page_count} pages")

                    # Start new chapter
                    current_chapter_idx = next_chapter_idx
                    global_page += 1
                    current_chapter_start_global = global_page

                    chapters_def.append({
                        "chapter": len(chapters_def) + 1,
                        "title": candidate_title,
                        "page": global_page,
                        "start_page": global_page,
                        "end_page": -1,
                        "part": part_num,
                        "partName": part_name,
                    })

                    print(f"  Ch {next_chapter_idx + 1}: \"{candidate_title}\" "
                          f"(PDF p.{pdf_page_num + 1}, output p.{global_page})")

                    # Strip headers from body text
                    clean_text = strip_headers(body_text, candidate_title, is_start=True)
                    all_pages.append(clean_text)
                    continue

            if not found_chapter and current_chapter_idx >= 0:
                global_page += 1
                clean_text = strip_headers(body_text, chapter_titles[current_chapter_idx], is_start=False)
                all_pages.append(clean_text)

        # Close last chapter of this part
        if current_chapter_idx >= 0 and chapters_def:
            chapters_def[-1]["end_page"] = global_page
            page_count = global_page - chapters_def[-1]["start_page"] + 1
            print(f"    -> {page_count} pages")

        doc.close()
        print(f"  Part {part_num} done: {current_chapter_idx + 1} chapters found, "
              f"{global_page - (chapters_def[0]['start_page'] - 1 if chapters_def else 0)} pages total so far")

    # ── Write english.txt ──────────────────────────────────────────────────────
    print(f"\nWriting {ENGLISH_TXT} ({len(all_pages)} pages)...")
    with open(ENGLISH_TXT, "w", encoding="utf-8") as f:
        for i, page_text in enumerate(all_pages, 1):
            f.write(f"--- Page {i} ---\n")
            f.write(page_text.strip())
            f.write("\n\n")

    # ── Write chapters_def.json ────────────────────────────────────────────────
    print(f"Writing {CHAPTERS_JSON} ({len(chapters_def)} chapters)...")
    with open(CHAPTERS_JSON, "w", encoding="utf-8") as f:
        json.dump({"chapters": chapters_def}, f, indent=2, ensure_ascii=False)

    # ── Write footnotes.json ──────────────────────────────────────────────────
    print(f"Writing {FOOTNOTES_JSON} ({len(all_footnotes)} footnotes)...")
    with open(FOOTNOTES_JSON, "w", encoding="utf-8") as f:
        json.dump(all_footnotes, f, indent=2, ensure_ascii=False)

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f"\nDone!")
    print(f"  Total pages: {len(all_pages)}")
    print(f"  Total chapters: {len(chapters_def)}")
    print(f"  Total footnotes: {len(all_footnotes)}")

    # Verify chapter counts per part
    for part_num in [1, 2, 3, 4]:
        part_chapters = [c for c in chapters_def if c["part"] == part_num]
        expected = len(PARTS[part_num - 1]["chapters"])
        found = len(part_chapters)
        status = "OK" if found == expected else f"MISMATCH (expected {expected})"
        print(f"  Part {part_num}: {found} chapters {status}")

    # Check for any chapters with end_page == -1
    bad = [c for c in chapters_def if c["end_page"] == -1]
    if bad:
        print(f"\n  WARNING: {len(bad)} chapters have no end_page set:")
        for c in bad:
            print(f"    {c['title']}")

    # Verify no junk remaining
    with open(ENGLISH_TXT) as f:
        text = f.read()
    issues = []
    if "All Chapters.indd" in text:
        issues.append("InDesign metadata")
    if "Orient BlackSwan" in text:
        issues.append("Orient BlackSwan watermark")
    if "For Review" in text:
        issues.append("For Review watermark")
    if re.search(r"\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+[AP]M", text):
        issues.append("Timestamps")
    if issues:
        print(f"\n  WARNING: Junk still found: {', '.join(issues)}")
    else:
        print(f"\n  CLEAN: No junk lines detected")

    # Count fn markers
    fn_marker_count = len(re.findall(r"\u27E8fn:\d+\u27E9", text))
    print(f"  Footnote markers in text: {fn_marker_count}")


if __name__ == "__main__":
    extract()
