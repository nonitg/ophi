"""Independent verifier: a good synthetic packet passes; each spec violation yields one precise finding."""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

import docx
import pytest
from PIL import Image
from reportlab.pdfgen import canvas

from colombus.verify.verifier import verify_packet

RADIOGRAPH = "02_radiographs_pa_bw_radiograph_PA-36_2026-05-14.png"
NARRATIVE_TXT = "04_narrative_txt_2026-05-14.txt"
NARRATIVE_TEXT = b"Tooth 36: fractured MOD amalgam, cusp loss. Crown recommended. See PA of 2026-05-14.\n"
FORBIDDEN = ["Whitfield", "Margaret"]


def pdf_bytes() -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(72, 720, "claim form")
    c.save()
    return buf.getvalue()


def png_bytes(mode: str = "L", dpi: int = 300) -> bytes:
    buf = io.BytesIO()
    Image.new(mode, (40, 40), 128 if mode == "L" else (128, 128, 128)).save(buf, "PNG", dpi=(dpi, dpi))
    return buf.getvalue()


def docx_bytes() -> bytes:
    buf = io.BytesIO()
    d = docx.Document()
    d.add_paragraph("Narrative")
    d.save(buf)
    return buf.getvalue()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_manifest(d: Path, kinds: list[tuple[str, str]], attestation: bool = True) -> None:
    """Manifest computed from what is on disk, so mutations to files stay self-consistent."""
    files = [
        {"seq": i, "filename": name, "sha256": sha256(d / name), "bytes": (d / name).stat().st_size,
         "media_type": "application/octet-stream", "kind": kind, "requirement_ids": [], "artifact_id": None,
         "captured_at": None,
         "spec_checks": {"dpi": None, "bit_depth": None, "format": Path(name).suffix[1:].upper(), "colour": "n/a",
                         "pass": True},
         "transformations_applied": []}
        for i, (name, kind) in enumerate(kinds)
    ]
    narrative = next(f for f in files if f["kind"] == "narrative_txt")["sha256"]
    manifest = {
        "packet_version": 1, "case_id": "whitfield", "assessment_id": "asmt-1", "engine_version": "0.1.0",
        "ruleset": {"id": "cdcp-crown", "version": "2026.05", "content_hash": "sha256:abc"},
        "built_at": "2026-09-17T00:00:00Z",
        "file_count": len(files), "total_bytes": sum(f["bytes"] for f in files),
        "preview": "preview.pdf", "narrative_sha256": narrative,
        "attestation": {"signed_by": "Dr. A", "licence": "ON-1", "signed_at": "2026-09-17T00:00:00Z",
                        "attestation": "I attest.", "narrative_sha256": narrative, "assessment_id": "asmt-1",
                        "ruleset_version": "2026.05"} if attestation else None,
        "files": files,
    }
    (d / "manifest.json").write_text(json.dumps(manifest, indent=1))


def mutate_manifest(d: Path, fn) -> None:
    m = json.loads((d / "manifest.json").read_text())
    fn(m)
    (d / "manifest.json").write_text(json.dumps(m))


def write_packet(root: Path, *, radiograph: bytes | None = None, index_text: str | None = None,
                 extra: list[tuple[str, str, bytes]] = ()) -> Path:
    d = root / "pkt"
    d.mkdir()
    files = [
        ("01_claim_form_cdcp_2026-05-14.pdf", "claim_form", pdf_bytes()),
        (RADIOGRAPH, "radiograph", radiograph or png_bytes()),
        ("03_narrative_docx_2026-05-14.docx", "narrative", docx_bytes()),
        (NARRATIVE_TXT, "narrative_txt", NARRATIVE_TEXT),
        *extra,
    ]
    for name, _, data in files:
        (d / name).write_bytes(data)
    (d / "preview.pdf").write_bytes(pdf_bytes())
    if index_text is None:
        index_text = "Packet contents\n" + "".join(f"{name}\n" for name, _, _ in files)
    (d / "00_index.txt").write_bytes(index_text.encode("utf-8"))
    write_manifest(d, [("00_index.txt", "index")] + [(n, k) for n, k, _ in files])
    return d


def failing(report, check: str, fragment: str) -> None:
    assert not report.ok
    assert report.checks[check] is False, report.findings
    assert any(fragment in f for f in report.findings), report.findings


def test_good_packet_passes(tmp_path):
    report = verify_packet(write_packet(tmp_path), forbidden_tokens=FORBIDDEN)
    assert report.ok, report.findings
    assert report.findings == []
    assert all(report.checks.values())
    assert report.file_count == 5
    assert "no_forbidden_tokens_in_filenames" in report.checks


def test_wrong_sha256(tmp_path):
    d = write_packet(tmp_path)
    mutate_manifest(d, lambda m: m["files"][2].__setitem__("sha256", "0" * 64))
    failing(verify_packet(d), "sha256_matches", f"{RADIOGRAPH}: sha256 ")


