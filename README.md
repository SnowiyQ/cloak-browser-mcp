# Cloak Browser MCP

MCP server for controlling [CloakHQ/CloakBrowser](https://github.com/CloakHQ/CloakBrowser) or any Chromium-compatible browser exposed over Chrome DevTools Protocol (CDP).

The default launch backend uses CloakBrowser, a Playwright-compatible wrapper around a patched Chromium binary. CDP mode is still available for attaching to an already-running browser, including Chrome, Edge, Chromium, and browser profiles that provide a CDP URL.

The server is intended for legitimate automation, QA, debugging, and sandbox testing. It does not add credential theft, spam, scraping-at-scale, account-abuse, or access-control bypass workflows.

## Tools

MCP clients discover tools with names similar to:

- `browser_status`
- `browser_connect`
- `browser_new_page`
- `browser_goto`
- `browser_click`
- `browser_type`
- `browser_press`
- `browser_mouse_click`
- `browser_wait`
- `browser_text`
- `browser_evaluate`
- `browser_screenshot`
- `browser_close`

## Install From NPM

Requirements:

- Node.js 18+
- Python 3.11+

```bash
npm install -g cloak-browser-mcp
```

The npm postinstall creates a package-local Python virtual environment and installs the Python MCP runtime plus CloakBrowser. CloakBrowser downloads its patched Chromium binary on first launch.

If you want the stock Playwright fallback backend, install the bundled Chromium browser:

```bash
cloak-browser-mcp-install-browsers
```

Run the MCP server:

```bash
cloak-browser-mcp
```

## Install From Source

```bash
git clone https://github.com/SnowiyQ/cloak-browser-mcp.git
cd cloak-browser-mcp
uv venv --seed
uv pip install -e .
```

For the stock Playwright fallback backend:

```bash
.venv/bin/python -m playwright install chromium
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m playwright install chromium
```

## Browser Setup

For CDP mode, start your browser with a remote debugging port or use its vendor-provided CDP URL.

Common Chromium example:

```bash
chromium --remote-debugging-port=9222 --user-data-dir=/tmp/cloak-browser-profile
```

Windows Chrome example:

```powershell
Start-Process "$env:ProgramFiles\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9222", "--user-data-dir=$env:TEMP\cloak-browser-profile"
```

Copy the example config only when you need file-based settings:

```bash
cp config.example.yaml config.yaml
```

`config.yaml` is intentionally gitignored because it is local runtime configuration.

## Configuration

All YAML settings can be overridden with environment variables:

| YAML key | Environment variable | Default |
| --- | --- | --- |
| `cdp_url` | `CLOAK_BROWSER_CDP_URL` | `null` |
| `launch_when_no_cdp` | `CLOAK_BROWSER_LAUNCH` | `false` |
| `headless` | `CLOAK_BROWSER_HEADLESS` | `false` |
| `executable_path` | `CLOAK_BROWSER_EXECUTABLE` | `null` |
| `launch_backend` | `CLOAK_BROWSER_LAUNCH_BACKEND` | `cloakbrowser` |
| `cloak_stealth_args` | `CLOAK_BROWSER_STEALTH_ARGS` | `true` |
| `cloak_humanize` | `CLOAK_BROWSER_HUMANIZE` | `false` |
| `cloak_human_preset` | `CLOAK_BROWSER_HUMAN_PRESET` | `default` |
| `cloak_proxy` | `CLOAK_BROWSER_PROXY` | `null` |
| `cloak_timezone` | `CLOAK_BROWSER_TIMEZONE` | `null` |
| `cloak_locale` | `CLOAK_BROWSER_LOCALE` | `null` |
| `cloak_geoip` | `CLOAK_BROWSER_GEOIP` | `false` |
| `default_timeout_ms` | `CLOAK_BROWSER_TIMEOUT_MS` | `10000` |
| `screenshots_dir` | `CLOAK_BROWSER_SCREENSHOTS_DIR` | `~/.cloak-browser-mcp/screenshots` |

If `cdp_url` is configured, `browser_connect()` attaches to that endpoint. Passing `launch=true` to `browser_connect` launches the configured backend instead, unless a `cdp_url` argument is explicitly provided.

Set `launch_backend: "playwright"` only when you intentionally want stock Playwright Chromium instead of CloakBrowser.

## Codex Config

After a global npm install:

```toml
[mcp_servers.cloak-browser-mcp]
command = "cloak-browser-mcp"
args = []
```

For a local Windows checkout:

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

Restart Codex after changing MCP config.

## Hermes Config

```yaml
mcp_servers:
  cloak_browser:
    command: "/path/to/cloak-browser-mcp/run.sh"
    args: []
    timeout: 120
    connect_timeout: 30
```

Restart Hermes after changing MCP config.

## Smoke Tests

Python import/runtime smoke test:

```bash
npm run smoke
```

Package publish-set check:

```bash
npm pack --dry-run
```

Local browser smoke test from source:

```bash
python scripts/browser_smoke.py https://example.com --headless
```

## Safety Boundary

This is a browser control bridge. It can navigate, click, type, take screenshots, read visible text, and run JavaScript on pages you are authorized to automate.

Do not use it for credential theft, spam, phishing, bypassing access controls, evading bot defenses, or abusing third-party services.
