// The Lab's car (the user's pick of the fresh layouts, A, 2026-09-28): the car being built fills the
// page, turned by a drag, by day or night or from the game's own camera, with the user's notes hanging on it as tags (lab-tags.js). Click the car where you mean and
// write what you want there, or draw on it with the pen (Draw: a strip where you'd want one, a ring
// round something; the user's idea, 2026-10-05), a line or several: the note keeps the point, the
// part under it, the lines drawn (in the paint box's cm, the car's own: tool/notes.py), the view (a
// click on its tag turns the car back to it) and a picture of what the user saw, in .notes/notes.json through the
// viewer's server (tool/notes.py, /api/notes), and reaches Claude with the user's next message (or at
// once, while Claude waits: tool.notes wait). Mesh lays the model's mesh over the paint (the viewer's mesh, from the
// UV room's template), on or off; with Mesh on, Draw picks a line on it instead (the user's idea, 2026-10-06: "click on
// certain multiple points similar to the draw tool"): each click lands on the nearest point where its lines cross, the tool
// runs the line between clicks (/api/meshpath, tool/meshlines.py path: along one of the model's lines when both are on
// it, else straight across), and the note keeps the clicks, so Claude paints that very line. Done, a note leaves the car and stays in the timeline
// beside it (lab-car.js), which also puts an option on the car to look at: its notes are that option's.
//   show(name)    a skin on the car: the car itself, or one of its options
//   look(note)    the car as the user saw it when they wrote the note
// Everything comes from the tool: tool.skin show paints a design step by step (paintbox.Skin.step),
// writes each step's frame and skins/<name>/steps.json (tool/view.py, export_steps), and studio.json,
// the skin it painted last. The page asks for both every 1.5 s: while Claude paints, the car shows
// each step as it's done, and it follows Claude to the skin it paints unless a note is being written
// or a tag is open. It says which skin it shows ('lab:stand') and what Claude is doing ('lab:status').
// The car is the viewer itself (index.html?embed=1).

import { $, ago, embedViewer, every, followed, note, post, titleOf } from './lab-common.js';
import { createTags } from './lab-tags.js';

const POLL = 1500;
let HINT = '';  // the hint over the car without the pen (lab.html's)

let skin = null;          // { name, title, entry: gallery.json's }: on the car
let carName = null;       // the car (lab-car.js), when the car shows one of its options
let optionName = (name) => name;  // an option's name as the list says it ("B · Magenta")
let doc = null;           // steps.json: the frames of the last show, while it paints and after
let stage = null;         // the viewer's window.viewer
let stageLook = '';       // while Claude paints, the look of the step on the stage
let following = null;     // studio.json's stamp when last read: a new one means Claude started a skin
let notes = [], nextN = 1;  // the skin's notes not done yet (tool/notes.py), and the next one's number
let writing = null;       // the note being written: { part, at, normal, view, picture, drawn }
let partInfo = new Map(); // uvmap.json's parts by id, to name the part under a click
let tags = null;          // lab-tags.js
let pen = false;          // Draw: a drag on the car draws on it
let meshOn = false;       // Mesh: the model's mesh over the paint
let picking = null;       // Draw with Mesh on, the line being picked: { set, clicks, hits, parts, line, ticks, closed } (cm)
let routing = 0;          // the latest ask for the picked line's way (a slower answer to an older one is dropped)
const PICK_SAME = 0.8;    // cm: a click this near the last ends the line (a double click)
const PICK_RING = 1.5;    // cm: one this near the first, after two more, closes it round
const PICK_COLOUR = '#ff3dd8';  // the line being picked, apart from the lines drawn
const picks = () => pen && meshOn;
const apart = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
let lift = 0;             // cm the viewer raises the car by, tyres on the floor (data/car.json)
const SIMPLER = 0.1;      // cm: a drawn line's points kept where it bends more than this

