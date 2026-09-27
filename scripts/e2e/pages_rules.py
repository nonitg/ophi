"""pages lane, part 4: the /rules approval gate. Nothing is approved — no draft is waiting, so every
POST below is refused by a guard before `approve()` could be reached."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pages_lib import BASE, OUT, Recorder, context, goto  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

out: dict = {}

with sync_playwright() as pw:
    browser, ctx = context(pw, "coordinator")
    page = ctx.new_page()
    rec = Recorder()
    rec.attach(page)

    # what each actor is offered on /rules
    for actor in ("coordinator", "dentist", None):
        c = ctx
        req = c.request
        headers = {"Cookie": f"actor={actor}"} if actor else {}
        r = req.get(f"{BASE}/rules", headers=headers)
        t = r.text()
        out[f"rules-{actor}"] = {
            "status": r.status,
            "has_use_button": "Use this rule update" in t,
            "has_check_now": "Check now" in t,
            "coordinator_notice": "puts rule updates into use" in t,
            "no_draft": "No rule update is waiting." in t,
        }

    # the gate: POST /rules/use, each guard in turn. No draft exists, so approve() is unreachable.
    req = ctx.request
    probes = [
        ("no actor cookie", {}, {"draft": "x", "draft_sha": "y"}),
        ("coordinator", {"Cookie": "actor=coordinator"}, {"draft": "x", "draft_sha": "y"}),
        ("bad actor cookie", {"Cookie": "actor=admin"}, {"draft": "x", "draft_sha": "y"}),
        ("dentist, wrong sha", {"Cookie": "actor=dentist"}, {"draft": "x", "draft_sha": "wrong"}),
        ("dentist, no fields", {"Cookie": "actor=dentist"}, {}),
    ]
    for name, h, form in probes:
        r = req.post(f"{BASE}/rules/use", headers=h, form=form, max_redirects=0)
        t = r.text()
        out[f"use-{name}"] = {
            "status": r.status, "loc": r.headers.get("location"),
            "msg": next((ln.strip() for ln in t.splitlines() if "rules-error" in ln or "Who is this" in ln
                         or "treating dentist" in ln), t[:160]).strip()[:220],
            "committed_marker": "rules_used" in (r.headers.get("location") or ""),
        }

    # the coordinator's /rules markup when a draft IS waiting: the ack form renders with no submit button.
    # Run the app's own app.js over exactly the markup rules.html emits for that branch.
    goto(page, rec, "/rules")
    errs: list[str] = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.evaluate(
        """() => {
          const d = document.createElement('div');
          d.innerHTML = `<form method="post" action="/rules/use" class="rules-use" data-ack-all>
            <input type="hidden" name="draft" value="draft-1"><input type="hidden" name="draft_sha" value="abc">
            <ul class="plain"><li><label class="rules-ack"><input type="checkbox" name="ack-0" required> <span>item</span></label></li></ul>
            <p class="small muted">Dr. Priya Lau puts rule updates into use.</p></form>`;
          document.querySelector('main').appendChild(d);
          const s = document.createElement('script'); s.src = '/static/app.js?probe=1';
          document.body.appendChild(s);
        }"""
    )
    page.wait_for_timeout(1200)
    out["coordinator_draft_js"] = {"pageerrors": errs}

    # and the dentist branch, to confirm the ack gate disables the button until every box is ticked
    page2 = ctx.new_page()
    errs2: list[str] = []
    page2.on("pageerror", lambda e: errs2.append(str(e)))
    page2.goto(BASE + "/rules", wait_until="load", timeout=30000)
    state = page2.evaluate(
        """() => {
          const d = document.createElement('div');
          d.innerHTML = `<form id="probe" method="post" action="/rules/use" class="rules-use" data-ack-all>
            <input type="hidden" name="draft" value="draft-1"><input type="hidden" name="draft_sha" value="abc">
            <ul class="plain">
              <li><label><input type="checkbox" name="ack-0" required> a</label></li>
              <li><label><input type="checkbox" name="ack-1" required> b</label></li></ul>
            <button class="btn btn-primary" type="submit" disabled>Use this rule update</button></form>`;
          document.querySelector('main').appendChild(d);
          const s = document.createElement('script'); s.src = '/static/app.js?probe=2';
          document.body.appendChild(s);
          return 'injected';
        }"""
    )
    page2.wait_for_timeout(1200)
    f = "#probe "
    seq = []
    seq.append(("initial", page2.locator(f + "button").is_disabled()))
    page2.locator(f + "input[name=ack-0]").check()
    seq.append(("one ticked", page2.locator(f + "button").is_disabled()))
    page2.locator(f + "input[name=ack-1]").check()
    seq.append(("both ticked", page2.locator(f + "button").is_disabled()))
    page2.locator(f + "input[name=ack-0]").uncheck()
    seq.append(("untick one", page2.locator(f + "button").is_disabled()))
    out["ack_gate"] = {"disabled_sequence": seq, "pageerrors": errs2}

    out["console"], out["failed"], out["bad_status"] = rec.console, rec.failed, rec.bad_status
    browser.close()

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "rules.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
