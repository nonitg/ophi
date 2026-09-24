"""Sextant table: exhaustive over all 32 FDI positions (docs/plan/02-reasoning.md §2)."""

from __future__ import annotations

import pytest

from ophi.dental.notation import ALL_FDI_PERMANENT
from ophi.dental.sextants import ALL_SEXTANTS, SEXTANTS, describe, sextant_of, sextants_of, teeth_in

# Transcribed from docs/plan/02-reasoning.md §2 "Sextant mapping", independently of the code.
DOC_TABLE = {
    "S1": [18, 17, 16, 15, 14],
    "S2": [13, 12, 11, 21, 22, 23],
    "S3": [24, 25, 26, 27, 28],
    "S6": [48, 47, 46, 45, 44],
    "S5": [43, 42, 41, 31, 32, 33],
    "S4": [34, 35, 36, 37, 38],
}


def test_table_matches_doc():
    assert SEXTANTS == DOC_TABLE
    assert ALL_SEXTANTS == ["S1", "S2", "S3", "S4", "S5", "S6"]


def test_every_tooth_in_exactly_one_sextant():
    for t in ALL_FDI_PERMANENT:
        homes = [s for s, teeth in SEXTANTS.items() if t in teeth]
        assert len(homes) == 1, f"{t} appears in {homes}"
        assert sextant_of(t) == homes[0]


def test_sextants_partition_the_dentition():
    all_teeth = [t for teeth in SEXTANTS.values() for t in teeth]
    assert len(all_teeth) == 32
    assert sorted(all_teeth) == ALL_FDI_PERMANENT


@pytest.mark.parametrize("tooth,sextant", [
    (18, "S1"), (14, "S1"), (13, "S2"), (11, "S2"), (21, "S2"), (23, "S2"), (24, "S3"), (28, "S3"),
    (34, "S4"), (38, "S4"), (33, "S5"), (31, "S5"), (41, "S5"), (43, "S5"), (44, "S6"), (48, "S6"),
])
def test_boundary_teeth(tooth, sextant):
    # The canine/premolar boundary is where a hand-written table goes wrong.
    assert sextant_of(tooth) == sextant


def test_sextants_of_sorted_and_deduped():
    assert sextants_of([46, 16, 46, 11, 44, 21]) == ["S1", "S2", "S6"]
    assert sextants_of([37]) == ["S4"]
    assert sextants_of([]) == []


def test_teeth_in_and_describe():
    assert teeth_in("S6") == [48, 47, 46, 45, 44]
    assert teeth_in("S6") is not SEXTANTS["S6"]  # a copy: callers cannot mutate the table
    assert describe("S6") == "S6 (teeth 48–44)"


@pytest.mark.parametrize("bad", [0, 19, 29, 39, 49, 55, 85])
def test_invalid_raises(bad):
    with pytest.raises(ValueError):
        sextant_of(bad)
    with pytest.raises(ValueError):
        sextants_of([46, bad])
