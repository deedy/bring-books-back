"""OCR a PDF using Sarvam AI Vision API.

Usage (standalone):
    uv run python -m pipeline.ocr --book chandrakanta

Usage (from orchestrator):
    from pipeline.ocr import run
    run("chandrakanta")
"""

import argparse
import fitz
import requests
import json
import os
import time
import threading
from dotenv import load_dotenv

from pipeline.config import get_book

load_dotenv()

API_KEYS = [
    "sk_8mhg147t_gPo9py5YnqXhpfdiGETu4Ido",
    "sk_p7nr9ycc_CHkNEUcb5WfUh1pjuWMtOoAK",
    "sk_mt4pdzme_UZicBzLEe6OoCyKrWEavX5JQ",
]

lock = threading.Lock()


def load_checkpoint(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"completed_pages": {}, "last_page": -1, "skipped": []}


def save_checkpoint(path, state):
    with open(path, "w") as f:
        json.dump(state, f)


def ocr_page(page_num, doc, book_name, thread_id=0, retries=5):
    page = doc[page_num]
    pix = page.get_pixmap(dpi=200)
    img_path = f"/tmp/sarvam_{book_name}_t{thread_id}_{page_num}.png"
    pix.save(img_path)

    url = "https://api.sarvam.ai/vision"
    last_error = None

    for attempt in range(retries):
        api_key = API_KEYS[attempt % len(API_KEYS)]
        key_label = api_key[-4:]
        headers = {"API-Subscription-Key": api_key}

        try:
            with open(img_path, "rb") as f:
                files = {"file": ("page.png", f, "image/png")}
                data = {"prompt_type": "default_ocr"}
                resp = requests.post(url, headers=headers, files=files, data=data, timeout=60)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            last_error = str(e)
            print(f"    [{key_label}] Page {page_num+1} attempt {attempt+1}/{retries}: {type(e).__name__}, retrying...")
            time.sleep(10)
            continue

        if resp.status_code == 200:
            os.remove(img_path)
            return resp.json().get("content", "")
        elif resp.status_code in (402, 429):
            print(f"    [{key_label}] Page {page_num+1}: key exhausted (HTTP {resp.status_code}), trying next key...")
            last_error = f"HTTP {resp.status_code}"
            time.sleep(2)
            continue
        elif resp.status_code in (504, 502, 503):
            print(f"    [{key_label}] Page {page_num+1} attempt {attempt+1}/{retries}: HTTP {resp.status_code}, retrying...")
            last_error = f"HTTP {resp.status_code}"
            time.sleep(10)
            continue
        else:
            last_error = f"HTTP {resp.status_code}"
            print(f"    [{key_label}] Page {page_num+1}: unexpected HTTP {resp.status_code}, retrying...")
            time.sleep(5)
            continue

    if os.path.exists(img_path):
        os.remove(img_path)
    raise RuntimeError(f"Failed after {retries} retries: {last_error}")


def worker(thread_id, primary_key, pages_to_do, state, total_pages, pdf_path, book_name, checkpoint_path):
    doc = fitz.open(pdf_path)
    for page_num in pages_to_do:
        key = str(page_num)
        with lock:
            if key in state["completed_pages"]:
                continue

        try:
            text = ocr_page(page_num, doc, book_name, thread_id)
            with lock:
                state["completed_pages"][key] = text
                save_checkpoint(checkpoint_path, state)
                done = len(state["completed_pages"])
            preview = text[:50].replace("\n", " ")
            print(f"  [t{thread_id}] Page {page_num+1}/{total_pages} OK ({done}/{total_pages} total) {preview}...")
        except RuntimeError as e:
            with lock:
                if "skipped" not in state:
                    state["skipped"] = []
                state["skipped"].append(page_num)
                save_checkpoint(checkpoint_path, state)
            print(f"  [t{thread_id}] Page {page_num+1}/{total_pages} FAILED: {e}")
        time.sleep(0.3)
    doc.close()


