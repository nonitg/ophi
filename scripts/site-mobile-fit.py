#!/usr/bin/env python3
"""At phone widths, compare the room inside the email field and the clinic-software trigger with the width of their text.

Usage: site-mobile-fit.py [base_url] [query]
"""
import sys
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
QUERY = sys.argv[2] if len(sys.argv) > 2 else ""
WIDTHS = [320, 360, 375, 393, 430]
MEASURE = """() => {
  const text = (cs, s) => { const probe = document.createElement('span');
    probe.style.cssText = `position:absolute;visibility:hidden;white-space:nowrap;font:${cs.font};letter-spacing:${cs.letterSpacing}`;
    probe.textContent = s; document.body.append(probe); const w = probe.getBoundingClientRect().width; probe.remove(); return w; };
  const input = document.querySelector('#email'); const ics = getComputedStyle(input);
  const inputRoom = input.clientWidth - parseFloat(ics.paddingLeft) - parseFloat(ics.paddingRight);
  // Phones show a shorter prompt than wide screens; innerText is whichever one is showing.
  const trigger = document.querySelector('.pms-trigger'); const tcs = getComputedStyle(trigger);
  const label = trigger.querySelector('span'); const pmsLabel = label.innerText;
  const chevron = trigger.querySelector('.pms-chevron').getBoundingClientRect().width;
  const pmsRoom = trigger.clientWidth - parseFloat(tcs.paddingLeft) - parseFloat(tcs.paddingRight) - chevron - parseFloat(tcs.columnGap);
  const join = document.querySelector('.join-button');
  const shown = [...document.querySelectorAll('.footer-actions > *')].filter(el => el.getBoundingClientRect().width > 0);
  return { inputRoom, placeholder: text(getComputedStyle(input, '::placeholder'), input.placeholder), pmsRoom,
           pmsText: text(getComputedStyle(label), pmsLabel), pmsLabel, join: join.getBoundingClientRect().width,
           footerRows: new Set(shown.map(el => { const r = el.getBoundingClientRect(); return Math.round(r.top + r.height / 2); })).size };
}"""

with sync_playwright() as p:
    browser = p.chromium.launch()
    for width in WIDTHS:
        page = browser.new_page(viewport={"width": width, "height": 800}, reduced_motion="reduce")
        page.goto(BASE + QUERY, wait_until="networkidle")
        page.wait_for_function("document.fonts.status === 'loaded'")
        m = page.evaluate(MEASURE)
        email = "fits" if m["placeholder"] <= m["inputRoom"] else f"CLIPPED by {m['placeholder'] - m['inputRoom']:.0f}px"
        pms = "fits" if m["pmsText"] <= m["pmsRoom"] + .5 else f"TRUNCATED by {m['pmsText'] - m['pmsRoom']:.0f}px"
        print(f"{width}px  email room {m['inputRoom']:.0f} need {m['placeholder']:.0f} {email:<18} join {m['join']:.0f}  "
              f"pms room {m['pmsRoom']:.0f} need {m['pmsText']:.0f} {pms:<18} footer action rows {m['footerRows']}  “{m['pmsLabel']}”")
        page.close()
    browser.close()
