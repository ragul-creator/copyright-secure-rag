#!/usr/bin/env bash
set -euo pipefail
if ! command -v cosign >/dev/null; then
  echo "cosign is not installed." >&2; exit 2
fi
cosign sign-blob --yes --bundle "${1}.sigstore.json" "$1"
