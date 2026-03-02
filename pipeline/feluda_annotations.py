"""Generate annotations.json for all 35 Feluda story-books.

Usage:
    uv run python -m pipeline.feluda_annotations
    uv run python -m pipeline.feluda_annotations --force
    uv run python -m pipeline.feluda_annotations --story feluda-danger-in-darjeeling
"""

import argparse
import asyncio
import json
import os
from pathlib import Path
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
WEB_BOOKS_DIR = PROJECT_ROOT / "web" / "public" / "data" / "books"

client = AsyncOpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=os.environ["OPENROUTER_API_KEY"],
)
MAX_CONCURRENT = 10

ANNOTATION_PROMPT = (
    'You are a literary analyst helping annotate an English translation of '
    '"The Complete Adventures of Feluda", '
    "a Bengali detective fiction anthology by Satyajit Ray featuring private investigator "
    "Prodosh C. Mitter (Feluda), his cousin Tapesh (Topshe), and thriller writer "
    "Lalmohan Ganguly (Jatayu).\n\n"
    "For the given chapter text, extract three categories of terms:\n\n"
    '1. **Characters** — Recurring named people. 1-2 sentence description.\n'
    '2. **Proper nouns** — Place names, cultural terms, historical references. Brief explanation.\n'
    '3. **Vocabulary** — Culturally-specific words/phrases. Brief definition.\n\n'
    "Rules:\n"
    "- Only extract terms that actually appear in the chapter text (exact spelling match).\n"
    "- Keep descriptions concise: 1-2 sentences max.\n"
    "- Do NOT extract common English words.\n"
    "- Focus on Bengali, Hindi, or Indian-origin terms.\n"
    "- Return valid JSON only, no markdown fences."
)

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


