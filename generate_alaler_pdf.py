"""
Generate a beautifully typeset PDF book of 'Alaler Gharer Dulal'
(The Spoilt Child) by Peary Chand Mitra.

Design system:
  - Headings: Inter Display (neo-grotesque sans)
  - Body: Source Serif 4 (readable serif for long-form text)
  - Palette: #FCFCFC bg, #0A0A0A text, single #1B3A5C accent (deep indigo), ≤5 hues
  - Baseline: √2 (1.414) leading ratio
  - Page: A5, generous margins
  - Chapter images: vintage Bengali woodblock print style from Gemini 3 Pro
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

INPUT_FILE = "data/alaler_english.txt"
OUTPUT_FILE = "data/alaler_book.pdf"
FONT_DIR = os.path.abspath("fonts")
IMAGE_DIR = os.path.abspath("alaler_images")

# ── Colors (5-hue max) ──
INK     = HexColor("#0A0A0A")
GRAY1   = HexColor("#333333")
GRAY2   = HexColor("#666666")
GRAY3   = HexColor("#999999")
GRAY4   = HexColor("#CCCCCC")
ACCENT  = HexColor("#1B3A5C")  # Deep indigo for colonial Calcutta aesthetic
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
# Structure: (start_page, chapter_num, title)
# Flat structure — no parts for this book
CHAPTERS = [
    (24,  1,  "Introduction to Baburam Babu"),
    (25,  2,  "The Spoilt Child"),
    (30,  3,  "Motilal Arrives in Bali"),
    (34,  4,  "English Education in Calcutta"),
    (39,  5,  "Baburam Sends a Messenger"),
    (45,  6,  "A Mother's Worries"),
    (52,  7,  "The Early History of Calcutta"),
    (58,  8,  "The Lawyer's Office"),
    (62,  9,  "Motilal's Decline"),
    (67,  10, "The Market at Baidyabati"),
    (71,  11, "Motilal's Wedding"),
    (75,  12, "Benibabu Visits Becharam"),
    (79,  13, "Bardaprasad's Wisdom"),
    (84,  14, "The Prank on the Kaviraj"),
    (89,  15, "The Hooghly Magistrate's Court"),
    (92,  16, "Thakchacha's House"),
    (94,  17, "The Barber and His Wife"),
    (97,  18, "The Encounter with Old Majumdar"),
    (101, 19, "Baburam's Illness and Death"),
    (105, 20, "The Funeral Rites"),
    (110, 21, "Motilal's Inheritance"),
    (113, 22, "The Trading Venture"),
    (116, 23, "The Failed Enterprise"),
    (121, 24, "Thakchacha's Forged Warrant"),
    (126, 25, "Journey to Jessore"),
    (130, 26, "Secrets Revealed in Sleep"),
    (135, 27, "The Tenants of Badar"),
    (141, 28, "Borda Babu's Honesty"),
    (144, 29, "Eviction from the House"),
    (148, 30, "The Journey to Benares"),
]

PAGE_TO_CHAPTER = {}
for i, (start_page, ch, title) in enumerate(CHAPTERS):
    end_page = CHAPTERS[i + 1][0] if i + 1 < len(CHAPTERS) else 999
    for p in range(start_page, end_page):
        PAGE_TO_CHAPTER[p] = (ch, title)


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

        title_y = page_y + PAGE_H * 0.72
        self._draw_shadow_text(c, "ALALER GHARER DULAL", center_x, title_y,
                               "InterDisplay-Bold", 26, shadow_offset=2.5)

        self._draw_shadow_text(c, "The Spoilt Child",
                               center_x, title_y - 34,
                               "InterDisplay-Med", 14, shadow_offset=1.5)

        self._draw_shadow_text(c, "Peary Chand Mitra",
                               center_x, title_y - 58,
                               "Inter-Light", 10, shadow_offset=1.2)

        self._draw_shadow_text(c, "Translated from the Bengali",
                               center_x, page_y + PAGE_H * 0.12,
                               "Inter-Light", 8, shadow_offset=1)


# ── Page number drawing ──
page_count = [0]
suppress_page_num = [False]


def draw_page_bg(canvas, doc):
    page_count[0] += 1
    canvas.saveState()
    canvas.setFillColor(BG)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.restoreState()
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
    s = line.strip()
    if not s:
        return False
    if re.match(r'^\d+\.?$', s):
        return True
    if re.match(r'^-?\d+$', s):
        return True
    # "Alaler Gharer Dulal" or "The Spoilt Child" running headers
    s_lower = s.lower()
    if s_lower in {"alaler gharer dulal", "the spoilt child",
                    "the spoilt child of alal's house",
                    "the spoilt child of the alal household",
                    "peary chand mitra", "tekchand thakur"}:
        return True
    # Page number patterns like "42 Alaler Gharer Dulal" or "Alaler Gharer Dulal 43"
    if re.match(r'^\d+\s+(Alaler|The Spoilt|In the)', s):
        return True
    if re.match(r'(Alaler Gharer Dulal|The Spoilt Child)\s+\d+$', s):
        return True
    # Variants from translation
    if re.match(r'^(The Spoilt Child of the Alal|The Spoilt Child of Alal)', s, re.I):
        return True
    if re.match(r'^In the Disarray of', s, re.I):
        return True
    return False


def is_chapter_header_line(line):
    """Check if a line is a chapter header/description line from the translation."""
    s = line.strip()
    if not s:
        return False
    # Standalone chapter number (1-30)
    if re.match(r'^(\d{1,2})\s*$', s):
        num = int(s.strip())
        return 1 <= num <= 30
    # "N. Long chapter description..." pattern
    m = re.match(r'^(\d{1,2})\.\s+\S', s)
    if m and 1 <= int(m.group(1)) <= 30:
        return True
    # "N Long chapter description..." (no period, starts with capital)
    m2 = re.match(r'^(\d{1,2})\s+[A-Z]', s)
    if m2 and 1 <= int(m2.group(1)) <= 30:
        return True
    return False


def extract_chapter_stream(pages):
    """Extract chapters using page-range mapping from CHAPTERS table.
    Strips running headers and chapter header lines."""
    page_nums = sorted(pages.keys())
    chapters = []

    for i, (start_page, ch_num, title) in enumerate(CHAPTERS):
        end_page = CHAPTERS[i + 1][0] if i + 1 < len(CHAPTERS) else 999
        ch_lines = []
        found_body = False

        for page_num in page_nums:
            if start_page <= page_num < end_page:
                content = pages[page_num]
                lines = content.split("\n")
                is_first_page = (page_num == start_page)

                for line in lines:
                    if is_running_header(line):
                        continue
                    # On first page, skip chapter header and description lines
                    if is_first_page and not found_body:
                        if is_chapter_header_line(line):
                            continue
                        # Skip chapter description continuation lines
                        s = line.strip()
                        if s and len(s) > 30 and (',' in s or '\u2014' in s or '—' in s):
                            # Looks like a multi-clause chapter description
                            if not any(c in s for c in ['.', '!', '?', '"', '\u201c']):
                                continue
                            # Has sentence-ending punctuation — might be body text
                            # Check if it starts with a preposition/conjunction (description continuation)
                            desc_starters = ('His ', 'Her ', 'Their ', 'The ', 'And ', 'Including ',
                                             'Encounters ', 'Barda ', 'Borda ')
                            if any(s.startswith(d) for d in desc_starters) and ',' in s:
                                continue
                    if line.strip():
                        found_body = True
                    ch_lines.append(line)
        chapters.append([ch_num, title, ch_lines])

    return chapters


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


def get_chapter_image(ch):
    path = os.path.join(IMAGE_DIR, f"chapter_{ch}.png")
    return path if os.path.exists(path) else None


def build_story(pages):
    story = []

    # ── Cover page ──
    story.append(SuppressPageNum())
    cover_path = os.path.join(IMAGE_DIR, "cover.png")
    if os.path.exists(cover_path):
        story.append(CoverPage(cover_path))
    else:
        story.append(Spacer(1, 55 * mm))
        story.append(Paragraph(
            "Alaler Gharer Dulal",
            ParagraphStyle("Title", fontName="InterDisplay-Bold", fontSize=30,
                           leading=36, textColor=INK, alignment=TA_CENTER,
                           spaceAfter=6)))
        story.append(Paragraph(
            "The Spoilt Child",
            ParagraphStyle("Sub", fontName="InterDisplay-Med", fontSize=14,
                           leading=18, textColor=GRAY2, alignment=TA_CENTER,
                           spaceAfter=16)))
        story.append(AccentRule(width=36, height=2))
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            "PEARY CHAND MITRA",
            ParagraphStyle("Author", fontName="Inter-SemiBold", fontSize=11,
                           leading=14, textColor=GRAY1, alignment=TA_CENTER,
                           spaceAfter=4)))
        story.append(Paragraph(
            "Translated from the Bengali &middot; Originally published 1858",
            ParagraphStyle("Meta", fontName="Inter-Light", fontSize=8,
                           leading=12, textColor=GRAY3, alignment=TA_CENTER)))
    story.append(PageBreak())

    # ── Title page ──
    story.append(SuppressPageNum())
    story.append(Spacer(1, 55 * mm))
    story.append(Paragraph(
        "Alaler Gharer Dulal",
        ParagraphStyle("Title", fontName="InterDisplay-Bold", fontSize=28,
                       leading=34, textColor=INK, alignment=TA_CENTER,
                       spaceAfter=6)))
    story.append(Paragraph(
        "The Spoilt Child",
        ParagraphStyle("Sub", fontName="InterDisplay-Med", fontSize=13,
                       leading=17, textColor=GRAY2, alignment=TA_CENTER,
                       spaceAfter=4)))
    story.append(Paragraph(
        "A Satire of Colonial Calcutta",
        ParagraphStyle("Sub2", fontName="InterDisplay-Med", fontSize=10,
                       leading=14, textColor=GRAY2, alignment=TA_CENTER,
                       spaceAfter=16)))
    story.append(AccentRule(width=36, height=2))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "PEARY CHAND MITRA",
        ParagraphStyle("Author", fontName="Inter-SemiBold", fontSize=11,
                       leading=14, textColor=GRAY1, alignment=TA_CENTER,
                       spaceAfter=2)))
    story.append(Paragraph(
        "(writing as Tekchand Thakur)",
        ParagraphStyle("Pen", fontName="Inter-Italic", fontSize=8,
                       leading=12, textColor=GRAY3, alignment=TA_CENTER,
                       spaceAfter=20)))
    story.append(Paragraph(
        "Translated from the Bengali &middot; Originally published 1858",
        ParagraphStyle("Meta", fontName="Inter-Light", fontSize=8,
                       leading=12, textColor=GRAY3, alignment=TA_CENTER,
                       spaceAfter=30)))
    story.append(Paragraph(
        "Bangiya Sahitya Parishat, Kolkata",
        ParagraphStyle("Pub", fontName="Inter-Light", fontSize=7.5,
                       leading=10, textColor=GRAY4, alignment=TA_CENTER)))
    story.append(PageBreak())

    # ── Half-title ──
    story.append(SuppressPageNum())
    story.append(Spacer(1, 55 * mm))
    story.append(Paragraph(
        "Alaler Gharer Dulal",
        ParagraphStyle("Half", fontName="InterDisplay-SBold", fontSize=18,
                       leading=22, textColor=GRAY1, alignment=TA_CENTER)))
    story.append(PageBreak())

    # ── Table of Contents ──
    story.append(SuppressPageNum())
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph("Contents", style_toc_head))
    story.append(GrayRule())
    story.append(Spacer(1, 6))

    for start_page, ch, title in CHAPTERS:
        entry = (f'<font name="Inter-SemiBold" color="#1B3A5C">'
                 f'{ch}.</font>&nbsp;&nbsp;&nbsp;{escape_xml(title)}')
        story.append(Paragraph(entry, style_toc_entry))

    story.append(PageBreak())

    # ── Body ──
    chapters = extract_chapter_stream(pages)
    print(f"Extracted {len(chapters)} chapter segments")

    for ch_num, ch_title, ch_lines in chapters:
        # Full-page illustration with title overlay
        img_path = get_chapter_image(ch_num)
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
        '<font name="Serif-Italic">Alaler Gharer Dulal</font> (The Spoilt Child)', col_style))
    story.append(Paragraph("Peary Chand Mitra (Tekchand Thakur)", col_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        'Translated from the Bengali original<br/>'
        'Originally published 1858',
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
        title="Alaler Gharer Dulal — The Spoilt Child",
        author="Peary Chand Mitra",
    )

    doc.build(story, onFirstPage=draw_page_bg, onLaterPages=draw_page_bg)
    size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"Wrote: {OUTPUT_FILE} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
