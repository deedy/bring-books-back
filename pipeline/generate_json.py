"""Generate web JSON files (chapters.json, meta.json) for a book.

Usage (standalone):
    uv run python -m pipeline.generate_json --book chandrakanta
"""

import argparse
import json
import os
import re
import shutil
from openai import OpenAI
from dotenv import load_dotenv

from pipeline.config import get_book, WEB_DATA_DIR, OPENROUTER_BASE_URL

load_dotenv()

client = OpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=os.environ["OPENROUTER_API_KEY"],
)

SCANNING_ARTIFACTS = [
    r"Digitized by srujanika@gmail\.com",
    r"www\.MurchOna\.(?:com|org)",
    r"suman_a[lh]*m@yahoo\.com\s*WWW\.MURCHONA\.COM[^\n]*(?:\n[^\n]*\|+[^\n]*)*",
    r"-{10,}",
]


def split_into_pages(text):
    parts = re.split(r"--- Page (\d+) ---\n", text)
    pages = {}
    for i in range(1, len(parts), 2):
        page_num = int(parts[i])
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        pages[page_num] = body
    return pages


def text_to_paragraphs(body_text, running_headers=None):
    for pattern in SCANNING_ARTIFACTS:
        body_text = re.sub(pattern, "", body_text)
    blocks = re.split(r"\n\n+", body_text)
    paragraphs = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        merged = []
        current = []
        for line in lines:
            if re.match(r"^\d+\s*$", line):
                continue
            if running_headers and any(h.lower() in line.lower() for h in running_headers):
                continue
            if line.startswith('"') and current:
                merged.append(" ".join(current))
                current = [line]
            else:
                current.append(line)
        if current:
            merged.append(" ".join(current))
        paragraphs.extend(merged)
    return paragraphs


def _find_markers_by_regex(full_text, chapters, chapter_regex):
    """Find chapter boundaries using a regex pattern that matches chapter markers in the text.

    This handles mid-page chapter splits correctly by finding the exact text position
    of each marker rather than relying on page boundaries.

    Returns list of (content_start, title_start) tuples.
    """
    pattern = re.compile(chapter_regex, re.MULTILINE)
    matches = list(pattern.finditer(full_text))

    marker_positions = []
    for ch in chapters:
        ch_num = ch["chapter"]
        # Find the match for this chapter number
        found = False
        for m in matches:
            # The regex should have a capture group with the marker text
            marker_text = m.group(1) if m.lastindex else m.group(0)
            marker_text = marker_text.strip()
            # Match by chapter marker field, or fall back to title
            expected = ch.get("marker", ch["title"])
            if marker_text == expected:
                marker_positions.append((m.end(), m.start()))
                matches.remove(m)
                found = True
                break
        if not found:
            print(f"  WARNING: No regex match for chapter {ch_num} (marker: {ch.get('marker', ch['title'])})")
            marker_positions.append((0, 0))

    return marker_positions


def _find_markers_by_page(full_text, pages, page_nums, chapters, use_title_markers):
    """Find chapter boundaries using page-based positions (original method).

    Works best when chapters start at the beginning of a page.
    """
    marker_positions = []
    for ch in chapters:
        ch_num = ch["chapter"]
        start_page = ch["page"]

        prefix_len = 0
        for pn in page_nums:
            if pn >= start_page:
                break
            prefix_len += len(pages[pn]) + 2

        search_start = max(0, prefix_len - 200)
        search_region = full_text[search_start:]

        if use_title_markers:
            title = ch["title"]
            pattern = re.compile(
                re.escape(title) + r'\s*\n(?:\s*\n)*(?:\d+\s*\n(?:\s*\n)*)?',
                re.IGNORECASE
            )
            m = pattern.search(search_region)
            if m:
                content_start = search_start + m.end()
                title_start = search_start + m.start()
                marker_positions.append((content_start, title_start))
            else:
                marker_positions.append((prefix_len, prefix_len))
        else:
            num_str = str(ch_num)
            pattern = re.compile(
                r'(?:\n\s*\n|\n[^\n]*(?:Part|भाग|Second|Third|Fourth)[^\n]*\n)'
                + re.escape(num_str) + r'\s*\n\s*\n'
            )
            m = pattern.search(search_region)
            if m:
                abs_pos = search_start + m.end()
                marker_positions.append((abs_pos, abs_pos))
            else:
                marker_positions.append((prefix_len, prefix_len))

    return marker_positions


