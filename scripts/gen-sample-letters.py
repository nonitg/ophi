"""Write synthetic Sun Life decision letters for the letter-upload demo (fixtures/letters/).

No real CDCP decision letters are public, so these are ours: plain text layout, no logo or branding, and every page
says SAMPLE. They cover the lab's two With-Sun-Life cases, and between them exercise every branch the reader has:
approved, a denial naming a reason the rule pack knows, a denial too vague to name one, and an acknowledgement that
decides nothing (outcome "unclear"). Patient, tooth, fee and reference match the lab fixtures.
Run: .venv/bin/python scripts/gen-sample-letters.py
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / "fixtures" / "letters"

# ABELDent pid 160, status Q: Sun Life answers by mail. Sent 2026-09-15.
CHERSKI = {"date": "September 17, 2026", "ref": "SL260915000160", "patient": "Mathew Cherski",
           "client_id": "CDCP-5512-0160", "dob": "1969-03-20", "provider": "Dr. Priya Lau", "tooth": "26",
           "procedure": "27211 Crown, porcelain fused to metal", "fee": "$581.00"}
# ABELDent pid 164, status S: still with Sun Life. Sent 2026-09-22.
GOERTSEN = {"date": "September 25, 2026", "ref": "SL260922000164", "patient": "Susan Goertsen",
            "client_id": "CDCP-5512-0164", "dob": "1972-03-24", "provider": "Dr. Priya Lau", "tooth": "36",
            "procedure": "27215 Crown, porcelain fused to metal base", "fee": "$629.45"}

REVIEWED = "We have reviewed the preauthorization request for the procedure listed below."
RECONSIDER = ("This decision is not a guarantee of payment. You may request a reconsideration within 60 days of "
              "this letter with new clinical information.")
PENDING = "This letter is not a decision. No benefit is authorized by this letter."

LETTERS = {
    "cherski-denied-ferrule": (CHERSKI, "Not approved", [
        REVIEWED,
        "The request is not approved. The documentation provided does not demonstrate at least 1.5 mm of sound "
        "tooth structure (ferrule) remaining for a crown on tooth 26. Please provide a narrative and radiograph "
        "showing the remaining tooth structure if you wish to submit a new request."]),
    "cherski-denied-vague": (CHERSKI, "Not approved", [
        REVIEWED,
        "The request is not approved. The requested service was denied as per the plan criteria."]),
    "cherski-approved": (CHERSKI, "Approved", [
        REVIEWED,
        "The request is approved. This preauthorization is valid for 12 months from the date of this letter, "
        "provided the client remains eligible on the date of service."]),
    "cherski-denied-perio": (CHERSKI, "Not approved", [
        REVIEWED,
        "The request is not approved. A complete periodontal charting (6 sites per tooth) was not received. "
        "Please submit a new request with the periodontal chart."]),
    "goertsen-approved": (GOERTSEN, "Approved", [
        REVIEWED,
        "The request is approved. This preauthorization is valid for 12 months from the date of this letter, "
        "provided the client remains eligible on the date of service."]),
    "goertsen-denied-radiograph": (GOERTSEN, "Not approved", [
        REVIEWED,
        "The request is not approved. A current periapical radiograph of tooth 36 was not received with the "
        "request. Please submit a new request with a diagnostic periapical radiograph of the tooth taken within "
        "the last 12 months."]),
    "goertsen-denied-notes": (GOERTSEN, "Not approved", [
        REVIEWED,
        "The request is not approved. The clinical notes submitted do not describe the condition of tooth 36 or "
        "the reason a crown is required. Please submit a new request with clinical notes that describe the tooth."]),
    # Decides nothing: the reader should come back "unclear" and leave staff to record it by hand.
    "goertsen-acknowledgement": (GOERTSEN, "Under review", [
        "We have received the preauthorization request for the procedure listed below.",
        "The request is under review. No decision has been made at this time. A further letter will be sent to "
        "your office once the review is complete. Please do not resubmit this request."]),
}

IMAGES = {"cherski-denied-perio"}  # a phone photo of the page, to show images are read too


def html(c: dict, decision: str, paras: list[str]) -> str:
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
<tr><td>{c['procedure']}</td><td>{c['tooth']}</td><td>{c['fee']}</td><td>{decision}</td></tr></table>
<p>{PENDING if decision == 'Under review' else RECONSIDER}</p><p>Canadian Dental Care Plan</p>"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        page = p.chromium.launch().new_page(viewport={"width": 816, "height": 1056})
        for name, (c, decision, paras) in LETTERS.items():
            page.set_content(html(c, decision, paras))
            if name in IMAGES:
                page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
            else:
                page.pdf(path=str(OUT / f"{name}.pdf"), format="Letter")
            print(OUT / name)


if __name__ == "__main__":
    main()
