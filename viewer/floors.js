// What the car stands on (the user, 2026-09-27: "i kind of feel we need a floor, it could still be
// studio like", "Keyshot has always been a nice default background and surface that i've liked",
// then, of the six rendered for them: "is there one that actually you can't tell the spheric to the
// background", "Could you apply all. and I pick which one I like from the actual viewer?"). The
// viewer's Floor menu switches between them; the light on the car is the same under every one.
//   today         the grey cove as before: floor and walls lit as they face, so the curve shows
//   keyshot       KeyShot's ground, light grey: no edge anywhere, a soft shadow and a faint reflection
//   keyshot-dark  the same in the viewer's own dark grey
//   concrete      a pool of matte concrete fading into the room
//   turntable     a round platform, as at a car's reveal
//   grid          a faint line every metre, fading out
// Every floor but today's lights the whole cove as if it were flat floor, one even grey that runs
// up the walls with no line where the floor bends (KeyShot has no wall at all), and puts a soft
// shadow under the car in place of today's dark patch.

import * as THREE from 'three';
import { Reflector } from 'three/addons/objects/Reflector.js';
import { FullScreenQuad } from 'three/addons/postprocessing/Pass.js';
import { HorizontalBlurShader } from 'three/addons/shaders/HorizontalBlurShader.js';
import { VerticalBlurShader } from 'three/addons/shaders/VerticalBlurShader.js';

export const FLOORS = ['today', 'keyshot', 'keyshot-dark', 'concrete', 'turntable', 'grid'];
const RADIUS = 14;  // the room's flat floor (viewer.js's addRoom: the cove curves up from here)
const LIGHT_GREY = 0.2;  // KeyShot's light grey (linear): about 190 on the screen by day
const TABLE = { r: 2.6, h: 0.08 };  // the turntable: 5.2 m across, 8 cm high

