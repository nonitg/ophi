"""Drive the whole preauthorization life in a browser against a running app with fresh seeded state,
as the coordinator and the dentist, screenshotting each step and failing loudly on any broken step.

Usage: .venv/bin/python scripts/app-flow.py <base_url> <out_dir>
"""
import sys
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

base, out = sys.argv[1].rstrip("/"), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
n = 0


def shot(page, name):
    global n
    n += 1
    page.screenshot(path=str(out / f"{n:02d}-{name}.png"), full_page=True)


def act_as(page, who):
    page.select_option("#actor-select", who)
    page.wait_for_load_state("networkidle")


with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1440, "height": 900})
    page.on("pageerror", lambda e: print("JS error:", e))

    # Coordinator confirms the note quote on Tremblay: chart work done, case moves to the dentist.
    page.goto(base + "/cases/tremblay")
    page.get_by_role("button", name="Confirm quote").click()
    expect(page.locator(".done-note")).to_have_text("Chart quote confirmed.")
    expect(page.locator(".stage-tag")).to_have_text("Dentist review")
    shot(page, "tremblay-quote-confirmed")

    # Dentist's worklist, then criteria in one pass.
    act_as(page, "dentist")
    page.goto(base + "/")
    expect(page.locator("h1")).to_contain_text("waiting on you")
    shot(page, "dentist-worklist")
    page.goto(base + "/cases/tremblay")
    page.get_by_role("button", name="Set the rest to Met").click()
    flagged = page.locator(".crit[data-needs-look]")
    assert flagged.count() > 0 and flagged.locator("input:checked").count() == 0, "bulk Met must skip rows Ophi flags"
    for i in range(flagged.count()):  # the dentist reads each flagged row and answers it herself
        flagged.nth(i).locator('label:has-text("Met")').first.click()
    page.get_by_role("button", name="Record answers").click()
    expect(page.locator(".done-note")).to_have_text("Criteria recorded.")
    shot(page, "tremblay-criteria-recorded")

    # Review and sign; the next case on the dentist's pile is offered.
    page.get_by_role("link", name="Review and sign").first.click()
    page.get_by_role("button", name="Sign as Dr. Priya Lau (ON-48213)").click()
    expect(page.locator(".done-note")).to_have_text("Packet signed.")
    expect(page.locator(".next-up")).to_be_visible()
    shot(page, "tremblay-signed-next-up")

    # Coordinator sends Fontaine, records Park's decision, books Nguyen, resubmits Marchand.
    act_as(page, "coordinator")
    page.goto(base + "/cases/fontaine")
    page.get_by_role("button", name="Mark as sent").click()
    expect(page.locator(".stage-tag")).to_have_text("Waiting on Sun Life")
    shot(page, "fontaine-sent")

    page.goto(base + "/cases/park")
    page.locator('.choice-cards label:has-text("Approved")').click()
    page.fill('textarea[name="reason"]', "")
    page.get_by_role("button", name="Record decision").click()
    expect(page.locator(".stage-tag")).to_have_text("Book the crown")
    shot(page, "park-approved")

    page.goto(base + "/cases/nguyen")
    page.fill('input[name="on"]', "2026-09-29")
    page.get_by_role("button", name="Mark as booked").click()
    expect(page.locator(".stage-tag")).to_have_text("Booked")
    shot(page, "nguyen-booked")

    page.goto(base + "/cases/marchand")
    page.get_by_role("button", name="Start resubmission").click()
    expect(page.locator(".stage-tag")).to_have_text("Dentist review")
    expect(page.locator(".attempts")).to_contain_text("Attempt 1")
    shot(page, "marchand-resubmitted")

    # Recover: log a call.
    page.goto(base + "/recover")
    first = page.locator(".call").first
    first.locator('input[name="note"]').fill("Wants it done before year end")
    first.get_by_role("button", name="Rebooking").click()
    expect(page.locator(".done-note")).to_have_text("Follow-up saved.")
    shot(page, "recover-followup")

    page.goto(base + "/")
    shot(page, "worklist-after")
    page.goto(base + "/results")
    shot(page, "results-after")
    b.close()
print("flow ok")
