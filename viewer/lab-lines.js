// The Lab's lines room: the user pins the car's own lines on the 3D car. Claude can't see or click;
// the user can (2026-09-29: "Maybe we build a tool to build the tool"). A line is a handful of pins
// (5 to 8 are plenty); the curve drawn through them here is only a rough picture for the eye. The
// paint goes by the pins: tool/skindraw.py's `through` runs a line through a pinned line's pins by
// its name, on the surface, with a corner at each pin. The lines are kept in car/lines.json through
// the viewer's server (/api/lines): a small asset, committed, the same on both computers.
//   /lab.html?room=lines
// The car is the viewer itself (index.html?embed=1) in the viewer's grey clay, matte, with the wheels off
// (the user, 2026-09-29: "hide wheels ... make the skin maybe clayish and matte so I can see
// properly"; a switch puts them back). Turn it with a drag. Click the body along a line to pin it;
// click a pin to pick it, then click the body to move it there, or press Delete; click between two
// pins to add one. The lines to start from are said in plain words, and hovering one lights the
// part of the car it means (the user: "I struggle to know what are the sidepods, shoulders etc").
// Everything saves as you go.

import { $, embedViewer } from './lab-common.js';

const CM = 100;  // the viewer works in metres, the file in cm
const SPACING = 1.0;  // cm between the drawn curve's points

// Lines to start from: a plain name, what it means on this car, and the parts lit while it's hovered
// (uvmap.json's part names). Any other name works too; Claude goes by the name.
const SUGGESTED = [
  ['side crease', 'The crease that runs along the side of the car, above both wheels, from the nose to the tail. Designers call it the shoulder.', ['rear flank', 'sidepod top', 'nose panel']],
  ['bottom edge', 'Where the side of the car turns under, just above the ground, from the nose to the tail.', ['side skirt', 'diffuser']],
  ['side box top', 'The box beside the driver with the air scoop in its front is the side box (a sidepod). This is its top edge.', ['sidepod top', 'sidepod inlet']],
  ['side box bottom', "The side box's bottom edge, where it meets the skirt.", ['sidepod inlet', 'side skirt']],
  ['front arch', 'The rim of the opening round the front wheel (the wheels are off so you can see it).', []],
  ['rear arch', 'The rim of the opening round the rear wheel.', []],
  ['nose crease', 'A crease over the nose, one side; the tool mirrors it.', ['nose panel', 'nose tip']],
  ['tail edge', "The top edge of the tail, where the deck ends.", ['tail panel', 'tail corner']],
];
// The wheels: the tyres, the rims and brakes, and the wheel covers on the body.
const WHEEL = (p) => p.mesh === 'Wheels' || p.parent === 'rims and brakes' || p.parent === 'wheel cover';

let doc = { lines: [] };  // as car/lines.json: [{ name, mirror, points: [[x, y, z] cm], normals }]
let cur = -1;             // the line being pinned
let sel = -1;             // the picked pin of it
let car = null;           // the viewer's window.viewer
let partInfo = new Map(); // uvmap.json's parts by id: which map a click lands on, and what to light
let wheels = false;       // the wheels shown
const undo = [];          // earlier states, newest last
let saveTimer = null;
let litTimer = null;
let opened = false;

// ---- the rough curve through the pins: a centripetal Catmull-Rom spline, put back on the body ----

const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const scale = (a, k) => [a[0] * k, a[1] * k, a[2] * k];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const norm = (a) => Math.hypot(a[0], a[1], a[2]);
const lerp = (a, b, t) => add(scale(a, 1 - t), scale(b, t));

