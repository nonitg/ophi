"""Past crown requests Sun Life denied, found by the fix a case still needs, so staff see the mistake before repeating it.

Reads the outcomes data set (fixtures/cdcp_crowns). Only what the clinic sent and what Sun Life wrote back is
exposed: never the generator's answer key, and never member or provider IDs.
"""

from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from pathlib import Path

from ophi.dental.notation import tooth_class
from ophi.outcomes.denial_map import load_denial_map
from ophi.rules.schema import RulePack

CROWNS = Path(__file__).resolve().parents[2] / "fixtures" / "cdcp_crowns"

# Sun Life's reason codes in as few words as staff need. Ophi's voice: no approved/eligible/covered.
REASONS = {
    "DOC_MISSING_PERIO_CHART": "No full perio chart",
    "DOC_MISSING_RADIOGRAPH": "Missing X-ray",
    "DOC_RADIOGRAPH_STALE": "X-ray over 12 months old",
    "DOC_INSUFFICIENT_NOTES": "Note didn't describe the damage",
    "CLIN_ACTIVE_DISEASE": "Fillings or cleaning still to do",
    "CLIN_NOT_EXT_RESTORED": "Tooth not broken down enough",
    "CLIN_NEED_NOT_MET": "Crown criteria not met",
    "CLIN_PERIO_PROGNOSIS": "Weak gum or bone support",
    "CLIN_FERRULE": "Too little tooth above the gum",
    "CLIN_ENDO_NOT_HEALED": "Root canal not healed yet",
    "CLIN_NOT_COVERED_INDICATION": "Crack, sensitivity or looks only",
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
}


def reason(code: str | None) -> str:
    return REASONS.get(code or "", (code or "").replace("_", " ").capitalize())


@lru_cache(maxsize=1)
def _requests() -> dict[str, dict]:
    return {d["preauth_id"]: d for d in (json.loads(f.read_text()) for f in sorted(CROWNS.glob("*.json")))}


def _tooth(d: dict) -> int | None:
    t = d["services"][0].get("tooth")
    return int(t) if t else None


def _fixed_on_resend(d: dict) -> bool:
    fu = d.get("followup") or {}
    return fu.get("type") == "resubmission" and fu.get("outcome") == "approved"


def denied_like(pack: RulePack, requirement_ids: list[str], code: str, tooth: int, limit: int = 3) -> list[dict]:
    """Past requests denied for a reason this fix addresses, one group per reason (most frequent first), each
    with the requests most like this case. Empty if Sun Life never denied one for it."""
    codes = {c for c, ids in load_denial_map(pack).items() if set(ids) & set(requirement_ids)}
    by_code: dict[str, list[dict]] = {}
    for d in _requests().values():
        if d["decision"]["reason_code"] in codes:
            by_code.setdefault(d["decision"]["reason_code"], []).append(d)

    def unlike(d: dict) -> tuple:
        t = _tooth(d)
        # Same tooth, then same kind of tooth, then same crown code; one that was resent with the fix shows the way out.
        return (t != tooth, t is None or tooth_class(t) != tooth_class(tooth), d["services"][0]["procedure_code"] != code,
                not _fixed_on_resend(d), -date.fromisoformat(d["submitted_date"]).toordinal())

    return [{"reason": reason(c), "count": len(ds),
             "examples": [{"id": d["preauth_id"], "tooth": _tooth(d), "sent_on": date.fromisoformat(d["submitted_date"])}
                          for d in sorted(ds, key=unlike)[:limit]]}
            for c, ds in sorted(by_code.items(), key=lambda kv: -len(kv[1]))]


def _attachments(items: list[dict]) -> list[dict]:
    return [{"name": DOCS.get(a["type"], a["type"].replace("_", " ").capitalize()), "count": a.get("count", 1),
             "on": date.fromisoformat(a["captured_date"]) if a.get("captured_date") else None} for a in items]


def _changes(fu: dict) -> list[str]:
    """What the clinic did differently on the resend, one short line each."""
    ch, out = fu.get("changes") or {}, []
    added = ch.get("added_attachments") or []
    out += [f"Added {a['name'].lower()}" + (f", taken {a['on']:%b %-d, %Y}" if a["on"] else "") for a in _attachments(added)]
    perio = ch.get("perio_summary")
    if perio and not any(a["type"] == "periodontal_charting" for a in added):
        out.append(f"Updated the perio chart, {date.fromisoformat(perio['captured_date']):%b %-d, %Y}")
    for t in ch.get("completed_treatment") or []:
        out.append(f"Finished code {t['code']} first" + (f", {date.fromisoformat(t['date']):%b %-d, %Y}" if t.get("date") else ""))
    if "lab_codes" in ch:
        out.append(f"Changed the lab code to {', '.join(ch['lab_codes']) or 'none'}")
    if "clinical_notes" in ch:
        out.append("Rewrote the clinical note")
    return out


def detail(preauth_id: str) -> dict | None:
    """One past request as the clinic sent it, Sun Life's answer, and what happened on a resend."""
    d = _requests().get(preauth_id)
    if d is None:
        return None
    svc, dec, fu = d["services"][0], d["decision"], d.get("followup")
    resend = None
    if fu and fu.get("type") == "resubmission":
        resend = {"on": date.fromisoformat(fu["submitted_date"]), "changes": _changes(fu), "outcome": fu["outcome"],
                  "reason": reason(fu.get("reason_code")) if fu["outcome"] == "denied" else None,
                  "letter": fu.get("explanation_of_benefits_text"),
                  "new_note": (fu.get("changes") or {}).get("clinical_notes")}
    return {
        "id": d["preauth_id"], "tooth": _tooth(d), "code": svc["procedure_code"], "description": svc.get("description"),
        "lab_codes": svc.get("lab_codes") or [], "age_band": d["member"]["age_band"],
        "sent_on": date.fromisoformat(d["submitted_date"]),
        "decided_on": date.fromisoformat(d["decision_date"]) if d.get("decision_date") else None,
        "outcome": dec["status"], "reason": reason(dec.get("reason_code")) if dec["status"] == "denied" else None,
        "letter": dec.get("explanation_of_benefits_text"),
        "wanted": [DOCS.get(t, t) for t in dec.get("missing_documents") or []],
        "attachments": _attachments(d["attachments"]), "note": d.get("clinical_notes"), "narrative": d.get("narrative"),
        "resend": resend,
    }
