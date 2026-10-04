// The Lab's levels room: the user draws the car's levels from the side (2026-10-04: "a tool I can
// define from the side how the line goes"; the car's line is its curved top and bottom seen from the
// side, and the levels follow it). A level is a height along the car through a handful of points:
// drag them up, down and along; double-click on the side view to add one there; pick one and press
// Delete to take it off. The curve through them is a natural cubic spline held level past the ends,
// the one tool/levels.py paints, so the side view shows exactly where the line runs on the car.
// The side's levels: the top and the bottom are drawn like any level, and the levels between are
// shared out between them (blue, not dragged: they follow the two), the bottom's shape fading out
// towards the top as tool/levels.py's do, and from the intake forward leaning to the side skirt's
// seams' direction by how near them they run. The bottom runs only between its first and last points
// (to the nose's tip along the side skirt's edge), the levels between from its first point to the
// sidepods' front, or to the front wheel opening's upright edge if they pass over it. The car's seams
// along the side are drawn in orange (tool/seams.py), to shape the top and the bottom by. The nose's
// lines run above the top from the intake to the tip, each keeping its height above it and going
// round over the nose in a U (blue too, their number from the room's second − and +).
// Above it, the car itself with the line drawn on it as it moves (through the car map's outline every
// cm: a close picture, the paint is exact), turned with a drag; "Show it on the car" paints it (about
// 20 s) and dresses the car in it. The live line shows for the level picked and for whatever has
// changed since the paint, the rest is the paint itself. Everything saves as you go (/api/levels,
// car/levels.json), and coming back to the page takes the levels as they are there (changed by Claude,
// or by another copy of the room), so an old page never saves over them.
//   /lab.html?room=levels

import { $, embedViewer } from './lab-common.js';

const CM = 100;  // the viewer works in metres, the levels in cm
const MOST = 12;  // levels between the top and the bottom, at most (tool/levels.py MOST)
const SIDE_FRONT = 82;  // where the levels between end, the sidepods' front (tool/levels.py SIDE_FRONT)
const OPENING = [70, 41];  // the front wheel opening's upright edge and its height (tool/levels.py OPENING)
const STEER = ['side skirt', 'side skirt ahead'];  // the seams the levels between lean to (tool/levels.py STEER)
const STEER_FADE = [-45, -25], STEER_AT = 16;  // tool/levels.py STEER_FADE, STEER_AT
const NOSE = [28, 220, 12.9];  // the nose's lines: from, to, and the nose's side where they begin (tool/levels.py NOSE_*)
const WHEEL = (p) => p.mesh === 'Wheels' || p.parent === 'rims and brakes' || p.parent === 'wheel cover';

let doc = { levels: [] };  // as car/levels.json: { levels: [{ name, role?, points: [[z, y] cm] }], between, nose }
let cur = 0;               // the level open
let sel = -1;              // its picked point
let car = null;            // the viewer's window.viewer
let side = null;           // the side view's place in cm (tool/levels.py side.json)
let outlines = [];         // the body's outline every cm: [[z, Float32Array x, y, ...]]
let seamLines = {};        // the seams along the side, as the paint traced them: { name: [[z, y] cm] }
let lift = 0;              // cm the viewer raises the car by, tyres on the floor (data/car.json)
let painted = null;        // the levels as last painted: { stamp, levels, between } (data/levels/painted.json)
let partInfo = new Map();
let drag = null;           // the point being dragged: { i, moved }
let saveTimer = null, liveFrame = 0, paintWatch = null, paintedStamp = 0;
let unsaved = false;       // a change here not saved yet
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

// the stretch a level runs along: the bottom only between its ends, any other all along the car
const span = (L) => (L.role === 'bottom' ? [L.points[0][0], L.points[L.points.length - 1][0]] : [side.z0, side.z1]);

