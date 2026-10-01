// The Lab's car room: the car fills it (lab-studio.js: the car and the user's notes on it), and beside
// it "With Claude", the car's timeline (the user's pick of the timeline's mockups, A, 2026-09-28:
// https://claude.ai/artifact/6nKpAWW1VFPfbrAZTfVZWM). Like an AI
// chat, newest at the bottom: the user's notes on the car and their words on the right, Claude's lines
// on the left, each set of options Claude offers as Claude's (a click puts an option on the car, a Pick
// on each), a pick and "In the game" as they happen. It opens at the bottom and follows what comes
// unless the user has scrolled up; the top fades while there's more above. The box under it sends the
// user's words to Claude, about the option on the car when one is. Picks and words go through the notes
// channel (/api/notes, tool/notes.py) and reach Claude at once while it waits (tool.notes wait), else
// with the user's next message. Over the page: the car's name (a menu of the cars, the materials, the
// UV map), whether it's in the game, and what Claude is doing. Everything comes from the tool:
// /api/sets?skin=<name> (tool/view.py): the car the skin is, or is an option of, its sets
// (skins/<car>/sets.json, tool/sets.py its only writer) and everything said about it (`said`:
// tool/notes.py's timeline(), Claude's lines by `tool.notes say` and `done --say`); an option's picture
// its gallery thumb, a decided set's the ones the pick kept (/sets/<car>/<n>/<letter>.png), a note's
// the one taken when it was written (/notes/<file>).
//   /lab.html?skin=<name>    the car <name> is or is an option of, <name> on the car

import { $, every, post } from './lab-common.js';

const el = (tag, cls, text) => Object.assign(document.createElement(tag), cls ? { className: cls } : {}, text != null ? { textContent: text } : {});
const POLL = 2000;
const STUCK = 40;  // px from the bottom that still counts as at the bottom

let lab = null;           // lab.js: open another room
let stand = null;         // lab-studio.js
let car = null;           // /api/sets: { car, title, skin, sets (newest first), said (in order) }
let carSig = '';
let onCar = null;         // the skin on the car ('lab:stand')
let status = null;        // what Claude is doing ('lab:status')
let gallery = new Map();  // gallery.json by name: titles, thumbs, in the game
let stick = true;         // the timeline follows what comes: the user is at the bottom

const when = (iso) => new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
const clock = (t) => new Date(t).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
const dayOf = (t) => {
  const d = new Date(t), today = new Date();
  const days = Math.round((new Date(today.toDateString()) - new Date(d.toDateString())) / 86400000);
  return days === 0 ? 'Today' : days === 1 ? 'Yesterday' : when(t);
};
const waiting = () => car ? car.sets.filter((s) => s.state === 'painting' || s.state === 'open') : [];
const optionOf = (skin) => { for (const s of car ? car.sets : []) for (const o of s.options) if (o.skin === skin) return { set: s, o }; return null; };
const optionName = (skin) => { const h = optionOf(skin); return h ? `${h.o.key} · ${h.o.title}` : null; };
const thumbOf = (name) => { const e = gallery.get(name); return e && e.thumb ? `data/${e.thumb}?t=${Math.floor(e.stamp)}` : null; };
const mine = () => car ? car.said.filter((x) => x.by !== 'claude') : [];

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

// ---- the option on the car, and what the box says it's about ----

function onTheCar() {
  const hit = onCar && car && onCar !== car.car ? optionOf(onCar) : null;
  $('stOn').hidden = !hit;
  if (hit) {
    $('stOn').querySelector('b').textContent = `${hit.o.key} · ${hit.o.title}`;
    $('stOn').querySelector('.s').textContent = hit.set.title;
  }
  $('sayText').placeholder = hit ? `Say something about ${hit.o.key} · ${hit.o.title}…` : 'Say something to Claude…';
}

// ---- the timeline ----

function who(name, t) {
  const w = el('div', 'who');
  w.append(el('span', 'teko', name), el('time', null, clock(t)));
  return w;
}

function stateOf(x) {  // a note of the user's on its way: where it stands, and a way to take it back
  if (x.state === 'done') return null;
  const box = el('div', 'state');
  box.append(el('span', null, x.state === 'sent' ? 'Claude has it' : 'On its way to Claude'));
  if (x.state === 'new') {
    const back = el('button', 'sk teko');
    back.append(el('span', null, 'Take it back'));
    back.addEventListener('click', (e) => { e.stopPropagation(); post({ skin: x.skin, remove: x.n }).then(refresh); });
    box.append(back);
  }
  return box;
}

function picture(src, cls) {
  const img = Object.assign(el('img', cls), { src, alt: '' });
  img.addEventListener('load', follow);  // a picture's height landing: still at the bottom
  return img;
}

