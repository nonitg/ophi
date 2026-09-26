"""Past crown requests -> training examples for Laya (request text + questions) and the tree model (features).

Only what the clinic sent is rendered or featurized. The decision is the label, and `_generator_truth`
is read only for the note-question labels (docs/plan/05-outcomes-learning.md §2.3, §4). Resubmissions
become their own examples: the first request with the clinic's changes applied, labelled with the
second decision.
"""

from __future__ import annotations

import copy
import json
import random
from datetime import date
from pathlib import Path

from pydantic import BaseModel

from ophi.dental.notation import tooth_class
from ophi.engine.assess import assess
from ophi.outcomes.adapter import to_case, to_submission
from ophi.rules.schema import RulePack

ROOT = Path(__file__).resolve().parents[2]
CROWNS = ROOT / "fixtures" / "cdcp_crowns"
SENT = ("submission_channel", "submitted_date", "member", "provider", "services", "attachments", "perio_summary",
        "treatment_plan", "clinical_notes", "narrative", "prior_history")
VAGUE = "UNSPECIFIED"

# What the rules can't read from structured data. Label = is it true of the tooth, given what was sent,
# so a terse note should come out near the base rate rather than a guess.
NOTE_QUESTIONS = {
    "structure_lost": ("Has the requested tooth lost a cusp or its incisal edge?",
                       lambda c, v: bool(c.get("cusp_fractured") or c.get("incisal_edge_lost"))),
    "extensively_restored": ("Does the requested tooth meet the CDCP definition of extensively restored?",
                             lambda c, v: "not_ext_restored" not in v),
    "endo_not_healed": ("Is a root canal on the requested tooth recent or not yet healed?", lambda c, v: "endo_not_healed" in v),
    "pending_basic": ("Are fillings or scaling still to be done elsewhere in the mouth?", lambda c, v: "pending_basic" in v),
    "subgingival_margin": ("Is the margin below the gum, or is crown lengthening needed?", lambda c, v: bool(c["subgingival_margin"])),
    "uncovered_indication": ("Is the crown for a cracked tooth, sensitivity or appearance?", lambda c, v: "crack_or_cosmetic" in v),
    "poor_support": ("Is there furcation involvement or poor bone support at the requested tooth?",
                     lambda c, v: "furcation" in v or "poor_support" in v),
}


class Example(BaseModel):
    preauth_id: str  # resubmissions: "<first request id>/resubmission"
    clinic: str
    submitted_on: date
    decided_on: date | None  # not exported for resubmissions
    sent: dict  # the request as the clinic sent it; never the decision or the truth
    decision: str  # "approved", the letter's reason code, or UNSPECIFIED for a vague letter
    truth: dict | None = None  # first requests only: after a fix the recorded truth no longer describes the tooth
    true_reason: str | None = None  # answer key: what a denial letter would name if it weren't vague; grading only


def load_examples(root: Path = CROWNS) -> list[Example]:
    out = []
    for f in sorted(root.glob("*.json")):
        d = json.loads(f.read_text())
        sent = {k: d[k] for k in SENT}
        dec = d["decision"]
        out.append(Example(preauth_id=d["preauth_id"], clinic=d["provider"]["provider_id"], submitted_on=d["submitted_date"],
                           decided_on=d["decision_date"], sent=sent, decision=dec["reason_code"] or "approved", truth=d["_generator_truth"],
                           true_reason=d["_generator_truth"]["denial_reason"]))
        fu = d.get("followup")
        if fu and fu.get("changes") is not None:
            out.append(Example(preauth_id=f"{d['preauth_id']}/resubmission", clinic=d["provider"]["provider_id"],
                               submitted_on=fu["submitted_date"], decided_on=None, sent=resubmitted(sent, fu),
                               decision="approved" if fu["outcome"] == "approved" else fu["reason_code"],
                               true_reason=d["_generator_truth"]["resubmission_denial_reason"]))
    return out


def resubmitted(sent: dict, followup: dict) -> dict:
    """The first request with the clinic's changes applied: new films or charts replace the old ones."""
    s, ch = copy.deepcopy(sent), followup["changes"]
    s["submitted_date"] = followup["submitted_date"]
    added = {a["type"] for a in ch.get("added_attachments", [])}
    s["attachments"] = [a for a in s["attachments"] if a["type"] not in added] + ch.get("added_attachments", [])
    if "perio_summary" in ch:
        s["perio_summary"] = ch["perio_summary"]
    if "lab_codes" in ch:
        s["services"][0]["lab_codes"] = ch["lab_codes"]
    if "clinical_notes" in ch:
        s["clinical_notes"] = ch["clinical_notes"]
    if done := ch.get("completed_treatment"):
        svc = s["services"][0]
        plan = s["treatment_plan"] or {"pending": [{"code": svc["procedure_code"], "tooth": int(svc["tooth"])}], "completed": []}
        finished = {(t["code"], t["tooth"]) for t in done}
        plan["pending"] = [p for p in plan["pending"] if (p["code"], p["tooth"]) not in finished]
        plan["completed"] = plan["completed"] + done
        s["treatment_plan"] = plan
    return s


def split_by_clinic(examples: list[Example], seed: int = 2026, n_test: int = 8, n_calib: int = 5) -> dict[str, list[Example]]:
    """No clinic in two splits: a clinic's documentation habits would otherwise leak into the test score."""
    clinics = sorted({e.clinic for e in examples})
    random.Random(seed).shuffle(clinics)
    role = {c: "test" for c in clinics[:n_test]} | {c: "calib" for c in clinics[n_test:n_test + n_calib]}
    parts: dict[str, list[Example]] = {"train": [], "calib": [], "test": []}
    for e in examples:
        parts[role.get(e.clinic, "train")].append(e)
    return parts


