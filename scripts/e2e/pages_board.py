"""pages lane, part 1: the / board for both actors, plus a crawl of every link on it."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pages_lib import BASE, OUT, Recorder, context, goto, shot  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

report: dict = {}

with sync_playwright() as pw:
    for actor in ("coordinator", "dentist"):
        browser, ctx = context(pw, actor)
        rec = Recorder()
        page = ctx.new_page()
        rec.attach(page)
        status = goto(page, rec, "/")
        a = report[actor] = {"status": status, "title": page.title()}

        a["headline"] = page.locator("h1").first.inner_text()
        a["who_pressed"] = page.locator("form.me button[aria-pressed='true']").inner_text()
        a["who_buttons"] = page.locator("form.me button").all_inner_texts()

        cols = []
        for sec in page.locator("section.col").all():
            n = sec.locator(".col-n").inner_text()
            cards = sec.locator("ul.tiles li a.tile")
            cols.append({
                "label": sec.locator("h2").inner_text(),
                "count_shown": n,
                "cards": cards.count(),
                "job": sec.locator(".col-job").inner_text() if sec.locator(".col-job").count() else None,
                "card_names": [c.locator(".tile-name").inner_text() for c in cards.all()],
            })
        a["columns"] = cols

        start = page.locator("section.start")
        a["start"] = None
        if start.count():
            a["start"] = {
                "aria": start.get_attribute("aria-label"),
                "text": start.inner_text()[:400],
                "cta": start.locator("a.btn").inner_text() if start.locator("a.btn").count() else None,
                "cta_href": start.locator("a.btn").get_attribute("href") if start.locator("a.btn").count() else None,
            }
        src = page.locator("a.src")
        a["source_links"] = [{"text": s.inner_text(), "href": s.get_attribute("href"),
                              "title": s.get_attribute("title"), "target": s.get_attribute("target")}
                             for s in src.all()]

        links = page.evaluate(
            """() => [...document.querySelectorAll('a[href]')].map(a => ({href: a.getAttribute('href'),
                  abs: a.href, text: (a.textContent||'').trim().slice(0,40), target: a.target}))"""
        )
        a["links"] = links
        # crawl every same-origin link with the actor cookie
        req = ctx.request
        seen, crawl = set(), []
        for l in links:
            u = l["abs"]
            if not u.startswith(BASE) or u in seen:
                continue
            seen.add(u)
            r = req.get(u, max_redirects=0)
            crawl.append({"url": u, "text": l["text"], "status": r.status,
                          "loc": r.headers.get("location")})
        # external links: just record, HEAD them separately
        a["external"] = sorted({l["abs"] for l in links if not l["abs"].startswith(BASE)})
        a["crawl"] = crawl

        shot(page, f"board-{actor}-1440.png")
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(300)
        shot(page, f"board-{actor}-390.png")

        rec.dump(f"console-board-{actor}.json")
        a["console"] = rec.console
        a["failed"] = rec.failed
        a["bad_status"] = rec.bad_status
        browser.close()

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "board.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2)[:12000])
