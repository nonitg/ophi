"""Packet assembler: turns a case plus its assessment into the files a human submits.

Only evidence the deterministic engine matched to a satisfied or at-risk requirement ships; stale or
unmatched artifacts never do. `manifest.json` records every file with its hash and spec checks so the
independent verifier (a separate program) can re-check the packet from scratch.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from ophi.cdm.models import ArtifactType, Case, ChartArtifact
from ophi.engine.models import Assessment, Status
from ophi.packet import documents, plates
from ophi.packet.files import PacketFile, packet_filename
from ophi.packet.labels import artifact_label, fmt_date, radiograph_descriptor
from ophi.packet.narrative import draft_narrative
from ophi.rules.loader import default_pack
from ophi.rules.schema import RulePack

if TYPE_CHECKING:
    from ophi.service import SignOff

PACKET_VERSION = 1
MAX_FILES = 30
MAX_BYTES = 7_000_000
INDEX_NAME = "00_index.txt"
CLAIM_FORM_NAME = "01_claim_form_treatment_form.pdf"
SHIPPABLE = (Status.SATISFIED, Status.AT_RISK)


class PacketBudgetError(RuntimeError):
    """The packet exceeds CDCP's 30-file / 7 MB limit and nothing in it is optional."""


def build_packet(case: Case, assessment: Assessment, out_dir: Path, narrative_text: str | None = None,
                 sign_off: SignOff | None = None, pack: RulePack | None = None) -> dict:
    pack = pack or default_pack()
    out_dir = Path(out_dir)
    _reset_dir(out_dir)
    text = narrative_text if narrative_text is not None else draft_narrative(case, assessment, pack)
    prepared_on = assessment.submission_date_assumed

    files: list[PacketFile] = []
    files.append(PacketFile(1, CLAIM_FORM_NAME, out_dir / CLAIM_FORM_NAME, "claim_form",
                            f"computer-generated treatment form, prepared {fmt_date(prepared_on)}", ["claim_form"],
                            spec=documents.render_claim_form(case, out_dir / CLAIM_FORM_NAME, sign_off, prepared_on)))
    for artifact, rids in _shippable_evidence(case, assessment):
        files.append(_render_evidence(artifact, rids, case, len(files) + 1, out_dir))
    files += _narrative_files(text, case, assessment, len(files) + 1, out_dir)
    files.insert(0, _write_index(files, case, assessment, out_dir, signed=sign_off is not None))
    _check_budget(files)

    documents.render_preview(case, assessment, pack, text, files, sign_off, out_dir / "preview.pdf")
    manifest = _manifest(case, assessment, files, text, sign_off)
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def _reset_dir(out_dir: Path) -> None:
    if out_dir.exists():
        if any(out_dir.iterdir()) and not (out_dir / "manifest.json").exists():
            raise FileExistsError(f"{out_dir} is not empty and is not a Ophi packet; refusing to wipe it")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)


def _shippable_evidence(case: Case, assessment: Assessment) -> list[tuple[ChartArtifact, list[str]]]:
    """Renderable artifacts cited by satisfied/at-risk requirements, in requirement order, deduplicated."""
    by_id: dict[str, list[str]] = {}
    for r in assessment.requirements:
        if r.status not in SHIPPABLE:
            continue
        for e in r.evidence:
            a = case.artifact(e.artifact_id)
            if a and a.type in (ArtifactType.RADIOGRAPH, ArtifactType.PERIO_CHART, ArtifactType.PSR):
                by_id.setdefault(a.artifact_id, [])
                if r.requirement_id not in by_id[a.artifact_id]:
                    by_id[a.artifact_id].append(r.requirement_id)
    return [(case.artifact(aid), rids) for aid, rids in by_id.items()]  # type: ignore[misc]


def _render_evidence(a: ChartArtifact, rids: list[str], case: Case, seq: int, out_dir: Path) -> PacketFile:
    if a.type == ArtifactType.RADIOGRAPH:
        name = packet_filename(seq, rids[0], "radiograph", radiograph_descriptor(a), a.captured_at, "png")
        spec = plates.render_radiograph_plate(a, out_dir / name)
        kind = "radiograph"
    elif a.type == ArtifactType.PERIO_CHART:
        name = packet_filename(seq, rids[0], "perio_chart", f"6-site-{a.payload.point_count}-sites", a.captured_at, "pdf")  # type: ignore[union-attr]
        spec = plates.render_perio_chart(a, case, out_dir / name)
        kind = "perio_chart"
    else:
        name = packet_filename(seq, rids[0], "psr", "sextants-S1-S6", a.captured_at, "pdf")
        spec = plates.render_psr(a, out_dir / name)
        kind = "psr"
    desc = f"{artifact_label(a)}, captured {fmt_date(a.captured_at)}"
    if "synthesized placeholder plate" in spec.get("transformations", []):
        desc += " [placeholder plate: Fictional Data ships no image pixels]"
    return PacketFile(seq, name, out_dir / name, kind, desc, rids, a.artifact_id, a.captured_at, spec)


