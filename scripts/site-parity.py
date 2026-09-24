#!/usr/bin/env python3
"""Pixel parity for a styling refactor: capture the Ophi page across widths and interactive states, then diff.

Usage:
  site-parity.py capture <dir> [base] [--only REGEX] [--shard i/n]   base defaults to http://localhost:3111
  site-parity.py compare <before> <after>    changed pixels per shot, *-diff.png highlights in <after>

Capture both sides from the same kind of server (two `next start` builds side by side is fastest), and run
the baseline twice first: any shot that differs between two baseline runs is noise, not a regression.

Covers every breakpoint edge, X-ray, dialogs, the listbox (both directions), FAQ, form error/busy/success, hovers,
copy, focus, no-JavaScript markup, motion end states and a 20px browser font size. Signups go through the honeypot, so no contact is stored.
"""
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

PAGE_WIDTHS = [1680, 1600, 1440, 1280, 1101, 1100, 1024, 768, 701, 700, 600, 480, 479, 430, 393, 361, 360, 346, 345, 320]
STATE_WIDTHS = [1440, 1024, 700, 390, 360, 340]
HEIGHTS = {1680: 1050, 1600: 1000, 1440: 900, 1280: 800, 1024: 768, 768: 1024, 430: 932, 393: 852, 390: 844, 360: 800, 320: 640}


def open_page(browser, base, width, *, js=True, motion="reduce", font=None):
    context = browser.new_context(viewport={"width": width, "height": HEIGHTS.get(width, 900)}, device_scale_factor=1,
                                  reduced_motion=motion, java_script_enabled=js)
    context.grant_permissions(["clipboard-read", "clipboard-write"], origin=base)
    context.set_default_timeout(20000)
    page = context.new_page()
    if font:
        # The reader's default font size setting, which rem units follow.
        context.new_cdp_session(page).send("Page.setFontSizes", {"fontSizes": {"standard": font, "fixed": font}})
    page.goto(base, wait_until="load" if not js else "networkidle")
    if not js:
        # Scripted waits need JavaScript; server-rendered markup and its fonts settle quickly.
        page.wait_for_timeout(1500)
        return page
    page.wait_for_selector('.tooth-viewer[data-ready="true"]', timeout=30000)
    page.add_style_tag(content="nextjs-portal { display: none !important; }")
    page.wait_for_function("document.fonts.status === 'loaded'")
    page.wait_for_timeout(600)
    return page


def xray_on(page):
    page.get_by_role("button", name="X-ray").click()
    page.wait_for_timeout(500)
    page.mouse.move(0, 0)


def form(page):
    return page.locator("#join")


def submit(page, email, bot=False):
    page.fill("#email", email)
    if bot:
        page.locator("#hp_ref").evaluate('(el) => { el.value = "parity-check"; }')
    page.locator("#join button[type=submit]").click()
    page.wait_for_selector(".waitlist-success" if bot else "#email-error")
    page.wait_for_timeout(300)


