#!/usr/bin/env python3
"""Exercise rtf_to_text on the tricky constructs the reviewer named. Inputs built with chr() so no
shell or Python escape processing can alter them."""
import sys; sys.path.insert(0, 'lab/tools')
import chart_dump as c
BS = chr(92)
cases = {
    "nested star group": "{" + BS + "rtf1{" + BS + "fonttbl{" + BS + "f0" + BS + "fcharset0{" + BS + "*" + BS + "panose 020b0604}Segoe UI;}{" + BS + "f1 Arial;}}" + BS + "f0 real note}",
    "unicode+fallback": "{" + BS + "rtf1 a " + BS + "u8212?dash}",
    "hex, nbsp, tab, par": "{" + BS + "rtf1 caf" + BS + "'e9" + BS + "~x" + BS + "tab y" + BS + "par second}",
    "themedata": "{" + BS + "rtf1 text{" + BS + "*" + BS + "themedata 504b0304}}",
    "escaped braces": "{" + BS + "rtf1 a" + BS + "{b" + BS + "}c}",
}
for name, rtf in cases.items():
    print(f"{name:<22} -> {c.rtf_to_text(rtf)!r}")
