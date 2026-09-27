from ophi.outcomes.live import LiveScorer
from ophi.rules.loader import default_pack
from ophi.service import CaseService
from tests._cases import DEMO_DAY
from tests.test_fixer import FakeScorer


class Counting(FakeScorer):
    calls = 0

    def score(self, requests, pack, clinic_denial_rate=None):
        Counting.calls += 1
        return super().score(requests, pack, clinic_denial_rate)


def test_scores_every_open_and_board_reuses_it_until_the_chart_changes():
    case = CaseService().base_case("kowalchuk")
    live = LiveScorer(lambda _case: default_pack(DEMO_DAY), model=Counting())
    rd = live.score(case)
    assert rd.matching(case)["model"] == {"laya": "fake", "risk": "fake"}
    calls = Counting.calls
    assert live.latest(case) is rd and Counting.calls == calls  # board: same chart, no new run
    live.score(case)
    assert Counting.calls > calls  # case page: always runs


def test_warm_cases_scores_in_the_background_so_the_case_page_never_waits():
    svc = CaseService()
    cases = [svc.base_case(cid) for cid in ("kowalchuk", "deng")]
    live = LiveScorer(lambda _case: default_pack(DEMO_DAY), model=Counting())
    live.warm_cases(cases)
    live._warming.acquire()  # the sweep releases it when every case is scored
    assert all(live.cached(c) is not None for c in cases)
