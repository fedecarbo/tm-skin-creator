// The skin viewer: the car in a photo studio, wearing one skin, by day or night.
//   /?skin=<name>          the skin prepared by `python -m tool.view <name>`
//   /?skin=<name>&snap=1   no controls on screen, for Claude's snapshots (tool/snap.py)
// Data comes from /data/ (see tool/view.py): car.json + car.bin (every triangle corner tagged
// with its part), parts.json (the named parts), <Set>_Shared.png (texels several parts share),
// the two lighting HDRIs, skins/<name>/skin.json, which gives the URL of every texture slot, and
// gallery.json (tool/gallery.py), the list of skins down the left.

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { HDRLoader } from 'three/addons/loaders/HDRLoader.js';

const params = new URLSearchParams(location.search);
let skinName = params.get('skin') || 'TSC_Test';
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
  // Looking down, the car's front at the top. roomy: further back on the page, where the title
  // and the buttons share the window (snapshots keep dist).
  top: { dir: [0, 1, -0.0001], dist: 7.6, roomy: 1.3 },
  // The game's cameras that show the car, under Driving (the user, 2026-09-25: not the cockpit
  // ones), all through the game's wide lens (58.7° tall, 90° wide at 16:9). The user sets each
  // by eye next to the game and pastes it to Claude ("Copy Cam N", below), who writes it here
  // squared up behind the car. They're as seen in the viewer's framing (FRAMED), standing still.
  // Cam 1 and Cam 2 aim at a point above the car, so the car sits low in the picture and the
  // track ahead shows, as the game means them to (the user, 2026-09-25, their second setting).
  // Cam 1, the chase camera: 2.47 m up, 5.35 m behind the point it looks at (1.32 m up), 12°
  // down. Pasted: camera at 0.037, 2.467, -4.790, looking at -0.068, 1.323, 0.562 (1.1° off
  // centre). Close to the user's first screenshot (3.75 m up, 13.5° down at a point 2.18 m up),
  // which the viewer had moved closer; the user's first setting aimed at the car, 26° down.
  cam1: { dir: [0, 0.209, -0.9779], dist: 5.474, target: [0, 1.323, 0.562], fov: 58.7 },
  // Cam 2: lower than Cam 1 and a little closer, not the farther one first guessed. 1.82 m up,
  // 5.21 m behind the point it looks at (1.28 m up), 6° down. Pasted: camera at -0.028, 1.816,
  // -4.770, looking at -0.028, 1.278, 0.440 (square already).
  cam2: { dir: [0, 0.1027, -0.9947], dist: 5.238, target: [0, 1.278, 0.44], fov: 58.7 },
  // Cam 3, the one over the driver's shoulder, set by the user (2026-09-25): 1.08 m up, 0.9 m
  // behind the point it looks at, over the bonnet, almost level (2° down). Pasted: camera at
  // 0.016, 1.080, -0.397, looking at -0.002, 1.045, 0.504 (1.1° off centre). Their first try
  // (1.18 m up, 9° down) met the orbit's 1 m limit, so Driving cameras may come closer (DRIVING_MIN).
  cam3: { dir: [0, 0.0388, -0.9992], dist: 0.902, target: [0, 1.045, 0.504], fov: 58.7 },
};
const FOV = 32;  // every other view's lens
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
// (and on a dusk map); energy is dim and tinted by the game (red for this player). Brake heat
// lights while braking (the lights test's videos, 2026-09-25: BRAKE_HEAT). Turbo, exhaust heat
// and boost weren't seen to light up, so they stay off.
const GLOW = [
  { code: 0, day: 1.2, night: 1.8 },  // brake lights: dim all the time, brighter when braking
  { code: 32, day: 0.6, night: 1, tint: [1, 0.2, 0.2] },  // energy, tinted by the game
  { code: 64, day: 0, night: 0 },  // brake heat: while braking (BRAKE_HEAT)
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
const camera = new THREE.PerspectiveCamera(FOV, 1, 0.05, 400);
const controls = new OrbitControls(camera, canvas);
controls.target.copy(CENTRE);
controls.enableDamping = true;
controls.minDistance = 1;
const DRIVING_MIN = 0.2;  // closer, with a Driving camera picked: Cam 3 sits over the driver's shoulder
controls.maxDistance = 18;
controls.autoRotateSpeed = 1.5;  // one turn in about 40 s
// No limit on the angle: skins paint the underside too, and the floor isn't drawn from below.

// view: a name from VIEWS, or { dir, dist, target, fov } for a close look. glide: move there smoothly.
let glide = null;
function setView(view, smooth = false) {
  const v = typeof view === 'string' ? VIEWS[view] : view;
  const target = new THREE.Vector3(...(v.target || CENTRE.toArray()));
  const offset = new THREE.Vector3(...v.dir).normalize().multiplyScalar(v.dist * (snap ? 1 : v.roomy || 1));
  const fov = v.fov || FOV;
  if (!smooth) {
    glide = null;
    controls.target.copy(target);
    camera.position.copy(target).add(offset);
    camera.fov = fov;
    camera.updateProjectionMatrix();
    controls.update();
    return;
  }
  // Round the car, not through it: angles and distance change, the target slides.
  const from = new THREE.Spherical().setFromVector3(camera.position.clone().sub(controls.target));
  const to = new THREE.Spherical().setFromVector3(offset);
  let turn = to.theta - from.theta;
  turn -= Math.round(turn / (2 * Math.PI)) * 2 * Math.PI;
  glide = { start: performance.now(), from, to, turn, target0: controls.target.clone(), target1: target, fov0: camera.fov, fov1: fov };
}

function stepGlide() {
  if (!glide) return;
  const t = Math.min(1, (performance.now() - glide.start) / 650);
  const e = t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2;
  const { from, to } = glide;
  controls.target.lerpVectors(glide.target0, glide.target1, e);
  const s = new THREE.Spherical(from.radius + (to.radius - from.radius) * e, from.phi + (to.phi - from.phi) * e, from.theta + glide.turn * e);
  camera.position.setFromSpherical(s).add(controls.target);
  camera.fov = glide.fov0 + (glide.fov1 - glide.fov0) * e;
  camera.updateProjectionMatrix();
  if (t >= 1) glide = null;
}

// The list down the left covers part of the window, so the picture's centre moves to the middle
// of the space beside it (a view offset, so the car still turns about its own centre), a little
// up to clear the buttons along the bottom, and the car is drawn a little smaller. Snapshots
// keep the plain framing.
const FRAMED = { up: 0.05, zoom: 0.92 };
function railWidth() {
  return parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--rail')) || 0;
}
function frame(w, h, plain) {
  if (plain) {
    camera.clearViewOffset();
    camera.aspect = w / h;
    camera.zoom = 1;
  } else {
    const rail = railWidth();
    camera.setViewOffset(w - rail, h, -rail, FRAMED.up * h, w, h);
    camera.zoom = FRAMED.zoom;
  }
  camera.updateProjectionMatrix();
}

function resize() {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  renderer.setSize(w, h, false);
  frame(w, h, snap);
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
    if (m.digit !== undefined) g.setAttribute('digit', new THREE.BufferAttribute(new Float32Array(bin, m.digit, m.vertices), 1));
    out[m.name] = g;
  }
  return out;
}

