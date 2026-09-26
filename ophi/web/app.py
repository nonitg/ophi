"""Ophi web app — five server-rendered screens over `CaseService`. Nothing here judges a case.

The packet renderer, verifier, narrative drafter and look-back are separate modules being built in
parallel; each is imported lazily and the screen degrades to an explanatory placeholder when absent.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import shutil
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ophi.lookback import run_lookback
from ophi.packet.build import build_packet
from ophi.packet.documents import narrative_ascii
from ophi.packet.narrative import draft_narrative
from ophi.verify.verifier import verify_packet
from ophi.engine.models import Status
from ophi.outcomes.weights import load as load_weights
from ophi.service import CaseService, CaseView, NarrativeInvalid, identity_tokens
from ophi.web import abeldent_api, present
from ophi.web.present import ACTORS, DEFAULT_ACTOR, READY_VERDICTS, Actor

HERE = Path(__file__).resolve().parent
# Static assets are cached by the browser; the newest mtime in static/ busts that cache on each deploy.
STATIC_V = max(int(p.stat().st_mtime) for p in (HERE / "static").iterdir())
templates = Jinja2Templates(directory=str(HERE / "templates"))
templates.env.globals.update(STATIC_V=STATIC_V,
    money=present.money, short_date=present.short_date, days_until=present.days_until, tooth_name=present.tooth_name,
    source_title=present.source_title, kb=present.kb, requirement_detail=present.requirement_detail, monogram=present.monogram,
    plural=present.plural, STATUS_LABEL=present.STATUS_LABEL, STATUS_CLASS=present.STATUS_CLASS,
    STATUS_NA=Status.NOT_APPLICABLE, ACTORS=ACTORS, EVENT_LABEL=present.EVENT_LABEL, REQ_SHORT=present.REQ_SHORT,
)

router = APIRouter()


# --- plumbing ---------------------------------------------------------------------------------------


def _svc(request: Request) -> CaseService:
    return request.app.state.svc


def _actor(request: Request) -> Actor:
    return ACTORS.get(request.cookies.get("actor", ""), ACTORS[DEFAULT_ACTOR])


def _base(request: Request) -> str:
    return request.app.state.base_path


def _home(request: Request) -> str:
    return _base(request) or "/"


def _render(request: Request, name: str, status: int = 200, **ctx) -> HTMLResponse:
    svc = _svc(request)
    base = _base(request)
    ctx.update(actor=_actor(request), pack=svc.pack, request=request,
               BASE=base, HOME=_home(request), here=request.url.path.removeprefix(base) or "/")
    return templates.TemplateResponse(request, name, ctx, status_code=status)


def _error(request: Request, status: int, title: str, detail: str) -> HTMLResponse:
    return _render(request, "error.html", status=status, title=title, detail=detail)


def _view(request: Request, case_id: str) -> CaseView | None:
    try:
        return _svc(request).view(case_id)
    except FileNotFoundError:
        return None


def _back(request: Request, fallback: str) -> RedirectResponse:
    return RedirectResponse(request.headers.get("referer") or fallback, status_code=303)


def _to(request: Request, path: str) -> RedirectResponse:
    return RedirectResponse(_base(request) + path, status_code=303)


def _form_text(text: str) -> str:
    """Browsers submit textarea content with CRLF; the packet and its hash are built over LF text."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _packet_dir(request: Request, case_id: str) -> Path:
    d: Path = request.app.state.packets_dir / case_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _narrative(view: CaseView, pack) -> tuple[str, str | None]:
    """Saved edits win; otherwise the template drafter. Returns (text, unavailable_reason)."""
    if view.state.narrative_edits is not None:
        return view.state.narrative_edits, None
    return draft_narrative(view.case, view.assessment, pack), None


