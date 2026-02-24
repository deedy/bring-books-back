"""Shared chapter parsing logic for Ponniyin Selvan.
Used by both generate_ponniyin_pdf.py and generate_ponniyin_json.py.
"""

import re

# Part boundaries (page numbers from the decoded Tamil text)
PARTS = [
    (1, "புது வெள்ளி", "New Flood", 15),
    (2, "சுழற்காற்று", "Whirlwind", 363),
    (3, "கொலை வாள்", "The Sword of Death", 714),
    (4, "மணிமகுடம்", "The Crown of Gems", 1035),
    (5, "தியாக சிகரம்", "The Pinnacle of Sacrifice", 1325),
]


def get_part_for_page(page_num):
    """Return (part_num, part_name_en) for a given source page number."""
    part = (1, "New Flood")
    for p_num, _, p_name_en, p_start in PARTS:
        if page_num >= p_start:
            part = (p_num, p_name_en)
    return part


def parse_translated_pages(text):
    """Split translated text into {page_num: content} dict."""
    parts = re.split(r"--- Page (\d+) ---\n", text)
    pages = {}
    for i in range(1, len(parts), 2):
        page_num = int(parts[i])
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        pages[page_num] = body
    return pages


def extract_chapters(text):
    """Extract chapters from translated English text.
    Returns list of dicts: {number, title, part, partName, body, source_page}
    """
    pages = parse_translated_pages(text)
    page_nums = sorted(pages.keys())

    # Build a single text stream with page markers
    chapters = []
    current_ch = None

    for page_num in page_nums:
        content = pages[page_num]
        part_num, part_name = get_part_for_page(page_num)

        # Check for chapter headers in this page
        lines = content.split("\n")
        for line_idx, line in enumerate(lines):
            # Match patterns like "Chapter 1 - Title" or "Chapter 1: Title" etc.
            m = re.match(
                r"^Chapter\s+(\d+)\s*[-–—:]+\s*(.+?)$",
                line.strip(),
                re.IGNORECASE,
            )
            if m:
                ch_num = int(m.group(1))
                ch_title = m.group(2).strip().rstrip(".")

                # Save previous chapter
                if current_ch and current_ch["lines"]:
                    current_ch["body"] = "\n".join(current_ch["lines"]).strip()
                    del current_ch["lines"]
                    chapters.append(current_ch)

                current_ch = {
                    "number": ch_num,
                    "title": ch_title,
                    "part": part_num,
                    "partName": part_name,
                    "source_page": page_num,
                    "lines": [],
                }
                continue

            # Add line to current chapter
            if current_ch is not None:
                # Skip running headers (standalone numbers, book title repeats)
                s = line.strip()
                if not s:
                    current_ch["lines"].append("")
                elif re.match(r"^\d+$", s):
                    continue  # page number
                else:
                    current_ch["lines"].append(line)

    # Save last chapter
    if current_ch and current_ch["lines"]:
        current_ch["body"] = "\n".join(current_ch["lines"]).strip()
        del current_ch["lines"]
        chapters.append(current_ch)

    # Deduplicate: if same part+number appears twice, merge bodies
    merged = {}
    for ch in chapters:
        key = (ch["part"], ch["number"])
        if key in merged:
            merged[key]["body"] += "\n\n" + ch["body"]
        else:
            merged[key] = ch
    chapters = list(merged.values())

    return chapters


def chapters_to_paragraphs(body_text):
    """Split chapter body into clean paragraphs for display."""
    blocks = re.split(r"\n\n+", body_text)
    paragraphs = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # Merge lines within a block (but keep dialogue starts)
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        merged = []
        current = []
        for line in lines:
            if line.startswith('"') and current:
                merged.append(" ".join(current))
                current = [line]
            else:
                current.append(line)
        if current:
            merged.append(" ".join(current))
        paragraphs.extend(merged)
    return paragraphs
