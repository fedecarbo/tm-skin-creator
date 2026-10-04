// The Lab's levels room: the user draws the car's levels from the side (2026-10-04: "a tool I can
// define from the side how the line goes"; the car's line is its curved top and bottom seen from the
// side, and the levels follow it). A level is a height along the car through a handful of points:
// drag them up, down and along; click anywhere on the side view to add one there; pick one and press
// Delete to take it off. The curve through them is a natural cubic spline held level past the ends,
// the one tool/levels.py paints, so the side view shows exactly where the line runs on the car.
// Above it, the car itself with the line drawn on it as it moves (through the car map's outline every
// cm: a close picture, the paint is exact), turned with a drag; "Show it on the car" paints it (about
// 20 s) and dresses the car in it. Everything saves as you go (/api/levels, car/levels.json).
//   /lab.html?room=levels

import { $, embedViewer } from './lab-common.js';

const CM = 100;  // the viewer works in metres, the levels in cm
const WHEEL = (p) => p.mesh === 'Wheels' || p.parent === 'rims and brakes' || p.parent === 'wheel cover';

let doc = { levels: [] };  // as car/levels.json: [{ name, points: [[z, y] cm] }]
let cur = 0;               // the level open
let sel = -1;              // its picked point
let car = null;            // the viewer's window.viewer
let side = null;           // the side view's place in cm (tool/levels.py side.json)
let outlines = [];         // the body's outline every cm: [[z, Float32Array x, y, ...]]
let partInfo = new Map();
let drag = null;           // the point being dragged: { i, moved }
let saveTimer = null, liveFrame = 0, paintWatch = null, paintedStamp = 0;
let opened = false;
const undo = [];

// ---- the level's curve: a natural cubic spline through its points, held level past the ends ----

export function spline(P) {
  let p = P.map((q) => [q[0], q[1]]).sort((a, b) => a[0] - b[0]);
  if (p.length === 2) p = [p[0], [(p[0][0] + p[1][0]) / 2, (p[0][1] + p[1][1]) / 2], p[1]];
  const n = p.length, x = p.map((q) => q[0]), y = p.map((q) => q[1]);
  const h = x.slice(1).map((v, i) => v - x[i]);
  const a = new Array(n).fill(0), b = new Array(n).fill(1), c = new Array(n).fill(0), d = new Array(n).fill(0);
  for (let i = 1; i < n - 1; i++) {
    a[i] = h[i - 1]; b[i] = 2 * (h[i - 1] + h[i]); c[i] = h[i];
    d[i] = 6 * ((y[i + 1] - y[i]) / h[i] - (y[i] - y[i - 1]) / h[i - 1]);
  }
  for (let i = 1; i < n; i++) { const m = a[i] / b[i - 1]; b[i] -= m * c[i - 1]; d[i] -= m * d[i - 1]; }
  const M = new Array(n).fill(0);
  M[n - 1] = d[n - 1] / b[n - 1];
  for (let i = n - 2; i >= 0; i--) M[i] = (d[i] - c[i] * M[i + 1]) / b[i];
  return (z) => {
    z = Math.min(Math.max(z, x[0]), x[n - 1]);
    let i = 0;
    while (i < n - 2 && z > x[i + 1]) i++;
    const hi = h[i], A = x[i + 1] - z, B = z - x[i];
    return (M[i] * A ** 3 + M[i + 1] * B ** 3) / (6 * hi) + (y[i] / hi - (M[i] * hi) / 6) * A + (y[i + 1] / hi - (M[i + 1] * hi) / 6) * B;
  };
}

// ---- the line on the 3D car: on each cm's outline, the outermost place at the level's height ----

function lineOnCar(Y) {
  const runs = [];
  let run = [];
  for (const [z, q] of outlines) {
    const yz = Y(z);
    let best = null;
    for (let k = 0; k + 3 < q.length; k += 2) {
      const y0 = q[k + 1] - yz, y1 = q[k + 3] - yz;
      if ((y0 < 0) === (y1 < 0)) continue;
      const t = y0 / (y0 - y1), x = q[k] + t * (q[k + 2] - q[k]);
      if (!best || x > best[0]) best = [x, yz, z];
    }
    const last = run[run.length - 1];
    if (!best || (last && Math.hypot(best[0] - last[0], best[2] - last[2]) > 4)) {
      if (run.length > 1) runs.push(run);
      run = [];
    }
    if (best) run.push(best);
  }
  if (run.length > 1) runs.push(run);
  return runs;
}

