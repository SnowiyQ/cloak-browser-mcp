# Cloak Browser MCP

MCP server for controlling [CloakHQ/CloakBrowser](https://github.com/CloakHQ/CloakBrowser).

This MCP launches CloakBrowser directly. It does not provide a stock Chromium fallback and does not attach to arbitrary Chrome/Chromium instances over CDP.

CloakBrowser itself is a Playwright-compatible package, so its own dependency tree may install Playwright internally. This project does not use Playwright as a fallback browser backend.

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
npm install -g @lumio_sn/cloak-browser-mcp
```

The npm postinstall creates a package-local Python virtual environment and installs the Python MCP runtime plus CloakBrowser. CloakBrowser downloads its patched Chromium binary on first launch.

If your package manager skips npm lifecycle scripts, the `cloak-browser-mcp` command bootstraps the same package-local Python runtime on first run.

Install it into supported MCP clients:

```bash
cloak-browser-mcp --install
```

Restart your MCP client after installation.

The server command is still available for clients that run MCP servers directly: `cloak-browser-mcp`.

## Install From Source

```bash
git clone https://github.com/SnowiyQ/cloak-browser-mcp.git
cd cloak-browser-mcp
uv venv --seed
uv pip install -e .
```

Copy the example config only when you need file-based settings:

```bash
cp config.example.yaml config.yaml
```

`config.yaml` is intentionally gitignored because it is local runtime configuration.

From a source checkout, the same helper flags are available through the run scripts:

```bash
./run.sh --install
```

```powershell
.\run.ps1 --install
```

## Configuration

All YAML settings can be overridden with environment variables:

| YAML key | Environment variable | Default |
| --- | --- | --- |
| `headless` | `CLOAK_BROWSER_HEADLESS` | `false` |
| `cloak_stealth_args` | `CLOAK_BROWSER_STEALTH_ARGS` | `true` |
| `cloak_humanize` | `CLOAK_BROWSER_HUMANIZE` | `false` |
| `cloak_human_preset` | `CLOAK_BROWSER_HUMAN_PRESET` | `default` |
| `cloak_proxy` | `CLOAK_BROWSER_PROXY` | `null` |
| `cloak_timezone` | `CLOAK_BROWSER_TIMEZONE` | `null` |
| `cloak_locale` | `CLOAK_BROWSER_LOCALE` | `null` |
| `cloak_geoip` | `CLOAK_BROWSER_GEOIP` | `false` |
| `default_timeout_ms` | `CLOAK_BROWSER_TIMEOUT_MS` | `10000` |
| `screenshots_dir` | `CLOAK_BROWSER_SCREENSHOTS_DIR` | `~/.cloak-browser-mcp/screenshots` |

`browser_connect()` launches CloakBrowser. `browser_new_page()`, `browser_goto()`, and the other browser tools launch CloakBrowser automatically if no browser is connected.

## MCP Client Config

The install helper follows the same shape as `ida-pro-mcp --install`:

```bash
cloak-browser-mcp --install
cloak-browser-mcp --uninstall
cloak-browser-mcp --config
```

`--install` writes config for supported clients whose config directories already exist, or whose config is normally stored directly under your home directory. Supported clients include Codex, Claude Desktop, Claude Code, Cursor, Cline, Roo Code, Kilo Code, VS Code, Windsurf, LM Studio, Gemini CLI, Qwen Coder, Copilot CLI, Opencode, Warp, Amazon Q, Kiro, Trae, Zed, and related MCP-compatible clients.

For unsupported clients, use the config printed by:

```bash
cloak-browser-mcp --config
```

Codex example:

```toml
[mcp_servers.cloak-browser-mcp]
command = "cloak-browser-mcp"
args = []
```

Local Windows checkout example:

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
