#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const { spawn, spawnSync } = require("child_process");

const root = path.resolve(__dirname, "..");
const venvDir = path.join(root, ".venv");
const SERVER_NAME = "cloak-browser-mcp";
const SERVER_CONFIG = { command: "cloak-browser-mcp", args: [] };

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

function usage() {
  console.log(`usage: cloak-browser-mcp [--install] [--uninstall] [--config] [--help]

Cloak Browser MCP Server

options:
  --install       Install the MCP server into supported client configs
  --uninstall     Remove the MCP server from supported client configs
  --config        Print MCP config snippets
  --help          Show this help message
`);
}

function mcpConfigJson() {
  return { mcpServers: { [SERVER_NAME]: SERVER_CONFIG } };
}

function mcpConfigToml() {
  return `[mcp_servers.${SERVER_NAME}]
command = "cloak-browser-mcp"
args = []
`;
}

function printMcpConfig() {
  console.log("[MCP JSON CONFIGURATION]");
  console.log(JSON.stringify(mcpConfigJson(), null, 2));
  console.log("\n[CODEX TOML CONFIGURATION]");
  console.log(mcpConfigToml());
}

function configCandidates() {
  const home = osHome();
  const appData = process.env.APPDATA || "";
  const platform = process.platform;
  const codexDir = process.env.CODEX_HOME || path.join(home, ".codex");

  const common = [
    ["Cursor", path.join(home, ".cursor"), "mcp.json"],
    ["Claude Code", home, ".claude.json"],
    ["LM Studio", path.join(home, ".lmstudio"), "mcp.json"],
    ["Codex", codexDir, "config.toml"],
    ["Gemini CLI", path.join(home, ".gemini"), "settings.json"],
    ["Qwen Coder", path.join(home, ".qwen"), "settings.json"],
    ["Copilot CLI", path.join(home, ".copilot"), "mcp-config.json"],
    ["Crush", home, "crush.json"],
    ["Warp", path.join(home, ".warp"), "mcp_config.json"],
    ["Amazon Q", path.join(home, ".aws", "amazonq"), "mcp_config.json"],
    ["Opencode", path.join(home, ".opencode"), "mcp_config.json"],
    ["Kiro", path.join(home, ".kiro"), "mcp_config.json"],
    ["Trae", path.join(home, ".trae"), "mcp_config.json"],
  ];

  if (platform === "win32") {
    return common.concat([
      ["Cline", path.join(appData, "Code", "User", "globalStorage", "saoudrizwan.claude-dev", "settings"), "cline_mcp_settings.json"],
      ["Roo Code", path.join(appData, "Code", "User", "globalStorage", "rooveterinaryinc.roo-cline", "settings"), "mcp_settings.json"],
      ["Kilo Code", path.join(appData, "Code", "User", "globalStorage", "kilocode.kilo-code", "settings"), "mcp_settings.json"],
      ["Claude", path.join(appData, "Claude"), "claude_desktop_config.json"],
      ["Windsurf", path.join(home, ".codeium", "windsurf"), "mcp_config.json"],
      ["Zed", path.join(appData, "Zed"), "settings.json"],
      ["Augment Code", path.join(appData, "Code", "User"), "settings.json"],
      ["Qodo Gen", path.join(appData, "Code", "User"), "settings.json"],
      ["Antigravity IDE", path.join(home, ".gemini", "antigravity"), "mcp_config.json"],
      ["VS Code", path.join(appData, "Code", "User"), "settings.json"],
    ]);
  }

  if (platform === "darwin") {
    return common.concat([
      ["Cline", path.join(home, "Library", "Application Support", "Code", "User", "globalStorage", "saoudrizwan.claude-dev", "settings"), "cline_mcp_settings.json"],
      ["Roo Code", path.join(home, "Library", "Application Support", "Code", "User", "globalStorage", "rooveterinaryinc.roo-cline", "settings"), "mcp_settings.json"],
      ["Kilo Code", path.join(home, "Library", "Application Support", "Code", "User", "globalStorage", "kilocode.kilo-code", "settings"), "mcp_settings.json"],
      ["Claude", path.join(home, "Library", "Application Support", "Claude"), "claude_desktop_config.json"],
      ["Windsurf", path.join(home, ".codeium", "windsurf"), "mcp_config.json"],
      ["Antigravity IDE", path.join(home, ".gemini", "antigravity"), "mcp_config.json"],
      ["Zed", path.join(home, "Library", "Application Support", "Zed"), "settings.json"],
      ["Augment Code", path.join(home, "Library", "Application Support", "Code", "User"), "settings.json"],
      ["Qodo Gen", path.join(home, "Library", "Application Support", "Code", "User"), "settings.json"],
      ["BoltAI", path.join(home, "Library", "Application Support", "BoltAI"), "config.json"],
      ["Perplexity", path.join(home, "Library", "Application Support", "Perplexity"), "mcp_config.json"],
      ["VS Code", path.join(home, "Library", "Application Support", "Code", "User"), "settings.json"],
    ]);
  }

  if (platform === "linux") {
    return common.concat([
      ["Cline", path.join(home, ".config", "Code", "User", "globalStorage", "saoudrizwan.claude-dev", "settings"), "cline_mcp_settings.json"],
      ["Roo Code", path.join(home, ".config", "Code", "User", "globalStorage", "rooveterinaryinc.roo-cline", "settings"), "mcp_settings.json"],
      ["Kilo Code", path.join(home, ".config", "Code", "User", "globalStorage", "kilocode.kilo-code", "settings"), "mcp_settings.json"],
      ["Windsurf", path.join(home, ".codeium", "windsurf"), "mcp_config.json"],
      ["Antigravity IDE", path.join(home, ".gemini", "antigravity"), "mcp_config.json"],
      ["Zed", path.join(home, ".config", "zed"), "settings.json"],
      ["Augment Code", path.join(home, ".config", "Code", "User"), "settings.json"],
      ["Qodo Gen", path.join(home, ".config", "Code", "User"), "settings.json"],
      ["VS Code", path.join(home, ".config", "Code", "User"), "settings.json"],
    ]);
  }

  return common;
}

