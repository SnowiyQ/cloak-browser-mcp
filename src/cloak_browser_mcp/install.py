from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

SERVER_NAME = "cloak-browser-mcp"

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent


def _bin_script() -> Path:
    return _PACKAGE_ROOT / "bin" / "cloak-browser-mcp.js"


def resolve_server_command() -> dict[str, Any]:
    """Absolute command + args that point at this package's bin script.

    Mirrors the jum install pattern: write an absolute entry path so the config
    does not depend on the user's PATH or shim shadowing.
    """
    bin_path = _bin_script()
    if bin_path.exists():
        return {"command": "node", "args": [str(bin_path)]}
    return {"command": "cloak-browser-mcp", "args": []}


SERVER_CONFIG = resolve_server_command()


def mcp_config_json() -> dict[str, Any]:
    return {"mcpServers": {SERVER_NAME: SERVER_CONFIG}}


def _toml_arg_list(args: list[str]) -> str:
    quoted = ", ".join(f'"{_escape_toml_string(a)}"' for a in args)
    return f"[{quoted}]"


def mcp_config_toml() -> str:
    cmd = _escape_toml_string(SERVER_CONFIG["command"])
    args = _toml_arg_list(SERVER_CONFIG.get("args", []))
    return f"""[mcp_servers.{SERVER_NAME}]
command = "{cmd}"
args = {args}
"""


def print_mcp_config(target: str | None = None) -> None:
    if target:
        client_name, _config_dir, config_file = _select_config_candidates([target])[0]
        if config_file.endswith(".toml"):
            print(mcp_config_toml())
            return

        config: dict[str, Any] = {}
        _json_server_container(client_name, config)[SERVER_NAME] = SERVER_CONFIG
        print(json.dumps(config, indent=2))
        return

    print("[MCP JSON CONFIGURATION]")
    print(json.dumps(mcp_config_json(), indent=2))
    print("\n[CODEX TOML CONFIGURATION]")
    print(mcp_config_toml())


def _home() -> str:
    return os.environ.get("HOME") or os.environ.get("USERPROFILE") or str(Path.home())


