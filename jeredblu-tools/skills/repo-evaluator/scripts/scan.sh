#!/usr/bin/env bash
# Compatibility entrypoint. Inspects bytes, never executes target code.
set -euo pipefail
exec python3 -I "$(cd -- "$(dirname -- "$0")" && pwd)/scan.py" "$@"