function seamsDirection() {  // tool/levels.py _seams_direction: [slope, the first's height at STEER_AT], or null
  const fits = [];
  for (const name of STEER) {
    const p = seamLines[name];
    if (!p || p.length < 2) return null;
    const mz = p.reduce((a, q) => a + q[0], 0) / p.length, my = p.reduce((a, q) => a + q[1], 0) / p.length;
    let sxy = 0, sxx = 0;
    for (const [z, y] of p) { sxy += (z - mz) * (y - my); sxx += (z - mz) ** 2; }
    const a = sxy / sxx;
    fits.push([a, my - a * mz, p[p.length - 1][0] - p[0][0]]);
  }
  const len = fits.reduce((t, f) => t + f[2], 0);
  return [fits.reduce((t, f) => t + f[0] * f[2], 0) / len, fits[0][0] * STEER_AT + fits[0][1]];
}

function between() {  // the levels between the top and the bottom, highest first: [{ Y, z0, z1 }]
  const top = doc.levels.find((L) => L.role === 'top'), bottom = doc.levels.find((L) => L.role === 'bottom');
  const n = doc.between || 0;
  if (!top || !bottom || top.points.length < 2 || bottom.points.length < 2) return [];
  const T = spline(top.points), B = spline(bottom.points), z0 = span(bottom)[0], z1 = Math.min(span(bottom)[1], SIDE_FRONT);
  const gaps = [];
  for (let z = z0; z <= z1 + 1e-9; z += 1) gaps.push(T(z) - B(z));
  gaps.sort((a, b) => a - b);
  const m = gaps.length, gap = m % 2 ? gaps[(m - 1) / 2] : (gaps[m / 2 - 1] + gaps[m / 2]) / 2;  // the typical gap
  // from the intake forward each leans to the side skirt's seams' direction by how near it runs to them
  const dir = seamsDirection(), steps = Math.floor((z1 - z0) / 0.25 + 1e-9) + 1;
  const grow = Float64Array.from({ length: steps }, (_, i) => {
    const t = Math.min(Math.max((z0 + i * 0.25 - STEER_FADE[0]) / (STEER_FADE[1] - STEER_FADE[0]), 0), 1);
    return t * t * (3 - 2 * t);
  });
  return Array.from({ length: n }, (_, k) => {
    const s = (k + 1) / (n + 1);  // how far down: 0 at the top, 1 at the bottom
    const Y0 = (z) => T(z) - s * gap - s * s * (T(z) - B(z) - gap);
    let Y = Y0;
    if (dir) {
      const near = Math.min(Math.max((T(STEER_AT) - Y0(STEER_AT)) / (T(STEER_AT) - dir[1]), 0), 1) ** 2;
      const lean = (i) => near * grow[i] * (dir[0] - (Y0(z0 + i * 0.25 + 0.05) - Y0(z0 + i * 0.25 - 0.05)) / 0.1);
      const rise = new Float64Array(steps);
      let prev = lean(0);
      for (let i = 1; i < steps; i++) { const cur = lean(i); rise[i] = rise[i - 1] + ((prev + cur) / 2) * 0.25; prev = cur; }
      Y = (z) => {
        const f = Math.min(Math.max((z - z0) / 0.25, 0), steps - 1), i = Math.min(Math.floor(f), steps - 2);
        return Y0(z) + rise[i] + (rise[i + 1] - rise[i]) * (f - i);
      };
    }
    return { Y, z0, z1: Y(OPENING[0]) > OPENING[1] ? OPENING[0] : z1 };
  });
}

function nose() {  // the nose's lines above the top, highest first: [{ Y, z0, z1 }]
  const top = doc.levels.find((L) => L.role === 'top'), n = doc.nose || 0;
  if (!top || top.points.length < 2) return [];
  const T = spline(top.points);
  return Array.from({ length: n }, (_, k) => {
    const d = (NOSE[2] * (n - k)) / n;
    return { Y: (z) => T(z) + d, z0: NOSE[0], z1: NOSE[1] };
  });
}