def extract_chapters(pages, chapters_def, running_headers=None):
    chapters = chapters_def.get("chapters", [])
    use_title_markers = chapters_def.get("use_title_markers", False)
    chapter_regex = chapters_def.get("chapter_regex", None)
    page_nums = sorted(pages.keys())

    full_text = "\n\n".join(pages[pn] for pn in page_nums)

    if chapter_regex:
        marker_positions = _find_markers_by_regex(full_text, chapters, chapter_regex)
    else:
        marker_positions = _find_markers_by_page(full_text, pages, page_nums, chapters, use_title_markers)

    result = []
    for i, ch in enumerate(chapters):
        start_pos = marker_positions[i][0]
        end_pos = marker_positions[i + 1][1] if i + 1 < len(chapters) else len(full_text)
        body = full_text[start_pos:end_pos]

        paras = text_to_paragraphs(body, running_headers)

        ch_num = ch["chapter"]
        ch_title = ch["title"]
        if paras:
            first = paras[0].strip().replace("\u2019", "'")
            norm_title = ch_title.replace("\u2019", "'")
            if re.match(rf"^{ch_num}\.\s*{re.escape(norm_title)}\s*$", first):
                paras.pop(0)
            elif first.lower() == norm_title.lower():
                paras.pop(0)

        wc = sum(len(p.split()) for p in paras)

        part = ch.get("part") or 1
        part_name = ch.get("part_name") or ""

        result.append({
            "id": f"ch-{part}-{ch_num}" if part else f"ch-{ch_num}",
            "number": ch_num,
            "title": ch["title"],
            "part": part,
            "partName": part_name,
            "image": "",
            "wordCount": wc,
            "paragraphs": paras,
        })

    return result


def generate_summary(book_id, chapters_data, cfg):
    sample = ""
    for ch in chapters_data[:3]:
        sample += f"\n\nChapter {ch['number']}: {ch['title']}\n"
        sample += "\n".join(ch["paragraphs"][:5])

    response = client.chat.completions.create(
        model="openai/gpt-4.1",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are writing marketing copy for a classic literature website. "
                    "Given sample chapters from a book, write:\n"
                    "1. A compelling subtitle (5-10 words, no quotes)\n"
                    "2. A book summary (3-5 sentences, ~100-150 words) that would make a reader want to read it. "
                    "Make it vivid and engaging without spoilers.\n\n"
                    'Return JSON: {"subtitle": "...", "summary": "..."}'
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Book: {cfg.title} ({cfg.original_year}) by {cfg.author_name}\n"
                    f"Language: {cfg.original_language}\n"
                    f"Genre: {', '.join(cfg.genre)}\n"
                    f"Context: {cfg.style_context}\n"
                    f"Total chapters: {len(chapters_data)}, Total words: {sum(ch['wordCount'] for ch in chapters_data):,}\n"
                    f"\nSample text:{sample[:3000]}"
                ),
            },
        ],
        temperature=0.7,
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)


def generate_author_bio(cfg):
    """Generate a 2-paragraph author biography using GPT."""
    response = client.chat.completions.create(
        model="openai/gpt-4.1",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are writing an author biography for a classic literature website. "
                    "Write exactly 2 paragraphs (~150-200 words total) about the author. "
                    "Paragraph 1: biographical facts (birth, education, career, key life events). "
                    "Paragraph 2: literary significance, major works, legacy. "
                    "Mention the specific book being featured on the site. "
                    "Be factual, engaging, and encyclopedic in tone. "
                    "Do NOT invent facts — if unsure, keep it general. "
                    'Return JSON: {"bio": "paragraph1\\n\\nparagraph2"}'
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Author: {cfg.author_name} ({cfg.author_years})\n"
                    f"Book on our site: {cfg.title} ({cfg.original_title}, {cfg.original_year})\n"
                    f"Original language: {cfg.original_language}\n"
                    f"Genre: {', '.join(cfg.genre)}\n"
                    f"Context: {cfg.style_context}"
                ),
            },
        ],
        temperature=0.7,
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)
    return result["bio"]


