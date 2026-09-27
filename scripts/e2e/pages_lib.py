"""Shared helpers for the `pages` E2E lane: a browser context per actor that records
console errors, failed requests and non-2xx responses for every page it loads."""
from __future__ import annotations

import json
from pathlib import Path

BASE = "http://127.0.0.1:8765"
OUT = Path("var/e2e/pages")
DESKTOP = {"width": 1440, "height": 900}
PHONE = {"width": 390, "height": 844}


class Recorder:
    def __init__(self):
        self.console: list[dict] = []
        self.failed: list[dict] = []
        self.bad_status: list[dict] = []
        self.where = "?"

    def attach(self, page):
        page.on("console", lambda m: m.type in ("error", "warning") and self.console.append(
            {"where": self.where, "type": m.type, "text": m.text[:300]}))
        page.on("pageerror", lambda e: self.console.append({"where": self.where, "type": "pageerror", "text": str(e)[:300]}))
        page.on("requestfailed", lambda r: self.failed.append(
            {"where": self.where, "url": r.url, "why": r.failure}))
        page.on("response", lambda r: r.status >= 400 and self.bad_status.append(
            {"where": self.where, "url": r.url, "status": r.status}))

    def dump(self, name):
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / name).write_text(json.dumps(
            {"console": self.console, "failed": self.failed, "bad_status": self.bad_status}, indent=2))


def context(pw, actor: str, viewport=DESKTOP):
    browser = pw.chromium.launch()
    ctx = browser.new_context(viewport=viewport, base_url=BASE)
    ctx.add_cookies([{"name": "actor", "value": actor, "url": BASE}])
    return browser, ctx


def goto(page, rec, path: str):
    rec.where = path
    resp = page.goto(BASE + path, wait_until="load", timeout=30000)
    return resp.status if resp else None


def shot(page, name: str):
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / name
    page.screenshot(path=str(p), full_page=True)
    return str(p)


def overflow(page) -> dict:
    """Horizontal overflow plus the widest offending elements, for the layout pass."""
    return page.evaluate(
        """() => {
          const de = document.documentElement;
          const vw = de.clientWidth;
          const wide = [];
          for (const el of document.querySelectorAll('body *')) {
            const r = el.getBoundingClientRect();
            if (r.width === 0 || r.height === 0) continue;
            if (r.right > vw + 1 || r.left < -1) {
              wide.push({tag: el.tagName.toLowerCase(), cls: el.className.toString().slice(0,60),
                         left: Math.round(r.left), right: Math.round(r.right),
                         text: (el.textContent||'').trim().slice(0,60)});
            }
          }
          return {vw, scrollW: de.scrollWidth, overflows: de.scrollWidth > vw + 1, wide: wide.slice(0, 12)};
        }"""
    )


def clipped(page) -> list:
    """Elements whose content is cut off by their own box (scrollWidth/Height beyond clientWidth/Height)."""
    return page.evaluate(
        """() => {
          const out = [];
          for (const el of document.querySelectorAll('body *')) {
            if (el.children.length > 3) continue;
            const s = getComputedStyle(el);
            if (s.overflow === 'visible' && s.overflowX === 'visible' && s.overflowY === 'visible') continue;
            if (el.scrollWidth > el.clientWidth + 2 || el.scrollHeight > el.clientHeight + 2) {
              if (s.overflowX === 'auto' || s.overflowX === 'scroll') continue;
              out.push({tag: el.tagName.toLowerCase(), cls: el.className.toString().slice(0,50),
                        sw: el.scrollWidth, cw: el.clientWidth, sh: el.scrollHeight, ch: el.clientHeight,
                        text: (el.textContent||'').trim().slice(0,60)});
            }
          }
          return out.slice(0, 15);
        }"""
    )
