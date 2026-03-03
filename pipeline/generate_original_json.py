"""Generate original-language chapters JSON from OCR text.

Reads the OCR text (same page markers as English), splits using the same
chapter definitions, and writes chapters_original.json for bilingual reading.

Two phases:
  1. Page-range extraction (instant, no LLM)
  2. Gemini Flash cleanup — removes OCR artifacts from each chapter in parallel

Usage (standalone):
    uv run python -m pipeline.generate_original_json --book na-hanyate
"""

import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from dotenv import load_dotenv

from pipeline.config import get_book, WEB_DATA_DIR, OPENROUTER_BASE_URL
from pipeline.generate_json import split_into_pages, text_to_paragraphs

load_dotenv()

text_client = OpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=os.environ["OPENROUTER_API_KEY"],
)
CLEANUP_MODEL = "google/gemini-2.5-flash"
MAX_CLEANUP_WORKERS = 10


def _load_english_chapter_ids(web_book_dir):
    """Read chapter IDs from the existing English chapters.json so original IDs match exactly."""
    chapters_path = os.path.join(str(web_book_dir), "chapters.json")
    if not os.path.exists(chapters_path):
        return None
    with open(chapters_path) as f:
        data = json.load(f)
    return [ch["id"] for ch in data["chapters"]]


def _cleanup_chapter(ch_id, paragraphs, language, book_title):
    """Use Gemini Flash to clean OCR artifacts from a chapter's paragraphs.

    Returns cleaned list of paragraphs.
    """
    if not paragraphs:
        return paragraphs

    # Join paragraphs with numbered markers so we can parse the response
    numbered = "\n".join(f"[{i}] {p}" for i, p in enumerate(paragraphs))

    import time
    for attempt in range(3):
        try:
            response = text_client.chat.completions.create(
                model=CLEANUP_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"You are cleaning OCR-scanned {language} text from the book \"{book_title}\". "
                            "The text has been split into numbered paragraphs. Your ONLY job is to remove scanning artifacts.\n\n"
                            "REMOVE a paragraph ONLY if it is entirely one of these:\n"
                            "- A standalone page number (e.g., '42', '১২৩')\n"
                            "- A running header/footer repeating the book title or chapter title\n"
                            "- A horizontal rule made of dashes or underscores\n"
                            "- A website URL, email address, or digitizer credit\n\n"
                            "TRIM from the start/end of a paragraph ONLY:\n"
                            "- Page numbers prepended/appended to actual text (e.g., '42 ঘরে-বাইরে তাকে...' → 'তাকে...')\n"
                            "- Running headers merged into text\n\n"
                            "CRITICAL RULES:\n"
                            "- KEEP every paragraph of actual literary content, even if short\n"
                            "- DO NOT remove, merge, summarize, or rephrase any story text\n"
                            "- When in doubt, KEEP the paragraph unchanged\n"
                            "- The output must have AT LEAST 80% of the input paragraphs\n\n"
                            "Return ONLY a JSON array of the cleaned paragraph strings (no numbers, no markers). "
                            "Return raw JSON — no markdown fences."
                        ),
                    },
                    {
                        "role": "user",
                        "content": numbered,
                    },
                ],
                temperature=0,
            )

            if not response.choices:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                break

            raw = response.choices[0].message.content
            if not raw:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                break

            raw = raw.strip()
            # Strip markdown fences if model adds them
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()

            cleaned = json.loads(raw)
            if isinstance(cleaned, list):
                # Ensure all items are strings (Gemini sometimes returns dicts)
                cleaned = [str(p) if not isinstance(p, str) else p for p in cleaned]
                cleaned = [p for p in cleaned if p and p.strip()]
                # Safety: reject if too many paragraphs removed OR added
                if len(paragraphs) > 3 and len(cleaned) < len(paragraphs) * 0.5:
                    print(f"    [{ch_id}] WARNING: Cleanup removed too many ({len(paragraphs)} -> {len(cleaned)}), keeping original")
                    return paragraphs
                if len(cleaned) > len(paragraphs) * 1.2:
                    print(f"    [{ch_id}] WARNING: Cleanup inflated paragraphs ({len(paragraphs)} -> {len(cleaned)}), keeping original")
                    return paragraphs
                return cleaned
        except json.JSONDecodeError:
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue
        except Exception as e:
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue
            print(f"    [{ch_id}] ERROR: {e}")

    # Fallback: return original paragraphs
    print(f"    [{ch_id}] WARNING: Cleanup failed after retries, keeping original")
    return paragraphs


