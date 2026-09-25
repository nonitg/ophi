"""Screenshot every internal-app screen (ophi/web) at desktop and phone widths, for redesign before/after.

Usage: .venv/bin/python scripts/app-shots.py <base_url> <out_dir> [--full] [--only name,name]
Walks the demo as the coordinator, then as the dentist through Tremblay's confirm → assert → sign-off
flow, so the signed states get captured too. Point it at scripts/demo-screens.py (throwaway state).
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

base = sys.argv[1].rstrip("/")
out = Path(sys.argv[2])
full = "--full" in sys.argv
only = next((a.split("=", 1)[1].split(",") for a in sys.argv if a.startswith("--only=")), None)
out.mkdir(parents=True, exist_ok=True)

COORD = [
    ("queue", "/"),
    ("case-singh", "/cases/singh"),
    ("case-kowalchuk", "/cases/kowalchuk"),
    ("case-rosco", "/cases/rosco"),
    ("case-tremblay", "/cases/tremblay"),
    ("case-deng", "/cases/deng"),
    ("case-whitfield", "/cases/whitfield"),
    ("packet-singh", "/cases/singh/packet"),
    ("packet-whitfield", "/cases/whitfield/packet"),
    ("lookback", "/look-back"),
    ("settings", "/settings"),
]
WIDTHS = [("d", 1440, 900), ("m", 390, 844)]


def shoot(page, name, path, w, h, tag):
    if only and name not in only:
        return
    page.set_viewport_size({"width": w, "height": h})
    page.goto(base + path, wait_until="networkidle")
    page.screenshot(path=str(out / f"{tag}-{name}.png"), full_page=full)
    print(f"{tag}-{name}.png")


with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(device_scale_factor=1)
    page = ctx.new_page()
    page.goto(base + "/")
    page.request.post(base + "/reset")
    for tag, w, h in WIDTHS:
        for name, path in COORD:
            shoot(page, name, path, w, h, tag)

    # Dentist flow on Tremblay: confirm the proposal, record every criterion, sign off.
    ctx.add_cookies([{"name": "actor", "value": "dentist", "url": base}])
    shoot(page, "case-singh-dentist", "/cases/singh", 1440, 900, "d")
    page.request.post(base + "/cases/tremblay/proposals/note_0514.proposal1", form={"decision": "confirmed"})
    for cid in ["no_active_perio", "crown_root_ratio", "no_furcation", "margin_3mm", "ferrule_1_5mm", "mesiodistal_space",
                "no_adjunctive_needed", "extensively_restored", "active_disease_addressed", "endo_healed"]:
        page.request.post(base + "/cases/tremblay/assert", form={"criterion_id": cid, "value": "met"})
    for tag, w, h in WIDTHS:
        shoot(page, "case-tremblay-ready", "/cases/tremblay", w, h, tag)
        shoot(page, "packet-tremblay-presign", "/cases/tremblay/packet", w, h, tag)
    page.set_viewport_size({"width": 1440, "height": 900})
    page.goto(base + "/cases/tremblay/packet", wait_until="networkidle")
    if page.locator("#signoff-form button").count():
        page.locator("#signoff-form button").click()
        page.wait_for_load_state("networkidle")
    for tag, w, h in WIDTHS:
        shoot(page, "packet-tremblay-signed", "/cases/tremblay/packet", w, h, tag)
        shoot(page, "queue-after-sign", "/", w, h, tag)
    shoot(page, "settings-after", "/settings", 1440, 900, "d")
    b.close()
