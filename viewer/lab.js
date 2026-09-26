// The Lab's materials room: every finish the tool knows (tool/swatches.py writes the list and
// each ball's textures from tool/finishes.py), drawn on a ball with the viewer's lighting, with its
// code and numbers and a line to copy for Claude.
//   /lab.html                 the first family
//   /lab.html?m=<slug>        that material picked (e.g. ?m=gold)
// Data: /data/materials/materials.json and /data/materials/<slug>/{B,RM,Coat}.png.

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { HDRLoader } from 'three/addons/loaders/HDRLoader.js';

const params = new URLSearchParams(location.search);
const $ = (id) => document.getElementById(id);
const BALL = 0x050506;  // the tiles' ground, so a ball's picture sits in its tile without an edge
const THUMB = 300;      // px: each tile's picture
const SOURCE = {
  lab: 'Set against the game with the lab skins (24 Sep 2026).',
  measured: 'Colour measured from the real metal (Physically Based), then set by eye. Not yet seen in the game.',
  eye: 'Set by eye in the viewer. Not yet seen in the game.',
  photo: 'A photographed surface you added (ambientCG). Not yet seen in the game.',
};

window.lab = { ready: false, error: null };

// ---- the balls: one renderer draws every tile's picture; the picked one spins in its own ----

function stage(canvas, size) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, preserveDrawingBuffer: !canvas.isConnected });
  renderer.setPixelRatio(1);
  renderer.setSize(size, size, false);
  renderer.setClearColor(BALL);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;  // the viewer's (viewer.js: TUNE.exposure)
  renderer.toneMappingExposure = 0.9;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, 1, 0.05, 50);
  camera.position.set(1.0, 0.7, 3.9).setLength(size > THUMB ? 4.35 : 5.1);
  camera.lookAt(0, 0, 0);
  const key = new THREE.DirectionalLight(0xfff4e8, 1.1);  // the viewer's key light by day
  key.position.set(2, 4, 1.5);
  scene.add(key);
  const ball = new THREE.Mesh(new THREE.SphereGeometry(1, 128, 96), new THREE.MeshPhysicalMaterial());
  ball.rotation.set(0.35, -0.5, 0);
  scene.add(ball);
  return { renderer, scene, camera, ball };
}

const loader = new THREE.TextureLoader();
async function textures(m) {
  const base = `data/materials/${m.slug}/`;
  const load = async (file, colour) => {
    const t = await loader.loadAsync(`${base}${file}?v=${m.stamp}`);
    t.colorSpace = colour ? THREE.SRGBColorSpace : THREE.NoColorSpace;
    t.anisotropy = 8;
    return t;
  };
  const [map, rm, coat] = await Promise.all([load('B.png', true), load('RM.png'), load('Coat.png')]);
  return { map, rm, coat };
}

function dress(ball, m, tex) {
  // The car's body material (viewer.js makeMaterials): colour, roughness and metalness from the
  // maps, and the varnish as a clear coat whose amount is the varnish map.
  const old = ball.material;
  ball.material = new THREE.MeshPhysicalMaterial({
    map: tex.map, roughnessMap: tex.rm, metalnessMap: tex.rm, roughness: 1, metalness: 1,
    clearcoat: 1, clearcoatRoughness: 0, clearcoatMap: tex.coat,
    emissive: m.glow ? new THREE.Color(...m.glow) : new THREE.Color(0), emissiveIntensity: m.glow ? 1.2 : 0,
  });
  old.dispose();
}

const shelf = stage(document.createElement('canvas'), THUMB);
const pictures = new Map();  // slug -> picture URL, for this visit
let queue = Promise.resolve();

function picture(m) {
  if (pictures.has(m.slug)) return Promise.resolve(pictures.get(m.slug));
  const job = queue.then(async () => {
    if (pictures.has(m.slug)) return pictures.get(m.slug);
    const tex = await textures(m);
    dress(shelf.ball, m, tex);
    shelf.renderer.render(shelf.scene, shelf.camera);
    const blob = await new Promise((r) => shelf.renderer.domElement.toBlob(r, 'image/png'));
    Object.values(tex).forEach((t) => t.dispose());
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
  if (m.source === 'measured' || m.source === 'eye') t.querySelector('.code').insertAdjacentHTML('beforeend', ' <em>New</em>');
  t.querySelector('.tv').innerHTML = `Matte ${m.matte} · Metal ${m.metal}<br>${m.varnish ? `Varnish ${m.varnish}` : 'No varnish'}`;
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
  $('colour').innerHTML = m.colour ? `<span class="chip" style="background:${m.colour}"></span>${m.colour}` : 'Any colour: say which';
  $('works').textContent = m.works_on + (m.varnish && !m.works_on.startsWith('Inner') ? '. The varnish shows on the body only.' : '');
  $('source').textContent = SOURCE[m.source] || '';
  $('about').textContent = m.about ? m.about[0].toUpperCase() + m.about.slice(1) + '.' : '';
  $('preview').textContent = m.line;
  const u = new URL(location.href);
  u.searchParams.set('m', m.slug);
  history.replaceState(null, '', u);
  const tex = await textures(m);
  if (picked !== m) { Object.values(tex).forEach((t) => t.dispose()); return; }
  dress(big.ball, m, tex);
  if (bigTex) Object.values(bigTex).forEach((t) => t.dispose());
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
  const hdr = await new HDRLoader().loadAsync('data/studio_small_09.hdr');
  hdr.mapping = THREE.EquirectangularReflectionMapping;
  for (const s of [shelf, big]) s.scene.environment = hdr;
  $('status').textContent = '';
  const want = items.find((m) => m.slug === params.get('m')) || items[0];
  const first = openFamily(want.family, false);
  await pick(want);
  big.renderer.setAnimationLoop(() => {
    big.ball.rotation.y += 0.003;
    controls.update();
    big.renderer.render(big.scene, big.camera);
  });
  await first;
  window.lab.ready = true;
}
start().catch((e) => {
  window.lab.error = String(e && e.stack || e);
  $('status').textContent = e.message || String(e);
  console.error(e);
});
