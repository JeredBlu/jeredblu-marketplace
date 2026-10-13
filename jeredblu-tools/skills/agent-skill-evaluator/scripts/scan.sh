#!/usr/bin/env bash
# Compatibility entry point; only the bundled evaluator code executes.
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 -I "$HERE/scan.py" "$@"
