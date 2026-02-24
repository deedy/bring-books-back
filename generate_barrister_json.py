"""Generate JSON data files for the web reader for Barrister Parvatishan.
Creates:
  - web/public/data/books/barrister-parvatishan/meta.json
  - web/public/data/books/barrister-parvatishan/chapters.json
  - Updates web/public/data/catalog.json
  - Copies images to web/public/data/images/
"""

import json
import os
import re
import shutil

TRANSLATION_FILE = "data/barrister_english.txt"
IMAGE_DIR = "barrister_images"
BOOK_ID = "barrister-parvatishan"
WEB_DATA_DIR = "web/public/data"
BOOK_DIR = f"{WEB_DATA_DIR}/books/{BOOK_ID}"
WEB_IMAGE_DIR = f"{WEB_DATA_DIR}/images"

# Part names
PART_NAMES = {
    1: "Parvatisham's Origins",
    2: "England Adventures",
    3: "Return Home",
}

# Chapter definitions: (part, number, start_page, end_page, title)
CHAPTERS = [
    (1, 1, 10, 26, "Parvatisham's Origins"),
    (1, 2, 27, 31, "Childhood Mischief"),
    (1, 3, 32, 34, "School Days"),
    (1, 4, 35, 39, "The Decision"),
    (1, 5, 40, 45, "Wedding and Departure"),
    (1, 6, 46, 47, "Farewell"),
    (1, 7, 48, 50, "The Journey Begins"),
    (1, 8, 51, 135, "Voyage to England"),
    (2, 1, 136, 159, "Arrival in England"),
    (2, 5, 160, 166, "First Acquaintances"),
    (2, 6, 167, 173, "Culture Shocks"),
    (2, 7, 174, 179, "Lodgings"),
    (2, 8, 180, 182, "The Boarding House"),
    (2, 9, 183, 190, "New Routines"),
    (2, 10, 191, 200, "English Lessons"),
    (2, 11, 201, 208, "Social Life"),
    (2, 12, 209, 213, "Indian Friends"),
    (2, 13, 214, 220, "Raju's Absence"),
    (2, 14, 221, 224, "Growing Fame"),
    (2, 15, 225, 231, "Edinburgh"),
    (2, 16, 232, 242, "Studies"),
    (2, 17, 243, 254, "Amusements"),
    (2, 18, 255, 263, "Theatre and Music"),
    (2, 19, 264, 273, "The Landlady's Daughter"),
    (2, 20, 274, 280, "New Lodgings"),
    (2, 21, 281, 284, "Wartime England"),
    (2, 22, 285, 295, "The Great War"),
    (2, 23, 296, 308, "Examinations"),
    (2, 24, 309, 328, "Farewell to England"),
    (2, 26, 329, 339, "The Voyage Home"),
    (3, 1, 346, 352, "Homecoming"),
    (3, 2, 353, 358, "The Train Home"),
    (3, 3, 359, 367, "Arrival in the Village"),
    (3, 4, 368, 381, "Family Reunion"),
    (3, 6, 385, 398, "Public Reception"),
    (3, 7, 399, 401, "The Speech"),
    (3, 8, 402, 408, "Train Journey"),
    (3, 9, 409, 428, "Starting Practice"),
    (3, 11, 429, 439, "Marriage Proposal"),
    (3, 12, 440, 444, "Wedding Preparations"),
    (3, 13, 445, 452, "The Wedding"),
    (3, 14, 453, 461, "Married Life"),
    (3, 15, 462, 469, "Return to Practice"),
    (3, 16, 470, 476, "Court Cases"),
    (3, 17, 477, 488, "Building a Reputation"),
    (3, 18, 489, 499, "Legal Career"),
    (3, 19, 500, 509, "A Turning Point"),
    (3, 20, 510, 516, "Public Life"),
    (3, 21, 517, 526, "Politics"),
    (3, 22, 527, 543, "Final Chapter"),
]


