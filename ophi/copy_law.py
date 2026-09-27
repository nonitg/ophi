"""Ophi's copy law: the words Ophi never says about payer behaviour, in one place.

Every screen, packet and drafted call script is about documentation completeness against a cited rule --
never about what Sun Life will do (`PLAN.md`, "The copy law"). Sun Life's own words and chart quotes are
exempt: they are attributed to their source, not spoken in Ophi's voice.

Lives here rather than in a test so the verifiers can enforce the same rule the test asserts. One rulebook.
"""

from __future__ import annotations

import re

FORBIDDEN = re.compile(r"\b(will be approved|approved|eligible|covered|likely|probability)\b", re.I)

# Only a spoken script needs these: nobody writes "guarantee" on a screen, but it is the first word that
# arrives when a model is asked to be reassuring on the phone.
SPOKEN_EXTRA = re.compile(r"\b(approval|coverage|guarantee\w*)\b", re.I)