const textureLoader = new THREE.TextureLoader();
const COLOUR_SLOTS = new Set(['Skin_B', 'Details_B', 'Wheels_B', 'Glass_T', 'Details_I', 'Glass_I']);

async function loadTexture(slot, url) {
  const t = await textureLoader.loadAsync('data/' + url);
  t.colorSpace = COLOUR_SLOTS.has(slot) ? THREE.SRGBColorSpace : THREE.NoColorSpace;
  t.anisotropy = maxAniso;
  if (slot.endsWith('_Code') || slot.endsWith('_Shared')) {  // read exactly: never blended with a neighbour
    t.minFilter = t.magFilter = THREE.NearestFilter;
    t.generateMipmaps = false;
  }
  return t;
}

// Which texels several parts share: the same for every skin, so loaded once.
const sharedMaps = {};
async function loadShared() {
  await Promise.all(['Skin', 'Details', 'Wheels', 'Glass'].map(async (set) => {
    sharedMaps[set] = await loadTexture(`${set}_Shared`, `${set}_Shared.png`);
  }));
}

// A skin's textures, kept by slot and URL. A skin is 4096² textures, so switching skins frees
// what the new one doesn't use; the stock ones it shares stay.
const texCache = new Map();  // "slot|url" -> Promise<Texture>
async function loadTextures(urls) {
  const out = {};
  await Promise.all(Object.entries(urls).map(async ([slot, url]) => {
    if (!url) return;
    const id = `${slot}|${url}`;
    if (!texCache.has(id)) texCache.set(id, loadTexture(slot, url));
    out[slot] = await texCache.get(id);
  }));
  return out;
}
function freeTexturesExcept(urls) {
  const keep = new Set(Object.entries(urls).filter(([, u]) => u).map(([s, u]) => `${s}|${u}`));
  for (const [id, pending] of texCache) {
    if (keep.has(id)) continue;
    texCache.delete(id);
    pending.then((t) => t.dispose(), () => {});
  }
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

// ---- The game's number. The game writes the player's initials and number on two engine-cover
// panels over every skin, and a skin can't hide or move them (CLAUDE.md). The viewer lays them
// on as a layer of its own, never part of the skin, so "Show → Number" turns them off. As in the
// user's Cam 1 screenshot (2026-09-25): the initials on "number panel", the narrow one just
// behind the cockpit, and the number on "engine cover panel" behind it, both reading from behind
// the car. The lettering (Russo One, white, thinned a little) is a guess at the game's typeface,
// until a close-up says more; the user likes it.
// ?initials=DEC&number=07 tries others. Snapshots (?snap=1) leave it off. ----

const PLATE = { initials: params.get('initials') || 'CAR', number: params.get('number') || '01' };
const PLATE_PANELS = [['number panel', PLATE.initials], ['engine cover panel', PLATE.number]];
const plateUniforms = { plateOn: { value: 0 }, plateColour: { value: new THREE.Color('#ececec') } };

// A panel's frame: its middle, and axes along the text (to the car's right, as read from behind)
// and up it (towards the nose), each divided by the panel's size, so the panel spans -0.5..0.5.
function panelFrame(geom, ids) {
  const pos = geom.getAttribute('position'), nrm = geom.getAttribute('normal'), part = geom.getAttribute('part');
  const pts = [], n = new THREE.Vector3(), p = new THREE.Vector3();
  for (let i = 0; i < part.count; i++) {
    if (!ids.has(part.getX(i))) continue;
    pts.push(new THREE.Vector3().fromBufferAttribute(pos, i));
    n.add(p.fromBufferAttribute(nrm, i));
  }
  n.normalize();
  const u = new THREE.Vector3(-1, 0, 0).addScaledVector(n, n.x).normalize();
  const v = new THREE.Vector3().crossVectors(n, u);
  let u0 = Infinity, u1 = -Infinity, v0 = Infinity, v1 = -Infinity;
  for (const q of pts) {
    u0 = Math.min(u0, q.dot(u)); u1 = Math.max(u1, q.dot(u));
    v0 = Math.min(v0, q.dot(v)); v1 = Math.max(v1, q.dot(v));
  }
  const centre = new THREE.Vector3().addScaledVector(u, (u0 + u1) / 2).addScaledVector(v, (v0 + v1) / 2);
  return { centre, u: u.divideScalar(u1 - u0), v: v.divideScalar(v1 - v0), aspect: (u1 - u0) / (v1 - v0) };
}

// How much each stroke of the lettering is thinned, as a share of the letters' size: Russo One
// has one weight, heavier than the game's ("bold but not too bold"). The user picked 0.02 out
// of 0, 0.02, 0.035 and 0.05 (2026-09-25); ?plateThin= tries others.
const PLATE_THIN = Number(params.get('plateThin') ?? 0.02);

// The text as a mask (alpha only, so its mips don't darken), as large as the panel allows.
function plateMask(text, aspect) {
  const w = 1024, h = Math.round(w / aspect);
  const g = Object.assign(document.createElement('canvas'), { width: w, height: h }).getContext('2d');
  const measure = (size) => { g.font = `${size}px "Russo One"`; return g.measureText(text); };
  let m = measure(100);
  const size = 100 * Math.min(w * 0.86 / m.width, h * 0.74 / (m.actualBoundingBoxAscent + m.actualBoundingBoxDescent));
  m = measure(size);
  const x = w / 2, y = h / 2 + (m.actualBoundingBoxAscent - m.actualBoundingBoxDescent) / 2;
  g.fillStyle = '#fff';
  g.textAlign = 'center';
  g.fillText(text, x, y);
  if (PLATE_THIN > 0) {  // a stroke along every outline, cut away: half its width off each side
    g.globalCompositeOperation = 'destination-out';
    g.lineJoin = 'round';
    g.lineWidth = 2 * PLATE_THIN * size;
    g.strokeText(text, x, y);
  }
  const t = new THREE.CanvasTexture(g.canvas);
  t.anisotropy = maxAniso;
  return t;
}

async function setupPlate(geom) {
  await document.fonts.load('100px "Russo One"');
  PLATE_PANELS.forEach(([name, text], k) => {
    const ids = new Set(partsState.doc.parts.flatMap((p, i) => (p.name === name ? [i] : [])));
    for (const i of ids) partsState.data[i * 4 + 2] = k ? 170 : 85;  // which panel, for the shader
    const f = panelFrame(geom, ids);
    Object.assign(plateUniforms, { [`plateMask${k}`]: { value: plateMask(text, f.aspect) },
      [`plateC${k}`]: { value: f.centre }, [`plateU${k}`]: { value: f.u }, [`plateV${k}`]: { value: f.v } });
  });
  partsState.table.needsUpdate = true;
}

// Body only; after addParts, whose part id and table it reads.
function addPlate(material) {
  const previous = material.onBeforeCompile;
  material.onBeforeCompile = (shader) => {
    if (previous) previous(shader);
    Object.assign(shader.uniforms, plateUniforms);
    shader.vertexShader = shader.vertexShader
      .replace('#include <uv_pars_vertex>', `#include <uv_pars_vertex>
        varying vec3 vPlatePos;`)
      .replace('#include <uv_vertex>', `#include <uv_vertex>
        vPlatePos = position;`);
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <map_pars_fragment>', `#include <map_pars_fragment>
        varying vec3 vPlatePos;
        uniform int plateOn; uniform vec3 plateColour;
        uniform sampler2D plateMask0; uniform vec3 plateC0; uniform vec3 plateU0; uniform vec3 plateV0;
        uniform sampler2D plateMask1; uniform vec3 plateC1; uniform vec3 plateU1; uniform vec3 plateV1;
        float plateSample( sampler2D mask, vec3 c, vec3 u, vec3 v ) {
          vec2 st = vec2( dot( vPlatePos - c, u ), dot( vPlatePos - c, v ) ) + 0.5;
          float inside = step( 0.0, st.x ) * step( st.x, 1.0 ) * step( 0.0, st.y ) * step( st.y, 1.0 );
          return texture2D( mask, st ).a * inside;
        }`)
      .replace('#include <map_fragment>', `#include <map_fragment>
        float plateA = 0.0;
        if ( plateOn == 1 ) {
          float which = texture2D( partTable, vec2( ( vPart + 0.5 ) / 256.0, 0.25 ) ).b;
          float a0 = plateSample( plateMask0, plateC0, plateU0, plateV0 );
          float a1 = plateSample( plateMask1, plateC1, plateU1, plateV1 );
          plateA = which > 0.5 ? a1 : which > 0.2 ? a0 : 0.0;
          diffuseColor.rgb = mix( diffuseColor.rgb, plateColour, plateA );
        }`)
      .replace('#include <roughnessmap_fragment>', `#include <roughnessmap_fragment>
        roughnessFactor = mix( roughnessFactor, 0.45, plateA );`)
      .replace('#include <metalnessmap_fragment>', `#include <metalnessmap_fragment>
        metalnessFactor *= 1.0 - plateA;`);
  };
  material.customProgramCacheKey = () => 'parts-plate';
}

function setPlate(on) {
  plateUniforms.plateOn.value = on ? 1 : 0;
  pressed(byId('plateToggle'), on);
  try { localStorage.setItem('tsc-viewer-number', on ? '1' : '0'); } catch {}
}

// ---- The speed display: three seven-segment digits on the rear bumper. Each segment is a bar
// of its own (three pieces: its face and two bevels), but all 21 share one patch of Details_I,
// lit, so the file says "888" (measured 2026-09-25): the game picks the lit bars
// itself. So does the viewer, from the segment each corner carries (tool/view.py
// digit_segments), showing a speed (?speed=180). Unlit bars don't glow. The game always
// lights three digits, leading zeros too ("075"), and a stopped car shows "000" (the user's
// straight-line video, 2026-09-25).

// The page starts standing still (the user, 2026-09-25); snapshots keep 180, so the digits show lit.
const SPEED = Math.max(0, Math.min(999, Math.round(Number(params.get('speed') ?? (snap ? 180 : 0))) || 0));
const SEVEN = [0x3f, 0x06, 0x5b, 0x4f, 0x66, 0x6d, 0x7d, 0x07, 0x7f, 0x6f];  // 0-9, bits a b c d e f g
const digitUniforms = { digitMask: { value: [0, 0, 0] } };
function showSpeed(kmh) {
  digitUniforms.digitMask.value = [...String(kmh).padStart(3, '0')].map((c) => SEVEN[Number(c)]);
  const out = document.getElementById('padSpeed');
  if (out) out.textContent = kmh;
}
showSpeed(SPEED);

// ---- The rear lights: a gear display. Each side's bar (the L from the tail's corner along its
// top) is split into five bands by dark lines in Details_I/Details_B, at these v's of its UV
// strip (measured 2026-09-25): the band from v 0.450 (the corner) is gear 1, the one ending at
// 0.532 (towards the middle) gear 5. The user's straight-line video (2026-09-25, the parts skin,
// whose Details_I is stock) settled how they behave: the bands fill up from the corner, one per
// gear (gear 1, standing still included, lights the corner only), in the file's own colour
// (white in the stock file, not red); unlit they look like the glass over them. Braking lights
// both bars whole and the small centre piece, red; so does the car held at the start. ----

// on: as "always on" (96). Braking also tints the bars' surface red: a red glow alone over the
// pale stock surface washes out to peach under the tone mapping. A tinted lens ("rear light lens")
// filters that red as in the game, with nothing more here: the glass's transmission multiplies
// what's behind it by Glass_T (behind cyan, dark by night and teal by day, as in the lights
// test's videos; checked 2026-09-25).
const REAR = { colour: [1, 0.015, 0.025], lens: [0.55, 0.06, 0.05], on: { day: 1.2, night: 1.8 }, brake: { day: 4, night: 4.5 } };
// Gear changes, from the video: up at these speeds under full throttle, down at the lower ones
// while coasting, and the speed pauses for a moment at each change up.
const GEAR_UP = [101, 162, 236, 342], GEAR_DOWN = [90, 142, 200, 279], SHIFT_PAUSE = 0.2;
const gearFor = (kmh) => 1 + GEAR_UP.filter((t) => kmh >= t).length;  // as when accelerating
const rearUniforms = { rearColour: { value: new THREE.Color(...REAR.colour) }, rearLens: { value: new THREE.Color(...REAR.lens) }, rearLevel: { value: REAR.on.day },
  rearBrake: { value: 0 }, rearGear: { value: gearFor(SPEED) } };

function setupRearLights() {
  partsState.doc.parts.forEach((p, i) => { if (p.name === 'rear light') partsState.data[i * 4 + 3] = 255; });
  partsState.table.needsUpdate = true;
}

// Details only; after addGlow and addParts: the speed digits and the rear lights.
function addDisplays(material) {
  const previous = material.onBeforeCompile;
  material.onBeforeCompile = (shader) => {
    if (previous) previous(shader);
    Object.assign(shader.uniforms, digitUniforms, rearUniforms);
    shader.vertexShader = shader.vertexShader
      .replace('#include <uv_pars_vertex>', `#include <uv_pars_vertex>
        attribute float digit; varying float vDigit;`)
      .replace('#include <uv_vertex>', `#include <uv_vertex>
        vDigit = digit;`);
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <map_pars_fragment>', `#include <map_pars_fragment>
        varying float vDigit;
        uniform int digitMask[ 3 ];
        uniform vec3 rearColour; uniform vec3 rearLens; uniform float rearLevel; uniform float rearBrake; uniform int rearGear;
        #define IS_REAR ( texture2D( partTable, vec2( ( vPart + 0.5 ) / 256.0, 0.25 ) ).a > 0.5 )  // a macro: partTable is declared after this`)
      .replace('#include <color_fragment>', `#include <color_fragment>
        if ( IS_REAR && rearBrake > 0.5 ) diffuseColor.rgb *= rearLens;`)
      .replace('#include <aomap_fragment>', `#include <aomap_fragment>
        if ( vDigit > 0.5 ) {  // 1 + 7 * digit + segment
          int code = int( vDigit + 0.5 ) - 1;
          totalEmissiveRadiance *= float( ( digitMask[ code / 7 ] >> ( code % 7 ) ) & 1 );
        }
        if ( IS_REAR ) {  // the rear lights: braking, all of it red; otherwise the gear's bands in the file's colour
          vec3 file = texture2D( emissiveMap, vEmissiveMapUv ).rgb;
          if ( rearBrake > 0.5 ) totalEmissiveRadiance = max( file.r, max( file.g, file.b ) ) * rearColour * rearLevel;
          else {
            float lit = 0.0;
            if ( vPartUv.x < 0.5 ) {  // a bar: its band, 0 at the tail's corner to 4 towards the middle
              int band = int( vPartUv.y >= 0.4747 ) + int( vPartUv.y >= 0.4903 ) + int( vPartUv.y >= 0.5030 ) + int( vPartUv.y >= 0.5157 );
              lit = float( band < rearGear );
            }
            totalEmissiveRadiance = file * rearLevel * lit;
          }
        }`);
  };
  material.customProgramCacheKey = () => 'parts-displays';
}

// ---- The rear wings. Two wings open under way (the user, 2026-09-25). They don't tilt: each
// moves straight out, then its side pieces slide apart from its centre piece. The top wing (the
// tail panel between the two tail corners) lifts, showing the tops of the rear light bars; the
// bottom wing (the plate under the bumper: the diffuser and the undertray between the diffuser
// strakes) drops. The blocks under each ("rear bumper", "rear bumper corner": white and purple
// in TSC_Parts) move out with it but not apart, so they show in the gaps, as in the video. They
// open from 60 km/h, stay open while coasting and close below 43 (the timeline: WING).
// Provisional until a side view: how far they move, and what moves when braking. Snapshots keep
// them shut. ----

// How far, in metres: out (+ up) and apart (each side). ?wingLift=, ?wingSpread=, ?flapDrop=
// and ?flapSpread= (cm) try others; ?wing=1 opens them in snapshots.
const cm = (key, fallback) => Number(params.get(key) ?? fallback) / 100;
const WINGS = [
  { parts: ['tail panel', 'tail corner', 'rear bumper'], blocks: ['rear bumper'], out: cm('wingLift', 6), apart: cm('wingSpread', 3.5) },
  { parts: ['diffuser', 'diffuser strake', 'rear undertray', 'rear bumper corner'], blocks: ['rear bumper corner'],
    out: -cm('flapDrop', 8), apart: cm('flapSpread', 3) },
];
// The timeline, in seconds, read frame by frame off the video: opening from 60 km/h (the user
// confirmed), out in 0.4, a 0.4 pause, apart in 0.75, fully open at 2.67 s on the race clock
// (the user timed it at 2.70); closing below 43, together in 0.6, then back in in 0.25.
const WING = { openFrom: 60, shutBelow: 43, out: 0.4, pause: 0.4, apart: 0.75, together: 0.6, back: 0.25,
  outer: 0.44 };  // outer: see addWing
const wingUniforms = { wingOut: { value: [0, 0] }, wingApart: { value: [0, 0] },
  wingIds: { value: new Array(16).fill(-1) }, wingOf: { value: new Array(16).fill(0) } };
// Each part's wing and role, packed as 4 * wing + role: 0 the centre piece, 1 a side, 2 a block,
// 3 the top wing's blocks, whose outer ends (the plates inside the tail corners) go with the sides.
function setupWing() {
  const ids = [], of = [];
  WINGS.forEach((w, k) => partsState.doc.parts.forEach((p, i) => {
    if (!w.parts.includes(p.name)) return;
    const role = w.blocks.includes(p.name) ? (k === 0 ? 3 : 2) : (p.side === 'centre' ? 0 : 1);
    ids.push(i);
    of.push(4 * k + role);
  }));
  wingUniforms.wingIds.value = [...ids, ...new Array(16).fill(-1)].slice(0, 16);
  wingUniforms.wingOf.value = [...of, ...new Array(16).fill(0)].slice(0, 16);
}
const easeWing = (t) => { t = Math.min(1, Math.max(0, t)); return t * t * (3 - 2 * t); };
function showWing(out, apart) {  // each 0..1
  wingUniforms.wingOut.value = WINGS.map((w) => w.out * easeWing(out));
  wingUniforms.wingApart.value = WINGS.map((w) => w.apart * easeWing(apart));
}

// ---- The air brakes (the user, 2026-09-25): braking, the two rear quarter panels tip up at the
// front and the nose panel tips up at the back, quickly, each pushed up by arms inside it. Unlike
// the wings these do tilt: each panel turns about its other edge, along a hinge line in its own
// plane, found from the mesh at load, and takes its underside along ("with"). Each arm swings
// about its base and stretches so that its tip stays on the panel: the "rear damper" in each
// quarter panel's opening and the "nose sensor" rods under the nose (names from checkpoint 3,
// before we knew what they were). Provisional until a side view: the angles and how quick.
// Snapshots keep them down; ?airbrake=1 raises them there. ----

const AIRBRAKES = [  // hinge: the edge that stays; angle in degrees
  { part: 'rear quarter panel', hinge: 'back', angle: Number(params.get('quarterAngle') ?? 20), with: [], arms: ['rear damper'] },
  { part: 'nose panel', hinge: 'front', angle: Number(params.get('noseAngle') ?? 30), with: ['nose plate'], arms: ['nose sensor'] },
];
const AIRBRAKE = { up: 0.15, down: 0.2 };  // seconds
const vec3s = (n, make = () => new THREE.Vector3()) => Array.from({ length: n }, make);
const tiltUniforms = { tiltOn: { value: 0 },
  tiltIds: { value: new Array(8).fill(-1) }, tiltSlot: { value: new Array(8).fill(0) },  // part -> panel
  tiltAngle: { value: [0, 0, 0, 0] }, tiltPivot: { value: vec3s(4) }, tiltAxis: { value: vec3s(4, () => new THREE.Vector3(1, 0, 0)) },
  armIds: { value: [-1, -1, -1, -1] }, armBase: { value: vec3s(4) }, armDir: { value: vec3s(4, () => new THREE.Vector3(0, 1, 0)) },
  armAxis: { value: vec3s(4, () => new THREE.Vector3(1, 0, 0)) }, armAngle: { value: [0, 0, 0, 0] }, armStretch: { value: [1, 1, 1, 1] } };
const airbrake = { max: [], arms: [] };  // per panel its angle; per arm its panel, base and tip

// The corners of the given parts, from the Skin and Details meshes.
function partVertices(geoms, ids) {
  const vs = [], ns = [];
  for (const g of [geoms.Skin, geoms.Details]) {
    const pos = g.attributes.position.array, nrm = g.attributes.normal.array, part = g.attributes.part.array;
    for (let v = 0; v < part.length; v++) {
      if (!ids.includes(part[v])) continue;
      vs.push(new THREE.Vector3(pos[3 * v], pos[3 * v + 1], pos[3 * v + 2]));
      ns.push(new THREE.Vector3(nrm[3 * v], nrm[3 * v + 1], nrm[3 * v + 2]));
    }
  }
  return { vs, ns };
}
// An arm's two ends: along its longest direction (power iteration on the spread of its corners).
function armEnds(vs) {
  const mean = vs.reduce((a, v) => a.add(v), new THREE.Vector3()).divideScalar(vs.length);
  const c = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
  for (const v of vs) {
    const d = v.clone().sub(mean).toArray();
    for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) c[i][j] += d[i] * d[j];
  }
  let dir = new THREE.Vector3(1, 1, 1).normalize();
  for (let k = 0; k < 30; k++) {
    const a = dir.toArray();
    dir = new THREE.Vector3(...c.map((row) => row[0] * a[0] + row[1] * a[1] + row[2] * a[2])).normalize();
  }
  const t = vs.map((v) => v.clone().sub(mean).dot(dir));
  const ends = [Math.min(...t), Math.max(...t)].map((s) => mean.clone().addScaledVector(dir, s));
  return ends[0].y < ends[1].y ? ends : [ends[1], ends[0]];  // [base, tip]: the base is the lower end
}

