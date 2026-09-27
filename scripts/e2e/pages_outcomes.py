"""pages lane, part 2: /outcomes filters, tab counts, pagination, and a row into /past/{id} and back."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pages_lib import BASE, OUT, Recorder, context, goto, shot  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

r: dict = {}


def scrape(page):
    tabs = page.evaluate(
        """() => [...document.querySelectorAll('.plist-tab')].map(a => ({
              label: a.textContent.replace(/\\s+/g,' ').trim(), n: +a.querySelector('.num').textContent,
              href: a.getAttribute('href'), on: a.classList.contains('is-on')}))"""
    )
    rows = page.evaluate(
        """() => [...document.querySelectorAll('table.plist tbody tr')].map(tr => ({
              cells: [...tr.querySelectorAll('td')].map(td => td.textContent.replace(/\\s+/g,' ').trim()),
              href: tr.querySelector('a.plist-link')?.getAttribute('href') || null}))"""
    )
    pager = page.locator(".plist-pager")
    return {
        "tabs": tabs, "rows": rows, "n_rows": len(rows),
        "pager": pager.inner_text().replace("\n", " ") if pager.count() else None,
        "filters_present": page.evaluate(
            """() => [...document.querySelectorAll('.plist-filters select')].map(s => ({
                  name: s.name, options: s.options.length, value: s.value}))"""),
        "clear": page.locator(".plist-clear").count(),
    }


with sync_playwright() as pw:
    browser, ctx = context(pw, "coordinator")
    rec = Recorder()
    page = ctx.new_page()
    rec.attach(page)

    r["default"] = {"status": goto(page, rec, "/outcomes")}
    r["default"] |= scrape(page)
    r["default"]["back_link"] = page.locator("a.back").inner_text()
    r["default"]["report_fold"] = page.locator("details.plist-report summary").inner_text().replace("\n", " ") \
        if page.locator("details.plist-report").count() else None
    shot(page, "outcomes-1440.png")

    # each status tab
    for t in ("approved", "denied", "resent"):
        r[f"tab-{t}"] = {"status": goto(page, rec, f"/outcomes?status={t}")} | scrape(page)

    # one value from each filter select, alone and combined
    sels = r["default"]["filters_present"]
    opts = page.evaluate(
        """() => Object.fromEntries([...document.querySelectorAll('.plist-filters select')].map(s =>
              [s.name, [...s.options].map(o => o.value).filter(v => v)]))"""
    )
    r["select_options"] = {k: {"n": len(v), "sample": v[:6]} for k, v in opts.items()}

    picks = {}
    for name, values in opts.items():
        if values:
            picks[name] = values[len(values) // 2]
    r["picks"] = picks

    for name, val in picks.items():
        r[f"filter-{name}"] = {"url": f"/outcomes?{name}={val}", "status": goto(page, rec, f"/outcomes?{name}={val}")} | scrape(page)

    combo = "&".join(f"{k}={v}" for k, v in picks.items())
    r["combo"] = {"url": f"/outcomes?{combo}", "status": goto(page, rec, f"/outcomes?{combo}")} | scrape(page)

    # combo + a status tab
    r["combo-denied"] = {"url": f"/outcomes?status=denied&{combo}",
                         "status": goto(page, rec, f"/outcomes?status=denied&{combo}")} | scrape(page)

    # empty result set: a tooth that cannot be in the data
    r["empty"] = {"status": goto(page, rec, "/outcomes?tooth=99")} | scrape(page)
    r["empty"]["body_text"] = page.locator("table.plist tbody").inner_text().replace("\n", " ")
    shot(page, "outcomes-empty-1440.png")

    # bad params
    r["bad_status_param"] = {"status": goto(page, rec, "/outcomes?status=banana")} | scrape(page)
    r["page_zero"] = {"status": goto(page, rec, "/outcomes?page=0")} | scrape(page)
    r["page_huge"] = {"status": goto(page, rec, "/outcomes?page=9999")} | scrape(page)
    r["page_nan"] = {"status": goto(page, rec, "/outcomes?page=abc")}

    # pagination walk: page 1 -> Older -> Newer
    goto(page, rec, "/outcomes")
    ids1 = [x["href"] for x in scrape(page)["rows"]]
    page.locator(".plist-pager a", has_text="Older").first.click()
    page.wait_for_load_state("load")
    s2 = scrape(page)
    ids2 = [x["href"] for x in s2["rows"]]
    r["paging"] = {"url_p2": page.url, "pager_p2": s2["pager"], "overlap": len(set(ids1) & set(ids2)),
                   "n1": len(ids1), "n2": len(ids2)}
    page.locator(".plist-pager a", has_text="Newer").first.click()
    page.wait_for_load_state("load")
    r["paging"]["back_url"] = page.url
    r["paging"]["back_matches_p1"] = [x["href"] for x in scrape(page)["rows"]] == ids1

    # last page
    last = r["default"]["pager"]
    goto(page, rec, "/outcomes?page=15")
    s = scrape(page)
    r["last_page"] = {"pager": s["pager"], "n_rows": s["n_rows"],
                      "has_older": page.locator(".plist-pager a", has_text="Older").count()}

    # follow a row into /past/{id} and back
    goto(page, rec, "/outcomes")
    href = scrape(page)["rows"][0]["href"]
    page.locator(f"a[href='{href}']").first.click()
    page.wait_for_load_state("load")
    r["past"] = {"url": page.url, "title": page.title(),
                 "h1": page.locator("h1").first.inner_text(),
                 "back": page.locator("a.back").inner_text() if page.locator("a.back").count() else None,
                 "back_href": page.locator("a.back").get_attribute("href") if page.locator("a.back").count() else None,
                 "text": page.locator("main").inner_text()[:1500]}
    shot(page, "past-detail-1440.png")
    page.locator("a.back").click()
    page.wait_for_load_state("load")
    r["past"]["after_back_url"] = page.url
    r["past"]["after_back_title"] = page.title()

    r["past_404"] = {"status": goto(page, rec, "/past/nope-does-not-exist"),
                     "text": page.locator("main").inner_text()[:400]}

    rec.dump("console-outcomes.json")
    r["console"], r["failed"], r["bad_status"] = rec.console, rec.failed, rec.bad_status
    browser.close()

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "outcomes.json").write_text(json.dumps(r, indent=2))
print("written")
