"""Past preauth decisions (administrator export JSON) -> engine Case, as the submission stood on its date.

The export only lists what was attached, never when it was captured, so attachments carry no date and
the engine reads them as indeterminate, never as fresh. Member and provider IDs are salted-hashed here
and the raw values go no further.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import date
from pathlib import Path

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel

from ophi.casegen.dsl import build_case
from ophi.cdm.models import Case
from ophi.rules.schema import RulePack

# Attachment types the pack can reason about. Anything else is reported as a pack blind spot.
_RADIOGRAPHS = {"periapical_radiograph": "PA", "bitewing_radiographs": "BW", "panoramic_radiograph": "PAN"}
_MODELLED = {*_RADIOGRAPHS, "clinical_notes", "periodontal_charting"}


class Outcome(BaseModel):
    status: str  # approved | denied
    reason_code: str | None = None
    reason_category: str | None = None
    followup_type: str | None = None
    followup_outcome: str | None = None


class PastSubmission(BaseModel):
    preauth_id: str
    member_hash: str
    provider_hash: str
    code: str
    tooth_fdi: int | None
    age_band: str
    channel: str
    submitted_on: date
    attachment_types: list[str]
    unmodelled_attachments: list[str]  # attached, but no pack requirement looks for them
    outcome: Outcome


def hash_id(raw: str) -> str:
    salt = os.environ.get("OPHI_ID_SALT", "")
    return hashlib.sha256(f"{salt}:{raw}".encode()).hexdigest()[:16]


def load_export(path: Path) -> dict:
    return json.loads(path.read_text())


def to_submission(d: dict) -> PastSubmission:
    svc = d["services"][0]  # the export carries exactly one service line per request
    dec, fu = d["decision"], d.get("followup") or {}
    types = [a["type"] for a in d["attachments"]]
    return PastSubmission(
        preauth_id=d["preauth_id"], member_hash=hash_id(d["member"]["member_id"]),
        provider_hash=hash_id(d["provider"]["provider_id"]), code=svc["procedure_code"],
        tooth_fdi=int(svc["tooth"]) if svc.get("tooth") else None, age_band=d["member"]["age_band"],
        channel=d["submission_channel"], submitted_on=date.fromisoformat(d["submitted_date"]),
        attachment_types=types, unmodelled_attachments=[t for t in types if t not in _MODELLED],
        outcome=Outcome(status=dec["status"], reason_code=dec.get("reason_code"), reason_category=dec.get("reason_category"),
                        followup_type=fu.get("type"), followup_outcome=fu.get("outcome")),
    )


def in_pack(sub: PastSubmission, pack: RulePack) -> bool:
    return sub.code.startswith(pack.schedule.family_prefix) and sub.tooth_fdi is not None


def to_case(d: dict, sub: PastSubmission) -> Case:
    """Only called for in-pack codes; out-of-pack requests are stored as outcomes without an assessment.
    Schema-2 exports carry capture dates, perio values, the treatment plan and lab codes; older exports
    carry attachment names only, and what they lack stays undated or unknown."""
    as_of, tooth = sub.submitted_on, sub.tooth_fdi
    att = {a["type"]: a for a in d["attachments"]}
    radiographs = [r for t, a in att.items() if t in _RADIOGRAPHS
                   for r in _radiographs(_RADIOGRAPHS[t], a.get("count", 1), tooth, a.get("captured_date"))]
    perio, psr = _perio(d.get("perio_summary"), tooth) if "periodontal_charting" in att else ([], [])
    notes = [{"text": d["clinical_notes"], "teeth": [tooth], "date": att["clinical_notes"].get("captured_date")}] \
        if "clinical_notes" in att and d.get("clinical_notes") else []
    plan = d.get("treatment_plan")
    tx_plans = [{"pending": [p["code"] for p in plan["pending"]], "completed": [c["code"] for c in plan["completed"]], "date": as_of.isoformat()}] if plan else []
    history = [{"code": c["code"], "tooth": c.get("tooth"), "date": c.get("date") or as_of.isoformat()} for c in (plan or {}).get("completed", [])]
    history += [{"code": p["code"], "tooth": p.get("tooth"), "status": "planned", "date": as_of.isoformat()}
                for p in (plan or {}).get("pending", []) if p["code"] != sub.code]
    prior = d["prior_history"]
    if prior.get("same_tooth_crown_months_ago"):
        history.append({"code": sub.code, "tooth": tooth, "date": (as_of - relativedelta(months=prior["same_tooth_crown_months_ago"])).isoformat()})
    elif prior["same_code_last_5y"]:
        # Inside the 96-month window whatever the exact date; assumes the same tooth.
        history.append({"code": sub.code, "tooth": tooth, "date": (as_of - relativedelta(years=5) + relativedelta(days=1)).isoformat()})
    endo = [c["tooth"] for c in (plan or {}).get("completed", []) if c["code"].startswith("33") and c.get("tooth")]
    return build_case({
        "id": sub.preauth_id, "as_of": as_of.isoformat(), "source": "outcome_export",
        "patient": {"id": sub.member_hash, "name": sub.member_hash, "dob": _dob_floor(sub.age_band, as_of).isoformat()},
        "treatment": {"code": sub.code, "tooth": tooth, "lab_codes": d["services"][0].get("lab_codes", [])},
        "dentition": {"endo_treated": endo},
        "radiographs": radiographs, "perio_charts": perio, "psr": psr, "notes": notes, "tx_plans": tx_plans, "history": history,
        # The attachment list is the whole submission, so imaging/perio/notes absence is real. Dentition
        # is never exported; the plan is known only when the clinic sent it.
        "assurance": {"dentition": "Unknown", "planned_procedures": "Present" if plan else "Unknown", "coverage": "Unknown"},
    }, sub.preauth_id)


def _perio(summary: dict | None, tooth: int) -> tuple[list[dict], list[dict]]:
    """Old exports: a charting attachment is taken as an undated full-mouth chart. Schema 2: a complete
    chart carries the requested tooth's six sites; a PSR-only chart is just the PSR."""
    if summary is None:
        return [{"sites": 6}], []
    when = summary["captured_date"]
    psr = [{"date": when, "scores": summary["psr"]}] if summary.get("psr") else []
    if summary["chart_type"] != "complete":
        return [], psr
    sites = summary.get("tooth_sites_mm")  # a chart can be attached before its values are known (a what-if)
    return [{"date": when, "sites": 6, "depth": 3, **({"teeth": {tooth: sites}} if sites else {})}], psr


def _radiographs(view: str, count: int, tooth: int, captured: str | None) -> list[dict]:
    """Bitewings come as a right/left pair; a single bitewing is taken as the right side only."""
    if view != "BW":
        return [{"view": view, "tooth": tooth, "date": captured}]
    sides = [("right", [14, 15, 16, 17, 44, 45, 46, 47]), ("left", [24, 25, 26, 27, 34, 35, 36, 37])][:max(1, min(count, 2))]
    return [{"view": "BW", "side": side, "teeth": teeth, "date": captured} for side, teeth in sides]


def _dob_floor(age_band: str, as_of: date) -> date:
    """Youngest age in the band: an age rule passes only if every member of the band would pass it."""
    low = int(age_band.rstrip("+").split("-")[0])
    return as_of - relativedelta(years=low)
