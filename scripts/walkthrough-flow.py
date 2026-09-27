"""Drive the live pitch walk-through for Jinay Patel (mocks/pms/walkthrough/patel.yaml) in a browser, from the chair
to the crown booked, screenshotting each step and failing loudly on any broken one. The screenshots double as the
presenter's click guide.

Usage: .venv/bin/python scripts/walkthrough-flow.py <board_url> <out_dir>
  board_url: a fresh server, e.g. scripts/demo-deployed-serve.sh -> http://127.0.0.1:8802/demo-4ajsmu
"""
import re
import sys
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

base, out = sys.argv[1].rstrip("/"), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
case = base + "/cases/patel"
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

    # 1. In the chair: the board opens on Jinay. Take the PA and the perio chart before he leaves.
    page.goto(base)
    hero = page.locator(".start-chair")
    expect(hero).to_contain_text("Before Jinay leaves")
    shot(page, "board-jinay-in-the-chair")
    page.goto(case)
    shot(page, "case-in-the-chair")
    page.goto(base)
    hero.get_by_role("button", name="Mark taken (demo)").first.click()
    expect(page.locator(".done-note")).to_have_text("Taken. Ophi checked the chart again.")
    page.locator(".start-chair").get_by_role("button", name="Mark taken (demo)").first.click()
    expect(page.locator(".done-note")).to_have_text("Nothing left to take. The patient can go.")
    shot(page, "board-chair-closed")

    # 2. Paperwork: Ophi swaps the retired lab code itself; the coordinator confirms the plan quote from the note.
    page.goto(case)
    on_step(page, "Paperwork")
    shot(page, "case-paperwork")
    page.get_by_role("button", name="Apply it").first.click()
    page.goto(case)
    page.get_by_role("button", name="Yes", exact=True).click()
    expect(page.locator(".done-note")).to_have_text("Chart note confirmed.")
    on_step(page, "Dentist review")
    shot(page, "case-paperwork-done")

    # 3. Dentist review: confirm the pre-filled criteria, answer the rest from the film, sign the packet.
    act_as(page, "dentist")
    page.goto(case)
    assert page.locator(".crit.is-pre input:checked").count() > 0, "Ophi pre-fills what the chart and note agree on"
    shot(page, "case-dentist-prefilled")
    calls = page.locator(".crit-group-call .crit")
    for i in range(calls.count()):
        calls.nth(i).locator('label:has-text("Met")').first.click()
    page.locator("[data-crit-count]").click()
    expect(page.locator(".done-note")).to_have_text("Criteria recorded.")
    page.get_by_role("link", name="Review and sign").first.click()
    shot(page, "packet-before-signing")
    page.get_by_role("button", name=re.compile(r"^Sign as Dr\. Terry Ackerman")).click()
    expect(page.locator(".done-note")).to_have_text("Packet signed.")
    shot(page, "packet-signed")

    # 4. Ready to send -> with Sun Life -> approved -> booked.
    act_as(page, "coordinator")
    page.goto(case)
    on_step(page, "Ready to send")
    shot(page, "case-ready-to-send")
    page.get_by_role("button", name="Mark as sent").click()
    on_step(page, "With Sun Life")
    shot(page, "case-with-sun-life")
    page.get_by_text("Decision arrived? Record it").click()
    page.locator('.choice-cards label:has-text("Approved")').click()
    page.get_by_role("button", name="Record decision").click()
    on_step(page, "Decision back")
    expect(page.locator(".now-head h2")).to_have_text("Book the crown")
    shot(page, "case-approved")
    page.get_by_role("button", name="Mark as booked").click()
    expect(page.locator(".now-head h2")).to_contain_text("Crown booked for")
    shot(page, "case-booked")

    page.goto(base)
    shot(page, "board-after")
    b.close()
print("walkthrough ok")