def update_images(book_id, chapters_data, images_dir):
    web_img_dir = str(WEB_DATA_DIR / "images" / "chapters" / book_id)
    os.makedirs(web_img_dir, exist_ok=True)

    if not os.path.exists(images_dir):
        print(f"  No image directory {images_dir}, skipping images")
        return

    count = 0
    for ch in chapters_data:
        part = ch["part"]
        num = ch["number"]
        key = f"p{part}_chapter_{num}" if part else f"chapter_{num}"

        web_src = os.path.join(images_dir, f"{key}_web.png")
        if os.path.exists(web_src):
            dst = os.path.join(web_img_dir, f"{key}.png")
            shutil.copy2(web_src, dst)
            ch["image"] = f"/data/images/chapters/{book_id}/{key}.webp"
            count += 1

    print(f"  Copied {count} chapter images -> {web_img_dir}")


def copy_cover(book_id, images_dir):
    cover_src = os.path.join(images_dir, "cover.png")
    if os.path.exists(cover_src):
        cover_dst = str(WEB_DATA_DIR / "images" / "covers" / f"{book_id}.png")
        os.makedirs(os.path.dirname(cover_dst), exist_ok=True)
        shutil.copy2(cover_src, cover_dst)
        print(f"  Copied cover -> {cover_dst}")


def generate_story_summary(story_name, story_chapters, cfg):
    """Generate a subtitle + summary for a single anthology story."""
    sample = ""
    for ch in story_chapters[:3]:
        sample += f"\nChapter {ch['number']}: {ch['title']}\n"
        sample += "\n".join(ch["paragraphs"][:5])

    response = client.chat.completions.create(
        model="openai/gpt-4.1",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are writing marketing copy for a detective story on a literature website. "
                    "Given sample text from a story, write:\n"
                    "1. A compelling subtitle (5-10 words, no quotes)\n"
                    "2. A 2-3 sentence summary that would make a reader want to read it. "
                    "Be intriguing without spoilers.\n\n"
                    'Return JSON: {"subtitle": "...", "summary": "..."}'
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Story: {story_name}\n"
                    f"From: {cfg.title} by {cfg.author_name}\n"
                    f"Genre: {', '.join(cfg.genre)}\n"
                    f"Chapters: {len(story_chapters)}\n"
                    f"\nSample text:{sample[:2000]}"
                ),
            },
        ],
        temperature=0.7,
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)


