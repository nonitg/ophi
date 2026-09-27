"""Past requests as the clinic reads them: Sun Life's reason codes in plain words, and one request's detail
(what was sent, Sun Life's letter, what changed on a resend). Works on outcomes.past_store rows.
"""

from __future__ import annotations

from datetime import date
from urllib.parse import urlencode

# Sun Life's reason codes in as few words as staff need. Shown in Sun Life's voice (data-voice="payer").
REASONS = {
    "DOC_MISSING_PERIO_CHART": "No full perio chart",
    "DOC_MISSING_RADIOGRAPH": "Missing X-ray",
    "DOC_RADIOGRAPH_STALE": "X-ray over 12 months old",
    "DOC_INSUFFICIENT_NOTES": "Note didn't describe the damage",
    "CLIN_ACTIVE_DISEASE": "Fillings or cleaning still to do",
    "CLIN_NOT_EXT_RESTORED": "Tooth not broken down enough",
    "CLIN_NEED_NOT_MET": "Crown criteria not met",
    "CLIN_PERIO_PROGNOSIS": "Weak gum or bone support",
    "CLIN_POOR_PROGNOSIS": "Poor outlook for the tooth",
    "CLIN_FERRULE": "Too little tooth above the gum",
    "CLIN_ENDO_NOT_HEALED": "Root canal not healed yet",
    "CLIN_NOT_COVERED_INDICATION": "Crack, sensitivity or looks only",
    "CLIN_ALT_BENEFIT": "A filling would do instead",
    "NOT_COVERED": "Not a CDCP benefit",
    "ADMIN_INVALID_CODE": "Retired lab fee code",
    "FREQ_LIMIT": "Crowned in the last 8 years",
    "ELIGIBILITY": "Patient under 18",
    "TOOTH_INELIGIBLE": "Wisdom tooth, molars still in place",
    "DUPLICATE_REQUEST": "Sent twice",
    "UNSPECIFIED": "No reason given",
}

DOCS = {
    "periapical_radiograph": "Periapical X-ray",
    "bitewing_radiographs": "Bitewing X-rays",
    "panoramic_radiograph": "Panoramic X-ray",
    "periodontal_charting": "Perio chart",
    "clinical_notes": "Clinical note",
    "narrative_letter": "Narrative letter",
    "tooth_structure_loss_pct": "Tooth structure loss estimate",
    "pulp_vitality_test": "Pulp vitality test",
    "missing_teeth_chart": "Missing teeth chart",
}


KINDS = {"incisor": "Incisor", "canine": "Canine", "premolar": "Premolar", "molar": "Molar", "third_molar": "Wisdom tooth"}

# The Past outcomes list's outcome tabs; "resent" is a denial the clinic resent and Sun Life then approved.
TABS = {"all": "All", "approved": "Approved", "denied": "Denied", "resent": "Resent → approved"}
PAGE_SIZE = 50


def reason(code: str | None) -> str:
    return REASONS.get(code or "", (code or "").replace("_", " ").capitalize())


def resent_approved(row: dict) -> bool:
    """Denied, then approved once the clinic resent it: the fix worth copying."""
    return row["followup_type"] == "resubmission" and row["followup_outcome"] == "approved"


def _on(s: str | None) -> date | None:
    return date.fromisoformat(s) if s else None


def _attachments(items: list[dict]) -> list[dict]:
    return [{"name": DOCS.get(a["type"], a["type"].replace("_", " ").capitalize()), "count": a.get("count", 1),
             "on": _on(a.get("captured_date"))} for a in items]


def _changes(fu: dict) -> list[str]:
    """What the clinic did differently on the resend, one short line each."""
    ch, out = fu.get("changes") or {}, []
    added = ch.get("added_attachments") or []
    out += [f"Added {a['name'].lower()}" + (f", taken {a['on']:%b %-d, %Y}" if a["on"] else "") for a in _attachments(added)]
    perio = ch.get("perio_summary")
    if perio and not any(a["type"] == "periodontal_charting" for a in added):
        out.append("Updated the perio chart" + (f", {_on(perio['captured_date']):%b %-d, %Y}" if perio.get("captured_date") else ""))
    for t in ch.get("completed_treatment") or []:
        out.append(f"Finished code {t['code']} first" + (f", {_on(t['date']):%b %-d, %Y}" if t.get("date") else ""))
    if "lab_codes" in ch:
        out.append(f"Changed the lab code to {', '.join(ch['lab_codes']) or 'none'}")
    if "clinical_notes" in ch:
        out.append("Rewrote the clinical note")
    return out


