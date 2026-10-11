// The studio the car stands in (the user, 2026-09-27, from floors tried in the viewer: "Matte, tiny bit
// grainy texture in the grid one, and the grid make it tiny bit smaller", "a bit whiter but with some
// kind of vignette so that the buttons dont dissapear", "the grid smaller in scale. but a bit farther
// covering", then "we can have the grainy grid, and have the dark and light options", "Maybe we keep
// one floor, but meet in the middle?" and last "Or maybe just meet the color that the screenshots
// have"). One room, its ground one of the game's surfaces (GROUNDS; the user, 2026-10-11, from their
// screenshots of each: "the types of surfaces in trackmania similar to the concrete, there's also grass,
// sand"): the concrete, the colour of the game's track in the user's screenshots, lit by the mood, reads
// the track's (205, 200, 204) by day and its (124, 123, 128) at sunrise from Cam 2; each mood's `studio`
// in viewer.js's LOOKS corrects the rest (setStudioTint). The other grounds are read off the user's
// screenshots by day the same way.
//   The room: a seamless cove, the floor curving up into the walls and a ceiling (floor radius 30 m,
//     curve 6 m, 14 m high), lit as if it were all flat floor (the normal straight up, no shine), so
//     it's one even colour with no line where the floor bends, in every mood.
//   The floor: a fine, even matte grain in the ground's colour (an ambientCG set, CC0, downloaded by
//     tool/view.py: FLOOR_SETS) averaging the room's colour, under a faint line every metre (on the ice, the ice road's lines), one under
//     the car's middle; both fade out between 10 and 30 m (the user, 2026-10-11, of the ice road: "little range in distance").
//   The mirror (the ice): the car reflected in the floor (three.js's Reflector, the scene drawn again from
//     under the floor), laid over the grain at a ground's `mirror` strength, stronger towards a low angle
//     as on real ice, and only what the mirror sees: nothing behind it darkens the floor.
//   The ground shadow: a soft shadow right under the car (KeyShot's ground occlusion), drawn again
//     only when the car's parts come or go.
//   The vignette: the studio, never the car, darkening gently towards the picture's corners, around
//     the car's middle on the screen.
// The other floors tried (KeyShot's reflection, concrete, asphalt, rubber, a turntable, a plain grid)
// are in the git history, 2026-09-27.

import * as THREE from 'three';
import { FullScreenQuad } from 'three/addons/postprocessing/Pass.js';
import { Reflector } from 'three/addons/objects/Reflector.js';
import { HorizontalBlurShader } from 'three/addons/shaders/HorizontalBlurShader.js';
import { VerticalBlurShader } from 'three/addons/shaders/VerticalBlurShader.js';

