"""Extract Tulsidas Ramcharitmanas EPUB into chapters_original.json for the Ramayana book."""

import json
import zipfile
from html.parser import HTMLParser
from pathlib import Path

EPUB_PATH = "/Users/debarghya/Downloads/tulsidas.epub"

KANDA_NAMES = {
    1: "बालकाण्ड",
    2: "अयोध्याकाण्ड",
    3: "अरण्यकाण्ड",
    4: "किष्किन्धाकाण्ड",
    5: "सुन्दरकाण्ड",
    6: "लंकाकाण्ड",
    7: "उत्तरकाण्ड",
}

# Chapter IDs must match existing Ramayana chapters
CHAPTER_IDS = {
    1: "ch-1-1",
    2: "ch-1-2",
    3: "ch-1-3",
    4: "ch-1-4",
    5: "ch-1-5",
    6: "ch-1-6",
    7: "ch-1-7",
}


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paragraphs: list[str] = []
        self.current = ""

    def handle_data(self, data):
        self.current += data

    def handle_starttag(self, tag, attrs):
        if tag in ("p", "h1", "h2", "h3", "h4", "h5", "h6", "br", "div"):
            if self.current.strip():
                self.paragraphs.append(self.current.strip())
            self.current = ""

    def handle_endtag(self, tag):
        if tag in ("p", "h1", "h2", "h3", "h4", "h5", "h6", "div"):
            if self.current.strip():
                self.paragraphs.append(self.current.strip())
            self.current = ""

    def finish(self):
        if self.current.strip():
            self.paragraphs.append(self.current.strip())
        return self.paragraphs


def extract():
    z = zipfile.ZipFile(EPUB_PATH)
    chapters = []

    for book in range(1, 8):
        # Main content is in chapitre3* (chapitre1 = preface, chapitre2 = title)
        content_files = sorted(
            n for n in z.namelist()
            if n.startswith(f"{book}/OPS/chapitre3") and n.endswith(".xhtml")
        )

        all_paras = []
        for fname in content_files:
            content = z.read(fname).decode("utf-8")
            ext = TextExtractor()
            ext.feed(content)
            paras = ext.finish()
            all_paras.extend(paras)

        # Skip the repeated title lines at the start (e.g. "श्रीरामचरितमानस", kanda name, "श्लोक")
        # Keep all content — the first few lines are headers but they're part of the text
        # Remove exact duplicates of the kanda title at the very start
        cleaned = []
        seen_title = False
        for p in all_paras:
            # Skip duplicate kanda headers (first 2 are usually title repeats)
            if not seen_title and KANDA_NAMES[book] in p:
                if not cleaned:  # Skip first occurrence
                    seen_title = True
                    continue
            cleaned.append(p)

        # Also handle book 7's chapitre4 (Arti)
        if book == 7:
            arti_files = [n for n in z.namelist() if n.startswith("7/OPS/chapitre4") and n.endswith(".xhtml")]
            for fname in arti_files:
                content = z.read(fname).decode("utf-8")
                ext = TextExtractor()
                ext.feed(content)
                cleaned.extend(ext.finish())

        word_count = sum(len(p.split()) for p in cleaned)
        chapters.append({
            "id": CHAPTER_IDS[book],
            "title": KANDA_NAMES[book],
            "paragraphs": cleaned,
        })
        print(f"Book {book} ({KANDA_NAMES[book]}): {len(cleaned)} paragraphs, {word_count:,} words")

    data = {
        "language": "Hindi",
        "script": "Devanagari",
        "chapters": chapters,
    }

    # Write to both server-data and public
    for dest_dir in [
        Path("web/server-data/books/ramayana"),
        Path("web/public/data/books/ramayana"),
    ]:
        dest_dir.mkdir(parents=True, exist_ok=True)
        out_path = dest_dir / "chapters_original.json"
        with open(out_path, "w") as f:
            json.dump(data, f, ensure_ascii=False)
        print(f"Wrote {out_path}")

    print(f"\nTotal: {len(chapters)} chapters")


if __name__ == "__main__":
    extract()
