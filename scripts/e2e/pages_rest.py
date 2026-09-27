"""pages lane, part 3: results / recover / look-back / settings / audit.csv / rules / api + errors,
for both actors. Read-only: no form on these pages is submitted except the actor switch."""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pages_lib import BASE, OUT, Recorder, context, goto, shot  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

CASE = "abeldent_9"  # read-only probe: assessment.json only, never posted to
out: dict = {}


def page_facts(page):
    return {
        "title": page.title(),
        "h1": [h.inner_text() for h in page.locator("h1").all()],
        "buttons": page.evaluate(
            """() => [...document.querySelectorAll('main button, main input[type=submit]')].map(b => ({
                  text: (b.textContent||b.value||'').replace(/\\s+/g,' ').trim().slice(0,60),
                  form: b.closest('form')?.getAttribute('action') || null, disabled: b.disabled}))"""),
        "links": page.evaluate(
            """() => [...document.querySelectorAll('main a[href]')].map(a => ({
                  text: (a.textContent||'').replace(/\\s+/g,' ').trim().slice(0,50), href: a.getAttribute('href')}))"""),
        "text": page.locator("main").inner_text()[:2500],
    }


with sync_playwright() as pw:
    for actor in ("coordinator", "dentist"):
        browser, ctx = context(pw, actor)
        rec = Recorder()
        page = ctx.new_page()
        rec.attach(page)
        a = out[actor] = {}

        for path, key in (("/results", "results"), ("/recover", "recover"), ("/settings", "settings"),
                          ("/rules", "rules")):
            a[key] = {"status": goto(page, rec, path)} | page_facts(page)
            shot(page, f"{key}-{actor}-1440.png")

        # /look-back should land on the Results retrospective
        st = goto(page, rec, "/look-back")
        a["look_back"] = {"status": st, "url": page.url, "title": page.title(),
                          "anchor_exists": page.locator("#before").count()}

        # settings audit log detail
        goto(page, rec, "/settings")
        a["audit"] = page.evaluate(
            """() => {
              const rows = [...document.querySelectorAll('table tbody tr')];
              return {n: rows.length, head: [...document.querySelectorAll('table thead th')].map(t=>t.textContent.trim()),
                      first: rows.slice(0,3).map(r => [...r.children].map(c => c.textContent.replace(/\\s+/g,' ').trim())),
                      last: rows.slice(-2).map(r => [...r.children].map(c => c.textContent.replace(/\\s+/g,' ').trim()))};
            }"""
        )

        # audit.csv download
        with page.expect_download() as dl:
            page.evaluate("() => { const a=document.createElement('a'); a.href='/settings/audit.csv'; a.download=''; document.body.appendChild(a); a.click(); }")
        d = dl.value
        p = OUT / f"audit-{actor}.csv"
        d.save_as(str(p))
        raw = p.read_text()
        rows = list(csv.reader(io.StringIO(raw)))
        a["csv"] = {"suggested": d.suggested_filename, "bytes": len(raw), "header": rows[0] if rows else None,
                    "n_rows": len(rows) - 1, "widths": sorted({len(r) for r in rows[1:]}),
                    "sample": rows[1:3], "last": rows[-1] if len(rows) > 1 else None}

        # rules page detail
        goto(page, rec, "/rules")
        a["rules_detail"] = page.evaluate(
            """() => {
              const f = document.querySelector('form[action$="/rules/use"]');
              const acks = [...document.querySelectorAll('input[type=checkbox]')].map(c => ({name: c.name, checked: c.checked, required: c.required}));
              return {
                has_use_form: !!f,
                use_button: f ? (f.querySelector('button')?.textContent||'').replace(/\\s+/g,' ').trim() : null,
                hidden: f ? [...f.querySelectorAll('input[type=hidden]')].map(i => ({name: i.name, value: i.value.slice(0,80)})) : [],
                acks,
                forms: [...document.querySelectorAll('main form')].map(x => ({action: x.getAttribute('action'), method: x.method})),
              };
            }"""
        )

        # API
        req = ctx.request
        r = req.get(f"{BASE}/api/cases/{CASE}/assessment.json")
        body = r.text()
        a["api_ok"] = {"status": r.status, "ctype": r.headers.get("content-type"), "bytes": len(body)}
        try:
            j = json.loads(body)
            a["api_ok"]["keys"] = sorted(j.keys()) if isinstance(j, dict) else type(j).__name__
            a["api_ok"]["sample"] = {k: (v if not isinstance(v, (list, dict)) else f"<{type(v).__name__} len={len(v)}>")
                                     for k, v in list(j.items())[:20]} if isinstance(j, dict) else None
            reqs = j.get("requirements") if isinstance(j, dict) else None
            a["api_ok"]["req0"] = reqs[0] if reqs else None
        except Exception as e:
            a["api_ok"]["parse_error"] = str(e)

        for bad in (f"{BASE}/api/cases/nope/assessment.json", f"{BASE}/api/cases/abeldent_99999/assessment.json"):
            rr = req.get(bad)
            a.setdefault("api_bad", []).append({"url": bad, "status": rr.status, "body": rr.text()[:200]})

        rr = req.get(f"{BASE}/cases/nope")
        a["case_bad"] = {"status": rr.status, "body": rr.text()[:300],
                         "is_html_error_page": "error" in rr.text().lower() and "<html" in rr.text().lower()}

        rec.dump(f"console-rest-{actor}.json")
        a["console"], a["failed"], a["bad_status"] = rec.console, rec.failed, rec.bad_status
        browser.close()

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "rest.json").write_text(json.dumps(out, indent=2, default=str))
print("written")
