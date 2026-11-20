#!/usr/bin/env python3
"""Measure the page at every breakpoint edge: page overflow, text escaping its section, and type under the 14px floor
(the copy tag is exempt). Exits 1 on any finding.

usage: site-widths.py [BASE]
"""
import sys
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
WIDTHS = [320, 345, 360, 390, 480, 600, 700, 701, 768, 899, 900, 940, 1024, 1100, 1101, 1280, 1440, 1600, 1920, 2560]
SECTIONS = ["header", "section[aria-labelledby=hero-title]", "#why", "#how", "#story", "#clinic", "#desk", "#join", "#questions", "footer"]
JS = """(sections) => {
  const out = [];
  if (document.documentElement.scrollWidth > innerWidth) out.push('page overflows');
  for (const sel of sections) {
    const el = document.querySelector(sel);
    if (!el) { out.push('missing ' + sel); continue; }
    const box = el.getBoundingClientRect();
    for (const node of el.querySelectorAll('p, h2, h3, li, dd, dt, a, button, span')) {
      if (node.closest('.sr-only, [aria-hidden=true]') || !node.offsetParent) continue;
      const r = node.getBoundingClientRect();
      if (r.width && (r.right > Math.min(innerWidth, box.right) + 1.5 || r.left < Math.max(0, box.left) - 1.5)) out.push(sel + ': escapes: ' + node.textContent.trim().slice(0, 40));
    }
  }
  // The type floor: nothing a visitor reads under 14px.
  for (const node of document.querySelectorAll('main *, footer *, header *')) {
    if (node.closest('.sr-only, .pill-tag') || !node.offsetParent || ![...node.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim())) continue;
    const size = parseFloat(getComputedStyle(node).fontSize);
    if (size < 14) out.push('small type ' + size + 'px: ' + node.textContent.trim().slice(0, 40));
  }
  return [...new Set(out)];
}"""
bad = 0
with sync_playwright() as p:
    browser = p.chromium.launch(args=["--mute-audio"])
    for width in WIDTHS:
        page = browser.new_page(viewport={"width": width, "height": 900}, device_scale_factor=1, reduced_motion="reduce")
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        # Vercel Analytics only exists on Vercel, so its script 404s on a local server.
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" and "/_vercel/" not in m.location.get("url", "") else None)
        page.goto(BASE, wait_until="networkidle")
        found = page.evaluate(JS, SECTIONS) + errors
        if found:
            bad += 1
            print(f"{width}: {found}")
        page.close()
    browser.close()
print("clean" if not bad else f"{bad} widths with findings")
sys.exit(1 if bad else 0)
