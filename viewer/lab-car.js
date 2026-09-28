// The Lab's car room, the fresh layouts' A (the user's pick, 2026-09-28: CHECKLIST.md, "The design
// studio", W3; the mockups: https://claude.ai/artifact/MWqNtBfhErGaBCLy9Sevb6). The car fills the room
// (lab-studio.js: the car and the user's notes on it), and a list on the right holds whatever Claude
// offers (the user: "a place where I can pick options as I go ... can we try 3 different materials for
// X ... a few concepts for the wheels, or anything in a non linear way"): the car's sets of options,
// newest on top, a set being painted as such, then the earlier picks, small. A click on an option puts
// it on the car; its Pick, or a few words about it, go to Claude through the notes channel (/api/notes,
// tool/notes.py, with `answer`) and reach it at once while it waits (tool.notes wait). Over the page:
// the car's name (a menu of the cars, the materials, the UV map), whether it's in the game, and what
// Claude is doing. Everything comes from the tool: the sets are skins/<car>/sets.json (tool/sets.py, its
// only writer, served as /api/sets?skin=<name>: the car the skin is, or is an option of), an option's
// picture its gallery thumb, an earlier pick's the one the pick kept (/sets/<car>/<n>/<letter>.png).
//   /lab.html?skin=<name>    the car <name> is or is an option of, <name> on the car

const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => Object.assign(document.createElement(tag), cls ? { className: cls } : {}, text != null ? { textContent: text } : {});
const POLL = 2000;

let lab = null;           // lab.js: open another room
let stand = null;         // lab-studio.js
let car = null;           // /api/sets: { car, title, skin, option, sets (newest first), states }
let carSig = '';
let onCar = null;         // the skin on the car ('lab:stand')
let status = null;        // what Claude is doing ('lab:status')
let gallery = new Map();  // gallery.json by name: titles, thumbs, in the game
let answers = [];         // the car's answers in the list not done yet (notes with `answer`)
let answersSig = '';
let earlierOpen = null;   // the earlier picks shown (null: shown only when nothing waits)
const drafts = new Map(); // words typed about an option, kept while the list redraws