const RADIUS = 30;  // the room's flat floor: the cove curves up from here (14 until 2026-10-11: the ice road ran out too soon)
// The grounds: the game's surfaces, each its colour (linear; by day the light alone makes it read as
// the screenshot's) and its grain (an ambientCG set: its colour picture's mean, the power the grain shows
// at, the metres one repeat covers, how much of its relief). The concrete's grain repeats every 40 cm,
// grey only (the rubber's lilac and beige blotches gone), at power 0.7 so it still shows as the viewer
// opens; finer melts into plain grey on the screen (the user's pick from renders, 2026-09-27: "make the
// floor grain a bit smaller"). The grass is the stadium's mown lawn, the dirt its terracotta, the ice its
// rink's white-blue; the grass's and the dirt's grains are the real surfaces at about their real size.
export const GROUNDS = {
  concrete: { label: 'Concrete', colour: [0.353, 0.329, 0.349], swatch: '#cdc8cc',
    grain: { asset: 'Rubber004', mean: [0.0238, 0.0255, 0.0323], power: 0.7, metres: 0.4, relief: 0.3 } },
  // the game's mown lawn (the user, 2026-10-11, from their screenshot of its grass road, then "just make it lawned (no
  // bushy) but interchanging between shades"): pale, mown in strips along the car, a shade lighter and darker in turn (LAWN)
  grass: { label: 'Grass', colour: [0.30, 0.355, 0.11], swatch: '#bfcd78', markings: 'lawn',
    grain: { asset: 'Grass005', mean: [0.1352, 0.2358, 0.0265], power: 0.5, metres: 1.0, relief: 0.35 } },
  // lighter than the first reading, and no grid on it (the user, 2026-10-11: "too dark. Also make it less tiley")
  dirt: { label: 'Dirt', colour: [0.41, 0.135, 0.055], swatch: '#d2814f', markings: 'plain',
    grain: { asset: 'Ground104', mean: [0.232, 0.1556, 0.0617], power: 0.4, metres: 0.6, relief: 0.25, turn: 90 } },  // its streaks along the car (the user: "more on the perpendicular direction")
  // a skating rink's ice (the user, 2026-10-11: "ice skating ice"): white-blue, with skate scratches (drawn by
  // tool/view.py, draw_rink), laid out as the game's ice road (ROAD) in place of the grid
  // the sky in its sheen and the car mirrored in it, faintly, more at a low angle (the user: "a bit more reflective")
  // a softened shadow on it, as ice scatters light (the user: "shadow does not make sense in ice", then "more faint
  // not off", then "whatever you think will look real")
  ice: { label: 'Ice', colour: [0.42, 0.45, 0.49], swatch: '#dee6ee', markings: 'road', shine: 0.3, mirror: 0.055, shadow: 0.55,  // a quarter of 0.22 (the user: "less mirrory like half", then "half it again")
    grain: { asset: 'Rink', mean: [0.6033, 0.6033, 0.6033], power: 0.8, metres: 1.5, relief: 0 } },
};
export const GROUND_NAMES = Object.keys(GROUNDS);
const GRID = 1.0;  // metres between the lines (50 cm until 2026-10-11: the user, "maybe 100cm")
// The ice as the game's ice road (the user, 2026-10-11, from their screenshot: "the center is more whitish ice, then
// a blue line, then more bluish ice then a red line, then blueish ice again", the other side the same), along the
// car's length, measured off the picture: the road 16 m wide, its middle the ice's own white, a thin blue line
// 1.9 m out, bluish ice to a thin red line 6.9 m out, bluish ice on beyond. The bands are a blue-grey laid thinly
// over the white; the lines the picture's blue and red.
// The lawn (the user's screenshot of the game's grass road, 2026-10-11): mown in strips 2 m wide along the car, the
// whole floor over, alternately a shade lighter and darker.
const LAWN = { strip: 2, light: 'rgba(255, 255, 220, 0.09)', dark: 'rgba(40, 80, 20, 0.08)' };
const ROAD = { tint: 'rgba(130, 145, 175, 0.24)',  // the bands a lighter touch (the user: "maybe less blue")
  blue: 'rgba(90, 110, 170, 0.8)', red: 'rgba(200, 80, 100, 0.75)',
  blueAt: 1.9, redAt: 6.9, line: 0.1 };
