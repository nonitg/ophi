"""Screenshot the board's Start-here banner for a case Sun Life has held past its usual turnaround.

The demo's top card is normally a patient in the chair, so this clears the cases ahead of it (capturing
their chair gaps through the app's own endpoints) until the late-with-Sun-Life case leads the board.

Usage: .venv/bin/python scripts/shot-late-payer-banner.py <out.png> [port]
"""
import re
import sys

import httpx
from playwright.sync_api import sync_playwright

out = sys.argv[1]
base = f"http://127.0.0.1:{sys.argv[2] if len(sys.argv) > 2 else 8801}"

FORM = re.compile(r'action="[^"]*/cases/([^/"]+)/capture"[^>]*>\s*<input[^>]*value="([^"]+)"', re.S)


def chair_gaps(html: str) -> list[tuple[str, str]]:
    return FORM.findall(html)


with httpx.Client(base_url=base, follow_redirects=True, timeout=20) as c:
    for _ in range(40):  # each capture may reveal the next blocking case
        html = c.get("/").text
        if "Past Sun Life" in html:
            break
        gaps = chair_gaps(html)
        if not gaps:  # the leading case has no chair gap on the board; open it and take its gaps there
            lead = re.search(r'<section class="start.*?</section>', html, re.S).group(0)
            cid = re.search(r'/cases/([^"/]+)"', lead).group(1)
            gaps = chair_gaps(c.get(f"/cases/{cid}").text)
        if gaps:
            cid, rid = gaps[0]
            c.post(f"/cases/{cid}/capture", data={"requirement_id": rid, "back": "board"})
        else:  # nothing a clinician can capture is left; skip the rest so the case stops leading
            c.post(f"/cases/{cid}/test-skip")
    else:
        sys.exit("gave up clearing the board")

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_context(viewport={"width": 1440, "height": 900}).new_page()
    resp = page.goto(base, wait_until="networkidle")
    if resp.status != 200:
        sys.exit(f"board: HTTP {resp.status}")
    page.evaluate("document.fonts.ready")
    banner = page.locator("section.start").first
    print(banner.inner_text())
    banner.screenshot(path=out)
    print(f"{out} ok")
    b.close()