const post = (body) => fetch('api/notes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
const ago = (iso) => {
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  return s < 60 ? 'just now' : s < 3600 ? `${Math.round(s / 60)} min ago` : s < 86400 ? `${Math.round(s / 3600)} h ago`
    : s < 172800 ? 'yesterday' : new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
};
const when = (iso) => new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
const waiting = () => car ? car.sets.filter((s) => s.state === 'painting' || s.state === 'open') : [];
const optionOf = (skin) => { for (const s of car ? car.sets : []) for (const o of s.options) if (o.skin === skin) return { set: s, o }; return null; };
const thumbOf = (name) => { const e = gallery.get(name); return e && e.thumb ? `data/${e.thumb}?t=${Math.floor(e.stamp)}` : null; };

// ---- over the page: the car, in the game, Claude ----

function top() {
  if (!car) return;
  $('carName').querySelector('span').textContent = car.title;
  const e = gallery.get(car.car);
  $('gameLabel').querySelector('span').textContent = e && e.installed
    ? (e.installed_at ? `In the game since ${when(e.installed_at)}` : 'In the game') : 'Not in the game yet';
  const painting = status && status.painting;
  const open = waiting().some((s) => s.state === 'open');
  const busy = waiting().some((s) => s.state === 'painting');
  $('statusLabel').classList.toggle('on', !!(painting || open || busy));
  $('statusLabel').classList.toggle('quiet', !(painting || open || busy));
  $('statusLabel').querySelector('span').textContent = painting ? status.text
    : busy ? 'Claude is painting your options' : open ? 'Waiting for your pick' : (status && status.text) || '';
}

function menu() {  // the cars, newest first, then the other rooms
  const list = $('carList');
  list.replaceChildren();
  const cars = [...gallery.values()].filter((e) => !optionOf(e.name) || e.name === (car && car.car))
    .sort((a, b) => (b.made || 0) - (a.made || 0));
  for (const e of cars) {
    const b = el('button', null, e.title);
    b.setAttribute('role', 'menuitem');
    b.setAttribute('aria-current', String(car && e.name === car.car));
    b.addEventListener('click', () => { closeMenu(); stand.show(e.name); });
    list.append(b);
  }
}

function closeMenu() {
  $('carMenu').hidden = true;
  $('carName').setAttribute('aria-expanded', 'false');
}

// ---- the option on the car ----

function onTheCar() {
  const hit = onCar && car && onCar !== car.car ? optionOf(onCar) : null;
  $('stOn').hidden = !hit;
  if (hit) {
    $('stOn').querySelector('b').textContent = `${hit.o.key} · ${hit.o.title}`;
    $('stOn').querySelector('.s').textContent = hit.set.title;
  }
}

// ---- the list: for you to pick, then the earlier picks ----

function said(s) {  // the user's answers on the set, still with Claude
  const box = el('div');
  for (const a of answers.filter((x) => x.answer.set === s.n)) {
    const row = el('div', 'answer');
    const what = a.answer.pick ? `You picked ${a.answer.pick} · ${a.answer.title}` : `About ${a.answer.about || 'the set'}`;
    row.append(el('span', 'pinDot', String(a.n)), el('b', 'teko', what));
    if (a.text) row.append(el('span', 'quote', `“${a.text}”`));
    row.append(el('span', 'state', a.state === 'sent' ? 'Claude has it' : 'On its way to Claude'));
    if (a.state === 'new') {
      const back = el('button', 'sk teko');
      back.append(el('span', null, 'Take it back'));
      back.addEventListener('click', () => post({ skin: car.car, remove: a.n }).then(loadAnswers));
      row.append(back);
    }
    box.append(row);
  }
  return box.children.length ? box : null;
}

function option(s, o) {
  const pending = [...answers].reverse().find((a) => a.answer.set === s.n && a.answer.pick);
  const shown = o.skin === onCar;
  const b = el('div', `opt${shown ? ' on' : ''}`);
  b.setAttribute('role', 'button');
  b.tabIndex = 0;
  b.title = `${o.key} · ${o.title}: on the car`;
  const pic = el('span', 'pic');
  const src = thumbOf(o.skin);
  if (src) pic.append(Object.assign(el('img'), { src, alt: '' }));
  else pic.append(el('span', 'none', 'Being painted…'));
  const cap = el('span', 'cap');
  const t = el('span', 't teko');
  t.append(el('b', null, o.key), document.createTextNode(o.title));
  cap.append(t, el('span', 'grow'));
  if (shown) cap.append(el('span', 'tagOn teko', 'On the car'));
  if (s.state === 'open') {
    const p = el('button', `sk teko${shown || (pending && pending.answer.pick === o.key) ? ' acc' : ''}`);
    const mine = pending && pending.answer.pick === o.key;
    p.append(el('span', null, mine ? 'Your pick' : 'Pick'));
    p.setAttribute('aria-disabled', String(!!mine));
    p.addEventListener('click', (e) => {
      e.stopPropagation();
      if (!mine) answer(s, { pick: o.key, title: o.title }, pending);
    });
    cap.append(p);
  }
  b.append(pic, cap);
  const look = () => { if (src && !shown) stand.show(o.skin); };
  b.addEventListener('click', look);
  b.addEventListener('keydown', (e) => { if (e.key === 'Enter') look(); });
  return b;
}

function words(s, o) {  // a few words about the option on the car
  const key = `${s.n}${o.key}`;
  const box = el('div', 'say');
  const input = Object.assign(el('input'), { placeholder: `Say something about ${o.key}…`, value: drafts.get(key) || '' });
  input.autocomplete = 'off';
  const send = el('button', 'sk acc teko');
  send.append(el('span', null, 'Send'));
  const go = () => { if (input.value.trim()) answer(s, { about: o.key, title: o.title }, null, input.value.trim()).then(() => drafts.delete(key)); };
  input.addEventListener('input', () => drafts.set(key, input.value));
  input.addEventListener('keydown', (e) => { if (e.key === 'Enter') go(); });
  send.addEventListener('click', go);
  box.append(input, send);
  return box;
}

function past(s) {
  const box = el('div', 'past');
  box.append(el('h3', 'teko', s.title));
  const kept = s.options.find((o) => o.key === s.pick);
  box.append(el('p', null, s.state === 'dropped' ? `Set aside ${ago(s.done)}${s.decision ? `: ${s.decision}` : ''}`
    : `${kept ? `You picked ${kept.key} · ${kept.title}` : 'None kept'} · ${ago(s.done)}`));
  const row = el('div', 'row');
  for (const o of s.options) {
    const f = el('figure', o.key === s.pick ? 'on' : '');
    if (o.picture) f.append(Object.assign(el('img'), { src: `sets/${encodeURIComponent(car.car)}/${s.n}/${o.key}.png`, alt: o.title, title: `${o.key} · ${o.title}` }));
    f.append(el('figcaption', 'teko', o.key));
    row.append(f);
  }
  box.append(row);
  return box;
}

function list() {
  const box = $('picks');
  const active = document.activeElement && box.contains(document.activeElement) && document.activeElement.tagName === 'INPUT'
    ? document.activeElement.closest('.say') && document.activeElement.placeholder : null;
  box.replaceChildren();
  if (!car) return;
  const open = waiting();
  const h = el('h2', 'teko', 'For you to pick');
  if (open.length) h.append(el('small', null, String(open.length)));
  box.append(h);
  if (!open.length) {
    const e = el('div', 'empty');
    e.append(el('b', null, 'Nothing to pick right now.'),
      document.createTextNode('Ask Claude for a few ideas on anything, like “three materials for the sidepods”, and they land here.'));
    box.append(e);
  }
  for (const s of open) {
    const sec = el('section', 'set');
    const head = el('div', 'setHead');
    head.append(el('h3', 'teko', s.title), el('span', null, [s.words && `for “${s.words}”`, ago(s.made)].filter(Boolean).join(' · ')));
    sec.append(head);
    if (s.state === 'painting') {
      const busy = el('div', 'setBusy');
      busy.append(el('i'), el('span', null, s.options.length ? 'Claude is painting them' : 'Claude is working out the ideas'));
      sec.append(busy);
    }
    for (const o of s.options) {
      sec.append(option(s, o));
      if (o.skin === onCar) sec.append(words(s, o));
    }
    const a = said(s);
    if (a) sec.append(a);
    box.append(sec);
  }
  if (open.some((s) => s.state === 'open')) box.append(el('p', 'foot', 'A pick, or a few words, goes straight to Claude.'));
  const done = car.sets.filter((s) => s.state === 'picked' || s.state === 'dropped');
  if (done.length) {
    const wrap = el('div', 'earlier');
    const show = earlierOpen ?? !open.length;
    const t = el('button');
    const h2 = el('h2', 'teko', 'Earlier picks');
    h2.append(el('small', null, String(done.length)));
    t.append(h2, el('span', null, show ? '▾' : '▸'));
    t.setAttribute('aria-expanded', String(show));
    t.addEventListener('click', () => { earlierOpen = !show; list(); });
    wrap.append(t);
    if (show) for (const s of done) wrap.append(past(s));
    box.append(wrap);
  }
  if (active) {  // the words being typed keep their place
    const input = [...box.querySelectorAll('.say input')].find((i) => i.placeholder === active);
    if (input) { input.focus(); input.setSelectionRange(input.value.length, input.value.length); }
  }
}

function draw() {
  top();
  onTheCar();
  list();
}

// ---- the user's answers ----

async function answer(s, what, replacing = null, text = '') {
  if (replacing && replacing.state === 'new') await post({ skin: car.car, remove: replacing.n });
  const r = await post({ skin: car.car, text, answer: { set: s.n, name: s.title, pick: what.pick || null, about: what.about || null, title: what.title } });
  if (!r.ok) {
    const e = await r.json().catch(() => ({}));
    alert(`Couldn't send it: ${e.error || r.status}`);
    return;
  }
  await loadAnswers();
}

async function loadAnswers() {
  if (!car) return;
  try {
    const r = await fetch(`api/notes?skin=${encodeURIComponent(car.car)}`, { cache: 'no-store' });
    if (!r.ok) return;
    const got = (await r.json()).notes.filter((x) => x.answer);
    const sig = JSON.stringify(got);
    if (sig === answersSig) return;
    answersSig = sig;
    answers = got;
  } catch { return; }
  list();
}

// ---- the car's sets, followed ----

async function loadGallery() {
  try {
    const got = await (await fetch('data/gallery.json', { cache: 'no-store' })).json();
    gallery = new Map(got.map((e) => [e.name, e]));
  } catch { /* the pictures wait */ }
}

async function refresh() {
  if ($('roomStudio').hidden) return;
  const name = onCar || new URLSearchParams(location.search).get('skin');
  if (!name) { top(); return; }
  try {
    const r = await fetch(`api/sets?skin=${encodeURIComponent(name)}`, { cache: 'no-store' });
    if (!r.ok) return;
    const got = await r.json();
    const { skin, ...rest } = got;
    const sig = JSON.stringify(rest);
    if (sig !== carSig) {
      const other = !car || car.car !== got.car;
      carSig = sig;
      car = got;
      if (other) { answers = []; answersSig = ''; earlierOpen = null; }
      await loadGallery();
      stand.car(car.car, (n) => { const h = optionOf(n); return h ? `${h.o.key} · ${h.o.title}` : n; });
      menu();
      draw();
    } else {
      top();
      onTheCar();
    }
  } catch { return; }
  await loadAnswers();
}

let opened = false;
export async function open(from) {
  lab = from;
  if (opened) return refresh();
  opened = true;
  addEventListener('lab:stand', (e) => { onCar = e.detail; refresh(); onTheCar(); list(); });
  addEventListener('lab:status', (e) => { status = e.detail; top(); });
  $('stBack').addEventListener('click', () => { if (car) stand.show(car.car); });
  $('carName').addEventListener('click', (e) => {
    e.stopPropagation();
    const open = $('carMenu').hidden;
    $('carMenu').hidden = !open;
    $('carName').setAttribute('aria-expanded', String(open));
  });
  addEventListener('click', (e) => { if (!$('carMenu').hidden && !$('carMenu').contains(e.target)) closeMenu(); });
  addEventListener('keydown', (e) => { if (e.key === 'Escape') closeMenu(); });
  for (const b of $('carMenu').querySelectorAll('[data-go]')) b.addEventListener('click', () => { closeMenu(); lab.room(b.dataset.go); });
  stand = await import('./lab-studio.js');
  await stand.open();
  await refresh();
  setInterval(refresh, POLL);
  // ready once the list's pictures are in (Claude's snapshots of the page wait for it), 8 s at most
  const pics = [...$('picks').querySelectorAll('img')];
  await Promise.race([Promise.all(pics.map((i) => i.decode().catch(() => {}))), new Promise((r) => setTimeout(r, 8000))]);
  window.lab.ready = true;
}

