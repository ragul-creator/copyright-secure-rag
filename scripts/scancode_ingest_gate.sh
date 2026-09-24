#!/usr/bin/env bash
set -euo pipefail
if ! command -v scancode >/dev/null; then
  echo "ScanCode CLI is not installed. Install scancode-toolkit in the compliance worker image." >&2
  exit 2
fi
INPUT=${1:?usage: scancode_ingest_gate.sh <path> [output.json]}
OUTPUT=${2:-scancode.json}
scancode --license --copyright --info --json-pp "$OUTPUT" "$INPUT"
echo "Scan complete: $OUTPUT"
