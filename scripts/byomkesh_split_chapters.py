"""Step 2: Split Byomkesh stories into multiple chapters based on detected boundaries.

Usage:
    uv run python scripts/byomkesh_split_chapters.py

Reads data/byomkesh/sub_chapters.json and splits each story's chapters.json
into multiple chapters. Also updates meta.json and catalog.json.
"""

import json
import os

WEB_DATA = "web/public/data/books"
CATALOG_PATH = "web/public/data/catalog.json"
SUB_CHAPTERS_PATH = "data/byomkesh/sub_chapters.json"


def count_words(paragraphs: list[str]) -> int:
    return sum(len(p.split()) for p in paragraphs)


def split_story(story_id: str, boundaries: list[dict]):
    chapters_path = f"{WEB_DATA}/{story_id}/chapters.json"
    meta_path = f"{WEB_DATA}/{story_id}/meta.json"

    with open(chapters_path) as f:
        data = json.load(f)

    original_chapter = data["chapters"][0]
    paragraphs = original_chapter["paragraphs"]
    part = original_chapter.get("part")
    part_name = original_chapter.get("partName")

    # Sort boundaries by para_index
    boundaries = sorted(boundaries, key=lambda x: x["para_index"])

    new_chapters = []
    for i, boundary in enumerate(boundaries):
        start = boundary["para_index"]
        end = boundaries[i + 1]["para_index"] if i + 1 < len(boundaries) else len(paragraphs)

        chapter_paras = paragraphs[start:end]
        wc = count_words(chapter_paras)

        new_chapters.append({
            "id": f"ch-{i + 1}",
            "number": i + 1,
            "title": boundary["title"],
            "part": part,
            "partName": part_name,
            "image": "",  # Will be filled in Step 3
            "wordCount": wc,
            "paragraphs": chapter_paras,
        })

    # Validate total paragraphs preserved
    total_paras = sum(len(ch["paragraphs"]) for ch in new_chapters)
    assert total_paras == len(paragraphs), (
        f"{story_id}: paragraph count mismatch {total_paras} vs {len(paragraphs)}"
    )

    # Write updated chapters.json
    data["chapters"] = new_chapters
    with open(chapters_path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Update meta.json
    with open(meta_path) as f:
        meta = json.load(f)
    meta["totalChapters"] = len(new_chapters)
    with open(meta_path, "w") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"  {story_id}: split into {len(new_chapters)} chapters "
          f"({', '.join(str(ch['wordCount']) + 'w' for ch in new_chapters)})")

    return len(new_chapters)


def update_catalog(story_chapter_counts: dict):
    with open(CATALOG_PATH) as f:
        catalog = json.load(f)

    for book in catalog["books"]:
        if book["id"] in story_chapter_counts:
            book["totalChapters"] = story_chapter_counts[book["id"]]

    with open(CATALOG_PATH, "w") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    print(f"\nUpdated catalog.json for {len(story_chapter_counts)} stories")


def main():
    with open(SUB_CHAPTERS_PATH) as f:
        sub_chapters = json.load(f)

    print(f"Splitting {len(sub_chapters)} stories...\n")

    story_chapter_counts = {}
    for story_id, boundaries in sorted(sub_chapters.items()):
        n = split_story(story_id, boundaries)
        story_chapter_counts[story_id] = n

    update_catalog(story_chapter_counts)
    print("\nDone! Run Step 3 to generate chapter images.")


if __name__ == "__main__":
    main()
