#!/usr/bin/env bash
# Supply-chain check before installing/upgrading the `laya` package or weights:
# the PyPI wheel must be attested by the same GitHub repo the HF model card links to.
# Usage: scripts/laya-provenance.sh [version]   (default: latest on PyPI)
set -euo pipefail

EXPECTED_REPO="NandhaKishorM/laya"          # GitHub repo linked from the HF model card
HF_REPO="convaiinnovations/laya"
work="$(mktemp -d)"; trap 'rm -rf "$work"' EXIT

version="${1:-$(curl -fsS https://pypi.org/pypi/laya/json | python3 -c 'import json,sys;print(json.load(sys.stdin)["info"]["version"])')}"
echo "laya version: $version"

curl -fsS "https://pypi.org/pypi/laya/$version/json" | python3 -c '
import json,sys; i=json.load(sys.stdin)["info"]
print("pypi author:", i["author"], "| license:", i["license"], "| urls:", i["project_urls"])'

# Publisher recorded by PyPI's Trusted Publishing (PEP 740 attestation).
whl="laya-$version-py3-none-any.whl"
publisher="$(curl -fsS "https://pypi.org/integrity/laya/$version/$whl/provenance" \
  | python3 -c 'import json,sys;print(json.load(sys.stdin)["attestation_bundles"][0]["publisher"]["repository"])')"
echo "attested publisher repo: $publisher"
[[ "$publisher" == "$EXPECTED_REPO" ]] || { echo "FAIL: publisher != $EXPECTED_REPO"; exit 1; }

# Verify the sigstore signature over the actual wheel bytes, not just the metadata.
uvx --quiet pypi-attestations verify pypi --repository "https://github.com/$EXPECTED_REPO" "pypi:$whl"

# The GitHub repo and the HF card must point at each other.
gh_home="$(curl -fsS "https://api.github.com/repos/$EXPECTED_REPO" | python3 -c 'import json,sys;print(json.load(sys.stdin)["homepage"])')"
echo "github homepage: $gh_home"
[[ "$gh_home" == *"$HF_REPO"* ]] || { echo "FAIL: GitHub homepage does not link $HF_REPO"; exit 1; }
curl -fsSL "https://huggingface.co/$HF_REPO/raw/main/README.md" -o "$work/card.md"
grep -q "github.com/$EXPECTED_REPO" "$work/card.md" || { echo "FAIL: HF card does not link $EXPECTED_REPO"; exit 1; }
echo "OK: PyPI laya $version <- github.com/$EXPECTED_REPO <-> hf.co/$HF_REPO"
