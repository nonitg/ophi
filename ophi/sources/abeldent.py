"""Moved to the shared `abeldent` package (abeldent/reads.py), which ophi-phone reads ABELDent through too.

Aliased rather than re-exported, so `ophi.sources.abeldent.X` -- imports and monkeypatches alike -- is the
one module's X.
"""

import sys

from abeldent import reads

sys.modules[__name__] = reads
