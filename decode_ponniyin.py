"""Decode Ponniyin Selvan PDF text by building a glyph-name-to-Unicode mapping.
The PDF uses Identity-H CMap with an incomplete ToUnicode map (only 39 of 332
glyphs mapped). PyMuPDF applies the partial map, so rawdict chars are a mix of:
  - Correct Unicode (code >= 0x0B80): already mapped by ToUnicode
  - Raw GIDs (code < 0x0B80): need remapping via glyph name -> Unicode

We build GID -> glyph name from the embedded font's post table,
then glyph name -> Unicode from Tamil phonetic naming conventions.
"""

import fitz
import re
import unicodedata
from fontTools.ttLib import TTFont

PDF_PATH = "data/ponniyin-selvan.pdf"
OUTPUT_FILE = "data/ponniyin_ocr.txt"

START_PAGE = 14   # 0-indexed, = PDF page 15
END_PAGE = 1939   # 0-indexed, = PDF page 1940

PULLI = "\u0BCD"  # virama

# Vowel marks (combining matras)
VOWEL_MARKS = {
    "aa": "\u0BBE", "i": "\u0BBF", "ii": "\u0BC0",
    "u": "\u0BC1", "uu": "\u0BC2", "e": "\u0BC6",
    "ee": "\u0BC7", "ai": "\u0BC8", "o": "\u0BCA",
    "oo": "\u0BCB", "au": "\u0BCC",
}

# Consonant base characters
CONSONANT_BASE = {
    "k": "\u0B95", "ng": "\u0B99", "c": "\u0B9A", "ny": "\u0B9E",
    "tt": "\u0B9F", "nn": "\u0BA3", "t": "\u0BA4", "n": "\u0BA8",
    "p": "\u0BAA", "m": "\u0BAE", "y": "\u0BAF", "r": "\u0BB0",
    "l": "\u0BB2", "v": "\u0BB5", "lll": "\u0BB4", "ll": "\u0BB3",
    "rr": "\u0BB1", "nnn": "\u0BA9",
}

# Grantha consonant base
GRANTHA_BASE = {
    "j": "\u0B9C", "ss": "\u0BB7", "s": "\u0BB8", "h": "\u0BB9",
    "sh": "\u0BB6", "x": "\u0B95\u0BCD\u0BB7",  # ksha
}


