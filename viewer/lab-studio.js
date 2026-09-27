// The Lab's Studio: the car a design builds, step by step from clay, while Claude works on it.
// The car at the picked step, big; a filmstrip of the car at every step under it (layout B of the
// mockups the user chose on 2026-09-26); the user's notes beside it: click the car where you mean,
// write what you want there, and the note is pinned to that spot (C of the mockups of 2026-09-27,
// in place of the step's words and a line to copy). The notes live in skins/notes.json through the
// viewer's server (tool/notes.py, /api/notes), each with a picture of the stage as the user saw it,
// and reach Claude with the user's next message.
// CHECKLIST.md, "The Lab", steps 5 and 7.
//   /lab.html                          the skin Claude painted last
//   /lab.html?skin=<name>              that skin (the viewer's "The Lab" link)
// Either way, when Claude starts painting a skin, the Studio follows it. A take in a round of
// concepts shows the round's title and a switch between its takes (lab-round.js), which opens the
// picked take at the same step.
// Everything comes from the tool: tool.skin show paints a design step by step (paintbox.Skin.step)
// and writes each step's frame and skins/<name>/steps.json (tool/view.py, export_steps), and
// studio.json, the skin it painted last. The page asks for both every 1.5 s, so the filmstrip
// fills in while a design is being painted. Both cars are the viewer itself (?embed=1): one big,
// one hidden behind it that draws the filmstrip's pictures.

import { note, render, wanted } from './lab-round.js';

const $ = (id) => document.getElementById(id);
const POLL = 1500;

let skin = null;          // { name, title }
let doc = null;           // steps.json
let picked = -1;
let stage = null, thumbs = null;  // the two viewers' window.viewer
let seen = {};            // step -> frame, when this browser last saw the skin: newer ones are New
let changed = new Set();
const pics = new Map();   // frame -> picture URL
let queue = Promise.resolve();
let stageLook = '';
let following = null;     // studio.json's stamp when last read: a new one means Claude started a skin
let notes = [], nextN = 1;  // the skin's notes not done yet (tool/notes.py), and the next one's number
let writing = null;       // the note being written: { part: { id, label, token }, at, normal }
let partInfo = [];        // uvmap.json's parts by id, to name the part under a click

const lookOf = (step) => {
  const words = (step.look || '').split(/\s+/);
  return { view: ['front', 'rear', 'left', 'right', 'top'].find((w) => words.includes(w)) || 'front', night: words.includes('night') };
};
const titleOf = (name) => name.replace(/^TSC_/, '').replaceAll('_', ' ').replace(/([a-z])(?=[A-Z])/g, '$1 ');
const ago = (t) => {
  const s = Math.max(0, Date.now() / 1000 - t);
  return s < 60 ? 'just now' : s < 3600 ? `${Math.round(s / 60)} min ago` : s < 86400 ? `${Math.round(s / 3600)} h ago` : `${Math.round(s / 86400)} days ago`;
};

// ---- the two viewers ----

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
    frame.src = './index.html?embed=1';  // no skin: the stock car, dressed step by step
  });
}

function picture(step) {  // the filmstrip's picture of a step, drawn once per frame
  if (pics.has(step.frame)) return Promise.resolve(pics.get(step.frame));
  const job = queue.then(async () => {
    if (pics.has(step.frame)) return pics.get(step.frame);
    const look = lookOf(step);
    await thumbs.dress(step.textures);
    await thumbs.show(look.view, look.night);
    const url = await thumbs.picture();
    pics.set(step.frame, url);
    return url;
  });
  queue = job.catch(() => {});
  return job;
}

async function showOnStage(step) {
  if (!stage || !step.textures) return;
  await stage.dress(step.textures);
  const look = step.look || '';
  if (look !== stageLook) {  // a step with its own look turns the car; back to the front after it
    const l = lookOf(step);
    await stage.show(l.view, l.night);
    stageLook = look;
  }
}

// ---- the page ----

function strip() {
  const box = $('stStrip');
  box.textContent = '';
  doc.steps.forEach((step, k) => {
    const b = document.createElement('button');
    b.className = 'still' + (step.textures ? '' : ' wip');
    b.setAttribute('aria-current', String(k === picked));
    b.innerHTML = `<img alt=""><span class="k teko">${k}</span><div class="fn teko"><span></span></div>`;
    b.querySelector('.fn span').textContent = step.name;
    if (!step.textures) b.querySelector('.fn').insertAdjacentHTML('beforeend', ' <small>painting…</small>');
    else if (changed.has(k)) b.querySelector('.fn').insertAdjacentHTML('beforeend', ' <em class="newTag">New</em>');
    if (step.textures) {
      b.addEventListener('click', () => pick(k));
      if (thumbs) picture(step).then((url) => { b.querySelector('img').src = url; }).catch((e) => console.error(e));
    }
    box.append(b);
  });
}

