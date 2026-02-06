"""
Generate a beautifully typeset PDF book of 'The Twenty-Second Century'
by Rahul Sankrityayan.

Design system:
  - Headings: Inter Display (neo-grotesque sans)
  - Body: Source Serif 4 (readable serif for long-form text)
  - Palette: #FCFCFC bg, #0A0A0A text, single #0066FF accent, ≤5 hues
  - Baseline: √2 (1.414) leading ratio
  - Page: A5, generous margins
  - Chapter images: woodblock prints from Gemini 3 Pro
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

INPUT_FILE = "data/baeesweensadi_english.txt"
OUTPUT_FILE = "data/baeesweensadi_book.pdf"
FONT_DIR = os.path.abspath("fonts")
IMAGE_DIR = os.path.abspath("chapter_images")

# ── Colors (5-hue max) ──
INK     = HexColor("#0A0A0A")
GRAY1   = HexColor("#333333")
GRAY2   = HexColor("#666666")
GRAY3   = HexColor("#999999")
GRAY4   = HexColor("#CCCCCC")
ACCENT  = HexColor("#0066FF")
BG      = HexColor("#FCFCFC")

# ── Page dims ──
PAGE_W, PAGE_H = A5
MARGIN_TOP    = 20 * mm
MARGIN_BOTTOM = 24 * mm
MARGIN_LEFT   = 16 * mm
MARGIN_RIGHT  = 16 * mm
CONTENT_W = PAGE_W - MARGIN_LEFT - MARGIN_RIGHT

# ── Register fonts ──
# Sans (headings, UI elements)
pdfmetrics.registerFont(TTFont("Inter",              f"{FONT_DIR}/Inter-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Inter-Light",        f"{FONT_DIR}/Inter-Light.ttf"))
pdfmetrics.registerFont(TTFont("Inter-Italic",       f"{FONT_DIR}/Inter-Italic.ttf"))
pdfmetrics.registerFont(TTFont("Inter-SemiBold",     f"{FONT_DIR}/Inter-SemiBold.ttf"))
pdfmetrics.registerFont(TTFont("Inter-Bold",         f"{FONT_DIR}/Inter-Bold.ttf"))
pdfmetrics.registerFont(TTFont("InterDisplay-Bold",  f"{FONT_DIR}/InterDisplay-Bold.ttf"))
pdfmetrics.registerFont(TTFont("InterDisplay-SBold", f"{FONT_DIR}/InterDisplay-SemiBold.ttf"))
pdfmetrics.registerFont(TTFont("InterDisplay-Med",   f"{FONT_DIR}/InterDisplay-Medium.ttf"))
# Serif (body text — much more readable for long-form)
pdfmetrics.registerFont(TTFont("Serif",              f"{FONT_DIR}/SourceSerif4-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Serif-Italic",       f"{FONT_DIR}/SourceSerif4-Italic.ttf"))
pdfmetrics.registerFont(TTFont("Serif-SemiBold",     f"{FONT_DIR}/SourceSerif4-SemiBold.ttf"))
pdfmetrics.registerFont(TTFont("Serif-Bold",         f"{FONT_DIR}/SourceSerif4-Bold.ttf"))

# ── Corrected chapter mapping (from careful analysis of the text) ──
CHAPTERS = [
    (7,   "1",  "The End of a Long Sleep"),
    (8,   "2",  "The Orchards of Sebgram"),
    (11,  "3",  "The Present World"),
    (24,  "4",  "About the School"),
    (27,  "5",  "The Twentieth Century"),
    (41,  "6",  "The Village and the Villagers"),
    (49,  "7",  "The World of Children"),
    (61,  "8",  "The Railway Journey"),
    (87,  "9",  "Welcome at Nalanda"),
    (91,  "10", "Education System: Infant Class"),
    (97,  "11", "Education System: Children's Class"),
    (101, "12", "Education System: Youth Class"),
    (105, "13", "System of Governance"),
    (113, "14", "Departure from Nalanda"),
    (117, "15", "The Democracies of India"),
    (119, "16", "Things That Have Disappeared from the Present World"),
]

PAGE_TO_CHAPTER = {}
for i, (start_page, num, title) in enumerate(CHAPTERS):
    end_page = CHAPTERS[i + 1][0] if i + 1 < len(CHAPTERS) else 999
    for p in range(start_page, end_page):
        PAGE_TO_CHAPTER[p] = (num, title)

# ── All known running headers to strip ──
RUNNING_HEADERS = {
    # Main title variants
    "The Twenty-Second Century",
    "22nd Century",
    "The 22nd Century",
    "Baeesveen Sadi (22nd Century)",
    "22nd Century",
    # Chapter title variants (running headers from original pages)
    "The End of the Long Sleep",
    "The End of a Long Sleep",
    "The Orchard of Sebgram",
    "The Orchards of Sebgram",
    "The Present World",
    "The Twentieth Century",
    "Twentieth Century",
    "Village and Villagers",
    "The Village and the Villagers",
    "Village and the Villagers",
    "The World of Children",
    "The Child's World",
    "The Infant World",
    "Railway Journey",
    "The Railway Journey",
    "The Train Journey",
    "Welcome at Nalanda",
    "Welcome in Nalanda",
    "Nalanda",
    "Infant Class",
    "The System of Education: The Infant Class",
    "Education System: Infant Class",
    "Children's Class",
    "The Method of Education: Children's Class",
    "Education System: Children's Class",
    "Youth Class",
    "Education System: The Youth Class",
    "Education System: Youth Class",
    "System of Governance",
    "The System of Governance",
    "System of Administration",
    "Departure from Nalanda",
    "The Democracies of India",
    "Democracy in India",
    "Democracies of India",
    "The Democracies of India",
    "Things That Have Disappeared from the Present World",
    "Things That Have Vanished from the Present World",
    # Partial matches
    "Shishu-Kakscha",
    "Shishu-Sansar",
    "Gram aur Gramin",
    # Section sub-headers that repeat
    "About the University",
    "About the School",
    "Naalndaa mein Svaagat",
    "Naalandaa mein Svaagat",
    "Nalanda mein Svaagat",
    "Welcome at Nalanda",
    "Naalandaase Prasthaan",
    "Naalandaa se Prasthaan",
    "Nalanda se Prasthaan",
    "Bhaaratke Prajatantra",
    "Vartamaan Jagat se Uthi Cheejen",
    "Shaasan-Pranaalee",
    # Other common stray headers
    "The Twenty-Second",
    "Century",
    "The Infant World",
    "Infant World",
    "Child's World",
    "Children's World",
    "The Children's World",
    "World of Children",
    "Infant's World",
    "Infants' World",
    "Education System",
    "Education System:",
    "Education System: The Infant Class",
    "Education System: The Youth Class",
    "Shiksha-Paddhati : Shishu-Kakscha",
    "Shiksha Paddhati : Shishu Kakscha",
    "Gram and Gramin",
}

# Lowercase version for case-insensitive matching
RUNNING_HEADERS_LOWER = {h.lower() for h in RUNNING_HEADERS}


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
    """A full-bleed image with chapter title overlaid at the bottom."""
    def __init__(self, img_path, ch_num="", ch_title=""):
        Flowable.__init__(self)
        self.img_path = img_path
        self.ch_num = ch_num
        self.ch_title = ch_title
        self.width = 0
        self.height = 0

    def wrap(self, avail_w, avail_h):
        self.width = avail_w
        self.height = avail_h
        return avail_w, avail_h

    def _draw_shadow_text(self, c, text, x, y, font, size, shadow_offset=1.5):
        """Draw text with a soft dark shadow for legibility over any image."""
        # Shadow layers (multiple passes for softness)
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
        # Foreground text in white
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

        # Draw the full-bleed image
        c.drawImage(
            self.img_path,
            page_x, page_y,
            width=PAGE_W, height=PAGE_H,
            preserveAspectRatio=True,
            anchor='c',
        )

        # Chapter number — centered, above title
        chapter_label = f"CHAPTER  {self.ch_num}"
        self._draw_shadow_text(
            c, chapter_label,
            center_x, center_y + 18,
            "Inter-SemiBold", 9, shadow_offset=1.2,
        )

        # Chapter title — centered, word-wrapped
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

        # Draw lines centered vertically below the chapter number
        line_height = 26
        start_y = center_y - 10 - (len(lines) - 1) * line_height / 2
        for i, line in enumerate(lines):
            self._draw_shadow_text(
                c, line,
                center_x, start_y - i * line_height,
                "InterDisplay-Bold", 20, shadow_offset=1.5,
            )


# ── Page number drawing ──
page_count = [0]
no_page_num_pages = set()
# Track pages that have full-bleed images (suppress page number + bg)
full_image_pages = set()


def draw_page_number(canvas, doc):
    page_count[0] += 1
    page_num = page_count[0]
    if page_num in no_page_num_pages:
        return
    canvas.saveState()
    canvas.setFont("Inter-Light", 8)
    canvas.setFillColor(GRAY3)
    canvas.drawCentredString(PAGE_W / 2, 10 * mm, str(page_num))
    canvas.restoreState()


def draw_page_bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(BG)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.restoreState()
    draw_page_number(canvas, doc)


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
    # Standalone numbers (original page numbers)
    if re.match(r'^\d+\.?$', s):
        return True
    # Standalone short number-dash patterns like "-14"
    if re.match(r'^-?\d+$', s):
        return True
    # Known headers (case-insensitive)
    if s.lower() in RUNNING_HEADERS_LOWER:
        return True
    # Partial: lines that are just "N Title" like "2 The Twenty-Second Century"
    if re.match(r'^\d+\s+The Twenty', s):
        return True
    return False


def clean_page_text(text):
    """Remove OCR artifacts: standalone numbers, repeated running headers."""
    lines = text.split("\n")
    clean = []
    for line in lines:
        if is_running_header(line):
            continue
        clean.append(line)
    return "\n".join(clean).strip()


def text_to_paragraphs(text):
    """Split cleaned text into paragraph strings."""
    blocks = re.split(r'\n\n+', text)
    result = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        # Split on dialogue boundaries
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


def get_chapter_image(ch_num):
    """Get path to chapter image if it exists."""
    path = os.path.join(IMAGE_DIR, f"chapter_{ch_num}.png")
    return path if os.path.exists(path) else None


def build_story(pages):
    story = []
    page_nums = sorted(pages.keys())

    # ── Title page (page 1 in PDF) ──
    no_page_num_pages.add(1)
    story.append(Spacer(1, 55 * mm))
    story.append(Paragraph(
        "The Twenty-Second<br/>Century",
        ParagraphStyle("Title", fontName="InterDisplay-Bold", fontSize=32,
                       leading=38, textColor=INK, alignment=TA_CENTER,
                       spaceAfter=6)))
    story.append(Paragraph(
        "A Vision of the Future",
        ParagraphStyle("Sub", fontName="InterDisplay-Med", fontSize=12,
                       leading=16, textColor=GRAY2, alignment=TA_CENTER,
                       spaceAfter=16)))
    story.append(AccentRule(width=36, height=2))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "RAHUL SANKRITYAYAN",
        ParagraphStyle("Author", fontName="Inter-SemiBold", fontSize=11,
                       leading=14, textColor=GRAY1, alignment=TA_CENTER,
                       spaceAfter=4)))
    story.append(Paragraph(
        "Translated from the Hindi &middot; Originally published 1924",
        ParagraphStyle("Meta", fontName="Inter-Light", fontSize=8,
                       leading=12, textColor=GRAY3, alignment=TA_CENTER,
                       spaceAfter=30)))
    story.append(Paragraph(
        "Kitab Mahal, Allahabad",
        ParagraphStyle("Pub", fontName="Inter-Light", fontSize=7.5,
                       leading=10, textColor=GRAY4, alignment=TA_CENTER)))
    story.append(PageBreak())

    # ── Half-title (page 2) ──
    no_page_num_pages.add(2)
    story.append(Spacer(1, 55 * mm))
    story.append(Paragraph(
        "The Twenty-Second Century",
        ParagraphStyle("Half", fontName="InterDisplay-SBold", fontSize=18,
                       leading=22, textColor=GRAY1, alignment=TA_CENTER)))
    story.append(PageBreak())

    # ── Preface (page 3) ──
    no_page_num_pages.add(3)
    if 3 in pages:
        story.append(Paragraph("From the Author", style_preface_head))
        story.append(Spacer(1, 4))
        paras = text_to_paragraphs(pages[3])
        for p in paras:
            story.append(Paragraph(escape_xml(p), style_preface_body))
        story.append(PageBreak())

    # ── Table of Contents (page 4) ──
    no_page_num_pages.add(4)
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph("Contents", style_toc_head))
    story.append(GrayRule())
    story.append(Spacer(1, 6))
    for start_page, num, title in CHAPTERS:
        entry = (f'<font name="Inter-SemiBold" color="#0066FF">'
                 f'{num}.</font>&nbsp;&nbsp;&nbsp;{escape_xml(title)}')
        story.append(Paragraph(entry, style_toc_entry))
    story.append(PageBreak())

    # ── Body ──
    current_chapter = None
    first_para_in_chapter = True

    for page_num in page_nums:
        if page_num <= 5 or page_num == 121:
            continue

        content = pages[page_num]
        chapter = PAGE_TO_CHAPTER.get(page_num)

        # New chapter?
        if chapter and chapter != current_chapter:
            current_chapter = chapter
            ch_num, ch_title = chapter
            first_para_in_chapter = True

            # Full-page illustration with title overlay
            img_path = get_chapter_image(ch_num)
            if img_path:
                story.append(PageBreak())
                story.append(FullPageImage(img_path, ch_num, ch_title))

            # Chapter heading repeated on text page
            story.append(PageBreak())
            story.append(Spacer(1, 40))
            story.append(Paragraph(
                f"CHAPTER {escape_xml(ch_num)}",
                style_chapter_num))
            story.append(Paragraph(
                escape_xml(ch_title),
                style_chapter_title))
            story.append(AccentRule(width=28, height=1.5))
            story.append(Spacer(1, 14))

        text = clean_page_text(content)
        if not text:
            continue

        paras = text_to_paragraphs(text)
        for p in paras:
            if first_para_in_chapter:
                story.append(Paragraph(escape_xml(p), style_body_first))
                first_para_in_chapter = False
            else:
                story.append(Paragraph(escape_xml(p), style_body))

    # ── Colophon ──
    story.append(PageBreak())
    story.append(Spacer(1, 55 * mm))
    col_style = ParagraphStyle("Colophon", fontName="Inter-Light", fontSize=8,
                                leading=13, textColor=GRAY3, alignment=TA_CENTER,
                                spaceAfter=4)
    story.append(Paragraph(
        '<font name="Serif-Italic">The Twenty-Second Century</font>', col_style))
    story.append(Paragraph("Rahul Sankrityayan", col_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        'Translated from the Hindi original<br/>'
        '<font name="Serif-Italic">Baeesween Sadi</font> (1924)',
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
        title="The Twenty-Second Century",
        author="Rahul Sankrityayan",
    )

    doc.build(story, onFirstPage=draw_page_bg, onLaterPages=draw_page_bg)
    size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"Wrote: {OUTPUT_FILE} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
