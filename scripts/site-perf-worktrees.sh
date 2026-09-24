#!/usr/bin/env bash
# Two isolated copies of site/ for performance work: "base" (HEAD, untouched) and "perf" (edits), each with its own
# cloned node_modules so builds never touch site/.next that peer sessions' dev servers use.
set -euo pipefail
ROOT=$(git -C "$(dirname "$0")/.." rev-parse --show-toplevel)
OUT=${1:?usage: site-perf-worktrees.sh <dir>}
for name in base perf; do
  dir="$OUT/$name"
  if [ ! -d "$dir" ]; then
    git -C "$ROOT" worktree add --detach "$dir" HEAD >/dev/null
    cp -Rc "$ROOT/site/node_modules" "$dir/site/node_modules"
  fi
  echo "$dir/site"
done