# Each state: (name, widths, setup(page) -> locator to shoot, or None for the viewport, xray).
def states():
    def faq(page):
        for summary in page.locator("summary").all():
            summary.click()
        page.wait_for_timeout(300)
        page.mouse.move(0, 0)
        return page.locator("section[aria-labelledby=faq-title]")

    def dialog(name):
        def run(page):
            page.get_by_role("button", name=name).click()
            page.wait_for_timeout(400)
            page.mouse.move(1, 1)
            return None
        return run

    def pms(page):
        form(page).scroll_into_view_if_needed()
        page.locator("#pms").click()
        page.keyboard.press("ArrowDown")
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(400)
        return None

    def pms_up(page):
        # Near the viewport's foot the listbox opens upward.
        page.locator("#pms").evaluate("el => window.scrollBy(0, el.getBoundingClientRect().bottom - innerHeight + 60)")
        page.locator("#pms").click()
        page.wait_for_timeout(400)
        return None

    def pms_selected(page):
        page.locator("#pms").click()
        page.get_by_role("option", name="ClearDent").click()
        page.locator("#pms").click()
        page.wait_for_timeout(400)
        return None

    def focus_pms(page):
        page.locator("#join button[type=submit]").focus()
        page.keyboard.press("Tab")
        return form(page)

    def in_dialog(selector):
        def run(page):
            page.get_by_role("button", name="Why Ophi?").click()
            page.wait_for_timeout(400)
            page.locator(selector).hover()
            page.wait_for_timeout(200)
            return None
        return run

    def pms_chosen(page):
        page.locator("#pms").click()
        page.get_by_role("option", name="ClearDent").click()
        page.mouse.move(0, 0)
        return form(page)

    def error(page):
        submit(page, "invalid")
        return form(page)

    def success(page):
        submit(page, "parity@example.com", bot=True)
        page.mouse.move(0, 0)
        return form(page)

    def hover(selector):
        def run(page):
            target = page.locator(selector).first
            target.scroll_into_view_if_needed()
            target.hover()
            page.wait_for_timeout(200)
            return target.locator("xpath=..")
        return run

    def copied(page):
        button = page.get_by_role("button", name="Copy email address", exact=False)
        button.scroll_into_view_if_needed()
        button.click()
        page.wait_for_timeout(150)
        return button

    def copied_away(page):
        button = copied(page)
        page.mouse.move(0, 0)
        page.wait_for_timeout(150)
        return button

    def focus_email(page):
        page.locator("#email").focus()
        page.keyboard.press("Shift+Tab")
        page.keyboard.press("Tab")
        return form(page)

    def focus_pill(page):
        page.get_by_role("button", name="Why Ophi?").focus()
        page.keyboard.press("Shift+Tab")
        page.keyboard.press("Tab")
        return page.get_by_role("button", name="Why Ophi?").locator("xpath=..")

    def busy(page):
        # Hold the request so the pending state stays on screen.
        page.route("**/*", lambda route: None if route.request.method == "POST" else route.continue_())
        page.fill("#email", "parity@example.com")
        page.locator("#join button[type=submit]").click()
        page.wait_for_timeout(300)
        return form(page)

    base = [
        ("faq", [1440, 700, 390], faq),
        ("why", STATE_WIDTHS, dialog("Why Ophi?")),
        ("privacy", [1440, 390], dialog("Your email & privacy")),
        ("pms", [1440, 700, 390, 340], pms),
        ("pms-chosen", [1440, 390], pms_chosen),
        ("pms-up", [1440, 390], pms_up),
        ("pms-selected", [1440], pms_selected),
        ("focus-pms", [1440], focus_pms),
        ("hover-close", [1440], in_dialog("dialog[open] button[aria-label=Close]")),
        ("hover-source", [1440], in_dialog("dialog[open] a[target=_blank]")),
        ("error", [1440, 390], error),
        ("success", [1440, 1024, 390, 340], success),
        ("hover-why", [1440, 390], hover("button:has-text('Why Ophi?')")),
        ("hover-join", [1440, 390], hover("#join button[type=submit]")),
        ("hover-copy", [1440], hover("button[aria-label^='Copy email']")),
        ("hover-pms", [1440], hover("#pms")),
        ("hover-privacy", [1440, 390], hover("button:has-text('Your email & privacy')")),
        ("hover-top", [1440, 390], hover("a[href='#top']")),
        ("hover-xray", [1440], hover("button:has-text('X-ray')")),
        ("copied", [1440], copied),
        ("copied-away", [1440], copied_away),
        ("focus-email", [1440, 390], focus_email),
        ("focus-pill", [1440], focus_pill),
        ("busy", [1440], busy),
    ]
    shots = []
    for name, widths, run in base:
        shots.append((name, widths, run, False))
    for name, widths, run in base:
        if name not in {"busy", "copied-away", "focus-pill"}:
            shots.append(("xray-" + name, widths[:2], run, True))
    return shots


