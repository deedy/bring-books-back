"""Generate annotations.json for any book using GPT-4.1.

Usage (standalone):
    uv run python -m pipeline.generate_annotations --book chandrakanta

Map phase: fire all chapters in parallel via asyncio.
Reduce phase: merge glossaries, dedupe, verify terms against text.
"""

import argparse
import asyncio
import json
import os
from pathlib import Path
from openai import AsyncOpenAI, OpenAI
from dotenv import load_dotenv

from pipeline.config import get_book, OPENROUTER_BASE_URL

load_dotenv()

client = AsyncOpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=os.environ["OPENROUTER_API_KEY"],
)
sync_client = OpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=os.environ["OPENROUTER_API_KEY"],
)
MAX_CONCURRENT = 10

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


async def extract_chapter_terms(sem, chapter, system_prompt, book_id):
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


def reduce_results(results, book_id):
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
            print(f"  [{book_id}] {ch_id}: filtered {filtered} hallucinated terms")

    used = set()
    for terms in chapter_terms.values():
        used.update(terms)
    glossary = {k: v for k, v in glossary.items() if k in used}

    return {"glossary": glossary, "chapters": chapter_terms}


async def deduplicate_glossary(data, book_id):
    glossary = data["glossary"]
    chapter_terms = data["chapters"]

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

    print(f"  [{book_id}] Merged {merged_count} duplicate entries across {len(groups)} groups")
    return {"glossary": glossary, "chapters": chapter_terms}


