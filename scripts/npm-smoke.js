"use strict";

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const root = path.resolve(__dirname, "..");
const python = process.platform === "win32"
  ? path.join(root, ".venv", "Scripts", "python.exe")
  : path.join(root, ".venv", "bin", "python");

if (!fs.existsSync(python)) {
  console.error("Missing .venv Python runtime. Run `npm install` first.");
  process.exit(1);
}

const code = [
  "import mcp, yaml",
  "import cloakbrowser",
  "from cloak_browser_mcp.config import BrowserConfig",
  "from cloak_browser_mcp.controller import BrowserController",
  "cfg = BrowserConfig.load()",
  "BrowserController(cfg)",
  "print('smoke ok')",
].join("; ");

const result = spawnSync(python, ["-c", code], {
  cwd: root,
  stdio: "inherit",
});

process.exit(result.status ?? 1);
