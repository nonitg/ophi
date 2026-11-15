#!/usr/bin/env python3
"""Load the site on a slow connection, cold cache: phone (390x844 @3x, touch) and desktop (1440x900 @2x), ~400 kbps
down, 400 ms RTT, 4x CPU slowdown. Reports medians of FCP, LCP, CLS, when each font face lands (the real type
replaces its fallback), hydrated (the signup's listbox replaces its native select, so React has taken over), TBT,
transfer bytes, JS bytes and requests, plus every request made.

usage: site-load.py [BASE] [runs] [paths]     e.g. site-load.py http://localhost:3170 3 /,/demo
"""
import statistics
import sys
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3170"
RUNS = int(sys.argv[2]) if len(sys.argv) > 2 else 3
PATHS = (sys.argv[3] if len(sys.argv) > 3 else "/,/demo").split(",")
DEVICES = {
    "phone": {"viewport": {"width": 390, "height": 844}, "device_scale_factor": 3, "is_mobile": True, "has_touch": True},
    "desktop": {"viewport": {"width": 1440, "height": 900}, "device_scale_factor": 2},
}
SLOW = {"offline": False, "latency": 400, "downloadThroughput": 400 * 1000 / 8, "uploadThroughput": 400 * 1000 / 8}

OBSERVE = """() => {
  const p = window.__perf = { lcp: 0, lcpEl: '', fcp: 0, cls: 0, longtasks: [], hydrated: 0, fonts: {} };
  const poll = setInterval(() => {
    for (const f of document.fonts) if (f.status === 'loaded') p.fonts[f.family.replace(/"/g, '') + ' ' + f.style] ??= performance.now();
    if (p.hydrated && performance.now() > p.hydrated + 5000) clearInterval(poll);
  }, 50);
  new PerformanceObserver((l) => { for (const e of l.getEntries()) { p.lcp = e.startTime; p.lcpEl = e.element ? e.element.tagName + (e.element.id ? '#' + e.element.id : '') + ' ' + (e.url || (e.element.textContent || '').slice(0, 30)) : ''; } }).observe({ type: 'largest-contentful-paint', buffered: true });
  new PerformanceObserver((l) => { for (const e of l.getEntries()) if (e.name === 'first-contentful-paint') p.fcp = e.startTime; }).observe({ type: 'paint', buffered: true });
  new PerformanceObserver((l) => { for (const e of l.getEntries()) p.longtasks.push([e.startTime, e.duration]); }).observe({ type: 'longtask', buffered: true });
  new PerformanceObserver((l) => { for (const e of l.getEntries()) if (!e.hadRecentInput) p.cls += e.value; }).observe({ type: 'layout-shift', buffered: true });
  new MutationObserver(() => { if (!p.hydrated && document.querySelector('#pms[role=combobox]')) p.hydrated = performance.now(); }).observe(document, { subtree: true, childList: true });
}"""


def run_once(browser, url, device):
    context = browser.new_context(**DEVICES[device])
    page = context.new_page()
    cdp = context.new_cdp_session(page)
    cdp.send("Network.enable")
    cdp.send("Network.setCacheDisabled", {"cacheDisabled": True})
    cdp.send("Network.emulateNetworkConditions", SLOW)
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
    sizes, kinds = {}, {}
    cdp.on("Network.responseReceived", lambda e: kinds.__setitem__(e["requestId"], (e["type"], e["response"]["url"])))
    cdp.on("Network.loadingFinished", lambda e: sizes.__setitem__(e["requestId"], e["encodedDataLength"]))
    page.add_init_script(f"({OBSERVE})()")
    page.goto(url, wait_until="load", timeout=180000)
    page.wait_for_function("window.__perf.hydrated > 0", timeout=180000)
    page.wait_for_load_state("networkidle", timeout=180000)
    page.wait_for_timeout(2000)
    perf = page.evaluate("window.__perf")
    context.close()
    js = sum(size for rid, size in sizes.items() if kinds.get(rid, ("",))[0] == "Script")
    tbt = sum(max(0, d - 50) for s, d in perf["longtasks"] if s >= perf["fcp"] and s <= perf["hydrated"] + 5000)
    requests = sorted((kinds.get(rid, ("?", "?"))[1].replace(BASE, ""), size) for rid, size in sizes.items())
    return {"fcp": perf["fcp"], "lcp": perf["lcp"], "cls": perf["cls"], "hydrated": perf["hydrated"], "tbt": tbt,
            "serif": perf["fonts"].get("newsreader normal", 0), "sans": perf["fonts"].get("DM Sans normal", 0),
            "italic": next((t for k, t in perf["fonts"].items() if k.endswith("italic")), 0),
            "kb": sum(sizes.values()) / 1024, "js_kb": js / 1024, "requests": len(sizes), "lcp_el": perf["lcpEl"], "list": requests}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--mute-audio"])
        for path in PATHS:
            for device in DEVICES:
                runs = [run_once(browser, BASE + path, device) for _ in range(RUNS)]
                med = {k: statistics.median(r[k] for r in runs) for k in ["fcp", "lcp", "cls", "hydrated", "tbt", "serif", "sans", "italic", "kb", "js_kb", "requests"]}
                print(f"{path:6} {device:7} FCP {med['fcp']:6.0f}  LCP {med['lcp']:6.0f}  CLS {med['cls']:.3f}  hydrated {med['hydrated']:6.0f}  "
                      f"TBT {med['tbt']:5.0f}  fonts in: sans {med['sans']:5.0f} serif {med['serif']:5.0f} italic {med['italic']:5.0f}  transfer {med['kb']:5.0f} KB  JS {med['js_kb']:4.0f} KB  requests {med['requests']:.0f}   "
                      f"(LCP runs {', '.join(f'{r['lcp']:.0f}' for r in runs)}; hydrated runs {', '.join(f'{r['hydrated']:.0f}' for r in runs)})")
                print(f"       LCP element: {runs[-1]['lcp_el']}")
                for url, size in runs[-1]["list"]:
                    print(f"         {size / 1024:7.1f} KB  {url[:110]}")
        browser.close()


if __name__ == "__main__":
    main()
