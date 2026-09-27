"""Past crown requests like this case, for one fix step: what Sun Life approved with the fix in place (resent after
the fix first) and what it denied for the reason the fix addresses. Secondary evidence under a step's "Why".

Counts come from every clinic's requests: an aggregate identifies no one and is the whole value of the corpus.
The linked examples are the viewer's own clinic only, since each one opens an identifiable request.

Nearest neighbour on the structured request (Gower distance over the training features), not text embeddings: a
few hundred rows with the same fields the models read, so the ranking stays explainable and needs no vector index.
"""

from __future__ import annotations

import logging
from collections import Counter

from ophi.cdm.models import Case
from ophi.outcomes import past_store
from ophi.outcomes.case_export import to_export
from ophi.outcomes.denial_map import load_denial_map
from ophi.outcomes.past_store import Cached
from ophi.outcomes.past_view import reason, resent_approved
from ophi.outcomes.training_set import Example, features
from ophi.rules.schema import RulePack

log = logging.getLogger("uvicorn.error")

CROWN = "27"  # v1 scope: only crown requests are like a crown request
SHOWN = 2  # examples per side; the counts carry the rest
CATEGORICAL = ("tooth", "code", "age_band")  # tooth class leads the ranking, so it is not repeated here
# The document a step is about: an old one and none at all are different gaps (and different denial letters).
SENT_FOR = {"radiograph_pa": "pa_age_days", "perio_chart": "perio_age_days"}
NUMERIC = ("pa_age_days", "perio_age_days", "perio_complete", "max_psr", "max_depth_at_tooth", "bleeding_at_tooth", "prior_crown_months")


def case_profile(case: Case, pack: RulePack) -> dict:
    """The case as the past rows describe a request: the training features plus tooth and code."""
    sent = to_export(case)
    e = Example(preauth_id=case.case_id, clinic="", submitted_on=case.as_of, decided_on=None, sent=sent)
    return {**features(e, pack, None), "tooth": case.requested_tooth, "code": case.treatment.code}


def _profile(row: dict) -> dict:
    return {**(row["features"] or {}), "tooth_class": row["tooth_class"], "age_band": row["age_band"],
            "tooth": row["tooth_fdi"], "code": row["procedure_code"], "featurized": row["features"] is not None}


def _spans(profiles: list[dict]) -> dict[str, float]:
    spans = {}
    for k in NUMERIC:
        vals = [p[k] for p in profiles if p.get(k) is not None]
        spans[k] = (max(vals) - min(vals)) if vals else 0.0
    return spans


def _gower(a: dict, b: dict, spans: dict[str, float]) -> float:
    """Mean per-field mismatch: 0 identical, 1 unlike in everything compared. A value only one side sent (a film,
    a chart) is a full mismatch, since a missing document and an old one are different denials."""
    parts = [float(a[k] != b[k]) for k in CATEGORICAL if a.get(k) is not None and b.get(k) is not None]
    for k in NUMERIC:
        x, y = a.get(k), b.get(k)
        if x is not None and y is not None:
            parts.append(abs(x - y) / spans[k] if spans[k] else 0.0)
        elif b["featurized"] and (x is None) != (y is None):  # legacy rows carry no values at all
            parts.append(1.0)
    return sum(parts) / len(parts) if parts else 1.0


def _example(row: dict) -> dict:
    fixed = resent_approved(row)
    return {"id": row["preauth_id"], "outcome": "approved" if fixed else row["status"],
            "reason": reason(row["reason_code"]) if row["status"] == "denied" else None,
            "tooth": row["tooth_fdi"], "sent_on": row["submitted_on"], "resent_then_approved": fixed}


def _own(rows: list[dict], clinic: str | None) -> list[dict]:
    """The examples a clinic may open: its own requests, or all of them when the app serves no single clinic."""
    return [r for r in rows if r["clinic_id"] == clinic] if clinic else rows


def like(rows: list[dict], target: dict, requirement_ids: list[str], dmap: dict[str, list[str]],
         clinic: str | None = None) -> dict | None:
    """Both ends for one step. Approved: denied for this reason then approved on a resend, or approved with the
    requirement met. Denied: denied for a reason the step addresses and not fixed on a resend. Each side ranked
    the same kind of gap (an old film or none), same tooth class, then Gower distance (tooth, code, age band, film and
    chart ages, perio values).
    None when the past has neither."""
    rids = set(requirement_ids)
    codes = {c for c, ids in dmap.items() if rids & set(ids)}
    crowns = [r for r in rows if r["procedure_code"].startswith(CROWN)]
    # A reason can name several requirements (Missing X-ray: periapical or bitewings); keep the requests that had this gap.
    addressed = [r for r in crowns if r["status"] == "denied" and r["reason_code"] in codes
                 and (r["features"] is None or any(r["features"].get(f"req_{i}") not in ("satisfied", None) for i in rids))]
    fixed = [r for r in addressed if resent_approved(r)]
    met = [r for r in crowns if r["status"] == "approved" and any((r["features"] or {}).get(f"req_{i}") == "satisfied" for i in rids)]
    denied = [r for r in addressed if not resent_approved(r)]
    if not (fixed or met or denied):
        return None
    profiles = {r["preauth_id"]: _profile(r) for r in crowns}
    spans = _spans(list(profiles.values()))
    sent = [SENT_FOR[i] for i in rids if i in SENT_FOR]

    def rank(r: dict) -> tuple:
        p = profiles[r["preauth_id"]]
        same_gap = all((p.get(k) is None) == (target.get(k) is None) for k in sent if p["featurized"])
        return (not resent_approved(r), not same_gap, p["tooth_class"] != target["tooth_class"], _gower(target, p, spans), r["preauth_id"])

    denied.sort(key=rank)
    n = Counter(r["reason_code"] for r in denied)
    # The closest denial's reason first: for an old film, "X-ray over 12 months old" before "Missing X-ray".
    order = list(dict.fromkeys([r["reason_code"] for r in denied[:1]] + [c for c, _ in n.most_common()]))
    return {"approved": [_example(r) for r in _own(sorted(fixed + met, key=rank), clinic)[:SHOWN]],
            "denied": [_example(r) for r in _own(denied, clinic)[:SHOWN]],
            "n_resent": len(fixed), "n_approved": len(fixed) + len(met), "n_denied": len(denied),
            "reasons": [{"reason": reason(c), "n": n[c]} for c in order]}


def clinic_denial_rate(past: Cached, connect, case: Case) -> float | None:
    """The case's clinic's past denial rate for live scoring. The clinic is the sending provider, as in the exports
    training reads; None when it has no past requests on file or the database is unavailable."""
    clinic = to_export(case)["provider"]["provider_id"]
    try:
        if not any(r["clinic_id"] == clinic for r in past.rows()):
            return None
        with connect() as conn:
            return past_store.clinic_denial_rate(conn, clinic, case.as_of)
    except Exception as e:
        log.warning("clinic denial rate unavailable: %s", e)
        return None


def for_steps(past: Cached, case: Case, pack: RulePack, steps: list[list[str]],
              clinic: str | None = None) -> list[dict | None]:
    """`like` for each step's requirement ids. With the outcomes database unavailable, nothing: the page still renders."""
    try:
        rows = past.rows()
    except Exception as e:
        log.warning("similar past requests unavailable: %s", e)
        return [None] * len(steps)
    target, dmap = case_profile(case, pack), load_denial_map(pack)
    return [like(rows, target, rids, dmap, clinic) if rids else None for rids in steps]
