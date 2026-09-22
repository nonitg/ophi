#!/usr/bin/env python3
"""List the elements that stick out past the viewport's right edge at a given width."""
import sys
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
WIDTH = int(sys.argv[2]) if len(sys.argv) > 2 else 320

with sync_playwright() as p:
    browser = p.chromium.launch(args=["--enable-webgl", "--use-angle=swiftshader"])
    page = browser.new_page(viewport={"width": WIDTH, "height": 740}, reduced_motion="reduce")
    page.goto(BASE, wait_until="networkidle")
    print("scrollWidth", page.evaluate("document.documentElement.scrollWidth"), "innerWidth", WIDTH)
    for row in page.evaluate("""() => [...document.querySelectorAll('body *')]
        .map(el => ({ el, r: el.getBoundingClientRect() }))
        .filter(({ r }) => r.right > innerWidth + .5 && r.width > 0)
        .map(({ el, r }) => `${el.tagName.toLowerCase()}.${[...el.classList].join('.')} right=${r.right.toFixed(1)} width=${r.width.toFixed(1)}`)"""):
        print(row)
    browser.close()
