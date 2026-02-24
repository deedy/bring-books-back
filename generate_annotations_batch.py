#!/usr/bin/env python3
"""
Generate annotations.json for any book using GPT-4.1.
Usage: python generate_annotations_batch.py <book-id>

Map phase: fire all chapters in parallel via asyncio.
Reduce phase: merge glossaries, dedupe, verify terms against text.
"""

import asyncio
import json
import sys
from pathlib import Path
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI()
MAX_CONCURRENT = 10

# Book-specific system prompts
BOOK_PROMPTS = {
    "baeesween-sadi": """You are a literary analyst helping annotate an English translation of "Baeesween Sadi" (The Twenty-Second Century, 1924), a Hindi science fiction novel by Rahul Sankrityayan. The translation preserves many Hindi proper nouns, cultural terms, and futuristic vocabulary.

For the given chapter text, extract three categories of terms that a modern English reader might want explained:

1. **Characters** — Recurring named people. Give a 1-2 sentence description of who they are and their role.
2. **Proper nouns** — Place names, cultural terms, historical references, Hindi/Sanskrit terms, scientific concepts, geographical references, etc. Give a brief explanation.
3. **Vocabulary** — Archaic, vernacular, or culturally-specific words/phrases (e.g., "kos", "vimana", "ashram") that might be unfamiliar. Give a brief definition.

Rules:
- Only extract terms that actually appear in the chapter text (exact spelling match).
- For character names, use the exact form that appears in the text.
- Keep descriptions concise: 1-2 sentences max.
- Do NOT extract common English words.
- Focus on terms that are clearly Hindi/Sanskrit/Indian in origin, or specific to the futuristic setting.
- Return valid JSON only, no markdown fences.""",

    "mrinalini": """You are a literary analyst helping annotate an English translation of "Mrinalini" (1882), a historical romance set in 13th-century Bengal by Bankim Chandra Chattopadhyay. The translation preserves many Bengali proper nouns, historical terms, and cultural vocabulary.

For the given chapter text, extract three categories of terms that a modern English reader might want explained:

1. **Characters** — Recurring named people. Give a 1-2 sentence description of who they are and their role.
2. **Proper nouns** — Place names, kingdoms, battles, cultural terms, historical references, caste names, religious terms, etc. Give a brief explanation.
3. **Vocabulary** — Archaic, vernacular, or culturally-specific words/phrases (e.g., "Yavan", "sannyasi", "ghat") that might be unfamiliar. Give a brief definition.

Rules:
- Only extract terms that actually appear in the chapter text (exact spelling match).
- For character names, use the exact form that appears in the text.
- Keep descriptions concise: 1-2 sentences max.
- Do NOT extract common English words.
- Focus on terms that are clearly Bengali/Indian in origin, or specific historical references to the Bakhtiyar Khilji invasion period.
- Return valid JSON only, no markdown fences.""",

    "ponniyin-selvan": """You are a literary analyst helping annotate an English translation of "Ponniyin Selvan" (1955), an epic historical novel set in 10th-century Chola dynasty India by Kalki Krishnamurthy. The translation preserves many Tamil proper nouns, historical terms, and cultural vocabulary.

For the given chapter text, extract three categories of terms that a modern English reader might want explained:

1. **Characters** — Recurring named people. Give a 1-2 sentence description of who they are and their role in the Chola court/story.
2. **Proper nouns** — Place names (cities, temples, rivers), kingdom names, dynasty references, cultural terms, religious terms, festival names, etc. Give a brief explanation.
3. **Vocabulary** — Archaic, vernacular, or culturally-specific words/phrases (e.g., "palanquin", "thambiran", "kumkum") that might be unfamiliar. Give a brief definition.

Rules:
- Only extract terms that actually appear in the chapter text (exact spelling match).
- For character names, use the exact form that appears in the text (e.g., "Vandiyathevan" not "Vallavaraiyan").
- Keep descriptions concise: 1-2 sentences max.
- Do NOT extract common English words.
- Focus on terms that are clearly Tamil/Indian in origin, or specific to the Chola dynasty period.
- Return valid JSON only, no markdown fences.""",

    "barrister-parvatishan": """You are a literary analyst helping annotate an English translation of "Barrister Parvatishan" (1924), a humorous Telugu novel by Mokkapati Narasimha Shastri about a naive young Brahmin's misadventures traveling to England. The translation preserves many Telugu proper nouns, cultural terms, and period vocabulary.

For the given chapter text, extract three categories of terms that a modern English reader might want explained:

1. **Characters** — Recurring named people. Give a 1-2 sentence description of who they are and their role.
2. **Proper nouns** — Place names, cultural terms, historical references, caste references, religious terms, British/Indian colonial terms, etc. Give a brief explanation.
3. **Vocabulary** — Archaic, vernacular, or culturally-specific words/phrases (e.g., "dhoti", "munshi", "tiffin") that might be unfamiliar. Give a brief definition.

Rules:
- Only extract terms that actually appear in the chapter text (exact spelling match).
- For character names, use the exact form that appears in the text.
- Keep descriptions concise: 1-2 sentences max.
- Do NOT extract common English words.
- Focus on terms that are clearly Telugu/Indian in origin, or specific to early 20th century colonial India/England.
- Return valid JSON only, no markdown fences.""",
}

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