def _config_candidates() -> list[tuple[str, str, str]]:
    home = _home()
    appdata = os.environ.get("APPDATA", "")
    codex_dir = os.environ.get("CODEX_HOME") or os.path.join(home, ".codex")
    common = [
        ("Cursor", os.path.join(home, ".cursor"), "mcp.json"),
        ("Claude Code", home, ".claude.json"),
        ("LM Studio", os.path.join(home, ".lmstudio"), "mcp.json"),
        ("Codex", codex_dir, "config.toml"),
        ("Gemini CLI", os.path.join(home, ".gemini"), "settings.json"),
        ("Qwen Coder", os.path.join(home, ".qwen"), "settings.json"),
        ("Copilot CLI", os.path.join(home, ".copilot"), "mcp-config.json"),
        ("Crush", home, "crush.json"),
        ("Warp", os.path.join(home, ".warp"), "mcp_config.json"),
        ("Amazon Q", os.path.join(home, ".aws", "amazonq"), "mcp_config.json"),
        ("Opencode", os.path.join(home, ".opencode"), "mcp_config.json"),
        ("Kiro", os.path.join(home, ".kiro"), "mcp_config.json"),
        ("Trae", os.path.join(home, ".trae"), "mcp_config.json"),
    ]

    if sys.platform == "win32":
        return common + [
            ("Cline", os.path.join(appdata, "Code", "User", "globalStorage", "saoudrizwan.claude-dev", "settings"), "cline_mcp_settings.json"),
            ("Roo Code", os.path.join(appdata, "Code", "User", "globalStorage", "rooveterinaryinc.roo-cline", "settings"), "mcp_settings.json"),
            ("Kilo Code", os.path.join(appdata, "Code", "User", "globalStorage", "kilocode.kilo-code", "settings"), "mcp_settings.json"),
            ("Claude", os.path.join(appdata, "Claude"), "claude_desktop_config.json"),
            ("Windsurf", os.path.join(home, ".codeium", "windsurf"), "mcp_config.json"),
            ("Zed", os.path.join(appdata, "Zed"), "settings.json"),
            ("Augment Code", os.path.join(appdata, "Code", "User"), "settings.json"),
            ("Qodo Gen", os.path.join(appdata, "Code", "User"), "settings.json"),
            ("Antigravity IDE", os.path.join(home, ".gemini", "antigravity"), "mcp_config.json"),
            ("VS Code", os.path.join(appdata, "Code", "User"), "settings.json"),
        ]

    if sys.platform == "darwin":
        return common + [
            ("Cline", os.path.join(home, "Library", "Application Support", "Code", "User", "globalStorage", "saoudrizwan.claude-dev", "settings"), "cline_mcp_settings.json"),
            ("Roo Code", os.path.join(home, "Library", "Application Support", "Code", "User", "globalStorage", "rooveterinaryinc.roo-cline", "settings"), "mcp_settings.json"),
            ("Kilo Code", os.path.join(home, "Library", "Application Support", "Code", "User", "globalStorage", "kilocode.kilo-code", "settings"), "mcp_settings.json"),
            ("Claude", os.path.join(home, "Library", "Application Support", "Claude"), "claude_desktop_config.json"),
            ("Windsurf", os.path.join(home, ".codeium", "windsurf"), "mcp_config.json"),
            ("Antigravity IDE", os.path.join(home, ".gemini", "antigravity"), "mcp_config.json"),
            ("Zed", os.path.join(home, "Library", "Application Support", "Zed"), "settings.json"),
            ("Augment Code", os.path.join(home, "Library", "Application Support", "Code", "User"), "settings.json"),
            ("Qodo Gen", os.path.join(home, "Library", "Application Support", "Code", "User"), "settings.json"),
            ("BoltAI", os.path.join(home, "Library", "Application Support", "BoltAI"), "config.json"),
            ("Perplexity", os.path.join(home, "Library", "Application Support", "Perplexity"), "mcp_config.json"),
            ("VS Code", os.path.join(home, "Library", "Application Support", "Code", "User"), "settings.json"),
        ]

    if sys.platform == "linux":
        return common + [
            ("Cline", os.path.join(home, ".config", "Code", "User", "globalStorage", "saoudrizwan.claude-dev", "settings"), "cline_mcp_settings.json"),
            ("Roo Code", os.path.join(home, ".config", "Code", "User", "globalStorage", "rooveterinaryinc.roo-cline", "settings"), "mcp_settings.json"),
            ("Kilo Code", os.path.join(home, ".config", "Code", "User", "globalStorage", "kilocode.kilo-code", "settings"), "mcp_settings.json"),
            ("Windsurf", os.path.join(home, ".codeium", "windsurf"), "mcp_config.json"),
            ("Antigravity IDE", os.path.join(home, ".gemini", "antigravity"), "mcp_config.json"),
            ("Zed", os.path.join(home, ".config", "zed"), "settings.json"),
            ("Augment Code", os.path.join(home, ".config", "Code", "User"), "settings.json"),
            ("Qodo Gen", os.path.join(home, ".config", "Code", "User"), "settings.json"),
            ("VS Code", os.path.join(home, ".config", "Code", "User"), "settings.json"),
        ]

    return common


