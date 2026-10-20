// The world, the Lab's front door (/ with no skin named, or ?room=garage): every skin the tool has painted for the
// viewer, parked on matte white in the lots the user named (skins/lots.json, by tool/gallery.py's `lot new`, `lot move`;
// a skin in no lot is in New), and the shop where a car is built, seen from one fixed angle (from the car's front-right,
// 32 degrees up; the user's pick of a mockup, 2026-10-19). Three levels, each a click (the user, 2026-10-20: a world like
// a game, click only, in levels):
//   the world   every lot with its cars and its name, and the shop; click a lot or the shop
//   a lot       its cars in numbered bays, each one's name and where it stands under it; click a car for the car itself
//   the shop    the takes of the open set (tool/sets.py), each on a lift, the one being painted lit with Claude at it
//               while the paint is on (steps.json painting); nothing open: the blank car. Click a take for the car.
// The crumb in the header (#crumb) is the way back up; ?lot=<name> and ?shop=1 keep the level in the address.
// Everything shown is the tool's: data/gallery.json (tool/gallery.py: the list, each skin's lot, its standing from
// tool/notes.py stands), data/lots.json (the lots in order), data/skins/<name>/skin.json (its paint as last shown),
// data/studio.json (the bench: the skin Claude painted last), /api/sets (the bench's sets), data/skins/<name>/steps.json.
// The cars are the page's own car (viewer.js's kit: its geometries, its materials without the studio's hooks, its day
// sky), each dressed in its skin's maps shrunk in the browser (1024 px wide for the colour, 512 for the rest; the full
// maps are half a gigabyte a car), the stock maps shared. Drag to pan, wheel or pinch to zoom; the angle never changes.
// While it's open the page follows Claude's painting as the car does: a skin shown opens the car with it; a change in
// the list, the lots or the shop is on the floor within 2 s.

import * as THREE from 'three';
import { kit } from './viewer.js';
import { $, every, followed, note, titleOf } from './lab-common.js';

const POLL = 1500, LIVE = 2000;
const DIR = new THREE.Vector3(-1, 0.9, 1).normalize();  // from a car to the camera
const KEY = new THREE.Vector3(0.555, 0.742, 0.377);  // the day's sun (viewer.js LOOKS.day), over the car's front left
const GAP = 1.0, ROWGAP = 2.8, LOTGAP = 4.0, WORLD_W = 34;  // metres: between bays, between rows (a sign sits there), between lots; a row of lots
const SHOP = { w: 14, d: 8, h: 3.4, gap: 5, pitch: 4.5, up: 0.55 };  // its floor, its walls, its distance from the lots, a lift from the next, a lift's height
const NEW = 'New';
const FLY = 600;  // ms, from one level to the next
const SLOTS = ['Skin_B', 'Skin_RM', 'Skin_Coat', 'Details_B', 'Details_RM', 'Wheels_B', 'Wheels_RM', 'Glass_T'];
const COLOUR = new Set(['Skin_B', 'Details_B', 'Wheels_B', 'Glass_T']);
const WIDE = { Skin_B: 1024, Details_B: 1024 };  // px wide; the others 512
const INK = '#0d0f12', ACC = '#e8ff47', CLAY = 0x8e8e93;

