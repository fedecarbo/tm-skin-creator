// The Lab's stand, its first room: the car a design builds, step by step, while Claude works on it,
// with the user's notes hanging on it as tags (the user's pick, B, of the factory mockups,
// 2026-09-27: CHECKLIST.md, "The Lab", step 9; before it, the Studio of steps 5 and 7). The car fills
// the room, framed between two gutters where the tags hang (lab-tags.js). Click the car where you
// mean and write what you want there: the note keeps the point, the part under it, the step, the
// view (a click on its tag turns the car back to it) and a picture of what the user saw, in
// .notes/notes.json through the viewer's server (tool/notes.py, /api/notes), and reaches Claude with
// the user's next message. Along the bottom: the build's steps, the game's cameras (the viewer's own
// Cam buttons, viewer.views) and the car in the game (gallery.json).
//   /lab.html                          the skin Claude painted last
//   /lab.html?skin=<name>              that skin (the viewer's "The Lab" link)
// Either way, when Claude starts painting a skin, the stand follows it, unless a note is being written
// or a tag is open. A take in a round of concepts shows the round's title and a switch between its
// takes (lab-round.js), which opens the picked take at the same step.
// Everything comes from the tool: tool.skin show paints a design step by step (paintbox.Skin.step)
// and writes each step's frame and skins/<name>/steps.json (tool/view.py, export_steps), and
// studio.json, the skin it painted last. The page asks for both every 1.5 s, so the strip fills in
// while a design is being painted. Both cars are the viewer itself (?embed=1): the stage, and a
// second one behind it at half its size and the same shape, which draws the strip's pictures. This
// browser keeps each picture (by its frame's hash and its view), so the second car starts only when
// one is missing: the first visit after Claude paints, not every visit.

import { note, render, wanted } from './lab-round.js';
import { createTags } from './lab-tags.js';

const $ = (id) => document.getElementById(id);
const POLL = 1500;

let skin = null;          // { name, title, entry: gallery.json's }
let doc = null;           // steps.json
let picked = -1;
let stage = null, thumbs = null;  // the two viewers' window.viewer (the second once a picture is missing)
let thumbsStart = null;
let seen = {};            // step -> frame, when this browser last saw the skin: newer ones are New
let changed = new Set();
const pics = new Map();   // frame (and view) -> picture URL
let queue = Promise.resolve();
let stageLook = '';
let following = null;     // studio.json's stamp when last read: a new one means Claude started a skin
let notes = [], nextN = 1;  // the skin's notes not done yet (tool/notes.py), and the next one's number
let writing = null;       // the note being written: { part, at, normal, step, step_name, view, picture }
let partInfo = new Map(); // uvmap.json's parts by id, to name the part under a click
let cams = [];            // the game's cameras, as the viewer names them: [{ view, label, title }]
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
const when = (iso) => new Date(iso).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });

// ---- the stage: the car framed between the gutters, a second car behind it for the pictures ----

const gutter = () => (matchMedia('(max-width: 1000px)').matches ? 0 : innerWidth <= 1280 ? 250 : 300);
const box = (k = 1) => ({ left: gutter() * k, right: gutter() * k, top: 10 * k, bottom: 10 * k });

function fitThumbs() {  // the picture car: half the stage, the same shape, so its pictures crop alike
  const r = $('stStage').getBoundingClientRect();
  Object.assign($('stThumbs').style, { width: `${Math.max(2, Math.round(r.width / 2))}px`, height: `${Math.max(2, Math.round(r.height / 2))}px` });
}

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

function framed() {  // the box each car frames itself in, after a resize
  fitThumbs();
  if (stage) stage.inset(box());
  if (thumbs) thumbs.inset(box(0.5));
  if (tags) tags.restack();
}

function pictureCar() {  // the second car, started the first time a picture isn't kept
  thumbsStart ||= viewer($('stThumbs')).then((v) => {
    thumbs = v;
    if (v) v.inset(box(0.5));
    return v;
  });
  return thumbsStart;
}

// The pictures this browser keeps (the Cache API), under the dates of the viewer's own files, so a
// change to how the car looks draws them afresh; the newest 400 are kept (about 15 MB).
const KEEP = 'tsc-lab-pictures', MOST = 400;
let kept = null;
function keeper() {
  kept ||= (async () => {
    if (!window.caches) return null;  // an address other than this computer's (a phone on the network)
    const dates = await Promise.all(['viewer.js', 'studio.js'].map((f) =>
      fetch(f, { method: 'HEAD' }).then((r) => r.headers.get('last-modified') || '')));
    const name = `${KEEP} ${dates.join(' ')}`;
    for (const k of await caches.keys()) if (k.startsWith(KEEP) && k !== name) await caches.delete(k);
    const c = await caches.open(name);
    const all = await c.keys();
    for (const r of all.slice(0, Math.max(0, all.length - MOST))) await c.delete(r);
    return c;
  })().catch(() => null);
  return kept;
}