async def reconcile_characters(data, book_id):
    """Aggressively merge character duplicates using Gemini Flash.

    The standard dedup step catches some aliases, but character-specific
    reconciliation is needed for names vs. honorifics vs. kinship terms
    (e.g., "Aai" = "Mother" = "Shyam's mother" = "Yashoda").
    """
    glossary = data["glossary"]
    chapter_terms = data["chapters"]

    characters = {k: v for k, v in glossary.items() if v["type"] == "character"}
    if len(characters) < 2:
        print(f"  [{book_id}] Only {len(characters)} characters, nothing to reconcile")
        return data

    entries = []
    for name, info in sorted(characters.items()):
        count = sum(1 for ch_terms in chapter_terms.values() if name in ch_terms)
        entries.append(f"  {name} ({count} chapters): {info['description'][:150]}")

    prompt = (
        "Below is a list of character entries extracted from a novel. Many entries refer to the "
        "SAME person under different names, spellings, honorifics, kinship terms, or references.\n\n"
        "For example:\n"
        "- 'Aai', 'Mother', 'Shyam\\'s mother', 'Yashoda' might all be the same person\n"
        "- 'Shyam' and 'Shyama' are likely the same person\n"
        "- 'Bhau', 'Father', 'Bapa', 'Bapu' might all refer to the same father figure\n"
        "- 'Dwarakakaku' and 'Dwaraka-kaku' are spelling variants\n"
        "- 'Mathura' and 'Mathure' are the same person\n\n"
        "AGGRESSIVELY identify ALL groups of entries that refer to the same person. "
        "Consider: variant spellings, nicknames, honorifics, kinship terms (mother, father, uncle, etc.), "
        "possessive forms ('Shyam's mother' vs 'Aai'), cultural equivalents, and hyphenation variants.\n\n"
        "For each group, pick the best canonical name — prefer the character's actual given name "
        "(e.g., 'Yashoda' over 'Mother'). If no proper name exists, use the most common reference "
        "(highest chapter count).\n\n"
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

        # Find canonical in glossary (or first alias that exists)
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

            # Always clean up chapter references, even if alias was already
            # removed from glossary by a previous group in this pass
            for ch_id, terms in chapter_terms.items():
                if alias in terms:
                    terms.remove(alias)
                    if canonical not in terms:
                        terms.append(canonical)

            # Only delete from glossary if still present
            if alias in glossary:
                if glossary[alias].get("image") and not glossary[canonical].get("image"):
                    glossary[canonical]["image"] = glossary[alias]["image"]
                del glossary[alias]
                merged_count += 1

    print(f"  [{book_id}] Reconciled {merged_count} character aliases across {len(groups)} groups")

    # Clean up orphan chapter references (terms in chapters but not in glossary)
    glossary_keys = set(glossary.keys())
    orphan_count = 0
    for ch_id, terms in chapter_terms.items():
        orphans = [t for t in terms if t not in glossary_keys]
        for o in orphans:
            terms.remove(o)
            orphan_count += 1
    if orphan_count:
        print(f"  [{book_id}] Removed {orphan_count} orphan chapter references")

    chars_after = sum(1 for v in glossary.values() if v["type"] == "character")
    print(f"  [{book_id}] Characters: {len(characters)} -> {chars_after}")
    return {"glossary": glossary, "chapters": chapter_terms}


SUMMARY_SYSTEM_PROMPT = (
    "You write concise chapter teasers for a book browsing page. "
    "Write exactly 1 sentence of 22-25 words. Count carefully before responding. "
    "Mention a character name and tease the scene. NEVER reveal outcomes, deaths, or twists. "
    'Return JSON: {"summary": "one sentence here"}'
)


def _trim_summary(text: str, max_words: int = 25) -> str:
    """Trim a summary to max_words, cutting at the last natural break (comma, em-dash, semicolon)."""
    words = text.split()
    if len(words) <= max_words:
        return text
    truncated = words[:max_words]
    fragment = " ".join(truncated)
    # Try to cut at last comma, semicolon, or em-dash for a clean ending
    for sep in [", ", "; ", " — ", "—"]:
        idx = fragment.rfind(sep)
        if idx > len(fragment) // 2:
            fragment = fragment[:idx] + "."
            return fragment
    # Otherwise just end with ellipsis-free period
    fragment = fragment.rstrip(".,;:—- ") + "."
    return fragment


def _generate_chapter_summary_sync(chapter, book_title, book_id):
    """Generate a 20-25 word summary for a single chapter using Gemini Flash via OpenRouter."""
    paras = chapter["paragraphs"]
    text = "\n\n".join(paras)
    if len(text) > 12000:
        text = text[:10000] + "\n\n[...]\n\n" + text[-2000:]

    user_prompt = (
        f'Book: "{book_title}"\n'
        f'Chapter {chapter["number"]}: "{chapter["title"]}"\n\n'
        f"Text:\n{text}\n\n"
        'Write a 22-25 word summary of this chapter. Return JSON: {"summary": "..."}'
    )

    for attempt in range(3):
        try:
            response = sync_client.chat.completions.create(
                model="google/gemini-3-flash-preview",
                messages=[
                    {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.5,
                response_format={"type": "json_object"},
            )
            result = json.loads(response.choices[0].message.content)
            summary = _trim_summary(result["summary"], max_words=25)
            wc = len(summary.split())
            print(f"  [{book_id}] summary ch-{chapter['number']}: {wc} words", flush=True)
            return chapter["id"], summary
        except Exception as e:
            if attempt < 2:
                print(f"  [{book_id}] summary ch-{chapter['number']}: retry {attempt+1} ({e})")
                import time; time.sleep(3 * (attempt + 1))
            else:
                print(f"  [{book_id}] summary ch-{chapter['number']}: FAILED ({e})")
                return chapter["id"], ""


async def generate_summaries(chapters, book_title, book_id):
    """Generate summaries for all chapters in parallel using Gemini Flash."""
    loop = asyncio.get_event_loop()
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as pool:
        futures = [
            loop.run_in_executor(pool, _generate_chapter_summary_sync, ch, book_title, book_id)
            for ch in chapters
        ]
        results = await asyncio.gather(*futures)

    summary_map = {ch_id: summary for ch_id, summary in results}
    count = sum(1 for s in summary_map.values() if s)
    print(f"  [{book_id}] Generated {count}/{len(chapters)} chapter summaries")
    return summary_map


async def _run_async(book_id, force=False):
    cfg = get_book(book_id)
    chapters_path = str(cfg.web_chapters_json)
    output_path = str(cfg.web_annotations_json)

    if not os.path.exists(chapters_path):
        print(f"[{book_id}] chapters.json not found: {chapters_path}")
        return False

    with open(chapters_path) as f:
        data = json.load(f)
    chapters = data["chapters"]

    # --- Glossary annotations ---
    if not force and os.path.exists(output_path):
        print(f"[{book_id}] Annotations exist: {output_path}")
    elif not cfg.annotation_prompt:
        print(f"[{book_id}] No annotation prompt configured")
        return False
    else:
        system_prompt = cfg.annotation_prompt

        print(f"[{book_id}] {len(chapters)} chapters, max {MAX_CONCURRENT} concurrent")
        sem = asyncio.Semaphore(MAX_CONCURRENT)

        tasks = [extract_chapter_terms(sem, ch, system_prompt, book_id) for ch in chapters]
        results = await asyncio.gather(*tasks)

        def sort_key(r):
            parts = r[0].replace("ch-", "").split("-")
            return tuple(int(p) for p in parts)
        results.sort(key=sort_key)

        print(f"\n[{book_id}] Reducing {len(results)} results...")
        output = reduce_results(results, book_id)

        print(f"\n[{book_id}] Deduplicating glossary...")
        output = await deduplicate_glossary(output, book_id)

        print(f"\n[{book_id}] Reconciling characters...")
        output = await reconcile_characters(output, book_id)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        g = output["glossary"]
        chars = sum(1 for v in g.values() if v["type"] == "character")
        nouns = sum(1 for v in g.values() if v["type"] == "proper_noun")
        vocab = sum(1 for v in g.values() if v["type"] == "vocabulary")
        print(f"\n[{book_id}] Done! {len(g)} entries ({chars} characters, {nouns} proper nouns, {vocab} vocabulary) -> {output_path}")

    # --- Chapter summaries ---
    has_summaries = all(ch.get("summary") for ch in chapters)
    if force or not has_summaries:
        print(f"\n[{book_id}] Generating chapter summaries...")
        summary_map = await generate_summaries(chapters, cfg.title, book_id)

        # Re-read chapters.json to avoid clobbering fields set by other stages
        with open(chapters_path) as f:
            fresh_data = json.load(f)
        for ch in fresh_data["chapters"]:
            if summary_map.get(ch["id"]):
                ch["summary"] = summary_map[ch["id"]]

        with open(chapters_path, "w") as f:
            json.dump(fresh_data, f, indent=2, ensure_ascii=False)
        print(f"[{book_id}] Updated {chapters_path} with summaries")
    else:
        print(f"[{book_id}] Chapter summaries already present, skipping (use --force to re-run)")

    return True


def run(book_id, force=False):
    """Run annotation generation for a book. Returns True if output exists after run."""
    return asyncio.run(_run_async(book_id, force=force))


async def _run_reconcile(book_id):
    """Run character reconciliation on existing annotations."""
    cfg = get_book(book_id)
    output_path = str(cfg.web_annotations_json)

    if not os.path.exists(output_path):
        print(f"[{book_id}] annotations.json not found: {output_path}")
        return False

    with open(output_path) as f:
        data = json.load(f)

    chars_before = sum(1 for v in data["glossary"].values() if v["type"] == "character")
    print(f"[{book_id}] Reconciling characters ({chars_before} characters)...")
    data = await reconcile_characters(data, book_id)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    chars_after = sum(1 for v in data["glossary"].values() if v["type"] == "character")
    print(f"[{book_id}] Saved {output_path} ({chars_after} characters)")
    return True


def run_reconcile(book_id):
    """Run character reconciliation on existing annotations."""
    return asyncio.run(_run_reconcile(book_id))


def main():
    parser = argparse.ArgumentParser(description="Generate annotations for a book")
    parser.add_argument("--book", required=True, help="Book ID")
    parser.add_argument("--force", action="store_true", help="Force re-run")
    parser.add_argument("--reconcile", action="store_true", help="Run character reconciliation only")
    args = parser.parse_args()

    if args.reconcile:
        run_reconcile(args.book)
    else:
        run(args.book, force=args.force)


if __name__ == "__main__":
    main()
