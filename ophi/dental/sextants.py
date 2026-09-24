"""Sextant table for PSR. Static data, versioned next to the ruleset. Exhaustively tested over all 32."""

from __future__ import annotations

SEXTANTS: dict[str, list[int]] = {
    "S1": [18, 17, 16, 15, 14],
    "S2": [13, 12, 11, 21, 22, 23],
    "S3": [24, 25, 26, 27, 28],
    "S4": [34, 35, 36, 37, 38],
    "S5": [43, 42, 41, 31, 32, 33],
    "S6": [48, 47, 46, 45, 44],
}
ALL_SEXTANTS: list[str] = list(SEXTANTS)

_TOOTH_TO_SEXTANT = {t: s for s, teeth in SEXTANTS.items() for t in teeth}


def sextant_of(fdi: int) -> str:
    try:
        return _TOOTH_TO_SEXTANT[fdi]
    except KeyError as e:
        raise ValueError(f"{fdi} is not an FDI permanent tooth") from e


def sextants_of(teeth: list[int]) -> list[str]:
    return sorted({sextant_of(t) for t in teeth})


def teeth_in(sextant: str) -> list[int]:
    return list(SEXTANTS[sextant])


def describe(sextant: str) -> str:
    teeth = SEXTANTS[sextant]
    return f"{sextant} (teeth {teeth[0]}–{teeth[-1]})"
