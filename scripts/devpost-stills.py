"""Devpost gallery stills: app captures with a subtitle burned in, at Devpost's 3:2 ratio.

Captions follow the pitch narration and the copy law (documentation completeness, never approval odds).
Usage: python3 scripts/devpost-stills.py [out_dir]   (default outputs/devpost)
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SRC = Path("video/public/app")
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "outputs/devpost")
W, H = 2400, 1600
SHOT_W, SHOT_TOP = 2080, 40
BG, FG, TAG = "#141414", "#f5f1e8", "#9a9486"
FONT = ImageFont.truetype("/System/Library/Fonts/Supplemental/Georgia.ttf", 54)
TAG_FONT = ImageFont.truetype("/System/Library/Fonts/Supplemental/Georgia Italic.ttf", 30)

STILLS = [
    ("20-board-hero", "Every CDCP request in the clinic on one board, sorted by who acts next."),
    ("04-case-teresa-requirements", "Teresa's chart, checked against every requirement in CDCP's guide while she's still in the chair."),
    ("05-case-teresa-fix-plan", "Her x-ray of #46 is 34 months old. Fixes are ranked by how much each lowers the risk of a denial."),
    ("07-board-chair-closed", "Two captures before Teresa reaches the door. Nothing left to take."),
    ("09-dentist-review", "One call belongs to the dentist. Laya pre-filled the rest from the chart, each with a pointer to it."),
    ("11-packet-review", "Ophi assembles the request. The dentist reviews and signs."),
    ("13-send-to-sun-life", "Staff send it from the practice software they already use. Ophi never sends anything."),
    ("16-book-the-crown", "Sun Life's answer comes back in. Next task: book the crown before the approval expires."),
    ("18-denied-marchand", "Denied? Ophi shows what the denial points to and the deadline for the one reconsideration."),
    ("19-results", "7 missing or out-of-date documents caught before they reached Sun Life, 2 while the patient was still in the chair."),
]


def wrap(draw, text, width):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=FONT) <= width:
            line = trial
        else:
            lines.append(line)
            line = word
    return lines + [line]


def still(name, caption):
    canvas = Image.new("RGB", (W, H), BG)
    shot = Image.open(SRC / f"{name}.png").convert("RGB")
    shot = shot.resize((SHOT_W, round(SHOT_W * shot.height / shot.width)), Image.LANCZOS)
    x = (W - SHOT_W) // 2
    canvas.paste(shot, (x, SHOT_TOP))
    draw = ImageDraw.Draw(canvas)
    band_top = SHOT_TOP + shot.height
    lines = wrap(draw, caption, SHOT_W)
    line_h = 70
    y = band_top + (H - band_top - line_h * len(lines)) // 2 - 10
    for line in lines:
        draw.text((W // 2, y), line, font=FONT, fill=FG, anchor="mt")
        y += line_h
    draw.text((W - x, H - 24), "Demo data · fictional patients", font=TAG_FONT, fill=TAG, anchor="rb")
    return canvas


OUT.mkdir(parents=True, exist_ok=True)
md = ["# Devpost gallery captions\n"]
for i, (name, caption) in enumerate(STILLS, 1):
    path = OUT / f"{i:02d}-{name}.jpg"
    still(name, caption).save(path, quality=90)
    md.append(f"{i:02d}. `{path.name}` — {caption}")
(OUT / "captions.md").write_text("\n".join(md) + "\n")
print(f"{len(STILLS)} stills -> {OUT}")
