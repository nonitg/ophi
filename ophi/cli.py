"""Command line: assess a case, build a packet, run evals, serve the demo."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ophi.casegen.dsl import load_case
from ophi.engine.assess import assess
from ophi.extract.proposer import propose_for_case
from ophi.outcomes.weights import load as load_weights
from ophi.rules.loader import default_pack


def cmd_assess(args: argparse.Namespace) -> int:
    case = load_case(Path(args.case))
    case = case.with_artifacts(propose_for_case(case))
    a = assess(case, default_pack(), load_weights())
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
    a = assess(case, default_pack())
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
    from ophi.outcomes import store, weights
    from ophi.outcomes.ingest import ingest_dir

    pack = default_pack()
    with store.connect() as conn:
        if args.action == "ingest":
            c = ingest_dir(conn, [Path(d) for d in args.dirs], pack)
            print(f"ingested {c['submissions']} submissions, {c['assessed']} assessed against {pack.id} {pack.version}")
            return 0
        rows = store.denial_lift(conn, pack.version)
    w = weights.compute(pack.version, rows)
    path = weights.write(w)
    print(f"{'requirement':<26} {'missing':>12} {'present':>12}  lift")
    for r in rows:
        print(f"{r['requirement_id']:<26} {r['denied_missing']:>4}/{r['n_missing']:<4} denied {r['denied_present']:>4}/{r['n_present']:<4} denied {w.lift[r['requirement_id']]:+.2f}")
    print(f"weights: {path}  (lift is 0 when either side has fewer than {weights.MIN_N} cases)")
    return 0


def main(argv: list[str] | None = None) -> int:
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

    sv = sub.add_parser("serve", help="run the web app")
    sv.add_argument("--host", default="127.0.0.1")
    sv.add_argument("--port", type=int, default=8765)
    sv.add_argument("--reload", action="store_true")
    sv.set_defaults(fn=cmd_serve)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
