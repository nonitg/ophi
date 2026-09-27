"""Demo timeline: put five fictional cases past sign-off, so every stage of a preauthorization's life has
a real example on the worklist. Each step goes through the same service call the dentist or staff make,
stamped on the day it happened. Runs only against an empty store.
"""

from __future__ import annotations

from datetime import date

from ophi.packet.narrative import draft_narrative
from ophi.service import CaseService
from ophi.web.present import ACTORS

# (case, signed, sent to Sun Life, Sun Life's decision: (outcome, on, reason verbatim))
TIMELINE = [
    ("fontaine", date(2026, 9, 16), None, None),
    ("park", date(2026, 9, 14), date(2026, 9, 15), None),
    ("okafor", date(2026, 9, 8), date(2026, 9, 9), None),
    ("nguyen", date(2026, 9, 1), date(2026, 9, 2), ("approved", date(2026, 9, 8), None)),
    ("marchand", date(2026, 8, 26), date(2026, 8, 27), ("denied", date(2026, 9, 3), "Denied as per the plan criteria.")),
]
# ABELDent mode (scripts/demo-abeldent.sh): the dentist has confirmed the criteria and signed, so the case is Ready to
# send. Sending, and Sun Life's answers, come from ABELDent itself (lab/fixtures/*.sql).
ABELDENT_SIGNED = [("abeldent_7", date(2026, 9, 24))]


def seed(svc: CaseService) -> None:
    if svc.store.audit_log():
        return
    dentist, coordinator = ACTORS["dentist"], ACTORS["coordinator"]
    known = set(svc.case_ids())
    for case_id, signed, sent, decision in TIMELINE + [(cid, day, None, None) for cid, day in ABELDENT_SIGNED]:
        if case_id not in known:
            continue
        with svc.at(signed):
            v = svc.view(case_id)
            if case_id.startswith("abeldent_"):  # a PMS chart carries no clinician answers: the dentist confirms them here
                open_ = sorted({c for r in v.assessment.requirements if r.applicable for c in r.shortfall.missing_assertions})
                svc.assert_many(case_id, [{"criterion_id": c, "value": "met"} for c in open_], dentist.name, dentist.licence, role=dentist.role)
                v = svc.view(case_id)
            svc.sign_off(case_id, dentist.name, dentist.licence, draft_narrative(v.case, v.assessment, v.pack), role=dentist.role)
        if sent:
            with svc.at(sent):
                svc.mark_submitted(case_id, coordinator.name, on=sent)
        if decision:
            outcome, on, reason = decision
            with svc.at(on):
                svc.record_decision(case_id, outcome, on, reason, coordinator.name)