let renderer, scene, camera, key, floor, maxAniso, openRoom;
let wake = 0;
const rouse = (n = 2) => { wake = Math.max(wake, n); };
let bay = { w: 2.6, l: 4.8 };  // a bay, from the car's own size (fill)
let lift = 0;                  // the model's wheels, raised to the floor (car.json)
const cars = new Map();        // name -> { group, materials, stamp }
let bench = null;              // the skin Claude painted last
let following = null;          // studio.json's stamp when the world last looked
let level = { kind: 'world', name: null };
let world = null;              // the layout (fill): its lots, the shop, the floor's extent
let marks = null;              // every mark on the floor and the shop's walls, rebuilt by fill
let live = '';                 // the data's signature when the floor was last laid out
const view = { target: new THREE.Vector3(), height: 12 };  // what the camera looks at, and how many metres it shows top to bottom
let flight = null;             // { from, to, t0 }: the camera on its way to a level

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
  camera = new THREE.OrthographicCamera(-1, 1, 1, -1, -300, 300);
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
  $('crumbWorld').addEventListener('click', () => setLevel({ kind: 'world', name: null }));
  renderer.setAnimationLoop(() => {
    if ($('roomGarage').hidden) return;
    if (flight) {
      const t = Math.min(1, (performance.now() - flight.t0) / FLY), e = 1 - (1 - t) ** 3;
      view.target.lerpVectors(flight.from.target, flight.to.target, e);
      view.height = flight.from.height + (flight.to.height - flight.from.height) * e;
      if (t >= 1) flight = null;
      aim();
    }
    if (wake <= 0) return;
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

// The camera: above view.target along DIR, showing view.height metres top to bottom.
function aim() {
  const canvas = $('lot');
  const aspect = canvas.clientWidth / Math.max(1, canvas.clientHeight);
  camera.top = view.height / 2; camera.bottom = -view.height / 2;
  camera.right = view.height / 2 * aspect; camera.left = -camera.right;
  camera.position.copy(view.target).addScaledVector(DIR, 80);
  camera.lookAt(view.target);
  camera.updateProjectionMatrix();
  rouse();
}

// The camera on its way to show a box of the floor whole (x, z extents), with a margin, at the angle.
function fly(box, margin = 3) {
  const canvas = $('lot');
  const aspect = canvas.clientWidth / Math.max(1, canvas.clientHeight);
  const forward = DIR.clone().negate();
  const right = new THREE.Vector3().crossVectors(forward, new THREE.Vector3(0, 1, 0)).normalize();
  const up = new THREE.Vector3().crossVectors(right, forward).normalize();
  let u0 = Infinity, u1 = -Infinity, v0 = Infinity, v1 = -Infinity;
  for (const x of [box.x0, box.x1]) for (const z of [box.z0, box.z1]) for (const y of [0, box.h || 0]) {
    const p = new THREE.Vector3(x, y, z);
    const u = p.dot(right), v = p.dot(up);
    u0 = Math.min(u0, u); u1 = Math.max(u1, u); v0 = Math.min(v0, v); v1 = Math.max(v1, v);
  }
  const to = {
    target: new THREE.Vector3((box.x0 + box.x1) / 2, 0, (box.z0 + box.z1) / 2),
    height: Math.max(8, v1 - v0 + margin, (u1 - u0 + margin) / aspect),
  };
  if (!world || !world.flown) { view.target.copy(to.target); view.height = to.height; flight = null; aim(); return; }
  flight = { from: { target: view.target.clone(), height: view.height }, to, t0: performance.now() };
  rouse();
}

// Drag pans across the floor, the wheel or a pinch zooms; the angle never changes.
function hand(canvas) {
  const down = new Map();  // pointerId -> {x, y}
  let pinch = 0;
  canvas.addEventListener('pointerdown', (e) => { down.set(e.pointerId, { x: e.clientX, y: e.clientY }); canvas.setPointerCapture(e.pointerId); pinch = 0; flight = null; });
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
      const hit = under(e);
      if (hit) go(hit);
    }
  };
  canvas.addEventListener('pointerup', up);
  canvas.addEventListener('pointercancel', up);
  canvas.addEventListener('wheel', (e) => { e.preventDefault(); flight = null; zoom(Math.exp(e.deltaY * 0.0015)); }, { passive: false });
}

function zoom(by) {
  view.height = Math.min(120, Math.max(5, view.height * by));
  aim();
}

// ---- the marks: shapes, words, the car's stand-ins ----

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
const sign = (title, line, lit = false, scale) => words([
  { text: title.toUpperCase(), font: '600 48px Teko', size: 48, colour: INK, box: lit ? ACC : null },
  ...(line ? [{ text: line.toUpperCase(), font: '400 28px Teko', size: 28, colour: 'rgba(13, 15, 18, 0.6)' }] : []),
], scale);

const shade = (hex, opacity) => new THREE.MeshBasicMaterial({ color: hex, transparent: true, opacity, depthWrite: false });
const matte = (c, roughness = 1, metalness = 0) => new THREE.MeshStandardMaterial({ color: c, roughness, metalness });
function box(w, h, d, mat, x = 0, y = 0, z = 0) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  m.position.set(x, y, z);
  m.castShadow = m.receiveShadow = true;
  return m;
}

