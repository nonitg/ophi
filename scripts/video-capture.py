"""Capture the pitch video's demo states as 2x stills, each with a JSON of named element boxes, so the video can
animate zooms, a cursor and highlights over real screens. Teresa Kowalchuk is the hero case; the recorded
ABELDent PMS supplies the states the PMS sync produces (sent and answered without anyone in Ophi).

Usage: .venv/bin/python scripts/video-capture.py <demo_url> <recorded_url> <out_dir>
Serve with scripts/video-serve.py (fixed morning clock, throwaway state); scripts/video-capture.sh does all of it.
"""
import json
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

demo, recorded, out = sys.argv[1].rstrip("/"), sys.argv[2].rstrip("/"), Path(sys.argv[3])
out.mkdir(parents=True, exist_ok=True)
VW, VH = 1440, 900
PAST_ID = "PA-SYN-300454"  # a past crown denied for a missing radiograph, resent with it, then approved
missing: list[str] = []
base = demo


def box(page, loc, full):
    try:
        b = loc.first.bounding_box(timeout=1500)
    except Exception:
        b = None
    if not b:
        return None
    dy = page.evaluate("scrollY") if full else 0
    return {"x": round(b["x"], 1), "y": round(b["y"] + dy, 1), "w": round(b["width"], 1), "h": round(b["height"], 1)}


def save(page, slug, boxes=None, click=None, full=None):
    """Viewport shot, plus a full-page shot when the page is taller than the viewport."""
    boxes = boxes or {}
    page.wait_for_timeout(300)  # let transitions settle
    page.screenshot(path=str(out / f"{slug}.png"))
    meta = {"url": page.url.split("127.0.0.1")[-1].split("/", 1)[-1], "scrollY": page.evaluate("scrollY"),
            "viewport": {"w": VW, "h": VH},
            "boxes": {k: box(page, v, False) for k, v in boxes.items()},
            "click": box(page, click, False) if click is not None else None}
    meta["url"] = "/" + meta["url"]
    for k, v in meta["boxes"].items():
        if v is None:
            missing.append(f"{slug}:{k}")
    height = page.evaluate("document.documentElement.scrollHeight")
    if full or (full is None and height > VH + 20):
        page.screenshot(path=str(out / f"{slug}-full.png"), full_page=True)
        meta["full"] = {"height": height, "boxes": {k: box(page, v, True) for k, v in boxes.items()},
                        "click": box(page, click, True) if click is not None else None}
    (out / f"{slug}.json").write_text(json.dumps(meta, indent=1))
    print("saved", slug)


def go(page, path):
    page.goto(base + path)
    page.wait_for_load_state("networkidle")


def act_as(page, who):
    page.locator(f'.me button[value="{who}"]').click()
    page.wait_for_load_state("networkidle")


def scroll_to(page, loc, top=90):
    loc.first.scroll_into_view_if_needed()
    page.evaluate("([el, top]) => window.scrollTo(0, el.getBoundingClientRect().top + scrollY - top)",
                  [loc.first.element_handle(), top])


def board_boxes(page):
    b = {f"col_{i}": page.locator(".col-head").nth(i) for i in range(page.locator(".col-head").count())}
    b.update({
        "banner": page.locator(".demo"), "headline": page.locator(".board-head h1"),
        "hero_card": page.locator(".start-chair"), "hero_title": page.locator(".start-chair .start-title"),
        "mark_taken_pa": page.locator(".start-chair").get_by_role("button", name="Mark taken (demo)").first,
        "mark_taken_perio": page.locator(".start-chair").get_by_role("button", name="Mark taken (demo)").nth(1),
        "teresa_card": page.locator(".tile", has_text="Teresa Kowalchuk"),
        "teresa_risk": page.locator(".tile", has_text="Teresa Kowalchuk").locator(".tile-risk"),
        "col_with_sun_life": page.locator(".col", has_text="With Sun Life").locator(".col-head"),
        "okafor_card": page.locator(".tile", has_text="Chidi Okafor"),
        "park_card": page.locator(".tile", has_text="Min-jun Park"),
        "nav": page.locator(".nav"), "view_as": page.locator(".me"), "toast": page.locator(".done-note"),
    })
    return b


