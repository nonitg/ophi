#!/usr/bin/env python3
"""Capture the signup band before and after a local submit, on desktop and phone, plus frames of the transition.

Usage: site-success.py [base_url] [out_dir] [query]
Local previews only. Submits take the honeypot branch, so nothing is stored or sent.
"""
import sys
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "outputs/site-success")
QUERY = sys.argv[3] if len(sys.argv) > 3 else ""
if urlparse(BASE).hostname not in {"localhost", "127.0.0.1", "::1"}:
    raise SystemExit("Submits are restricted to a local preview.")
OUT.mkdir(parents=True, exist_ok=True)
VIEWS = {"desktop": (1440, 900, False), "phone": (393, 852, True)}
FRAMES_MS = [0, 120, 260, 420, 650, 1000]
RECTS = [".entry-row", ".signup-head > h2", ".signup-note", ".email-row", ".waitlist-form", ".waitlist-success",
         ".waitlist-success > *", ".introduction-actions"]

def rects(page):
    return page.evaluate("""(sels) => sels.flatMap(s => [...document.querySelectorAll(s)].map((el, i) => {
        const r = el.getBoundingClientRect(); return [s + (i ? `#${i}` : ''), Math.round(r.left), Math.round(r.top + scrollY), Math.round(r.width), Math.round(r.height)]; }))""", RECTS)

with sync_playwright() as p:
    browser = p.chromium.launch(args=["--enable-webgl", "--use-angle=swiftshader"])
    for motion in ["no-preference", "reduce"]:
        for name, (w, h, mobile) in VIEWS.items():
            page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=2, is_mobile=mobile,
                                    has_touch=mobile, reduced_motion=motion)
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(BASE + QUERY, wait_until="networkidle")
            band = page.locator(".entry-row")
            band.scroll_into_view_if_needed()
            page.wait_for_timeout(400)
            tag = f"{name}-{'motion' if motion == 'no-preference' else 'reduced'}"
            band.screenshot(path=str(OUT / f"{tag}-before.png"))
            before = rects(page)
            page.locator("#email").fill("preview@example.com")
            # The honeypot branch renders the same success UI without the rate limit or a stored contact.
            page.locator("#hp_ref").evaluate("el => el.value = 'preview'")
            if motion == "no-preference":
                # Hold the server action so the pending state stays on screen long enough to capture.
                page.evaluate("""() => { const send = window.fetch; window.fetch = (...args) => new Promise(r => setTimeout(r, 1500)).then(() => send(...args)); }""")
            page.locator("button[type=submit]").click()
            if motion == "no-preference":
                page.wait_for_selector(".waitlist-form[aria-busy=true]", timeout=5000)
                page.mouse.move(0, 0)
                for i, ms in enumerate((150, 300, 450)):
                    page.wait_for_timeout(150)
                    page.locator(".join-button").screenshot(path=str(OUT / f"{tag}-pending-{i}.png"))
                print("  pending label:", page.locator(".join-button").inner_text())
            page.wait_for_selector(".waitlist-success", state="attached", timeout=15000)
            # Only the signup's own motion; the page-load daylight and headline keep running.
            page.evaluate("window.signup = () => document.getAnimations().filter(a => a.effect?.target?.closest?.('.waitlist'))")
            if motion == "no-preference":
                # Screenshots are slower than the motion, so freeze every animation and seek it frame by frame.
                names = page.evaluate("""() => signup().map(a => { a.pause(); return a.animationName || a.transitionProperty || 'height'; })""")
                print(f"  animations: {sorted(set(names))}")
                for ms in FRAMES_MS:
                    page.evaluate("(t) => signup().forEach(a => { a.currentTime = t; })", ms)
                    band.screenshot(path=str(OUT / f"{tag}-t{ms:04d}.png"), animations="allow")
                page.evaluate("() => signup().forEach(a => a.finish())")
            page.wait_for_timeout(600)
            band.screenshot(path=str(OUT / f"{tag}-after.png"))
            after = rects(page)
            focused = page.evaluate("document.activeElement?.className")
            print(f"\n{tag} {w}x{h} errors {errors or 'none'} focus={focused}")
            for label, rows in (("before", before), ("after", after)):
                print(f"  {label}")
                for s, x, y, rw, rh in rows:
                    print(f"    {s:<28} x={x:<5} y={y:<5} w={rw:<4} h={rh}")
            page.close()
    browser.close()
print(f"\nScreens in {OUT}")
