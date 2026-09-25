#!/bin/bash
# End-to-end check of the hosted demo path without deploying: the staged bundle served locally,
# proxied through the site's real rewrite, then the presenter click-through (scripts/app-flow.py).
# Usage: scripts/demo-proxy-check.sh [out_dir]
set -uo pipefail
cd "$(dirname "$0")/.."
APP_PORT=8766; SITE_PORT=3107
SLUG=$(sed -n 's/^SLUG="\([^"]*\)".*/\1/p' scripts/demo-deploy.sh)
state="${TMPDIR:-/tmp}/ophi-demo-check"; rm -rf "$state"
scripts/demo-deploy.sh --stage-only || exit 1

OPHI_VAR_DIR="$state" .venv/bin/python -m uvicorn index:app --app-dir outputs/ophi-demo --port $APP_PORT > "$state.app.log" 2>&1 &
app_pid=$!
(cd site && DEMO_ORIGIN="http://127.0.0.1:$APP_PORT" exec node_modules/.bin/next dev -p $SITE_PORT) > "$state.site.log" 2>&1 &
site_pid=$!
trap 'kill $app_pid $site_pid 2>/dev/null; pkill -f "next dev -p $SITE_PORT" 2>/dev/null' EXIT

for _ in $(seq 1 120); do
  [ "$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$SITE_PORT/$SLUG")" = "200" ] && break
  sleep 0.5
done
code() { curl -s -o /dev/null -w "%{http_code}" "$@"; }
echo "bare prefix:       $(code "http://127.0.0.1:$SITE_PORT/$SLUG")"
echo "trailing slash:    $(code "http://127.0.0.1:$SITE_PORT/$SLUG/")"
echo "case page:         $(code "http://127.0.0.1:$SITE_PORT/$SLUG/cases/singh")"
echo "stylesheet:        $(code "http://127.0.0.1:$SITE_PORT/$SLUG/static/app.css")"
echo "waitlist home:     $(code "http://127.0.0.1:$SITE_PORT/")"
echo "staged ophi from:  $(cd outputs/ophi-demo && ../../.venv/bin/python -c 'import ophi; print(ophi.__file__)')"
.venv/bin/python scripts/app-flow.py "http://127.0.0.1:$SITE_PORT/$SLUG" ${1:+"$1"}
