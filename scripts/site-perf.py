#!/usr/bin/env python3
"""Performance probe for the Ophi page: load on a throttled phone, tooth drag frame rate, and scroll smoothness per engine.

Usage:
  site-perf.py load   [base] [runs]   phone (390x844 @3x, touch), Slow 4G + 4x CPU: FCP, LCP, TBT, CLS, tooth ready, bytes
  site-perf.py drag   [base]          drag the tooth for 3 s; frame intervals on SwiftShader (CPU raster, a proxy for a
                                      weak phone GPU) and on this Mac's GPU
  site-perf.py scroll [base]          wheel-scroll the page for 3 s in chromium, webkit and firefox; frame intervals

base defaults to http://localhost:3201. Compare two `next start` builds side by side (scripts/site-perf-worktrees.sh).
Headless Chromium draws WebGL with SwiftShader unless launched with --use-angle=metal; METAL below opts in.
"""
import statistics
import sys
from playwright.sync_api import sync_playwright

PHONE = {"viewport": {"width": 390, "height": 844}, "device_scale_factor": 3, "is_mobile": True, "has_touch": True}
DESKTOP = {"viewport": {"width": 1440, "height": 900}, "device_scale_factor": 2}
# Lighthouse's mobile preset.
SLOW_4G = {"offline": False, "latency": 150, "downloadThroughput": 1.6 * 1024 * 1024 / 8, "uploadThroughput": 750 * 1024 / 8}
METAL = ["--use-angle=metal", "--enable-gpu", "--ignore-gpu-blocklist"]

OBSERVE = """() => {
  window.__perf = { lcp: 0, fcp: 0, cls: 0, longtasks: [] };
  new PerformanceObserver((l) => { for (const e of l.getEntries()) window.__perf.lcp = e.startTime; }).observe({ type: 'largest-contentful-paint', buffered: true });
  new PerformanceObserver((l) => { for (const e of l.getEntries()) if (e.name === 'first-contentful-paint') window.__perf.fcp = e.startTime; }).observe({ type: 'paint', buffered: true });
  new PerformanceObserver((l) => { for (const e of l.getEntries()) window.__perf.longtasks.push([e.startTime, e.duration]); }).observe({ type: 'longtask', buffered: true });
  new PerformanceObserver((l) => { for (const e of l.getEntries()) if (!e.hadRecentInput) window.__perf.cls += e.value; }).observe({ type: 'layout-shift', buffered: true });
  new MutationObserver(() => { const v = document.querySelector('.tooth-viewer[data-ready="true"]'); if (v && !window.__perf.ready) window.__perf.ready = performance.now(); })
    .observe(document, { subtree: true, attributes: true, attributeFilter: ['data-ready'] });
}"""

# Frame intervals from requestAnimationFrame while `action` runs.
FRAMES_START = "() => { window.__frames = []; let last = performance.now(); const tick = (t) => { window.__frames.push(t - last); last = t; if (window.__frames.length < 100000) window.__raf = requestAnimationFrame(tick); }; window.__raf = requestAnimationFrame(tick); }"
FRAMES_STOP = "() => { cancelAnimationFrame(window.__raf); return window.__frames.slice(2); }"


def frame_summary(frames):
    if not frames:
        return "no frames"
    frames = sorted(frames)
    p95 = frames[int(len(frames) * .95) - 1]
    janky = sum(1 for f in frames if f > 25)
    return f"{len(frames)} frames, mean {statistics.mean(frames):.1f} ms, p95 {p95:.1f} ms, worst {frames[-1]:.0f} ms, >25ms: {janky}"


