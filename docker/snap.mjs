// Claude's snapshots on the Mac, as tool/snap.py takes them on the Windows PC. Run from anywhere,
// with the container up (docker compose up) and the skin shown (tool.skin show <name> --no-snap):
//
//   node docker/snap.mjs <name>                  the six views -> build/<name>_views.png, and the
//                                                gallery's picture with a version kept (what
//                                                tool.skin show's snapshot does on the PC)
//   node docker/snap.mjs <name> --close          the close looks -> build/<name>_close.png
//   node docker/snap.mjs <name> --cams           the game's Cam 1 and 2 and their alts, day and night, at
//                                                16:9 -> build/<name>_cams.png
//   node docker/snap.mjs <name> --body           the body alone, no wheels, nine views (the car map's)
//   node docker/snap.mjs <name> --stretches      the car map's close looks, each stretch of the body, no wheels
//   node docker/snap.mjs <name> --review         the angles the other sheets miss, for the studio's
//                                                critic -> build/<name>_review.png
// Each sheet is copied to .snap/ too, for Claude to look at on the Mac.
//   node docker/snap.mjs <name> [<more> ...] --picture --titles "…" [--views …] [--close-row <name> 3 4 9 ...]
//                                                the picture for the user, opened on the screen
//   node docker/snap.mjs --page "mood.html?car=<car>" [--size 1600x1000]
//                                                any page of the viewer's, whole, once it says it's ready
//                                                (window.mood or window.lab) -> .snap/<page>_<car>.png
//
// The container has no browser, so the Mac's own Chrome takes the pictures: headless, on a
// throwaway profile, driven over its DevTools port on 127.0.0.1 only (Node 24's fetch and
// WebSocket, nothing to install). The views to take come from tool.snap (--shots), and the
// pictures go back to it through the repo's .snap/ folder, which the container sees as
// /app/.snap, to be made into the same sheets (--tiles). Sheets stay in the container's build
// folder, where tool.snap --picture finds them, and are copied out to .snap/; the picture is
// opened.
import { spawn, spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
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
  // port 0: Chrome picks a free port and writes it to its profile, so several snapshots can run at
  // once (the studio's concept designers, 2026-09-28)
  const proc = spawn(CHROME, ['--headless=new', '--use-angle=metal', '--enable-gpu', '--hide-scrollbars',
    '--remote-debugging-port=0', `--user-data-dir=${profile}`, 'about:blank'], { stdio: 'ignore' });
  const portFile = join(profile, 'DevToolsActivePort');
  let targets;
  for (let i = 0; i < 75 && !targets; i++) {
    try {
      const port = existsSync(portFile) && readFileSync(portFile, 'utf8').split('\n')[0].trim();
      if (port) targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json(); else await sleep(200);
    } catch { await sleep(200); }
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

async function snap(name, kind, size) {  // kind: views, close, cams or review
  const flag = kind === 'views' ? [] : [`--${kind}`];
  const { build, shots } = JSON.parse(tool(['-m', 'tool.snap', name, ...flag, '--shots'], true));
  const dir = join(ROOT, '.snap', name);
  rmSync(dir, { recursive: true, force: true });
  mkdirSync(dir, { recursive: true });
  const b = await chrome();
  try {
    await b.send('Emulation.setDeviceMetricsOverride', { width: size[0], height: size[1], deviceScaleFactor: 1, mobile: false });
    const start = Date.now();
    await b.send('Page.navigate', { url: `${VIEWER}/?skin=${encodeURIComponent(name)}&snap=1${kind === 'cams' ? '&lens=game' : ''}` });
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
  tool(['-m', 'tool.snap', name, ...(flag.length ? flag : ['--thumb']), '--tiles', `/app/.snap/${name}`]);
  console.log(`copied: ${copyOut(build, `${name}_${kind}.png`)}`);
}

function picture(args) {
  const { build } = JSON.parse(tool(['-m', 'tool.snap', args[0], '--shots'], true));
  tool(['-m', 'tool.snap', ...args]);
  const out = copyOut(build, `${args[0]}_picture.png`);
  spawnSync('open', [out]);
  console.log(`opened: ${out}`);
}

async function page(path, size) {  // any page of the viewer's, whole: e.g. a studio car's mood boards
  const b = await chrome();
  const name = path.replace(/\.html.*$/, '') + (new URL(path, VIEWER).searchParams.get('car') ? `_${new URL(path, VIEWER).searchParams.get('car')}` : '');
  const out = join(ROOT, '.snap', `${name}.png`);
  try {
    await b.send('Emulation.setDeviceMetricsOverride', { width: size[0], height: size[1], deviceScaleFactor: 1, mobile: false });
    await b.send('Page.navigate', { url: `${VIEWER}/${path}` });
    for (let i = 0; i < 600; i++) {  // up to 2 minutes: a page says it's done through window.mood (or window.lab)
      await sleep(200);
      try { if (await b.evaluate('!!["mood", "lab"].some((k) => window[k] && (window[k].ready || window[k].error))')) break; } catch { /* still loading */ }
    }
    const err = await b.evaluate('(window.mood || window.lab || {}).error || null');
    if (err) throw new Error(err);
    const height = await b.evaluate('Math.ceil(document.documentElement.scrollHeight)');
    await b.send('Emulation.setDeviceMetricsOverride', { width: size[0], height, deviceScaleFactor: 1, mobile: false });
    await sleep(300);
    const shot = await b.send('Page.captureScreenshot', { format: 'png' });
    mkdirSync(join(ROOT, '.snap'), { recursive: true });
    writeFileSync(out, Buffer.from(shot.result.data, 'base64'));
    for (const e of b.errors) console.log(`page error: ${e}`);
  } finally {
    b.close();
  }
  console.log(`photographed: ${out}`);
}

const args = process.argv.slice(2);
if (args[0] === '--page') {
  const i = args.indexOf('--size');
  await page(args[1], (i >= 0 ? args[i + 1] : '1600x1000').split('x').map(Number));
  process.exit(0);
}
if (!args.length || args[0].startsWith('-')) {
  console.log('node docker/snap.mjs <name> [--close | --cams | --review | --body | --stretches] [--size 960x720] | <name> [<more> ...] --picture [--titles ...] [--views ...] [--close-row <name> N ...]');
  process.exit(1);
}
if (args.includes('--picture')) picture(args);
else {
  const kind = args.includes('--close') ? 'close' : args.includes('--cams') ? 'cams' : args.includes('--review') ? 'review'
    : args.includes('--body') ? 'body' : args.includes('--stretches') ? 'stretches' : 'views';
  const i = args.indexOf('--size');
  const size = (i >= 0 ? args[i + 1] : kind === 'cams' ? '1280x720' : '960x720').split('x').map(Number);
  await snap(args[0], kind, size);
}
