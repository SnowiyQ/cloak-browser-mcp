#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const { spawn, spawnSync } = require("child_process");

const root = path.resolve(__dirname, "..");
const venvDir = path.join(root, ".venv");

function venvPython() {
  return process.platform === "win32"
    ? path.join(venvDir, "Scripts", "python.exe")
    : path.join(venvDir, "bin", "python");
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

function findPython() {
  const candidates = [];
  if (process.env.CLOAK_BROWSER_PYTHON) {
    candidates.push([process.env.CLOAK_BROWSER_PYTHON, []]);
  }
  if (process.platform === "win32") {
    candidates.push(["py", ["-3.12"]], ["py", ["-3.11"]], ["py", ["-3"]], ["python", []], ["python3", []]);
  } else {
    candidates.push(["python3", []], ["python", []]);
  }

  for (const [command, args] of candidates) {
    if (checkPython(command, args)) {
      return { command, args };
    }
  }

  throw new Error("Python 3.11+ is required. Re-run npm install after installing Python.");
}

function runSetup(command, args) {
  const result = spawnSync(command, args, {
    cwd: root,
    encoding: "utf8",
    maxBuffer: 100 * 1024 * 1024,
  });
  if (result.stdout) {
    process.stderr.write(result.stdout);
  }
  if (result.stderr) {
    process.stderr.write(result.stderr);
  }
  if (result.error) {
    throw result.error;
  }
  if (result.status !== 0) {
    throw new Error(`${command} ${args.join(" ")} failed with exit code ${result.status}`);
  }
}

function hasRuntime(python) {
  const result = spawnSync(
    python,
    ["-c", "import cloak_browser_mcp, mcp, cloakbrowser, yaml"],
    { cwd: root, stdio: "ignore" }
  );
  return result.status === 0;
}

function ensureRuntime() {
  const python = venvPython();
  if (fs.existsSync(python) && hasRuntime(python)) {
    return python;
  }
  if (process.env.CLOAK_BROWSER_SKIP_PYTHON_INSTALL === "1") {
    throw new Error("Missing Python runtime and CLOAK_BROWSER_SKIP_PYTHON_INSTALL=1 is set.");
  }

  process.stderr.write("Setting up cloak-browser-mcp Python runtime...\n");
  const base = findPython();
  if (!fs.existsSync(python)) {
    runSetup(base.command, base.args.concat(["-m", "venv", venvDir]));
  }
  runSetup(python, ["-m", "pip", "install", "-e", root]);
  if (!hasRuntime(python)) {
    throw new Error("Python runtime setup completed, but required modules are still unavailable.");
  }
  return python;
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

let command;
try {
  command = ensureRuntime();
} catch (error) {
  console.error(error.message);
  process.exit(1);
}

const child = spawn(command, ["-m", "cloak_browser_mcp.server"], {
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
