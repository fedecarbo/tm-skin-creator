// The skin viewer: the car in a photo studio, wearing one skin, by day or night.
//   /?skin=<name>          the skin prepared by `python -m tool.view <name>`
//   /?skin=<name>&snap=1   no controls on screen, for Claude's snapshots (tool/snap.py)
//   /?skin=<name>&embed=1  just the car, which another page lights, turns and takes parts off (the
//                          Lab's UV map room, viewer/lab-rooms.js: show, hide, light, onPick)
//                          or dresses step by step and hangs notes on (the Lab's stand,
//                          viewer/lab-studio.js: dress, picture, onPick, inset, track, camera, go)
//                          and lets the user draw on (pen, onStroke, drawings)
//                          or pins the car's lines on (the Lab's lines room, viewer/lab-lines.js:
//                          snap, curves)
// Data comes from /data/ (see tool/view.py): car.json + car.bin (every triangle corner tagged
// with its part), parts.json (the named parts), <Set>_Shared.png (texels several parts share),
// the two lighting HDRIs, skins/<name>/skin.json, which gives the URL of every texture slot, and
// gallery.json (tool/gallery.py), the list of skins down the left.

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { HDRLoader } from 'three/addons/loaders/HDRLoader.js';
import { createStudio, setStudioTint } from './studio.js';

const params = new URLSearchParams(location.search);
let skinName = params.get('skin') || '';
const snap = params.has('snap');
const embed = params.has('embed');
document.body.classList.toggle('snap', snap || embed);
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
  // ones), standing still, fitted to the user's 2560x1440 screenshots of each (2026-09-25): the
  // tyres' outer edges and tops and the horizon, projected from the model, the lens free, then
  // raised 1.2 cm with the car (car.json's lift_cm). Cam 1 and 2 land within 1.5 px. The game's
  // lens is wider than the 58.7° tall (90° wide) first assumed: 70 to 75° tall, 100 to 110° wide
  // at 16:9. The user had set Cam 1 and 2 by eye in the viewer first: Cam 1 2.47 m up at 12°
  // down, Cam 2 1.82 m up at 6°, through the narrower lens, which drew the car about 1.4 times too
  // big.
  // Cam 1, the chase camera: 3.36 m up, 5.21 m behind the car's centre, 10.9° down.
  cam1: { dir: [0, 0.1891, -0.9820], dist: 5.970, target: [0, 2.238, 0.652], fov: 72.8, ours: 14.03 },
  // Cam 1 again (its key pressed twice), closer: 2.03 m up, 3.00 m behind, 7.7° down. Fitted on
  // 2026-09-27 to the calibration car's screenshot by day (the tyres' outlines, exactly, and the
  // track's vanishing point), within 1.2 px; the same fit gave Cam 1 and 2 within 6 cm and 0.4°.
  cam1alt: { dir: [0, 0.1331, -0.9911], dist: 3.533, target: [0, 1.559, 0.500], fov: 75.0, ours: 7.22 },
  // Cam 2: lower and closer, 2.22 m up, 4.56 m behind, 3.4° down.
  cam2: { dir: [0, 0.0588, -0.9983], dist: 4.962, target: [0, 1.941, 0.390], fov: 74.1, ours: 11.48 },
  // Cam 2 again: lower and closer still, 1.53 m up, 3.20 m behind, 3.3° down, within 1.8 px (as
  // Cam 1 again). Cam 3, over the cockpit, left the menu on 2026-09-27 (the user): the game hides
  // the cockpit there, the viewer didn't.
  cam2alt: { dir: [0, 0.0569, -0.9984], dist: 3.709, target: [0, 1.317, 0.500], fov: 69.9, ours: 6.87 },
};
const FOV = 32;  // every other view's lens
// The Driving cameras through that lens too (the user, 2026-09-27: "the car in the viewer looks
// really badly distorted" through the game's wide one). Each keeps the game camera's line to the
// car's middle and the middle's height in the picture, further back along that line: `ours` metres
// from the middle, where the tyres' widths across the picture (rear and front, averaged) are the
// game's (the wide lens drew the near rear tyres bigger, the front ones smaller). The game's own
// poses stay above. ?lens=game draws them as the game does, for pictures set beside the game's
// screenshots (tool.snap --cams).
const CAR_MIDDLE = new THREE.Vector3(0, 0.55, 0.27);
function throughOurLens(v) {
  const back = new THREE.Vector3(...v.dir).normalize();
  const cam = new THREE.Vector3(...v.target).addScaledVector(back, v.dist);
  const toMid = CAR_MIDDLE.clone().sub(cam);
  const d = toMid.length();
  toMid.divideScalar(d);
  const half = THREE.MathUtils.degToRad(v.fov) / 2, ours = THREE.MathUtils.degToRad(FOV) / 2;
  const pitch = Math.asin(back.y), drop = Math.asin(-toMid.y);  // the view's tilt down; the car's middle's
  const tilt = drop - Math.atan(Math.tan(drop - pitch) * Math.tan(ours) / Math.tan(half));
  const dist = v.ours;
  const dir = new THREE.Vector3(0, Math.sin(tilt), -Math.cos(tilt));
  const target = CAR_MIDDLE.clone().addScaledVector(toMid, -dist).addScaledVector(dir, -dist);
  return { dir: dir.toArray(), dist, target: target.toArray() };
}
if (params.get('lens') !== 'game') for (const k of ['cam1', 'cam1alt', 'cam2', 'cam2alt']) VIEWS[k] = throughOurLens(VIEWS[k]);
// The four moods, each a Poly Haven sky (CC0) lighting the car, matched to the user's screenshots of
// the calibration car in the game. The game maps light to the screen straight, clipping each channel at white
// (LinearToneMapping). Every mood is a sky whose sun (or moon) is the key, the one light that casts
// a shadow, with the sky only a fill: the tops keep the game's greys and the faces the key misses
// fall into shade.
//   day      Kloofendal 48d Partly Cloudy: a blue sky with white clouds, its sun 48 degrees up over the
//            car's front left; sunless cuts the sky's own sun disc to that luminance, so the key alone
//            is the sun (its shadow and its highlight). Was a photo studio (Studio Small 09) until then.
//   sunrise  Belfast Sunset: hazy, its sun low ahead of the car, the back in deep shade, the light a
//            little cool, as the game's.
//   sunset   Qwantani Dusk 2: the sky lights the car's top pink and warm; the sun, low behind it,
//            warms its back.
//   night    Dikhololo Night (no moon in it): a dim blue moonlight from the front left; brighter than
//            the game's, as the user asked ("night is too dark though").
// env and key: the sky's and the key's strength. keyFrom: where the key comes from. envTurn: the sky
// turned about the vertical (degrees) so its sun or glow is where the key comes from (three.js turns
// the sky the other way to the Euler: turn = the sky's sun azimuth - the key's, atan2(z, x)). tint:
// the sky's colour corrected so the calibration car's greys read as the game's. lights: which glows
// are on (GLOW's day or night column): the game lights the night glows at sunset, not at sunrise.
// studio: the studio's colour corrected in that mood (linear, per channel) so its floor reads as the
// game's track in the user's Cam 2 screenshot of the mood (viewer/studio.js); by day the light alone
// does it. Night's is a third: the car is lit brighter than the game's (the user's wish), its
// surroundings as dark as the game's.
const LOOKS = {
  day: { hdr: 'kloofendal_48d_partly_cloudy_puresky', sunless: 8, env: 0.44, key: 4.4, keyColour: 0xfffcf1, exposure: 1.44,
    keyFrom: [0.555, 0.742, 0.377] },
  sunrise: { hdr: 'belfast_sunset_puresky', tint: [0.91, 1, 0.82], env: 0.37, key: 5.8, keyColour: 0xf8f8ff, exposure: 0.48, lights: 'day', keyFrom: [-0.35, 0.45, 0.8],
    envTurn: -75.8, studio: [1.02, 1.07, 1.01] },
  sunset: { hdr: 'qwantani_dusk_2_puresky', tint: [1.33, 1, 0.66], env: 0.8, key: 8, keyColour: 0xffb080, exposure: 0.6, lights: 'night', keyFrom: [-0.6, 0.17, -0.55],
    envTurn: 170, studio: [0.918, 1.1, 1.184] },
  night: { hdr: 'dikhololo_night', env: 2.64, key: 1.5, keyColour: 0xd4dcff, exposure: 0.6, studio: [0.335, 0.326, 0.3] },
};
const KEY_FROM = new THREE.Vector3(0.55, 1, 0.35).normalize();  // above the car's front left
const MOODS = Object.keys(LOOKS);

// Settings any of which can be tried from the address, e.g. ?exposure=1.1&env=0.8, when matching
// the game again. exposure, env, key and glow scale the moods' own; spec the paint's sheen; room how
// light the studio is (a scale on its colour, viewer/studio.js). Also ?turn=<degrees>, added to the sky's envTurn,
// ?keyFrom=x,y,z for the key's direction, and ?tone=aces (or neutral, agx...) for another tone mapping.
const TUNE = { exposure: 1, env: 1, key: 1, glow: 1, coat: 1, room: 1, spec: 1 };
// The paint's own sheen (the body's specularIntensity, under any varnish), half three.js's: at full
// strength it lifted every dark colour like a veil (the calibration car's pure black 64 by day against
// the game's 53, 37 at sunrise against 17); at half, Black to N6.5 read 81 117 158 204 by day against
// the game's 80 114 158 204 (2026-09-27, the user: "its still a bit hazy"). spec in the address scales it.
const SHEEN = 0.5;
for (const key of Object.keys(TUNE)) if (params.has(key)) TUNE[key] = Number(params.get(key));

