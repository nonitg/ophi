#!/bin/bash
# Score the recorded-PMS demo board (mocks/pms/snapshot.json) into cases/demo/laya/, so the deployed
# demo — which ships without torch — has a fix plan for the ABELDent patients, not just the fixtures.
set -euo pipefail
cd "$(dirname "$0")/.."
export USE_MOCK_PMS_API=true PYTHONPATH=.
unset USE_ABELDENT_PMS
.venv/bin/python scripts/laya-demo-predict.py "$@"