function drawCar() {
  liveFrame = 0;
  if (!car || !outlines.length) return;
  const list = [];
  doc.levels.forEach((L, i) => {
    if (L.points.length < 2) return;
    lineOnCar(spline(L.points)).forEach((r, k) => {
      const m = r.map((p) => p.map((v) => v / CM));
      const look = i === cur ? { colour: '#e8ff47', radius: 0.007 } : { colour: '#3a3d45', radius: 0.004, dim: true };
      list.push({ key: `l${i}r${k}`, points: m, ...look });
      list.push({ key: `l${i}m${k}`, points: m.map(([x, y, z]) => [-x, y, z]), ...look });
    });
  });
  car.curves(list);
}

const live = () => { if (!liveFrame) liveFrame = requestAnimationFrame(drawCar); };

// ---- the side view ----

const NS = 'http://www.w3.org/2000/svg';
const el = (name, attrs) => { const e = document.createElementNS(NS, name); for (const k in attrs) e.setAttribute(k, attrs[k]); return e; };

function svgPoint(e) {  // a pointer's place in the side view, as [z, y] cm
  const svg = $('lvSvg'), pt = svg.createSVGPoint();
  pt.x = e.clientX; pt.y = e.clientY;
  const p = pt.matrixTransform(svg.getScreenCTM().inverse());
  return [p.x, -p.y];
}

function drawSide() {
  const g = $('lvCurves');
  g.textContent = '';
  const z0 = side.z0, z1 = side.z1;
  doc.levels.forEach((L, i) => {
    if (L.points.length < 2) return;
    const Y = spline(L.points);
    let d = '';
    for (let z = z0; z <= z1; z += 1) d += `${d ? 'L' : 'M'}${z.toFixed(1)},${(-Y(z)).toFixed(2)}`;
    g.appendChild(el('path', { d, class: i === cur ? 'lvCurve on' : 'lvCurve' }));
  });
  const L = doc.levels[cur];
  if (L) L.points.forEach(([z, y], k) => {
    const c = el('circle', { cx: z, cy: -y, r: 2.4, class: k === sel ? 'lvPt picked' : 'lvPt' });
    c.dataset.k = k;
    g.appendChild(c);
  });
}

function draw() {
  drawSide();
  live();
  panel();
}

function down(e) {
  const L = doc.levels[cur];
  if (!L || e.button !== 0) return;
  const k = e.target.dataset && e.target.dataset.k !== undefined ? Number(e.target.dataset.k) : -1;
  remember();
  if (k < 0) {  // a new point where the click is
    const [z, y] = svgPoint(e);
    if (L.points.some((p) => Math.abs(p[0] - z) < 1)) { undo.pop(); return; }
    L.points.push([round(z), round(y)]);
    L.points.sort((a, b) => a[0] - b[0]);
    sel = L.points.findIndex((p) => p[0] === round(z));
  } else sel = k;
  drag = { i: sel, moved: false };
  $('lvSvg').setPointerCapture(e.pointerId);
  draw();
}

function move(e) {
  if (!drag) return;
  const L = doc.levels[cur], P = L.points, i = drag.i;
  let [z, y] = svgPoint(e);
  const lo = i > 0 ? P[i - 1][0] + 1 : side.z0, hi = i < P.length - 1 ? P[i + 1][0] - 1 : side.z1;
  P[i] = [round(Math.min(Math.max(z, lo), hi)), round(Math.min(Math.max(y, side.y0), side.y1))];
  drag.moved = true;
  drawSide();
  live();
}

function up() {
  if (!drag) return;
  drag = null;
  changed();
}

const round = (v) => Math.round(v * 10) / 10;

// ---- the levels ----

function remember() {
  undo.push(JSON.stringify(doc));
  if (undo.length > 80) undo.shift();
  $('lvUndo').removeAttribute('aria-disabled');
}

function takeBack() {
  if (!undo.length) return;
  doc = JSON.parse(undo.pop());
  if (!undo.length) $('lvUndo').setAttribute('aria-disabled', 'true');
  cur = Math.min(cur, doc.levels.length - 1);
  sel = -1;
  changed();
}

