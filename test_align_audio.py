"""Tests for align_audio_paragraphs._align_words_to_paragraphs."""

import pytest
from align_audio_paragraphs import _align_words_to_paragraphs, _normalize


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_words(text: str, wps: float = 2.5) -> list[dict]:
    """Fake whisper words from plain text at `wps` words-per-second."""
    tokens = text.split()
    dt = 1.0 / wps
    words = []
    t = 0.0
    for tok in tokens:
        words.append({"word": tok, "start": round(t, 2), "end": round(t + dt, 2)})
        t += dt
    return words


def _total_dur(words: list[dict]) -> float:
    return words[-1]["end"] if words else 0.0


# ── tests ────────────────────────────────────────────────────────────────────

class TestBasicAlignment:
    """Core happy-path tests."""

    def test_one_paragraph(self):
        text = "In my younger and more vulnerable years"
        words = _make_words(text)
        segs = _align_words_to_paragraphs(words, [text], _total_dur(words))
        assert len(segs) == 1
        assert segs[0]["paragraphStart"] == 0
        assert segs[0]["paragraphEnd"] == 0
        assert segs[0]["startSec"] == 0.0
        assert segs[0]["endSec"] > 0

    def test_two_paragraphs(self):
        p1 = "In my younger and more vulnerable years"
        p2 = "Whenever you feel like criticizing anyone"
        words = _make_words(f"{p1} {p2}")
        segs = _align_words_to_paragraphs(words, [p1, p2], _total_dur(words))
        assert len(segs) == 2
        assert segs[0]["paragraphStart"] == 0
        assert segs[1]["paragraphStart"] == 1
        # First segment should end before second starts (or equal)
        assert segs[0]["endSec"] <= segs[1]["endSec"]

    def test_many_paragraphs_all_get_segments(self):
        paragraphs = [f"Sentence number {i} with some extra words here" for i in range(20)]
        words = _make_words(" ".join(paragraphs))
        segs = _align_words_to_paragraphs(words, paragraphs, _total_dur(words))
        assert len(segs) == 20
        for i, seg in enumerate(segs):
            assert seg["paragraphStart"] == i
            assert seg["paragraphEnd"] == i


class TestNonStarvation:
    """The original bug: later paragraphs got zero duration."""

    def test_no_zero_duration_segments(self):
        """Every real paragraph should get non-zero duration."""
        paragraphs = [f"This is paragraph {i} with enough words to match" for i in range(50)]
        words = _make_words(" ".join(paragraphs))
        segs = _align_words_to_paragraphs(words, paragraphs, _total_dur(words))
        zero_dur = [s for s in segs if s["endSec"] - s["startSec"] == 0]
        assert len(zero_dur) == 0, f"{len(zero_dur)} of {len(segs)} segments have zero duration"

    def test_last_paragraph_has_duration(self):
        paragraphs = [f"Paragraph {i} words words words" for i in range(30)]
        words = _make_words(" ".join(paragraphs))
        segs = _align_words_to_paragraphs(words, paragraphs, _total_dur(words))
        last = segs[-1]
        assert last["endSec"] > last["startSec"], "Last paragraph has zero duration"

    def test_timestamps_monotonically_increase(self):
        paragraphs = [f"Some words for paragraph {i} that are unique" for i in range(25)]
        words = _make_words(" ".join(paragraphs))
        segs = _align_words_to_paragraphs(words, paragraphs, _total_dur(words))
        for i in range(1, len(segs)):
            assert segs[i]["startSec"] >= segs[i - 1]["startSec"], (
                f"Segment {i} start {segs[i]['startSec']} < segment {i-1} start {segs[i-1]['startSec']}"
            )


class TestEdgeCases:
    """Empty paragraphs, mismatched words, etc."""

    def test_empty_paragraph_gets_zero_duration(self):
        p1 = "Some real words here"
        p2 = ""  # e.g. a section header stripped by TTS
        p3 = "More real words after"
        words = _make_words(f"{p1} {p3}")
        segs = _align_words_to_paragraphs(words, [p1, p2, p3], _total_dur(words))
        assert len(segs) == 3
        assert segs[1]["endSec"] - segs[1]["startSec"] == 0

    def test_whisper_paraphrases_still_align(self):
        """Whisper often slightly changes words. Should still align reasonably."""
        paragraphs = [
            "The great Gatsby stood at the edge of his dock",
            "He stretched out his arms toward the dark water",
        ]
        # Whisper hears slightly different words
        whisper_text = "The great Gatsby stood at the edge of his dock He stretched out his arms towards the dark water"
        words = _make_words(whisper_text)
        segs = _align_words_to_paragraphs(words, paragraphs, _total_dur(words))
        assert len(segs) == 2
        # Both should have non-zero duration
        assert segs[0]["endSec"] > segs[0]["startSec"]
        assert segs[1]["endSec"] > segs[1]["startSec"]

    def test_empty_inputs(self):
        assert _align_words_to_paragraphs([], ["hello"], 0) == []
        assert _align_words_to_paragraphs([{"word": "hi", "start": 0, "end": 1}], [], 0) == []

    def test_last_segment_ends_at_total_duration(self):
        paragraphs = ["Hello world", "Goodbye world"]
        words = _make_words("Hello world Goodbye world")
        total = 10.0  # arbitrary, longer than actual words
        segs = _align_words_to_paragraphs(words, paragraphs, total)
        assert segs[-1]["endSec"] == total


class TestNormalize:
    def test_basic(self):
        assert _normalize("Hello, World!") == ["hello", "world"]

    def test_contractions(self):
        assert _normalize("don't won't") == ["don't", "won't"]

    def test_curly_quotes(self):
        """Curly quotes (U+2019) must be treated same as ASCII apostrophe."""
        assert _normalize("I\u2019ve") == ["i've"]
        assert _normalize("don\u2019t") == ["don't"]
        # Must match Whisper's ASCII output
        assert _normalize("I\u2019ve") == _normalize("I've")

    def test_numbers(self):
        assert _normalize("Chapter 42") == ["chapter", "42"]