def parse_pages(text):
    """Split translated text into {page_num: content} dict."""
    parts = re.split(r"--- Page (\d+) ---\n", text)
    pages = {}
    for i in range(1, len(parts), 2):
        page_num = int(parts[i])
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        pages[page_num] = body
    return pages


def is_page_header(line):
    """Check if a line is a running page header that should be filtered."""
    s = line.strip()
    # Standalone page numbers (with or without text prefix)
    if re.match(r"^\d+\s*$", s):
        return True
    # "N Title" pattern (page number followed by chapter title)
    if re.match(r"^\d+\s+[A-Z]", s) and len(s) < 60:
        return True
    # Author name with optional page number
    if re.match(r"^Mokkapati Narasimha Shastri\s*\d*$", s, re.IGNORECASE):
        return True
    # Book title with optional page number
    if re.match(r"^Barrister Parvat[ei]+sh[ae]m\s*\d*$", s, re.IGNORECASE):
        return True
    # Chapter/section running headers (various OCR spellings)
    # e.g. "Parvateesham's Origins", "Parvatisham's Ancestry", "Parvateesam's Origins"
    # Handle both ASCII and unicode apostrophes
    if re.match(r"^Parvat[ei]+s?h?[ae]+[ms]", s, re.IGNORECASE) and len(s) < 40:
        return True
    # "Part One/Two/Three" standalone headers
    if re.match(r"^Part\s+(One|Two|Three)\s*$", s, re.IGNORECASE):
        return True
    # Combined "Part One Title" headers
    if re.match(r"^Part\s+(One|Two|Three)\s+\w", s, re.IGNORECASE) and len(s) < 60:
        return True
    return False


def text_to_paragraphs(body_text):
    """Split chapter body into clean paragraphs for display."""
    blocks = re.split(r"\n\n+", body_text)
    paragraphs = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # Merge lines within a block (but keep dialogue starts)
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        merged = []
        current = []
        for line in lines:
            if is_page_header(line):
                continue
            if line.startswith('"') and current:
                merged.append(" ".join(current))
                current = [line]
            else:
                current.append(line)
        if current:
            merged.append(" ".join(current))
        paragraphs.extend(merged)
    return paragraphs


def extract_chapters(pages):
    """Extract chapters using page-range definitions."""
    chapters = []
    for part, number, start_page, end_page, title in CHAPTERS:
        text_parts = []
        for pn in range(start_page, end_page + 1):
            if pn in pages:
                text_parts.append(pages[pn])
        body = "\n\n".join(text_parts)
        paras = text_to_paragraphs(body)
        wc = sum(len(p.split()) for p in paras)

        img_key = f"p{part}_chapter_{number}"
        img_path = f"/data/images/chapters/{BOOK_ID}/{img_key}.png"
        if not os.path.exists(f"{IMAGE_DIR}/{img_key}_web.png"):
            img_path = ""

        chapters.append({
            "id": f"ch-{part}-{number}",
            "number": number,
            "title": title,
            "part": part,
            "partName": PART_NAMES[part],
            "image": img_path,
            "wordCount": wc,
            "paragraphs": paras,
        })

    return chapters


def copy_images():
    """Copy chapter images (web landscape versions) to web public directory."""
    dest_dir = f"{WEB_IMAGE_DIR}/chapters/{BOOK_ID}"
    os.makedirs(dest_dir, exist_ok=True)

    count = 0
    for fname in os.listdir(IMAGE_DIR):
        if fname.endswith("_web.png") and fname.startswith("p"):
            src = os.path.join(IMAGE_DIR, fname)
            dst_name = fname.replace("_web.png", ".png")
            dst = os.path.join(dest_dir, dst_name)
            shutil.copy2(src, dst)
            count += 1
    print(f"  Copied {count} chapter images -> {dest_dir}")


