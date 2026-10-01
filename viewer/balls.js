// The balls the Lab draws a finish on: one ball, or the car's own tyre for a tread, with the
// viewer's lighting by day. tool/swatches.py paints the textures: {B,RM,Coat}.png, a tread's
// {B,RM,N,AO}.png.

import * as THREE from 'three';
import { HDRLoader } from 'three/addons/loaders/HDRLoader.js';

export const BALL = 0x050506;  // the tiles' ground, so a ball's picture sits in its tile without an edge
export const THUMB = 300;      // px: each tile's picture
export const EXPOSURE = 1.44;  // the viewer's by day; a glow shows as "always on" by day (0.63 on the screen)

export function stage(canvas, size) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, preserveDrawingBuffer: !canvas.isConnected });
  renderer.setPixelRatio(1);
  renderer.setSize(size, size, false);
  renderer.setClearColor(BALL);
  renderer.toneMapping = THREE.LinearToneMapping;  // the viewer's day, matched to the game (viewer.js: LOOKS)
  renderer.toneMappingExposure = EXPOSURE;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, 1, 0.05, 50);
  camera.position.set(1.0, 0.7, 3.9).setLength(size > THUMB ? 4.35 : 5.1);
  camera.lookAt(0, 0, 0);
  const key = new THREE.DirectionalLight(0xfffcf1, 4.4);  // the viewer's sun by day (LOOKS.day), from its side
  key.position.set(0.555, 0.742, 0.377).multiplyScalar(5);
  scene.add(key);
  const ball = new THREE.Mesh(SPHERE, new THREE.MeshPhysicalMaterial());
  const holder = new THREE.Group();  // tilts a tyre so its tread and outer sidewall face the camera
  holder.add(ball);
  scene.add(holder);
  const st = { renderer, scene, camera, ball, holder, shape: null, big: size > THUMB };
  shape(st, 'ball');
  return st;
}

// ---- the shapes: a ball, or the car's own tyre for a tread ----

const SPHERE = new THREE.SphereGeometry(1, 128, 96);
let TYRE = null;  // built from tyre.json the first time a tread shows
async function tyreGeometry() {
  if (TYRE) return TYRE;
  const doc = await (await fetch('data/materials/tyre.json', { cache: 'no-store' })).json();
  TYRE = new THREE.LatheGeometry(doc.points.map(([r, x]) => new THREE.Vector2(r, x)), 256);
  return TYRE;
}
export function shape(st, kind) {
  if (st.shape === kind) return;
  st.shape = kind;
  if (kind === 'tyre') {  // the axle across the picture, the tread rolling toward the camera and filling it
    st.ball.geometry = TYRE;
    st.ball.rotation.set(0, 0, 0);
    st.ball.scale.setScalar(st.big ? 1.3 : 2.3);
    st.holder.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), new THREE.Vector3(1, 0, -0.18).normalize());
  } else {
    st.ball.geometry = SPHERE;
    st.ball.scale.setScalar(1);
    st.ball.rotation.set(0.35, -0.5, 0);
    st.holder.quaternion.identity();
  }
}

const loader = new THREE.TextureLoader();
export async function textures(m, base = `data/materials/${m.slug}/`) {
  const load = async (file, colour) => {
    const t = await loader.loadAsync(`${base}${file}?v=${m.stamp}`);
    t.colorSpace = colour ? THREE.SRGBColorSpace : THREE.NoColorSpace;
    t.anisotropy = 8;
    return t;
  };
  const names = m.maps || ['B', 'RM', 'Coat'];
  const got = await Promise.all(names.map((n) => load(`${n}.png`, n === 'B')));
  const t = Object.fromEntries(names.map((n, i) => [n, got[i]]));
  if (m.shape === 'tyre') await tyreGeometry();
  return { map: t.B, rm: t.RM, coat: t.Coat || null, normal: t.N || null, ao: t.AO || null };
}

export function dress(ball, m, tex) {
  // The car's body material (viewer.js makeMaterials): colour, roughness and metalness from the
  // maps, and the varnish as a clear coat whose amount is the varnish map.
  const old = ball.material;
  // A tyre is the viewer's Wheels material: no varnish, its relief in the normal map, Nadeo's
  // shading in the ambient occlusion as the game adds it.
  ball.material = new THREE.MeshPhysicalMaterial({
    map: tex.map, roughnessMap: tex.rm, metalnessMap: tex.rm, roughness: 1, metalness: 1,
    clearcoat: tex.coat ? 1 : 0, clearcoatRoughness: 0, clearcoatMap: tex.coat, specularIntensity: 0.5,  // the paint's sheen, viewer.js's SHEEN
    normalMap: tex.normal, aoMap: tex.ao, side: m.shape === 'tyre' ? THREE.DoubleSide : THREE.FrontSide,
    emissive: m.glow ? new THREE.Color(...m.glow) : new THREE.Color(0), emissiveIntensity: m.glow ? 0.63 / EXPOSURE : 0,
  });
  old.dispose();
}

// The sky's sun disc cut to `most` (luminance), as viewer.js's sunlessSky: the key is the sun.
function sunless(hdr, most) {
  const d = hdr.image.data, half = d instanceof Uint16Array;
  const get = half ? (i) => THREE.DataUtils.fromHalfFloat(d[i]) : (i) => d[i];
  for (let i = 0; i < d.length; i += 4) {
    const lum = 0.2126 * get(i) + 0.7152 * get(i + 1) + 0.0722 * get(i + 2);
    if (lum <= most) continue;
    for (let c = 0; c < 3; c++) d[i + c] = half ? THREE.DataUtils.toHalfFloat(get(i + c) * most / lum) : d[i + c] * most / lum;
  }
  hdr.needsUpdate = true;
}

// The viewer's day sky, sunless, lighting the given stages as LOOKS.day does.
export async function daySky(stages) {
  const hdr = await new HDRLoader().loadAsync('data/kloofendal_48d_partly_cloudy_puresky.hdr');
  hdr.mapping = THREE.EquirectangularReflectionMapping;
  sunless(hdr, 8);
  for (const s of stages) Object.assign(s.scene, { environment: hdr, environmentIntensity: 0.44 });  // LOOKS.day's env
  return hdr;
}