// The viewer's metres and the paint box's cm (tool/shapes.py: the car's own, as the notes keep it).
const toCm = ([x, y, z]) => [x * 100, y * 100 - lift, z * 100].map((v) => Math.round(v * 10) / 10);
const toMetres = ([x, y, z]) => [x / 100, (y + lift) / 100, z / 100];

const lookOf = (step) => {
  const words = (step.look || '').split(/\s+/);
  return { view: ['front', 'rear', 'left', 'right', 'top'].find((w) => words.includes(w)) || 'front', night: words.includes('night') };
};

// ---- the stage: the car framed between the gutters where its tags hang ----

// the gutters a fifth of the stage each, 200 to 300 px; none under 1000 px, where the tags are a list
const gutter = () => (matchMedia('(max-width: 1000px)').matches ? 0
  : Math.round(Math.min(300, Math.max(200, $('stStage').clientWidth * 0.2))));
const box = () => ({ left: gutter(), right: gutter(), top: 56, bottom: 10 });  // the top: the buttons over the car

function framed() {  // the box the car frames itself in, after a resize
  if (!$('stStage').clientWidth) return;
  if (stage) stage.inset(box());
  if (tags) tags.restack();
}

const lastFrame = () => doc && [...doc.steps].reverse().find((s) => s.textures);

function moodShown(m) {
  $('stand').classList.toggle('night', m === 'night');
  for (const b of $('stMood').querySelectorAll('[data-mood]')) b.setAttribute('aria-pressed', String(b.dataset.mood === m));
}

async function loadNotes(force = false) {
  if (!skin) return;
  const name = skin.name;
  try {
    const r = await fetch(`api/notes?skin=${encodeURIComponent(name)}`, { cache: 'no-store' });
    if (!r.ok || !skin || skin.name !== name) return;
    const got = await r.json();
    const list = got.notes.filter((x) => x.at);  // picks and words in the timeline hang on no point
    if (!force && JSON.stringify(list) === JSON.stringify(notes) && got.next === nextN) return;
    notes = list;
    nextN = got.next;
  } catch { return; }  /* a server from before the notes */
  drawNotes();
}

const stateOf = (x) => (x.state === 'sent' ? 'Claude has it' : 'Goes to Claude with your next message');
const whereOf = (x) => (x.skin !== carName ? `On ${optionName(x.skin)}` : '');

function renderNote(el, x, open) {
  if (!open) {
    el.innerHTML = '<div class="tagRow"><span class="pinDot"></span><span class="tn"></span></div>';
    el.querySelector('.pinDot').textContent = x.n;
    el.querySelector('.tn').textContent = x.text;
    return;
  }
  el.innerHTML = '<div class="tagRow"><span class="pinDot"></span><span class="teko"></span>'
    + '<button class="x" title="Close" aria-label="Close">×</button></div><p class="words"></p><span class="state"></span>'
    + '<div class="tagButtons teko"><button class="sk"><span>Take it back</span></button></div>';
  el.querySelector('.pinDot').textContent = x.n;
  el.querySelector('.teko').textContent = x.part.label || 'the car';
  el.querySelector('.words').textContent = x.text;
  el.querySelector('.state').textContent = [whereOf(x), stateOf(x)].filter(Boolean).join(' · ');
  el.querySelector('.x').addEventListener('click', () => tags.close());
  el.querySelector('.tagButtons .sk').addEventListener('click', () => post({ skin: skin.name, remove: x.n }).then(() => loadNotes(true)));
}

