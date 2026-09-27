"""Past requests in Supabase: stored once from every export folder, read back as the same training data."""

from __future__ import annotations

import pytest

from tests import _pg
from ophi.outcomes import past_store, store
from ophi.outcomes.training_set import clinic_denial_rates, load_examples
from ophi.rules.loader import default_pack


@pytest.fixture(scope="module")
def conn():
    name, url = _pg.start()
    try:
        with store.connect(url) as c:
            store.migrate(c)
            past_store.save_all(c, default_pack())
            yield c
    finally:
        _pg.stop(name)


def test_training_reads_the_same_examples_as_the_files(conn):
    db, files = past_store.training_examples(conn), load_examples()
    assert [e.preauth_id for e in db] == [e.preauth_id for e in files]
    assert [(e.decision, e.truth, e.sent["services"]) for e in db] == [(e.decision, e.truth, e.sent["services"]) for e in files]
    assert all(e.sent["member"]["member_id"] != f.sent["member"]["member_id"] for e, f in zip(db, files))  # hashed


def test_every_folder_stored_without_the_answer_key(conn):
    rows = past_store.requests(conn)
    assert len(rows) == 720 and {r["source"] for r in rows} == {"cdcp_crowns", "cdcp_approvals", "cdcp_denials"}
    assert "truth" not in rows[0]
    assert past_store.save_all(conn, default_pack())["requests"] == 720  # idempotent


def test_clinic_rate_matches_training(conn):
    e = load_examples()[100]
    assert past_store.clinic_denial_rate(conn, e.clinic, e.submitted_on) == pytest.approx(clinic_denial_rates(load_examples())[e.preauth_id])
