"""Extract Hindi Mahabharata EPUB into chapters_original.json.

The EPUB has 6 physical volumes containing 18 Parvas.
Maps to existing English Mahabharata chapter IDs (ch-1-1 through ch-18-1).
"""

import json
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path

EPUB_PATH = "/Users/debarghya/Downloads/mahabharata-hindi.epub"

# Chapter IDs must match existing Mahabharata chapters
PARVA_MAP = {
    1: {"id": "ch-1-1", "hindi": "आदिपर्व"},
    2: {"id": "ch-2-1", "hindi": "सभापर्व"},
    3: {"id": "ch-3-1", "hindi": "वनपर्व"},
    4: {"id": "ch-4-1", "hindi": "विराटपर्व"},
    5: {"id": "ch-5-1", "hindi": "उद्योगपर्व"},
    6: {"id": "ch-6-1", "hindi": "भीष्मपर्व"},
    7: {"id": "ch-7-1", "hindi": "द्रोणपर्व"},
    8: {"id": "ch-8-1", "hindi": "कर्णपर्व"},
    9: {"id": "ch-9-1", "hindi": "शल्यपर्व"},
    10: {"id": "ch-10-1", "hindi": "सौप्तिकपर्व"},
    11: {"id": "ch-11-1", "hindi": "स्त्रीपर्व"},
    12: {"id": "ch-12-1", "hindi": "शान्तिपर्व"},
    13: {"id": "ch-13-1", "hindi": "अनुशासनपर्व"},
    14: {"id": "ch-14-1", "hindi": "आश्वमेधिकपर्व"},
    15: {"id": "ch-15-1", "hindi": "आश्रमवासिकपर्व"},
    16: {"id": "ch-16-1", "hindi": "मौसलपर्व"},
    17: {"id": "ch-17-1", "hindi": "महाप्रस्थानिकपर्व"},
    18: {"id": "ch-18-1", "hindi": "स्वर्गारोहणपर्व"},
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
    toc = z.read("toc.ncx").decode("utf-8")

    # Parse TOC to get ordered content entries
    points = re.findall(
        r'<navLabel>\s*<text>([^<]+)</text>\s*</navLabel>\s*<content src="([^"]+)"',
        toc,
    )
    all_content = [(label.strip(), src.split("#")[0]) for label, src in points]

    # Find parva start indices
    parva_toc_indices = []
    for i, (label, src) in enumerate(all_content):
        m = re.match(r"(\d+)\.\s*(\S+)", label)
        if m and m.group(2) in {v["hindi"] for v in PARVA_MAP.values()}:
            num = int(m.group(1))
            parva_toc_indices.append((i, num, m.group(2), src))

    if len(parva_toc_indices) != 18:
        print(f"WARNING: Expected 18 parvas, found {len(parva_toc_indices)}")

    # Build file list for each parva
    parva_files: dict[int, list[str]] = {}
    for idx, (toc_i, num, name, src) in enumerate(parva_toc_indices):
        next_i = (
            parva_toc_indices[idx + 1][0]
            if idx + 1 < len(parva_toc_indices)
            else len(all_content)
        )
        files = []
        seen = set()
        for j in range(toc_i, next_i):
            f = all_content[j][1]
            if f not in seen:
                seen.add(f)
                files.append(f)
        parva_files[num] = files

    # Extract text for each parva
    chapters = []
    total_words = 0
    for num in range(1, 19):
        info = PARVA_MAP[num]
        files = parva_files.get(num, [])
        all_paras = []

        for fname in files:
            try:
                content = z.read(fname).decode("utf-8", errors="replace")
            except KeyError:
                print(f"  WARNING: File not found: {fname}")
                continue
            ext = TextExtractor()
            ext.feed(content)
            paras = ext.finish()

            # Filter out junk paragraphs (file markers like "part0006", single numbers, etc.)
            for p in paras:
                text = p.strip()
                # Skip empty, file markers, bare numbers, and very short non-Hindi lines
                if not text:
                    continue
                if re.match(r"^part\d+", text):
                    continue
                if re.match(r"^\d+$", text):
                    continue
                all_paras.append(text)

        word_count = sum(len(p.split()) for p in all_paras)
        total_words += word_count
        chapters.append(
            {
                "id": info["id"],
                "title": info["hindi"],
                "paragraphs": all_paras,
            }
        )
        print(
            f"  {num}. {info['hindi']}: {len(files)} files -> {len(all_paras)} paragraphs, {word_count:,} words"
        )

    data = {
        "language": "Hindi",
        "script": "Devanagari",
        "chapters": chapters,
    }

    # Write to both server-data and public
    for dest_dir in [
        Path("web/server-data/books/mahabharata"),
        Path("web/public/data/books/mahabharata"),
    ]:
        dest_dir.mkdir(parents=True, exist_ok=True)
        out_path = dest_dir / "chapters_original.json"
        with open(out_path, "w") as f:
            json.dump(data, f, ensure_ascii=False)
        print(f"Wrote {out_path}")

    print(f"\nTotal: {len(chapters)} chapters, {total_words:,} words")


if __name__ == "__main__":
    extract()
