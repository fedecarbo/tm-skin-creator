// The studio the car stands in (the user, 2026-09-27, from floors tried in the viewer: "Matte, tiny bit
// grainy texture in the grid one, and the grid make it tiny bit smaller", "a bit whiter but with some
// kind of vignette so that the buttons dont dissapear", "the grid smaller in scale. but a bit farther
// covering", then "we can have the grainy grid, and have the dark and light options", "Maybe we keep
// one floor, but meet in the middle?" and last "Or maybe just meet the color that the screenshots
// have"). One room, the colour of the game's track in the user's screenshots: FLOOR, lit by the mood,
// reads the track's (205, 200, 204) by day and its (124, 123, 128) at sunrise from Cam 2; each mood's
// `studio` in viewer.js's LOOKS corrects the rest (setStudioTint).
//   The room: a seamless cove, the floor curving up into the walls and a ceiling (floor radius 14 m,
//     curve 6 m, 14 m high), lit as if it were all flat floor (the normal straight up, no shine), so
//     it's one even grey with no line where the floor bends, in every mood.
//   The floor: a fine matte grain (ambientCG Rubber004, CC0, downloaded by tool/view.py: FLOOR_SETS)
//     averaging the room's grey, under a faint line every 50 cm, one under the car's middle; both fade
//     out between 8 and 13.8 m.
//   The ground shadow: a soft shadow right under the car (KeyShot's ground occlusion), drawn again
//     only when the car's parts come or go.
//   The vignette: the studio, never the car, darkening gently towards the picture's corners, around
//     the car's middle on the screen.
// The other floors tried (KeyShot's reflection, concrete, asphalt, rubber, a turntable, a plain grid)
// are in the git history, 2026-09-27.

import * as THREE from 'three';
import { FullScreenQuad } from 'three/addons/postprocessing/Pass.js';
import { HorizontalBlurShader } from 'three/addons/shaders/HorizontalBlurShader.js';
import { VerticalBlurShader } from 'three/addons/shaders/VerticalBlurShader.js';

const RADIUS = 14;  // the room's flat floor: the cove curves up from here
// The studio's colour (linear): a light grey with the track's faint warm-pink cast.
const FLOOR = [0.353, 0.329, 0.349];
const GRAIN = { asset: 'Rubber004', mean: [0.0238, 0.0255, 0.0323], power: 0.45, metres: 1, relief: 0.3 };
const GRID = 0.5;  // metres between the lines
const FADE = { r0: 8, r1: 13.8 };
// The vignette, shared by every studio surface: the car's middle on the screen and half the
// picture's height (pixels), set as each frame is drawn. Gentle (the user: "the vignette is very
// strong"): the studio keeps its grey within about half the picture's height of the car and is down to
// 0.6 of it by the corners. The buttons over the studio read by their own dark glass (viewer.js,
// body.lightStudio).
// studioTint: the mood's correction (setStudioTint), on everything the studio draws.
const VIGNETTE = { vignetteAt: { value: new THREE.Vector3(0, 0, 1) }, vignetteStrength: { value: 1 },
  studioTint: { value: new THREE.Vector3(1, 1, 1) } };
export function setStudioTint(rgb) { VIGNETTE.studioTint.value.set(...rgb); }