function catmullRom(P, spacing = SPACING) {
  if (P.length < 2) return P.map((p) => [...p]);
  if (P.length === 2) {
    const n = Math.max(2, Math.ceil(norm(sub(P[1], P[0])) / spacing) + 1);
    return Array.from({ length: n }, (_, i) => lerp(P[0], P[1], i / (n - 1)));
  }
  const Q = [sub(scale(P[0], 2), P[1]), ...P, sub(scale(P[P.length - 1], 2), P[P.length - 2])];  // the ends carried straight on
  const out = [];
  for (let i = 1; i < Q.length - 2; i++) {
    const [p0, p1, p2, p3] = [Q[i - 1], Q[i], Q[i + 1], Q[i + 2]];
    const t0 = 0, t1 = t0 + Math.sqrt(norm(sub(p1, p0))), t2 = t1 + Math.sqrt(norm(sub(p2, p1))), t3 = t2 + Math.sqrt(norm(sub(p3, p2)));
    const n = Math.max(1, Math.ceil(norm(sub(p2, p1)) / spacing));
    for (let k = 0; k < n; k++) {
      const t = t1 + ((t2 - t1) * k) / n;
      const A1 = lerp(p0, p1, (t - t0) / Math.max(t1 - t0, 1e-9)), A2 = lerp(p1, p2, (t - t1) / Math.max(t2 - t1, 1e-9)), A3 = lerp(p2, p3, (t - t2) / Math.max(t3 - t2, 1e-9));
      const B1 = lerp(A1, A2, (t - t0) / Math.max(t2 - t0, 1e-9)), B2 = lerp(A2, A3, (t - t1) / Math.max(t3 - t1, 1e-9));
      out.push(lerp(B1, B2, (t - t1) / Math.max(t2 - t1, 1e-9)));
    }
  }
  out.push([...P[P.length - 1]]);
  return out;
}

function smooth(pts, radius = 2) {  // a moving average, the ends kept
  return pts.map((p, i) => {
    if (i === 0 || i === pts.length - 1) return p;
    let s = [0, 0, 0], n = 0;
    for (let j = Math.max(0, i - radius); j <= Math.min(pts.length - 1, i + radius); j++) { s = add(s, pts[j]); n++; }
    return scale(s, 1 / n);
  });
}

// The pins' normals, carried along the curve, for the snap's rays.
function normalsAlong(L, pts) {
  const P = L.points, N = L.normals;
  return pts.map((p) => {
    let best = 0, bd = Infinity;
    for (let i = 0; i < P.length; i++) { const d = norm(sub(p, P[i])); if (d < bd) { bd = d; best = i; } }
    return N[best] || [0, 1, 0];
  });
}

const JUMP = 1.5;   // cm: a later snap that moves a point further than this caught another panel (a step, a lip): kept off it
const REACH = 0.2;  // metres: how far the first snap looks for the body (between two pins the spline cuts through its bulge)

function curveOf(L) {  // cm, on the body (tool/lines.py draws the same, and paints by it)
  if (L.points.length < 2) return [];
  let pts = catmullRom(L.points);
  const nrm = normalsAlong(L, pts);
  const onBody = (p, reach, guard) => car.snap(p.map((q) => scale(q, 1 / CM)), nrm, reach).map((q, i) => {
    const s = scale(q, CM);
    return guard && norm(sub(s, p[i])) > JUMP ? p[i] : s;
  });
  pts = onBody(pts, REACH, false);
  for (let k = 0; k < 2; k++) pts = onBody(smooth(pts), 0.05, true);
  return smooth(pts);
}

// ---- drawing ----

const mirror = (p) => [-p[0], p[1], p[2]];
const isCur = (i) => i === cur;

function draw() {
  panel();
  if (!car) return;
  const list = [];
  doc.lines.forEach((L, i) => {
    const pts = curveOf(L);
    if (!pts.length) return;
    const m = pts.map((p) => scale(p, 1 / CM));
    list.push({ key: `l${i}`, points: m, colour: isCur(i) ? '#e8ff47' : '#3a3d45', radius: isCur(i) ? 0.0035 : 0.0025, dim: !isCur(i) });
    if (L.mirror) list.push({ key: `m${i}`, points: m.map(mirror), colour: isCur(i) ? '#e8ff47' : '#3a3d45', radius: 0.002, dim: true });
  });
  car.curves(list);
  const L = doc.lines[cur];
  car.track(L ? L.points.map((p, i) => ({ key: `p${i}`, at: scale(p, 1 / CM), normal: L.normals[i] })) : [], placeDots);
  if (!L) $('lnDots').textContent = '';
}

