#!/bin/bash
# Deploy the demo app to Vercel project `ophi-demo`. ophi.app/<slug> proxies to it (site/next.config.ts).
# Usage: scripts/demo-deploy.sh [--stage-only] [--skip-pms-check]
#   --stage-only      stage what the app reads at runtime, don't deploy.
#   --skip-pms-check  deploy whatever snapshot is on disk, without checking it against the VM.
# Stages only what the app reads at runtime, then deploys to production.
# The demo keeps its state in /tmp on the function, shared by every viewer. It resets whenever Vercel
# recycles the instance, and a second instance under load would not see the first one's sign-offs.
set -euo pipefail
cd "$(dirname "$0")/.."
stage_only="" skip_pms_check=""
for arg in "$@"; do
  case "$arg" in
    --stage-only) stage_only=1 ;;
    --skip-pms-check) skip_pms_check=1 ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

SLUG="demo-4ajsmu"  # keep in step with DEMO_SLUG in site/next.config.ts
stage="outputs/ophi-demo"
origin="https://ophi-demo-nonitgs-projects.vercel.app"  # DEMO_ORIGIN in site/next.config.ts

# The demo board is mocks/pms/snapshot.json replayed. It goes stale silently whenever the lab VM is
# reseeded, so check it against the VM before shipping and re-record if the two have diverged.
if [ -z "$skip_pms_check" ]; then
  if ! ./lab/vm/vm status >/dev/null 2>&1; then
    echo "warning: lab VM unreachable — deploying mocks/pms/snapshot.json unverified" >&2
  else
    export USE_ABELDENT_PMS=true PYTHONPATH=.
    if .venv/bin/python scripts/recorded-pms-check.py >/dev/null 2>&1; then
      echo "PMS snapshot matches the VM"
    else
      echo "PMS snapshot is stale — re-recording from the VM"
      .venv/bin/python scripts/record-pms-snapshot.py
      .venv/bin/python scripts/recorded-pms-check.py \
        || { echo "error: snapshot still disagrees with the VM after re-recording" >&2; exit 1; }
    fi
    unset USE_ABELDENT_PMS
  fi
fi

mkdir -p "$stage"
rsync -a --delete --exclude .vercel --exclude __pycache__ --exclude "*.pyc" \
  --include "/ophi/***" --include "/packs/***" --include "/cases/***" --include "/mocks/***" \
  --include "/pyproject.toml" --include "/uv.lock" --exclude "*" ./ "$stage/"

echo "3.13" > "$stage/.python-version"  # the version the test suite runs on
cat > "$stage/index.py" <<PY
import os

os.environ.setdefault("OPHI_BASE_PATH", "/$SLUG")
os.environ.setdefault("OPHI_VAR_DIR", "/tmp/ophi")
os.environ.setdefault("USE_MOCK_PMS_API", "true")  # the clinic's own PMS, recorded: the same board without the VM

from ophi.web.app import app  # noqa: E402,F401
PY

[ -n "$stage_only" ] && { echo "staged in $stage"; exit 0; }
[ -f "$stage/.vercel/project.json" ] || vercel link --yes --project ophi-demo --cwd "$stage"
# ophi.app proxies to the project's .vercel.app URL, which Vercel login would otherwise gate.
vercel project protection disable ophi-demo --sso
vercel deploy --prod --yes --cwd "$stage"
curl -fsS -o /dev/null "$origin/$SLUG" && echo "live: $origin/$SLUG (shared as https://www.ophi.app/$SLUG)"
