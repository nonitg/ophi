#!/usr/bin/env python3
"""At every phone width, check the email placeholder and the clinic-software prompt show whole and the footer
actions stay on one row. Measures after hydration, when the custom listbox has replaced the native select.

Usage: site-mobile-fit.py [base_url] [min_width] [max_width]
"""
import sys
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
LOW, HIGH = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (320, 700)
MEASURE = """() => {
  const text = (cs, s) => { const probe = document.createElement('span');
    probe.style.cssText = `position:absolute;visibility:hidden;white-space:nowrap;font:${cs.font};letter-spacing:${cs.letterSpacing}`;
    probe.textContent = s; document.body.append(probe); const w = probe.getBoundingClientRect().width; probe.remove(); return w; };
  const input = document.querySelector('#email'); const ics = getComputedStyle(input);
  const inputRoom = input.clientWidth - parseFloat(ics.paddingLeft) - parseFloat(ics.paddingRight);
  // Phones show a shorter prompt than wide screens; innerText is whichever one is showing.
  const trigger = document.querySelector('button.pms-trigger'); const tcs = getComputedStyle(trigger);
  const label = trigger.querySelector('span');
  const chevron = trigger.querySelector('.pms-chevron').getBoundingClientRect().width;
  const pmsRoom = trigger.clientWidth - parseFloat(tcs.paddingLeft) - parseFloat(tcs.paddingRight) - chevron - parseFloat(tcs.columnGap);
  const shown = [...document.querySelectorAll('.footer-actions > *')].filter(el => el.getBoundingClientRect().width > 0);
  return { email: text(getComputedStyle(input, '::placeholder'), input.placeholder) - inputRoom,
           pms: text(getComputedStyle(label), label.innerText) - pmsRoom, prompt: label.innerText,
           footerRows: new Set(shown.map(el => { const r = el.getBoundingClientRect(); return Math.round(r.top + r.height / 2); })).size };
}"""

failures = 0
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": LOW, "height": 800}, reduced_motion="reduce")
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_selector("button.pms-trigger")
    page.wait_for_function("document.fonts.status === 'loaded'")
    for width in range(LOW, HIGH + 1):
        page.set_viewport_size({"width": width, "height": 800})
        m = page.evaluate(MEASURE)
        problems = [f"email placeholder clipped {m['email']:.1f}px"] * (m["email"] > 0) + \
                   [f"“{m['prompt']}” clipped {m['pms']:.1f}px"] * (m["pms"] > .5) + \
                   [f"footer actions on {m['footerRows']} rows"] * (m["footerRows"] > 1)
        if problems:
            failures += 1
            print(f"FAIL {width}px: {'; '.join(problems)}")
    browser.close()
print(f"{HIGH - LOW + 1 - failures}/{HIGH - LOW + 1} widths {LOW}–{HIGH}px pass")
sys.exit(1 if failures else 0)
