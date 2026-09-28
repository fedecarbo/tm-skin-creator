// The Lab: its rooms, and the materials room: every finish the tool knows (tool/swatches.py writes
// the list and each ball's textures from tool/finishes.py), drawn on a ball with the viewer's
// lighting, with its code and numbers and a line to copy for Claude.
//   /lab.html                 the Studio (lab-studio.js), the skin Claude painted last
//   /lab.html?room=materials  the materials room, the first family
//   /lab.html?m=<slug>        that material picked (e.g. ?m=gold)
//   /lab.html?room=uv         the UV map room (lab-rooms.js, from tool/rooms.py): the game's four
//                             flat maps; &tab=car for the car
// Data: /data/materials/materials.json and /data/materials/<slug>/{B,RM,Coat}.png. A tread (the
// Treads family, shape "tyre") goes on the car's own tyre instead of a ball: tyre.json's
// cross-section on a lathe, with {B,RM,N,AO}.png (tool/swatches.py: write_tread).

import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { THUMB, daySky, dress, shape, stage, textures } from './balls.js';

const params = new URLSearchParams(location.search);
const $ = (id) => document.getElementById(id);
const SOURCE = {
  lab: 'Set against the game with the lab skins (24 Sep 2026).',
  measured: 'Colour measured from the real metal (Physically Based), then set by eye. Not yet seen in the game.',
  eye: 'Set by eye in the viewer. Not yet seen in the game.',
  photo: 'A photographed surface you added (ambientCG). Not yet seen in the game.',
  tread: 'Drawn by the tool as relief on the tyres (27 Sep 2026). Not yet seen in the game.',
};

window.lab = { ready: false, error: null };

// ---- the balls (balls.js): one renderer draws every tile's picture; the picked one spins in its own ----

const shelf = stage(document.createElement('canvas'), THUMB);
const pictures = new Map();  // slug -> picture URL, for this visit
let queue = Promise.resolve();

function picture(m) {
  if (pictures.has(m.slug)) return Promise.resolve(pictures.get(m.slug));
  const job = queue.then(async () => {
    if (pictures.has(m.slug)) return pictures.get(m.slug);
    const tex = await textures(m);
    shape(shelf, m.shape || 'ball');
    dress(shelf.ball, m, tex);
    shelf.renderer.render(shelf.scene, shelf.camera);
    const blob = await new Promise((r) => shelf.renderer.domElement.toBlob(r, 'image/png'));
    Object.values(tex).forEach((t) => t && t.dispose());
    const url = URL.createObjectURL(blob);
    pictures.set(m.slug, url);
    return url;
  });
  queue = job.catch(() => {});
  return job;
}

const big = stage($('big'), 440);
const controls = new OrbitControls(big.camera, big.renderer.domElement);
controls.enablePan = false;
controls.enableZoom = false;
controls.enableDamping = true;
let bigTex = null;

// ---- the page ----

let items = [];
let families = [];
let family = null;
let picked = null;

function familiesOf(list) {
  const out = new Map();
  for (const m of list) {
    if (!out.has(m.family)) out.set(m.family, []);
    out.get(m.family).push(m);
  }
  return out;
}

function showFamilies() {
  const box = $('families');
  box.textContent = '';
  for (const [name, list] of families) {
    const b = document.createElement('button');
    b.className = 'item';
    b.innerHTML = `<span class="n"></span><span class="cnt">${list.length}</span>`;
    b.querySelector('.n').textContent = name;
    b.setAttribute('aria-current', String(name === family));
    b.addEventListener('click', () => openFamily(name));
    box.append(b);
  }
}

function tile(m) {
  const t = document.createElement('div');
  t.className = 'tile';
  t.dataset.slug = m.slug;
  t.innerHTML = `<img class="pic" alt=""><span class="code teko"></span>
    <button class="copyBtn" title="copy for Claude"><svg class="ic"><use href="#i-copy"/></svg></button>
    <span class="tn teko"></span><span class="tv"></span>`;
  t.querySelector('.code').textContent = m.code;
  t.querySelector('.tn').textContent = m.name;
  if (['measured', 'eye', 'tread'].includes(m.source)) t.querySelector('.code').insertAdjacentHTML('beforeend', ' <em>New</em>');
  t.querySelector('.tv').innerHTML = m.sub ? `${m.sub}<br>Rubber` : `Matte ${m.matte} · Metal ${m.metal}<br>${m.varnish ? `Varnish ${m.varnish}` : 'No varnish'}`;
  t.addEventListener('click', () => pick(m));
  t.querySelector('.copyBtn').addEventListener('click', (e) => {
    e.stopPropagation();
    copy(m, e.currentTarget);
  });
  picture(m).then((url) => { t.querySelector('.pic').src = url; }).catch((err) => console.error(m.slug, err));
  return t;
}

function openFamily(name, pickFirst = true) {
  family = name;
  const list = families.get(name);
  $('familyName').textContent = name;
  $('familyCount').textContent = `${list.length} material${list.length === 1 ? '' : 's'}`;
  const box = $('tiles');
  box.textContent = '';
  for (const m of list) box.append(tile(m));
  showFamilies();
  $('shelf').scrollTop = 0;
  if (pickFirst) pick(list[0]);
  return Promise.all(list.map(picture));
}

