"""
Process translated book text files into structured JSON for the web ebook reader.

Parses three books:
  1. Baeesween Sadi (The Twenty-Second Century) by Rahul Sankrityayan
  2. Mrinalini by Bankim Chandra Chattopadhyay
  3. Alaler Gharer Dulal (The Spoilt Child) by Peary Chand Mitra

Generates:
  - catalog.json (book list + author info)
  - books/<id>/meta.json and chapters.json for each book
  - Copies chapter/cover images to web/public/data/images/
  - Generates author bios (GPT-4.1) and portrait images (Gemini)
"""

import json
import os
import re
import shutil

from dotenv import load_dotenv
from openai import OpenAI
from google import genai
from google.genai import types as genai_types

load_dotenv()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DATA = os.path.join(ROOT, "web", "public", "data")

# ---------------------------------------------------------------------------
# Text parsing helpers (adapted from generate_pdf.py / generate_mrinalini_pdf.py)
# ---------------------------------------------------------------------------

def parse_pages(text):
    """Split text file into {page_num: page_text} dict."""
    parts = re.split(r"--- Page (\d+) ---\n", text)
    pages = {}
    i = 1
    while i < len(parts):
        page_num = int(parts[i])
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        pages[page_num] = body
        i += 2
    return pages


def text_to_paragraphs(text):
    """Split cleaned text into paragraph strings."""
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


# ---------------------------------------------------------------------------
# Baeesween Sadi helpers
# ---------------------------------------------------------------------------