def run(book_id, force=False):
    """Generate chapters_original.json for a book. Returns True on success."""
    cfg = get_book(book_id)
    output_path = str(cfg.web_original_chapters_json)

    if not force and os.path.exists(output_path):
        print(f"[{book_id}] chapters_original.json exists: {output_path}")
        return True

    if not cfg.original_script or cfg.original_script == "Latin":
        print(f"[{book_id}] No Indic script configured (script={cfg.original_script!r}), skipping")
        return True

    ocr_path = str(cfg.ocr_txt)
    if not os.path.exists(ocr_path):
        print(f"[{book_id}] OCR text not found: {ocr_path}")
        return True  # Not a failure — book may not have OCR

    chapters_def_path = str(cfg.chapters_def_json)
    if not os.path.exists(chapters_def_path):
        print(f"[{book_id}] Chapters def not found: {chapters_def_path}")
        return True

    # Load OCR text
    with open(ocr_path) as f:
        ocr_text = f.read()
    pages = split_into_pages(ocr_text)
    print(f"[{book_id}] Loaded {len(pages)} OCR pages")

    # Load chapter definitions
    with open(chapters_def_path) as f:
        chapters_def = json.load(f)

    running_headers = chapters_def.get("running_headers", [])
    page_nums = sorted(pages.keys())

    # Read English chapters to get IDs and compute proportional offsets
    eng_chapters_path = os.path.join(str(cfg.web_book_dir), "chapters.json")
    if not os.path.exists(eng_chapters_path):
        print(f"[{book_id}] English chapters.json not found, cannot split original text")
        return True

    with open(eng_chapters_path) as f:
        eng_chapters = json.load(f)["chapters"]

    # Load English text and compute chapter boundary offsets
    with open(str(cfg.english_txt)) as f:
        eng_text = f.read()
    eng_pages = split_into_pages(eng_text)
    eng_page_nums = sorted(eng_pages.keys())
    eng_full = "\n\n".join(eng_pages[pn] for pn in eng_page_nums)
    eng_total_len = len(eng_full)

    # Find each English chapter's start position in the full English text
    # by searching for the first paragraph
    eng_offsets = []
    search_from = 0
    for ech in eng_chapters:
        # Try multiple paragraphs as needles in case the first one was reformatted
        found = False
        for para in ech["paragraphs"][:3]:
            needle = para[:120]
            if not needle:
                continue
            pos = eng_full.find(needle, search_from)
            if pos != -1:
                eng_offsets.append(pos)
                search_from = pos + 1
                found = True
                break
        if not found:
            eng_offsets.append(-1)  # mark for interpolation

    # Interpolate missing offsets from neighbors
    for i in range(len(eng_offsets)):
        if eng_offsets[i] != -1:
            continue
        # Find previous and next known offsets
        prev_offset = eng_offsets[i - 1] if i > 0 else 0
        next_idx = next((j for j in range(i + 1, len(eng_offsets)) if eng_offsets[j] != -1), None)
        next_offset = eng_offsets[next_idx] if next_idx is not None else eng_total_len
        gap_count = (next_idx if next_idx is not None else len(eng_offsets)) - (i - 1 if i > 0 else 0)
        step = (next_offset - prev_offset) / gap_count if gap_count > 0 else 0
        eng_offsets[i] = int(prev_offset + step * (i - (i - 1 if i > 0 else 0)))

    # Build OCR full text in page order
    ocr_full = "\n\n".join(pages[pn] for pn in page_nums)
    ocr_total_len = len(ocr_full)

    # Map English proportional offsets to OCR text positions
    original_chapters = []
    empty_chapters = []
    for i, ech in enumerate(eng_chapters):
        # Proportional mapping: where this chapter starts/ends in the OCR text
        eng_start_frac = eng_offsets[i] / eng_total_len if eng_total_len > 0 else 0
        eng_end_frac = eng_offsets[i + 1] / eng_total_len if i + 1 < len(eng_offsets) else 1.0

        ocr_start = int(eng_start_frac * ocr_total_len)
        ocr_end = int(eng_end_frac * ocr_total_len)

        body = ocr_full[ocr_start:ocr_end]
        paras = text_to_paragraphs(body, running_headers)

        ch_id = ech["id"]

        if not paras:
            empty_chapters.append(ch_id)
        original_chapters.append({
            "id": ch_id,
            "paragraphs": paras,
        })

    print(f"[{book_id}] Extracted {len(original_chapters)} chapters (pre-cleanup)")

    # ── Gemini cleanup pass ────────────────────────────────────────────
    print(f"[{book_id}] Cleaning OCR artifacts with {CLEANUP_MODEL} ({MAX_CLEANUP_WORKERS} workers)...")
    pre_total = sum(len(ch["paragraphs"]) for ch in original_chapters)

    def cleanup_one(ch):
        cleaned = _cleanup_chapter(ch["id"], ch["paragraphs"], cfg.original_language, cfg.title)
        return ch["id"], cleaned

    with ThreadPoolExecutor(max_workers=MAX_CLEANUP_WORKERS) as pool:
        futures = {pool.submit(cleanup_one, ch): ch["id"] for ch in original_chapters}
        results = {}
        for future in as_completed(futures):
            ch_id, cleaned = future.result()
            results[ch_id] = cleaned

    for ch in original_chapters:
        ch["paragraphs"] = results[ch["id"]]

    post_total = sum(len(ch["paragraphs"]) for ch in original_chapters)
    removed = pre_total - post_total
    print(f"[{book_id}] Cleanup removed {removed} artifact paragraphs ({pre_total} -> {post_total})")

    # ── Translate chapter titles ──────────────────────────────────────
    eng_titles = [ech["title"] for ech in eng_chapters]
    if eng_titles:
        print(f"[{book_id}] Translating {len(eng_titles)} chapter titles to {cfg.original_language}...")
        try:
            titles_json = json.dumps(eng_titles, ensure_ascii=False)
            response = text_client.chat.completions.create(
                model=CLEANUP_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"Translate the following JSON array of English chapter titles into {cfg.original_language} "
                            f"({cfg.original_script} script). Return ONLY a JSON array of translated strings, "
                            "same length and order as input. Use literary/formal register. "
                            "Return raw JSON — no markdown fences."
                        ),
                    },
                    {"role": "user", "content": titles_json},
                ],
                temperature=0,
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()
            translated_titles = json.loads(raw)
            if isinstance(translated_titles, list) and len(translated_titles) == len(eng_titles):
                for ch, title in zip(original_chapters, translated_titles):
                    ch["title"] = str(title)
                print(f"[{book_id}] Translated {len(translated_titles)} titles")
            else:
                print(f"[{book_id}] WARNING: Title translation returned wrong count, skipping")
        except Exception as e:
            print(f"[{book_id}] WARNING: Title translation failed ({e}), skipping")

    # Re-check for empty chapters after cleanup
    empty_chapters = [ch["id"] for ch in original_chapters if not ch["paragraphs"]]

    # ── Quality validation ──────────────────────────────────────────────
    problems = []

    # 1. No empty chapters
    if empty_chapters:
        problems.append(f"{len(empty_chapters)} empty chapters: {', '.join(empty_chapters[:5])}")

    # 2. Chapter IDs must match English
    eng_ids = [ech["id"] for ech in eng_chapters]
    orig_ids = [ch["id"] for ch in original_chapters]
    if orig_ids != eng_ids:
        mismatches = sum(1 for a, b in zip(orig_ids, eng_ids) if a != b)
        problems.append(f"{mismatches} chapter ID mismatches vs English")

    # 3. Total original paragraphs should be at least 10% of English total
    eng_chapters_path = os.path.join(str(cfg.web_book_dir), "chapters.json")
    if os.path.exists(eng_chapters_path):
        with open(eng_chapters_path) as f:
            eng_total = sum(len(ch["paragraphs"]) for ch in json.load(f)["chapters"])
        orig_total = sum(len(ch["paragraphs"]) for ch in original_chapters)
        if eng_total > 0 and orig_total < eng_total * 0.1:
            problems.append(f"too few paragraphs overall: {orig_total} original vs {eng_total} English ({orig_total/eng_total:.0%})")

    quality_ok = len(problems) == 0
    if problems:
        print(f"[{book_id}] QUALITY ISSUES (toggle will be hidden):")
        for p in problems:
            print(f"  - {p}")

    original_data = {
        "language": cfg.original_language,
        "script": cfg.original_script,
        "chapters": original_chapters,
    }

    # Always write the file (so re-runs can improve the data)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(original_data, f, ensure_ascii=False, indent=2)
    print(f"[{book_id}] Wrote {output_path}")

    # Only set hasOriginalText if quality checks pass
    meta_path = os.path.join(str(cfg.web_book_dir), "meta.json")
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)
        meta["hasOriginalText"] = quality_ok
        meta["originalScript"] = cfg.original_script if quality_ok else ""
        with open(meta_path, "w") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print(f"[{book_id}] Updated meta.json (hasOriginalText={quality_ok})")

    # Update catalog.json
    catalog_path = str(WEB_DATA_DIR / "catalog.json")
    if os.path.exists(catalog_path):
        with open(catalog_path) as f:
            catalog = json.load(f)
        for book in catalog["books"]:
            if book["id"] == book_id:
                book["hasOriginalText"] = quality_ok
                book["originalScript"] = cfg.original_script if quality_ok else ""
                break
        with open(catalog_path, "w") as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)
        print(f"[{book_id}] Updated catalog.json (hasOriginalText={quality_ok})")

    total_paras = sum(len(ch["paragraphs"]) for ch in original_chapters)
    print(f"[{book_id}] Done! {len(original_chapters)} chapters, {total_paras} paragraphs")
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate original-language chapters JSON")
    parser.add_argument("--book", required=True, help="Book ID")
    parser.add_argument("--force", action="store_true", help="Force re-run")
    args = parser.parse_args()

    run(args.book, force=args.force)


if __name__ == "__main__":
    main()
