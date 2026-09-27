"""Write synthetic Sun Life decision letters for the letter-upload demo (fixtures/letters/).

No real CDCP decision letters are public, so these are ours: plain text layout, no logo or branding, and every page
says SAMPLE. They are about the lab's Cherski case (ABELDent pid 160, status Q: Sun Life answers by mail).
Run: .venv/bin/python scripts/gen-sample-letters.py
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / "fixtures" / "letters"
COMMON = {"date": "September 17, 2026", "ref": "SL260915000160", "patient": "Mathew Cherski",
          "client_id": "CDCP-5512-0160", "dob": "1969-03-20", "provider": "Dr. Priya Lau", "tooth": "26"}

LETTERS = {
    "cherski-denied-ferrule": ("Not approved", [
        "We have reviewed the preauthorization request for the procedure listed below.",
        "The request is not approved. The documentation provided does not demonstrate at least 1.5 mm of sound "
        "tooth structure (ferrule) remaining for a crown on tooth 26. Please provide a narrative and radiograph "
        "showing the remaining tooth structure if you wish to submit a new request."]),
    "cherski-denied-vague": ("Not approved", [
        "We have reviewed the preauthorization request for the procedure listed below.",
        "The request is not approved. The requested service was denied as per the plan criteria."]),
    "cherski-approved": ("Approved", [
        "We have reviewed the preauthorization request for the procedure listed below.",
        "The request is approved. This preauthorization is valid for 12 months from the date of this letter, "
        "provided the client remains eligible on the date of service."]),
    "cherski-denied-perio": ("Not approved", [
        "We have reviewed the preauthorization request for the procedure listed below.",
        "The request is not approved. A complete periodontal charting (6 sites per tooth) was not received. "
        "Please submit a new request with the periodontal chart."]),
}


def html(decision: str, paras: list[str]) -> str:
    c = COMMON
    body = "".join(f"<p>{p}</p>" for p in paras)
    return f"""<!doctype html><meta charset="utf-8"><style>
body {{ font: 12pt/1.5 Georgia, serif; margin: 56px 64px; color: #111; }}
.sample {{ border: 2px solid #b00; color: #b00; font: bold 11pt sans-serif; padding: 6px 10px; display: inline-block; }}
h1 {{ font-size: 15pt; margin: 18px 0 4px; }} table {{ border-collapse: collapse; margin: 16px 0; }}
td, th {{ border: 1px solid #888; padding: 6px 10px; text-align: left; font-size: 11pt; }}
.meta td {{ border: 0; padding: 1px 16px 1px 0; }}
</style>
<div class="sample">SAMPLE — synthetic letter for software testing. Not issued by Sun Life or the CDCP.</div>
<h1>Canadian Dental Care Plan — Preauthorization decision</h1>
<p>Administered by Sun Life</p>
<table class="meta">
<tr><td>Date</td><td>{c['date']}</td></tr><tr><td>Reference number</td><td>{c['ref']}</td></tr>
<tr><td>Client</td><td>{c['patient']} (born {c['dob']})</td></tr><tr><td>Client ID</td><td>{c['client_id']}</td></tr>
<tr><td>Provider</td><td>{c['provider']}</td></tr></table>
<p>Dear provider,</p>{body}
<table><tr><th>Procedure</th><th>Tooth</th><th>Submitted</th><th>Decision</th></tr>
<tr><td>27211 Crown, porcelain fused to metal</td><td>{c['tooth']}</td><td>$581.00</td><td>{decision}</td></tr></table>
<p>This decision is not a guarantee of payment. You may request a reconsideration within 60 days of this letter
with new clinical information.</p><p>Canadian Dental Care Plan</p>"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        page = p.chromium.launch().new_page(viewport={"width": 816, "height": 1056})
        for name, (decision, paras) in LETTERS.items():
            page.set_content(html(decision, paras))
            if name == "cherski-denied-perio":  # a phone photo of the page, to show images are read too
                page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
            else:
                page.pdf(path=str(OUT / f"{name}.pdf"), format="Letter")
            print(OUT / name)


if __name__ == "__main__":
    main()
