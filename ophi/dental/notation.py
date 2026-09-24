"""Tooth notation: FDI (ISO 3950) is canonical. Universal (1–32) is converted, never guessed.

"16" is a valid tooth in both systems and means different teeth. Notation therefore comes from the
source system's declared convention; an undeclared notation raises rather than guesses.
"""

from __future__ import annotations

from ophi.cdm.models import Notation

# Universal 1..32 runs clockwise from upper-right third molar. FDI quadrant 1 = upper right (18..11),
# quadrant 2 = upper left (21..28), quadrant 3 = lower left (31..38), quadrant 4 = lower right (41..48).
_UNIVERSAL_TO_FDI: dict[int, int] = {}
for i, fdi in enumerate(range(18, 10, -1), start=1):  # 1..8  -> 18..11
    _UNIVERSAL_TO_FDI[i] = fdi
for i, fdi in enumerate(range(21, 29), start=9):  # 9..16 -> 21..28
    _UNIVERSAL_TO_FDI[i] = fdi
for i, fdi in enumerate(range(38, 30, -1), start=17):  # 17..24 -> 38..31
    _UNIVERSAL_TO_FDI[i] = fdi
for i, fdi in enumerate(range(41, 49), start=25):  # 25..32 -> 41..48
    _UNIVERSAL_TO_FDI[i] = fdi
_FDI_TO_UNIVERSAL = {v: k for k, v in _UNIVERSAL_TO_FDI.items()}

ALL_FDI_PERMANENT: list[int] = sorted(_FDI_TO_UNIVERSAL)


class NotationError(ValueError):
    pass


def is_valid_fdi(n: int) -> bool:
    return n in _FDI_TO_UNIVERSAL


def universal_to_fdi(n: int) -> int:
    try:
        return _UNIVERSAL_TO_FDI[n]
    except KeyError as e:
        raise NotationError(f"{n} is not a Universal permanent tooth number (1–32)") from e


def fdi_to_universal(n: int) -> int:
    try:
        return _FDI_TO_UNIVERSAL[n]
    except KeyError as e:
        raise NotationError(f"{n} is not an FDI permanent tooth number") from e


def to_fdi(as_written: str | int, declared: Notation | None) -> int:
    """Normalise a tooth number to FDI using the source's declared notation. Never infers."""
    if declared is None:
        raise NotationError(f"tooth {as_written!r}: notation not declared by source; refusing to guess")
    n = int(str(as_written).strip())
    if declared == Notation.FDI:
        if not is_valid_fdi(n):
            raise NotationError(f"{n} is not a valid FDI permanent tooth")
        return n
    return universal_to_fdi(n)


def quadrant(fdi: int) -> int:
    return fdi // 10


def arch(fdi: int) -> str:
    return "upper" if quadrant(fdi) in (1, 2) else "lower"


def side(fdi: int) -> str:
    """Patient's right or left. Quadrants 1 and 4 are the patient's right."""
    return "right" if quadrant(fdi) in (1, 4) else "left"


def position(fdi: int) -> int:
    """1 = central incisor ... 8 = third molar."""
    return fdi % 10


def tooth_class(fdi: int) -> str:
    p = position(fdi)
    if p in (1, 2):
        return "incisor"
    if p == 3:
        return "canine"
    if p in (4, 5):
        return "premolar"
    if p in (6, 7):
        return "molar"
    return "third_molar"


def is_anterior(fdi: int) -> bool:
    return position(fdi) <= 3


def describe(fdi: int) -> str:
    names = {1: "central incisor", 2: "lateral incisor", 3: "canine", 4: "first premolar",
             5: "second premolar", 6: "first molar", 7: "second molar", 8: "third molar"}
    return f"{arch(fdi)} {side(fdi)} {names[position(fdi)]}"
