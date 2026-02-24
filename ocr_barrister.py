import fitz
import requests
import json
import os
import time
import threading
from dotenv import load_dotenv

load_dotenv()

API_KEYS = [
    "sk_8mhg147t_gPo9py5YnqXhpfdiGETu4Ido",
    "sk_p7nr9ycc_CHkNEUcb5WfUh1pjuWMtOoAK",
    "sk_mt4pdzme_UZicBzLEe6OoCyKrWEavX5JQ",
]

PDF_PATH = "data/barrister-paarvatiishan.pdf"
OUTPUT_FILE = "data/barrister_ocr.txt"
CHECKPOINT_FILE = "data/barrister_ocr_checkpoint.json"

lock = threading.Lock()


def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE) as f:
            return json.load(f)
    return {"completed_pages": {}, "last_page": -1, "skipped": []}


def save_checkpoint(state):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(state, f)


def ocr_page(page_num, doc, thread_id=0, retries=5):
    """OCR a page, rotating through all API keys on failure."""
    page = doc[page_num]
    pix = page.get_pixmap(dpi=200)
    img_path = f"/tmp/sarvam_barrister_t{thread_id}_{page_num}.png"
    pix.save(img_path)

    url = "https://api.sarvam.ai/vision"
    last_error = None

    for attempt in range(retries):
        # Rotate through API keys on each attempt
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
            # This key is exhausted, try next key
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

    os.remove(img_path)
    raise RuntimeError(f"Failed after {retries} retries: {last_error}")


def worker(thread_id, primary_key, pages_to_do, state, total_pages):
    key_label = primary_key[-4:]
    doc = fitz.open(PDF_PATH)
    for page_num in pages_to_do:
        key = str(page_num)
        with lock:
            if key in state["completed_pages"]:
                continue

        try:
            text = ocr_page(page_num, doc, thread_id)
            with lock:
                state["completed_pages"][key] = text
                save_checkpoint(state)
                done = len(state["completed_pages"])
            preview = text[:50].replace("\n", " ")
            print(f"  [t{thread_id}] Page {page_num+1}/{total_pages} OK ({done}/{total_pages} total) {preview}...")
        except RuntimeError as e:
            with lock:
                if "skipped" not in state:
                    state["skipped"] = []
                state["skipped"].append(page_num)
                save_checkpoint(state)
            print(f"  [t{thread_id}] Page {page_num+1}/{total_pages} FAILED: {e}")
        time.sleep(0.3)
    doc.close()


def main():
    doc = fitz.open(PDF_PATH)
    total_pages = len(doc)
    print(f"PDF has {total_pages} pages")

    state = load_checkpoint()
    if "skipped" not in state:
        state["skipped"] = []

    remaining = [i for i in range(total_pages) if str(i) not in state["completed_pages"]]
    print(f"Already done: {len(state['completed_pages'])}, Remaining: {len(remaining)}")

    if not remaining:
        print("All pages already completed!")
    else:
        # Split remaining pages across 3 threads (round-robin)
        chunks = [[], [], []]
        for i, page_num in enumerate(remaining):
            chunks[i % 3].append(page_num)

        for i, chunk in enumerate(chunks):
            print(f"  Thread {i+1}: {len(chunk)} pages")

        threads = []
        for i in range(3):
            t = threading.Thread(target=worker, args=(i, API_KEYS[i], chunks[i], state, total_pages))
            t.start()
            threads.append(t)
            time.sleep(0.5)  # stagger starts slightly

        for t in threads:
            t.join()

    doc.close()

    # Write output
    with open(OUTPUT_FILE, "w") as f:
        for i in range(total_pages):
            key = str(i)
            if key in state["completed_pages"]:
                f.write(f"--- Page {i + 1} ---\n")
                f.write(state["completed_pages"][key])
                f.write("\n\n")

    done = len(state["completed_pages"])
    skipped = [p+1 for p in state.get("skipped", []) if str(p) not in state["completed_pages"]]
    print(f"\nWrote {done}/{total_pages} pages to {OUTPUT_FILE}")
    if skipped:
        print(f"Still skipped: {skipped}")


if __name__ == "__main__":
    main()
