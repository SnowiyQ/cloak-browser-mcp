#!/usr/bin/env python3
"""Register the cloak-browser MCP server in ~/.hermes/config.yaml.

This script is intentionally separate so config modification is explicit.
"""
from __future__ import annotations

from pathlib import Path

import yaml

HOME = Path.home()
CONFIG = HOME / ".hermes" / "config.yaml"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SERVER = {
    "command": str(PROJECT_ROOT / "run.sh"),
    "args": [],
    "timeout": 120,
    "connect_timeout": 30,
}


def main() -> None:
    if not CONFIG.exists():
        raise SystemExit(f"Config not found: {CONFIG}")
    data = yaml.safe_load(CONFIG.read_text()) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"Config is not a YAML mapping: {CONFIG}")
    servers = data.setdefault("mcp_servers", {})
    servers["cloak_browser"] = SERVER
    backup = CONFIG.with_suffix(".yaml.bak-cloak-browser")
    backup.write_text(CONFIG.read_text())
    CONFIG.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
    print(f"registered cloak_browser MCP in {CONFIG}")
    print(f"backup: {backup}")
    print("restart Hermes gateway/session for tools to appear")


if __name__ == "__main__":
    main()
