// The skin viewer: the car in a photo studio, wearing one skin, by day or night.
//   /?skin=<name>          the skin prepared by `python -m tool.view <name>`
//   /?skin=<name>&snap=1   no controls on screen, for Claude's snapshots (tool/snap.py)
// Data comes from /data/ (see tool/view.py): car.json + car.bin, the two lighting HDRIs, and
// skins/<name>/skin.json, which gives the URL of every texture slot.

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

// The Details_I alpha codes (CLAUDE.md): how bright each kind of glow is on a parked car, by
// day and at night, and the colour the game supplies for codes whose RGB must be grey. Best
// guesses until checkpoint 4 compares them with the game. Glows that depend on driving are off:
// the stock turbo-colour (160) areas hold smooth white-to-black ramps over the wheel pods, which
// look like a mask the game animates, and in the user's night screenshots they stayed dark
// except thin green edges on the front wing.
const GLOW = [
  { code: 0, day: 1.5, night: 3 },  // brake lights: on all the time, brighter when braking
  { code: 32, day: 1, night: 2 },  // energy, tinted with the team colour
  { code: 64, day: 0, night: 0 },  // brake heat: only when braking hard
  { code: 96, day: 1.5, night: 3 },  // always glowing
  { code: 128, day: 1, night: 8 },  // front lights, bright at night
  { code: 160, day: 0, night: 0, tint: [0.15, 1, 0.3] },  // turbo colour, green in the game
  { code: 192, day: 0, night: 0 },  // exhaust heat: only during turbo
  { code: 224, day: 0, night: 0 },  // boost colour
  { code: 255, day: 0, night: 3 },  // night only
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
  for (const m of meta.meshes) {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(bin, m.position, m.vertices * 3), 3));
    g.setAttribute('normal', new THREE.BufferAttribute(new Float32Array(bin, m.normal, m.vertices * 3), 3));
    g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(bin, m.uv, m.vertices * 2), 2));
    g.setIndex(new THREE.BufferAttribute(new Uint32Array(bin, m.index, m.indices), 1));
    out[m.name] = g;
  }
  return out;
}

const textureLoader = new THREE.TextureLoader();

async function loadTextures(urls) {
  const colour = new Set(['Skin_B', 'Details_B', 'Wheels_B', 'Glass_T', 'Details_I', 'Glass_I']);
  const out = {};
  await Promise.all(Object.entries(urls).map(async ([slot, url]) => {
    if (!url) return;
    const t = await textureLoader.loadAsync('data/' + url);
    t.colorSpace = colour.has(slot) ? THREE.SRGBColorSpace : THREE.NoColorSpace;
    t.anisotropy = maxAniso;
    if (slot.endsWith('_Code')) {  // codes are read exactly: never blended with a neighbour
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

function buildCar(geoms, tex) {
  const std = (set, extra = {}) => ({
    map: tex[`${set}_B`], roughnessMap: tex[`${set}_RM`], metalnessMap: tex[`${set}_RM`],
    roughness: 1, metalness: 1, aoMap: tex[`${set}_AO`], ...extra,
  });
  // Body: a clear coat over the paint. Skin_CoatR sets the coat's roughness; without it the coat
  // follows the paint's roughness. A guess until checkpoint 4 compares it with the game.
  const skin = new THREE.MeshPhysicalMaterial(std('Skin', {
    clearcoat: TUNE.coat, clearcoatRoughness: 1, clearcoatRoughnessMap: tex.Skin_Coat || tex.Skin_RM,
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
document.getElementById('night').onclick = () => setNight(true);for (const b of document.querySelectorAll('#parts button')) {
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
  const [geoms, tex] = await Promise.all([loadMeshes(), loadTextures(skin.textures), loadLighting()]);
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
