"""
Generate a beautifully typeset PDF book of 'Mrinalini'
by Bankim Chandra Chattopadhyay.

Design system:
  - Headings: Inter Display (neo-grotesque sans)
  - Body: Source Serif 4 (readable serif for long-form text)
  - Palette: #FCFCFC bg, #0A0A0A text, single #8B0000 accent (deep vermilion), ≤5 hues
  - Baseline: √2 (1.414) leading ratio
  - Page: A5, generous margins
  - Chapter images: vintage Bengali miniature style from Gemini 3 Pro
"""

import re
import os

from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Flowable, Image as RLImage,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT

INPUT_FILE = "data/mrinalini_english.txt"
OUTPUT_FILE = "data/mrinalini_book.pdf"
FONT_DIR = os.path.abspath("fonts")
IMAGE_DIR = os.path.abspath("mrinalini_images")

# ── Colors (5-hue max) ──
INK     = HexColor("#0A0A0A")
GRAY1   = HexColor("#333333")
GRAY2   = HexColor("#666666")
GRAY3   = HexColor("#999999")
GRAY4   = HexColor("#CCCCCC")
ACCENT  = HexColor("#8B0000")  # Deep vermilion red for Bengali aesthetic
BG      = HexColor("#FCFCFC")

# ── Page dims ──
PAGE_W, PAGE_H = A5
MARGIN_TOP    = 20 * mm
MARGIN_BOTTOM = 24 * mm
MARGIN_LEFT   = 16 * mm
MARGIN_RIGHT  = 16 * mm
CONTENT_W = PAGE_W - MARGIN_LEFT - MARGIN_RIGHT

# ── Register fonts ──
pdfmetrics.registerFont(TTFont("Inter",              f"{FONT_DIR}/Inter-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Inter-Light",        f"{FONT_DIR}/Inter-Light.ttf"))
pdfmetrics.registerFont(TTFont("Inter-Italic",       f"{FONT_DIR}/Inter-Italic.ttf"))
pdfmetrics.registerFont(TTFont("Inter-SemiBold",     f"{FONT_DIR}/Inter-SemiBold.ttf"))
pdfmetrics.registerFont(TTFont("Inter-Bold",         f"{FONT_DIR}/Inter-Bold.ttf"))
pdfmetrics.registerFont(TTFont("InterDisplay-Bold",  f"{FONT_DIR}/InterDisplay-Bold.ttf"))
pdfmetrics.registerFont(TTFont("InterDisplay-SBold", f"{FONT_DIR}/InterDisplay-SemiBold.ttf"))
pdfmetrics.registerFont(TTFont("InterDisplay-Med",   f"{FONT_DIR}/InterDisplay-Medium.ttf"))
pdfmetrics.registerFont(TTFont("Serif",              f"{FONT_DIR}/SourceSerif4-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Serif-Italic",       f"{FONT_DIR}/SourceSerif4-Italic.ttf"))
pdfmetrics.registerFont(TTFont("Serif-SemiBold",     f"{FONT_DIR}/SourceSerif4-SemiBold.ttf"))
pdfmetrics.registerFont(TTFont("Serif-Bold",         f"{FONT_DIR}/SourceSerif4-Bold.ttf"))

