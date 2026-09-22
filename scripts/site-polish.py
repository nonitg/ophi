#!/usr/bin/env python3
"""Capture the pill controls and the custom software listbox (mouse and keyboard) at desktop and mobile."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else ".impeccable/review")
OUT.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(args=["--enable-webgl", "--use-angle=swiftshader"])
    for name, (w, h) in {"desktop": (1440, 900), "mobile": (390, 844)}.items():
        page = browser.new_page(viewport={"width": w, "height": h})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(BASE, wait_until="networkidle")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"Overflow at {w}px"
        page.locator(".entry-row").screenshot(path=str(OUT / f"polish-entry-{name}.png"))
        page.locator("#pms").scroll_into_view_if_needed()
        page.locator("#pms").click()
        page.wait_for_timeout(400)
        assert page.locator("#pms").get_attribute("aria-expanded") == "true"
        page.screenshot(path=str(OUT / f"polish-menu-{name}.png"))
        page.get_by_role("option", name="Dentrix").click()
        assert page.locator("input[name=pms]").input_value() == "Dentrix"
        assert page.locator("#pms").get_attribute("aria-expanded") == "false"
        # Keyboard: open, typeahead, commit, reopen, Escape.
        page.locator("#pms").focus()
        page.keyboard.press("ArrowDown")
        page.keyboard.type("op")
        page.keyboard.press("Enter")
        assert page.locator("input[name=pms]").input_value() == "Open Dental"
        page.keyboard.press("ArrowDown")
        page.keyboard.press("Escape")
        assert page.locator("#pms").get_attribute("aria-expanded") == "false"
        page.locator(".signup").screenshot(path=str(OUT / f"polish-focus-{name}.png"))
        # Outside click closes.
        page.locator("#pms").click()
        page.mouse.click(5, 5)
        page.wait_for_timeout(400)
        assert page.locator("#pms").get_attribute("aria-expanded") == "false"
        page.locator(".site-footer").screenshot(path=str(OUT / f"polish-footer-{name}.png"))
        page.locator(".why-button").click()
        page.wait_for_timeout(300)
        page.locator(".why-panel").screenshot(path=str(OUT / f"polish-why-{name}.png"))
        assert not errors, errors
        print(f"{name}: pills and listbox (mouse, keyboard, outside click) passed")
        page.close()
    browser.close()