BAEESWEEN_CHAPTERS = [
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

BAEESWEEN_RUNNING_HEADERS = {
    "The Twenty-Second Century", "22nd Century", "The 22nd Century",
    "Baeesveen Sadi (22nd Century)", "The End of the Long Sleep",
    "The End of a Long Sleep", "The Orchard of Sebgram",
    "The Orchards of Sebgram", "The Present World", "The Twentieth Century",
    "Twentieth Century", "Village and Villagers",
    "The Village and the Villagers", "Village and the Villagers",
    "The World of Children", "The Child's World", "The Infant World",
    "Railway Journey", "The Railway Journey", "The Train Journey",
    "Welcome at Nalanda", "Welcome in Nalanda", "Nalanda",
    "Infant Class", "The System of Education: The Infant Class",
    "Education System: Infant Class", "Children's Class",
    "The Method of Education: Children's Class",
    "Education System: Children's Class", "Youth Class",
    "Education System: The Youth Class", "Education System: Youth Class",
    "System of Governance", "The System of Governance",
    "System of Administration", "Departure from Nalanda",
    "The Democracies of India", "Democracy in India", "Democracies of India",
    "Things That Have Disappeared from the Present World",
    "Things That Have Vanished from the Present World",
    "Shishu-Kakscha", "Shishu-Sansar", "Gram aur Gramin",
    "About the University", "About the School",
    "Naalndaa mein Svaagat", "Naalandaa mein Svaagat",
    "Nalanda mein Svaagat", "Naalandaase Prasthaan",
    "Naalandaa se Prasthaan", "Nalanda se Prasthaan",
    "Bhaaratke Prajatantra", "Vartamaan Jagat se Uthi Cheejen",
    "Shaasan-Pranaalee", "The Twenty-Second", "Century",
    "Infant World", "Child's World", "Children's World",
    "The Children's World", "World of Children", "Infant's World",
    "Infants' World", "Education System", "Education System:",
    "Education System: The Infant Class",
    "Education System: The Youth Class",
    "Shiksha-Paddhati : Shishu-Kakscha",
    "Shiksha Paddhati : Shishu Kakscha", "Gram and Gramin",
}
BAEESWEEN_RUNNING_HEADERS_LOWER = {h.lower() for h in BAEESWEEN_RUNNING_HEADERS}


def baeesween_is_running_header(line):
    s = line.strip()
    if not s:
        return False
    if re.match(r'^\d+\.?$', s):
        return True
    if re.match(r'^-?\d+$', s):
        return True
    if s.lower() in BAEESWEEN_RUNNING_HEADERS_LOWER:
        return True
    if re.match(r'^\d+\s+The Twenty', s):
        return True
    return False


def baeesween_clean_page_text(text):
    lines = text.split("\n")
    return "\n".join(l for l in lines if not baeesween_is_running_header(l)).strip()


def process_baeesween_sadi():
    """Parse Baeesween Sadi text and return chapter data."""
    path = os.path.join(ROOT, "data", "baeesweensadi_english.txt")
    with open(path) as f:
        text = f.read()
    pages = parse_pages(text)
    print(f"  Baeesween Sadi: parsed {len(pages)} pages")

    # Build page-to-chapter mapping
    page_to_chapter = {}
    for i, (start_page, num, title) in enumerate(BAEESWEEN_CHAPTERS):
        end_page = BAEESWEEN_CHAPTERS[i + 1][0] if i + 1 < len(BAEESWEEN_CHAPTERS) else 999
        for p in range(start_page, end_page):
            page_to_chapter[p] = (num, title)

    # Extract chapter text
    chapters = []
    current_chapter = None
    chapter_text = []

    for page_num in sorted(pages.keys()):
        if page_num <= 5 or page_num == 121:
            continue
        chapter = page_to_chapter.get(page_num)
        if chapter and chapter != current_chapter:
            if current_chapter is not None:
                chapters.append((current_chapter, "\n\n".join(chapter_text)))
            current_chapter = chapter
            chapter_text = []
        cleaned = baeesween_clean_page_text(pages[page_num])
        if cleaned:
            chapter_text.append(cleaned)

    if current_chapter is not None:
        chapters.append((current_chapter, "\n\n".join(chapter_text)))

    result = []
    global_ch = 0
    for (ch_num, ch_title), raw_text in chapters:
        global_ch += 1
        paras = text_to_paragraphs(raw_text)
        word_count = sum(len(p.split()) for p in paras)
        result.append({
            "id": f"ch-{global_ch}",
            "number": global_ch,
            "title": ch_title,
            "part": None,
            "partName": None,
            "image": f"/data/images/chapters/baeesween-sadi/chapter_{ch_num}.png",
            "wordCount": word_count,
            "paragraphs": paras,
        })

    print(f"  Baeesween Sadi: {len(result)} chapters extracted")
    return result


# ---------------------------------------------------------------------------
# Mrinalini helpers
# ---------------------------------------------------------------------------

MRINALINI_CHAPTERS = [
    (3,   1, 1,  "The Acharya"),
    (9,   1, 2,  "The Bird in the Cage"),
    (13,  1, 3,  "The Beggar Woman"),
    (19,  1, 4,  "The Messenger"),
    (25,  1, 5,  "The Greedy"),
    (29,  1, 6,  "Hrishikesh"),
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

MRINALINI_PART_NAMES = {1: "Volume One", 2: "Part Two", 3: "Part Three", 4: "Part Four"}


def mrinalini_is_running_header(line):
    s = line.strip()
    if not s:
        return False
    if re.match(r'^\d+\.?$', s):
        return True
    if re.match(r'^-?\d+$', s):
        return True
    if re.match(r'^Mrinalini\s*[\u2014\u2013\-]\s*\d*$', s):
        return True
    s_lower = s.lower()
    if s_lower in {"mrinalini", "bankim chandra chattopadhyay",
                    "bankim chandra", "chattopadhyay"}:
        return True
    return False


def mrinalini_is_chapter_header(line):
    s = line.strip()
    if not s:
        return None
    if re.match(r'^(Volume|Part)\s+(One|Two|Three|Four|Five)', s, re.I):
        return ('part', s)
    m = re.match(r'^Chapter\s+\w+:\s*(.*)', s, re.I)
    if m:
        return ('chapter', s)
    m2 = re.match(r'^(First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth)\s+Chapter:', s, re.I)
    if m2:
        return ('chapter', s)
    return None


def mrinalini_extract_chapter_stream(pages):
    """Extract chapters using chapter header detection (same approach as generate_mrinalini_pdf.py)."""
    page_nums = sorted(pages.keys())
    segments = []
    current_segment_lines = []

    for page_num in page_nums:
        if page_num <= 2:
            continue
        content = pages[page_num]
        lines = content.split("\n")
        for line in lines:
            if mrinalini_is_running_header(line):
                continue
            header = mrinalini_is_chapter_header(line)
            if header:
                htype, htext = header
                if htype == 'part':
                    continue
                elif htype == 'chapter':
                    if segments:
                        segments[-1][3].extend(current_segment_lines)
                    current_segment_lines = []
                    segments.append([0, 0, htext, []])
                    continue
            current_segment_lines.append(line)

    if segments:
        segments[-1][3].extend(current_segment_lines)

    if len(segments) != len(MRINALINI_CHAPTERS):
        print(f"  WARNING: Found {len(segments)} chapter segments but expected {len(MRINALINI_CHAPTERS)}")

    for i, (start_page, part, ch, title) in enumerate(MRINALINI_CHAPTERS):
        if i < len(segments):
            segments[i][0] = part
            segments[i][1] = ch
            segments[i][2] = title

    return segments


def process_mrinalini():
    """Parse Mrinalini text and return chapter data."""
    path = os.path.join(ROOT, "data", "mrinalini_english.txt")
    with open(path) as f:
        text = f.read()
    pages = parse_pages(text)
    print(f"  Mrinalini: parsed {len(pages)} pages")

    segments = mrinalini_extract_chapter_stream(pages)
    print(f"  Mrinalini: {len(segments)} chapters extracted")

    result = []
    global_ch = 0
    for part_num, ch_num, ch_title, ch_lines in segments:
        global_ch += 1
        body_text = "\n".join(ch_lines).strip()
        paras = text_to_paragraphs(body_text) if body_text else []
        word_count = sum(len(p.split()) for p in paras)
        result.append({
            "id": f"ch-{global_ch}",
            "number": global_ch,
            "title": ch_title,
            "part": part_num,
            "partName": MRINALINI_PART_NAMES.get(part_num),
            "image": f"/data/images/chapters/mrinalini/{part_num}_{ch_num}.png",
            "wordCount": word_count,
            "paragraphs": paras,
        })

    return result


# ---------------------------------------------------------------------------
# Alaler Gharer Dulal helpers
# ---------------------------------------------------------------------------

ALALER_CHAPTERS = [
    (24,  1,  "The Wealthy Patriarch"),
    (27,  2,  "The Spoilt Heir"),
    (30,  3,  "Frolics in Bali"),
    (34,  4,  "The Police Station"),
    (39,  5,  "The Assembly of Sycophants"),
    (45,  6,  "The Mother\u2019s Sorrow"),
    (52,  7,  "Storm on the River"),
    (58,  8,  "The Lawyer\u2019s Office"),
    (62,  9,  "The Path of Vice"),
    (67,  10, "The Wedding Plot"),
    (71,  11, "The Wedding Poets"),
    (75,  12, "The Good Brother"),
    (79,  13, "The Wise Counselor"),
    (84,  14, "The Quack Doctor"),
    (89,  15, "The Magistrate\u2019s Court"),
    (92,  16, "The Trickster\u2019s Wife"),
    (94,  17, "The Second Marriage"),
    (97,  18, "News of the Remarriage"),
    (101, 19, "The Death of Baburam"),
    (105, 20, "The Funeral Farce"),
    (110, 21, "The New Master"),
    (113, 22, "The Trading Scheme"),
    (116, 23, "The Failed Merchant"),
    (121, 24, "The Forger\u2019s Downfall"),
    (126, 25, "The Indigo Dispute"),
    (130, 26, "The Prison"),
    (135, 27, "The Great Trial"),
    (141, 28, "The Honest Man"),
    (144, 29, "Eviction from Home"),
    (147, 30, "The Return Home"),
]


def alaler_is_running_header(line):
    s = line.strip()
    if not s:
        return False
    if re.match(r'^\d+\.?$', s):
        return True
    if re.match(r'^-?\d+$', s):
        return True
    s_lower = s.lower()
    if s_lower in {"alaler gharer dulal", "the spoilt child",
                    "the spoilt child of the alal household",
                    "the spoilt child of the alal family",
                    "the spoilt child of alal's house",
                    "peary chand mitra", "tekchand thakur"}:
        return True
    if re.match(r'^\d+\s+(Alaler|The Spoilt|In the)', s):
        return True
    if re.match(r'(Alaler Gharer Dulal|The Spoilt Child)\s+\d+$', s):
        return True
    if re.match(r'^(The Spoilt Child of the Alal|The Spoilt Child of Alal)', s, re.I):
        return True
    if re.match(r'^In the Disarray of', s, re.I):
        return True
    return False


def alaler_is_chapter_header_line(line):
    s = line.strip()
    if not s:
        return False
    if re.match(r'^(\d{1,2})\s*$', s):
        num = int(s.strip())
        return 1 <= num <= 30
    m = re.match(r'^(\d{1,2})\.\s+\S', s)
    if m and 1 <= int(m.group(1)) <= 30:
        return True
    m2 = re.match(r'^(\d{1,2})\s+[A-Z]', s)
    if m2 and 1 <= int(m2.group(1)) <= 30:
        return True
    return False


def process_alaler():
    """Parse Alaler Gharer Dulal text and return chapter data."""
    path = os.path.join(ROOT, "data", "alaler_english.txt")
    with open(path) as f:
        text = f.read()
    pages = parse_pages(text)
    print(f"  Alaler Gharer Dulal: parsed {len(pages)} pages")

    # Build page-to-chapter mapping
    page_to_chapter = {}
    for i, (start_page, ch_num, title) in enumerate(ALALER_CHAPTERS):
        end_page = ALALER_CHAPTERS[i + 1][0] if i + 1 < len(ALALER_CHAPTERS) else 999
        for p in range(start_page, end_page):
            page_to_chapter[p] = (ch_num, title)

    # Extract chapters using page-range assignment
    chapters_text = {ch: [] for _, ch, _ in ALALER_CHAPTERS}
    for page_num in sorted(pages.keys()):
        chapter_info = page_to_chapter.get(page_num)
        if not chapter_info:
            continue
        ch_num, title = chapter_info
        content = pages[page_num]
        lines = content.split("\n")
        start_page = ALALER_CHAPTERS[ch_num - 1][0]
        is_first_page = (page_num == start_page)
        found_body = bool(chapters_text[ch_num])

        for line in lines:
            if alaler_is_running_header(line):
                continue
            if is_first_page and not found_body:
                if alaler_is_chapter_header_line(line):
                    continue
                s = line.strip()
                if s and len(s) > 30 and (',' in s or '\u2014' in s or '—' in s):
                    if not any(c in s for c in ['.', '!', '?', '"', '\u201c']):
                        continue
                    desc_starters = ('His ', 'Her ', 'Their ', 'The ', 'And ', 'Including ',
                                     'Encounters ', 'Barda ', 'Borda ')
                    if any(s.startswith(d) for d in desc_starters) and ',' in s:
                        continue
            if line.strip():
                found_body = True
            chapters_text[ch_num].append(line)

    result = []
    for start_page, ch_num, ch_title in ALALER_CHAPTERS:
        body_text = "\n".join(chapters_text[ch_num]).strip()
        paras = text_to_paragraphs(body_text) if body_text else []
        word_count = sum(len(p.split()) for p in paras)
        result.append({
            "id": f"ch-{ch_num}",
            "number": ch_num,
            "title": ch_title,
            "part": None,
            "partName": None,
            "image": f"/data/images/chapters/alaler-gharer-dulal/chapter_{ch_num}.png",
            "wordCount": word_count,
            "paragraphs": paras,
        })

    print(f"  Alaler Gharer Dulal: {len(result)} chapters extracted")
    return result


# ---------------------------------------------------------------------------
# AI generation: author bios, book summaries, author portraits
# ---------------------------------------------------------------------------

def generate_author_bios():
    """Use GPT-4.1 to generate author bios."""
    client = OpenAI()
    bios = {}

    authors = [
        ("rahul-sankrityayan",
         "Rahul Sankrityayan (1893-1963), Hindi writer known as the 'Father of Hindi Travel Literature'. "
         "He was a polymath, Buddhist monk, historian, and author of over 150 books. "
         "His novel 'Baeesween Sadi' (The Twenty-Second Century, 1924) is one of the earliest Hindi science fiction novels."),
        ("bankim-chandra-chattopadhyay",
         "Bankim Chandra Chattopadhyay (1838-1894), Bengali writer and poet. "
         "He composed 'Vande Mataram', which became India's national song. "
         "He is considered one of the greatest Bengali novelists. "
         "'Mrinalini' (1882) is a historical romance set in 13th century Bengal during the invasion of Bakhtiyar Khilji."),
        ("peary-chand-mitra",
         "Peary Chand Mitra (1814-1882), Bengali writer and social reformer, pen name Tekchand Thakur. "
         "He was a product of Hindu College and the Young Bengal movement. "
         "He co-founded 'Masik Patrika' (Monthly Magazine) in 1854 to promote colloquial Bengali prose. "
         "'Alaler Gharer Dulal' (The Spoilt Child, 1858) is widely regarded as the first Bengali novel, "
         "a social satire about the moral decline of a wealthy family in colonial Calcutta."),
    ]

    for author_id, context in authors:
        print(f"  Generating bio for {author_id}...")
        resp = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are a literary biographer. Write concise, engaging author biographies for a book reader app. 2-3 paragraphs, no headings."},
                {"role": "user", "content": f"Write a 2-3 paragraph biography for: {context}"},
            ],
            max_tokens=500,
        )
        bios[author_id] = resp.choices[0].message.content.strip()

    return bios