def run_anthology(book_id, chapters_data, cfg, force=False):
    """Split an anthology into individual story-books, each with its own chapters.json + meta.json.

    Also writes an anthology.json listing all story-book IDs for the parent landing page.
    """
    # Group chapters by part
    stories = {}
    for ch in chapters_data:
        part = ch["part"]
        if part not in stories:
            stories[part] = {"partName": ch["partName"], "chapters": []}
        stories[part]["chapters"].append(ch)

    catalog_path = str(WEB_DATA_DIR / "catalog.json")
    with open(catalog_path) as f:
        catalog = json.load(f)

    # Remove old story-book entries for this anthology
    catalog["books"] = [
        b for b in catalog["books"]
        if b.get("anthologyId") != book_id and b["id"] != book_id
    ]

    story_book_ids = []

    for part_num in sorted(stories.keys()):
        story = stories[part_num]
        story_chapters = story["chapters"]
        story_name = story["partName"]
        story_slug = re.sub(r"[^a-z0-9]+", "-", story_name.lower()).strip("-")
        story_book_id = f"{book_id}-{story_slug}"
        story_book_ids.append(story_book_id)

        story_book_dir = str(WEB_DATA_DIR / "books" / story_book_id)
        story_chapters_json = os.path.join(story_book_dir, "chapters.json")

        if not force and os.path.exists(story_chapters_json):
            print(f"  [{story_book_id}] already exists, skipping")
            # Still add to catalog from existing meta
            meta_path = os.path.join(story_book_dir, "meta.json")
            if os.path.exists(meta_path):
                with open(meta_path) as f:
                    existing_meta = json.load(f)
                # Reconstruct preview
                with open(story_chapters_json) as f:
                    existing_ch = json.load(f)
                preview = ""
                if existing_ch["chapters"] and existing_ch["chapters"][0]["paragraphs"]:
                    preview = " ".join(existing_ch["chapters"][0]["paragraphs"][:3])[:1200]
                catalog["books"].append({**existing_meta, "previewText": preview})
            continue

        # Flatten chapters: remove part, renumber from 1
        flat_chapters = []
        for i, ch in enumerate(story_chapters):
            flat_chapters.append({
                "id": f"ch-{i+1}",
                "number": i + 1,
                "title": ch["title"],
                "part": None,
                "partName": None,
                "image": ch.get("image", ""),
                "wordCount": ch["wordCount"],
                "paragraphs": ch["paragraphs"],
            })

        word_count = sum(ch["wordCount"] for ch in flat_chapters)

        # Write chapters.json
        os.makedirs(story_book_dir, exist_ok=True)
        with open(story_chapters_json, "w") as f:
            json.dump({"chapters": flat_chapters}, f, ensure_ascii=False, indent=2)

        # Generate summary
        print(f"  [{story_book_id}] Generating summary ({len(flat_chapters)} ch, {word_count:,} words)...")
        summary_data = generate_story_summary(story_name, flat_chapters, cfg)

        # Build meta.json
        story_meta = {
            "id": story_book_id,
            "title": story_name,
            "transliteratedTitle": story_name,
            "subtitle": summary_data["subtitle"],
            "authorId": cfg.author_id,
            "coverImage": f"/data/images/covers/{book_id}.webp",
            "accentColor": cfg.accent_color,
            "genre": cfg.genre,
            "originalLanguage": cfg.original_language,
            "originalTitle": cfg.original_title,
            "originalYear": cfg.original_year,
            "totalChapters": len(flat_chapters),
            "wordCount": word_count,
            "summary": summary_data["summary"],
            "anthologyId": book_id,
        }

        meta_path = os.path.join(story_book_dir, "meta.json")
        with open(meta_path, "w") as f:
            json.dump(story_meta, f, ensure_ascii=False, indent=2)

        # Add to catalog
        preview = ""
        if flat_chapters and flat_chapters[0]["paragraphs"]:
            preview = " ".join(flat_chapters[0]["paragraphs"][:3])[:1200]
        catalog["books"].append({**story_meta, "previewText": preview})

        print(f"  [{story_book_id}] Done")

    # Write the parent anthology entry to catalog (no chapters.json needed)
    total_words = sum(ch["wordCount"] for ch in chapters_data)
    print("Generating anthology-level summary...")
    anthology_summary = generate_summary(book_id, chapters_data, cfg)
    anthology_meta = {
        "id": book_id,
        "title": cfg.title,
        "transliteratedTitle": cfg.transliterated_title,
        "subtitle": anthology_summary["subtitle"],
        "authorId": cfg.author_id,
        "coverImage": f"/data/images/covers/{book_id}.webp",
        "accentColor": cfg.accent_color,
        "genre": cfg.genre,
        "originalLanguage": cfg.original_language,
        "originalTitle": cfg.original_title,
        "originalYear": cfg.original_year,
        "totalChapters": len(chapters_data),
        "wordCount": total_words,
        "summary": anthology_summary["summary"],
        "type": "anthology",
        "totalStories": len(story_book_ids),
    }
    catalog["books"].append({**anthology_meta, "previewText": ""})

    # Write anthology meta.json (parent)
    parent_book_dir = str(cfg.web_book_dir)
    os.makedirs(parent_book_dir, exist_ok=True)
    with open(os.path.join(parent_book_dir, "meta.json"), "w") as f:
        json.dump(anthology_meta, f, ensure_ascii=False, indent=2)

    # Write anthology.json (list of story-book IDs for the landing page)
    anthology_listing = {
        "storyBookIds": story_book_ids,
    }
    with open(os.path.join(parent_book_dir, "anthology.json"), "w") as f:
        json.dump(anthology_listing, f, ensure_ascii=False, indent=2)

    # Ensure author
    author_id = cfg.author_id
    author_entry = next((a for a in catalog["authors"] if a["id"] == author_id), None)
    if not author_entry:
        print("Generating author bio...")
        bio = generate_author_bio(cfg)
        catalog["authors"].append({
            "id": author_id,
            "name": cfg.author_name,
            "image": f"/data/images/authors/{author_id}.webp",
            "years": cfg.author_years,
            "bio": bio,
            "bookIds": [book_id],
        })
    else:
        if not author_entry.get("bio"):
            author_entry["bio"] = generate_author_bio(cfg)
        if book_id not in author_entry["bookIds"]:
            author_entry["bookIds"].append(book_id)

    with open(catalog_path, "w") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print(f"Updated {catalog_path}")
    print(f"\nDone! {len(story_book_ids)} story-books, {total_words:,} total words")
    return True