// Per panel: its mean normal n; the hinge, the middle of the edge that stays (its front- or
// rearmost corners); d, the way to the other edge within the panel's plane; the axis d x n,
// about which a positive turn lifts that edge along n.
function setupAirbrakes(geoms) {
  const doc = partsState.doc.parts, ids = [], slots = [], arms = [];
  const find = (names, side) => doc.flatMap((p, i) => (names.includes(p.name) && p.side === side ? [i] : []));
  AIRBRAKES.forEach((a) => doc.forEach((p, id) => {
    if (p.name !== a.part || airbrake.max.length >= 4) return;
    const k = airbrake.max.length;
    const { vs, ns } = partVertices(geoms, [id]);
    const n = ns.reduce((s, v) => s.add(v), new THREE.Vector3()).normalize();
    const zs = vs.map((v) => v.z);
    const edge = (z) => { const e = vs.filter((v) => Math.abs(v.z - z) < 0.015); return e.reduce((s, v) => s.add(v), new THREE.Vector3()).divideScalar(e.length); };
    const [hinge, other] = a.hinge === 'front' ? [edge(Math.max(...zs)), edge(Math.min(...zs))] : [edge(Math.min(...zs)), edge(Math.max(...zs))];
    const d = other.clone().sub(hinge);
    d.addScaledVector(n, -d.dot(n)).normalize();
    tiltUniforms.tiltPivot.value[k].copy(hinge);
    tiltUniforms.tiltAxis.value[k].crossVectors(d, n).normalize();
    airbrake.max.push(THREE.MathUtils.degToRad(a.angle));
    // what turns with it: the panel, its underside, and on a centre panel the arms' centre piece
    for (const i of [id, ...find(a.with, p.side), ...(p.side === 'centre' ? find(a.arms, 'centre') : [])]) { ids.push(i); slots.push(k); }
    // its arms: on the same side, or both sides under a centre panel
    for (const i of p.side === 'centre' ? [...find(a.arms, 'left'), ...find(a.arms, 'right')] : find(a.arms, p.side)) {
      const [base, tip] = armEnds(partVertices(geoms, [i]).vs);
      arms.push({ id: i, panel: k, base, tip });
    }
  }));
  tiltUniforms.tiltIds.value = [...ids, ...new Array(8).fill(-1)].slice(0, 8);
  tiltUniforms.tiltSlot.value = [...slots, ...new Array(8).fill(0)].slice(0, 8);
  airbrake.arms = arms.slice(0, 4);
  airbrake.arms.forEach((arm, j) => { tiltUniforms.armIds.value[j] = arm.id; tiltUniforms.armBase.value[j].copy(arm.base); });
}
function showAirbrakes(t) {  // 0 down .. 1 up
  const u = tiltUniforms;
  u.tiltOn.value = t > 0 ? 1 : 0;
  u.tiltAngle.value = [0, 1, 2, 3].map((k) => (airbrake.max[k] || 0) * easeWing(t));
  airbrake.arms.forEach((arm, j) => {  // swing the arm so its tip follows the panel, stretching it to reach
    const pivot = u.tiltPivot.value[arm.panel];
    const moved = arm.tip.clone().sub(pivot).applyAxisAngle(u.tiltAxis.value[arm.panel], u.tiltAngle.value[arm.panel]).add(pivot);
    const from = arm.tip.clone().sub(arm.base), to = moved.sub(arm.base);
    const axis = new THREE.Vector3().crossVectors(from, to);
    u.armAngle.value[j] = axis.lengthSq() > 1e-12 ? from.angleTo(to) : 0;
    if (axis.lengthSq() > 1e-12) u.armAxis.value[j].copy(axis.normalize());
    u.armDir.value[j].copy(from).normalize();
    u.armStretch.value[j] = to.length() / from.length();
  });
}

