"""Drive the demo flow through the real UI with clicks, the way a presenter would, and assert each step.

Usage: .venv/bin/python scripts/app-flow.py <base_url> [out_dir]
Resets demo state first. Tremblay: confirm the proposed finding as the coordinator, switch to the dentist
from the case page, try an incomplete bulk record (inline message, no submit), record every criterion as
met, sign off, download, mark submitted, and check the queue shows it as submitted.
"""
import sys
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

base = sys.argv[1].rstrip("/")
out = Path(sys.argv[2]) if len(sys.argv) > 2 else None
if out:
    out.mkdir(parents=True, exist_ok=True)


def shot(page, name):
    if out:
        page.screenshot(path=str(out / f"flow-{name}.png"), full_page=False)


def step(msg):
    print(f"ok  {msg}")


with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_context(viewport={"width": 1440, "height": 900}, accept_downloads=True).new_page()
    page.goto(base + "/settings")
    page.once("dialog", lambda d: d.accept())
    page.get_by_role("button", name="Reset demo state").click()
    page.wait_for_url(base + "/")
    expect(page.locator(".stage.submitted .stage-n")).to_have_text("0")
    step("reset from Settings, queue shows 0 submitted")

    page.get_by_role("link", name="Yves Tremblay").click()
    expect(page.locator(".verdict h2")).to_have_text("Needs a human before it can go out.")
    expect(page.locator(".verdict .cell.pending")).to_have_count(1)
    page.locator(".step.hero").get_by_role("button", name="Confirm").click()
    expect(page.locator(".verdict .cell.pending")).to_have_count(0)
    step("coordinator confirmed the proposed finding; the hatched cell is gone")

    page.locator(".lane-foot").get_by_role("button", name="Switch to Dr. Priya Lau").click()
    expect(page.locator(".who select")).to_have_value("dentist")
    expect(page.locator("#assertions")).to_have_attribute("open", "")
    step("switched to the dentist from the case page; criteria form is open")

    page.locator(".assert-rows .assert-select").first.check()
    page.locator("#bulk-submit").click()
    expect(page.locator("#bulk-msg")).to_contain_text("Choose Met, Not met or N/A")
    expect(page.locator(".assert-row.is-missing")).to_have_count(1)
    step("incomplete bulk record stays on the page with an inline message")

    page.locator("#bulk-select-all").check()
    page.locator("[data-bulk-value=met]").click()
    shot(page, "1-criteria")
    page.locator("#bulk-submit").click()
    expect(page.locator(".verdict h2")).to_have_text("Documentation complete — ready for sign-off.")
    expect(page.locator(".verdict .pill")).to_have_text("Ready to sign")
    step("recorded every criterion as met; verdict is ready to sign")

    page.get_by_role("link", name="Review and sign").click()
    expect(page.locator(".rail-step.now .rail-top")).to_contain_text("Sign-off by Dr. Priya Lau")
    page.get_by_role("button", name="Sign off as Dr. Priya Lau").click()
    expect(page.locator(".sign-name")).to_have_text("Signed by Dr. Priya Lau")
    shot(page, "2-signed")
    step("signed off from the packet screen")

    with page.expect_download() as dl:
        page.get_by_role("link", name="Download packet (.zip)").click()
    assert dl.value.suggested_filename == "ophi-packet-tremblay.zip", dl.value.suggested_filename
    step(f"downloaded {dl.value.suggested_filename}")

    page.get_by_role("button", name="Mark as submitted").click()
    expect(page.locator(".sign")).to_contain_text("Marked submitted")
    page.goto(base + "/")
    expect(page.locator(".stage.submitted .stage-n")).to_have_text("1")
    expect(page.locator(".qrow", has_text="Yves Tremblay").locator(".pill")).to_have_text("Submitted")
    shot(page, "3-queue")
    step("queue shows Tremblay as submitted")

    page.goto(base + "/cases/rosco")
    why = page.locator(".step:not(.hero) details.why").first
    why.locator("summary").click()
    expect(why).to_have_attribute("open", "")
    step("Details disclosure opens on a secondary gap")

    page.goto(base + "/settings")
    expect(page.locator(".audit li").first).to_contain_text("marked submitted")
    step("audit log leads with the submission")
    b.close()
print("flow passed")
