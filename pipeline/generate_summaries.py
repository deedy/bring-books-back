"""Generate 1-2 sentence summaries for Feluda story-book chapters using GPT-4.1 via OpenRouter."""

import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

BASE = Path(__file__).resolve().parent.parent
BOOKS_DIR = BASE / "web" / "public" / "data" / "books"
ANTHOLOGY_PATH = BOOKS_DIR / "feluda" / "anthology.json"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

SYSTEM_PROMPT = (
    "You are summarizing chapters of a detective story for a book website. "
    "Given chapter text, write a 1-2 sentence summary that describes what happens in this chapter. "
    "Be concise and intriguing without major spoilers. Return valid JSON: {\"summary\": \"...\"}"
)


def get_first_n_words(paragraphs: list[str], n: int = 1000) -> str:
    """Get approximately the first n words from paragraphs."""
    text = " ".join(paragraphs)
    words = text.split()
    return " ".join(words[:n])


def generate_summary(chapter_text: str) -> str:
    """Call GPT-4.1 to generate a chapter summary."""
    resp = client.chat.completions.create(
        model="openai/gpt-4.1",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": chapter_text},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    content = resp.choices[0].message.content
    data = json.loads(content)
    return data["summary"]


def summarize_chapter(book_id: str, chapter_idx: int, chapter_text: str) -> tuple[str, int, str]:
    """Summarize a single chapter. Returns (book_id, chapter_idx, summary)."""
    summary = generate_summary(chapter_text)
    return (book_id, chapter_idx, summary)


def main():
    with open(ANTHOLOGY_PATH) as f:
        anthology = json.load(f)

    book_ids = anthology["storyBookIds"]

    # Load all book data and collect all chapter tasks
    book_data: dict[str, dict] = {}  # book_id -> parsed JSON
    tasks: list[tuple[str, int, str]] = []  # (book_id, chapter_idx, text)

    for bid in book_ids:
        chapters_path = BOOKS_DIR / bid / "chapters.json"
        if not chapters_path.exists():
            continue
        with open(chapters_path) as f:
            data = json.load(f)
        book_data[bid] = data
        for i, ch in enumerate(data["chapters"]):
            if ch.get("summary"):
                continue
            text = get_first_n_words(ch.get("paragraphs", []), 1000)
            if text.strip():
                tasks.append((bid, i, text))

    print(f"Submitting {len(tasks)} chapter summary tasks across {len(book_ids)} books with 15 workers...\n")

    if not tasks:
        print("All chapters already have summaries.")
        return

    # Track results per book for writing back
    lock = threading.Lock()
    completed = 0
    errors = 0

    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {
            executor.submit(summarize_chapter, bid, idx, text): (bid, idx)
            for bid, idx, text in tasks
        }
        for future in as_completed(futures):
            bid, idx = futures[future]
            try:
                _, _, summary = future.result()
                with lock:
                    book_data[bid]["chapters"][idx]["summary"] = summary
                    completed += 1
                ch = book_data[bid]["chapters"][idx]
                print(f"  [{completed}/{len(tasks)}] {bid} ch-{ch['number']}: {summary[:80]}...")
            except Exception as e:
                with lock:
                    errors += 1
                print(f"  ERROR {bid} ch-{idx}: {e}")

    # Write back all modified books
    written = 0
    for bid, data in book_data.items():
        chapters_path = BOOKS_DIR / bid / "chapters.json"
        with open(chapters_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        written += 1

    print(f"\nDone. {completed} chapters summarized, {errors} errors, {written} files written.")


if __name__ == "__main__":
    main()
