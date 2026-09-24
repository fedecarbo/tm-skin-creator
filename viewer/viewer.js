// The skin viewer: the car in a photo studio, wearing one skin, by day or night.
//   /?skin=<name>          the skin prepared by `python -m tool.view <name>`
//   /?skin=<name>&snap=1   no controls on screen, for Claude's snapshots (tool/snap.py)
// Data comes from /data/ (see tool/view.py): car.json + car.bin (every triangle corner tagged
// with its part), parts.json (the named parts), <Set>_Shared.png (texels several parts share),
// the two lighting HDRIs, and skins/<name>/skin.json, which gives the URL of every texture slot.

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { HDRLoader } from 'three/addons/loaders/HDRLoader.js';

const params = new URLSearchParams(location.search);
const skinName = params.get('skin') || 'TSC_Test';
const snap = params.has('snap');
document.body.classList.toggle('snap', snap);
const statusBox = document.getElementById('status');

// Coordinates: metres, y up, the car faces +z, and its left is +x. The wheels touch y = 0.
const CENTRE = new THREE.Vector3(0, 0.44, 0.27);
const VIEWS = {  // direction from the car's centre to the camera, and distance
  front: { dir: [0.62, 0.3, 0.72], dist: 6.4 },  // front three-quarter, from the car's left
  rear: { dir: [-0.62, 0.3, -0.72], dist: 6.4 },  // rear three-quarter, from the car's right
  left: { dir: [1, 0.06, 0], dist: 6.2 },
  right: { dir: [-1, 0.06, 0], dist: 6.2 },
  top: { dir: [0, 1, -0.0001], dist: 7.6 },  // looking down, the car's front at the top
};
// The look the user chose on 2026-09-24, after a studio they like. A neutral photo studio lights
// the car and shows in its reflections. Night is a moonlit sky with a dim blue key. Both HDRIs
// are from Poly Haven (CC0). key: the one light that casts a shadow. The room around the car is a
// plain grey cove lit by the same light, so it darkens with the car (the user's wish).
const LOOKS = {
  day: { hdr: 'studio_small_09', env: 1, key: 1.1, keyColour: 0xfff4e8 },
  night: { hdr: 'dikhololo_night', env: 2.2, key: 0.22, keyColour: 0xb9c9ff },
};
const KEY_FROM = new THREE.Vector3(0.55, 1, 0.35).normalize();  // above the car's front left

// Settings any of which can be tried from the address, e.g. ?exposure=1&env=0.8, when matching
// the game again. env and key scale both looks. room: how light the room's grey is (linear).
const TUNE = { exposure: 0.9, env: 1, key: 1, coat: 1, room: 0.035 };
for (const key of Object.keys(TUNE)) if (params.has(key)) TUNE[key] = Number(params.get(key));

// The Details_I alpha codes (CLAUDE.md): how bright each kind of glow is on a car that's just
// driving, by day and at night, and the colour the game supplies for codes whose RGB must be
// grey. From the user's game screenshots (2026-09-24, CHECKLIST.md): brake lights glow dimly
// all the time and flare towards white when braking (checkpoint 1's stock strips); the front lights are
// bright white by day and at night; "always on" keeps its colour; "night only" comes on at night
// (and on a dusk map); energy is dim and tinted by the game (red for this player). Brake heat,
// turbo, exhaust heat and boost weren't seen to light up, so they stay off.
const GLOW = [
  { code: 0, day: 1.2, night: 1.8 },  // brake lights: dim all the time, brighter when braking
  { code: 32, day: 0.6, night: 1, tint: [1, 0.2, 0.2] },  // energy, tinted by the game
  { code: 64, day: 0, night: 0 },  // brake heat: only when braking hard
  { code: 96, day: 1.2, night: 1.8 },  // always glowing, its own colour
  { code: 128, day: 4, night: 8 },  // front lights, bright white day and night
  { code: 160, day: 0, night: 0, tint: [0.15, 1, 0.3] },  // turbo colour, green in the game
  { code: 192, day: 0, night: 0 },  // exhaust heat: only during turbo
  { code: 224, day: 0, night: 0 },  // boost colour
  { code: 255, day: 0, night: 1.4 },  // night only. Coloured glows above ~1.5 wash out under the tone mapping
];
const glowUniforms = {
  glowGain: { value: GLOW.map((g) => g.day) },
  glowTint: { value: GLOW.map((g) => new THREE.Vector3(...(g.tint || [1, 1, 1]))) },
};

