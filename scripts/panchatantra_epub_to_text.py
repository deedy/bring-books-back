"""Extract Panchatantra EPUB → english.txt + chapters_def.json.

Parses the Arthur Ryder translation EPUB, splits on #chN anchors from TOC,
and produces pipeline-compatible output files.
"""

import json
import re
from pathlib import Path

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup, NavigableString

EPUB_PATH = Path.home() / "Downloads" / "panchatantra.epub"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "panchatantra"

# Book structure from TOC
BOOKS = [
    {
        "part": 1,
        "part_name": "The Loss of Friends",
        "file_prefix": "text/part0007_split_",
        "files": ["text/part0007_split_001.html", "text/part0007_split_002.html"],
        "ch_start": 1,
        "ch_end": 34,
    },
    {
        "part": 2,
        "part_name": "The Winning of Friends",
        "file_prefix": "text/part0008_split_",
        "files": ["text/part0008_split_001.html"],
        "ch_start": 35,
        "ch_end": 44,
    },
    {
        "part": 3,
        "part_name": "Crows and Owls",
        "file_prefix": "text/part0009_split_",
        "files": ["text/part0009_split_001.html"],
        "ch_start": 45,
        "ch_end": 62,
    },
    {
        "part": 4,
        "part_name": "Loss of Gains",
        "file_prefix": "text/part0010_split_",
        "files": ["text/part0010_split_001.html"],
        "ch_start": 63,
        "ch_end": 75,
    },
    {
        "part": 5,
        "part_name": "Ill-Considered Action",
        "file_prefix": "text/part0011_split_",
        "files": ["text/part0011_split_001.html"],
        "ch_start": 76,
        "ch_end": 87,
    },
]

# Fix OCR typos and normalize titles from the TOC
TITLE_FIXES = {
    "THE, LION AND THE CARPENTER": "The Lion and the Carpenter",
    "THE PLOVER WHO FOUGHT THE OCEAN'": "The Plover Who Fought the Ocean",
    "FORETHOUGHT, READYWIT, AND ATALIST": "Forethought, Readywit, and Fatalist",
    "THE SHREWD OLD ANDE": "The Shrewd Old Gander",
    "SMART, THE ACKAL": "Smart, the Jackal",
    "AREMEDY WORSE THAN THE DISEASE": "A Remedy Worse than the Disease",
    "MOTHER'S SHANDILEE'S BARGAIN": "Mother Shandilee's Bargain",
    "SELF-DEFEATING FORTHTHOUGHT": "Self-Defeating Forethought",
    "SOFT, THE WEVER": "Soft, the Weaver",
    "HANG BALL AND GREEDY": "Hang-Ball and Greedy",
    "THE BRAHMAN, THE THIDF, AND THE GHOST": "The Brahman, the Thief, and the Ghost",
    "MOUSE-MAID MADE HOUSE": "Mouse-Maid Made Mouse",
    "How THE CROW-HEN KILLED THE BLACK SNAKE": "How the Crow-Hen Killed the Black Snake",
    "HOW THE BIRDS PICKED A KING": "How the Birds Picked a King",
    "HOW THE RABBIT FOOLED THE ELEPHANT": "How the Rabbit Fooled the Elephant",
    "HOW SUPERSMART ATE THE ELEPHANT": "How Supersmart Ate the Elephant",
    "THE SELF SACRIFICING DOVE": "The Self-Sacrificing Dove",
}


def title_case(s: str) -> str:
    """Convert ALL CAPS title to Title Case, preserving fixes."""
    # Normalize curly quotes to straight for lookup, then apply fixes
    normalized = s.replace("\u2019", "'").replace("\u2018", "'")
    if s in TITLE_FIXES:
        return TITLE_FIXES[s]
    if normalized in TITLE_FIXES:
        return TITLE_FIXES[normalized]
    # Title case with lowercase for small words
    small = {"a", "an", "the", "and", "but", "or", "for", "nor", "in", "on", "at", "to", "of", "who", "that", "than"}
    words = s.split()
    result = []
    for i, w in enumerate(words):
        lower = w.lower()
        if i == 0 or lower not in small:
            result.append(w[0] + w[1:].lower() if w else w)
        else:
            result.append(lower)
    return " ".join(result)


