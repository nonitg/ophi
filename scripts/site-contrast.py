#!/usr/bin/env python3
"""WCAG contrast of the site's text colours on paper, lit and under the window-light shade (plain alpha over)."""
import sys

PAPER = "#f4f2e9"
SHADE, DEPTH = "#232a2e", .1   # must match site/scripts/build-room.mjs
GRAIN = .025                  # mean darkening by the paper grain tile, measured from screenshots
TEXTS = sys.argv[1:] or ["#626b5d", "#5c6557", "#53604d", "#193a30"]


def rgb(hex_):
    return [int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5)]


def over(colour, top, alpha):
    return [c * (1 - alpha) + t * alpha for c, t in zip(colour, top)]


def luminance(colour):
    lin = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in colour]
    return .2126 * lin[0] + .7152 * lin[1] + .0722 * lin[2]


def contrast(a, b):
    la, lb = sorted([luminance(a), luminance(b)], reverse=True)
    return (la + .05) / (lb + .05)


lit = over(rgb(PAPER), [0, 0, 0], GRAIN)
for text in TEXTS:
    shaded_text = over(rgb(text), rgb(SHADE), DEPTH)
    shaded_paper = over(lit, rgb(SHADE), DEPTH)
    print(f"{text}: lit {contrast(rgb(text), lit):.2f}:1, deepest shade {contrast(shaded_text, shaded_paper):.2f}:1")

# X-ray mode (site/app/xray.css): pale type on film, backlit by the lightbox glow behind the content.
FILM = "#0e1f19"
GLOW, GLOW_DEPTH = "#9fd3b9", .1       # brightest point of the lightbox glow
SOFT, SOFT_DEPTH = "#e6ece3", .06      # the signup band, a soft-tissue shadow
XRAY_TEXTS = ["#e6ece3", "#c3cfc4", "#9fb0a3", "#f2a58a"]
film_dark = rgb(FILM)
film_lit = over(film_dark, rgb(GLOW), GLOW_DEPTH)
band_lit = over(film_lit, rgb(SOFT), SOFT_DEPTH)
print("X-ray mode")
for text in XRAY_TEXTS:
    worst = min(contrast(rgb(text), bg) for bg in (film_dark, film_lit, band_lit))
    print(f"{text}: film {contrast(rgb(text), film_dark):.2f}:1, lit band {contrast(rgb(text), band_lit):.2f}:1, worst {worst:.2f}:1")
print(f"join button #0e1f19 on #f4f8f1: {contrast(rgb('#0e1f19'), rgb('#f4f8f1')):.2f}:1")
print(f"focus ring #a9c0b1 on lit band: {contrast(rgb('#a9c0b1'), band_lit):.2f}:1")
