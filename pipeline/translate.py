"""Translate OCR text to English using GPT-4.1.

Usage (standalone):
    uv run python -m pipeline.translate --book chandrakanta

Page-by-page translation (CRITICAL: never chunk). 20 concurrent workers with API key rotation.
"""

import argparse
import os
import json
import re
import shutil
import time
import threading
import concurrent.futures
from openai import OpenAI
from dotenv import load_dotenv

from pipeline.config import get_book, OPENROUTER_BASE_URL

load_dotenv()

MODEL = "openai/gpt-4.1"
MAX_WORKERS = 20

client = OpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=os.environ["OPENROUTER_API_KEY"],
)


def load_checkpoint(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"completed_pages": {}}


def save_checkpoint(path, state):
    with open(path, "w") as f:
        json.dump(state, f, ensure_ascii=False)


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


def translate_page(page_num, page_text, system_prompt, retries=3):
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": page_text},
                ],
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(5 * (attempt + 1))
                continue
            raise RuntimeError(f"API error after {retries} retries: {e}")


checkpoint_lock = threading.Lock()


def translate_worker(args):
    page_num, page_text, state, total, page_nums, system_prompt, checkpoint_path = args
    key = str(page_num)

    with checkpoint_lock:
        if key in state["completed_pages"]:
            return page_num, None, True

    if not page_text.strip():
        with checkpoint_lock:
            state["completed_pages"][key] = ""
            save_checkpoint(checkpoint_path, state)
        return page_num, "", True

    try:
        translation = translate_page(page_num, page_text, system_prompt)
        with checkpoint_lock:
            state["completed_pages"][key] = translation
            save_checkpoint(checkpoint_path, state)
            done = len(state["completed_pages"])
        preview = translation[:60].replace("\n", " ")
        print(f"  Page {page_num}/{page_nums[-1]} ({done}/{total} done) — {preview}...")
        return page_num, translation, True
    except RuntimeError as e:
        print(f"  Page {page_num}/{page_nums[-1]} FAILED: {e}")
        return page_num, None, False


def run(book_id, force=False, start=1, end=-1):
    """Run translation for a book. Returns True if output exists after run."""
    cfg = get_book(book_id)
    input_path = str(cfg.ocr_txt)
    raw_path = str(cfg.english_raw_txt)
    edited_path = str(cfg.english_txt)
    checkpoint_path = str(cfg.translate_checkpoint)

    if not cfg.translation_prompt:
        print(f"[{book_id}] No translation prompt configured")
        return False

    if not force and os.path.exists(raw_path):
        print(f"[{book_id}] Translation output exists: {raw_path}")
        return True

    if not os.path.exists(input_path):
        print(f"[{book_id}] OCR text not found: {input_path}")
        return False

    os.makedirs(str(cfg.book_dir), exist_ok=True)
    system_prompt = cfg.translation_prompt

    with open(input_path) as f:
        text = f.read()

    all_pages = split_into_pages(text)

    if end == -1:
        pages = all_pages
    else:
        pages = {k: v for k, v in all_pages.items() if start <= k <= end}

    page_nums = sorted(pages.keys())
    total = len(page_nums)
    print(f"[{book_id}] Found {len(all_pages)} total OCR pages")
    print(f"Translating pages: {total} pages")

    state = load_checkpoint(checkpoint_path)
    already = len(state["completed_pages"])
    print(f"Already translated: {already}")

    remaining = [(pn, pages[pn]) for pn in page_nums if str(pn) not in state["completed_pages"]]
    print(f"Remaining: {len(remaining)}")

    if not remaining:
        print("All pages already translated!")
    else:
        print(f"Starting translation with {MAX_WORKERS} concurrent workers...")
        args_list = [(pn, txt, state, total, page_nums, system_prompt, checkpoint_path) for pn, txt in remaining]

        failed = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(translate_worker, a): a[0] for a in args_list}
            for future in concurrent.futures.as_completed(futures):
                page_num = futures[future]
                try:
                    pn, translation, ok = future.result()
                    if not ok and translation is None:
                        failed.append(pn)
                except Exception as e:
                    print(f"  Page {page_num} EXCEPTION: {e}")
                    failed.append(page_num)

        if failed:
            print(f"\n{len(failed)} pages failed: {sorted(failed)}")
            print("Re-run to retry.")

    # Write final output to raw file
    with open(raw_path, "w") as f:
        for page_num in page_nums:
            key = str(page_num)
            if key in state["completed_pages"]:
                f.write(f"--- Page {page_num} ---\n")
                f.write(state["completed_pages"][key])
                f.write("\n\n")

    done = len(state["completed_pages"])
    print(f"\nWrote {done}/{total} pages to {raw_path}")

    # Copy raw -> edited on first run; never overwrite the edited file
    if not os.path.exists(edited_path):
        shutil.copy2(raw_path, edited_path)
        print(f"Copied {raw_path} -> {edited_path} (edit this file directly)")
    else:
        print(f"Edited file exists: {edited_path} (not overwritten)")

    return os.path.exists(raw_path)


def main():
    parser = argparse.ArgumentParser(description="Translate OCR text to English using GPT-4.1")
    parser.add_argument("--book", required=True, help="Book ID")
    parser.add_argument("--start", type=int, default=1, help="Start page number (default: 1)")
    parser.add_argument("--end", type=int, default=-1, help="End page number (-1 = last)")
    parser.add_argument("--force", action="store_true", help="Force re-run")
    args = parser.parse_args()

    run(args.book, force=args.force, start=args.start, end=args.end)


if __name__ == "__main__":
    main()
