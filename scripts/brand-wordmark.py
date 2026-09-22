#!/usr/bin/env python3
"""Outline the Ophi wordmark into font-free SVGs in assets/logo/.

Matches the site header: DM Sans 650, letter-spacing -3.7px at 46px, orange period.
Needs fonttools, brotli and uharfbuzz (not project deps):
  python3 -m venv /tmp/fontenv && /tmp/fontenv/bin/pip install fonttools brotli uharfbuzz
  /tmp/fontenv/bin/python scripts/brand-wordmark.py
"""
import io
import math
import re
import subprocess
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets/logo"
FONT_CSS = "https://fonts.googleapis.com/css2?family=DM+Sans:wght@100..1000"
CHROME_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
WEIGHT = 650
TRACKING_EM = -3.7 / 46
INKS = {"ophi-wordmark": ("#193a30", "#d96335"), "ophi-wordmark-ivory": ("#f4f2e9", "#ef865b")}


def fetch(url: str) -> bytes:
    # curl, not urllib: python.org builds on macOS ship without system CA certs.
    return subprocess.run(["curl", "-sfL", "-A", CHROME_UA, url], check=True, capture_output=True).stdout


def latin_font() -> TTFont:
    """The same variable DM Sans latin subset that next/font serves the site."""
    css = fetch(FONT_CSS).decode()
    url = re.findall(r"/\* latin \*/.*?url\((\S+?)\)", css, re.S)[-1]
    return TTFont(io.BytesIO(fetch(url)))


def outline(font: TTFont, text: str) -> tuple[list[tuple[str, str]], tuple]:
    """Shape text at WEIGHT; return (char, svg path) pairs in font units (y down) and their ink bounds."""
    buf = io.BytesIO()
    font.flavor = None
    font.save(buf)
    hb_font = hb.Font(hb.Face(buf.getvalue()))
    hb_font.set_variations({"wght": WEIGHT})
    shaped = hb.Buffer()
    shaped.add_str(text)
    shaped.guess_segment_properties()
    hb.shape(hb_font, shaped, {"liga": False})
    tracking = TRACKING_EM * font["head"].unitsPerEm
    glyphs = font.getGlyphSet(location={"wght": WEIGHT})
    order = font.getGlyphOrder()
    ink = BoundsPen(glyphs)
    x, paths = 0.0, []
    for char, info, pos in zip(text, shaped.glyph_infos, shaped.glyph_positions):
        place = (1, 0, 0, -1, x + pos.x_offset, 0)
        pen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.1f}".removesuffix(".0"))
        glyphs[order[info.codepoint]].draw(TransformPen(pen, place))
        glyphs[order[info.codepoint]].draw(TransformPen(ink, place))
        paths.append((char, pen.getCommands()))
        x += pos.x_advance + tracking
    return paths, ink.bounds


def main() -> None:
    font = latin_font()
    paths, (x0, y0, x1, y1) = outline(font, "ophi.")
    x0, y0, x1, y1 = math.floor(x0), math.floor(y0), math.ceil(x1), math.ceil(y1)
    view = f"{x0} {y0} {x1 - x0} {y1 - y0}"
    word = "".join(d for c, d in paths if c != ".")
    dot = "".join(d for c, d in paths if c == ".")
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (ink, accent) in INKS.items():
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view}" role="img" aria-label="Ophi">'
               f'<path fill="{ink}" d="{word}"/><path fill="{accent}" d="{dot}"/></svg>\n')
        (OUT / f"{name}.svg").write_text(svg)
        print(OUT / f"{name}.svg")


if __name__ == "__main__":
    main()
