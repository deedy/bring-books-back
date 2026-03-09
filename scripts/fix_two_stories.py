"""Fix chapter detection for The Submerged Peak and The Death of Amrito.

Uses full paragraph text, two-pass for Submerged Peak (long story).
"""

import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

WEB = "web/public/data/books"


def get_paras(sid):
    with open(f"{WEB}/{sid}/chapters.json") as f:
        data = json.load(f)
    paras = []
    for ch in data["chapters"]:
        paras.extend(ch["paragraphs"])
    return paras


def detect(paras, n_chapters, start=0, end=None):
    if end is None:
        end = len(paras)
    subset = paras[start:end]
    wc = sum(len(p.split()) for p in subset)
    target_wpc = wc // n_chapters

    lines = []
    cum = 0
    for i, p in enumerate(subset):
        pw = len(p.split())
        cum += pw
        lines.append(f"[{start + i}] {p}")

    text = "\n\n".join(lines)

    prompt = (
        f"Split this story section (paras {start}-{end - 1}, {wc} words, {len(subset)} paragraphs) "
        f"into exactly {n_chapters} chapters.\n"
        f"Target ~{target_wpc} words per chapter. Each chapter must be {max(2500, target_wpc - 1500)}-{target_wpc + 2000} words.\n"
        f"First chapter starts at para_index {start}.\n"
        f"IMPORTANT: para_index must be between {start} and {end - 1}.\n"
        f"Return ONLY JSON array: "
        '[{"para_index": N, "title": "Evocative Title 3-6 Words"}]\n\n'
        f"{text}"
    )

    response = client.chat.completions.create(
        model="openai/gpt-4.1",
        messages=[
            {"role": "system", "content": "Split stories into equal chapters. Return ONLY JSON array."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        if raw.endswith("```"):
            raw = raw[: raw.rfind("```")]
        raw = raw.strip()
    return json.loads(raw)


def print_chapters(paras, chs):
    for i, ch in enumerate(chs):
        start = ch["para_index"]
        end = chs[i + 1]["para_index"] if i + 1 < len(chs) else len(paras)
        wc = sum(len(p.split()) for p in paras[start:end])
        flag = " ***" if wc < 2500 or wc > 7000 else ""
        print(f"  Ch {i + 1}: para {start:4d}, {wc:5d}w - {ch['title']}{flag}")


# === The Death of Amrito (18553w -> 4 chapters) ===
# Single pass — fits in context
print("=== The Death of Amrito ===")
paras2 = get_paras("byomkesh-the-death-of-amrito")
print(f"  {len(paras2)} paragraphs, {sum(len(p.split()) for p in paras2)} words")
chs2 = detect(paras2, 4)
print_chapters(paras2, chs2)

# === The Submerged Peak (24531w -> 5 chapters) ===
# Two-pass: split at midpoint
print("\n=== The Submerged Peak ===")
paras = get_paras("byomkesh-the-submerged-peak")
total_w = sum(len(p.split()) for p in paras)
print(f"  {len(paras)} paragraphs, {total_w} words")

mid = len(paras) // 2
mid_w = sum(len(p.split()) for p in paras[:mid])
first_n = round(5 * mid_w / total_w)
second_n = 5 - first_n
print(f"  First half: paras 0-{mid - 1} ({mid_w}w, {first_n} chapters)")
print(f"  Second half: paras {mid}-{len(paras) - 1} ({total_w - mid_w}w, {second_n} chapters)")

chs_a = detect(paras, first_n, 0, mid)
chs_b = detect(paras, second_n, mid, len(paras))
chs = chs_a + chs_b
print_chapters(paras, chs)

# Update sub_chapters.json
with open("data/byomkesh/sub_chapters.json") as f:
    d = json.load(f)
d["byomkesh-the-submerged-peak"] = chs
d["byomkesh-the-death-of-amrito"] = chs2
with open("data/byomkesh/sub_chapters.json", "w") as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
print("\nSaved!")
