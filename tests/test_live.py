from ophi.outcomes.live import LiveScorer
from ophi.rules.loader import default_pack
from ophi.service import CaseService
from tests.test_fixer import FakeScorer


class Counting(FakeScorer):
    calls = 0

    def score(self, requests, pack, clinic_denial_rate=None):
        Counting.calls += 1
        return super().score(requests, pack, clinic_denial_rate)


def test_scores_every_open_and_board_reuses_it_until_the_chart_changes():
    case = CaseService().base_case("kowalchuk")
    live = LiveScorer(default_pack(), model=Counting())
    rd = live.score(case)
    assert rd.matching(case)["model"] == {"laya": "fake", "risk": "fake"}
    calls = Counting.calls
    assert live.latest(case) is rd and Counting.calls == calls  # board: same chart, no new run
    live.score(case)
    assert Counting.calls > calls  # case page: always runs
