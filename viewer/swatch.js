// One material on a ball, lit like the car in the viewer (the same studio HDRI, key light and
// clear-coat model), so what you see here is what the same words give on the car.
//   /swatch.html?m=<slug>          spin it with the mouse
//   /swatch.html?m=<slug>&snap=1   no label, for tool/swatches.py's pictures
// Data: /data/materials/<slug>/swatch.json + PNGs, written by tool/swatches.py.

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { HDRLoader } from 'three/addons/loaders/HDRLoader.js';

const params = new URLSearchParams(location.search);
const snap = params.has('snap');
document.body.classList.toggle('snap', snap);

const canvas = document.getElementById('view');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(snap ? 1 : Math.min(window.devicePixelRatio, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.9;
renderer.shadowMap.enabled = true;
const scene = new THREE.Scene();
scene.background = new THREE.Color('#2a2b2e');
const camera = new THREE.PerspectiveCamera(30, 1, 0.05, 50);
camera.position.set(1.0, 0.7, 3.9);
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.enablePan = false;
controls.minDistance = 2.2;
controls.maxDistance = 6;

const key = new THREE.DirectionalLight(0xfff4e8, 1.1);
key.position.set(2, 4, 1.5);
key.castShadow = true;
key.shadow.mapSize.set(1024, 1024);
scene.add(key);
const floor = new THREE.Mesh(new THREE.CircleGeometry(3, 64), new THREE.MeshStandardMaterial({ color: 0x2a2b2e, roughness: 0.95 }));
floor.rotation.x = -Math.PI / 2;
floor.position.y = -1;
floor.receiveShadow = true;
scene.add(floor);

const ball = new THREE.Mesh(new THREE.SphereGeometry(1, 96, 64), new THREE.MeshPhysicalMaterial({ color: 0x888888 }));
ball.castShadow = true;
scene.add(ball);

function resize() {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
window.addEventListener('resize', resize);

const loader = new THREE.TextureLoader();
async function tex(url, colour = false) {
  const t = await loader.loadAsync(url);
  t.colorSpace = colour ? THREE.SRGBColorSpace : THREE.NoColorSpace;
  t.anisotropy = renderer.capabilities.getMaxAnisotropy();
  return t;
}

async function show(slug) {
  const info = await (await fetch(`data/materials/${slug}/swatch.json`, { cache: 'no-store' })).json();
  const base = `data/materials/${slug}/`;
  const [map, rm, coat] = await Promise.all([tex(base + 'B.png', true), tex(base + 'RM.png'), tex(base + 'Coat.png')]);
  const old = ball.material;
  ball.material = new THREE.MeshPhysicalMaterial({
    map, roughnessMap: rm, metalnessMap: rm, roughness: 1, metalness: 1,
    clearcoat: 1, clearcoatRoughness: 0, clearcoatMap: coat,
    emissive: info.glow ? new THREE.Color(info.glow[0], info.glow[1], info.glow[2]) : new THREE.Color(0),
    emissiveIntensity: 1.2,
  });
  old.dispose();
  document.getElementById('name').textContent = info.name;
  document.getElementById('about').textContent = info.about || '';
  document.title = `${info.name} · Material`;
  await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
}

window.swatch = { ready: false, error: null, show };

async function start() {
  resize();
  const hdr = await new HDRLoader().loadAsync('data/studio_small_09.hdr');
  hdr.mapping = THREE.EquirectangularReflectionMapping;
  scene.environment = hdr;
  scene.environmentIntensity = 1;
  if (params.get('m')) await show(params.get('m'));
  renderer.setAnimationLoop(() => {
    controls.update();
    if (!snap) ball.rotation.y += 0.003;
    renderer.render(scene, camera);
  });
  await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  window.swatch.ready = true;
}
start().catch((e) => { window.swatch.error = String(e && e.stack || e); console.error(e); });
