"""Independent packet verifier.

Opens every file in a finished packet from scratch and re-checks it against the CDCP
submission spec and the manifest contract. Deliberately shares no code with the assembler
(`ophi.packet`): the assembler asserting its own output is compliant is not evidence.
"""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from collections.abc import Callable
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, ConfigDict, Field, ValidationError

MANIFEST_NAME = "manifest.json"
INDEX_NAME = "00_index.txt"
PACKET_VERSION = 1
MAX_FILES = 30
MAX_BYTES = 7_000_000
FILENAME_RE = re.compile(r"^[0-9]{2}_[A-Za-z0-9._-]+$")
# Words the packet must never assert about coverage; documentation completeness only.
COPY_LAW_TOKENS = ("approved", "eligible", "covered", "medically necessary")

GREYSCALE_MODES = {"L", "I;16", "I;16B", "I;16L", "I;16N"}
COLOUR_MODES = {"RGB", "RGBA"}
RADIOGRAPH_FORMATS = {"PNG", "TIFF"}
PHOTO_FORMATS = {"JPEG", "PNG", "TIFF"}
RADIOGRAPH_DPI = (150, 300)
PHOTO_DPI = (300, 600)
DPI_TOLERANCE = 1  # PNG stores pixels/metre, so 300 dpi round-trips as 299.9994


class VerifyReport(BaseModel):
    ok: bool
    shippable: bool = False  # ok AND signed by the treating provider for a READY verdict
    signed: bool = False
    findings: list[str]
    checks: dict[str, bool]
    file_count: int
    total_bytes: int


# --- The verifier's own reading of the manifest contract -------------------------------------

