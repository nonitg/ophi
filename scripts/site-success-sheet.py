#!/usr/bin/env python3
"""Stack the signup-column crops of each captured frame into one contact sheet per variant and view."""
import sys
from pathlib import Path
from PIL import Image

root = Path(sys.argv[1] if len(sys.argv) > 1 else "outputs/site-success")
for folder in sorted(p for p in root.iterdir() if p.is_dir()):
    for view, left in (("desktop", 0.57), ("phone", 0.0)):
        frames = sorted(folder.glob(f"{view}-motion-t*.png"))
        if not frames:
            continue
        crops = []
        for f in frames:
            im = Image.open(f)
            w, h = im.size
            top = int(h * 0.36) if view == "desktop" else int(h * 0.62)
            crops.append(im.crop((int(w * left), top, w, h)))
        sheet = Image.new("RGB", (crops[0].width, sum(c.height for c in crops) + 8 * len(crops)), "white")
        y = 0
        for c in crops:
            sheet.paste(c, (0, y))
            y += c.height + 8
        out = folder / f"sheet-{view}.png"
        sheet.save(out)
        print(out)
