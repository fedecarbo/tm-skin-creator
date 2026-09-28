// The Lab's wizard (CHECKLIST.md, "The design studio", W3): a studio car's build sheet on the left, the
// step on show filling the page, with its question, its options, "Or tell Claude in your own words",
// Back and Next (the user's pick of the screens, 2026-09-28:
// https://claude.ai/artifact/JHwbvVDKNTCiHTGepPQB2F). A car made the old way has no sheet: it stays
// on the stand (lab-studio.js).
//   /lab.html?room=build&skin=<name>   the wizard of the studio car <name> is, or is an option of
//   ...&step=<key>                     that step on show
// Everything comes from the tool. The sheet is skins/<car>/sheet.json (tool/sheet.py, its only
// writer), served with the brief's card and each step's question (/api/sheet?skin=<name>, the
// studio car the skin belongs to: the Lab follows whichever skin Claude painted last, often an
// option). An option's picture is its gallery thumb (gallery.json), a mood board's its colour story
// and first drawing (tool/mood.py's boards.json). The page never changes the sheet: the user's answers
// (a pick, a yes, their words) go through the notes channel (/api/notes, tool/notes.py) with their
// step, and reach Claude with the next message, or at once while Claude waits for them (tool.notes
// wait). Claude writes the sheet, and the page follows it (asked every 2 s while the room is open).

import { note, pick as pickSkin } from './lab-round.js';

const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => Object.assign(document.createElement(tag), cls ? { className: cls } : {}, text != null ? { textContent: text } : {});
const POLL = 2000;

let doc = null;          // /api/sheet: the car's sheet, its card, `at` (the step it's at), `asks`, `states`
let docSig = '';
let shown = null;        // the step on show, or null to follow the car's step
let answers = [];        // the car's answers in the wizard not done yet (notes with `sheet`)
let answersSig = '';
let gallery = new Map(); // gallery.json's entries by name, for the options' thumbs
let boards = new Map();  // mood board file -> boards.json's board
let rooms = null;        // lab.js: open another room
let ask = null;          // the skin the page was asked for

