"""Step 1: Detect chapter boundaries in long Byomkesh stories.

Usage:
    uv run python scripts/byomkesh_detect_chapters.py

Stories with explicit numbered sections (One, Two, Three...) are split
deterministically. Stories without markers use Gemini Flash Lite.
Very long stories (>30K chars text) use a two-pass approach.

Output: data/byomkesh/sub_chapters.json
"""

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

WEB_DATA = "web/public/data/books"

LONG_STORIES = [
    "byomkesh-the-menagerie",
    "byomkesh-the-primal-enemy",
    "byomkesh-the-quills-of-the-porcupine",
    "byomkesh-the-mystery-of-the-fortress",
    "byomkesh-the-moth-and-the-flame",
    "byomkesh-the-submerged-peak",
    "byomkesh-thus-spoke-poet-kalidasa",
    "byomkesh-the-annihilation-of-beni",
    "byomkesh-picture-imperfect",
    "byomkesh-the-death-of-amrito",
    "byomkesh-byomkesh-and-barada",
    "byomkesh-the-gramophone-pin-mystery",
    "byomkesh-quicksand",
    "byomkesh-the-arrow-of-fire",
    "byomkesh-where-there-s-a-will",
    "byomkesh-calamity-strikes",
    "byomkesh-an-encore-for-byomkesh",
    "byomkesh-the-inquisitor",
]

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

MODEL = "google/gemini-3-flash-preview"

NUMBER_WORDS = [
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
    "eighteen", "nineteen", "twenty", "twenty-one", "twenty-two", "twenty-three",
]


def load_paragraphs(story_id: str) -> list[str]:
    with open(f"{WEB_DATA}/{story_id}/chapters.json") as f:
        data = json.load(f)
    paras = []
    for ch in data["chapters"]:
        paras.extend(ch["paragraphs"])
    return paras


def find_explicit_markers(paras: list[str]) -> list[tuple[int, str]]:
    """Find paragraphs that are standalone section numbers/markers."""
    markers = []
    for i, p in enumerate(paras):
        s = p.strip()
        if s.isdigit() and int(s) < 30:
            markers.append((i, s))
        elif s.lower() in NUMBER_WORDS:
            markers.append((i, s))
        elif re.match(r"^[IVXL]+$", s) and len(s) <= 5:
            markers.append((i, s))
        elif s.lower() in ["prologue", "epilogue"]:
            markers.append((i, s))
    return markers


def split_with_markers(story_id: str, paras: list[str], markers: list[tuple[int, str]]) -> list[dict]:
    """For stories with explicit numbered sections, use markers directly as chapter boundaries."""
    # Include para 0 if the first marker isn't at 0 or 1
    chapters = []
    if markers[0][0] > 1:
        chapters.append({"para_index": 0, "title": "Prologue"})

    for idx, label in markers:
        # The marker paragraph itself is a header; the chapter content starts at idx+1
        # But we want the chapter to "start" at the marker so it gets included
        chapters.append({"para_index": idx, "title": label.title()})

    # Generate titles via Gemini for each section
    chapters = generate_titles_for_sections(story_id, paras, chapters)
    return chapters


