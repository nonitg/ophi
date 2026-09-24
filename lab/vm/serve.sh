#!/bin/bash
# Serve the guest bootstrap script on the UTM host-only network so the Windows VM
# can pull it with one short command instead of the user typing a wall of PowerShell.
# Bound to 192.168.64.1 only — not reachable from the LAN.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SERVE_DIR="${TMPDIR:-/tmp}/ophi-serve"
mkdir -p "$SERVE_DIR"
cp "$HERE/bootstrap.ps1" "$SERVE_DIR/b.ps1"
cp "$HOME/.ssh/id_ed25519_abeldent.pub" "$SERVE_DIR/id.pub"
echo "serving $SERVE_DIR on http://192.168.64.1:8099"
echo "in the guest:  irm http://192.168.64.1:8099/b.ps1 | iex"
exec python3 -m http.server 8099 --bind 192.168.64.1 --directory "$SERVE_DIR"
