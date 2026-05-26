"use strict";

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const root = path.resolve(__dirname, "..");
const venvDir = path.join(root, ".venv");

function run(command, args) {
  const result = spawnSync(command, args, { cwd: root, stdio: "inherit" });
  if (result.error) {
    throw result.error;
  }
  if (result.status !== 0) {
    throw new Error(`${command} ${args.join(" ")} failed with exit code ${result.status}`);
  }
}

function checkPython(command, args = []) {
  const result = spawnSync(
    command,
    args.concat([
      "-c",
      "import sys; print(sys.executable); raise SystemExit(0 if sys.version_info >= (3, 11) else 1)",
    ]),
    { cwd: root, encoding: "utf8" }
  );
  if (result.status !== 0) {
    return null;
  }
  return { command, args, executable: result.stdout.trim().split(/\r?\n/).pop() };
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
    const found = checkPython(command, args);
    if (found) {
      return found;
    }
  }

  throw new Error("Python 3.11+ is required to install cloak-browser-mcp.");
}

function venvPython() {
  return process.platform === "win32"
    ? path.join(venvDir, "Scripts", "python.exe")
    : path.join(venvDir, "bin", "python");
}

if (process.env.CLOAK_BROWSER_SKIP_PYTHON_INSTALL === "1") {
  console.log("Skipping Python install because CLOAK_BROWSER_SKIP_PYTHON_INSTALL=1.");
  process.exit(0);
}

const python = findPython();
if (!fs.existsSync(venvPython())) {
  run(python.command, python.args.concat(["-m", "venv", venvDir]));
}

run(venvPython(), ["-m", "pip", "install", "-e", root]);
console.log("Installed cloak-browser-mcp Python runtime.");
console.log("cloak-browser-mcp launches CloakHQ/CloakBrowser only.");
