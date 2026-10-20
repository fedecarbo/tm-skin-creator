// The garage, the Lab's front door (/ with no skin named, or ?room=garage): every skin the tool has painted for the
// viewer, parked on matte white in a numbered bay, seen from one fixed angle (from the car's front-right, 32 degrees
// up: its side and its roof, the nose to the lower right; the user's pick of a mockup, 2026-10-19), its name and where
// it stands under it, the car Claude painted last in the accent bay. Click a car: the car itself (lab-studio.js).
// Everything shown is the tool's: data/gallery.json (tool/gallery.py: the list, newest first, each skin's standing from
// tool/notes.py stands), data/skins/<name>/skin.json (its paint as last shown), data/studio.json (the bench).
// The cars are the page's own car (viewer.js's kit: its geometries, its materials without the studio's hooks, its day
// sky), each dressed in its skin's maps shrunk in the browser (1024 px wide for the colour, 512 for the rest; the full
// maps are half a gigabyte a car), the stock maps shared. Drag to pan, wheel or pinch to zoom; the angle never changes.
// While it's open the page follows Claude's painting as the car does: a skin shown opens the car with it.

import * as THREE from 'three';
import { kit } from './viewer.js';
import { $, every, followed, note } from './lab-common.js';

const POLL = 1500;
const DIR = new THREE.Vector3(-1, 0.9, 1).normalize();  // from a car to the camera
const KEY = new THREE.Vector3(0.555, 0.742, 0.377);  // the day's sun (viewer.js LOOKS.day), over the car's front left
const ROW = 4, GAP = 1.0, ROWGAP = 2.8;  // bays a row, metres between bays, and between rows (a sign sits there)
const SLOTS = ['Skin_B', 'Skin_RM', 'Skin_Coat', 'Details_B', 'Details_RM', 'Wheels_B', 'Wheels_RM', 'Glass_T'];
const COLOUR = new Set(['Skin_B', 'Details_B', 'Wheels_B', 'Glass_T']);
const WIDE = { Skin_B: 1024, Details_B: 1024 };  // px wide; the others 512
const INK = '#0d0f12', ACC = '#e8ff47';

let renderer, scene, camera, key, floor, maxAniso, openRoom;
let wake = 0;
const rouse = (n = 2) => { wake = Math.max(wake, n); };
let bay = { w: 2.6, l: 4.8 };  // a bay, from the car's own size (fit)
let lift = 0;                  // the model's wheels, raised to the floor (car.json)
const cars = new Map();        // name -> { group, materials, bay: index, stamp, lit, marks }
let bench = null;              // the skin Claude painted last
let following = null;          // studio.json's stamp when the garage last looked
const view = { target: new THREE.Vector3(), height: 12 };  // what the camera looks at, and how many metres it shows top to bottom

// ---- the scene ----

function build() {
  const canvas = $('lot');
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setClearColor(0xf2f2f3);
  renderer.toneMapping = THREE.LinearToneMapping;  // the viewer's day (viewer.js LOOKS.day)
  renderer.toneMappingExposure = 1.44;
  renderer.shadowMap.enabled = true;
  maxAniso = renderer.capabilities.getMaxAnisotropy();
  scene = new THREE.Scene();
  scene.environment = kit.environment();
  scene.environmentIntensity = 0.44;
  camera = new THREE.OrthographicCamera(-1, 1, 1, -1, -200, 200);
  key = new THREE.DirectionalLight(0xfffcf1, 4.4);
  key.castShadow = true;
  key.shadow.mapSize.set(4096, 4096);
  key.shadow.bias = -0.0004;
  key.shadow.normalBias = 0.02;
  key.shadow.radius = 4;
  scene.add(key, key.target);
  // matte white: lit by the day's sun and sky, this reads as the page's white without clipping
  floor = new THREE.Mesh(new THREE.PlaneGeometry(600, 600), new THREE.MeshStandardMaterial({ color: new THREE.Color(0.5, 0.5, 0.51), roughness: 1, metalness: 0 }));
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  scene.add(floor);
  new ResizeObserver(resize).observe(canvas);
  hand(canvas);
  renderer.setAnimationLoop(() => {
    if ($('roomGarage').hidden || wake <= 0) return;
    wake -= 1;
    renderer.render(scene, camera);
  });
}

function resize() {
  const canvas = $('lot');
  const w = canvas.clientWidth, h = canvas.clientHeight;
  if (!w || !h) return;
  renderer.setSize(w, h, false);
  aim();
}

// The camera: above the lot's middle along DIR, showing view.height metres top to bottom.
function aim() {
  const canvas = $('lot');
  const aspect = canvas.clientWidth / Math.max(1, canvas.clientHeight);
  camera.top = view.height / 2; camera.bottom = -view.height / 2;
  camera.right = view.height / 2 * aspect; camera.left = -camera.right;
  camera.position.copy(view.target).addScaledVector(DIR, 60);
  camera.lookAt(view.target);
  camera.updateProjectionMatrix();
  rouse();
}

