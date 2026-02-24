"""
Generate a beautifully typeset PDF book of 'Ponniyin Selvan'
(The Son of Ponni) by Kalki Krishnamurthy.

Design system:
  - Headings: Inter Display (neo-grotesque sans)
  - Body: Source Serif 4 (readable serif for long-form text)
  - Palette: #FFFCF5 bg (warm parchment), #0A0A0A text, #C5961B accent (Chola gold)
  - Baseline: √2 (1.414) leading ratio
  - Page: A5, generous margins
  - Chapter images: Tanjore painting style from Gemini 3 Pro
"""

import re
import os
import sys

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

sys.path.insert(0, "scripts")
from parse_ponniyin_chapters import extract_chapters, chapters_to_paragraphs, PARTS

INPUT_FILE = "data/ponniyin_english.txt"
OUTPUT_FILE = "data/ponniyin_book.pdf"
FONT_DIR = os.path.abspath("fonts")
IMAGE_DIR = os.path.abspath("ponniyin_images")

# ── Colors ──
INK     = HexColor("#0A0A0A")
GRAY1   = HexColor("#333333")
GRAY2   = HexColor("#666666")
GRAY3   = HexColor("#999999")
GRAY4   = HexColor("#CCCCCC")
ACCENT  = HexColor("#C5961B")  # Chola gold
BG      = HexColor("#FFFCF5")  # Warm parchment

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

# ── Styles ──
BODY_SIZE = 10.5
BODY_LEADING = BODY_SIZE * 1.414

style_body = ParagraphStyle(
    "Body", fontName="Serif", fontSize=BODY_SIZE, leading=BODY_LEADING,
    textColor=INK, alignment=TA_JUSTIFY, firstLineIndent=16, spaceAfter=2,
)
style_body_first = ParagraphStyle("BodyFirst", parent=style_body, firstLineIndent=0)

style_chapter_num = ParagraphStyle(
    "ChapterNum", fontName="Inter-SemiBold", fontSize=9, leading=12,
    textColor=ACCENT, spaceAfter=4,
)
style_chapter_title = ParagraphStyle(
    "ChapterTitle", fontName="InterDisplay-Bold", fontSize=20, leading=24,
    textColor=INK, spaceAfter=6,
)
style_part_title = ParagraphStyle(
    "PartTitle", fontName="InterDisplay-Bold", fontSize=24, leading=30,
    textColor=INK, alignment=TA_CENTER, spaceAfter=8,
)
style_part_subtitle = ParagraphStyle(
    "PartSubtitle", fontName="InterDisplay-Med", fontSize=12, leading=16,
    textColor=ACCENT, alignment=TA_CENTER, spaceAfter=4,
)
style_toc_head = ParagraphStyle(
    "TOCHead", fontName="InterDisplay-Bold", fontSize=16, leading=20,
    textColor=INK, spaceAfter=18,
)
style_toc_entry = ParagraphStyle(
    "TOCEntry", fontName="Serif", fontSize=10, leading=18, textColor=GRAY1,
)
style_toc_part = ParagraphStyle(
    "TOCPart", fontName="Inter-SemiBold", fontSize=10.5, leading=16,
    textColor=ACCENT, spaceBefore=12, spaceAfter=4,
)


# ── Custom flowables ──
class SuppressPageNum(Flowable):
    def __init__(self):
        Flowable.__init__(self)
        self.width = self.height = 0
    def wrap(self, aw, ah): return 0, 0
    def draw(self): suppress_page_num[0] = True


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
        self.width = self.height = 0

    def wrap(self, aw, ah):
        self.width, self.height = aw, ah
        suppress_page_num[0] = True
        return aw, ah

    def _shadow_text(self, c, text, x, y, font, size, offset=1.5):
        for dx, dy, a in [(0,0,0.6),(offset,-offset,0.4),(-offset*0.5,offset*0.5,0.2)]:
            c.saveState(); c.setFillColorRGB(0.03,0.03,0.03,a)
            c.setFont(font, size); c.drawCentredString(x+dx,y+dy,text); c.restoreState()
        c.saveState(); c.setFillColorRGB(1,1,1)
        c.setFont(font, size); c.drawCentredString(x,y,text); c.restoreState()

    def draw(self):
        c = self.canv
        pad = 6
        px, py = -(MARGIN_LEFT+pad), -(MARGIN_BOTTOM+pad)
        cx = px + PAGE_W/2
        cy = py + PAGE_H/2
        c.drawImage(self.img_path, px, py, width=PAGE_W, height=PAGE_H,
                     preserveAspectRatio=True, anchor='c')
        self._shadow_text(c, self.ch_label, cx, cy+18, "Inter-SemiBold", 9, 1.2)
        words = self.ch_title.split()
        lines, cur = [], ""
        c.setFont("InterDisplay-Bold", 20)
        max_w = PAGE_W - 40*mm
        for w in words:
            t = (cur+" "+w).strip()
            if c.stringWidth(t,"InterDisplay-Bold",20) > max_w:
                lines.append(cur); cur = w
            else: cur = t
        if cur: lines.append(cur)
        lh = 26
        sy = cy - 10 - (len(lines)-1)*lh/2
        for i, ln in enumerate(lines):
            self._shadow_text(c, ln, cx, sy-i*lh, "InterDisplay-Bold", 20, 1.5)


