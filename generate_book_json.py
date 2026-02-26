"""Generate web JSON files for any book.

Usage:
    uv run python generate_book_json.py --book-id chandrakanta --chapters-def data/chandrakanta_chapters_def.json

Creates:
  - web/public/data/books/{book-id}/chapters.json
  - web/public/data/books/{book-id}/meta.json
  - Updates web/public/data/catalog.json
  - Copies images if available
"""

import argparse
import json
import os
import re
import shutil
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()
WEB_DATA_DIR = "web/public/data"

BOOK_METADATA = {
    "chandrakanta": {
        "title": "Chandrakanta",
        "transliterated_title": "Chandrakanta",
        "original_title": "चंद्रकांता",
        "author_id": "devaki-nandan-khatri",
        "author_name": "Devaki Nandan Khatri",
        "author_years": "1861–1913",
        "original_language": "Hindi",
        "original_year": 1888,
        "genre": ["Fantasy", "Romance", "Adventure"],
        "accent_color": "#8B0000",  # Dark red — Mughal/magical
        "translation_file": "data/chandrakanta_english.txt",
        "image_dir": "chandrakanta_images",
        "style_context": "Hindi fantasy novel with tilism (magical realms)",
    },
    "matira-manisha": {
        "title": "Man of the Soil",
        "transliterated_title": "Matira Manisha",
        "original_title": "ମାଟିର ମଣିଷ",
        "author_id": "kalindi-charan-panigrahi",
        "author_name": "Kalindi Charan Panigrahi",
        "author_years": "1901–1991",
        "original_language": "Odia",
        "original_year": 1929,
        "genre": ["Realist Fiction", "Rural Life"],
        "accent_color": "#B8860B",  # Earthy gold — rural/folk
        "translation_file": "data/matira-manisha_english.txt",
        "image_dir": "matira-manisha_images",
        "style_context": "Odia realist novel about farmers",
    },
    "shyamchi-aai": {
        "title": "Shyam's Mother",
        "transliterated_title": "Shyamchi Aai",
        "original_title": "श्यामची आई",
        "author_id": "sane-guruji",
        "author_name": "Sane Guruji",
        "author_years": "1899–1950",
        "original_language": "Marathi",
        "original_year": 1935,
        "genre": ["Autobiography", "Coming of Age"],
        "accent_color": "#D2691E",  # Warm chocolate — maternal warmth
        "translation_file": "data/shyamchi-aai_english.txt",
        "image_dir": "shyamchi-aai_images",
        "style_context": "Marathi autobiography about mother-son bond",
    },
    "kayar": {
        "title": "Coir",
        "transliterated_title": "Kayar",
        "original_title": "கயர்",
        "author_id": "thakazhi-sivasankara-pillai",
        "author_name": "Thakazhi Sivasankara Pillai",
        "author_years": "1912–1999",
        "original_language": "Tamil (translation of Malayalam)",
        "original_year": 1978,
        "genre": ["Epic Fiction", "Social Realism"],
        "accent_color": "#2E8B57",  # Sea green — Kerala backwaters
        "translation_file": "data/kayar_english.txt",
        "image_dir": "kayar_images",
        "style_context": "Epic novel about coir workers in Kerala",
    },
    "malegalalli-madumagalu": {
        "title": "Malegalalli Madumagalu",
        "transliterated_title": "Malegalalli Madumagalu",
        "original_title": "ಮಲೆಗಳಲ್ಲಿ ಮದುಮಗಳು",
        "author_id": "kuvempu",
        "author_name": "Kuvempu",
        "author_years": "1904–1994",
        "original_language": "Kannada",
        "original_year": 1967,
        "genre": ["Literary Fiction", "Nature Writing"],
        "accent_color": "#556B2F",  # Dark olive green — Western Ghats
        "translation_file": "data/malegalalli-madumagalu_english.txt",
        "image_dir": "malegalalli-madumagalu_images",
        "style_context": "Kannada novel set in the Western Ghats",
    },
}


def split_into_pages(text):
    parts = re.split(r"--- Page (\d+) ---\n", text)
    pages = {}
    for i in range(1, len(parts), 2):
        page_num = int(parts[i])
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        pages[page_num] = body
    return pages


SCANNING_ARTIFACTS = [
    r"Digitized by srujanika@gmail\.com",
]


def text_to_paragraphs(body_text, running_headers=None):
    """Split chapter body into clean paragraphs."""
    # Strip known scanning artifacts
    for pattern in SCANNING_ARTIFACTS:
        body_text = re.sub(pattern, "", body_text)
    blocks = re.split(r"\n\n+", body_text)
    paragraphs = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        merged = []
        current = []
        for line in lines:
            # Skip standalone page numbers
            if re.match(r"^\d+\s*$", line):
                continue
            # Skip running headers
            if running_headers and any(h.lower() in line.lower() for h in running_headers):
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


