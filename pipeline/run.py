"""Pipeline orchestrator — run stages for any book.

Usage:
    uv run python -m pipeline.run --book chandrakanta              # Full pipeline
    uv run python -m pipeline.run --book chandrakanta --stage ocr  # Single stage
    uv run python -m pipeline.run --book chandrakanta --from translate  # Resume from stage
    uv run python -m pipeline.run --book chandrakanta --stage images --force
    uv run python -m pipeline.run --status                         # Status table
"""

import argparse
import os
import sys

from pipeline.config import get_book, BOOKS

# Stage order
STAGES = [
    "ocr",
    "translate",
    "chapters",
    "json",
    "annotations",
    "images",
    "characters",
    "heroes",
]


def check_stage(book_id, stage):
    """Check if a stage's output exists. Returns True if done."""
    cfg = get_book(book_id)
    checks = {
        "ocr": lambda: os.path.exists(str(cfg.ocr_txt)),
        "translate": lambda: os.path.exists(str(cfg.english_raw_txt)),
        "chapters": lambda: os.path.exists(str(cfg.chapters_def_json)),
        "json": lambda: os.path.exists(str(cfg.web_chapters_json)),
        "annotations": lambda: os.path.exists(str(cfg.web_annotations_json)),
        "images": lambda: (
            os.path.exists(str(cfg.images_dir))
            and any(f.endswith("_web.png") for f in os.listdir(str(cfg.images_dir)))
            if os.path.exists(str(cfg.images_dir)) else False
        ),
        "characters": lambda: (
            os.path.exists(str(cfg.web_annotations_json))
            and _has_character_images(book_id)
        ),
        "heroes": lambda: os.path.exists(
            str(cfg.web_book_dir.parent.parent / "images" / "heroes" / f"{book_id}.webp")
        ),
    }
    return checks.get(stage, lambda: False)()


def _has_character_images(book_id):
    from pipeline.config import WEB_DATA_DIR
    char_dir = WEB_DATA_DIR / "images" / "characters" / book_id
    if not char_dir.exists():
        return False
    return any(f.endswith(".webp") or f.endswith(".png") for f in os.listdir(str(char_dir)))


def run_stage(book_id, stage, force=False):
    """Run a single stage. Returns True on success."""
    print(f"\n{'='*60}")
    print(f"  Stage: {stage} | Book: {book_id}" + (" (FORCE)" if force else ""))
    print(f"{'='*60}\n")

    if stage == "ocr":
        from pipeline.ocr import run
        return run(book_id, force=force)
    elif stage == "translate":
        from pipeline.translate import run
        return run(book_id, force=force)
    elif stage == "chapters":
        from pipeline.detect_chapters import run
        return run(book_id, force=force)
    elif stage == "json":
        from pipeline.generate_json import run
        return run(book_id, force=force)
    elif stage == "annotations":
        from pipeline.generate_annotations import run
        return run(book_id, force=force)
    elif stage == "images":
        from pipeline.generate_images import run
        return run(book_id, force=force)
    elif stage == "characters":
        from pipeline.generate_characters import run
        return run(book_id, force=force)
    elif stage == "heroes":
        from pipeline.generate_heroes import run
        return run(book_id, force=force)
    else:
        print(f"Unknown stage: {stage}")
        return False


def print_status():
    """Print a status table for all books and stages."""
    # Header
    col_w = max(len(s) for s in STAGES) + 2
    book_w = max(len(bid) for bid in BOOKS) + 2
    header = f"{'Book':<{book_w}}" + "".join(f"{s:^{col_w}}" for s in STAGES)
    print(header)
    print("-" * len(header))

    for book_id in sorted(BOOKS.keys()):
        row = f"{book_id:<{book_w}}"
        for stage in STAGES:
            done = check_stage(book_id, stage)
            symbol = " done " if done else "  --  "
            row += f"{symbol:^{col_w}}"
        print(row)

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline orchestrator for book processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Stages (in order): {' -> '.join(STAGES)}",
    )
    parser.add_argument("--book", help="Book ID to process")
    parser.add_argument("--stage", choices=STAGES, help="Run a single stage")
    parser.add_argument("--from", dest="from_stage", choices=STAGES, help="Resume from this stage onwards")
    parser.add_argument("--force", action="store_true", help="Force re-run even if output exists")
    parser.add_argument("--status", action="store_true", help="Print status table")
    parser.add_argument("--list-books", action="store_true", help="List available book IDs")
    args = parser.parse_args()

    if args.status:
        print_status()
        return

    if args.list_books:
        for bid in sorted(BOOKS.keys()):
            cfg = BOOKS[bid]
            print(f"  {bid:<30s} {cfg.title} ({cfg.original_year}) — {cfg.original_language}")
        return

    if not args.book:
        parser.print_help()
        sys.exit(1)

    book_id = args.book
    if book_id not in BOOKS:
        print(f"Unknown book: {book_id}")
        print(f"Available: {', '.join(sorted(BOOKS.keys()))}")
        sys.exit(1)

    # Determine which stages to run
    if args.stage:
        stages_to_run = [args.stage]
    elif args.from_stage:
        start_idx = STAGES.index(args.from_stage)
        stages_to_run = STAGES[start_idx:]
    else:
        stages_to_run = STAGES

    print(f"Book: {book_id}")
    print(f"Stages: {' -> '.join(stages_to_run)}")
    print()

    for stage in stages_to_run:
        if not args.force and check_stage(book_id, stage):
            print(f"[{stage}] Already done, skipping (use --force to re-run)")
            continue

        ok = run_stage(book_id, stage, force=args.force)
        if not ok:
            print(f"\n[{stage}] Stage failed or skipped. Stopping pipeline.")
            sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  Pipeline complete for {book_id}!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
