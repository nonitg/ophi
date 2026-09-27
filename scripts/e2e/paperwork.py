#!/usr/bin/env python
"""E2E lane `paperwork`: drive the coordinator's Paperwork-column cases through the real board flow.

Usage: paperwork.py <step> [args]   — steps are small so the run can be inspected between them.
Output: var/e2e/paperwork/*.json and *.png
"""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765"
OUT = pathlib.Path(__file__).resolve().parents[2] / "var/e2e/paperwork"
OUT.mkdir(parents=True, exist_ok=True)

CASES = {
    "abeldent_7": "Lenny Jones",
    "abeldent_8": "Karen Jones",
    "abeldent_56": "John Provost",
    "abeldent_163": "Christa Galatio",
    "abeldent_165": "Bob Miller",
}


def facts(page):
    """The parts of a case page a coordinator acts on, as plain text, for before/after comparison."""
    return page.evaluate(
        """() => {
      const t = el => el ? el.innerText.replace(/\\s+/g,' ').trim() : null;
      const all = sel => [...document.querySelectorAll(sel)].map(t);
      return {
        url: location.pathname + location.search,
        h1: t(document.querySelector('h1')),
        now_title: t(document.querySelector('#now-title')),
        now: t(document.querySelector('#now')),
        risk: t(document.querySelector('.risk')),
        risk_src: t(document.querySelector('.risk-src')),
        gaps: all('.gap-title'),
        gap_effects: all('.gap-effect'),
        applied: all('.autofix-done'),
        apply_buttons: [...document.querySelectorAll('button[name=fix]')].map(b => b.value),
        capture_buttons: [...document.querySelectorAll("form[action*='/capture'] input[name=requirement_id]")].map(i => i.value),
        undo: all('.now-undo'),
        steps: all('.stepper li, .steps li'),
        crit_form: !!document.querySelector('#crit-form'),
        crit_rows: [...document.querySelectorAll('#crit-form .crit')].map(r => t(r)),
        crit_radios: [...document.querySelectorAll('#crit-form input[type=radio]')].map(r => ({n: r.name, v: r.value, on: r.checked})),
        crit_notes: [...document.querySelectorAll('#crit-form input[name^=note_]')].map(i => ({n: i.name, v: i.value})),
        requirements: all('#requirements .req'),
        activity: all('.feed li').slice(0, 8),
        links: [...document.querySelectorAll('a')].map(a => a.getAttribute('href')).filter(h => h && !h.startsWith('#')),
        banner: t(document.querySelector('.flash, .toast, .banner')),
        body_len: document.body.innerText.length,
      };
    }"""
    )


def overflow(page):
    return page.evaluate(
        """() => {
      const de = document.documentElement;
      const wide = [...document.querySelectorAll('body *')].filter(e => {
        const r = e.getBoundingClientRect();
        return r.width > 0 && (r.right > de.clientWidth + 1 || r.left < -1);
      }).slice(0, 12).map(e => e.tagName + '.' + (e.className || '') + ' :: ' + e.innerText.slice(0,60).replace(/\\s+/g,' '));
      const clipped = [...document.querySelectorAll('body *')].filter(e =>
        e.children.length === 0 && e.scrollWidth > e.clientWidth + 2 && e.clientWidth > 0
      ).slice(0, 12).map(e => e.tagName + '.' + (e.className||'') + ' sw=' + e.scrollWidth + ' cw=' + e.clientWidth + ' :: ' + e.innerText.slice(0,60));
      return {doc_scroll: de.scrollWidth, doc_client: de.clientWidth, wide, clipped};
    }"""
    )


def ctx(p, actor="coordinator", width=1440, height=900):
    b = p.chromium.launch()
    c = b.new_context(viewport={"width": width, "height": height})
    c.add_cookies([{"name": "actor", "value": actor, "url": BASE}])
    errs = []
    c.on("weberror", lambda e: errs.append(str(e)))
    return b, c, errs


def goto(page, path):
    r = page.goto(BASE + path, wait_until="load", timeout=30000)
    return r.status if r else None


def save(name, data):
    (OUT / f"{name}.json").write_text(json.dumps(data, indent=2, default=str))
    print(f"wrote {OUT / (name + '.json')}")


