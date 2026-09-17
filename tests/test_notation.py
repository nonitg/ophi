"""FDI <-> Universal is a bijection over 32 teeth; notation is declared, never guessed."""

from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from colombus.cdm.models import Notation
from colombus.dental.notation import (
    ALL_FDI_PERMANENT, NotationError, arch, describe, fdi_to_universal, is_anterior, is_valid_fdi,
    position, quadrant, side, to_fdi, tooth_class, universal_to_fdi,
)

# Universal runs clockwise from the upper-right third molar (1) to the lower-right third molar (32).
# One anchor per quadrant end, checked against the ISO 3950 / ADA tables independently of the code.
UNIVERSAL_ANCHORS = {1: 18, 8: 11, 9: 21, 16: 28, 17: 38, 24: 31, 25: 41, 32: 48}


def test_all_32_round_trip_and_partition():
    fdi_from_universal = [universal_to_fdi(u) for u in range(1, 33)]
    assert len(set(fdi_from_universal)) == 32
    assert sorted(fdi_from_universal) == ALL_FDI_PERMANENT
    for u in range(1, 33):
        assert fdi_to_universal(universal_to_fdi(u)) == u
    for f in ALL_FDI_PERMANENT:
        assert universal_to_fdi(fdi_to_universal(f)) == f
        assert is_valid_fdi(f)


def test_universal_anchors():
    for u, f in UNIVERSAL_ANCHORS.items():
        assert universal_to_fdi(u) == f, f"Universal {u} should be FDI {f}"


def test_universal_16_is_upper_left_third_molar():
    # The trap from docs/plan/02-reasoning.md §2: "16" is valid in both systems. Universal 16 is the
    # upper-left third molar = FDI 28, not FDI 16 (upper-right first molar).
    assert to_fdi("16", Notation.UNIVERSAL) == 28
    assert to_fdi("16", Notation.FDI) == 16
    assert describe(28) == "upper left third molar"
    assert describe(16) == "upper right first molar"


def test_undeclared_notation_refuses_to_guess():
    with pytest.raises(NotationError):
        to_fdi("16", None)
    with pytest.raises(NotationError):
        to_fdi(46, None)


@pytest.mark.parametrize("bad", [0, 9, 10, 19, 20, 29, 30, 39, 40, 49, 50, 55, 85, -11])
def test_invalid_fdi_raises(bad):
    assert not is_valid_fdi(bad)
    with pytest.raises(NotationError):
        to_fdi(bad, Notation.FDI)
    with pytest.raises(NotationError):
        fdi_to_universal(bad)


@pytest.mark.parametrize("bad", [0, 33, 46, -1, 100])
def test_invalid_universal_raises(bad):
    with pytest.raises(NotationError):
        to_fdi(bad, Notation.UNIVERSAL)
    with pytest.raises(NotationError):
        universal_to_fdi(bad)


@given(st.integers().filter(lambda n: not 1 <= n <= 32))
def test_universal_out_of_range_always_raises(n):
    with pytest.raises(NotationError):
        universal_to_fdi(n)


def test_to_fdi_accepts_strings_with_whitespace():
    assert to_fdi(" 46 ", Notation.FDI) == 46
    assert to_fdi("30", Notation.UNIVERSAL) == 46


@pytest.mark.parametrize("fdi,q,a,s", [
    (11, 1, "upper", "right"), (18, 1, "upper", "right"),
    (21, 2, "upper", "left"), (28, 2, "upper", "left"),
    (31, 3, "lower", "left"), (38, 3, "lower", "left"),
    (41, 4, "lower", "right"), (48, 4, "lower", "right"),
])
def test_quadrant_arch_side_all_four_quadrants(fdi, q, a, s):
    assert quadrant(fdi) == q
    assert arch(fdi) == a
    assert side(fdi) == s


@pytest.mark.parametrize("fdi,pos,cls,anterior", [
    (11, 1, "incisor", True), (12, 2, "incisor", True), (13, 3, "canine", True),
    (14, 4, "premolar", False), (15, 5, "premolar", False),
    (16, 6, "molar", False), (17, 7, "molar", False), (18, 8, "third_molar", False),
    (43, 3, "canine", True), (34, 4, "premolar", False), (27, 7, "molar", False), (38, 8, "third_molar", False),
])
def test_position_class_anterior(fdi, pos, cls, anterior):
    assert position(fdi) == pos
    assert tooth_class(fdi) == cls
    assert is_anterior(fdi) is anterior


def test_third_molars_are_never_plain_molars():
    # Crown eligibility hinges on this split (Guide 6.3.5): 1st/2nd molars in, 3rd molars by exception only.
    for f in ALL_FDI_PERMANENT:
        assert (tooth_class(f) == "third_molar") == (position(f) == 8)


@pytest.mark.parametrize("fdi,text", [
    (11, "upper right central incisor"), (22, "upper left lateral incisor"),
    (24, "upper left first premolar"), (37, "lower left second molar"),
    (46, "lower right first molar"), (48, "lower right third molar"), (33, "lower left canine"),
])
def test_describe(fdi, text):
    assert describe(fdi) == text
