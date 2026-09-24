#!/usr/bin/env bash
# One-off history rewrite: strip outputs/ (review screenshots) and AI co-author trailers
# from every branch, then force-push. Rewrites in a scratch mirror so the working tree is untouched.
set -eu
cd "$(dirname "$0")/.."
REPO="$PWD"
WORK="${1:?usage: purge-outputs-history.sh <scratch-dir>}"
REMOTE_URL="$(git remote get-url origin)"
REMOTE_BRANCHES="main assertions-ui-bug"

mkdir -p "$WORK"
echo "== backup bundle of every ref =="
git bundle create -q "$WORK/ophi-pre-purge.bundle" --all

# Local branch per remote branch so the mirror holds them as refs/heads.
git fetch -q origin
git branch -f assertions-ui-bug origin/assertions-ui-bug

echo "== rewrite in scratch mirror =="
rm -rf "$WORK/rewrite.git"
git clone -q --mirror --no-local "$REPO" "$WORK/rewrite.git"
cd "$WORK/rewrite.git"
git for-each-ref --format='%(refname)' | grep -vE '^refs/(heads|tags)/' | sed 's/^/delete /' | git update-ref --stdin
git filter-repo --force --invert-paths --path outputs/ --message-callback '
import re
message = re.sub(rb"(?im)^co-authored-by:.*(claude|anthropic|internal-model).*\n?", b"", message)
return message.rstrip(b"\n") + b"\n"
'

echo "== verify =="
if git rev-list --all --objects | grep -q ' outputs/'; then echo "outputs/ blobs remain, abort"; exit 1; fi
if git log --all --format=%B | grep -qiE 'co-authored-by:.*(claude|anthropic|internal-model)'; then echo "trailers remain, abort"; exit 1; fi
[ "$(git rev-list --count main)" = "$(git -C "$REPO" rev-list --count main)" ] || { echo "commit count changed, abort"; exit 1; }
git count-objects -vH | grep size-pack || true

echo "== force push (lease on current remote tips) =="
for b in $REMOTE_BRANCHES; do
  old="$(git -C "$REPO" rev-parse "origin/$b")"
  git push --force-with-lease="$b:$old" "$REMOTE_URL" "refs/heads/$b:refs/heads/$b"
done

echo "== adopt new history locally, keep working tree =="
cd "$REPO"
git fetch -q --update-head-ok "$WORK/rewrite.git" '+refs/heads/*:refs/heads/*'
git reset -q --mixed HEAD
git fetch -q --prune origin
git reflog expire --expire=now --all
git gc -q --prune=now
du -sh .git
git status -sb | head -1
