#!/usr/bin/env python3
"""Review pass: screenshots at many viewports plus layout measurements (overlap, overflow, tap targets)."""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "outputs/site-review")
OUT.mkdir(parents=True, exist_ok=True)
VIEWPORTS = {
    "4k": (2560, 1440), "fhd": (1920, 1080), "mac-short": (1440, 700), "desktop": (1440, 900),
    "laptop": (1280, 800), "ipad-land": (1180, 820), "ipad": (820, 1180), "tablet-small": (700, 900),
    "phone-land": (844, 390), "iphone": (390, 844), "se": (375, 667), "tiny": (320, 568),
}

MEASURE = """() => {
  const r = s => { const e = document.querySelector(s); if (!e) return null; const b = e.getBoundingClientRect(); return {x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height),r:Math.round(b.right),b:Math.round(b.bottom)}; };
  const hits = (a, b) => a && b && a.x < b.r && b.x < a.r && a.y < b.b && b.y < a.b;
  const span = r('.poster-title > span'), em = r('.poster-title > em'), ctr = r('.xray-slot'), canvas = r('.tooth-canvas canvas');
  const small = [...document.querySelectorAll('button, a, summary, input, select')].filter(e => e.offsetParent).map(e => { const b = e.getBoundingClientRect(); return {t:(e.textContent||e.getAttribute('aria-label')||e.tagName).trim().slice(0,30), w:Math.round(b.width), h:Math.round(b.height)}; }).filter(o => o.h < 24 || o.w < 24);
  return {
    scrollW: document.documentElement.scrollWidth, innerW: innerWidth, docH: document.documentElement.scrollHeight, innerH: innerHeight,
    title1: span, title2: em, controls: ctr, canvas, signup: r('#join'), footer: r('.site-footer'),
    controlsOverTitle: hits(ctr, span) || hits(ctr, em),
    emOffRight: em ? em.r > innerWidth : null,
    small,
  };
}"""

with sync_playwright() as p:
    browser = p.chromium.launch(args=["--enable-webgl", "--use-angle=swiftshader"])
    report = {}
    for name, (w, h) in VIEWPORTS.items():
        page = browser.new_page(viewport={"width": w, "height": h}, reduced_motion="reduce")
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: m.type in ("error", "warning") and errors.append(m.text))
        page.goto(BASE, wait_until="networkidle")
        page.wait_for_selector('.tooth-viewer[data-ready="true"]', timeout=15000)
        page.wait_for_timeout(300)
        page.screenshot(path=str(OUT / f"{name}.png"))
        page.screenshot(path=str(OUT / f"{name}-full.png"), full_page=True)
        report[name] = page.evaluate(MEASURE) | {"errors": errors}
        page.close()
    # Server-side error state: honeypot off, invalid email.
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto(BASE, wait_until="networkidle")
    page.fill("#email", "nope")
    page.click(".join-button")
    page.wait_for_selector(".waitlist-error")
    page.screenshot(path=str(OUT / "error.png"))
    report["error-focus"] = page.evaluate("document.activeElement && (document.activeElement.id || document.activeElement.tagName)")
    page.click(".why-button")
    page.wait_for_timeout(300)
    page.screenshot(path=str(OUT / "why.png"))
    page.keyboard.press("Escape")
    page.click(".privacy-button")
    page.wait_for_timeout(300)
    page.screenshot(path=str(OUT / "privacy.png"))
    page.close()
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.goto(BASE, wait_until="networkidle")
    page.click(".why-button")
    page.wait_for_timeout(300)
    page.screenshot(path=str(OUT / "why-mobile.png"))
    page.close()
    # Head tags a crawler and social previewer see.
    page = browser.new_page()
    page.goto(BASE, wait_until="networkidle")
    report["head"] = page.evaluate("[...document.head.querySelectorAll('meta,link')].map(e => e.outerHTML).filter(s => !s.includes('stylesheet') && !s.includes('preload'))")
    for path in ["/robots.txt", "/sitemap.xml", "/nope-404", "/apple-icon.png", "/favicon.ico"]:
        report[path] = page.request.get(BASE + path).status
    browser.close()
    (OUT / "report.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))