function osHome() {
  return process.env.HOME || process.env.USERPROFILE || "";
}

function jsonServerContainer(clientName, config) {
  const special = {
    "VS Code": ["mcp", "servers"],
    "Visual Studio 2022": [null, "servers"],
  };
  const shape = special[clientName];
  if (shape) {
    const [topKey, nestedKey] = shape;
    if (topKey === null) {
      config[nestedKey] = config[nestedKey] || {};
      return config[nestedKey];
    }
    config[topKey] = config[topKey] || {};
    config[topKey][nestedKey] = config[topKey][nestedKey] || {};
    return config[topKey][nestedKey];
  }
  config.mcpServers = config.mcpServers || {};
  return config.mcpServers;
}

function readJsonConfig(configPath) {
  if (!fs.existsSync(configPath)) {
    return {};
  }
  const raw = fs.readFileSync(configPath, "utf8").trim();
  return raw ? JSON.parse(raw) : {};
}

function writeAtomic(filePath, data) {
  const dir = path.dirname(filePath);
  const temp = path.join(dir, `.tmp_${process.pid}_${Date.now()}${path.extname(filePath)}`);
  fs.writeFileSync(temp, data);
  fs.renameSync(temp, filePath);
}

function escapeTomlString(value) {
  return String(value).replace(/\\/g, "\\\\").replace(/"/g, '\\"');
}

function updateCodexToml(configPath, uninstall) {
  const header = `[mcp_servers.${SERVER_NAME}]`;
  const blockPattern = new RegExp(`(?:^|\\n)\\[mcp_servers\\.${SERVER_NAME.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\][\\s\\S]*?(?=\\n\\[[^\\n]+\\]|$)`);
  let raw = fs.existsSync(configPath) ? fs.readFileSync(configPath, "utf8") : "";
  raw = raw.replace(blockPattern, "").replace(/\n{3,}/g, "\n\n").trimEnd();
  if (!uninstall) {
    const block = `${header}\ncommand = "${escapeTomlString(SERVER_CONFIG.command)}"\nargs = []\n`;
    raw = raw ? `${raw}\n\n${block}` : block;
  }
  writeAtomic(configPath, `${raw.trimEnd()}\n`);
}

function installMcpServers({ uninstall = false, quiet = false } = {}) {
  let installed = 0;
  for (const [clientName, configDir, configFile] of configCandidates()) {
    const configPath = path.join(configDir, configFile);
    if (!fs.existsSync(configDir)) {
      if (!quiet) {
        const action = uninstall ? "uninstall" : "installation";
        console.log(`Skipping ${clientName} ${action}\n  Config: ${configPath} (not found)`);
      }
      continue;
    }

    try {
      if (configFile.endsWith(".toml")) {
        updateCodexToml(configPath, uninstall);
      } else {
        const config = readJsonConfig(configPath);
        const servers = jsonServerContainer(clientName, config);
        if (uninstall) {
          if (!Object.prototype.hasOwnProperty.call(servers, SERVER_NAME)) {
            if (!quiet) {
              console.log(`Skipping ${clientName} uninstall\n  Config: ${configPath} (not installed)`);
            }
            continue;
          }
          delete servers[SERVER_NAME];
        } else {
          servers[SERVER_NAME] = SERVER_CONFIG;
        }
        writeAtomic(configPath, `${JSON.stringify(config, null, 2)}\n`);
      }
    } catch (error) {
      if (!quiet) {
        const action = uninstall ? "uninstall" : "installation";
        console.log(`Skipping ${clientName} ${action}\n  Config: ${configPath} (${error.message})`);
      }
      continue;
    }

    if (!quiet) {
      const action = uninstall ? "Uninstalled" : "Installed";
      console.log(`${action} ${clientName} MCP server (restart required)\n  Config: ${configPath}`);
    }
    installed += 1;
  }

  if (!uninstall && installed === 0) {
    console.log("No MCP servers installed. For unsupported MCP clients, use the following config:\n");
    printMcpConfig();
  }
}

function handleCli(args) {
  if (args.includes("--help") || args.includes("-h")) {
    usage();
    return true;
  }
  if (args.includes("--install") && args.includes("--uninstall")) {
    console.error("Cannot install and uninstall at the same time");
    process.exit(1);
  }
  if (args.includes("--config")) {
    printMcpConfig();
    return true;
  }
  if (args.includes("--install")) {
    installMcpServers();
    return true;
  }
  if (args.includes("--uninstall")) {
    installMcpServers({ uninstall: true });
    return true;
  }
  return false;
}

if (handleCli(process.argv.slice(2))) {
  process.exit(0);
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
