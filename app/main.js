// The app: one window, the Lab on the left (an iframe on the Lab's server), the real Claude Code
// in a terminal on the right (node-pty). It starts the Lab's server the way tool/doctor.py does
// when nothing answers /api/health, and leaves it running when it quits. Nothing here changes
// how the tool or the Lab work: they're the same code, in the same repo, as in a terminal.
const { app, BrowserWindow, ipcMain, dialog, shell } = require("electron");
const { spawn, execFileSync } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");
const pty = require("node-pty");

const PORT = 8765;
const HEALTH = `http://127.0.0.1:${PORT}/api/health`;
const WORK = path.join(os.homedir(), "Library", "Application Support", "TrackmaniaSkinChallenge");
const PY = path.join(WORK, "venv", "bin", "python");
const CONFIG = path.join(app.getPath("userData"), "config.json");

function readConfig() {
  try { return JSON.parse(fs.readFileSync(CONFIG, "utf8")); } catch { return {}; }
}
function writeConfig(c) {
  fs.mkdirSync(path.dirname(CONFIG), { recursive: true });
  fs.writeFileSync(CONFIG, JSON.stringify(c, null, 2));
}
function isRepo(dir) {
  return dir && fs.existsSync(path.join(dir, "tool", "doctor.py")) && fs.existsSync(path.join(dir, "viewer", "index.html"));
}

// The repo: next to app/ when run from a checkout, else the folder remembered, else asked once.
async function findRepo() {
  const beside = path.resolve(__dirname, "..");
  if (isRepo(beside)) return beside;
  const config = readConfig();
  if (isRepo(config.repo)) return config.repo;
  const r = await dialog.showOpenDialog({
    title: "Where is the tm-skin-creator folder?",
    message: "Pick the tm-skin-creator folder (the one with tool/ and viewer/ in it).",
    properties: ["openDirectory"],
  });
  const picked = r.filePaths[0];
  if (!isRepo(picked)) { dialog.showErrorBox("Skin Lab", "That folder isn't tm-skin-creator."); app.quit(); return null; }
  writeConfig({ ...config, repo: picked });
  return picked;
}

async function healthy() {
  try {
    const r = await fetch(HEALTH, { signal: AbortSignal.timeout(1500) });
    const j = await r.json();
    return !!j.ok;
  } catch { return false; }
}

// Start the Lab's server as the tool does (tool/doctor.py server: detached, output to server.log).
function startServer(repo) {
  if (!fs.existsSync(PY)) {
    dialog.showErrorBox("Skin Lab", `The tool's Python isn't set up (${PY}). Set up the work folder first.`);
    return;
  }
  const child = spawn(PY, ["-m", "tool.doctor", "server"], { cwd: repo, detached: true, stdio: "ignore" });
  child.unref();
}

async function waitForLab(repo) {
  if (await healthy()) return true;
  startServer(repo);
  for (let i = 0; i < 90; i++) {
    await new Promise((r) => setTimeout(r, 1000));
    if (await healthy()) return true;
  }
  return false;
}

// The `claude` command: the native install (~/.local/bin), Homebrew, or whatever the login shell finds.
function claudeCommand() {
  for (const p of [path.join(os.homedir(), ".local", "bin", "claude"), "/opt/homebrew/bin/claude", "/usr/local/bin/claude"]) {
    if (fs.existsSync(p)) return p;
  }
  try { return execFileSync(process.env.SHELL || "/bin/zsh", ["-l", "-i", "-c", "command -v claude"], { encoding: "utf8" }).trim() || "claude"; }
  catch { return "claude"; }
}

let win = null;
let term = null;

function startClaude(repo, cols, rows) {
  if (term) return;
  const shell = process.env.SHELL || "/bin/zsh";
  const env = { ...process.env, TERM: "xterm-256color", COLORTERM: "truecolor", LANG: process.env.LANG || "en_US.UTF-8",
    PATH: [path.join(os.homedir(), ".local", "bin"), "/opt/homebrew/bin", process.env.PATH || "/usr/bin:/bin"].join(":") };
  const claude = claudeCommand();
  // A login, interactive shell so the user's own PATH, git and Python are there; then Claude in its place.
  term = pty.spawn(shell, ["-l", "-i", "-c", `exec ${JSON.stringify(claude)}`], { name: "xterm-256color", cols, rows, cwd: repo, env });
  term.onData((d) => win && !win.isDestroyed() && win.webContents.send("term:data", d));
  term.onExit(({ exitCode }) => { term = null; win && !win.isDestroyed() && win.webContents.send("term:exit", exitCode); });
}

async function main() {
  const repo = await findRepo();
  if (!repo) return;
  const config = readConfig();
  const b = config.bounds || {};
  win = new BrowserWindow({
    width: b.width || 1500, height: b.height || 950, x: b.x, y: b.y, minWidth: 900, minHeight: 500,
    title: "Skin Lab", backgroundColor: "#111214", titleBarStyle: "hiddenInset", trafficLightPosition: { x: 14, y: 14 },
    webPreferences: { preload: path.join(__dirname, "preload.js"), contextIsolation: true, nodeIntegration: false, sandbox: false },
  });
  win.on("close", () => writeConfig({ ...readConfig(), repo: isRepo(config.repo) ? config.repo : undefined, bounds: win.getBounds() }));
  // Links the Lab opens in a new tab go to the user's browser; the app keeps its one window.
  win.webContents.setWindowOpenHandler(({ url }) => { shell.openExternal(url); return { action: "deny" }; });

  ipcMain.handle("lab:ready", () => waitForLab(repo));
  ipcMain.handle("lab:url", () => `http://127.0.0.1:${PORT}/`);
  ipcMain.on("term:start", (_e, { cols, rows }) => startClaude(repo, cols, rows));
  ipcMain.on("term:write", (_e, d) => term && term.write(d));
  ipcMain.on("term:resize", (_e, { cols, rows }) => { try { term && term.resize(cols, rows); } catch {} });

  await win.loadFile("index.html");
  // The check: SKIN_LAB_SHOT=<file.png> saves a picture of the window after 30 s (app/README.md).
  if (process.env.SKIN_LAB_SHOT) {
    setTimeout(async () => {
      const img = await win.webContents.capturePage();
      fs.writeFileSync(process.env.SKIN_LAB_SHOT, img.toPNG());
    }, 30000);
  }
}

app.whenReady().then(main);
app.on("window-all-closed", () => app.quit());
app.on("before-quit", () => { if (term) { try { term.kill("SIGHUP"); } catch {} term = null; } });
