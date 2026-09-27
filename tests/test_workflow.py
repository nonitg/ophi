"""Stage derivation and the scheduling dates that come from published figures."""

from datetime import date

from ophi.demo import seed
from ophi.service import CaseService, Store
from ophi.workflow import Stage, reconsider_by, send_by, valid_until


def test_dates_follow_the_published_turnaround_validity_and_reconsideration_windows():
    assert send_by(date(2026, 9, 24)) == date(2026, 9, 17)
    assert valid_until(date(2026, 9, 8)) == date(2027, 9, 8)
    assert reconsider_by(date(2026, 9, 3)) == date(2026, 11, 2)


def test_demo_seed_puts_one_case_at_every_stage_after_sign_off(tmp_path):
    svc = CaseService(store=Store(tmp_path / "state"))
    seed(svc)
    stages = {cid: svc.view(cid).stage for cid in svc.case_ids()}
    assert stages["singh"] == Stage.PATIENT and stages["tremblay"] == Stage.PREPARE and stages["whitfield"] == Stage.DENTIST
    assert (stages["fontaine"], stages["park"], stages["nguyen"], stages["marchand"]) == (Stage.SEND, Stage.SUN_LIFE, Stage.BOOK, Stage.RESUBMIT)
    seed(svc)  # a second run is a no-op on a store that already has history
    assert len([e for e in svc.store.audit_log() if e.event == "sign_off"]) == 5
