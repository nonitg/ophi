"""Check the app's Supabase login from .env and count what's stored; never prints the URL."""
from dotenv import load_dotenv

from ophi.outcomes import store

load_dotenv()
with store.connect() as conn:
    print("connected as", conn.execute("select current_user").fetchone()[0])
    for t in ("clinic", "past_request", "submission", "decision", "requirement_result", "denial_map"):
        print(f"  outcomes.{t}: {conn.execute(f'select count(*) from outcomes.{t}').fetchone()[0]}")