function pick(k) {
  picked = k;
  const step = doc.steps[k], n = doc.steps.length;
  for (const [i, b] of [...$('stStrip').children].entries()) b.setAttribute('aria-current', String(i === k));
  $('stAt').innerHTML = '<span></span><small></small>';
  $('stAt').querySelector('span').textContent = step.name;
  $('stAt').querySelector('small').textContent = `step ${k} of ${n - 1}`;
  const params = new URLSearchParams(location.search);
  if (params.has('skin') || params.has('step')) {
    const u = new URL(location.href);
    u.searchParams.set('step', k);
    history.replaceState(null, '', u);
  }
  showOnStage(step).catch((e) => console.error(e));
}

// ---- notes on the car ----

const post = (body) => fetch('api/notes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });

async function loadNotes() {
  if (!skin) return;
  const name = skin.name;
  try {
    const r = await fetch(`api/notes?skin=${encodeURIComponent(name)}`, { cache: 'no-store' });
    if (!r.ok || !skin || skin.name !== name) return;
    const got = await r.json();
    if (JSON.stringify(got.notes) === JSON.stringify(notes) && got.next === nextN) return;
    notes = got.notes;
    nextN = got.next;
  } catch { return; }  /* a server from before the notes */
  drawNotes();
}

function drawNotes() {
  const box = $('ntList');
  box.textContent = '';
  for (const x of notes) {
    const row = document.createElement('div');
    row.className = 'note';
    row.innerHTML = '<span class="pinDot"></span><div class="nt"><span class="t"></span><small></small></div><button class="x" title="Take this note back" aria-label="Take this note back">×</button>';
    row.querySelector('.pinDot').textContent = x.n;
    row.querySelector('.t').textContent = x.text;
    row.querySelector('small').textContent = [x.part.label || 'the car', x.step_name && `at ${x.step_name}`, x.state === 'sent' && 'Claude has it'].filter(Boolean).join(' · ');
    row.querySelector('.x').addEventListener('click', () => post({ skin: skin.name, remove: x.n }).then(loadNotes));
    box.append(row);
  }
  $('ntCount').textContent = notes.length || '';
  $('ntAsk').hidden = !!writing;
  $('ntNew').hidden = !writing;
  $('ntNum').textContent = nextN;
  if (writing) $('ntPart').textContent = writing.part.label || 'the car';
  if (stage) stage.pins([...notes.map((x) => ({ n: x.n, at: x.at, normal: x.normal })),
    ...(writing ? [{ n: nextN, at: writing.at, normal: writing.normal, writing: true }] : [])]);
}

function startNote(id, hit) {  // a click on the car: the part under it, and the point for the pin
  const p = partInfo[id];
  writing = { part: { id, label: p ? p.label : '', token: p ? p.line.split(' (')[0] : '' }, at: hit.at, normal: hit.normal };
  drawNotes();
  $('ntText').focus();
}

// What the user sees on the stage, the note's pin drawn on, for Claude (a JPEG data: URL). The list
// stays words only (the user's pick, 2026-09-27).
async function notePicture() {
  const url = await stage.picture();
  try {
    const img = new Image();
    img.src = url;
    await img.decode();
    const c = document.createElement('canvas');
    c.width = img.width;
    c.height = img.height;
    const g = c.getContext('2d');
    g.drawImage(img, 0, 0);
    const frame = $('stCar');
    const pin = frame.contentDocument.querySelector('#pins .pin.writing');
    if (pin && !pin.hidden) {
      const k = img.width / frame.clientWidth;
      const x = parseFloat(pin.style.left) * k, y = parseFloat(pin.style.top) * k, r = 13 * k;
      g.beginPath();
      g.arc(x, y, r + 4 * k, 0, 2 * Math.PI);
      g.fillStyle = 'rgba(232, 255, 71, 0.3)';
      g.fill();
      g.beginPath();
      g.arc(x, y, r, 0, 2 * Math.PI);
      g.fillStyle = '#e8ff47';
      g.fill();
      g.fillStyle = '#0d0f12';
      g.font = `600 ${Math.round(17 * k)}px Teko, sans-serif`;
      g.textAlign = 'center';
      g.textBaseline = 'middle';
      g.fillText(String(nextN), x, y + 1.5 * k);
    }
    return c.toDataURL('image/jpeg', 0.85);
  } finally {
    URL.revokeObjectURL(url);
  }
}

async function addNote(e) {
  e.preventDefault();
  const text = $('ntText').value.trim();
  if (!text || !writing || !skin) return;
  const step = doc && picked >= 0 ? doc.steps[picked] : null;
  const picture = await notePicture().catch((err) => { console.error(err); return null; });
  const r = await post({ skin: skin.name, text, step: step ? picked : null, step_name: step ? step.name : '', ...writing, picture });
  if (!r.ok) {
    $('ntPart').textContent = `Couldn't keep it: ${(await r.json().catch(() => ({}))).error || r.status}`;
    return;
  }
  writing = null;
  $('ntText').value = '';
  await loadNotes();
  drawNotes();
}

function cancelNote() {
  writing = null;
  $('ntText').value = '';
  drawNotes();
}

function live() {
  const box = $('stLive'), text = $('stLiveText');
  const open = doc.steps.find((s) => !s.textures);
  box.classList.toggle('on', !!doc.painting);
  if (doc.painting) {
    text.textContent = open ? `Claude is painting · ${open.name}` : 'Claude is painting';
    return;
  }
  if (!doc.stamp) { text.textContent = 'Made before the Studio'; return; }
  const names = [...changed].map((k) => doc.steps[k] && doc.steps[k].name).filter(Boolean);
  text.textContent = `Painted ${ago(doc.stamp)}` + (names.length && names.length < doc.steps.length ? ` · changed ${names.join(', ')}` : '');
}

function apply(next) {
  const before = doc;
  doc = next;
  const was = before ? Object.fromEntries(before.steps.map((s, k) => [k, s.frame])) : seen;
  if (Object.keys(was).length) {
    changed = new Set(doc.steps.map((s, k) => (s.frame && s.frame !== was[k] ? k : -1)).filter((k) => k >= 0));
  }
  const params = new URLSearchParams(location.search);  // now: a take picked on the switch keeps the step
  const wantStep = Number(params.get('step'));
  const done = doc.steps.filter((s) => s.textures).length;
  if (!before && params.has('step') && doc.steps[wantStep] && doc.steps[wantStep].textures) picked = wantStep;
  else if (picked < 0 || picked >= done || (before && before.painting)) picked = Math.max(0, done - 1);
  strip();
  live();
  if (done) pick(picked);
  if (!doc.painting) {
    try { localStorage.setItem(`tsc-studio-${skin.name}`, JSON.stringify(Object.fromEntries(doc.steps.map((s, k) => [k, s.frame])))); } catch {}
  }
}

async function load(name) {
  const res = await fetch(`data/skins/${encodeURIComponent(name)}/steps.json`, { cache: 'no-store' });
  if (res.ok) return res.json();
  // painted before the Studio: the whole design is one step
  const s = await fetch(`data/skins/${encodeURIComponent(name)}/skin.json`);
  if (!s.ok) return null;
  const sk = await s.json();
  return { name, stamp: 0, painting: false, steps: [{ name: 'The design', does: 'Made before the Studio, so its steps weren\'t kept. The next time Claude paints it, they show here.', words: '', look: '', paints: [], line: `${name}: the design`, frame: `skin:${name}`, textures: sk.textures }] };
}

async function openSkin(name) {
  const list = await (await fetch('data/gallery.json')).json();
  const entry = list.find((s) => s.name === name);
  skin = { name, title: entry ? entry.title : titleOf(name) };
  const round = await render($('stRound'), name);
  $('stTitle').textContent = round ? round.title : skin.title;
  try { seen = JSON.parse(localStorage.getItem(`tsc-studio-${name}`) || '{}'); } catch { seen = {}; }
  doc = null; picked = -1; changed = new Set(); stageLook = '';
  notes = []; nextN = 1; writing = null;
  if (!stage) {
    [stage, thumbs] = await Promise.all([viewer($('stCar')), viewer($('stThumbs'))]);
    if (stage) stage.onPick = startNote;
  }
  drawNotes();
  loadNotes();
  const first = await load(name);
  if (first) apply(first);
  else $('stLiveText').textContent = 'Not shown in the viewer yet';
}

async function followed() {  // the skin Claude painted last: { skin, stamp }
  try {
    const r = await fetch('data/studio.json', { cache: 'no-store' });
    if (r.ok) return await r.json();
  } catch { /* none yet */ }
  return {};
}

async function poll() {
  loadNotes();  // Claude reads them (Claude has it) and marks them done (their pins go)
  try {
    const now = await followed();
    if (now.stamp && now.stamp !== following) {
      following = now.stamp;
      if (skin && now.skin !== skin.name) { note(now.skin); await openSkin(now.skin); return; }
    }
    const res = await fetch(`data/skins/${encodeURIComponent(skin.name)}/steps.json`, { cache: 'no-store' });
    if (res.ok) {
      const next = await res.json();
      if (!doc || next.stamp !== doc.stamp) apply(next);
      else live();
    }
  } catch (e) { console.error(e); }
}

let opened = false;
export async function open() {
  if (opened) return;
  opened = true;
  $('ntNew').addEventListener('submit', addNote);
  $('ntCancel').addEventListener('click', cancelNote);
  $('ntText').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) addNote(e);  // Shift+Enter for a new line
    if (e.key === 'Escape') cancelNote();
  });
  fetch('data/uvmap.json').then((r) => r.json()).then((d) => { partInfo = d.parts; }).catch(() => {});
  const now = await followed();
  following = now.stamp;
  let name = wanted() || now.skin;
  try { name ||= localStorage.getItem('tsc-viewer-skin'); } catch { /* no storage */ }
  if (!name) { $('stLiveText').textContent = 'No skin yet: ask Claude for one'; return; }
  await openSkin(name);
  addEventListener('lab:skin', (e) => openSkin(e.detail).catch((err) => console.error(err)));
  setInterval(poll, POLL);
  window.lab.studioReady = true;
}