function placeDots(points) {
  const box = $('lnDots');
  const have = new Map([...box.children].map((el) => [el.dataset.key, el]));
  for (const p of points) {
    let el = have.get(p.key);
    if (!el) {
      el = document.createElement('button');
      el.className = 'lnDot';
      el.dataset.key = p.key;
      el.textContent = String(Number(p.key.slice(1)) + 1);
      el.title = 'Pick this pin, then click the body to move it, or press Delete';
      el.addEventListener('click', (e) => { e.stopPropagation(); pick(Number(p.key.slice(1))); });
      box.appendChild(el);
    } else have.delete(p.key);
    el.style.transform = `translate(${p.x}px, ${p.y}px)`;
    el.hidden = !p.shown;
    el.classList.toggle('away', p.away);
    el.classList.toggle('picked', Number(p.key.slice(1)) === sel);
  }
  for (const el of have.values()) el.remove();
}

function pick(i) {
  sel = sel === i ? -1 : i;
  for (const el of $('lnDots').children) el.classList.toggle('picked', Number(el.dataset.key.slice(1)) === sel);
  hint();
}

// Light the parts a suggestion means, on the car, while it's hovered (or for a moment).
const idsOf = (names) => [...partInfo.values()].filter((p) => names.includes(p.name)).map((p) => p.id);
function light(names, moment = false) {
  if (!car) return;
  clearTimeout(litTimer);
  car.light(idsOf(names || []));
  if (moment && names && names.length) litTimer = setTimeout(() => car.light([]), 3000);
}

function showWheels(on) {
  wheels = on;
  if (car) car.hide(on ? [] : [...partInfo.values()].filter(WHEEL).map((p) => p.id));
  $('lnWheels').setAttribute('aria-pressed', String(on));
}

// ---- the pins ----

function remember() {
  undo.push(JSON.stringify(doc));
  if (undo.length > 60) undo.shift();
  $('lnUndo').removeAttribute('aria-disabled');
}

function takeBack() {
  if (!undo.length) return;
  doc = JSON.parse(undo.pop());
  if (!undo.length) $('lnUndo').setAttribute('aria-disabled', 'true');
  cur = Math.min(cur, doc.lines.length - 1);
  sel = -1;
  changed();
}

// Where a new pin goes: beyond an end the line grows, otherwise it goes in between the two it fell among.
function insert(L, at, n) {
  const P = L.points;
  if (P.length < 2) { P.push(at); L.normals.push(n); return; }
  let best = { d: Infinity, i: 0, t: 0 };
  for (let i = 0; i < P.length - 1; i++) {
    const ab = sub(P[i + 1], P[i]), ap = sub(at, P[i]);
    const t = Math.max(0, Math.min(1, dot(ap, ab) / Math.max(dot(ab, ab), 1e-9)));
    const d = norm(sub(ap, scale(ab, t)));
    if (d < best.d) best = { d, i, t };
  }
  const before = best.i === 0 && best.t === 0, after = best.i === P.length - 2 && best.t === 1;
  const idx = before ? 0 : after ? P.length : best.i + 1;
  P.splice(idx, 0, at);
  L.normals.splice(idx, 0, n);
}

function pinned(id, hit) {  // a click on the car
  const p = partInfo.get(id);
  if (p && p.mesh !== 'Skin') { say(`The lines live on the body. That's ${p.label || 'the inner car'}.`); return; }
  if (cur < 0) { say('Start a line first: pick one on the right.'); return; }
  const L = doc.lines[cur];
  const at = hit.at.map((v) => Math.round(v * CM * 100) / 100);
  const n = hit.normal.map((v) => Math.round(v * 1000) / 1000);
  remember();
  if (sel >= 0) { L.points[sel] = at; L.normals[sel] = n; sel = -1; }
  else insert(L, at, n);
  changed();
}

function removePin() {
  const L = doc.lines[cur];
  if (!L || sel < 0) return;
  remember();
  L.points.splice(sel, 1);
  L.normals.splice(sel, 1);
  sel = -1;
  changed();
}

// ---- the lines ----

