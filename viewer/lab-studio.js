// The Lab's stand, its first room: the car Claude builds, with the user's notes hanging on it as
// tags (the user's pick, B, of the factory mockups, 2026-09-27: CHECKLIST.md, "The Lab", step 9;
// before it, the Studio of steps 5 and 7). The car fills the room, framed between two gutters where
// the tags hang (lab-tags.js). Click the car where you mean and write what you want there: the note
// keeps the point, the part under it, the station and try on show, the view (a click on its tag
// turns the car back to it) and a picture of what the user saw, in .notes/notes.json through the
// viewer's server (tool/notes.py, /api/notes), and reaches Claude with the user's next message.
// Along the bottom, the stations (the user's pick, B, 2026-09-28: "shouldnt it be like main
// stations, like the body, the details, etc. And I guess each might have their iteration?"): Body,
// Details, Tyres and Glass, the game's four maps (tool/rooms.py, STATIONS), each with its tries, one
// for every show that changed its paint. The open station shows its tries; a click on one puts it on
// the car, with the other stations as they are now. Only the stations: the game's Cam 1 and 2 and the
// car in the game left the strip (the user, 2026-09-28: "I would remove cam 1 and 2 for now and
// remove the in game"); the line over the car says since when it's in the game (gallery.json).
//   /lab.html                          the skin Claude painted last
//   /lab.html?skin=<name>              that skin (the viewer's "The Lab" link)
// Either way, when Claude starts painting a skin, the stand follows it, unless a note is being written
// or a tag is open. A take in a round of concepts shows the round's title and a switch between its
// takes (lab-round.js), which opens the picked take at the same station.
// Everything comes from the tool: tool.skin show paints a design step by step (paintbox.Skin.step),
// writes each step's frame and skins/<name>/steps.json (tool/view.py, export_steps), then each
// station's new try (stations.json, export_stations), and studio.json, the skin it painted last.
// The page asks for steps.json and studio.json every 1.5 s: while Claude paints, the car on the
// stage shows each step as it's done, and the stations it changes say so. Both cars are the viewer
// itself (?embed=1): the stage, and a second one behind it at half its size and the same shape, which
// draws the strip's pictures. This browser keeps each picture (by its pictures' names and its view),
// so the second car starts only when one is missing: the first visit after Claude paints.

import { note, render, wanted } from './lab-round.js';
import { createTags } from './lab-tags.js';

const $ = (id) => document.getElementById(id);
const POLL = 1500;

let skin = null;          // { name, title, entry: gallery.json's }
let doc = null;           // steps.json: the frames of the last show, while it paints and after
let stations = [];        // tool/rooms.py's STATIONS, from uvmap.json: [{ key, name, set, view }]
let tries = {};           // station -> its tries, oldest first (stations.json; one, from the last frame, before it)
let triesKept = false;    // stations.json exists: the tries are the tool's, not made up here
let picked = null;        // the open station's key
let chosen = null;        // the try on the car at the open station (its n), or null for its newest
let stage = null, thumbs = null;  // the two viewers' window.viewer (the second once a picture is missing)
let thumbsStart = null;
let seen = {};            // station -> its newest try when this browser last saw the skin
let fresh = new Set();    // the stations with a try newer than this browser had seen: New
const pics = new Map();   // pictures' names, view and mood -> picture URL
let queue = Promise.resolve();
let stageLook = '';       // while Claude paints, the look of the step on the stage
let following = null;     // studio.json's stamp when last read: a new one means Claude started a skin
let notes = [], nextN = 1;  // the skin's notes not done yet (tool/notes.py), and the next one's number
let writing = null;       // the note being written: { part, at, normal, station, view, picture }
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
    frame.src = './index.html?embed=1';  // no skin: the stock car, dressed by the stand
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