def _build_packet(request: Request, view: CaseView, narrative: str) -> dict:
    """Assemble the packet into var/packets/{case_id}/ and run the independent verifier over it."""
    out = _packet_dir(request, view.case.case_id)
    result: dict = {"dir": out, "manifest": None, "files": [], "report": None, "unavailable": None, "pdf": out / "preview.pdf"}
    sign_off = view.state.sign_off if view.signed else None  # a stale sign-off never reaches the packet
    manifest = _existing_manifest(out, view, narrative, sign_off)
    if manifest is None:
        manifest = build_packet(view.case, view.assessment, out, narrative_text=narrative, sign_off=sign_off, pack=_svc(request).pack)
    result["manifest"] = manifest
    result["files"] = present.manifest_files(manifest)
    result["report"] = verify_packet(out, forbidden_tokens=identity_tokens(view.case))
    return result


def _existing_manifest(out: Path, view: CaseView, narrative: str, sign_off) -> dict | None:
    """Reuse the packet on disk when nothing it depends on has changed (GET must not churn files)."""
    p = out / "manifest.json"
    if not p.exists():
        return None
    try:
        m = json.loads(p.read_text())
    except ValueError:
        return None
    same = (m.get("assessment_id") == view.assessment.assessment_id
            and m.get("narrative_sha256") == hashlib.sha256(narrative_ascii(narrative).encode()).hexdigest()
            and m.get("status") == ("signed" if sign_off else "draft"))
    return m if same else None


# --- screen 1: queue --------------------------------------------------------------------------------


@router.get("/", response_class=HTMLResponse)
def queue(request: Request):
    views = _svc(request).queue()
    rows = [{"view": v, "lead": present.queue_lead(v), "strip": present.strip(v.assessment), "stage": present.stage(v),
             "waiting": present.waiting_on(v)} for v in views]
    return _render(request, "queue.html", rows=rows, stages=present.stage_rail(views), families=present.REQ_FAMILIES,
                   inbox=present.inbox(views, _actor(request)), summary=present.queue_summary(views))


# --- screen 2: case review --------------------------------------------------------------------------


@router.get("/cases/{case_id}", response_class=HTMLResponse)
def case_review(request: Request, case_id: str):
    view = _view(request, case_id)
    if view is None:
        return _error(request, 404, "Case not found", f"No case '{case_id}' in the demo set.")
    relevant, other = present.assertion_rows(view, _svc(request).pack)
    gaps = present.gap_groups(view)
    return _render(request, "case.html", view=view, case=view.case, a=view.assessment, gaps=gaps,
                   head=present.headline(view, gaps), strip=present.strip(view.assessment), stage=present.stage(view),
                   parts=present.completeness_parts(view.assessment), documented=present.documented(view), handoff=present.handoff(view), work=present.work_done(view),
                   timeline=present.chart_timeline(view), evidence=present.evidence_panel(view), criteria=relevant, criteria_other=other,
                   not_applicable=[r for r in view.assessment.requirements if not r.applicable])


@router.post("/cases/{case_id}/assert")
def assert_criterion(request: Request, case_id: str, criterion_id: str = Form(...), value: str = Form(...), note: str = Form("")):
    actor = _actor(request)
    if not actor.is_dentist:
        return _error(request, 403, "Dentist only", "Clinician assertions are attributed clinical judgment; only the treating dentist records them.")
    try:
        _svc(request).assert_criterion(case_id, criterion_id, value, actor.name, actor.licence, note.strip() or None, role=actor.role)
    except (KeyError, ValueError) as e:
        return _error(request, 400, "Invalid assertion", str(e))
    return _to(request, f"/cases/{case_id}#assertions")


@router.post("/cases/{case_id}/assert/bulk")
async def bulk_assert(request: Request, case_id: str):
    actor = _actor(request)
    if not actor.is_dentist:
        return _error(request, 403, "Dentist only", "Clinician assertions are attributed clinical judgment; only the treating dentist records them.")
    form = await request.form()
    selected = form.getlist("selected")
    if not selected:
        return _error(request, 400, "No selection", "Select at least one criterion to record.")
    items: list[dict] = []
    for cid in selected:
        val = form.get(f"value_{cid}")
        note_raw = form.get(f"note_{cid}", "")
        note = note_raw.strip() if isinstance(note_raw, str) else None
        if not val:
            continue  # nothing chosen for this row; skip
        items.append({"criterion_id": cid, "value": val, "note": note or None})
    if not items:
        return _error(request, 400, "No value", "Choose Met / Not met / N/A for each selected criterion.")
    try:
        _svc(request).assert_many(case_id, items, actor.name, actor.licence, role=actor.role)
    except (KeyError, ValueError) as e:
        return _error(request, 400, "Invalid assertion", str(e))
    return _to(request, f"/cases/{case_id}#assertions")


