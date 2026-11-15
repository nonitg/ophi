#!/usr/bin/env python3
"""Drive the page's working parts the way a visitor would: the hero's patients, How's care thread,
Why's counts, the crown story (autoplay, the step buttons, the real call), the team view's Approve button and an FAQ
answer. Exits 1 on any failure.

usage: site-vision-flow.py [BASE]
"""
import sys
from playwright.sync_api import sync_playwright, expect

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
failures = []


def check(name, fn):
    try:
        fn()
        print("ok  ", name)
    except Exception as error:  # noqa: BLE001 - report every failed step, then exit non-zero
        failures.append(name)
        print("FAIL", name, "-", str(error).splitlines()[0][:200])


with sync_playwright() as p:
    browser = p.chromium.launch(args=["--mute-audio", "--autoplay-policy=no-user-gesture-required"])
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    # Vercel Analytics only exists on Vercel, so its script 404s on a local server.
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" and "/_vercel/" not in m.location.get("url", "") else None)
    page.goto(BASE, wait_until="networkidle")

    def hero_moments():
        hero = page.locator("section[aria-labelledby=hero-title]")
        # Three patients take turns, one door each: Alex calls, Margaret texts, Chloé books from her page.
        expect(hero).to_contain_text("Alex’s care, from your records")
        expect(hero).to_contain_text("Hi, is my denture back from the lab yet?", timeout=20000)
        expect(hero).to_contain_text("Margaret’s care, from your records")
        expect(hero).to_contain_text("Book this time", timeout=20000)

    def hero_see_how():
        # The hero's second way in jumps to How.
        page.get_by_role("link", name="See how it works").click()
        page.wait_for_function("location.hash === '#how'")
        page.evaluate("scrollTo(0, 0)")

    def how_thread():
        how = page.locator("#how")
        how.scroll_into_view_if_needed()
        # Each door changes Alex's care, and each change lands in the same timeline and is saved back.
        expect(how).to_contain_text("Booked Thu Nov 19, 9:30 am", timeout=10000)
        expect(how).to_contain_text("Saved to your record system", timeout=8000)
        expect(how).to_contain_text("The insurer replied.", timeout=12000)
        expect(how).to_contain_text("Alex is calling", timeout=30000)

    def gap_today():
        why = page.locator("#why")
        why.scroll_into_view_if_needed()
        # Alex's plan as they see it today, then each count with its fix underneath.
        expect(why).to_contain_text("To learn the rest, Alex has to call.")
        expect(why).to_contain_text("Every call answered")
        expect(why).to_contain_text("Every patient gets their page in a text")

    def story_plays():
        story = page.locator("#story")
        story.scroll_into_view_if_needed()
        # The first call plays out on Alex's phone and leaves the request waiting.
        expect(story).to_contain_text("you'll get a text once the clinic confirms", timeout=9000)
        expect(story).to_contain_text("Name and birthday matched one patient file first", timeout=4000)

    def real_call():
        story = page.locator("#story")
        story.get_by_role("button", name="Hear the real call").click()
        expect(story).to_contain_text("Real recording", timeout=8000)
        expect(story).to_contain_text("Welcome to our dental office", timeout=8000)
        story.get_by_role("button", name="Stop").click()
        expect(story.get_by_role("button", name="Hear the real call")).to_be_visible()

    def story_steps():
        story = page.locator("#story")
        story.get_by_role("button", name="The lab delivers the crown").click()
        expect(story).to_contain_text("Booked: crown fitting", timeout=9000)
        story.get_by_role("button", name="Crown fitted. Paid from the same page.").click()
        expect(story).to_contain_text("Paid Dec 4", timeout=9000)

    def approve():
        team = page.locator("#clinic")
        team.scroll_into_view_if_needed()
        team.get_by_role("button", name="Approve").click()
        # The patient is told last, once the change is written and read back.
        expect(team).to_contain_text("Jordan texted", timeout=8000)
        expect(team).to_contain_text("Surgery, Mon Dec 14, 9:00 am", timeout=4000)
        expect(team.get_by_role("button", name="Approve")).to_have_count(0)

    def faq():
        question = page.locator("#questions summary", has_text="Will Ophi give clinical advice?")
        question.click()
        expect(page.locator("#questions")).to_contain_text("Questions about care go to your team.")

    check("the hero's patients take turns, one door each", hero_moments)
    check("the hero's See how it works link jumps to How", hero_see_how)
    check("How lands every door's change in Alex's one timeline", how_thread)
    check("Why shows what Alex knows today and each count's fix", gap_today)
    check("the story plays the first call when it comes into view", story_plays)
    check("the real call plays and the phone follows it", real_call)
    check("step buttons move through the story", story_steps)
    check("approving the held request runs its checks", approve)
    check("an FAQ answer opens", faq)
    check("no console errors", lambda: (_ for _ in ()).throw(AssertionError(errors[0])) if errors else None)
    browser.close()

sys.exit(1 if failures else 0)
