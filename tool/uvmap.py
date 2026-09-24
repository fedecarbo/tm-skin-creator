"""The car's own unfolding, in centimetres: flat coordinates for drawing patterns without stretch.

Nadeo's UV layout unfolds each panel of the car onto the flat texture with very little
distortion (measured 2026-09-24: on the body shell the stretch is under 5 % on 98 % of its
area, and the shell is one continuous island; the whole Skin set is under 10 % on 87 %). So a
pattern drawn in texture space, scaled by that island's texels-per-cm, sits on the car
undistorted, like a sticker cut to fit. Islands meet along the folds between parts, where a
pattern break is natural. This beats any projection invented from outside (three planes, a
tube), which stretch wherever the surface curves away from them.

    uv_cm = uvmap.uv_cm("Skin", 4096, 4096)   -> (h, w, 2) float32: flat position in cm per texel,
                                                  each island scaled by its own density
    label, density, angle = uvmap.islands("Skin")  -> per triangle: island, UV units per cm, and the
                                                  turn that puts the car's length up the pattern
"""

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

from tool import bake, fbx, paths

MESH_OF = {"Skin": "Skin_01", "Details": "Details_01", "Wheels": "Wheels_01", "Glass": "Glass_01"}


def islands(texture_set):
    """Per triangle: the UV island it belongs to, and the island's UV units per cm (area-weighted
    median of the triangles' scale)."""
    cache = paths.CACHE / f"uvislands_{texture_set}.npz"
    if cache.exists() and cache.stat().st_mtime > fbx.CACHE.stat().st_mtime:
        d = np.load(cache)
        return d["label"], d["density"], d["angle"]
    m = fbx.meshes()[MESH_OF[texture_set]]
    P = m["positions"][m["tri_vertex"]].astype(np.float64)
    UV = m["tri_uv"].astype(np.float64)
    T = len(P)
    # islands: triangles joined by a shared UV corner
    key = np.round(UV.reshape(-1, 2), 5)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(T, 3)
    A = coo_matrix((np.ones(3 * T), (np.repeat(np.arange(T), 3), inv.reshape(-1))), shape=(T, inv.max() + 1))
    _, label = connected_components(A @ A.T, directed=False)
    # scale: UV area / 3D area per triangle, sqrt -> UV units per cm
    e1, e2 = P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]
    a3 = np.linalg.norm(np.cross(e1, e2), axis=1) / 2
    u1, u2 = UV[:, 1] - UV[:, 0], UV[:, 2] - UV[:, 0]
    a2 = np.abs(u1[:, 0] * u2[:, 1] - u1[:, 1] * u2[:, 0]) / 2
    ok = (a3 > 1e-6) & (a2 > 1e-12)
    scale = np.zeros(T)
    scale[ok] = np.sqrt(a2[ok] / a3[ok])
    # which way the car's length (+z) runs in each triangle's UV: solve the 2x2 map from
    # in-plane 3D edges to UV edges, apply it to z projected into the plane
    n = np.cross(e1, e2)
    nn = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    x = e1 / np.maximum(np.linalg.norm(e1, axis=1, keepdims=True), 1e-9)
    y = np.cross(nn, x)
    E = np.stack([np.stack([(e1 * x).sum(1), (e2 * x).sum(1)], -1), np.stack([(e1 * y).sum(1), (e2 * y).sum(1)], -1)], 1)
    Uv = np.stack([np.stack([u1[:, 0], u2[:, 0]], -1), np.stack([u1[:, 1], u2[:, 1]], -1)], 1)
    z_dir = np.zeros((T, 2))
    good = ok & (np.abs(np.linalg.det(E)) > 1e-9)
    J = np.einsum("tij,tjk->tik", Uv[good], np.linalg.inv(E[good]))
    zp = np.array([0, 0, 1.0]) - nn[good] * nn[good][:, 2:3]  # z projected into the plane
    zloc = np.stack([(zp * x[good]).sum(1), (zp * y[good]).sum(1)], -1)
    z_dir[good] = np.einsum("tij,tj->ti", J, zloc)
    density = np.zeros(label.max() + 1)
    angle = np.zeros(label.max() + 1)
    for i in range(len(density)):
        sel = (label == i) & ok
        if sel.any():
            order = np.argsort(scale[sel])
            cum = np.cumsum(a3[sel][order])
            density[i] = scale[sel][order][np.searchsorted(cum, cum[-1] / 2)]
            d = (z_dir[sel] * a3[sel][:, None]).sum(0)
            # in image rows v runs down (row = 1 - v); turn so the car's +z points up the image
            dx, dy = d[0], -d[1]
            angle[i] = (-np.pi / 2 - np.arctan2(dy, dx)) if np.hypot(dx, dy) > 1e-9 else 0.0
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, label=label.astype(np.int32), density=density.astype(np.float64), angle=angle)
    return label.astype(np.int32), density, angle


def uv_cm(texture_set, width, height):
    """(h, w, 2): for each texel, its flat position in cm within its island (u across, v down
    the texture), so a pattern drawn on (u, v) has true size on the car. Uncovered texels are 0."""
    cache = paths.CACHE / f"uvcm_{texture_set}_{width}x{height}.npy"
    mesh_file = paths.CACHE / "mesh.npz"
    if cache.exists() and cache.stat().st_mtime > mesh_file.stat().st_mtime:
        return np.load(cache)
    label, density, angle = islands(texture_set)
    b = bake.bake(texture_set, width, height)
    tri = b["tri"]
    cov = tri >= 0
    out = np.zeros((height, width, 2), np.float32)
    rows, cols = np.nonzero(cov)
    isl = label[tri[cov]]
    dens = density[isl]  # UV units per cm
    u = (cols + 0.5) / width / dens
    v = (rows + 0.5) / height / dens
    # turn each island so the car's length runs up the pattern: rows of a pattern then line
    # up with the car on every panel, instead of with the texture's layout
    ca, sa = np.cos(angle[isl]), np.sin(angle[isl])
    out[rows, cols, 0] = ca * u - sa * v
    out[rows, cols, 1] = sa * u + ca * v
    np.save(cache, out)
    return out
