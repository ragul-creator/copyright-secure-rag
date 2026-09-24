#!/usr/bin/env bash
set -euo pipefail
if ! command -v ort >/dev/null; then
  echo "ORT CLI is not installed. Run this inside the OSS Review Toolkit worker image." >&2
  exit 2
fi
ort analyze -i "${1:-.}" -o "${2:-ort-results}"
