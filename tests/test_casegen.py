"""casegen dialect: relative ages, dentition shorthand, perio site counts, declared notation."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from ophi.casegen.dsl import build_case, resolve_date
from ophi.cdm.models import ArtifactType, Notation, PerioChartPayload, ToothState
from tests._cases import ready_dict

AS_OF = date(2026, 9, 17)


@pytest.mark.parametrize("value,expected", [
    ("364d", AS_OF - timedelta(days=364)),
    ("13m", date(2025, 8, 17)),
    ("2y", date(2024, 9, 17)),
    ("10 days", AS_OF - timedelta(days=10)),
    ("3 months", date(2026, 6, 17)),
    ("2026-01-05", date(2026, 1, 5)),
    (date(2025, 12, 31), date(2025, 12, 31)),
    (None, None),
])
def test_resolve_date(value, expected):
    assert resolve_date(value, AS_OF) == expected


def test_resolve_date_rejects_garbage():
    with pytest.raises(ValueError):
        resolve_date("yesterday", AS_OF)


def test_missing_shorthand_sets_tooth_state():
    d = ready_dict()
    d["dentition"] = {"missing": [18, 48], "teeth": {36: "implant"}}
    case = build_case(d, "t")
    assert case.dentition.state(18) == ToothState.MISSING
    assert case.dentition.state(48) == ToothState.MISSING
    assert case.dentition.state(36) == ToothState.IMPLANT
    assert case.dentition.state(17) == ToothState.PRESENT  # unlisted teeth default to present
    assert case.as_of == AS_OF


def test_perio_sites_4_gives_four_measured_sites_per_present_tooth():
    d = ready_dict()
    d["perio_charts"] = [{"id": "p4", "age": "10d", "sites": 4, "depth": 3}]
    case = build_case(d, "t")
    chart = case.artifact("p4")
    assert chart is not None and chart.type == ArtifactType.PERIO_CHART
    assert chart.captured_at == AS_OF - timedelta(days=10)
    p = chart.payload
    assert isinstance(p, PerioChartPayload)
    assert len(p.teeth) == 32 - 4  # 18, 28, 38, 48 missing in the base dentition
    for t in p.teeth:
        assert t.sites_measured == 4
        assert t.depths_mm == [3, 3, 3, 3, None, None]
    assert p.point_count == 28 * 4


def test_perio_explicit_teeth_and_except():
    d = ready_dict()
    d["perio_charts"] = [{"id": "p", "age": "10d", "sites": 6, "except": [17], "teeth": {46: [3, 4, 3, 3, 3, 4]}}]
    p = build_case(d, "t").artifact("p").payload
    assert isinstance(p, PerioChartPayload)
    assert 17 not in p.teeth_charted
    assert p.sites_for(46) == 6 and p.sites_for(47) == 6
    assert next(t for t in p.teeth if t.tooth_fdi == 46).depths_mm == [3, 4, 3, 3, 3, 4]


def test_partial_chart_when_not_full_mouth():
    d = ready_dict()
    d["perio_charts"] = [{"id": "p", "age": "10d", "full_mouth": False, "teeth": {46: [3, 3, 3, 3, 3, 3]}}]
    p = build_case(d, "t").artifact("p").payload
    assert isinstance(p, PerioChartPayload)
    assert p.teeth_charted == {46}


def test_universal_notation_converts_every_tooth_field():
    """A source that declares Universal writes every tooth number in Universal; nothing stays mixed."""
    d = ready_dict()
    d["notation"] = "universal"
    d["treatment"]["tooth"] = 16                       # Universal 16 = FDI 28
    d["dentition"] = {"missing": [1, 17, 32], "restored_surfaces": {30: ["M", "O"]}}   # 1=FDI 18, 30=FDI 46
    d["history"] = [{"code": "21223", "tooth": 30, "date": "2020-01-01"}]
    d["radiographs"] = [{"id": "pa", "view": "PA", "tooth": 16, "age": "10d"},
                        {"id": "bw", "view": "BW", "teeth": [3, 14], "age": "10d"}]   # Universal 3 = FDI 16, 14 = FDI 26
    d["perio_charts"] = [{"id": "perio", "age": "10d", "sites": 6, "teeth": {30: [3, 3, 3, 3, 3, 3]}, "except": [2]}]  # 2 = FDI 17
    d["notes"] = [{"id": "n", "age": "10d", "teeth": [16], "text": "x"}]
    case = build_case(d, "t")
    assert case.treatment.tooth.tooth_fdi == 28
    assert case.treatment.tooth.tooth_as_written == "16"
    assert case.treatment.tooth.notation_declared == Notation.UNIVERSAL
    assert case.dentition.state(18).value == "missing" and case.dentition.state(48).value == "missing"
    assert case.dentition.restored_surfaces == {46: ["M", "O"]}
    assert case.procedure_history[0].tooth_fdi == 46
    assert case.artifact("pa").teeth_fdi == [28]
    assert case.artifact("bw").teeth_fdi == [16, 26]
    assert case.artifact("n").teeth_fdi == [28]
    charted = case.artifact("perio").payload.teeth_charted
    assert 46 in charted and 17 not in charted


def test_notation_defaults_to_fdi():
    case = build_case(ready_dict(), "t")
    assert case.treatment.tooth.notation_declared == Notation.FDI
    assert case.treatment.tooth.tooth_fdi == 46
