"""Extract Eknath Easwaran's Bhagavad Gita commentary from EPUB into chapters.json format."""

import json
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path


EPUB_PATH = Path("/Users/debarghya/Downloads/bhagavad.epub")
OUT_DIR = Path("web/server-data/books/bhagavad-gita")


class ParagraphExtractor(HTMLParser):
    """Extract paragraphs with their CSS class from XHTML."""

    def __init__(self):
        super().__init__()
        self.result: list[tuple[str, str]] = []  # (class, text)
        self._cls = ""
        self._capture = False
        self._text = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "p":
            self._cls = a.get("class", "")
            self._capture = True
            self._text = ""
        elif tag == "br" and self._capture:
            self._text += " "

    def handle_endtag(self, tag):
        if tag == "p" and self._capture:
            self._capture = False
            t = " ".join(self._text.split())  # normalize whitespace
            if t:
                self.result.append((self._cls, t))
            self._text = ""

    def handle_data(self, data):
        if self._capture:
            self._text += data


def classify(css_class: str) -> str:
    """Map CSS class to a simple type."""
    c = css_class.lower()
    if "para" in c:
        return "para"
    if "verse" in c:
        return "verse"
    if "speaker" in c:
        return "speaker"
    if "chapter-number" in c:
        return "chapter_number"
    if "chapter-title" in c:
        return "chapter_title"
    if "excerpt" in c:
        return "excerpt"
    return "other"


def parse_verse_number(text: str) -> int | None:
    """Extract the first verse number from text like '4–5. The different...'"""
    m = re.match(r"^(\d+)", text)
    return int(m.group(1)) if m else None


def extract_chapter(xhtml_content: str, chapter_num: int) -> dict:
    """Parse one XHTML chapter file into our JSON structure."""
    ext = ParagraphExtractor()
    ext.feed(xhtml_content)

    title = ""
    paragraphs = []
    sections = []
    current_speaker = ""

    for css_class, text in ext.result:
        kind = classify(css_class)

        if kind == "chapter_title":
            title = text
            continue
        if kind == "chapter_number":
            continue  # skip "CHAPTER TEN" etc.
        if kind == "speaker":
            current_speaker = text.rstrip(":")
            continue

        if kind == "verse":
            vnum = parse_verse_number(text)
            verse_text = text
            if current_speaker:
                verse_text = f"{current_speaker}: {text}"
                current_speaker = ""  # consumed

            # Insert section header before the verse
            sec_idx = len(paragraphs)
            if vnum is not None:
                sections.append({
                    "number": vnum,
                    "label": f"Verse {vnum}",
                    "paragraphIndex": sec_idx,
                })
                paragraphs.append({"text": f"Verse {vnum}", "type": "section_header"})

            paragraphs.append({"text": verse_text, "type": "verse"})
        elif kind == "para":
            if current_speaker:
                # Speaker label before commentary — prepend to first para
                paragraphs.append(f"{current_speaker}: {text}")
                current_speaker = ""
            else:
                paragraphs.append(text)
        elif kind == "excerpt":
            paragraphs.append({"text": text, "type": "excerpt"})
        else:
            if text.strip():
                paragraphs.append(text)

    # Compute word count
    wc = sum(
        len((p["text"] if isinstance(p, dict) else p).split())
        for p in paragraphs
    )

    return {
        "id": f"ch-1-{chapter_num}",
        "number": chapter_num,
        "title": title,
        "part": 1 + (chapter_num - 1) // 6,  # 3 volumes of 6
        "partName": ["The End of Sorrow", "Like a Thousand Suns", "To Love Is to Know Me"][(chapter_num - 1) // 6],
        "image": f"/data/images/chapters/bhagavad-gita/p1_chapter_{chapter_num}.webp",
        "wordCount": wc,
        "paragraphs": paragraphs,
        "sections": sections,
        "summary": "",
    }


def main():
    # Sort chapter files by number
    with zipfile.ZipFile(EPUB_PATH) as z:
        chapter_files = [f for f in z.namelist() if re.match(r".*OEBPS/\d+_.*\.xhtml$", f)]
        chapter_files.sort(key=lambda f: int(re.search(r"/(\d+)_", f).group(1)))

        chapters = []
        for f in chapter_files:
            num = int(re.search(r"/(\d+)_", f).group(1))
            content = z.read(f).decode("utf-8")
            ch = extract_chapter(content, num)
            chapters.append(ch)
            print(f"Ch {num:2d} '{ch['title']}': {len(ch['sections'])} verses, {len(ch['paragraphs'])} paragraphs, {ch['wordCount']} words")

    out = {"chapters": chapters}
    out_path = OUT_DIR / "chapters_easwaran.json"
    with open(out_path, "w") as fp:
        json.dump(out, fp, ensure_ascii=False, indent=2)

    total_sections = sum(len(ch["sections"]) for ch in chapters)
    total_words = sum(ch["wordCount"] for ch in chapters)
    print(f"\nTotal: {len(chapters)} chapters, {total_sections} verse sections, {total_words} words")
    print(f"Written to {out_path}")


if __name__ == "__main__":
    main()
