"""Shared Playwright helpers for the sunlife E2E lane."""
from __future__ import annotations

import json
import pathlib
import re

BASE = "http://127.0.0.1:8765"
OUT = pathlib.Path(__file__).resolve().parents[2] / "var/e2e/sunlife"
DESKTOP = {"width": 1440, "height": 900}
MOBILE = {"width": 390, "height": 844}
CASES = ["abeldent_158", "abeldent_160", "abeldent_162", "abeldent_164", "abeldent_170"]


def new_context(pw, actor="coordinator", viewport=None):
    browser = pw.chromium.launch()
    ctx = browser.new_context(viewport=viewport or DESKTOP)
    ctx.add_cookies([{"name": "actor", "value": actor, "url": BASE}])
    return browser, ctx


def page_with_log(ctx):
    page = ctx.new_page()
    errs: list[str] = []
    page.on("console", lambda m: errs.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
    page.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
    return page, errs


def goto(page, path, timeout=60000):
    r = page.goto(BASE + path, wait_until="load", timeout=timeout)
    return r.status if r else None


def text(page):
    return re.sub(r"\n{3,}", "\n\n", page.inner_text("body"))


def overflow(page):
    return page.evaluate(
        "() => ({sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth})")


def shot(page, name):
    p = OUT / name
    page.screenshot(path=str(p), full_page=True)
    return str(p)


def dump(name, obj):
    p = OUT / name
    p.write_text(json.dumps(obj, indent=2, default=str))
    return str(p)