// The wings' and air brakes' parts move in the vertex shader, in the materials and in the
// shadow's depth pass. After addParts, which declares the part attribute.
function addWing(material) {
  const previous = material.onBeforeCompile;
  const previousKey = material.customProgramCacheKey ? material.customProgramCacheKey.bind(material) : () => '';
  material.onBeforeCompile = (shader) => {
    if (previous) previous(shader);
    Object.assign(shader.uniforms, wingUniforms, tiltUniforms);
    const declare = shader.vertexShader.includes('attribute float part') ? '' : 'attribute float part;';
    shader.vertexShader = shader.vertexShader
      .replace('#include <uv_pars_vertex>', `#include <uv_pars_vertex>
        ${declare}
        uniform float wingOut[ 2 ]; uniform float wingApart[ 2 ]; uniform float wingIds[ 16 ]; uniform float wingOf[ 16 ];
        vec3 wingMove( vec3 v, float p ) {
          if ( wingOut[ 0 ] == 0.0 ) return v;  // shut
          for ( int i = 0; i < 16; i++ ) {
            if ( abs( p - wingIds[ i ] ) > 0.5 ) continue;
            int k = int( wingOf[ i ] + 0.5 ) / 4, role = int( wingOf[ i ] + 0.5 ) - 4 * k;
            float out_ = k == 0 ? wingOut[ 0 ] : wingOut[ 1 ], apart = k == 0 ? wingApart[ 0 ] : wingApart[ 1 ];
            v.y += out_;
            if ( role == 1 || ( role == 3 && abs( v.x ) > ${WING.outer.toFixed(3)} ) ) v.x += sign( v.x ) * apart;
            return v;
          }
          return v;
        }
        uniform float tiltOn; uniform float tiltIds[ 8 ]; uniform float tiltSlot[ 8 ];
        uniform float tiltAngle[ 4 ]; uniform vec3 tiltPivot[ 4 ]; uniform vec3 tiltAxis[ 4 ];
        uniform float armIds[ 4 ]; uniform vec3 armBase[ 4 ]; uniform vec3 armDir[ 4 ]; uniform vec3 armAxis[ 4 ];
        uniform float armAngle[ 4 ]; uniform float armStretch[ 4 ];
        vec3 tiltTurn( vec3 v, vec3 a, float t ) {  // Rodrigues: v turned by t about the unit axis a
          return v * cos( t ) + cross( a, v ) * sin( t ) + a * dot( a, v ) * ( 1.0 - cos( t ) );
        }
        // the air brakes: a panel's parts turn about its hinge; an arm stretches along itself and
        // swings about its base. point: a position (else a normal, which only turns).
        vec3 tiltMove( vec3 v, float p, bool point ) {
          if ( tiltOn == 0.0 ) return v;
          for ( int i = 0; i < 8; i++ ) {
            if ( abs( p - tiltIds[ i ] ) > 0.5 ) continue;
            int s = int( tiltSlot[ i ] + 0.5 );
            if ( !point ) return tiltTurn( v, tiltAxis[ s ], tiltAngle[ s ] );
            return tiltPivot[ s ] + tiltTurn( v - tiltPivot[ s ], tiltAxis[ s ], tiltAngle[ s ] );
          }
          for ( int i = 0; i < 4; i++ ) {
            if ( abs( p - armIds[ i ] ) > 0.5 ) continue;
            if ( !point ) return tiltTurn( v, armAxis[ i ], armAngle[ i ] );
            vec3 l = v - armBase[ i ];
            l += armDir[ i ] * dot( l, armDir[ i ] ) * ( armStretch[ i ] - 1.0 );
            return armBase[ i ] + tiltTurn( l, armAxis[ i ], armAngle[ i ] );
          }
          return v;
        }`)
      .replace('#include <beginnormal_vertex>', `#include <beginnormal_vertex>
        objectNormal = tiltMove( objectNormal, part, false );`)
      .replace('#include <begin_vertex>', `#include <begin_vertex>
        transformed = tiltMove( wingMove( transformed, part ), part, true );`);
  };
  material.customProgramCacheKey = () => `${previousKey()}-wing`;
}
function wingDepthMaterial() {
  const m = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking });
  addWing(m);
  return m;
}

