// The Lab's UV map room: the car's four flat paint maps as the tool paints them, every part named.
// Point at the map to name a part and light it here and on the car; click to pick it, and copy its
// line for Claude. Clicking the car picks a part too. Layout A of the mockups the user chose on
// 2026-09-26 (CHECKLIST.md, "The Lab", step 2).
//   /lab.html?room=uv[&map=Details][&part=<id>][&skin=<name>]
// Everything comes from the tool (tool/view.py, export_uvmap): uvmap.json (each map, and each part
// in words and numbers), <Set>_Parts.png (the part covering each texel: R + 256 G = id + 1) and
// <Set>_Shared.png (texels several parts share), over a skin's own paint (skins/<name>/skin.json):
// the one in the address, else the one the viewer showed last, else the one installed last. The
// car is the viewer itself (?embed=1).

const $ = (id) => document.getElementById(id);
const params = new URLSearchParams(location.search);
const GROUND = [5, 5, 6];      // the Lab's ball ground (--ball)
const OUTLINE = [255, 217, 51];  // the lit part's edge
const SLOT = { Skin: 'Skin_B', Details: 'Details_B', Wheels: 'Wheels_B', Glass: 'Glass_T' };

let doc = null;
const byId = [];
let skin = null;         // { name, title, textures }
let copyLine = null;     // lab.js's copy
let map = null;          // the open map: { set, info, w, h, ids, shared, paint, box }
let show = 'paint';
let base = null;         // the open map as shown (ImageData)
let picked = null;       // { id, lit: [ids] }
let pointed = null;
let car = null;          // the embedded viewer's window.viewer, once ready
const maps = new Map();

// ---- colours: the viewer lights a part by mixing it 65 % toward (1, .85, .2) in linear light ----

const toLin = (v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
const toSrgb = (v) => 255 * (v <= 0.0031308 ? v * 12.92 : 1.055 * v ** (1 / 2.4) - 0.055);
const TINT = [1, 0.85, 0.2].map((l) => Uint8ClampedArray.from({ length: 256 }, (_, v) => toSrgb(toLin(v / 255) * 0.35 + l * 0.65)));

function hsl(h, s, l) {  // as three.js Color.setHSL, in linear light
  const f = (n) => {
    const k = (n + h * 12) % 12;
    return l - s * Math.min(l, 1 - l) * Math.max(-1, Math.min(k - 3, 9 - k, 1));
  };
  return [f(0), f(8), f(4)];
}
let partColour = [];  // the viewer's "colour by part": one hue per name

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

async function loadMap(set) {
  if (maps.has(set)) return maps.get(set);
  const info = doc.maps.find((m) => m.set === set);
  const [w, h] = info.grid;
  const paintUrl = skin ? skin.textures[SLOT[set]] : `stock/${SLOT[set]}.png`;
  const [idPx, sharedPx, paint] = await Promise.all([
    pixels(`data/${set}_Parts.png`), pixels(`data/${set}_Shared.png`), pixels(`data/${paintUrl}`, w, h)]);
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
  const m = { set, info, w, h, ids, shared, paint, box };
  maps.set(set, m);
  return m;
}

// ---- drawing: the map as shown, and the lit part over it ----

function compose() {
  const { w, h, ids, shared, paint } = map;
  const out = new ImageData(w, h), o = out.data;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const k = y * w + x, j = k * 4, id = ids[k];
      let r = GROUND[0], g = GROUND[1], b = GROUND[2];
      if (id >= 0) {
        if (show === 'parts') [r, g, b] = partColour[id];
        else { r = paint[j]; g = paint[j + 1]; b = paint[j + 2]; }
        if (show === 'shared' && shared[k] && (x + y) & 8) {  // the viewer's magenta stripes
          r = r * 0.4 + 153; g *= 0.4; b = b * 0.4 + 130;
        }
        // every part's outline, faint: a texel whose neighbour is another part or empty
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
  const c = $('uvBase');
  c.width = map.w; c.height = map.h;
  c.getContext('2d').putImageData(base, 0, 0);
  drawLit();
}

let drawQueued = false;
function drawLit() {
  if (drawQueued) return;
  drawQueued = true;
  requestAnimationFrame(() => { drawQueued = false; paintLit((pointed || picked || { lit: [] }).lit); });
}

function paintLit(lit) {
  const c = $('uvLit'), { w, h, ids, box } = map;
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
  if (!map) return;
  const shelf = $('uvShelf'), frame = $('uvMap'), cs = getComputedStyle(shelf);
  const narrow = matchMedia('(max-width: 1000px)').matches;
  const aw = shelf.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight) - 4;  // 4: the map's margin
  const ah = narrow ? Infinity : shelf.clientHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom) - $('uvHead').offsetHeight - 14;
  const cw = Math.max(120, Math.min(aw, ah * (map.w / map.h)));
  frame.style.width = `${Math.floor(cw)}px`;
  frame.style.height = `${Math.floor(cw * (map.h / map.w))}px`;
}