async def extract_chapter_terms(sem: asyncio.Semaphore, chapter: dict, system_prompt: str, book_id: str) -> tuple[str, dict, dict]:
    async with sem:
        text = "\n\n".join(chapter["paragraphs"])
        prompt = USER_PROMPT_TEMPLATE.format(
            number=chapter["number"],
            title=chapter["title"],
            text=text,
        )

        for attempt in range(3):
            try:
                response = await client.chat.completions.create(
                    model="gpt-4.1",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"},
                )

                raw = response.choices[0].message.content
                result = json.loads(raw)
                print(f"  [{book_id}] ch-{chapter['number']}: {chapter['title']}", flush=True)
                return chapter["id"], result, chapter
            except Exception as e:
                if attempt < 2:
                    print(f"  [{book_id}] ch-{chapter['number']}: retry {attempt+1} ({e})")
                    await asyncio.sleep(5 * (attempt + 1))
                else:
                    print(f"  [{book_id}] ch-{chapter['number']}: FAILED ({e})")
                    return chapter["id"], {"characters": {}, "proper_nouns": {}, "vocabulary": {}}, chapter


def reduce_results(results: list[tuple[str, dict, dict]], book_id: str) -> dict:
    glossary: dict[str, dict] = {}
    chapter_terms: dict[str, list[str]] = {}

    for ch_id, result, chapter in results:
        terms_in_chapter = []

        for type_key, type_label in [("characters", "character"), ("proper_nouns", "proper_noun"), ("vocabulary", "vocabulary")]:
            for name, desc in result.get(type_key, {}).items():
                if name not in glossary:
                    glossary[name] = {"type": type_label, "description": desc}
                terms_in_chapter.append(name)

        text = "\n".join(chapter["paragraphs"])
        verified = [t for t in terms_in_chapter if t in text]
        chapter_terms[ch_id] = verified

        filtered = len(terms_in_chapter) - len(verified)
        if filtered:
            print(f"  [{book_id}] {ch_id}: filtered {filtered} hallucinated terms")

    used = set()
    for terms in chapter_terms.values():
        used.update(terms)
    glossary = {k: v for k, v in glossary.items() if k in used}

    return {"glossary": glossary, "chapters": chapter_terms}


async def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <book-id>")
        print(f"Available: {', '.join(BOOK_PROMPTS.keys())}")
        sys.exit(1)

    book_id = sys.argv[1]
    if book_id not in BOOK_PROMPTS:
        print(f"Unknown book: {book_id}")
        print(f"Available: {', '.join(BOOK_PROMPTS.keys())}")
        sys.exit(1)

    chapters_path = Path(f"web/public/data/books/{book_id}/chapters.json")
    output_path = Path(f"web/public/data/books/{book_id}/annotations.json")
    system_prompt = BOOK_PROMPTS[book_id]

    with open(chapters_path) as f:
        data = json.load(f)
    chapters = data["chapters"]

    print(f"[{book_id}] {len(chapters)} chapters, max {MAX_CONCURRENT} concurrent")
    sem = asyncio.Semaphore(MAX_CONCURRENT)

    tasks = [extract_chapter_terms(sem, ch, system_prompt, book_id) for ch in chapters]
    results = await asyncio.gather(*tasks)

    # Sort by chapter id parts (handles ch-1, ch-1-1, ch-5-91, etc.)
    def sort_key(r):
        parts = r[0].replace("ch-", "").split("-")
        return tuple(int(p) for p in parts)
    results.sort(key=sort_key)

    print(f"\n[{book_id}] Reducing {len(results)} results...")
    output = reduce_results(results, book_id)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    g = output["glossary"]
    chars = sum(1 for v in g.values() if v["type"] == "character")
    nouns = sum(1 for v in g.values() if v["type"] == "proper_noun")
    vocab = sum(1 for v in g.values() if v["type"] == "vocabulary")
    print(f"\n[{book_id}] Done! {len(g)} entries ({chars} characters, {nouns} proper nouns, {vocab} vocabulary) → {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