// Braking: the brake lights (code 0) flare, as in the game (checkpoint 1: towards white). Show →
// Braking holds them on (for a picture); the pad's Brake while it's held.
// Brake heat (code 64): the lights test's videos (2026-09-25) show the rims glow faint red
// within a moment of braking, red-orange at 1 s, bright orange (their colour) at 1.5 s, and fade
// out over about 1 s after letting go. The glow goes with the square of the heat, so it starts
// faint. Show → Braking shows it full on.
// Turbo (code 160) isn't on the pad: it comes from turbo pads. A first try lit it from 100 km/h,
// but the lights test's videos (2026-09-25) show nothing green on a straight up to 357 km/h.
const BRAKING = { day: 8, night: 10 };
const BRAKE_HEAT = { up: 1.5, down: 1.3, day: 1.5, night: 2 };
let braking = false, night = false;
function setBraking(on) {
  braking = on;
  if (on) drive.heat = 1;
  pressed(byId('brakeToggle'), on);
  applyBraking();
}
function applyBraking() {
  const look = night ? 'night' : 'day';
  glowUniforms.glowGain.value[0] = braking || drive.brake ? BRAKING[look] : GLOW[0][look];
  glowUniforms.glowGain.value[2] = drive.heat ** 2 * BRAKE_HEAT[look];
  const brake = braking || drive.brake;
  rearUniforms.rearBrake.value = brake ? 1 : 0;
  rearUniforms.rearLevel.value = (brake ? REAR.brake : REAR.on)[look];
}

