#!/bin/bash
# Deploy the demo app to Vercel project `ophi-demo`. ophi.app/<slug> proxies to it (site/next.config.ts).
# Usage: scripts/demo-deploy.sh [--stage-only]   — stages only what the app reads at runtime, then deploys to production.
# The demo keeps its state in /tmp on the function, shared by every viewer. It resets whenever Vercel
# recycles the instance, and a second instance under load would not see the first one's sign-offs.
set -euo pipefail
cd "$(dirname "$0")/.."
SLUG="demo-4ajsmu"  # keep in step with DEMO_SLUG in site/next.config.ts
stage="outputs/ophi-demo"
origin="https://ophi-demo-nonitgs-projects.vercel.app"  # DEMO_ORIGIN in site/next.config.ts

mkdir -p "$stage"
rsync -a --delete --exclude .vercel --exclude __pycache__ --exclude "*.pyc" \
  --include "/ophi/***" --include "/packs/***" --include "/cases/***" \
  --include "/pyproject.toml" --include "/uv.lock" --exclude "*" ./ "$stage/"

echo "3.13" > "$stage/.python-version"  # the version the test suite runs on
cat > "$stage/index.py" <<PY
import os

os.environ.setdefault("OPHI_BASE_PATH", "/$SLUG")
os.environ.setdefault("OPHI_VAR_DIR", "/tmp/ophi")

from ophi.web.app import app  # noqa: E402,F401
PY

[ "${1:-}" = "--stage-only" ] && { echo "staged in $stage"; exit 0; }
[ -f "$stage/.vercel/project.json" ] || vercel link --yes --project ophi-demo --cwd "$stage"
# ophi.app proxies to the project's .vercel.app URL, which Vercel login would otherwise gate.
vercel project protection disable ophi-demo --sso
vercel deploy --prod --yes --cwd "$stage"
curl -fsS -o /dev/null "$origin/$SLUG" && echo "live: $origin/$SLUG (shared as https://www.ophi.app/$SLUG)"
