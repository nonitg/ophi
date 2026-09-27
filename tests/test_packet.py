"""Packet assembler: every demo case builds a packet whose manifest, files, index and narrative hold."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from PIL import Image

from ophi.casegen.dsl import load_case
from ophi.cdm.models import FileRef
from ophi.engine.assess import assess
from ophi.extract.proposer import propose_for_case
from ophi.packet.build import MAX_BYTES, MAX_FILES, build_packet
from ophi.packet.narrative import draft_narrative, validate_narrative
from ophi.packet.plates import render_radiograph_plate
from ophi.rules.loader import pack_for

ROOT = Path(__file__).resolve().parents[1]
CASES = sorted((ROOT / "cases" / "demo").glob("*.yaml"))
MANIFEST_KEYS = {"packet_version", "case_id", "assessment_id", "engine_version", "ruleset", "built_at", "file_count",
                 "total_bytes", "preview", "status", "test_run", "verdict", "narrative_sha256", "attestation", "files"}
FILE_KEYS = {"seq", "filename", "sha256", "bytes", "media_type", "kind", "requirement_ids", "artifact_id", "captured_at",
             "spec_checks", "transformations_applied"}
SPEC_KEYS = {"dpi", "bit_depth", "format", "colour", "pass"}


def _assessed(path: Path):
    case = load_case(path)
    case = case.with_artifacts(propose_for_case(case))
    return case, assess(case, pack_for(case))


@pytest.fixture(params=CASES, ids=[p.stem for p in CASES])
def built(request, tmp_path):
    case, assessment = _assessed(request.param)
    manifest = build_packet(case, assessment, tmp_path)
    return case, assessment, tmp_path, manifest


def test_manifest_shape_and_file_integrity(built):
    case, assessment, out, manifest = built
    assert set(manifest) == MANIFEST_KEYS
    assert manifest["packet_version"] == 1
    assert manifest["case_id"] == case.case_id and manifest["assessment_id"] == assessment.assessment_id
    assert manifest["ruleset"] == assessment.ruleset.model_dump(mode="json", include={"id", "version", "content_hash"})
    assert manifest["attestation"] is None
    assert json.loads((out / "manifest.json").read_text()) == manifest
    assert (out / manifest["preview"]).stat().st_size > 0

    assert manifest["file_count"] == len(manifest["files"]) <= MAX_FILES
    assert manifest["total_bytes"] == sum(f["bytes"] for f in manifest["files"]) <= MAX_BYTES
    assert [f["seq"] for f in manifest["files"]] == list(range(len(manifest["files"])))
    for f in manifest["files"]:
        assert set(f) == FILE_KEYS and set(f["spec_checks"]) == SPEC_KEYS
        data = (out / f["filename"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == f["sha256"] and len(data) == f["bytes"]
    kinds = {f["kind"] for f in manifest["files"]}
    assert {"index", "claim_form", "narrative", "narrative_txt"} <= kinds
    # Only the packet's own files count; manifest and preview live beside them.
    first = manifest["files"][0]
    assert (first["seq"], first["filename"], first["kind"]) == (0, "00_index.txt", "index")
    on_disk = {p.name for p in out.iterdir()} - {"manifest.json", "preview.pdf"}
    assert on_disk == {f["filename"] for f in manifest["files"]}


def test_index_is_ascii_and_lists_every_file(built):
    _, _, out, manifest = built
    index = (out / "00_index.txt").read_text()
    assert index.isascii()
    for f in manifest["files"][1:]:
        assert f["filename"] in index


def test_filenames_carry_no_patient_identity(built):
    case, _, _, manifest = built
    tokens = [t.lower() for t in case.patient.display_name.replace(",", " ").split() if len(t) >= 3]
    for f in manifest["files"]:
        assert not any(t in f["filename"].lower() for t in tokens), f["filename"]


def test_narrative_is_grounded_and_shipped_as_ascii(built):
    case, assessment, out, manifest = built
    draft = draft_narrative(case, assessment, pack_for(case))
    assert validate_narrative(draft, case) == []
    txt = next(f for f in manifest["files"] if f["kind"] == "narrative_txt")
    body = (out / txt["filename"]).read_bytes()
    assert body.isascii()
    assert hashlib.sha256(body).hexdigest() == manifest["narrative_sha256"]
    assert "Clinical findings recorded in the chart" in body.decode()


def test_plates_are_8bit_greyscale_at_300_dpi(built):
    case, _, out, manifest = built
    plates = [f for f in manifest["files"] if f["kind"] == "radiograph"]
    shipped_radiographs = {f["artifact_id"] for f in plates}
    for f in plates:
        with Image.open(out / f["filename"]) as im:
            assert im.mode == "L"
            assert tuple(round(x) for x in im.info["dpi"]) == (300, 300)
        assert f["spec_checks"] == {"dpi": 300, "bit_depth": 8, "format": "PNG", "colour": "greyscale", "pass": True}
        assert f["transformations_applied"] == ["synthesized placeholder plate"]
    # Stale radiographs the engine did not match must never ship.
    for a in case.artifacts_of("radiograph"):
        if a.artifact_id in ("pa_46_2023", "pa_16_2023"):
            assert a.artifact_id not in shipped_radiographs


def test_narrative_variant_and_assertions_for_whitfield():
    case, assessment = _assessed(ROOT / "cases" / "demo" / "whitfield.yaml")
    text = draft_narrative(case, assessment, pack_for(case))
    assert "Dr. Priya Lau (ON-48213) confirmed on 2026-09-15: Adequate ferrule (1.5 mm)." in text
    assert "Non-endodontically treated: 5 continuous surfaces" in text
    assert "“36 five-surface amalgam" in text


def test_validator_flags_ungrounded_text():
    case, _ = _assessed(ROOT / "cases" / "demo" / "rosco.yaml")  # no perio chart, so #47 is not in this case
    bad = "Radiograph dated 2019-01-01 of #47. “not in any note” This tooth is eligible and will be approved."
    violations = validate_narrative(bad, case)
    assert any("2019-01-01" in v for v in violations)
    assert any("#47" in v for v in violations)
    assert any("not verbatim" in v for v in violations)
    assert any("eligible" in v for v in violations) and any("will be approved" in v for v in violations)


def _radiograph_with_file(case, path: Path):
    rad = next(a for a in case.artifacts if a.type == "radiograph")
    return rad.model_copy(update={"file": FileRef(path=str(path))})


def test_rgb_greyscale_jpeg_is_converted_to_8bit_L(tmp_path):
    case, _ = _assessed(ROOT / "cases" / "demo" / "whitfield.yaml")
    src = tmp_path / "bridge_export.jpg"
    grey = Image.linear_gradient("L").resize((400, 300))
    Image.merge("RGB", (grey, grey, grey)).save(src, "JPEG", quality=95, dpi=(300, 300))

    spec = render_radiograph_plate(_radiograph_with_file(case, src), tmp_path / "plate.png")

    assert spec["pass"] is True
    assert spec["dpi"] == 300 and spec["bit_depth"] == 8 and spec["colour"] == "greyscale" and spec["format"] == "PNG"
    assert "converted 24-bit colour to 8-bit greyscale" in spec["transformations"]
    with Image.open(tmp_path / "plate.png") as im:
        assert im.mode == "L" and im.size == (400, 300)


def test_low_dpi_radiograph_fails_spec_and_is_not_upsampled(tmp_path):
    case, _ = _assessed(ROOT / "cases" / "demo" / "whitfield.yaml")
    src = tmp_path / "low.png"
    Image.new("L", (300, 200), 90).save(src, "PNG", dpi=(96, 96))

    spec = render_radiograph_plate(_radiograph_with_file(case, src), tmp_path / "plate.png")

    assert spec["pass"] is False and spec["dpi"] == 96
    assert "not upsampled" in spec["reason"]
    with Image.open(tmp_path / "plate.png") as im:
        assert im.size == (300, 200)
