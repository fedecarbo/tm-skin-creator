"""Per-texel maps of the car: for every pixel of a texture, where it sits on the car.

bake(mesh, width, height) returns a dict of arrays, cached in the work folder:
  tri       (h, w) triangle id, -1 where no triangle covers the texel
  position  (h, w, 3) 3D position in cm (x = side, y = up, z = forward)
  normal    (h, w, 3) unit surface normal
  count     (h, w) how many triangles cover the texel: more than 1 means a shared texel
  sides     (h, w) bit 1: a left-side (x > 1) triangle covers it, bit 2: a right-side one
  near      (h * w,) each texel's nearest covered texel (itself when covered), a flat index
  pos, nrm  (h * w, 3) position and normal taken from that nearest texel: a texel on an island's edge that a
            part covers in part, while its centre misses every triangle, has a place (the paint box's)
Where several triangles share texels (mirrored or repeated parts), the last one drawn wins,
so position and normal describe one of them; count and sides say the texel is shared.

The cache is a folder of plain arrays (save), mapped from the disk when read (load): read-only, and only the
texels a paint reads come into memory, shared by every process that reads them.
"""

import os
import shutil

import numpy as np

from tool import fbx, paths, raster

VERSION = 3


def save(folder, arrays):
    """Arrays as plain .npy files in a folder, put in place whole: written beside it, then renamed."""
    tmp, old = (folder.with_name(f"{folder.name}.{k}{os.getpid()}") for k in ("tmp", "old"))
    tmp.mkdir(parents=True)
    for k, v in arrays.items():
        np.save(tmp / f"{k}.npy", np.ascontiguousarray(v))
    if folder.exists():
        folder.rename(old)
    tmp.rename(folder)
    shutil.rmtree(old, ignore_errors=True)  # on Windows, kept while another process still maps it


def load(folder):
    """A folder's arrays (save), mapped from the disk, read-only."""
    return {f.stem: np.load(f, mmap_mode="r").view(np.ndarray) for f in sorted(folder.glob("*.npy"))}


def bake(texture_set, width, height):
    folder = paths.CACHE / f"bake{VERSION}_{texture_set}_{width}x{height}"
    if (folder / "tri.npy").exists() and fbx.CACHE.exists() and (folder / "tri.npy").stat().st_mtime > fbx.CACHE.stat().st_mtime:
        return load(folder)
    m = fbx.meshes()[fbx.MESH_OF[texture_set]]
    uv = m["tri_uv"].astype(np.float64)
    xy = np.stack([uv[..., 0] * width, (1 - uv[..., 1]) * height], -1)  # image row = 1 - v
    tri, bary = raster.rasterise(xy, width, height)
    corner_pos = m["positions"][m["tri_vertex"]]
    position = raster.interpolate(tri, bary, corner_pos)
    normal = raster.interpolate(tri, bary, m["tri_normal"])
    normal /=np.maximum(np.linalg.norm(normal, axis=-1, keepdims=True), 1e-9)
    normal = normal.astype(np.float32)
    cx = corner_pos[:, :, 0].mean(1)
    flags = (cx > 1).astype(np.uint8) | ((cx < -1).astype(np.uint8) << 1)
    count, sides = raster.coverage(xy, width, height, flags)
    near = raster.nearest(tri >= 0)
    save(folder, {"tri": tri, "position": position, "normal": normal, "count": count, "sides": sides, "near": near,
                  "pos": position.reshape(-1, 3)[near], "nrm": normal.reshape(-1, 3)[near]})
    return load(folder)
