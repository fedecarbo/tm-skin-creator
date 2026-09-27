// What the car stands on (the user, 2026-09-27: "i kind of feel we need a floor, it could still be
// studio like", "Keyshot has always been a nice default background and surface that i've liked",
// then, of six floors rendered for them: "is there one that actually you can't tell the spheric to
// the background", "Could you apply all. and I pick which one I like from the actual viewer?", and
// "was thinking like a matte floor with a bit of texture?", and last "Matte, tiny bit grainy texture
// in the grid one, and the grid make it tiny bit smaller"). The viewer's Floor menu picks a surface
// and a shade of grey; the light on the car is the same under every one.
//   gridgrain  the user's pick: the rubber's fine grain, fainter, under a line every 75 cm
//   today      the grey cove as before: floor and walls lit as they face, so the bend shows
//   keyshot    KeyShot's ground: no edge anywhere, a soft shadow and a faint reflection
//   concrete, asphalt, rubber, speckle
//              matte floors with a bit of texture (SURFACES), fading into the backdrop
//   turntable  a round platform, as at a car's reveal
//   grid       a faint line every metre, fading out
// Every floor but today's lights the whole cove as if it were flat floor, one even grey that runs
// up the walls with no line where the floor bends (KeyShot has no wall at all), and puts a soft
// shadow under the car in place of today's dark patch. The shade: the viewer's dark grey, or
// KeyShot's light grey.

import * as THREE from 'three';
import { Reflector } from 'three/addons/objects/Reflector.js';
import { FullScreenQuad } from 'three/addons/postprocessing/Pass.js';
import { HorizontalBlurShader } from 'three/addons/shaders/HorizontalBlurShader.js';
import { VerticalBlurShader } from 'three/addons/shaders/VerticalBlurShader.js';

export const FLOORS = ['gridgrain', 'today', 'keyshot', 'concrete', 'asphalt', 'rubber', 'speckle', 'turntable', 'grid'];
export const SHADES = ['dark', 'light'];
const RADIUS = 14;  // the room's flat floor (viewer.js's addRoom: the cove curves up from here)
const LIGHT_GREY = 0.2;  // KeyShot's light grey (linear): about 190 on the screen by day
const TABLE = { r: 2.6, h: 0.08 };  // the turntable: 5.2 m across, 8 cm high

// The matte floors: ambientCG sets (CC0), downloaded by tool/view.py (FLOOR_SETS). mean: the colour
// picture's average (linear), so the floor averages the backdrop's grey and only its grain fades;
// grain: how much of the picture's contrast is kept (a power of each texel's ratio to the mean),
// "a bit of texture"; metres: one repeat; relief: the normal map's strength.
const SURFACES = {
  concrete: { asset: 'Concrete034', mean: [0.4821, 0.4821, 0.4821], grain: 1.3, metres: 3, relief: 0.12 },  // trowelled, soft blotches
  asphalt: { asset: 'Asphalt031', mean: [0.1991, 0.1991, 0.199], grain: 0.4, metres: 2, relief: 0.35 },  // fine and even, like a track
  rubber: { asset: 'Rubber004', mean: [0.0238, 0.0255, 0.0323], grain: 0.6, metres: 1, relief: 0.3 },  // a very fine soft grain
  speckle: { asset: 'Rubber001', mean: [0.0156, 0.018, 0.0193], grain: 0.36, metres: 1, relief: 0.2 },  // rubber with light flecks
};

