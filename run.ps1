$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONUNBUFFERED = "1"

if (-not $env:CLOAK_BROWSER_CONFIG) {
    $env:CLOAK_BROWSER_CONFIG = Join-Path $Root "config.yaml"
}

$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path -LiteralPath $VenvPython) {
    & $VenvPython -m cloak_browser_mcp.server
    exit $LASTEXITCODE
}

$env:PYTHONPATH = Join-Path $Root "src"
& python -m cloak_browser_mcp.server
exit $LASTEXITCODE
