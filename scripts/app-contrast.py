#!/usr/bin/env python3
"""WCAG contrast of the internal app's colour tokens, read straight from ophi/web/static/app.css.

Each pair is (text token, background token, minimum): 4.5 for body text, 3 for large text and for
non-text marks (status cells, dots). Exits 1 if any pair falls short.
"""
import re
import sys
from pathlib import Path

CSS = Path(__file__).resolve().parents[1] / "ophi" / "web" / "static" / "app.css"
PAIRS = [
    ("ink", "paper", 4.5), ("ink", "linen", 4.5), ("ink", "stone", 4.5),
    ("ink-strong", "stone", 4.5), ("muted", "paper", 4.5), ("muted", "linen", 4.5), ("muted", "stone", 4.5),
    ("ok", "paper", 4.5), ("ok", "ok-tint", 4.5), ("bad", "paper", 4.5), ("bad", "bad-tint", 4.5),
    ("ask", "paper", 4.5), ("ask", "ask-tint", 4.5), ("ask", "linen", 4.5),
    ("#ffffff", "ink", 4.5),                                    # primary buttons, signed pill
    ("faint", "paper", 3.0),                                    # zero counts, set at 30px
    ("ok", "stone", 3.0), ("bad", "stone", 3.0), ("ask", "stone", 3.0),   # strip cells on the verdict panel
    ("#ffffff", "ok", 3.0), ("#ffffff", "bad", 3.0), ("#ffffff", "ask", 3.0),  # glyphs inside cells
]


def tokens() -> dict[str, str]:
    root = re.search(r":root\s*{(.*?)}", CSS.read_text(), re.S).group(1)
    return dict(re.findall(r"--([a-z0-9-]+):\s*(#[0-9a-fA-F]{6})", root))


def luminance(hex_: str) -> float:
    c = [int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in c]
    return .2126 * lin[0] + .7152 * lin[1] + .0722 * lin[2]


def contrast(a: str, b: str) -> float:
    hi, lo = sorted([luminance(a), luminance(b)], reverse=True)
    return (hi + .05) / (lo + .05)


t = tokens()
failed = 0
for fg, bg, need in PAIRS:
    a, b = t.get(fg, fg), t.get(bg, bg)
    r = contrast(a, b)
    ok = r >= need
    failed += not ok
    print(f"{'ok  ' if ok else 'FAIL'} {fg:>10} on {bg:<8} {r:5.2f}:1 (needs {need})")
sys.exit(1 if failed else 0)