def extract_chapters(pages, chapters_def, running_headers=None):
    """Extract chapters using the chapter definition JSON.

    Chapters don't always start at page boundaries, so we concatenate
    all page text in order, find each chapter's marker position
    (a standalone number matching the expected chapter number), and
    split the full text at those positions.
    """
    chapters = chapters_def.get("chapters", [])
    page_nums = sorted(pages.keys())

    # Build one big string with page markers stripped
    full_text = "\n\n".join(pages[pn] for pn in page_nums)

    # Find the text position of each chapter marker.
    # A chapter marker is a standalone number on its own line matching
    # the expected chapter number, appearing on or after the declared page.
    # We search forward from the approximate page position.
    marker_positions = []
    for ch in chapters:
        ch_num = ch["chapter"]
        start_page = ch["page"]

        # Build text up to start_page to know the approximate char offset
        prefix_len = 0
        for pn in page_nums:
            if pn >= start_page:
                break
            prefix_len += len(pages[pn]) + 2  # +2 for "\n\n" join

        # Search for the standalone chapter number from that offset.
        # Patterns to match:
        #   \n\n5\n\n  (normal mid-page chapter break)
        #   Part One\n1\n\n  (chapter 1 right after a part header line)
        search_start = max(0, prefix_len - 200)
        search_region = full_text[search_start:]
        num_str = str(ch_num)

        # Try: number on its own line preceded by blank line or part header line
        pattern = re.compile(
            r'(?:\n\s*\n|\n[^\n]*(?:Part|भाग|Second|Third|Fourth)[^\n]*\n)'
            + re.escape(num_str) + r'\s*\n\s*\n'
        )
        m = pattern.search(search_region)
        if m:
            abs_pos = search_start + m.end()
            marker_positions.append(abs_pos)
        else:
            # Fallback: use the page boundary
            marker_positions.append(prefix_len)

    # Split text into chapter bodies using marker positions
    result = []
    for i, ch in enumerate(chapters):
        start_pos = marker_positions[i]
        end_pos = marker_positions[i + 1] if i + 1 < len(chapters) else len(full_text)
        body = full_text[start_pos:end_pos]

        paras = text_to_paragraphs(body, running_headers)

        # Strip repeated chapter title if first paragraph matches "N. Title"
        ch_num = ch["chapter"]
        ch_title = ch["title"]
        if paras and re.match(rf"^{ch_num}\.\s*{re.escape(ch_title)}\s*$", paras[0].strip()):
            paras.pop(0)

        wc = sum(len(p.split()) for p in paras)

        part = ch.get("part") or 1
        part_name = ch.get("part_name") or ""

        result.append({
            "id": f"ch-{part}-{ch_num}" if part else f"ch-{ch_num}",
            "number": ch_num,
            "title": ch["title"],
            "part": part,
            "partName": part_name,
            "image": "",  # filled in later when images exist
            "wordCount": wc,
            "paragraphs": paras,
        })

    return result


def generate_summary(book_id, chapters_data, meta):
    """Use GPT-4.1 to generate a book summary and subtitle."""
    # Get first 3 chapters' text
    sample = ""
    for ch in chapters_data[:3]:
        sample += f"\n\nChapter {ch['number']}: {ch['title']}\n"
        sample += "\n".join(ch["paragraphs"][:5])

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are writing marketing copy for a classic literature website. "
                    "Given sample chapters from a book, write:\n"
                    "1. A compelling subtitle (5-10 words, no quotes)\n"
                    "2. A book summary (3-5 sentences, ~100-150 words) that would make a reader want to read it. "
                    "Make it vivid and engaging without spoilers.\n\n"
                    "Return JSON: {\"subtitle\": \"...\", \"summary\": \"...\"}"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Book: {meta['title']} ({meta['original_year']}) by {meta['author_name']}\n"
                    f"Language: {meta['original_language']}\n"
                    f"Genre: {', '.join(meta['genre'])}\n"
                    f"Context: {meta['style_context']}\n"
                    f"Total chapters: {len(chapters_data)}, Total words: {sum(ch['wordCount'] for ch in chapters_data):,}\n"
                    f"\nSample text:{sample[:3000]}"
                ),
            },
        ],
        temperature=0.7,
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)


