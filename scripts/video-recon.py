"""Walk the pitch video's demo beats against a running app with fresh seeded state: screenshot each beat at 1440x900
and dump each screen's visible text, so narration can echo the exact on-screen wording.

Usage: .venv/bin/python scripts/video-recon.py <base_url> <out_dir>
"""
import sys
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

base, out = sys.argv[1].rstrip("/"), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
n = 0


def shot(page, name, full=False):
    global n
    n += 1
    page.screenshot(path=str(out / f"{n:02d}-{name}.png"), full_page=full)
    (out / f"{n:02d}-{name}.txt").write_text(page.locator("body").inner_text())


def act_as(page, who):
    page.locator(f'.me button[value="{who}"]').click()
    page.wait_for_load_state("networkidle")


with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1440, "height": 900})
    page.on("pageerror", lambda e: print("JS error:", e))

    # Board, then every candidate case as the coordinator, before anything changes.
    page.goto(base + "/")
    shot(page, "board")
    shot(page, "board-full", full=True)
    for case in ["kowalchuk", "whitfield", "deng", "singh", "rosco", "tremblay"]:
        page.goto(f"{base}/cases/{case}")
        shot(page, f"case-{case}")
        shot(page, f"case-{case}-full", full=True)

    # Expand every fold on the in-chair case so the checks, citations and fix reasons are visible.
    page.goto(base + "/cases/kowalchuk")
    page.evaluate("document.querySelectorAll('details').forEach(d => d.open = true)")
    shot(page, "case-kowalchuk-open-full", full=True)
    page.goto(base + "/cases/deng")
    page.evaluate("document.querySelectorAll('details').forEach(d => d.open = true)")
    shot(page, "case-deng-open-full", full=True)

    # In the chair: take the film and the perio chart from the board hero.
    page.goto(base + "/")
    hero = page.locator(".start-chair")
    hero.get_by_role("button", name="Mark taken (demo)").first.click()
    shot(page, "board-first-taken")
    page.locator(".start-chair").get_by_role("button", name="Mark taken (demo)").first.click()
    expect(page.locator(".done-note")).to_have_text("Nothing left to take. The patient can go.")
    shot(page, "board-chair-closed")

    # Dentist view: pre-filled criteria, confirm, review and sign.
    act_as(page, "dentist")
    page.goto(base + "/")
    shot(page, "dentist-board")
    page.goto(base + "/cases/kowalchuk")
    shot(page, "kowalchuk-dentist")
    shot(page, "kowalchuk-dentist-full", full=True)
    calls = page.locator(".crit-group-call .crit")
    for i in range(calls.count()):
        calls.nth(i).locator('label:has-text("Met")').first.click()
    page.locator("[data-crit-count]").click()
    shot(page, "kowalchuk-criteria-recorded")
    page.get_by_role("link", name="Review and sign").first.click()
    page.wait_for_load_state("networkidle")
    shot(page, "kowalchuk-packet-review")
    shot(page, "kowalchuk-packet-review-full", full=True)
    page.get_by_role("button", name="Sign as Dr. Priya Lau (ON-48213)").click()
    shot(page, "kowalchuk-signed")

    # Coordinator: packet ready to send, then sent.
    act_as(page, "coordinator")
    page.goto(base + "/cases/kowalchuk")
    shot(page, "kowalchuk-ready-to-send")
    shot(page, "kowalchuk-ready-to-send-full", full=True)
    page.get_by_role("button", name="Mark as sent").click()
    shot(page, "kowalchuk-with-sunlife")
    page.goto(base + "/")
    shot(page, "board-after-send")

    # Decision back on the same case: record approval, then book.
    page.goto(base + "/cases/kowalchuk")
    page.get_by_text("Decision arrived? Record it").click()
    shot(page, "kowalchuk-record-decision")
    page.locator('.choice-cards label:has-text("Approved")').click()
    page.get_by_role("button", name="Record decision").click()
    shot(page, "kowalchuk-approved")
    shot(page, "kowalchuk-approved-full", full=True)
    page.get_by_role("button", name="Mark as booked").click()
    shot(page, "kowalchuk-booked")

    # Denied, seeded: resubmit or reconsider, with the deadline.
    page.goto(base + "/cases/marchand")
    page.evaluate("document.querySelectorAll('details').forEach(d => d.open = true)")
    shot(page, "marchand-denied")
    shot(page, "marchand-denied-full", full=True)

    # Owner view, and the model page.
    page.goto(base + "/results")
    shot(page, "results")
    shot(page, "results-full", full=True)
    page.goto(base + "/model")
    shot(page, "model")
    shot(page, "model-full", full=True)
    page.goto(base + "/")
    shot(page, "board-end")
    b.close()
print("recon ok")
