import fitz
import requests
import json
import os
import sys
import time

from dotenv import load_dotenv
load_dotenv()

API_KEY = os.environ["SARVAM_KEY"]
PDF_PATH = "data/baeesweensadi.pdf"
OUTPUT_FILE = "data/baeesweensadi_ocr.txt"
CHECKPOINT_FILE = "data/baeesweensadi_checkpoint.json"

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE) as f:
            return json.load(f)
    return {"completed_pages": {}, "last_page": -1}

def save_checkpoint(state):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(state, f)

def ocr_page(page_num, doc):
    page = doc[page_num]
    pix = page.get_pixmap(dpi=200)
    img_path = f"/tmp/sarvam_page_{page_num}.png"
    pix.save(img_path)

    url = "https://api.sarvam.ai/vision"
    headers = {"API-Subscription-Key": API_KEY}
    with open(img_path, "rb") as f:
        files = {"file": ("page.png", f, "image/png")}
        data = {"prompt_type": "default_ocr"}
        resp = requests.post(url, headers=headers, files=files, data=data)

    os.remove(img_path)

    if resp.status_code == 200:
        result = resp.json()
        return result.get("content", "")
    elif resp.status_code in (402, 429):
        raise RuntimeError(f"CREDITS EXHAUSTED or RATE LIMITED (HTTP {resp.status_code}): {resp.text}")
    else:
        raise RuntimeError(f"API error (HTTP {resp.status_code}): {resp.text}")

def main():
    doc = fitz.open(PDF_PATH)
    total_pages = len(doc)
    print(f"PDF has {total_pages} pages")

    state = load_checkpoint()
    start_page = state["last_page"] + 1

    if start_page > 0:
        print(f"Resuming from page {start_page + 1}/{total_pages} (checkpoint found)")

    for page_num in range(start_page, total_pages):
        print(f"Processing page {page_num + 1}/{total_pages}...", end=" ", flush=True)
        try:
            text = ocr_page(page_num, doc)
            state["completed_pages"][str(page_num)] = text
            state["last_page"] = page_num
            save_checkpoint(state)
            preview = text[:60].replace("\n", " ")
            print(f"OK ({len(text)} chars) {preview}...")
        except RuntimeError as e:
            save_checkpoint(state)
            print(f"\n\n*** STOPPED at page {page_num + 1}/{total_pages}: {e}")
            print(f"*** Checkpoint saved. Re-run this script to resume.")
            break
        # small delay to be polite to the API
        time.sleep(0.3)

    doc.close()

    # Write final output
    with open(OUTPUT_FILE, "w") as f:
        for i in range(total_pages):
            key = str(i)
            if key in state["completed_pages"]:
                f.write(f"--- Page {i + 1} ---\n")
                f.write(state["completed_pages"][key])
                f.write("\n\n")

    done = len(state["completed_pages"])
    print(f"\nWrote {done}/{total_pages} pages to {OUTPUT_FILE}")
    if done == total_pages:
        print("All pages complete!")
    else:
        print(f"Incomplete — re-run to resume from page {state['last_page'] + 2}")

if __name__ == "__main__":
    main()
