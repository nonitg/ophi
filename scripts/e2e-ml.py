"""Click through the app in a browser and report, per action, what the server printed about Laya/LightGBM and
whether the models were ever loaded into the server process.

Usage: PYTHONPATH=. .venv/bin/python scripts/e2e-ml.py
"""
import re
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

PORT, ROOT = 8790, Path(__file__).resolve().parent.parent
URL = f"http://127.0.0.1:{PORT}"
state = tempfile.mkdtemp(prefix="ophi-e2e-")
readouts = {p: p.stat().st_mtime for p in (ROOT / "cases/demo/laya").glob("*.json")}
srv = subprocess.Popen([sys.executable, "-u", str(ROOT / "scripts/e2e-ml-serve.py"), state, str(PORT)],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=ROOT)
out: list[str] = []
threading.Thread(target=lambda: [out.append(l.rstrip()) for l in srv.stdout], daemon=True).start()


def models_loaded() -> bool:
    maps = Path(f"/proc/{srv.pid}/maps").read_text()
    return bool(re.search(r"libtorch|lib_lightgbm", maps))


def step(label, fn):
    start = len(out)
    fn()
    time.sleep(0.4)
    new = out[start:]
    ml = [l for l in new if "ML " in l]
    reqs = [re.search(r'"(\w+ [^ ]+)', l).group(1) for l in new if '" 200' in l or '" 30' in l if "/static" not in l]
    print(f"\n== {label}\n   requests: {reqs}\n   ML lines: {len(ml)}  models in process: {models_loaded()}")
    for l in ml:
        print("   " + l.replace("INFO:     ", ""))
    for l in new:
        if "LightGBM P(denied)" in l:
            print("   " + l.strip())


try:
    for _ in range(240):
        if any("Uvicorn running" in l for l in out):
            break
        time.sleep(0.25)
    with sync_playwright() as p:
        page = p.chromium.launch().new_page()
        step("open board", lambda: page.goto(URL + "/"))
        ids = sorted({h.split("/cases/")[1].split("/")[0].split("?")[0].split("#")[0]
                      for h in page.eval_on_selector_all("a[href*='/cases/']", "els => els.map(e => e.getAttribute('href'))")})
        print("   cases on board:", ids)
        for cid in ids:
            step(f"click into {cid}", lambda: page.click(f"a[href$='/cases/{cid}']") if page.url.endswith("/") else page.goto(f"{URL}/cases/{cid}"))
            page.goto(URL + "/")
        page.goto(f"{URL}/cases/kowalchuk")
        for label in ["Check the chart again", "Mark taken (demo)", "Apply all", "Apply it"]:
            btn = page.get_by_role("button", name=label).or_(page.get_by_role("link", name=label)).first
            if btn.count():
                step(f"kowalchuk: click '{label}'", lambda: (btn.click(), page.wait_for_load_state("networkidle")))
                page.goto(f"{URL}/cases/kowalchuk")
        page.on("dialog", lambda d: d.accept())
        step("kowalchuk: click 'Skip gaps to test'", lambda: page.get_by_role("button", name="Skip gaps to test").click())
    changed = [p.name for p, m in readouts.items() if p.stat().st_mtime != m]
    print(f"\nmodels ever loaded in server: {models_loaded()}\nreadout files rewritten during run: {changed or 'none'}")
finally:
    srv.terminate()