function renderNew(el) {
  el.innerHTML = '<div class="tagRow"><span class="pinDot writing"></span><span class="teko"></span>'
    + '<button class="x" title="Cancel" aria-label="Cancel">×</button></div>'
    + '<textarea rows="3" placeholder="What do you want here?"></textarea>'
    + '<div class="tagButtons teko"><button class="sk acc"><span>Add note</span></button><button class="sk"><span>Cancel</span></button></div>'
    + '<span class="state">Claude reads it with your next message.</span>';
  el.querySelector('.pinDot').textContent = nextN;
  el.querySelector('.teko').textContent = writing.part.label || 'the car';
  const text = el.querySelector('textarea'), say = el.querySelector('.state');
  const add = () => addNote(text.value, say);
  text.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); add(); }  // Shift+Enter for a new line
    if (e.key === 'Escape') cancelNote();
  });
  const [ok, no] = el.querySelectorAll('.tagButtons .sk');
  ok.addEventListener('click', add);
  no.addEventListener('click', cancelNote);
  el.querySelector('.x').addEventListener('click', cancelNote);
  setTimeout(() => text.focus());
}

function drawNotes() {
  const list = notes.map((x) => ({
    key: `n${x.n}`, dot: String(x.n), dotClass: x.state, title: x.text,
    sig: JSON.stringify([x.text, x.state, x.part.label, whereOf(x)]),
    render: (el, open) => renderNote(el, x, open),
  }));
  if (writing) list.push({ key: 'new', dot: String(nextN), dotClass: 'writing', sig: `new ${nextN}`, render: renderNew, open: true });
  tags.set(list);
  $('stHint').hidden = list.length > 0 || picks();
  if (!stage) return;
  stage.drawings([...notes, ...(writing ? [writing] : [])].flatMap((x) => (x.drawn ? x.drawn.strokes : [])
    .map((points, k) => ({ points: points.map(toMetres), colour: x.drawn.mesh && x.drawn.mesh[k] ? PICK_COLOUR : undefined })))
    .concat(picking ? [picking.line, ...picking.ticks].map((points) => ({ points: points.map(toMetres), colour: PICK_COLOUR })) : []));
  stage.track([...notes.filter((x) => x.at).map((x) => ({ key: `n${x.n}`, at: x.at, normal: x.normal })),
    ...(writing ? [{ key: 'new', at: writing.at, normal: writing.normal }] : [])], tags.place);
}

function goToNote(key) {  // a click on a note's tag or dot
  const x = notes.find((n) => `n${n.n}` === key);
  if (x) look(x);
}

// A note's view: the car as the user saw it when they wrote it (its tag, or its place in the timeline).
export function look(x) {
  if (!x.view || !stage) return;
  const { mood, framing, ...view } = x.view;
  stage.mood(mood || 'day');
  moodShown(mood || 'day');
  stage.go(view);
}

const partOf = (id) => {
  const p = partInfo.get(id);
  return { id, label: p ? p.label : '', token: p ? p.line.split(' (')[0] : '' };
};

function startNote(id, hit) {  // a click on the car: the part under it, and the point for its dot (the lines drawn stay)
  writing = { part: partOf(id), at: hit.at, normal: hit.normal, drawn: writing ? writing.drawn : null };
  if (tags.openKey && tags.openKey !== 'new') tags.close();
  seen();
}

function seen() {  // the note on the car, and a picture of it as the user sees it now (at the click, or the last line drawn)
  drawNotes();
  writing.view = stage.camera();
  writing.picture = notePicture(writing.at, nextN).catch((err) => { console.error(err); return null; });
}

// A line drawn with the pen, in pieces (the viewer's onStroke): a new note, its dot halfway along the
// longest piece, or more lines for the note being written. Kept in cm, only where it bends.
function drew(pieces) {
  const lines = pieces.map((p) => ({ points: simplify(p.points.map(toCm), SIMPLER), parts: p.parts }));
  if (!writing) {
    const p = pieces.reduce((a, b) => (b.points.length > a.points.length ? b : a)), k = Math.floor(p.points.length / 2);
    writing = { part: partOf(p.parts[k]), at: p.points[k], normal: p.normals[k], drawn: { strokes: [], parts: [] } };
    if (tags.openKey && tags.openKey !== 'new') tags.close();
  }
  writing.drawn ||= { strokes: [], parts: [] };
  for (const l of lines) {
    writing.drawn.strokes.push(l.points);
    for (const id of l.parts) if (!writing.drawn.parts.some((q) => q.id === id)) writing.drawn.parts.push(partOf(id));
  }
  seen();
}