// A flat shape on the floor, as an outline (a line of `line` metres) or a fill.
function flat(w, l, r, mat, line = 0) {
  const shape = rounded(w, l, r);
  if (line) shape.holes.push(rounded(w - 2 * line, l - 2 * line, r - line));
  const m = new THREE.Mesh(new THREE.ShapeGeometry(shape, 8), mat);
  m.rotation.x = -Math.PI / 2;
  return m;
}

// A bay's marks at (x, z): its outline and number (the accent bay filled), its sign at its near corner, and the pad a
// click lands on (userData.go). `at`: the level its words show at.
function bayMarks(g, x, z, i, entry, lit, at) {
  const line = 0.06, r = 0.4;
  const edge = flat(bay.w, bay.l, r, shade(lit ? ACC : INK, lit ? 1 : entry ? 0.13 : 0.07), line);
  edge.position.set(x, 0.003, z);
  g.add(edge);
  const pad = flat(bay.w, bay.l, r, shade(ACC, lit ? 0.22 : 0));
  pad.position.set(x, 0.002, z);
  g.add(pad);
  if (i != null) {
    const n = words([{ text: String(i).padStart(2, '0'), font: '600 44px Teko', size: 44, colour: 'rgba(13, 15, 18, 0.22)' }], 0.006);
    n.position.set(x + bay.w / 2 - 0.1, 0.02, z - bay.l / 2 + 0.55);
    n.userData.at = at;
    g.add(n);
  }
  if (!entry) return pad;
  pad.userData.go = { kind: 'car', name: entry.name };
  pad.userData.edge = edge;
  pad.userData.rest = lit ? 1 : 0.13;
  const s = sign(entry.title, standing(entry), lit);
  s.position.set(x - bay.w / 2 + 0.3, 0.02, z + bay.l / 2 + 0.15);
  s.userData.at = at;
  g.add(s);
  return pad;
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

// A lift at (x, z): two rails the car's wheels rest on, and a bar at its far end.
function liftAt(g, x, z) {
  const steel = matte(0x9a9ca2, 0.5, 0.4);
  const up = SHOP.up;
  g.add(box(0.5, up, bay.l - 1.2, steel, x - 0.78, up / 2, z));
  g.add(box(0.5, up, bay.l - 1.2, steel, x + 0.78, up / 2, z));
  g.add(box(2.2, 0.06, 0.4, steel, x, up, z - bay.l / 2 + 0.6));
}

// Claude: a small figure in overalls and the accent cap, the spray gun on, its mist in the air.
function figure(x, z) {
  const g = new THREE.Group();
  const suit = matte(0xe4e4e7), skin = matte(0xd9b08c), cap = matte(0xe8ff47);
  const body = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.26, 0.75, 16), suit);
  body.position.y = 0.62; body.castShadow = true; g.add(body);
  for (const dx of [-0.1, 0.1]) g.add(box(0.14, 0.3, 0.14, suit, dx, 0.15, 0));
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.2, 20, 16), skin);
  head.position.y = 1.2; head.castShadow = true; g.add(head);
  g.add(box(0.44, 0.1, 0.44, cap, 0, 1.36, 0));
  g.add(box(0.46, 0.04, 0.2, cap, 0, 1.31, 0.3));
  g.add(box(0.12, 0.12, 0.5, suit, 0.28, 0.85, 0.2));
  g.add(box(0.1, 0.16, 0.22, matte(0x2a2c30, 0.8), 0.28, 0.85, 0.52));
  const mist = new THREE.MeshStandardMaterial({ color: 0xe8ff47, roughness: 1, transparent: true, opacity: 0.45 });
  for (let k = 0; k < 7; k++) {
    const p = new THREE.Mesh(new THREE.SphereGeometry(0.05 + k * 0.025, 10, 8), mist);
    p.position.set(0.28 + Math.sin(k * 2.1) * 0.025 * k, 0.8 + Math.cos(k * 1.7) * 0.06 * k, 0.75 + k * 0.17);
    g.add(p);
  }
  g.position.set(x, 0, z);
  g.rotation.y = -Math.PI / 2;  // facing the car's flank, from the near side
  return g;
}

