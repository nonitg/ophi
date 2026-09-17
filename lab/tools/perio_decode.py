#!/usr/bin/env python3
"""Decode ABELDent's Perio byte arrays into per-tooth, per-site measurements.

ABELDent stores a perio exam as fixed-width binary columns, not rows: one byte per
measurement site, laid out tooth by tooth in Universal 1-32 order, with 0xFF meaning
"tooth absent or site not measured". Read them as varbinary — as char they are mojibake.

Note the notation trap this exists to expose: Perio positions are Universal 1-32, but
tdi.itooth is FDI. Anything joining a planned procedure to its perio evidence must convert.

Usage:
    vm sql "SELECT patID, ExamNum, CONVERT(varchar(400), CAST(Pocket AS varbinary(192)), 2) AS pocket_hex,
                   CONVERT(varchar(400), CAST(Bleeding_Suppuration AS varbinary(192)), 2) AS bleed_hex
            FROM Perio WHERE patID = 155" '' json | ./lab/tools/perio_decode.py
"""
import json
import sys

ABSENT = 0xFF
SITES_PER_TOOTH = {"pocket": 6, "recession": 6, "bleeding": 6, "attachment": 6,
                   "furcation": 3, "mag": 2, "mobility": 1}
# Universal 1-32 -> FDI. Position i in a Perio array is Universal tooth i+1.
UNIVERSAL_TO_FDI = (
    [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28] +
    [38, 37, 36, 35, 34, 33, 32, 31, 41, 42, 43, 44, 45, 46, 47, 48]
)


def decode(hex_str, sites_per_tooth=6):
    """-> {universal_tooth: [mm or None per site]}. None means absent/unmeasured."""
    raw = bytes.fromhex(hex_str.strip())
    expected = 32 * sites_per_tooth
    if len(raw) != expected:
        raise ValueError(f"expected {expected} bytes, got {len(raw)}")
    return {
        t + 1: [None if b == ABSENT else b
                for b in raw[t * sites_per_tooth:(t + 1) * sites_per_tooth]]
        for t in range(32)
    }


def summarise(teeth):
    """The numbers a CDCP documentation rule actually asks for.

    0xFF does not mean the same thing in every column. In Pocket it reads as "tooth absent
    or site not probed"; in Bleeding_Suppuration a tooth that was probed and did not bleed
    is also 0xFF. So this reports "no value" and refuses to call it absence — deciding a
    tooth is missing is a clinical claim, and inferring it from a sentinel would be exactly
    the kind of fabricated gap SourceAssurance exists to prevent.
    """
    measured = [v for sites in teeth.values() for v in sites if v is not None]
    no_value = [t for t, sites in teeth.items() if all(v is None for v in sites)]
    deep = [(t, UNIVERSAL_TO_FDI[t - 1], i + 1, v)
            for t, sites in teeth.items()
            for i, v in enumerate(sites) if v is not None and v >= 5]
    return {
        # The M0 exit criterion: a 192-point full-mouth exam and a 12-point spot check
        # are opposite clinical conclusions, and only the point count separates them.
        "point_count": len(measured),
        "sites_total": sum(len(s) for s in teeth.values()),
        "teeth_no_value_universal": no_value,
        "teeth_no_value_fdi": [UNIVERSAL_TO_FDI[t - 1] for t in no_value],
        "value_min": min(measured) if measured else None,
        "value_max": max(measured) if measured else None,
        "sites_5mm_plus": [{"universal": u, "fdi": f, "site": s, "mm": v} for u, f, s, v in deep],
    }


def main():
    payload = json.load(sys.stdin)
    rows = payload.get("value", payload) if isinstance(payload, dict) else payload
    out = []
    for row in rows if isinstance(rows, list) else [rows]:
        rec = {k: v for k, v in row.items() if not k.endswith("_hex")}
        for key, val in row.items():
            if not key.endswith("_hex") or not val:
                continue
            name = key[:-4]
            try:
                rec[name] = summarise(decode(val, SITES_PER_TOOTH.get(name, 6)))
            except ValueError as e:
                rec[name] = {"error": str(e)}
        out.append(rec)
    json.dump(out, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
