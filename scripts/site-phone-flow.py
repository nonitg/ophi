#!/usr/bin/env python3
"""Drive the page on a phone (390x750, touch) the way a visitor would: the menu, the hero holding still while its
patients take turns, How and the story each fitting one screen, a swipe through the story, and every clinic patient
with what Ophi did. Exits 1 on any failure.

usage: site-phone-flow.py [BASE]
"""
import sys
from playwright.sync_api import sync_playwright, expect

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
W, H, HEADER = 390, 750, 64
failures = []


def check(name, fn):
    try:
        fn()
        print("ok  ", name)
    except Exception as error:  # noqa: BLE001 - report every failed step, then exit non-zero
        failures.append(name)
        print("FAIL", name, "-", str(error).splitlines()[0][:200])


def scroll_to(page, selector, offset=0):
    page.evaluate(f"""window.scrollTo(0, document.querySelector("{selector}").getBoundingClientRect().top + scrollY + {offset})""")


def box(page, selector):
    return page.evaluate(f"""(() => {{ const r = document.querySelector("{selector}").getBoundingClientRect(); return {{ top: r.top, bottom: r.bottom }}; }})()""")


with sync_playwright() as p:
    browser = p.chromium.launch(args=["--mute-audio"])
    page = browser.new_context(viewport={"width": W, "height": H}, is_mobile=True, has_touch=True).new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    # Vercel Analytics only exists on Vercel, so its script 404s on a local server.
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" and "/_vercel/" not in m.location.get("url", "") else None)
    page.goto(BASE, wait_until="networkidle")
    page.add_style_tag(content="html{scroll-behavior:auto!important}")

    def menu():
        page.get_by_role("button", name="Open menu").tap()
        page.get_by_role("link", name="For clinics").tap()
        expect(page.locator("#site-menu")).to_have_count(0)
        page.wait_for_timeout(300)
        assert abs(box(page, "#clinic")["top"] - 80) < 4, "didn't land on For clinics"

    def hero_still():
        scroll_to(page, "section[aria-labelledby=hero-title]")
        tops, spill = [], 0
        for _ in range(16):
            page.wait_for_timeout(700)
            tops.append(round(page.evaluate("document.querySelector('#how').getBoundingClientRect().top + scrollY")))
            # How far the phone, cards or dots reach past the stage's fixed height.
            spill = max(spill, page.evaluate("""(() => { const stage = document.querySelector('section[aria-labelledby=hero-title] [class*="max-w-[560px]"]');
              const bottom = stage.getBoundingClientRect().bottom; return Math.max(...[...stage.children].map((el) => el.getBoundingClientRect().bottom - bottom)); })()"""))
        assert len(set(tops)) == 1, f"How moved while the hero played: {sorted(set(tops))}"
        assert spill <= 0, f"the hero's cards reach {round(spill)}px past the stage"
        height = page.evaluate("""document.querySelector('section[aria-labelledby=hero-title] [class*="max-w-[560px]"]').offsetHeight""")
        assert height <= H - HEADER, f"the hero's stage is {height}px, screen has {H - HEADER}"

    def how_fits():
        scroll_to(page, "#how ol", -260)
        page.wait_for_timeout(400)
        # The card holds the list; the doors' waiting room sits just above it.
        card = page.evaluate("document.querySelector('#how ol').parentElement.getBoundingClientRect().bottom")
        zone = page.evaluate("document.querySelector('#how ol').parentElement.previousElementSibling.getBoundingClientRect().top")
        assert card - zone <= H - HEADER, f"doors and card take {round(card - zone)}px, screen has {H - HEADER}"

    def story_fits():
        scroll_to(page, "#story button[aria-label^='Moment 1']", -HEADER - 16)
        page.wait_for_timeout(400)
        bars = box(page, "#story button[aria-label^='Moment 1']")
        screen = page.evaluate("document.querySelector('#story [aria-live]').getBoundingClientRect().bottom")
        assert screen - bars["top"] <= H - HEADER, f"bars to the bottom of the phone screen take {round(screen - bars['top'])}px"

    def story_swipe():
        scroll_to(page, "#story .touch-pan-y", -HEADER - 24)
        page.wait_for_timeout(300)
        phone = page.locator("#story .touch-pan-y").bounding_box()
        y = phone["y"] + phone["height"] / 2
        for direction, want in ((-1, "Moment 2"), (1, "Moment 1")):
            page.mouse.move(phone["x"] + phone["width"] / 2 - direction * 90, y)
            page.mouse.down()
            page.mouse.move(phone["x"] + phone["width"] / 2 + direction * 90, y, steps=8)
            page.mouse.up()
            expect(page.locator(f"#story button[aria-label^='{want}']")).to_have_attribute("aria-current", "step")
        page.locator("#story button[aria-label^='Moment 4']").tap()
        expect(page.locator("#story button[aria-label^='Moment 4']")).to_have_attribute("aria-current", "step")

    def clinic_rows():
        scroll_to(page, "#clinic")
        rows = page.locator("#clinic ul > li")
        expect(rows).to_have_count(6)
        for i in range(6):
            expect(rows.nth(i)).to_be_visible()
        expect(page.locator("#clinic ul > li p.tablet\\:flex")).to_have_count(5)
        for i in range(5):
            expect(page.locator("#clinic ul > li p.tablet\\:flex").nth(i)).to_be_visible()

    def approve():
        page.get_by_role("button", name="Approve", exact=True).tap()
        # The button runs its checks, then gives way to what happened.
        expect(page.locator("#clinic button", has_text="Approv")).to_have_count(0, timeout=8000)

    check("the menu jumps to a section and closes", menu)
    check("the hero's stage fits one screen and holds still while its patients take turns", hero_still)
    check("How's doors, card and all five steps fit one screen", how_fits)
    check("the story's bars, words and phone screen fit one screen", story_fits)
    check("a swipe on the story's phone moves between moments", story_swipe)
    check("the clinic shows all six patients and what Ophi did", clinic_rows)
    check("Approve runs on a phone", approve)
    check("no console errors", lambda: (_ for _ in ()).throw(AssertionError(errors[0])) if errors else None)
    browser.close()

print("clean" if not failures else f"{len(failures)} failed")
sys.exit(1 if failures else 0)