# ── Chapter mapping ──
# Structure: (start_page, part_num, chapter_num_in_part, title)
# part_num is 1-4, chapter_num_in_part is the chapter within that part
CHAPTERS = [
    # Volume One
    (3,   1, 1,  "The Acharya"),
    (9,   1, 2,  "The Bird in the Cage"),
    (13,  1, 3,  "The Beggar Woman"),
    (19,  1, 4,  "The Messenger"),
    (25,  1, 5,  "The Greedy"),
    (29,  1, 6,  "Hrishikesh"),
    # Part Two
    (33,  2, 1,  "The Lord of Gauda"),
    (36,  2, 2,  "Kusum-nirmita"),
    (40,  2, 3,  "On the Boat"),
    (43,  2, 4,  "At the Window"),
    (45,  2, 5,  "Among the Ancestors"),
    (49,  2, 6,  "Pashupati"),
    (55,  2, 7,  "The Spy"),
    (58,  2, 8,  "Mohini"),
    (59,  2, 9,  "Enchanted"),
    (63,  2, 10, "The Trap"),
    (65,  2, 11, "Freedom"),
    (66,  2, 12, "The Guest's Reception"),
    # Part Three
    (69,  3, 1,  '"Who is he to you?"'),
    (71,  3, 2,  "The Vow"),
    (73,  3, 3,  "The Cause"),
    (76,  3, 4,  "The Initiation"),
    (79,  3, 5,  "Another Message"),
    (81,  3, 6,  '"I am Ushmadini"'),
    (86,  3, 7,  "News of Girijaya"),
    (88,  3, 8,  "Mrinalini's Letter"),
    (92,  3, 9,  "Poison in Nectar"),
    (97,  3, 10, "After So Many Days!"),
    # Part Four
    (101, 4, 1,  "Urnanabha"),
    (103, 4, 2,  "The Necklace Without a Thread"),
    (104, 4, 3,  "The Bird in the Cage"),
    (109, 4, 4,  "The Envoy of the Yavanas"),
    (111, 4, 5,  "The Net is Torn"),
    (114, 4, 6,  "The Cage is Broken"),
    (115, 4, 7,  "The Turmoil of the Yavanas"),
    (119, 4, 8,  "Is There Happiness for Mrinalini?"),
    (122, 4, 9,  "The Dream"),
    (123, 4, 10, "Love \u2014 Of Many Kinds"),
    (126, 4, 11, "The Earlier Story"),
    (129, 4, 12, "Counsel"),
    (132, 4, 13, "Muhammad Ali's Atonement"),
    (133, 4, 14, "The Immersion of the Metal Idol"),
    (136, 4, 15, "At the Final Hour"),
]

PART_NAMES = {1: "Volume One", 2: "Part Two", 3: "Part Three", 4: "Part Four"}

# Image keys match generate_mrinalini_images.py naming
def get_image_key(part, ch):
    return f"{part}_{ch}"

PAGE_TO_CHAPTER = {}
for i, (start_page, part, ch, title) in enumerate(CHAPTERS):
    end_page = CHAPTERS[i + 1][0] if i + 1 < len(CHAPTERS) else 999
    for p in range(start_page, end_page):
        PAGE_TO_CHAPTER[p] = (part, ch, title)


# ── Styles ──
BODY_SIZE = 10.5
BODY_LEADING = BODY_SIZE * 1.414

style_body = ParagraphStyle(
    "Body",
    fontName="Serif",
    fontSize=BODY_SIZE,
    leading=BODY_LEADING,
    textColor=INK,
    alignment=TA_JUSTIFY,
    firstLineIndent=16,
    spaceAfter=2,
)

style_body_first = ParagraphStyle(
    "BodyFirst",
    parent=style_body,
    firstLineIndent=0,
)

style_chapter_num = ParagraphStyle(
    "ChapterNum",
    fontName="Inter-SemiBold",
    fontSize=9,
    leading=12,
    textColor=ACCENT,
    spaceAfter=4,
)

style_chapter_title = ParagraphStyle(
    "ChapterTitle",
    fontName="InterDisplay-Bold",
    fontSize=20,
    leading=24,
    textColor=INK,
    spaceAfter=6,
)

style_toc_head = ParagraphStyle(
    "TOCHead",
    fontName="InterDisplay-Bold",
    fontSize=16,
    leading=20,
    textColor=INK,
    spaceAfter=18,
)

style_toc_entry = ParagraphStyle(
    "TOCEntry",
    fontName="Serif",
    fontSize=10.5,
    leading=20,
    textColor=GRAY1,
)

style_toc_part = ParagraphStyle(
    "TOCPart",
    fontName="InterDisplay-SBold",
    fontSize=11,
    leading=16,
    textColor=GRAY1,
    spaceBefore=10,
    spaceAfter=2,
)

style_preface_head = ParagraphStyle(
    "PrefaceHead",
    fontName="InterDisplay-SBold",
    fontSize=13,
    leading=17,
    textColor=GRAY1,
    spaceAfter=10,
)

style_preface_body = ParagraphStyle(
    "PrefaceBody",
    fontName="Serif",
    fontSize=9.5,
    leading=9.5 * 1.414,
    textColor=GRAY1,
    alignment=TA_JUSTIFY,
    spaceAfter=6,
)


# ── Custom flowables ──
class SuppressPageNum(Flowable):
    """Zero-height flowable that sets a flag to suppress page number on this page."""
    def __init__(self):
        Flowable.__init__(self)
        self.width = 0
        self.height = 0

    def wrap(self, avail_w, avail_h):
        return 0, 0

    def draw(self):
        suppress_page_num[0] = True