// A studio surface. flat: lit as flat floor wherever it is (the normal straight up); matte: no shine
// at all (a satin floor catches the sky's bright spots as blotches the grey room doesn't have); fade:
// the alpha going from 1 to 0 between r0 and r1 metres from the car; grain: the colour picture as
// colour * (texel / mean)^power, "a tiny bit grainy".
function studio(material, { flat = false, matte = flat, fade = null, grain = null } = {}) {
  const uniforms = {
    fadeCentre: { value: new THREE.Vector2() },
    fadeRange: { value: new THREE.Vector2(...(fade ? [fade.r0, fade.r1] : [0, 1])) },
    floorGrey: { value: new THREE.Vector3(...(grain ? grain.colour : [0, 0, 0])) },
    grainMean: { value: new THREE.Vector3(...(grain ? grain.mean : [1, 1, 1])) },
    grainPower: { value: grain ? grain.power : 1 },
  };
  material.userData.studio = uniforms;
  material.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, uniforms, VIGNETTE);
    let frag = shader.fragmentShader.replace('#include <common>', `#include <common>
      varying vec2 vStudioXZ; uniform vec2 fadeCentre, fadeRange; uniform vec3 floorGrey; uniform float grainPower; uniform vec3 grainMean;
      uniform vec3 vignetteAt, studioTint; uniform float vignetteStrength;`)
      .replace('#include <opaque_fragment>', `#include <opaque_fragment>
        float vignette = smoothstep( 0.5, 1.4, length( ( gl_FragCoord.xy - vignetteAt.xy ) / vignetteAt.z * vec2( 0.6, 1.0 ) ) );
        gl_FragColor.rgb *= mix( 1.0, 0.6, vignette * vignetteStrength ) * studioTint;`);
    if (grain) {
      frag = frag.replace('#include <map_fragment>', `#include <map_fragment>
        diffuseColor.rgb = floorGrey * pow( max( texture2D( map, vMapUv ).rgb / grainMean, 0.0 ), vec3( grainPower ) );`);
    }
    if (fade) {
      frag = frag.replace('#include <alphamap_fragment>', `#include <alphamap_fragment>
        diffuseColor.a *= 1.0 - smoothstep( fadeRange.x, fadeRange.y, length( vStudioXZ - fadeCentre ) );`);
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

// The soft shadow right under the car, where the studio's light can't reach: the car seen from the
// floor up, its nearness as darkness, blurred. The depth pass sees the car at rest (its own material
// leaves out the wings' and wheels' movement), so the picture changes only when a mesh is shown or
// hidden: it's drawn again then, not every frame.
function groundShadow(scene, pick, { z = 0, size = 5.6, height = 0.9, blur = 3.2, opacity = 0.92, power = 1.6, res = 512, order = 2 } = {}) {
  const target = new THREE.WebGLRenderTarget(res, res), spare = new THREE.WebGLRenderTarget(res, res);
  target.texture.generateMipmaps = spare.texture.generateMipmaps = false;
  const plane = new THREE.PlaneGeometry(size, size).rotateX(-Math.PI / 2);
  const uv = plane.getAttribute('uv');
  for (let i = 0; i < uv.count; i++) uv.setY(i, 1 - uv.getY(i));  // the camera below sees +z as up
  const shadow = new THREE.Mesh(plane, new THREE.MeshBasicMaterial({ map: target.texture, transparent: true, opacity, depthWrite: false }));
  shadow.position.set(0, 0.002 + order * 0.0005, z);
  shadow.renderOrder = order;
  scene.add(shadow);
  const cam = new THREE.OrthographicCamera(-size / 2, size / 2, size / 2, -size / 2, 0, height);
  cam.rotation.x = Math.PI / 2;  // looking up from the floor
  cam.position.set(0, 0, z);
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
  let drawn = '';  // the meshes it was last drawn with
  shadow.onBeforeRender = (r) => {
    const meshes = [];
    scene.traverse((o) => { if (o.isMesh && o.visible && pick(o)) meshes.push(o); });
    const now = meshes.map((o) => o.uuid).join();
    if (!meshes.length || now === drawn) return;
    drawn = now;
    for (const o of meshes) o.layers.enable(5 + order);
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

// The studio in the scene. light: FLOOR's scale (viewer.js's ?room= to try another).
export function createStudio({ scene, renderer, centre, light = 1 }) {
  const colour = FLOOR.map((c) => c * light);
  const aniso = renderer.capabilities.getMaxAnisotropy();
  const z = centre.z;

  // the cove, drawn from inside: from under the floor it isn't drawn at all, and the car's
  // underside stays in view
  const profile = [new THREE.Vector2(0, 0), new THREE.Vector2(RADIUS, 0)];
  for (let i = 1; i <= 12; i++) {
    const t = (i / 12) * (Math.PI / 2);
    profile.push(new THREE.Vector2(RADIUS + 6 * Math.sin(t), 6 - 6 * Math.cos(t)));
  }
  profile.push(new THREE.Vector2(RADIUS + 6, 14), new THREE.Vector2(0, 14));
  const cove = studio(new THREE.MeshStandardMaterial({ roughness: 1, metalness: 0, side: THREE.BackSide }), { flat: true });
  cove.color.setRGB(...colour);
  const room = new THREE.Mesh(new THREE.LatheGeometry(profile, 128), cove);
  room.position.set(0, -0.003, z);  // just under the floor
  room.receiveShadow = true;
  scene.add(room);
  // the vignette's centre, each time the room is drawn on the screen (not into a shadow's picture)
  const mid = new THREE.Vector3(), px = new THREE.Vector2();
  room.onBeforeRender = (r, s, cam) => {
    if (r.getRenderTarget() !== null) return;
    r.getDrawingBufferSize(px);
    mid.copy(centre).project(cam);
    VIGNETTE.vignetteAt.value.set((mid.x + 1) / 2 * px.x, (mid.y + 1) / 2 * px.y, px.y / 2);
  };

  const disc = () => new THREE.CircleGeometry(RADIUS, 160).rotateX(-Math.PI / 2).translate(0, 0, z);
  const fadeFrom = (material) => { material.userData.studio.fadeCentre.value.set(centre.x, z); return material; };
  const load = (url, repeat, colour) => {
    const t = new THREE.TextureLoader().load(url);
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.repeat.set(repeat, repeat);
    t.anisotropy = aniso;
    t.colorSpace = colour ? THREE.SRGBColorSpace : THREE.NoColorSpace;
    return t;
  };
  // the grain
  const base = `data/floor/${GRAIN.asset}/${GRAIN.asset}_1K-JPG`, n = RADIUS * 2 / GRAIN.metres;
  const grain = fadeFrom(studio(new THREE.MeshStandardMaterial({
    map: load(`${base}_Color.jpg`, n, true), normalMap: load(`${base}_NormalGL.jpg`, n, false),
    normalScale: new THREE.Vector2(GRAIN.relief, GRAIN.relief), roughness: 1, metalness: 0, transparent: true,
  }), { matte: true, fade: FADE, grain: { colour, mean: GRAIN.mean, power: GRAIN.power } }));
  const floor = new THREE.Mesh(disc(), grain);
  floor.receiveShadow = true;
  floor.renderOrder = 1;
  scene.add(floor);
  // the grid: a line 7/512 of a square wide (7 mm at 50 cm), nothing between: the grain shows through
  const c = document.createElement('canvas');
  c.width = c.height = 512;
  const g = c.getContext('2d');
  g.fillStyle = '#ffffff';
  g.fillRect(0, 0, 512, 7);
  g.fillRect(0, 0, 7, 512);
  const lines = new THREE.CanvasTexture(c);
  lines.wrapS = lines.wrapT = THREE.RepeatWrapping;
  lines.repeat.setScalar(RADIUS * 2 / GRID);
  lines.offset.setScalar(-((RADIUS / GRID) % 1));
  lines.anisotropy = aniso;
  const grid = fadeFrom(studio(new THREE.MeshStandardMaterial({ alphaMap: lines, transparent: true, roughness: 1, metalness: 0,
    depthWrite: false }), { flat: true, fade: FADE }));
  grid.color.setRGB(...colour.map((c) => c * 0.6));  // lines a little darker than the room
  const gridMesh = new THREE.Mesh(disc(), grid);
  gridMesh.renderOrder = 1;
  gridMesh.position.y = 0.001;
  scene.add(gridMesh);
  // two layers of ground shadow, as KeyShot's ground occlusion looks: a wide soft one from
  // everything within 90 cm of the floor, a tight dark one where the tyres and the plank come nearest
  const isCar = (o) => Boolean(o.geometry.getAttribute('part'));
  groundShadow(scene, isCar, { z, height: 0.9, blur: 3.5, opacity: 0.75, power: 1.4, order: 2 });
  groundShadow(scene, isCar, { z, height: 0.22, blur: 1.1, opacity: 0.9, power: 1.2, order: 3 });

}
