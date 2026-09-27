"""Build the test uploads for the letter flow: a fictional Sun Life denial letter and three bad files."""
from __future__ import annotations

import pathlib

from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

OUT = pathlib.Path(__file__).resolve().parents[2] / "var/e2e/sunlife"
OUT.mkdir(parents=True, exist_ok=True)

# Fictional. Mirrors the shape of a Sun Life CDCP predetermination denial letter.
LINES = [
    ("Helvetica-Bold", 14, "Sun Life Assurance Company of Canada"),
    ("Helvetica", 9, "PO Box 2010 Stn Waterloo, Waterloo ON  N2J 0A6"),
    ("", 0, ""),
    ("Helvetica", 10, "September 24, 2026"),
    ("", 0, ""),
    ("Helvetica", 10, "MAPLE RIDGE DENTAL"),
    ("Helvetica", 10, "18 King Street West, Hamilton ON"),
    ("", 0, ""),
    ("Helvetica-Bold", 11, "Canadian Dental Care Plan - Predetermination decision"),
    ("", 0, ""),
    ("Helvetica", 10, "Client:            MATHEW CHERSKI"),
    ("Helvetica", 10, "Client ID:         551200160"),
    ("Helvetica", 10, "Date of birth:     March 20, 1969"),
    ("Helvetica", 10, "Our reference:     SL260915000160"),
    ("Helvetica", 10, "Procedure:         27211  Crown, porcelain/ceramic fused to metal"),
    ("Helvetica", 10, "Tooth:             26"),
    ("Helvetica", 10, "Submitted amount:  $581.00"),
    ("", 0, ""),
    ("Helvetica-Bold", 11, "Decision: NOT APPROVED"),
    ("", 0, ""),
    ("Helvetica", 10, "Predetermination not approved. A complete 6-site periodontal chart for"),
    ("Helvetica", 10, "the requested tooth was not received with this request. Please resubmit"),
    ("Helvetica", 10, "with a current periodontal chart."),
    ("", 0, ""),
    ("Helvetica", 10, "You may request a reconsideration within 60 days of the date of this"),
    ("Helvetica", 10, "letter if you have new clinical information."),
    ("", 0, ""),
    ("Helvetica", 9, "This is a fictional document created for software testing."),
]


def letter_pdf(path: pathlib.Path) -> None:
    c = canvas.Canvas(str(path), pagesize=LETTER)
    y = LETTER[1] - inch
    for font, size, txt in LINES:
        if txt:
            c.setFont(font, size)
            c.drawString(inch, y, txt)
        y -= (size + 6) if size else 10
    c.showPage()
    c.save()


def main() -> None:
    letter_pdf(OUT / "sunlife-denial.pdf")
    (OUT / "empty.pdf").write_bytes(b"")
    (OUT / "letter.txt").write_text("Sun Life denied the predetermination for tooth 26.\n")
    img = Image.new("RGB", (900, 600), "white")
    d = ImageDraw.Draw(img)
    d.rectangle([80, 80, 820, 520], outline="black", width=6)
    d.text((140, 280), "x-ray placeholder - not a letter", fill="black")
    img.save(OUT / "not-a-letter.png")
    for f in sorted(OUT.glob("*")):
        if f.suffix in (".pdf", ".txt", ".png") and "recon" not in f.name and not f.name.startswith("15"):
            print(f, f.stat().st_size)


main()