def main():
    if not os.path.exists(TRANSLATION_FILE):
        print(f"ERROR: {TRANSLATION_FILE} not found.")
        return

    with open(TRANSLATION_FILE) as f:
        text = f.read()

    pages = parse_pages(text)
    print(f"Loaded {len(pages)} translated pages")

    chapters_data = extract_chapters(pages)
    total_words = sum(ch["wordCount"] for ch in chapters_data)
    print(f"Extracted {len(chapters_data)} chapters, {total_words:,} words")

    # Write chapters.json
    os.makedirs(BOOK_DIR, exist_ok=True)
    with open(f"{BOOK_DIR}/chapters.json", "w") as f:
        json.dump({"chapters": chapters_data}, f, ensure_ascii=False, indent=2)
    print(f"Wrote {BOOK_DIR}/chapters.json")

    # Build meta.json
    meta = {
        "id": BOOK_ID,
        "title": "Barrister Parvatishan",
        "subtitle": "A Humorous Tale of East Meets West",
        "authorId": "mokkapati-narasimha-shastri",
        "coverImage": f"/data/images/covers/{BOOK_ID}.png",
        "accentColor": "#B8860B",  # Dark goldenrod — vintage, warm
        "genre": ["Satirical Fiction", "Comedy", "Coming of Age"],
        "originalLanguage": "Telugu",
        "originalTitle": "బారిస్టర్ పార్వతీశం",
        "originalYear": 1924,
        "totalChapters": len(chapters_data),
        "wordCount": total_words,
        "summary": (
            "A naive young Brahmin from rural Andhra Pradesh sets out for England "
            "to become a barrister, armed with more enthusiasm than common sense. "
            "Through a series of hilarious misadventures — from baffling train journeys "
            "and seasick ocean crossings to bewildering English customs and ill-fitting "
            "suits — Parvatishan stumbles through the culture shock of early 20th century "
            "England and returns home a changed man. Mokkapati Narasimha Shastri's "
            "beloved 1924 Telugu classic is one of India's funniest novels, a warm-hearted "
            "satire on ambition, identity, and the comedy of crossing cultures."
        ),
    }
    with open(f"{BOOK_DIR}/meta.json", "w") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"Wrote {BOOK_DIR}/meta.json")

    # Update catalog.json
    catalog_path = f"{WEB_DATA_DIR}/catalog.json"
    with open(catalog_path) as f:
        catalog = json.load(f)

    # Remove existing entry if present
    catalog["books"] = [b for b in catalog["books"] if b["id"] != BOOK_ID]

    # Add preview text from first chapter
    preview = ""
    if chapters_data and chapters_data[0]["paragraphs"]:
        preview = " ".join(chapters_data[0]["paragraphs"][:3])[:1200]

    catalog["books"].append({
        **meta,
        "previewText": preview,
    })

    # Add author if not present
    author_id = "mokkapati-narasimha-shastri"
    author_exists = any(a["id"] == author_id for a in catalog["authors"])
    if not author_exists:
        catalog["authors"].append({
            "id": author_id,
            "name": "Mokkapati Narasimha Shastri",
            "image": f"/data/images/authors/{author_id}.png",
            "years": "1892–1960",
            "bio": (
                "Mokkapati Narasimha Shastri (1892-1960) was a celebrated Telugu writer, "
                "humorist, and playwright whose works brought laughter and social commentary "
                "to Telugu literature. Born in Mogalturru, Andhra Pradesh, he is best known "
                "for 'Barrister Parvatishan' (1924), a satirical novel about a young Indian's "
                "misadventures in England that became one of the most beloved Telugu novels "
                "of the 20th century. Shastri's gift for observational humor and his ability "
                "to capture the absurdities of cross-cultural encounters made him a pioneer "
                "of humorous writing in Telugu. His works continue to be widely read and have "
                "been adapted for stage and screen."
            ),
            "bookIds": [BOOK_ID],
        })
    else:
        for a in catalog["authors"]:
            if a["id"] == author_id and BOOK_ID not in a["bookIds"]:
                a["bookIds"].append(BOOK_ID)

    with open(catalog_path, "w") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print(f"Updated {catalog_path}")

    # Copy images
    copy_images()

    print(f"\nDone! {len(chapters_data)} chapters, {total_words:,} words")


if __name__ == "__main__":
    main()
