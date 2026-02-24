import os
import json
import re
import tiktoken
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

INPUT_FILE = "data/alaler_ocr.txt"
OUTPUT_FILE = "data/alaler_english.txt"
CHECKPOINT_FILE = "data/alaler_translate_checkpoint.json"
MODEL = "gpt-4.1"

# Novel pages only (skip front matter and appendix)
# Adjust these after inspecting OCR output
START_PAGE = 24
END_PAGE = 158

client = OpenAI(api_key=OPENAI_API_KEY)
enc = tiktoken.encoding_for_model("gpt-4o")

SYSTEM_PROMPT = (
    "You are translating a Bengali novel titled 'Alaler Gharer Dulal' "
    "(The Spoilt Child) by Peary Chand Mitra (pen name Tekchand Thakur), "
    "written in 1858. This is considered the first Bengali novel, a social "
    "satire about the moral decline of a wealthy family in colonial Calcutta. "
    "The language is colloquial Bengali (Alali bhasha). Translate into fluent, "
    "literary English. Preserve paragraph breaks and the original tone and style. "
    "Preserve the humor and satirical edge. Do not add commentary — output only "
    "the English translation. Do NOT skip or summarize any content."
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


def translate_page(page_num, page_text):
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
        raise RuntimeError(f"API error: {e}")


def main():
    with open(INPUT_FILE) as f:
        text = f.read()

    all_pages = split_into_pages(text)
    # Filter to novel pages only
    pages = {k: v for k, v in all_pages.items() if START_PAGE <= k <= END_PAGE}
    total = len(pages)
    page_nums = sorted(pages.keys())
    print(f"Found {len(all_pages)} total OCR pages")
    print(f"Translating novel pages {START_PAGE}-{END_PAGE}: {total} pages")

    state = load_checkpoint()

    for page_num in page_nums:
        key = str(page_num)
        if key in state["completed_pages"]:
            print(f"Page {page_num}/{page_nums[-1]}: cached, skipping")
            continue

        page_text = pages[page_num]
        toks = len(enc.encode(page_text))
        print(f"Page {page_num}/{page_nums[-1]} ({toks} tokens)...", end=" ", flush=True)

        try:
            translation = translate_page(page_num, page_text)
            state["completed_pages"][key] = translation
            save_checkpoint(state)
            preview = translation[:70].replace("\n", " ")
            print(f"OK — {preview}...")
        except RuntimeError as e:
            save_checkpoint(state)
            print(f"\n\n*** STOPPED at page {page_num}: {e}")
            print("*** Checkpoint saved. Re-run to resume.")
            break

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
        print(f"All {total} pages translated!")
    else:
        print(f"Incomplete — re-run to resume.")


if __name__ == "__main__":
    main()
