"""Shared Playwright harness for the dentist E2E lane: one browser, console-error capture, shot naming."""
from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765"
OUT = Path("/home/arch/Desktop/code/colombus/var/e2e/dentist")
CASES = ["abeldent_5", "abeldent_6", "abeldent_33", "abeldent_60", "abeldent_168", "abeldent_9", "abeldent_166"]
DESKTOP = {"width": 1440, "height": 900}
PHONE = {"width": 390, "height": 844}


class Lane:
    def __init__(self, actor: str = "dentist", viewport: dict | None = None):
        self.actor = actor
        self.viewport = viewport or DESKTOP
        self.console: list[dict] = []
        self.pageerrors: list[str] = []

    def __enter__(self):
        OUT.mkdir(parents=True, exist_ok=True)
        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.launch()
        self.ctx = self.browser.new_context(viewport=self.viewport)
        if self.actor:
            self.ctx.add_cookies([{"name": "actor", "value": self.actor, "url": BASE}])
        self.page = self.ctx.new_page()
        self.page.on("console", lambda m: self.console.append({"type": m.type, "text": m.text, "url": self.page.url})
                     if m.type in ("error", "warning") else None)
        self.page.on("pageerror", lambda e: self.pageerrors.append(f"{self.page.url} :: {e}"))
        return self

    def __exit__(self, *a):
        self.ctx.close()
        self.browser.close()
        self._pw.stop()

    def go(self, path: str):
        r = self.page.goto(BASE + path, wait_until="load", timeout=45000)
        return r.status if r else None

    def shot(self, name: str, full: bool = True):
        p = OUT / f"{name}.png"
        self.page.screenshot(path=str(p), full_page=full)
        return str(p)

    def overflow(self) -> dict:
        return self.page.evaluate("""() => {
          const d = document.documentElement;
          const wide = [...document.querySelectorAll('body *')]
            .filter(e => e.getBoundingClientRect().right > d.clientWidth + 2 && e.offsetParent !== null)
            .slice(0, 8)
            .map(e => e.tagName + '.' + (e.className && e.className.toString ? e.className.toString().slice(0,50) : '')
                      + ' right=' + Math.round(e.getBoundingClientRect().right));
          const clipped = [...document.querySelectorAll('body *')]
            .filter(e => e.scrollWidth > e.clientWidth + 2 && e.clientWidth > 0 && getComputedStyle(e).overflowX !== 'auto'
                         && getComputedStyle(e).overflowX !== 'scroll' && e.children.length === 0)
            .slice(0, 8)
            .map(e => e.tagName + ' "' + (e.textContent||'').trim().slice(0,40) + '" ' + e.scrollWidth + '>' + e.clientWidth);
          return {docScroll: d.scrollWidth, docClient: d.clientWidth, wide, clipped};
        }""")


def save(name: str, obj) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(obj, indent=2, default=str))
