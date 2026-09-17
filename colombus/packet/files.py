"""One shipped packet file: where it is on disk, what it is, and what the manifest says about it."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from unidecode import unidecode

MEDIA_TYPES = {
    "txt": "text/plain",
    "png": "image/png",
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "tif": "image/tiff",
    "tiff": "image/tiff",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
}
SPEC_KEYS = ("dpi", "bit_depth", "format", "colour", "pass")


def safe_name(s: str) -> str:
    """ASCII, no spaces, no path characters. Filenames get logged and screenshotted."""
    return re.sub(r"[^A-Za-z0-9._-]+", "-", unidecode(s)).strip("-")


def packet_filename(seq: int, requirement_id: str, artifact_type: str, descriptor: str, captured_at: date | None, ext: str) -> str:
    return safe_name(f"{seq:02d}_{requirement_id}_{artifact_type}_{descriptor}_{captured_at.isoformat() if captured_at else 'undated'}.{ext}")


@dataclass
class PacketFile:
    seq: int
    filename: str
    path: Path
    kind: str
    description: str  # one line for the index and preview captions
    requirement_ids: list[str]
    artifact_id: str | None = None
    captured_at: date | None = None
    spec: dict = field(default_factory=dict)  # renderer output: SPEC_KEYS plus transformations/reason

    @property
    def bytes(self) -> int:
        return self.path.stat().st_size

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.path.read_bytes()).hexdigest()

    @property
    def spec_failure(self) -> str | None:
        return None if self.spec.get("pass", True) else self.spec.get("reason") or "failed spec check"

    def manifest_entry(self) -> dict:
        return {
            "seq": self.seq,
            "filename": self.filename,
            "sha256": self.sha256,
            "bytes": self.bytes,
            "media_type": MEDIA_TYPES[self.path.suffix.lstrip(".").lower()],
            "kind": self.kind,
            "requirement_ids": list(self.requirement_ids),
            "artifact_id": self.artifact_id,
            "captured_at": self.captured_at.isoformat() if self.captured_at else None,
            "spec_checks": {k: self.spec.get(k) for k in SPEC_KEYS},
            "transformations_applied": list(self.spec.get("transformations", [])),
        }
