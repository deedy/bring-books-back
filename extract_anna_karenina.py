"""Extract Anna Karenina EPUB → english.txt + chapters_def.json with GPT-generated titles."""

import json
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path

import openai

EPUB_PATH = Path.home() / "Downloads" / "annakarenina.epub"
OUT_DIR = Path(__file__).resolve().parent / "data" / "anna-karenina"

PART_NAMES = {
    1: "Part One",
    2: "Part Two",
    3: "Part Three",
    4: "Part Four",
    5: "Part Five",
    6: "Part Six",
    7: "Part Seven",
    8: "Part Eight",
}

CHAPTERS_PER_PART = {1: 34, 2: 35, 3: 32, 4: 23, 5: 33, 6: 32, 7: 31, 8: 19}


class HTMLTextExtractor(HTMLParser):
    """Strip HTML tags, collect paragraph text."""

    def __init__(self):
        super().__init__()
        self._paragraphs: list[str] = []
        self._current = []
        self._in_p = False
        self._skip_tags = {"h1", "h2", "h3", "h4", "title", "style", "script"}
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self._skip_tags:
            self._skip_depth += 1
        elif tag == "p" and self._skip_depth == 0:
            self._in_p = True
            self._current = []

    def handle_endtag(self, tag):
        if tag in self._skip_tags and self._skip_depth > 0:
            self._skip_depth -= 1
        elif tag == "p" and self._in_p:
            text = "".join(self._current).strip()
            if text:
                self._paragraphs.append(text)
            self._in_p = False

    def handle_data(self, data):
        if self._in_p and self._skip_depth == 0:
            self._current.append(data)

    def get_text(self) -> str:
        return "\n\n".join(self._paragraphs)


def extract_chapter_text(z: zipfile.ZipFile, part: int, chapter: int) -> str:
    """Extract clean text from a single chapter XHTML file."""
    path = f"OEBPS/Text/chapter{part}.{chapter}.xhtml"
    html = z.read(path).decode("utf-8")
    extractor = HTMLTextExtractor()
    extractor.feed(html)
    return extractor.get_text()


def generate_titles_batch(chapters_texts: list[tuple[int, int, str]], client: openai.OpenAI) -> dict[tuple[int, int], str]:
    """Generate evocative chapter titles using GPT in batches."""
    titles = {}
    # Process in batches of ~30 chapters
    batch_size = 30
    items = list(chapters_texts)

    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        summaries = []
        for part, ch, text in batch:
            # Take first ~500 chars for context
            preview = text[:500].replace("\n", " ")
            summaries.append(f"Part {part}, Chapter {ch}: {preview}")

        prompt = (
            "You are helping create short, evocative chapter titles for Tolstoy's Anna Karenina "
            "(Louise & Aylmer Maude translation). Each title should be 2-5 words, capturing the "
            "essence or key event of the chapter. Be literary and specific — avoid generic titles.\n\n"
            "For each chapter below, return a JSON object mapping 'Part.Chapter' to the title.\n\n"
            + "\n---\n".join(summaries)
            + "\n\nReturn ONLY a JSON object like {\"1.1\": \"Title\", \"1.2\": \"Title\", ...}. No markdown fences."
        )

        resp = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        text_resp = resp.choices[0].message.content.strip()
        # Strip markdown fences if present
        if text_resp.startswith("```"):
            text_resp = re.sub(r"^```\w*\n?", "", text_resp)
            text_resp = re.sub(r"\n?```$", "", text_resp)
        batch_titles = json.loads(text_resp)
        for key, title in batch_titles.items():
            p, c = key.split(".")
            titles[(int(p), int(c))] = title
        print(f"  Generated titles for batch {i // batch_size + 1} ({len(batch)} chapters)")

    return titles


def main():
    z = zipfile.ZipFile(EPUB_PATH)

    # 1. Extract all chapter texts
    print("Extracting chapter texts from EPUB...")
    chapters: list[tuple[int, int, str]] = []
    for part in range(1, 9):
        for ch in range(1, CHAPTERS_PER_PART[part] + 1):
            text = extract_chapter_text(z, part, ch)
            chapters.append((part, ch, text))
    print(f"  Extracted {len(chapters)} chapters")

    # 2. Write english.txt with page markers
    print("Writing english.txt...")
    with open(OUT_DIR / "english.txt", "w") as f:
        for page_num, (part, ch, text) in enumerate(chapters, 1):
            f.write(f"--- Page {page_num} ---\n")
            f.write(text)
            f.write("\n\n")
    print(f"  Written {len(chapters)} pages to english.txt")

    # 3. Generate chapter titles with GPT
    print("Generating chapter titles with GPT...")
    client = openai.OpenAI()
    titles = generate_titles_batch(chapters, client)

    # 4. Write chapters_def.json
    print("Writing chapters_def.json...")
    chapters_def = []
    for page_num, (part, ch, _text) in enumerate(chapters, 1):
        title = titles.get((part, ch), f"Chapter {ch}")
        chapters_def.append({
            "page": page_num,
            "chapter": ch,
            "title": title,
            "part": part,
            "part_name": PART_NAMES[part],
            "partName": PART_NAMES[part],
        })

    with open(OUT_DIR / "chapters_def.json", "w") as f:
        json.dump({"chapters": chapters_def}, f, indent=2, ensure_ascii=False)
    print(f"  Written {len(chapters_def)} chapter definitions")

    # 5. Verify
    total_words = sum(len(text.split()) for _, _, text in chapters)
    print(f"\nVerification:")
    print(f"  Total chapters: {len(chapters)}")
    print(f"  Total words: ~{total_words:,}")
    print(f"  First chapter starts with: {chapters[0][2][:60]}...")
    print(f"  Last chapter (8.19) part: {chapters[-1][0]}, ch: {chapters[-1][1]}")


if __name__ == "__main__":
    main()
