// The world's props (lab-garage.js): real shapes from tool/props.py's models (data/props/<name>/<name>.gltf, the
// shapes alone) and Claude's figure (data/props/character.glb, Kenney's blocky character with its animations), each
// loaded once and cloned where it's put, all in one matte white (the user, 2026-10-20: "everything could be whitish
// apart from the car"). A prop's origin is where it stands on the floor; its size is real, in metres.

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { clone as cloneSkeleton } from 'three/addons/utils/SkeletonUtils.js';

const loader = new GLTFLoader();
const loaded = new Map();  // name -> Promise<{ scene, animations }>
export const WHITE = new THREE.MeshStandardMaterial({ color: 0xd9d9dd, roughness: 0.95, metalness: 0 });

function load(name) {
  if (!loaded.has(name)) loaded.set(name, new Promise((ok, fail) => {
    const url = name === 'character' ? 'data/props/character.glb' : `data/props/${name}/${name}.gltf`;
    loader.load(url, (gltf) => {
      gltf.scene.traverse((o) => {
        if (!o.isMesh) return;
        o.material = WHITE;
        o.castShadow = true;
        o.receiveShadow = true;
      });
      ok(gltf);
    }, undefined, fail);
  }));
  return loaded.get(name);
}

// A prop put down at (x, z) on the floor, turned `turn` radians about the vertical, scaled `scale`: the clone is
// added to `parent` once loaded, and `parent` is told (rouse) so the page draws it.
export function put(parent, name, x, z, turn = 0, scale = 1, y = 0, rouse = () => {}, material = null) {
  load(name).then((gltf) => {
    const o = gltf.scene.clone(true);
    o.traverse((m) => { m.userData.shared = true; if (material && m.isMesh) m.material = material; });  // never disposed: the shapes are the loaded copy's
    o.position.set(x, y, z);
    o.rotation.y = turn;
    o.scale.setScalar(scale);
    parent.add(o);
    rouse();
  }).catch((err) => console.error(`${name}: ${err.message || err}`));
}

// Claude's figure, `height` metres tall, playing `clip` (idle, walk, interact-right...): { group, mixer } once loaded.
export async function figure(clip = 'interact-right', height = 1.75) {
  const gltf = await load('character');
  const group = cloneSkeleton(gltf.scene);
  const box = new THREE.Box3().setFromObject(group);
  const s = height / (box.max.y - box.min.y);
  group.scale.setScalar(s);
  group.position.y = -box.min.y * s;
  const mixer = new THREE.AnimationMixer(group);
  const action = gltf.animations.find((a) => a.name === clip) || gltf.animations[0];
  if (action) mixer.clipAction(action).play();
  return { group, mixer };
}