const FADE = { r0: 10, r1: 30 };  // early and long, a gentle melt into the room (the user, 2026-10-11: "the fading is too intense")
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
// at all (a satin floor catches the sky's bright spots as blotches the grey room doesn't have; a ground's
// `shine` turns it back on, studioMatte, with that roughness); fade:
// the alpha going from 1 to 0 between r0 and r1 metres from the car; grain: the colour picture as
// colour * (the texel's lightness against the mean)^power, "a tiny bit grainy".
function studio(material, { flat = false, matte = flat, fade = null, grain = null } = {}) {
  const uniforms = {
    fadeCentre: { value: new THREE.Vector2() },
    fadeRange: { value: new THREE.Vector2(...(fade ? [fade.r0, fade.r1] : [0, 1])) },
    floorGrey: { value: new THREE.Vector3(...(grain ? grain.colour : [0, 0, 0])) },
    grainMean: { value: new THREE.Vector3(...(grain ? grain.mean : [1, 1, 1])) },
    grainPower: { value: grain ? grain.power : 1 },
    studioMatte: { value: matte ? 1 : 0 },
  };
  material.userData.studio = uniforms;
  material.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, uniforms, VIGNETTE);
    let frag = shader.fragmentShader.replace('#include <common>', `#include <common>
      varying vec2 vStudioXZ; uniform vec2 fadeCentre, fadeRange; uniform vec3 floorGrey; uniform float grainPower, studioMatte; uniform vec3 grainMean;
      uniform vec3 vignetteAt, studioTint; uniform float vignetteStrength;`)
      .replace('#include <opaque_fragment>', `#include <opaque_fragment>
        float vignette = smoothstep( 0.5, 1.4, length( ( gl_FragCoord.xy - vignetteAt.xy ) / vignetteAt.z * vec2( 0.6, 1.0 ) ) );
        gl_FragColor.rgb *= mix( 1.0, 0.6, vignette * vignetteStrength ) * studioTint;`);
    if (grain) {
      // the picture without its repeat (the user, 2026-10-11, of the ice's cracks: "more spread out instead of
      // tiles"): each cell of the floor, one repeat square, shows its own random window of the picture,
      // blended into its neighbours' over the middle half of the cell
      frag = frag.replace('#include <map_pars_fragment>', `#include <map_pars_fragment>
        vec2 studioCellShift( vec2 cell ) {
          return fract( sin( vec2( dot( cell, vec2( 127.1, 311.7 ) ), dot( cell, vec2( 269.5, 183.3 ) ) ) ) * 43758.5453 );
        }
        vec3 studioNoTile( sampler2D picture, vec2 uv ) {
          vec2 cell = floor( uv ), f = fract( uv ), b = smoothstep( 0.25, 0.75, f );
          vec3 a = texture2D( picture, uv + studioCellShift( cell ) ).rgb;
          vec3 c = texture2D( picture, uv + studioCellShift( cell + vec2( 1.0, 0.0 ) ) ).rgb;
          vec3 d = texture2D( picture, uv + studioCellShift( cell + vec2( 0.0, 1.0 ) ) ).rgb;
          vec3 e = texture2D( picture, uv + studioCellShift( cell + vec2( 1.0, 1.0 ) ) ).rgb;
          return mix( mix( a, c, b.x ), mix( d, e, b.x ), b.y );
        }`)
        .replace('#include <map_fragment>', `#include <map_fragment>
        float grainRatio = dot( studioNoTile( map, vMapUv ).rgb / grainMean, vec3( 0.2126, 0.7152, 0.0722 ) );
        diffuseColor.rgb = floorGrey * pow( max( grainRatio, 0.0 ), grainPower );`);
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
        material.specularColor *= 1.0 - studioMatte; material.specularColorBlended *= 1.0 - studioMatte; material.specularF90 *= 1.0 - studioMatte;`);
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
// leaves out the wings' and wheels' movement), so the picture changes only when a mesh or a part is
// shown or hidden: it's drawn again then, not every frame. parts: the viewer's part table (a part
// whose texel is dark is hidden, and casts nothing) and the count of its changes.
function groundShadow(scene, pick, parts, { z = 0, size = 5.6, height = 0.9, blur = 3.2, opacity = 0.92, power = 1.6, res = 512, order = 2 } = {}) {
  const target = new THREE.WebGLRenderTarget(res, res), spare = new THREE.WebGLRenderTarget(res, res);
  target.texture.generateMipmaps = spare.texture.generateMipmaps = false;
  const plane = new THREE.PlaneGeometry(size, size).rotateX(-Math.PI / 2);
  const uv = plane.getAttribute('uv');
  for (let i = 0; i < uv.count; i++) uv.setY(i, 1 - uv.getY(i));  // the camera below sees +z as up
  const shadow = new THREE.Mesh(plane, new THREE.MeshBasicMaterial({ map: target.texture, transparent: true, opacity, depthWrite: false }));
  shadow.userData.opacity = opacity;  // its own, for a ground that shadows less (shadowed)
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
    shader.uniforms.partTable = { value: parts.table };
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', `#include <common>
        attribute float part; varying float vGroundPart;`)
      .replace('#include <begin_vertex>', `#include <begin_vertex>
        vGroundPart = part;`);
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', `#include <common>
        uniform sampler2D partTable; varying float vGroundPart;`)
      .replace('#include <clipping_planes_fragment>', `#include <clipping_planes_fragment>
        if ( texture2D( partTable, vec2( ( vGroundPart + 0.5 ) / 256.0, 0.25 ) ).r < 0.5 ) discard;`)
      .replace('gl_FragColor = vec4( vec3( 1.0 - fragCoordZ ), opacity );',
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
    const now = `${meshes.map((o) => o.uuid).join()} ${parts.changes()}`;
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

// The studio in the scene. light: the ground colour's scale (viewer.js's ?room= to try another). parts: as
// groundShadow's. ground: a name from GROUNDS; setGround swaps it later.
let studioNow = null;  // what setGround changes: the cove, the floor and the grid, and the loader
export function createStudio({ scene, renderer, centre, parts, light = 1, ground = 'concrete' }) {
  const spec = GROUNDS[ground] || GROUNDS.concrete;
  const colour = spec.colour.map((c) => c * light);
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
  const load = (url, repeat, colour, turn = 0) => {  // turn: the picture turned on the floor, degrees
    const t = new THREE.TextureLoader().load(url);
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.repeat.set(repeat, repeat);
    t.center.set(0.5, 0.5);
    t.rotation = THREE.MathUtils.degToRad(turn);
    t.anisotropy = aniso;
    t.colorSpace = colour ? THREE.SRGBColorSpace : THREE.NoColorSpace;
    return t;
  };
  // the grain
  const G = spec.grain, base = `data/floor/${G.asset}/${G.asset}_1K-JPG`, n = RADIUS * 2 / G.metres;
  const grain = fadeFrom(studio(new THREE.MeshStandardMaterial({
    map: load(`${base}_Color.jpg`, n, true, G.turn), normalMap: load(`${base}_NormalGL.jpg`, n, false, G.turn),
    normalScale: new THREE.Vector2(G.relief, G.relief), roughness: spec.shine || 1, metalness: 0, transparent: true,
  }), { matte: true, fade: FADE, grain: { colour, mean: G.mean, power: G.power } }));
  grain.userData.studio.studioMatte.value = spec.shine ? 0 : 1;
  const floor = new THREE.Mesh(disc(), grain);
  floor.receiveShadow = true;
  floor.renderOrder = 1;
  scene.add(floor);
  // the grid: a line 7/1024 of a square wide (7 mm at 1 m), nothing between: the grain shows through
  const c = document.createElement('canvas');
  c.width = c.height = 1024;
  const g = c.getContext('2d');
  g.fillStyle = '#ffffff';
  g.fillRect(0, 0, 1024, 7);
  g.fillRect(0, 0, 7, 1024);
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
  gridMesh.visible = !spec.markings;
  scene.add(gridMesh);
  // what's painted on a ground in place of the grid (the ice road, the grass road): one picture of the whole floor
  // (60 m, 4096 px: 1.5 cm a pixel), the car's middle at its centre, drawn again for each ground (drawMarkings)
  const rc = document.createElement('canvas');
  rc.width = rc.height = 4096;
  const paint = new THREE.CanvasTexture(rc);
  paint.colorSpace = THREE.SRGBColorSpace;
  paint.anisotropy = aniso;
  drawMarkings(rc, paint, spec);
  const road = fadeFrom(studio(new THREE.MeshStandardMaterial({ map: paint, transparent: true, roughness: 1, metalness: 0,
    depthWrite: false }), { flat: true, fade: FADE }));
  const rinkMesh = new THREE.Mesh(disc(), road);
  rinkMesh.renderOrder = 1;
  rinkMesh.position.y = 0.001;
  rinkMesh.visible = Boolean(spec.markings);
  scene.add(rinkMesh);
  // the mirror: a flat disc at the floor (the Reflector's own normal is its +z, so the mesh is turned, not the geometry)
  const size = renderer.getDrawingBufferSize(new THREE.Vector2());
  const mirror = new Reflector(new THREE.CircleGeometry(RADIUS, 160), { clipBias: 0.003, textureWidth: size.x, textureHeight: size.y });
  mirror.rotation.x = -Math.PI / 2;
  mirror.position.set(0, 0.0007, z);
  mirror.renderOrder = 1;
  const seen = mirror.material;  // the Reflector's own: its texture and matrix are what the blend reads
  mirror.material = new THREE.ShaderMaterial({
    uniforms: { tDiffuse: seen.uniforms.tDiffuse, textureMatrix: seen.uniforms.textureMatrix, strength: { value: spec.mirror || 0 },
      fadeCentre: { value: new THREE.Vector2(centre.x, z) }, fadeRange: { value: new THREE.Vector2(FADE.r0, FADE.r1) } },
    transparent: true, depthWrite: false,
    vertexShader: `uniform mat4 textureMatrix; varying vec4 vUv; varying vec3 vWorld;
      void main() {
        vec4 w = modelMatrix * vec4( position, 1.0 );
        vWorld = w.xyz;
        vUv = textureMatrix * vec4( position, 1.0 );
        gl_Position = projectionMatrix * viewMatrix * w;
      }`,
    fragmentShader: `uniform sampler2D tDiffuse; uniform float strength; uniform vec2 fadeCentre, fadeRange;
      varying vec4 vUv; varying vec3 vWorld;
      void main() {
        vec4 seen = texture2DProj( tDiffuse, vUv );
        vec3 v = normalize( cameraPosition - vWorld );
        float low = pow( 1.0 - clamp( v.y, 0.0, 1.0 ), 4.0 );
        float a = seen.a * clamp( strength + ( 1.0 - strength ) * 0.2 * low, 0.0, 1.0 );
        a *= 1.0 - smoothstep( fadeRange.x, fadeRange.y, length( vWorld.xz - fadeCentre ) );
        gl_FragColor = vec4( seen.rgb, a );
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  });
  // the mirror's picture: cleared to nothing, not to the scene's black, so only what it sees is laid over the floor
  const draw = mirror.onBeforeRender, clear = new THREE.Color();
  mirror.onBeforeRender = function (r, sc, cam) {
    const bg = sc.background, alpha = r.getClearAlpha();
    r.getClearColor(clear);
    sc.background = null;
    r.setClearColor(0x000000, 0);
    draw.call(this, r, sc, cam);
    r.setClearColor(clear, alpha);
    sc.background = bg;
  };
  mirror.visible = Boolean(spec.mirror);
  scene.add(mirror);
  // two layers of ground shadow, as KeyShot's ground occlusion looks: a wide soft one from
  // everything within 90 cm of the floor, a tight dark one where the tyres and the plank come nearest
  const isCar = (o) => Boolean(o.geometry.getAttribute('part'));
  const shadows = [groundShadow(scene, isCar, parts, { z, height: 0.9, blur: 3.5, opacity: 0.75, power: 1.4, order: 2 }),
    groundShadow(scene, isCar, parts, { z, height: 0.22, blur: 1.1, opacity: 0.9, power: 1.2, order: 3 })];
  studioNow = { cove, grain, grid, gridMesh, rinkMesh, rc, paint, mirror, shadows, scene, load, light };
  shadowed(spec.shadow ?? 1);
}