def _target_id(client_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", client_name.lower()).strip("-")


def _normalize_target(value: str) -> str:
    normalized = value.strip().lower().replace("_", "-")
    normalized = re.sub(r"[^a-z0-9-]+", "-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    aliases = {
        "claude-code": "claude-code",
        "claudecode": "claude-code",
        "codex-cli": "codex",
        "claude-desktop": "claude",
        "claude-app": "claude",
        "vscode": "vs-code",
        "code": "vs-code",
    }
    return aliases.get(normalized, normalized)


def _select_config_candidates(targets: list[str] | None = None) -> list[tuple[str, str, str]]:
    candidates = _config_candidates()
    if not targets:
        return candidates

    wanted = [_normalize_target(target) for target in targets]
    if "all" in wanted:
        return candidates

    selected: list[tuple[str, str, str]] = []
    for target in wanted:
        match = next((candidate for candidate in candidates if _target_id(candidate[0]) == target), None)
        if not match:
            available = ", ".join(_target_id(candidate[0]) for candidate in candidates)
            raise ValueError(f"unknown MCP target '{target}'. Available targets: {available}")
        if match not in selected:
            selected.append(match)
    return selected


def list_mcp_targets() -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    for client_name, config_dir, config_file in _config_candidates():
        config_path = os.path.join(config_dir, config_file)
        targets.append(
            {
                "id": _target_id(client_name),
                "name": client_name,
                "config": config_path,
                "exists": os.path.exists(config_path),
            }
        )
    return targets


def print_mcp_targets() -> None:
    for target in list_mcp_targets():
        exists = "exists" if target["exists"] else "missing"
        print(f"{target['id']:<20} {target['name']} ({exists})")
        print(f"  {target['config']}")


def _json_server_container(client_name: str, config: dict[str, Any]) -> dict[str, Any]:
    special = {
        "VS Code": ("mcp", "servers"),
        "Visual Studio 2022": (None, "servers"),
    }
    shape = special.get(client_name)
    if shape:
        top_key, nested_key = shape
        if top_key is None:
            return config.setdefault(nested_key, {})
        return config.setdefault(top_key, {}).setdefault(nested_key, {})
    return config.setdefault("mcpServers", {})


def _read_json_config(config_path: str) -> dict[str, Any]:
    if not os.path.exists(config_path):
        return {}
    raw = Path(config_path).read_text(encoding="utf-8-sig").strip()
    return json.loads(raw) if raw else {}


def _write_atomic(file_path: str, data: str) -> None:
    directory = os.path.dirname(file_path)
    fd, temp_path = tempfile.mkstemp(dir=directory, prefix=".tmp_", suffix=Path(file_path).suffix, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(data)
        os.replace(temp_path, file_path)
    except Exception:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def _escape_toml_string(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def _update_codex_toml(config_path: str, *, uninstall: bool) -> None:
    raw = Path(config_path).read_text(encoding="utf-8") if os.path.exists(config_path) else ""
    block_pattern = re.compile(rf"(?:^|\n)\[mcp_servers\.{re.escape(SERVER_NAME)}\][\s\S]*?(?=\n\[[^\n]+\]|\Z)")
    raw = block_pattern.sub("", raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw).rstrip()
    if not uninstall:
        cmd = _escape_toml_string(SERVER_CONFIG["command"])
        args = _toml_arg_list(SERVER_CONFIG.get("args", []))
        block = f'[mcp_servers.{SERVER_NAME}]\ncommand = "{cmd}"\nargs = {args}\n'
        raw = f"{raw}\n\n{block}" if raw else block
    _write_atomic(config_path, f"{raw.rstrip()}\n")


def install_mcp_servers(*, uninstall: bool = False, quiet: bool = False, targets: list[str] | None = None) -> None:
    installed = 0
    explicit_targets = bool(targets) and "all" not in [_normalize_target(target) for target in targets]
    for client_name, config_dir, config_file in _select_config_candidates(targets):
        config_path = os.path.join(config_dir, config_file)
        if not os.path.exists(config_dir):
            if explicit_targets:
                os.makedirs(config_dir, exist_ok=True)
            else:
                if not quiet:
                    action = "uninstall" if uninstall else "installation"
                    print(f"Skipping {client_name} {action}\n  Config: {config_path} (not found)")
                continue

        try:
            if config_file.endswith(".toml"):
                _update_codex_toml(config_path, uninstall=uninstall)
            else:
                config = _read_json_config(config_path)
                servers = _json_server_container(client_name, config)
                if uninstall:
                    if SERVER_NAME not in servers:
                        if not quiet:
                            print(f"Skipping {client_name} uninstall\n  Config: {config_path} (not installed)")
                        continue
                    del servers[SERVER_NAME]
                else:
                    servers[SERVER_NAME] = SERVER_CONFIG
                _write_atomic(config_path, f"{json.dumps(config, indent=2)}\n")
        except Exception as exc:
            if not quiet:
                action = "uninstall" if uninstall else "installation"
                print(f"Skipping {client_name} {action}\n  Config: {config_path} ({exc})")
            continue

        if not quiet:
            action = "Uninstalled" if uninstall else "Installed"
            print(f"{action} {client_name} MCP server (restart required)\n  Config: {config_path}")
        installed += 1

    if not uninstall and installed == 0:
        print("No MCP servers installed. For unsupported MCP clients, use the following config:\n")
        print_mcp_config()
