#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");

const root = path.resolve(__dirname, "..");
const python = process.platform === "win32"
  ? path.join(root, ".venv", "Scripts", "python.exe")
  : path.join(root, ".venv", "bin", "python");

if (!fs.existsSync(python)) {
  console.error("Python virtual environment was not found. Run `npm install` first.");
  process.exit(1);
}

console.log("Installing stock Playwright Chromium for launch_backend='playwright'.");
console.log("The default CloakBrowser backend downloads its patched Chromium binary on first launch.");

const child = spawn(python, ["-m", "playwright", "install", "chromium"], {
  cwd: root,
  stdio: "inherit",
});

child.on("exit", (code) => process.exit(code ?? 0));
child.on("error", (error) => {
  console.error(error.message);
  process.exit(1);
});