// Ramer-Douglas-Peucker in 3D: the points a line keeps so that none it drops is more than `tol` off it.
function simplify(pts, tol) {
  if (pts.length < 3) return pts;
  const keep = new Uint8Array(pts.length);
  keep[0] = keep[pts.length - 1] = 1;
  const todo = [[0, pts.length - 1]];
  while (todo.length) {
    const [a, b] = todo.pop();
    const A = pts[a], B = pts[b], ab = [B[0] - A[0], B[1] - A[1], B[2] - A[2]];
    const len2 = ab[0] ** 2 + ab[1] ** 2 + ab[2] ** 2;
    let far = -1, worst = tol;
    for (let k = a + 1; k < b; k++) {
      const ap = [pts[k][0] - A[0], pts[k][1] - A[1], pts[k][2] - A[2]];
      const t = len2 ? Math.max(0, Math.min(1, (ap[0] * ab[0] + ap[1] * ab[1] + ap[2] * ab[2]) / len2)) : 0;
      const d = Math.hypot(ap[0] - t * ab[0], ap[1] - t * ab[1], ap[2] - t * ab[2]);
      if (d > worst) { worst = d; far = k; }
    }
    if (far >= 0) { keep[far] = 1; todo.push([a, far], [far, b]); }
  }
  return pts.filter((_, k) => keep[k]);
}

function setPen(on) {
  pen = on;
  $('stPen').setAttribute('aria-pressed', String(on));
  drawMode();
}

async function setMesh(on) {
  meshOn = on;
  $('stMesh').setAttribute('aria-pressed', String(on));
  if (stage && !(await stage.mesh(on)) && on) {  // no template built yet
    meshOn = false;
    $('stMesh').setAttribute('aria-pressed', 'false');
  }
  if (meshOn) fetch('api/meshpath?set=Skin').catch(() => {});  // the model's lines made ready for the first click
  drawMode();
}

// Draw: by hand without the mesh (the viewer's pen), clicks on the mesh with it.
function drawMode() {
  if (stage) stage.pen(pen && !meshOn);
  if (!picks()) picking = null;
  $('stHint').textContent = pen && !meshOn
    ? 'Draw on the car where you mean: a line where you want a strip, a ring round something. Drag off the car to turn it; a click still pins a note.'
    : HINT;
  pickSays();
  drawNotes();
}

// ---- Draw with Mesh on: a line picked on the model's mesh ----

function pickSays(trouble) {
  $('stPick').hidden = !picks();
  if (!picks()) return;
  const p = picking, n = p ? p.clicks.length : 0;
  const length = p && p.line.length > 1 ? p.line.slice(1).reduce((t, q, k) => t + apart(q, p.line[k]), 0) : 0;
  $('stPick').querySelector('span').textContent = trouble
    || (!n ? 'Click the points your line goes through: each click lands on the nearest point where the mesh\'s lines '
      + 'cross. Between two points on one line, your line follows it; otherwise it runs straight across. Click the last '
      + 'point again, or Done, to finish; the first point to close a ring. Drag to turn the car.'
      : `${n} click${n > 1 ? 's' : ''}${length ? ` · ${Math.round(length)} cm` : ''}${p.closed ? ' · a ring' : ''}. `
      + 'Click the last point again, or Done, to finish.');
  for (const id of ['stPickDone', 'stPickUndo']) $(id).disabled = !n;
}

