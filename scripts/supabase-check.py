"""Check the app's Supabase login from .env and count what's stored; never prints the URL."""
from dotenv import load_dotenv

from ophi.outcomes import store

load_dotenv()
with store.connect() as conn:
    print("connected as", conn.execute("select current_user").fetchone()[0])
    for t in ("clinic", "past_request", "submission", "decision", "requirement_result", "denial_map"):
        print(f"  outcomes.{t}: {conn.execute(f'select count(*) from outcomes.{t}').fetchone()[0]}")
    for t in ("patient_case", "case_state", "followup", "audit_event"):
        print(f"  app.{t}: {conn.execute(f'select count(*) from app.{t}').fetchone()[0]}")
    print("  last workflow writes:")
    for cid, at in conn.execute("select case_id, updated_at from app.case_state order by updated_at desc limit 5"):
        print(f"    {cid} {at:%Y-%m-%d %H:%M:%S}")
    print("  last audit events:")
    for at, cid, ev in conn.execute("select at, case_id, event from app.audit_event order by id desc limit 5"):
        print(f"    {at:%Y-%m-%d %H:%M:%S} {cid} {ev}")