// ---- pointing, picking, the car ----

function lightCar() {
  if (car) car.light((pointed || picked || { lit: [] }).lit);
}

function point(p, e) {
  const tag = $('uvTag');
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
  const part = byId[p.id];
  tag.textContent = part.label + (p.here ? ' · shared paint' : '');
  tag.hidden = false;
  const r = $('uvMap').getBoundingClientRect();
  const x = e.clientX - r.left, y = e.clientY - r.top;
  const right = x + 16 + tag.offsetWidth > r.width;
  tag.style.left = `${right ? x - 12 - tag.offsetWidth : x + 16}px`;
  tag.style.top = `${Math.min(y + 18, r.height - tag.offsetHeight)}px`;
}

function hit(e) {
  const r = $('uvBase').getBoundingClientRect();
  const x = Math.floor(((e.clientX - r.left) / r.width) * map.w), y = Math.floor(((e.clientY - r.top) / r.height) * map.h);
  if (x < 0 || y < 0 || x >= map.w || y >= map.h) return null;
  const k = y * map.w + x, id = map.ids[k];
  if (id < 0) return null;
  const here = map.shared[k] === 1 && byId[id].twins.length > 0;  // this texel's paint lands on the twins too
  return { id, here, lit: here ? [id, ...byId[id].twins] : [id] };
}

function pick(p, aim = true) {
  picked = p;
  const part = byId[p.id];
  $('uvPart').innerHTML = '<span></span> <small></small>';
  $('uvPart').querySelector('span').textContent = part.name;
  $('uvPart').querySelector('small').textContent = part.tag;
  $('uvWhere').textContent = `${part.mesh}, ${part.pct < 0.1 ? 'under 0.1' : part.pct} % of it`;
  $('uvParent').textContent = `${part.parent}: ${doc.assemblies[part.parent] || ''}`;
  $('uvPaint').textContent = part.paint[0].toUpperCase() + part.paint.slice(1);
  $('uvSharp').textContent = `${part.sharp} dots per cm`;
  $('uvSize').textContent = `${part.area.toLocaleString('en-GB')} cm² on the car`;
  $('uvLine').textContent = part.line;
  const u = new URL(location.href);
  u.searchParams.set('part', p.id);
  history.replaceState(null, '', u);
  drawLit();
  lightCar();
  if (car && aim) car.aim([p.id]);
}

async function pickId(id) {  // from a click on the car, or the address
  const part = byId[id];
  if (!part) return;
  if (!map || map.set !== part.mesh) await openMap(part.mesh, id);
  else pick({ id, here: false, lit: [id] });
}

// ---- the page ----

function showMaps() {
  const box = $('uvMaps');
  box.textContent = '';
  for (const m of doc.maps) {
    const b = document.createElement('button');
    b.className = 'item';
    b.title = m.holds.join(', ');
    b.innerHTML = `<span class="n"></span><span class="cnt">${m.parts}</span>`;
    b.querySelector('.n').textContent = m.set;
    b.setAttribute('aria-current', String(map && m.set === map.set));
    b.addEventListener('click', () => openMap(m.set));
    box.append(b);
  }
}