def note_labels(e: Example) -> dict[str, bool] | None:
    if e.truth is None:
        return None
    c, v = e.truth["clinical"], set(e.truth["violations"])
    return {q: rule(c, v) for q, (_, rule) in NOTE_QUESTIONS.items()}


def request_text(e: Example) -> str:
    """The request as one short text for Laya: structured summary first, then the clinic's own words."""
    s, as_of = e.sent, e.submitted_on
    svc = s["services"][0]
    tooth = int(svc["tooth"])
    att = {a["type"]: a for a in s["attachments"]}
    lines = [f"Crown {svc['procedure_code']} on tooth {tooth} ({tooth_class(tooth).replace('_', ' ')}). "
             f"Member age {s['member']['age_band']}. Lab codes: {', '.join(svc.get('lab_codes') or []) or 'none'}.",
             f"Films: periapical {_age(att.get('periapical_radiograph'), as_of)}; bitewings {_age(att.get('bitewing_radiographs'), as_of)}"
             + (f" ({att['bitewing_radiographs']['count']} side)" if att.get("bitewing_radiographs", {}).get("count") == 1 else "") + "."]
    p = s["perio_summary"]
    if p:
        sites = f"depths at tooth {'/'.join(map(str, p['tooth_sites_mm']))} mm, bleeding {'yes' if p['bop_at_tooth'] else 'no'}" \
            if p["tooth_sites_mm"] else "no site depths"
        furc = f", furcation class {p['furcation_class']}" if p.get("furcation_class") else ""
        lines.append(f"Perio: {p['chart_type'].replace('_', ' ')} chart {_age(p, as_of)}, highest PSR {max(p['psr'].values())}, {sites}{furc}.")
    else:
        lines.append("Perio: none sent.")
    plan = s["treatment_plan"]
    if plan:
        lines.append("Plan pending: " + ", ".join(_tx(t) for t in plan["pending"]) + ". Completed: " + (", ".join(_tx(t) for t in plan["completed"]) or "none") + ".")
    if months := s["prior_history"].get("same_tooth_crown_months_ago"):
        lines.append(f"Prior crown on this tooth {months} months ago.")
    lines.append(f"Note: {s['clinical_notes']}")
    if s["narrative"]:
        lines.append(f"Narrative: {s['narrative']}")
    return "\n".join(lines)


def features(e: Example, pack: RulePack, clinic_denial_rate: float | None) -> dict[str, float | str | None]:
    """Structured inputs for the tree model: the engine's reading of each requirement plus the raw values it
    can't weigh (film ages, depths). Numbers stay None when not sent, so the model learns absence."""
    s, as_of = e.sent, e.submitted_on
    record = {**s, "preauth_id": e.preauth_id, "decision": {"status": "unknown"}}  # to_case reads only what was sent
    a = assess(to_case(record, to_submission(record)), pack)
    att = {x["type"]: x for x in s["attachments"]}
    p, plan, svc = s["perio_summary"] or {}, s["treatment_plan"], s["services"][0]
    f: dict[str, float | str | None] = {f"req_{r.requirement_id}": r.status.value for r in a.requirements}
    f |= {
        "verdict": a.verdict.value,
        "tooth_class": tooth_class(int(svc["tooth"])),
        "age_band": s["member"]["age_band"],
        "channel": s["submission_channel"],
        "pa_age_days": _days(att.get("periapical_radiograph"), as_of),
        "bw_sides": att["bitewing_radiographs"]["count"] if "bitewing_radiographs" in att else 0,
        "perio_age_days": _days(p or None, as_of),
        "perio_complete": float(p.get("chart_type") == "complete") if p else None,
        "max_psr": max(p["psr"].values()) if p else None,
        "max_depth_at_tooth": max(p["tooth_sites_mm"]) if p.get("tooth_sites_mm") else None,
        "bleeding_at_tooth": float(p["bop_at_tooth"]) if p.get("bop_at_tooth") is not None else None,
        "furcation_class": p.get("furcation_class"),
        "plan_sent": float(plan is not None),
        "pending_other": float(len(plan["pending"]) - 1) if plan else None,
        "prior_crown_months": s["prior_history"].get("same_tooth_crown_months_ago"),
        "note_chars": float(len(s["clinical_notes"])),
        "has_narrative": float(bool(s["narrative"])),
        "clinic_denial_rate": clinic_denial_rate,
    }
    return f


def clinic_denial_rates(examples: list[Example], min_n: int = 3) -> dict[str, float | None]:
    """Each request's clinic denial rate over decisions already received when it was sent, so no request sees
    its own outcome or a later one. None until the clinic has min_n such decisions."""
    rates: dict[str, float | None] = {}
    for e in examples:
        prior = [x for x in examples if x.clinic == e.clinic and x.decided_on and x.decided_on < e.submitted_on]
        rates[e.preauth_id] = sum(x.decision != "approved" for x in prior) / len(prior) if len(prior) >= min_n else None
    return rates


def _days(attachment: dict | None, as_of: date) -> float | None:
    return float((as_of - date.fromisoformat(attachment["captured_date"])).days) if attachment else None


def _age(attachment: dict | None, as_of: date) -> str:
    days = _days(attachment, as_of)
    return "not sent" if days is None else f"{int(days)} days old"


def _tx(t: dict) -> str:
    return t["code"] + (f" #{t['tooth']}" if t.get("tooth") else "")
