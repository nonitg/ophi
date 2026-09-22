#!/usr/bin/env python3
"""Capture the signup band before and after a local submit, on desktop and phone, plus frames of the transition.

Usage: site-success.py [base_url] [out_dir] [query]
Local previews only: without RESEND_API_KEY the dev server logs the signup instead of storing it.
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
            page.locator("button[type=submit]").click()
            page.wait_for_selector(".waitlist-success", state="attached", timeout=15000)
            last = 0
            for ms in FRAMES_MS:
                page.wait_for_timeout(ms - last)
                last = ms
                if motion == "no-preference":
                    band.screenshot(path=str(OUT / f"{tag}-t{ms:04d}.png"))
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