// ---- The pad under the car: hold Accelerate or Brake (or ↑/W, ↓/S) and the car shows it, the
// speed on its digits, the gear on its rear lights, the brake lights and brake heat (the user's
// idea, 2026-09-25). The pace is the game's, read frame by frame off the user's straight-line
// video (2026-09-25; CHECKLIST.md): full throttle from a standstill on the flat reaches 101 km/h
// at 1.8 s, 162 at 3.6 s, 236 at 6.2 s, 342 at 10.7 s and 372 at 12 s. Braking is the lights
// test's videos (2026-09-25): BRAKE. Reactor boost and the other glows join once the game's
// screenshots show what they do. ----

// km/h per second from each speed up. The video stops at 372: past it the last pace goes on, a guess.
const PACE = [[0, 56], [101, 37], [162, 40], [200, 25]];
const climb = (kmh) => PACE.findLast(([v]) => kmh >= v)[1];
// Letting go (no brake): the car loses 3.5 km/h a second plus 0.3 of its speed, so it rolls
// from 371 km/h to a stop in about 11.6 s, as in the video.
const coast = (kmh) => 3.5 + 0.3 * kmh;
// Braking hard (the lights test's videos, read off the digits): about 180 km/h a second from
// 290 to 145 and 145 from 185 to 85, so 93 + 0.4 of the speed; from 357 or 314 the car stopped
// in 2 to 2.5 s.
const BRAKE = (kmh) => 93 + 0.4 * kmh;
const drive = { speed: SPEED, gear: gearFor(SPEED), pause: 0, gas: false, brake: false, heat: 0, shown: '', last: 0,
  wingUp: SPEED >= WING.openFrom, wingOut: 0, wingApart: 0, wingPause: 0, airbrake: snap ? Number(params.get('airbrake') ?? 0) : 0 };
{  // at the start: open at speed; in snapshots shut, or ?wing= (0.5 out, 1 open too)
  const open = snap ? Number(params.get('wing') ?? 0) : +(SPEED >= WING.openFrom);
  drive.wingOut = Math.min(1, open * 2);
  drive.wingApart = Math.max(0, open * 2 - 1);
  showWing(drive.wingOut, drive.wingApart);
}
function stepWing(dt) {
  const d = drive, was = [d.wingOut, d.wingApart];
  if (d.wingUp) {
    if (d.wingOut < 1) d.wingOut = Math.min(1, d.wingOut + dt / WING.out);
    else if (d.wingApart === 0 && d.wingPause < WING.pause) d.wingPause += dt;
    else d.wingApart = Math.min(1, d.wingApart + dt / WING.apart);
  } else {
    d.wingPause = 0;
    if (d.wingApart > 0) d.wingApart = Math.max(0, d.wingApart - dt / WING.together);
    else d.wingOut = Math.max(0, d.wingOut - dt / WING.back);
  }
  if (d.wingOut !== was[0] || d.wingApart !== was[1]) showWing(d.wingOut, d.wingApart);
  // the air brakes: up while braking (the pad's Brake, or Show → Braking)
  const air = braking || d.brake
    ? Math.min(1, d.airbrake + dt / AIRBRAKE.up) : Math.max(0, d.airbrake - dt / AIRBRAKE.down);
  if (air !== d.airbrake) showAirbrakes(d.airbrake = air);
}
function stepDrive(now) {
  const dt = drive.last ? Math.min(0.1, (now - drive.last) / 1000) : 0;
  drive.last = now;
  if (drive.brake) drive.speed -= BRAKE(drive.speed) * dt;
  else if (!drive.gas) drive.speed -= coast(drive.speed) * dt;
  else if (drive.pause > 0) drive.pause -= dt;  // changing up: the speed holds
  else drive.speed += climb(drive.speed) * dt;
  drive.speed = Math.min(999, Math.max(0, drive.speed));
  if (!drive.gas) drive.pause = 0;
  while (drive.gear < 5 && drive.speed >= GEAR_UP[drive.gear - 1]) {
    drive.gear += 1;
    if (drive.gas) drive.pause = SHIFT_PAUSE;
  }
  while (drive.gear > 1 && drive.speed < GEAR_DOWN[drive.gear - 2]) drive.gear -= 1;
  if (drive.speed >= WING.openFrom) drive.wingUp = true;
  else if (drive.speed < WING.shutBelow) drive.wingUp = false;
  stepWing(dt);
  const heat = braking || drive.brake
    ? Math.min(1, drive.heat + dt / BRAKE_HEAT.up) : Math.max(0, drive.heat - dt / BRAKE_HEAT.down);
  if (heat !== drive.heat) {
    drive.heat = heat;
    applyBraking();
  }
  const kmh = Math.round(drive.speed), shown = `${kmh} ${drive.gear}`;
  if (shown !== drive.shown) {
    drive.shown = shown;
    showSpeed(kmh);
    rearUniforms.rearGear.value = drive.gear;
    byId('padGear').textContent = drive.gear;
  }
}
function hold(pedal, on) {
  if (drive[pedal] === on) return;
  drive[pedal] = on;
  pressed(byId(pedal === 'gas' ? 'padGas' : 'padBrake'), on);
  if (pedal === 'brake') applyBraking();
}
for (const [id, pedal] of [['padGas', 'gas'], ['padBrake', 'brake']]) {
  const b = document.getElementById(id);
  b.addEventListener('pointerdown', (e) => { b.setPointerCapture(e.pointerId); hold(pedal, true); });
  for (const type of ['pointerup', 'pointercancel', 'lostpointercapture']) b.addEventListener(type, () => hold(pedal, false));
}
const PEDAL_KEYS = { ArrowUp: 'gas', KeyW: 'gas', ArrowDown: 'brake', KeyS: 'brake' };
addEventListener('keydown', (e) => { if (PEDAL_KEYS[e.code] && !e.repeat) { hold(PEDAL_KEYS[e.code], true); e.preventDefault(); } });
addEventListener('keyup', (e) => { if (PEDAL_KEYS[e.code]) hold(PEDAL_KEYS[e.code], false); });
addEventListener('blur', () => { hold('gas', false); hold('brake', false); });

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

