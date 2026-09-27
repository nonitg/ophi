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
    page.locator(f'.me button[value="{who}"]').click()
    page.wait_for_load_state("networkidle")


def on_step(page, label):
    expect(page.locator('.stp[aria-current="step"] .stp-label')).to_have_text(label)


with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1440, "height": 900})
    page.on("pageerror", lambda e: print("JS error:", e))

    # In the chair: take Teresa's perio chart and film from the board hero; her card moves on by itself.
    page.goto(base + "/")
    hero = page.locator(".start-chair")
    expect(hero).to_contain_text("Before Teresa leaves")
    shot(page, "board-in-the-chair")
    hero.get_by_role("button", name="Mark taken (demo)").first.click()
    expect(page.locator(".done-note")).to_have_text("Taken. Ophi checked the chart again.")
    page.locator(".start-chair").get_by_role("button", name="Mark taken (demo)").first.click()
    expect(page.locator(".done-note")).to_have_text("Nothing left to take. The patient can go.")
    expect(page.locator('section[aria-labelledby="col-dentist"]')).to_contain_text("Teresa Kowalchuk")
    shot(page, "board-chair-closed")

    # New films change the request, not the note: Laya's note reading still pre-fills Teresa's criteria.
    act_as(page, "dentist")
    page.goto(base + "/cases/kowalchuk")
    expect(page.locator(".crit.is-pre .laya").first).to_be_visible()
    shot(page, "kowalchuk-prefilled")
    act_as(page, "coordinator")

    # Coordinator confirms the chart note on Tremblay: chart work done, case moves to the dentist.
    page.goto(base + "/cases/tremblay")
    page.get_by_role("button", name="Yes", exact=True).click()
    expect(page.locator(".done-note")).to_have_text("Chart note confirmed.")
    on_step(page, "Dentist review")
    shot(page, "tremblay-quote-confirmed")

    # Dentist's board, then criteria in one pass.
    act_as(page, "dentist")
    page.goto(base + "/")
    expect(page.locator("h1")).to_contain_text("waiting on you")
    shot(page, "dentist-board")
    page.goto(base + "/cases/tremblay")
    calls = page.locator(".crit-group-call .crit")
    assert calls.count() > 0 and calls.locator("input:checked").count() == 0, "Ophi must not pre-fill what it can't read"
    assert page.locator(".crit.is-pre input:checked").count() > 0, "Ophi pre-fills what the chart and note agree on"
    for i in range(calls.count()):  # the dentist answers what Ophi left to her, and confirms the rest
        calls.nth(i).locator('label:has-text("Met")').first.click()
    page.get_by_role("button", name="Confirm answers").click()
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
    on_step(page, "With Sun Life")
    shot(page, "fontaine-sent")

    page.goto(base + "/cases/park")
    page.get_by_text("Decision arrived? Record it").click()
    page.locator('.choice-cards label:has-text("Approved")').click()
    page.get_by_role("button", name="Record decision").click()
    on_step(page, "Decision back")
    expect(page.locator(".now-head h2")).to_have_text("Book the crown")
    shot(page, "park-approved")

    page.goto(base + "/cases/nguyen")
    page.fill('input[name="on"]', "2026-09-29")
    page.get_by_role("button", name="Mark as booked").click()
    expect(page.locator(".now-head h2")).to_contain_text("Crown booked for")
    shot(page, "nguyen-booked")

    page.goto(base + "/cases/marchand")
    page.get_by_role("button", name="Start resubmission").click()
    on_step(page, "Dentist review")
    expect(page.locator(".attempts")).to_contain_text("Attempt 1")
    shot(page, "marchand-resubmitted")

    # Recover: log a call.
    page.goto(base + "/recover")
    first = page.locator(".call").first
    first.get_by_text("Add a note").click()
    first.locator('input[name="note"]').fill("Wants it done before year end")
    first.get_by_role("button", name="Rebooking").click()
    expect(page.locator(".done-note")).to_have_text("Follow-up saved.")
    shot(page, "recover-followup")

    # Test run: Singh has no periapical on file. Skip the gap and walk the rest of the flow.
    page.goto(base + "/cases/singh")
    page.once("dialog", lambda d: d.accept())  # the skip asks first
    page.get_by_role("button", name="Skip gaps to test").click()
    expect(page.locator(".test-run")).to_be_visible()
    on_step(page, "Dentist review")
    shot(page, "singh-skipped")
    page.get_by_role("button", name="View as Dr. Priya Lau").first.click()
    page.wait_for_load_state("networkidle")
    calls = page.locator(".crit-group-call .crit")
    for i in range(calls.count()):
        calls.nth(i).locator('label:has-text("Met")').first.click()
    page.get_by_role("button", name="Confirm answers").click()
    page.get_by_role("link", name="Review and sign").first.click()
    expect(page.locator(".test-run")).to_be_visible()
    page.get_by_role("button", name="Sign test run as Dr. Priya Lau (ON-48213)").click()
    expect(page.locator(".done-note")).to_have_text("Test packet signed.")
    shot(page, "singh-test-signed")
    act_as(page, "coordinator")
    page.goto(base + "/cases/singh")
    expect(page.locator(".substeps")).to_contain_text("No download in a test run.")
    page.get_by_role("button", name="Mark as sent").click()
    on_step(page, "With Sun Life")
    page.get_by_text("Decision arrived? Record it").click()
    page.locator('.choice-cards label:has-text("Approved")').click()
    page.get_by_role("button", name="Record decision").click()
    page.get_by_role("button", name="Mark as booked").click()
    expect(page.locator(".now-head h2")).to_contain_text("Crown booked for")
    shot(page, "singh-test-booked")
    assert page.request.get(base + "/cases/singh/packet/download").status == 409, "a test run's packet must never download"

    page.goto(base + "/")
    shot(page, "board-after")
    page.goto(base + "/results")
    shot(page, "results-after")
    b.close()
print("flow ok")
