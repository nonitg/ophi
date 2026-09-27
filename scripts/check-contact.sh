#!/usr/bin/env bash
# Every PMS mode must give the desk a way to reach the patient: mock fixtures, demo YAML, recorded VM snapshot.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHONPATH=. .venv/bin/python - <<'PY'
from ophi.sources.pms_repository import MockPmsRepository, FileSystemPmsRepository

for name, repo in [("mock", MockPmsRepository()), ("demo yaml", FileSystemPmsRepository())]:
    for cid in repo.list_case_ids():
        try:
            p = repo.get_case(cid).patient
        except ValueError:  # a pid the mocks have no planned crown for
            continue
        print(f"{name:10} {cid:12} phone={p.phone or '-':16} email={p.email or '-'}")
PY