// The Details_I alpha codes (CLAUDE.md): how bright each kind of glow is on the screen on a car
// standing or driving, by day and at night, and the colour the game supplies for codes whose RGB
// must be grey. A gain is a level on the screen whatever the exposure: 1 shows the texel's own
// colour; above 1 its brightest channel clips and the colour shifts, as in the game (light blue
// goes cyan). From the calibration car in the editor's test drive, standing still (2026-09-27):
// "always on" keeps its colour, a little brighter at night; "night only", the front lights and
// the brake lights are off by day and bright at night (and at sunset), the front lights the
// brightest; energy stayed dark in all four moods (it had glowed dim red at rest in the garage,
// 2026-09-24). Braking flares the brake lights (checkpoint 1's stock strips went towards white:
// BRAKING). Brake heat lights while braking (the lights test's videos, 2026-09-25: BRAKE_HEAT).
// Turbo lights only after a turbo pad, in the pad's colour (the turbo videos, 2026-09-25: the hubs
// yellow for about 3 s after a yellow pad): the pad's Turbo button (TURBO). Exhaust heat ("ON when
// Turbo is enabled", xrayjay's table) lights with it there, a guess until the game shows it. Boost
// stays off.
const GLOW = [
  { code: 0, day: 0, night: 1.6 },  // brake lights: off by day, on at night; BRAKING when braking
  { code: 32, day: 0, night: 0, tint: [1, 0.2, 0.2] },  // energy, tinted by the game (red here)
  { code: 64, day: 0, night: 0 },  // brake heat: while braking (BRAKE_HEAT)
  { code: 96, day: 0.63, night: 0.8 },  // always glowing, its own colour
  { code: 128, day: 0, night: 2.5 },  // front lights: at night, the brightest
  { code: 160, day: 0, night: 0, tint: [1, 0.78, 0.1] },  // turbo: the pad's colour (a yellow pad here)
  { code: 192, day: 0, night: 0 },  // exhaust heat: only during turbo
  { code: 224, day: 0, night: 0 },  // boost colour
  { code: 255, day: 0, night: 1.6 },  // night only
];
const glowUniforms = {
  glowScale: { value: 1 },  // 1 / the exposure, so the gains are levels on the screen
  glowGain: { value: GLOW.map((g) => g.day) },
  glowTint: { value: GLOW.map((g) => new THREE.Vector3(...(g.tint || [1, 1, 1]))) },
};

// ---- Renderer, camera, controls ----

const canvas = document.getElementById('view');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(snap ? 1 : Math.min(window.devicePixelRatio, 2));
const TONES = { aces: THREE.ACESFilmicToneMapping, neutral: THREE.NeutralToneMapping, agx: THREE.AgXToneMapping,
  linear: THREE.LinearToneMapping, reinhard: THREE.ReinhardToneMapping, cineon: THREE.CineonToneMapping };
renderer.toneMapping = TONES[params.get('tone')] ?? THREE.LinearToneMapping;
renderer.toneMappingExposure = LOOKS.day.exposure * TUNE.exposure;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap;  // soft already; PCFSoftShadowMap is gone in 0.186
const maxAniso = renderer.capabilities.getMaxAnisotropy();

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(FOV, 1, 0.05, 400);
const controls = new OrbitControls(camera, canvas);
controls.target.copy(CENTRE);
controls.enableDamping = true;
controls.minDistance = 1;
const DRIVING_MIN = 0.2;  // closer, with a Driving camera picked
controls.maxDistance = 18;
// No limit on the angle: skins paint the underside too, and the floor isn't drawn from below.

// view: a name from VIEWS, or { dir, dist, target, fov } for a close look, or { dir, fit, margin }
// to frame parts (the Lab's rooms, tool/rooms.py). glide: move there smoothly.
let glide = null;
let fitted = null;  // a framing view, framed again when the window changes, until the user turns the car
function setView(view, smooth = false) {
  let v = typeof view === 'string' ? VIEWS[view] : view;
  fitted = v.fit ? v : null;
  if (v.fit) v = { ...v, ...fitView(v) };
  const target = new THREE.Vector3(...(v.target || CENTRE.toArray()));
  const offset = new THREE.Vector3(...v.dir).normalize().multiplyScalar(v.dist * (snap || embed ? 1 : v.roomy || 1));
  const fov = v.fov || FOV;
  framedFrom = { pos: target.clone().add(offset), target: target.clone() };
  if (!smooth) {
    glide = null;
    controls.target.copy(target);
    camera.position.copy(target).add(offset);
    camera.fov = fov;
    camera.updateProjectionMatrix();
    controls.update();
    reframe();
    return;
  }
  // Round the car, not through it: angles and distance change, the target slides.
  const from = new THREE.Spherical().setFromVector3(camera.position.clone().sub(controls.target));
  const to = new THREE.Spherical().setFromVector3(offset);
  let turn = to.theta - from.theta;
  turn -= Math.round(turn / (2 * Math.PI)) * 2 * Math.PI;
  const on = camera.view?.enabled ? camera.view : null;  // the framing on screen
  const frame0 = on && { w: on.fullWidth, h: on.fullHeight, x: on.offsetX, y: on.offsetY, zoom: camera.zoom };
  glide = { start: performance.now(), from, to, turn, target0: controls.target.clone(), target1: target, fov0: camera.fov, fov1: fov, frame0 };
  reframe();
}

// The distance, and the target slid across the picture, that frame the parts `fit` (ids) seen from
// `dir`: their corners inside the picture with `margin` (a share of its half-size) to spare at the
// nearest edge. Found by steps, from a sample of every 8th corner, a few milliseconds.
let fitCorners = null;  // per part id, x y z of every 8th corner
function carCorners() {
  if (!fitCorners) {
    const lists = Array.from({ length: 256 }, () => []);
    for (const g of Object.values(geometries)) {
      const pos = g.getAttribute('position').array, part = g.getAttribute('part').array;
      for (let k = 0; k < part.length; k += 8) lists[part[k]].push(pos[k * 3], pos[k * 3 + 1], pos[k * 3 + 2]);
    }
    fitCorners = lists.map((l) => new Float32Array(l));
  }
  return fitCorners;
}
function fitView(v) {
  const pts = v.fit.map((i) => carCorners()[i]).filter((p) => p && p.length);
  const back = new THREE.Vector3(...v.dir).normalize();
  const right = new THREE.Vector3(0, 1, 0).cross(back).normalize(), up = back.clone().cross(right);
  const ty = Math.tan(THREE.MathUtils.degToRad(v.fov || FOV) / 2), tx = ty * camera.aspect, keep = 1 - (v.margin ?? 0.06);
  const target = new THREE.Vector3();
  let n = 0;
  for (const p of pts) for (let k = 0; k < p.length; k += 3) { target.x += p[k]; target.y += p[k + 1]; target.z += p[k + 2]; n++; }
  if (!n) return { dist: VIEWS.front.dist };
  target.divideScalar(n);
  let dist = VIEWS.front.dist;
  const eye = new THREE.Vector3();
  for (let step = 0; step < 60; step++) {
    eye.copy(target).addScaledVector(back, dist);
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity, behind = false;
    for (const p of pts) {
      for (let k = 0; k < p.length; k += 3) {
        const qx = p[k] - eye.x, qy = p[k + 1] - eye.y, qz = p[k + 2] - eye.z;
        const z = -(qx * back.x + qy * back.y + qz * back.z);
        if (z < 0.05) { behind = true; break; }
        const sx = (qx * right.x + qy * right.y + qz * right.z) / z / tx, sy = (qx * up.x + qy * up.y + qz * up.z) / z / ty;
        if (sx < x0) x0 = sx; if (sx > x1) x1 = sx; if (sy < y0) y0 = sy; if (sy > y1) y1 = sy;
      }
      if (behind) break;
    }
    if (behind) { dist *= 1.3; continue; }
    const size = Math.max(x1 - x0, y1 - y0) / 2 / keep;
    target.addScaledVector(right, ((x0 + x1) / 2) * tx * dist * 0.7).addScaledVector(up, ((y0 + y1) / 2) * ty * dist * 0.7);
    dist *= 1 + 0.6 * (size - 1);
    if (Math.abs(size - 1) < 0.001 && Math.abs(x0 + x1) + Math.abs(y0 + y1) < 0.002) break;
  }
  return { dist, target: target.toArray() };
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
  const f0 = glide.frame0, f1 = framedTo;
  if (f0 && f1 && f0.w === f1.w && f0.h === f1.h) {
    showFraming({ w: f1.w, h: f1.h, x: f0.x + (f1.x - f0.x) * e, y: f0.y + (f1.y - f0.y) * e, zoom: f0.zoom + (f1.zoom - f0.zoom) * e });
  } else if (f1) showFraming(f1);
  if (t >= 1) glide = null;
}