def glyph_name_to_unicode(name):
    """Convert a TSCII-style glyph name to a Unicode string."""
    if name in (".notdef", ".null"):
        return ""

    # Handle .ornl and other suffixes
    base_name = name.split(".")[0] if "." in name else name

    # Tamil vowels: tgv_X
    if base_name.startswith("tgv_"):
        suffix = base_name[4:]
        vowel_map = {
            "a": "\u0B85", "aa": "\u0B86", "i": "\u0B87", "ii": "\u0B88",
            "u": "\u0B89", "uu": "\u0B8A", "e": "\u0B8E", "ee": "\u0B8F",
            "ai": "\u0B90", "o": "\u0B92", "oo": "\u0B93", "au": "\u0B94",
            "q": "\u0B83",
        }
        return vowel_map.get(suffix, "")

    # Tamil vowel marks (matras): tgm_X
    if base_name.startswith("tgm_"):
        suffix = base_name[4:]
        if suffix == "pulli":
            return PULLI
        if suffix == "aumark":
            return "\u0BD7"
        return VOWEL_MARKS.get(suffix, "")

    # Tamil consonants: tgc_X
    if base_name.startswith("tgc_"):
        suffix = base_name[4:]
        # Try each consonant root (longest first to match "nnn" before "nn" before "n")
        for root in sorted(CONSONANT_BASE.keys(), key=len, reverse=True):
            if suffix == root + "a":  # inherent vowel: tgc_ka -> க
                return CONSONANT_BASE[root]
            if suffix == root:  # pure consonant with pulli: tgc_k -> க்
                return CONSONANT_BASE[root] + PULLI
            if suffix.startswith(root):
                vowel_part = suffix[len(root):]
                if vowel_part in VOWEL_MARKS:
                    return CONSONANT_BASE[root] + VOWEL_MARKS[vowel_part]
        return ""

    # Grantha consonants: tgg_X
    if base_name.startswith("tgg_"):
        suffix = base_name[4:]
        if suffix == "sri":
            return "\u0BB8\u0BCD\u0BB0\u0BC0"
        for root in sorted(GRANTHA_BASE.keys(), key=len, reverse=True):
            if suffix == root + "a":
                return GRANTHA_BASE[root]
            if suffix == root:
                return GRANTHA_BASE[root] + PULLI
            if suffix.startswith(root):
                vowel_part = suffix[len(root):]
                if vowel_part in VOWEL_MARKS:
                    return GRANTHA_BASE[root] + VOWEL_MARKS[vowel_part]
        return ""

    # Tamil numerals: tgn_X
    if base_name.startswith("tgn_"):
        num = base_name[4:]
        num_map = {
            "0": "\u0BE6", "1": "\u0BE7", "2": "\u0BE8", "3": "\u0BE9",
            "4": "\u0BEA", "5": "\u0BEB", "6": "\u0BEC", "7": "\u0BED",
            "8": "\u0BEE", "9": "\u0BEF", "10": "\u0BF0", "100": "\u0BF1",
            "1000": "\u0BF2",
        }
        return num_map.get(num, "")

    # Tamil symbols: tgs_X
    if base_name.startswith("tgs_"):
        sym = base_name[4:]
        sym_map = {
            "day": "\u0BF3", "month": "\u0BF4", "year": "\u0BF5",
            "rupee": "\u0BF9", "number": "\u0BF8", "debit": "\u0BF6",
            "credit": "\u0BF7", "asabove": "\u0BFA", "om": "\u0BD0",
        }
        return sym_map.get(sym, "")

    # Standard glyph names
    standard = {
        "space": " ", "exclam": "!", "quotedbl": '"', "numbersign": "#",
        "dollar": "$", "percent": "%", "ampersand": "&", "quotesingle": "'",
        "parenleft": "(", "parenright": ")", "asterisk": "*", "plus": "+",
        "comma": ",", "hyphen": "-", "period": ".", "slash": "/",
        "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
        "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
        "colon": ":", "semicolon": ";", "less": "<", "equal": "=",
        "greater": ">", "question": "?", "at": "@",
        "bracketleft": "[", "backslash": "\\", "bracketright": "]",
        "asciicircum": "^", "underscore": "_", "grave": "`",
        "braceleft": "{", "bar": "|", "braceright": "}", "asciitilde": "~",
        "quoteleft": "\u2018", "quoteright": "\u2019",
        "quotedblleft": "\u201C", "quotedblright": "\u201D",
        "bullet": "\u2022", "endash": "\u2013", "emdash": "\u2014",
        "copyright": "\u00A9", "onequarter": "\u00BC", "onehalf": "\u00BD",
        "threequarters": "\u00BE", "NBSPACE": "\u00A0",
        "uni200B": "\u200B", "ZWNJ": "\u200C", "ZWJ": "\u200D",
        "uni25CC": "\u25CC", "uni2219": "\u2219", "uni20B9": "\u20B9",
    }
    if base_name in standard:
        return standard[base_name]

    # Single letter names
    if len(name) == 1:
        return name

    return None  # unknown