@router.post("/cases/{case_id}/proposals/{artifact_id}")
def decide_proposal(request: Request, case_id: str, artifact_id: str, decision: str = Form(...)):
    view = _view(request, case_id)
    if view is None or not any(p.artifact_id == artifact_id for p in view.proposals):
        return _error(request, 404, "Proposal not found", f"No proposed evidence '{artifact_id}' on this case.")
    try:
        _svc(request).confirm_proposal(case_id, artifact_id, decision, _actor(request).name)
    except ValueError as e:
        return _error(request, 400, "Invalid decision", str(e))
    return _to(request, f"/cases/{case_id}")


# --- screen 3: packet preview & sign-off -------------------------------------------------------------


@router.get("/cases/{case_id}/packet", response_class=HTMLResponse)
def packet(request: Request, case_id: str):
    view = _view(request, case_id)
    if view is None:
        return _error(request, 404, "Case not found", f"No case '{case_id}' in the demo set.")
    narrative, narrative_note = _narrative(view, _svc(request).pack)
    pk = _build_packet(request, view, narrative)
    return _render(request, "packet.html", view=view, case=view.case, a=view.assessment, narrative=narrative,
                   narrative_note=narrative_note, pk=pk, can_sign=view.assessment.verdict in READY_VERDICTS,
                   blocking=[x for x in view.assessment.actions if x.blocking])


@router.get("/cases/{case_id}/packet/preview.pdf")
def packet_pdf(request: Request, case_id: str):
    p = request.app.state.packets_dir / case_id / "preview.pdf"
    if not p.exists():
        return Response("preview.pdf has not been rendered for this case", status_code=404, media_type="text/plain")
    return FileResponse(p, media_type="application/pdf")


