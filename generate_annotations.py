#!/usr/bin/env python3
"""
Generate annotations.json for a book using GPT-4.1.
Map phase: fire all 30 chapters in parallel via asyncio.
Reduce phase: merge glossaries, dedupe, verify terms against text.
"""

import asyncio
import json
from pathlib import Path
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI()

BOOK_ID = "alaler-gharer-dulal"
CHAPTERS_PATH = Path(f"web/public/data/books/{BOOK_ID}/chapters.json")
OUTPUT_PATH = Path(f"web/public/data/books/{BOOK_ID}/annotations.json")
MAX_CONCURRENT = 10  # parallel requests

SYSTEM_PROMPT = """You are a literary analyst helping annotate an English translation of "Alaler Gharer Dulal" (1858), the first Bengali novel by Peary Chand Mitra. The translation preserves many Bengali proper nouns, cultural terms, and archaic vocabulary.

For the given chapter text, extract three categories of terms that a modern English reader might want explained:

1. **Characters** — Recurring named people. Give a 1-2 sentence description of who they are and their role.
2. **Proper nouns** — Place names, cultural terms, historical references, caste names, religious terms, festival names, etc. Give a brief explanation.
3. **Vocabulary** — Archaic, vernacular, or culturally-specific English words/phrases (e.g., "tole", "munshi", "chadar", "paisa") that might be unfamiliar. Give a brief definition.

Rules:
- Only extract terms that actually appear in the chapter text (exact spelling match).
- For character names, use the exact form that appears in the text (e.g., "Baburam Babu" not just "Baburam").
- Keep descriptions concise: 1-2 sentences max.
- Do NOT extract common English words, even if slightly old-fashioned (e.g., "obsequiousness" is fine to skip).
- Focus on terms that are clearly Bengali/Indian in origin, or highly specific cultural references.
- Return valid JSON only, no markdown fences."""

USER_PROMPT_TEMPLATE = """Chapter {number}: "{title}"

Text:
{text}

Return a JSON object with this exact structure:
{{
  "characters": {{
    "Name As In Text": "1-2 sentence description"
  }},
  "proper_nouns": {{
    "Term As In Text": "1-2 sentence explanation"
  }},
  "vocabulary": {{
    "term": "brief definition"
  }}
}}"""


async def extract_chapter_terms(sem: asyncio.Semaphore, chapter: dict) -> tuple[str, dict, dict]:
    """Map: send one chapter to GPT-4.1, return (ch_id, raw_result, chapter)."""
    async with sem:
        text = "\n\n".join(chapter["paragraphs"])
        prompt = USER_PROMPT_TEMPLATE.format(
            number=chapter["number"],
            title=chapter["title"],
            text=text,
        )

        response = await client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        result = json.loads(raw)
        print(f"  ✓ ch-{chapter['number']}: {chapter['title']}")
        return chapter["id"], result, chapter


def reduce_results(results: list[tuple[str, dict, dict]]) -> dict:
    """Reduce: merge all chapter results into a single annotations.json."""
    glossary: dict[str, dict] = {}
    chapter_terms: dict[str, list[str]] = {}

    for ch_id, result, chapter in results:
        terms_in_chapter = []

        for type_key, type_label in [("characters", "character"), ("proper_nouns", "proper_noun"), ("vocabulary", "vocabulary")]:
            for name, desc in result.get(type_key, {}).items():
                # First description wins (from earliest chapter)
                if name not in glossary:
                    glossary[name] = {"type": type_label, "description": desc}
                terms_in_chapter.append(name)

        # Verify each term actually appears in the chapter text
        text = "\n".join(chapter["paragraphs"])
        verified = [t for t in terms_in_chapter if t in text]
        chapter_terms[ch_id] = verified

        filtered = len(terms_in_chapter) - len(verified)
        if filtered:
            print(f"  {ch_id}: filtered {filtered} hallucinated terms")

    # Remove glossary entries not in any chapter
    used = set()
    for terms in chapter_terms.values():
        used.update(terms)
    glossary = {k: v for k, v in glossary.items() if k in used}

    return {"glossary": glossary, "chapters": chapter_terms}


async def main():
    with open(CHAPTERS_PATH) as f:
        data = json.load(f)
    chapters = data["chapters"]

    print(f"Firing {len(chapters)} chapters in parallel (max {MAX_CONCURRENT} concurrent)...")
    sem = asyncio.Semaphore(MAX_CONCURRENT)

    # Map: all chapters in parallel
    tasks = [extract_chapter_terms(sem, ch) for ch in chapters]
    results = await asyncio.gather(*tasks)

    # Sort by chapter id to get stable "first description wins" order
    results.sort(key=lambda r: int(r[0].split("-")[1]))

    print(f"\nReducing {len(results)} results...")
    output = reduce_results(results)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nDone! {len(output['glossary'])} glossary entries → {OUTPUT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