function removePoint() {
  const L = doc.levels[cur];
  if (!L || sel < 0) return;
  if (L.points.length <= 2) { say('A level needs two points at least.'); return; }
  remember();
  L.points.splice(sel, 1);
  sel = -1;
  changed();
}

function newLevel() {
  const taken = new Set(doc.levels.map((l) => l.name.toLowerCase()));
  let name = '';
  for (let k = doc.levels.length + 1; !name; k++) if (!taken.has(`level ${k}`)) name = `level ${k}`;
  remember();
  doc.levels.push({ name, points: [[-150, 40], [0, 40], [200, 30]] });
  cur = doc.levels.length - 1;
  sel = -1;
  changed();
}

function deleteLevel() {
  if (doc.levels.length <= 1) { say('Keep one level at least: move its points instead.'); return; }
  remember();
  doc.levels.splice(cur, 1);
  cur = Math.min(cur, doc.levels.length - 1);
  sel = -1;
  changed();
}

function rename(value) {
  const L = doc.levels[cur];
  const name = value.trim().slice(0, 40);
  if (!L || !name || name === L.name) return;
  if (doc.levels.some((l, i) => i !== cur && l.name.toLowerCase() === name.toLowerCase())) { say(`There's a level called ${name} already.`); $('lvName').value = L.name; return; }
  remember();
  L.name = name;
  changed();
}

function changed() {
  draw();
  clearTimeout(saveTimer);
  $('lvSaved').textContent = 'Saving…';
  saveTimer = setTimeout(() => save(false), 400);
}

// ---- the panel ----

function panel() {
  const list = $('lvList');
  list.textContent = '';
  doc.levels.forEach((L, i) => {
    const b = document.createElement('button');
    b.className = 'item';
    b.setAttribute('aria-current', String(i === cur));
    b.innerHTML = '<span class="n"></span><span class="cnt"></span>';
    b.querySelector('.n').textContent = L.name;
    b.querySelector('.cnt').textContent = `${L.points.length} points`;
    b.addEventListener('click', () => { cur = i; sel = -1; draw(); });
    list.appendChild(b);
  });
  const L = doc.levels[cur];
  if (L && document.activeElement !== $('lvName')) $('lvName').value = L.name;
  $('lvDelPt').hidden = sel < 0;
  const hint = $('lvHint');
  if (sel >= 0 && L) hint.textContent = `Point ${sel + 1}: ${L.points[sel][1].toFixed(1)} cm up, ${Math.abs(L.points[sel][0]).toFixed(0)} cm ${L.points[sel][0] < 0 ? 'behind' : 'in front of'} the middle. Drag it, or press Delete to take it off.`;
  else hint.textContent = 'Drag the points up, down and along. Click anywhere on the side view to add a point there. The line on the car above follows as you drag.';
}

let sayTimer = null;
function say(text) {
  const box = $('lvSay');
  box.querySelector('span').textContent = text;
  box.hidden = false;
  clearTimeout(sayTimer);
  sayTimer = setTimeout(() => { box.hidden = true; }, 4000);
}

// ---- keeping and painting (tool/server.py /api/levels -> car/levels.json, tool/levels.py) ----

async function save(paint) {
  try {
    const r = await fetch('api/levels', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ levels: doc.levels, paint }) });
    const out = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(out.error || String(r.status));
    $('lvSaved').textContent = 'Saved';
    return true;
  } catch (e) {
    $('lvSaved').textContent = `Not saved: ${e.message}`;
    say(`Not saved, so not painted: ${e.message}`);
    return false;
  }
}

async function paintStamp() {
  try { const r = await fetch('data/levels/painted.json', { cache: 'no-store' }); if (r.ok) return (await r.json()).stamp; } catch { /* not yet */ }
  return 0;
}

async function showPainted() {
  const r = await fetch('data/skins/Look_Levels/skin.json', { cache: 'no-store' });
  if (!r.ok) return;
  const skin = await r.json();
  const urls = Object.fromEntries(Object.entries(skin.textures).filter(([, u]) => u).map(([s, u]) => [s, u]));
  await car.dress(urls);
}

