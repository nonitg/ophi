#!/usr/bin/env python3
"""Probe the hero: how the headline breaks at several widths, and any console errors or Next dev issues.

usage: site-hero-probe.py [BASE]
"""
import sys
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
LINES = """() => {
  const h = document.querySelector('#hero-title');
  const range = document.createRange();
  const tops = new Map();
  for (const node of h.childNodes) {
    if (node.nodeType !== 3) continue;
    for (let i = 0; i < node.length; i++) {
      range.setStart(node, i); range.setEnd(node, i + 1);
      const r = range.getClientRects()[0]; if (!r) continue;
      const k = Math.round(r.top); tops.set(k, (tops.get(k) || '') + node.data[i]);
    }
  }
  return { lines: [...tops.values()].map((s) => s.trim()), column: Math.round(h.getBoundingClientRect().width) };
}"""

with sync_playwright() as p:
    browser = p.chromium.launch(args=["--mute-audio"])
    for width in [320, 345, 360, 390, 480, 700, 701, 900, 1100, 1101, 1280, 1440, 1920]:
        page = browser.new_page(viewport={"width": width, "height": 900}, reduced_motion="reduce")
        logs = []
        page.on("console", lambda m: logs.append(f"{m.type}: {m.text[:200]}") if m.type in ("error", "warning") else None)
        page.goto(BASE, wait_until="networkidle")
        print(width, page.evaluate(LINES), logs[:4] if width == 1440 else "")
        page.close()
    browser.close()