async def extract_chapter_terms(sem, chapter, story_id):
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
                    model="openai/gpt-4.1",
                    messages=[
                        {"role": "system", "content": ANNOTATION_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"},
                )

                raw = response.choices[0].message.content
                result = json.loads(raw)
                print(f"  [{story_id}] ch-{chapter['number']}: {chapter['title']}", flush=True)
                return chapter["id"], result, chapter
            except Exception as e:
                if attempt < 2:
                    print(f"  [{story_id}] ch-{chapter['number']}: retry {attempt+1} ({e})")
                    await asyncio.sleep(5 * (attempt + 1))
                else:
                    print(f"  [{story_id}] ch-{chapter['number']}: FAILED ({e})")
                    return chapter["id"], {"characters": {}, "proper_nouns": {}, "vocabulary": {}}, chapter


def reduce_results(results, story_id):
    glossary = {}
    chapter_terms = {}

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
            print(f"  [{story_id}] {ch_id}: filtered {filtered} hallucinated terms")

    used = set()
    for terms in chapter_terms.values():
        used.update(terms)
    glossary = {k: v for k, v in glossary.items() if k in used}

    return {"glossary": glossary, "chapters": chapter_terms}


async def deduplicate_glossary(data, story_id):
    glossary = data["glossary"]
    chapter_terms = data["chapters"]

    if len(glossary) < 3:
        print(f"  [{story_id}] Only {len(glossary)} entries, skipping dedup")
        return data

    entries = []
    for name, info in sorted(glossary.items()):
        entries.append(f"  {name} ({info['type']}): {info['description'][:120]}")

    prompt = (
        "Below is a glossary of terms from a novel. Many entries refer to the same entity "
        "under different spellings, nicknames, or honorifics.\n\n"
        "Identify ALL groups of duplicate entries that refer to the same person/thing. "
        "For each group, pick the best canonical name (the most common or full form).\n\n"
        "Glossary:\n" + "\n".join(entries) + "\n\n"
        'Return JSON: {"duplicates": [{"canonical": "BestName", "aliases": ["Alias1", "Alias2"], '
        '"merged_description": "Best 1-2 sentence description"}]}\n'
        "Only include groups with 2+ entries. Do NOT include singletons."
    )

    response = await client.chat.completions.create(
        model="openai/gpt-4.1",
        messages=[
            {"role": "system", "content": "You are a literary analyst deduplicating a glossary. Be thorough — catch all variant spellings, nicknames, titles, and honorifics that refer to the same entity."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)
    groups = result.get("duplicates", [])

    merged_count = 0
    for group in groups:
        canonical = group["canonical"]
        aliases = group["aliases"]
        merged_desc = group.get("merged_description", "")

        if canonical not in glossary:
            for alias in [canonical] + aliases:
                if alias in glossary:
                    canonical = alias
                    break
            else:
                continue

        if merged_desc:
            glossary[canonical]["description"] = merged_desc

        for alias in aliases:
            if alias == canonical or alias not in glossary:
                continue

            for ch_id, terms in chapter_terms.items():
                if alias in terms:
                    terms.remove(alias)
                    if canonical not in terms:
                        terms.append(canonical)

            del glossary[alias]
            merged_count += 1

    print(f"  [{story_id}] Merged {merged_count} duplicate entries across {len(groups)} groups")
    return {"glossary": glossary, "chapters": chapter_terms}


async def reconcile_characters(data, story_id):
    glossary = data["glossary"]
    chapter_terms = data["chapters"]

    characters = {k: v for k, v in glossary.items() if v["type"] == "character"}
    if len(characters) < 2:
        print(f"  [{story_id}] Only {len(characters)} characters, nothing to reconcile")
        return data

    entries = []
    for name, info in sorted(characters.items()):
        count = sum(1 for ch_terms in chapter_terms.values() if name in ch_terms)
        entries.append(f"  {name} ({count} chapters): {info['description'][:150]}")

    prompt = (
        "Below is a list of character entries extracted from a novel. Many entries refer to the "
        "SAME person under different names, spellings, honorifics, kinship terms, or references.\n\n"
        "For example:\n"
        "- 'Feluda', 'Felu', 'Prodosh Mitter', 'Prodosh C. Mitter' are the same person\n"
        "- 'Topshe', 'Tapesh', 'Tapesh Ranjan Mitter' are the same person\n"
        "- 'Jatayu', 'Lalmohan Babu', 'Lalmohan Ganguly' are the same person\n\n"
        "AGGRESSIVELY identify ALL groups of entries that refer to the same person. "
        "Consider: variant spellings, nicknames, honorifics, kinship terms, "
        "possessive forms, cultural equivalents, and hyphenation variants.\n\n"
        "For each group, pick the best canonical name — prefer the most recognized form.\n\n"
        "Characters:\n" + "\n".join(entries) + "\n\n"
        'Return JSON: {"groups": [{"canonical": "BestName", "aliases": ["Alias1", "Alias2"], '
        '"merged_description": "Best 1-2 sentence description combining all info"}]}\n'
        "Include ALL groups with 2+ entries. Be aggressive — err on the side of merging."
    )

    response = await client.chat.completions.create(
        model="google/gemini-3-flash-preview",
        messages=[
            {"role": "system", "content": (
                "You are a literary analyst specializing in Indian literature. "
                "You understand that Indian novels use many different names, honorifics, "
                "and kinship terms for the same character. Be thorough and aggressive "
                "in identifying duplicates."
            )},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)
    groups = result.get("groups", [])

    merged_count = 0
    for group in groups:
        canonical = group["canonical"]
        aliases = group.get("aliases", [])
        merged_desc = group.get("merged_description", "")

        if canonical not in glossary:
            for candidate in [canonical] + aliases:
                if candidate in glossary:
                    canonical = candidate
                    break
            else:
                continue

        if merged_desc:
            glossary[canonical]["description"] = merged_desc

        for alias in aliases:
            if alias == canonical:
                continue

            for ch_id, terms in chapter_terms.items():
                if alias in terms:
                    terms.remove(alias)
                    if canonical not in terms:
                        terms.append(canonical)

            if alias in glossary:
                del glossary[alias]
                merged_count += 1

    print(f"  [{story_id}] Reconciled {merged_count} character aliases across {len(groups)} groups")

    glossary_keys = set(glossary.keys())
    orphan_count = 0
    for ch_id, terms in chapter_terms.items():
        orphans = [t for t in terms if t not in glossary_keys]
        for o in orphans:
            terms.remove(o)
            orphan_count += 1
    if orphan_count:
        print(f"  [{story_id}] Removed {orphan_count} orphan chapter references")

    chars_after = sum(1 for v in glossary.values() if v["type"] == "character")
    print(f"  [{story_id}] Characters: {len(characters)} -> {chars_after}")
    return {"glossary": glossary, "chapters": chapter_terms}


async def process_story(story_id, force=False):
    chapters_path = WEB_BOOKS_DIR / story_id / "chapters.json"
    output_path = WEB_BOOKS_DIR / story_id / "annotations.json"

    if not chapters_path.exists():
        print(f"[{story_id}] chapters.json not found: {chapters_path}")
        return False

    if not force and output_path.exists():
        print(f"[{story_id}] annotations.json already exists, skipping")
        return True

    with open(chapters_path) as f:
        data = json.load(f)
    chapters = data["chapters"]

    print(f"[{story_id}] {len(chapters)} chapters, extracting terms...")
    sem = asyncio.Semaphore(MAX_CONCURRENT)

    tasks = [extract_chapter_terms(sem, ch, story_id) for ch in chapters]
    results = await asyncio.gather(*tasks)

    def sort_key(r):
        parts = r[0].replace("ch-", "").split("-")
        return tuple(int(p) for p in parts)
    results.sort(key=sort_key)

    print(f"[{story_id}] Reducing {len(results)} results...")
    output = reduce_results(results, story_id)

    print(f"[{story_id}] Deduplicating glossary...")
    output = await deduplicate_glossary(output, story_id)

    print(f"[{story_id}] Reconciling characters...")
    output = await reconcile_characters(output, story_id)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    g = output["glossary"]
    chars = sum(1 for v in g.values() if v["type"] == "character")
    nouns = sum(1 for v in g.values() if v["type"] == "proper_noun")
    vocab = sum(1 for v in g.values() if v["type"] == "vocabulary")
    print(f"[{story_id}] Done! {len(g)} entries ({chars} characters, {nouns} proper nouns, {vocab} vocabulary) -> {output_path}\n")
    return True


async def main_async(force=False, story_filter=None):
    anthology_path = WEB_BOOKS_DIR / "feluda" / "anthology.json"
    with open(anthology_path) as f:
        anthology = json.load(f)
    story_ids = anthology["storyBookIds"]

    if story_filter:
        story_ids = [s for s in story_ids if s == story_filter]
        if not story_ids:
            print(f"Story '{story_filter}' not found in anthology")
            return

    print(f"Processing {len(story_ids)} Feluda story-books...\n")

    # Process stories sequentially (each story uses parallel chapter extraction internally)
    success = 0
    for story_id in story_ids:
        try:
            ok = await process_story(story_id, force=force)
            if ok:
                success += 1
        except Exception as e:
            print(f"[{story_id}] ERROR: {e}\n")

    print(f"\nCompleted: {success}/{len(story_ids)} story-books")


def main():
    parser = argparse.ArgumentParser(description="Generate annotations for Feluda story-books")
    parser.add_argument("--force", action="store_true", help="Force re-run even if annotations exist")
    parser.add_argument("--story", type=str, help="Process a single story-book ID")
    args = parser.parse_args()

    asyncio.run(main_async(force=args.force, story_filter=args.story))


if __name__ == "__main__":
    main()