// The shop's floor and walls (the near one low, no roof, a lintel), its bench and desk, its lamp lit while the paint
// is on, a lift for each take with its sign, the pad of each and of the shop itself.
function shopMarks(g, shop) {
  const { x: X, z: Z } = shop;
  const W = SHOP.w, D = SHOP.d, H = SHOP.h;
  const plaster = matte(0xdedee1), wood = matte(0xcfc3b0), steel = matte(0x9a9ca2, 0.5, 0.4);
  const inner = new THREE.Mesh(new THREE.PlaneGeometry(W, D), matte(new THREE.Color(0.42, 0.42, 0.43)));
  inner.rotation.x = -Math.PI / 2; inner.position.set(X, 0.002, Z); inner.receiveShadow = true; g.add(inner);
  const wall = (w, h, d, x, z) => box(w, h, d, plaster, x, h / 2, z);
  g.add(wall(W + 0.4, H, 0.2, X, Z - D / 2 - 0.1));
  g.add(wall(0.2, H, D, X + W / 2 + 0.1, Z));
  g.add(wall(0.2, 0.9, D, X - W / 2 - 0.1, Z));
  g.add(wall(W + 0.4, 0.9, 0.2, X, Z + D / 2 + 0.1));
  g.add(box(W + 0.4, 0.35, 0.2, plaster, X, H - 0.18, Z + D / 2 + 0.1));
  g.add(box(0.2, H, 0.2, plaster, X - W / 2 - 0.1, H / 2, Z + D / 2 + 0.1));
  g.add(box(6, 0.08, 0.3, shop.painting ? matte(0xe8ff47) : plaster, X, H - 0.5, Z - D / 4));
  // the bench against the back wall, its paint; the desk, where the words arrive
  g.add(box(4.0, 0.08, 0.9, wood, X - 4.5, 0.9, Z - D / 2 + 0.6));
  for (const dx of [-6.4, -2.6]) for (const dz of [-D / 2 + 0.25, -D / 2 + 0.95]) g.add(box(0.1, 0.86, 0.1, steel, X + dx, 0.43, Z + dz));
  [0xf0c020, 0x1a1c20, 0xe8ff47, 0x2b2f36, 0xc69a6a, 0xff7a1a].forEach((c, k) => {
    const t = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.13, 0.28, 16), matte(c, 0.5));
    t.position.set(X - 6.1 + k * 0.5, 1.08, Z - D / 2 + 0.6); t.castShadow = true; g.add(t);
  });
  g.add(box(3.6, 1.0, 0.2, wood, X - 4.5, 2.2, Z - D / 2 + 0.1));
  g.add(box(2.2, 0.08, 0.9, wood, X + 4.5, 0.78, Z - D / 2 + 0.6));
  for (const dx of [3.5, 5.5]) for (const dz of [-D / 2 + 0.25, -D / 2 + 0.95]) g.add(box(0.1, 0.74, 0.1, steel, X + dx, 0.37, Z + dz));
  g.add(box(1.1, 0.68, 0.06, matte(0x1a1c20, 0.5), X + 4.5, 1.25, Z - D / 2 + 0.5));
  g.add(box(0.6, 0.1, 0.4, steel, X + 4.5, 0.86, Z - D / 2 + 0.5));
  // the lifts: one a take, or one for the blank car
  shop.spots.forEach((spot, k) => {
    liftAt(g, spot.x, spot.z);
    const t = shop.takes[k];
    const lit = !!t && t.skin === shop.painting;
    const edge = flat(bay.w + 0.6, bay.l + 0.4, 0.4, shade(lit ? ACC : INK, lit ? 1 : 0.13), 0.06);
    edge.position.set(spot.x, 0.004, spot.z); g.add(edge);
    const pad = flat(bay.w + 0.6, bay.l + 0.4, 0.4, shade(ACC, lit ? 0.22 : 0));
    pad.position.set(spot.x, 0.003, spot.z); g.add(pad);
    if (t) {
      pad.userData.go = { kind: 'car', name: t.skin, where: 'shop' };
      pad.userData.edge = edge;
      pad.userData.rest = lit ? 1 : 0.13;
      const line = lit ? 'Claude is painting' : t.entry ? standing(t.entry) : 'Not painted yet';
      const s = sign(t.key ? `${t.key} · ${t.title}` : t.title, line, lit);
      s.position.set(spot.x - bay.w / 2 - 0.1, 0.02, spot.z + bay.l / 2 + 0.45);
      s.userData.at = 'shop';
      g.add(s);
    }
    if (lit) g.add(figure(spot.x - 1.6, spot.z - 0.6));
  });
  const line = shop.painting ? `Claude is painting ${titleOf(shop.painting)}` : shop.takes.length ? 'For you to pick: click a take for the car' : 'Say what you want in the chat';
  const s = sign('The shop', line, !!shop.painting, 0.0105);
  s.position.set(X - W / 2 - 0.1, 0.02, Z + D / 2 + 0.7);
  g.add(s);
  const pad = flat(W + 0.4, D + 0.4, 0.3, shade(ACC, 0));
  pad.position.set(X, 0.001, Z);
  pad.userData.go = { kind: 'shop' };
  g.add(pad);
}