// ---- the line on the 3D car: on each cm's outline, the outermost place at the level's height ----

function lineOnCar(Y, z0, z1) {  // runs of [x, y, z] cm along the left side
  const runs = [];
  let run = [];
  for (const [z, q] of outlines) {
    if (z < z0 || z > z1) continue;
    const yz = Y(z), xs = [];
    for (let k = 0; k + 3 < q.length; k += 2) {
      const y0 = q[k + 1] - yz, y1 = q[k + 3] - yz;
      if ((y0 < 0) === (y1 < 0)) continue;
      xs.push(q[k] + (y0 / (y0 - y1)) * (q[k + 2] - q[k]));
    }
    // a run keeps to the surface it's on (the nearest crossing, within 4 cm: the sidepod's lip and the
    // body above it cross the same height side by side) and steps over up to 2 cm of outline that
    // doesn't go on with it (under the rear wheel's opening the outline flips between the flank's foot
    // and the diffuser from one cm to the next; at a panel's join it misses a slice); a new run starts
    // on the outermost
    const last = run[run.length - 1];
    let x = null;
    if (last) for (const c of xs) if (Math.abs(c - last[0]) <= 4 && (x === null || Math.abs(c - last[0]) < Math.abs(x - last[0]))) x = c;
    if (x === null && last && z - last[2] <= 3) continue;
    if (x === null) {
      if (run.length > 1) runs.push(run);
      run = [];
      if (xs.length) x = Math.max(...xs);
    }
    if (x !== null) run.push([x, yz, z]);
  }
  if (run.length > 1) runs.push(run);
  return runs;
}

// what the paint shows already: a level painted as it is now, and the levels between unchanged
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const ends = (d) => d && JSON.stringify(['top', 'bottom'].map((r) => (d.levels.find((l) => l.role === r) || {}).points).concat(d.between || 0, d.nose || 0));