def run(book_id, force=False):
    """Run JSON generation for a book. Returns True if output exists after run."""
    cfg = get_book(book_id)
    book_dir = str(cfg.web_book_dir)
    chapters_json_path = str(cfg.web_chapters_json)

    if not force and os.path.exists(chapters_json_path):
        print(f"[{book_id}] chapters.json exists: {chapters_json_path}")
        return True

    if not os.path.exists(str(cfg.english_txt)):
        print(f"[{book_id}] English text not found: {cfg.english_txt}")
        return False

    if not os.path.exists(str(cfg.chapters_def_json)):
        print(f"[{book_id}] Chapters def not found: {cfg.chapters_def_json}")
        return False

    # Load translation
    with open(str(cfg.english_txt)) as f:
        text = f.read()
    pages = split_into_pages(text)
    print(f"[{book_id}] Loaded {len(pages)} translated pages")

    # Load chapter definitions
    with open(str(cfg.chapters_def_json)) as f:
        chapters_def = json.load(f)

    running_headers = chapters_def.get("running_headers", [])

    # Extract chapters
    chapters_data = extract_chapters(pages, chapters_def, running_headers)
    total_words = sum(ch["wordCount"] for ch in chapters_data)
    print(f"Extracted {len(chapters_data)} chapters, {total_words:,} words")

    # Anthology: split into individual story-books
    is_anthology = getattr(cfg, "type", "book") == "anthology"
    if is_anthology:
        return run_anthology(book_id, chapters_data, cfg, force=force)

    # Update images
    images_dir = str(cfg.images_dir)
    update_images(book_id, chapters_data, images_dir)
    copy_cover(book_id, images_dir)

    # Write chapters.json
    os.makedirs(book_dir, exist_ok=True)
    with open(chapters_json_path, "w") as f:
        json.dump({"chapters": chapters_data}, f, ensure_ascii=False, indent=2)
    print(f"Wrote {chapters_json_path}")

    # Generate summary
    print("Generating summary...")
    summary_data = generate_summary(book_id, chapters_data, cfg)

    # Build meta.json
    book_meta = {
        "id": book_id,
        "title": cfg.title,
        "transliteratedTitle": cfg.transliterated_title,
        "subtitle": summary_data["subtitle"],
        "authorId": cfg.author_id,
        "coverImage": f"/data/images/covers/{book_id}.webp",
        "accentColor": cfg.accent_color,
        "genre": cfg.genre,
        "originalLanguage": cfg.original_language,
        "originalTitle": cfg.original_title,
        "originalYear": cfg.original_year,
        "totalChapters": len(chapters_data),
        "wordCount": total_words,
        "summary": summary_data["summary"],
    }

    meta_path = os.path.join(book_dir, "meta.json")
    with open(meta_path, "w") as f:
        json.dump(book_meta, f, ensure_ascii=False, indent=2)
    print(f"Wrote {meta_path}")

    # Update catalog.json
    catalog_path = str(WEB_DATA_DIR / "catalog.json")
    with open(catalog_path) as f:
        catalog = json.load(f)

    catalog["books"] = [b for b in catalog["books"] if b["id"] != book_id]

    preview = ""
    if chapters_data and chapters_data[0]["paragraphs"]:
        preview = " ".join(chapters_data[0]["paragraphs"][:3])[:1200]

    catalog["books"].append({
        **book_meta,
        "previewText": preview,
    })

    author_id = cfg.author_id
    author_entry = next((a for a in catalog["authors"] if a["id"] == author_id), None)
    if not author_entry:
        print("Generating author bio...")
        bio = generate_author_bio(cfg)
        catalog["authors"].append({
            "id": author_id,
            "name": cfg.author_name,
            "image": f"/data/images/authors/{author_id}.webp",
            "years": cfg.author_years,
            "bio": bio,
            "bookIds": [book_id],
        })
    else:
        if not author_entry.get("bio"):
            print("Generating missing author bio...")
            author_entry["bio"] = generate_author_bio(cfg)
        if book_id not in author_entry["bookIds"]:
            author_entry["bookIds"].append(book_id)

    with open(catalog_path, "w") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print(f"Updated {catalog_path}")

    print(f"\nDone! {len(chapters_data)} chapters, {total_words:,} words")
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate web JSON for a book")
    parser.add_argument("--book", required=True, help="Book ID")
    parser.add_argument("--force", action="store_true", help="Force re-run")
    args = parser.parse_args()

    run(args.book, force=args.force)


if __name__ == "__main__":
    main()