def detail(row: dict) -> dict:
    """One past request as the clinic sent it, Sun Life's answer, and what happened on a resend."""
    sent, dec, fu = row["sent"], row["decision"], row["followup"]
    svc = sent["services"][0]
    resend = None
    if fu and fu.get("type") == "resubmission":
        resend = {"on": _on(fu.get("submitted_date")), "changes": _changes(fu), "outcome": fu["outcome"],
                  "reason": reason(fu.get("reason_code")) if fu["outcome"] == "denied" else None,
                  "letter": fu.get("explanation_of_benefits_text"),
                  "new_note": (fu.get("changes") or {}).get("clinical_notes")}
    return {
        "id": row["preauth_id"], "clinic_id": row["clinic_id"], "tooth": row["tooth_fdi"], "code": row["procedure_code"],
        "description": svc.get("description"), "lab_codes": svc.get("lab_codes") or [], "age_band": row["age_band"],
        "sent_on": row["submitted_on"], "decided_on": row["decided_on"],
        "outcome": row["status"], "reason": reason(row["reason_code"]) if row["status"] == "denied" else None,
        "letter": dec.get("explanation_of_benefits_text"),
        "wanted": [DOCS.get(t, t) for t in dec.get("missing_documents") or []],
        "attachments": _attachments(sent.get("attachments") or []), "note": sent.get("clinical_notes"),
        "narrative": sent.get("narrative"), "resend": resend,
    }


def find(rows: list[dict], preauth_id: str) -> dict | None:
    return next((r for r in rows if r["preauth_id"] == preauth_id), None)


def _in_tab(row: dict, tab: str) -> bool:
    return tab == "all" or (resent_approved(row) if tab == "resent" else row["status"] == tab)


def _line(row: dict) -> dict:
    return {"id": row["preauth_id"], "sent_on": row["submitted_on"], "tooth": row["tooth_fdi"],
            "kind": KINDS.get(row["tooth_class"] or ""), "code": row["procedure_code"], "clinic_id": row["clinic_id"],
            "outcome": row["status"], "reason": reason(row["reason_code"]) if row["status"] == "denied" else None,
            "resent_approved": resent_approved(row)}


def listing(rows: list[dict], tab: str = "all", clinic: str = "", tooth: str = "", reason_code: str = "", page: int = 1) -> dict:
    """One page of past requests for the Past outcomes list. Tooth is a tooth number or a kind (molar, ...).
    Tab counts follow the other filters, so the MOA sees how a slice split between approved and denied."""
    tab = tab if tab in TABS else "all"
    filters = {k: v for k, v in (("clinic", clinic), ("tooth", tooth), ("reason", reason_code)) if v}
    scoped = [r for r in rows if (not clinic or r["clinic_id"] == clinic)
              and (not tooth or tooth in (r["tooth_class"], str(r["tooth_fdi"])))
              and (not reason_code or r["reason_code"] == reason_code)]
    shown = [r for r in scoped if _in_tab(r, tab)]
    pages = max(1, -(-len(shown) // PAGE_SIZE))
    page = min(max(page, 1), pages)

    def href(**kw) -> str:
        q = {**filters, "status": tab, "page": page, **kw}
        return "?" + urlencode({k: v for k, v in q.items() if v not in ("", "all", 1)})

    return {
        "tab": tab, "filters": filters, "total": len(shown), "page": page, "pages": pages,
        "tabs": [{"key": k, "label": label, "count": sum(_in_tab(r, k) for r in scoped), "href": href(status=k, page=1)}
                 for k, label in TABS.items()],
        "rows": [_line(r) for r in shown[(page - 1) * PAGE_SIZE: page * PAGE_SIZE]],
        "prev": href(page=page - 1) if page > 1 else None, "next": href(page=page + 1) if page < pages else None,
        "clinics": sorted({r["clinic_id"] for r in rows}),
        "kinds": [(k, label) for k, label in KINDS.items() if any(r["tooth_class"] == k for r in rows)],
        "teeth": sorted({r["tooth_fdi"] for r in rows if r["tooth_fdi"]}),
        "reasons": sorted({(r["reason_code"], reason(r["reason_code"])) for r in rows if r["reason_code"]}, key=lambda c: c[1]),
    }
