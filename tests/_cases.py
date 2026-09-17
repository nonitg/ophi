"""Shared builders for engine tests.

`ready_dict()` is a fully documented PFM crown on #46 that the engine must read as READY_TO_SUBMIT.
Every engine test perturbs exactly one thing from it, so a verdict change is attributable to that
perturbation and nothing else. Ages are relative to `as_of` so the case never goes stale.
"""

from __future__ import annotations

import copy
from pathlib import Path

from colombus.casegen.dsl import build_case, load_case
from colombus.engine.assess import assess
from colombus.engine.models import Assessment
from colombus.extract.proposer import propose_for_case
from colombus.rules.loader import default_pack

ROOT = Path(__file__).resolve().parents[1]
CASES_DIR = ROOT / "cases"
EXPECTED_DIR = ROOT / "evals" / "expected"

ALL_CRITERIA = [
    "no_active_perio", "crown_root_ratio", "no_furcation", "margin_3mm", "ferrule_1_5mm",
    "mesiodistal_space", "no_adjunctive_needed", "extensively_restored", "active_disease_addressed",
]

_READY: dict = {
    "id": "inline",
    "as_of": "2026-09-17",
    "patient": {"id": "9001", "name": "Base Patient", "dob": "1975-05-20", "sex": "F", "cdcp_client_id": "CDCP-0000-9001"},
    "provider": {"name": "Dr. Priya Lau", "licence": "ON-48213"},
    "treatment": {"code": "27211", "description": "Crown, porcelain fused to metal", "tooth": 46,
                  "planned": "10d", "appointment": "2026-09-27", "fee_cents": 128500, "lab_codes": ["99112"]},
    "dentition": {"missing": [18, 28, 38, 48], "restored_surfaces": {46: ["M", "O", "D", "B", "L"]}},
    "history": [
        {"code": "21225", "tooth": 46, "surfaces": ["M", "O", "D", "B", "L"], "date": "2020-03-10"},
        {"code": "01202", "age": "40d"},
    ],
    "radiographs": [
        {"id": "pa_46", "view": "PA", "tooth": 46, "age": "40d"},
        {"id": "bw_r", "view": "BW", "side": "right", "teeth": [14, 15, 16, 17, 44, 45, 46, 47], "age": "40d"},
        {"id": "bw_l", "view": "BW", "side": "left", "teeth": [24, 25, 26, 27, 34, 35, 36, 37], "age": "40d"},
    ],
    "perio_charts": [{"id": "perio_full", "age": "40d", "sites": 6, "depth": 2, "examiner": "K. Osei RDH"}],
    "notes": [{"id": "note_1", "age": "40d", "author": "Dr. Priya Lau", "teeth": [46],
               "text": "46 five-surface amalgam, fractured lingual cusp. Plan PFM crown 46. No other treatment outstanding."}],
    "tx_plans": [{"id": "plan_46", "age": "40d", "pending": ["27211"], "completed": ["21225", "01202"]}],
    "assertions": [{"criterion": c, "age": "2d"} for c in ALL_CRITERIA],
}


def ready_dict() -> dict:
    return copy.deepcopy(_READY)


def assess_dict(d: dict, case_id: str = "inline", with_proposer: bool = False) -> Assessment:
    case = build_case(d, case_id)
    if with_proposer:
        case = case.with_artifacts(propose_for_case(case))
    return assess(case, default_pack())


def assess_path(path: Path) -> Assessment:
    """Same pipeline as the CLI and the eval runner: casegen -> proposer -> engine."""
    case = load_case(path)
    case = case.with_artifacts(propose_for_case(case))
    return assess(case, default_pack())


def corpus_files() -> list[Path]:
    return sorted(CASES_DIR.rglob("*.yaml"))