def case_boxes(page):
    return {
        "banner": page.locator(".demo"), "title": page.locator(".case-title"), "tx": page.locator(".case-tx"),
        "stepper": page.locator(".stepper"), "now": page.locator(".now").first,
        "now_head": page.locator(".now-head").first, "now_lead": page.locator(".now-lead").first,
        "risk_line": page.locator(".risk-line").first, "risk_levels": page.locator(".risk-levels").first,
        "toast": page.locator(".done-note"), "activity": page.get_by_text("Activity").first,
        "pms_line": page.locator(".pms-line").first, "letter_form": page.locator(".letter-form").first,
    }


with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": VW, "height": VH}, device_scale_factor=2)
    page = ctx.new_page()
    page.on("pageerror", lambda e: print("JS error:", e))

    # 01-02 board, front desk.
    go(page, "/")
    b = board_boxes(page)
    save(page, "01-board", b, click=b["mark_taken_pa"])
    save(page, "20-board-hero", {k: b[k] for k in ("headline", "hero_card", "teresa_card")}, full=False)
    b["mark_taken_pa"].hover()
    save(page, "02-board-hover-mark-taken", b, click=b["mark_taken_pa"], full=False)
    page.mouse.move(5, 5)

    # 03-05 Teresa's case, desk view.
    go(page, "/cases/kowalchuk")
    case = case_boxes(page)
    case.update({
        "risk_left": page.get_by_text("Most of what's left"),
        "fix_1": page.locator(".gap", has_text="Take a periapical of #46"),
        "fix_1_effect": page.get_by_text("Lowers denial risk the most"),
        "fix_1_age": page.locator(".gap", has_text="Take a periapical of #46").get_by_text("34 months old"),
        "fix_2": page.locator(".gap", has_text="6-site periodontal chart"),
        "fix_3": page.get_by_text("Add a narrative for the dentist to approve."),
        "reqs_fold": page.locator("details", has_text="CDCP requirements").last,
        "chart_fold": page.locator("details", has_text="What Ophi read in the chart").last,
    })
    save(page, "03-case-teresa", case, full=True)
    save(page, "21-case-banner", {"banner": case["banner"], "title": case["title"]}, full=False)

    reqs = page.locator("details", has_text="CDCP requirements").last
    reqs.evaluate("d => d.open = true")
    scroll_to(page, reqs, top=70)
    rows = page.locator(".req")
    rb = {"reqs_fold": reqs, "reqs_count": reqs.get_by_text("7 of 12 documented")}
    for i in range(rows.count()):
        rb[f"req_{i}"] = rows.nth(i)
    rb.update({
        "req_pa": page.locator(".req", has_text="Dated periapical radiograph"),
        "req_bw": page.locator(".req", has_text="Dated bitewing radiographs"),
        "req_perio": page.locator(".req", has_text="Dated complete periodontal chart"),
        "req_frequency": page.locator(".req", has_text="No CDCP crown on this tooth"),
        "req_extensively": page.locator(".req", has_text="extensively restored"),
        "citation_matrix_pa": page.locator(".req", has_text="Dated periapical radiograph").get_by_text("PA+BW (R&L) <=12mo").first,
        "citation_row_guide_635": page.locator(".req").get_by_text("Guide 6.3.5 Crowns", exact=True).first,
        "citation_grid_96mo": page.locator(".req", has_text="No CDCP crown on this tooth").get_by_text("Grid Schedule B").first,
    })
    save(page, "04-case-teresa-requirements", rb, full=True)

    go(page, "/cases/kowalchuk")
    gap1 = page.locator(".gap", has_text="Take a periapical of #46")
    try:
        gap1.locator("details").first.evaluate("d => d.open = true")
    except Exception:
        missing.append("05:why-fold")
    fix = dict(case)
    fix.update({"fix_1": gap1, "fix_1_why": gap1.locator("details").first,
                "fix_1_why_text": gap1.get_by_text("673 days past the 12 months").first,
                "fix_1_rule": gap1.get_by_text("Required by").first,
                "fix_1_effect": page.get_by_text("Lowers denial risk the most"),
                "fix_2": page.locator(".gap", has_text="6-site periodontal chart")})
    page.evaluate("window.scrollTo(0, 0)")
    save(page, "05-case-teresa-fix-plan", fix, click=gap1.get_by_role("button", name="Mark taken (demo)"))

    # 06-07 chair captures from the board hero.
    go(page, "/")
    page.locator(".start-chair").get_by_role("button", name="Mark taken (demo)").first.click()
    page.wait_for_load_state("networkidle")
    b = board_boxes(page)
    b["mark_taken_perio"] = b.pop("mark_taken_pa")  # the PA is taken; the perio chart's button is the one left
    save(page, "06-board-first-taken", b, click=b["mark_taken_perio"])
    page.locator(".start-chair").get_by_role("button", name="Mark taken (demo)").first.click()
    expect(page.locator(".done-note")).to_have_text("Nothing left to take. The patient can go.")
    b = board_boxes(page)
    b["col_dentist_review"] = page.locator(".col", has_text="Dentist review").locator(".col-head")
    save(page, "07-board-chair-closed", b)

    # 08-10 dentist.
    act_as(page, "dentist")
    go(page, "/")
    b = board_boxes(page)
    save(page, "08-board-dentist", b, click=b["teresa_card"])
    go(page, "/cases/kowalchuk")
    crit = {
        "banner": page.locator(".demo"), "title": page.locator(".case-title"),
        "header": page.get_by_text("need your call").first, "now_lead": page.locator(".now-lead").first,
        "group_call": page.locator(".crit-group-call"),
        "your_call_row_surfaces": page.locator(".crit", has_text="needs 5 to count as heavily filled"),
        "surfaces_evidence": page.get_by_text("needs 5 to count as heavily filled").first,
        "sugg_first": page.locator(".crit-sugg").first, "pre_row_first": page.locator(".crit.is-pre").first,
        "prefilled_group": page.locator(".crit-group").nth(1),
        "confirm_bar": page.locator(".crit-submit"), "confirm_button": page.locator("[data-crit-count]"),
    }
    calls = page.locator(".crit-group-call .crit")
    for i in range(calls.count()):
        crit[f"call_{i}"] = calls.nth(i)
    scroll_to(page, page.locator(".crit-group").first, top=70)
    save(page, "09-dentist-review", crit, click=crit["confirm_button"])
    for i in range(calls.count()):
        calls.nth(i).locator('label:has-text("Met")').first.click()
    save(page, "09b-dentist-calls-answered", crit, click=crit["confirm_button"], full=False)
    page.locator("[data-crit-count]").click()
    page.wait_for_load_state("networkidle")
    page.evaluate("window.scrollTo(0, 0)")
    sign_link = page.get_by_role("link", name="Review and sign").first
    save(page, "10-criteria-recorded", {"title": page.locator(".case-title"), "now": page.locator(".now").first,
                                        "review_and_sign": sign_link, "toast": page.locator(".done-note")}, click=sign_link)

    # 11-12 packet review and sign.
    sign_link.click()
    page.wait_for_load_state("networkidle")
    sign_btn = page.locator("button", has_text="Sign as").first
    pk = {"title": page.locator(".case-title"), "now": page.locator(".now").first, "pdf_frame": page.locator("iframe.pdf"),
          "packet_files": page.locator("ol.files"), "files_head": page.locator(".side-h").first, "sign_button": sign_btn}
    files = page.locator("ol.files li")
    for i in range(files.count()):
        pk[f"file_{i}"] = files.nth(i)
    save(page, "11-packet-review", pk, click=sign_btn)
    pdf = out / "11b-packet.pdf"
    pdf.write_bytes(page.request.get(base + "/cases/kowalchuk/packet/preview.pdf").body())
    subprocess.run(["pdftoppm", "-r", "200", "-png", str(pdf), str(out / "11b-packet-page")], check=True)
    pdf.unlink()
    sign_btn.click()
    page.wait_for_load_state("networkidle")
    save(page, "12-signed", {"title": page.locator(".case-title"), "now_head": page.locator(".now-head").first,
                             "toast": page.locator(".done-note"), "packet_files": page.locator("ol.files")})

    # 13-14 staff send, then Ophi watches for Sun Life's answer.
    act_as(page, "coordinator")
    go(page, "/cases/kowalchuk")
    sent = page.get_by_role("button", name="Mark as sent")
    save(page, "13-send-to-sun-life", {
        **case_boxes(page), "download": page.get_by_text("Download packet (.zip)"), "pms_step": page.get_by_text("In your PMS").first,
        "mark_sent": sent}, click=sent)
    sent.click()
    page.wait_for_load_state("networkidle")
    page.evaluate("window.scrollTo(0, 0)")
    wait = case_boxes(page)
    wait.update({"turnaround": page.get_by_text("Sun Life processes most requests within").first,
                 "decision_reveal": page.get_by_text("Decision arrived? Record it").first,
                 "read_letter": page.get_by_role("button", name="Read the letter")})
    save(page, "14a-case-with-sun-life", wait)
    go(page, "/")
    b = board_boxes(page)
    b["teresa_card"] = page.locator(".col", has_text="With Sun Life").locator(".tile", has_text="Teresa Kowalchuk")
    save(page, "14-board-with-sun-life", b)
    # A request past Sun Life's usual turnaround: Ophi turns the wait into a task.
    go(page, "/cases/okafor")
    od = case_boxes(page)
    od.update({"sent_ago": page.get_by_text("Sent 8 days ago").first,
               "past_turnaround": page.get_by_text("Past Sun Life's usual 7 days").first,
               "mailbox_line": page.get_by_text("Check your CDAnet mailbox").first,
               "read_letter": page.get_by_role("button", name="Read the letter"),
               "letter_input": page.locator('input[name="letter"]').first})
    save(page, "14c-okafor-overdue", od)

    # 15-17 decision back: approved, then booked.
    go(page, "/cases/kowalchuk")
    page.get_by_text("Decision arrived? Record it").click()
    page.locator('.choice-cards label:has-text("Approved")').click()
    rec = page.get_by_role("button", name="Record decision")
    scroll_to(page, page.locator(".choice-cards"), top=200)
    save(page, "15-record-decision", {"choices": page.locator(".choice-cards"), "approved": page.locator('.choice-cards label:has-text("Approved")'),
                                      "reason_field": page.locator(".decision-form .reason"), "record": rec,
                                      "form": page.locator(".decision-form").first, "letter_form": page.locator(".letter-form").first}, click=rec)
    rec.click()
    page.wait_for_load_state("networkidle")
    page.evaluate("window.scrollTo(0, 0)")
    booked = page.get_by_role("button", name="Mark as booked")
    save(page, "16-book-the-crown", {**case_boxes(page), "payer_line": page.get_by_text("Sun Life approved it").first,
                                     "mark_booked": booked}, click=booked)
    booked.click()
    page.wait_for_load_state("networkidle")
    save(page, "17-crown-booked", {**case_boxes(page), "booked_line": page.get_by_text("Crown booked").first})
    go(page, "/")
    b = board_boxes(page)
    save(page, "17b-board-booked", b)

    # 18 denied, seeded (Sun Life's letter named no reason).
    go(page, "/cases/marchand")
    page.evaluate("window.scrollTo(0, 0)")
    save(page, "18-denied-marchand", {
        **case_boxes(page), "payer_line": page.get_by_text("Sun Life denied it").first,
        "resubmit_option": page.locator(".option").first, "reason_note": page.locator(".option .note-warn").first,
        "reason_form": page.locator(".option .letter-form").first,
        "reconsider_block": page.locator(".option", has_text="Ask for reconsideration"),
        "reconsider_by": page.get_by_text("By Nov 2, 2026").first})

    # 19 results; 22 past denials call list; 23-24 past outcomes; 25 rules check.
    go(page, "/results")
    save(page, "19-results", {"headline": page.locator("h1").first, "caught": page.get_by_text("taken while the patient").first,
                              "in_progress": page.get_by_text("of crown treatment is moving").first}, full=True)
    go(page, "/recover")
    first = page.locator(".call").first
    row_id = first.get_attribute("id")
    rc = {"headline": page.locator("h1").first, "lede": page.locator(".lede").first, "first_call": first,
          "first_why": first.locator(".call-why").first, "first_missing": first.locator(".call-why").nth(1),
          "first_actions": first.locator(".call-act").first, "left_message": first.get_by_role("button", name="Left a message"),
          "call_back": first.locator(".call-when").first, "draft_script": first.get_by_role("button", name="Draft what to say")}
    save(page, "22-recover", rc, full=True)
    try:  # a follow-up with a call-back date: the list keeps the history and brings the call back when it's due
        first.locator('.call-when input[type="date"]').first.fill("2026-09-18")
    except Exception:
        missing.append("22b:call-back-date")
    first.get_by_role("button", name="Left a message").click()
    page.wait_for_load_state("networkidle")
    row = page.locator(f"#{row_id}")
    save(page, "22b-recover-followup", {"headline": page.locator("h1").first, "row": row, "call_status": row.locator(".call-status"),
                                        "call_due": row.locator(".call-due"), "toast": page.locator(".done-note")}, full=True)
    go(page, "/outcomes")
    save(page, "23-past-outcomes", {"headline": page.locator("h1, h2").first, "filters": page.locator(".plist-filter, .filters, nav").first,
                                    "first_row": page.locator(".plist-link").first,
                                    "count_resent": page.get_by_text("Resent → approved").first}, full=True)
    go(page, f"/past/{PAST_ID}")
    save(page, "24-past-request", {"title": page.locator("h1").first, "denied_line": page.get_by_text("Sun Life denied it").first,
                                   "resent_line": page.get_by_text("Resent").first, "approved_line": page.get_by_text("Sun Life approved it").first,
                                   "sent_docs": page.get_by_text("What the clinic sent").first}, full=True)
    go(page, "/rules")
    if page.get_by_text("Not checked yet").count():
        page.get_by_role("button", name="Check now").click()
        page.wait_for_load_state("networkidle")
        for _ in range(60):  # the check fetches the CDCP pages in the background
            go(page, "/rules")
            if not page.get_by_text("Checking").count() and not page.get_by_text("Not checked yet").count():
                break
            page.wait_for_timeout(2000)
    save(page, "25-rules-check", {"headline": page.locator("h1").first, "lede": page.locator(".lede, p").first,
                                  "waiting": page.get_by_text("Waiting for review").first,
                                  "last_check": page.get_by_text("Rules checked against").first,
                                  "sources": page.locator("table").first, "check_now": page.get_by_role("button", name="Check now")})

    # 30-34 the recorded ABELDent PMS: the sync marks requests sent and reads Sun Life's answers itself.
    base = recorded
    go(page, "/")
    b = board_boxes(page)
    b.update({"cherski_card": page.locator(".tile", has_text="Mathew Cherski"), "goertsen_card": page.locator(".tile", has_text="Susan Goertsen"),
              "randal_card": page.locator(".tile", has_text="Kris Randal"), "yokoyama_card": page.locator(".tile", has_text="Sumi Yokoyama"),
              "col_decision_back": page.locator(".col", has_text="Decision back").locator(".col-head")})
    save(page, "30-rec-board", b)
    for slug, cid, extra in (
        ("31-rec-paper-answer", "abeldent_160", {"paper_lead": "Sun Life will answer this one by mail", "carrier_ref": "Sun Life's reference"}),
        ("32-rec-waiting", "abeldent_164", {"turnaround": "Sun Life processes most requests within"}),
        ("33-rec-denied-eob", "abeldent_158", {"payer_line": "Sun Life denied it", "reconsider_by": "By Nov 16, 2026",
                                               "abeldent_sent": "ABELDent marked it sent", "abeldent_decision": "ABELDent recorded Sun Life's decision"}),
        ("34-rec-approved", "abeldent_162", {"payer_line": "Sun Life approved it", "abeldent_decision": "ABELDent recorded Sun Life's decision"}),
    ):
        go(page, f"/cases/{cid}")
        bx = case_boxes(page)
        bx.update({k: page.get_by_text(v).first for k, v in extra.items()})
        save(page, slug, bx, full=True)
    browser.close()

print("MISSING BOXES:", ", ".join(missing) if missing else "none")