def generate_titles_for_sections(story_id: str, paras: list[str], chapters: list[dict]) -> list[dict]:
    """Ask Gemini to generate evocative titles for numbered sections."""
    sections_info = []
    for i, ch in enumerate(chapters):
        start = ch["para_index"]
        # Skip the marker paragraph, get first few content paragraphs
        content_start = start + 1 if start > 0 else 0
        end = chapters[i + 1]["para_index"] if i + 1 < len(chapters) else len(paras)
        excerpt = " ".join(paras[content_start:min(content_start + 5, end)])[:500]
        sections_info.append(f"Section {i + 1} (was: \"{ch['title']}\"): {excerpt}")

    prompt = (
        f"Given these {len(chapters)} sections of the detective story, generate a short evocative title "
        f"(3-6 words) for each. Return ONLY a JSON array of strings, one per section.\n\n"
        + "\n\n".join(sections_info)
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "Generate short chapter titles. Return ONLY a JSON array of strings."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            if raw.endswith("```"):
                raw = raw[: raw.rfind("```")]
            raw = raw.strip()
        titles = json.loads(raw)
        if len(titles) == len(chapters):
            for i, title in enumerate(titles):
                chapters[i]["title"] = title
    except Exception as e:
        print(f"  [{story_id}] Title generation failed, keeping numbered titles: {e}")

    return chapters


def build_indexed_text(paras: list[str], offset: int = 0, max_chars: int = 180000) -> str:
    """Build [index] paragraph text, respecting max_chars limit."""
    text = ""
    for i, p in enumerate(paras):
        line = f"[{offset + i}] {p}\n\n"
        if len(text) + len(line) > max_chars:
            break
        text += line
    return text


def detect_with_llm(story_id: str, paras: list[str], target_chapters: int,
                     start_idx: int = 0, end_idx: int | None = None) -> list[dict]:
    """Use Gemini Flash Lite to detect chapter boundaries."""
    if end_idx is None:
        end_idx = len(paras)
    subset = paras[start_idx:end_idx]
    word_count = sum(len(p.split()) for p in subset)
    target_wpc = word_count // target_chapters

    text = build_indexed_text(subset, offset=start_idx)

    prompt = f"""This is part of a Bengali detective story translated to English.
Paragraphs {start_idx}-{end_idx - 1}, {word_count} words total.

Split into exactly {target_chapters} chapters of roughly {target_wpc} words each.
Find scene transitions, time skips, dialogue pauses, or narrative breaks.

HARD RULES:
- First chapter starts at para_index {start_idx}
- Each chapter MUST be at least {max(2000, target_wpc - 2000)} words
- Each chapter MUST NOT exceed {target_wpc + 2500} words
- Split at natural transitions even without explicit markers

Return ONLY a JSON array: [{{"para_index": N, "title": "Short Evocative Title (3-6 words)"}}]

{text}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Split a story into evenly-sized chapters. Return ONLY a JSON array."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        if raw.endswith("```"):
            raw = raw[: raw.rfind("```")]
        raw = raw.strip()

    return json.loads(raw)


def detect_chapters(story_id: str) -> list[dict]:
    """Detect chapter boundaries for a single story."""
    paras = load_paragraphs(story_id)
    word_count = sum(len(p.split()) for p in paras)
    markers = find_explicit_markers(paras)

    print(f"  [{story_id}] {len(paras)} paragraphs, {word_count} words, {len(markers)} markers")

    # Stories with explicit numbered sections (>=5 markers)
    if len(markers) >= 5:
        print(f"  [{story_id}] Using {len(markers)} explicit markers")
        chapters = split_with_markers(story_id, paras, markers)
        print(f"  [{story_id}] -> {len(chapters)} chapters")
        return chapters

    # Target ~4500 words per chapter
    target_chapters = max(3, min(12, word_count // 4500))

    # Very long stories need two-pass approach (text exceeds LLM context window)
    text_chars = sum(len(p) for p in paras)
    if text_chars > 150000:
        print(f"  [{story_id}] Two-pass split ({text_chars} chars)")
        mid_para = len(paras) // 2
        mid_words = sum(len(p.split()) for p in paras[:mid_para])
        first_target = max(2, round(target_chapters * mid_words / word_count))
        second_target = target_chapters - first_target

        ch1 = detect_with_llm(story_id, paras, first_target, 0, mid_para)
        ch2 = detect_with_llm(story_id, paras, second_target, mid_para, len(paras))
        chapters = ch1 + ch2
    else:
        chapters = detect_with_llm(story_id, paras, target_chapters)

    # Validate
    if chapters[0]["para_index"] != 0:
        chapters[0]["para_index"] = 0

    # Print word counts
    for i, ch in enumerate(chapters):
        start = ch["para_index"]
        end = chapters[i + 1]["para_index"] if i + 1 < len(chapters) else len(paras)
        wc = sum(len(p.split()) for p in paras[start:end])
        flag = " *** UNEVEN" if wc < 2000 or wc > 8000 else ""
        print(f"    Ch {i + 1}: para {start:4d}, {wc:5d}w - {ch['title']}{flag}")

    print(f"  [{story_id}] -> {len(chapters)} chapters")
    return chapters


def main():
    output_path = "data/byomkesh/sub_chapters.json"
    os.makedirs("data/byomkesh", exist_ok=True)

    # Load existing results for resumability
    results = {}
    if os.path.exists(output_path):
        with open(output_path) as f:
            results = json.load(f)

    todo = [s for s in LONG_STORIES if s not in results]
    if not todo:
        print(f"All {len(LONG_STORIES)} stories already done. Delete {output_path} to rerun.")
        return

    print(f"Processing {len(todo)} stories ({len(results)} already done)...")

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(detect_chapters, sid): sid for sid in todo}
        for future in as_completed(futures):
            sid = futures[future]
            try:
                chapters = future.result()
                results[sid] = chapters
                # Save after each completion
                with open(output_path, "w") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"  [{sid}] ERROR: {e}")
                import traceback
                traceback.print_exc()

    print(f"\nDone! {len(results)}/{len(LONG_STORIES)} stories saved to {output_path}")


if __name__ == "__main__":
    main()
