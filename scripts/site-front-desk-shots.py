#!/usr/bin/env python3
"""Screens of the front-desk section (desktop, tablet, phone), the hero's Priya and Owen turns, and the clinic view.
Writes PNGs to outputs/front-desk/.

usage: site-front-desk-shots.py [BASE] [--quick]   (--quick skips waiting for the hero's later patients)
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

args = [a for a in sys.argv[1:] if not a.startswith("--")]
BASE = args[0] if args else "http://localhost:3111"
OUT = Path(__file__).resolve().parent.parent / "outputs" / "front-desk"
OUT.mkdir(parents=True, exist_ok=True)
SIZES = {"desktop": (1440, 900), "tablet": (900, 1100), "phone": (390, 844)}


def shoot(page, selector, name):
    page.evaluate(f"document.querySelector('{selector}').scrollIntoView()")
    page.wait_for_timeout(2500)
    page.screenshot(path=str(OUT / f"{name}.png"))


with sync_playwright() as p:
    browser = p.chromium.launch(args=["--mute-audio"])
    for size, (w, h) in SIZES.items():
        page = browser.new_page(viewport={"width": w, "height": h})
        page.goto(BASE, wait_until="networkidle")
        page.wait_for_timeout(1200)
        page.screenshot(path=str(OUT / f"{size}-hero.png"))
        shoot(page, "#desk", f"{size}-desk")
        shoot(page, "#clinic", f"{size}-clinic")
        page.close()
    if "--quick" not in sys.argv:
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(BASE, wait_until="networkidle")
        for who in ["Priya"]:
            page.wait_for_function(f"document.body.innerText.includes('{who}’s care')", timeout=60000)
            page.wait_for_timeout(7000)
            page.screenshot(path=str(OUT / f"desktop-hero-{who.lower()}.png"))
    browser.close()
print("shots in", OUT)