function newLine(name) {
  const taken = new Set(doc.lines.map((l) => l.name.toLowerCase()));
  if (!name) for (let k = doc.lines.length + 1; !name; k++) if (!taken.has(`line ${k}`)) name = `line ${k}`;
  if (taken.has(name.toLowerCase())) { openLine(doc.lines.findIndex((l) => l.name.toLowerCase() === name.toLowerCase())); return; }
  remember();
  doc.lines.push({ name, mirror: true, points: [], normals: [] });
  cur = doc.lines.length - 1;
  sel = -1;
  changed();
  light(null);
}

function openLine(i) {
  cur = i;
  sel = -1;
  draw();
  hint();
}

function deleteLine() {
  if (cur < 0) return;
  remember();
  doc.lines.splice(cur, 1);
  cur = Math.min(cur, doc.lines.length - 1);
  sel = -1;
  changed();
}

function rename(value) {
  const L = doc.lines[cur];
  const name = value.trim().slice(0, 40);
  if (!L || !name || name === L.name) return;
  if (doc.lines.some((l, i) => i !== cur && l.name.toLowerCase() === name.toLowerCase())) { say(`There's a line called ${name} already.`); $('lnName').value = L.name; return; }
  remember();
  L.name = name;
  changed();
}

function changed() {
  draw();
  hint();
  clearTimeout(saveTimer);
  $('lnSaved').textContent = 'Saving…';
  saveTimer = setTimeout(save, 400);
}

// ---- the panel ----

const meaning = (name) => SUGGESTED.find(([n]) => n === name.toLowerCase());

function panel() {
  const list = $('lnList');
  list.textContent = '';
  doc.lines.forEach((L, i) => {
    const b = document.createElement('button');
    b.className = 'item';
    b.setAttribute('aria-current', String(i === cur));
    b.innerHTML = '<span class="n"></span><span class="cnt"></span>';
    b.querySelector('.n').textContent = L.name;
    b.querySelector('.cnt').textContent = `${L.points.length} pin${L.points.length === 1 ? '' : 's'}${L.mirror ? ' · both sides' : ''}`;
    b.addEventListener('click', () => openLine(i));
    list.appendChild(b);
  });
  $('lnCount').textContent = doc.lines.length ? String(doc.lines.length) : '';
  // the lines to start from, less the ones pinned already
  const taken = new Set(doc.lines.map((l) => l.name.toLowerCase()));
  const sug = $('lnSuggest');
  sug.textContent = '';
  for (const [name, about, parts] of SUGGESTED) {
    if (taken.has(name)) continue;
    const b = document.createElement('button');
    b.className = 'lnSug';
    b.innerHTML = '<b class="teko"></b><span></span>';
    b.querySelector('b').textContent = name;
    b.querySelector('span').textContent = about;
    b.addEventListener('mouseenter', () => light(parts));
    b.addEventListener('mouseleave', () => light(null));
    b.addEventListener('click', () => newLine(name));
    sug.appendChild(b);
  }
  const L = doc.lines[cur];
  $('lnOpen').hidden = !L;
  if (L) {
    if (document.activeElement !== $('lnName')) $('lnName').value = L.name;
    const s = meaning(L.name);
    $('lnAbout').textContent = s ? s[1] : 'Your own line: Claude goes by its name.';
    $('lnWhere').hidden = !(s && s[2].length);
    for (const b of $('lnSides').querySelectorAll('[data-mirror]')) b.setAttribute('aria-pressed', String((b.dataset.mirror === 'both') === !!L.mirror));
    $('lnDelPin').hidden = sel < 0;
  }
}

function hint() {
  const L = doc.lines[cur];
  const el = $('lnHint');
  if (!L) el.textContent = 'Pick a line to start from on the right, or start one of your own. Then click the body where it runs. Turn the car with a drag.';
  else if (sel >= 0) el.textContent = `Pin ${sel + 1} is picked: click the body to move it there, or press Delete to take it off.`;
  else if (L.points.length === 0) el.textContent = `Click the body where "${L.name}" starts. Five to eight pins are plenty: the tool draws the smooth curve through them.`;
  else if (L.points.length === 1) el.textContent = 'Click further along the line. The curve appears from the second pin.';
  else el.textContent = 'Click beyond an end to carry the line on, or between two pins to add one there. Click a pin to move or remove it.';
  $('lnDelPin').hidden = sel < 0;
}