def _narrative_files(text: str, case: Case, assessment: Assessment, seq: int, out_dir: Path) -> list[PacketFile]:
    # The narrative carries plan details (footnote 1) and the clinician assertions, so it supports
    # every requirement those assertions satisfied.
    rids = ["tx_plan_details"] + [r.requirement_id for r in assessment.requirements
                                  if r.status in SHIPPABLE and r.requirement_id != "tx_plan_details"
                                  and any(e.type == ArtifactType.CLINICIAN_ASSERTION.value for e in r.evidence)]
    docx_name = packet_filename(seq, "tx_plan_details", "narrative", "rationale", case.as_of, "docx")
    txt_name = packet_filename(seq + 1, "tx_plan_details", "narrative", "rationale", case.as_of, "txt")
    docx_spec = documents.render_narrative_docx(text, out_dir / docx_name)
    (out_dir / txt_name).write_text(documents.narrative_ascii(text), encoding="ascii")
    txt_spec = {**documents.DOC_SPEC, "format": "TXT", "transformations": ["transliterated to ASCII"]}
    desc = f"documentation narrative with clinical findings quoted from the chart and clinician assertions, prepared {fmt_date(assessment.submission_date_assumed)}"
    return [PacketFile(seq, docx_name, out_dir / docx_name, "narrative", desc, rids, spec=docx_spec),
            PacketFile(seq + 1, txt_name, out_dir / txt_name, "narrative_txt", f"{desc} (ASCII text copy)", rids, spec=txt_spec)]


def _index_line(f: PacketFile, assessment: Assessment) -> str:
    cites = []
    for rid in f.requirement_ids:
        r = assessment.requirement(rid)
        cites.append(f"{rid}, {r.clause.source} {r.clause.ref}" if r else rid)
    failure = f" SPEC CHECK FAILED: {f.spec_failure}." if f.spec_failure else ""
    return f"{f.seq:02d}  {f.filename} — {f.description}; supports {'; '.join(cites)}.{failure}"


def _write_index(files: list[PacketFile], case: Case, assessment: Assessment, out_dir: Path, signed: bool) -> PacketFile:
    t = case.treatment
    lines = [
        "Ophi packet index" + (" — TEST RUN, chart gaps skipped, not for submission" if assessment.test_run
                               else "" if signed else " — DRAFT, not signed, not for submission"),
        f"Clinic: {case.clinic}",
        f"Reference: {assessment.assessment_id}",
        f"Procedure: {t.code} ({t.description or 'no description'}) on tooth #{t.tooth.tooth_fdi} (FDI)",
        f"Ruleset: {assessment.ruleset.id} {assessment.ruleset.version}",
        "Prepared for review; submitted by the treating provider.",
        "",
        f"00  {INDEX_NAME} — this index",
        *(_index_line(f, assessment) for f in files),
    ]
    text = documents.narrative_ascii("\n".join(lines) + "\n")
    (out_dir / INDEX_NAME).write_text(text, encoding="ascii")
    spec = {**documents.DOC_SPEC, "format": "TXT"}
    return PacketFile(0, INDEX_NAME, out_dir / INDEX_NAME, "index", "index of the files in this packet", [], spec=spec)


def _check_budget(files: list[PacketFile]) -> None:
    # Every file here is required evidence or the mandated index/form, so the plan's fallbacks
    # (recompress colour photos, drop optional duplicates, merge text) have nothing to act on.
    # Radiographs are never recompressed. Over budget, stop and let the human decide.
    total = sum(f.bytes for f in files)
    if len(files) <= MAX_FILES and total <= MAX_BYTES:
        return
    listing = "\n".join(f"  {f.filename}: {f.bytes:,} bytes" for f in files)
    raise PacketBudgetError(f"packet has {len(files)} files / {total:,} bytes; limit is {MAX_FILES} files / {MAX_BYTES:,} bytes\n{listing}")


def _manifest(case: Case, assessment: Assessment, files: list[PacketFile], text: str, sign_off: SignOff | None) -> dict:
    txt = next(f for f in files if f.kind == "narrative_txt")
    return {
        "packet_version": PACKET_VERSION,
        "case_id": case.case_id,
        "assessment_id": assessment.assessment_id,
        "engine_version": assessment.engine_version,
        "ruleset": {"id": assessment.ruleset.id, "version": assessment.ruleset.version, "content_hash": assessment.ruleset.content_hash},
        "built_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "file_count": len(files),
        "total_bytes": sum(f.bytes for f in files),
        "preview": "preview.pdf",
        "status": "signed" if sign_off else "draft",
        "test_run": assessment.test_run,
        "verdict": assessment.verdict.value,
        "narrative_sha256": hashlib.sha256(txt.path.read_bytes()).hexdigest(),
        "attestation": sign_off.model_dump(mode="json") if sign_off else None,
        "files": [f.manifest_entry() for f in files],
    }