// Drag pans across the lot, the wheel or a pinch zooms; the angle never changes.
function hand(canvas) {
  const down = new Map();  // pointerId -> {x, y}
  let pinch = 0;
  canvas.addEventListener('pointerdown', (e) => { down.set(e.pointerId, { x: e.clientX, y: e.clientY }); canvas.setPointerCapture(e.pointerId); pinch = 0; });
  canvas.addEventListener('pointermove', (e) => {
    if (!down.has(e.pointerId)) { hover(e); return; }
    const was = down.get(e.pointerId);
    down.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (down.size === 2) {
      const [a, b] = [...down.values()];
      const d = Math.hypot(a.x - b.x, a.y - b.y);
      if (pinch) zoom(pinch / d);
      pinch = d;
      return;
    }
    const per = view.height / canvas.clientHeight;  // metres a pixel
    const right = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 0);
    const up = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 1);
    view.target.addScaledVector(right, -(e.clientX - was.x) * per).addScaledVector(up, (e.clientY - was.y) * per);
    canvas.style.cursor = 'grabbing';
    aim();
  });
  const up = (e) => {
    const was = down.get(e.pointerId);
    down.delete(e.pointerId);
    canvas.style.cursor = '';
    if (was && Math.hypot(e.clientX - was.x, e.clientY - was.y) < 4 && down.size === 0 && e.type === 'pointerup') {
      const name = under(e);
      if (name) go(name);
    }
  };
  canvas.addEventListener('pointerup', up);
  canvas.addEventListener('pointercancel', up);
  canvas.addEventListener('wheel', (e) => { e.preventDefault(); zoom(Math.exp(e.deltaY * 0.0015)); }, { passive: false });
}

function zoom(by) {
  view.height = Math.min(60, Math.max(5, view.height * by));
  aim();
}

// ---- the lot: a bay per skin, rows of ROW along x, the rows along z ----

const place = (i) => ({ x: ((i % ROW) - (ROW - 1) / 2) * (bay.w + GAP), z: Math.floor(i / ROW) * (bay.l + ROWGAP) });

function rounded(w, l, r) {
  const s = new THREE.Shape();
  s.moveTo(-w / 2 + r, -l / 2);
  s.lineTo(w / 2 - r, -l / 2); s.quadraticCurveTo(w / 2, -l / 2, w / 2, -l / 2 + r);
  s.lineTo(w / 2, l / 2 - r); s.quadraticCurveTo(w / 2, l / 2, w / 2 - r, l / 2);
  s.lineTo(-w / 2 + r, l / 2); s.quadraticCurveTo(-w / 2, l / 2, -w / 2, l / 2 - r);
  s.lineTo(-w / 2, -l / 2 + r); s.quadraticCurveTo(-w / 2, -l / 2, -w / 2 + r, -l / 2);
  return s;
}

// Words on a canvas, as a sprite the size of the words in metres, anchored at its top left.
function words(lines, scale = 0.0065) {
  const c = document.createElement('canvas');
  const ctx = c.getContext('2d');
  const widths = lines.map((l) => { ctx.font = l.font; return ctx.measureText(l.text).width; });
  c.width = Math.ceil(Math.max(...widths) + 24);
  c.height = Math.ceil(lines.reduce((h, l) => h + l.size * 1.1, 0) + 16);
  let y = 8;
  for (const l of lines) {
    ctx.font = l.font;
    ctx.textBaseline = 'top';
    if (l.box) { ctx.fillStyle = l.box; ctx.fillRect(0, y - 2, ctx.measureText(l.text).width + 24, l.size * 1.06); }
    ctx.fillStyle = l.colour;
    ctx.fillText(l.text, 12, y);
    y += l.size * 1.1;
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = maxAniso;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, transparent: true, depthTest: false }));
  sprite.scale.set(c.width * scale, c.height * scale, 1);
  sprite.center.set(0, 1);
  sprite.renderOrder = 2;
  return sprite;
}

const shade = (hex, opacity) => new THREE.MeshBasicMaterial({ color: hex, transparent: true, opacity, depthWrite: false });