def extract_text_between(soup, start_id, end_id):
    """Extract all text between two #chN anchors."""
    start_el = soup.find(id=start_id)
    if not start_el:
        return None

    paragraphs = []
    el = start_el.find_next_sibling()
    while el:
        if el.get("id") and el["id"] == end_id:
            break
        text = el.get_text().strip()
        if text:
            paragraphs.append(text)
        el = el.find_next_sibling()
    return "\n\n".join(paragraphs)


def extract_text_from_id_to_end(soup, start_id):
    """Extract all text from a #chN anchor to end of document."""
    start_el = soup.find(id=start_id)
    if not start_el:
        return None

    paragraphs = []
    el = start_el.find_next_sibling()
    while el:
        if el.get("id") and el["id"].startswith("ch"):
            break
        text = el.get_text().strip()
        if text:
            paragraphs.append(text)
        el = el.find_next_sibling()
    return "\n\n".join(paragraphs)


def main():
    book = epub.read_epub(str(EPUB_PATH))

    # Build TOC mapping: ch_num -> title
    toc_titles = {}

    def walk_toc(toc):
        for item in toc:
            if isinstance(item, tuple):
                section, children = item
                walk_toc(children)
            else:
                href = item.href
                match = re.search(r"#ch(\d+)", href)
                if match:
                    ch_num = int(match.group(1))
                    toc_titles[ch_num] = item.title

    walk_toc(book.toc)

    # Parse all content files and build soups
    soups = {}
    for book_def in BOOKS:
        for f in book_def["files"]:
            if f not in soups:
                item = book.get_item_with_href(f)
                soups[f] = BeautifulSoup(item.get_content(), "html.parser")

    # Extract chapters
    chapters_def = []
    pages = []  # (page_num, text)
    page_num = 0

    for book_def in BOOKS:
        part = book_def["part"]
        part_name = book_def["part_name"]

        for ch_num in range(book_def["ch_start"], book_def["ch_end"] + 1):
            ch_id = f"ch{ch_num}"
            next_ch_id = f"ch{ch_num + 1}" if ch_num < book_def["ch_end"] else None

            # Find which file has this ch_id
            text = None
            for f in book_def["files"]:
                soup = soups[f]
                el = soup.find(id=ch_id)
                if not el:
                    continue

                if next_ch_id:
                    # Check if next_ch_id is in same file
                    next_el = soup.find(id=next_ch_id)
                    if next_el:
                        text = extract_text_between(soup, ch_id, next_ch_id)
                    else:
                        # Extract to end of this file
                        text = extract_text_from_id_to_end(soup, ch_id)
                        # But next chapter might be in the next file - extract_from_id_to_end
                        # already stops at next ch id, so just get to end of siblings
                        paragraphs = []
                        sibling = el.find_next_sibling()
                        while sibling:
                            t = sibling.get_text().strip()
                            if t:
                                paragraphs.append(t)
                            sibling = sibling.find_next_sibling()
                        text = "\n\n".join(paragraphs)
                else:
                    # Last chapter in this book - extract to end
                    paragraphs = []
                    sibling = el.find_next_sibling()
                    while sibling:
                        t = sibling.get_text().strip()
                        if t:
                            paragraphs.append(t)
                        sibling = sibling.find_next_sibling()
                    text = "\n\n".join(paragraphs)
                break

            if text is None:
                print(f"WARNING: Could not find {ch_id}")
                continue

            page_num += 1
            raw_title = toc_titles.get(ch_num, f"Chapter {ch_num}")
            title = title_case(raw_title)

            chapters_def.append({
                "part": part,
                "part_name": part_name,
                "chapter": ch_num - book_def["ch_start"] + 1,
                "title": title,
                "page": page_num,
            })
            pages.append((page_num, text))

    # Write english.txt
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "english.txt", "w") as f:
        for page_num, text in pages:
            f.write(f"--- Page {page_num} ---\n")
            f.write(text)
            f.write("\n\n")

    # Write chapters_def.json
    with open(OUT_DIR / "chapters_def.json", "w") as f:
        json.dump({"chapters": chapters_def, "use_title_markers": True}, f, indent=2)

    print(f"Extracted {len(chapters_def)} chapters across {len(BOOKS)} books")
    print(f"Written to {OUT_DIR / 'english.txt'} and {OUT_DIR / 'chapters_def.json'}")

    # Summary by part
    for book_def in BOOKS:
        count = sum(1 for c in chapters_def if c["part"] == book_def["part"])
        print(f"  Part {book_def['part']}: {book_def['part_name']} — {count} stories")


if __name__ == "__main__":
    main()