def load(base, runs):
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(args=METAL)
        for _ in range(runs):
            context = browser.new_context(**PHONE)
            page = context.new_page()
            cdp = context.new_cdp_session(page)
            cdp.send("Network.enable")
            cdp.send("Network.setCacheDisabled", {"cacheDisabled": True})
            cdp.send("Network.emulateNetworkConditions", SLOW_4G)
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
            sizes = {}
            types = {}
            cdp.on("Network.responseReceived", lambda e: types.__setitem__(e["requestId"], (e["type"], e["response"]["url"])))
            cdp.on("Network.loadingFinished", lambda e: sizes.__setitem__(e["requestId"], e["encodedDataLength"]))
            page.add_init_script(f"({OBSERVE})()")
            page.goto(base, wait_until="load")
            page.wait_for_selector('.tooth-viewer[data-ready="true"]', timeout=120000)
            page.wait_for_timeout(3000)
            perf = page.evaluate("window.__perf")
            tbt = sum(max(0, d - 50) for s, d in perf["longtasks"] if s >= perf["fcp"])
            longest = max((d for _, d in perf["longtasks"]), default=0)
            by_type = {}
            for rid, size in sizes.items():
                kind, url = types.get(rid, ("Other", ""))
                kind = "tooth.bin" if url.endswith("tooth.bin") else kind
                by_type[kind] = by_type.get(kind, 0) + size
            results.append({"fcp": perf["fcp"], "lcp": perf["lcp"], "cls": perf["cls"] * 1000, "tbt": tbt, "longest": longest, "ready": perf.get("ready", 0),
                            "kb": sum(sizes.values()) / 1024, "by_type": by_type})
            context.close()
        browser.close()
    for key in ["fcp", "lcp", "cls", "tbt", "longest", "ready", "kb"]:
        values = [r[key] for r in results]
        print(f"{key + (" x1000" if key == "cls" else ""):8} median {statistics.median(values):8.0f}   runs {', '.join(f'{v:.0f}' for v in values)}")
    print("bytes by type (last run, KB):", ", ".join(f"{k} {v / 1024:.0f}" for k, v in sorted(results[-1]["by_type"].items(), key=lambda kv: -kv[1])))


def drag(base):
    with sync_playwright() as p:
        for label, args in [("swiftshader", []), ("mac gpu", METAL)]:
            browser = p.chromium.launch(args=args)
            for device_label, device in [("desktop 1440@2x", DESKTOP), ("phone 390@3x", PHONE)]:
                context = browser.new_context(**{k: v for k, v in device.items() if k != "has_touch"})
                page = context.new_page()
                page.goto(base, wait_until="networkidle")
                page.wait_for_selector('.tooth-viewer[data-ready="true"]', timeout=60000)
                page.wait_for_timeout(800)
                box = page.locator(".tooth-canvas").bounding_box()
                x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
                page.mouse.move(x, y)
                page.mouse.down()
                page.evaluate(FRAMES_START)
                for i in range(90):
                    page.mouse.move(x + (i % 30 - 15) * 8, y + (i % 20 - 10) * 3)
                    page.wait_for_timeout(33)
                page.mouse.up()
                frames = page.evaluate(FRAMES_STOP)
                print(f"{label:12} {device_label:16} {frame_summary(frames)}")
                context.close()
            browser.close()


def scroll(base):
    with sync_playwright() as p:
        for name in ["chromium", "webkit", "firefox"]:
            engine = getattr(p, name)
            browser = engine.launch(args=METAL) if name == "chromium" else engine.launch()
            for device_label, device in [("desktop 1440@2x", DESKTOP), ("phone 390@3x", {k: v for k, v in PHONE.items() if name == "chromium" or k not in ("is_mobile", "has_touch")})]:
                context = browser.new_context(**device)
                page = context.new_page()
                page.goto(base, wait_until="networkidle")
                page.wait_for_selector('.tooth-viewer[data-ready="true"]', timeout=60000)
                page.wait_for_timeout(2500)
                page.mouse.move(200, 400)
                page.evaluate(FRAMES_START)
                for i in range(60):
                    page.mouse.wheel(0, 60 if (i // 15) % 2 == 0 else -60)
                    page.wait_for_timeout(16)
                page.wait_for_timeout(300)
                frames = page.evaluate(FRAMES_STOP)
                print(f"{name:9} {device_label:16} {frame_summary(frames)}")
                context.close()
            browser.close()


if __name__ == "__main__":
    mode = sys.argv[1]
    base = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:3201"
    {"load": lambda: load(base, int(sys.argv[3]) if len(sys.argv) > 3 else 3), "drag": lambda: drag(base), "scroll": lambda: scroll(base)}[mode]()