class AccentRule(Flowable):
    def __init__(self, width=30, height=2, color=ACCENT):
        Flowable.__init__(self)
        self.rule_width = width
        self.rule_height = height
        self.color = color
        self.width = width
        self.height = height + 10

    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.rect(0, 5, self.rule_width, self.rule_height, fill=1, stroke=0)


class GrayRule(Flowable):
    def __init__(self, width=None, color=GRAY4):
        Flowable.__init__(self)
        self.rule_width = width
        self.color = color
        self.height = 8

    def draw(self):
        w = self.rule_width or CONTENT_W
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(0.5)
        self.canv.line(0, 4, w, 4)


class FullPageImage(Flowable):
    """A full-bleed image with chapter title overlaid."""
    def __init__(self, img_path, ch_label="", ch_title=""):
        Flowable.__init__(self)
        self.img_path = img_path
        self.ch_label = ch_label
        self.ch_title = ch_title
        self.width = 0
        self.height = 0

    def wrap(self, avail_w, avail_h):
        self.width = avail_w
        self.height = avail_h
        suppress_page_num[0] = True
        return avail_w, avail_h

    def _draw_shadow_text(self, c, text, x, y, font, size, shadow_offset=1.5):
        for dx, dy, alpha in [
            (0, 0, 0.6),
            (shadow_offset, -shadow_offset, 0.4),
            (-shadow_offset * 0.5, shadow_offset * 0.5, 0.2),
            (shadow_offset * 0.3, shadow_offset * 0.3, 0.2),
        ]:
            c.saveState()
            c.setFillColorRGB(0.03, 0.03, 0.03, alpha)
            c.setFont(font, size)
            c.drawCentredString(x + dx, y + dy, text)
            c.restoreState()
        c.saveState()
        c.setFillColorRGB(1, 1, 1)
        c.setFont(font, size)
        c.drawCentredString(x, y, text)
        c.restoreState()

    def draw(self):
        c = self.canv
        pad = 6
        page_x = -(MARGIN_LEFT + pad)
        page_y = -(MARGIN_BOTTOM + pad)
        center_x = page_x + PAGE_W / 2
        center_y = page_y + PAGE_H / 2

        c.drawImage(
            self.img_path,
            page_x, page_y,
            width=PAGE_W, height=PAGE_H,
            preserveAspectRatio=True,
            anchor='c',
        )

        self._draw_shadow_text(
            c, self.ch_label,
            center_x, center_y + 18,
            "Inter-SemiBold", 9, shadow_offset=1.2,
        )

        title = self.ch_title
        max_w = PAGE_W - 40 * mm
        words = title.split()
        lines = []
        current = ""
        c.setFont("InterDisplay-Bold", 20)
        for w in words:
            test = (current + " " + w).strip()
            if c.stringWidth(test, "InterDisplay-Bold", 20) > max_w:
                lines.append(current)
                current = w
            else:
                current = test
        if current:
            lines.append(current)

        line_height = 26
        start_y = center_y - 10 - (len(lines) - 1) * line_height / 2
        for i, line in enumerate(lines):
            self._draw_shadow_text(
                c, line,
                center_x, start_y - i * line_height,
                "InterDisplay-Bold", 20, shadow_offset=1.5,
            )


class CoverPage(Flowable):
    """Full-page cover image with book title overlaid."""
    def __init__(self, img_path):
        Flowable.__init__(self)
        self.img_path = img_path
        self.width = 0
        self.height = 0

    def wrap(self, avail_w, avail_h):
        self.width = avail_w
        self.height = avail_h
        suppress_page_num[0] = True
        return avail_w, avail_h

    def _draw_shadow_text(self, c, text, x, y, font, size, shadow_offset=2):
        for dx, dy, alpha in [
            (0, 0, 0.7),
            (shadow_offset, -shadow_offset, 0.5),
            (-shadow_offset * 0.5, shadow_offset * 0.5, 0.3),
            (shadow_offset * 0.4, shadow_offset * 0.4, 0.3),
        ]:
            c.saveState()
            c.setFillColorRGB(0.03, 0.03, 0.03, alpha)
            c.setFont(font, size)
            c.drawCentredString(x + dx, y + dy, text)
            c.restoreState()
        c.saveState()
        c.setFillColorRGB(1, 1, 1)
        c.setFont(font, size)
        c.drawCentredString(x, y, text)
        c.restoreState()

    def draw(self):
        c = self.canv
        pad = 6
        page_x = -(MARGIN_LEFT + pad)
        page_y = -(MARGIN_BOTTOM + pad)
        center_x = page_x + PAGE_W / 2

        c.drawImage(
            self.img_path,
            page_x, page_y,
            width=PAGE_W, height=PAGE_H,
            preserveAspectRatio=True,
            anchor='c',
        )

        # Title at upper third
        title_y = page_y + PAGE_H * 0.7
        self._draw_shadow_text(c, "MRINALINI", center_x, title_y,
                               "InterDisplay-Bold", 36, shadow_offset=2.5)

        # Author below
        self._draw_shadow_text(c, "Bankim Chandra Chattopadhyay",
                               center_x, title_y - 40,
                               "InterDisplay-Med", 12, shadow_offset=1.5)

        # Subtitle at bottom
        self._draw_shadow_text(c, "Translated from the Bengali",
                               center_x, page_y + PAGE_H * 0.12,
                               "Inter-Light", 8, shadow_offset=1)


