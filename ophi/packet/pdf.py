"""Thin reportlab helpers so every PDF in the packet shares one look and one escaping path."""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

PAGE = letter
MARGIN = 0.75 * inch
BODY_WIDTH = PAGE[0] - 2 * MARGIN

_base = getSampleStyleSheet()
STYLES: dict[str, ParagraphStyle] = {
    "title": ParagraphStyle("title", parent=_base["Title"], fontSize=18, leading=22, alignment=TA_LEFT, spaceAfter=8),
    "h1": ParagraphStyle("h1", parent=_base["Heading2"], fontSize=13, leading=16, spaceBefore=12, spaceAfter=4),
    "h2": ParagraphStyle("h2", parent=_base["Heading3"], fontSize=11, leading=14, spaceBefore=8, spaceAfter=2),
    "body": ParagraphStyle("body", parent=_base["BodyText"], fontSize=9.5, leading=12.5),
    "small": ParagraphStyle("small", parent=_base["BodyText"], fontSize=8, leading=10, textColor=colors.HexColor("#444444")),
    "quote": ParagraphStyle("quote", parent=_base["BodyText"], fontSize=9.5, leading=12.5, leftIndent=24,
                            fontName="Helvetica-Oblique"),
    "attribution": ParagraphStyle("attribution", parent=_base["BodyText"], fontSize=8.5, leading=11, leftIndent=24,
                                  textColor=colors.HexColor("#444444"), spaceAfter=6),
    "cell": ParagraphStyle("cell", parent=_base["BodyText"], fontSize=8.5, leading=10.5),
}

SHADE = colors.HexColor("#f2f2f2")
HIGHLIGHT = colors.HexColor("#fff3bf")
WARN = colors.HexColor("#fbd5d5")


def P(text: str, style: str = "body") -> Paragraph:
    return Paragraph(escape(text), STYLES[style])


def spacer(h: float = 6) -> Spacer:
    return Spacer(1, h)


def grid(rows: list[list], col_widths: list[float] | None = None, header: bool = True) -> Table:
    """A bordered table; strings are wrapped as cell paragraphs so long text folds."""
    cells = [[c if not isinstance(c, str) else Paragraph(escape(c), STYLES["cell"]) for c in r] for r in rows]
    t = Table(cells, colWidths=col_widths, repeatRows=1 if header else 0)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#999999")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), SHADE), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
    t.setStyle(TableStyle(style))
    return t


def build_pdf(path: Path, flowables: list, title: str) -> None:
    doc = SimpleDocTemplate(str(path), pagesize=PAGE, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=MARGIN,
                            bottomMargin=MARGIN, title=title, author="Ophi")
    doc.build(flowables)
