"""OCR Ponniyin Selvan PDF using Sarvam AI Vision API.
1940 pages, Tamil text with broken font encoding — needs image-based OCR.
Skips TOC pages (1-14), processes content pages 15-1940.
"""

import fitz
import requests
import json
import os
import time

from dotenv import load_dotenv
load_dotenv()

API_KEY = os.environ["SARVAM_KEY"]
PDF_PATH = "data/ponniyin-selvan.pdf"
OUTPUT_FILE = "data/ponniyin_ocr.txt"
CHECKPOINT_FILE = "data/ponniyin_ocr_checkpoint.json"

START_PAGE = 14  # 0-indexed (= PDF page 15, first content page)
END_PAGE = 1939  # 0-indexed (= PDF page 1940, last page)


def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE) as f:
            return json.load(f)
    return {"completed_pages": {}, "skipped": []}


def save_checkpoint(state):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(state, f)


def ocr_page(page_num, doc, retries=5):
    page = doc[page_num]
    pix = page.get_pixmap(dpi=200)
    img_path = f"/tmp/sarvam_ponniyin_{page_num}.png"
    pix.save(img_path)

    url = "https://api.sarvam.ai/vision"
    headers = {"API-Subscription-Key": API_KEY}

    for attempt in range(retries):
        try:
            with open(img_path, "rb") as f:
                files = {"file": ("page.png", f, "image/png")}
                data = {"prompt_type": "default_ocr"}
                resp = requests.post(url, headers=headers, files=files, data=data, timeout=60)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            if attempt < retries - 1:
                time.sleep(10)
                continue
            os.remove(img_path)
            raise RuntimeError("Request timeout/connection error after retries")

        if resp.status_code == 200:
            os.remove(img_path)
            return resp.json().get("content", "")
        elif resp.status_code in (402, 429):
            os.remove(img_path)
            raise RuntimeError(f"CREDITS EXHAUSTED (HTTP {resp.status_code})")
        elif resp.status_code in (504, 502, 503):
            if attempt < retries - 1:
                time.sleep(10)
                continue
            os.remove(img_path)
            raise RuntimeError(f"API error (HTTP {resp.status_code})")
        else:
            os.remove(img_path)
            raise RuntimeError(f"API error (HTTP {resp.status_code}): {resp.text[:200]}")

    os.remove(img_path)
    raise RuntimeError("Failed after retries")


def main():
    doc = fitz.open(PDF_PATH)
    total_pages = len(doc)
    content_pages = list(range(START_PAGE, min(END_PAGE + 1, total_pages)))
    total_content = len(content_pages)
    print(f"PDF has {total_pages} pages, processing {total_content} content pages ({START_PAGE+1}-{END_PAGE+1})")

    state = load_checkpoint()
    if "skipped" not in state:
        state["skipped"] = []

    remaining = [p for p in content_pages if str(p) not in state["completed_pages"]]
    done_count = total_content - len(remaining)
    print(f"Already done: {done_count}, Remaining: {len(remaining)}")

    if not remaining:
        print("All pages already completed!")
    else:
        for page_num in remaining:
            done = len([p for p in content_pages if str(p) in state["completed_pages"]])
            print(f"Page {page_num+1}/{total_pages} ({done}/{total_content} done)...", end=" ", flush=True)
            try:
                text = ocr_page(page_num, doc)
                state["completed_pages"][str(page_num)] = text
                save_checkpoint(state)
                preview = text[:50].replace("\n", " ")
                print(f"OK ({len(text)} chars) {preview}...")
            except RuntimeError as e:
                state["skipped"].append(page_num)
                save_checkpoint(state)
                print(f"SKIP: {e}")
            time.sleep(0.3)

    doc.close()

    # Retry skipped pages
    skipped = [p for p in state.get("skipped", []) if str(p) not in state["completed_pages"]]
    if skipped:
        print(f"\nRetrying {len(skipped)} skipped pages...")
        doc = fitz.open(PDF_PATH)
        for page_num in skipped:
            print(f"  Retry page {page_num+1}...", end=" ", flush=True)
            try:
                text = ocr_page(page_num, doc)
                state["completed_pages"][str(page_num)] = text
                state["skipped"] = [s for s in state["skipped"] if s != page_num]
                save_checkpoint(state)
                print("OK")
            except RuntimeError as e:
                print(f"FAIL: {e}")
            time.sleep(0.3)
        doc.close()

    # Write output
    with open(OUTPUT_FILE, "w") as f:
        for i in content_pages:
            key = str(i)
            if key in state["completed_pages"]:
                f.write(f"--- Page {i + 1} ---\n")
                f.write(state["completed_pages"][key])
                f.write("\n\n")

    done = len([p for p in content_pages if str(p) in state["completed_pages"]])
    still_skipped = [p+1 for p in state.get("skipped", []) if str(p) not in state["completed_pages"]]
    print(f"\nWrote {done}/{total_content} pages to {OUTPUT_FILE}")
    if still_skipped:
        print(f"Still skipped: {still_skipped}")
    else:
        print("All pages complete!")


if __name__ == "__main__":
    main()