// ---- Renderer, camera, controls ----

const canvas = document.getElementById('view');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(snap ? 1 : Math.min(window.devicePixelRatio, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = TUNE.exposure;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap;  // soft already; PCFSoftShadowMap is gone in 0.186
const maxAniso = renderer.capabilities.getMaxAnisotropy();

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(32, 1, 0.05, 400);
const controls = new OrbitControls(camera, canvas);
controls.target.copy(CENTRE);
controls.enableDamping = true;
controls.minDistance = 1;
controls.maxDistance = 18;
// No limit on the angle: skins paint the underside too, and the floor isn't drawn from below.

// view: a name from VIEWS, or { dir, dist, target } for a close look.
function setView(view) {
  const v = typeof view === 'string' ? VIEWS[view] : view;
  controls.target.set(...(v.target || CENTRE.toArray()));
  camera.position.copy(controls.target).addScaledVector(new THREE.Vector3(...v.dir).normalize(), v.dist);
  controls.update();
}

function resize() {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
window.addEventListener('resize', resize);

// ---- Studio: the key light and the room ----

const key = new THREE.DirectionalLight(LOOKS.day.keyColour, LOOKS.day.key);
key.position.copy(CENTRE).addScaledVector(KEY_FROM, 15);
key.target.position.copy(CENTRE);
key.castShadow = true;
key.shadow.mapSize.set(2048, 2048);
Object.assign(key.shadow.camera, { left: -3.5, right: 3.5, top: 3.5, bottom: -3.5, near: 1, far: 40 });
key.shadow.bias = -0.0004;
key.shadow.normalBias = 0.02;
key.shadow.radius = 3;
scene.add(key, key.target);

scene.background = new THREE.Color('#050506');  // seen only from under the floor

// The room: a seamless cove, the floor curving up into the walls and a ceiling, all one matte
// grey lit by the same light as the car. Floor radius 14 m, curve 6 m, 14 m high.
function addRoom() {
  const profile = [new THREE.Vector2(0, 0), new THREE.Vector2(14, 0)];
  for (let i = 1; i <= 12; i++) {
    const t = (i / 12) * (Math.PI / 2);
    profile.push(new THREE.Vector2(14 + 6 * Math.sin(t), 6 - 6 * Math.cos(t)));
  }
  profile.push(new THREE.Vector2(20, 14), new THREE.Vector2(0, 14));
  // The lathe's faces point out of the room, so draw their backs: from under the floor it
  // isn't drawn at all, and the car's underside stays in view.
  const material = new THREE.MeshStandardMaterial({ roughness: 0.95, metalness: 0, side: THREE.BackSide });
  material.color.setScalar(TUNE.room);
  const room = new THREE.Mesh(new THREE.LatheGeometry(profile, 128), material);
  room.position.z = CENTRE.z;
  room.receiveShadow = true;
  scene.add(room);
  // A soft dark patch under the car, where the room's light can't reach.
  const c = document.createElement('canvas');
  c.width = c.height = 256;
  const g = c.getContext('2d');
  const grad = g.createRadialGradient(128, 128, 0, 128, 128, 128);
  grad.addColorStop(0, 'rgba(0,0,0,0.8)');
  grad.addColorStop(0.55, 'rgba(0,0,0,0.5)');
  grad.addColorStop(1, 'rgba(0,0,0,0)');
  g.fillStyle = grad;
  g.fillRect(0, 0, 256, 256);
  const contact = new THREE.Mesh(new THREE.PlaneGeometry(2.6, 4.6),
    new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(c), transparent: true, depthWrite: false }));
  contact.rotation.x = -Math.PI / 2;
  contact.position.set(0, 0.004, CENTRE.z);
  scene.add(contact);
}

const envMaps = {};  // day, night -> HDRI texture

async function loadLighting() {
  const loader = new HDRLoader();
  await Promise.all(Object.entries(LOOKS).map(async ([id, look]) => {
    const hdr = await loader.loadAsync(`data/${look.hdr}.hdr`);
    hdr.mapping = THREE.EquirectangularReflectionMapping;
    envMaps[id] = hdr;
  }));
}

// ---- The car ----

const parts = {};  // Skin, Details, Wheels, Glass -> mesh

async function loadMeshes() {
  const meta = await (await fetch('data/car.json')).json();
  const bin = await (await fetch('data/car.bin')).arrayBuffer();
  const out = {};
  for (const m of meta.meshes) {  // one vertex per triangle corner, so parts have hard edges
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(bin, m.position, m.vertices * 3), 3));
    g.setAttribute('normal', new THREE.BufferAttribute(new Float32Array(bin, m.normal, m.vertices * 3), 3));
    g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(bin, m.uv, m.vertices * 2), 2));
    g.setAttribute('part', new THREE.BufferAttribute(new Float32Array(bin, m.part, m.vertices), 1));
    out[m.name] = g;
  }
  return out;
}

