// The Lab's painting rooms: Body, Wheels, Details, Lights (tool/rooms.py). Each room shows the car
// Claude is working on with a camera framing its area (the Car tab; the Details room takes the
// shell off), or its own flat maps with only its parts lit and named (the UV map tab). Point at a
// part on the map to name it; click it, or click the car, to pick it and copy its line for Claude.
// The Lights room is seen at night, and its map is the light map. The user's plan of 2026-09-26
// (CHECKLIST.md, "The Lab rethought").
//   /lab.html?room=wheels[&tab=map][&map=Details][&part=<id>][&skin=<name>]
// Everything comes from the tool (tool/view.py, export_uvmap): uvmap.json (each map; each part in
// words and numbers; the rooms, each with its parts and camera), <Set>_Parts.png (the part covering
// each texel: R + 256 G = id + 1) and <Set>_Shared.png (texels several parts share). The skin is
// the one in the address (the viewer's "The Lab" link), else the one Claude painted last
// (studio.json), else the one the viewer showed last; as in the Studio, when Claude starts painting
// another, the rooms follow it, and they show each step as it lands (steps.json).
// The car is the viewer itself (?embed=1).

const $ = (id) => document.getElementById(id);
const params = new URLSearchParams(location.search);
const POLL = 1500;
const GROUND = [5, 5, 6];      // the Lab's ball ground (--ball)
const OUTLINE = [255, 217, 51];  // the lit part's edge
const PAINT = { Skin: 'Skin_B', Details: 'Details_B', Wheels: 'Wheels_B', Glass: 'Glass_T' };
const MOODS = [['day', 'Day'], ['night', 'Night'], ['sunrise', 'Sunrise'], ['sunset', 'Sunset']];  // Trackmania's four; the viewer has two

let doc = null;
const byId = [];
let copyLine = null;     // lab.js's copy
let room = null;         // doc.rooms entry
let inRoom = new Uint8Array(256);
let tab = params.get('tab') === 'map' ? 'map' : 'car';
const mood = {};         // room key -> 'day' | 'night'
let skin = null;         // { name, title, textures, stamp, painting, step }
let map = null;          // the open map: { set, slot, info, w, h, ids, shared, paint, box }
let base = null;         // the open map as shown (ImageData)
let picked = null;       // { id, lit: [ids] }
let pointed = null;
let car = null;          // the embedded viewer's window.viewer, once ready
let following = null;    // studio.json's stamp when last read
const grids = new Map(); // set -> { ids, shared, box }
const paints = new Map(); // url -> pixels

