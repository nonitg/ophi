#!/usr/bin/env python3
"""Tile stills into labelled contact sheets. Usage: scripts/video-sheet.py out.png cols width img1 img2 ..."""
import sys
from PIL import Image, ImageDraw
out, cols, width, *imgs = sys.argv[1:]
cols, width = int(cols), int(width)
ims = [Image.open(p).convert("RGB") for p in imgs]
h = int(width * ims[0].height / ims[0].width)
rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (cols * width, rows * (h + 24)), "white")
d = ImageDraw.Draw(sheet)
for i, (p, im) in enumerate(zip(imgs, ims)):
    x, y = (i % cols) * width, (i // cols) * (h + 24)
    sheet.paste(im.resize((width, h)), (x, y + 24))
    d.text((x + 6, y + 6), p.rsplit("/", 1)[-1], fill="black")
sheet.save(out)