// A picture of the car in a frame's textures (frame: its hash, from the paint box), drawn once and
// kept. A skin painted before the Studio has no hash: drawn each visit, never kept.
function picture(frame, textures, view, night) {
  const key = `${frame}|${typeof view === 'string' ? view : JSON.stringify(view)}|${night ? 'night' : 'day'}`;
  if (pics.has(key)) return Promise.resolve(pics.get(key));
  const job = queue.then(async () => {
    if (pics.has(key)) return pics.get(key);
    const shelf = /^[0-9a-f]{12}$/.test(frame) ? await keeper() : null;
    const at = `${location.origin}/lab-pictures/${encodeURIComponent(key)}`;
    let blob = shelf ? await shelf.match(at).then((r) => r && r.blob()).catch(() => null) : null;
    if (!blob) {
      const car = await pictureCar();
      if (!car) throw new Error('the picture car didn\'t start');
      await car.dress(textures);
      await car.show(view, night);
      const drawn = await car.picture({ crop: 'inset' });
      blob = await (await fetch(drawn)).blob();
      $('stThumbs').contentWindow.URL.revokeObjectURL(drawn);
      if (shelf) await shelf.put(at, new Response(blob, { headers: { 'Content-Type': 'image/jpeg' } })).catch(() => {});
    }
    const url = URL.createObjectURL(blob);
    pics.set(key, url);
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
    moodShown(l.night ? 'night' : 'day');
  }
}

function moodShown(m) {
  $('stand').classList.toggle('night', m === 'night');
  for (const b of $('stMood').querySelectorAll('[data-mood]')) b.setAttribute('aria-pressed', String(b.dataset.mood === m));
}

// ---- the strip: the build's steps, the game's cameras, the car in the game ----

function still(label, cls = '') {
  const b = document.createElement('button');
  b.className = `still ${cls}`;
  b.innerHTML = '<img alt=""><div class="fn teko"><span></span></div>';
  b.querySelector('.fn span').textContent = label;
  return b;
}
const gap = () => Object.assign(document.createElement('span'), { className: 'gap' });

function strip() {
  const box = document.createElement('div'), side = document.createElement('div');
  box.className = 'steps';
  side.className = 'side';
  $('stStrip').replaceChildren(box, gap(), side);
  doc.steps.forEach((step, k) => {
    const b = still(step.name, step.textures ? 'step' : 'step wip');
    b.setAttribute('aria-current', String(k === picked));
    b.insertAdjacentHTML('afterbegin', `<span class="k teko">${k}</span>`);
    if (!step.textures) b.querySelector('.fn').insertAdjacentHTML('beforeend', ' <small>painting…</small>');
    else if (changed.has(k)) b.querySelector('.fn').insertAdjacentHTML('beforeend', ' <em class="newTag">New</em>');
    if (step.textures) {
      b.addEventListener('click', () => pick(k));
      const l = lookOf(step);
      picture(step.frame, step.textures, l.view, l.night).then((url) => { b.querySelector('img').src = url; }).catch((e) => console.error(e));
    }
    box.append(b);
  });
  const last = [...doc.steps].reverse().find((s) => s.textures);
  if (cams.length && last) {  // the game's cameras, on the car as built so far
    for (const c of cams) {
      const b = still(c.label, 'cam');
      b.title = c.title;
      b.addEventListener('click', () => stage && stage.go(c.view));
      picture(last.frame, last.textures, c.view, false).then((url) => { b.querySelector('img').src = url; }).catch((e) => console.error(e));
      side.append(b);
    }
  }
  const e = skin.entry;
  const game = still('In the game', 'plain');
  game.querySelector('.fn').insertAdjacentHTML('beforeend', `<br><small>${e && e.installed_at ? `since ${when(e.installed_at)}` : 'not yet'}</small>`);
  if (e && e.installed && e.thumb) game.querySelector('img').src = `data/${e.thumb}`;
  side.append(game);
}

function pick(k) {
  picked = k;
  const step = doc.steps[k], n = doc.steps.length;
  $('stStrip').querySelectorAll('.still.step').forEach((b, i) => {
    b.setAttribute('aria-current', String(i === k));
    if (i === k) b.scrollIntoView({ block: 'nearest', inline: 'nearest' });
  });
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

// ---- notes on the car, as tags ----

const post = (body) => fetch('api/notes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });

async function loadNotes(force = false) {
  if (!skin) return;
  const name = skin.name;
  try {
    const r = await fetch(`api/notes?skin=${encodeURIComponent(name)}`, { cache: 'no-store' });
    if (!r.ok || !skin || skin.name !== name) return;
    const got = await r.json();
    if (!force && JSON.stringify(got.notes) === JSON.stringify(notes) && got.next === nextN) return;
    notes = got.notes;
    nextN = got.next;
  } catch { return; }  /* a server from before the notes */
  drawNotes();
}

const stateOf = (x) => (x.state === 'sent' ? 'Claude has it' : 'Goes to Claude with your next message');

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
  el.querySelector('.state').textContent = [x.step_name && `At ${x.step_name}`, stateOf(x)].filter(Boolean).join(' · ');
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
    key: `n${x.n}`, dot: String(x.n), dotClass: x.state, title: x.text, note: x,
    sig: JSON.stringify([x.text, x.state, x.part.label, x.step_name]),
    render: (el, open) => renderNote(el, x, open),
  }));
  if (writing) list.push({ key: 'new', dot: String(nextN), dotClass: 'writing', sig: `new ${nextN}`, render: renderNew, open: true });
  tags.set(list);
  $('stHint').hidden = list.length > 0;
  if (!stage) return;
  stage.track([...notes.filter((x) => x.at).map((x) => ({ key: `n${x.n}`, at: x.at, normal: x.normal })),
    ...(writing ? [{ key: 'new', at: writing.at, normal: writing.normal }] : [])], tags.place);
}