// The car is framed by its own outline in the space the page leaves it: beside the list, between
// the skin's name above and the buttons below (the user, 2026-09-27: in a smaller window "the viewer
// of the car shrinks"). The camera stays where the view puts it, so the car keeps its shape at any
// size: the zoom sizes the picture and a view offset centres the car in that space (it still turns
// about its own centre). Sized so the car stays whole all the way round, as a drag turns it, and
// never bigger than on a full screen. On a screen taller than wide (a phone held upright) the car
// comes closer than that, its nose and tail off the edges, only seen by turning it: nearly twice as
// big on a phone (the user's pick, C, from three renders, 2026-09-27: "right now it's too distant"),
// but never more than 1.55 times as wide as the screen, so the side views keep half of each wheel.
// Where the name and the buttons leave too little room between them (a phone on its side), the car
// is framed in the whole window. Snapshots keep the plain framing.
const FRAMED = { zoom: 0.92, fill: 0.9, tall: 0.8, closer: 2.7, run: 1.55 };
// A Driving camera: the car as big as on the game's screen, lifted clear of the pad (the game's
// picture has the car's tail at 89 % of the height, where the pad sits).
const GAME_FRAMED = { up: 0.12, zoom: 1 };
function railWidth() {
  return parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--rail')) || 0;
}
// Where the car is framed from: the pose the view last set puts the camera in (while it glides
// there, the end of the glide), or where the user left it.
let framedFrom = null;
// The Lab's stand (embed) leaves the car a box between its tags and its strip: viewer.inset.
let embedBox = null;
function frame(w, h, plain) {
  if (plain && !(embed && embedBox)) {
    camera.clearViewOffset();
    camera.aspect = w / h;
    camera.zoom = 1;
    camera.updateProjectionMatrix();
    return;
  }
  framedTo = framing(w, h, embed ? embedBox : null);
  if (!glide) showFraming(framedTo);
}
// The zoom, and the view offset (x, y) that moves the picture's centre, for a window w x h. box: the
// space the Lab leaves the car ({ left, right, top, bottom } in pixels); else beside the list, between
// the name and the buttons.
function framing(w, h, box = null) {
  const left = box ? box.left : railWidth(), right = box ? box.right : 0;
  const pos = framedFrom?.pos || camera.position, target = framedFrom?.target || controls.target;
  const own = !camPicked && outline(pos, target), round = own && outline(pos, target, true);
  if (!own) {  // a Driving camera, or the car not loaded yet: fits across as on the game's 16:9
    const f = camPicked ? GAME_FRAMED : { up: 0.05, zoom: FRAMED.zoom };
    const top = box ? box.top : 0, bottom = box ? box.bottom : 0, freeH = h - top - bottom;
    return { w, h, x: -(left - right) / 2, y: f.up * freeH - (top - bottom) / 2,
      zoom: f.zoom * Math.min(freeH / h, (w - left - right) / h / (camPicked ? 16 / 9 : 1.3)) };
  }
  let top, bottom;
  if (box) [top, bottom] = [box.top, h - box.bottom];
  else {
    const name = byId('name').getBoundingClientRect(), dock = byId('dock').getBoundingClientRect();
    [top, bottom] = [Math.max(0, name.bottom), dock.top];
    if (bottom - top < 0.35 * h) [top, bottom] = [0, h];
  }
  const free = w - left - right;
  const across = free * FRAMED.fill / ((round.x1 - round.x0) * h / 2);
  const down = (bottom - top) * FRAMED.fill / ((round.y1 - round.y0) * h / 2);
  const closer = 1 + FRAMED.closer * Math.max(0, FRAMED.tall - free / h);
  const run = free * FRAMED.run / ((own.x1 - own.x0) * h / 2);
  const zoom = Math.min(FRAMED.zoom, down, across * closer, Math.max(across, run));
  // Move the middle of the car's own outline to the middle of the space.
  const dx = (left + w - right) / 2 - (w / 2 + (own.x0 + own.x1) / 2 * zoom * h / 2);
  const dy = (top + bottom) / 2 - (h / 2 - (own.y0 + own.y1) / 2 * zoom * h / 2);
  return { w, h, x: -dx, y: -dy, zoom };
}
let framedTo = null;  // the framing frame() last worked out
function showFraming(f) {
  camera.setViewOffset(f.w, f.h, f.x, f.y, f.w, f.h);
  camera.zoom = f.zoom;
  camera.updateProjectionMatrix();
}

// The car's outline seen from `pos` looking at `target`: how far it reaches left, right, down and up
// of the picture's centre, in half-heights of the picture through the lens at zoom 1. From every
// 8th corner, as fitView. round: swept all the way round the car at that height and distance, as a
// drag turns it (kept for the next call from the same height and distance).
let roundOutline = null;
function outline(pos, target, round = false) {
  if (!geometries) return null;
  const rel = pos.clone().sub(target);
  const key = [rel.y, Math.hypot(rel.x, rel.z), ...target.toArray()].map((v) => v.toFixed(3)).join();
  if (round && roundOutline?.key === key) return roundOutline.box;
  const ty = Math.tan(THREE.MathUtils.degToRad(FOV) / 2), yAxis = new THREE.Vector3(0, 1, 0);
  const eye = new THREE.Vector3(), back = new THREE.Vector3(), right = new THREE.Vector3(), up = new THREE.Vector3();
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  const turns = round ? 24 : 1;
  for (let t = 0; t < turns; t++) {
    eye.copy(rel).applyAxisAngle(yAxis, (t / turns) * 2 * Math.PI);
    back.copy(eye).normalize();
    eye.add(target);
    right.crossVectors(yAxis, back).normalize();
    up.crossVectors(back, right);
    for (const p of carCorners()) {
      for (let k = 0; k < p.length; k += 3) {
        const qx = p[k] - eye.x, qy = p[k + 1] - eye.y, qz = p[k + 2] - eye.z;
        const z = -(qx * back.x + qy * back.y + qz * back.z);
        if (z < 0.05) continue;
        const sx = (qx * right.x + qy * right.y + qz * right.z) / z / ty, sy = (qx * up.x + qy * up.y + qz * up.z) / z / ty;
        if (sx < x0) x0 = sx; if (sx > x1) x1 = sx; if (sy < y0) y0 = sy; if (sy > y1) y1 = sy;
      }
    }
  }
  if (x0 >= x1) return null;
  const box = { x0, x1, y0, y1 };
  if (round) roundOutline = { key, box };
  return box;
}

// The car is drawn only when something has changed: the camera moved, the car is driving (its wheels,
// wings, air brakes, glows), the user touched the page, a skin or a texture arrived, the Lab called
// (dress, show, mood, hide...), or the page was resized. Two cars drawn at the screen's rate (240 a
// second on the user's PC) kept a processor core busy with the Lab standing still (2026-09-28: "the
// website now is soooo slow"), and a phone warms up showing a car at rest. Claude's snapshots draw
// every frame. wake: frames still to draw; anything new that changes the picture on its own rouses.
let wake = 0;
const drawnCam = new THREE.Matrix4(), drawnProj = new THREE.Matrix4();
const rouse = (n = 3) => { wake = Math.max(wake, n); };
THREE.DefaultLoadingManager.onProgress = () => rouse();  // a texture or the lighting arrived
if (!snap) {
  for (const type of ['pointerdown', 'pointermove', 'pointerup', 'wheel', 'keydown', 'keyup', 'click', 'input', 'change']) {
    addEventListener(type, () => rouse(), { capture: true, passive: true });
  }
}

function resize() {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  rouse();
  renderer.setSize(w, h, false);
  frame(w, h, snap || embed);
  if (fitted) setView(fitted);
}
function reframe() {
  frame(canvas.clientWidth, canvas.clientHeight, snap || embed);
}
window.addEventListener('resize', resize);

// ---- The key light (the room: viewer/studio.js) ----

const key = new THREE.DirectionalLight(LOOKS.day.keyColour, LOOKS.day.key);
key.position.copy(CENTRE).addScaledVector(KEY_FROM, 15);
key.target.position.copy(CENTRE);
key.castShadow = true;
key.shadow.mapSize.set(2048, 2048);
Object.assign(key.shadow.camera, { left: -3.5, right: 3.5, top: 3.5, bottom: -3.5, near: 1, far: 40 });
key.shadow.bias = -0.0004;
key.shadow.normalBias = 0.02;
key.shadow.radius = 8;  // soft, as from a big studio light (3 until the dehaze of 2026-09-27 made it the main light)
scene.add(key, key.target);

scene.background = new THREE.Color('#050506');  // seen only from under the floor

// The room, the floor and the ground shadow: viewer/studio.js.

const envMaps = {};  // a mood -> its HDRI texture

// A sky's colour times tint ([r, g, b]), in place: the HDR's half floats (or floats), RGBA.
function tintSky(hdr, tint) {
  const d = hdr.image.data, half = d instanceof Uint16Array;
  for (let i = 0; i < d.length; i += 4) {
    for (let c = 0; c < 3; c++) {
      d[i + c] = half ? THREE.DataUtils.toHalfFloat(THREE.DataUtils.fromHalfFloat(d[i + c]) * tint[c]) : d[i + c] * tint[c];
    }
  }
  hdr.needsUpdate = true;
}

// A sky's sun taken out, in place: any texel brighter than `most` (luminance) is scaled down to it.
function sunlessSky(hdr, most) {
  const d = hdr.image.data, half = d instanceof Uint16Array;
  const get = half ? (i) => THREE.DataUtils.fromHalfFloat(d[i]) : (i) => d[i];
  const put = half ? (i, v) => { d[i] = THREE.DataUtils.toHalfFloat(v); } : (i, v) => { d[i] = v; };
  for (let i = 0; i < d.length; i += 4) {
    const lum = 0.2126 * get(i) + 0.7152 * get(i + 1) + 0.0722 * get(i + 2);
    if (lum > most) for (let c = 0; c < 3; c++) put(i + c, get(i + c) * most / lum);
  }
  hdr.needsUpdate = true;
}

// A mood's sky, loaded once; the mood on show takes it as soon as it arrives.
const skies = {};
function loadSky(id) {
  return (skies[id] ||= new HDRLoader().loadAsync(`data/${LOOKS[id].hdr}.hdr`).then((hdr) => {
    const look = LOOKS[id];
    hdr.mapping = THREE.EquirectangularReflectionMapping;
    if (look.sunless) sunlessSky(hdr, look.sunless);
    if (look.tint) tintSky(hdr, look.tint);
    envMaps[id] = hdr;
    if (mood === id) scene.environment = hdr;
    return hdr;
  }));
}

// The day's sky before the car shows (the page opens on day), the other moods' once it's up (9 MB
// in all, the day's 5); Claude's snapshots, which show the night too, wait for all four.
async function loadLighting() {
  await (snap ? Promise.all(Object.keys(LOOKS).map(loadSky)) : loadSky('day'));
}

// ---- The car ----

const parts = {};  // Skin, Details, Wheels, Glass -> mesh
const curveGroup = new THREE.Group();  // the Lab's lines room: curves drawn on the body (viewer.curves)
scene.add(curveGroup);
const snapRay = new THREE.Raycaster();