function note(x) {  // a note on the car: its number, the part, what the user saw, their words
  const b = el('div', 'me note');
  const w = who('', x.made);
  w.firstChild.textContent = x.part.label || 'the car';
  w.prepend(el('span', 'pinDot', String(x.n)));
  b.append(w);
  if (x.picture) b.append(picture(x.picture, 'seen'));
  b.append(el('p', null, x.text));
  const on = x.skin !== car.car ? optionName(x.skin) || 'an option' : null;
  if (on) b.append(el('div', 'on', `On ${on}`));
  const st = stateOf(x);
  if (st) b.append(st);
  if (x.view) {  // the car turned back to where the user wrote it
    b.classList.add('go');
    b.title = 'Show the car as you saw it';
    b.addEventListener('click', () => stand.look(x));
  }
  return b;
}

function words(x) {  // the user's words: in the box, or a pick
  const b = el('div', 'me');
  b.append(who('You', x.made));
  if (x.answer) b.append(el('p', 'picked teko', `Pick: ${x.answer.pick} · ${x.answer.title}`));
  if (x.text) b.append(el('p', null, x.text));
  const on = !x.answer && x.skin !== car.car ? optionName(x.skin) || 'an option' : null;
  if (on) b.append(el('div', 'on', `About ${on}`));
  const st = stateOf(x);
  if (st) b.append(st);
  return b;
}

function claude(x) {
  const b = el('div', 'ai');
  b.append(who('Claude', x.made), el('p', null, x.text));
  return b;
}

function event(text, t) {
  const b = el('div', 'event');
  b.append(el('i'), el('span', null, text), el('time', null, clock(t)));
  return b;
}

function option(s, o) {  // an option waiting: a click puts it on the car, a Pick sends it
  const pending = [...mine()].reverse().find((a) => a.answer && a.answer.set === s.n && a.state !== 'done');
  const shown = o.skin === onCar;
  const b = el('div', `opt${shown ? ' on' : ''}`);
  b.setAttribute('role', 'button');
  b.tabIndex = 0;
  b.title = `${o.key} · ${o.title}: on the car`;
  const pic = el('span', 'pic');
  const src = thumbOf(o.skin);
  if (src) pic.append(picture(src));
  else pic.append(el('span', 'none', 'Being painted…'));
  const cap = el('span', 'cap');
  const t = el('span', 't teko');
  t.append(el('b', null, o.key), document.createTextNode(o.title));
  cap.append(t, el('span', 'grow'));
  if (shown) cap.append(el('span', 'tagOn teko', 'On the car'));
  if (s.state === 'open') {
    const picked = pending && pending.answer.pick === o.key;
    const p = el('button', `sk teko${shown || picked ? ' acc' : ''}`);
    p.append(el('span', null, picked ? 'Your pick' : 'Pick'));
    p.setAttribute('aria-disabled', String(!!picked));
    p.addEventListener('click', (e) => {
      e.stopPropagation();
      if (!picked) pick(s, o, pending);
    });
    cap.append(p);
  }
  b.append(pic, cap);
  const look = () => { if (src && !shown) stand.show(o.skin); };
  b.addEventListener('click', look);
  b.addEventListener('keydown', (e) => { if (e.key === 'Enter') look(); });
  return b;
}

function set(s) {  // a set of options, as Claude's
  const b = el('div', 'ai wide');
  b.append(who('Claude', s.made));
  const sec = el('section', 'set');
  const head = el('div', 'setHead');
  const kept = s.options.find((o) => o.key === s.pick);
  head.append(el('h3', 'teko', s.title), el('span', null, s.state === 'painting' ? ''
    : s.state === 'open' ? 'for you to pick' : s.state === 'dropped' ? 'set aside'
      : kept ? `you picked ${kept.key} · ${kept.title}` : 'none kept'));
  sec.append(head);
  if (s.state === 'painting') {
    const busy = el('div', 'setBusy');
    busy.append(el('i'), el('span', null, s.options.length ? 'Claude is painting them' : 'Claude is working out the ideas'));
    sec.append(busy);
  }
  if (s.state === 'painting' || s.state === 'open') {
    for (const o of s.options) sec.append(option(s, o));
  } else {  // decided: the pictures the pick kept, the pick outlined
    const row = el('div', 'past');
    for (const o of s.options) {
      const f = el('figure', o.key === s.pick ? 'on' : '');
      if (o.picture) f.append(Object.assign(el('img'), { src: `sets/${encodeURIComponent(car.car)}/${s.n}/${o.key}.png`, alt: o.title, title: `${o.key} · ${o.title}` }));
      f.append(el('figcaption', 'teko', o.key));
      row.append(f);
    }
    sec.append(row);
  }
  b.append(sec);
  return b;
}