// A bay's marks: its outline and number on the floor (the accent bay filled), and its sign at its near corner.
function marks(i, entry, lit) {
  const g = new THREE.Group();
  const { x, z } = place(i);
  g.position.set(x, 0.003, z);
  const line = 0.06, r = 0.4;
  const outline = rounded(bay.w, bay.l, r);
  outline.holes.push(rounded(bay.w - 2 * line, bay.l - 2 * line, r - line));
  const edge = new THREE.Mesh(new THREE.ShapeGeometry(outline, 8), shade(lit ? ACC : INK, lit ? 1 : 0.13));
  edge.rotation.x = -Math.PI / 2;
  g.add(edge);
  g.userData.edge = edge;
  const pad = new THREE.Mesh(new THREE.ShapeGeometry(rounded(bay.w, bay.l, r), 8), shade(ACC, lit ? 0.22 : 0));
  pad.rotation.x = -Math.PI / 2;
  pad.position.y = -0.001;
  pad.userData.skin = entry.name;
  g.add(pad);
  g.userData.pad = pad;
  const n = words([{ text: String(i + 1).padStart(2, '0'), font: '600 44px Teko', size: 44, colour: 'rgba(13, 15, 18, 0.22)' }], 0.006);
  n.position.set(bay.w / 2 - 0.1, 0.02, -bay.l / 2 + 0.55);
  g.add(n);
  const sign = words([
    { text: entry.title.toUpperCase(), font: '600 48px Teko', size: 48, colour: INK, box: lit ? ACC : null },
    { text: standing(entry).toUpperCase(), font: '400 28px Teko', size: 28, colour: 'rgba(13, 15, 18, 0.6)' },
  ]);
  sign.position.set(-bay.w / 2 + 0.3, 0.02, bay.l / 2 + 0.15);
  g.add(sign);
  return g;
}

