"""What past denials say the rule pack does not yet cover, grouped for the SME."""

from __future__ import annotations

from collections import Counter

from pydantic import BaseModel

from ophi.outcomes import store
from ophi.rules.schema import RulePack

KIND_LABELS = {
    "no_requirement": "No pack requirement covers this denial reason",
    "unmapped_reason": "Denial reason not yet reviewed in denial_map.yaml",
    "mapped_gap_not_found": "Mapped requirement was not found missing on the submission date",
}


class BlindSpot(BaseModel):
    kind: str
    label: str
    reason_code: str | None
    count: int


class OutcomesReport(BaseModel):
    pack_version: str
    blind_spots: list[BlindSpot]
    unmodelled_attachments: list[tuple[str, int]]  # attached to denied requests, never checked by the pack
    lift: list[dict]


def build(pack: RulePack) -> OutcomesReport:
    with store.connect() as conn:
        spots = store.blind_spots(conn)
        lift = store.denial_lift(conn, pack.version)
    grouped = Counter((s["kind"], s["reason_code"]) for s in spots)
    attachments = Counter(t for s in spots for t in s["unmodelled_attachments"])
    return OutcomesReport(
        pack_version=pack.version,
        blind_spots=[BlindSpot(kind=k, label=KIND_LABELS[k], reason_code=code, count=n)
                     for (k, code), n in sorted(grouped.items(), key=lambda kv: (-kv[1], kv[0]))],
        unmodelled_attachments=attachments.most_common(),
        lift=lift,
    )