class CoverPage(Flowable):
    def __init__(self, img_path):
        Flowable.__init__(self)
        self.img_path = img_path
        self.width = self.height = 0

    def wrap(self, aw, ah):
        self.width, self.height = aw, ah
        suppress_page_num[0] = True
        return aw, ah

    def _shadow_text(self, c, text, x, y, font, size, offset=2):
        for dx, dy, a in [(0,0,0.7),(offset,-offset,0.5),(-offset*0.5,offset*0.5,0.3)]:
            c.saveState(); c.setFillColorRGB(0.03,0.03,0.03,a)
            c.setFont(font, size); c.drawCentredString(x+dx,y+dy,text); c.restoreState()
        c.saveState(); c.setFillColorRGB(1,1,1)
        c.setFont(font, size); c.drawCentredString(x,y,text); c.restoreState()

    def draw(self):
        c = self.canv
        pad = 6
        px, py = -(MARGIN_LEFT+pad), -(MARGIN_BOTTOM+pad)
        cx = px + PAGE_W/2
        c.drawImage(self.img_path, px, py, width=PAGE_W, height=PAGE_H,
                     preserveAspectRatio=True, anchor='c')
        ty = py + PAGE_H * 0.72
        self._shadow_text(c, "PONNIYIN SELVAN", cx, ty, "InterDisplay-Bold", 26, 2.5)
        self._shadow_text(c, "The Son of the Kaveri", cx, ty-34, "InterDisplay-Med", 14, 1.5)
        self._shadow_text(c, "Kalki Krishnamurthy", cx, ty-58, "Inter-Light", 10, 1.2)
        self._shadow_text(c, "Translated from the Tamil", cx, py+PAGE_H*0.12, "Inter-Light", 8, 1)


# ── Page rendering ──
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
    canvas.drawCentredString(PAGE_W/2, 10*mm, str(page_count[0]))
    canvas.restoreState()


def escape_xml(s):
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")


def get_chapter_image(part, ch_num):
    path = os.path.join(IMAGE_DIR, f"p{part}_chapter_{ch_num}.png")
    return path if os.path.exists(path) else None


