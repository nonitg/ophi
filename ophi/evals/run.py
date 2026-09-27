"""Golden-expectation regression. Every case under cases/ has an expected verdict, per-requirement
status and top action under evals/expected/<pack version>/<case>.yaml. Any changed verdict is a
failure that a human must acknowledge by rewriting the expectation (`--write`)."""

from __future__ import annotations

from pathlib import Path

import yaml

from ophi.casegen.dsl import load_case
from ophi.engine.assess import assess
from ophi.engine.models import Assessment, Status, Verdict
from ophi.extract.proposer import propose_for_case
from ophi.rules.loader import pack_for
from ophi.rules.schema import RulePack


def snapshot(a: Assessment) -> dict:
    return {
        "verdict": a.verdict.value,
        "completeness": f"{a.completeness['satisfied']}/{a.completeness['applicable']}",
        "requirements": {r.requirement_id: (r.status.value + (f" via {r.satisfied_via}" if r.satisfied_via else ""))
                         for r in a.requirements if r.applicable},
        "top_action": a.actions[0].title if a.actions else None,
        "blocking_actions": sum(1 for x in a.actions if x.blocking),
    }


def assess_file(path: Path, pack: RulePack | None = None) -> Assessment:
    case = load_case(path)
    case = case.with_artifacts(propose_for_case(case))
    return assess(case, pack or pack_for(case))  # each case under the rules for its own date


def run_all(cases_dir: Path, expected_dir: Path, write: bool = False) -> tuple[bool, str]:
    lines, ok, false_ready, packs = [], True, [], set()
    # Look-Back history is judged as of each submission date by ophi.lookback, not here.
    files = sorted(f for f in cases_dir.rglob("*.yaml") if "lookback" not in f.parts)
    for f in files:
        a = assess_file(f)
        got = snapshot(a)
        packs.add(f"{a.ruleset.id} {a.ruleset.version}")
        exp_dir = expected_dir / a.ruleset.version
        exp_dir.mkdir(parents=True, exist_ok=True)
        exp_path = exp_dir / f"{f.stem}.yaml"
        if write or not exp_path.exists():
            exp_path.write_text(yaml.safe_dump(got, sort_keys=False, allow_unicode=True))
            lines.append(f"  wrote   {f.stem}: {got['verdict']} {got['completeness']}")
            continue
        exp = yaml.safe_load(exp_path.read_text())
        if exp == got:
            lines.append(f"  pass    {f.stem}: {got['verdict']} {got['completeness']}")
        else:
            ok = False
            lines.append(f"  FAIL    {f.stem}: expected {exp['verdict']} got {got['verdict']}")
            for k in ("completeness", "top_action", "blocking_actions"):
                if exp.get(k) != got.get(k):
                    lines.append(f"            {k}: expected {exp.get(k)!r} got {got.get(k)!r}")
            for rid in sorted(set(exp["requirements"]) | set(got["requirements"])):
                if exp["requirements"].get(rid) != got["requirements"].get(rid):
                    lines.append(f"            {rid}: expected {exp['requirements'].get(rid)} got {got['requirements'].get(rid)}")
        # The unforgivable error, tracked separately: READY while any applicable requirement is not satisfied.
        if a.verdict == Verdict.READY_TO_SUBMIT and any(r.applicable and r.status != Status.SATISFIED for r in a.requirements):
            false_ready.append(f.stem)
    if false_ready:
        ok = False
        lines.append(f"  FALSE-READY: {', '.join(false_ready)}")
    head = f"eval: {len(files)} cases against {', '.join(sorted(packs))} — {'PASS' if ok else 'FAIL'}; false-ready: {len(false_ready)}"
    return ok, "\n".join([head, *lines])