async function openMap(set, partId = null) {
  $('status').textContent = `Loading the ${set} map…`;
  const m = await loadMap(set);
  $('status').textContent = '';
  map = m;
  pointed = null;
  $('uvName').textContent = set;
  const [pw, ph] = m.info.size;
  $('uvAbout').textContent = `${pw} × ${ph} · ${m.info.parts} parts · ${skin ? `painted as ${skin.title}` : 'the stock paint'}`;
  const u = new URL(location.href);
  u.searchParams.set('map', set);
  history.replaceState(null, '', u);
  showMaps();
  fit();
  drawBase();
  const mine = doc.parts.filter((p) => p.mesh === set);
  const want = mine.find((p) => p.id === partId) || mine.reduce((a, p) => (p.pct > a.pct ? p : a));
  pick({ id: want.id, here: false, lit: [want.id] });
}

function embedCar() {
  const frame = $('uvCar');
  frame.src = `./index.html?embed=1${skin ? `&skin=${encodeURIComponent(skin.name)}` : ''}`;
  frame.addEventListener('load', () => {
    const wait = setInterval(() => {
      const v = frame.contentWindow && frame.contentWindow.viewer;
      if (!v || !(v.ready || v.error)) return;
      clearInterval(wait);
      if (v.error) return;
      car = v;
      car.onPick = (id) => pickId(id);
      lightCar();
      if (picked) car.aim([picked.id]);
    }, 150);
  });
}

async function chooseSkin() {
  let want = params.get('skin');
  try {  // the skin the viewer showed, when the Lab was opened from it, or last
    const from = document.referrer && new URL(document.referrer);
    if (!want && from && from.origin === location.origin) want = from.searchParams.get('skin');
    if (!want) want = localStorage.getItem('tsc-viewer-skin');
  } catch { /* no referrer, or no storage */ }
  const list = (await (await fetch('data/gallery.json')).json()).filter((s) => s.viewable);
  const last = list.filter((s) => s.installed_at).sort((a, b) => b.installed_at.localeCompare(a.installed_at))[0];
  const entry = list.find((s) => s.name === want) || last || list[0];
  if (!entry) return null;
  const s = await (await fetch(`data/skins/${encodeURIComponent(entry.name)}/skin.json`)).json();
  return { name: entry.name, title: entry.title, textures: s.textures };
}

let opened = false;
export async function open(helpers) {
  if (opened) { fit(); return; }
  opened = true;
  copyLine = helpers.copy;
  $('status').textContent = 'Loading…';
  const res = await fetch('data/uvmap.json');
  if (!res.ok) throw new Error('The UV map isn\'t ready on this computer yet: run python -m tool.swatches.');
  doc = await res.json();
  for (const p of doc.parts) byId[p.id] = p;
  const names = [...new Set(doc.parts.map((p) => p.name))];
  partColour = [];
  for (const p of doc.parts) partColour[p.id] = hsl((names.indexOf(p.name) * 0.618034) % 1, 0.75, 0.5).map(toSrgb);
  $('uvCount').textContent = doc.maps.length;
  skin = await chooseSkin();
  embedCar();

  const frame = $('uvMap');
  frame.addEventListener('pointermove', (e) => point(hit(e), e));
  frame.addEventListener('pointerleave', () => point(null));
  frame.addEventListener('click', (e) => { const p = hit(e); if (p) pick(p); });
  for (const b of document.querySelectorAll('#uvShow [data-show]')) {
    b.addEventListener('click', () => {
      show = b.dataset.show;
      for (const o of document.querySelectorAll('#uvShow [data-show]')) o.setAttribute('aria-pressed', String(o === b));
      drawBase();
    });
  }
  $('uvCopy').addEventListener('click', (e) => picked && copyLine({ line: byId[picked.id].line }, e.currentTarget));
  addEventListener('resize', fit);

  const want = params.has('part') ? byId[Number(params.get('part'))] : null;
  const set = doc.maps.some((m) => m.set === params.get('map')) ? params.get('map') : want ? want.mesh : 'Skin';
  await openMap(set, want && want.mesh === set ? want.id : null);
  window.lab.uvReady = true;
}