function goToNote(key) {  // a click on a note's tag or dot: the car as the user saw it when they wrote it
  const x = notes.find((n) => `n${n.n}` === key);
  if (!x || !x.view || !stage) return;
  const { mood, framing, ...view } = x.view;
  stage.mood(mood || 'day');
  moodShown(mood || 'day');
  stage.go(view);
}

function startNote(id, hit) {  // a click on the car: the part under it, and the point for its dot
  const p = partInfo.get(id);
  const step = doc && picked >= 0 ? doc.steps[picked] : null;  // what the user was looking at, now
  writing = { part: { id, label: p ? p.label : '', token: p ? p.line.split(' (')[0] : '' }, at: hit.at, normal: hit.normal,
              step: step ? picked : null, step_name: step ? step.name : '', view: stage.camera() };
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
  skin = { name, title: entry ? entry.title : titleOf(name), entry };
  const round = await render($('stRound'), name);
  $('stTitle').textContent = round ? round.title : skin.title;
  try { seen = JSON.parse(localStorage.getItem(`tsc-studio-${name}`) || '{}'); } catch { seen = {}; }
  doc = null; picked = -1; changed = new Set(); stageLook = '';
  notes = []; nextN = 1; writing = null;
  if (!stage) {
    fitThumbs();
    stage = await viewer($('stCar'));
    if (stage) {
      stage.onPick = startNote;
      cams = stage.views();
      const credit = $('stCar').contentDocument.getElementById('credit');
      if (credit) $('stCredit').innerHTML = credit.innerHTML;  // the car model's licence asks for it
    }
    framed();
  } else if (stage) {
    await stage.show('front', false);  // a step's own look (the rear at night) mustn't carry over
  }
  moodShown('day');
  drawNotes();
  loadNotes(true);
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
  if ($('roomStudio').hidden) return;  // another room is open
  loadNotes();  // Claude reads them (Claude has it) and marks them done (their dots go)
  try {
    const now = await followed();
    // a note being written, or a tag open, holds the car until it's done
    let fresh = false;
    if (now.stamp && now.stamp !== following && !writing && !tags.openKey) {
      following = now.stamp;
      fresh = true;
      if (skin && now.skin !== skin.name) { note(now.skin); await openSkin(now.skin); return; }
    }
    if (doc && !doc.stamp && !fresh) return;  // made before the Studio: nothing to ask for until Claude paints it
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
  tags = createTags({ stage: $('stStage'), lines: $('stLines'), dots: $('stDots'), tags: $('stTags'), list: $('stList'), gutter, onOpen: goToNote });
  for (const b of $('stMood').querySelectorAll('[data-mood]')) {
    b.addEventListener('click', () => { if (stage) { stage.mood(b.dataset.mood); moodShown(b.dataset.mood); } });
  }
  $('stFront').addEventListener('click', () => stage && stage.go('front'));
  addEventListener('keydown', (e) => {
    if (e.key !== 'Escape' || $('roomStudio').hidden) return;
    if (writing) cancelNote();
    else if (tags.openKey) tags.close();
  });
  new ResizeObserver(framed).observe($('stStage'));
  fetch('data/uvmap.json').then((r) => r.json()).then((d) => { partInfo = new Map(d.parts.map((p) => [p.id, p])); }).catch(() => {});
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
