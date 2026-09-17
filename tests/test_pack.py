"""The rule pack loads, lints, and refuses to load when a citation or precedence is broken."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from colombus.cdm.models import ArtifactType
from colombus.rules.loader import PACKS_DIR, default_pack, load_pack
from colombus.rules.schema import Clause, Find, FindP, OneOf, Predicate, RequireAll, RulePack

PACK_PATH = PACKS_DIR / "cdcp" / "2026-01-26" / "pack.yaml"


@pytest.fixture(scope="module")
def pack() -> RulePack:
    return load_pack(PACK_PATH)


def _finds(p: Predicate) -> list[Find]:
    if isinstance(p, FindP):
        return [p.find]
    if isinstance(p, OneOf):
        return [f for o in p.one_of for f in _finds(o.predicate())]
    if isinstance(p, RequireAll):
        return [f for q in p.require_all for f in _finds(q)]
    return []


def _clauses(pack: RulePack) -> list[tuple[str, Clause]]:
    out: list[tuple[str, Clause]] = []
    for r in pack.requirements:
        c: Clause | None = r.clause
        while c is not None:
            out.append((r.id, c))
            c = c.also
    out += [(f"criterion:{k}", v.clause) for k, v in pack.assertion_criteria.items()]
    out += [(f"retired:{r.code}", r.clause) for r in pack.schedule.retired_codes]
    out += [(f"excluded:{e.prefix}", e.clause) for e in pack.schedule.excluded_families]
    return out


def test_loads_and_is_content_hashed(pack: RulePack):
    assert pack.id == "cdcp-preauth-crowns" and pack.version == "2026.01.26"
    assert pack.content_hash is not None and pack.content_hash.startswith("sha256:")
    assert len(pack.content_hash) == len("sha256:") + 64
    assert default_pack().content_hash == pack.content_hash  # the default pack is this file


def test_every_clause_cites_a_declared_source(pack: RulePack):
    for owner, c in _clauses(pack):
        assert c.source in pack.sources, f"{owner} cites unknown source {c.source!r}"
        assert c.ref.strip(), f"{owner} has an empty ref"
    assert {"matrix", "guide", "grid", "factsheet"} <= set(pack.sources)


def test_every_referenced_assertion_criterion_exists(pack: RulePack):
    referenced = {f.criterion for r in pack.requirements for f in _finds(r.satisfied_by)
                  if f.artifact_type == ArtifactType.CLINICIAN_ASSERTION}
    assert referenced, "expected at least one assertion criterion in the crown pack"
    assert referenced <= set(pack.assertion_criteria)


def test_every_escalation_demand_resolves(pack: RulePack):
    for r in pack.requirements:
        option_ids = {o.id for o in r.satisfied_by.one_of} if isinstance(r.satisfied_by, OneOf) else set()
        for e in r.escalations:
            assert e.demand in option_ids | {"sextant_perio_charting"}, f"{r.id}: {e.id} demands {e.demand!r}"


def test_escalation_precedences_unique(pack: RulePack):
    for r in pack.requirements:
        precs = [e.precedence for e in r.escalations]
        assert len(precs) == len(set(precs)), f"{r.id}: duplicate precedence"
    perio = pack.requirement("perio_chart")
    by_id = {e.id: e.precedence for e in perio.escalations}
    # Footnote 7: the full-chart demand supersedes the sextant demand when both fire.
    assert by_id["psr_requires_full_chart"] > by_id["psr_requires_sextant_chart"]


def test_requirement_ids_unique(pack: RulePack):
    ids = [r.id for r in pack.requirements]
    assert len(ids) == len(set(ids))


def _mutated(tmp_path: Path, mutate) -> Path:
    data = yaml.safe_load(PACK_PATH.read_text())
    mutate(data)
    p = tmp_path / "pack.yaml"
    p.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
    return p


def test_unknown_source_is_rejected(tmp_path: Path):
    def mutate(d):
        d["requirements"][0]["clause"]["source"] = "blog_post"
    with pytest.raises(ValueError, match="unknown source"):
        load_pack(_mutated(tmp_path, mutate))


def test_unknown_assertion_criterion_is_rejected(tmp_path: Path):
    def mutate(d):
        req = next(r for r in d["requirements"] if r["id"] == "extensively_restored")
        req["satisfied_by"]["find"]["criterion"] = "not_a_criterion"
    with pytest.raises(ValueError, match="unknown assertion criterion"):
        load_pack(_mutated(tmp_path, mutate))


def test_duplicate_escalation_precedence_is_rejected(tmp_path: Path):
    def mutate(d):
        req = next(r for r in d["requirements"] if r["id"] == "perio_chart")
        for e in req["escalations"]:
            e["precedence"] = 100
    with pytest.raises(ValueError, match="precedence"):
        load_pack(_mutated(tmp_path, mutate))


def test_unknown_escalation_demand_is_rejected(tmp_path: Path):
    def mutate(d):
        req = next(r for r in d["requirements"] if r["id"] == "perio_chart")
        req["escalations"][0]["demand"] = "rationale_path"
    with pytest.raises(ValueError, match="unknown option"):
        load_pack(_mutated(tmp_path, mutate))


def test_mutation_changes_hash(tmp_path: Path, pack: RulePack):
    def mutate(d):
        d["verified_on"] = "2026-09-18"
    assert load_pack(_mutated(tmp_path, mutate)).content_hash != pack.content_hash
