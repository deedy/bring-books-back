"""Translate Ponniyin Selvan OCR text from Tamil to English using GPT-4.1.
Batched concurrent translation for maximum throughput.
Output is used by BOTH the PDF generator and web JSON generator.
"""

import os
import json
import re
import time
import threading
import concurrent.futures
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv()

INPUT_FILE = "data/ponniyin_ocr.txt"
OUTPUT_FILE = "data/ponniyin_english.txt"
CHECKPOINT_FILE = "data/ponniyin_translate_checkpoint.json"
MODEL = "gpt-4.1"
MAX_WORKERS = 20  # concurrent translation threads

# Rotate between two API keys for 2x throughput
API_KEYS = [
    os.environ["OPENAI_API_KEY"],
    os.environ.get("OPENAI_API_KEY_2", os.environ["OPENAI_API_KEY"]),
]
clients = [OpenAI(api_key=k) for k in API_KEYS]

import itertools
_key_cycle = itertools.cycle(range(len(clients)))

SYSTEM_PROMPT = (
    "You are translating the Tamil historical novel 'Ponniyin Selvan' "
    "(The Son of Ponni / The River's Prince) by Kalki Krishnamurthy, "
    "written between 1950-1955. This is one of the greatest Tamil novels ever written, "
    "a sprawling historical epic set in the 10th century Chola dynasty. "
    "The story follows Vandiyathevan's journey through political intrigue, "
    "romance, and war during the reign of Sundara Chola. "
    "Translate into fluent, literary English. Preserve paragraph breaks "
    "and the original dramatic, vivid tone. Preserve character names in "
    "their Tamil transliteration (e.g., Vandiyathevan, Kundavai, Arulmozhi). "
    "Do not add commentary — output only the English translation. "
    "Do NOT skip or summarize any content."
)


def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE) as f:
            return json.load(f)
    return {"completed_pages": {}}


def save_checkpoint(state):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(state, f, ensure_ascii=False)


def split_into_pages(text):
    """Split the OCR text into individual pages."""
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


_key_lock = threading.Lock()

def translate_page(page_num, page_text, retries=3):
    # Round-robin across API keys
    with _key_lock:
        client_idx = next(_key_cycle)
    client = clients[client_idx]

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
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
    page_num, page_text, state, total, page_nums = args
    key = str(page_num)

    with checkpoint_lock:
        if key in state["completed_pages"]:
            return page_num, None, True  # already done

    try:
        translation = translate_page(page_num, page_text)
        with checkpoint_lock:
            state["completed_pages"][key] = translation
            save_checkpoint(state)
            done = len(state["completed_pages"])
        preview = translation[:60].replace("\n", " ")
        print(f"  Page {page_num}/{page_nums[-1]} ({done}/{total} done) — {preview}...")
        return page_num, translation, True
    except RuntimeError as e:
        print(f"  Page {page_num}/{page_nums[-1]} FAILED: {e}")
        return page_num, None, False


def main():
    with open(INPUT_FILE) as f:
        text = f.read()

    all_pages = split_into_pages(text)
    page_nums = sorted(all_pages.keys())
    total = len(page_nums)
    print(f"Found {total} OCR pages to translate")

    state = load_checkpoint()
    already = len(state["completed_pages"])
    print(f"Already translated: {already}")

    remaining = [(pn, all_pages[pn]) for pn in page_nums if str(pn) not in state["completed_pages"]]
    print(f"Remaining: {len(remaining)}")

    if not remaining:
        print("All pages already translated!")
    else:
        print(f"Starting translation with {MAX_WORKERS} concurrent workers...")
        args_list = [(pn, txt, state, total, page_nums) for pn, txt in remaining]

        failed = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(translate_worker, args): args[0] for args in args_list}
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

    # Write final output
    with open(OUTPUT_FILE, "w") as f:
        for page_num in page_nums:
            key = str(page_num)
            if key in state["completed_pages"]:
                f.write(f"--- Page {page_num} ---\n")
                f.write(state["completed_pages"][key])
                f.write("\n\n")

    done = len(state["completed_pages"])
    print(f"\nWrote {done}/{total} pages to {OUTPUT_FILE}")
    if done == total:
        print("All pages translated!")
    else:
        print(f"Incomplete — re-run to resume.")


if __name__ == "__main__":
    main()