function hash(s) {  // FNV-1a, two ways: a short name for a car's pictures
  let a = 0x811c9dc5, b = 0x9747b28c;
  for (let i = 0; i < s.length; i++) {
    const c = s.charCodeAt(i);
    a = Math.imul(a ^ c, 16777619);
    b = Math.imul(b ^ c, 2246822519);
  }
  return (a >>> 0).toString(16).padStart(8, '0') + (b >>> 0).toString(16).padStart(8, '0');
}
// Every picture named by what's in it (a frame's ?v=, a try's file, the stock): the car can be kept.
const named = (textures) => Object.values(textures).every((u) => !u || /\?v=|\/tries\/|^stock\//.test(u));

// A picture of the car in these textures ({slot: url}), drawn once and kept (a skin painted before
// the Studio has pictures without names: drawn each visit, never kept).
function picture(textures, view, night = false) {
  const key = `${hash(JSON.stringify(Object.entries(textures).sort()))}|${typeof view === 'string' ? view : JSON.stringify(view)}|${night ? 'night' : 'day'}`;
  if (pics.has(key)) return Promise.resolve(pics.get(key));
  const job = queue.then(async () => {
    if (pics.has(key)) return pics.get(key);
    const shelf = named(textures) ? await keeper() : null;
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

// ---- the stations and their tries ----

const lastFrame = () => doc && [...doc.steps].reverse().find((s) => s.textures);
const newest = (key) => { const l = tries[key] || []; return l[l.length - 1] || null; };
const stationOf = (key) => stations.find((s) => s.key === key);
const ownOf = (st, textures) => Object.entries(textures).filter(([slot]) => slot.startsWith(`${st.set}_`) && !slot.endsWith('_AO'));

// The car's textures: each station at its newest try (over the last frame, for the AO and anything
// without a try), and station `key` at try `n`.
function carWith(key = null, n = null) {
  const tex = { ...lastFrame().textures };
  for (const st of stations) { const t = newest(st.key); if (t) Object.assign(tex, t.textures); }
  const t = key && n && (tries[key] || []).find((x) => x.n === n);
  if (t) Object.assign(tex, t.textures);
  return tex;
}

// A skin shown before the stations: each painted station's one try, the last frame's.
function derive() {
  const out = {};
  for (const st of stations) {
    const slots = Object.fromEntries(ownOf(st, lastFrame().textures));
    out[st.key] = Object.values(slots).some((u) => u && !u.startsWith('stock/')) ? [{ n: 1, textures: slots }] : [];
  }
  return out;
}

// While Claude paints: the stations the frames so far have changed since their newest try.
function changing() {
  if (!triesKept) return new Set(stations.map((s) => s.key));
  const out = new Set(), tex = lastFrame() ? lastFrame().textures : {};
  for (const st of stations) {
    const sig = (newest(st.key) || {}).sig || {};
    for (const [slot, url] of ownOf(st, tex)) {
      const own = url && !url.startsWith('stock/') ? url.split('?v=')[1] || url : undefined;
      if (own !== sig[slot]) { out.add(st.key); break; }
    }
  }
  return out;
}

async function loadTries(name) {
  try {
    const r = await fetch(`data/skins/${encodeURIComponent(name)}/stations.json`, { cache: 'no-store' });
    if (r.ok) return (await r.json()).tries;
  } catch { /* none yet */ }
  return null;
}

const newestNs = () => Object.fromEntries(stations.map((s) => [s.key, (newest(s.key) || {}).n || 0]));
const isNew = (st) => fresh.has(st.key);
const shownTry = (st) => (st.key === picked && chosen) || (newest(st.key) || {}).n || null;

async function dressStage() {
  if (!stage || !lastFrame()) return;
  await stage.dress(doc.painting ? lastFrame().textures : carWith(picked, chosen));
}

function moodShown(m) {
  $('stand').classList.toggle('night', m === 'night');
  for (const b of $('stMood').querySelectorAll('[data-mood]')) b.setAttribute('aria-pressed', String(b.dataset.mood === m));
}

function label() {
  const st = stationOf(picked);
  if (!st) { $('stAt').textContent = ''; return; }
  const t = newest(st.key);
  $('stAt').innerHTML = '<span></span><small></small>';
  $('stAt').querySelector('span').textContent = st.name;
  $('stAt').querySelector('small').textContent = t ? `try ${shownTry(st)} of ${t.n}` : 'as it comes';
}

function pickStation(key, move = true) {
  const st = stationOf(key);
  if (!st) return;
  if (key !== picked) chosen = null;
  picked = key;
  const u = new URL(location.href);
  u.searchParams.set('station', key);
  history.replaceState(null, '', u);
  label();
  strip();
  dressStage().catch((e) => console.error(e));
  if (move && stage) stage.go(st.view);
}

function pickTry(key, n) {
  chosen = n === (newest(key) || {}).n ? null : n;
  label();
  strip();
  dressStage().catch((e) => console.error(e));
}

// ---- the strip: the stations, the game's cameras, the car in the game ----

function still(label, cls = '') {
  const b = document.createElement('button');
  b.className = `still ${cls}`;
  b.innerHTML = '<img alt=""><div class="fn teko"><span></span></div>';
  b.querySelector('.fn span').textContent = label;
  return b;
}
const show = (img) => (url) => { img.src = url; };

function strip() {
  const row = document.createElement('div');
  row.className = 'steps';
  $('stStrip').replaceChildren(row);
  if (!lastFrame()) return;
  const busy = doc.painting ? changing() : new Set();
  const car = carWith();
  for (const st of stations) {
    const list = tries[st.key] || [], open = st.key === picked, t = newest(st.key);
    const b = still(st.name, `step${open && list.length > 1 ? ' wide' : ''}${busy.has(st.key) ? ' wip' : ''}`);
    b.setAttribute('aria-current', String(open));
    const small = document.createElement('small');
    small.textContent = busy.has(st.key) ? 'painting…' : !t ? 'as it comes' : open ? `try ${shownTry(st)} of ${t.n}` : `try ${t.n}`;
    b.querySelector('.fn').append(' ', small);
    if (!busy.has(st.key) && isNew(st)) b.querySelector('.fn').insertAdjacentHTML('beforeend', ' <em class="newTag">New</em>');
    b.addEventListener('click', () => pickStation(st.key));
    if (open && list.length > 1 && !busy.has(st.key)) {  // its tries, each on the car as it is now
      const box = document.createElement('div');
      box.className = `tries${list.length > 4 ? ' many' : ''}`;
      b.querySelector('img').replaceWith(box);
      for (const x of list) {
        const f = document.createElement('figure');
        f.className = x.n === shownTry(st) ? 'on' : '';
        f.title = `Try ${x.n}${x.at ? `, ${when(x.at)}` : ''}`;
        f.innerHTML = '<img alt=""><figcaption class="teko"></figcaption>';
        f.querySelector('figcaption').textContent = x.n;
        f.addEventListener('click', (e) => { e.stopPropagation(); pickTry(st.key, x.n); });
        picture(carWith(st.key, x.n), st.view).then(show(f.querySelector('img'))).catch((e) => console.error(e));
        box.append(f);
      }
    } else if (!busy.has(st.key)) {
      picture(car, st.view).then(show(b.querySelector('img'))).catch((e) => console.error(e));
    }
    row.append(b);
  }
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
const whereOf = (x) => (x.station ? `At ${x.station.name}${x.station.try ? `, try ${x.station.try}` : ''}` : x.step_name && `At ${x.step_name}`);

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
    key: `n${x.n}`, dot: String(x.n), dotClass: x.state, title: x.text, note: x,
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
  // the station the part is painted at (its map), and the try on the car there now
  const st = (p && stations.find((s) => s.set === p.mesh)) || stationOf(picked);
  const station = st && { key: st.key, name: st.name, try: shownTry(st), latest: !(st.key === picked && chosen) };
  writing = { part: { id, label: p ? p.label : '', token: p ? p.line.split(' (')[0] : '' }, at: hit.at, normal: hit.normal,
              station, view: stage.camera() };
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
  // the car in the game: here since the strip dropped its tile (the user, 2026-09-28)
  const fresh = stations.filter(isNew).map((s) => s.name), e = skin.entry;
  const game = e && e.installed && e.installed_at ? ` · in the game since ${when(e.installed_at)}` : '';
  if (!doc.stamp) { text.textContent = `Made before the Studio${game}`; return; }
  text.textContent = `Painted ${ago(doc.stamp)}` + (fresh.length ? ` · new: ${fresh.join(', ')}` : '') + game;
}

async function apply(next) {
  const before = doc;
  doc = next;
  if (!doc.painting || !before) {  // the stations' tries (written before steps.json says it's done)
    const was = before ? newestNs() : seen;  // what this page had, or this browser's last visit
    const got = doc.stations ? await loadTries(skin.name) : null;  // shown before the stations: none kept
    triesKept = !!got;
    tries = got || (!doc.painting && lastFrame() ? derive() : {});
    if (before && before.painting) chosen = null;
    if (Object.keys(was).length) fresh = new Set(stations.filter((s) => (newest(s.key) || {}).n > (was[s.key] || 0)).map((s) => s.key));
  }
  if (!before) {
    const want = new URLSearchParams(location.search).get('station');
    picked = stationOf(want) ? want : stations.length ? stations[0].key : null;
  }
  strip();
  live();
  label();
  if (doc.painting) {  // the car as it's being painted, turned as each step asks
    const step = lastFrame();
    if (step && stage) {
      await stage.dress(step.textures);
      if ((step.look || '') !== stageLook) {
        const l = lookOf(step);
        await stage.show(l.view, l.night);
        stageLook = step.look || '';
        moodShown(l.night ? 'night' : 'day');
      }
    }
    return;
  }
  await dressStage();
  if (stage && (!before || before.painting)) {  // opened, or just painted: the open station's view, by day
    await stage.show(stationOf(picked) ? stationOf(picked).view : 'front', false);
    moodShown('day');
    stageLook = '';
  }
  try { localStorage.setItem(`tsc-stations-${skin.name}`, JSON.stringify(newestNs())); } catch {}
}

async function load(name) {
  const res = await fetch(`data/skins/${encodeURIComponent(name)}/steps.json`, { cache: 'no-store' });
  if (res.ok) return res.json();
  // painted before the Studio: the whole design is one step
  const s = await fetch(`data/skins/${encodeURIComponent(name)}/skin.json`);
  if (!s.ok) return null;
  const sk = await s.json();
  return { name, stamp: 0, painting: false, steps: [{ name: 'The design', does: 'Made before the Studio.', words: '', look: '', paints: [], line: `${name}: the design`, frame: `skin:${name}`, textures: sk.textures }] };
}

async function openSkin(name) {
  const list = await (await fetch('data/gallery.json')).json();
  const entry = list.find((s) => s.name === name);
  skin = { name, title: entry ? entry.title : titleOf(name), entry };
  const round = await render($('stRound'), name);
  $('stTitle').textContent = round ? round.title : skin.title;
  try { seen = JSON.parse(localStorage.getItem(`tsc-stations-${name}`) || '{}'); } catch { seen = {}; }
  doc = null; tries = {}; triesKept = false; chosen = null; stageLook = ''; fresh = new Set();
  notes = []; nextN = 1; writing = null;
  if (!stage) {
    fitThumbs();
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
      if (!doc || next.stamp !== doc.stamp) await apply(next);
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
  const uv = await fetch('data/uvmap.json').then((r) => r.json()).catch(() => ({}));
  partInfo = new Map((uv.parts || []).map((p) => [p.id, p]));
  stations = uv.stations || [];
  const now = await followed();
  following = now.stamp;
  let name = wanted() || now.skin;
  try { name ||= localStorage.getItem('tsc-viewer-skin'); } catch { /* no storage */ }
  if (!name) { $('stLiveText').textContent = 'No skin yet: ask Claude for one'; return; }
  try {
    await openSkin(name);
  } finally {
    $('stCover').classList.add('off');  // the car dressed, framed and turned (or failed): shown
  }
  addEventListener('lab:skin', (e) => openSkin(e.detail).catch((err) => console.error(err)));
  setInterval(poll, POLL);
  window.lab.studioReady = true;
}