// The four materials for one skin's textures.
function makeMaterials(tex) {
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
  const out = { Skin: skin, Details: details, Wheels: wheels, Glass: glass };
  for (const [name, material] of Object.entries(out)) addParts(material, sharedMaps[name]);
  addPlate(skin);
  if (tex.Details_I) addDisplays(details);
  addWing(skin);
  addWing(details);
  return out;
}

// Dresses the car in a skin's textures; the first call builds the car.
function dressCar(geoms, tex) {
  const materials = makeMaterials(tex);
  if (!Object.keys(parts).length) {
    const car = new THREE.Group();
    for (const [name, material] of Object.entries(materials)) {
      const mesh = new THREE.Mesh(geoms[name], material);
      mesh.castShadow = name !== 'Glass';
      mesh.receiveShadow = true;
      if (name === 'Skin' || name === 'Details') mesh.customDepthMaterial = wingDepthMaterial();  // its shadow follows the wing
      parts[name] = mesh;
      car.add(mesh);
    }
    scene.add(car);
    return;
  }
  for (const [name, material] of Object.entries(materials)) {
    const old = parts[name].material;
    parts[name].material = material;
    old.dispose();
  }
}

// ---- Day and night ----

function setNight(on) {
  night = on;
  const look = LOOKS[night ? 'night' : 'day'];
  GLOW.forEach((g, i) => { glowUniforms.glowGain.value[i] = night ? g.night : g.day; });
  setBraking(braking);
  scene.environment = envMaps[night ? 'night' : 'day'] || null;
  scene.environmentIntensity = look.env * TUNE.env;
  key.color.set(look.keyColour);
  key.intensity = look.key * TUNE.key;
  document.getElementById('day').setAttribute('aria-pressed', String(!night));
  document.getElementById('night').setAttribute('aria-pressed', String(night));
}

// ---- Skins: the list down the left, and switching the car's paint in place ----

let geometries = null;
let gallery = [];  // tool/gallery.py's entries
let loading = 0;   // the latest request wins when skins are clicked quickly
const titleOf = (name) => name.replace(/^TSC_/, '').replaceAll('_', ' ').replace(/([a-z])(?=[A-Z])/g, '$1 ');

async function loadSkin(name) {
  const ticket = ++loading;
  const res = await fetch(`data/skins/${encodeURIComponent(name)}/skin.json`);
  if (!res.ok) throw new Error(`no skin called ${name} has been prepared for the viewer`);
  const skin = await res.json();
  const tex = await loadTextures(skin.textures);
  if (ticket !== loading) return;
  dressCar(geometries, tex);
  freeTexturesExcept(skin.textures);
  skinName = name;
  showSkinName();
}

function markSkin(name) {
  for (const item of document.querySelectorAll('#skinList .item')) {
    item.setAttribute('aria-current', String(item.dataset.skin === name));
  }
}

function showSkinName() {
  const entry = gallery.find((s) => s.name === skinName);
  const title = entry?.title || titleOf(skinName);
  document.getElementById('title').textContent = title;
  document.getElementById('tag').hidden = !entry?.installed;
  document.title = `${title} · Skin viewer`;
  markSkin(skinName);
}

async function buildSkinList() {
  const res = await fetch('data/gallery.json');
  gallery = res.ok ? await res.json() : [];
  const list = document.getElementById('skinList');
  list.textContent = '';
  document.getElementById('count').textContent = gallery.length || '';
  for (const s of gallery) {
    const item = document.createElement('button');
    item.className = 'item';
    item.dataset.skin = s.name;
    item.disabled = !s.viewable;
    if (!s.viewable) item.title = 'not painted for the viewer yet';
    const pic = s.thumb ? Object.assign(document.createElement('img'), { src: `data/${s.thumb}?t=${Math.floor(s.stamp)}`, alt: '', loading: 'lazy' })
      : Object.assign(document.createElement('span'), { className: 'noPic' });
    const n = Object.assign(document.createElement('span'), { className: 'n', textContent: s.title || titleOf(s.name) });
    if (s.installed) n.append(Object.assign(document.createElement('small'), { textContent: 'In the game' }));
    item.append(pic, n);
    item.onclick = () => switchSkin(s.name);
    list.append(item);
  }
  showSkinName();
  list.querySelector('[aria-current="true"]')?.scrollIntoView({ block: 'center' });
}

async function switchSkin(name) {
  document.body.classList.remove('railOpen');
  if (name === skinName) return;
  const p = new URLSearchParams(location.search);
  p.set('skin', name);
  history.replaceState(null, '', `?${p}`);
  markSkin(name);
  const ticket = loading + 1;
  const slow = setTimeout(() => { if (loading === ticket) statusBox.textContent = `Loading ${titleOf(name)}…`; }, 250);
  try {
    await loadSkin(name);
  } catch (err) {
    showSkinName();
    statusBox.textContent = `Couldn't show ${titleOf(name)}: ${err.message}`;
    setTimeout(() => { statusBox.textContent = ''; }, 4000);
    return;
  } finally {
    clearTimeout(slow);
  }
  if (loading === ticket) statusBox.textContent = '';
}