def build_gid_unicode_map():
    """Build GID -> Unicode string from the embedded font's glyph names."""
    doc = fitz.open(PDF_PATH)
    for pg_num in range(20):
        page = doc[pg_num]
        for xref, _, _, name, _, _, _ in page.get_fonts(full=True):
            if "Tamil" in name:
                font_data = doc.extract_font(xref)
                font_bytes = font_data[3]
                with open("/tmp/tamil_font_ps.ttf", "wb") as f:
                    f.write(font_bytes)
                font = TTFont("/tmp/tamil_font_ps.ttf")
                glyph_order = font.getGlyphOrder()

                gid_map = {}  # GID -> Unicode string
                unmapped = []
                for gid, gname in enumerate(glyph_order):
                    uni = glyph_name_to_unicode(gname)
                    if uni is not None:
                        gid_map[gid] = uni
                    else:
                        unmapped.append((gid, gname))

                font.close()
                doc.close()
                if unmapped:
                    print(f"  WARNING: {len(unmapped)} unmapped: {unmapped[:5]}")
                return gid_map
    doc.close()
    raise RuntimeError("Tamil font not found")


# Parse the ToUnicode CMap to know which GIDs were already mapped by PyMuPDF
TOUNICODE_GIDS = {
    0x21, 0x26, 0x27, 0x28, 0x2a, 0x2b, 0x2c, 0x2d, 0x2e, 0x2f,
    0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x37, 0x3d, 0x43, 0x49,
    0x4f, 0x55, 0x5b, 0x61, 0x67, 0x6d, 0x73, 0x79, 0x7f, 0x85,
    0x8b, 0x91, 0x97, 0x9d, 0xa3, 0xa7, 0xab, 0xaf, 0xd8,
}


def extract_page_text(page, gid_map):
    """Extract Unicode text from a page, fixing the incomplete ToUnicode mapping."""
    blocks = page.get_text("rawdict")["blocks"]
    lines = []

    for block in blocks:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            chars = []
            for span in line["spans"]:
                font = span["font"]
                is_tamil_font = "Tamil" in font

                for ch_info in span.get("chars", []):
                    c = ch_info["c"]
                    code = ord(c)

                    if not is_tamil_font:
                        # ArialMT etc: already correct
                        chars.append(c)
                        continue

                    # Tamil font character: check if code was mapped by ToUnicode
                    if code >= 0x0B80:
                        # Already correctly mapped to Tamil Unicode by ToUnicode
                        chars.append(c)
                    else:
                        # Raw GID — remap via our table
                        if code in gid_map:
                            chars.append(gid_map[code])
                        else:
                            # Unknown GID, skip
                            pass

            line_text = "".join(chars).rstrip()
            if line_text:
                lines.append(line_text)

    text = "\n".join(lines)

    # Reorder left-side matras: in the PDF they appear before the consonant
    # (visual order), but Unicode requires them after (logical order).
    LEFT_MATRAS = "\u0BC6\u0BC7\u0BC8"  # ெ ே ை
    TAMIL_CONS = "[\u0B95-\u0BB9]"  # Tamil consonant range
    text = re.sub(f"([{LEFT_MATRAS}])({TAMIL_CONS})", r"\2\1", text)

    # NFC normalization combines sequences like க + ெ + ா → கொ
    text = unicodedata.normalize("NFC", text)
    return text


def main():
    print("Building GID -> Unicode map from font glyph names...")
    gid_map = build_gid_unicode_map()
    print(f"  {len(gid_map)} GIDs mapped to Unicode")

    doc = fitz.open(PDF_PATH)
    total = len(doc)
    content_pages = list(range(START_PAGE, min(END_PAGE + 1, total)))
    print(f"Processing {len(content_pages)} content pages...")

    with open(OUTPUT_FILE, "w") as f:
        for i, page_num in enumerate(content_pages):
            page = doc[page_num]
            text = extract_page_text(page, gid_map)
            f.write(f"--- Page {page_num + 1} ---\n")
            f.write(text)
            f.write("\n\n")

            if (i + 1) % 100 == 0 or i == 0:
                preview = text[:60].replace("\n", " ")
                print(f"  Page {page_num+1}/{total} ({i+1}/{len(content_pages)}) — {preview}...")

    doc.close()
    print(f"\nDone! Wrote {len(content_pages)} pages to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
