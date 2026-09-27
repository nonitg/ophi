"""A PMS chart export (lab/tools/chart_dump.py's shape) as a Case, built by the same casegen code as the demo files.

The export is translated into casegen's dialect (ophi/casegen/dsl.py) so both sources are judged identically. What
ABELDent can't show stays unknown: a radiograph billed without a tooth doesn't cover the crown, and an uncertified
perio chart stays a draft.
"""

from __future__ import annotations

from datetime import date

from ophi.casegen.dsl import build_case
from ophi.cdm.models import Case

# Radiograph procedure codes (USC&LS 02xxx, ABELDent ChartCode 242) by view.
_PA = range(2111, 2120)  # 02111-02119: periapical films
_BW = range(2141, 2145)  # 02141-02144: bitewings
_PAN = (2601,)
# A bitewing series in the export names no teeth; two or four films cover the posterior teeth on both sides.
_POSTERIOR = {"right": [14, 15, 16, 17, 44, 45, 46, 47], "left": [24, 25, 26, 27, 34, 35, 36, 37]}


def _is_cdcp(coverage: dict) -> bool:
    """A clinic sets CDCP up as a Sun Life plan, number 333333 (docs/research/cdcp-rules.md); the certificate is the
    client's CDCP number."""
    return coverage.get("plan_id") == "CDCP" or "dental care plan" in (coverage.get("plan_name") or "").lower()


def _items(chart: dict, section: str) -> list[dict]:
    s = chart.get(section)
    return s.get("items", []) if isinstance(s, dict) else []


def _radiographs(chart: dict) -> list[dict]:
    out = []
    for ev in (chart.get("imaging") or {}).get("procedure_events", []):
        code = int(ev["code"]) if str(ev.get("code", "")).isdigit() else 0
        rid, day = f"rad_{ev['trans_id']}", ev["date"]
        if code in _PA:
            out.append({"id": rid, "view": "PA", "teeth": [ev["tooth_fdi"]] if ev.get("tooth_fdi") else [], "date": day,
                        "description": ev.get("description")})
        elif code in _BW:
            out += [{"id": f"{rid}_{side}", "view": "BW", "side": side, "teeth": teeth, "date": day, "description": ev.get("description")}
                    for side, teeth in _POSTERIOR.items()]
        elif code in _PAN:
            out.append({"id": rid, "view": "PANO", "teeth": [], "date": day, "description": ev.get("description")})
    return out


def _perio_charts(chart: dict) -> list[dict]:
    out = []
    for ex in _items(chart, "perio_exams"):
        teeth = {int(t): d for t, d in ((ex.get("pocket") or {}).get("by_tooth_fdi") or {}).items() if any(v is not None for v in d)}
        if teeth:
            out.append({"id": f"perio_{ex.get('exam_num', len(out) + 1)}", "date": ex["date"], "teeth": teeth, "full_mouth": False,
                        "examiner": ex.get("provider"), "certified": bool(ex.get("date_certified"))})
    return out


def chart_to_dsl(chart: dict, crown: dict, *, case_id: str, as_of: date, providers: dict[str, str] | None = None,
                 appointment: date | None = None, clinic: str = "ABELDent", source: str = "abeldent") -> dict:
    """The export in casegen's dialect, for the planned procedure `crown`. `providers` maps PMS provider ids to names;
    `appointment` is the booked crown visit, if any."""
    p, names = chart["patient"], providers or {}
    dentist = crown.get("responsible_provider") or crown.get("provider") or p.get("dentist") or ""
    plan = [x for x in _items(chart, "planned_procedures") if x.get("plan_num") == crown.get("plan_num")]
    covs = _items(chart, "coverage")
    cdcp = next((c for c in covs if _is_cdcp(c)), None)
    cov = cdcp or next(iter(covs), None)
    films = _radiographs(chart)
    perio = _perio_charts(chart)
    latest = max(_items(chart, "perio_exams"), key=lambda e: e["date"], default=None)
    d = {
        "id": case_id, "as_of": as_of, "clinic": clinic, "source": source,
        "patient": {"id": str(p["pid"]), "name": f"{p.get('given', '')} {p.get('surname', '')}".strip().title(),
                    "dob": p.get("dob"), "sex": p.get("gender"), "cdcp_client_id": cdcp.get("certificate") if cdcp else None},
        "provider": {"name": names.get(dentist, f"Dentist {dentist}".strip()), "licence": None},
        "treatment": {"code": crown["code"], "description": crown.get("description"), "tooth": crown["tooth_fdi"],
                      "planned": crown.get("date"), "fee_cents": round(crown["fee"] * 100) if crown.get("fee") else None,
                      "surfaces": list(crown.get("surfaces") or ""), "appointment": appointment},
        "history": [{"code": h["code"], "tooth": h.get("tooth_fdi"), "surfaces": list(h.get("surfaces") or ""), "date": h["date"],
                     "description": h.get("description")} for h in _items(chart, "completed_procedures") if h.get("date")],
        "radiographs": films,
        "perio_charts": perio,
        # ABELDent stores 0xFF for a tooth that is absent or not measured; the latest exam is the best odontogram here.
        "dentition": {"missing": (latest.get("pocket") or {}).get("teeth_no_value_fdi", []) if latest else []},
        "notes": [{"id": f"note_{n.get('ref_number') or i}", "date": n["date"], "author": names.get(n.get("operator"), n.get("operator")),
                   "teeth": [n["tooth_fdi"]] if n.get("tooth_fdi") else [], "text": n.get("text") or "",
                   "signed_off": n.get("signed_off") is not False} for i, n in enumerate(_items(chart, "clinical_notes")) if n.get("date")],
        "tx_plans": [{"id": f"plan_{crown.get('plan_num')}", "date": (crown.get("plan") or {}).get("date") or crown.get("date"),
                      "description": (crown.get("plan") or {}).get("description"),
                      "pending": [x["code"] for x in plan if x.get("status") == "planned"],
                      "completed": [x["code"] for x in plan if x.get("status") == "planned_applied"]}] if plan else [],
        "coverage": {"payer": cov.get("carrier_name") or "CDCP", "plan_number": cov.get("plan_id"), "member_id": cov.get("certificate"),
                     "active": cov.get("active")} if cov else None,
    }
    if not films:  # no film on file at all: ABELDent can't tell "none taken" from "held by the imaging software"
        sa = (chart.get("imaging") or {}).get("source_assurance") or {}
        d["assurance"] = {"imaging": {"availability": "Unknown", "reason": sa.get("detail", "no radiograph in the PMS")[:300]}}
    return d


def chart_to_case(chart: dict, crown: dict, **kw) -> Case:
    return build_case(chart_to_dsl(chart, crown, **kw), kw["case_id"])
