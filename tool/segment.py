"""Take the car apart: every mesh into its pieces, touching pieces into groups, mirrored pairs.

The exporter already split the meshes along every hard edge and UV seam, by duplicating the
vertices there (measured 2026-09-24: no normal breaks and no UV seams inside any
index-connected piece). So a "piece" here is a set of triangles joined by shared vertex
indices, which is exactly the crease-and-island split the plan asked for. A "group" joins the
pieces that touch (vertices at the same position), such as a bolt and the arm it sits on.

Ids are global across the four meshes, in the order Skin, Details, Wheels, Glass, and they are
deterministic: they only change if the FBX or this file changes. tool/naming.py refers to them.

segments() returns a dict of arrays over all T triangles:
  mesh      (T)   0 Skin, 1 Details, 2 Wheels, 3 Glass
  piece     (T)   piece id
  group     (T)   group id (touching pieces)
  centroid  (T,3) triangle centroid, cm
  normal    (T,3) face normal
  area      (T)
and per piece:
  piece_mesh, piece_tris, piece_centroid (P,3), piece_lo, piece_hi (P,3), piece_area (P),
  piece_twin (P) the piece mirrored in x, or -1
"""

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

from tool import fbx, paths

MESHES = ("Skin_01", "Details_01", "Wheels_01", "Glass_01")
SETS = ("Skin", "Details", "Wheels", "Glass")
CACHE = paths.CACHE / "segments.npz"


def _components(n_nodes, a, b):
    g = coo_matrix((np.ones(len(a)), (a, b)), shape=(n_nodes, n_nodes))
    return connected_components(g, directed=False)


def _build():
    meshes = fbx.meshes()
    out = {k: [] for k in ("mesh", "piece", "group", "centroid", "normal", "area")}
    piece_off = group_off = 0
    for i, name in enumerate(MESHES):
        m = meshes[name]
        tv, P = m["tri_vertex"], m["positions"].astype(np.float64)
        edges = np.concatenate([tv[:, [0, 1]], tv[:, [1, 2]], tv[:, [2, 0]]])
        k, lab = _components(len(P), edges[:, 0], edges[:, 1])
        out["piece"].append(lab[tv[:, 0]] + piece_off)
        piece_off += k
        # touching pieces: weld vertices that sit at the same position (0.01 cm)
        _, inv = np.unique(np.round(P, 2), axis=0, return_inverse=True)
        we = inv[edges]
        k, lab = _components(inv.max() + 1, we[:, 0], we[:, 1])
        out["group"].append(lab[we[: len(tv), 0]] + group_off)
        group_off += k
        p = P[tv]
        n = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
        out["area"].append(0.5 * np.linalg.norm(n, axis=1))
        out["normal"].append(n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12))
        out["centroid"].append(p.mean(1))
        out["mesh"].append(np.full(len(tv), i))
    seg = {k: np.concatenate(v) for k, v in out.items()}
    seg["mesh"] = seg["mesh"].astype(np.int8)
    seg["piece"] = seg["piece"].astype(np.int32)
    seg["group"] = seg["group"].astype(np.int32)
    seg["centroid"] = seg["centroid"].astype(np.float32)
    seg["normal"] = seg["normal"].astype(np.float32)
    seg["area"] = seg["area"].astype(np.float32)
    # per piece
    piece, n_pieces = seg["piece"], piece_off
    tris = np.bincount(piece, minlength=n_pieces)
    area = np.bincount(piece, weights=seg["area"], minlength=n_pieces)
    cen = np.stack([np.bincount(piece, weights=seg["centroid"][:, k] * seg["area"], minlength=n_pieces) for k in range(3)], 1)
    cen /= np.maximum(area, 1e-9)[:, None]
    lo = np.full((n_pieces, 3), np.inf)
    hi = np.full((n_pieces, 3), -np.inf)
    corners = np.concatenate([meshes[n]["positions"][meshes[n]["tri_vertex"]] for n in MESHES]).reshape(-1, 3)
    pid3 = np.repeat(piece, 3)
    for k in range(3):
        np.minimum.at(lo[:, k], pid3, corners[:, k])
        np.maximum.at(hi[:, k], pid3, corners[:, k])
    seg["piece_mesh"] = np.bincount(piece, weights=seg["mesh"], minlength=n_pieces) / np.maximum(tris, 1)
    seg["piece_mesh"] = np.rint(seg["piece_mesh"]).astype(np.int8)
    seg["piece_tris"] = tris.astype(np.int32)
    seg["piece_area"] = area.astype(np.float32)
    seg["piece_centroid"] = cen.astype(np.float32)
    seg["piece_lo"], seg["piece_hi"] = lo.astype(np.float32), hi.astype(np.float32)
    seg["piece_twin"] = _twins(seg).astype(np.int32)
    return seg


def _twins(seg):
    """For each piece, the piece that mirrors it in x (same mesh, similar size, mirrored box)."""
    cen, lo, hi, tris, mesh = seg["piece_centroid"], seg["piece_lo"], seg["piece_hi"], seg["piece_tris"], seg["piece_mesh"]
    n = len(cen)
    twin = np.full(n, -1)
    mlo = np.stack([-hi[:, 0], lo[:, 1], lo[:, 2]], 1)
    mhi = np.stack([-lo[:, 0], hi[:, 1], hi[:, 2]], 1)
    for p in range(n):
        if abs(cen[p, 0]) < 0.5:
            continue
        tol = 1.0 + 0.03 * (hi[p] - lo[p]).max()
        ok = (mesh == mesh[p]) & (np.abs(tris - tris[p]) <= 0.2 * tris[p] + 2)
        ok &= (np.abs(lo - mlo[p]).max(1) < tol) & (np.abs(hi - mhi[p]).max(1) < tol)
        ok[p] = False
        cands = np.flatnonzero(ok)
        if len(cands):
            twin[p] = cands[np.argmin(np.abs(tris[cands] - tris[p]))]
    return twin


def segments():
    if CACHE.exists() and CACHE.stat().st_mtime > max(fbx.CACHE.stat().st_mtime if fbx.CACHE.exists() else 0,
                                                      paths.FBX.stat().st_mtime, __import__("pathlib").Path(__file__).stat().st_mtime):
        return dict(np.load(CACHE))
    seg = _build()
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE, **seg)
    return seg


if __name__ == "__main__":
    s = segments()
    for i, name in enumerate(SETS):
        sel = s["piece_mesh"] == i
        print(f"{name}: {sel.sum()} pieces, {len(np.unique(s['group'][s['mesh'] == i]))} groups, "
              f"{(s['piece_twin'][sel] >= 0).sum()} mirrored")