@router.get("/cases/{case_id}/packet/download")
def packet_download(request: Request, case_id: str):
    view = _view(request, case_id)
    if view is None:
        return _error(request, 404, "Case not found", f"No case '{case_id}' in the demo set.")
    if not view.signed:
        return _error(request, 409, "Not signed", "The packet can be downloaded once the treating dentist has signed off on this assessment.")
    narrative, _ = _narrative(view, _svc(request).pack)
    pk = _build_packet(request, view, narrative)
    if not pk["report"].shippable:
        return _error(request, 409, "Verifier refused", "The independent verifier did not pass this packet: " + "; ".join(pk["report"].findings))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(pk["dir"].rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(pk["dir"]).as_posix())
    _svc(request).store.audit(case_id, _actor(request).name, "download_packet", f"{buf.tell()} bytes")
    return Response(buf.getvalue(), media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="ophi-packet-{case_id}.zip"'})


@router.post("/cases/{case_id}/narrative")
def save_narrative(request: Request, case_id: str, narrative: str = Form("")):
    try:
        _svc(request).save_narrative(case_id, _form_text(narrative), _actor(request).name)
    except NarrativeInvalid as e:
        return _narrative_error(request, e)
    return _to(request, f"/cases/{case_id}/packet")


def _narrative_error(request: Request, e: NarrativeInvalid) -> HTMLResponse:
    return _error(request, 409, "Narrative not accepted",
                  "Every clinical statement must be grounded in the chart and Ophi's own voice must not assert approval or coverage. "
                  + " ".join(e.violations))


@router.post("/cases/{case_id}/sign-off")
def sign_off(request: Request, case_id: str, narrative: str = Form("")):
    actor = _actor(request)
    if not actor.is_dentist:
        return _error(request, 403, "Dentist only", "Sign-off is the treating dentist's attestation; only the dentist may record it.")
    try:
        _svc(request).sign_off(case_id, actor.name, actor.licence, _form_text(narrative), role=actor.role)
    except NarrativeInvalid as e:
        return _narrative_error(request, e)
    except PermissionError as e:
        return _error(request, 409, "Sign-off is blocked", f"{e}. Sign-off is blocked until every requirement is satisfied or accepted.")
    return _to(request, f"/cases/{case_id}/packet")


@router.post("/cases/{case_id}/submitted")
def mark_submitted(request: Request, case_id: str):
    _svc(request).mark_submitted(case_id, _actor(request).name)
    return _to(request, f"/cases/{case_id}/packet")


# --- screen 4: look-back -----------------------------------------------------------------------------


@router.get("/look-back", response_class=HTMLResponse)
def look_back(request: Request):
    from ophi.lookback import run_lookback
    try:
        report = run_lookback()
    except Exception as e:  # a broken retrospective must not take the demo down
        return _render(request, "lookback.html", report=None, unavailable=f"Look-back could not run: {e}")
    return _render(request, "lookback.html", report=report, unavailable=None,
                   months=present.lookback_months(report), gaps=present.lookback_gaps(report))


@router.get("/outcomes", response_class=HTMLResponse)
def outcomes(request: Request):
    from ophi.outcomes.report import build
    try:
        report = build(_svc(request).pack)
    except Exception as e:  # no outcomes database configured must not take the demo down
        return _render(request, "outcomes.html", report=None, unavailable=f"Past outcomes are unavailable: {e}")
    return _render(request, "outcomes.html", report=report, unavailable=None)


# --- screen 5: settings & audit -----------------------------------------------------------------------


@router.get("/settings", response_class=HTMLResponse)
def settings(request: Request):
    svc = _svc(request)
    events = sorted(svc.store.audit_log(), key=lambda e: e.at, reverse=True)
    ids = svc.case_ids()
    engine_version = svc.view(ids[0]).assessment.engine_version if ids else "—"
    return _render(request, "settings.html", events=events, engine_version=engine_version, case_count=len(ids))


@router.get("/settings/audit.csv")
def audit_csv(request: Request):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["at", "case_id", "actor", "event", "detail"])
    for e in _svc(request).store.audit_log():
        w.writerow([e.at.isoformat(), e.case_id, e.actor, e.event, e.detail])
    return Response(buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="ophi-audit-{datetime.now(UTC):%Y%m%d}.csv"'})


@router.post("/reset")
def reset(request: Request):
    _svc(request).reset()
    shutil.rmtree(request.app.state.packets_dir, ignore_errors=True)
    return RedirectResponse(_home(request), status_code=303)


# --- api & actor ---------------------------------------------------------------------------------------


@router.get("/api/cases/{case_id}/assessment.json")
def assessment_json(request: Request, case_id: str):
    view = _view(request, case_id)
    if view is None:
        return Response('{"error": "case not found"}', status_code=404, media_type="application/json")
    return Response(view.assessment.model_dump_json(indent=2), media_type="application/json")


@router.post("/actor")
def set_actor(request: Request, actor: str = Form(...)):
    resp = _back(request, _home(request))
    if actor in ACTORS:
        resp.set_cookie("actor", actor, httponly=True, samesite="lax", path=_home(request))
    return resp


# --- factory -----------------------------------------------------------------------------------------


def create_app(svc: CaseService | None = None, packets_dir: Path | None = None, base_path: str | None = None) -> FastAPI:
    """`base_path` serves every screen under a prefix, for the demo proxied at ophi.app/<slug>."""
    base = (os.environ.get("OPHI_BASE_PATH", "") if base_path is None else base_path).rstrip("/")
    app = FastAPI(title="Ophi", docs_url=None, redoc_url=None)
    app.state.svc = svc or CaseService(weights=load_weights())
    app.state.packets_dir = packets_dir or (app.state.svc.store.root / "packets")
    app.state.base_path = base
    app.mount(f"{base}/static", StaticFiles(directory=str(HERE / "static")), name="static")
    app.include_router(router, prefix=base)
    if base:  # the proxy strips trailing slashes, so the queue must answer at the bare prefix too
        app.add_api_route(base, queue, response_class=HTMLResponse, include_in_schema=False)
    else:  # live-PMS API is lab-only: a base path means the public demo, which must not expose patient search
        app.include_router(abeldent_api.router)
    return app


app = create_app()