def build_story(chapters):
    story = []

    # ── Cover ──
    story.append(SuppressPageNum())
    cover = os.path.join(IMAGE_DIR, "cover.png")
    if os.path.exists(cover):
        story.append(CoverPage(cover))
    else:
        story.append(Spacer(1, 55*mm))
        story.append(Paragraph("Ponniyin Selvan", ParagraphStyle(
            "T", fontName="InterDisplay-Bold", fontSize=30, leading=36,
            textColor=INK, alignment=TA_CENTER, spaceAfter=6)))
        story.append(Paragraph("The Son of the Kaveri", ParagraphStyle(
            "S", fontName="InterDisplay-Med", fontSize=14, leading=18,
            textColor=GRAY2, alignment=TA_CENTER, spaceAfter=16)))
        story.append(AccentRule(36, 2))
        story.append(Spacer(1, 8))
        story.append(Paragraph("KALKI KRISHNAMURTHY", ParagraphStyle(
            "A", fontName="Inter-SemiBold", fontSize=11, leading=14,
            textColor=GRAY1, alignment=TA_CENTER)))
    story.append(PageBreak())

    # ── Title page ──
    story.append(SuppressPageNum())
    story.append(Spacer(1, 55*mm))
    story.append(Paragraph("Ponniyin Selvan", ParagraphStyle(
        "T2", fontName="InterDisplay-Bold", fontSize=28, leading=34,
        textColor=INK, alignment=TA_CENTER, spaceAfter=6)))
    story.append(Paragraph("The Son of the Kaveri", ParagraphStyle(
        "S2", fontName="InterDisplay-Med", fontSize=13, leading=17,
        textColor=GRAY2, alignment=TA_CENTER, spaceAfter=4)))
    story.append(Paragraph("An Epic of the Chola Dynasty", ParagraphStyle(
        "S3", fontName="InterDisplay-Med", fontSize=10, leading=14,
        textColor=GRAY2, alignment=TA_CENTER, spaceAfter=16)))
    story.append(AccentRule(36, 2))
    story.append(Spacer(1, 8))
    story.append(Paragraph("KALKI KRISHNAMURTHY", ParagraphStyle(
        "A2", fontName="Inter-SemiBold", fontSize=11, leading=14,
        textColor=GRAY1, alignment=TA_CENTER, spaceAfter=2)))
    story.append(Paragraph(
        "Translated from the Tamil &middot; Originally serialized 1950\u20131955",
        ParagraphStyle("M", fontName="Inter-Light", fontSize=8, leading=12,
                       textColor=GRAY3, alignment=TA_CENTER)))
    story.append(PageBreak())

    # ── Half-title ──
    story.append(SuppressPageNum())
    story.append(Spacer(1, 55*mm))
    story.append(Paragraph("Ponniyin Selvan", ParagraphStyle(
        "H", fontName="InterDisplay-SBold", fontSize=18, leading=22,
        textColor=GRAY1, alignment=TA_CENTER)))
    story.append(PageBreak())

    # ── Table of Contents ──
    story.append(SuppressPageNum())
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph("Contents", style_toc_head))
    story.append(GrayRule())
    story.append(Spacer(1, 6))

    current_part = None
    for ch in chapters:
        if ch["part"] != current_part:
            current_part = ch["part"]
            part_label = f"Part {ch['part']}: {ch['partName']}"
            story.append(Paragraph(escape_xml(part_label), style_toc_part))

        entry = (f'<font name="Inter-SemiBold" color="#C5961B">'
                 f'{ch["number"]}.</font>&nbsp;&nbsp;&nbsp;{escape_xml(ch["title"])}')
        story.append(Paragraph(entry, style_toc_entry))

    story.append(PageBreak())

    # ── Body ──
    current_part = None
    for ch in chapters:
        # Part divider page
        if ch["part"] != current_part:
            current_part = ch["part"]
            story.append(SuppressPageNum())
            story.append(Spacer(1, 60*mm))
            story.append(Paragraph(f"Part {ch['part']}", ParagraphStyle(
                "PN", fontName="Inter-SemiBold", fontSize=11, leading=14,
                textColor=ACCENT, alignment=TA_CENTER, spaceAfter=8)))
            story.append(Paragraph(escape_xml(ch["partName"]), style_part_title))
            story.append(AccentRule(40, 2))
            story.append(PageBreak())

        # Chapter image
        img_path = get_chapter_image(ch["part"], ch["number"])
        if img_path:
            story.append(PageBreak())
            label = f"CHAPTER  {ch['number']}"
            story.append(FullPageImage(img_path, label, ch["title"]))
            story.append(PageBreak())

        # Chapter heading
        story.append(Spacer(1, 40))
        story.append(Paragraph(f"CHAPTER {ch['number']}", style_chapter_num))
        story.append(Paragraph(escape_xml(ch["title"]), style_chapter_title))
        story.append(AccentRule(28, 1.5))
        story.append(Spacer(1, 14))

        # Body text
        paras = chapters_to_paragraphs(ch["body"])
        first = True
        for p in paras:
            if first:
                story.append(Paragraph(escape_xml(p), style_body_first))
                first = False
            else:
                story.append(Paragraph(escape_xml(p), style_body))

    # ── Colophon ──
    story.append(PageBreak())
    story.append(Spacer(1, 55*mm))
    col = ParagraphStyle("Col", fontName="Inter-Light", fontSize=8, leading=13,
                         textColor=GRAY3, alignment=TA_CENTER, spaceAfter=4)
    story.append(Paragraph(
        '<font name="Serif-Italic">Ponniyin Selvan</font> (The Son of the Kaveri)', col))
    story.append(Paragraph("Kalki Krishnamurthy", col))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Translated from the Tamil original<br/>"
        "Originally serialized 1950\u20131955 in Kalki magazine", col))
    story.append(Spacer(1, 14))
    story.append(Paragraph("&bull;", ParagraphStyle("dot", parent=col, textColor=GRAY4, fontSize=10)))
    story.append(Spacer(1, 14))
    story.append(Paragraph(
        "Text decoded from PDF via font glyph mapping &middot; Translation by GPT-4.1<br/>"
        "Chapter illustrations by Gemini 3 Pro<br/>"
        "Typeset in Source Serif 4 &amp; Inter &middot; Generated 2026", col))

    return story


def main():
    with open(INPUT_FILE) as f:
        text = f.read()

    chapters = extract_chapters(text)
    print(f"Extracted {len(chapters)} chapters")

    story = build_story(chapters)
    print(f"Built {len(story)} flowable elements")

    doc = SimpleDocTemplate(
        OUTPUT_FILE, pagesize=A5,
        topMargin=MARGIN_TOP, bottomMargin=MARGIN_BOTTOM,
        leftMargin=MARGIN_LEFT, rightMargin=MARGIN_RIGHT,
        title="Ponniyin Selvan — The Son of the Kaveri",
        author="Kalki Krishnamurthy",
    )
    doc.build(story, onFirstPage=draw_page_bg, onLaterPages=draw_page_bg)
    size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"Wrote: {OUTPUT_FILE} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