# ── Page number drawing ──
page_count = [0]
# Flag set by flowables to suppress page numbers on current page
suppress_page_num = [False]


def draw_page_bg(canvas, doc):
    page_count[0] += 1
    canvas.saveState()
    canvas.setFillColor(BG)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.restoreState()
    # Check and reset suppression flag
    if suppress_page_num[0]:
        suppress_page_num[0] = False
        return
    canvas.saveState()
    canvas.setFont("Inter-Light", 8)
    canvas.setFillColor(GRAY3)
    canvas.drawCentredString(PAGE_W / 2, 10 * mm, str(page_count[0]))
    canvas.restoreState()


# ── Parse ──
def parse_pages(text):
    parts = re.split(r"--- Page (\d+) ---\n", text)
    pages = {}
    i = 1
    while i < len(parts):
        page_num = int(parts[i])
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        pages[page_num] = body
        i += 2
    return pages


def is_running_header(line):
    """Check if a line is a running header that should be stripped."""
    s = line.strip()
    if not s:
        return False
    # Standalone numbers (OCR page numbers)
    if re.match(r'^\d+\.?$', s):
        return True
    if re.match(r'^-?\d+$', s):
        return True
    # "Mrinalini—" or "Mrinalini—2" style running headers
    if re.match(r'^Mrinalini\s*[\u2014\u2013\-]\s*\d*$', s):
        return True
    # Common Bengali OCR artifacts
    s_lower = s.lower()
    if s_lower in {"mrinalini", "bankim chandra chattopadhyay",
                    "bankim chandra", "chattopadhyay"}:
        return True
    return False


def is_chapter_header(line):
    """Check if a line is a chapter or part header. Returns match info or None."""
    s = line.strip()
    if not s:
        return None
    # "Volume One", "Part Two", etc.
    if re.match(r'^(Volume|Part)\s+(One|Two|Three|Four|Five)', s, re.I):
        return ('part', s)
    # "Chapter One: Title", "Chapter Two: Title", etc.
    m = re.match(r'^Chapter\s+\w+:\s*(.*)', s, re.I)
    if m:
        return ('chapter', s)
    # "Seventh Chapter: Title" variant
    m2 = re.match(r'^(First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth)\s+Chapter:', s, re.I)
    if m2:
        return ('chapter', s)
    return None


def clean_page_text(text):
    """Remove OCR artifacts: standalone numbers, running headers."""
    lines = text.split("\n")
    clean = []
    for line in lines:
        if is_running_header(line):
            continue
        clean.append(line)
    return "\n".join(clean).strip()