async function loadMeshes() {
  const meta = await (await fetch('data/car.json')).json();
  spinUniforms.spinLift.value = meta.lift_cm / 100;  // the model's axles, raised with it
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
  if (slot.endsWith('_Code') || slot.endsWith('_Shared') || slot.endsWith('_Surfaces')) {  // read exactly: never blended with a neighbour
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
        uniform float glowScale;
        uniform float glowGain[ 9 ];
        uniform vec3 glowTint[ 9 ];`)
      .replace('#include <emissivemap_fragment>', `#ifdef USE_EMISSIVEMAP
          vec3 glowColour = texture2D( emissiveMap, vEmissiveMapUv ).rgb;
          int glowIndex = int( floor( texture2D( glowCodeMap, vEmissiveMapUv ).r * 255.0 / 32.0 + 0.5 ) );
          totalEmissiveRadiance *= glowColour * glowGain[ glowIndex ] * glowTint[ glowIndex ] * glowScale;
        #endif`);
  };
}

// ---- Parts: every corner carries its part id (car/parts.json). A 256x2 table texture holds,
// per part, row 0: visible and highlighted flags, row 1: its colour for "colour by part". The
// materials' shaders read it, so hiding a part is a discard and needs no extra meshes. ----

const partsState = { doc: null, table: null, data: null, hides: 0, mode: { value: 0 }, shared: { value: 0 }, rows: [] };

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
  if (channel === 0) partsState.hides++;  // the floor's shadow is drawn again
}

// One surface of a flat map lit where its paint shows on the car (the Lab's UV map, lightSurface):
// per texture set, <Set>_Surfaces.png (each texel's surface number + 1, tool/view.py) and the
// number lit, -1 for none. Loaded when first lit: the viewer itself never needs them.
const surfaceState = Object.fromEntries(['Skin', 'Details', 'Wheels', 'Glass'].map((set) =>
  [set, { map: { value: null }, id: { value: -1 } }]));