// A lot's marks: its outline and name, its bays (the empty ones fainter), the pad a click lands on.
function lotMarks(g, lot) {
  const edge = flat(lot.w, lot.l, 0.8, shade(INK, 0.3), 0.1);
  edge.position.set(lot.x, 0.004, lot.z);
  g.add(edge);
  const pad = flat(lot.w, lot.l, 0.8, shade(ACC, 0));
  pad.position.set(lot.x, 0.001, lot.z);
  pad.userData.go = { kind: 'lot', name: lot.name };
  pad.userData.edge = edge;
  pad.userData.rest = 0.3;
  g.add(pad);
  const n = lot.entries.length;
  const title = words([
    { text: lot.name.toUpperCase(), font: '600 48px Teko', size: 48, colour: INK },
    { text: `${n} ${n === 1 ? 'car' : 'cars'}`.toUpperCase(), font: '400 28px Teko', size: 28, colour: 'rgba(13, 15, 18, 0.6)' },
  ], 0.014);
  title.position.set(lot.x - lot.w / 2 + 0.4, 0.02, lot.z + lot.l / 2 + 0.3);
  g.add(title);
  for (let i = 0; i < lot.cols * lot.rows; i++) {
    const { x, z } = lot.bay(i);
    const entry = lot.entries[i];
    bayMarks(g, x, z, i + 1, entry, !!entry && entry.name === bench, 'lot');
    if (!entry && i === n) {
      const w = words([{ text: 'ROOM FOR THE NEXT CAR', font: '400 28px Teko', size: 28, colour: 'rgba(13, 15, 18, 0.4)' }], 0.006);
      w.position.set(x - bay.w / 2 + 0.3, 0.02, z + bay.l / 2 + 0.15);
      w.userData.at = 'lot';
      g.add(w);
    }
  }
}

// ---- the layout: the lots in rows, the shop beyond them ----

