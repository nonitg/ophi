"""Check the clinic split against the real outcomes database: counts stay corpus-wide, links stay one clinic's."""
import os
import re

from dotenv import load_dotenv

load_dotenv()
from ophi.outcomes import past_store, store  # noqa: E402  (needs SUPABASE_DB_URL loaded first)

CHIP = re.compile(r'href="/past/(PA-[A-Z0-9-]+)\?from=')
COUNTS = re.compile(r"Past requests like this: Sun Life[^<]*")


def page(clinic: str | None) -> str:
    from fastapi.testclient import TestClient
    from ophi.web.app import create_app
    app = create_app(live_ml=False)
    app.state.clinic = clinic
    return TestClient(app).get(f"/cases/{os.environ.get('SCOPE_CASE', 'kowalchuk')}").text


rows = {r["preauth_id"]: r["clinic_id"] for r in past_store.Cached(store.connect).rows()}
everyone = CHIP.findall(page(None))
owner = rows[everyone[0]]  # a clinic that owns one of the links the demo shows
for clinic in (None, owner, "SYN-P-NOBODY"):
    html = page(clinic)
    ids = CHIP.findall(html)
    clinics = {rows[i] for i in ids}
    print(f"clinic={clinic or '<all>'}: {len(ids)} links across {len(clinics)} clinics")
    print("  counts:", COUNTS.findall(html)[:1])
    if clinic:
        assert clinics <= {clinic}, f"leaked links from {clinics - {clinic}}"
print("ok")
