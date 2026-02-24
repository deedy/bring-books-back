"""Generate JSON data files for the web reader for Ponniyin Selvan.
Creates:
  - web/public/data/books/ponniyin-selvan/meta.json
  - web/public/data/books/ponniyin-selvan/chapters.json
  - Updates web/public/data/catalog.json
"""

import json
import os
import sys
import shutil

sys.path.insert(0, "scripts")
from parse_ponniyin_chapters import extract_chapters, chapters_to_paragraphs

TRANSLATION_FILE = "data/ponniyin_english.txt"
IMAGE_DIR = "ponniyin_images"
BOOK_ID = "ponniyin-selvan"
WEB_DATA_DIR = "web/public/data"
BOOK_DIR = f"{WEB_DATA_DIR}/books/{BOOK_ID}"
WEB_IMAGE_DIR = f"{WEB_DATA_DIR}/images"


def copy_images():
    """Copy chapter images (web landscape versions) to web public directory."""
    dest_dir = f"{WEB_IMAGE_DIR}/chapters/{BOOK_ID}"
    os.makedirs(dest_dir, exist_ok=True)

    # Cover — use portrait version (16:9 covers not supported in web yet)
    cover_src = f"{IMAGE_DIR}/cover.png"
    cover_dest = f"{WEB_IMAGE_DIR}/covers/{BOOK_ID}.png"
    if os.path.exists(cover_src):
        os.makedirs(os.path.dirname(cover_dest), exist_ok=True)
        shutil.copy2(cover_src, cover_dest)
        print(f"  Copied cover -> {cover_dest}")

    count = 0
    for fname in os.listdir(IMAGE_DIR):
        # Copy web (landscape) versions: p1_chapter_3_web.png -> p1_chapter_3.png
        if fname.endswith("_web.png") and fname.startswith("p"):
            src = os.path.join(IMAGE_DIR, fname)
            # Keep the key name but remove _web suffix for web paths
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

    chapters = extract_chapters(text)
    print(f"Extracted {len(chapters)} chapters")

    # Build chapters.json
    chapters_data = []
    total_words = 0
    for ch in chapters:
        paras = chapters_to_paragraphs(ch["body"])
        wc = sum(len(p.split()) for p in paras)
        total_words += wc

        img_key = f"p{ch['part']}_chapter_{ch['number']}"
        img_path = f"/data/images/chapters/{BOOK_ID}/{img_key}.png"
        # Check if web image exists (or will exist)
        if not os.path.exists(f"{IMAGE_DIR}/{img_key}_web.png"):
            img_path = ""

        chapters_data.append({
            "id": f"ch-{ch['part']}-{ch['number']}",
            "number": ch["number"],
            "title": ch["title"],
            "part": ch["part"],
            "partName": ch["partName"],
            "image": img_path,
            "wordCount": wc,
            "paragraphs": paras,
        })

    os.makedirs(BOOK_DIR, exist_ok=True)
    with open(f"{BOOK_DIR}/chapters.json", "w") as f:
        json.dump({"chapters": chapters_data}, f, ensure_ascii=False, indent=2)
    print(f"Wrote {BOOK_DIR}/chapters.json ({len(chapters_data)} chapters, {total_words:,} words)")

    # Build meta.json
    meta = {
        "id": BOOK_ID,
        "title": "Ponniyin Selvan",
        "subtitle": "The Son of the Kaveri",
        "authorId": "kalki-krishnamurthy",
        "coverImage": f"/data/images/covers/{BOOK_ID}.png",
        "accentColor": "#C5961B",  # Gold — Chola dynasty
        "genre": ["Historical Fiction", "Epic", "Political Intrigue"],
        "originalLanguage": "Tamil",
        "originalTitle": "பொன்னியின் செல்வன்",
        "originalYear": 1955,
        "totalChapters": len(chapters_data),
        "wordCount": total_words,
        "summary": (
            "Set in the 10th century during the zenith of the Chola dynasty, "
            "Ponniyin Selvan follows the young warrior Vandiyathevan as he carries "
            "a secret message through a kingdom seething with conspiracy. "
            "From the grand courts of Thanjavur to the shores of Lanka, "
            "political intrigue, forbidden romance, and dynastic ambition collide "
            "in Kalki Krishnamurthy's greatest Tamil novel — a sweeping epic of "
            "loyalty, betrayal, and the destiny of an empire."
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
    author_exists = any(a["id"] == "kalki-krishnamurthy" for a in catalog["authors"])
    if not author_exists:
        catalog["authors"].append({
            "id": "kalki-krishnamurthy",
            "name": "Kalki Krishnamurthy",
            "image": "/data/images/authors/kalki-krishnamurthy.png",
            "years": "1899–1954",
            "bio": (
                "Kalki Krishnamurthy (R. Krishnamurthy) was one of the most celebrated "
                "Tamil writers of the 20th century. A novelist, short story writer, journalist, "
                "poet, and critic, he is best known for his historical novels, especially "
                "Ponniyin Selvan, which is considered one of the greatest Tamil literary works. "
                "He was also a prominent figure in the Indian independence movement and served "
                "as editor of the influential Tamil magazine Kalki."
            ),
            "bookIds": [BOOK_ID],
        })
    else:
        for a in catalog["authors"]:
            if a["id"] == "kalki-krishnamurthy" and BOOK_ID not in a["bookIds"]:
                a["bookIds"].append(BOOK_ID)

    with open(catalog_path, "w") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print(f"Updated {catalog_path}")

    # Copy images
    copy_images()

    print("\nDone!")


if __name__ == "__main__":
    main()
