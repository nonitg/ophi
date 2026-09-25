"""Count the words a viewer actually sees on internal-app pages: above the fold, and on the whole page with
closed folds left closed. The glance budget from the 2026-09-21 review was ~380 words on Case Review.

Usage: .venv/bin/python scripts/app-words.py <base_url> [path ...]
"""
import sys

from playwright.sync_api import sync_playwright

base = sys.argv[1].rstrip("/")
paths = sys.argv[2:] or ["/", "/cases/singh", "/cases/rosco", "/cases/whitfield/packet", "/look-back", "/settings"]

COUNT = """(foldPx) => {
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let all = 0, fold = 0;
  while (walker.nextNode()) {
    const n = walker.currentNode, el = n.parentElement;
    if (!el || el.closest('script, style, .chip-pop, .sr, noscript')) continue;
    const d = el.closest('details:not([open])');
    if (d && !el.closest('summary')) continue;
    const s = getComputedStyle(el);
    if (s.display === 'none' || s.visibility === 'hidden') continue;
    const words = (n.textContent.match(/[A-Za-z0-9$#%][^\\s]*/g) || []).length;
    if (!words) continue;
    all += words;
    const r = el.getBoundingClientRect();
    if (r.top + window.scrollY < foldPx) fold += words;
  }
  return {all, fold, height: document.documentElement.scrollHeight};
}"""

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_context(viewport={"width": 1440, "height": 900}).new_page()
    for path in paths:
        page.goto(base + path, wait_until="networkidle")
        r = page.evaluate(COUNT, 900)
        print(f"{path:28} {r['fold']:4} words above the fold  {r['all']:5} visible  {r['height']:5}px tall")
    b.close()
