"""Ophi's pre-read of each clinical criterion, so the dentist confirms instead of answering from scratch.

It gathers what the chart records (odontogram, perio chart, plan, procedure history) and what Laya read in the
note, and suggests an answer only when that evidence backs the criterion and nothing in it goes against it.
Anything else is left for the dentist, with the reason. A pre-read is never recorded as an answer: only the
dentist's confirmation becomes an AssertionPayload, under their name and licence.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel

from ophi.assertions.criteria import extensively_restored_variant, relevant_criteria, single_rooted
from ophi.cdm.models import ArtifactType, Case, PerioChartPayload, RadiographPayload, SiteDepths, ToothState
from ophi.dental import notation
from ophi.outcomes.fixer import CONCERN, FLAG
from ophi.rules.schema import RulePack

SURE = 0.7  # Laya is calibrated: backing a criterion needs this much; going against it, more likely than not (FLAG)

# The criteria each of Laya's note questions bears on, and the answer that backs the criterion. A "yes only"
# question backs on a yes and says nothing on a no (a lost cusp is one route to "extensively restored").
NOTE_CRITERIA: dict[str, list[tuple[str, str]]] = {
    "extensively_restored": [("extensively_restored", "yes"), ("structure_lost", "yes only")],
    "endo_healed": [("endo_not_healed", "no")], "active_disease_addressed": [("pending_basic", "no")],
    "no_furcation": [("poor_support", "no")], "crown_root_ratio": [("poor_support", "no")],
    "margin_3mm": [("subgingival_margin", "no")], "ferrule_1_5mm": [("subgingival_margin", "no")],
    "no_adjunctive_needed": [("subgingival_margin", "no")],
}
BACKS = {"extensively_restored": "says the tooth is already heavily filled", "structure_lost": "says part of the tooth has broken away",
         "endo_not_healed": "does not say the root canal is still healing", "pending_basic": "says no fillings or cleanings are still to do",
         "poor_support": "does not say the bone or gum holding the tooth is a problem",
         "subgingival_margin": "does not say the filling edge sits under the gum"}
# Judged on the radiograph, which Ophi can't read: the dentist glances at the film before confirming.
ON_FILM = {"crown_root_ratio", "margin_3mm", "ferrule_1_5mm", "no_adjunctive_needed", "mesiodistal_space", "endo_healed"}

Stance = Literal["supports", "against"]


class Evidence(BaseModel):
    source: Literal["chart", "note"]  # note: Laya's reading
    text: str
    stance: Stance


class PreRead(BaseModel):
    criterion_id: str
    suggest: Literal["met", "not_applicable"] | None  # None: the dentist's call
    evidence: list[Evidence]
    on_film: bool

    @property
    def against(self) -> list[Evidence]:
        return [e for e in self.evidence if e.stance == "against"]


def pre_reads(case: Case, pack: RulePack, note: dict[str, float] | None) -> dict[str, PreRead]:
    """A pre-read for every criterion this case asks the dentist for."""
    return {cid: pre_read(case, cid, note) for cid in relevant_criteria(case, pack)}


def pre_read(case: Case, criterion_id: str, note: dict[str, float] | None) -> PreRead:
    no_roots_apart = criterion_id == "no_furcation" and single_rooted(case.requested_tooth)
    evidence = _chart(case, criterion_id) + (_note(note, criterion_id) if note else [])
    if any(e.stance == "against" for e in evidence):
        suggest = None
    elif no_roots_apart:
        suggest = "not_applicable"
    else:
        suggest = "met" if evidence else None
    return PreRead(criterion_id=criterion_id, suggest=suggest, evidence=evidence, on_film=criterion_id in ON_FILM)


def latest_pa(case: Case) -> date | None:
    """The day the most recent periapical of the requested tooth was taken."""
    t = case.requested_tooth
    days = [a.captured_at for a in case.artifacts_of(ArtifactType.RADIOGRAPH)
            if isinstance(a.payload, RadiographPayload) and a.payload.view.value == "PA" and t in a.payload.teeth_fdi and a.captured_at]
    return max(days) if days else None


def _note(note: dict[str, float], criterion_id: str) -> list[Evidence]:
    out = []
    for q, backing in NOTE_CRITERIA.get(criterion_id, []):
        if (p := note.get(q)) is None:
            continue
        p_backs = 1 - p if backing == "no" else p
        if p_backs >= SURE:
            out.append(Evidence(source="note", text=f"The note {BACKS[q]}", stance="supports"))
        elif 1 - p_backs > FLAG and backing != "yes only":
            out.append(Evidence(source="note", text=f"The note {CONCERN[q]}", stance="against"))
    return out


def _chart(case: Case, criterion_id: str) -> list[Evidence]:
    t = case.requested_tooth
    if criterion_id == "extensively_restored":
        return _restored(case)
    if criterion_id == "active_disease_addressed":
        pending = [h for h in case.procedure_history if h.status == "planned" and h.code != case.treatment.code]
        if pending:
            listed = ", ".join(f"{h.code}{' #' + str(h.tooth_fdi) if h.tooth_fdi else ''}" for h in pending)
            return [Evidence(source="chart", text=f"The treatment plan still has {listed} waiting to be done", stance="against")]
        return [Evidence(source="chart", text="The treatment plan has nothing else waiting to be done", stance="supports")]
    if criterion_id == "no_active_perio" and (site := _perio_at(case)):
        return [_perio_evidence(site)]
    if criterion_id == "no_furcation":
        if single_rooted(t):
            return [Evidence(source="chart", text=f"#{t} has only one root, so there is no split between roots to check", stance="supports")]
        if (site := _perio_at(case)) and site.furcation is not None:
            return [Evidence(source="chart", text=f"Gum chart: bone loss has reached the split between the roots of #{t} (furcation grade {site.furcation})", stance="against") if site.furcation
                    else Evidence(source="chart", text=f"Gum chart: no bone loss where the roots of #{t} split apart", stance="supports")]
    if criterion_id == "endo_healed":
        return _endo(case)
    if criterion_id == "third_molar_in_occlusion":
        return [_third_molar(case)]
    return []


def _restored(case: Case) -> list[Evidence]:
    """The odontogram against the definition for this tooth type (pack: extensively_restored variants)."""
    t, variant = case.requested_tooth, extensively_restored_variant(case)
    surfaces = set(case.dentition.restored_surfaces.get(t, []))
    if not surfaces:
        return []
    shown = f"Tooth chart: #{t} is already filled on {len(surfaces)} sides ({', '.join(sorted(surfaces, key='MIODBLF'.find))})"
    if variant == "posterior_non_endo":
        return [Evidence(source="chart", text=f"{shown}; this tooth needs 5 to count as heavily filled",
                         stance="supports" if len(surfaces) >= 5 else "against")]
    ridges = {"M", "D"} <= surfaces
    if variant == "posterior_endo" and ridges and len(surfaces) >= 3:
        return [Evidence(source="chart", text=f"{shown}, including both edges that meet the neighbouring teeth", stance="supports")]
    if variant == "anterior" and ridges and "I" in surfaces:
        return [Evidence(source="chart", text=f"{shown}, including the biting edge and both sides that meet the neighbouring teeth", stance="supports")]
    return []  # short of the surface route, a lost cusp may still meet it: the note or the dentist decides


def _perio_at(case: Case) -> SiteDepths | None:
    charts = [a for a in case.artifacts_of(ArtifactType.PERIO_CHART) if isinstance(a.payload, PerioChartPayload) and a.captured_at]
    if not charts:
        return None
    pl = max(charts, key=lambda a: a.captured_at).payload
    assert isinstance(pl, PerioChartPayload)
    return next((s for s in pl.teeth if s.tooth_fdi == case.requested_tooth and s.sites_measured), None)


def _perio_evidence(site: SiteDepths) -> Evidence:
    """Stable per the 2017 World Workshop: no pocket over 4 mm, and no bleeding at a 4 mm site. Otherwise the
    dentist looks."""
    bleeding = site.bleeding or [False] * 6
    depths = [(d, b) for d, b in zip(site.depths_mm, bleeding) if d is not None]
    deepest = max(d for d, _ in depths)
    unstable = deepest >= 5 or any(d >= 4 and b for d, b in depths)
    bleeds = any(b for _, b in depths)
    # Plain reading of the numbers, so a new coordinator sees what they mean without knowing the thresholds.
    reading = "the gum there is not healthy enough yet" if unstable else "the gum there is healthy"
    text = (f"Gum chart: the deepest gap between gum and tooth at #{site.tooth_fdi} is {deepest} mm and it "
            f"{'bleeds when measured' if bleeds else 'does not bleed'} - {reading}")
    return Evidence(source="chart", text=text, stance="against" if unstable else "supports")


def _endo(case: Case) -> list[Evidence]:
    t = case.requested_tooth
    rct = [h.performed_on for h in case.procedure_history if h.status == "completed" and h.tooth_fdi == t and h.code.startswith("33")]
    if not rct:
        return []
    done, pa = max(rct), latest_pa(case)
    if not pa or pa <= done:
        return [Evidence(source="chart", text=f"No x-ray of #{t} has been taken since its root canal on {done:%b %-d, %Y}", stance="against")]
    months = (pa.year - done.year) * 12 + pa.month - done.month
    return [Evidence(source="chart", text=f"An x-ray of #{t} was taken {months} months after its root canal", stance="supports")]


def _third_molar(case: Case) -> Evidence:
    t = case.requested_tooth
    q = notation.quadrant(t)
    first_second_missing = all(case.dentition.state(q * 10 + p) == ToothState.MISSING for p in (6, 7))
    opposing = {1: 4, 2: 3, 3: 2, 4: 1}[q]
    opposed = any(case.dentition.state(opposing * 10 + p) != ToothState.MISSING for p in (6, 7, 8))
    if first_second_missing and opposed:
        return Evidence(source="chart", text=f"Tooth chart: #{q}6 and #{q}7 are both missing, and there is a molar in the opposite jaw for #{t} to bite against", stance="supports")
    return Evidence(source="chart", text=f"Tooth chart: #{q}6 is {case.dentition.state(q * 10 + 6).value}, #{q}7 is {case.dentition.state(q * 10 + 7).value}",
                    stance="against")