// The studio's surfaces. flat: lit as flat floor wherever it is (the normal straight up), so the
// cove's bend and walls are the floor's own grey; matte: no shine at all (a satin floor catches the
// studio HDR's lamps as white blotches the grey room doesn't have); fade: from r0 to r1 metres from
// the car the alpha goes from `from` to `to`; grain: the colour picture as grey * (texel / mean)^grain.
function studio(material, { flat = false, matte = flat, fade = null, grain = null } = {}) {
  const uniforms = {
    fadeCentre: { value: new THREE.Vector2() },
    fadeRange: { value: new THREE.Vector2(...(fade ? [fade.r0, fade.r1] : [0, 1])) },
    fadeEnds: { value: new THREE.Vector2(fade?.from ?? 1, fade?.to ?? 0) },
    floorGrey: { value: grain ? grain.grey : 0 },
    grainMean: { value: new THREE.Vector3(...(grain ? grain.mean : [1, 1, 1])) },
    grainPower: { value: grain ? grain.power : 1 },
  };
  material.userData.studio = uniforms;
  material.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, uniforms);
    let frag = shader.fragmentShader.replace('#include <common>', `#include <common>
      varying vec2 vStudioXZ; uniform vec2 fadeCentre, fadeRange, fadeEnds; uniform float floorGrey, grainPower; uniform vec3 grainMean;`);
    if (grain) {
      frag = frag.replace('#include <map_fragment>', `#include <map_fragment>
        diffuseColor.rgb = floorGrey * pow( max( texture2D( map, vMapUv ).rgb / grainMean, 0.0 ), vec3( grainPower ) );`);
    }
    if (fade) {
      frag = frag.replace('#include <alphamap_fragment>', `#include <alphamap_fragment>
        diffuseColor.a *= mix( fadeEnds.x, fadeEnds.y, smoothstep( fadeRange.x, fadeRange.y, length( vStudioXZ - fadeCentre ) ) );`);
    }
    if (flat) {
      frag = frag.replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
        normal = normalize( ( viewMatrix * vec4( 0.0, 1.0, 0.0, 0.0 ) ).xyz );`);
    }
    if (matte) {
      frag = frag.replace('#include <lights_physical_fragment>', `#include <lights_physical_fragment>
        material.specularColor = vec3( 0.0 ); material.specularColorBlended = vec3( 0.0 ); material.specularF90 = 0.0;`);
    }
    shader.fragmentShader = frag;
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec2 vStudioXZ;')
      .replace('#include <project_vertex>', '#include <project_vertex>\nvStudioXZ = ( modelMatrix * vec4( transformed, 1.0 ) ).xz;');
  };
  material.customProgramCacheKey = () => `studio-${flat}-${matte}-${Boolean(fade)}-${Boolean(grain)}`;
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

// A floor's name as the menu and the address give it: "rubber", "rubber-light", "keyshot-dark".
export function parseFloor(text) {
  const [, name, shade] = /^(.*?)(?:-(dark|light))?$/.exec(text || '');
  return { name: FLOORS.includes(name) ? name : 'today', shade: shade || 'dark' };
}

// The floors, built the first time each is picked in each shade. room and contact: addRoom's cove
// and dark patch.
export function createFloors({ scene, renderer, room, contact, centre, roomGrey }) {
  const aniso = renderer.capabilities.getMaxAnisotropy();
  const z = centre.z;
  const today = room.material;
  const greyOf = (shade) => (shade === 'light' ? LIGHT_GREY : roomGrey);
  const coves = {};  // a grey -> the cove lit flat in it
  const coveIn = (grey) => {
    if (!coves[grey]) {
      coves[grey] = studio(new THREE.MeshStandardMaterial({ roughness: 1, metalness: 0, side: THREE.BackSide }), { flat: true });
      coves[grey].color.setScalar(grey);
    }
    return coves[grey];
  };
  const textures = {};
  const texture = (url, repeat, colour) => {
    if (!textures[url]) {
      const t = textures[url] = new THREE.TextureLoader().load(url);
      t.wrapS = t.wrapT = THREE.RepeatWrapping;
      t.repeat.set(repeat, repeat);
      t.anisotropy = aniso;
      t.colorSpace = colour ? THREE.SRGBColorSpace : THREE.NoColorSpace;
    }
    return textures[url];
  };
  const fadeFrom = (material) => { material.userData.studio.fadeCentre.value.set(centre.x, z); return material; };
  const isCar = (o) => Boolean(o.geometry.getAttribute('part'));
  let shadows = null;  // the car's ground shadow, the same on every floor but today's
  const built = {};

  const build = {
    keyshot: (grey) => {
      // A mirror under a see-through skin of the backdrop's grey: 22 % of it shows by the car, none
      // from 6 m out. Drawn at half the screen's size, which softens it as a real floor would.
      const size = renderer.getDrawingBufferSize(new THREE.Vector2());
      const mirror = new Reflector(new THREE.CircleGeometry(RADIUS, 160), {  // its normal is the mesh's +z: turn the mesh
        clipBias: 0.002, textureWidth: Math.round(size.x * 0.5), textureHeight: Math.round(size.y * 0.5), color: 0x7f7f7f,
      });
      mirror.rotation.x = -Math.PI / 2;
      mirror.position.set(0, -0.001, z);
      const skin = fadeFrom(studio(new THREE.MeshStandardMaterial({ roughness: 1, metalness: 0, transparent: true }),
        { flat: true, fade: { r0: 1.2, r1: 6, from: 0.78, to: 1 } }));
      skin.color.setScalar(grey);
      const top = new THREE.Mesh(disc(RADIUS, z), skin);
      top.receiveShadow = true;
      top.renderOrder = 1;
      return [mirror, top];
    },
    turntable: (grey) => {
      // Dark satin top, brushed-metal rim, no bottom (the car's underside stays in view from
      // below), on the backdrop's floor 8 cm down, grounded by its own soft shadow.
      const top = new THREE.MeshStandardMaterial({ color: new THREE.Color().setScalar(0.05), roughness: 0.45, metalness: 0 });
      const rim = new THREE.MeshStandardMaterial({ color: 0xb8bcc2, roughness: 0.32, metalness: 1 });
      const table = new THREE.Mesh(new THREE.CylinderGeometry(TABLE.r, TABLE.r, TABLE.h, 192, 1),
        [rim, top, new THREE.MeshBasicMaterial({ visible: false })]);
      table.position.set(centre.x, -TABLE.h / 2, z);
      table.castShadow = table.receiveShadow = true;
      table.userData.turntable = true;
      const under = groundShadow(scene, (o) => isCar(o) || o.userData.turntable,
        { y: -TABLE.h, z, size: 7, height: 0.3, blur: 3, opacity: grey > 0.1 ? 0.6 : 0.8, power: 1.2, order: 4 });
      return [table, under];
    },
    grid: (grey, metres = 1) => {
      // A faint line every `metres`, one under the car's middle, and nothing between them: the
      // backdrop shows through. Fading out between 5 and 12 m, before the lines crowd.
      const c = document.createElement('canvas');
      c.width = c.height = 512;
      const g = c.getContext('2d');
      g.fillStyle = '#ffffff';
      g.fillRect(0, 0, 512, 5);
      g.fillRect(0, 0, 5, 512);
      const map = new THREE.CanvasTexture(c);
      map.wrapS = map.wrapT = THREE.RepeatWrapping;
      map.repeat.set(RADIUS * 2 / metres, RADIUS * 2 / metres);
      map.offset.setScalar(-((RADIUS / metres) % 1));
      map.anisotropy = aniso;
      const material = fadeFrom(studio(new THREE.MeshStandardMaterial({ alphaMap: map, transparent: true, roughness: 1, metalness: 0,
        depthWrite: false }), { flat: true, fade: { r0: 5, r1: 12 } }));
      material.color.setScalar(grey > 0.1 ? grey * 0.55 : grey * 2.6);  // lines a little darker, or lighter, than the backdrop
      const floor = new THREE.Mesh(disc(RADIUS, z), material);
      floor.renderOrder = 1;
      floor.position.y = 0.001;
      return [floor];
    },
  };
  for (const [name, s] of Object.entries(SURFACES)) {
    // A matte floor averaging the backdrop's grey, its grain fading out between 4 and 13 m, so no
    // ring shows where it ends.
    build[name] = (grey, grain = s.grain) => {
      const base = `data/floor/${s.asset}/${s.asset}_2K-JPG`, n = RADIUS * 2 / s.metres;
      const material = fadeFrom(studio(new THREE.MeshStandardMaterial({
        map: texture(`${base}_Color.jpg`, n, true), normalMap: texture(`${base}_NormalGL.jpg`, n, false),
        normalScale: new THREE.Vector2(s.relief, s.relief), roughness: 1, metalness: 0, transparent: true,
      }), { matte: true, fade: { r0: 4, r1: 13 }, grain: { grey, mean: s.mean, power: grain } }));
      const floor = new THREE.Mesh(disc(RADIUS, z), material);
      floor.receiveShadow = true;
      floor.renderOrder = 1;
      return [floor];
    };
  }

  build.gridgrain = (grey) => [...build.rubber(grey, 0.45), ...build.grid(grey, 0.75)];

  let current = 'today';
  function set(text) {
    const { name, shade } = parseFloor(text);
    for (const objects of Object.values(built)) for (const o of objects) o.visible = false;
    current = name === 'today' ? 'today' : `${name}-${shade}`;
    if (name === 'today') {
      room.material = today;
      room.position.y = 0;
      contact.visible = true;
      if (shadows) for (const s of shadows) s.visible = false;
      return { name, shade };
    }
    const grey = greyOf(shade);
    if (!built[current]) {
      built[current] = build[name](grey);
      for (const o of built[current]) scene.add(o);
    }
    if (!shadows) {
      // two layers, as KeyShot's ground occlusion looks: a wide soft one from everything within
      // 90 cm of the floor, and a tight dark one where the tyres and the floor's plank come nearest
      shadows = [groundShadow(scene, isCar, { z, height: 0.9, blur: 3.5, opacity: 0.75, power: 1.4, order: 2 }),
        groundShadow(scene, isCar, { z, height: 0.22, blur: 1.1, opacity: 0.9, power: 1.2, order: 3 })];
    }
    for (const s of shadows) s.visible = true;
    for (const o of built[current]) o.visible = true;
    room.material = coveIn(grey);
    room.position.y = -(name === 'turntable' ? TABLE.h : 0) - 0.003;  // just under the new floor
    contact.visible = false;
    return { name, shade };
  }
  return { set, get: () => current };
}
