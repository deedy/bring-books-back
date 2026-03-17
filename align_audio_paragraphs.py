"""Align audio to paragraph boundaries using OpenAI Whisper API.

For each chapter MP3, transcribes with word-level timestamps, then aligns
the transcribed words to the source paragraphs to produce per-paragraph
timing in the audio manifest.

Caches Whisper transcriptions to data/{book_id}/audio/whisper_cache/ so
re-running alignment doesn't require re-transcription.
"""

import json
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import OpenAI


def _get_paragraph_texts(chapters_path: Path, ch_id: str) -> list[str]:
    """Get plain paragraph texts for a chapter."""
    with open(chapters_path) as f:
        data = json.load(f)
    for ch in data["chapters"]:
        if ch["id"] == ch_id:
            texts = []
            for p in ch.get("paragraphs", []):
                if isinstance(p, str):
                    texts.append(p)
                elif isinstance(p, dict):
                    texts.append(p.get("text", ""))
                else:
                    texts.append(str(p))
            return texts
    return []


def _normalize(text: str) -> list[str]:
    """Normalize text to lowercase words for matching."""
    # Replace curly quotes with ASCII so contractions match consistently
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    return re.findall(r"[a-z0-9]+(?:'[a-z]+)?", text.lower())


def _transcribe_file(client: OpenAI, audio_path: Path) -> list[dict]:
    """Transcribe an audio file and return word-level timestamps."""
    with open(audio_path, "rb") as f:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["word"],
        )
    return response.words or []


def _get_mp3_duration(path: Path) -> float:
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=30,
        )
        return float(r.stdout.strip()) if r.stdout.strip() else 0.0
    except Exception:
        return 0.0


def _transcribe_chapter(
    client: OpenAI, audio_dir: Path, ch_id: str,
) -> list[dict]:
    """Transcribe a chapter, using cache if available."""
    cache_dir = audio_dir / "whisper_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{ch_id}.json"

    # Return cached transcription if available
    if cache_file.exists():
        with open(cache_file) as f:
            cached = json.load(f)
        print(f"  {ch_id}: loaded {len(cached)} words from cache")
        return cached

    chapter_mp3 = audio_dir / f"{ch_id}.mp3"
    size_mb = chapter_mp3.stat().st_size / (1024 * 1024)

    if size_mb <= 25:
        print(f"  {ch_id}: transcribing full file ({size_mb:.1f}MB)")
        words = _transcribe_file(client, chapter_mp3)
        # Normalize to dicts
        result = [{"word": w.word, "start": w.start, "end": w.end} for w in words]
    else:
        # Too large — transcribe individual segments and offset timestamps
        print(f"  {ch_id}: file too large ({size_mb:.1f}MB), using segments")
        segments_dir = audio_dir / "segments"
        seg_files = sorted(
            segments_dir.glob(f"{ch_id}_seg*.mp3"),
            key=lambda p: int(re.search(r"seg(\d+)", p.stem).group(1)),
        )

        result = []
        cumulative_offset = 0.0
        for seg_path in seg_files:
            words = _transcribe_file(client, seg_path)
            for w in words:
                result.append({
                    "word": w.word,
                    "start": w.start + cumulative_offset,
                    "end": w.end + cumulative_offset,
                })
            dur = _get_mp3_duration(seg_path)
            cumulative_offset += dur

    # Save to cache
    with open(cache_file, "w") as f:
        json.dump(result, f)
    print(f"  {ch_id}: cached {len(result)} words")

    return result


def _seq_score(whisper_words: list[dict], pos: int, seq: list[str]) -> int:
    """Count how many of seq match whisper_words starting at pos (consecutive)."""
    score = 0
    for k, sw in enumerate(seq):
        wi = pos + k
        if wi < len(whisper_words) and whisper_words[wi]["word"] == sw:
            score += 1
    return score


