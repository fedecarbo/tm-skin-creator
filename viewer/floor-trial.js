// Trial floors for the studio (the user, 2026-09-27: "i kind of feel we need a floor, it could still
// be studio like", then "Keyshot has always been a nice default background and surface that i've
// liked"). ?floor=keyshot | keyshot-dark | concrete | turntable | grid in the viewer's address puts
// one under the car; the light stays the day look matched to the game. For the pictures the user
// picks from: the chosen one moves into viewer.js's addRoom and this file goes.

import * as THREE from 'three';
import { Reflector } from 'three/addons/objects/Reflector.js';
import { FullScreenQuad } from 'three/addons/postprocessing/Pass.js';
import { HorizontalBlurShader } from 'three/addons/shaders/HorizontalBlurShader.js';
import { VerticalBlurShader } from 'three/addons/shaders/VerticalBlurShader.js';

const dbg = new URLSearchParams(location.search).get('dbg');
const RADIUS = 14;  // the room's flat floor (addRoom's cove starts curving up here)
let discZ = 0;  // the room's middle, under the car
const disc = (r) => new THREE.CircleGeometry(r, 160).rotateX(-Math.PI / 2).translate(0, 0, discZ);

// A floor's colour, finish and see-through fading into the cove's between r0 and r1 metres from
// the car, so it melts into the room without a seam: the colour to `edge` (linear grey), the finish
// to the cove's matte, and the floor to opaque (a reflection under it shows only near the car).
function fadeFloor(material, centre, r0, r1, edge) {
  material.onBeforeCompile = (shader) => {
    shader.uniforms.fadeEdge = { value: new THREE.Color().setScalar(edge) };
    shader.uniforms.fadeCentre = { value: new THREE.Vector2(centre.x, centre.z) };
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec2 vFloorXZ;')
      .replace('#include <project_vertex>', '#include <project_vertex>\nvFloorXZ = ( modelMatrix * vec4( transformed, 1.0 ) ).xz;');
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', `#include <common>\nvarying vec2 vFloorXZ; uniform vec3 fadeEdge; uniform vec2 fadeCentre;`)
      .replace('#include <map_fragment>', `#include <map_fragment>
        float floorFade = smoothstep( ${r0.toFixed(2)}, ${r1.toFixed(2)}, length( vFloorXZ - fadeCentre ) );
        diffuseColor.rgb = mix( diffuseColor.rgb, fadeEdge, floorFade );
        diffuseColor.a = mix( diffuseColor.a, 1.0, floorFade );`)
      .replace('#include <roughnessmap_fragment>', `#include <roughnessmap_fragment>
        roughnessFactor = mix( roughnessFactor, 0.95, floorFade );`)
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
        normal = normalize( mix( normal, nonPerturbedNormal, floorFade ) );`);
  };
  return material;
}

// KeyShot's ground: the floor is the room's own matte grey, so it has no edge, and the car stands
// on its soft reflection: a mirror under the floor, which lets `strength` of it through by the car
// and none from `far` metres out. The mirror is drawn at a fraction of the screen's size, which
// softens it a little, as a real floor's would be.
function mirrorFloor(scene, renderer, centre, grey, strength, far) {
  const size = new THREE.Vector2();
  renderer.getDrawingBufferSize(size);
  // Reflector takes its plane's normal as the mesh's own +z: a flat disc, turned to face up
  const mirror = new Reflector(new THREE.CircleGeometry(RADIUS, 160), {
    clipBias: 0.002, textureWidth: Math.round(size.x * 0.5), textureHeight: Math.round(size.y * 0.5), color: 0x7f7f7f,
  });
  mirror.rotation.x = -Math.PI / 2;
  mirror.position.set(0, -0.001, centre.z);
  scene.add(mirror);
  const top = new THREE.Mesh(disc(RADIUS), fadeFloor(new THREE.MeshStandardMaterial({
    color: new THREE.Color().setScalar(grey), roughness: 0.95, metalness: 0, transparent: true, opacity: 1 - strength,
  }), centre, 1.2, far, grey));
  top.receiveShadow = true;
  top.renderOrder = 1;
  scene.add(top);
}

// The soft shadow right under the car, where the studio's light can't reach (KeyShot's ground
// occlusion): the car seen from below, its nearness to the floor as darkness, blurred. Drawn
// again each frame, since the wings and air brakes move (the depth pass sees the car at rest).
function groundShadow(scene, renderer, centre, { size = 5.6, height = 0.9, blur = 3.2, opacity = 0.92, power = 1.6, res = 512, order = 2 } = {}) {
  const target = new THREE.WebGLRenderTarget(res, res);
  const spare = new THREE.WebGLRenderTarget(res, res);
  target.texture.generateMipmaps = spare.texture.generateMipmaps = false;
  const plane = new THREE.PlaneGeometry(size, size).rotateX(-Math.PI / 2);
  const uv = plane.getAttribute('uv');
  for (let i = 0; i < uv.count; i++) uv.setY(i, 1 - uv.getY(i));  // the camera below sees +z as up
  const shadow = new THREE.Mesh(plane, new THREE.MeshBasicMaterial({ map: target.texture, transparent: true, opacity, depthWrite: false }));
  shadow.position.set(0, 0.002 + order * 0.0005, centre.z);
  shadow.renderOrder = order;
  scene.add(shadow);
  const cam = new THREE.OrthographicCamera(-size / 2, size / 2, size / 2, -size / 2, 0, height);
  cam.rotation.x = Math.PI / 2;  // looking up from the floor
  cam.position.set(0, 0, centre.z);
  cam.layers.set(5);
  cam.updateMatrixWorld();
  const depth = new THREE.MeshDepthMaterial();  // depth-tested: the surface nearest the floor wins
  depth.onBeforeCompile = (shader) => {
    shader.fragmentShader = shader.fragmentShader.replace('gl_FragColor = vec4( vec3( 1.0 - fragCoordZ ), opacity );',
      `gl_FragColor = vec4( vec3( 0.0 ), pow( 1.0 - fragCoordZ, ${power.toFixed(2)} ) );`);
  };
  const hBlur = new FullScreenQuad(new THREE.ShaderMaterial(HorizontalBlurShader));
  const vBlur = new FullScreenQuad(new THREE.ShaderMaterial(VerticalBlurShader));
  hBlur.material.depthTest = vBlur.material.depthTest = false;
  const blurOnce = (amount) => {
    hBlur.material.uniforms.tDiffuse.value = target.texture;
    hBlur.material.uniforms.h.value = amount / 256;
    renderer.setRenderTarget(spare);
    hBlur.render(renderer);
    vBlur.material.uniforms.tDiffuse.value = spare.texture;
    vBlur.material.uniforms.v.value = amount / 256;
    renderer.setRenderTarget(target);
    vBlur.render(renderer);
  };
  shadow.onBeforeRender = (r) => {
    let any = false;
    scene.traverse((o) => {
      if (o.isMesh && o.geometry.getAttribute('part') && o.visible) {
        o.layers.enable(5);
        if (dbg === 'shadow') o.layers.disable(0);  // the shadow alone, to check it
        any = true;
      }
    });
    if (!any) return;
    const before = r.getRenderTarget(), bg = scene.background, alpha = r.getClearAlpha(), auto = r.shadowMap.autoUpdate;
    const colour = r.getClearColor(new THREE.Color());
    scene.background = null;
    scene.overrideMaterial = depth;
    r.shadowMap.autoUpdate = false;
    r.setClearColor(0x000000, 0);
    r.setRenderTarget(target);
    r.clear();
    r.render(scene, cam);
    scene.overrideMaterial = null;
    scene.background = bg;
    blurOnce(blur);
    blurOnce(blur * 0.4);
    r.shadowMap.autoUpdate = auto;
    r.setClearColor(colour, alpha);
    r.setRenderTarget(before);
  };
}

function tiled(url, repeat, colour, aniso) {
  const t = new THREE.TextureLoader().load(url);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(repeat, repeat);
  t.anisotropy = aniso;
  t.colorSpace = colour ? THREE.SRGBColorSpace : THREE.NoColorSpace;
  return t;
}

export async function trialFloor(kind, { scene, renderer, room, contact, centre, roomGrey }) {
  const aniso = renderer.capabilities.getMaxAnisotropy();
  room.position.y = -0.003;  // under the new floor
  discZ = centre.z;
  contact.visible = false;  // the ground shadows take its place
  // two layers, as KeyShot's ground occlusion looks: a wide soft one from everything within 90 cm
  // of the floor, and a tight dark one where the tyres and the floor's plank come nearest
  groundShadow(scene, renderer, centre, { height: 0.9, blur: 3.5, opacity: 0.75, power: 1.4, order: 2 });
  groundShadow(scene, renderer, centre, { height: 0.22, blur: 1.1, opacity: 0.9, power: 1.2, order: 3 });

  if (kind === 'keyshot' || kind === 'keyshot-dark') {
    // KeyShot's default look: one seamless grey from the floor to the horizon, the car grounded by
    // its shadow and a faint reflection. Light grey as KeyShot's, or the viewer's own dark grey.
    const grey = kind === 'keyshot' ? 0.2 : roomGrey;
    room.material.color.setScalar(grey);
    mirrorFloor(scene, renderer, centre, grey, 0.22, 6);
  }

  if (kind === 'concrete') {
    // Concrete (ambientCG Concrete034, CC0), three metres a repeat, matte, greyed down to sit a
    // little lighter than the dark room, fading into the cove's grey far from the car.
    const base = 'data/floor/Concrete034/Concrete034_2K-JPG';
    const material = fadeFloor(new THREE.MeshStandardMaterial({
      map: tiled(`${base}_Color.jpg`, RADIUS * 2 / 3, true, aniso),
      roughnessMap: tiled(`${base}_Roughness.jpg`, RADIUS * 2 / 3, false, aniso),
      normalMap: tiled(`${base}_NormalGL.jpg`, RADIUS * 2 / 3, false, aniso),
      normalScale: new THREE.Vector2(0.12, 0.12),
      color: new THREE.Color().setScalar(0.1), roughness: 1.8, metalness: 0,
    }), centre, 7, RADIUS, roomGrey);
    const floor = new THREE.Mesh(disc(RADIUS), material);
    floor.receiveShadow = true;
    scene.add(floor);
  }

  if (kind === 'turntable') {
    // A turntable the car stands on, as at a car's reveal: 5.2 m across, 8 cm high, dark satin top,
    // a brushed-metal rim; the room's floor darker around it.
    const r = 2.6, h = 0.08;
    const top = new THREE.MeshStandardMaterial({ color: new THREE.Color().setScalar(0.05), roughness: 0.45, metalness: 0 });
    const rim = new THREE.MeshStandardMaterial({ color: 0xb8bcc2, roughness: 0.32, metalness: 1 });
    const table = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, 192, 1), [rim, top, top]);
    table.position.set(centre.x, -h / 2, centre.z);
    table.receiveShadow = true;
    scene.add(table);
    room.position.y = -h;
    room.material.color.setScalar(roomGrey * 0.7);
  }

  if (kind === 'grid') {
    // A design studio's floor: the room's grey with a faint line every metre (the car's scale at a
    // glance), fading out with distance before the lines crowd.
    const c = document.createElement('canvas');
    c.width = c.height = 512;
    const g = c.getContext('2d');
    g.fillStyle = '#343434';  // the room's own grey (0.035 linear): only the lines show
    g.fillRect(0, 0, 512, 512);
    g.fillStyle = '#5a5a5a';
    g.fillRect(0, 0, 512, 5);
    g.fillRect(0, 0, 5, 512);
    const map = new THREE.CanvasTexture(c);
    map.colorSpace = THREE.SRGBColorSpace;
    map.wrapS = map.wrapT = THREE.RepeatWrapping;
    map.repeat.set(RADIUS * 2, RADIUS * 2);
    map.anisotropy = aniso;
    const material = fadeFloor(new THREE.MeshStandardMaterial({ map, roughness: 0.9, metalness: 0 }), centre, 6, 12, roomGrey);
    const floor = new THREE.Mesh(disc(RADIUS), material);
    floor.receiveShadow = true;
    scene.add(floor);
  }
}