// The markings on a ground, drawn on the floor's picture: a column of the picture is a line along the car's length.
function drawMarkings(rc, paint, spec) {
  const rg = rc.getContext('2d'), ppm = rc.width / (RADIUS * 2), at = (m) => rc.width / 2 + m * ppm;
  rg.clearRect(0, 0, rc.width, rc.height);
  if (spec.markings === 'road') {  // the ice road: white in the middle, a blue line, bluish, a red line, bluish on
    const w = ROAD.line * ppm;
    rg.fillStyle = ROAD.tint;
    rg.fillRect(0, 0, at(-ROAD.blueAt), rc.height);
    rg.fillRect(at(ROAD.blueAt), 0, rc.width - at(ROAD.blueAt), rc.height);
    for (const sgn of [1, -1]) {
      rg.fillStyle = ROAD.blue;
      rg.fillRect(at(sgn * ROAD.blueAt) - w / 2, 0, w, rc.height);
      rg.fillStyle = ROAD.red;
      rg.fillRect(at(sgn * ROAD.redAt) - w / 2, 0, w, rc.height);
    }
  } else if (spec.markings === 'lawn') {  // ('plain': nothing drawn, and no grid either)  // the lawn: mowing strips the whole floor over
    for (let k = -Math.ceil(RADIUS / LAWN.strip); k < Math.ceil(RADIUS / LAWN.strip); k++) {
      rg.fillStyle = (k + 1000) % 2 ? LAWN.light : LAWN.dark;
      rg.fillRect(at(k * LAWN.strip), 0, LAWN.strip * ppm, rc.height);
    }
  }
  paint.needsUpdate = true;
}

