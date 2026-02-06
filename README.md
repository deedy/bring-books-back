# Bring Books Back

A pipeline that takes old Hindi books (scanned PDFs), OCRs them, translates them to English, generates chapter illustrations, and typesets a beautiful PDF — all using AI.

![Chapter 1](chapter_images/chapter_1.png)

## The Book

**Baeesween Sadi** (The Twenty-Second Century) by **Rahul Sankrityayan** (1924) — one of the earliest science fiction novels written in Hindi. The narrator, a sage who has slept for centuries in a Himalayan cave, wakes up in the 22nd century to find a radically transformed India: a classless society, universal education, democratic governance, electric trains threading through the mountains, and the abolition of caste, religion, and poverty.

The original book exists only as a scanned Hindi PDF. This project brings it back to life as a typeset English book with illustrated chapter openers.

## Pipeline

```
PDF (Hindi) ──► OCR (Sarvam AI) ──► Translation (GPT-4.1) ──► Illustrations (Gemini 3 Pro) ──► Typeset PDF (ReportLab)
```

### Step 1: OCR with Sarvam AI

```bash
python ocr_all_pages.py
```

Extracts each page of the source PDF as an image, sends it to [Sarvam AI's](https://sarvam.ai) vision OCR endpoint, and saves the Hindi text. Checkpointed — safe to interrupt and resume.

### Step 2: Translate with GPT-4.1

```bash
python translate.py
```

Translates the OCR'd Hindi text to English, page by page, preserving structure. Checkpointed.

### Step 3: Generate chapter illustrations with Gemini

```bash
python generate_chapter_images.py
```

Generates 16 chapter illustrations using Gemini 3 Pro's image generation. All images share a consistent aesthetic: **vintage Indian woodblock print** with monochromatic sepia tones and a single deep saffron accent. Checkpointed.

### Step 4: Typeset the final PDF

```bash
python generate_pdf.py
```

Produces an A5 book PDF with:
- **Source Serif 4** for body text (readable serif)
- **Inter Display** for headings (neo-grotesque sans)
- Full-page chapter illustrations with overlaid titles
- Title page, table of contents, preface, and colophon
- Clean running page numbers

## Setup

```bash
uv venv && uv pip install pymupdf requests openai tiktoken google-genai Pillow reportlab python-dotenv
cp .env.example .env
# Fill in your API keys in .env
```

Place your source PDF at `data/baeesweensadi.pdf`, then run the steps in order.

## Output

The final typeset book is generated at `data/baeesweensadi_book.pdf` (~170 pages, 16 illustrated chapters).

## Credits

- **OCR**: [Sarvam AI](https://sarvam.ai) Vision API
- **Translation**: OpenAI GPT-4.1
- **Illustrations**: Google Gemini 3 Pro (image generation)
- **Typography**: [Source Serif 4](https://github.com/adobe-fonts/source-serif) (Adobe) & [Inter](https://rsms.me/inter/) (Rasmus Andersson)
- **Typesetting**: [ReportLab](https://www.reportlab.com/)
