"""Evidence proposers read free text and *propose* structured artifacts. They never judge.

Every proposal carries a verbatim `quote` that must be an exact substring of the source note; anything
else is discarded. That single check is the hallucination filter and the prompt-injection defence.
Proposed artifacts enter the index as unconfirmed and can only yield `satisfied_pending_confirmation`
until a human confirms them, after which the engine re-runs deterministically.

v1 ships a heuristic proposer (regex over plan language). `ClaudeProposer` is the seam for the LLM
extractor and accepts only a `DeidentifiedNote` — never a Patient.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from colombus.cdm.models import (
    ArtifactType, Case, ChartArtifact, ExtractedDetailPayload, NotePayload, Provenance,
)

_SENTENCE = re.compile(r"[^.!?\n]+[.!?]?")
_PLAN_CUE = re.compile(r"\b(plan(?:ned|ning)?|tx plan|treatment plan|propos\w+|recommend\w*)\b", re.I)
_PROCEDURE_CUE = re.compile(r"\b(crown|pfm|ceramic|onlay|restor\w+|rct|root canal|endo\w*|extract\w*|fill\w*|amalgam|composite|hygiene|scal\w+|perio\w*)\b", re.I)
_TOOTH = re.compile(r"(?<!\d)([1-4][1-8])(?!\d)")


@dataclass(frozen=True)
class DeidentifiedNote:
    """The only shape a model-backed proposer may receive: text, date, teeth. No identity fields."""

    artifact_id: str
    text: str
    captured_at: str | None
    teeth_fdi: tuple[int, ...]


class Proposer(Protocol):
    name: str

    def propose(self, note: DeidentifiedNote) -> list[tuple[str, str, list[int]]]:
        """Return (quote, claim, teeth) triples. Quotes must be exact substrings of note.text."""


class HeuristicProposer:
    """Finds sentences that state a treatment plan. Cheap, deterministic, no network."""

    name = "heuristic"

    def propose(self, note: DeidentifiedNote) -> list[tuple[str, str, list[int]]]:
        out = []
        for m in _SENTENCE.finditer(note.text):
            sent = m.group(0).strip()
            if _PLAN_CUE.search(sent) and _PROCEDURE_CUE.search(sent):
                teeth = sorted({int(t) for t in _TOOTH.findall(sent)})
                out.append((sent, "Treatment plan details stated in the clinical note", teeth))
        return out


def literal(quote: str, text: str) -> bool:
    return bool(quote) and quote in text


def propose_for_case(case: Case, proposer: Proposer | None = None) -> list[ChartArtifact]:
    """Run the proposer over every signed-off note. Returns unconfirmed TX_PLAN_DETAILS artifacts."""
    proposer = proposer or HeuristicProposer()
    proposals: list[ChartArtifact] = []
    for note in case.artifacts_of(ArtifactType.CLINICAL_NOTE):
        p = note.payload
        assert isinstance(p, NotePayload)
        if not p.signed_off:
            continue
        view = DeidentifiedNote(note.artifact_id, p.text, str(note.captured_at) if note.captured_at else None, tuple(p.teeth_fdi))
        for i, (quote, claim, teeth) in enumerate(proposer.propose(view), start=1):
            if not literal(quote, p.text):
                continue  # the hallucination filter: no exact quote, no artifact
            proposals.append(ChartArtifact(
                artifact_id=f"{note.artifact_id}.proposal{i}",
                type=ArtifactType.TX_PLAN_DETAILS,
                captured_at=note.captured_at,
                provenance=Provenance(source_system="colombus", source_table="proposer", source_row_key=note.artifact_id,
                                      extraction_method="llm" if proposer.name != "heuristic" else "heuristic"),
                payload=ExtractedDetailPayload(source_artifact_id=note.artifact_id, quote=quote, claim=claim,
                                               teeth_fdi=teeth or list(p.teeth_fdi)),
            ))
    return proposals
