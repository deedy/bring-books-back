"""Generate modern English rewrite using OpenAI Batch API (50% cheaper).

Splits chapters by section markers, submits as a batch job, then assembles results.

Usage:
    # Step 1: Submit batch
    uv run python -m pipeline.batch_modern --book ramayana --submit

    # Step 2: Check status
    uv run python -m pipeline.batch_modern --book ramayana --status

    # Step 3: Download results and assemble chapters_modern.json
    uv run python -m pipeline.batch_modern --book ramayana --collect
"""

import argparse
import json
import os
import re
from pathlib import Path

from openai import OpenAI

from pipeline.config import get_book, SERVER_DATA_DIR
from pipeline.generate_modern import PROMPT_TEMPLATE, _parse_response, _set_has_modern_text

BATCH_DIR = Path("data")


def _split_into_sections(ch: dict) -> list[dict]:
    """Split a chapter into sections based on SECTION markers."""
    paragraphs = ch["paragraphs"]
    sections = []
    current_paras = []
    current_start_idx = 0

    for i, p in enumerate(paragraphs):
        text = p if isinstance(p, str) else p["text"]
        if re.match(r"^SECTION\s+[IVXLCDM]+", text.strip()) and current_paras:
            sections.append({
                "start_idx": current_start_idx,
                "paragraphs": current_paras,
            })
            current_paras = [(i, p)]
            current_start_idx = i
        else:
            current_paras.append((i, p))

    if current_paras:
        sections.append({
            "start_idx": current_start_idx,
            "paragraphs": current_paras,
        })

    return sections


def _format_section(section: dict) -> str:
    lines = []
    for idx, p in section["paragraphs"]:
        text = p if isinstance(p, str) else p["text"]
        lines.append(f"[{idx}] {text}")
    return "\n\n".join(lines)


def submit(book_id: str):
    cfg = get_book(book_id)
    chapters_path = cfg.server_chapters_json

    if not os.path.exists(str(chapters_path)):
        print(f"No chapters.json found for {book_id}")
        return

    with open(str(chapters_path)) as f:
        chapters_data = json.load(f)
    chapters = chapters_data["chapters"]

    batch_dir = BATCH_DIR / book_id
    batch_dir.mkdir(parents=True, exist_ok=True)
    input_path = batch_dir / "batch_modern_input.jsonl"

    total_sections = 0
    total_in_tokens = 0

    with open(input_path, "w") as f:
        for ch in chapters:
            sections = _split_into_sections(ch)
            for sec_idx, section in enumerate(sections):
                section_text = _format_section(section)
                prompt = PROMPT_TEMPLATE.format(title=cfg.title) + section_text
                word_count = len(section_text.split())
                max_tokens = max(4000, int(word_count * 1.2))

                custom_id = f"{ch['id']}__sec{sec_idx}"
                request = {
                    "custom_id": custom_id,
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": "gpt-4.1",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": min(max_tokens, 16000),
                    },
                }
                f.write(json.dumps(request) + "\n")
                total_sections += 1
                total_in_tokens += len(prompt) // 4

    print(f"Created {total_sections} requests in {input_path}")
    print(f"Estimated: ~{total_in_tokens:,} input tokens, ~{int(total_in_tokens * 0.85):,} output tokens")
    est_cost = total_in_tokens * 1.0 / 1_000_000 + int(total_in_tokens * 0.85) * 4.0 / 1_000_000
    print(f"Estimated batch cost: ~${est_cost:.2f}")

    # Upload and create batch
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not set")
        return

    client = OpenAI(api_key=api_key)

    print("\nUploading input file...")
    with open(input_path, "rb") as f:
        uploaded = client.files.create(file=f, purpose="batch")
    print(f"  File ID: {uploaded.id}")

    print("Creating batch...")
    batch = client.batches.create(
        input_file_id=uploaded.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={"book_id": book_id, "type": "modern_rewrite"},
    )
    print(f"  Batch ID: {batch.id}")
    print(f"  Status: {batch.status}")

    # Save batch info
    info_path = batch_dir / "batch_modern_info.json"
    with open(info_path, "w") as f:
        json.dump({
            "batch_id": batch.id,
            "input_file_id": uploaded.id,
            "book_id": book_id,
            "total_sections": total_sections,
        }, f, indent=2)
    print(f"\nBatch info saved to {info_path}")
    print("Run --status to check progress, --collect when done.")