def generate_book_summaries(baeesween_chapters, mrinalini_chapters, alaler_chapters):
    """Use GPT-4.1 to generate book summaries."""
    client = OpenAI()
    summaries = {}

    # Baeesween Sadi
    ch_titles = [ch["title"] for ch in baeesween_chapters]
    first_paras = " ".join(baeesween_chapters[0]["paragraphs"][:3]) if baeesween_chapters else ""
    print("  Generating summary for Baeesween Sadi...")
    resp = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": "Write a compelling ~100 word book summary for a reader app. No spoilers."},
            {"role": "user", "content": (
                f"Book: 'The Twenty-Second Century' (Baeesween Sadi) by Rahul Sankrityayan, 1924. "
                f"Hindi science fiction novel. Chapters: {', '.join(ch_titles)}. "
                f"Opening: {first_paras[:500]}"
            )},
        ],
        max_tokens=200,
    )
    summaries["baeesween-sadi"] = resp.choices[0].message.content.strip()

    # Mrinalini
    ch_titles = [ch["title"] for ch in mrinalini_chapters]
    first_paras = " ".join(mrinalini_chapters[0]["paragraphs"][:3]) if mrinalini_chapters else ""
    print("  Generating summary for Mrinalini...")
    resp = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": "Write a compelling ~100 word book summary for a reader app. No spoilers."},
            {"role": "user", "content": (
                f"Book: 'Mrinalini' by Bankim Chandra Chattopadhyay, 1882. "
                f"Bengali historical romance set in 13th century Bengal. Chapters: {', '.join(ch_titles)}. "
                f"Opening: {first_paras[:500]}"
            )},
        ],
        max_tokens=200,
    )
    summaries["mrinalini"] = resp.choices[0].message.content.strip()

    # Alaler Gharer Dulal
    ch_titles = [ch["title"] for ch in alaler_chapters]
    first_paras = " ".join(alaler_chapters[0]["paragraphs"][:3]) if alaler_chapters else ""
    print("  Generating summary for Alaler Gharer Dulal...")
    resp = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": "Write a compelling ~100 word book summary for a reader app. No spoilers."},
            {"role": "user", "content": (
                f"Book: 'Alaler Gharer Dulal' (The Spoilt Child) by Peary Chand Mitra, 1858. "
                f"Bengali social satire, considered the first Bengali novel. Set in colonial Calcutta. "
                f"Chapters: {', '.join(ch_titles)}. "
                f"Opening: {first_paras[:500]}"
            )},
        ],
        max_tokens=200,
    )
    summaries["alaler-gharer-dulal"] = resp.choices[0].message.content.strip()

    return summaries