function drawCar() {
  liveFrame = 0;
  if (!car || !outlines.length) return;
  const list = [];
  const add = (key, Y, [z0, z1], look) => lineOnCar(Y, z0, z1).forEach((r, k) => {
    const m = r.map(([x, y, z]) => [x / CM, (y + lift) / CM, z / CM]);
    list.push({ key: `${key}r${k}`, points: m, ...look });
    list.push({ key: `${key}m${k}`, points: m.map(([x, y, z]) => [-x, y, z]), ...look });
  });
  const was = new Map(((painted && painted.levels) || []).map((L) => [L.name, L]));
  doc.levels.forEach((L, i) => {
    if (L.points.length < 2) return;
    const old = was.get(L.name);
    if (i !== cur && old && same(old.points, L.points) && old.role === L.role) return;
    add(`l${i}`, spline(L.points), span(L), i === cur ? { colour: '#e8ff47', radius: 0.007 } : { colour: '#3a3d45', radius: 0.004, dim: true });
  });
  if (ends(doc) !== ends(painted)) between().concat(nose()).forEach((b, k) => add(`b${k}`, b.Y, [b.z0, b.z1], { colour: '#3d7bff', radius: 0.004 }));
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
  const path = (Y, z0, z1) => {
    let d = '';
    for (let z = z0; z < z1 + 1; z += 1) { const zz = Math.min(z, z1); d += `${d ? 'L' : 'M'}${zz.toFixed(1)},${(-Y(zz)).toFixed(2)}`; }
    return d;
  };
  for (const pts of Object.values(seamLines)) g.appendChild(el('path', { d: path(spline(pts), pts[0][0], pts[pts.length - 1][0]), class: 'lvSeam' }));
  between().forEach((b) => g.appendChild(el('path', { d: path(b.Y, b.z0, b.z1), class: 'lvCurve between' })));
  nose().forEach((b) => {  // seen from the side, each stops where it goes round over the nose's top
    let z1 = b.z0;
    for (const [z, q] of outlines) {
      if (z < b.z0) continue;
      let top = -Infinity;
      for (let k = 1; k < q.length; k += 2) top = Math.max(top, q[k]);
      if (b.Y(z) >= top) break;
      z1 = z;
    }
    g.appendChild(el('path', { d: path(b.Y, b.z0, z1), class: 'lvCurve between' }));
  });
  doc.levels.forEach((L, i) => {
    if (L.points.length < 2) return;
    g.appendChild(el('path', { d: path(spline(L.points), ...span(L)), class: i === cur ? 'lvCurve on' : 'lvCurve' }));
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

// A click off the points only lets go of the one picked, and a point moves only once the pointer has
// moved a few pixels: a stray click changes nothing (the user, 2026-10-04, after edits they didn't want).
function down(e) {
  const L = doc.levels[cur];
  if (!L || e.button !== 0) return;
  const k = e.target.dataset && e.target.dataset.k !== undefined ? Number(e.target.dataset.k) : -1;
  if (k < 0) { if (sel >= 0) { sel = -1; draw(); } return; }
  remember();
  sel = k;
  drag = { i: sel, moved: false, x: e.clientX, y: e.clientY };
  $('lvSvg').setPointerCapture(e.pointerId);
  draw();
}

function add(e) {  // a double-click on the side view: a new point there
  const L = doc.levels[cur];
  if (!L || (e.target.dataset && e.target.dataset.k !== undefined)) return;
  const [z, y] = svgPoint(e);
  if (L.points.some((p) => Math.abs(p[0] - z) < 1)) return;
  remember();
  L.points.push([round(z), round(y)]);
  L.points.sort((a, b) => a[0] - b[0]);
  sel = L.points.findIndex((p) => p[0] === round(z));
  changed();
}

function move(e) {
  if (!drag || (!drag.moved && Math.hypot(e.clientX - drag.x, e.clientY - drag.y) < 4)) return;
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
  const moved = drag.moved;
  drag = null;
  if (moved) return changed();
  undo.pop();  // only picked
  if (!undo.length) $('lvUndo').setAttribute('aria-disabled', 'true');
}

function keys(e) {  // the room's keys, from the page or from the car above it
  if ($('roomLevels').hidden || (e.target.matches && e.target.matches('input, textarea'))) return;
  if ((e.key === 'Delete' || e.key === 'Backspace') && sel >= 0) { e.preventDefault(); removePoint(); }
  if (e.key === 'Escape') { sel = -1; draw(); }
  if ((e.key === 'z' || e.key === 'Z') && (e.metaKey || e.ctrlKey)) { e.preventDefault(); takeBack(); }
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

function more(key, by) {  // how many levels between the top and the bottom, or on the nose: none to MOST
  const n = Math.min(Math.max((doc[key] || 0) + by, 0), MOST);
  if (n === (doc[key] || 0)) return;
  remember();
  doc[key] = n;
  changed();
}

function changed() {
  draw();
  unsaved = true;
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
  const both = doc.levels.some((l) => l.role === 'top') && doc.levels.some((l) => l.role === 'bottom');
  $('lvBetweenRow').hidden = !both;
  $('lvBetween').textContent = String(doc.between || 0);
  $('lvNoseRow').hidden = !doc.levels.some((l) => l.role === 'top');
  $('lvNose').textContent = String(doc.nose || 0);
  $('lvDelPt').hidden = sel < 0;
  const hint = $('lvHint');
  if (sel >= 0 && L) hint.textContent = `Point ${sel + 1}: ${L.points[sel][1].toFixed(1)} cm up, ${Math.abs(L.points[sel][0]).toFixed(0)} cm ${L.points[sel][0] < 0 ? 'behind' : 'in front of'} the middle. Drag it, or press Delete to take it off.`;
  else if (L && L.role === 'top') hint.textContent = 'The top: the levels between follow it. Drag its points up, down and along; double-click on the side view to add one.';
  else if (L && L.role === 'bottom') hint.textContent = 'The bottom: the levels between follow it, as far as the sidepods\' front. Drag its points, or its end points along to make it longer or shorter.';
  else hint.textContent = 'Drag the points up, down and along. Double-click on the side view to add a point there. The line on the car above follows as you drag.';
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

const kept = () => JSON.stringify({ levels: doc.levels, between: doc.between || 0, nose: doc.nose || 0 });

async function save(paint) {
  try {
    const sent = kept();
    const r = await fetch('api/levels', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ levels: doc.levels, between: doc.between || 0, nose: doc.nose || 0, paint }) });
    const out = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(out.error || String(r.status));
    if (kept() === sent) unsaved = false;
    $('lvSaved').textContent = 'Saved';
    return true;
  } catch (e) {
    $('lvSaved').textContent = `Not saved: ${e.message}`;
    say(`Not saved, so not painted: ${e.message}`);
    return false;
  }
}

async function sync() {  // coming back to the page: the levels and the paint as they are now
  if (drag || unsaved) return;
  try {
    const r = await fetch('api/levels', { cache: 'no-store' });
    if (!r.ok) return;
    const d = await r.json();
    const there = { levels: d.levels || [], between: d.between || 0, nose: d.nose || 0 };
    if (!drag && !unsaved && JSON.stringify(there) !== kept()) {
      doc = there;
      undo.length = 0;  // undo would bring back what was changed elsewhere
      $('lvUndo').setAttribute('aria-disabled', 'true');
      cur = Math.max(0, Math.min(cur, doc.levels.length - 1));
      sel = -1;
      draw();
    }
    const stamp = await paintStamp();
    if (car && stamp && stamp !== paintedStamp) { paintedStamp = stamp; await showPainted(); drawCar(); }
  } catch { /* the server is away */ }
}

async function paintStamp() {  // the last paint's stamp, and what it painted into `painted`
  try {
    const r = await fetch('data/levels/painted.json', { cache: 'no-store' });
    if (r.ok) { const p = await r.json(); if (!painted || p.stamp !== painted.stamp) painted = p; return p.stamp; }
  } catch { /* not yet */ }
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
      drawCar();
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
  lift = (await fetch('data/car.json').then((r) => r.json()).catch(() => ({}))).lift_cm || 0;
  seamLines = await fetch('data/levels/seams.json', { cache: 'no-store' }).then((r) => (r.ok ? r.json() : {})).catch(() => ({}));
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
  svg.addEventListener('dblclick', add);
  svg.addEventListener('pointermove', move);
  svg.addEventListener('pointerup', up);
  svg.addEventListener('pointercancel', up);
  $('lvUndo').addEventListener('click', takeBack);
  $('lvDelPt').addEventListener('click', removePoint);
  $('lvNew').addEventListener('click', newLevel);
  $('lvFewer').addEventListener('click', () => more('between', -1));
  $('lvMore').addEventListener('click', () => more('between', 1));
  $('lvNoseFewer').addEventListener('click', () => more('nose', -1));
  $('lvNoseMore').addEventListener('click', () => more('nose', 1));
  $('lvDelete').addEventListener('click', deleteLevel);
  $('lvPaint').addEventListener('click', () => { if (!$('lvPaint').hasAttribute('aria-disabled')) paint(); });
  $('lvName').addEventListener('change', (e) => rename(e.target.value));
  $('lvName').addEventListener('keydown', (e) => { if (e.key === 'Enter') e.target.blur(); });
  for (const b of $('lvViews').querySelectorAll('[data-view]')) b.addEventListener('click', () => car && car.go(b.dataset.view));
  addEventListener('focus', sync);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) sync(); });
  addEventListener('keydown', keys);
  draw();
  try {
    car = await embedViewer($('lvCar'), $('lvCredit'));
    try { $('lvCar').contentWindow.addEventListener('keydown', keys); } catch { /* not ours to listen to */ }
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