def status(book_id: str):
    batch_dir = BATCH_DIR / book_id
    info_path = batch_dir / "batch_modern_info.json"

    if not info_path.exists():
        print(f"No batch info found for {book_id}. Run --submit first.")
        return

    with open(info_path) as f:
        info = json.load(f)

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    batch = client.batches.retrieve(info["batch_id"])

    print(f"Batch ID: {batch.id}")
    print(f"Status: {batch.status}")
    if batch.request_counts:
        print(f"  Total:     {batch.request_counts.total}")
        print(f"  Completed: {batch.request_counts.completed}")
        print(f"  Failed:    {batch.request_counts.failed}")
    if batch.output_file_id:
        print(f"Output file: {batch.output_file_id}")
    if batch.error_file_id:
        print(f"Error file: {batch.error_file_id}")


def collect(book_id: str):
    cfg = get_book(book_id)
    batch_dir = BATCH_DIR / book_id
    info_path = batch_dir / "batch_modern_info.json"

    if not info_path.exists():
        print(f"No batch info found for {book_id}")
        return

    with open(info_path) as f:
        info = json.load(f)

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    batch = client.batches.retrieve(info["batch_id"])

    if batch.status != "completed":
        print(f"Batch not done yet. Status: {batch.status}")
        if batch.request_counts:
            print(f"  Completed: {batch.request_counts.completed}/{batch.request_counts.total}")
        return

    if not batch.output_file_id:
        print("No output file available")
        return

    # Download results
    print("Downloading results...")
    content = client.files.content(batch.output_file_id)
    output_path = batch_dir / "batch_modern_output.jsonl"
    with open(output_path, "wb") as f:
        f.write(content.read())

    # Parse results
    results: dict[str, dict[str, list[str]]] = {}  # ch_id -> {sec_idx -> paragraphs}
    failed = 0
    with open(output_path) as f:
        for line in f:
            entry = json.loads(line)
            custom_id = entry["custom_id"]
            ch_id, sec_part = custom_id.rsplit("__sec", 1)
            sec_idx = int(sec_part)

            if entry.get("error"):
                print(f"  FAILED: {custom_id}: {entry['error']}")
                failed += 1
                continue

            response = entry["response"]
            if response["status_code"] != 200:
                print(f"  ERROR {response['status_code']}: {custom_id}")
                failed += 1
                continue

            text = response["body"]["choices"][0]["message"]["content"]
            paragraphs = _parse_response(text)

            if ch_id not in results:
                results[ch_id] = {}
            results[ch_id][sec_idx] = paragraphs

    print(f"Parsed {sum(len(v) for v in results.values())} sections from {len(results)} chapters ({failed} failed)")

    # Load original chapters to get structure
    with open(str(cfg.server_chapters_json)) as f:
        chapters_data = json.load(f)

    # Assemble chapters_modern.json
    all_chapters = []
    for ch in chapters_data["chapters"]:
        ch_id = ch["id"]
        if ch_id not in results:
            print(f"  WARNING: No results for {ch_id}")
            all_chapters.append({"id": ch_id, "paragraphs": []})
            continue

        # Merge sections in order
        ch_sections = results[ch_id]
        merged_paragraphs = []
        for sec_idx in sorted(ch_sections.keys()):
            merged_paragraphs.extend(ch_sections[sec_idx])

        orig_count = len(ch["paragraphs"])
        print(f"  {ch_id}: {len(merged_paragraphs)} paragraphs (orig {orig_count})")
        all_chapters.append({"id": ch_id, "paragraphs": merged_paragraphs})

    modern_data = {
        "language": "Modern",
        "script": "Latin",
        "chapters": all_chapters,
    }

    modern_path = Path(SERVER_DATA_DIR) / "books" / book_id / "chapters_modern.json"
    modern_path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(modern_path), "w") as f:
        json.dump(modern_data, f, ensure_ascii=False)

    _set_has_modern_text(book_id)

    print(f"\nDone! Wrote {len(all_chapters)} chapters to {modern_path}")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("--book", required=True)
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--collect", action="store_true")
    args = parser.parse_args()

    if args.submit:
        submit(args.book)
    elif args.status:
        status(args.book)
    elif args.collect:
        collect(args.book)
    else:
        print("Specify --submit, --status, or --collect")
