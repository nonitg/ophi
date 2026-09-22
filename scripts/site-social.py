#!/usr/bin/env python3
"""Export Ophi's original live-rendered poster as a static social sharing image."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
base = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3111"
root = Path(__file__).resolve().parent.parent
with sync_playwright() as p:
    browser = p.chromium.launch(args=["--enable-webgl", "--use-angle=swiftshader"])
    page = browser.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1, reduced_motion="reduce")
    page.goto(base, wait_until="networkidle")
    page.wait_for_selector('.tooth-viewer[data-ready="true"]')
    # Export-only framing: retain the real brand, typography, sculpture and materials.
    page.add_style_tag(content='''
      #main > :not(.poster), .site-footer, .tooth-controls, .launch-status, nextjs-portal { display: none !important; }
      .site-shell { width: calc(100% - 96px); min-height: 630px; }
      .site-header { height: 90px; }
      .poster { height: 460px; }
      .poster-title { font-size: 139px; }
      body::after { content: "ophi.app"; position: absolute; bottom: 28px; left: 48px; font-size: 15px; color: #626b5d; }
    ''')
    page.wait_for_timeout(1500)
    page.screenshot(path=str(root / "site/app/opengraph-image.png"))
    browser.close()
(root / "site/app/opengraph-image.alt.txt").write_text("Ophi. Good care. Less paperwork. An original ivory tooth sculpture on warm paper in soft window light.\n")
print(root / "site/app/opengraph-image.png")