const textureLoader = new THREE.TextureLoader();

async function loadTextures(urls) {
  const colour = new Set(['Skin_B', 'Details_B', 'Wheels_B', 'Glass_T', 'Details_I', 'Glass_I']);
  const out = {};
  urls = { ...urls, Skin_Shared: 'Skin_Shared.png', Details_Shared: 'Details_Shared.png',
    Wheels_Shared: 'Wheels_Shared.png', Glass_Shared: 'Glass_Shared.png' };
  await Promise.all(Object.entries(urls).map(async ([slot, url]) => {
    if (!url) return;
    const t = await textureLoader.loadAsync('data/' + url);
    t.colorSpace = colour.has(slot) ? THREE.SRGBColorSpace : THREE.NoColorSpace;
    t.anisotropy = maxAniso;
    if (slot.endsWith('_Code') || slot.endsWith('_Shared')) {  // read exactly: never blended with a neighbour
      t.minFilter = t.magFilter = THREE.NearestFilter;
      t.generateMipmaps = false;
    }
    out[slot] = t;
  }));
  return out;
}

// Glow from an _I texture: its RGB times the gain and tint of each texel's code.
function addGlow(material, codeMap) {
  material.emissive = new THREE.Color(0xffffff);
  material.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, glowUniforms, { glowCodeMap: { value: codeMap } });
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <emissivemap_pars_fragment>', `#include <emissivemap_pars_fragment>
        uniform sampler2D glowCodeMap;
        uniform float glowGain[ 9 ];
        uniform vec3 glowTint[ 9 ];`)
      .replace('#include <emissivemap_fragment>', `#ifdef USE_EMISSIVEMAP
          vec3 glowColour = texture2D( emissiveMap, vEmissiveMapUv ).rgb;
          int glowIndex = int( floor( texture2D( glowCodeMap, vEmissiveMapUv ).r * 255.0 / 32.0 + 0.5 ) );
          totalEmissiveRadiance *= glowColour * glowGain[ glowIndex ] * glowTint[ glowIndex ];
        #endif`);
  };
}

// ---- Parts: every corner carries its part id (car/parts.json). A 256x2 table texture holds,
// per part, row 0: visible and highlighted flags, row 1: its colour for "colour by part". The
// materials' shaders read it, so hiding a part is a discard and needs no extra meshes. ----

const partsState = { doc: null, table: null, data: null, mode: { value: 0 }, shared: { value: 0 }, rows: [] };

function partTable() {
  if (partsState.table) return partsState.table;
  const data = new Uint8Array(256 * 2 * 4);
  const n = partsState.doc.parts.length;
  const names = [...new Set(partsState.doc.parts.map((p) => p.name))];
  for (let i = 0; i < n; i++) {
    data[i * 4] = 255;  // visible
    const h = (names.indexOf(partsState.doc.parts[i].name) * 0.618034) % 1;  // one colour per name
    const c = new THREE.Color().setHSL(h, 0.75, 0.5);
    data[(256 + i) * 4] = c.r * 255; data[(256 + i) * 4 + 1] = c.g * 255; data[(256 + i) * 4 + 2] = c.b * 255;
  }
  const t = new THREE.DataTexture(data, 256, 2, THREE.RGBAFormat, THREE.UnsignedByteType);
  t.magFilter = t.minFilter = THREE.NearestFilter;
  t.needsUpdate = true;
  partsState.table = t;
  partsState.data = data;
  return t;
}

function setPartFlag(ids, channel, on) {  // channel 0: visible, 1: highlighted
  for (const i of ids) partsState.data[i * 4 + channel] = on ? 255 : 0;
  partsState.table.needsUpdate = true;
}