async function pick(id, hit) {  // a click on the car while picking
  const set = (partInfo.get(id) || {}).mesh || 'Skin', at = toCm(hit.at);
  if (set === 'Glass') return pickSays('The glass has no mesh to pick on: click the body.');
  if (picking && picking.set !== set) return pickSays('Keep the line on one map: the body, or the inner car, or the wheels.');
  picking ||= { set, clicks: [], hits: [], parts: [], line: [], ticks: [], closed: false };
  const p = picking, last = p.clicks[p.clicks.length - 1];
  if (last && apart(at, last) < PICK_SAME) return endPick();
  if (p.clicks.length > 2 && apart(at, p.clicks[0]) < PICK_RING) {
    p.closed = true;
    await route();
    return endPick();
  }
  p.clicks.push(at);
  p.hits.push(hit);
  if (!p.parts.includes(id)) p.parts.push(id);
  await route();
}

async function route() {  // the picked line's way through its clicks, from the tool
  const p = picking, n = ++routing;
  if (!p) return;
  if (!p.clicks.length) { p.line = []; p.ticks = []; pickSays(); drawNotes(); return; }
  const q = new URLSearchParams({ set: p.set, at: p.clicks.map((c) => c.join(',')).join(';'), closed: p.closed ? '1' : '0' });
  let trouble = '';
  try {
    const r = await fetch(`api/meshpath?${q}`, { cache: 'no-store' });
    const got = await r.json();
    if (n !== routing || picking !== p) return;
    if (r.ok) { p.line = got.points; p.ticks = got.ticks; } else {
      trouble = `That click can't be joined: ${got.error || r.status}`;
      p.clicks.pop();
      p.hits.pop();
      p.closed = false;
    }
  } catch (e) { trouble = `Couldn't reach the tool: ${e.message}`; }
  pickSays(trouble);
  drawNotes();
}

// The picked line into the note being written (a new one, its dot at the middle click), as a line drawn by hand is,
// with its clicks, so Claude paints that very line (tool/notes.py, drawn's mesh).
function endPick() {
  const p = picking;
  picking = null;
  if (p && p.line.length > 1) {
    const mid = p.hits[Math.floor(p.hits.length / 2)];
    if (!writing) {
      writing = { part: partOf(p.parts[0]), at: mid.at, normal: mid.normal, drawn: null };
      if (tags.openKey && tags.openKey !== 'new') tags.close();
    }
    const d = (writing.drawn ||= { strokes: [], parts: [] });
    d.mesh ||= [];
    while (d.mesh.length < d.strokes.length) d.mesh.push(null);
    d.strokes.push(p.line);
    d.mesh.push({ set: p.set, clicks: p.clicks, closed: p.closed });
    for (const id of p.parts) if (!d.parts.some((q) => q.id === id)) d.parts.push(partOf(id));
    seen();
  } else drawNotes();
  pickSays();
}

function undoPick() {
  if (!picking) return;
  picking.clicks.pop();
  picking.hits.pop();
  picking.closed = false;
  route();
}

function dropPick() {
  picking = null;
  pickSays();
  drawNotes();
}

// What the user sees in the car's box, the note's dot drawn on, for Claude (a JPEG data: URL).
async function notePicture(at, n) {
  const url = await stage.picture({ crop: 'inset' });
  try {
    const img = new Image();
    img.src = url;
    await img.decode();
    const c = document.createElement('canvas');
    c.width = img.width;
    c.height = img.height;
    const g = c.getContext('2d');
    g.drawImage(img, 0, 0);
    const b = box(), [p] = stage.project([at]);
    const k = img.width / ($('stStage').clientWidth - b.left - b.right);
    if (p.shown) {
      const x = (p.x - b.left) * k, y = (p.y - b.top) * k, r = 12 * k;
      g.beginPath();
      g.arc(x, y, r + 4 * k, 0, 2 * Math.PI);
      g.fillStyle = 'rgba(232, 255, 71, 0.3)';
      g.fill();
      g.beginPath();
      g.arc(x, y, r, 0, 2 * Math.PI);
      g.fillStyle = '#e8ff47';
      g.fill();
      g.fillStyle = '#0d0f12';
      g.font = `600 ${Math.round(16 * k)}px Teko, sans-serif`;
      g.textAlign = 'center';
      g.textBaseline = 'middle';
      g.fillText(String(n), x, y + 1.5 * k);
    }
    return c.toDataURL('image/jpeg', 0.85);
  } finally {
    URL.revokeObjectURL(url);
  }
}

