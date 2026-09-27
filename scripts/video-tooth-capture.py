"""Render the site's enamel tooth as a transparent turntable for the pitch video.

Serves the repo root, opens video/tools/tooth/ (build it first:
  cd video/tools/tooth && NODE_PATH=../../../site/node_modules ../../node_modules/.bin/esbuild main.ts \
     --bundle --format=esm --outfile=dist/main.js)
and writes video/public/tooth/{normal,normal-noshadow,xray}/0000..0119.png plus still-hero.png.

Usage: .venv/bin/python scripts/video-tooth-capture.py [--only normal,xray] [--size 1200]
"""
import argparse
import base64
import http.server
import threading
from functools import partial
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "video/public/tooth"
PORT = 8932


def save(data_url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(base64.b64decode(data_url.split(",", 1)[1]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="normal,normal-noshadow,xray")
    ap.add_argument("--size", type=int, default=1200)
    ap.add_argument("--hero", type=int, default=2400)
    args = ap.parse_args()

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    handler = partial(Quiet, directory=str(ROOT))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--use-angle=metal", "--enable-gpu", "--ignore-gpu-blocklist"])
            page = browser.new_page(viewport={"width": 800, "height": 800})
            page.on("console", lambda m: print("console:", m.text))
            page.on("pageerror", lambda e: print("pageerror:", e))
            page.goto(f"http://127.0.0.1:{PORT}/video/tools/tooth/index.html")
            page.wait_for_function("window.toothReady === true", timeout=60000)
            print("gl:", page.evaluate("(() => { const c = document.createElement('canvas').getContext('webgl2'); const d = c.getExtension('WEBGL_debug_renderer_info'); return d ? c.getParameter(d.UNMASKED_RENDERER_WEBGL) : 'n/a'; })()"))
            print("framing:", page.evaluate("window.tooth.frameUp()"))
            frames = page.evaluate("window.tooth.FRAMES")
            for mode in args.only.split(","):
                for i in range(frames):
                    save(page.evaluate(f"window.tooth.frame({i}, '{mode}', {args.size})"), OUT / mode / f"{i:04d}.png")
                print("done", mode)
            save(page.evaluate(f"window.tooth.frame(0, 'normal', {args.hero})"), OUT / "still-hero.png")
            print("done hero")
            browser.close()
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
