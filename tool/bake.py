"""Per-texel maps of the car: for every pixel of a texture, where it sits on the car.

bake(mesh, width, height) returns a dict of arrays, cached in the work folder:
  tri       (h, w) triangle id, -1 where no triangle covers the texel
  position  (h, w, 3) 3D position in cm (x = side, y = up, z = forward)
  normal    (h, w, 3) unit surface normal
  count     (h, w) how many triangles cover the texel: more than 1 means a shared texel
  sides     (h, w) bit 1: a left-side (x > 1) triangle covers it, bit 2: a right-side one
Where several triangles share texels (mirrored or repeated parts), the last one drawn wins,
so position and normal describe one of them; count and sides say the texel is shared.
"""

import numpy as np

from tool import fbx, paths, raster

MESH_OF = {"Skin": "Skin_01", "Details": "Details_01", "Wheels": "Wheels_01", "Glass": "Glass_01"}


def bake(texture_set, width, height):
    cache = paths.CACHE / f"bake2_{texture_set}_{width}x{height}.npz"
    mesh_file = paths.CACHE / "mesh.npz"
    if cache.exists() and mesh_file.exists() and cache.stat().st_mtime > mesh_file.stat().st_mtime:
        return dict(np.load(cache))
    m = fbx.meshes()[MESH_OF[texture_set]]
    uv = m["tri_uv"].astype(np.float64)
    xy = np.stack([uv[..., 0] * width, (1 - uv[..., 1]) * height], -1)  # image row = 1 - v
    tri, bary = raster.rasterise(xy, width, height)
    corner_pos = m["positions"][m["tri_vertex"]]
    position = raster.interpolate(tri, bary, corner_pos)
    normal = raster.interpolate(tri, bary, m["tri_normal"])
    normal /= np.maximum(np.linalg.norm(normal, axis=-1, keepdims=True), 1e-9)
    cx = corner_pos[:, :, 0].mean(1)
    flags = (cx > 1).astype(np.uint8) | ((cx < -1).astype(np.uint8) << 1)
    count, sides = raster.coverage(xy, width, height, flags)
    result = {"tri": tri, "position": position, "normal": normal.astype(np.float32), "count": count, "sides": sides}
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, **result)
    return result
