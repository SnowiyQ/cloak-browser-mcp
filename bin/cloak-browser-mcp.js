#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const { spawn, spawnSync } = require("child_process");

const root = path.resolve(__dirname, "..");

function venvPython() {
  return process.platform === "win32"
    ? path.join(root, ".venv", "Scripts", "python.exe")
    : path.join(root, ".venv", "bin", "python");
}

function checkPython(command, args = []) {
  const result = spawnSync(
    command,
    args.concat([
      "-c",
      "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)",
    ]),
    { stdio: "ignore" }
  );
  return result.status === 0;
}

function fallbackPython() {
  const candidates = process.platform === "win32"
    ? [["py", ["-3.12"]], ["py", ["-3.11"]], ["py", ["-3"]], ["python", []], ["python3", []]]
    : [["python3", []], ["python", []]];

  for (const [command, args] of candidates) {
    if (checkPython(command, args)) {
      return { command, args };
    }
  }

  throw new Error("Python 3.11+ is required. Re-run npm install after installing Python.");
}

let command = venvPython();
let args = [];
if (!fs.existsSync(command)) {
  const fallback = fallbackPython();
  command = fallback.command;
  args = fallback.args;
}

const localConfig = path.join(root, "config.yaml");
if (!process.env.CLOAK_BROWSER_CONFIG && fs.existsSync(localConfig)) {
  process.env.CLOAK_BROWSER_CONFIG = localConfig;
}

process.env.PYTHONUNBUFFERED = "1";
process.env.PYTHONPATH = [
  path.join(root, "src"),
  process.env.PYTHONPATH || "",
].filter(Boolean).join(path.delimiter);

const child = spawn(command, args.concat(["-m", "cloak_browser_mcp.server"]), {
  cwd: root,
  env: process.env,
  stdio: "inherit",
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 0);
});

child.on("error", (error) => {
  console.error(error.message);
  process.exit(1);
});