async function paint() {
  clearTimeout(saveTimer);
  const before = await paintStamp();
  if (!(await save(true))) return;
  const btn = $('lvPaint');
  btn.setAttribute('aria-disabled', 'true');
  btn.querySelector('span').textContent = 'Painting… about 20 s';
  clearInterval(paintWatch);
  const started = Date.now();
  paintWatch = setInterval(async () => {
    const stamp = await paintStamp();
    if (stamp && stamp !== before) {
      clearInterval(paintWatch);
      paintedStamp = stamp;
      await showPainted();
      btn.removeAttribute('aria-disabled');
      btn.querySelector('span').textContent = 'Show it on the car';
      say('Painted on the car: turn it to check it close up. The yellow line is the live one.');
    } else if (Date.now() - started > 180000) {
      clearInterval(paintWatch);
      btn.removeAttribute('aria-disabled');
      btn.querySelector('span').textContent = 'Show it on the car';
      say("The paint didn't come back. Ask Claude.");
    }
  }, 1500);
}

async function load() {
  try {
    const r = await fetch('api/levels', { cache: 'no-store' });
    if (r.ok) doc = await r.json();
  } catch { /* a server from before the levels */ }
  if (!doc || !Array.isArray(doc.levels)) doc = { levels: [] };
  side = await fetch('data/levels/side.json', { cache: 'no-store' }).then((r) => r.json());
  const rows = await fetch('data/levels/sections.json').then((r) => r.json());
  outlines = rows.map(([z, q]) => [z, Float32Array.from(q)]);
}

async function clay() {
  const [stock, clayed] = await Promise.all([fetch('data/stock/stock.json').then((r) => r.json()), fetch('data/clay/clay.json').then((r) => r.json())]);
  const urls = Object.fromEntries(stock.filter((s) => s !== 'Skin_Coat').map((s) => [s, `stock/${s}.png`]));
  for (const s of clayed) urls[s] = `clay/${s}.png`;
  await car.dress(urls);
}

export async function open() {
  if (opened) { draw(); return; }
  opened = true;
  const uv = await fetch('data/uvmap.json').then((r) => r.json()).catch(() => ({}));
  partInfo = new Map((uv.parts || []).map((p) => [p.id, p]));
  await load();
  const svg = $('lvSvg');
  svg.setAttribute('viewBox', `${side.z0} ${-side.y1} ${side.z1 - side.z0} ${side.y1 - side.y0}`);
  const img = $('lvImg');
  for (const [k, v] of Object.entries({ x: side.z0, y: -side.y1, width: side.z1 - side.z0, height: side.y1 - side.y0 })) img.setAttribute(k, v);
  img.setAttribute('href', `data/levels/side.png?t=${side.mesh}`);
  svg.addEventListener('pointerdown', down);
  svg.addEventListener('pointermove', move);
  svg.addEventListener('pointerup', up);
  svg.addEventListener('pointercancel', up);
  $('lvUndo').addEventListener('click', takeBack);
  $('lvDelPt').addEventListener('click', removePoint);
  $('lvNew').addEventListener('click', newLevel);
  $('lvDelete').addEventListener('click', deleteLevel);
  $('lvPaint').addEventListener('click', () => { if (!$('lvPaint').hasAttribute('aria-disabled')) paint(); });
  $('lvName').addEventListener('change', (e) => rename(e.target.value));
  $('lvName').addEventListener('keydown', (e) => { if (e.key === 'Enter') e.target.blur(); });
  for (const b of $('lvViews').querySelectorAll('[data-view]')) b.addEventListener('click', () => car && car.go(b.dataset.view));
  addEventListener('keydown', (e) => {
    if ($('roomLevels').hidden || e.target.matches('input, textarea')) return;
    if ((e.key === 'Delete' || e.key === 'Backspace') && sel >= 0) { e.preventDefault(); removePoint(); }
    if (e.key === 'Escape') { sel = -1; draw(); }
    if ((e.key === 'z' || e.key === 'Z') && (e.metaKey || e.ctrlKey)) { e.preventDefault(); takeBack(); }
  });
  draw();
  try {
    car = await embedViewer($('lvCar'), $('lvCredit'));
    if (car) {
      paintedStamp = await paintStamp();
      if (paintedStamp) await showPainted(); else await clay();
      car.hide([...partInfo.values()].filter(WHEEL).map((p) => p.id));
      await car.show('right', false);
      drawCar();
    } else $('lvSaved').textContent = "The car couldn't be shown.";
  } finally {
    $('lvCover').classList.add('off');
  }
  window.lab.ready = true;  // for Claude's snapshots (tool/snap.py --page)
}