const toLin = (v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
const toSrgb = (v) => 255 * (v <= 0.0031308 ? v * 12.92 : 1.055 * v ** (1 / 2.4) - 0.055);
// the viewer lights a part by mixing it 65 % toward (1, .85, .2) in linear light
const TINT = [1, 0.85, 0.2].map((l) => Uint8ClampedArray.from({ length: 256 }, (_, v) => toSrgb(toLin(v / 255) * 0.35 + l * 0.65)));
const titleOf = (name) => name.replace(/^TSC_/, '').replaceAll('_', ' ').replace(/([a-z])(?=[A-Z])/g, '$1 ');
const ago = (t) => {
  const s = Math.max(0, Date.now() / 1000 - t);
  return s < 60 ? 'just now' : s < 3600 ? `${Math.round(s / 60)} min ago` : s < 86400 ? `${Math.round(s / 3600)} h ago` : `${Math.round(s / 86400)} days ago`;
};

// ---- loading ----

async function pixels(url, w, h) {
  const blob = await (await fetch(url)).blob();
  const opts = { colorSpaceConversion: 'none', premultiplyAlpha: 'none' };
  const bmp = await createImageBitmap(blob, w ? { ...opts, resizeWidth: w, resizeHeight: h, resizeQuality: 'high' } : opts);
  const c = new OffscreenCanvas(bmp.width, bmp.height);
  const g = c.getContext('2d', { willReadFrequently: true });
  g.drawImage(bmp, 0, 0);
  bmp.close();
  return g.getImageData(0, 0, c.width, c.height).data;
}

async function grid(set) {
  if (grids.has(set)) return grids.get(set);
  const info = doc.maps.find((m) => m.set === set);
  const [w, h] = info.grid;
  const [idPx, sharedPx] = await Promise.all([pixels(`data/${set}_Parts.png`), pixels(`data/${set}_Shared.png`)]);
  const n = w * h;
  const ids = new Int32Array(n), shared = new Uint8Array(n);
  const box = new Int32Array(256 * 4);
  for (let i = 0; i < 256; i++) box.set([w, h, -1, -1], i * 4);
  for (let k = 0; k < n; k++) {
    const id = idPx[k * 4] + 256 * idPx[k * 4 + 1] - 1;
    ids[k] = id;
    shared[k] = sharedPx[k * 4] > 127 ? 1 : 0;
    if (id < 0) continue;
    const x = k % w, y = (k - x) / w, b = id * 4;
    if (x < box[b]) box[b] = x;
    if (y < box[b + 1]) box[b + 1] = y;
    if (x > box[b + 2]) box[b + 2] = x;
    if (y > box[b + 3]) box[b + 3] = y;
  }
  const g = { info, w, h, ids, shared, box };
  grids.set(set, g);
  return g;
}

async function loadMap(set, slot) {
  const g = await grid(set);
  const url = (skin && skin.textures[slot]) || `stock/${slot}.png`;
  if (!paints.has(url)) paints.set(url, await pixels(`data/${url}`, g.w, g.h));
  return { set, slot, ...g, paint: paints.get(url) };
}

// ---- drawing: the room's parts on the map, the rest dimmed, and the lit part over it ----

function compose() {
  const { w, h, ids, paint } = map;
  const out = new ImageData(w, h), o = out.data;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const k = y * w + x, j = k * 4, id = ids[k];
      let r = GROUND[0], g = GROUND[1], b = GROUND[2];
      if (id >= 0 && inRoom[id]) {  // only the room's parts: the rest of the map stays empty
        r = paint[j]; g = paint[j + 1]; b = paint[j + 2];
        // the room's parts outlined, faint: a texel whose neighbour is another part or empty
        if ((x > 0 && ids[k - 1] !== id) || (x < w - 1 && ids[k + 1] !== id) || (y > 0 && ids[k - w] !== id) || (y < h - 1 && ids[k + w] !== id)) {
          r += (255 - r) * 0.3; g += (255 - g) * 0.3; b += (255 - b) * 0.3;
        }
      }
      o[j] = r; o[j + 1] = g; o[j + 2] = b; o[j + 3] = 255;
    }
  }
  return out;
}

function drawBase() {
  base = compose();
  const c = $('prBase');
  c.width = map.w; c.height = map.h;
  c.getContext('2d').putImageData(base, 0, 0);
  drawLit();
}

let drawQueued = false;
function drawLit() {
  if (drawQueued) return;
  drawQueued = true;
  requestAnimationFrame(() => { drawQueued = false; if (map) paintLit((pointed || picked || { lit: [] }).lit); });
}

function paintLit(lit) {
  const c = $('prLit'), { w, h, ids, box } = map;
  if (c.width !== w || c.height !== h) { c.width = w; c.height = h; }
  const g = c.getContext('2d');
  g.clearRect(0, 0, w, h);
  const on = new Uint8Array(256);
  let x0 = w, y0 = h, x1 = -1, y1 = -1;
  for (const id of lit) {
    if (box[id * 4 + 2] < 0) continue;
    on[id] = 1;
    x0 = Math.min(x0, box[id * 4]); y0 = Math.min(y0, box[id * 4 + 1]);
    x1 = Math.max(x1, box[id * 4 + 2]); y1 = Math.max(y1, box[id * 4 + 3]);
  }
  if (x1 < 0) return;
  g.fillStyle = 'rgba(5, 5, 6, 0.55)';  // everything else dimmed
  g.fillRect(0, 0, w, h);
  const R = 3;  // the outline's width, in texels
  x0 = Math.max(0, x0 - R); y0 = Math.max(0, y0 - R); x1 = Math.min(w - 1, x1 + R); y1 = Math.min(h - 1, y1 + R);
  const bw = x1 - x0 + 1, bh = y1 - y0 + 1;
  const inside = new Uint8Array(bw * bh);
  for (let y = 0; y < bh; y++) for (let x = 0; x < bw; x++) {
    const id = ids[(y + y0) * w + x + x0];
    inside[y * bw + x] = id >= 0 && on[id];
  }
  const img = g.createImageData(bw, bh), o = img.data, b = base.data;
  for (let y = 0; y < bh; y++) {
    for (let x = 0; x < bw; x++) {
      const i = y * bw + x, j = i * 4;
      if (!inside[i]) { o[j] = 5; o[j + 1] = 5; o[j + 2] = 6; o[j + 3] = 140; continue; }
      let edge = false;
      for (let d = 1; d <= R && !edge; d++) {
        edge = x < d || y < d || x + d >= bw || y + d >= bh ||
          !inside[i - d] || !inside[i + d] || !inside[i - d * bw] || !inside[i + d * bw];
      }
      const k = ((y + y0) * w + x + x0) * 4;
      if (edge) { o[j] = OUTLINE[0]; o[j + 1] = OUTLINE[1]; o[j + 2] = OUTLINE[2]; }
      else { o[j] = TINT[0][b[k]]; o[j + 1] = TINT[1][b[k + 1]]; o[j + 2] = TINT[2][b[k + 2]]; }
      o[j + 3] = 255;
    }
  }
  g.putImageData(img, x0, y0);
}

