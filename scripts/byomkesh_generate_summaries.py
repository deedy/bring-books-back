"""Generate chapter summaries for all Byomkesh stories — massively parallel.

Usage:
    uv run python scripts/byomkesh_generate_summaries.py
"""

import json
import os
import glob
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

WEB_DATA = "web/public/data/books"
MODEL = "google/gemini-2.5-flash-lite"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)


def generate_summary(story_id: str, chapter: dict, story_title: str) -> tuple[str, int, str]:
    """Generate a 1-2 sentence summary for a chapter."""
    num = chapter["number"]
    title = chapter["title"]
    paras = chapter["paragraphs"]

    # Use first ~2000 words and last ~500 words for context
    text = "\n\n".join(paras)
    if len(text) > 8000:
        first = "\n\n".join(paras[:15])[:6000]
        last = "\n\n".join(paras[-5:])[:2000]
        text = first + "\n\n[...]\n\n" + last

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Write a 1-2 sentence chapter summary (max 30 words). "
                    "Capture the key event or turning point. "
                    "Use present tense. No spoilers for the resolution. "
                    "Output ONLY the summary text, nothing else."
                ),
            },
            {
                "role": "user",
                "content": f'Story: "{story_title}"\nChapter {num}: "{title}"\n\n{text}',
            },
        ],
        temperature=0.3,
        max_tokens=100,
    )
    summary = response.choices[0].message.content.strip().strip('"')
    print(f"  {story_id} ch {num}: {summary}", flush=True)
    return story_id, num, summary


def main():
    # Collect all chapters needing summaries
    tasks = []
    story_titles = {}

    for meta_path in sorted(glob.glob(f"{WEB_DATA}/byomkesh-*/meta.json")):
        sid = os.path.basename(os.path.dirname(meta_path))
        with open(meta_path) as f:
            meta = json.load(f)
        story_titles[sid] = meta["title"]

        chapters_path = f"{WEB_DATA}/{sid}/chapters.json"
        with open(chapters_path) as f:
            data = json.load(f)

        for ch in data["chapters"]:
            if not ch.get("summary"):
                tasks.append((sid, ch, meta["title"]))

    if not tasks:
        print("All chapters already have summaries!")
        return

    print(f"Generating {len(tasks)} summaries with 20 workers...\n", flush=True)

    # Massively parallel — these are tiny LLM calls
    results = []
    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = {
            pool.submit(generate_summary, sid, ch, title): (sid, ch["number"])
            for sid, ch, title in tasks
        }
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                sid, num = futures[future]
                print(f"  ERROR {sid} ch {num}: {e}", flush=True)

    # Group results by story and update chapters.json
    by_story = {}
    for sid, num, summary in results:
        by_story.setdefault(sid, {})[num] = summary

    for sid, summaries in by_story.items():
        chapters_path = f"{WEB_DATA}/{sid}/chapters.json"
        with open(chapters_path) as f:
            data = json.load(f)
        for ch in data["chapters"]:
            if ch["number"] in summaries:
                ch["summary"] = summaries[ch["number"]]
        with open(chapters_path, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nDone! {len(results)} summaries generated across {len(by_story)} stories.", flush=True)


if __name__ == "__main__":
    main()