def generate_author_portraits():
    """Use Gemini to generate author portrait images."""
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    portraits = {}

    authors = [
        ("rahul-sankrityayan",
         "A dignified portrait painting of Rahul Sankrityayan, an Indian scholar and writer from the early 20th century. "
         "He has a strong, intellectual face, wearing simple Indian attire. "
         "Painted in a classical portrait style with warm tones, reminiscent of early 20th century Indian portraiture. "
         "Background is a warm neutral tone."),
        ("bankim-chandra-chattopadhyay",
         "A dignified portrait painting of Bankim Chandra Chattopadhyay, a 19th century Bengali writer. "
         "He has a distinguished appearance with traditional Bengali attire and a thoughtful expression. "
         "Painted in a classical portrait style with warm tones, reminiscent of 19th century Bengal Renaissance portraiture. "
         "Background is a warm neutral tone."),
        ("peary-chand-mitra",
         "A dignified portrait painting of Peary Chand Mitra, a Bengali writer and social reformer from the mid-19th century. "
         "He has a scholarly appearance with traditional Bengali attire, a clean-shaven face, and intelligent eyes. "
         "Painted in a classical portrait style with warm sepia tones, reminiscent of early Victorian-era Indian portraiture. "
         "Background is a warm neutral tone."),
    ]

    for author_id, prompt in authors:
        print(f"  Generating portrait for {author_id}...")
        out_path = os.path.join(WEB_DATA, "images", "authors", f"{author_id}.png")

        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash-exp-image-generation",
                    contents=prompt,
                    config=genai_types.GenerateContentConfig(
                        response_modalities=["IMAGE", "TEXT"],
                    ),
                )
                if response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                            with open(out_path, "wb") as f:
                                f.write(part.inline_data.data)
                            portraits[author_id] = out_path
                            print(f"    Saved portrait: {out_path}")
                            break
                if author_id in portraits:
                    break
                print(f"    Attempt {attempt+1}: no image returned, retrying...")
            except Exception as e:
                print(f"    Attempt {attempt+1} failed: {e}")

        if author_id not in portraits:
            print(f"    WARNING: Could not generate portrait for {author_id}")

    return portraits