def extract_chapter_stream(pages):
    """
    Process all pages and split content at chapter boundaries.
    Returns a list of (part_num, ch_num, title, text) tuples,
    where text is the body content for that chapter with headers stripped.
    """
    # Build the full text stream, splitting pages at chapter headers
    # First, concatenate all pages in order
    page_nums = sorted(pages.keys())

    # We'll build segments: list of (part, ch, title, [text_lines])
    segments = []
    current_segment_lines = []  # Lines before the first chapter

    for page_num in page_nums:
        if page_num <= 2:  # Skip title/copyright pages
            continue

        content = pages[page_num]
        lines = content.split("\n")

        for line in lines:
            # Check if this line is a running header to skip
            if is_running_header(line):
                continue

            header = is_chapter_header(line)
            if header:
                htype, htext = header
                if htype == 'part':
                    # Part headers are informational; skip them as text
                    # (we handle part dividers via CHAPTERS mapping)
                    continue
                elif htype == 'chapter':
                    # Start a new segment — save previous lines to previous segment
                    if segments:
                        segments[-1][3].extend(current_segment_lines)
                    current_segment_lines = []
                    # Create new segment placeholder (part/ch/title filled in later)
                    segments.append([0, 0, htext, []])
                    continue

            current_segment_lines.append(line)

    # Don't forget the last segment
    if segments:
        segments[-1][3].extend(current_segment_lines)

    # Now match segments to our CHAPTERS mapping by order
    # The segments should appear in the same order as CHAPTERS
    if len(segments) != len(CHAPTERS):
        print(f"WARNING: Found {len(segments)} chapter segments but expected {len(CHAPTERS)}")
        # Try to match anyway
        for i, seg in enumerate(segments):
            print(f"  Segment {i+1}: {seg[2][:60]}")

    for i, (start_page, part, ch, title) in enumerate(CHAPTERS):
        if i < len(segments):
            segments[i][0] = part
            segments[i][1] = ch
            # Use our clean title, not the OCR'd one
            segments[i][2] = title

    return segments


def text_to_paragraphs(text):
    blocks = re.split(r'\n\n+', text)
    result = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
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
        result.extend(merged)
    return result