// ---- A picture of the car: the studio only, no buttons, framed like the snapshots ----

let currentView = 'front';
function savePicture() {
  const ratio = renderer.getPixelRatio();
  const w = canvas.clientWidth, h = canvas.clientHeight;
  renderer.setPixelRatio(Math.max(2, ratio));
  renderer.setSize(w, h, false);
  frame(w, h, true);
  renderer.render(scene, camera);
  canvas.toBlob((blob) => {  // the canvas is copied at the call, before the next frame draws
    const a = Object.assign(document.createElement('a'), { href: URL.createObjectURL(blob), download: `${skinName}_${currentView || 'view'}.png` });
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 10000);
  }, 'image/png');
  renderer.setPixelRatio(ratio);
  resize();
}

// ---- The game's cameras, set by the user ----
// Pick one under Driving, move the view until it looks like the game (drag to turn, right-drag to
// slide the car in the picture, scroll to go nearer), then "Copy Cam N" and paste it to Claude
// (the user's way, 2026-09-25). Claude squares it up straight behind the car, since nobody can
// centre it by hand: only the height, the tilt, the distance and where the car sits count.

let camPicked = null;  // the Driving camera last picked, while the user moves it
const camTitle = (name) => document.querySelector(`#camMenu [data-view="${name}"]`).firstElementChild.textContent;

async function copyCamera() {
  const p = (v) => v.toArray().map((x) => x.toFixed(3)).join(', ');
  const text = `${camTitle(camPicked)} from the viewer: camera at ${p(camera.position)}, looking at ${p(controls.target)}, lens ${camera.fov.toFixed(1)}°`;
  const label = byId('copyCam').firstElementChild;
  try {
    await navigator.clipboard.writeText(text);
    label.textContent = 'Copied: paste it to Claude';
  } catch {  // no clipboard: show the text to copy by hand
    statusBox.textContent = text;
    setTimeout(() => { if (statusBox.textContent === text) statusBox.textContent = ''; }, 20000);
  }
}

// ---- Controls on the page ----

const pressed = (el, on) => el.setAttribute('aria-pressed', String(on));
const byId = (id) => document.getElementById(id);
byId('day').onclick = () => setNight(false);
byId('night').onclick = () => setNight(true);
byId('colourBy').onclick = () => {
  partsState.mode.value = partsState.mode.value ? 0 : 1;
  pressed(byId('colourBy'), partsState.mode.value === 1);
};
byId('shared').onclick = () => {
  partsState.shared.value = partsState.shared.value ? 0 : 1;
  pressed(byId('shared'), partsState.shared.value === 1);
};
byId('togglePartsPanel').onclick = () => {
  const panel = byId('partsPanel');
  panel.hidden = !panel.hidden;
  pressed(byId('togglePartsPanel'), !panel.hidden);
};
byId('showAll').onclick = () => { for (const r of partsState.rows) r.setVisible(true); highlight([]); tip.textContent = ''; };
byId('show').onclick = (e) => {
  e.stopPropagation();
  const menu = byId('showMenu');
  menu.hidden = !menu.hidden;
  byId('show').setAttribute('aria-expanded', String(!menu.hidden));
};
document.addEventListener('click', (e) => {
  if (!byId('showWrap').contains(e.target)) { byId('showMenu').hidden = true; byId('show').setAttribute('aria-expanded', 'false'); }
  if (!byId('camWrap').contains(e.target)) openCams(false);
  if (!byId('rail').contains(e.target) && !byId('railToggle').contains(e.target)) document.body.classList.remove('railOpen');
});
for (const b of document.querySelectorAll('#showMenu [data-part]')) {
  b.onclick = () => {
    const mesh = parts[b.dataset.part];
    if (!mesh) return;
    mesh.visible = !mesh.visible;
    pressed(b, mesh.visible);
  };
}
byId('plateToggle').onclick = () => setPlate(!plateUniforms.plateOn.value);
byId('brakeToggle').onclick = () => setBraking(!braking);
const viewButtons = [...document.querySelectorAll('#bar [data-view]')];
const openCams = (open) => { byId('camMenu').hidden = !open; byId('cam').setAttribute('aria-expanded', String(open)); };
const markView = (name) => {
  currentView = name;
  for (const b of viewButtons) pressed(b, b.dataset.view === name);
  const cam = viewButtons.find((b) => b.dataset.view === name && byId('camMenu').contains(b));
  pressed(byId('cam'), Boolean(cam));  // Driving shows which of the game's cameras is on
  if (cam) byId('camName').textContent = cam.firstElementChild.textContent;
};
for (const b of viewButtons) {
  b.onclick = () => {
    setView(b.dataset.view, true);
    markView(b.dataset.view);
    openCams(false);
    camPicked = byId('camMenu').contains(b) ? b.dataset.view : null;
    controls.minDistance = camPicked ? DRIVING_MIN : 1;
    showCopy();
  };
}
// Copy shows from picking a Driving camera until another view is picked.
const showCopy = () => {
  byId('copyCam').hidden = !camPicked;
  if (camPicked) byId('copyCam').firstElementChild.textContent = `Copy ${camTitle(camPicked)}`;
};
byId('cam').onclick = (e) => { e.stopPropagation(); openCams(byId('camMenu').hidden); };
controls.addEventListener('start', () => {  // the user took the camera
  glide = null;
  markView(null);
  showCopy();
});
byId('copyCam').onclick = copyCamera;
byId('spin').onclick = () => {
  controls.autoRotate = !controls.autoRotate;
  pressed(byId('spin'), controls.autoRotate);
};
byId('save').onclick = savePicture;
byId('railToggle').onclick = () => document.body.classList.toggle('railOpen');
matchMedia('(max-width: 900px)').addEventListener('change', resize);

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
  document.getElementById('title').textContent = titleOf(skinName);
  document.title = `${titleOf(skinName)} · Skin viewer`;
  resize();
  setView('front');
  const [geoms, , doc] = await Promise.all([loadMeshes(), loadLighting(),
    fetch('data/parts.json').then((r) => r.json()), loadShared()]);
  geometries = geoms;
  partsState.doc = doc;
  partTable();
  buildPartsList();
  addRoom();
  await setupPlate(geoms.Skin);
  setupRearLights();
  setupWing();
  setupAirbrakes(geoms);
  showAirbrakes(drive.airbrake);
  await loadSkin(skinName);
  setNight(false);
  if (!snap) {  // on unless this browser turned it off last time
    let on = true;
    try { on = localStorage.getItem('tsc-viewer-number') !== '0'; } catch {}
    setPlate(on);
  }
  renderer.setAnimationLoop((now) => {
    stepGlide();
    if (!snap) stepDrive(now);
    controls.update();
    renderer.render(scene, camera);
  });
  await frames(2);
  statusBox.textContent = '';
  window.viewer.ready = true;
  if (!snap) buildSkinList().catch((err) => console.error(err));
}

start().catch(fail);
