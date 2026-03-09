"""Re-map Byomkesh annotations to match new chapter splits.

The glossary already exists. This script just scans each chapter's text
to determine which glossary terms appear in which chapter.

Usage:
    uv run python scripts/byomkesh_remap_annotations.py
"""

import json
import os
import glob

WEB_DATA = "web/public/data/books"


def remap_story(story_id: str):
    ann_path = f"{WEB_DATA}/{story_id}/annotations.json"
    chapters_path = f"{WEB_DATA}/{story_id}/chapters.json"

    if not os.path.exists(ann_path):
        return

    with open(ann_path) as f:
        annotations = json.load(f)

    with open(chapters_path) as f:
        chapters_data = json.load(f)

    glossary = annotations.get("glossary", {})
    if not glossary:
        return

    # Build new chapter_terms mapping
    chapter_terms = {}
    for chapter in chapters_data["chapters"]:
        ch_id = chapter["id"]
        text = "\n".join(chapter["paragraphs"])
        terms_in_chapter = [term for term in glossary if term in text]
        chapter_terms[ch_id] = terms_in_chapter

    annotations["chapters"] = chapter_terms

    with open(ann_path, "w") as f:
        json.dump(annotations, f, ensure_ascii=False, indent=2)

    total_terms = len(glossary)
    mapped = sum(len(v) for v in chapter_terms.values())
    print(f"  {story_id}: {len(chapter_terms)} chapters, {total_terms} glossary terms, {mapped} mappings")


def main():
    stories = sorted(glob.glob(f"{WEB_DATA}/byomkesh-*/annotations.json"))
    print(f"Re-mapping annotations for {len(stories)} stories...\n")

    for ann_path in stories:
        story_id = os.path.basename(os.path.dirname(ann_path))
        remap_story(story_id)

    print("\nDone!")


if __name__ == "__main__":
    main()
