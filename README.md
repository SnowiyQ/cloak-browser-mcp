# Cloak Browser MCP Controller

Local MCP server that gives Hermes direct tools to control a Chromium-compatible browser over CDP.
It is designed for legitimate automation, QA, and sandbox testing.

It works with any browser that exposes a Chrome DevTools Protocol endpoint, including many
"Cloak/Cloaked/anti-detect" browsers, **without implementing stealth, evasion, spam, or account-abuse logic**.

## What Hermes gets

After wiring this MCP server into Hermes and restarting, tools appear with names like:

- `mcp_cloak_browser_browser_connect`
- `mcp_cloak_browser_browser_new_page`
- `mcp_cloak_browser_browser_goto`
- `mcp_cloak_browser_browser_click`
- `mcp_cloak_browser_browser_type`
- `mcp_cloak_browser_browser_press`
- `mcp_cloak_browser_browser_mouse_click`
- `mcp_cloak_browser_browser_text`
- `mcp_cloak_browser_browser_evaluate`
- `mcp_cloak_browser_browser_screenshot`
- `mcp_cloak_browser_browser_close`

## Setup

```bash
cd /mnt/e/personal_projects/__MCP__/cloak-browser-mcp
uv venv --seed
uv pip install --python .venv/bin/python -e .
playwright install chromium
```

For CDP mode, start your Cloak/Cloaked browser with a remote debugging port, or use its vendor-provided CDP URL.
Common Chromium example:

```bash
chromium --remote-debugging-port=9222 --user-data-dir=/tmp/cloak-browser-profile
```

Then:

```bash
cp config.example.yaml config.yaml
# edit cdp_url if the browser uses a different endpoint
./run.sh
```

## Hermes MCP config

Add this to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  cloak_browser:
    command: "/mnt/e/personal_projects/__MCP__/cloak-browser-mcp/run.sh"
    args: []
    timeout: 120
    connect_timeout: 30
```

Then restart Hermes gateway/session so MCP tools are discovered.

## Codex MCP config on Windows

Add this to `%USERPROFILE%\.codex\config.toml`:

```toml
[mcp_servers.cloak-browser-mcp]
command = "powershell.exe"
args = [
  "-NoProfile",
  "-ExecutionPolicy",
  "Bypass",
  "-File",
  "E:\\personal_projects\\__MCP__\\cloak-browser-mcp\\run.ps1",
]
```

Then restart Codex so MCP tools are discovered.

## Smoke test outside Hermes

```bash
cd /mnt/e/personal_projects/__MCP__/cloak-browser-mcp
PYTHONPATH=src .venv/bin/python -m cloak_browser_mcp.server
```

It waits on stdio because it is an MCP server. Use Hermes after configuring it.

## Safety boundary

This is a browser control bridge. It can navigate, click, type, screenshot, and run JavaScript on pages you are authorized to automate.
It should not be used for credential theft, spam, bypassing access controls, evading bot defenses, or abusing third-party services.
