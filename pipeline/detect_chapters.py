"""Detect chapter boundaries in translated text using GPT-4.1.

Usage (standalone):
    uv run python -m pipeline.detect_chapters --book chandrakanta
"""

import argparse
import json
import re
import os
from openai import OpenAI
from dotenv import load_dotenv

from pipeline.config import get_book, OPENROUTER_BASE_URL

load_dotenv()

client = OpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=os.environ["OPENROUTER_API_KEY"],
)
MODEL = "openai/gpt-4.1"


def split_into_pages(text):
    parts = re.split(r"(--- Page \d+ ---\n)", text)
    pages = {}
    i = 0
    while i < len(parts):
        if re.match(r"--- Page (\d+) ---", parts[i]):
            m = re.match(r"--- Page (\d+) ---", parts[i])
            page_num = int(m.group(1))
            body = parts[i + 1] if i + 1 < len(parts) else ""
            pages[page_num] = body.strip()
            i += 2
        else:
            i += 1
    return pages


def get_page_first_lines(pages, n_lines=3):
    result = {}
    for page_num in sorted(pages.keys()):
        lines = [l.strip() for l in pages[page_num].split("\n") if l.strip()]
        result[page_num] = lines[:n_lines]
    return result


def detect_chapters_gpt(pages, book_info):
    page_summaries = get_page_first_lines(pages)

    page_text = ""
    for pn in sorted(page_summaries.keys()):
        lines = page_summaries[pn]
        page_text += f"Page {pn}: {' | '.join(lines)}\n"

    system_prompt = f"""You are analyzing the translated English text of "{book_info['title']}" ({book_info['year']}) by {book_info['author']}, originally in {book_info['language']}.

Context: {book_info['context']}

You are given the first few lines of each page. Your task is to identify chapter boundaries.

Return a JSON object with:
1. "chapters": array of objects, each with:
   - "page": the page number where the chapter starts
   - "chapter": chapter number (sequential, starting from 1)
   - "title": the chapter title (translate if needed, or use "Chapter N" if untitled)
   - "part": part number if the book has parts/sections (null if not)
   - "part_name": part name if applicable (null if not)

2. "running_headers": array of strings that are running headers/page numbers to filter out (patterns that repeat across pages)

3. "notes": any observations about the structure

Rules:
- Look for chapter headers like "Chapter 1", "Chapter I", numbered sections, or clear thematic breaks
- If the book has parts/volumes, identify those too
- Page numbers in the data refer to the translated text page numbers
- Be thorough — include ALL chapters, even short ones
- If you see patterns like "Chapter X - Title" or "X. Title" or just numbered sections, detect them all
- Return valid JSON only, no markdown fences."""

    user_prompt = f"Here are the first lines of each page ({len(page_summaries)} pages total):\n\n{page_text}"

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)


def refine_chapters(pages, initial_result, book_info):
    chapters = initial_result.get("chapters", [])
    if not chapters:
        return initial_result

    verification_text = ""
    for ch in chapters:
        pn = ch["page"]
        if pn in pages:
            content = pages[pn][:500]
            verification_text += f"\n--- Chapter {ch['chapter']} (page {pn}) ---\n{content}\n"

    system_prompt = f"""You previously detected chapter boundaries in "{book_info['title']}". Now verify and refine them.

For each chapter, you'll see the first ~500 chars of the starting page. Verify:
1. Is this actually a chapter start? (remove false positives)
2. Is the title correct? (fix if needed)
3. Are there any chapters you missed?

Return the FINAL corrected JSON with the same structure:
- "chapters": array of {{"page", "chapter", "title", "part", "part_name"}}
- "running_headers": patterns to filter
- "notes": any observations

Return valid JSON only."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Initial detection:\n{json.dumps(initial_result, indent=2)}\n\nPage content for verification:\n{verification_text}"},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)


def run(book_id, force=False):
    """Run chapter detection for a book. Returns True if output exists after run."""
    cfg = get_book(book_id)
    input_path = str(cfg.english_txt)
    output_path = str(cfg.chapters_def_json)

    if not force and os.path.exists(output_path):
        print(f"[{book_id}] Chapters def exists: {output_path}")
        return True

    if not os.path.exists(input_path):
        print(f"[{book_id}] English text not found: {input_path}")
        return False

    if not cfg.chapter_context:
        print(f"[{book_id}] No chapter context configured")
        return False

    book_info = {
        "title": cfg.title,
        "author": cfg.author_name,
        "language": cfg.original_language,
        "year": cfg.original_year,
        "context": cfg.chapter_context,
    }

    with open(input_path) as f:
        text = f.read()

    pages = split_into_pages(text)
    print(f"[{book_id}] Loaded {len(pages)} pages")

    # Phase 1: Initial detection
    print("\nPhase 1: Detecting chapter boundaries...")
    initial = detect_chapters_gpt(pages, book_info)
    n_chapters = len(initial.get("chapters", []))
    print(f"  Found {n_chapters} chapters initially")

    # Phase 2: Refinement
    print("\nPhase 2: Verifying chapter boundaries...")
    refined = refine_chapters(pages, initial, book_info)
    n_final = len(refined.get("chapters", []))
    print(f"  Final: {n_final} chapters")

    # Print chapter list
    print(f"\n{'='*60}")
    print(f"Chapter list for {book_info['title']}:")
    print(f"{'='*60}")
    for ch in refined.get("chapters", []):
        part_str = f" (Part {ch['part']}: {ch.get('part_name', '')})" if ch.get("part") else ""
        print(f"  Ch {ch['chapter']:3d} — Page {ch['page']:4d} — {ch['title']}{part_str}")

    # Save output
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(refined, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to {output_path}")

    return os.path.exists(output_path)


def main():
    parser = argparse.ArgumentParser(description="Detect chapter boundaries using GPT-4.1")
    parser.add_argument("--book", required=True, help="Book ID")
    parser.add_argument("--force", action="store_true", help="Force re-run")
    args = parser.parse_args()

    run(args.book, force=args.force)


if __name__ == "__main__":
    main()
