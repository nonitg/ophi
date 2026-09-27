"""Tile the captured app stills (viewport shots only) into one labelled contact sheet.

Usage: .venv/bin/python scripts/video-contact-sheet.py video/public/app
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

d = Path(sys.argv[1])
shots = sorted(p for p in d.glob("[0-9]*.png") if not p.stem.endswith("-full") and "-page-" not in p.stem)
cols, tw, th = 5, 576, 360
sheet = Image.new("RGB", (cols * tw, ((len(shots) + cols - 1) // cols) * (th + 24)), "white")
draw = ImageDraw.Draw(sheet)
for i, p in enumerate(shots):
    x, y = (i % cols) * tw, (i // cols) * (th + 24)
    sheet.paste(Image.open(p).convert("RGB").resize((tw, th), Image.LANCZOS), (x, y + 24))
    draw.text((x + 6, y + 6), p.stem, fill="black")
sheet.save(d / "contact.png")
print(f"{len(shots)} shots -> {d / 'contact.png'}")
