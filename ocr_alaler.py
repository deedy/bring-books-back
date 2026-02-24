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

PDF_PATH = "data/alaler-gharer-book.pdf"
OUTPUT_FILE = "data/alaler_ocr.txt"
CHECKPOINT_FILE = "data/alaler_ocr_checkpoint.json"

lock = threading.Lock()


def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE) as f:
            return json.load(f)
    return {"completed_pages": {}, "last_page": -1, "skipped": []}


def save_checkpoint(state):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(state, f)


def ocr_page(page_num, doc, api_key, thread_id=0, retries=5):
    page = doc[page_num]
    pix = page.get_pixmap(dpi=200)
    img_path = f"/tmp/sarvam_alaler_t{thread_id}_{page_num}.png"
    pix.save(img_path)

    url = "https://api.sarvam.ai/vision"
    headers = {"API-Subscription-Key": api_key}

    for attempt in range(retries):
        try:
            with open(img_path, "rb") as f:
                files = {"file": ("page.png", f, "image/png")}
                data = {"prompt_type": "default_ocr"}
                resp = requests.post(url, headers=headers, files=files, data=data, timeout=60)
        except requests.exceptions.Timeout:
            if attempt < retries - 1:
                time.sleep(10)
                continue
            os.remove(img_path)
            raise RuntimeError("Request timeout after retries")
        except requests.exceptions.ConnectionError:
            if attempt < retries - 1:
                time.sleep(10)
                continue
            os.remove(img_path)
            raise RuntimeError("Connection error after retries")

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
            raise RuntimeError(f"API error (HTTP {resp.status_code})")

    os.remove(img_path)
    raise RuntimeError("Failed after retries")


def worker(thread_id, api_key, pages_to_do, state):
    key_label = api_key[-4:]
    doc = fitz.open(PDF_PATH)
    for page_num in pages_to_do:
        key = str(page_num)
        with lock:
            if key in state["completed_pages"]:
                continue

        try:
            text = ocr_page(page_num, doc, api_key, thread_id)
            with lock:
                state["completed_pages"][key] = text
                save_checkpoint(state)
                done = len(state["completed_pages"])
            preview = text[:50].replace("\n", " ")
            print(f"  [{key_label}] Page {page_num+1}/190 OK ({done}/190 total) {preview}...")
        except RuntimeError as e:
            with lock:
                if "skipped" not in state:
                    state["skipped"] = []
                state["skipped"].append(page_num)
                save_checkpoint(state)
            print(f"  [{key_label}] Page {page_num+1}/190 FAILED: {e}")
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
            print(f"  Thread {i+1} ({API_KEYS[i][-4:]}): {len(chunk)} pages")

        threads = []
        for i in range(3):
            t = threading.Thread(target=worker, args=(i, API_KEYS[i], chunks[i], state))
            t.start()
            threads.append(t)
            time.sleep(0.5)  # stagger starts slightly

        for t in threads:
            t.join()

    doc.close()  # close the main doc used for page count

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
