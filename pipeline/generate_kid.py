"""Generate a kid-friendly rewrite of all chapters for a book.

Produces web/server-data/books/{book_id}/chapters_kid.json
using GPT-4.1 to rewrite each chapter for readers aged 10 and below.
"""

import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import OpenAI

from pipeline.config import get_book, SERVER_DATA_DIR

PROMPT_TEMPLATE = """You are rewriting a chapter of "{title}" for a child aged 10 or younger. Your goals:

1. READING LEVEL: Use simple, clear English appropriate for a 10-year-old. Short sentences, everyday vocabulary. Avoid complex or abstract language.

2. RETAIN ALL PLOT POINTS: Every key event must be preserved. Don't skip scenes. But aggressively condense descriptions, internal monologues, and lengthy passages. Aim for 20-35% of the original length.

3. RETAIN ALL NAMES: Keep all character names from the original. You may add simple explanations in parentheses on first use if helpful, but always use the original names.

4. MUCH SHORTER LENGTH: Aggressively reduce the volume of text. Cut long descriptions, compress dialogue, remove repetition, and simplify complex passages. Target roughly 20-35% of the original length while keeping every important plot point. Merge paragraphs freely.

5. KID-FRIENDLY LANGUAGE: Use natural, simple English a child would understand. Replace difficult words with easy ones. Keep sentences short and clear.

6. PRESERVE PARAGRAPH STRUCTURE: Output each paragraph with its index number in the same [N] format as the input. You may merge multiple input paragraphs into one output paragraph — just use the index of the first paragraph in the merged group. Skip indices for paragraphs you've merged into others.

Here is the chapter:

"""

MAX_WORKERS = 15


def _format_chapter(ch: dict) -> str:
    lines = []
    for i, p in enumerate(ch["paragraphs"]):
        text = p if isinstance(p, str) else p["text"]
        lines.append(f"[{i}] {text}")
    return "\n\n".join(lines)


def _parse_response(text: str) -> list[str]:
    paragraphs = []
    for match in re.finditer(r"\[(\d+)\]\s*(.*?)(?=\n\[|\Z)", text, re.DOTALL):
        content = match.group(2).strip()
        if content:
            paragraphs.append(content)
    return paragraphs


def _process_chapter(
    client: OpenAI, title: str, ch_idx: int, ch: dict
) -> tuple[str, list[str]]:
    chapter_text = _format_chapter(ch)
    word_count = len(chapter_text.split())
    max_tokens = max(2000, int(word_count * 0.8))

    prompt = PROMPT_TEMPLATE.format(title=title) + chapter_text

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=min(max_tokens, 16000),
            )
            result = response.choices[0].message.content
            paragraphs = _parse_response(result)
            orig_count = len(ch["paragraphs"])
            print(
                f"  Ch {ch_idx + 1}: {len(paragraphs)} paragraphs "
                f"(orig {orig_count}), {len(result.split())} words",
                flush=True,
            )
            return ch["id"], paragraphs
        except Exception as e:
            print(f"  Ch {ch_idx + 1} attempt {attempt + 1} failed: {e}", flush=True)
            time.sleep(2)

    print(f"  Ch {ch_idx + 1} FAILED after 3 attempts", flush=True)
    return ch["id"], []


def run(book_id: str, force: bool = False) -> bool:
    cfg = get_book(book_id)
    chapters_path = cfg.server_chapters_json
    kid_path = Path(SERVER_DATA_DIR) / "books" / book_id / "chapters_kid.json"

    if not os.path.exists(str(chapters_path)):
        print(f"No chapters.json found for {book_id}")
        return False

    if kid_path.exists() and not force:
        print(f"chapters_kid.json already exists for {book_id} (use --force)")
        return True

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not set")
        return False

    client = OpenAI(api_key=api_key)

    with open(str(chapters_path)) as f:
        chapters_data = json.load(f)
    chapters = chapters_data["chapters"]

    # Load existing if resuming
    existing_map: dict[str, dict] = {}
    if kid_path.exists() and not force:
        with open(str(kid_path)) as f:
            existing = json.load(f)
        existing_map = {ch["id"]: ch for ch in existing["chapters"]}

    todo = [
        (i, ch) for i, ch in enumerate(chapters) if ch["id"] not in existing_map
    ]
    print(
        f"Generating {len(todo)} chapters ({len(existing_map)} already done)",
        flush=True,
    )

    if not todo:
        print("All chapters already generated.")
        return True

    results: dict[str, list[str]] = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(
                _process_chapter, client, cfg.title, i, ch
            ): i
            for i, ch in todo
        }
        for future in as_completed(futures):
            ch_id, paragraphs = future.result()
            results[ch_id] = paragraphs

    # Merge maintaining chapter order
    all_chapters = []
    for ch in chapters:
        if ch["id"] in existing_map:
            all_chapters.append(existing_map[ch["id"]])
        elif ch["id"] in results:
            all_chapters.append({"id": ch["id"], "paragraphs": results[ch["id"]]})
        else:
            all_chapters.append({"id": ch["id"], "paragraphs": []})

    kid_data = {
        "language": "Child",
        "script": "Latin",
        "chapters": all_chapters,
    }

    kid_path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(kid_path), "w") as f:
        json.dump(kid_data, f, indent=2, ensure_ascii=False)

    # Enable in the UI
    _set_has_kid_text(book_id)

    print(f"\nDone! Wrote {len(all_chapters)} chapters to {kid_path}", flush=True)
    return True


def _set_has_kid_text(book_id: str) -> None:
    from pipeline.config import WEB_DATA_DIR

    catalog_path = WEB_DATA_DIR / "catalog.json"
    if catalog_path.exists():
        with open(str(catalog_path)) as f:
            catalog = json.load(f)
        for b in catalog["books"]:
            if b["id"] == book_id:
                b["hasKidText"] = True
                break
        with open(str(catalog_path), "w") as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)

    meta_path = WEB_DATA_DIR / "books" / book_id / "meta.json"
    if meta_path.exists():
        with open(str(meta_path)) as f:
            meta = json.load(f)
        meta["hasKidText"] = True
        with open(str(meta_path), "w") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