const dateOf = (iso) => (iso ? new Date(`${iso}T12:00:00`).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' }) : '');
const stepOf = (key) => doc.steps.find((s) => s.key === key);
const indexOf = (key) => doc.steps.findIndex((s) => s.key === key);
const onShow = () => stepOf(shown || doc.at) || doc.steps[doc.steps.length - 1];
const picked = (st) => (st.pick || '').split('+').filter(Boolean);
const post = (body) => fetch('api/notes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });

// ---- the build sheet: one line per step, what was decided, the car so far ----

function tagOf(st) {
  if (st.state === 'waiting') return ['your turn', 'turn'];
  if (st.state === 'claude') return ['Claude on it', 'busy'];
  if (st.state === 'look') return ['needs a look', 'look'];
  if (st.state === 'decided' && st.was.length) return ['changed', 'changed'];
  return null;
}

function lineOf(st) {
  if (st.state === 'decided') return st.decision;
  if (st.state === 'skipped') return `skipped: ${st.why}`;
  if (st.state === 'look') return st.why || st.decision;
  if (st.state === 'waiting') return (st.options.length ? st.options.map((o) => `${o.key} ${o.title}`).join(', ') : doc.states.waiting);
  if (st.state === 'claude') return st.why || '';
  return '';
}

function drawSheet() {
  $('wzCar').textContent = doc.title;
  $('wzSub').textContent = `The studio · since ${dateOf(doc.started)}`;
  const list = $('wzSteps');
  list.replaceChildren();
  const now = onShow();
  doc.steps.forEach((st, i) => {
    const li = el('li', `${st.state}${st === now ? ' now' : ''}`);
    const b = el('button');
    const n = el('span', 'n teko');
    n.append(el('i', null, String(i + 1)), el('span', 'nm', st.name));
    const tag = tagOf(st);
    if (tag) n.append(el('em', tag[1], tag[0]));
    b.append(n, el('span', 'd', lineOf(st) || ' '));
    b.title = [st.name, lineOf(st)].filter(Boolean).join(': ');
    b.addEventListener('click', () => go(st.key));
    li.append(b);
    list.append(li);
  });
  const own = gallery.get(doc.car);
  const soFar = $('wzSoFar');
  soFar.hidden = !(own && own.thumb);
  if (own && own.thumb) {
    const src = `data/${own.thumb}?t=${Math.floor(own.stamp)}`;
    if (soFar.querySelector('img').getAttribute('src') !== src) soFar.querySelector('img').src = src;
  }
}

// ---- the step on show ----

function thumbOf(name) {
  const e = gallery.get(name);
  return e && e.thumb ? `data/${e.thumb}?t=${Math.floor(e.stamp)}` : null;
}

// An option as a card: a car's picture (its gallery thumb), or a mood board's colour story and first
// drawing; its letter and title; Pick while the step waits, or whether it was kept once decided.
function card(st, o) {
  const decided = st.state === 'decided' || st.state === 'look';
  const kept = picked(st).includes(o.key);
  const pending = [...answers].reverse().find((a) => a.sheet.step === st.key && a.sheet.pick);
  const c = el('div', `card${decided ? (kept ? ' on' : ' off') : pending && pending.sheet.pick === o.key ? ' on' : ''}`);
  const pic = el('div', 'pic');
  if (o.file) {
    const b = boards.get(o.file);
    if (b) {
      const story = el('div', 'story');
      const total = b.colours.reduce((s, x) => s + (x.share || 0), 0) || b.colours.length;
      for (const x of b.colours) {
        const i = el('i');
        i.style.cssText = `background:${x.hex};flex:${(x.share || total / b.colours.length) / total}`;
        i.title = x.name;
        story.append(i);
      }
      const w = b.wall.find((x) => x.wide) || b.wall[0];
      if (w) {
        const src = w.svg ? `data:image/svg+xml;charset=utf-8,${encodeURIComponent(w.svg)}` : w.picture;
        pic.append(Object.assign(el('img'), { src, alt: w.caption || '' }));
      }
      pic.classList.add('board');
      c.append(story);
      c.dataset.line = b.line;
    } else pic.append(el('span', 'none', decided && !kept ? 'Not kept' : 'Its board isn’t drawn yet'));
  } else {
    const src = thumbOf(o.skin);
    if (src) pic.append(Object.assign(el('img'), { src, alt: '' }));
    else pic.append(el('span', 'none', decided && !kept ? 'Not kept' : st.state === 'claude' || st.state === 'waiting' ? 'Being painted…' : 'No picture kept'));
    if (src && o.skin !== doc.car) {  // a look at it on the stand, where notes go on the car
      const look = el('button', 'sk teko look');
      look.append(el('span', null, 'On the car'));
      look.title = 'Open it on the stand, to turn it and leave notes on it';
      look.addEventListener('click', () => onTheCar(o.skin));
      pic.append(look);
    }
  }
  c.append(pic);
  if (c.dataset.line) c.append(el('p', 'line', c.dataset.line));
  const cap = el('div', 'cap');
  const t = el('span', 't teko');
  t.append(el('b', null, o.key), document.createTextNode(o.title));
  cap.append(t, el('span', 'grow'));
  if (decided) cap.append(el('span', 'kept teko', kept ? 'Picked' : 'Not kept'));
  else if (st.state === 'waiting') {
    const b = el('button', 'sk acc teko');
    b.append(el('span', null, pending ? (pending.sheet.pick === o.key ? 'Your pick' : 'Pick this instead') : 'Pick'));
    b.disabled = !!pending && pending.sheet.pick === o.key;
    b.setAttribute('aria-disabled', String(b.disabled));
    b.addEventListener('click', () => answer(st, { pick: o.key, title: o.title }, pending));
    cap.append(b);
  }
  c.append(cap);
  return c;
}

function cards(st) {
  const list = st.options.filter((o) => !(o.skin === doc.car && o.title === 'as it is' && st.state !== 'waiting' && st.state !== 'claude'));
  if (!list.some((o) => (o.file ? boards.has(o.file) : thumbOf(o.skin)))) {  // none kept a picture: their names only
    const row = el('div', 'offered');
    for (const o of list) {
      const kept = picked(st).includes(o.key);
      const x = el('span', `teko${kept ? ' on' : ''}`);
      x.append(el('b', null, o.key), document.createTextNode(o.title), el('small', null, kept ? 'picked' : st.state === 'decided' || st.state === 'look' ? 'not kept' : 'being made'));
      row.append(x);
    }
    return row;
  }
  const grid = el('div', 'cards');
  for (const o of list) grid.append(card(st, o));
  return grid;
}

// The car as it is now, for a step with no options to show (its gallery thumb), with a way to the stand.
function carNow(st) {
  const src = thumbOf(doc.car);
  if (!src || st.options.length && st.state !== 'decided') return null;
  const f = el('figure', 'carNow');
  f.append(Object.assign(el('img'), { src, alt: '' }), el('figcaption', 'teko', 'The car now'));
  const look = el('button', 'sk teko look');
  look.append(el('span', null, 'On the car'));
  look.title = 'Open it on the stand, to turn it and leave notes on it';
  look.addEventListener('click', () => onTheCar(doc.car));
  f.append(look);
  return f;
}

// The cards laid out so each option's picture is as big as the room allows: as many columns as make
// a car's 4:3 thumb biggest (a board's line and colour story take some of the height), side by side
// unless that's far smaller, and no taller than 5:6 of its width, so the picture keeps the whole car.
function fit() {
  const grid = $('wzBody').querySelector('.cards');
  if (!grid) return;
  grid.style.gridTemplateColumns = grid.style.gridTemplateRows = '';
  if (matchMedia('(max-width: 1000px)').matches) return;
  const n = grid.children.length, gap = 10, W = grid.clientWidth, H = grid.clientHeight;
  const extra = 46 + (grid.querySelector('.story') ? 70 : 0);
  let best = null;
  for (let cols = 1; cols <= n; cols++) {
    const rows = Math.ceil(n / cols);
    const w = (W - gap * (cols - 1)) / cols, h = (H - gap * (rows - 1)) / rows - extra;
    const size = Math.min(w / 4, h / 3) * (rows === 1 ? 1.25 : 1);  // side by side, unless far smaller
    if (!best || size > best.size + 0.5) best = { cols, rows, w, h, size };
  }
  grid.style.gridTemplateColumns = `repeat(${best.cols}, minmax(0, 1fr))`;
  grid.style.gridTemplateRows = `repeat(${best.rows}, ${Math.floor(Math.min(best.h, best.w * 5 / 6) + extra)}px)`;
}

function block(kicker, text, cls = '') {
  const b = el('div', `said ${cls}`);
  b.append(el('div', 'teko', kicker), el('p', null, text));
  return b;
}

function earlier(st) {
  if (!st.was.length) return null;
  const box = el('div', 'was');
  box.append(el('div', 'teko', 'Before'));
  for (const w of [...st.was].reverse()) {
    const kept = w.options.filter((o) => (w.pick || '').split('+').includes(o.key)).map((o) => `${o.key} ${o.title}`);
    box.append(el('p', null, `${dateOf(w.date)}: ${kept.length ? `${kept.join(' + ')}: ` : ''}${w.decision}`));
  }
  return box;
}

function brief(st) {
  const c = doc.card, box = el('div', 'brief');
  if (!c) {
    box.append(block('Your words', doc.words, 'quote'),
      block('Claude on it', 'Claude is reading your idea. The talk goes on in the chat; the brief’s card shows here once Claude has written it.', 'busy'));
    return box;
  }
  box.append(block('What it is', c.what, 'draft'));
  const from = el('div', 'bq from');
  from.append(el('div', 'teko', 'Drawn from'));
  const ul = el('ul');
  for (const d of c.drawn) {
    const li = el('li');
    if (d.name) li.append(el('b', null, d.name), document.createTextNode(`: ${d.gives}`));
    else li.textContent = d.gives;
    ul.append(li);
  }
  from.append(ul);
  const rules = el('div', 'bq rules');
  rules.append(el('div', 'teko', 'Not'));
  const no = el('div', 'pills');
  for (const x of c.not) no.append(el('span', 'no', x));
  rules.append(no, el('div', 'teko', 'Fixed'));
  const fixed = el('div', 'pills');
  for (const x of c.fixed) fixed.append(el('span', 'on', x));
  if (!c.fixed.length) fixed.append(el('span', null, 'Nothing'));
  rules.append(fixed);
  box.append(from, rules, block('Your words', c.words || doc.words, 'quote wide'));
  return box;
}

function body(st) {
  const box = $('wzBody');
  box.replaceChildren();
  box.dataset.step = st.key;
  if (st.key === 'brief') {
    box.append(brief(st));
    if (st.state === 'decided' && st.was.length) box.append(earlier(st));
    return;
  }
  if (st.state === 'todo') {
    const before = doc.steps[indexOf(st.key) - 1];
    if (st.key !== doc.at) {
      box.append(block('Not yet', `It comes after ${before ? before.name : 'the brief'}.`, 'quiet'));
      return;
    }
    box.append(block('Next', 'Claude starts this step next.', 'quiet'));  // the car's own step, not begun
  }
  if (st.state === 'decided' || st.state === 'look') box.append(block(`Decided ${dateOf(st.date)}`, st.decision, 'draft'));
  if (st.state === 'look') box.append(block('Needs a look', st.why || 'The car changed since.', 'lookout'));
  if (st.state === 'skipped') box.append(block(`Skipped ${dateOf(st.date)}`, st.why, 'quiet'));
  if (st.state === 'claude') {
    box.append(block('Claude on it', st.why ? `Going back: ${st.why}` : st.options.length
      ? 'The options appear here as they’re painted. You choose once they’re all done.'
      : 'Claude is working on this step, and shows it here when it’s done.', 'busy'));
  }
  if (st.options.length) box.append(cards(st));
  const h = earlier(st);
  if (h) box.append(h);
  const now = !box.querySelector('.cards') && carNow(st);
  if (now) box.append(now);
}

function head(st) {
  const i = indexOf(st.key), a = doc.asks[st.key] || {};
  const waits = st.state === 'waiting' || st.state === 'look';
  const kicker = `Step ${i + 1} of ${doc.steps.length}` + (st.key === doc.at ? '' : st.state === 'todo' ? ' · not yet' : ` · ${doc.states[st.state]}`);
  $('wzKicker').textContent = kicker;
  $('wzQuestion').textContent = waits ? a.question : st.key === 'brief' && st.state === 'claude' && !doc.card ? 'What car do you want to build?' : st.name;
  $('wzLine').textContent = waits ? a.line : st.state === 'claude' ? a.line || '' : '';
}

// What the user has answered at the step, still with Claude: a pick, a yes or words, and taking it back
// while Claude hasn't read it yet.
function said(st) {
  const box = $('wzSaid');
  const mine = answers.filter((a) => a.sheet.step === st.key);
  box.hidden = !mine.length;
  box.replaceChildren();
  for (const a of mine) {
    const row = el('div', 'answer');
    const what = a.sheet.pick ? `You picked ${a.sheet.pick}${a.sheet.title ? ` · ${a.sheet.title}` : ''}` : a.sheet.yes ? 'You said yes' : 'You wrote';
    row.append(el('span', 'pinDot', String(a.n)), el('b', 'teko', what));
    if (a.text) row.append(el('span', 'quote', `“${a.text}”`));
    row.append(el('span', 'state', a.state === 'sent' ? 'Claude has it' : 'Goes to Claude with your next message, or at once if Claude is waiting'));
    if (a.state === 'new') {
      const back = el('button', 'sk teko');
      back.append(el('span', null, 'Take it back'));
      back.addEventListener('click', () => post({ skin: doc.car, remove: a.n }).then(loadAnswers));
      row.append(back);
    }
    box.append(row);
  }
}

function foot(st) {
  const i = indexOf(st.key);
  const next = doc.steps[i + 1];
  const back = $('wzBack'), go = $('wzNext');
  back.setAttribute('aria-disabled', String(i === 0));
  const yes = (st.key === 'brief' && st.state === 'waiting') ? 'Approve the brief' : st.state === 'look' ? 'Keep it as it is' : null;
  const answered = answers.some((a) => a.sheet.step === st.key && (a.sheet.yes || a.sheet.pick));
  go.dataset.action = yes ? 'yes' : 'next';
  go.querySelector('span').textContent = yes ? (answered ? 'Sent' : yes) : 'Next';
  go.classList.toggle('acc', !!yes);
  go.setAttribute('aria-disabled', String(yes ? answered : !next || next.state === 'todo'));
  $('wzTell').placeholder = st.state === 'waiting' && st.options.length
    ? 'Or tell Claude in your own words: what to mix, what to change…' : 'Or tell Claude in your own words…';
}

function draw() {
  if (!doc) return;
  const st = onShow();
  drawSheet();
  head(st);
  body(st);
  said(st);
  foot(st);
  fit();
  const u = new URL(location.href);
  if (shown) u.searchParams.set('step', shown);
  else u.searchParams.delete('step');
  history.replaceState(null, '', u);
}

function go(key) {  // a step on show; the car's own step follows the car again
  shown = key === doc.at ? null : key;
  draw();
}

// ---- the user's answers ----

async function answer(st, what = {}, replacing = null) {
  const input = $('wzTell');
  const text = input.value.trim();
  if (!what.pick && !what.yes && !text) return;
  if (replacing && replacing.state === 'new') await post({ skin: doc.car, remove: replacing.n });
  const r = await post({ skin: doc.car, text, sheet: { step: st.key, name: st.name, pick: what.pick || null, title: what.title || '', yes: !!what.yes } });
  if (!r.ok) {
    const e = await r.json().catch(() => ({}));
    $('wzSaid').hidden = false;
    $('wzSaid').textContent = `Couldn't send it: ${e.error || r.status}`;
    return;
  }
  input.value = '';
  $('wzSend').hidden = true;
  await loadAnswers();
}

async function loadAnswers() {
  if (!doc) return;
  try {
    const r = await fetch(`api/notes?skin=${encodeURIComponent(doc.car)}`, { cache: 'no-store' });
    if (!r.ok) return;
    const got = (await r.json()).notes.filter((x) => x.sheet);
    const sig = JSON.stringify(got);
    if (sig === answersSig) return;
    answersSig = sig;
    answers = got;
  } catch { return; }
  draw();
}

// ---- the car's sheet, followed ----

async function loadGallery() {
  try {
    const list = await (await fetch('data/gallery.json', { cache: 'no-store' })).json();
    gallery = new Map(list.map((e) => [e.name, e]));
  } catch { /* the pictures wait */ }
}

async function loadBoards(car) {
  try {
    const r = await fetch(`data/mood/${encodeURIComponent(car)}/boards.json`, { cache: 'no-store' });
    if (!r.ok) return;
    boards = new Map((await r.json()).boards.map((b) => [`mood/${b.slug}.json`, b]));
  } catch { /* none yet */ }
}

// The sheet of the studio car `name` belongs to, or null (a car made the old way).
export async function sheetOf(name) {
  if (!name) return null;
  try {
    const r = await fetch(`api/sheet?skin=${encodeURIComponent(name)}`, { cache: 'no-store' });
    return r.ok ? await r.json() : null;
  } catch { return null; }
}

let following = null;  // studio.json's stamp when last read: a new one means Claude started a skin
async function followed() {
  try {
    const r = await fetch('data/studio.json', { cache: 'no-store' });
    if (r.ok) return await r.json();
  } catch { /* none yet */ }
  return {};
}

async function refresh() {
  if ($('roomBuild').hidden || !ask) return;
  const now = await followed();  // Claude painting another studio car: the wizard follows it
  if (following === null) following = now.stamp;
  else if (now.stamp && now.stamp !== following) {
    following = now.stamp;
    if (now.skin && now.skin !== ask && await sheetOf(now.skin)) {
      ask = now.skin;
      note(ask);  // the address, so the other rooms open it too
    }
  }
  const got = await sheetOf(ask);
  if (!got) return;
  const { skin, ...rest } = got;
  const sig = JSON.stringify(rest);
  if (sig === docSig) return loadAnswers();
  const was = doc;
  docSig = sig;
  doc = got;
  // another car, the car moved on to a new step, or a step came back to the user: show it
  if (was && (was.car !== doc.car || was.at !== doc.at
      || (stepOf(doc.at) || {}).state !== (was.steps.find((s) => s.key === doc.at) || {}).state)) shown = null;
  await Promise.all([loadGallery(), loadBoards(doc.car)]);
  draw();
  await loadAnswers();
}

function onTheCar(skin) {  // an option on the stand, to turn it and leave notes on it
  pickSkin(skin);
  rooms('studio');
}

let opened = false;
export async function open(lab, name) {
  rooms = lab.room;
  if (name && name !== ask) {
    ask = name;
    docSig = '';
    const want = new URLSearchParams(location.search).get('step');
    doc = null;
    await refresh();
    if (doc && want && stepOf(want)) go(want);
  } else await refresh();
  if (opened) return;
  opened = true;
  $('wzBack').addEventListener('click', () => {
    const i = indexOf(onShow().key);
    if (i > 0) go(doc.steps[i - 1].key);
  });
  $('wzNext').addEventListener('click', () => {
    const st = onShow(), b = $('wzNext');
    if (b.getAttribute('aria-disabled') === 'true') return;
    if (b.dataset.action === 'yes') answer(st, { yes: true });
    else go(doc.steps[indexOf(st.key) + 1].key);
  });
  const input = $('wzTell');
  input.addEventListener('input', () => { $('wzSend').hidden = !input.value.trim(); });
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); answer(onShow()); }
  });
  $('wzSend').addEventListener('click', () => answer(onShow()));
  $('wzSoFar').addEventListener('click', () => { if (doc) onTheCar(doc.car); });
  addEventListener('lab:skin', (e) => { ask = e.detail; refresh(); });
  new ResizeObserver(fit).observe($('wzBody'));
  setInterval(refresh, POLL);
  // ready once its pictures are in (Claude's snapshots of the page wait for it), 8 s at most
  const pics = [...$('roomBuild').querySelectorAll('img')].filter((i) => i.getAttribute('src'));
  await Promise.race([Promise.all(pics.map((i) => i.decode().catch(() => {}))), new Promise((r) => setTimeout(r, 8000))]);
  window.lab.ready = true;
  window.lab.wizardReady = true;
}