def motion_page(page):
    # Motion end states: entrance animations and the open FAQ settle to the same frame.
    page.wait_for_timeout(2500)
    page.locator("summary").first.click()
    page.wait_for_timeout(800)
    page.mouse.move(0, 0)
    return FULL


def motion_success(page):
    page.wait_for_timeout(2500)
    submit(page, "parity@example.com", bot=True)
    page.mouse.move(0, 0)
    page.wait_for_timeout(1500)
    return form(page)


FULL = "full"


def jobs():
    """(name, width, page options, setup(page) -> locator | FULL | None for the viewport)."""
    out = [(f"page-{w}", w, {}, lambda page: FULL) for w in PAGE_WIDTHS]
    out += [(f"xray-page-{w}", w, {"xray": True}, lambda page: FULL) for w in [1440, 1024, 700, 390, 360]]
    out += [(f"bigfont-page-{w}", w, {"font": 20}, lambda page: FULL) for w in [1440, 390]]
    for w in [1440, 390]:
        out += [(f"nojs-{w}", w, {"js": False}, lambda page: FULL),
                (f"motion-{w}", w, {"motion": "no-preference"}, motion_page),
                (f"motion-success-{w}", w, {"motion": "no-preference"}, motion_success)]
    out += [(f"{name}-{w}", w, {"xray": xray}, run) for name, widths, run, xray in states() for w in widths]
    return out


def capture(out: Path, base: str, only: str | None, shard: tuple[int, int]) -> None:
    from playwright.sync_api import sync_playwright
    if urlparse(base).hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise SystemExit("Form states submit the waitlist; local previews only.")
    out.mkdir(parents=True, exist_ok=True)
    todo = [job for job in jobs() if not only or re.search(only, job[0])][shard[0]::shard[1]]
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--enable-webgl", "--use-angle=swiftshader"])
        for name, width, options, run in todo:
            page = open_page(browser, base, width, js=options.get("js", True), motion=options.get("motion", "reduce"), font=options.get("font"))
            if options.get("xray"):
                xray_on(page)
            target = run(page)
            path = str(out / f"{name}.png")
            if target is FULL:
                page.screenshot(path=path, full_page=True)
            else:
                (target or page).screenshot(path=path)
            print(f"{name}.png", flush=True)
            page.context.close()
        browser.close()


def compare(before: Path, after: Path, only: str | None) -> None:
    from PIL import Image, ImageChops
    changed_shots = 0
    shots = sorted(p for p in before.glob("*.png") if not p.stem.endswith("-diff") and (not only or re.search(only, p.stem)))
    for a_path in shots:
        b_path = after / a_path.name
        if not b_path.exists():
            print(f"{a_path.stem}: MISSING")
            changed_shots += 1
            continue
        a, b = Image.open(a_path).convert("RGB"), Image.open(b_path).convert("RGB")
        if a.size != b.size:
            print(f"{a_path.stem}: SIZE {a.size} -> {b.size}")
            changed_shots += 1
            continue
        diff = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > 8 else 0)
        changed = diff.histogram()[255]
        if changed:
            changed_shots += 1
            print(f"{a_path.stem}: {changed} px, region {diff.getbbox()}")
            highlight = b.copy()
            highlight.paste(Image.new("RGB", b.size, "#ff00ff"), mask=diff)
            highlight.save(after / f"{a_path.stem}-diff.png")
    print(f"{changed_shots} changed of {len(shots)}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["capture", "compare"])
    parser.add_argument("dirs", nargs="+", help="capture: <dir> [base]; compare: <before> <after>")
    parser.add_argument("--only", help="regex over shot names, e.g. '^(page|why)-1440'")
    parser.add_argument("--shard", default="0/1", help="i/n: take every n-th shot from i, to run captures in parallel")
    args = parser.parse_args()
    if args.mode == "capture":
        i, n = map(int, args.shard.split("/"))
        capture(Path(args.dirs[0]), args.dirs[1] if len(args.dirs) > 1 else "http://localhost:3111", args.only, (i, n))
    else:
        compare(Path(args.dirs[0]), Path(args.dirs[1]), args.only)