function addParts(material, sharedMap, surface) {
  const previous = material.onBeforeCompile;
  material.onBeforeCompile = (shader) => {
    if (previous) previous(shader);
    Object.assign(shader.uniforms, { partTable: { value: partTable() }, partMode: partsState.mode,
      showShared: partsState.shared, sharedMap: { value: sharedMap || null },
      surfaceMap: surface.map, surfaceId: surface.id });
    shader.vertexShader = shader.vertexShader
      .replace('#include <uv_pars_vertex>', `#include <uv_pars_vertex>
        attribute float part; varying float vPart; varying vec2 vPartUv;`)
      .replace('#include <uv_vertex>', `#include <uv_vertex>
        vPart = part;
        vPartUv = uv;`);
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <map_pars_fragment>', `#include <map_pars_fragment>
        varying float vPart; varying vec2 vPartUv;
        uniform sampler2D partTable; uniform sampler2D sharedMap; uniform int partMode; uniform int showShared;
        uniform sampler2D surfaceMap; uniform float surfaceId;`)
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
          if ( surfaceId >= 0.0 ) {
            vec4 sv = texture2D( surfaceMap, vPartUv );
            float sid = floor( sv.r * 255.0 + 0.5 ) + 256.0 * floor( sv.g * 255.0 + 0.5 ) - 1.0;
            if ( abs( sid - surfaceId ) < 0.5 ) diffuseColor.rgb = mix( diffuseColor.rgb, vec3( 1.0, 0.85, 0.2 ), 0.65 );
          }
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
// Levels on the screen, as GLOW's: on, as "always on"; braking, a red well past full.
const REAR = { colour: [1, 0.015, 0.025], lens: [0.55, 0.06, 0.05], on: { day: 0.63, night: 0.8 }, brake: { day: 3, night: 3 } };
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
// strakes) drops. The blocks under each ("rear bumper", "rear bumper corner")
// move out with it but not apart, so they show in the gaps, as in the video. They
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

// ---- The wheels turn with the pad's speed (the user, 2026-09-25). What turns about each axle:
// the tyre, the rim, the thin ring at the tyre's bead, the wheel covers, and the small split
// ring at the centre (named "brake caliper" in checkpoint 3, but it sits 5 to 7 cm from the
// axle on the outer face). What stays: the fairing inside the wheel ("hub") and the brake light
// that shows through its slot, always behind the axle in the game. Axles from tool/shapes.py,
// raised by the lift that puts the tyres on the floor (car.json's lift_cm: 1.2 cm; without it
// the wheels wobbled, the user saw at once).
// A screen can't show the true rate (at 400 km/h a wheel turns 290° a frame and would seem to
// crawl or run backwards), so the turn eases off towards SPIN.max (rad/s, about 4 turns a
// second): true at walking pace, a steady fast spin from about 40 km/h. Snapshots keep the
// wheels still; ?spin=90 turns them by that many degrees there. ----
const SPIN = { radius: 0.364, max: 25, axle: [0.35252, 1.78314, -1.20163],
  parts: ['tread', 'sidewall', 'rim', 'wheel ring', 'wheel cover ring', 'wheel cover disc', 'wheel cover hub', 'brake caliper'] };
const spinUniforms = { spinAngle: { value: snap ? THREE.MathUtils.degToRad(Number(params.get('spin') ?? 0)) : 0 },
  spinIds: { value: new Array(40).fill(-1) }, spinLift: { value: 0 } };
function setupSpin() {
  const ids = partsState.doc.parts.flatMap((p, i) => (SPIN.parts.includes(p.name) ? [i] : []));
  spinUniforms.spinIds.value = [...ids, ...new Array(40).fill(-1)].slice(0, 40);
}
function stepSpin(dt) {
  const omega = drive.speed / 3.6 / SPIN.radius;  // rad/s
  spinUniforms.spinAngle.value = (spinUniforms.spinAngle.value + SPIN.max * Math.tanh(omega / SPIN.max) * dt) % (2 * Math.PI);
}

// The wings', air brakes' and wheels' parts move in the vertex shader, in the materials and in
// the shadow's depth pass. After addParts, which declares the part attribute.
function addWing(material) {
  const previous = material.onBeforeCompile;
  const previousKey = material.customProgramCacheKey ? material.customProgramCacheKey.bind(material) : () => '';
  material.onBeforeCompile = (shader) => {
    if (previous) previous(shader);
    Object.assign(shader.uniforms, wingUniforms, tiltUniforms, spinUniforms);
    const declare = shader.vertexShader.includes('attribute float part') ? '' : 'attribute float part;';
    const [wy, wzFront, wzRear] = SPIN.axle.map((a) => a.toFixed(5));
    shader.vertexShader = shader.vertexShader
      .replace('#include <uv_pars_vertex>', `#include <uv_pars_vertex>
        ${declare}
        uniform float spinAngle; uniform float spinIds[ 40 ]; uniform float spinLift;
        // the wheels: a turning part's corners go round its axle (the front one ahead of z 0.3 m).
        // point: a position (else a normal, which only turns). A positive angle rolls forward.
        vec3 spinMove( vec3 v, vec3 at, float p, bool point ) {
          if ( spinAngle == 0.0 ) return v;
          bool turns = false;
          for ( int i = 0; i < 40; i++ ) if ( abs( p - spinIds[ i ] ) < 0.5 ) turns = true;
          if ( !turns ) return v;
          float c = cos( spinAngle ), s = sin( spinAngle );
          vec3 axle = point ? vec3( 0.0, ${wy} + spinLift, at.z > 0.3 ? ${wzFront} : ${wzRear} ) : vec3( 0.0 );
          vec3 r = v - axle;
          return axle + vec3( r.x, r.y * c - r.z * s, r.y * s + r.z * c );
        }
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
        objectNormal = tiltMove( spinMove( objectNormal, position, part, false ), part, false );`)
      .replace('#include <begin_vertex>', `#include <begin_vertex>
        transformed = tiltMove( wingMove( spinMove( transformed, position, part, true ), part ), part, true );`);
  };
  material.customProgramCacheKey = () => `${previousKey()}-wing`;
}
// The car's shadow: it follows the wing and the wheels' turn, and a hidden part casts none (the
// Lab's rooms take the shell or the wheels off).
function wingDepthMaterial() {
  const m = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking });
  addWing(m);
  const previous = m.onBeforeCompile, previousKey = m.customProgramCacheKey.bind(m);
  m.onBeforeCompile = (shader) => {
    previous(shader);
    shader.uniforms.partTable = { value: partTable() };
    shader.vertexShader = shader.vertexShader
      .replace('#include <uv_pars_vertex>', `#include <uv_pars_vertex>
        varying float vShadowPart;`)
      .replace('#include <begin_vertex>', `#include <begin_vertex>
        vShadowPart = part;`);
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <clipping_planes_pars_fragment>', `#include <clipping_planes_pars_fragment>
        varying float vShadowPart; uniform sampler2D partTable;`)
      .replace('#include <clipping_planes_fragment>', `#include <clipping_planes_fragment>
        if ( texture2D( partTable, vec2( ( vShadowPart + 0.5 ) / 256.0, 0.25 ) ).r < 0.5 ) discard;`);
  };
  m.customProgramCacheKey = () => `${previousKey()}-hidden`;
  return m;
}

// Braking: the brake lights (code 0) flare, as in the game (checkpoint 1: towards white). Show →
// Braking holds them on (for a picture); the pad's Brake while it's held.
// Brake heat (code 64): the lights test's videos (2026-09-25) show the rims glow faint red
// within a moment of braking, red-orange at 1 s, bright orange (their colour) at 1.5 s, and fade
// out over about 1 s after letting go. The glow goes with the square of the heat, so it starts
// faint. Show → Braking shows it full on.
// Turbo (code 160) isn't on the pad: it comes from turbo pads. Nothing lights it on a straight,
// at any speed (the user's videos, up to 357 km/h).
// Levels on the screen (GLOW): braking well past white, brake heat and turbo about their own colour.
const BRAKING = { day: 6, night: 6 };
const BRAKE_HEAT = { up: 1.5, down: 1.3, day: 1.1, night: 1.3 };
let braking = false, mood = 'day';
const lightsNow = () => LOOKS[mood].lights || mood;  // 'day' or 'night': GLOW's column
function setBraking(on) {
  braking = on;
  if (on) drive.heat = 1;
  pressed(byId('brakeToggle'), on);
  applyBraking();
}
function applyBraking() {
  const look = lightsNow();
  glowUniforms.glowGain.value[0] = braking || drive.brake ? BRAKING[look] : GLOW[0][look];
  glowUniforms.glowGain.value[2] = drive.heat ** 2 * BRAKE_HEAT[look];
  // after a turbo pad the rear lights go red as when braking, with no brake pressed
  const red = braking || drive.brake || drive.turbo > TURBO.glow - TURBO.red;
  rearUniforms.rearBrake.value = red ? 1 : 0;
  rearUniforms.rearLevel.value = (red ? REAR.brake : REAR.on)[look] * glowUniforms.glowScale.value;
  // the turbo colour (code 160) and exhaust heat (192): full on, fading over the last half second
  const turbo = Math.min(1, drive.turbo / TURBO.fade);
  glowUniforms.glowGain.value[5] = turbo * TURBO.gain[look];
  glowUniforms.glowGain.value[6] = turbo * TURBO.gain[look];
}

// ---- The pad under the car: hold Accelerate or Brake (or ↑/W, ↓/S) and the car shows it, the
// speed on its digits, the gear on its rear lights, the brake lights and brake heat (the user's
// idea, 2026-09-25). The pace is the game's, read frame by frame off the user's straight-line
// video (2026-09-25): full throttle from a standstill on the flat reaches 101 km/h
// at 1.8 s, 162 at 3.6 s, 236 at 6.2 s, 342 at 10.7 s and 372 at 12 s. Braking is the lights
// test's videos (2026-09-25): BRAKE. Turbo is a yellow turbo pad, from the user's turbo videos
// (2026-09-25): TURBO. Reactor boost joins once the game shows what it does. ----

// A yellow turbo pad, from the turbo videos (2026-09-25): the turbo colour glows for about 3 s, fading
// over the last half second; the rear lights go red for the first 1.5 s; the speed climbs from about
// 130 to 400 km/h in 2 s. ?turbo=1 holds it on in snapshots.
const TURBO = { glow: 3, fade: 0.5, red: 1.5, push: 2, climb: 135, gain: { day: 0.9, night: 1 } };
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
  turbo: snap && params.get('turbo') === '1' ? TURBO.fade : 0,
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
// One frame of driving; true when the car looks any different for it.
function stepDrive(now) {
  const dt = drive.last ? Math.min(0.1, (now - drive.last) / 1000) : 0;
  drive.last = now;
  const was = [drive.speed, drive.turbo, drive.heat, drive.wingOut, drive.wingApart, drive.airbrake];
  if (drive.turbo > 0) {
    if (drive.turbo > TURBO.glow - TURBO.push && !drive.brake) drive.speed += TURBO.climb * dt;
    drive.turbo = Math.max(0, drive.turbo - dt);
    applyBraking();
    pressed(byId('padTurbo'), drive.turbo > 0);
  }
  if (drive.brake) drive.speed -= BRAKE(drive.speed) * dt;
  else if (!drive.gas && drive.turbo <= TURBO.glow - TURBO.push) drive.speed -= coast(drive.speed) * dt;
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
  stepSpin(dt);
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
  return drive.speed > 0 || [drive.speed, drive.turbo, drive.heat, drive.wingOut, drive.wingApart, drive.airbrake].some((v, i) => v !== was[i]);
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
function turbo() {
  drive.turbo = TURBO.glow;
  applyBraking();
  pressed(byId('padTurbo'), true);
}
document.getElementById('padTurbo').addEventListener('click', turbo);
// The pedal keys drive the viewer's own page only: embedded in the Lab nothing counts the turbo down
// (stepDrive doesn't run there), so T left the car glowing for good (2026-09-27).
if (!snap && !embed) {
  addEventListener('keydown', (e) => { if (e.code === 'KeyT' && !e.repeat) turbo(); });
  const PEDAL_KEYS = { ArrowUp: 'gas', KeyW: 'gas', ArrowDown: 'brake', KeyS: 'brake' };
  addEventListener('keydown', (e) => { if (PEDAL_KEYS[e.code] && !e.repeat) { hold(PEDAL_KEYS[e.code], true); e.preventDefault(); } });
  addEventListener('keyup', (e) => { if (PEDAL_KEYS[e.code]) hold(PEDAL_KEYS[e.code], false); });
  addEventListener('blur', () => { hold('gas', false); hold('brake', false); });
}

function partLabel(p) {
  const tag = [p.end, p.side === 'centre' ? '' : p.side].filter(Boolean).join(' ');
  return tag ? `${p.name} (${tag})` : p.name;
}

// The list: the car's groups (the game's maps: Body, Details, Tyres, Glass), their assemblies, then
// one row per (name, end); the row's checkbox hides both sides together. A short group (Tyres,
// Glass) lists its parts right under it.
const SHORT_GROUP = 10;  // rows
function buildPartsList() {
  const list = document.getElementById('partsList');
  list.textContent = '';
  const { parts, groups, assemblies } = partsState.doc;
  for (const grp of groups) {
    const asms = assemblies.map((asm) => ({ asm, rows: partRows(parts, asm.name, grp.name) })).filter((a) => a.rows.length);
    if (!asms.length) continue;
    const all = asms.flatMap((a) => a.rows);
    const [gbox, gitems] = listBox('group', grp.name, grp.about, all, 'show or hide the whole group');
    if (all.length <= SHORT_GROUP) {
      gitems.append(...all.map((r) => r.row));
      list.append(gbox);
      continue;
    }
    for (const { asm, rows } of asms) {
      const [abox, aitems] = listBox('assembly closed', asm.name, asm.about, rows, 'show or hide the whole assembly');
      aitems.append(...rows.map((r) => r.row));
      gitems.append(abox);
    }
    list.append(gbox);
  }
}

// A heading that opens and closes its items, with a checkbox for all its rows.
function listBox(cls, name, about, rows, title) {
  const box = document.createElement('div');
  box.className = cls;
  const head = document.createElement('div');
  head.className = 'head';
  const all = document.createElement('input');
  all.type = 'checkbox';
  all.checked = true;
  all.title = title;
  all.onclick = (e) => { e.stopPropagation(); for (const r of rows) r.setVisible(all.checked); };
  head.append(all, Object.assign(document.createElement('span'), { className: 'label', textContent: name }),
    Object.assign(document.createElement('span'), { className: 'about', textContent: about }));
  head.onclick = () => box.classList.toggle('closed');
  const items = document.createElement('div');
  items.className = 'items';
  box.append(head, items);
  return [box, items];
}

function partRows(parts, assembly, group) {
  const rows = new Map();
  parts.forEach((p, i) => {
    if (p.parent !== assembly || p.group !== group) return;
    const key = `${p.name}|${p.end}`;
    if (!rows.has(key)) rows.set(key, { name: p.name, end: p.end, ids: [] });
    rows.get(key).ids.push(i);
  });
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
    only.onclick = (e) => { e.stopPropagation(); for (const o of partsState.rows) o.setVisible(o === r); };
    row.onclick = () => highlight(r.ids, r);
    row.append(cb, name, tag, only);
    r.row = row;
    partsState.rows.push(r);
  }
  return [...rows.values()];
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
      for (let el = r.row.closest('.closed'); el; el = el.closest('.closed')) el.classList.remove('closed');
      r.row.scrollIntoView({ block: 'nearest' });
    }
  }
}

// Clicking the car names the part under the pointer.
const raycaster = new THREE.Raycaster();
const tip = document.getElementById('tip');
const partOfHit = (hit) => hit.object.geometry.getAttribute('part').getX(hit.face.a);
// The car under a point of the page: { at, normal, part, distance } (metres; the surface's facing),
// or null. Only the parts shown count.
function carAt(x, y) {
  raycaster.setFromCamera(new THREE.Vector2((x / innerWidth) * 2 - 1, -(y / innerHeight) * 2 + 1), camera);
  const hit = raycaster.intersectObjects(Object.values(parts).filter((m) => m.visible))
    .find((h) => partsState.data[partOfHit(h) * 4] > 0);
  return hit ? { at: hit.point.toArray(), normal: hit.face.normal.clone().transformDirection(hit.object.matrixWorld).toArray(),
    part: partOfHit(hit), distance: hit.distance } : null;
}
let pressAt = null;
canvas.addEventListener('pointerdown', (e) => { pressAt = [e.clientX, e.clientY]; });
canvas.addEventListener('pointerup', (e) => {
  if (!pressAt || Math.hypot(e.clientX - pressAt[0], e.clientY - pressAt[1]) > 4 || !partsState.doc) return;
  const hit = carAt(e.clientX, e.clientY);
  if (embed) {  // the page around it picks the part; the Studio pins a note to the point
    if (hit && window.viewer.onPick) window.viewer.onPick(hit.part, { at: hit.at, normal: hit.normal });
    return;
  }
  tip.textContent = '';
  if (!hit) { highlight([]); return; }
  const id = hit.part;
  const p = partsState.doc.parts[id];
  highlight([id]);
  tip.textContent = `${partLabel(p)} · ${p.mesh}${p.shared > 0.5 ? ' · shared with its twin' : ''}`;
  tip.style.left = `${Math.min(e.clientX + 14, innerWidth - 260)}px`;
  tip.style.top = `${e.clientY + 14}px`;
});

// The Lab's pen (viewer.pen, the stand's Draw): a drag that starts on the car draws on it, one that
// starts off it turns the car, and a tap still picks (onPick). The line shows as it's drawn, and at
// its end onStroke([{ points, normals, parts }]) gets it on the body in metres, in pieces: where the
// pointer leaves the car, or the line jumps across an opening or off an edge, a new piece starts.
// The moves are read once a frame, a ray every PEN_PX pixels along each, so a fast one still hugs
// the surface round a corner.
const PEN_PX = 5;          // px between the rays along a move
const PEN_STEP = 0.003;    // m between kept points
const PEN_JUMP = 6;        // a jump this many times the ray step's own length on the car is a gap
const PEN_WIDTH = 5;        // px, however near the car is
const PEN_COLOUR = '#e8ff47';
let penOn = false, stroke = null;
const penGroup = new THREE.Group(), drawnGroup = new THREE.Group();  // the line being drawn; the notes' (viewer.drawings)
scene.add(penGroup, drawnGroup);
const penHeight = { value: 1 };  // the page's height in px, for the lines' width

// A drawn line: a tube PEN_WIDTH pixels thick wherever the camera is, brought towards the camera by
// a little more than its own thickness, so it lies on the paint instead of sinking into it, and
// still goes behind whatever of the car is in front of it.
function penMaterial(colour, dim) {
  const m = new THREE.MeshBasicMaterial({ color: colour, transparent: dim, opacity: dim ? 0.5 : 1, toneMapped: false });
  m.onBeforeCompile = (shader) => {
    shader.uniforms.penHeight = penHeight;
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nattribute vec3 centre;\nuniform float penHeight;')
      .replace('#include <project_vertex>', `
        vec4 mid = modelViewMatrix * vec4(centre, 1.0);
        float r = ${(PEN_WIDTH / 2).toFixed(1)} * 2.0 * -mid.z / (projectionMatrix[1][1] * penHeight);  // m
        vec4 mvPosition = vec4(mid.xyz + mat3(modelViewMatrix) * (transformed - centre) * r
          - normalize(mid.xyz) * (r + 0.004), 1.0);
        gl_Position = projectionMatrix * mvPosition;`);
  };
  return m;
}

function penLine(list, group) {  // [{ points, colour, dim }] as lines on the body
  for (const c of group.children) { c.geometry.dispose(); c.material.dispose(); }
  group.clear();
  for (const c of list) {
    if (!c.points || c.points.length < 2) continue;
    const path = new THREE.CatmullRomCurve3(c.points.map((p) => new THREE.Vector3(...p)), false, 'centripetal');
    const n = Math.min(2000, Math.max(2, c.points.length * 3)), round = 6;
    const geo = new THREE.TubeGeometry(path, n, 1, round, false);  // a unit radius: the shader sizes it
    const centre = new Float32Array(geo.getAttribute('position').count * 3), at = new THREE.Vector3();
    for (let i = 0; i <= n; i++) {
      path.getPointAt(i / n, at);
      for (let j = 0; j <= round; j++) at.toArray(centre, (i * (round + 1) + j) * 3);
    }
    geo.setAttribute('centre', new THREE.BufferAttribute(centre, 3));
    const mesh = new THREE.Mesh(geo, penMaterial(c.colour || PEN_COLOUR, !!c.dim));
    mesh.frustumCulled = false;  // the shader moves it off its bounds
    mesh.onBeforeRender = () => { penHeight.value = canvas.clientHeight || 1; };
    group.add(mesh);
  }
}

function penAdd(hit, px) {  // a ray's hit into the stroke: kept, skipped (too near), or a new piece
  const piece = stroke.pieces[stroke.pieces.length - 1];
  const last = piece && piece.points[piece.points.length - 1];
  if (last) {
    const d = Math.hypot(hit.at[0] - last[0], hit.at[1] - last[1], hit.at[2] - last[2]);
    if (d < PEN_STEP && !stroke.missed) return;
    // the length one pixel covers on the car, there: a jump far past it left the surface
    const perPx = 2 * hit.distance * Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2) / (innerHeight * camera.zoom);
    if (stroke.missed || d > Math.max(0.03, PEN_JUMP * px * perPx)) stroke.pieces.push({ points: [], normals: [], parts: [] });
  } else if (!piece) stroke.pieces.push({ points: [], normals: [], parts: [] });
  const p = stroke.pieces[stroke.pieces.length - 1];
  p.points.push(hit.at);
  p.normals.push(hit.normal);
  p.parts.push(hit.part);
  stroke.missed = false;
}

function penMove() {  // the moves since the last frame, a ray every PEN_PX pixels
  stroke.frame = 0;
  const [x1, y1] = stroke.to, [x0, y0] = stroke.from;
  const n = Math.min(24, Math.max(1, Math.ceil(Math.hypot(x1 - x0, y1 - y0) / PEN_PX)));
  for (let k = 1; k <= n; k++) {
    const x = x0 + (x1 - x0) * k / n, y = y0 + (y1 - y0) * k / n;
    const hit = carAt(x, y);
    if (hit) penAdd(hit, Math.hypot(x1 - x0, y1 - y0) / n);
    else stroke.missed = true;
  }
  stroke.from = stroke.to;
  penLine(stroke.pieces.map((p) => ({ points: p.points })), penGroup);
  rouse();
}

if (embed) {  // on the window, ahead of the controls: a drag that starts on the car isn't theirs
  addEventListener('pointerdown', (e) => {
    if (!penOn || stroke || e.button !== 0 || e.target !== canvas || !partsState.doc) return;
    const hit = carAt(e.clientX, e.clientY);
    if (!hit) return;  // off the car: it turns
    e.stopPropagation();
    canvas.setPointerCapture(e.pointerId);
    stroke = { id: e.pointerId, start: [e.clientX, e.clientY], from: [e.clientX, e.clientY], to: null, first: hit,
      moved: false, missed: false, frame: 0, pieces: [] };
    penAdd(hit, 1);
  }, { capture: true });
  addEventListener('pointermove', (e) => {
    if (!stroke || e.pointerId !== stroke.id) return;
    e.stopPropagation();
    if (Math.hypot(e.clientX - stroke.start[0], e.clientY - stroke.start[1]) > 4) stroke.moved = true;
    if (!stroke.moved) return;
    stroke.to = [e.clientX, e.clientY];
    if (!stroke.frame) stroke.frame = requestAnimationFrame(penMove);
  }, { capture: true });
  const penUp = (e) => {
    if (!stroke || e.pointerId !== stroke.id) return;
    e.stopPropagation();
    if (stroke.frame) { cancelAnimationFrame(stroke.frame); penMove(); }
    const s = stroke;
    stroke = null;
    pressAt = null;
    if (!s.moved) {  // a tap: a pin, as without the pen
      if (window.viewer.onPick) window.viewer.onPick(s.first.part, { at: s.first.at, normal: s.first.normal });
      return;
    }
    const pieces = s.pieces.filter((p) => p.points.length >= 2);
    if (pieces.length && window.viewer.onStroke) window.viewer.onStroke(pieces);
    else penLine([], penGroup);
  };
  addEventListener('pointerup', penUp, { capture: true });
  addEventListener('pointercancel', penUp, { capture: true });
}

// The four materials for one skin's textures.
function makeMaterials(tex) {
  const std = (set, extra = {}) => ({
    map: tex[`${set}_B`], roughnessMap: tex[`${set}_RM`], metalnessMap: tex[`${set}_RM`],
    roughness: 1, metalness: 1, aoMap: tex[`${set}_AO`], ...extra,
  });
  // Body: a glossy varnish (clear coat) over the paint. In the game, Skin_CoatR at 0 is a glossy
  // varnish over anything, 255 adds no gloss, and a skin without the file is glossy all over
  // (checked with the lab skins, 2026-09-24). Skin_Coat holds 255 - CoatR in R,
  // which three.js reads as the coat's amount.
  const skin = new THREE.MeshPhysicalMaterial(std('Skin', {
    clearcoat: TUNE.coat, clearcoatRoughness: 0, clearcoatMap: tex.Skin_Coat || null, specularIntensity: SHEEN * TUNE.spec,
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
  for (const [name, material] of Object.entries(out)) addParts(material, sharedMaps[name], surfaceState[name]);
  addPlate(skin);
  if (tex.Details_I) addDisplays(details);
  addWing(skin);
  addWing(details);
  addWing(wheels);  // for the wheels' turn
  return out;
}

// Dresses the car in a skin's textures; the first call builds the car.
function dressCar(geoms, tex) {
  rouse();
  const materials = makeMaterials(tex);
  if (!Object.keys(parts).length) {
    const car = new THREE.Group();
    for (const [name, material] of Object.entries(materials)) {
      const mesh = new THREE.Mesh(geoms[name], material);
      mesh.castShadow = name !== 'Glass';
      mesh.receiveShadow = true;
      if (name !== 'Glass') mesh.customDepthMaterial = wingDepthMaterial();  // its shadow follows the wing
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

// ---- Day, sunrise, sunset and night ----

// m: a name from LOOKS, or true / false for night / day (what snapshots pass).
function setMood(m) {
  mood = m === true ? 'night' : m === false || !LOOKS[m] ? 'day' : m;
  const look = LOOKS[mood];
  GLOW.forEach((g, i) => { glowUniforms.glowGain.value[i] = g[lightsNow()]; });
  glowUniforms.glowScale.value = TUNE.glow / (look.exposure * TUNE.exposure);
  renderer.toneMappingExposure = look.exposure * TUNE.exposure;
  setBraking(braking);
  scene.environment = envMaps[mood] || null;
  setStudioTint(look.studio || [1, 1, 1]);
  // envTurn: the sky turned about the vertical (degrees) so its sun or glow is where the key comes from
  scene.environmentRotation.set(0, THREE.MathUtils.degToRad((look.envTurn || 0) + Number(params.get('turn') || 0)), 0);
  scene.environmentIntensity = look.env * TUNE.env;
  key.color.set(look.keyColour);
  key.intensity = look.key * TUNE.key;
  const keyFrom = params.get('keyFrom') ? params.get('keyFrom').split(',').map(Number) : look.keyFrom;  // ?keyFrom=x,y,z to try one
  key.position.copy(CENTRE).addScaledVector(keyFrom ? new THREE.Vector3(...keyFrom).normalize() : KEY_FROM, 15);
  for (const m of MOODS) document.getElementById(m).setAttribute('aria-pressed', String(m === mood));
  // the menu's button shows the mood picked: its icon and name
  const picked = document.getElementById(mood);
  document.getElementById('moodIcon').setAttribute('href', picked.querySelector('use').getAttribute('href'));
  document.getElementById('moodName').textContent = picked.lastElementChild.textContent;
  markStudio();
}

// ---- The page's lettering over the studio (viewer/studio.js; index.html) ----

// The buttons on a dark glass always (body.lightStudio), and where the studio is light (by day, the
// track's 205, and at sunset, 155), the car's name and the speed in dark ink (body.brightStudio).
function markStudio() {
  document.body.classList.add('lightStudio');
  document.body.classList.toggle('brightStudio', mood === 'day' || mood === 'sunset');
}

// ---- Skins: the list down the left, and switching the car's paint in place ----

let geometries = null;
let gallery = [];  // tool/gallery.py's entries
let loading = 0;   // the latest request wins when skins are clicked quickly (loadSkin, dress)
let wanted = '';   // the skin last asked for: shown, or on its way
const titleOf = (name) => name.replace(/^TSC_/, '').replaceAll('_', ' ').replace(/([a-z])(?=[A-Z])/g, '$1 ');

async function loadSkin(name) {
  const ticket = ++loading;
  wanted = name;
  const res = await fetch(`data/skins/${encodeURIComponent(name)}/skin.json`);
  if (!res.ok) throw new Error(`no skin called ${name} has been prepared for the viewer`);
  const skin = await res.json();
  const tex = await loadTextures(skin.textures);
  if (ticket !== loading) return;
  dressCar(geometries, tex);
  freeTexturesExcept(skin.textures);
  skinName = name;
  showSkinName();
  const lab = document.querySelector('#railFoot a[href*="lab.html"]');  // the Lab shows this skin's paint
  if (lab) lab.href = `./lab.html?skin=${encodeURIComponent(name)}`;
  if (!snap && !embed) try { localStorage.setItem('tsc-viewer-skin', name); } catch {}
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
  reframe();  // the name may take another line
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
  if (name === wanted) return;
  const p = new URLSearchParams(location.search);
  p.set('skin', name);
  history.replaceState(null, '', `?${p}`);
  markSkin(name);
  const ticket = loading + 1;
  const slow = setTimeout(() => { if (loading === ticket) statusBox.textContent = `Loading ${titleOf(name)}…`; }, 250);
  try {
    await loadSkin(name);
  } catch (err) {
    if (wanted === name) wanted = skinName;
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

// ---- The game's cameras ----
// Beside the views, the game's closer Cam 1 and Cam 2 (cam1alt and cam2alt in VIEWS, fitted to the
// user's screenshots), as two buttons named Cam 1 and Cam 2 with no others (the user, 2026-09-27).

let camPicked = null;  // the game camera (Cam 1 or 2) last picked, while the user moves it

// ---- Controls on the page ----

const pressed = (el, on) => el.setAttribute('aria-pressed', String(on));
const byId = (id) => document.getElementById(id);
const openMoods = (open) => { byId('moodMenu').hidden = !open; byId('mood').setAttribute('aria-expanded', String(open)); };
byId('mood').onclick = (e) => { e.stopPropagation(); openMoods(byId('moodMenu').hidden); };
for (const m of MOODS) byId(m).onclick = () => { setMood(m); openMoods(false); };
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
  if (!byId('moodWrap').contains(e.target)) openMoods(false);
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
const markView = (name) => {
  currentView = name;
  for (const b of viewButtons) pressed(b, b.dataset.view === name);
};
for (const b of viewButtons) {
  b.onclick = () => {
    setView(b.dataset.view, true);
    markView(b.dataset.view);
    camPicked = 'cam' in b.dataset ? b.dataset.view : null;
    controls.minDistance = camPicked ? DRIVING_MIN : 1;
    resize();  // a Driving camera frames the car as the game does
  };
}
controls.addEventListener('start', () => {  // the user took the camera
  glide = null;
  if (framedTo) showFraming(framedTo);
  fitted = null;
  framedFrom = null;
  markView(null);
});
byId('save').onclick = savePicture;
byId('railToggle').onclick = () => document.body.classList.toggle('railOpen');
matchMedia('(max-width: 1280px)').addEventListener('change', resize);  // the list folds (index.html)

// ---- Start ----

const frames = (n) => new Promise((done) => {
  rouse(n + 1);  // drawn in them, in the Lab too
  const step = () => (--n <= 0 ? done() : requestAnimationFrame(step));
  requestAnimationFrame(step);
});

// What tool/snap.py drives.
window.viewer = {
  ready: false,
  error: null,
  async load(name) {  // another skin in the same page: the tyre library's sheet (tool/tyresheet.py)
    await loadSkin(name);
    await frames(3);
  },
  async show(view, night = false, hidden = []) {  // night: true, false or a mood's name
    setMood(night);
    if (embed) pickCam(view);
    setView(view);
    for (const [name, mesh] of Object.entries(parts)) mesh.visible = !hidden.includes(name);
    await frames(3);
  },
  // Parts settings: { colourBy, shared, hidden: [part names], only: [part names], highlight: [part names] }.
  // A name matches a part, its assembly, its group (unless a part or assembly has that name, as the
  // paint box reads it: "floor"), or "name|side|end".
  async showParts(opts = {}) {
    const own = new Set(partsState.doc.parts.flatMap((p) => [p.name, p.parent]));
    const match = (names) => partsState.doc.parts.map((p, i) => [p, i]).filter(([p]) => names.some((n) =>
      n === p.name || n === p.parent || (n === p.group && !own.has(n)) || n === `${p.name}|${p.side}|${p.end}`)).map(([, i]) => i);
    partsState.mode.value = opts.colourBy ? 1 : 0;
    partsState.shared.value = opts.shared ? 1 : 0;
    const hidden = new Set(match(opts.hidden || []));
    const only = opts.only ? new Set(match(opts.only)) : null;
    for (const r of partsState.rows) r.setVisible(r.ids.every((i) => !hidden.has(i) && (!only || only.has(i))));
    highlight([]);
    if (opts.highlight) highlight(match(opts.highlight));
    await frames(3);
  },
  // The Lab's UV map room (viewer/lab-rooms.js, ?embed=1): take parts off (by id; the rest
  // show), light parts by id, turn the car to face them, and hear which part a click on the car picks.
  hide(ids) {
    const off = new Set(ids);
    partsState.doc.parts.forEach((p, i) => { partsState.data[i * 4] = off.has(i) ? 0 : 255; });
    partsState.table.needsUpdate = true;
    partsState.hides++;  // the floor's shadow is drawn again
    for (const a of tracked) a.behind = undefined;  // a part taken off may have hidden a tag's point
  },
  light(ids) {
    setPartFlag(litIds, 1, false);
    litIds = [...ids];
    setPartFlag(litIds, 1, true);
  },
  // light one surface of a texture set's flat map (its number in uvmap.json), or none (set null)
  async lightSurface(set, id) {
    for (const [name, s] of Object.entries(surfaceState)) s.id.value = name === set ? id : -1;
    const s = surfaceState[set];
    if (s && id >= 0 && !s.map.value) s.map.value = await loadTexture(`${set}_Surfaces`, `${set}_Surfaces.png`);
  },
  onPick: null,
  // The Lab's stand (viewer/lab-studio.js, ?embed=1), which draws its own tags over this page.
  // inset: the box the car is framed in, the rest of the page left to the tags ({ left, right, top,
  // bottom } in pixels, or null for the whole page).
  inset(box) {
    embedBox = box && { left: box.left || 0, right: box.right || 0, top: box.top || 0, bottom: box.bottom || 0 };
    resize();
  },
  // track: points on the car ([{ key, at: [x, y, z], normal }]); onMove([{ key, x, y, shown, away }])
  // runs at the end of every frame in which one of them moved on the page, so the tags drawn from it
  // land in the same frame as the car. shown: in the picture; away: facing away, or hidden by the car.
  track(list, onMove) {
    tracked = list.filter((a) => a.at).map((a) => ({ key: a.key, at: new THREE.Vector3(...a.at), normal: a.normal ? new THREE.Vector3(...a.normal) : null }));
    onTrack = onMove;
    trackSig = '';
    stillFor = 0;
    if (onTrack) trackAnchors();
  },
  // the pen (above): while it's on, a drag that starts on the car draws, and onStroke gets the line
  pen(on) {
    penOn = !!on;
    canvas.style.cursor = penOn ? 'crosshair' : '';
  },
  onStroke: null,
  // lines drawn on the car, the notes' drawings ([{ points: [[x, y, z]] metres, colour, dim }]): the
  // list replaces what was drawn, and the line just drawn with the pen
  drawings(list) {
    penLine([], penGroup);
    penLine(list, drawnGroup);
  },
  project(points) {  // [[x, y, z]] -> [{ x, y, shown }] in this page's pixels, now
    return points.map((p) => {
      trackV.set(...p).project(camera);
      return { x: (trackV.x + 1) / 2 * innerWidth, y: (1 - trackV.y) / 2 * innerHeight, shown: trackV.z < 1 };
    });
  },
  // Where the camera is, as a view show() and go() take back, with the mood and the framing
  // (the view offset as shares of the page, and the zoom) that put the car where the user saw it.
  camera() {
    const rel = camera.position.clone().sub(controls.target), r = (v) => Math.round(v * 1e4) / 1e4;
    const v = camera.view && camera.view.enabled ? camera.view : null;
    return { dir: rel.clone().normalize().toArray().map(r), dist: r(rel.length()), target: controls.target.toArray().map(r),
      fov: r(camera.fov), mood, framing: v ? { x: r(v.offsetX / v.fullWidth), y: r(v.offsetY / v.fullHeight), zoom: r(camera.zoom) } : null };
  },
  go(view) {  // glide there; the game's cameras frame the car as the game does
    pickCam(view);
    setView(view, true);
  },
  mood(m) { setMood(m); },  // day or night, the camera left where it is
  views() {  // the game's cameras, as the viewer's own buttons name them
    return viewButtons.filter((b) => 'cam' in b.dataset).map((b) => ({ view: b.dataset.view, label: b.textContent.trim(), title: b.title }));
  },
  // The Lab's lines room (viewer/lab-lines.js): the user's pins for the car's lines, and the curves
  // through them drawn on the body.
  // snap: points ([[x, y, z]] metres) put back on the body along their normals (either way, the
  // nearer hit within `reach` metres, 5 cm unless said; a point with no body that near stays put).
  // Only the parts shown count.
  snap(points, normals, reach = 0.05) {
    const meshes = Object.values(parts).filter((m) => m.visible);
    const p = new THREE.Vector3(), n = new THREE.Vector3(), from = new THREE.Vector3(), dir = new THREE.Vector3();
    return points.map((q, i) => {
      p.set(...q);
      n.set(...((normals && normals[i]) || [0, 1, 0])).normalize();
      let best = null;
      for (const sgn of [1, -1]) {
        from.copy(p).addScaledVector(n, reach * sgn);
        dir.copy(n).multiplyScalar(-sgn);
        snapRay.set(from, dir);
        snapRay.far = 2 * reach;
        const hit = snapRay.intersectObjects(meshes, false).find((h) => partsState.data[partOfHit(h) * 4] > 0);
        if (hit && (!best || Math.abs(hit.distance - reach) < Math.abs(best.distance - reach))) best = hit;
      }
      return best ? best.point.toArray() : q;
    });
  },
  // curves: [{ key, points: [[x, y, z]] metres, colour, radius (metres), dim }], each drawn on the
  // body as a thin tube through its points; the list replaces what was drawn (an empty one clears).
  curves(list) {
    for (const c of curveGroup.children) { c.geometry.dispose(); c.material.dispose(); }
    curveGroup.clear();
    for (const c of list) {
      if (!c.points || c.points.length < 2) continue;
      const path = new THREE.CatmullRomCurve3(c.points.map((p) => new THREE.Vector3(...p)), false, 'centripetal');
      const geo = new THREE.TubeGeometry(path, Math.max(2, c.points.length), c.radius || 0.003, 6, false);
      const mat = new THREE.MeshBasicMaterial({ color: c.colour || '#e8ff47', transparent: !!c.dim, opacity: c.dim ? 0.5 : 1 });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.name = c.key || '';
      curveGroup.add(mesh);
    }
  },
  // The stock car, for a Lab with no skin to show (it builds the car only when it dresses it).
  async stock() {
    const slots = await (await fetch('data/stock/stock.json')).json();
    await window.viewer.dress(Object.fromEntries(slots.filter((s) => s !== 'Skin_Coat').map((s) => [s, `stock/${s}.png`])));
  },
  // The Lab's stand: dress the car in one step's textures ({slot: url}, as skin.json's).
  async dress(urls) {
    const ticket = ++loading;  // a later dress or skin wins, whichever finishes first
    const tex = await loadTextures(urls);
    if (ticket !== loading) return;
    dressCar(geometries, tex);
    freeTexturesExcept(urls);
    await frames(2);
  },
  // A picture of what's on screen (a JPEG blob URL); crop: 'inset', only the box the car is framed in.
  picture(opts = {}) {
    renderer.render(scene, camera);  // copied below, before the next frame draws
    let src = canvas;
    if (opts.crop === 'inset' && embedBox) {
      const k = canvas.width / canvas.clientWidth, b = embedBox;
      const w = Math.round((canvas.clientWidth - b.left - b.right) * k), h = Math.round((canvas.clientHeight - b.top - b.bottom) * k);
      src = Object.assign(document.createElement('canvas'), { width: w, height: h });
      src.getContext('2d').drawImage(canvas, b.left * k, b.top * k, w, h, 0, 0, w, h);
    }
    return new Promise((resolve) => src.toBlob((b) => resolve(URL.createObjectURL(b)), 'image/jpeg', 0.88));
  },
  gpu() {
    const gl = renderer.getContext();
    const ext = gl.getExtension('WEBGL_debug_renderer_info');
    return ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
  },
};
if (embed) {  // whatever the Lab asks for is drawn, when it's asked and when it's done
  const reads = new Set(['project', 'camera', 'views', 'gpu', 'snap']);
  for (const [k, f] of Object.entries(window.viewer)) {
    if (typeof f !== 'function' || reads.has(k)) continue;
    window.viewer[k] = (...args) => {
      rouse();
      const out = f.apply(window.viewer, args);
      if (out && typeof out.then === 'function') out.then(() => rouse(), () => rouse());
      return out;
    };
  }
}

// The Lab's tags: { key, at, normal, behind }, projected at the end of each frame. Whether the car
// hides a point is a ray from the camera against the car (about 99k triangles, no index), so it waits
// for the camera to settle (10 still frames) and casts at most 4 a frame; a move forgets them.
let tracked = [], onTrack = null, trackSig = '', stillFor = 0;
const trackV = new THREE.Vector3(), trackTo = new THREE.Vector3(), trackRay = new THREE.Raycaster();
const trackCam = new THREE.Matrix4(), trackProj = new THREE.Matrix4();
function trackAnchors() {
  if (!trackCam.equals(camera.matrixWorld) || !trackProj.equals(camera.projectionMatrix)) {
    trackCam.copy(camera.matrixWorld);
    trackProj.copy(camera.projectionMatrix);
    stillFor = 0;
    for (const a of tracked) a.behind = undefined;
  } else stillFor++;
  let rays = stillFor >= 10 ? 4 : 0;
  const meshes = rays ? Object.values(parts).filter((m) => m.visible) : null;
  const out = tracked.map((a) => {
    trackV.copy(a.at).project(camera);
    const shown = trackV.z < 1 && Math.abs(trackV.x) <= 1.05 && Math.abs(trackV.y) <= 1.05;
    trackTo.subVectors(a.at, camera.position);
    const facing = !a.normal || trackTo.dot(a.normal) <= 0;
    if (a.behind === undefined && shown && rays > 0) {
      rays--;
      const d = trackTo.length();
      trackRay.set(camera.position, trackTo.normalize());
      trackRay.far = d - 0.03;
      a.behind = trackRay.intersectObjects(meshes, false).some((h) => partsState.data[partOfHit(h) * 4] > 0);
    }
    return { key: a.key, x: Math.round((trackV.x + 1) / 2 * innerWidth * 10) / 10, y: Math.round((1 - trackV.y) / 2 * innerHeight * 10) / 10,
      shown, away: !facing || !!a.behind };
  });
  const sig = JSON.stringify(out);
  if (sig !== trackSig) {
    trackSig = sig;
    onTrack(out);
  }
}
// The Lab's go() and show(): the game's cameras (the viewer's Cam buttons) frame the car as the game
// does, any other view by its own outline.
function pickCam(view) {
  camPicked = typeof view === 'string' && viewButtons.some((b) => b.dataset.view === view && 'cam' in b.dataset) ? view : null;
  controls.minDistance = camPicked ? DRIVING_MIN : 1;
}

function fail(err) {
  console.error(err);
  if (window.viewer.ready) return;  // the car is up: a later error isn't a skin that failed to show
  // a file that didn't load rejects with its element's error event: name the file
  const said = err instanceof Event ? `couldn't load ${err.target?.src || err.target?.href || 'a file'}` : err && err.message || err;
  window.viewer.error = err instanceof Event ? said : String(err && err.stack || err);
  statusBox.textContent = `Couldn't show the skin: ${said}`;
}
window.addEventListener('error', (e) => fail(e.error || e.message));
window.addEventListener('unhandledrejection', (e) => fail(e.reason));

async function start() {
  if (!skinName && !embed) {  // none named: the one this browser showed last, else the newest painted
    try { skinName = localStorage.getItem('tsc-viewer-skin') || ''; } catch { /* no storage */ }
    if (!skinName) {
      const list = await fetch('data/gallery.json').then((r) => (r.ok ? r.json() : [])).catch(() => []);
      skinName = (list.find((s) => s.viewable) || {}).name || '';
    }
  }
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
  createStudio({ scene, renderer, centre: CENTRE, light: TUNE.room, parts: { table: partTable(), changes: () => partsState.hides } });
  await setupPlate(geoms.Skin);
  setupRearLights();
  setupWing();
  setupAirbrakes(geoms);
  setupSpin();
  showAirbrakes(drive.airbrake);
  // The Lab (embed, no skin) dresses the car itself, and its first dress builds it: no stock car
  // loaded first and thrown away (a second or more of the Lab's load, 2026-09-28).
  if (skinName && (!embed || params.has('skin'))) await loadSkin(skinName);
  else if (!embed) await window.viewer.stock();  // no skin painted yet: the stock car
  setMood('day');
  if (!snap && !embed) {  // on unless this browser turned it off last time
    let on = true;
    try { on = localStorage.getItem('tsc-viewer-number') !== '0'; } catch {}
    setPlate(on);
  }
  renderer.setAnimationLoop((now) => {
    const gliding = !!glide;
    stepGlide();
    if (!snap && !embed && stepDrive(now)) rouse(1);
    controls.update();
    let draw = true;
    if (!snap) {
      camera.updateMatrixWorld();
      const moved = !drawnCam.equals(camera.matrixWorld) || !drawnProj.equals(camera.projectionMatrix);
      draw = moved || gliding || wake > 0;
      if (draw) {
        drawnCam.copy(camera.matrixWorld);
        drawnProj.copy(camera.projectionMatrix);
        wake = Math.max(0, wake - 1);
      }
    }
    if (draw) renderer.render(scene, camera);
    if (onTrack && tracked.length) trackAnchors();  // counts the still frames, even undrawn
  });
  await frames(2);
  statusBox.textContent = '';
  window.viewer.ready = true;
  if (!snap) for (const id of Object.keys(LOOKS)) loadSky(id).catch((err) => console.error(err));
  if (!snap && !embed) buildSkinList().catch((err) => console.error(err));
}

start().catch(fail);
