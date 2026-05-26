#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONUNBUFFERED=1
export CLOAK_BROWSER_CONFIG="${CLOAK_BROWSER_CONFIG:-$PWD/config.yaml}"
if [ -x "$PWD/.venv/bin/python" ]; then
  exec "$PWD/.venv/bin/python" -m cloak_browser_mcp.server
fi
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m cloak_browser_mcp.server