class _SpecChecks(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    pass_: bool = Field(alias="pass")
    dpi: int | None = None
    bit_depth: int | None = None
    format: str | None = None
    colour: str | None = None


class _FileEntry(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    seq: int
    filename: str
    sha256: str
    bytes: int
    kind: str
    media_type: str | None = None
    requirement_ids: list[str] = []
    artifact_id: str | None = None
    captured_at: str | None = None
    spec_checks: _SpecChecks
    transformations_applied: list[str] = []


class _Ruleset(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    id: str
    version: str
    content_hash: str


class _Attestation(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    signed_by: str
    licence: str | None
    signed_at: str
    attestation: str
    narrative_sha256: str
    assessment_id: str
    ruleset_version: str


class _Manifest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    packet_version: int
    case_id: str
    assessment_id: str
    engine_version: str
    ruleset: _Ruleset
    built_at: str
    file_count: int
    total_bytes: int
    preview: str
    status: str
    verdict: str
    narrative_sha256: str | None
    attestation: _Attestation | None
    files: list[_FileEntry]


class _Packet:
    """What is actually on disk, read once and shared by every check."""

    def __init__(self, packet_dir: Path, manifest: _Manifest | None):
        self.dir = packet_dir
        self.manifest = manifest
        self.preview = manifest.preview if manifest else None
        entries = sorted(packet_dir.iterdir(), key=lambda p: p.name) if packet_dir.is_dir() else []
        self.actual = [p for p in entries if not p.name.startswith(".")]
        # Packet files are what ships to the insurer; manifest and preview stay with the case.
        self.packet_files = [p for p in self.actual if p.name not in (MANIFEST_NAME, self.preview)]
        self.listed = manifest.files if manifest else []
        self.image_verdicts: dict[str, bool] = {}
        self._index_bytes: bytes | None = None

    def path(self, filename: str) -> Path:
        return self.dir / filename

    def exists(self, filename: str) -> bool:
        return Path(filename).name == filename and self.path(filename).is_file()

    def index_bytes(self) -> bytes | None:
        if self._index_bytes is None and self.exists(INDEX_NAME):
            self._index_bytes = self.path(INDEX_NAME).read_bytes()
        return self._index_bytes

    def index_text_lower(self) -> str:
        data = self.index_bytes()
        return data.decode("ascii", errors="replace").lower() if data else ""


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _first_non_ascii(data: bytes) -> str:
    for i, b in enumerate(data):
        if b > 0x7F:
            return f"byte 0x{b:02X} at offset {i}"
    return ""


# --- Manifest -------------------------------------------------------------------------------

def _load_manifest(packet_dir: Path) -> tuple[_Manifest | None, list[str]]:
    path = packet_dir / MANIFEST_NAME
    if not path.is_file():
        return None, [f"{MANIFEST_NAME}: not found in {packet_dir}"]
    try:
        raw = json.loads(path.read_bytes())
    except (ValueError, UnicodeDecodeError) as e:
        return None, [f"{MANIFEST_NAME}: not valid JSON ({e})"]
    try:
        manifest = _Manifest.model_validate(raw)
    except ValidationError as e:
        return None, [f"{MANIFEST_NAME}: {'.'.join(str(x) for x in err['loc'])}: {err['msg']}" for err in e.errors()]
    if manifest.packet_version != PACKET_VERSION:
        return None, [f"{MANIFEST_NAME}: packet_version {manifest.packet_version}, expected {PACKET_VERSION}"]
    return manifest, []


# --- Directory-level checks (run even when the manifest is unusable) -----------------------------

def _check_file_count(pkt: _Packet) -> list[str]:
    n = len(pkt.packet_files)
    return [f"{n} files in packet, max {MAX_FILES}"] if n > MAX_FILES else []


def _check_total_bytes(pkt: _Packet) -> list[str]:
    total = sum(p.stat().st_size for p in pkt.packet_files if p.is_file())
    return [f"packet totals {total} bytes, max {MAX_BYTES}"] if total > MAX_BYTES else []


def _check_filename_charset(pkt: _Packet) -> list[str]:
    return [f"{p.name}: filename does not match {FILENAME_RE.pattern}"
            for p in pkt.packet_files if not FILENAME_RE.match(p.name)]


def _check_documents_openable(pkt: _Packet) -> list[str]:
    findings: list[str] = []
    for p in pkt.actual:
        if p.name == MANIFEST_NAME or not p.is_file():
            continue
        ext = p.suffix.lower()
        if ext == ".pdf":
            data = p.read_bytes()
            if not data.startswith(b"%PDF-"):
                findings.append(f"{p.name}: does not start with %PDF-")
            if not data.rstrip().endswith(b"%%EOF"):
                findings.append(f"{p.name}: does not end with %%EOF")
        elif ext == ".docx":
            if not zipfile.is_zipfile(p):
                findings.append(f"{p.name}: not a valid zip archive")
                continue
            with zipfile.ZipFile(p) as z:
                corrupt = z.testzip()
                if "word/document.xml" not in z.namelist():
                    findings.append(f"{p.name}: zip lacks word/document.xml")
                elif corrupt is not None:
                    findings.append(f"{p.name}: corrupt member {corrupt}")
        elif ext == ".txt":
            bad = _first_non_ascii(p.read_bytes())
            if bad:
                findings.append(f"{p.name}: not pure ASCII ({bad})")
    return findings


# --- Manifest-dependent checks --------------------------------------------------------------------

def _check_listed_exist(pkt: _Packet) -> list[str]:
    findings: list[str] = []
    seen: set[str] = set()
    for e in pkt.listed:
        if e.filename in seen:
            findings.append(f"{e.filename}: listed more than once in manifest")
        seen.add(e.filename)
        if not pkt.exists(e.filename):
            findings.append(f"{e.filename}: listed in manifest but missing from packet")
    assert pkt.manifest is not None
    if not pkt.exists(pkt.manifest.preview):
        findings.append(f"{pkt.manifest.preview}: named as preview in manifest but missing from packet")
    return findings


def _check_no_unlisted(pkt: _Packet) -> list[str]:
    listed = {e.filename for e in pkt.listed}
    return [f"{p.name}: present in packet but not listed in manifest" for p in pkt.packet_files if p.name not in listed]


def _check_sha256(pkt: _Packet) -> list[str]:
    findings: list[str] = []
    for e in pkt.listed:
        if pkt.exists(e.filename):
            actual = _sha256(pkt.path(e.filename))
            if actual != e.sha256.lower():
                findings.append(f"{e.filename}: sha256 {actual} != manifest {e.sha256}")
    return findings


def _check_bytes(pkt: _Packet) -> list[str]:
    findings: list[str] = []
    for e in pkt.listed:
        if pkt.exists(e.filename):
            actual = pkt.path(e.filename).stat().st_size
            if actual != e.bytes:
                findings.append(f"{e.filename}: {actual} bytes on disk != manifest {e.bytes}")
    return findings


def _check_manifest_counts(pkt: _Packet) -> list[str]:
    assert pkt.manifest is not None
    findings: list[str] = []
    n = len(pkt.packet_files)
    total = sum(p.stat().st_size for p in pkt.packet_files if p.is_file())
    if pkt.manifest.file_count != n:
        findings.append(f"{MANIFEST_NAME}: file_count {pkt.manifest.file_count} != {n} files in packet")
    if pkt.manifest.total_bytes != total:
        findings.append(f"{MANIFEST_NAME}: total_bytes {pkt.manifest.total_bytes} != {total} bytes in packet")
    return findings


def _check_index(pkt: _Packet) -> list[str]:
    if not pkt.listed or pkt.listed[0].filename != INDEX_NAME:
        first = pkt.listed[0].filename if pkt.listed else "(no files)"
        return [f"{MANIFEST_NAME}: files[0] is {first}, expected {INDEX_NAME}"]
    data = pkt.index_bytes()
    if data is None:
        return [f"{INDEX_NAME}: missing from packet"]
    bad = _first_non_ascii(data)
    if bad:
        return [f"{INDEX_NAME}: not pure ASCII ({bad})"]
    text = data.decode("ascii")
    return [f"{INDEX_NAME}: does not mention {e.filename}" for e in pkt.listed[1:] if e.filename not in text]


def _dpi_findings(filename: str, dpi: object, band: tuple[int, int]) -> list[str]:
    lo, hi = band
    if not isinstance(dpi, (tuple, list)) or len(dpi) != 2:
        return [f"{filename}: no DPI metadata, expected {lo}-{hi}"]
    try:
        x, y = (round(float(v)) for v in dpi)
    except (TypeError, ValueError):
        return [f"{filename}: unreadable DPI metadata {dpi!r}, expected {lo}-{hi}"]
    if not all(lo - DPI_TOLERANCE <= v <= hi + DPI_TOLERANCE for v in (x, y)):
        return [f"{filename}: dpi {x}x{y}, expected {lo}-{hi}"]
    return []


def _image_findings(pkt: _Packet, e: _FileEntry, formats: set[str], modes: set[str], band: tuple[int, int],
                    mode_label: str) -> list[str]:
    try:
        with Image.open(pkt.path(e.filename)) as img:
            img.load()
            fmt, mode, dpi = img.format, img.mode, img.info.get("dpi")
    except (UnidentifiedImageError, OSError, ValueError) as ex:
        pkt.image_verdicts[e.filename] = False
        return [f"{e.filename}: cannot be opened as an image ({type(ex).__name__})"]
    findings: list[str] = []
    if fmt not in formats:
        findings.append(f"{e.filename}: format {fmt}, expected {'/'.join(sorted(formats))}")
    if mode not in modes:
        findings.append(f"{e.filename}: mode {mode}, expected {mode_label}")
    findings.extend(_dpi_findings(e.filename, dpi, band))
    pkt.image_verdicts[e.filename] = not findings
    return findings


def _check_radiographs(pkt: _Packet) -> list[str]:
    findings: list[str] = []
    for e in pkt.listed:
        if e.kind == "radiograph" and pkt.exists(e.filename):
            findings += _image_findings(pkt, e, RADIOGRAPH_FORMATS, GREYSCALE_MODES, RADIOGRAPH_DPI, "8/16-bit greyscale")
    return findings


def _check_photos(pkt: _Packet) -> list[str]:
    findings: list[str] = []
    for e in pkt.listed:
        if e.kind == "photo" and pkt.exists(e.filename):
            findings += _image_findings(pkt, e, PHOTO_FORMATS, COLOUR_MODES, PHOTO_DPI, "RGB/RGBA colour")
    return findings


def _check_spec_checks_honest(pkt: _Packet) -> list[str]:
    # Only images have a spec the verifier can independently measure; compare our verdict to the assembler's.
    return [f"{e.filename}: manifest spec_checks.pass={str(e.spec_checks.pass_).lower()} but verifier found "
            f"{'pass' if pkt.image_verdicts[e.filename] else 'fail'}"
            for e in pkt.listed if e.filename in pkt.image_verdicts and pkt.image_verdicts[e.filename] != e.spec_checks.pass_]


def _check_narrative_hash(pkt: _Packet) -> list[str]:
    m = pkt.manifest
    assert m is not None
    narratives = [e for e in pkt.listed if e.kind == "narrative_txt"]
    findings: list[str] = []
    if m.narrative_sha256 is None:
        findings.append(f"{MANIFEST_NAME}: narrative_sha256 is null")
    if len(narratives) != 1:
        findings.append(f"{MANIFEST_NAME}: {len(narratives)} files of kind narrative_txt, expected exactly 1")
    elif m.narrative_sha256 is not None and pkt.exists(narratives[0].filename):
        actual = _sha256(pkt.path(narratives[0].filename))
        if actual != m.narrative_sha256.lower():
            findings.append(f"{narratives[0].filename}: sha256 {actual} != manifest.narrative_sha256 {m.narrative_sha256}")
    if m.attestation is not None:
        # The dentist must have attested exactly the text that ships, for this assessment.
        if m.attestation.narrative_sha256.lower() != (m.narrative_sha256 or "").lower():
            findings.append(f"{MANIFEST_NAME}: attestation.narrative_sha256 {m.attestation.narrative_sha256} "
                            f"!= manifest.narrative_sha256 {m.narrative_sha256}")
        if m.attestation.assessment_id != m.assessment_id:
            findings.append(f"{MANIFEST_NAME}: attestation.assessment_id {m.attestation.assessment_id} "
                            f"!= manifest.assessment_id {m.assessment_id}")
    return findings


def _check_sequence(pkt: _Packet) -> list[str]:
    findings: list[str] = []
    for i, e in enumerate(pkt.listed):
        if e.seq != i:
            findings.append(f"{e.filename}: seq {e.seq} at position {i}, expected {i}")
        if not e.filename.startswith(f"{e.seq:02d}_"):
            findings.append(f"{e.filename}: filename does not start with {e.seq:02d}_")
    return findings


def _check_copy_law(pkt: _Packet) -> list[str]:
    """Ophi's own voice must not assert approval or coverage: index, and the narrative outside quotes."""
    findings = [f"{INDEX_NAME}: contains '{tok}' (copy law: never assert approval or coverage)"
                for tok in COPY_LAW_TOKENS if tok in pkt.index_text_lower()]
    for e in pkt.listed:
        if e.kind != "narrative_txt" or not pkt.exists(e.filename):
            continue
        own_voice = re.sub(r'"[^"]*"', " ", pkt.path(e.filename).read_text(encoding="ascii", errors="replace")).lower()
        findings += [f"{e.filename}: contains '{tok}' outside a quotation (copy law)" for tok in COPY_LAW_TOKENS if tok in own_voice]
    return findings


SIGNED_VERDICTS = ("READY_TO_SUBMIT", "READY_WITH_RISKS")


def _check_status(pkt: _Packet) -> list[str]:
    """A signed packet carries an attestation for a READY verdict; a draft carries none."""
    m = pkt.manifest
    assert m is not None
    findings = []
    if m.status not in ("draft", "signed"):
        findings.append(f"{MANIFEST_NAME}: status {m.status!r} is not draft|signed")
    if m.status == "signed" and m.attestation is None:
        findings.append(f"{MANIFEST_NAME}: status signed but no attestation")
    if m.status == "draft" and m.attestation is not None:
        findings.append(f"{MANIFEST_NAME}: status draft but an attestation is present")
    if m.status == "signed" and m.verdict not in SIGNED_VERDICTS:
        findings.append(f"{MANIFEST_NAME}: signed packet for verdict {m.verdict}; only {', '.join(SIGNED_VERDICTS)} may be signed")
    return findings


def _check_forbidden_tokens(pkt: _Packet, tokens: list[str]) -> list[str]:
    findings: list[str] = []
    wanted = [t.lower() for t in tokens if t.strip()]
    for e in pkt.listed:
        for tok in wanted:
            if tok in e.filename.lower():
                findings.append(f"{e.filename}: filename contains forbidden token '{tok}'")
    index = pkt.index_text_lower()
    findings += [f"{INDEX_NAME}: contains forbidden token '{tok}'" for tok in wanted if tok in index]
    return findings


_Check = Callable[[_Packet], list[str]]

DIRECTORY_CHECKS: list[tuple[str, _Check]] = [
    ("file_count_le_30", _check_file_count),
    ("total_bytes_le_7mb", _check_total_bytes),
    ("documents_openable", _check_documents_openable),
    ("filename_charset", _check_filename_charset),
]

MANIFEST_CHECKS: list[tuple[str, _Check]] = [
    ("every_listed_file_exists", _check_listed_exist),
    ("no_unlisted_files", _check_no_unlisted),
    ("sha256_matches", _check_sha256),
    ("bytes_match", _check_bytes),
    ("manifest_counts_consistent", _check_manifest_counts),
    ("index_first_and_ascii", _check_index),
    ("radiograph_spec", _check_radiographs),
    ("photo_spec", _check_photos),
    ("spec_checks_honest", _check_spec_checks_honest),  # must follow the image checks
    ("narrative_hash", _check_narrative_hash),
    ("sequence_contiguous", _check_sequence),
    ("copy_law_in_index", _check_copy_law),
    ("status_consistent", _check_status),
]


def verify_packet(packet_dir: Path, forbidden_tokens: list[str] | None = None) -> VerifyReport:
    packet_dir = Path(packet_dir)
    checks: dict[str, bool] = {}
    findings: list[str] = []

    def record(name: str, found: list[str]) -> None:
        checks[name] = not found
        findings.extend(found)

    manifest, manifest_findings = _load_manifest(packet_dir)
    record("manifest_present_and_valid", manifest_findings)
    pkt = _Packet(packet_dir, manifest)

    for name, check in DIRECTORY_CHECKS:
        record(name, check(pkt))
    if manifest is None:
        for name, _ in MANIFEST_CHECKS:
            checks[name] = False
        if forbidden_tokens is not None:
            checks["no_forbidden_tokens_in_filenames"] = False
        findings.append(f"{MANIFEST_NAME}: unusable, manifest-dependent checks not run")
    else:
        for name, check in MANIFEST_CHECKS:
            record(name, check(pkt))
        if forbidden_tokens is not None:
            record("no_forbidden_tokens_in_filenames", _check_forbidden_tokens(pkt, forbidden_tokens))

    signed = manifest is not None and manifest.status == "signed" and manifest.attestation is not None
    return VerifyReport(
        ok=all(checks.values()),
        shippable=all(checks.values()) and signed,
        signed=signed,
        findings=findings,
        checks=checks,
        file_count=len(pkt.packet_files),
        total_bytes=sum(p.stat().st_size for p in pkt.packet_files if p.is_file()),
    )