async function addNote(value, say) {
  const text = value.trim();
  if (!text || !writing || !skin) return;
  const { picture, drawn, ...note } = writing;
  const lines = drawn && { strokes: drawn.strokes, parts: drawn.parts.map(({ token, label }) => ({ token, label })), mesh: drawn.mesh };
  const r = await post({ skin: skin.name, text, ...note, drawn: lines, picture: await picture });
  if (!r.ok) {
    say.textContent = `Couldn't keep it: ${(await r.json().catch(() => ({}))).error || r.status}`;
    return;
  }
  writing = null;
  await loadNotes(true);
}

function cancelNote() {
  writing = null;
  drawNotes();
}

// ---- following Claude's painting ----

function live() {  // what Claude is doing, for the line over the page (lab-car.js)
  const open = doc && doc.steps.find((s) => !s.textures);
  const text = !doc ? 'Not painted yet' : doc.painting ? (open ? `Claude is painting · ${open.name}` : 'Claude is painting')
    : doc.stamp ? `Painted ${ago(doc.stamp)}` : 'Made before the Lab';
  dispatchEvent(new CustomEvent('lab:status', { detail: { painting: !!(doc && doc.painting), text } }));
}

async function apply(next) {
  const before = doc;
  doc = next;
  live();
  if (!stage || !lastFrame()) return;
  await stage.dress(lastFrame().textures);
  if (doc.painting) {  // the car as it's being painted, turned as each step asks
    const step = lastFrame();
    if ((step.look || '') !== stageLook) {
      const l = lookOf(step);
      await stage.show(l.view, l.night);
      stageLook = step.look || '';
      moodShown(l.night ? 'night' : 'day');
    }
    return;
  }
  if (!before || before.painting) {  // opened, or just painted: from the front, by day
    await stage.show('front', false);
    moodShown('day');
    stageLook = '';
  }
}

async function load(name) {
  const res = await fetch(`data/skins/${encodeURIComponent(name)}/steps.json`, { cache: 'no-store' });
  if (res.ok) return res.json();
  // painted before the Lab kept its steps: the whole design is one step
  const s = await fetch(`data/skins/${encodeURIComponent(name)}/skin.json`);
  if (!s.ok) return null;
  const sk = await s.json();
  return { name, stamp: 0, painting: false, steps: [{ name: 'The design', does: '', words: '', look: '', paints: [], line: `${name}: the design`, frame: `skin:${name}`, textures: sk.textures }] };
}

async function openSkin(name) {
  const list = await (await fetch('data/gallery.json', { cache: 'no-store' })).json();
  const entry = list.find((s) => s.name === name);
  skin = { name, title: entry ? entry.title : titleOf(name), entry };
  dispatchEvent(new CustomEvent('lab:stand', { detail: name }));
  doc = null; stageLook = '';
  notes = []; nextN = 1; writing = null;
  if (!stage) {
    stage = await embedViewer($('stCar'), $('stCredit'));
    if (stage) {
      stage.onPick = (id, hit) => (picks() ? pick(id, hit) : startNote(id, hit));
      stage.onStroke = drew;
      stage.pen(pen && !meshOn);
      if (meshOn) stage.mesh(true);
      $('stCar').contentWindow.addEventListener('keydown', keys);  // a click on the car gives it the keys
    }
    framed();
  }
  moodShown('day');
  drawNotes();
  loadNotes(true);
  const first = await load(name);
  if (first) await apply(first);
  else live();
}

