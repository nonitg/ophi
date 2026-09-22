#!/usr/bin/env python3
"""Capture Ophi's X-ray mode for visual review: paper and film on desktop and phone, the panoramic sweep
mid-flight, the film-in-backwards and ALARA notes, and the dialogs and listbox on film.

Usage: site-xray.py [base_url] [out_dir]
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "outputs/site-xray")
OUT.mkdir(parents=True, exist_ok=True)
SIZES = {"desktop": {"width": 1440, "height": 900}, "phone": {"width": 390, "height": 844}, "small": {"width": 320, "height": 640}, "tablet": {"width": 1024, "height": 768}}
SWEEP_MS = 950  # must match site/lib/xray-mode.ts


def open_page(browser, size, motion="reduce"):
    page = browser.new_page(viewport=SIZES[size], reduced_motion=motion)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_selector('.tooth-viewer[data-ready="true"]')
    page.wait_for_timeout(300)
    return page, errors


def shot(page, name, **kwargs):
    page.screenshot(path=str(OUT / f"{name}.png"), **kwargs)


def xray(page):
    return page.get_by_role("button", name="X-ray")


def note(page):
    return page.locator(".xray-note").inner_text()


with sync_playwright() as p:
    browser = p.chromium.launch(args=["--enable-webgl", "--use-angle=swiftshader"])
    for size in SIZES:
        page, errors = open_page(browser, size)
        shot(page, f"{size}-paper")
        xray(page).click()
        assert page.evaluate("document.documentElement.hasAttribute('data-xray')"), "X-ray should reach the whole page"
        page.wait_for_timeout(700)
        shot(page, f"{size}-xray")
        shot(page, f"{size}-xray-full", full_page=True)

        # Turning the tooth's back to the viewer: the film reads as loaded back to front.
        page.locator(".tooth-canvas").focus()
        for _ in range(10):
            page.keyboard.press("ArrowRight")
        page.wait_for_timeout(600)
        assert page.evaluate("document.documentElement.hasAttribute('data-film-reversed')")
        assert "backwards" in note(page), note(page)
        page.evaluate("scrollTo(0, 0)")
        shot(page, f"{size}-backwards")
        page.keyboard.press("Home")
        page.wait_for_timeout(300)
        assert not page.evaluate("document.documentElement.hasAttribute('data-film-reversed')")
        assert note(page) == "", note(page)

        # A burst of five exposures earns the ALARA reminder; turning X-ray off clears it.
        for _ in range(4):
            xray(page).click()
            xray(page).click()
        assert "reasonably achievable" in note(page), note(page)
        page.evaluate("scrollTo(0, 0)")
        shot(page, f"{size}-alara")
        xray(page).click()
        assert note(page) == "" and not page.evaluate("document.documentElement.hasAttribute('data-xray')")
        xray(page).click()

        page.get_by_role("button", name="Why Ophi?").click()
        page.wait_for_timeout(300)
        shot(page, f"{size}-why")
        page.keyboard.press("Escape")
        page.locator("#pms").click()
        page.wait_for_timeout(400)
        page.locator(".signup").scroll_into_view_if_needed()
        shot(page, f"{size}-menu")
        page.keyboard.press("Escape")
        assert not errors, errors
        page.close()

    # The sweep itself, frozen part-way across the page.
    page, errors = open_page(browser, "desktop", motion="no-preference")
    xray(page).click()
    page.wait_for_function("document.getAnimations().some(a => a.effect && a.effect.pseudoElement === '::view-transition-new(root)')")
    for fraction in (.35, .7):
        page.evaluate(f"document.getAnimations().forEach(a => {{ a.pause(); a.currentTime = {SWEEP_MS * fraction}; }})")
        page.wait_for_timeout(150)
        shot(page, f"desktop-sweep-{int(fraction * 100)}")
    page.evaluate("document.getAnimations().forEach(a => a.finish())")
    page.wait_for_timeout(500)
    assert not page.evaluate("document.documentElement.hasAttribute('data-sweep')"), "Sweep state should clear"
    assert page.locator(".xray-beam").count() == 0, "Beam should be removed after the sweep"
    # Rapid presses interrupt the sweep; the page must still land in the state the button shows.
    for _ in range(3):
        xray(page).click()
        page.wait_for_timeout(120)
    page.wait_for_timeout(1500)
    pressed = xray(page).get_attribute("aria-pressed") == "true"
    assert pressed == page.evaluate("document.documentElement.hasAttribute('data-xray')"), "Page and button disagree"
    assert not page.evaluate("document.documentElement.hasAttribute('data-sweep')") and page.locator(".xray-beam").count() == 0
    # Two presses inside one frame, before the first transition has swapped the page, must cancel out.
    before = page.evaluate("document.documentElement.hasAttribute('data-xray')")
    page.evaluate("() => { const b = [...document.querySelectorAll('button')].find(e => e.textContent === 'X-ray'); b.click(); b.click(); }")
    page.wait_for_timeout(1500)
    assert page.evaluate("document.documentElement.hasAttribute('data-xray')") == before, "A same-frame double press was dropped"
    assert (xray(page).get_attribute("aria-pressed") == "true") == before
    assert not errors, errors
    print(f"All X-ray checks passed; screens in {OUT}")
    browser.close()
