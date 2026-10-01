// The Lab's car (the user's pick of the fresh layouts, A, 2026-09-28: CHECKLIST.md, "The design studio",
// W3): the car being built fills the page, turned by a drag, by day or night or from the game's own
// camera, with the user's notes hanging on it as tags (lab-tags.js). Click the car where you mean and
// write what you want there: the note keeps the point, the part under it, the view (a click on its tag
// turns the car back to it) and a picture of what the user saw, in .notes/notes.json through the
// viewer's server (tool/notes.py, /api/notes), and reaches Claude with the user's next message (or at
// once, while Claude waits: tool.notes wait). Done, a note leaves the car and stays in the timeline
// beside it (lab-car.js), which also puts an option on the car to look at: its notes are that option's.
//   show(name)    a skin on the car: the car itself, or one of its options
//   look(note)    the car as the user saw it when they wrote the note
// Everything comes from the tool: tool.skin show paints a design step by step (paintbox.Skin.step),
// writes each step's frame and skins/<name>/steps.json (tool/view.py, export_steps), and studio.json,
// the skin it painted last. The page asks for both every 1.5 s: while Claude paints, the car shows
// each step as it's done, and it follows Claude to the skin it paints unless a note is being written
// or a tag is open. It says which skin it shows ('lab:stand') and what Claude is doing ('lab:status').
// The car is the viewer itself (index.html?embed=1).

import { note } from './lab-address.js';
import { createTags } from './lab-tags.js';

const $ = (id) => document.getElementById(id);
const POLL = 1500;

let skin = null;          // { name, title, entry: gallery.json's }: on the car
let carName = null;       // the car (lab-car.js), when the car shows one of its options
let optionName = (name) => name;  // an option's name as the list says it ("B · Magenta")
let doc = null;           // steps.json: the frames of the last show, while it paints and after
let stage = null;         // the viewer's window.viewer
let stageLook = '';       // while Claude paints, the look of the step on the stage
let following = null;     // studio.json's stamp when last read: a new one means Claude started a skin
let notes = [], nextN = 1;  // the skin's notes not done yet (tool/notes.py), and the next one's number
let writing = null;       // the note being written: { part, at, normal, view, picture }
let partInfo = new Map(); // uvmap.json's parts by id, to name the part under a click
let tags = null;          // lab-tags.js

const lookOf = (step) => {
  const words = (step.look || '').split(/\s+/);
  return { view: ['front', 'rear', 'left', 'right', 'top'].find((w) => words.includes(w)) || 'front', night: words.includes('night') };
};
const titleOf = (name) => name.replace(/^TSC_/, '').replaceAll('_', ' ').replace(/([a-z])(?=[A-Z])/g, '$1 ');
const ago = (t) => {
  const s = Math.max(0, Date.now() / 1000 - t);
  return s < 60 ? 'just now' : s < 3600 ? `${Math.round(s / 60)} min ago` : s < 86400 ? `${Math.round(s / 3600)} h ago` : `${Math.round(s / 86400)} days ago`;
};

// ---- the stage: the car framed between the gutters where its tags hang ----

// the gutters a fifth of the stage each, 200 to 300 px; none under 1000 px, where the tags are a list
const gutter = () => (matchMedia('(max-width: 1000px)').matches ? 0
  : Math.round(Math.min(300, Math.max(200, $('stStage').clientWidth * 0.2))));
const box = () => ({ left: gutter(), right: gutter(), top: 56, bottom: 10 });  // the top: the buttons over the car

function viewer(frame) {
  return new Promise((resolve) => {
    frame.addEventListener('load', () => {
      const wait = setInterval(() => {
        const v = frame.contentWindow && frame.contentWindow.viewer;
        if (!v || !(v.ready || v.error)) return;
        clearInterval(wait);
        resolve(v.error ? null : v);
      }, 150);
    }, { once: true });
    frame.src = './index.html?embed=1';  // no skin: no car until the first dress
  });
}

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

const post = (body) => fetch('api/notes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });

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
  $('stHint').hidden = list.length > 0;
  if (!stage) return;
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

function startNote(id, hit) {  // a click on the car: the part under it, and the point for its dot
  const p = partInfo.get(id);
  writing = { part: { id, label: p ? p.label : '', token: p ? p.line.split(' (')[0] : '' }, at: hit.at, normal: hit.normal,
              view: stage.camera() };
  if (tags.openKey && tags.openKey !== 'new') tags.close();
  drawNotes();
  writing.picture = notePicture(hit.at, nextN).catch((err) => { console.error(err); return null; });  // as seen at the click
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
  const { picture, ...note } = writing;
  const r = await post({ skin: skin.name, text, ...note, picture: await picture });
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
    stage = await viewer($('stCar'));
    if (stage) {
      stage.onPick = startNote;
      const credit = $('stCar').contentDocument.getElementById('credit');
      if (credit) $('stCredit').innerHTML = credit.innerHTML;  // the car model's licence asks for it
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

async function followed() {  // the skin Claude painted last: { skin, stamp }
  try {
    const r = await fetch('data/studio.json', { cache: 'no-store' });
    if (r.ok) return await r.json();
  } catch { /* none yet */ }
  return {};
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
  addEventListener('keydown', (e) => {
    if (e.key !== 'Escape' || $('roomStudio').hidden) return;
    if (writing) cancelNote();
    else if (tags.openKey) tags.close();
  });
  new ResizeObserver(framed).observe($('stStage'));
  const uv = await fetch('data/uvmap.json').then((r) => r.json()).catch(() => ({}));
  partInfo = new Map((uv.parts || []).map((p) => [p.id, p]));
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
  setInterval(poll, POLL);  // follows Claude's painting, from the first skin painted
}