def update_images(book_id, chapters_data, image_dir):
    """Update chapter image paths if images exist."""
    web_img_dir = f"{WEB_DATA_DIR}/images/chapters/{book_id}"
    os.makedirs(web_img_dir, exist_ok=True)

    if not os.path.exists(image_dir):
        print(f"  No image directory {image_dir}, skipping images")
        return

    count = 0
    for ch in chapters_data:
        part = ch["part"]
        num = ch["number"]
        key = f"p{part}_chapter_{num}" if part else f"chapter_{num}"

        web_src = os.path.join(image_dir, f"{key}_web.png")
        if os.path.exists(web_src):
            dst = os.path.join(web_img_dir, f"{key}.png")
            shutil.copy2(web_src, dst)
            ch["image"] = f"/data/images/chapters/{book_id}/{key}.webp"
            count += 1

    print(f"  Copied {count} chapter images -> {web_img_dir}")


def copy_cover(book_id, image_dir):
    """Copy cover image if it exists."""
    cover_src = os.path.join(image_dir, "cover.png")
    if os.path.exists(cover_src):
        cover_dst = f"{WEB_DATA_DIR}/images/covers/{book_id}.png"
        os.makedirs(os.path.dirname(cover_dst), exist_ok=True)
        shutil.copy2(cover_src, cover_dst)
        print(f"  Copied cover -> {cover_dst}")


def main():
    parser = argparse.ArgumentParser(description="Generate web JSON for a book")
    parser.add_argument("--book-id", required=True, choices=list(BOOK_METADATA.keys()), help="Book ID")
    parser.add_argument("--chapters-def", required=True, help="Path to chapter definition JSON")
    args = parser.parse_args()

    book_id = args.book_id
    meta = BOOK_METADATA[book_id]
    book_dir = f"{WEB_DATA_DIR}/books/{book_id}"

    # Load translation
    with open(meta["translation_file"]) as f:
        text = f.read()
    pages = split_into_pages(text)
    print(f"Loaded {len(pages)} translated pages")

    # Load chapter definitions
    with open(args.chapters_def) as f:
        chapters_def = json.load(f)

    running_headers = chapters_def.get("running_headers", [])
    print(f"Running headers to filter: {running_headers}")

    # Extract chapters
    chapters_data = extract_chapters(pages, chapters_def, running_headers)
    total_words = sum(ch["wordCount"] for ch in chapters_data)
    print(f"Extracted {len(chapters_data)} chapters, {total_words:,} words")

    # Update images
    update_images(book_id, chapters_data, meta["image_dir"])
    copy_cover(book_id, meta["image_dir"])

    # Write chapters.json
    os.makedirs(book_dir, exist_ok=True)
    with open(f"{book_dir}/chapters.json", "w") as f:
        json.dump({"chapters": chapters_data}, f, ensure_ascii=False, indent=2)
    print(f"Wrote {book_dir}/chapters.json")

    # Generate summary
    print("Generating summary...")
    summary_data = generate_summary(book_id, chapters_data, meta)

    # Build meta.json
    book_meta = {
        "id": book_id,
        "title": meta["title"],
        "transliteratedTitle": meta["transliterated_title"],
        "subtitle": summary_data["subtitle"],
        "authorId": meta["author_id"],
        "coverImage": f"/data/images/covers/{book_id}.webp",
        "accentColor": meta["accent_color"],
        "genre": meta["genre"],
        "originalLanguage": meta["original_language"],
        "originalTitle": meta["original_title"],
        "originalYear": meta["original_year"],
        "totalChapters": len(chapters_data),
        "wordCount": total_words,
        "summary": summary_data["summary"],
    }

    with open(f"{book_dir}/meta.json", "w") as f:
        json.dump(book_meta, f, ensure_ascii=False, indent=2)
    print(f"Wrote {book_dir}/meta.json")

    # Update catalog.json
    catalog_path = f"{WEB_DATA_DIR}/catalog.json"
    with open(catalog_path) as f:
        catalog = json.load(f)

    # Remove existing entry if present
    catalog["books"] = [b for b in catalog["books"] if b["id"] != book_id]

    # Preview text from first chapter
    preview = ""
    if chapters_data and chapters_data[0]["paragraphs"]:
        preview = " ".join(chapters_data[0]["paragraphs"][:3])[:1200]

    catalog["books"].append({
        **book_meta,
        "previewText": preview,
    })

    # Add author if not present
    author_id = meta["author_id"]
    author_exists = any(a["id"] == author_id for a in catalog["authors"])
    if not author_exists:
        catalog["authors"].append({
            "id": author_id,
            "name": meta["author_name"],
            "image": f"/data/images/authors/{author_id}.webp",
            "years": meta["author_years"],
            "bio": "",  # Will be filled by generate_author_bios later
            "bookIds": [book_id],
        })
    else:
        for a in catalog["authors"]:
            if a["id"] == author_id and book_id not in a["bookIds"]:
                a["bookIds"].append(book_id)

    with open(catalog_path, "w") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print(f"Updated {catalog_path}")

    print(f"\nDone! {len(chapters_data)} chapters, {total_words:,} words")


if __name__ == "__main__":
    main()
