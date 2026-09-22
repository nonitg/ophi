#!/usr/bin/env python3
"""Check the phone layout's moved and relabelled controls: names, tap size, focus order, prompts, X-ray band.

Usage: site-mobile-a11y.py [base_url]
"""
import sys
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
FOCUSED = "() => { const el = document.activeElement; return el.getAttribute('aria-label') || el.textContent.trim(); }"


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {label}{f'  ({detail})' if detail else ''}")
    if not ok:
        check.failed = True


check.failed = False
with sync_playwright() as p:
    browser = p.chromium.launch(args=["--enable-webgl", "--use-angle=swiftshader"])
    for width, height, phone in [(393, 852, True), (1440, 900, False)]:
        page = browser.new_page(viewport={"width": width, "height": height}, reduced_motion="reduce", has_touch=phone, is_mobile=phone)
        page.goto(BASE, wait_until="networkidle")
        page.wait_for_selector('.tooth-viewer[data-ready="true"]', timeout=30000)
        tag = f"{width}px:"

        top = page.get_by_role("link", name="Back to the top")
        box = top.bounding_box()
        # Phones show it as a 40px round button; wide screens keep the labelled 38px pill.
        big_enough = box["width"] >= 40 and box["height"] >= 40 if phone else box["height"] >= 38
        check(f"{tag} back-to-top keeps its name and its target size", top.is_visible() and big_enough, f"{box['width']:.0f}x{box['height']:.0f}")

        # Focus moves from the last question to the contact: the order on screen on phones; on wide screens
        # it steps back left to the contact under the heading.
        page.locator(".faq-items summary").last.focus()
        page.keyboard.press("Tab")
        check(f"{tag} Tab from last question reaches the contact copy button", page.evaluate(FOCUSED).startswith("Copy email address"), page.evaluate(FOCUSED))

        prompt = page.locator(".pms-trigger > span").inner_text()
        want = "Your clinic’s software (optional)" if phone else "At a clinic? Tell us your software (optional)"
        check(f"{tag} clinic-software prompt", prompt == want, prompt)

        if phone:
            tag_bg = page.evaluate("getComputedStyle(document.querySelector('.why-button .pill-tag')).backgroundColor")
            band_bg = page.evaluate("getComputedStyle(document.querySelector('.entry-row')).backgroundColor")
            check(f"{tag} Why Ophi? on paper keeps its sage tag; band background moved to the signup", tag_bg == "rgb(228, 231, 217)" and band_bg == "rgba(0, 0, 0, 0)", f"tag {tag_bg}, row {band_bg}")
            page.click(".view-mode")
            page.wait_for_selector(":root[data-xray]")
            film = page.evaluate("getComputedStyle(document.querySelector('.signup')).backgroundColor")
            check(f"{tag} X-ray turns the signup band to soft tissue", film.startswith("rgba(230, 236, 227"), film)
        page.close()
    browser.close()
sys.exit(1 if check.failed else 0)
