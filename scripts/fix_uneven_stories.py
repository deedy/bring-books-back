"""Fix uneven chapter splits for problematic stories."""

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
    return data["chapters"][0]["paragraphs"]


def detect(paras, n_chapters):
    wc = sum(len(p.split()) for p in paras)
    target_wpc = wc // n_chapters

    lines = []
    cum = 0
    for i, p in enumerate(paras):
        pw = len(p.split())
        cum += pw
        lines.append(f"[{i}] {p}")

    text = "\n\n".join(lines)

    prompt = (
        f"Split this detective story ({wc} words, {len(paras)} paragraphs) "
        f"into exactly {n_chapters} chapters.\n"
        f"Target ~{target_wpc} words per chapter. Each chapter must be "
        f"{max(2500, target_wpc - 1500)}-{target_wpc + 2000} words.\n"
        f"First chapter MUST start at para_index 0.\n"
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


def show(paras, chs):
    for i, ch in enumerate(chs):
        start = ch["para_index"]
        end = chs[i + 1]["para_index"] if i + 1 < len(chs) else len(paras)
        wc = sum(len(p.split()) for p in paras[start:end])
        flag = " ***" if wc < 2500 or wc > 7000 else ""
        print(f"  Ch {i + 1}: para {start:4d}, {wc:5d}w - {ch['title']}{flag}")


with open("data/byomkesh/sub_chapters.json") as f:
    d = json.load(f)

# 1. Annihilation of Beni (19272w -> 4 chapters, ignore the numbered markers since they're uneven)
print("=== Annihilation of Beni ===")
paras = get_paras("byomkesh-the-annihilation-of-beni")
chs = detect(paras, 4)
show(paras, chs)
d["byomkesh-the-annihilation-of-beni"] = chs

# 2. Mystery of Fortress (30894w -> 7 chapters)
print("\n=== Mystery of the Fortress ===")
paras = get_paras("byomkesh-the-mystery-of-the-fortress")
chs = detect(paras, 7)
show(paras, chs)
d["byomkesh-the-mystery-of-the-fortress"] = chs

# 3. Quills of Porcupine (36846w -> 8 chapters)
print("\n=== Quills of the Porcupine ===")
paras = get_paras("byomkesh-the-quills-of-the-porcupine")
chs = detect(paras, 8)
show(paras, chs)
d["byomkesh-the-quills-of-the-porcupine"] = chs

with open("data/byomkesh/sub_chapters.json", "w") as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
print("\nSaved!")