function fit() {
  if (!map || tab !== 'map') return;
  const stage = $('prStage');
  const narrow = matchMedia('(max-width: 1000px)').matches;
  const aw = stage.clientWidth - 24, ah = narrow ? Infinity : stage.clientHeight - 24;
  const cw = Math.max(120, Math.min(aw, ah * (map.w / map.h)));
  const frame = $('prMap');
  frame.style.width = `${Math.floor(cw)}px`;
  frame.style.height = `${Math.floor(cw * (map.h / map.w))}px`;
}

// ---- pointing, picking, the car ----

function lightCar() {
  if (car) car.light((pointed || picked || { lit: [] }).lit);
}

function point(p, e) {
  const tag = $('prTag');
  if (!p) {
    tag.hidden = true;
    if (pointed) { pointed = null; drawLit(); lightCar(); }
    return;
  }
  if (!pointed || pointed.id !== p.id || pointed.lit.length !== p.lit.length) {
    pointed = p;
    drawLit();
    lightCar();
  }
  tag.textContent = byId[p.id].label + (p.here ? ' · shared paint' : '');
  tag.hidden = false;
  const r = $('prMap').getBoundingClientRect();
  const x = e.clientX - r.left, y = e.clientY - r.top;
  const right = x + 16 + tag.offsetWidth > r.width;
  tag.style.left = `${right ? x - 12 - tag.offsetWidth : x + 16}px`;
  tag.style.top = `${Math.min(y + 18, r.height - tag.offsetHeight)}px`;
}

function hit(e) {
  const r = $('prBase').getBoundingClientRect();
  const x = Math.floor(((e.clientX - r.left) / r.width) * map.w), y = Math.floor(((e.clientY - r.top) / r.height) * map.h);
  if (x < 0 || y < 0 || x >= map.w || y >= map.h) return null;
  const k = y * map.w + x, id = map.ids[k];
  if (id < 0 || !inRoom[id]) return null;
  const here = map.shared[k] === 1 && byId[id].twins.length > 0;  // this texel's paint lands on the twins too
  return { id, here, lit: here ? [id, ...byId[id].twins] : [id] };
}

function roomsOf(id) {
  return doc.rooms.filter((r) => r.ids.includes(id)).map((r) => r.name);
}

function pick(p) {
  picked = p;
  const part = byId[p.id];
  $('prPart').innerHTML = '<span></span> <small></small>';
  $('prPart').querySelector('span').textContent = part.name;
  $('prPart').querySelector('small').textContent = part.tag;
  const rooms = roomsOf(p.id);
  $('prRooms').textContent = inRoom[p.id] ? rooms.join(', ') : `${rooms.join(', ')}: not this room's`;
  $('prWhere').textContent = `${part.mesh}, ${part.pct < 0.1 ? 'under 0.1' : part.pct} % of it`;
  $('prParent').textContent = `${part.parent}: ${doc.assemblies[part.parent] || ''}`;
  $('prPaint').textContent = part.paint[0].toUpperCase() + part.paint.slice(1);
  $('prSharp').textContent = `${part.sharp} dots per cm`;
  $('prSize').textContent = `${part.area.toLocaleString('en-GB')} cm² on the car`;
  $('prLine').textContent = part.line;
  const u = new URL(location.href);
  u.searchParams.set('part', p.id);
  history.replaceState(null, '', u);
  drawLit();
  lightCar();
}

async function pickId(id) {  // from a click on the car, or the address
  const part = byId[id];
  if (!part) return;
  if (tab === 'map' && inRoom[id] && map && map.set !== part.mesh && room.maps.some((m) => m.set === part.mesh)) await openMap(part.mesh);
  pick({ id, here: false, lit: [id] });
}