async function poll() {
  if ($('roomStudio').hidden) return;  // another room is open
  loadNotes();  // Claude reads them (Claude has it) and marks them done (their dots go)
  try {
    const now = await followed();
    // a note being written, or a tag open, holds the car until it's done
    let fresh = false;
    if (now.stamp && now.stamp !== following && !writing && !tags.openKey) {
      following = now.stamp;
      fresh = true;
      if (!skin || now.skin !== skin.name) { note(now.skin); await openSkin(now.skin); return; }
    }
    if (!skin) return;  // opened before any skin was painted: waiting for Claude's first
    if (doc && !doc.stamp && !fresh) return;  // made before the Lab kept steps: nothing to ask for until Claude paints it
    const res = await fetch(`data/skins/${encodeURIComponent(skin.name)}/steps.json`, { cache: 'no-store' });
    if (res.ok) {
      const next = await res.json();
      if (!doc || next.stamp !== doc.stamp) await apply(next);
      else live();
    }
  } catch (e) { console.error(e); }
}

// A skin on the car: the car, or one of its options (the list), unless a note is being written.
export async function show(name) {
  if (!name || (skin && skin.name === name)) return;
  if (writing) cancelNote();
  if (tags.openKey) tags.close();
  note(name);
  await openSkin(name);
}

// The car the list is about, and how it names its options, for the notes' tags.
export function car(name, nameOf) {
  carName = name;
  if (nameOf) optionName = nameOf;
}

function keys(e) {
  if ($('roomStudio').hidden || /^(INPUT|TEXTAREA)$/.test(e.target.tagName || '')) return;
  if (picking && e.key === 'Enter') { e.preventDefault(); endPick(); return; }
  if (picking && e.key === 'Backspace') { e.preventDefault(); undoPick(); return; }
  if (e.key !== 'Escape') return;
  if (picking) dropPick();
  else if (writing) cancelNote();
  else if (tags.openKey) tags.close();
  else if (pen) setPen(false);
}

let opened = false;
export async function open() {
  if (opened) return;
  opened = true;
  tags = createTags({ stage: $('stStage'), lines: $('stLines'), dots: $('stDots'), tags: $('stTags'), list: $('stList'), gutter, onOpen: goToNote });
  for (const b of $('stMood').querySelectorAll('[data-mood]')) {
    b.addEventListener('click', () => { if (stage) { stage.mood(b.dataset.mood); moodShown(b.dataset.mood); } });
  }
  $('stGame').addEventListener('click', () => {  // the game's own chase camera (the viewer's Cam 1, as you drive)
    const cam = stage && stage.views()[0];
    if (cam) stage.go(cam.view);
  });
  HINT = $('stHint').textContent;
  $('stPen').addEventListener('click', () => setPen(!pen));
  $('stMesh').addEventListener('click', () => setMesh(!meshOn));
  $('stPickDone').addEventListener('click', endPick);
  $('stPickUndo').addEventListener('click', undoPick);
  $('stPickDrop').addEventListener('click', dropPick);
  addEventListener('keydown', keys);
  new ResizeObserver(framed).observe($('stStage'));
  const uv = await fetch('data/uvmap.json').then((r) => r.json()).catch(() => ({}));
  partInfo = new Map((uv.parts || []).map((p) => [p.id, p]));
  lift = (await fetch('data/car.json').then((r) => r.json()).catch(() => ({}))).lift_cm || 0;
  const now = await followed();
  following = now.stamp;
  let name = new URLSearchParams(location.search).get('skin') || now.skin;
  try { name ||= localStorage.getItem('tsc-viewer-skin'); } catch { /* no storage */ }
  try {
    if (name) await openSkin(name);
    else live();
  } finally {
    $('stCover').classList.add('off');  // the car dressed, framed and turned (or failed): shown
  }
  every(POLL, poll);  // follows Claude's painting, from the first skin painted
}