async function pick(m) {
  picked = m;
  for (const t of document.querySelectorAll('.tile')) t.setAttribute('aria-current', String(t.dataset.slug === m.slug));
  $('spec').hidden = false;
  $('specName').innerHTML = '<small></small><span></span>';
  $('specName').querySelector('small').textContent = m.code;
  $('specName').querySelector('span').textContent = m.name;
  $('meters').innerHTML = [['Matte', m.matte], ['Metal', m.metal], ['Varnish', m.varnish]].map(([k, v]) =>
    `<div><div class="mk teko"><span>${k}</span><b>${v}%</b></div><div class="track"><i style="width:${v}%"></i></div></div>`).join('');
  $('colour').innerHTML = m.colour ? `<span class="chip" style="background:${m.colour}"></span>${m.colour}`
    : m.shape === 'tyre' ? 'Black rubber, or say a colour' : 'Any colour: say which';
  $('works').textContent = m.works_on + (m.varnish && !m.works_on.startsWith('Inner') ? '. The varnish shows on the body only.' : '');
  $('source').textContent = SOURCE[m.source] || '';
  $('about').textContent = m.about ? m.about[0].toUpperCase() + m.about.slice(1) + '.' : '';
  $('preview').textContent = m.line;
  const u = new URL(location.href);
  u.searchParams.set('m', m.slug);
  history.replaceState(null, '', u);
  const tex = await textures(m);
  if (picked !== m) { Object.values(tex).forEach((t) => t && t.dispose()); return; }
  shape(big, m.shape || 'ball');
  dress(big.ball, m, tex);
  if (bigTex) Object.values(bigTex).forEach((t) => t && t.dispose());
  bigTex = tex;
}

// ---- copying for Claude ----

let toastTimer = 0;
async function copy(m, button) {
  let ok = false;
  try {
    await navigator.clipboard.writeText(m.line);
    ok = true;
  } catch {
    const area = Object.assign(document.createElement('textarea'), { value: m.line });
    area.style.cssText = 'position:fixed;opacity:0';
    document.body.append(area);
    area.select();
    try { ok = document.execCommand('copy'); } catch { ok = false; }
    area.remove();
  }
  $('toast').querySelector('b').textContent = ok ? 'Copied' : 'Copy this';
  $('toastText').textContent = m.line;
  $('toast').classList.add('on');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => $('toast').classList.remove('on'), ok ? 2600 : 8000);
  if (button) {
    const use = button.querySelector('use');
    const was = use.getAttribute('href');
    button.classList.add('done');
    use.setAttribute('href', '#i-check');
    setTimeout(() => { button.classList.remove('done'); use.setAttribute('href', was); }, 1500);
  }
}
$('copy').addEventListener('click', (e) => picked && copy(picked, e.currentTarget));

// Back to the viewer on the skin it came from, if it came from the viewer.
if (params.get('skin')) $('back').href = `./index.html?skin=${encodeURIComponent(params.get('skin'))}`;
try {
  const from = document.referrer && new URL(document.referrer);
  if (from && from.origin === location.origin && /\/(index\.html)?$/.test(from.pathname)) $('back').href = from.pathname + from.search;
} catch { /* no referrer */ }

// ---- start ----

async function start() {
  const res = await fetch('data/materials/materials.json', { cache: 'no-store' });
  if (!res.ok) throw new Error('The materials aren\'t painted on this computer yet: run python -m tool.swatches.');
  items = await res.json();
  families = familiesOf(items);
  $('count').textContent = items.length;
  await daySky([shelf, big]);
  $('status').textContent = '';
  const want = items.find((m) => m.slug === params.get('m')) || items[0];
  const first = openFamily(want.family, false);
  await pick(want);
  big.renderer.setAnimationLoop(() => {
    if ($('roomMaterials').hidden) return;  // another room open: not drawn for nobody
    big.ball.rotation.y += 0.003;
    controls.update();
    big.renderer.render(big.scene, big.camera);
  });
  await first;
  window.lab.ready = true;
}
function failed(e) {
  window.lab.error = String(e && e.stack || e);
  $('status').textContent = e.message || String(e);
  console.error(e);
}

// ---- the rooms ----

const ROOMS = { studio: $('roomStudio'), materials: $('roomMaterials') };
const painting = new Set();  // the rooms' keys (tool/rooms.py: the UV map), shown in #roomPaint
const begun = {};
function openRoom(name) {
  for (const [k, el] of Object.entries(ROOMS)) el.hidden = k !== name;
  $('roomPaint').hidden = !painting.has(name);
  for (const b of document.querySelectorAll('#rooms [data-room]')) b.setAttribute('aria-pressed', String(b.dataset.room === name));
  const u = new URL(location.href);
  if (name === 'studio') u.searchParams.delete('room');
  else u.searchParams.set('room', name);
  history.replaceState(null, '', u);
  $('status').textContent = '';
  if (name === 'materials') begun.materials ||= start().catch(failed);
  if (painting.has(name)) import('./lab-rooms.js').then((room) => room.open({ copy }, name)).catch(failed);
  if (name === 'studio') (begun.studio ||= import('./lab-studio.js')).then((room) => room.open({ copy })).catch(failed);
}

async function rooms() {
  const list = await (await import('./lab-rooms.js')).list();
  const materials = document.querySelector('#rooms [data-room="materials"]');
  for (const r of list) {
    painting.add(r.key);
    const b = document.createElement('button');
    b.className = 'sk';
    b.dataset.room = r.key;
    b.setAttribute('aria-pressed', 'false');
    b.innerHTML = '<span></span>';
    b.querySelector('span').textContent = r.name;
    materials.before(b);
  }
  for (const b of document.querySelectorAll('#rooms [data-room]')) b.addEventListener('click', () => openRoom(b.dataset.room));
  let want = params.get('room');
  if (['body', 'details', 'tyres', 'glass', 'wheels', 'lights'].includes(want)) want = 'uv';  // the rooms before the UV map (2026-09-27)
  openRoom(ROOMS[want] || painting.has(want) ? want : params.has('m') ? 'materials' : 'studio');
}
rooms().catch(failed);
