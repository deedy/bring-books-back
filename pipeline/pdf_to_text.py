"""Extract text from English PDFs and write page-marked text file.

For books that are already in English (e.g., Feluda translations),
skip OCR/translation and extract text directly.

Usage:
    uv run python -m pipeline.pdf_to_text --book feluda
"""

import argparse

import pymupdf

from pipeline.config import get_book


def extract_text(book_id: str, force: bool = False):
    cfg = get_book(book_id)
    output_path = cfg.english_txt

    if not force and output_path.exists():
        print(f"[{book_id}] english.txt already exists: {output_path}")
        return

    # Find all PDF files in the book directory (e.g., feluda1.pdf, feluda2.pdf)
    pdf_files = sorted(cfg.book_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"[{book_id}] No PDF files found in {cfg.book_dir}")
        return

    print(f"[{book_id}] Found {len(pdf_files)} PDF file(s): {[p.name for p in pdf_files]}")

    page_num = 1
    lines = []

    for pdf_path in pdf_files:
        print(f"  Processing {pdf_path.name}...")
        doc = pymupdf.open(str(pdf_path))
        for page in doc:
            text = page.get_text() or ""
            lines.append(f"--- Page {page_num} ---")
            lines.append(text.strip())
            page_num += 1
        doc.close()

    total_pages = page_num - 1
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[{book_id}] Wrote {total_pages} pages to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Extract text from English PDFs")
    parser.add_argument("--book", required=True, help="Book ID")
    parser.add_argument("--force", action="store_true", help="Force re-run")
    args = parser.parse_args()

    extract_text(args.book, force=args.force)


if __name__ == "__main__":
    main()
