"""Extract Mahabharata EPUB into chapters.json (18 Parvas = 18 chapters)."""

import json
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path

EPUB_PATH = Path.home() / "Downloads" / "mahabharata.epub"
OUTPUT_DIR = Path("web/server-data/books/mahabharata")
PUBLIC_DIR = Path("web/public/data/books/mahabharata")

PARVA_NAMES = [
    ("ch110777", "Adi Parva", 1),
    ("ch110778", "Sabha Parva", 2),
    ("ch110779", "Vana Parva", 3),
    ("ch110780", "Virata Parva", 4),
    ("ch110781", "Udyoga Parva", 5),
    ("ch110782", "Bhishma Parva", 6),
    ("ch110783", "Drona Parva", 7),
    ("ch110784", "Karna Parva", 8),
    ("ch110785", "Shalya Parva", 9),
    ("ch110786", "Sauptika Parva", 10),
    ("ch110787", "Stri Parva", 11),
    ("ch110788", "Santi Parva", 12),
    ("ch110789", "Anusasana Parva", 13),
    ("ch110790", "Aswamedha Parva", 14),
    ("ch110791", "Asramavasika Parva", 15),
    ("ch110792", "Mausala Parva", 16),
    ("ch110793", "Mahaprasthanika Parva", 17),
    ("ch110794", "Svargarohanika Parva", 18),
]


class TextExtractor(HTMLParser):
    """Extract clean text from HTML, splitting into paragraphs."""

    def __init__(self):
        super().__init__()
        self.paragraphs: list[str] = []
        self._current: list[str] = []
        self._in_p = False
        self._in_body = False
        self._skip = False  # skip style/script tags

    def handle_starttag(self, tag, attrs):
        if tag == "body":
            self._in_body = True
        if tag in ("style", "script"):
            self._skip = True
        if not self._in_body or self._skip:
            return
        if tag in ("p", "h1", "h2", "h3", "h4", "h5", "h6"):
            self._in_p = True
            self._current = []
        elif tag == "br" and self._in_p:
            # Treat <br> as paragraph separator within <p> blocks
            text = " ".join(self._current).strip()
            if text:
                self.paragraphs.append(text)
            self._current = []

    def handle_endtag(self, tag):
        if tag in ("style", "script"):
            self._skip = False
        if not self._in_body:
            return
        if tag in ("p", "h1", "h2", "h3", "h4", "h5", "h6"):
            text = " ".join(self._current).strip()
            if text:
                self.paragraphs.append(text)
            self._in_p = False
            self._current = []

    def handle_data(self, data):
        if self._in_p and not self._skip:
            cleaned = data.strip()
            if cleaned:
                self._current.append(cleaned)


def extract_text_from_html(html_content: str) -> list[str]:
    """Extract paragraphs from HTML content."""
    parser = TextExtractor()
    parser.feed(html_content)
    return parser.paragraphs


def main():
    epub = zipfile.ZipFile(EPUB_PATH)
    html_files = sorted([n for n in epub.namelist() if n.endswith(".html")])

    # Group HTML files by chapter prefix
    file_groups: dict[str, list[str]] = {}
    for f in html_files:
        m = re.search(r"(ch\d+)", f)
        if m:
            prefix = m.group(1)
            file_groups.setdefault(prefix, []).append(f)

    chapters = []
    total_words = 0

    for ch_prefix, parva_name, book_num in PARVA_NAMES:
        files = file_groups.get(ch_prefix, [])
        all_paragraphs = []

        for f in sorted(files):
            content = epub.read(f).decode("utf-8", errors="replace")
            paragraphs = extract_text_from_html(content)
            all_paragraphs.extend(paragraphs)

        # Clean up paragraphs - remove very short ones that are just section headers
        # but keep them as they provide structure
        cleaned = []
        for p in all_paragraphs:
            # Skip empty or whitespace-only
            if not p.strip():
                continue
            # Normalize whitespace
            p = re.sub(r"\s+", " ", p).strip()
            if p:
                cleaned.append(p)

        word_count = sum(len(p.split()) for p in cleaned)
        total_words += word_count

        chapter = {
            "id": f"ch-{book_num}-1",
            "number": book_num,
            "title": f"{parva_name} (Book {book_num})",
            "part": book_num,
            "partName": "",
            "image": "",
            "wordCount": word_count,
            "paragraphs": cleaned,
            "summary": "",
        }
        chapters.append(chapter)
        print(f"  {parva_name}: {len(cleaned)} paragraphs, {word_count:,} words ({len(files)} HTML files)")

    print(f"\nTotal: {len(chapters)} chapters, {total_words:,} words")

    # Write chapters.json
    output = {"chapters": chapters}
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_DIR / "chapters.json", "w") as f:
        json.dump(output, f, ensure_ascii=False)
    print(f"\nWrote {OUTPUT_DIR / 'chapters.json'}")

    # Copy to public dir
    with open(PUBLIC_DIR / "chapters.json", "w") as f:
        json.dump(output, f, ensure_ascii=False)
    print(f"Wrote {PUBLIC_DIR / 'chapters.json'}")


if __name__ == "__main__":
    main()