def step_open_from_board():
    """Click into each case from the board, record its opening state + both screenshots."""
    res = {}
    with sync_playwright() as p:
        b, c, errs = ctx(p)
        page = c.new_page()
        console = []
        page.on("console", lambda m: console.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
        for cid, name in CASES.items():
            st = goto(page, "/")
            card = page.locator(f"a:has-text('{name}')").first
            href = card.get_attribute("href")
            card.click()
            page.wait_for_load_state("load", timeout=30000)
            f = facts(page)
            f["board_status"] = st
            f["card_href"] = href
            f["overflow_1440"] = overflow(page)
            page.screenshot(path=str(OUT / f"{cid}-1440.png"), full_page=True)
            page.set_viewport_size({"width": 390, "height": 844})
            page.wait_for_timeout(300)
            f["overflow_390"] = overflow(page)
            page.screenshot(path=str(OUT / f"{cid}-390.png"), full_page=True)
            page.set_viewport_size({"width": 1440, "height": 900})
            res[cid] = f
            print(f"{cid} {name}: {f['now_title']} | risk={f['risk']} | gaps={f['gaps']}")
        res["_console"] = console
        res["_weberrors"] = errs
        b.close()
    save("01-open", res)


def step_apply_one(cid):
    """Apply a single suggested fix with the UI button, then reload and diff."""
    with sync_playwright() as p:
        b, c, errs = ctx(p)
        page = c.new_page()
        goto(page, f"/cases/{cid}")
        before = facts(page)
        out = {"before": before}
        btns = page.locator("button[name=fix]")
        n = btns.count()
        out["n_apply_buttons"] = n
        if n:
            out["clicked"] = btns.first.get_attribute("value")
            btns.first.click()
            page.wait_for_load_state("load", timeout=30000)
            out["after_redirect_url"] = page.url
            out["after_redirect"] = facts(page)
            goto(page, f"/cases/{cid}")
            out["after_reload"] = facts(page)
        out["weberrors"] = errs
        b.close()
    save(f"02-apply-one-{cid}", out)
    print(json.dumps({k: (v.get("risk") if isinstance(v, dict) else v) for k, v in out.items()}, indent=2, default=str))


def step_apply_all(cid):
    """The `all` path on /fixes — the route supports it; check whether the UI offers it and what it does."""
    with sync_playwright() as p:
        b, c, errs = ctx(p)
        page = c.new_page()
        goto(page, f"/cases/{cid}")
        before = facts(page)
        r = page.evaluate(
            """async (cid) => {
          const body = new URLSearchParams({all: '1'});
          const res = await fetch(`/cases/${cid}/fixes`, {method: 'POST', body, redirect: 'follow'});
          return {status: res.status, url: res.url};
        }""",
            cid,
        )
        goto(page, f"/cases/{cid}")
        out = {"before": before, "post": r, "after": facts(page), "weberrors": errs}
        b.close()
    save(f"03-apply-all-{cid}", out)
    print(json.dumps(out["post"], indent=2))
    print("before risk:", out["before"]["risk"], "\nafter risk:", out["after"]["risk"])
    print("before gaps:", out["before"]["gaps"], "\nafter gaps:", out["after"]["gaps"])


def step_criteria(cid, actor):
    """Try the single assert and the bulk assert (with a note) as the given actor."""
    out = {"actor": actor}
    with sync_playwright() as p:
        b, c, errs = ctx(p, actor=actor)
        page = c.new_page()
        goto(page, f"/cases/{cid}")
        out["before"] = facts(page)
        # single assert, posted the way the page's own markup would
        single = page.evaluate(
            """async (cid) => {
          const r = [...document.querySelectorAll('#crit-form input[type=radio]')][0];
          if (!r) return {skipped: 'no criteria radios'};
          const body = new URLSearchParams({criterion_id: r.name.replace(/^value_/,''), value: r.value, note: 'e2e single note'});
          const res = await fetch(`/cases/${cid}/assert`, {method: 'POST', body, redirect: 'follow'});
          return {status: res.status, url: res.url, sent: body.toString(), text: (await res.text()).slice(0, 400)};
        }""",
            cid,
        )
        out["single_assert"] = single
        goto(page, f"/cases/{cid}")
        out["after_single"] = facts(page)
        # bulk: use the real form. pick the first option of every group, add a note on the first
        if page.locator("#crit-form").count():
            picked = page.evaluate(
                """() => {
              const names = [...new Set([...document.querySelectorAll('#crit-form input[type=radio]')].map(r=>r.name))];
              const out = [];
              for (const n of names) {
                const r = document.querySelector(`#crit-form input[name="${n}"]`);
                r.checked = true; out.push({n, v: r.value});
              }
              const note = document.querySelector('#crit-form input[name^=note_]');
              if (note) { note.value = 'e2e bulk note'; out.push({note: note.name}); }
              return out;
            }"""
            )
            out["bulk_picked"] = picked
            page.locator("#crit-form button[type=submit]").first.click()
            page.wait_for_load_state("load", timeout=30000)
            out["bulk_url"] = page.url
            out["bulk_result"] = facts(page)
            goto(page, f"/cases/{cid}")
            out["after_bulk"] = facts(page)
        out["weberrors"] = errs
        b.close()
    save(f"04-criteria-{actor}-{cid}", out)
    print(json.dumps({"single": out["single_assert"], "bulk_url": out.get("bulk_url")}, indent=2, default=str)[:1500])


def step_capture(cid):
    with sync_playwright() as p:
        b, c, errs = ctx(p)
        page = c.new_page()
        goto(page, f"/cases/{cid}")
        before = facts(page)
        out = {"before": before}
        btn = page.locator("form[action*='/capture'] button")
        out["n_capture"] = btn.count()
        if btn.count():
            btn.first.click()
            page.wait_for_load_state("load", timeout=30000)
            out["after_url"] = page.url
            goto(page, f"/cases/{cid}")
            out["after"] = facts(page)
        out["weberrors"] = errs
        b.close()
    save(f"05-capture-{cid}", out)
    print("n_capture", out["n_capture"], "->", out.get("after", {}).get("now_title"))


def step_undo(cid, step):
    """POST the undo the page would post, and one the page would not, to see what the server allows."""
    with sync_playwright() as p:
        b, c, errs = ctx(p)
        page = c.new_page()
        goto(page, f"/cases/{cid}")
        before = facts(page)
        r = page.evaluate(
            """async ([cid, step]) => {
          const res = await fetch(`/cases/${cid}/undo`, {method:'POST', body: new URLSearchParams({step}), redirect:'follow'});
          const t = await res.text();
          return {status: res.status, url: res.url, title: (t.match(/<h1[^>]*>(.*?)<\\/h1>/s)||[])[1], snippet: t.replace(/\\s+/g,' ').slice(0,300)};
        }""",
            [cid, step],
        )
        goto(page, f"/cases/{cid}")
        out = {"step": step, "before": before, "post": r, "after": facts(page), "weberrors": errs}
        b.close()
    save(f"06-undo-{step}-{cid}", out)
    print(json.dumps(r, indent=2)[:1200])
    print("now before:", before["now_title"], "| after:", out["after"]["now_title"])


def step_submit(cid):
    with sync_playwright() as p:
        b, c, errs = ctx(p)
        page = c.new_page()
        goto(page, f"/cases/{cid}")
        before = facts(page)
        r = page.evaluate(
            """async (cid) => {
          const res = await fetch(`/cases/${cid}/submitted`, {method:'POST', body: new URLSearchParams({on: ''}), redirect:'follow'});
          const t = await res.text();
          return {status: res.status, url: res.url, snippet: t.replace(/\\s+/g,' ').slice(0,400)};
        }""",
            cid,
        )
        goto(page, f"/cases/{cid}")
        after = facts(page)
        goto(page, "/")
        board = page.evaluate(
            """() => [...document.querySelectorAll('.col, section')].map(c => (c.innerText||'').replace(/\\s+/g,' ').slice(0,400))"""
        )
        col = page.evaluate(
            """(name) => {
          for (const col of document.querySelectorAll('[class*=col]')) {
            if (col.innerText && col.innerText.includes(name)) return col.innerText.replace(/\\s+/g,' ').slice(0,300);
          } return null;
        }""",
            CASES[cid],
        )
        out = {"before": before, "post": r, "after": after, "board_col_with_case": col, "board": board[:8], "weberrors": errs}
        b.close()
    save(f"07-submit-{cid}", out)
    print(json.dumps({"post": r, "now": after["now_title"], "col": col}, indent=2)[:1500])


def step_packet(cid, actor="coordinator"):
    out = {"actor": actor}
    with sync_playwright() as p:
        b, c, errs = ctx(p, actor=actor)
        page = c.new_page()
        st = goto(page, f"/cases/{cid}/packet")
        out["packet_status"] = st
        out["packet"] = page.evaluate(
            """() => ({h1: (document.querySelector('h1')||{}).innerText,
                       text: document.body.innerText.replace(/\\s+/g,' ').slice(0,1200),
                       buttons: [...document.querySelectorAll('button, a.btn')].map(b=>b.innerText.trim()),
                       forms: [...document.querySelectorAll('form')].map(f=>f.getAttribute('action'))})"""
        )
        page.screenshot(path=str(OUT / f"{cid}-packet-1440.png"), full_page=True)
        out["packet_overflow_1440"] = overflow(page)
        for sub in ("preview.pdf", "download"):
            r = page.evaluate(
                """async ([cid, sub]) => {
              const res = await fetch(`/cases/${cid}/packet/${sub}`, {redirect:'follow'});
              const ct = res.headers.get('content-type');
              const t = ct && ct.includes('text') ? (await res.text()).replace(/\\s+/g,' ').slice(0,400) : `[${ct}]`;
              return {status: res.status, ct, body: t};
            }""",
                [cid, sub],
            )
            out[sub] = r
        out["weberrors"] = errs
        b.close()
    save(f"08-packet-{actor}-{cid}", out)
    print(json.dumps({k: v for k, v in out.items() if k in ("packet_status", "preview.pdf", "download")}, indent=2)[:1200])


def step_shots(cid):
    with sync_playwright() as p:
        b, c, errs = ctx(p)
        page = c.new_page()
        out = {}
        for w, h in ((1440, 900), (390, 844)):
            page.set_viewport_size({"width": w, "height": h})
            goto(page, f"/cases/{cid}")
            page.wait_for_timeout(300)
            out[f"{w}"] = overflow(page)
            page.screenshot(path=str(OUT / f"{cid}-final-{w}.png"), full_page=True)
        out["weberrors"] = errs
        b.close()
    save(f"09-shots-{cid}", out)
    print(cid, json.dumps(out, indent=2)[:900])


if __name__ == "__main__":
    fn = globals()["step_" + sys.argv[1].replace("-", "_")]
    fn(*sys.argv[2:])