# ---------------------------------------------------------------------------
# Image copying
# ---------------------------------------------------------------------------

def copy_images():
    """Copy chapter and cover images to web/public/data/images/."""
    # Baeesween Sadi
    src_dir = os.path.join(ROOT, "chapter_images")
    dst_chapters = os.path.join(WEB_DATA, "images", "chapters", "baeesween-sadi")
    dst_covers = os.path.join(WEB_DATA, "images", "covers")
    os.makedirs(dst_chapters, exist_ok=True)
    os.makedirs(dst_covers, exist_ok=True)

    for fname in os.listdir(src_dir):
        if not fname.endswith(".png"):
            continue
        src = os.path.join(src_dir, fname)
        if fname == "cover.png":
            shutil.copy2(src, os.path.join(dst_covers, "baeesween-sadi.png"))
        else:
            shutil.copy2(src, os.path.join(dst_chapters, fname))

    # Mrinalini
    src_dir = os.path.join(ROOT, "mrinalini_images")
    dst_chapters = os.path.join(WEB_DATA, "images", "chapters", "mrinalini")
    os.makedirs(dst_chapters, exist_ok=True)

    for fname in os.listdir(src_dir):
        if not fname.endswith(".png"):
            continue
        src = os.path.join(src_dir, fname)
        if fname == "cover.png":
            shutil.copy2(src, os.path.join(dst_covers, "mrinalini.png"))
        else:
            shutil.copy2(src, os.path.join(dst_chapters, fname))

    # Alaler Gharer Dulal
    src_dir = os.path.join(ROOT, "alaler_images")
    dst_chapters = os.path.join(WEB_DATA, "images", "chapters", "alaler-gharer-dulal")
    os.makedirs(dst_chapters, exist_ok=True)

    if os.path.exists(src_dir):
        for fname in os.listdir(src_dir):
            if not fname.endswith(".png"):
                continue
            src = os.path.join(src_dir, fname)
            if fname == "cover.png":
                shutil.copy2(src, os.path.join(dst_covers, "alaler-gharer-dulal.png"))
            else:
                shutil.copy2(src, os.path.join(dst_chapters, fname))

    print("  Images copied to web/public/data/images/")


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------

