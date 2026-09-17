"""Evidence renderers: radiograph plates (PNG) and periodontal tables (PDF).

DPI is metadata plus pixels and cannot be created. A plate below 150 DPI fails spec and is written
unchanged with the reason recorded, never upsampled (docs/plan/02-reasoning.md, section 5).
Radiographs are never re-encoded lossily: every plate leaves as PNG.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont
from reportlab.platypus import TableStyle
from unidecode import unidecode

from colombus.cdm.models import Case, ChartArtifact, PerioChartPayload, PSRPayload, RadiographPayload
from colombus.dental import notation, sextants
from colombus.packet import pdf
from colombus.packet.labels import fmt_date, teeth_list

DPI_MIN, DPI_MAX = 150, 300
PLACEHOLDER_PX = (1200, 900)
PLACEHOLDER_NOTE = ("PLACEHOLDER \u2014 Fictional Data has no image pixels.",
                    "Replace with the clinic's radiograph at assembly.")
SITE_COLUMNS = ["DB", "B", "MB", "DL", "L", "ML"]
# Upper arch right-to-left, then lower arch right-to-left, as a perio chart is read.
UPPER_ARCH = list(range(18, 10, -1)) + list(range(21, 29))
LOWER_ARCH = list(range(48, 40, -1)) + list(range(31, 39))


def _spec(dpi: int | None, bit_depth: int | None, fmt: str, colour: str, ok: bool, transformations: list[str],
          reason: str | None = None) -> dict:
    return {"dpi": dpi, "bit_depth": bit_depth, "format": fmt, "colour": colour, "pass": ok,
            "transformations": transformations, "reason": reason}


# --- radiographs ----------------------------------------------------------------------------------


def render_radiograph_plate(artifact: ChartArtifact, out_path: Path) -> dict:
    assert isinstance(artifact.payload, RadiographPayload)
    src = Path(artifact.file.path) if artifact.file and artifact.file.path else None
    if src is None or not src.exists():
        return _synthesize_placeholder(artifact, out_path)
    with Image.open(src) as im:
        im.load()
        return _normalise_radiograph(im, src, artifact, out_path)


def _normalise_radiograph(im: Image.Image, src: Path, artifact: ChartArtifact, out_path: Path) -> dict:
    transformations: list[str] = []
    img, bit_depth, colour, conversion = _to_greyscale(im)
    if conversion:
        transformations.append(conversion)
    if src.suffix.lower() != ".png":
        transformations.append(f"transcoded {im.format or src.suffix.lstrip('.').upper()} to PNG (lossless)")

    dpi = _source_dpi(im, artifact)
    ok, reason, out_dpi = True, None, dpi
    if dpi is None:
        ok, reason = False, "DPI cannot be established: no DPI metadata and no stated sensor size"
    elif dpi < DPI_MIN:
        ok, reason = False, f"{dpi} DPI is below the {DPI_MIN} DPI minimum; written unchanged, not upsampled"
    elif dpi > DPI_MAX:
        scale = DPI_MAX / dpi
        img = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.LANCZOS)
        transformations.append(f"downsampled from {dpi} DPI to {DPI_MAX} DPI (LANCZOS)")
        out_dpi = DPI_MAX
    if colour != "greyscale":
        ok, reason = False, "colour pixels supplied for a radiograph; the radiograph band requires greyscale"

    img.save(out_path, "PNG", **({"dpi": (out_dpi, out_dpi)} if out_dpi else {}))
    return _spec(out_dpi, bit_depth, "PNG", colour, ok, transformations, reason)


def _to_greyscale(im: Image.Image) -> tuple[Image.Image, int, str, str | None]:
    """Return (image, bit_depth, colour, transformation). Greyscale-in-RGB is the common bridge failure."""
    if im.mode == "L":
        return im, 8, "greyscale", None
    if im.mode.startswith("I;16"):
        return im, 16, "greyscale", None
    if im.mode in ("RGB", "RGBA"):
        if _channels_equal(im):
            return im.convert("L"), 8, "greyscale", "converted 24-bit colour to 8-bit greyscale"
        return im.convert("RGB"), 8, "colour", None
    if im.mode in ("P", "LA", "1", "I"):
        return im.convert("L"), 8, "greyscale", f"converted mode {im.mode} to 8-bit greyscale"
    return im.convert("RGB"), 8, "colour", None


def _channels_equal(im: Image.Image) -> bool:
    # JPEG chroma rounding leaves +-1..2 between channels on a grey source; that is still greyscale.
    r, g, b = im.convert("RGB").split()
    spread = max(ImageChops.difference(r, g).getextrema()[1], ImageChops.difference(r, b).getextrema()[1])
    return spread <= 2


def _source_dpi(im: Image.Image, artifact: ChartArtifact) -> int | None:
    dpi = im.info.get("dpi")
    if dpi and dpi[0] > 1:
        if abs(dpi[0] - dpi[1]) > 1:
            return None  # anisotropic resolution: do not rewrite it as square metadata
        return round(dpi[0])
    if artifact.file and artifact.file.dpi:
        return artifact.file.dpi  # stated by the imaging source, not inferred
    return None


def _font(size: int) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow < 10.1
        return ImageFont.load_default()


def _draw_tooth(d: ImageDraw.ImageDraw, cx: int, top: int, roots: int) -> None:
    """A crown with tapered roots, drawn as a radiograph would show them: bright enamel, darker pulp."""
    crown_w, crown_h = 260, 210
    d.rounded_rectangle((cx - crown_w // 2, top, cx + crown_w // 2, top + crown_h), radius=60, fill=205)
    d.rounded_rectangle((cx - 70, top + 70, cx + 70, top + crown_h - 20), radius=30, fill=95)  # pulp chamber
    root_top = top + crown_h - 10
    root_len = 300
    offsets = [0] if roots == 1 else [-80, 80]
    for off in offsets:
        d.polygon([(cx + off - 70, root_top), (cx + off + 70, root_top), (cx + off + 12, root_top + root_len),
                   (cx + off - 12, root_top + root_len)], fill=175)
        d.polygon([(cx + off - 18, root_top), (cx + off + 18, root_top), (cx + off + 3, root_top + root_len - 40),
                   (cx + off - 3, root_top + root_len - 40)], fill=105)  # canal


def _plate_title(p: RadiographPayload) -> str:
    if p.view.value == "PA" and len(p.teeth_fdi) == 1:
        return f"PA  #{p.teeth_fdi[0]}"
    side = f" {p.laterality.value}" if p.laterality else ""
    return f"{p.view.value}{side}"


def _synthesize_placeholder(artifact: ChartArtifact, out_path: Path) -> dict:
    p = artifact.payload
    assert isinstance(p, RadiographPayload)
    w, h = PLACEHOLDER_PX
    img = Image.new("L", (w, h), 18)
    d = ImageDraw.Draw(img)
    d.rectangle((0, h // 2 + 40, w, h), fill=48)  # alveolar bone band
    focus = p.teeth_fdi[0] if p.teeth_fdi else 36
    _draw_tooth(d, w // 2, 150, roots=2 if notation.tooth_class(focus) in ("molar", "third_molar") else 1)
    d.text((40, 30), unidecode(_plate_title(p)), fill=235, font=_font(64))
    if len(p.teeth_fdi) > 1:
        d.text((40, 110), unidecode(teeth_list(p.teeth_fdi)), fill=200, font=_font(30))
    d.text((40, 160), f"captured {fmt_date(artifact.captured_at)}", fill=200, font=_font(30))
    d.text((40, h - 100), unidecode(PLACEHOLDER_NOTE[0]), fill=245, font=_font(30))
    d.text((40, h - 60), unidecode(PLACEHOLDER_NOTE[1]), fill=245, font=_font(30))
    img.save(out_path, "PNG", dpi=(DPI_MAX, DPI_MAX))
    return _spec(DPI_MAX, 8, "PNG", "greyscale", True, ["synthesized placeholder plate"])


# --- periodontal tables ---------------------------------------------------------------------------


def _depth_cell(v: int | None) -> str:
    return "" if v is None else str(v)


def perio_flowables(artifact: ChartArtifact, case: Case) -> list:
    """Header plus the 6-site table; shared by the standalone PDF and the preview."""
    p = artifact.payload
    assert isinstance(p, PerioChartPayload)
    present = case.dentition.present_teeth(UPPER_ARCH + LOWER_ARCH)
    by_tooth = {t.tooth_fdi: t for t in p.teeth}
    head = [
        pdf.P("Periodontal chart — 6-site probing depths (mm)", "h1"),
        pdf.P(f"Exam date: {fmt_date(artifact.captured_at)}    Examiner: {p.examiner or 'not recorded'}    "
              f"Certified: {'yes' if p.certified else 'no (draft)'}"),
        pdf.P(f"Sites recorded: {p.point_count} of {len(present) * 6} ({len(present)} teeth present). "
              f"Requested tooth #{case.requested_tooth} is highlighted; pockets of 4 mm or more are bold, 5 mm or more shaded."),
        pdf.spacer(6),
    ]
    rows: list[list] = [["Tooth", *SITE_COLUMNS]]
    style: list[tuple] = []
    for arch_name, arch in (("Upper arch", UPPER_ARCH), ("Lower arch", LOWER_ARCH)):
        rows.append([arch_name, "", "", "", "", "", ""])
        style += [("SPAN", (0, len(rows) - 1), (-1, len(rows) - 1)), ("BACKGROUND", (0, len(rows) - 1), (-1, len(rows) - 1), pdf.SHADE)]
        for tooth in (t for t in arch if t in present):
            depths = by_tooth[tooth].depths_mm if tooth in by_tooth else [None] * 6
            r = len(rows)
            rows.append([f"#{tooth}", *(_depth_cell(v) for v in depths)])
            if tooth == case.requested_tooth:
                style.append(("BACKGROUND", (0, r), (-1, r), pdf.HIGHLIGHT))
            for c, v in enumerate(depths, start=1):
                if v is not None and v >= 4:
                    style.append(("FONTNAME", (c, r), (c, r), "Helvetica-Bold"))
                if v is not None and v >= 5:
                    style.append(("BACKGROUND", (c, r), (c, r), pdf.WARN))
    table = pdf.grid(rows, col_widths=[60] + [48] * 6)
    table.setStyle(TableStyle(style + [("ALIGN", (1, 0), (-1, -1), "CENTER")]))
    return head + [table]


def render_perio_chart(artifact: ChartArtifact, case: Case, out_path: Path) -> dict:
    pdf.build_pdf(out_path, perio_flowables(artifact, case), "Periodontal chart")
    return _spec(None, None, "PDF", "n/a", True, ["rendered table from PMS probing depths"])


def psr_flowables(artifact: ChartArtifact) -> list:
    p = artifact.payload
    assert isinstance(p, PSRPayload)
    rows = [["Sextant", "Teeth", "PSR score"]]
    for s in sextants.ALL_SEXTANTS:
        teeth = sextants.teeth_in(s)
        score = p.scores.get(s)
        rows.append([s, f"{teeth[0]}–{teeth[-1]}", "not recorded" if score is None else str(score)])
    return [
        pdf.P("Periodontal Screening and Recording (PSR)", "h1"),
        pdf.P(f"Exam date: {fmt_date(artifact.captured_at)}. One score per sextant, 0–4."),
        pdf.spacer(6),
        pdf.grid(rows, col_widths=[70, 90, 90]),
    ]


def render_psr(artifact: ChartArtifact, out_path: Path) -> dict:
    pdf.build_pdf(out_path, psr_flowables(artifact), "PSR scores")
    return _spec(None, None, "PDF", "n/a", True, ["rendered table from PMS PSR scores"])