function layout(list, lotsFile, shop) {
  const byLot = new Map(lotsFile.map((l) => [l.name, []]));
  byLot.set(NEW, []);
  const inShop = new Set(shop.takes.map((t) => t.skin));
  for (const e of list) {
    if (inShop.has(e.name)) continue;
    byLot.get(e.lot && byLot.has(e.lot) ? e.lot : NEW).push(e);
  }
  const lots = [];
  let x = -WORLD_W / 2, z = 0, rowL = 0;
  for (const [name, entries] of byLot) {
    const n = entries.length, cols = Math.min(4, n + 1), rows = Math.ceil((n + 1) / cols);
    const w = cols * (bay.w + GAP) + GAP, l = rows * (bay.l + ROWGAP) + 0.6;
    if (x + w > WORLD_W / 2 && lots.length) { x = -WORLD_W / 2; z += rowL + LOTGAP; rowL = 0; }
    const lot = { name, entries, cols, rows, w, l, x: x + w / 2, z: z + l / 2 };
    lot.bay = (i) => ({ x: lot.x - w / 2 + GAP + bay.w / 2 + (i % cols) * (bay.w + GAP), z: lot.z - l / 2 + 0.6 + bay.l / 2 + Math.floor(i / cols) * (bay.l + ROWGAP) });
    lot.box = { x0: lot.x - w / 2, x1: lot.x + w / 2, z0: lot.z - l / 2, z1: lot.z + l / 2 + 1.2 };
    lots.push(lot);
    x += w + LOTGAP; rowL = Math.max(rowL, l);
  }
  const k = Math.max(1, shop.takes.length);
  shop.x = 0; shop.z = -(SHOP.d / 2 + SHOP.gap);
  shop.spots = Array.from({ length: k }, (_, i) => ({ x: shop.x + (i - (k - 1) / 2) * SHOP.pitch, y: SHOP.up, z: shop.z }));
  shop.box = { x0: shop.x - SHOP.w / 2 - 1, x1: shop.x + SHOP.w / 2 + 1, z0: shop.z - SHOP.d / 2 - 0.5, z1: shop.z + SHOP.d / 2 + 2, h: SHOP.h };
  const x1 = Math.max(shop.box.x1, ...lots.map((l) => l.box.x1)), x0 = Math.min(shop.box.x0, ...lots.map((l) => l.box.x0));
  return { lots, shop, box: { x0, x1, z0: shop.box.z0, z1: z + rowL + 1.5, h: SHOP.h } };
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
const json = async (url, fallback) => { try { return await (await get(url)).json(); } catch { return fallback; } };

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

function carOf(materials) {
  const group = new THREE.Group();
  for (const [name, geometry] of Object.entries(kit.geometries())) {
    const mesh = new THREE.Mesh(geometry, materials[name]);
    mesh.castShadow = name !== 'Glass';
    mesh.receiveShadow = true;
    group.add(mesh);
  }
  return group;
}

async function park(entry, spot) {
  const sk = await (await get(`data/skins/${encodeURIComponent(entry.name)}/skin.json`)).json();
  const tex = { Skin_AO: null, Details_N: null, Details_AO: null, Wheels_N: null, Wheels_AO: null, Glass_AO: null };  // not loaded: unseen on a small car
  await Promise.all(SLOTS.map(async (slot) => { if (sk.textures[slot]) tex[slot] = await texture(slot, sk.textures[slot], entry.stamp); }));
  const materials = kit.materials(tex);
  const group = carOf(materials);
  group.position.set(spot.x, lift + spot.y, spot.z);
  scene.add(group);
  cars.set(entry.name, { group, materials, stamp: entry.stamp });
  rouse();
}

// The blank car: the one not painted yet, in clay.
function blank(name, spot) {
  const dark = matte(0x2a2c30, 0.8);
  const materials = { Skin: matte(CLAY, 0.9), Details: dark, Wheels: dark, Glass: new THREE.MeshStandardMaterial({ color: 0x1a1c20, roughness: 0.3, transparent: true, opacity: 0.6 }) };
  const group = carOf(materials);
  group.position.set(spot.x, lift + spot.y, spot.z);
  scene.add(group);
  cars.set(name, { group, materials, stamp: 'blank' });
  rouse();
}

function unpark(name) {
  const c = cars.get(name);
  if (!c) return;
  scene.remove(c.group);
  for (const m of Object.values(c.materials)) m.dispose();  // ours; the maps stay cached, the geometries are the page's
  cars.delete(name);
  rouse();
}

// The shop as the tool's data stands: the bench (studio.json), whether its paint is on (steps.json), the takes of its
// open set (/api/sets). The bench car being painted outside a set is a take of its own, on the lift.
async function shopData() {
  const now = await followed();
  bench = now.skin || null;
  following = now.stamp || null;
  const shop = { takes: [], painting: null };
  if (!bench) return shop;
  const steps = await json(`data/skins/${encodeURIComponent(bench)}/steps.json`, {});
  shop.painting = steps.painting ? bench : null;
  const sets = await json(`api/sets?skin=${encodeURIComponent(bench)}`, null);
  const open = ((sets && sets.sets) || []).find((s) => s.state === 'painting' || s.state === 'open');
  if (open) shop.takes = open.options.map((o) => ({ key: o.key, title: o.title, skin: o.skin }));
  if (shop.painting && !shop.takes.some((t) => t.skin === shop.painting)) shop.takes.push({ key: '', title: titleOf(bench), skin: bench });
  return shop;
}

// The floor as the tool's data stands: the lots laid out, the shop, every car in its spot (parked when new or
// repainted, moved when its spot changed), the marks drawn again, the camera on the level. Nothing changed: nothing done.
async function fill() {
  const [all, lotsFile, shop] = await Promise.all([json('data/gallery.json', []), json('data/lots.json', { lots: [] }), shopData()]);
  const list = all.filter((e) => e.viewable);
  const byName = new Map(all.map((e) => [e.name, e]));
  for (const t of shop.takes) t.entry = byName.get(t.skin);
  const sig = JSON.stringify([list.map((e) => [e.name, e.stamp, e.lot, standing(e)]), lotsFile.lots, shop.takes.map((t) => t.skin), shop.painting, bench]);
  if (sig === live) return;
  live = sig;
  const fit = kit.geometries();
  if (!bay.fit && fit) {
    const b = new THREE.Box3().setFromBufferAttribute(fit.Skin.attributes.position);
    for (const g of ['Details', 'Wheels']) b.union(new THREE.Box3().setFromBufferAttribute(fit[g].attributes.position));
    bay = { w: b.max.x - b.min.x + 0.7, l: b.max.z - b.min.z + 0.9, fit: true };
  }
  const flown = world && world.flown;
  world = layout(list, lotsFile.lots, shop);
  world.flown = flown;
  // every car's spot: in its bay, or on a lift in the shop
  const spots = new Map();
  for (const lot of world.lots) lot.entries.forEach((e, i) => spots.set(e.name, { ...lot.bay(i), y: 0, entry: e }));
  shop.takes.forEach((t, k) => { if (t.entry && t.entry.viewable) spots.set(t.skin, { ...shop.spots[k], entry: t.entry }); else spots.set(`blank:${t.skin}`, { ...shop.spots[k], blank: true }); });
  if (!shop.takes.length) spots.set('blank:', { ...shop.spots[0], blank: true });
  for (const name of [...cars.keys()]) {
    const spot = spots.get(name);
    const c = cars.get(name);
    if (!spot || (!spot.blank && c.stamp !== spot.entry.stamp)) { unpark(name); continue; }
    c.group.position.set(spot.x, lift + spot.y, spot.z);
  }
  if (marks) {
    scene.remove(marks);
    marks.traverse((o) => { if (o.material) { if (o.material.map) o.material.map.dispose(); o.material.dispose(); } if (o.geometry) o.geometry.dispose(); });
  }
  marks = new THREE.Group();
  for (const lot of world.lots) lotMarks(marks, lot);
  shopMarks(marks, world.shop);
  scene.add(marks);
  showWords();
  const reach = Math.max(world.box.x1 - world.box.x0, world.box.z1 - world.box.z0) / 2 + 6;
  key.position.set((world.box.x0 + world.box.x1) / 2, 0, (world.box.z0 + world.box.z1) / 2).addScaledVector(KEY, 60);
  key.target.position.set((world.box.x0 + world.box.x1) / 2, 0, (world.box.z0 + world.box.z1) / 2);
  Object.assign(key.shadow.camera, { left: -reach, right: reach, top: reach, bottom: -reach, near: 1, far: 140 });
  key.shadow.camera.updateProjectionMatrix();
  frame();
  rouse();
  const t0 = performance.now();
  const status = (text) => { $('lotStatus').textContent = text; };
  const queue = [...spots].filter(([name]) => !cars.has(name)).sort(([a], [b]) => (b === bench) - (a === bench));
  if (queue.length) status(list.length ? 'The cars are coming…' : 'No car painted yet');
  let first = 0;
  const workers = Array.from({ length: 2 }, async () => {  // two at a time: a car's maps in flight stay small
    while (queue.length) {
      const [name, spot] = queue.shift();
      try {
        if (spot.blank) blank(name, spot); else await park(spot.entry, spot);
        first ||= performance.now() - t0;
      } catch (err) { console.error(`${name}: ${err.message || err}`); }
    }
  });
  await Promise.all(workers);
  status('');
  if (first) console.log(`the world: ${list.length} cars, the first in ${(first / 1000).toFixed(1)} s, all in ${((performance.now() - t0) / 1000).toFixed(1)} s`);
}

// ---- the levels ----

// The words that show at this level: a car's sign and number at its lot or in the shop, never from the world.
function showWords() {
  if (!marks) return;
  marks.traverse((o) => { if (o.userData.at) o.visible = o.userData.at === level.kind; });
  rouse();
}

// The camera on this level: the world whole, the lot, or the shop.
function frame() {
  if (!world) return;
  const lot = level.kind === 'lot' && world.lots.find((l) => l.name === level.name);
  if (level.kind === 'lot' && !lot) { level = { kind: 'world', name: null }; }
  fly(level.kind === 'shop' ? world.shop.box : lot ? lot.box : world.box, level.kind === 'world' ? 4 : 2);
  world.flown = true;
  $('crumb').hidden = level.kind === 'world';
  $('crumbHere').textContent = level.kind === 'shop' ? 'The shop' : level.name || '';
}

function setLevel(l) {
  level = l;
  const u = new URL(location.href);
  if (level.kind === 'lot') u.searchParams.set('lot', level.name); else u.searchParams.delete('lot');
  if (level.kind === 'shop') u.searchParams.set('shop', '1'); else u.searchParams.delete('shop');
  history.replaceState(null, '', u);
  showWords();
  frame();
}

// What a click can land on at this level: the lots and the shop from the world, the cars in a lot or the shop's takes.
function pads() {
  if (!marks) return [];
  const want = level.kind === 'world' ? (p) => p.kind !== 'car'
    : level.kind === 'lot' ? (p) => p.kind === 'car' && !p.where && world.lots.find((l) => l.name === level.name).entries.some((e) => e.name === p.name)
      : (p) => p.kind === 'car' && p.where === 'shop';
  return marks.children.filter((o) => o.userData.go && want(o.userData.go));
}

// ---- picking: the pad under the pointer ----

const ray = new THREE.Raycaster();
let hovered = null;
function under(e) {
  const canvas = $('lot');
  const r = canvas.getBoundingClientRect();
  ray.setFromCamera(new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1), camera);
  const hit = ray.intersectObjects(pads())[0];
  return hit ? hit.object : null;
}
function hover(e) {
  const pad = under(e);
  if (pad === hovered) return;
  for (const p of [hovered, pad]) {
    if (p && p.userData.edge) p.userData.edge.material.opacity = p === pad ? Math.max(p.userData.rest, 0.5) : p.userData.rest;
  }
  hovered = pad;
  $('lot').style.cursor = pad ? 'pointer' : '';
  rouse();
}

