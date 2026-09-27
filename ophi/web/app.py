"""Ophi web app — server-rendered screens over `CaseService`. Nothing here judges a case.

Worklist (every open preauthorization by the step it is on) → Case (the steps from chart to chair) →
Packet (preview, narrative, the dentist's sign-off) → Recover (past denials worth a call) → Results
(what Ophi has done for the clinic) → Settings & audit.
"""

from __future__ import annotations

import asyncio
import csv
import hashlib
import io
import json
import logging
import os
import shutil
import threading
import time
import zipfile
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from pathlib import Path

from fastapi import APIRouter, FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ophi import db_store, demo, fixes, letters, workflow
from ophi.callscript import draft_call_script
from ophi.engine.models import Status
from ophi.outcomes import past_store, past_view, readout, similar, store
from ophi.outcomes.live import LiveScorer
from ophi.outcomes.weights import load as load_weights
from ophi.packet.build import build_packet
from ophi.packet.documents import narrative_ascii
from ophi.packet.narrative import draft_narrative
from ophi.rules import auto
from ophi.rules.loader import load_pack
from ophi.service import CaseService, CaseView, NarrativeInvalid, identity_tokens
from ophi.sources import abeldent
from ophi.sources.pms_lookback import PmsLookBack
from ophi.sources.pms_repository import AbelDentPmsRepository
from ophi.verify.verifier import verify_packet
from ophi.web import abeldent_api, present
from ophi.web.present import ACTORS, DEFAULT_ACTOR, READY_VERDICTS, Actor

HERE = Path(__file__).resolve().parent
log = logging.getLogger("uvicorn.error")  # uvicorn's own app logger, so lines reach the `make demo` terminal
# Static assets are cached by the browser; the newest mtime in static/ busts that cache on each deploy.
STATIC_V = max(int(p.stat().st_mtime) for p in (HERE / "static").rglob("*") if p.is_file())
templates = Jinja2Templates(directory=str(HERE / "templates"))
templates.env.globals.update(
    STATIC_V=STATIC_V, money=present.money, short_date=present.short_date, long_date=present.long_date,
    full_date=present.full_date, day_heading=present.day_heading, sentence=present.sentence, plain_label=present.plain_label, local_time=present.local_time, days_until=present.days_until, in_days=present.in_days, plural=present.plural,
    tooth_name=present.tooth_name, source_title=present.source_title, kb=present.kb, requirement_detail=present.requirement_detail, action_title=present.action_title,
    who_tag=present.who_tag, initials=present.initials, skipped_note=present.skipped_note, VERDICT_LABEL=present.VERDICT_LABEL, VERDICT_CLASS=present.VERDICT_CLASS,
    STATUS_LABEL=present.STATUS_LABEL, STATUS_CLASS=present.STATUS_CLASS, STATUS_NA=Status.NOT_APPLICABLE,
    STAGE_LABEL=present.STAGE_LABEL, FOLLOWUP_LABEL=present.FOLLOWUP_LABEL, ACTORS=ACTORS,
    TURNAROUND_DAYS=workflow.SUN_LIFE_TURNAROUND_DAYS, TURNAROUND_SOURCE=workflow.TURNAROUND_SOURCE,
    RECONSIDERATION_DAYS=workflow.RECONSIDERATION_DAYS, RISK_LABEL=present.RISK_LABEL,
)

# Confirmation after a write, named with the same verb as the button that caused it.
DONE_MESSAGES = {
    "confirmed": "Chart note confirmed.", "rejected": "Chart note rejected.", "criteria": "Criteria recorded.",
    "saved": "Narrative saved.", "signed": "Packet signed.", "signed_test": "Test packet signed.", "sent": "Marked as sent.",
    "decision": "Sun Life's decision recorded.", "resubmit": "Resubmission started. The dentist reviews and signs the new request.",
    "booked": "Marked as booked.", "asked": "Marked done. Sun Life's request is covered.", "followup": "Follow-up saved.", "undone": "Step taken back.",
    "skipped": "Gaps skipped for this test run.", "restored": "Gaps are back.",
    "fixed": "Fix applied.", "rules_used": "Rule update saved. It applies from its effective date.",
    "rules_checking": "Checking CDCP sources. Reload in a minute.", "rules_busy": "A check is already running. Reload in a minute.",
    "captured": "Taken. Ophi checked the chart again.", "chair_done": "Nothing left to take. The patient can go.",
}
_RESET_LOCK = threading.Lock()  # a double-submitted reset must not reseed twice at once
PMS_SYNC_SECONDS = 30  # how stale the PMS's sent/decided steps may get: each sync is a round trip to the VM

router = APIRouter()


# --- plumbing ---------------------------------------------------------------------------------------