// The studio's surfaces. flat: lit as flat floor wherever it is (the normal straight up, no shine),
// so the cove's curve and walls are the floor's own grey. fade: from r0 to r1 metres from the car
// the surface goes see-through (alpha to 0) or, with `solid`, see-through only where it starts.
function studio(material, { flat = false, fade = null } = {}) {
  const uniforms = {
    fadeCentre: { value: new THREE.Vector2() },
    fadeRange: { value: new THREE.Vector2(...(fade ? [fade.r0, fade.r1] : [0, 1])) },
    fadeFrom: { value: fade ? fade.from ?? 1 : 1 },  // the alpha by the car
  };
  material.userData.fade = uniforms;
  material.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, uniforms);
    if (fade) {
      shader.vertexShader = shader.vertexShader
        .replace('#include <common>', '#include <common>\nvarying vec2 vStudioXZ;')
        .replace('#include <project_vertex>', '#include <project_vertex>\nvStudioXZ = ( modelMatrix * vec4( transformed, 1.0 ) ).xz;');
      shader.fragmentShader = shader.fragmentShader
        .replace('#include <common>', '#include <common>\nvarying vec2 vStudioXZ; uniform vec2 fadeCentre, fadeRange; uniform float fadeFrom;')
        .replace('#include <alphamap_fragment>', `#include <alphamap_fragment>
          diffuseColor.a *= mix( fadeFrom, 0.0, smoothstep( fadeRange.x, fadeRange.y, length( vStudioXZ - fadeCentre ) ) );`);
    }
    if (flat) {
      shader.fragmentShader = shader.fragmentShader
        .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
          normal = normalize( ( viewMatrix * vec4( 0.0, 1.0, 0.0, 0.0 ) ).xyz );`)
        .replace('#include <lights_physical_fragment>', `#include <lights_physical_fragment>
          material.specularColor = vec3( 0.0 ); material.specularColorBlended = vec3( 0.0 ); material.specularF90 = 0.0;`);
    }
  };
  material.customProgramCacheKey = () => `studio-${flat}-${Boolean(fade)}`;
  return material;
}

// A fading overlay: its alpha by the car is fadeFrom, reaching 1 (opaque) at r1 instead of 0.
function overlay(material, r0, r1, from) {
  studio(material, { flat: true, fade: { r0, r1, from } });
  material.onBeforeCompile = ((inner) => (shader) => {
    inner(shader);
    shader.fragmentShader = shader.fragmentShader.replace('mix( fadeFrom, 0.0,', 'mix( fadeFrom, 1.0,');
  })(material.onBeforeCompile);
  material.customProgramCacheKey = () => 'studio-overlay';
  return material;
}

const disc = (r, z) => new THREE.CircleGeometry(r, 160).rotateX(-Math.PI / 2).translate(0, 0, z);

// The soft shadow right under something, where the studio's light can't reach (KeyShot's ground
// occlusion): seen from the floor up, its nearness as darkness, blurred. `pick` says which meshes
// cast it. Drawn every frame while shown, since the wings and air brakes move (the depth pass sees
// the car at rest).
function groundShadow(scene, pick, { y = 0, z = 0, size = 5.6, height = 0.9, blur = 3.2, opacity = 0.92, power = 1.6, res = 512, order = 2 } = {}) {
  const target = new THREE.WebGLRenderTarget(res, res), spare = new THREE.WebGLRenderTarget(res, res);
  target.texture.generateMipmaps = spare.texture.generateMipmaps = false;
  const plane = new THREE.PlaneGeometry(size, size).rotateX(-Math.PI / 2);
  const uv = plane.getAttribute('uv');
  for (let i = 0; i < uv.count; i++) uv.setY(i, 1 - uv.getY(i));  // the camera below sees +z as up
  const shadow = new THREE.Mesh(plane, new THREE.MeshBasicMaterial({ map: target.texture, transparent: true, opacity, depthWrite: false }));
  shadow.position.set(0, y + 0.002 + order * 0.0005, z);
  shadow.renderOrder = order;
  scene.add(shadow);
  const cam = new THREE.OrthographicCamera(-size / 2, size / 2, size / 2, -size / 2, 0, height);
  cam.rotation.x = Math.PI / 2;  // looking up from the floor
  cam.position.set(0, y, z);
  cam.layers.set(5 + order);
  cam.updateMatrixWorld();
  const depth = new THREE.MeshDepthMaterial();  // depth-tested: the surface nearest the floor wins
  depth.onBeforeCompile = (shader) => {
    shader.fragmentShader = shader.fragmentShader.replace('gl_FragColor = vec4( vec3( 1.0 - fragCoordZ ), opacity );',
      `gl_FragColor = vec4( vec3( 0.0 ), pow( 1.0 - fragCoordZ, ${power.toFixed(2)} ) );`);
  };
  depth.customProgramCacheKey = () => `ground-${power.toFixed(2)}`;
  const hBlur = new FullScreenQuad(new THREE.ShaderMaterial(HorizontalBlurShader));
  const vBlur = new FullScreenQuad(new THREE.ShaderMaterial(VerticalBlurShader));
  hBlur.material.depthTest = vBlur.material.depthTest = false;
  const blurOnce = (r, amount) => {
    hBlur.material.uniforms.tDiffuse.value = target.texture;
    hBlur.material.uniforms.h.value = amount / 256;
    r.setRenderTarget(spare);
    hBlur.render(r);
    vBlur.material.uniforms.tDiffuse.value = spare.texture;
    vBlur.material.uniforms.v.value = amount / 256;
    r.setRenderTarget(target);
    vBlur.render(r);
  };
  const colour = new THREE.Color();
  shadow.onBeforeRender = (r) => {
    let any = false;
    scene.traverse((o) => { if (o.isMesh && o.visible && pick(o)) { o.layers.enable(5 + order); any = true; } });
    if (!any) return;
    const before = r.getRenderTarget(), bg = scene.background, alpha = r.getClearAlpha(), auto = r.shadowMap.autoUpdate;
    r.getClearColor(colour);
    scene.background = null;
    scene.overrideMaterial = depth;
    r.shadowMap.autoUpdate = false;
    r.setClearColor(0x000000, 0);
    r.setRenderTarget(target);
    r.clear();
    r.render(scene, cam);
    scene.overrideMaterial = null;
    scene.background = bg;
    blurOnce(r, blur);
    blurOnce(r, blur * 0.4);
    r.shadowMap.autoUpdate = auto;
    r.setClearColor(colour, alpha);
    r.setRenderTarget(before);
  };
  return shadow;
}

function tiled(url, repeat, colour, aniso) {
  const t = new THREE.TextureLoader().load(url);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(repeat, repeat);
  t.anisotropy = aniso;
  t.colorSpace = colour ? THREE.SRGBColorSpace : THREE.NoColorSpace;
  return t;
}

// The floors, built the first time each is picked. room and contact: addRoom's cove and dark patch.
export function createFloors({ scene, renderer, room, contact, centre, roomGrey }) {
  const aniso = renderer.capabilities.getMaxAnisotropy();
  const z = centre.z;
  const today = room.material;
  const flatRoom = {};  // a grey -> the cove lit flat in it
  const coveIn = (grey) => {
    if (!flatRoom[grey]) {
      flatRoom[grey] = studio(new THREE.MeshStandardMaterial({ roughness: 1, metalness: 0, side: THREE.BackSide }), { flat: true });
      flatRoom[grey].color.setScalar(grey);
    }
    return flatRoom[grey];
  };
  const isCar = (o) => Boolean(o.geometry.getAttribute('part'));
  let shadows = null;  // the car's ground shadow, the same on every floor but today's
  const built = {};

  // KeyShot's ground in a grey
  const mirrorFloor = (grey) => {
    // A mirror under a see-through skin of the room's grey: 22 % of it shows by the car, none
    // from 6 m out. Drawn at half the screen's size, which softens it as a real floor would.
    const size = renderer.getDrawingBufferSize(new THREE.Vector2());
    const mirror = new Reflector(new THREE.CircleGeometry(RADIUS, 160), {  // its normal is the mesh's +z: turn the mesh
      clipBias: 0.002, textureWidth: Math.round(size.x * 0.5), textureHeight: Math.round(size.y * 0.5), color: 0x7f7f7f,
    });
    mirror.rotation.x = -Math.PI / 2;
    mirror.position.set(0, -0.001, z);
    const skin = overlay(new THREE.MeshStandardMaterial({ roughness: 1, metalness: 0, transparent: true }), 1.2, 6, 0.78);
    skin.color.setScalar(grey);
    skin.userData.fade.fadeCentre.value.set(centre.x, z);
    const top = new THREE.Mesh(disc(RADIUS, z), skin);
    top.receiveShadow = true;
    top.renderOrder = 1;
    return { objects: [mirror, top], grey };
  };

  const build = {
    keyshot: () => mirrorFloor(LIGHT_GREY),
    'keyshot-dark': () => mirrorFloor(roomGrey),
    concrete: () => {
      // Matte concrete (ambientCG Concrete034, CC0), three metres a repeat, on average the room's
      // own grey (its picture averages 0.48), fading out between 4 and 13 m from the car, so only
      // its grain fades and no ring shows where it ends.
      const base = 'data/floor/Concrete034/Concrete034_2K-JPG', n = RADIUS * 2 / 3;
      const material = studio(new THREE.MeshStandardMaterial({
        map: tiled(`${base}_Color.jpg`, n, true, aniso), roughnessMap: tiled(`${base}_Roughness.jpg`, n, false, aniso),
        normalMap: tiled(`${base}_NormalGL.jpg`, n, false, aniso), normalScale: new THREE.Vector2(0.12, 0.12),
        color: new THREE.Color().setScalar(roomGrey / 0.48), roughness: 1.8, metalness: 0, transparent: true,
      }), { fade: { r0: 4, r1: 13 } });
      material.userData.fade.fadeCentre.value.set(centre.x, z);
      const floor = new THREE.Mesh(disc(RADIUS, z), material);
      floor.receiveShadow = true;
      floor.renderOrder = 1;
      return { objects: [floor], grey: roomGrey };
    },
    turntable: () => {
      // Dark satin top, brushed-metal rim, no bottom (the car's underside stays in view from
      // below), on the room's floor 8 cm down, grounded by its own soft shadow.
      const top = new THREE.MeshStandardMaterial({ color: new THREE.Color().setScalar(0.05), roughness: 0.45, metalness: 0 });
      const rim = new THREE.MeshStandardMaterial({ color: 0xb8bcc2, roughness: 0.32, metalness: 1 });
      const table = new THREE.Mesh(new THREE.CylinderGeometry(TABLE.r, TABLE.r, TABLE.h, 192, 1),
        [rim, top, new THREE.MeshBasicMaterial({ visible: false })]);
      table.position.set(centre.x, -TABLE.h / 2, z);
      table.castShadow = table.receiveShadow = true;
      table.userData.turntable = true;
      const under = groundShadow(scene, (o) => isCar(o) || o.userData.turntable,
        { y: -TABLE.h, z, size: 7, height: 0.3, blur: 3, opacity: 0.8, power: 1.2, order: 4 });
      return { objects: [table, under], grey: roomGrey, drop: TABLE.h };
    },
    grid: () => {
      // A faint line every metre, and nothing between them: the room shows through. Fading out
      // between 5 and 12 m, before the lines crowd.
      const c = document.createElement('canvas');
      c.width = c.height = 512;
      const g = c.getContext('2d');
      g.fillStyle = '#ffffff';
      g.fillRect(0, 0, 512, 5);
      g.fillRect(0, 0, 5, 512);
      const map = new THREE.CanvasTexture(c);
      map.wrapS = map.wrapT = THREE.RepeatWrapping;
      map.repeat.set(RADIUS * 2, RADIUS * 2);
      map.anisotropy = aniso;
      const material = studio(new THREE.MeshStandardMaterial({ color: new THREE.Color().setScalar(0.09), alphaMap: map, transparent: true,
        roughness: 1, metalness: 0, depthWrite: false }), { flat: true, fade: { r0: 5, r1: 12 } });
      material.userData.fade.fadeCentre.value.set(centre.x, z);
      const floor = new THREE.Mesh(disc(RADIUS, z), material);
      floor.renderOrder = 1;
      floor.position.y = 0.001;
      return { objects: [floor], grey: roomGrey };
    },
  };
  let current = 'today';
  function set(name) {
    if (!FLOORS.includes(name)) name = 'today';
    for (const f of Object.values(built)) for (const o of f.objects) o.visible = false;
    current = name;
    if (name === 'today') {
      room.material = today;
      room.position.y = 0;
      contact.visible = true;
      if (shadows) for (const s of shadows) s.visible = false;
      return name;
    }
    if (!built[name]) {
      built[name] = build[name]();
      for (const o of built[name].objects) scene.add(o);
    }
    if (!shadows) {
      // two layers, as KeyShot's ground occlusion looks: a wide soft one from everything within
      // 90 cm of the floor, and a tight dark one where the tyres and the floor's plank come nearest
      shadows = [groundShadow(scene, isCar, { z, height: 0.9, blur: 3.5, opacity: 0.75, power: 1.4, order: 2 }),
        groundShadow(scene, isCar, { z, height: 0.22, blur: 1.1, opacity: 0.9, power: 1.2, order: 3 })];
    }
    for (const s of shadows) s.visible = true;
    for (const o of built[name].objects) o.visible = true;
    room.material = coveIn(built[name].grey);
    room.position.y = -(built[name].drop || 0) - 0.003;  // just under the new floor
    contact.visible = false;
    return name;
  }
  return { set, get: () => current };
}
