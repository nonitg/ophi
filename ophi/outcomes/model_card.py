"""What the app states about Laya and the risk model: what they learned from and how they scored on clinics they
never saw. Figures from the 2026-09-26 run (docs/outcomes-explainer.md §4-5); retraining updates both.
"""

TRAINED_ON = 600  # synthetic crown requests from 40 fictional clinics (fixtures/cdcp_crowns)
TEST_CLINICS, TEST_REQUESTS = 8, 142
# AUC on the held-out clinics: how often a denied request ranks riskier than an approved one.
AUC = [("The rules and chart values alone", 0.722), ("Adding Laya's reading of the note", 0.769)]
# Share of held-out requests denied at each level the page shows.
DENIED_BY_LEVEL = [("low", 14), ("medium", 62), ("high", 77)]
# Right on "extensively restored": fine-tuned, untrained, base-rate guess (%).
NOTE_ACCURACY = {"question": "extensively restored", "tuned": 94, "untrained": 62, "guess": 77}
# Trained but kept off screens: naming the reason behind a vague denial letter, right this often as a top guess (%).
VAGUE_REASON_TOP1 = 33