def test_extra_unlisted_file(tmp_path):
    d = write_packet(tmp_path)
    (d / "99_extra_note.txt").write_bytes(b"stray")
    failing(verify_packet(d), "no_unlisted_files", "99_extra_note.txt: present in packet but not listed")


def test_rgb_radiograph(tmp_path):
    d = write_packet(tmp_path, radiograph=png_bytes(mode="RGB"))
    report = verify_packet(d)
    failing(report, "radiograph_spec", f"{RADIOGRAPH}: mode RGB, expected 8/16-bit greyscale")
    failing(report, "spec_checks_honest", f"{RADIOGRAPH}: manifest spec_checks.pass=true but verifier found fail")


@pytest.mark.parametrize("dpi", [72, 600])
def test_radiograph_dpi_out_of_band(tmp_path, dpi):
    d = write_packet(tmp_path, radiograph=png_bytes(dpi=dpi))
    failing(verify_packet(d), "radiograph_spec", f"{RADIOGRAPH}: dpi {dpi}x{dpi}, expected 150-300")


def test_non_ascii_index(tmp_path):
    d = write_packet(tmp_path, index_text=f"Contenu — {RADIOGRAPH}\n01_claim_form_cdcp_2026-05-14.pdf\n"
                                          f"03_narrative_docx_2026-05-14.docx\n{NARRATIVE_TXT}\n")
    failing(verify_packet(d), "index_first_and_ascii", "00_index.txt: not pure ASCII (byte 0xE2 at offset 8)")


def test_index_missing_filename(tmp_path):
    d = write_packet(tmp_path, index_text="01_claim_form_cdcp_2026-05-14.pdf\n03_narrative_docx_2026-05-14.docx\n"
                                          f"{NARRATIVE_TXT}\n")
    failing(verify_packet(d), "index_first_and_ascii", f"00_index.txt: does not mention {RADIOGRAPH}")


def test_31_files(tmp_path):
    extra = [(f"{i:02d}_psr_extra_{i}.txt", "psr", b"psr\n") for i in range(5, 31)]
    d = write_packet(tmp_path, extra=extra)
    failing(verify_packet(d), "file_count_le_30", "31 files in packet, max 30")


def test_total_over_7mb(tmp_path):
    d = write_packet(tmp_path, extra=[("05_psr_big.txt", "psr", b"a" * 7_000_001)])
    report = verify_packet(d)
    failing(report, "total_bytes_le_7mb", f"packet totals {report.total_bytes} bytes, max 7000000")
    assert report.total_bytes > 7_000_000


def test_narrative_hash_mismatch(tmp_path):
    d = write_packet(tmp_path)
    mutate_manifest(d, lambda m: m.__setitem__("narrative_sha256", "f" * 64))
    failing(verify_packet(d), "narrative_hash", f"{NARRATIVE_TXT}: sha256 ")


def test_attestation_hash_mismatch(tmp_path):
    d = write_packet(tmp_path)
    mutate_manifest(d, lambda m: m["attestation"].__setitem__("narrative_sha256", "f" * 64))
    failing(verify_packet(d), "narrative_hash", "manifest.json: attestation.narrative_sha256 " + "f" * 64)


def test_forbidden_token_in_filename(tmp_path):
    d = write_packet(tmp_path)
    leaky = "02_radiographs_pa_Whitfield_2026-05-14.png"
    (d / RADIOGRAPH).rename(d / leaky)
    (d / "00_index.txt").write_bytes(f"01_claim_form_cdcp_2026-05-14.pdf\n{leaky}\n03_narrative_docx_2026-05-14.docx\n"
                                     f"{NARRATIVE_TXT}\n".encode())
    write_manifest(d, [("00_index.txt", "index"), ("01_claim_form_cdcp_2026-05-14.pdf", "claim_form"),
                       (leaky, "radiograph"), ("03_narrative_docx_2026-05-14.docx", "narrative"),
                       (NARRATIVE_TXT, "narrative_txt")])
    report = verify_packet(d, forbidden_tokens=FORBIDDEN)
    failing(report, "no_forbidden_tokens_in_filenames", f"{leaky}: filename contains forbidden token 'whitfield'")
    failing(report, "no_forbidden_tokens_in_filenames", "00_index.txt: contains forbidden token 'whitfield'")
    assert verify_packet(d).ok  # same packet passes when the caller supplies no tokens


def test_copy_law_in_index(tmp_path):
    d = write_packet(tmp_path, index_text=f"Approved crown. 01_claim_form_cdcp_2026-05-14.pdf {RADIOGRAPH} "
                                          f"03_narrative_docx_2026-05-14.docx {NARRATIVE_TXT}\n")
    failing(verify_packet(d), "copy_law_in_index", "00_index.txt: contains 'approved'")


def test_missing_manifest(tmp_path):
    d = write_packet(tmp_path)
    (d / "manifest.json").unlink()
    report = verify_packet(d)
    failing(report, "manifest_present_and_valid", "manifest.json: not found")
    assert report.checks["sha256_matches"] is False