def escape_xml(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def get_chapter_image(part, ch):
    key = get_image_key(part, ch)
    path = os.path.join(IMAGE_DIR, f"{key}.png")
    return path if os.path.exists(path) else None


def build_story(pages):
    story = []
    page_nums = sorted(pages.keys())

    # ── Cover page ──
    story.append(SuppressPageNum())
    cover_path = os.path.join(IMAGE_DIR, "cover.png")
    if os.path.exists(cover_path):
        story.append(CoverPage(cover_path))
    else:
        # Fallback: text-only cover
        story.append(Spacer(1, 55 * mm))
        story.append(Paragraph(
            "Mrinalini",
            ParagraphStyle("Title", fontName="InterDisplay-Bold", fontSize=36,
                           leading=42, textColor=INK, alignment=TA_CENTER,
                           spaceAfter=6)))
        story.append(Paragraph(
            "A Historical Romance",
            ParagraphStyle("Sub", fontName="InterDisplay-Med", fontSize=12,
                           leading=16, textColor=GRAY2, alignment=TA_CENTER,
                           spaceAfter=16)))
        story.append(AccentRule(width=36, height=2))
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            "BANKIM CHANDRA CHATTOPADHYAY",
            ParagraphStyle("Author", fontName="Inter-SemiBold", fontSize=11,
                           leading=14, textColor=GRAY1, alignment=TA_CENTER,
                           spaceAfter=4)))
        story.append(Paragraph(
            "Translated from the Bengali &middot; Originally published 1882",
            ParagraphStyle("Meta", fontName="Inter-Light", fontSize=8,
                           leading=12, textColor=GRAY3, alignment=TA_CENTER)))
    story.append(PageBreak())

    # ── Title page ──
    story.append(SuppressPageNum())
    story.append(Spacer(1, 55 * mm))
    story.append(Paragraph(
        "Mrinalini",
        ParagraphStyle("Title", fontName="InterDisplay-Bold", fontSize=32,
                       leading=38, textColor=INK, alignment=TA_CENTER,
                       spaceAfter=6)))
    story.append(Paragraph(
        "A Historical Romance of 13th Century Bengal",
        ParagraphStyle("Sub", fontName="InterDisplay-Med", fontSize=11,
                       leading=15, textColor=GRAY2, alignment=TA_CENTER,
                       spaceAfter=16)))
    story.append(AccentRule(width=36, height=2))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "BANKIM CHANDRA CHATTOPADHYAY",
        ParagraphStyle("Author", fontName="Inter-SemiBold", fontSize=11,
                       leading=14, textColor=GRAY1, alignment=TA_CENTER,
                       spaceAfter=4)))
    story.append(Paragraph(
        "Translated from the Bengali &middot; Originally published 1882",
        ParagraphStyle("Meta", fontName="Inter-Light", fontSize=8,
                       leading=12, textColor=GRAY3, alignment=TA_CENTER,
                       spaceAfter=30)))
    story.append(Paragraph(
        "Aditya Prakashalaya, Kolkata",
        ParagraphStyle("Pub", fontName="Inter-Light", fontSize=7.5,
                       leading=10, textColor=GRAY4, alignment=TA_CENTER)))
    story.append(PageBreak())

    # ── Half-title ──
    story.append(SuppressPageNum())
    story.append(Spacer(1, 55 * mm))
    story.append(Paragraph(
        "Mrinalini",
        ParagraphStyle("Half", fontName="InterDisplay-SBold", fontSize=18,
                       leading=22, textColor=GRAY1, alignment=TA_CENTER)))
    story.append(PageBreak())

    # ── Table of Contents ──
    story.append(SuppressPageNum())
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph("Contents", style_toc_head))
    story.append(GrayRule())
    story.append(Spacer(1, 6))

    current_part = None
    for start_page, part, ch, title in CHAPTERS:
        if part != current_part:
            current_part = part
            story.append(Paragraph(
                escape_xml(PART_NAMES[part]),
                style_toc_part))
        entry = (f'<font name="Inter-SemiBold" color="#8B0000">'
                 f'{ch}.</font>&nbsp;&nbsp;&nbsp;{escape_xml(title)}')
        story.append(Paragraph(entry, style_toc_entry))

    story.append(PageBreak())

    # ── Body ──
    chapters = extract_chapter_stream(pages)
    print(f"Extracted {len(chapters)} chapter segments")
    current_part_num = None

    for part_num, ch_num, ch_title, ch_lines in chapters:
        # Part divider page if new part
        if part_num != current_part_num:
            current_part_num = part_num
            story.append(PageBreak())
            story.append(SuppressPageNum())
            story.append(Spacer(1, 65 * mm))
            story.append(Paragraph(
                escape_xml(PART_NAMES[part_num]),
                ParagraphStyle("PartTitle", fontName="InterDisplay-Bold",
                               fontSize=24, leading=30, textColor=INK,
                               alignment=TA_CENTER, spaceAfter=8)))
            story.append(AccentRule(width=40, height=2))
            story.append(PageBreak())

        # Full-page illustration with title overlay
        img_path = get_chapter_image(part_num, ch_num)
        if img_path:
            story.append(PageBreak())
            ch_label = f"CHAPTER  {ch_num}"
            story.append(FullPageImage(img_path, ch_label, ch_title))
            story.append(PageBreak())

        # Chapter heading on text page
        story.append(Spacer(1, 40))
        story.append(Paragraph(
            f"CHAPTER {ch_num}",
            style_chapter_num))
        story.append(Paragraph(
            escape_xml(ch_title),
            style_chapter_title))
        story.append(AccentRule(width=28, height=1.5))
        story.append(Spacer(1, 14))

        # Chapter body text
        body_text = "\n".join(ch_lines).strip()
        if not body_text:
            continue

        paras = text_to_paragraphs(body_text)
        first = True
        for p_text in paras:
            if first:
                story.append(Paragraph(escape_xml(p_text), style_body_first))
                first = False
            else:
                story.append(Paragraph(escape_xml(p_text), style_body))

    # ── Colophon ──
    story.append(PageBreak())
    story.append(Spacer(1, 55 * mm))
    col_style = ParagraphStyle("Colophon", fontName="Inter-Light", fontSize=8,
                                leading=13, textColor=GRAY3, alignment=TA_CENTER,
                                spaceAfter=4)
    story.append(Paragraph(
        '<font name="Serif-Italic">Mrinalini</font>', col_style))
    story.append(Paragraph("Bankim Chandra Chattopadhyay", col_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        'Translated from the Bengali original<br/>'
        'Originally published 1882',
        col_style))
    story.append(Spacer(1, 14))
    story.append(Paragraph("&bull;", ParagraphStyle("dot", parent=col_style,
                                                      textColor=GRAY4, fontSize=10)))
    story.append(Spacer(1, 14))
    story.append(Paragraph(
        "OCR by Sarvam AI &middot; Translation by GPT-4.1<br/>"
        "Chapter illustrations by Gemini 3 Pro<br/>"
        "Typeset in Source Serif 4 &amp; Inter &middot; Generated 2026",
        col_style))

    return story


def main():
    with open(INPUT_FILE) as f:
        text = f.read()

    pages = parse_pages(text)
    print(f"Parsed {len(pages)} pages")

    story = build_story(pages)
    print(f"Built {len(story)} flowable elements")

    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=A5,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
        leftMargin=MARGIN_LEFT,
        rightMargin=MARGIN_RIGHT,
        title="Mrinalini",
        author="Bankim Chandra Chattopadhyay",
    )

    doc.build(story, onFirstPage=draw_page_bg, onLaterPages=draw_page_bg)
    size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"Wrote: {OUTPUT_FILE} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
