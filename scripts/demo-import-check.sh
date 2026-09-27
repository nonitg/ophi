#!/bin/bash
# Import the demo app in a fresh venv holding only the base dependencies, as the Vercel build does.
# Catches a runtime import that only resolves locally through the dev or ml extras.
# Usage: scripts/demo-import-check.sh   (run after scripts/demo-deploy.sh --stage-only)
set -euo pipefail
cd "$(dirname "$0")/.."
stage="outputs/ophi-demo"
venv="$(mktemp -d)/venv"
uv venv -q --python "$(cat "$stage/.python-version")" "$venv"
uv pip install -q --python "$venv/bin/python" -r pyproject.toml
cd "$stage" && "$venv/bin/python" -c "import index" && echo "demo app imports with base deps only"
