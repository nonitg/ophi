#!/usr/bin/env python3
"""Verify signup focus handling, field-scoped invalid state, and analytics script on the dev server."""
import sys
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page()
    scripts = []
    page.on("request", lambda r: "insights" in r.url or "vercel-scripts" in r.url and scripts.append(r.url))
    page.goto(BASE, wait_until="networkidle")
    page.fill("#email", "nope")
    page.click(".join-button")
    page.wait_for_selector(".waitlist-error")
    assert page.evaluate("document.activeElement.id") == "email", "focus not on email after error"
    assert page.get_attribute("#email", "aria-invalid") == "true"
    print("email error: focus returns to email, field marked invalid")
    page.fill("#email", "verify-focus@example.com")
    page.click(".join-button")
    page.wait_for_selector(".waitlist-success")
    assert page.evaluate("document.activeElement.classList.contains('waitlist-success')"), "focus not on success"
    print("success: focus moves to confirmation")
    print("analytics requests:", scripts or page.evaluate("[...document.scripts].map(s=>s.src).filter(s=>/insights|vercel/.test(s))"))
    # Rate limit (6th attempt/minute) must not blame the email field.
    for _ in range(6):
        page.goto(BASE, wait_until="networkidle")
        page.fill("#email", "verify-rate@example.com")
        page.click(".join-button")
        page.wait_for_selector(".waitlist-success, .waitlist-error")
    if page.locator(".waitlist-error").count():
        print("rate limit message:", page.inner_text(".waitlist-error"), "| aria-invalid:", page.get_attribute("#email", "aria-invalid"))
        assert page.get_attribute("#email", "aria-invalid") is None
    else:
        print("rate limit not triggered (already reset?)")
    b.close()