// Where a skin stands, in one line: in the game since when, or its record's last event and the day it changed.
const day = (iso) => { const d = new Date(`${String(iso).slice(0, 10)}T12:00`); return isNaN(d) ? '' : `${d.getDate()} ${d.toLocaleString('en', { month: 'short' })}`; };  // the day as written, whatever the zone
function standing(entry) {
  if (entry.installed) return `In the game since ${day(entry.installed_at)}`;
  const s = entry.stand || {};
  const head = (s.last || '').split(/[(:]/)[0].trim();
  const open = (s.open || []).length;
  return [head, s.day ? day(s.day) : 'new', open ? (open === 1 ? '1 thing open' : `${open} things open`) : ''].filter(Boolean).join(' · ');
}

// ---- the cars ----

const textures = new Map();  // url -> Promise<Texture>; the stock maps once for every car

// A file of the viewer's data, asked again when the server drops a connection (many maps are asked at once).
async function get(url) {
  for (let k = 0; ; k++) {
    try {
      const r = await fetch(url, { cache: 'no-store' });
      if (r.ok) return r;
      if (k >= 2) throw new Error(`${r.status} for ${url}`);
    } catch (e) {
      if (k >= 2) throw e;
    }
    await new Promise((ok) => setTimeout(ok, 300 * (k + 1)));
  }
}

// A skin's map shrunk to its garage size (PNG: the size is in its header), the right way up for three.js.
function texture(slot, url, stamp) {
  const k = url.startsWith('stock/') ? url : `${url}?${stamp}`;
  if (!textures.has(k)) textures.set(k, (async () => {
    const blob = await (await get(`data/${k}`)).blob();
    const head = new DataView(await blob.slice(16, 24).arrayBuffer());
    const w = head.getUint32(0), h = head.getUint32(4);
    const s = Math.min(1, (WIDE[slot] || 512) / w);
    const bmp = await createImageBitmap(blob, { imageOrientation: 'flipY', premultiplyAlpha: 'none', colorSpaceConversion: 'none',
      resizeWidth: Math.round(w * s), resizeHeight: Math.round(h * s), resizeQuality: 'high' });
    const t = new THREE.Texture(bmp);
    t.flipY = false;
    t.colorSpace = COLOUR.has(slot) ? THREE.SRGBColorSpace : THREE.NoColorSpace;
    t.anisotropy = maxAniso;
    t.needsUpdate = true;
    return t;
  })());
  return textures.get(k);
}

async function park(entry, i) {
  const sk = await (await get(`data/skins/${encodeURIComponent(entry.name)}/skin.json`)).json();
  const tex = { Skin_AO: null, Details_N: null, Details_AO: null, Wheels_N: null, Wheels_AO: null, Glass_AO: null };  // not loaded: unseen on a small car
  await Promise.all(SLOTS.map(async (slot) => { if (sk.textures[slot]) tex[slot] = await texture(slot, sk.textures[slot], entry.stamp); }));
  const materials = kit.materials(tex);
  const group = new THREE.Group();
  for (const [name, geometry] of Object.entries(kit.geometries())) {
    const mesh = new THREE.Mesh(geometry, materials[name]);
    mesh.castShadow = name !== 'Glass';
    mesh.receiveShadow = true;
    group.add(mesh);
  }
  const { x, z } = place(i);
  group.position.set(x, lift, z);
  scene.add(group);
  const lit = entry.name === bench;
  const m = marks(i, entry, lit);
  scene.add(m);
  cars.set(entry.name, { group, materials, bay: i, stamp: entry.stamp, lit, marks: m });
  rouse();
}

function unpark(name) {
  const c = cars.get(name);
  if (!c) return;
  scene.remove(c.group, c.marks);
  for (const m of Object.values(c.materials)) m.dispose();  // ours; the maps stay cached, the geometries are the page's
  cars.delete(name);
  rouse();
}

// The lot as the list stands: cars added, gone or repainted, the bench lit, the camera on the whole.
async function fill() {
  const list = (await (await get('data/gallery.json')).json()).filter((e) => e.viewable);
  const now = await followed();
  following = now.stamp || null;
  bench = now.skin || null;
  const fit = kit.geometries();
  if (!bay.fit && fit) {
    const box = new THREE.Box3().setFromBufferAttribute(fit.Skin.attributes.position);
    for (const g of ['Details', 'Wheels']) box.union(new THREE.Box3().setFromBufferAttribute(fit[g].attributes.position));
    bay = { w: box.max.x - box.min.x + 0.7, l: box.max.z - box.min.z + 0.9, fit: true };
  }
  for (const name of [...cars.keys()]) {
    const i = list.findIndex((e) => e.name === name);
    const c = cars.get(name);
    if (i < 0 || c.stamp !== list[i].stamp || c.bay !== i || c.lit !== (name === bench)) unpark(name);
  }
  const rows = Math.ceil(list.length / ROW);
  view.target.set(0, 0, (rows - 1) * (bay.l + ROWGAP) / 2 + 1);
  view.height = Math.max(9, rows * (bay.l + ROWGAP) * 0.62 + 6);
  key.position.copy(view.target).addScaledVector(KEY, 40);
  key.target.position.copy(view.target);
  const reach = Math.max(ROW * (bay.w + GAP), rows * (bay.l + ROWGAP)) / 2 + 4;
  Object.assign(key.shadow.camera, { left: -reach, right: reach, top: reach, bottom: -reach, near: 1, far: 100 });
  key.shadow.camera.updateProjectionMatrix();
  aim();
  const t0 = performance.now();
  const order = list.map((e, i) => [e, i]).sort(([a], [b]) => (b.name === bench) - (a.name === bench));
  let first = 0;
  const status = (text) => { $('lotStatus').textContent = text; };
  status(list.length ? 'The cars are coming…' : 'No car painted yet');
  const queue = order.filter(([e]) => !cars.has(e.name));
  const workers = Array.from({ length: 2 }, async () => {  // two at a time: a car's maps in flight stay small
    while (queue.length) {
      const [e, i] = queue.shift();
      try {
        await park(e, i);
        first ||= performance.now() - t0;
      } catch (err) { console.error(`${e.name}: ${err.message || err}`); }
    }
  });
  await Promise.all(workers);
  status('');
  console.log(`garage: ${list.length} cars, the first in ${(first / 1000).toFixed(1)} s, all in ${((performance.now() - t0) / 1000).toFixed(1)} s`);
}

// ---- picking: the bay under the pointer ----

const ray = new THREE.Raycaster();
let hovered = null;
function under(e) {
  const canvas = $('lot');
  const r = canvas.getBoundingClientRect();
  ray.setFromCamera(new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1), camera);
  const hit = ray.intersectObjects([...cars.values()].map((c) => c.marks.userData.pad))[0];
  return hit ? hit.object.userData.skin : null;
}
function hover(e) {
  const name = under(e);
  if (name === hovered) return;
  for (const n of [hovered, name]) {
    const c = n && cars.get(n);
    if (c) c.marks.userData.edge.material.opacity = n === name ? (n === bench ? 1 : 0.45) : (n === bench ? 1 : 0.13);
  }
  hovered = name;
  $('lot').style.cursor = name ? 'pointer' : '';
  rouse();
}

// A car picked: the car itself, with that skin (the way a click in "My skins" goes).
function go(name) {
  note(name);
  openRoom('studio');
  if (window.viewer && window.viewer.onSkin) window.viewer.onSkin(name);
}

// Claude's painting, followed while the garage is open: a skin shown opens the car with it.
async function poll() {
  if ($('roomGarage').hidden) return;
  const now = await followed();
  if (now.stamp && following && now.stamp !== following) { following = now.stamp; go(now.skin); }
}

let opened = false;
export async function open(helpers) {
  openRoom = helpers.openRoom;
  if (!opened) {
    opened = true;
    await document.fonts.load('600 48px Teko');
    lift = ((await fetch('data/car.json').then((r) => r.json()).catch(() => ({}))).lift_cm || 0) / 100;
    build();
    every(POLL, poll);
  }
  resize();
  await fill();
  window.lab.ready = true;  // for Claude's pictures of the page (tool/snap.py --page)
}