def _align_words_to_paragraphs(
    words: list[dict], paragraphs: list[str], total_duration: float,
) -> list[dict]:
    """Match transcribed words to paragraph boundaries.

    Strategy: walk through the whisper stream sequentially. For each paragraph
    boundary, search forward from the current position for the first words of
    the next paragraph. This avoids drift from proportional estimates.
    """
    if not words or not paragraphs:
        return []

    # Normalize all paragraph words
    para_word_lists = [_normalize(p) for p in paragraphs]

    # Build a flat list of normalized whisper words with timestamps
    whisper_words = []
    for w in words:
        word = w["word"] if isinstance(w, dict) else w.word
        start = w["start"] if isinstance(w, dict) else w.start
        end = w["end"] if isinstance(w, dict) else w.end
        cleaned = re.findall(r"[a-z0-9]+(?:'[a-z]+)?", word.lower())
        for cw in cleaned:
            whisper_words.append({"word": cw, "start": start, "end": end})

    total_whisper = len(whisper_words)
    total_para_words = sum(len(pw) for pw in para_word_lists)
    if total_para_words == 0:
        return []

    # Walk through whisper stream sequentially, finding where each paragraph
    # starts by matching its first words as a consecutive sequence.
    para_starts = [0]  # first paragraph always starts at whisper index 0
    cursor = 0  # current position in whisper stream

    for pi in range(1, len(paragraphs)):
        prev_para_words = len(para_word_lists[pi - 1])
        if not para_word_lists[pi]:
            # Empty paragraph — starts where we are
            para_starts.append(cursor)
            continue

        # Advance cursor past the previous paragraph's expected words.
        # Allow some slack (TTS may add/remove words), so advance by 80% of
        # expected word count as a minimum starting point for search.
        min_advance = max(1, int(prev_para_words * 0.7))
        search_from = cursor + min_advance

        # Take first 8 words of next paragraph as sequence to find
        seq = para_word_lists[pi][:8]

        # Search forward from search_from, up to 2x the previous paragraph's
        # word count (generous to handle TTS insertions)
        search_limit = cursor + prev_para_words * 3
        search_limit = min(search_limit, total_whisper - 1)

        best_pos = search_from
        best_score = -1

        for candidate in range(max(search_from, cursor + 1), search_limit):
            score = _seq_score(whisper_words, candidate, seq)
            if score > best_score:
                best_score = score
                best_pos = candidate
                # If we matched all (or nearly all) of the sequence, stop early
                if score >= len(seq) - 1:
                    break

        # Ensure strictly after previous start
        best_pos = max(best_pos, para_starts[-1] + 1)
        para_starts.append(best_pos)
        cursor = best_pos

    # Build segments: each paragraph starts at its whisper word, ends where
    # the next one starts. Last paragraph ends at total_duration.
    segments = []
    for pi in range(len(paragraphs)):
        start_wi = para_starts[pi]

        if not para_word_lists[pi]:
            # Empty paragraph — zero duration at current position
            prev_end = segments[-1]["endSec"] if segments else 0.0
            segments.append({
                "paragraphStart": pi,
                "paragraphEnd": pi,
                "startSec": round(prev_end, 1),
                "endSec": round(prev_end, 1),
            })
            continue

        start_sec = whisper_words[start_wi]["start"] if start_wi < total_whisper else total_duration

        # End time = start of next non-empty paragraph, or total_duration
        end_sec = total_duration
        for npi in range(pi + 1, len(paragraphs)):
            if para_word_lists[npi]:
                next_wi = para_starts[npi]
                end_sec = whisper_words[next_wi]["start"] if next_wi < total_whisper else total_duration
                break

        segments.append({
            "paragraphStart": pi,
            "paragraphEnd": pi,
            "startSec": round(start_sec, 1),
            "endSec": round(end_sec, 1),
        })

    return segments


def run(book_id: str, chapter: str | None = None):
    audio_dir = Path(f"data/{book_id}/audio")
    chapters_path = Path(f"web/server-data/books/{book_id}/chapters.json")
    manifest_path = audio_dir / "manifest.json"

    if not manifest_path.exists():
        print(f"No manifest.json found at {manifest_path}")
        return

    with open(manifest_path) as f:
        manifest = json.load(f)

    api_key = os.environ.get("OPENAI_API_KEY_2") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("No OPENAI_API_KEY or OPENAI_API_KEY_2 set")
        return
    client = OpenAI(api_key=api_key)

    chapters_to_process = list(manifest["chapters"].keys())
    if chapter:
        chapters_to_process = [ch for ch in chapters_to_process if ch == chapter]

    for ch_id in sorted(chapters_to_process):
        print(f"\nProcessing {ch_id}...")

        # Get source paragraphs
        para_texts = _get_paragraph_texts(chapters_path, ch_id)
        if not para_texts:
            print(f"  No paragraphs found for {ch_id}")
            continue

        # Transcribe (uses cache if available)
        words = _transcribe_chapter(client, audio_dir, ch_id)
        print(f"  {len(words)} whisper words, {len(para_texts)} paragraphs")

        # Get total duration for end-fixing
        chapter_mp3 = audio_dir / f"{ch_id}.mp3"
        total_duration = _get_mp3_duration(chapter_mp3)

        # Align
        segments = _align_words_to_paragraphs(words, para_texts, total_duration)
        zero_dur = sum(1 for s in segments if s["endSec"] - s["startSec"] == 0)
        print(f"  Aligned to {len(segments)} segments ({zero_dur} zero-dur)")

        # Update manifest
        manifest["chapters"][ch_id]["segments"] = segments

        # Save incrementally
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

    # Also write to web/public
    web_manifest = Path(f"web/public/data/books/{book_id}/audio_manifest.json")
    if web_manifest.parent.exists():
        with open(web_manifest, "w") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"Wrote {web_manifest}")

    print(f"\nDone! Updated {manifest_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("book_id")
    parser.add_argument("--chapter", default=None)
    args = parser.parse_args()
    run(args.book_id, args.chapter)
