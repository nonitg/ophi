#!/usr/bin/env python3
"""Verify Ophi's local waitlist, information panels, and 3D controls without storing a contact."""
import sys
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else ".impeccable/review")
if urlparse(BASE).hostname not in {"localhost", "127.0.0.1", "::1"}:
    raise SystemExit("Form-state checks are restricted to a local preview.")
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(args=["--enable-webgl", "--use-angle=swiftshader"])
    page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_selector('.tooth-viewer[data-ready="true"]')
    assert page.locator('link[rel="canonical"]').get_attribute("href").rstrip("/") == "https://ophi.app"
    assert "Colombus" not in page.inner_text("body")

    canvas = page.locator(".tooth-canvas canvas")
    before = canvas.screenshot()
    box = canvas.bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] / 2 + 120, box["y"] + box["height"] / 2, steps=6)
    page.mouse.up()
    page.wait_for_timeout(100)
    assert canvas.screenshot() != before, "Dragging should rotate the rendered sculpture"
    xray = page.get_by_role("button", name="X-ray")
    before = canvas.screenshot()
    xray.click()
    assert xray.get_attribute("aria-pressed") == "true"
    page.wait_for_timeout(100)
    assert canvas.screenshot() != before, "X-ray should change the rendered sculpture"
    page.screenshot(path=str(OUT / "xray.png"))
    page.locator(".tooth-canvas").focus()
    before = canvas.screenshot()
    page.keyboard.press("ArrowLeft")
    page.wait_for_timeout(100)
    assert canvas.screenshot() != before, "Keyboard rotation should change the sculpture"
    page.keyboard.press("Home")
    xray.click()
    assert xray.get_attribute("aria-pressed") == "false"
    print("3D: drag rotation, keyboard rotation, X-ray and reset passed")

    why = page.get_by_role("button", name="Why Ophi?")
    why.click()
    assert page.locator(".why-panel").is_visible()
    page.get_by_role("button", name="Close", exact=True).focus()
    page.keyboard.press("Tab")
    assert page.evaluate("!!document.activeElement.closest('dialog')"), "Modal focus must remain inside"
    page.locator("#email").evaluate("el => el.focus()")
    assert page.evaluate("!!document.activeElement.closest('dialog')"), "Background controls must be inert"
    page.screenshot(path=str(OUT / "why.png"))
    page.keyboard.press("Escape")
    assert not page.locator(".why-panel").is_visible()
    assert why.evaluate("el => document.activeElement === el"), "Closing should restore trigger focus"
    page.get_by_role("button", name="Your email & privacy").click()
    assert page.locator(".privacy-panel").is_visible()
    page.mouse.click(8, 8)
    assert not page.locator(".privacy-panel").is_visible()
    print("Panels: open, modal focus, Escape, backdrop and focus restoration passed")

    page.locator("#email").fill("invalid")
    page.locator("button[type=submit]").click()
    page.wait_for_selector("#email-error")
    assert page.locator("#email").get_attribute("aria-invalid") == "true"
    assert page.locator("#email").input_value() == "invalid", "Validation must preserve input"
    page.locator(".signup").screenshot(path=str(OUT / "error.png"))
    page.locator("#pms").click()
    page.get_by_role("option", name="ClearDent").click()
    assert page.locator("input[name=pms]").input_value() == "ClearDent"
    page.fill("#email", "ophi-review@example.com")
    # The existing no-write bot branch tests success rendering without creating a real contact.
    page.locator("#hp_ref").evaluate('(el) => { el.value = "automated-ui-review"; }')
    page.locator("button[type=submit]").click()
    page.wait_for_selector(".waitlist-success")
    page.locator(".signup").screenshot(path=str(OUT / "success.png"))
    assert "You’re on the list." in page.locator(".waitlist-success").inner_text()
    print("Signup: validation, preserved input, optional software and no-write success UI passed")
    assert not errors, errors
    print("No page errors")
    browser.close()
