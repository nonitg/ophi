# Shared by the demo runners and the reset script: keys from .env, and where this mode keeps its state.
# Source it, don't run it. Set USE_ABELDENT_PMS=true first for the ABELDent mode's own state directory.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
set -a; [ -f "$ROOT/.env" ] && . "$ROOT/.env"; set +a
export OPHI_VAR_DIR="${OPHI_VAR_DIR:-$ROOT/var/${USE_ABELDENT_PMS:+abeldent}}"
