// Claude's snapshots on the Mac, as tool/snap.py takes them on the Windows PC. Run from anywhere,
// with the container up (docker compose up) and the skin shown (tool.skin show <name> --no-snap):
//
//   node docker/snap.mjs <name>                  the six views -> build/<name>_views.png, and the
//                                                gallery's picture with a version kept (what
//                                                tool.skin show's snapshot does on the PC)
//   node docker/snap.mjs <name> --close          the close looks -> build/<name>_close.png
// Each sheet is copied to .snap/ too, for Claude to look at on the Mac.
//   node docker/snap.mjs <name> [<more> ...] --picture --titles "…" [--views …] [--close-row <name> 3 4 9]
//                                                the picture for the user, opened on the screen
//
// The container has no browser, so the Mac's own Chrome takes the pictures: headless, on a
// throwaway profile, driven over its DevTools port on 127.0.0.1 only (Node 24's fetch and
// WebSocket, nothing to install). The views to take come from tool.snap (--shots), and the
// pictures go back to it through the repo's .snap/ folder, which the container sees as
// /app/.snap, to be made into the same sheets (--tiles). Sheets stay in the container's build
// folder, where tool.snap --picture finds them, and are copied out to .snap/; the picture is
// opened.
import { spawn, spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const PORT = 9333;
const VIEWER = 'http://localhost:8765';  // the container's server, published on this Mac only
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function copyOut(build, file) {  // a file from the container's build folder to .snap/
  const png = tool(['-c', `import sys; sys.stdout.buffer.write(open(${JSON.stringify(`${build}/${file}`)}, 'rb').read())`], true);
  mkdirSync(join(ROOT, '.snap'), { recursive: true });
  const out = join(ROOT, '.snap', file);
  writeFileSync(out, png);
  return out;
}

function tool(args, capture = false) {  // python in the container, from the repo root
  const r = spawnSync('docker', ['compose', 'exec', '-T', 'app', 'python', ...args],
    { cwd: ROOT, encoding: capture ? 'buffer' : 'utf8', stdio: capture ? ['ignore', 'pipe', 'inherit'] : 'inherit', maxBuffer: 1 << 28 });
  if (r.status !== 0) throw new Error(`tool ${args.join(' ')} failed`);
  return r.stdout;
}

async function chrome() {
  const profile = mkdtempSync(join(tmpdir(), 'tsc-snap-'));
  const proc = spawn(CHROME, ['--headless=new', '--use-angle=metal', '--enable-gpu', '--hide-scrollbars',
    `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, 'about:blank'], { stdio: 'ignore' });
  let targets;
  for (let i = 0; i < 75 && !targets; i++) {
    try { targets = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json(); } catch { await sleep(200); }
  }
  if (!targets) throw new Error('Chrome did not start');
  const ws = new WebSocket(targets.find((t) => t.type === 'page').webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener('open', r));
  let id = 0;
  const pending = new Map(), errors = [];
  ws.addEventListener('message', (e) => {
    const m = JSON.parse(e.data);
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
    if (m.method === 'Runtime.exceptionThrown') errors.push(m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text);
    if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') errors.push(m.params.args.map((a) => a.value ?? a.description).join(' '));
  });
  const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
  const evaluate = async (expression) => {
    const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
    if (r.result.exceptionDetails) throw new Error(r.result.exceptionDetails.exception?.description || r.result.exceptionDetails.text);
    return r.result.result.value;
  };
  await send('Runtime.enable');
  const close = () => { ws.close(); proc.kill(); setTimeout(() => rmSync(profile, { recursive: true, force: true }), 500); };
  return { send, evaluate, errors, close };
}

async function snap(name, close, size) {
  const { build, shots } = JSON.parse(tool(['-m', 'tool.snap', name, ...(close ? ['--close'] : []), '--shots'], true));
  const dir = join(ROOT, '.snap', name);
  rmSync(dir, { recursive: true, force: true });
  mkdirSync(dir, { recursive: true });
  const b = await chrome();
  try {
    await b.send('Emulation.setDeviceMetricsOverride', { width: size[0], height: size[1], deviceScaleFactor: 1, mobile: false });
    const start = Date.now();
    await b.send('Page.navigate', { url: `${VIEWER}/?skin=${encodeURIComponent(name)}&snap=1` });
    for (let i = 0; i < 900; i++) {  // up to 3 minutes, as on the PC
      await sleep(200);
      try { if (await b.evaluate('!!(window.viewer && (window.viewer.ready || window.viewer.error))')) break; } catch { /* still loading */ }
    }
    const err = await b.evaluate('window.viewer ? window.viewer.error : "the viewer did not load"');
    if (err) throw new Error(err);
    console.log(`GPU: ${await b.evaluate('viewer.gpu()')}; loaded in ${((Date.now() - start) / 1000).toFixed(1)} s`);
    for (const [k, [, view, night, hidden, parts]] of shots.entries()) {
      await b.evaluate(`viewer.show(${JSON.stringify(view)}, ${night}, ${JSON.stringify(hidden)})`);
      await b.evaluate(`viewer.showParts(${JSON.stringify(parts || {})})`);
      const shot = await b.send('Page.captureScreenshot', { format: 'png' });
      writeFileSync(join(dir, `${k}.png`), Buffer.from(shot.result.data, 'base64'));
    }
    for (const e of b.errors) console.log(`page error: ${e}`);
  } finally {
    b.close();
  }
  tool(['-m', 'tool.snap', name, ...(close ? ['--close'] : ['--thumb']), '--tiles', `/app/.snap/${name}`]);
  console.log(`copied: ${copyOut(build, `${name}_${close ? 'close' : 'views'}.png`)}`);
}

function picture(args) {
  const { build } = JSON.parse(tool(['-m', 'tool.snap', args[0], '--shots'], true));
  tool(['-m', 'tool.snap', ...args]);
  const out = copyOut(build, `${args[0]}_picture.png`);
  spawnSync('open', [out]);
  console.log(`opened: ${out}`);
}

const args = process.argv.slice(2);
if (!args.length || args[0].startsWith('-')) {
  console.log('node docker/snap.mjs <name> [--close] [--size 960x720] | <name> [<more> ...] --picture [--titles ...] [--views ...] [--close-row <name> N ...]');
  process.exit(1);
}
if (args.includes('--picture')) picture(args);
else {
  const i = args.indexOf('--size');
  const size = (i >= 0 ? args[i + 1] : '960x720').split('x').map(Number);
  await snap(args[0], args.includes('--close'), size);
}