function addParts(material, sharedMap) {
  const previous = material.onBeforeCompile;
  material.onBeforeCompile = (shader) => {
    if (previous) previous(shader);
    Object.assign(shader.uniforms, { partTable: { value: partTable() }, partMode: partsState.mode,
      showShared: partsState.shared, sharedMap: { value: sharedMap || null } });
    shader.vertexShader = shader.vertexShader
      .replace('#include <uv_pars_vertex>', `#include <uv_pars_vertex>
        attribute float part; varying float vPart; varying vec2 vPartUv;`)
      .replace('#include <uv_vertex>', `#include <uv_vertex>
        vPart = part;
        vPartUv = uv;`);
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <map_pars_fragment>', `#include <map_pars_fragment>
        varying float vPart; varying vec2 vPartUv;
        uniform sampler2D partTable; uniform sampler2D sharedMap; uniform int partMode; uniform int showShared;`)
      .replace('#include <map_fragment>', `#include <map_fragment>
        {
          float px = (vPart + 0.5) / 256.0;
          vec4 flags = texture2D( partTable, vec2( px, 0.25 ) );
          if ( flags.r < 0.5 ) discard;
          if ( partMode == 1 ) diffuseColor.rgb = mix( diffuseColor.rgb, texture2D( partTable, vec2( px, 0.75 ) ).rgb, 0.85 );
          if ( showShared == 1 && texture2D( sharedMap, vPartUv ).r > 0.5 ) {
            float stripe = step( 0.5, fract( ( vPartUv.x + vPartUv.y ) * 160.0 ) );
            diffuseColor.rgb = mix( diffuseColor.rgb, vec3( 1.0, 0.0, 0.85 ), 0.6 * stripe );
          }
          if ( flags.g > 0.5 ) diffuseColor.rgb = mix( diffuseColor.rgb, vec3( 1.0, 0.85, 0.2 ), 0.65 );
        }`);
  };
  material.customProgramCacheKey = () => 'parts';
}

function partLabel(p) {
  const tag = [p.end, p.side === 'centre' ? '' : p.side].filter(Boolean).join(' ');
  return tag ? `${p.name} (${tag})` : p.name;
}

// The list: one row per (name, end); the row's checkbox hides both sides together.
function buildPartsList() {
  const list = document.getElementById('partsList');
  list.textContent = '';
  const parts = partsState.doc.parts;
  for (const asm of partsState.doc.assemblies) {
    const rows = new Map();
    parts.forEach((p, i) => {
      if (p.parent !== asm.name) return;
      const key = `${p.name}|${p.end}`;
      if (!rows.has(key)) rows.set(key, { name: p.name, end: p.end, ids: [] });
      rows.get(key).ids.push(i);
    });
    if (!rows.size) continue;
    const box = document.createElement('div');
    box.className = 'assembly closed';
    const head = document.createElement('div');
    head.className = 'head';
    const all = document.createElement('input');
    all.type = 'checkbox';
    all.checked = true;
    all.title = 'show or hide the whole assembly';
    all.onclick = (e) => { e.stopPropagation(); for (const r of rows.values()) r.setVisible(all.checked); };
    head.append(all, Object.assign(document.createElement('span'), { textContent: asm.name }),
      Object.assign(document.createElement('span'), { className: 'about', textContent: asm.about }));
    head.onclick = () => box.classList.toggle('closed');
    const items = document.createElement('div');
    items.className = 'items';
    for (const r of rows.values()) {
      const row = document.createElement('div');
      row.className = 'part';
      const cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.checked = true;
      r.setVisible = (on) => { cb.checked = on; row.classList.toggle('off', !on); setPartFlag(r.ids, 0, on); };
      cb.onclick = (e) => { e.stopPropagation(); r.setVisible(cb.checked); };
      const name = Object.assign(document.createElement('span'), { className: 'name', textContent: r.name });
      const tag = Object.assign(document.createElement('span'), { className: 'tag', textContent: r.end || '' });
      const only = Object.assign(document.createElement('button'), { className: 'only', textContent: 'only', title: 'show only this' });
      only.onclick = (e) => { e.stopPropagation(); for (const o of partsState.rows) o.setVisible(o === r); box.classList.remove('closed'); };
      row.onclick = () => highlight(r.ids, r);
      row.append(cb, name, tag, only);
      r.row = row;
      items.append(row);
      partsState.rows.push(r);
    }
    box.append(head, items);
    list.append(box);
  }
}

let litIds = [];
function highlight(ids, row) {
  setPartFlag(litIds, 1, false);
  for (const r of partsState.rows) r.row.classList.remove('lit');
  litIds = litIds.length && litIds.join() === ids.join() ? [] : ids;  // click again to clear
  setPartFlag(litIds, 1, true);
  if (litIds.length) {
    const r = row || partsState.rows.find((o) => o.ids.includes(ids[0]));
    if (r) {
      r.row.classList.add('lit');
      r.row.parentElement.parentElement.classList.remove('closed');
      r.row.scrollIntoView({ block: 'nearest' });
    }
  }
}

// Clicking the car names the part under the pointer.
const raycaster = new THREE.Raycaster();
const tip = document.getElementById('tip');
const partOfHit = (hit) => hit.object.geometry.getAttribute('part').getX(hit.face.a);
let pressAt = null;
canvas.addEventListener('pointerdown', (e) => { pressAt = [e.clientX, e.clientY]; });
canvas.addEventListener('pointerup', (e) => {
  if (!pressAt || Math.hypot(e.clientX - pressAt[0], e.clientY - pressAt[1]) > 4 || !partsState.doc) return;
  const ndc = new THREE.Vector2((e.clientX / innerWidth) * 2 - 1, -(e.clientY / innerHeight) * 2 + 1);
  raycaster.setFromCamera(ndc, camera);
  const hit = raycaster.intersectObjects(Object.values(parts).filter((m) => m.visible))
    .find((h) => partsState.data[partOfHit(h) * 4] > 0);
  tip.textContent = '';
  if (!hit) { highlight([]); return; }
  const id = partOfHit(hit);
  const p = partsState.doc.parts[id];
  highlight([id]);
  tip.textContent = `${partLabel(p)} · ${p.mesh}${p.shared > 0.5 ? ' · shared with its twin' : ''}`;
  tip.style.left = `${Math.min(e.clientX + 14, innerWidth - 260)}px`;
  tip.style.top = `${e.clientY + 14}px`;
});

function buildCar(geoms, tex) {
  const std = (set, extra = {}) => ({
    map: tex[`${set}_B`], roughnessMap: tex[`${set}_RM`], metalnessMap: tex[`${set}_RM`],
    roughness: 1, metalness: 1, aoMap: tex[`${set}_AO`], ...extra,
  });
  // Body: a glossy varnish (clear coat) over the paint. In the game, Skin_CoatR at 0 is a glossy
  // varnish over anything, 255 adds no gloss, and a skin without the file is glossy all over
  // (checked with the lab skins, 2026-09-24, CHECKLIST.md). Skin_Coat holds 255 - CoatR in R,
  // which three.js reads as the coat's amount.
  const skin = new THREE.MeshPhysicalMaterial(std('Skin', {
    clearcoat: TUNE.coat, clearcoatRoughness: 0, clearcoatMap: tex.Skin_Coat || null,
  }));
  const details = new THREE.MeshStandardMaterial(std('Details', { normalMap: tex.Details_N }));
  if (tex.Details_I) {
    details.emissiveMap = tex.Details_I;
    addGlow(details, tex.Details_Code);
  }
  const wheels = new THREE.MeshStandardMaterial(std('Wheels', { normalMap: tex.Wheels_N }));
  // Glass: Glass_T tints what's seen through it. Its alpha isn't used yet (checkpoint 4).
  const glass = new THREE.MeshPhysicalMaterial({
    map: tex.Glass_T, transmission: 1, thickness: 0, ior: 1.5, roughness: 0.04, metalness: 0,
    aoMap: tex.Glass_AO,
  });
  if (tex.Glass_I) {
    glass.emissiveMap = tex.Glass_I;
    addGlow(glass, tex.Glass_Code);
  }
  const car = new THREE.Group();
  for (const [name, material] of Object.entries({ Skin: skin, Details: details, Wheels: wheels, Glass: glass })) {
    addParts(material, tex[`${name}_Shared`]);
    const mesh = new THREE.Mesh(geoms[name], material);
    mesh.castShadow = name !== 'Glass';
    mesh.receiveShadow = true;
    parts[name] = mesh;
    car.add(mesh);
  }
  scene.add(car);
}

// ---- Day and night ----

function setNight(night) {
  const look = LOOKS[night ? 'night' : 'day'];
  GLOW.forEach((g, i) => { glowUniforms.glowGain.value[i] = night ? g.night : g.day; });
  scene.environment = envMaps[night ? 'night' : 'day'] || null;
  scene.environmentIntensity = look.env * TUNE.env;
  key.color.set(look.keyColour);
  key.intensity = look.key * TUNE.key;
  document.getElementById('day').setAttribute('aria-pressed', String(!night));
  document.getElementById('night').setAttribute('aria-pressed', String(night));
}

// ---- Controls on the page ----

document.getElementById('day').onclick = () => setNight(false);
document.getElementById('night').onclick = () => setNight(true);
const pressed = (id, on) => document.getElementById(id).setAttribute('aria-pressed', String(on));
document.getElementById('colourBy').onclick = () => {
  partsState.mode.value = partsState.mode.value ? 0 : 1;
  pressed('colourBy', partsState.mode.value === 1);
};
document.getElementById('shared').onclick = () => {
  partsState.shared.value = partsState.shared.value ? 0 : 1;
  pressed('shared', partsState.shared.value === 1);
};
document.getElementById('togglePartsPanel').onclick = () => {
  const panel = document.getElementById('partsPanel');
  panel.hidden = !panel.hidden;
  pressed('togglePartsPanel', !panel.hidden);
};
document.getElementById('showAll').onclick = () => { for (const r of partsState.rows) r.setVisible(true); highlight([]); tip.textContent = ''; };
if (innerWidth < 720) document.getElementById('togglePartsPanel').click();for (const b of document.querySelectorAll('#parts button')) {
  b.onclick = () => {
    const mesh = parts[b.dataset.part];
    if (!mesh) return;
    mesh.visible = !mesh.visible;
    b.setAttribute('aria-pressed', String(mesh.visible));
  };
}

// ---- Start ----

const frames = (n) => new Promise((done) => {
  const step = () => (--n <= 0 ? done() : requestAnimationFrame(step));
  requestAnimationFrame(step);
});

// What tool/snap.py drives.
window.viewer = {
  ready: false,
  error: null,
  async show(view, night = false, hidden = []) {
    setNight(night);
    setView(view);
    for (const [name, mesh] of Object.entries(parts)) mesh.visible = !hidden.includes(name);
    await frames(3);
  },
  // Parts settings: { colourBy, shared, hidden: [part names], only: [part names], highlight: [part names] }.
  // A name matches a part, its assembly, or "name|side|end".
  async showParts(opts = {}) {
    const match = (names) => partsState.doc.parts.map((p, i) => [p, i]).filter(([p]) => names.some((n) =>
      n === p.name || n === p.parent || n === `${p.name}|${p.side}|${p.end}`)).map(([, i]) => i);
    partsState.mode.value = opts.colourBy ? 1 : 0;
    partsState.shared.value = opts.shared ? 1 : 0;
    const hidden = new Set(match(opts.hidden || []));
    const only = opts.only ? new Set(match(opts.only)) : null;
    for (const r of partsState.rows) r.setVisible(r.ids.every((i) => !hidden.has(i) && (!only || only.has(i))));
    highlight([]);
    if (opts.highlight) highlight(match(opts.highlight));
    await frames(3);
  },
  gpu() {
    const gl = renderer.getContext();
    const ext = gl.getExtension('WEBGL_debug_renderer_info');
    return ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
  },
};

function fail(err) {
  window.viewer.error = String(err && err.stack || err);
  statusBox.textContent = `Couldn't show the skin: ${err && err.message || err}`;
  console.error(err);
}
window.addEventListener('error', (e) => fail(e.error || e.message));
window.addEventListener('unhandledrejection', (e) => fail(e.reason));

async function start() {
  document.getElementById('title').textContent = skinName;
  document.title = `${skinName} · Skin viewer`;
  resize();
  setView('front');
  const res = await fetch(`data/skins/${encodeURIComponent(skinName)}/skin.json`);
  if (!res.ok) throw new Error(`no skin called ${skinName} has been prepared for the viewer`);
  const skin = await res.json();
  const [geoms, tex, , doc] = await Promise.all([loadMeshes(), loadTextures(skin.textures), loadLighting(),
    fetch('data/parts.json').then((r) => r.json())]);
  partsState.doc = doc;
  partTable();
  buildPartsList();
  addRoom();
  buildCar(geoms, tex);
  setNight(false);
  renderer.setAnimationLoop(() => {
    controls.update();
    renderer.render(scene, camera);
  });
  await frames(2);
  statusBox.textContent = '';
  window.viewer.ready = true;
}

start().catch(fail);