def _svc(request: Request) -> CaseService:
    app = request.app
    if app.state.seed_demo and not app.state.seeded:  # first request, not startup: serverless hosts may skip startup
        with _RESET_LOCK:
            if not app.state.seeded:
                demo.seed(app.state.svc)
                app.state.seeded = True
    _sync_pms(app)
    return app.state.svc


def _sync_pms(app) -> None:
    """Pull what the PMS knows about sent requests, at most every PMS_SYNC_SECONDS. A PMS that can't be reached
    leaves the board as staff last recorded it."""
    if app.state.svc.pms_claims is None or time.monotonic() - app.state.pms_synced_at < PMS_SYNC_SECONDS:
        return
    app.state.pms_synced_at = time.monotonic()
    try:
        app.state.svc.sync_from_pms()
    except RuntimeError as e:  # chart_dump.VmSqlError: the VM is down or rejected the query
        log.warning(f"PMS sync skipped: {e}")


def _note_reason(text: str) -> str | None:
    """Which denial reason Sun Life's note names, when Gemini can say; otherwise staff pick it."""
    try:
        return letters.read_note(text).reason_key
    except letters.LetterError as e:
        log.warning(f"PMS sync: couldn't read Sun Life's note: {e}")
        return None


def _base(request: Request) -> str:
    return request.app.state.base_path


def _home(request: Request) -> str:
    return _base(request) or "/"


def _known_readout(request: Request, case) -> readout.Readout | None:
    """The fix plan already made for this chart: the last live one while the chart is unchanged, else the offline one.
    Never runs the models, so a page listing every case stays fast."""
    live = request.app.state.live
    return (live.cached(case) if live else None) or readout.load(case.case_id)


def _actors_for(case) -> dict[str, Actor]:
    """Signed in against one chart: the dentist is the one the PMS put on it."""
    return present.actors(present.case_provider(case))


def _actors(request: Request, case_id: str | None = None) -> dict[str, Actor]:
    """The people who can be signed in. The dentist is the one the PMS put on the chart in hand, so the header, the
    criteria and the signature never name a dentist other than this case's. Away from a case, the clinic's name for
    the dentist, when its charts agree on one."""
    app = request.app
    if case_id is not None:
        try:
            return _actors_for(app.state.svc.base_case(case_id))
        except (FileNotFoundError, KeyError):
            pass
    if app.state.provider is None:
        app.state.provider = present.treating_provider(app.state.svc) or ""
    return present.actors(app.state.provider)


def _actor(request: Request, case_id: str | None = None) -> Actor:
    a = _actors(request, case_id)
    return a.get(request.cookies.get("actor", ""), a[DEFAULT_ACTOR])