// How much the car shadows the ground, 0 to 1: the two ground shadows' opacity, and the strength of the shadow
// cast by the scene's lights (the key, viewer.js).
function shadowed(strength) {
  const { shadows, scene } = studioNow;
  for (const sh of shadows) { sh.material.opacity = sh.userData.opacity * strength; sh.visible = strength > 0; }
  scene.traverse((o) => { if (o.isLight && o.castShadow) o.shadow.intensity = strength; });
}

// Another of the game's surfaces under the car: the room's colour, the floor's grain, its grid (the lines, or
// on the ice the road's), its mirror and whether the car shadows it change; the vignette stays. The pictures load as the floor is already drawn, so the colour
// shows at once and the grain a moment later.
export function setGround(name) {
  if (!studioNow || !GROUNDS[name]) return;
  const spec = GROUNDS[name], { cove, grain, grid, gridMesh, rinkMesh, rc, paint, mirror, load, light } = studioNow;
  shadowed(spec.shadow ?? 1);
  mirror.visible = Boolean(spec.mirror);
  mirror.material.uniforms.strength.value = spec.mirror || 0;
  gridMesh.visible = !spec.markings;
  rinkMesh.visible = Boolean(spec.markings);
  drawMarkings(rc, paint, spec);
  const colour = spec.colour.map((c) => c * light);
  cove.color.setRGB(...colour);
  grid.color.setRGB(...colour.map((c) => c * 0.6));
  const G = spec.grain, base = `data/floor/${G.asset}/${G.asset}_1K-JPG`, n = RADIUS * 2 / G.metres;
  const u = grain.userData.studio;
  u.floorGrey.value.set(...colour);
  u.grainMean.value.set(...G.mean);
  u.grainPower.value = G.power;
  u.studioMatte.value = spec.shine ? 0 : 1;
  grain.roughness = spec.shine || 1;
  for (const t of [grain.map, grain.normalMap]) if (t) t.dispose();
  grain.map = load(`${base}_Color.jpg`, n, true, G.turn);
  grain.normalMap = load(`${base}_NormalGL.jpg`, n, false, G.turn);
  grain.normalScale.set(G.relief, G.relief);
  grain.needsUpdate = true;
}