def run(book_id, force=False, start=0, end=-1, verify=False):
    """Run OCR for a book. Returns True if output exists after run."""
    cfg = get_book(book_id)
    pdf_path = str(cfg.source_pdf)
    output_path = str(cfg.ocr_txt)
    checkpoint_path = str(cfg.ocr_checkpoint)

    if not force and os.path.exists(output_path) and not verify:
        print(f"[{book_id}] OCR output exists: {output_path}")
        return True

    if not os.path.exists(pdf_path):
        print(f"[{book_id}] Source PDF not found: {pdf_path}")
        return False

    os.makedirs(str(cfg.book_dir), exist_ok=True)

    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f"[{book_id}] PDF has {total_pages} pages")

    start_page = start
    end_page = end if end >= 0 else total_pages - 1
    page_range = list(range(start_page, end_page + 1))

    state = load_checkpoint(checkpoint_path)
    if "skipped" not in state:
        state["skipped"] = []

    if verify:
        skipped_set = set(state.get("skipped", []))
        missing = [i for i in page_range if str(i) not in state["completed_pages"]]
        force_retry = [i for i in page_range if str(i) in state["completed_pages"]
                       and i in skipped_set]
        if force_retry:
            print(f"Verify: clearing {len(force_retry)} skipped pages from checkpoint for re-OCR")
            for i in force_retry:
                del state["completed_pages"][str(i)]
        state["skipped"] = [s for s in state.get("skipped", []) if s not in set(missing + force_retry)]
        save_checkpoint(checkpoint_path, state)
        if missing or force_retry:
            print(f"Verify: {len(missing)} missing + {len(force_retry)} skipped -> re-running {len(set(missing + force_retry))} pages")
        else:
            print("Verify: all pages present, no gaps found!")

    remaining = [i for i in page_range if str(i) not in state["completed_pages"]]
    print(f"Already done: {len(state['completed_pages'])}, Remaining: {len(remaining)}")

    if not remaining:
        print("All pages already completed!")
    else:
        num_threads = min(3, len(remaining))
        chunks = [[] for _ in range(num_threads)]
        for i, page_num in enumerate(remaining):
            chunks[i % num_threads].append(page_num)

        for i, chunk in enumerate(chunks):
            print(f"  Thread {i+1}: {len(chunk)} pages")

        threads = []
        for i in range(num_threads):
            t = threading.Thread(
                target=worker,
                args=(i, API_KEYS[i % len(API_KEYS)], chunks[i], state, total_pages,
                      pdf_path, book_id, checkpoint_path),
            )
            t.start()
            threads.append(t)
            time.sleep(0.5)

        for t in threads:
            t.join()

    doc.close()

    # Write output
    all_pages = sorted(int(k) for k in state["completed_pages"].keys())
    with open(output_path, "w") as f:
        for i in all_pages:
            key = str(i)
            if key in state["completed_pages"]:
                f.write(f"--- Page {i + 1} ---\n")
                f.write(state["completed_pages"][key])
                f.write("\n\n")

    done = len(state["completed_pages"])
    print(f"\nWrote {done}/{len(page_range)} pages to {output_path}")
    return os.path.exists(output_path)


def main():
    parser = argparse.ArgumentParser(description="OCR a PDF using Sarvam AI")
    parser.add_argument("--book", required=True, help="Book ID")
    parser.add_argument("--start", type=int, default=0, help="Start page (0-indexed)")
    parser.add_argument("--end", type=int, default=-1, help="End page (0-indexed, -1 = last)")
    parser.add_argument("--verify", action="store_true", help="Verify and re-OCR missing pages")
    parser.add_argument("--force", action="store_true", help="Force re-run even if output exists")
    args = parser.parse_args()

    run(args.book, force=args.force, start=args.start, end=args.end, verify=args.verify)


if __name__ == "__main__":
    main()
