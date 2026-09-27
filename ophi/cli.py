"""Command line: assess a case, build a packet, run evals, serve the demo."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from ophi.casegen.dsl import load_case
from ophi.engine.assess import assess
from ophi.extract.proposer import propose_for_case
from ophi.outcomes.weights import load as load_weights
from ophi.rules.auto import PackEnv
from ophi.rules.loader import default_pack, pack_for


def cmd_assess(args: argparse.Namespace) -> int:
    case = load_case(Path(args.case))
    case = case.with_artifacts(propose_for_case(case))
    a = assess(case, pack_for(case), load_weights())
    if args.json:
        print(a.model_dump_json(indent=2))
        return 0
    print(f"{case.case_id}: {a.verdict}  {a.completeness['satisfied']}/{a.completeness['applicable']} requirements satisfied  "
          f"[{a.ruleset.id} {a.ruleset.version}]")
    print(f"  schedule: {a.schedule.disposition} — {a.schedule.detail}")
    for r in a.requirements:
        if not r.applicable:
            continue
        via = f" via {r.satisfied_via}" if r.satisfied_via else ""
        print(f"  {r.status.value:<32} {r.requirement_id}{via}")
        if args.verbose:
            print(f"      {r.explanation}")
    if a.actions:
        print("  actions:")
        for act in a.actions:
            print(f"    {act.rank}. [{'BLOCKING' if act.blocking else 'advisory'}] {act.title}")
            if args.verbose:
                print(f"       {act.why}")
    return 0


def cmd_packet(args: argparse.Namespace) -> int:
    from ophi.packet.build import build_packet
    from ophi.verify.verifier import verify_packet

    case = load_case(Path(args.case))
    case = case.with_artifacts(propose_for_case(case))
    a = assess(case, pack_for(case))
    out = Path(args.out) / case.case_id
    manifest = build_packet(case, a, out)
    tokens = [t for t in [*case.patient.display_name.split(), case.patient.patient_id, case.patient.cdcp_client_id or ""] if len(t) >= 3]
    report = verify_packet(out, forbidden_tokens=tokens)
    print(f"packet: {out}  files={len(manifest['files'])}  bytes={manifest['total_bytes']}")
    print(f"verifier: {'PASS' if report.ok else 'FAIL'}")
    for f in report.findings:
        print(f"  - {f}")
    return 0 if report.ok else 1


def cmd_eval(args: argparse.Namespace) -> int:
    from ophi.evals.run import run_all

    ok, report = run_all(Path(args.cases), Path(args.expected), write=args.write)
    print(report)
    return 0 if ok else 1


def cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    uvicorn.run("ophi.web.app:app", host=args.host, port=args.port, reload=args.reload)
    return 0


def cmd_outcomes(args: argparse.Namespace) -> int:
    from ophi import db_store
    from ophi.outcomes import past_store, store, weights
    from ophi.outcomes.ingest import ingest_dir

    pack = default_pack()
    with store.connect() as conn:
        if args.action == "ingest":
            c = ingest_dir(conn, [Path(d) for d in args.dirs], pack)
            print(f"ingested {c['submissions']} submissions, {c['assessed']} assessed against {pack.id} {pack.version}")
            p = past_store.save_all(conn, pack, [Path(d) for d in args.dirs])
            print(f"stored {p['requests']} past requests from {p['clinics']} clinics in outcomes.past_request")
            n = db_store.seed_cases(conn, Path("cases/demo"))
            print(f"stored {n} patient charts in app.patient_case")
            return 0
        rows = store.denial_lift(conn, pack.version)
    w = weights.compute(pack.version, rows)
    path = weights.write(w)
    print(f"{'requirement':<26} {'missing':>12} {'present':>12}  lift")
    for r in rows:
        print(f"{r['requirement_id']:<26} {r['denied_missing']:>4}/{r['n_missing']:<4} denied {r['denied_present']:>4}/{r['n_present']:<4} denied {w.lift[r['requirement_id']]:+.2f}")
    print(f"weights: {path}  (lift is 0 when either side has fewer than {weights.MIN_N} cases)")
    return 0


def _pack_env(args: argparse.Namespace) -> PackEnv:
    return args.env.resolved()


def _files(pairs: list[str]) -> dict[str, Path]:
    out = {}
    for pair in pairs:
        key, sep, path = pair.partition("=")
        if not sep or not key or not path:
            raise SystemExit(f"--file takes source=path, e.g. grid=~/Downloads/grid.pdf (got {pair!r})")
        out[key] = Path(path).expanduser()
    return out


def _print_check(r) -> None:
    print(f"check: pack {r.pack_version} against {len(r.sources)} sources — {len(r.changed)} changed, "
          f"{len(r.shrank)} shrank, {len(r.new_links)} new documents, {len(r.unreachable)} unreachable")
    for s in r.sources:
        note = {"unreachable": s.error, "shrank": f"{s.error}; needs a person",
                "manual": f"checked by hand; last read {s.last_read or 'never'} (pass --file {s.key}=<path>)"}.get(s.state, "")
        print(f"  {s.state:<11} {s.key:<10} {'by hand ' if s.by_hand else ''}{note}".rstrip())
    for n in r.new_links:
        print(f"  new         {n.title or '(untitled)'}  {n.url}")
    for page in r.unreachable_pages:
        print(f"  unreachable watch page {page}")


def _check(args: argparse.Namespace, e: PackEnv):
    from ophi.rules import watch

    try:
        r = watch.check(watch.latest_pack_dir(e.cdcp_dir), e.today, e.fetcher, e.config, _files(args.file))
    except KeyError as err:
        raise SystemExit(f"--file: {err.args[0]}") from None
    watch.save_status(r, e.status)
    _print_check(r)
    return r


def cmd_pack_check(args: argparse.Namespace) -> int:
    r = _check(args, _pack_env(args))
    for s in r.changed + r.shrank:
        print(f"\n{s.diff}")
    return 0


def cmd_pack_draft(args: argparse.Namespace) -> int:
    from ophi.rules import watch
    from ophi.rules.draft import DraftBlocked, draft

    e = _pack_env(args)
    r = _check(args, e)
    try:
        d = draft(r, e.today, e.fetcher, cases_dir=e.cases_dir, drafts_dir=e.cdcp_dir / "drafts")
    except DraftBlocked as err:
        print(f"draft blocked: {err}", file=sys.stderr)
        return 1
    if d.dir is None:
        watch.mark_reviewed(e.status)  # what was new has nothing for this pack and is now recorded as seen
        print(d.report_md.strip())
        return 0
    print(f"draft: {d.dir}  {len(d.changes)} changes, {len(d.needs_person)} need a person, "
          f"{len(d.out_of_scope)} out of scope, {len(d.impact)} cases change")
    print(f"  read {d.dir / 'report.md'}")
    return 0


def cmd_pack_approve(args: argparse.Namespace) -> int:
    from ophi.rules.approve import approve
    from ophi.rules.draft import DraftBlocked

    e = _pack_env(args)
    try:
        target = approve(Path(args.draft_dir), args.by, e.today, cdcp_dir=e.cdcp_dir, ack=args.ack, status=e.status)
    except (DraftBlocked, ValueError) as err:
        print(f"not approved: {err}", file=sys.stderr)
        return 1
    print(f"approved: {target}")
    return 0


def cmd_pack_baseline(args: argparse.Namespace) -> int:
    from ophi.rules import watch

    e = _pack_env(args)
    pack_dir = watch.latest_pack_dir(e.cdcp_dir)
    try:
        r = watch.baseline(pack_dir, e.today, e.fetcher, e.config, _files(args.file), note=args.note, force=args.force)
    except watch.BaselineRefused as err:
        print(f"baseline refused: {err}. Draft and review them, or pass --force.", file=sys.stderr)
        return 1
    except KeyError as err:
        raise SystemExit(f"--file: {err.args[0]}") from None
    replaced = [s.key for s in r.changed + r.shrank]
    print(f"baseline: {pack_dir}  {len(r.unreachable)} unreachable"
          + (f"; replaced the snapshots of {', '.join(replaced)}" if replaced else ""))
    for s in r.unreachable:
        print(f"  unreachable {s.key}: {s.error} (kept its previous snapshot)")
    if not r.unreachable:
        watch.mark_reviewed(e.status)
    return 0


def main(argv: list[str] | None = None, env: PackEnv | None = None) -> int:
    load_dotenv()  # SUPABASE_DB_URL; the nearest .env up from here, so worktrees share the main checkout's
    p = argparse.ArgumentParser(prog="ophi")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("assess", help="assess one casegen YAML")
    a.add_argument("case")
    a.add_argument("--json", action="store_true")
    a.add_argument("-v", "--verbose", action="store_true")
    a.set_defaults(fn=cmd_assess)

    pk = sub.add_parser("packet", help="assemble and verify a packet")
    pk.add_argument("case")
    pk.add_argument("--out", default="out")
    pk.set_defaults(fn=cmd_packet)

    ev = sub.add_parser("eval", help="run golden-expectation regression over cases/")
    ev.add_argument("--cases", default="cases")
    ev.add_argument("--expected", default="evals/expected")
    ev.add_argument("--write", action="store_true", help="(re)write expectations from current output")
    ev.set_defaults(fn=cmd_eval)

    oc = sub.add_parser("outcomes", help="ingest past preauth decisions; derive action tie-break weights")
    oc.add_argument("action", choices=["ingest", "stats"])
    oc.add_argument("dirs", nargs="*", default=["fixtures/cdcp_approvals", "fixtures/cdcp_denials", "fixtures/cdcp_crowns"])
    oc.set_defaults(fn=cmd_outcomes)

    pc = sub.add_parser("pack", help="check the pack's CDCP sources; draft and approve rule updates")
    pcs = pc.add_subparsers(dest="action", required=True)
    files = {"action": "append", "default": [], "metavar": "SOURCE=PATH",
             "help": "read this source from a local copy, e.g. grid=grid.pdf downloaded by hand"}
    x = pcs.add_parser("check", help="compare the sources with the baseline; list new documents")
    x.add_argument("--file", **files)
    x.set_defaults(fn=cmd_pack_check)
    x = pcs.add_parser("draft", help="check, then draft a pack update from what changed")
    x.add_argument("--file", **files)
    x.set_defaults(fn=cmd_pack_draft)
    x = pcs.add_parser("approve", help="turn a reviewed draft into a new pack version")
    x.add_argument("draft_dir")
    x.add_argument("--by", required=True, help="the person who reviewed the draft")
    x.add_argument("--ack", action="store_true", help="approve with needs-a-person items still open (logged)")
    x.set_defaults(fn=cmd_pack_approve)
    x = pcs.add_parser("baseline", help="record the sources as they read now as the newest pack's baseline")
    x.add_argument("--note", help="a note recorded in the lock")
    x.add_argument("--force", action="store_true", help="even while a change is pending review")
    x.add_argument("--file", **files)
    x.set_defaults(fn=cmd_pack_baseline)

    sv = sub.add_parser("serve", help="run the web app")
    sv.add_argument("--host", default="127.0.0.1")
    sv.add_argument("--port", type=int, default=8765)
    sv.add_argument("--reload", action="store_true")
    sv.set_defaults(fn=cmd_serve)

    args = p.parse_args(argv)
    args.env = env or PackEnv()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
