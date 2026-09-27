"""pages lane, part 6: every shared screen at 1440x900 and 390x844 — horizontal overflow, clipped
text, overlapping controls and text contrast. Screenshots under var/e2e/pages/."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pages_lib import BASE, DESKTOP, OUT, PHONE, Recorder, clipped, context, goto, overflow, shot  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

PAGES = [
    ("board", "/"),
    ("outcomes", "/outcomes"),
    ("outcomes-denied", "/outcomes?status=denied&tooth=molar"),
    ("outcomes-empty", "/outcomes?tooth=99"),
    ("results", "/results"),
    ("recover", "/recover"),
    ("settings", "/settings"),
    ("rules", "/rules"),
]

CONTRAST = """() => {
  function lum(c) {
    const m = c.match(/[\\d.]+/g).map(Number);
    const f = v => { v /= 255; return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); };
    return 0.2126*f(m[0]) + 0.7152*f(m[1]) + 0.0722*f(m[2]);
  }
  function bg(el) {
    for (let e = el; e; e = e.parentElement) {
      const c = getComputedStyle(e).backgroundColor;
      const m = c.match(/[\\d.]+/g);
      if (m && (m.length < 4 || Number(m[3]) > 0.5)) return c;
    }
    return 'rgb(255,255,255)';
  }
  const out = [];
  for (const el of document.querySelectorAll('body *')) {
    if (!el.childNodes.length) continue;
    const t = [...el.childNodes].filter(n => n.nodeType === 3 && n.textContent.trim()).map(n => n.textContent.trim()).join(' ');
    if (!t) continue;
    const s = getComputedStyle(el);
    if (s.visibility === 'hidden' || s.display === 'none' || Number(s.opacity) < 0.5) continue;
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    const l1 = lum(s.color), l2 = lum(bg(el));
    const ratio = (Math.max(l1,l2)+0.05) / (Math.min(l1,l2)+0.05);
    const px = parseFloat(s.fontSize), bold = Number(s.fontWeight) >= 700;
    const need = (px >= 24 || (px >= 18.66 && bold)) ? 3.0 : 4.5;
    if (ratio < need) out.push({text: t.slice(0,50), cls: el.className.toString().slice(0,40),
                                color: s.color, bg: bg(el), size: s.fontSize, ratio: +ratio.toFixed(2), need});
  }
  const seen = new Set();
  return out.filter(o => { const k = o.cls + o.color; if (seen.has(k)) return false; seen.add(k); return true; }).slice(0, 20);
}"""

report: dict = {}

with sync_playwright() as pw:
    for actor in ("coordinator", "dentist"):
        browser, ctx = context(pw, actor)
        rec = Recorder()
        page = ctx.new_page()
        rec.attach(page)
        for name, path in PAGES:
            for vw, label in ((DESKTOP, "1440"), (PHONE, "390")):
                page.set_viewport_size(vw)
                st = goto(page, rec, path)
                page.wait_for_timeout(250)
                key = f"{actor}/{name}@{label}"
                report[key] = {
                    "status": st,
                    "overflow": overflow(page),
                    "clipped": clipped(page),
                    "contrast": page.evaluate(CONTRAST) if label == "1440" else None,
                    "shot": shot(page, f"{name}-{actor}-{label}.png"),
                }
        rec.dump(f"console-layout-{actor}.json")
        report[f"{actor}/console"] = {"console": rec.console, "failed": rec.failed, "bad": rec.bad_status}
        browser.close()

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "layout.json").write_text(json.dumps(report, indent=2))
print("written")