def _render(request: Request, name: str, status: int = 200, **ctx) -> HTMLResponse:
    svc = _svc(request)
    if request.app.state.auto_rules:  # a week-old source check restarts in the background; the page never waits
        auto.maybe_start(request.app.state.rules_env)
    base = _base(request)
    ctx.setdefault("pack", ctx["view"].pack if "view" in ctx else svc.pack)  # a case's pages cite its own pack
    acts = _actors_for(ctx["view"].case) if "view" in ctx else _actors(request)
    ctx.update(actor=acts.get(request.cookies.get("actor", ""), acts[DEFAULT_ACTOR]), ACTORS=acts, request=request, today=svc.today(),
               done=DONE_MESSAGES.get(request.query_params.get("done", "")),
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


def _done(request: Request, path: str, key: str) -> RedirectResponse:
    """Back to a screen under the app's prefix, with the confirmation for what was just done."""
    url, _, frag = path.partition("#")
    return RedirectResponse(f"{_base(request)}{url}?done={key}" + (f"#{frag}" if frag else ""), status_code=303)


def _form_text(text: str) -> str:
    """Browsers submit textarea content with CRLF; the packet and its hash are built over LF text."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


class BadDate(ValueError):
    pass


def _form_date(value: str) -> date | None:
    """Empty means 'not given'; anything else must be a real date, or the form is refused rather than guessed."""
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as e:
        raise BadDate(f"'{value}' is not a date") from e


def _dentist_only(request: Request, what: str) -> HTMLResponse | None:
    actor = _actor(request)
    if actor.is_dentist:
        return None
    return _error(request, 403, "Dentist only", f"{what} Switch Acting as to the treating dentist.")


def _packet_dir(request: Request, case_id: str) -> Path:
    d: Path = request.app.state.packets_dir / case_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _narrative(view: CaseView, pack) -> str:
    """Saved edits win; otherwise the template drafter."""
    if view.state.narrative_edits is not None:
        return view.state.narrative_edits
    return draft_narrative(view.case, view.assessment, pack)


def _build_packet(request: Request, view: CaseView, narrative: str) -> dict:
    """Assemble the packet into var/packets/{case_id}/ and run the independent verifier over it."""
    out = _packet_dir(request, view.case.case_id)
    result: dict = {"dir": out, "manifest": None, "files": [], "report": None, "pdf": out / "preview.pdf"}
    sign_off = view.state.sign_off if view.signed else None  # a stale sign-off never reaches the packet
    manifest = _existing_manifest(out, view, narrative, sign_off)
    if manifest is None:
        manifest = build_packet(view.case, view.assessment, out, narrative_text=narrative, sign_off=sign_off, pack=view.pack)
    result["manifest"] = manifest
    result["files"] = present.manifest_files(manifest, view.case)
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


# --- worklist ---------------------------------------------------------------------------------------


@router.get("/", response_class=HTMLResponse)
def worklist(request: Request):
    svc = _svc(request)
    views = svc.queue()
    live = request.app.state.live
    # The board never waits on the models: it shows the plans it already has, and scores the rest in the
    # background so the case staff click next is ready by the time they get there.
    risks = {v.case.case_id: r for v in views if v.stage in workflow.CHART_STAGES
             and (r := present.board_risk(v, _known_readout(request, v.case), v.pack))}
    if live:
        live.warm_cases([v.case for v in views])  # any card can be clicked, and the case page scores every stage
    prefills = {v.case.case_id: n for v in views if v.stage in (*workflow.CHART_STAGES, workflow.Stage.DENTIST)
                and (n := present.prefilled(v, present.pre_reads_for(v, v.pack, _known_readout(request, v.case))))}
    return _render(request, "board.html", b=present.board(views, _actor(request), svc.today(), risks, prefills,
                                                           auto.review_status(request.app.state.rules_env)))


# --- case -------------------------------------------------------------------------------------------


@router.get("/cases/{case_id}", response_class=HTMLResponse)
def case_page(request: Request, case_id: str):
    return _case_page(request, case_id)


def _case_page(request: Request, case_id: str, **extra):
    view = _view(request, case_id)
    if view is None:
        return _error(request, 404, "Case not found", f"No case '{case_id}' in the demo set.")
    svc, actor = _svc(request), _actor(request, case_id)
    today = svc.today()
    live = request.app.state.live
    rd, gaps = live.latest(view.case) if live else readout.load(case_id), present.gap_rows(view)
    relevant, other = present.assertion_rows(view, view.pack, present.pre_reads_for(view, view.pack, rd))
    steps = present.case_steps(view)
    now = present.now_step(steps, actor)
    timing = present.timing(view, today)
    fx = present.fix_panel(view, rd, view.pack, gaps) if view.stage in workflow.CHART_STAGES else None
    ml = present.ml_debug(view, rd)
    log.info(present.ml_report(ml))
    return _render(request, "case.html", view=view, case=view.case, a=view.assessment, stage=view.stage,
                   steps=steps, now=now, waiting=present.waiting_on(now, actor, view.case.treatment.provider.name, timing),
                   next_case=present.next_up(svc.queue(), view, actor, today),
                   stepper=present.stepper(view, actor), gaps=gaps,
                   advisory=present.advisory(view),
                   timing=timing, advice=present.advice(view, timing, today), evidence=present.evidence_panel(view),
                   fx=fx, ml=ml,
                   plan=present.dentist_panel(view, rd) if view.stage in (*workflow.CHART_STAGES, workflow.Stage.DENTIST) else None,
                   criteria=relevant, crit=present.criteria_groups(view, relevant), criteria_other=other, activity=present.activity(svc.store.audit_log(case_id)),
                   applicable=[r for r in view.assessment.requirements if r.applicable],
                   not_applicable=[r for r in view.assessment.requirements if not r.applicable],
                   reasons=workflow.REASONS, **extra)


@router.post("/cases/{case_id}/assert")
def assert_criterion(request: Request, case_id: str, criterion_id: str = Form(...), value: str = Form(...), note: str = Form("")):
    if (denied := _dentist_only(request, "Clinical criteria are the treating dentist's judgment.")) is not None:
        return denied
    actor = _actor(request, case_id)
    try:
        _svc(request).assert_criterion(case_id, criterion_id, value, actor.name, actor.licence, note.strip() or None, role=actor.role)
    except (KeyError, ValueError) as e:
        return _error(request, 400, "Invalid answer", str(e))
    except PermissionError as e:
        return _error(request, 409, "Already sent", str(e).capitalize() + ".")
    return _done(request, f"/cases/{case_id}", "criteria")


@router.post("/cases/{case_id}/assert/bulk")
async def bulk_assert(request: Request, case_id: str):
    """Record every criterion the dentist answered on the form. Unchanged answers are not re-recorded, so
    re-saving the form never voids a sign-off by itself."""
    if (denied := _dentist_only(request, "Clinical criteria are the treating dentist's judgment.")) is not None:
        return denied
    view = _view(request, case_id)
    if view is None:
        return _error(request, 404, "Case not found", f"No case '{case_id}' in the demo set.")
    actor, svc = _actor(request), _svc(request)
    rows = present.assertion_rows(view, view.pack, present.pre_reads_for(view, view.pack, _known_readout(request, view.case)))[0]
    form = await request.form()
    items: list[dict] = []
    for r in rows:
        cid, cur = r["id"], r["current"]
        val = form.get(f"value_{cid}")
        note = (form.get(f"note_{cid}") or "").strip() or None
        if not val or (cur and cur.value == val and (cur.note or None) == note):
            continue
        items.append({"criterion_id": cid, "value": val, "note": note, "ophi": r["pre"].suggest if r["pre"] else None})
    if not items:
        return _done(request, f"/cases/{case_id}", "criteria")
    try:
        svc.assert_many(case_id, items, actor.name, actor.licence, role=actor.role)
    except (KeyError, ValueError) as e:
        return _error(request, 400, "Invalid answer", str(e))
    except PermissionError as e:
        return _error(request, 409, "Already sent", str(e).capitalize() + ".")
    return _done(request, f"/cases/{case_id}", "criteria")


@router.post("/cases/{case_id}/proposals/{artifact_id}")
def decide_proposal(request: Request, case_id: str, artifact_id: str, decision: str = Form(...)):
    view = _view(request, case_id)
    if view is None or not any(p.artifact_id == artifact_id for p in view.proposals):
        return _error(request, 404, "Chart note not found", f"No proposed evidence '{artifact_id}' on this case.")
    try:
        _svc(request).confirm_proposal(case_id, artifact_id, decision, _actor(request, case_id).name)
    except ValueError as e:
        return _error(request, 400, "Invalid decision", str(e))
    except PermissionError as e:
        return _error(request, 409, "Already sent", str(e).capitalize() + ".")
    return _done(request, f"/cases/{case_id}", decision)


@router.post("/cases/{case_id}/fixes")
async def apply_fixes(request: Request, case_id: str):
    """Apply the fixes Ophi can make itself: the ones ticked, or with `all`, every one open on the case."""
    view = _view(request, case_id)
    if view is None:
        return _error(request, 404, "Case not found", f"No case '{case_id}' in the demo set.")
    form = await request.form()
    ids = [str(x) for x in form.getlist("fix")]
    if form.get("all"):
        ids = fixes.open_on(view.assessment)
    try:
        _svc(request).apply_fixes(case_id, ids, _actor(request).name)
    except ValueError as e:
        return _error(request, 400, "Nothing to apply", str(e).capitalize() + ".")
    except PermissionError as e:
        return _error(request, 409, "Already sent", str(e).capitalize() + ".")
    return _done(request, f"/cases/{case_id}#now", "fixed")


@router.post("/cases/{case_id}/submitted")
def mark_submitted(request: Request, case_id: str, on: str = Form("")):
    if _view(request, case_id) is None:
        return _error(request, 404, "Case not found", f"No case '{case_id}' in the demo set.")
    try:
        _svc(request).mark_submitted(case_id, _actor(request, case_id).name, _form_date(on))
    except PermissionError as e:
        return _error(request, 409, "Can't mark it sent", str(e).capitalize() + ".")
    except ValueError as e:
        return _error(request, 400, "Check the date", str(e).capitalize() + ".")
    return _done(request, f"/cases/{case_id}", "sent")


@router.post("/cases/{case_id}/letter", response_class=HTMLResponse)
async def read_letter(request: Request, case_id: str, letter: UploadFile = File(...)):
    """Gemini reads Sun Life's letter; the case page comes back with the decision form filled in for staff to check."""
    if _view(request, case_id) is None:
        return _error(request, 404, "Case not found", f"No case '{case_id}' in the demo set.")
    data = await letter.read()
    try:
        reading = await asyncio.to_thread(letters.read_letter, data, letter.content_type or "")
    except letters.LetterError as e:
        return _case_page(request, case_id, letter_error=str(e))
    _svc(request).audit(case_id, _actor(request).name, "read_letter", f"{letter.filename}: {reading.outcome}")
    return _case_page(request, case_id, letter=reading)


@router.post("/cases/{case_id}/decision")
def record_decision(request: Request, case_id: str, outcome: str = Form(""), decided_on: str = Form(""), reason: str = Form(""),
                    reason_key: str = Form("")):
    try:
        on = _form_date(decided_on)
    except BadDate as e:
        return _error(request, 400, "Check the date", str(e).capitalize() + ".")
    if on is None or outcome not in ("approved", "denied"):
        return _error(request, 400, "Decision incomplete", "Choose Sun Life's decision and the date on it.")
    try:
        _svc(request).record_decision(case_id, outcome, on, _form_text(reason), _actor(request, case_id).name,
                                      reason_key=reason_key if outcome == "denied" and reason_key else None)
    except PermissionError as e:
        return _error(request, 409, "Not waiting on Sun Life", str(e).capitalize() + ".")
    except ValueError as e:
        return _error(request, 400, "Check the date", str(e).capitalize() + ".")
    return _done(request, f"/cases/{case_id}", "decision")


@router.post("/cases/{case_id}/resubmit")
def start_resubmission(request: Request, case_id: str, reason_key: str = Form("")):
    try:
        _svc(request).start_resubmission(case_id, _actor(request, case_id).name, reason_key or None)
    except PermissionError as e:
        return _error(request, 409, "Nothing to resubmit", str(e).capitalize() + ".")
    except ValueError as e:
        return _error(request, 400, "Pick Sun Life's reason", str(e).capitalize() + ".")
    return _done(request, f"/cases/{case_id}", "resubmit")


@router.post("/cases/{case_id}/ask/done")
def resolve_ask(request: Request, case_id: str):
    try:
        _svc(request).resolve_ask(case_id, _actor(request, case_id).name)
    except PermissionError as e:
        return _error(request, 409, "Nothing open", str(e).capitalize() + ".")
    return _done(request, f"/cases/{case_id}", "asked")


@router.post("/cases/{case_id}/booked")
def mark_booked(request: Request, case_id: str, on: str = Form("")):
    try:
        day = _form_date(on)
    except BadDate as e:
        return _error(request, 400, "Check the date", str(e).capitalize() + ".")
    if day is None:
        return _error(request, 400, "Date needed", "Enter the date of the crown appointment.")
    try:
        _svc(request).mark_booked(case_id, day, _actor(request, case_id).name)
    except PermissionError as e:
        return _error(request, 409, "Sun Life's decision isn't recorded", str(e).capitalize() + ".")
    except ValueError as e:
        return _error(request, 400, "Check the date", str(e).capitalize() + ".")
    return _done(request, f"/cases/{case_id}", "booked")


@router.post("/cases/{case_id}/test-skip")
def test_skip(request: Request, case_id: str):
    try:
        _svc(request).skip_gaps(case_id, _actor(request, case_id).name)
    except FileNotFoundError:
        return _error(request, 404, "Case not found", f"No case '{case_id}' in the demo set.")
    except PermissionError as e:
        return _error(request, 409, "Nothing to skip", str(e).capitalize() + ".")
    return _done(request, f"/cases/{case_id}", "skipped")


@router.post("/cases/{case_id}/capture")
def capture(request: Request, case_id: str, requirement_id: str = Form(""), back: str = Form("")):
    """Demo: a clinician took a chair gap; the case moves on by itself once the chart shows it."""
    svc = _svc(request)
    try:
        svc.record_capture(case_id, requirement_id, _actor(request, case_id).name)
    except FileNotFoundError:
        return _error(request, 404, "Case not found", f"No case '{case_id}' in the demo set.")
    except PermissionError as e:
        return _error(request, 409, "Nothing to take", str(e).capitalize() + ".")
    left = svc.view(case_id).stage == workflow.Stage.PATIENT
    return _done(request, "/" if back == "board" else f"/cases/{case_id}", "captured" if left else "chair_done")


@router.post("/cases/{case_id}/test-restore")
def test_restore(request: Request, case_id: str):
    try:
        _svc(request).restore_gaps(case_id, _actor(request, case_id).name)
    except PermissionError as e:
        return _error(request, 409, "Can't restore the gaps", str(e).capitalize() + ".")
    return _done(request, f"/cases/{case_id}", "restored")


@router.post("/cases/{case_id}/undo")
def undo(request: Request, case_id: str, step: str = Form("")):
    try:
        _svc(request).undo(case_id, step, _actor(request, case_id).name)
    except PermissionError as e:
        return _error(request, 409, "Can't take that back", str(e).capitalize() + ".")
    return _done(request, f"/cases/{case_id}", "undone")


# --- packet -----------------------------------------------------------------------------------------


@router.get("/cases/{case_id}/packet", response_class=HTMLResponse)
def packet(request: Request, case_id: str):
    view = _view(request, case_id)
    if view is None:
        return _error(request, 404, "Case not found", f"No case '{case_id}' in the demo set.")
    svc = _svc(request)
    narrative = _narrative(view, view.pack)
    pk = _build_packet(request, view, narrative)
    nxt = present.next_up(svc.queue(), view, _actor(request, case_id), svc.today())
    return _render(request, "packet.html", view=view, case=view.case, a=view.assessment, narrative=narrative, pk=pk,
                   can_sign=view.assessment.verdict in READY_VERDICTS, stage=view.stage, next_case=nxt,
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
        return _error(request, 409, "Not signed", "The packet can be downloaded once the treating dentist has signed it.")
    svc = _svc(request)
    pk = _build_packet(request, view, _narrative(view, view.pack))
    if not pk["report"].shippable:
        return _error(request, 409, "Verifier refused", "The independent verifier did not pass this packet: " + "; ".join(pk["report"].findings))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(pk["dir"].rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(pk["dir"]).as_posix())
    svc.audit(case_id, _actor(request, case_id).name, "download_packet", f"{buf.tell()} bytes")
    return Response(buf.getvalue(), media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="ophi-packet-{case_id}.zip"'})


@router.post("/cases/{case_id}/narrative")
def save_narrative(request: Request, case_id: str, narrative: str = Form("")):
    try:
        _svc(request).save_narrative(case_id, _form_text(narrative), _actor(request, case_id).name)
    except NarrativeInvalid as e:
        return _narrative_error(request, e)
    except PermissionError as e:
        return _error(request, 409, "Already sent", str(e).capitalize() + ".")
    return _done(request, f"/cases/{case_id}/packet", "saved")


def _narrative_error(request: Request, e: NarrativeInvalid) -> HTMLResponse:
    return _error(request, 409, "Narrative not accepted",
                  "Every clinical statement must be grounded in the chart and Ophi's own voice must not assert approval or coverage. "
                  + " ".join(e.violations))


@router.post("/cases/{case_id}/sign-off")
def sign_off(request: Request, case_id: str, narrative: str = Form("")):
    if (denied := _dentist_only(request, "Sign-off is the treating dentist's attestation.")) is not None:
        return denied
    actor = _actor(request, case_id)
    try:
        _svc(request).sign_off(case_id, actor.name, actor.licence, _form_text(narrative), role=actor.role)
    except NarrativeInvalid as e:
        return _narrative_error(request, e)
    except PermissionError as e:
        return _error(request, 409, "Sign-off is blocked", str(e).capitalize() + ".")
    return _done(request, f"/cases/{case_id}/packet", "signed_test" if _view(request, case_id).test_run else "signed")


# --- recover & results ------------------------------------------------------------------------------


def _lookback_unavailable(e: Exception) -> str:
    return f"The look-back of past requests could not run ({e}). The worklist is not affected."


def _recover_page(request: Request, status: int = 200, **extra) -> HTMLResponse:
    svc = _svc(request)
    r = present.recover(svc.recover_rows(), svc.orphan_followups(), svc.today())
    return _render(request, "recover.html", status=status, r=r, **extra)


@router.get("/recover", response_class=HTMLResponse)
def recover(request: Request):
    try:
        return _recover_page(request)
    except Exception as e:  # a broken retrospective must not take the page down
        return _error(request, 503, "Recover is unavailable", _lookback_unavailable(e))


@router.post("/recover/{row_id}")
def recover_followup(request: Request, row_id: str, status: str = Form(...), note: str = Form(""),
                     callback_on: str = Form("")):
    try:
        _svc(request).record_followup(row_id, status, note, _actor(request).name, _form_date(callback_on))
    except KeyError:
        return _error(request, 404, "Not on the list", f"No past denial '{row_id}' is waiting on a call.")
    except ValueError as e:
        return _error(request, 400, "Invalid follow-up", str(e))
    return _done(request, f"/recover#r-{row_id}", "followup")


@router.post("/recover/{row_id}/script", response_class=HTMLResponse)
def recover_script(request: Request, row_id: str):
    """Draft what to say. Ophi never dials: a person reads this and makes the call."""
    svc = _svc(request)
    row = next((x["row"] for x in svc.recover_rows() if x["row"].case_id == row_id), None)
    if row is None:
        return _error(request, 404, "Not on the list", f"No past denial '{row_id}' is waiting on a call.")
    try:
        script = draft_call_script(row, svc.clinic_name())
    except letters.LetterError as e:
        return _recover_page(request, script_row=row_id, script_error=str(e))
    return _recover_page(request, script_row=row_id, script=script)


@router.get("/results", response_class=HTMLResponse)
def results(request: Request):
    svc = _svc(request)
    try:
        report, recovered = svc.lookback(), present.recover(svc.recover_rows())
    except Exception as e:  # a broken retrospective must not take the report down
        return _error(request, 503, "Results are unavailable", _lookback_unavailable(e))
    return _render(request, "results.html", res=present.results(svc.queue(), svc.pack, report, recovered))


def _own_rows(request: Request) -> list[dict]:
    """Past requests this app may show one at a time: its clinic's, or every clinic's when it serves no single one.
    A request names its patient's tooth, note and letter, so another clinic's is not the viewer's to read."""
    rows = request.app.state.past.rows()
    clinic = request.app.state.clinic
    return [r for r in rows if r["clinic_id"] == clinic] if clinic else rows


@router.get("/outcomes", response_class=HTMLResponse)
def outcomes(request: Request, status: str = "all", clinic: str = "", tooth: str = "", reason: str = "", page: int = 1):
    from ophi.outcomes.report import build
    try:
        rows = _own_rows(request)
    except Exception as e:  # no outcomes database configured must not take the demo down
        log.warning("past outcomes unavailable: %s", e)
        return _render(request, "outcomes.html", past=None, report=None, unavailable="Past outcomes are unavailable.")
    try:
        report = build(_svc(request).pack)
    except Exception as e:  # the pack's blind-spot report is secondary; the list still shows
        log.warning("outcomes report unavailable: %s", e)
        report = None
    past = past_view.listing(rows, status, clinic, tooth, reason, page)
    return _render(request, "outcomes.html", past=past, report=report, unavailable=None)


@router.get("/past/{preauth_id}", response_class=HTMLResponse)
def past_request(request: Request, preauth_id: str):
    try:
        row = past_view.find(_own_rows(request), preauth_id)
    except Exception as e:
        log.warning("past outcomes unavailable: %s", e)
        return _error(request, 503, "Past outcomes are unavailable", "The past requests could not be read. Try again shortly.")
    if row is None:
        return _error(request, 404, "Past request not found", f"No past request '{preauth_id}'.")
    svc, from_id = _svc(request), request.query_params.get("from")
    from_case = svc.base_case(from_id) if from_id in svc.case_ids() else None  # the case whose fix linked here
    return _render(request, "past.html", p=past_view.detail(row), from_case=from_case)


@router.get("/look-back")
def look_back(request: Request):
    return RedirectResponse(_base(request) + "/results#before", status_code=303)


# --- CDCP rule updates -------------------------------------------------------------------------------


def _rules_page(request: Request, error: str | None = None, status: int = 200) -> HTMLResponse:
    svc, env = _svc(request), request.app.state.rules_env.resolved()
    draft_dir = auto.current_draft(env.cdcp_dir)
    changes = None
    if draft_dir is not None:
        try:
            proposed = load_pack(draft_dir / "pack.yaml")
        except Exception:  # noqa: BLE001 — a broken draft still shows its draft.json; using it will refuse
            proposed = None
        if proposed is not None:
            changes = present.request_changes(svc.queue(), proposed, svc.assess_under)
    return _render(request, "rules.html", status=status, error=error, read_only=bool(request.app.state.base_path),
                   r=present.rules_page(auto.review_status(env), draft_dir, changes), DENTIST=_actors(request)["dentist"])


@router.get("/rules", response_class=HTMLResponse)
def rules(request: Request):
    return _rules_page(request)


def _read_only(request: Request) -> HTMLResponse | None:
    if request.app.state.base_path:  # the public demo shows rule updates but never checks or changes them
        return _error(request, 403, "Read-only demo", "Checking CDCP sources and using rule updates are off in this demo.")
    return None


@router.post("/rules/check")
def rules_check_now(request: Request):
    if (denied := _read_only(request)) is not None:
        return denied
    started = auto.maybe_start(request.app.state.rules_env, force=True)
    return _done(request, "/rules", "rules_checking" if started else "rules_busy")


@router.post("/rules/use")
async def rules_use(request: Request):
    """The treating dentist puts the waiting draft in force from its effective date. Every needs-a-person item
    must be ticked; that is the reviewer's acknowledgement, recorded with their name in the changelog."""
    from ophi.rules.approve import approve
    from ophi.rules.draft import DraftBlocked

    if (denied := _read_only(request)) is not None:
        return denied
    if request.cookies.get("actor") not in ACTORS:
        return _error(request, 403, "Who is this?", "Choose who you are under View as, then review the update again.")
    if (denied := _dentist_only(request, "The treating dentist puts CDCP rule updates into use.")) is not None:
        return denied
    env = request.app.state.rules_env.resolved()
    form = await request.form()
    draft_dir = auto.current_draft(env.cdcp_dir)
    shown = present.rules_page(None, draft_dir)["draft"] if draft_dir is not None else None
    if shown is None or form.get("draft") != draft_dir.name or form.get("draft_sha") != shown["sha"]:
        return _rules_page(request, "The rule update changed since you opened it. Review it again.", 409)
    items = shown["needs_person"]
    if any(form.get(f"ack-{i}") != "on" for i in range(len(items))):
        return _rules_page(request, "Tick each item that needs a person before using this rule update.", 400)
    try:
        approve(draft_dir, _actor(request).name, env.today, cdcp_dir=env.cdcp_dir, ack=bool(items), status=env.status)
    except (DraftBlocked, ValueError) as err:
        return _rules_page(request, f"This rule update was not used: {err}", 409)
    return _done(request, "/rules", "rules_used")


# --- settings & audit --------------------------------------------------------------------------------


@router.get("/settings", response_class=HTMLResponse)
def settings(request: Request):
    svc = _svc(request)
    ids = svc.case_ids()
    names = {cid: svc.base_case(cid).patient.display_name for cid in ids}
    try:
        names |= {r.case_id: r.patient_name for r in svc.lookback().rows}
    except Exception:  # names for Recover rows are a nicety; the log still renders with ids
        pass
    return _render(request, "settings.html", events=present.audit_rows(svc.store.audit_log(), names))


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
    svc = _svc(request)
    with _RESET_LOCK:
        svc.reset()
        shutil.rmtree(request.app.state.packets_dir, ignore_errors=True)
        if request.app.state.seed_demo:
            demo.seed(svc)
        request.app.state.pms_synced_at = float("-inf")  # the reseeded cases take the PMS's steps on the next page
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
        resp.set_cookie("actor", actor, httponly=True, samesite="lax")
    return resp


# --- factory -----------------------------------------------------------------------------------------


def create_app(svc: CaseService | None = None, packets_dir: Path | None = None, seed_demo: bool | None = None,
               base_path: str | None = None, live_ml: bool | None = None, auto_rules_check: bool | None = None,
               rules_env: auto.PackEnv | None = None) -> FastAPI:
    """`seed_demo` puts the demo cases at their places in the timeline on an empty store, on the first request.
    It defaults on for the demo's own service and off when a caller (a test) brings its own. `base_path`
    serves every screen under a prefix, for the demo proxied at ophi.app/<slug>. `live_ml` runs Laya and
    LightGBM on every case page open; it defaults from OPHI_LIVE_ML (on unless "0", "false" or "off") for the
    app's own service without a base path, and off for tests and the proxied demo, which ship without the
    models and read the offline readouts instead. `auto_rules_check` re-checks the CDCP
    sources in the background when a page is visited and the last check is a week old; it defaults from
    OPHI_AUTO_RULES_CHECK (on unless "0", "false" or "off") for the app's own service without a base path, and off
    otherwise (tests, the proxied demo). `rules_env` points
    the check and the /rules review page at other packs and another web (tests)."""
    base = (os.environ.get("OPHI_BASE_PATH", "") if base_path is None else base_path).rstrip("/")
    own = svc is None
    svc = svc or db_store.service_from_env(weights=load_weights()) or CaseService(weights=load_weights())
    if isinstance(svc.repository, AbelDentPmsRepository) and svc.pms_claims is None:  # cases from the VM: so are their claims
        pms = svc.repository
        svc.pms_claims, svc.note_reader = (lambda: abeldent.list_predeterminations(pms.sql)), _note_reason
        svc.lookback_report = PmsLookBack(pms).report  # the live clinic's own past, in place of the saved rows
    if live_ml is None:
        live_ml = (own and not base
                   and os.environ.get("OPHI_LIVE_ML", "1").strip().lower() not in ("0", "false", "off", "no"))
    live = LiveScorer(svc.pack_for) if live_ml else None
    past = past_store.Cached(store.connect)  # lazy: no database is touched until a page reads past requests
    if live:
        live.clinic_rate = lambda case: similar.clinic_denial_rate(past, store.connect, case)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if live:  # load the models before the first page, not during it
            await asyncio.to_thread(live.warm)
        yield

    app = FastAPI(title="Ophi", docs_url=None, redoc_url=None, lifespan=lifespan)
    app.state.live = live
    if auto_rules_check is None:  # like live_ml: the app's own service only, and never the proxied public demo
        auto_rules_check = (own and not base
                            and os.environ.get("OPHI_AUTO_RULES_CHECK", "1").strip().lower() not in ("0", "false", "off", "no"))
    app.state.auto_rules = auto_rules_check
    app.state.rules_env = rules_env or auto.PackEnv()
    app.state.past = past
    # One clinic's deployment sees only its own past requests one by one; unset (the demo) shows every clinic's.
    app.state.clinic = os.environ.get("OPHI_CLINIC_ID", "").strip() or None
    if app.state.clinic is None:
        log.warning("OPHI_CLINIC_ID is not set: past requests from every clinic are readable one at a time")
    app.state.provider = None  # the PMS's name for the treating dentist, read on the first page
    app.state.seed_demo = own if seed_demo is None else seed_demo
    app.state.seeded = False
    app.state.pms_synced_at = float("-inf")
    app.state.svc = svc
    app.state.packets_dir = packets_dir or (app.state.svc.store.root / "packets")
    app.state.base_path = base
    app.mount(f"{base}/static", StaticFiles(directory=str(HERE / "static")), name="static")
    app.include_router(router, prefix=base)
    if base:  # the proxy strips trailing slashes, so the worklist must answer at the bare prefix too
        app.add_api_route(base, worklist, response_class=HTMLResponse, include_in_schema=False)
    else:  # live-PMS API is lab-only: a base path means the public demo, which must not expose patient search
        app.include_router(abeldent_api.router)
    return app


app = create_app()