def get_preview_text(chapters, max_words=500):
    """Get first ~500 words from chapter 1."""
    if not chapters:
        return ""
    words = []
    for para in chapters[0]["paragraphs"]:
        words.extend(para.split())
        if len(words) >= max_words:
            break
    return " ".join(words[:max_words])


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Wrote: {path}")


def main():
    print("=== Processing books ===\n")

    # 1. Parse text files
    print("Parsing text files...")
    baeesween_chapters = process_baeesween_sadi()
    mrinalini_chapters = process_mrinalini()
    alaler_chapters = process_alaler()

    # 2. Copy images
    print("\nCopying images...")
    copy_images()

    # 3. Generate AI content
    print("\nGenerating AI content...")
    author_bios = generate_author_bios()
    book_summaries = generate_book_summaries(baeesween_chapters, mrinalini_chapters, alaler_chapters)
    generate_author_portraits()

    # 4. Compute word counts
    baeesween_total_words = sum(ch["wordCount"] for ch in baeesween_chapters)
    mrinalini_total_words = sum(ch["wordCount"] for ch in mrinalini_chapters)
    alaler_total_words = sum(ch["wordCount"] for ch in alaler_chapters)

    # 5. Write chapters.json for each book
    print("\nWriting JSON output...")

    # Baeesween Sadi chapters
    baeesween_chapters_out = []
    for ch in baeesween_chapters:
        baeesween_chapters_out.append({
            "id": ch["id"],
            "number": ch["number"],
            "title": ch["title"],
            "part": ch["part"],
            "partName": ch["partName"],
            "image": ch["image"],
            "wordCount": ch["wordCount"],
            "paragraphs": ch["paragraphs"],
        })
    write_json(
        os.path.join(WEB_DATA, "books", "baeesween-sadi", "chapters.json"),
        {"chapters": baeesween_chapters_out},
    )

    # Mrinalini chapters
    mrinalini_chapters_out = []
    for ch in mrinalini_chapters:
        mrinalini_chapters_out.append({
            "id": ch["id"],
            "number": ch["number"],
            "title": ch["title"],
            "part": ch["part"],
            "partName": ch["partName"],
            "image": ch["image"],
            "wordCount": ch["wordCount"],
            "paragraphs": ch["paragraphs"],
        })
    write_json(
        os.path.join(WEB_DATA, "books", "mrinalini", "chapters.json"),
        {"chapters": mrinalini_chapters_out},
    )

    # Alaler Gharer Dulal chapters
    alaler_chapters_out = []
    for ch in alaler_chapters:
        alaler_chapters_out.append({
            "id": ch["id"],
            "number": ch["number"],
            "title": ch["title"],
            "part": ch["part"],
            "partName": ch["partName"],
            "image": ch["image"],
            "wordCount": ch["wordCount"],
            "paragraphs": ch["paragraphs"],
        })
    write_json(
        os.path.join(WEB_DATA, "books", "alaler-gharer-dulal", "chapters.json"),
        {"chapters": alaler_chapters_out},
    )

    # 6. Write meta.json for each book
    baeesween_meta = {
        "id": "baeesween-sadi",
        "title": "The Twenty-Second Century",
        "subtitle": "A Vision of the Future",
        "authorId": "rahul-sankrityayan",
        "coverImage": "/data/images/covers/baeesween-sadi.png",
        "accentColor": "#0066FF",
        "genre": ["Science Fiction", "Utopian Fiction"],
        "originalLanguage": "Hindi",
        "originalTitle": "Baeesween Sadi",
        "originalYear": 1924,
        "totalChapters": len(baeesween_chapters),
        "wordCount": baeesween_total_words,
        "summary": book_summaries.get("baeesween-sadi", ""),
        "previewText": get_preview_text(baeesween_chapters),
    }
    write_json(
        os.path.join(WEB_DATA, "books", "baeesween-sadi", "meta.json"),
        baeesween_meta,
    )

    mrinalini_meta = {
        "id": "mrinalini",
        "title": "Mrinalini",
        "subtitle": "A Historical Romance of 13th Century Bengal",
        "authorId": "bankim-chandra-chattopadhyay",
        "coverImage": "/data/images/covers/mrinalini.png",
        "accentColor": "#8B0000",
        "genre": ["Historical Fiction", "Romance"],
        "originalLanguage": "Bengali",
        "originalTitle": "Mrinalini",
        "originalYear": 1882,
        "totalChapters": len(mrinalini_chapters),
        "wordCount": mrinalini_total_words,
        "summary": book_summaries.get("mrinalini", ""),
        "previewText": get_preview_text(mrinalini_chapters),
    }
    write_json(
        os.path.join(WEB_DATA, "books", "mrinalini", "meta.json"),
        mrinalini_meta,
    )

    alaler_meta = {
        "id": "alaler-gharer-dulal",
        "title": "The Spoilt Child",
        "subtitle": "A Satire of Colonial Calcutta",
        "authorId": "peary-chand-mitra",
        "coverImage": "/data/images/covers/alaler-gharer-dulal.png",
        "accentColor": "#1B3A5C",
        "genre": ["Social Satire", "Domestic Fiction"],
        "originalLanguage": "Bengali",
        "originalTitle": "Alaler Gharer Dulal",
        "originalYear": 1858,
        "totalChapters": len(alaler_chapters),
        "wordCount": alaler_total_words,
        "summary": book_summaries.get("alaler-gharer-dulal", ""),
        "previewText": get_preview_text(alaler_chapters),
    }
    write_json(
        os.path.join(WEB_DATA, "books", "alaler-gharer-dulal", "meta.json"),
        alaler_meta,
    )

    # 7. Write catalog.json
    catalog = {
        "books": [
            {
                "id": baeesween_meta["id"],
                "title": baeesween_meta["title"],
                "subtitle": baeesween_meta["subtitle"],
                "authorId": baeesween_meta["authorId"],
                "coverImage": baeesween_meta["coverImage"],
                "accentColor": baeesween_meta["accentColor"],
                "genre": baeesween_meta["genre"],
                "originalLanguage": baeesween_meta["originalLanguage"],
                "originalTitle": baeesween_meta["originalTitle"],
                "originalYear": baeesween_meta["originalYear"],
                "totalChapters": baeesween_meta["totalChapters"],
                "wordCount": baeesween_meta["wordCount"],
                "summary": baeesween_meta["summary"],
                "previewText": baeesween_meta["previewText"],
            },
            {
                "id": mrinalini_meta["id"],
                "title": mrinalini_meta["title"],
                "subtitle": mrinalini_meta["subtitle"],
                "authorId": mrinalini_meta["authorId"],
                "coverImage": mrinalini_meta["coverImage"],
                "accentColor": mrinalini_meta["accentColor"],
                "genre": mrinalini_meta["genre"],
                "originalLanguage": mrinalini_meta["originalLanguage"],
                "originalTitle": mrinalini_meta["originalTitle"],
                "originalYear": mrinalini_meta["originalYear"],
                "totalChapters": mrinalini_meta["totalChapters"],
                "wordCount": mrinalini_meta["wordCount"],
                "summary": mrinalini_meta["summary"],
                "previewText": mrinalini_meta["previewText"],
            },
            {
                "id": alaler_meta["id"],
                "title": alaler_meta["title"],
                "subtitle": alaler_meta["subtitle"],
                "authorId": alaler_meta["authorId"],
                "coverImage": alaler_meta["coverImage"],
                "accentColor": alaler_meta["accentColor"],
                "genre": alaler_meta["genre"],
                "originalLanguage": alaler_meta["originalLanguage"],
                "originalTitle": alaler_meta["originalTitle"],
                "originalYear": alaler_meta["originalYear"],
                "totalChapters": alaler_meta["totalChapters"],
                "wordCount": alaler_meta["wordCount"],
                "summary": alaler_meta["summary"],
                "previewText": alaler_meta["previewText"],
            },
        ],
        "authors": [
            {
                "id": "rahul-sankrityayan",
                "name": "Rahul Sankrityayan",
                "image": "/data/images/authors/rahul-sankrityayan.png",
                "years": "1893\u20131963",
                "bio": author_bios.get("rahul-sankrityayan", ""),
                "bookIds": ["baeesween-sadi"],
            },
            {
                "id": "bankim-chandra-chattopadhyay",
                "name": "Bankim Chandra Chattopadhyay",
                "image": "/data/images/authors/bankim-chandra-chattopadhyay.png",
                "years": "1838\u20131894",
                "bio": author_bios.get("bankim-chandra-chattopadhyay", ""),
                "bookIds": ["mrinalini"],
            },
            {
                "id": "peary-chand-mitra",
                "name": "Peary Chand Mitra",
                "image": "/data/images/authors/peary-chand-mitra.png",
                "years": "1814\u20131882",
                "bio": author_bios.get("peary-chand-mitra", ""),
                "bookIds": ["alaler-gharer-dulal"],
            },
        ],
    }
    write_json(os.path.join(WEB_DATA, "catalog.json"), catalog)

    # Summary
    print(f"\n=== Done ===")
    print(f"Baeesween Sadi: {len(baeesween_chapters)} chapters, {baeesween_total_words:,} words")
    print(f"Mrinalini: {len(mrinalini_chapters)} chapters, {mrinalini_total_words:,} words")
    print(f"Alaler Gharer Dulal: {len(alaler_chapters)} chapters, {alaler_total_words:,} words")


if __name__ == "__main__":
    main()