// A pad picked: down a level, or the car itself with that skin (the way a click in "My skins" goes).
function go(pad) {
  const { kind, name } = pad.userData.go;
  if (kind === 'lot') return setLevel({ kind: 'lot', name });
  if (kind === 'shop') return setLevel({ kind: 'shop', name: null });
  note(name);
  openRoom('studio');
  if (window.viewer && window.viewer.onSkin) window.viewer.onSkin(name);
}

// Claude's painting, followed while the world is open: a skin shown opens the car with it.
async function poll() {
  if ($('roomGarage').hidden) return;
  const now = await followed();
  if (now.stamp && following && now.stamp !== following) {
    following = now.stamp;
    note(now.skin);
    openRoom('studio');
    if (window.viewer && window.viewer.onSkin) window.viewer.onSkin(now.skin);
  }
}

let opened = false;
export async function open(helpers) {
  openRoom = helpers.openRoom;
  const params = new URLSearchParams(location.search);
  level = params.get('shop') ? { kind: 'shop', name: null } : params.get('lot') ? { kind: 'lot', name: params.get('lot') } : { kind: 'world', name: null };
  if (!opened) {
    opened = true;
    await document.fonts.load('600 48px Teko');
    lift = ((await fetch('data/car.json').then((r) => r.json()).catch(() => ({}))).lift_cm || 0) / 100;
    build();
    every(POLL, poll);
    every(LIVE, () => $('roomGarage').hidden ? null : fill());
  }
  resize();
  live = '';  // laid out again: the data may have moved while another room was open
  await fill();
  window.lab.ready = true;  // for Claude's pictures of the page (tool/snap.py --page)
}