// ---- the room ----

function buttons(box, items, current, onClick) {
  box.textContent = '';
  for (const it of items) {
    const b = document.createElement('button');
    b.className = 'sk';
    b.innerHTML = '<span></span>';
    b.querySelector('span').textContent = it.label;
    b.setAttribute('aria-pressed', String(it.key === current));
    if (it.off) { b.setAttribute('aria-disabled', 'true'); b.title = it.off; }
    else b.addEventListener('click', () => onClick(it.key));
    box.append(b);
  }
}

function heads() {
  const tabs = [{ key: 'car', label: 'Car' }, { key: 'map', label: 'UV map' }];
  buttons($('prTabs'), tabs, tab, (k) => showTab(k));
  $('prMaps').hidden = tab !== 'map' || room.maps.length < 2;
  if (tab === 'map') buttons($('prMaps'), room.maps.map((m) => ({ key: m.set, label: m.set })), map && map.set, (k) => openMap(k));
  const lights = room.key === 'lights';
  $('prMood').hidden = !lights;
  if (lights) {
    buttons($('prMood'), MOODS.map(([k, label]) => ({ key: k, label, off: k === 'day' || k === 'night' ? null : 'not in the viewer yet' })),
      mood.lights || 'night', (k) => { mood.lights = k; heads(); aimCar(); });
    $('prMood').insertAdjacentHTML('afterbegin', '<span class="say">Mood</span>');
  }
}

function aimCar() {  // the room's camera, framing its parts (tool/rooms.py), and the parts it takes off
  if (!car || !room) return;
  const night = room.key === 'lights' ? (mood.lights || 'night') === 'night' : false;
  car.hide(room.hides);
  car.show(room.view, night, []);
}

async function openMap(set) {
  const m = room.maps.find((x) => x.set === set) || room.maps[0];
  $('status').textContent = `Loading the ${m.set} map…`;
  map = await loadMap(m.set, m.slot || PAINT[m.set]);
  $('status').textContent = '';
  pointed = null;
  const u = new URL(location.href);
  u.searchParams.set('map', m.set);
  history.replaceState(null, '', u);
  heads();
  fit();
  drawBase();
}

async function showTab(k) {
  tab = k;
  const u = new URL(location.href);
  if (k === 'map') u.searchParams.set('tab', 'map'); else { u.searchParams.delete('tab'); u.searchParams.delete('map'); }
  history.replaceState(null, '', u);
  $('prCar').hidden = k !== 'car';
  $('prMap').hidden = k !== 'map';
  $('prTag').hidden = true;
  if (k === 'map') {  // the picked part's map, else the one open, else the address's
    const has = (set) => set && room.maps.some((m) => m.set === set);
    const mine = picked && inRoom[picked.id] ? byId[picked.id].mesh : null;
    await openMap(has(mine) ? mine : map && has(map.set) ? map.set : params.get('map'));
  } else heads();
}

async function setRoom(key) {
  room = doc.rooms.find((r) => r.key === key) || doc.rooms[0];
  inRoom = new Uint8Array(256);
  for (const id of room.ids) inRoom[id] = 1;
  $('prName').textContent = room.name;
  $('prAbout').textContent = `${room.about} · ${room.ids.length} parts`;
  map = null;
  aimCar();
  const want = picked && inRoom[picked.id] ? picked.id : Number(params.get('part'));
  const inView = room.view.fit ? room.ids.filter((id) => room.view.fit.includes(id)) : [];  // the biggest part the camera frames
  const pool = inView.length ? inView : room.ids;
  const first = inRoom[want] ? want : pool.reduce((a, id) => (byId[id].area > byId[a].area ? id : a), pool[0]);
  picked = { id: first, here: false, lit: [] };  // in the panel, but nothing lit until it's picked
  await showTab(tab);
  pick(picked);  // lit: [] when it's the room's first pick, so the car keeps its paint
}

// ---- the skin: the one Claude is painting, live ----

function live() {
  const box = $('prLive'), text = $('prLiveText');
  box.classList.toggle('on', !!(skin && skin.painting));
  if (!skin) { text.textContent = 'No skin yet: ask Claude for one'; return; }
  if (skin.painting) text.textContent = `${skin.title} · Claude is painting${skin.step ? ` · ${skin.step}` : ''}`;
  else text.textContent = `${skin.title}${skin.stamp ? ` · painted ${ago(skin.stamp)}` : ''}`;
}