// Everything in the order it happened: [time, voice, element]. Sets and installs keep local times,
// notes UTC; both read as dates.
function moments() {
  const out = [];
  for (const x of car.said) {
    const t = new Date(x.made).getTime();
    out.push(x.by === 'claude' ? [t, 'ai', () => claude(x)] : x.at ? [t, 'me', () => note(x)] : [t, 'me', () => words(x)]);
  }
  for (const s of car.sets) {
    const t = new Date(s.made).getTime();
    if (s.words) out.push([t - 1, 'me', () => words({ made: s.made, text: s.words, state: 'done', skin: car.car })]);
    out.push([t, 'ai', () => set(s)]);
    if (s.done && s.state === 'picked') {
      const kept = s.options.find((o) => o.key === s.pick);
      out.push([new Date(s.done).getTime(), 'event', () => event(kept ? `${kept.key} · ${kept.title} is the car now` : `${s.title}: none kept`, s.done)]);
    }
  }
  const e = gallery.get(car.car);
  if (e && e.installed_at) out.push([new Date(e.installed_at).getTime(), 'event', () => event('In the game', e.installed_at)]);
  return out.sort((a, b) => a[0] - b[0]);
}

function timeline() {
  const box = $('stream');
  const keep = box.scrollTop;
  box.replaceChildren();
  if (!car) return;
  const all = moments();
  if (!all.length) {
    const e = el('div', 'empty');
    e.append(el('b', null, 'Nothing here yet.'),
      document.createTextNode('Click the car to leave a note on it, or ask Claude for a few ideas on anything, like “three materials for the sidepods”, and they land here.'));
    box.append(e);
  }
  let day = '', voice = '';
  for (const [t, v, make] of all) {
    const d = dayOf(t);
    if (d !== day) { box.append(el('div', 'day', d)); day = d; voice = ''; }
    const node = make();
    if (v === 'me' && voice && voice !== 'me') node.classList.add('turn');  // a new exchange: room above it
    box.append(node);
    voice = v;
  }
  const live = el('div', 'live on');
  live.id = 'streamLive';
  live.append(el('i'), el('span'));
  box.append(live);
  painting();
  box.scrollTop = keep;
  follow();
}

function painting() {  // Claude at work, the last line of the timeline
  const live = $('streamLive');
  if (!live) return;
  live.hidden = !(status && status.painting);
  live.lastChild.textContent = status && status.painting ? status.text : '';
  follow();
}

function follow() {
  const box = $('stream');
  if (stick) box.scrollTop = box.scrollHeight;
  box.classList.toggle('above', box.scrollTop > 4);
}

function draw() {
  top();
  onTheCar();
  timeline();
}

// ---- the user's picks and words ----

async function pick(s, o, replacing) {
  if (replacing && replacing.state === 'new') await post({ skin: replacing.skin, remove: replacing.n });
  await send({ skin: car.car, text: '', answer: { set: s.n, name: s.title, pick: o.key, title: o.title } });
}

async function send(body) {
  const r = await post(body);
  if (!r.ok) {
    const e = await r.json().catch(() => ({}));
    alert(`Couldn't send it: ${e.error || r.status}`);
    return false;
  }
  stick = true;
  await refresh();
  return true;
}

async function say() {
  const input = $('sayText');
  const text = input.value.trim();
  if (!text || !car) return;
  if (await send({ skin: onCar || car.car, text })) input.value = '';
}

// ---- the car's timeline, followed ----

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
    await loadGallery();  // an option's picture as soon as it's painted, and the car put in the game
    const { skin, ...rest } = got;
    const names = [got.car, ...got.sets.flatMap((s) => s.options.map((o) => o.skin))];
    const sig = JSON.stringify([rest, names.map((n) => { const e = gallery.get(n); return e && [e.stamp, e.installed_at]; })]);
    if (sig === carSig) { top(); onTheCar(); return; }
    if (!car || car.car !== got.car) stick = true;
    carSig = sig;
    car = got;
    stand.car(car.car, (n) => optionName(n) || n);
    menu();
    draw();
  } catch { /* the server busy: the next poll */ }
}

let opened = false;
export async function open(from) {
  lab = from;
  if (opened) return refresh();
  opened = true;
  addEventListener('lab:stand', (e) => { onCar = e.detail; if (car) { onTheCar(); timeline(); } refresh(); });
  addEventListener('lab:status', (e) => { status = e.detail; top(); painting(); });
  $('stream').addEventListener('scroll', () => {
    const box = $('stream');
    stick = box.scrollHeight - box.scrollTop - box.clientHeight < STUCK;
    box.classList.toggle('above', box.scrollTop > 4);
  });
  $('saySend').addEventListener('click', say);
  $('sayText').addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); say(); } });
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
  every(POLL, refresh);
  // ready once the timeline's pictures are in (Claude's snapshots of the page wait for it), 8 s at most
  const pics = [...$('stream').querySelectorAll('img')];
  await Promise.race([Promise.all(pics.map((i) => i.decode().catch(() => {}))), new Promise((r) => setTimeout(r, 8000))]);
  follow();
  window.lab.ready = true;
}
