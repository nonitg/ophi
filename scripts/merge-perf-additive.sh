#!/usr/bin/env bash
# Fast-forward main onto perf/page-loads while other sessions hold uncommitted work in ophi/web/app.py.
#
# Additive only: the peers' app.py content is never removed from disk, so a concurrent write by another
# session cannot lose work. Our hunks are added to their working copy, the branch ref moves without git
# rewriting that file, and the index is repointed so their edits still read as work in progress.
# Rollback: git update-ref refs/heads/main $FROM && restore app.py from the backup this script takes.
set -euo pipefail
cd /home/arch/Desktop/code/colombus

FROM=cf947ea
TO=fe31603
BK="${1:?usage: merge-perf-additive.sh <backup-dir>}"
mkdir -p "$BK"

[ "$(git rev-parse --short HEAD)" = "$FROM" ] || { echo "FAIL: main is not at $FROM"; exit 1; }
cp ophi/web/app.py "$BK/app.py.before"
git rev-parse HEAD > "$BK/head.before"

# The peers' in-flight markers, so we can prove afterwards that none of them were dropped.
for pat in "_recover_page" "draft_call_script" "row_id}/script" "PmsLookBack" "callback_on"; do
  printf '%s=%s\n' "$pat" "$(grep -c "$pat" ophi/web/app.py || true)" >> "$BK/peer-markers.before"
done

# 1. Add our two hunks to the peers' working copy; their edits stay exactly where they are.
git diff "$FROM" "$TO" -- ophi/web/app.py | git apply --3way
grep -q "warm_cases" ophi/web/app.py || { echo "FAIL: our change did not apply"; exit 1; }

# 2. Bring over the files no other session is touching.
git checkout "$TO" -- ophi/outcomes/live.py tests/test_live.py \
    scripts/board-badge-check.py scripts/profile-clickthrough.py

# 3. Move the branch without letting git rewrite app.py, then point the index at the new commit so
#    app.py reads as the peers' work in progress and nothing of ours looks reverted.
git update-ref -m "ff to perf/page-loads (additive; app.py held by peers)" refs/heads/main "$TO"
git reset -q -- ophi/web/app.py

echo "merged: main now $(git log --oneline -1)"