async function readSkin(name) {  // its textures: the newest step while it's being painted, else the whole skin
  const list = await (await fetch('data/gallery.json')).json();
  const entry = list.find((s) => s.name === name);
  const out = { name, title: entry ? entry.title : titleOf(name), textures: null, stamp: 0, painting: false, step: '' };
  const st = await fetch(`data/skins/${encodeURIComponent(name)}/steps.json`, { cache: 'no-store' });
  if (st.ok) {
    const steps = await st.json();
    out.stamp = steps.stamp;
    out.painting = steps.painting;
    const done = steps.steps.filter((s) => s.textures);
    const open = steps.steps.find((s) => !s.textures);
    out.step = open ? open.name : '';
    if (steps.painting && done.length) out.textures = done[done.length - 1].textures;
  }
  if (!out.textures) {
    const sk = await fetch(`data/skins/${encodeURIComponent(name)}/skin.json`, { cache: 'no-store' });
    if (!sk.ok) return null;
    out.textures = (await sk.json()).textures;
  }
  return out;
}

async function wear(next) {  // dress the car and the map in a skin's textures
  const before = skin;
  skin = next;
  live();
  if (!skin) return;
  if (car) await car.dress(skin.textures);
  if (before && before.name !== skin.name) paints.clear();
  if (map) {
    const slot = map.slot;
    map = await loadMap(map.set, slot);
    drawBase();
  }
}

async function followed() {  // the skin Claude painted last: { skin, stamp }
  try {
    const r = await fetch('data/studio.json', { cache: 'no-store' });
    if (r.ok) return await r.json();
  } catch { /* none yet */ }
  return {};
}

async function poll() {
  try {
    const now = await followed();
    let name = skin && skin.name;
    if (now.stamp && now.stamp !== following) { following = now.stamp; name = now.skin; }
    if (!name) return;
    const next = await readSkin(name);
    if (!next) return;
    const changed = !skin || next.name !== skin.name || next.stamp !== skin.stamp || next.painting !== skin.painting ||
      JSON.stringify(next.textures) !== JSON.stringify(skin.textures);
    if (changed) await wear(next);
    else live();
  } catch (e) { console.error(e); }
}

function embedCar() {
  return new Promise((resolve) => {
    const frame = $('prCar');
    frame.addEventListener('load', () => {
      const wait = setInterval(() => {
        const v = frame.contentWindow && frame.contentWindow.viewer;
        if (!v || !(v.ready || v.error)) return;
        clearInterval(wait);
        if (v.error) { resolve(null); return; }
        car = v;
        car.onPick = (id) => pickId(id);
        resolve(car);
      }, 150);
    }, { once: true });
    frame.src = './index.html?embed=1';  // no skin: the stock car, dressed in the skin's textures
  });
}

// ---- start ----

let begun = null;
async function begin(helpers) {
  copyLine = helpers.copy;
  $('status').textContent = 'Loading…';
  const res = await fetch('data/uvmap.json', { cache: 'no-store' });
  if (!res.ok) throw new Error('The rooms aren\'t ready on this computer yet: run python -m tool.swatches.');
  doc = await res.json();
  for (const p of doc.parts) byId[p.id] = p;
  const now = await followed();
  following = now.stamp;
  let name = params.get('skin') || now.skin;
  try { name ||= localStorage.getItem('tsc-viewer-skin'); } catch { /* no storage */ }
  const [first] = await Promise.all([name ? readSkin(name) : null, embedCar()]);
  await wear(first);
  const frame = $('prMap');
  frame.addEventListener('pointermove', (e) => point(hit(e), e));
  frame.addEventListener('pointerleave', () => point(null));
  frame.addEventListener('click', (e) => { const p = hit(e); if (p) pick(p); });
  $('prCopy').addEventListener('click', (e) => picked && copyLine({ line: byId[picked.id].line }, e.currentTarget));
  addEventListener('resize', fit);
  setInterval(poll, POLL);
  $('status').textContent = '';
}

// The painting rooms, from the tool, for lab.js's tabs.
export async function list() {
  const res = await fetch('data/uvmap.json', { cache: 'no-store' });
  if (!res.ok) return [];
  return (await res.json()).rooms.map((r) => ({ key: r.key, name: r.name }));
}

export async function open(helpers, key) {
  begun ||= begin(helpers);
  await begun;
  if (!room || room.key !== key) await setRoom(key);
  else fit();
  window.lab.roomsReady = key;
}