let sayTimer = null;
function say(text) {
  const el = $('lnSay');
  el.querySelector('span').textContent = text;
  el.hidden = false;
  clearTimeout(sayTimer);
  sayTimer = setTimeout(() => { el.hidden = true; }, 3500);
}

// ---- keeping the lines (tool/view.py, /api/lines -> car/lines.json) ----

async function save() {
  try {
    const r = await fetch('api/lines', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ lines: doc.lines }) });
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || String(r.status));
    $('lnSaved').textContent = 'Saved';
  } catch (e) {
    $('lnSaved').textContent = `Not saved: ${e.message}`;
  }
}

async function load() {
  try {
    const r = await fetch('api/lines', { cache: 'no-store' });
    if (r.ok) doc = await r.json();
  } catch { /* a server from before the lines */ }
  if (!doc || !Array.isArray(doc.lines)) doc = { lines: [] };
  for (const L of doc.lines) L.normals ||= L.points.map(() => [0, 1, 0]);
}

// The car in the viewer's grey clay (tool/view.py, ensure_clay): the stock textures with the clay ones over them.
async function clay() {
  const [stock, clayed] = await Promise.all([fetch('data/stock/stock.json').then((r) => r.json()), fetch('data/clay/clay.json').then((r) => r.json())]);
  const urls = Object.fromEntries(stock.filter((s) => s !== 'Skin_Coat').map((s) => [s, `stock/${s}.png`]));
  for (const s of clayed) urls[s] = `clay/${s}.png`;
  await car.dress(urls);
}

async function embedCar() {
  car = await embedViewer($('lnCar'), $('lnCredit'));
  if (car) car.onPick = pinned;
  return car;
}

export async function open() {
  if (opened) { draw(); return; }
  opened = true;
  const uv = await fetch('data/uvmap.json').then((r) => r.json()).catch(() => ({}));
  partInfo = new Map((uv.parts || []).map((p) => [p.id, p]));
  $('lnOwn').addEventListener('click', () => { newLine(); setTimeout(() => { $('lnName').focus(); $('lnName').select(); }); });
  $('lnUndo').addEventListener('click', takeBack);
  $('lnDelete').addEventListener('click', deleteLine);
  $('lnDelPin').addEventListener('click', removePin);
  $('lnWhere').addEventListener('click', () => { const s = doc.lines[cur] && meaning(doc.lines[cur].name); if (s) light(s[2], true); });
  $('lnWheels').addEventListener('click', () => showWheels(!wheels));
  $('lnName').addEventListener('change', (e) => rename(e.target.value));
  $('lnName').addEventListener('keydown', (e) => { if (e.key === 'Enter') e.target.blur(); if (e.key === 'Escape') { e.target.value = doc.lines[cur].name; e.target.blur(); } });
  for (const b of $('lnSides').querySelectorAll('[data-mirror]')) {
    b.addEventListener('click', () => { const L = doc.lines[cur]; if (!L) return; remember(); L.mirror = b.dataset.mirror === 'both'; changed(); });
  }
  for (const b of $('lnViews').querySelectorAll('[data-view]')) b.addEventListener('click', () => car && car.go(b.dataset.view));
  addEventListener('keydown', (e) => {
    if ($('roomLines').hidden || e.target.matches('input, textarea')) return;
    if ((e.key === 'Delete' || e.key === 'Backspace') && sel >= 0) { e.preventDefault(); removePin(); }
    if (e.key === 'Escape' && sel >= 0) pick(sel);
    if ((e.key === 'z' || e.key === 'Z') && (e.metaKey || e.ctrlKey)) { e.preventDefault(); takeBack(); }
  });
  await load();
  cur = doc.lines.length ? 0 : -1;
  hint();
  panel();
  try {
    await embedCar();
    if (car) {
      await clay();
      showWheels(false);
      await car.show('left', false);
      draw();
    } else $('lnSaved').textContent = "The car couldn't be shown.";
  } finally {
    $('lnCover').classList.add('off');
  }
  window.lab.ready = true;  // for Claude's snapshots (tool/snap.py --page)
}
