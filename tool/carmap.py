"""The car map: the body's shape worked out once from its mesh, so every design knows the car.

Before it, each design learned the car on its own (TSC_WindTunnel's smoke lines cut the body
into sections to find where its top ends; the guides' "Learned" kept repeating the same folds,
inlets and creases). The map is built from the body's mesh (Skin_01, welded into one surface), is
cached in the work folder, and answers for any point on the car:

    m = carmap.load()
    m.at(pos, nrm)           the body's triangle and barycentric weights under each point
    m.value("open", pos, nrm)  a per-vertex layer at those points

Layers (per welded vertex of the body):
    open       how much of the open air a spot sees, 0 (inside an inlet, under a panel) to 1
               (the top of the sidepod): the cosine-weighted share of directions it's seen from,
               with the inner car (Details) in the way and the wheels and glass not
    seen       (V, K) bits: whether the spot is seen from each of the K directions in `dirs`

    python -m tool.carmap            build it (about 2 minutes) and print a summary
"""

import functools

import numpy as np
from scipy.spatial import cKDTree

from tool import fbx, parts, paths

CACHE = paths.CACHE / "carmap.npz"
VERSION = 1
N_DIRS = 200
PIXEL = 1.0  # cm, the depth maps' pixel when testing what each spot sees


# ---- the body as one surface ----

def _weld():
    """Skin_01 welded by position (0.01 cm): vertices V, triangles F over them (Skin_01's order),
    each triangle's normal from the model's own normals (so the outside is known), and its part."""
    m = fbx.meshes()["Skin_01"]
    pos = m["positions"].astype(np.float64)
    _, first, inv = np.unique(np.round(pos, 2), axis=0, return_index=True, return_inverse=True)
    V = pos[first]
    F = inv.reshape(-1)[m["tri_vertex"]]
    fn = m["tri_normal"].astype(np.float64).mean(1)
    fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
    P = parts.load()
    off = P.mesh_offset["Skin"]
    part = P.tri_part[off:off + len(F)].astype(np.int32)
    return V, F.astype(np.int32), fn, part


def _vertex_normals(V, F, fn):
    """Area-weighted mean of the triangles' (model) normals round each vertex."""
    e1, e2 = V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]
    area = 0.5 * np.linalg.norm(np.cross(e1, e2), axis=1)
    vn = np.zeros_like(V)
    for k in range(3):
        np.add.at(vn, F[:, k], fn * area[:, None])
    vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
    return vn, area


def directions(n=N_DIRS):
    """n directions spread evenly over the sphere (a Fibonacci lattice)."""
    i = np.arange(n) + 0.5
    y = 1 - 2 * i / n
    r = np.sqrt(1 - y * y)
    phi = np.pi * (3 - np.sqrt(5)) * i
    return np.stack([r * np.cos(phi), y, r * np.sin(phi)], 1)


# ---- what each spot sees ----

def _occluders():
    """The corners of every triangle that can hide the body: the body and the inner car."""
    ms = fbx.meshes()
    tris = [ms[k]["positions"][ms[k]["tri_vertex"]] for k in ("Skin_01", "Details_01")]
    return np.concatenate(tris).astype(np.float64)


def _depth_map(tris, d, pixel=PIXEL):
    """The nearest depth per pixel of the triangles seen from direction d (the eye far off along
    +d, looking back along -d), orthographic. Returns (zbuf, to_pixel), where to_pixel(points)
    gives each point's flat pixel index and depth."""
    d = d / np.linalg.norm(d)
    helper = np.array([0.0, 1.0, 0.0]) if abs(d[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u = np.cross(helper, d)
    u /= np.linalg.norm(u)
    v = np.cross(d, u)
    flat = tris.reshape(-1, 3)
    pu, pv, pz = flat @ u, flat @ v, -(flat @ d)
    u0, v0 = pu.min() - 2 * pixel, pv.min() - 2 * pixel
    W = int(np.ceil((pu.max() - u0) / pixel)) + 3
    H = int(np.ceil((pv.max() - v0) / pixel)) + 3
    xy = np.stack([(pu - u0) / pixel, (pv - v0) / pixel], 1).reshape(-1, 3, 2)
    z = pz.reshape(-1, 3)
    zbuf = np.full(W * H, np.inf)
    lo = np.floor(xy.min(1) - 0.5).astype(np.int64)
    hi = np.ceil(xy.max(1) - 0.5).astype(np.int64)
    size = (hi - lo + 1).max(1)
    a, b, c = xy[:, 0], xy[:, 1], xy[:, 2]
    area = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    good = np.abs(area) > 1e-12
    # triangles in buckets by their box's size, each bucket tested against every pixel of its
    # largest box at once
    for s0, s1 in ((0, 2), (2, 4), (4, 8), (8, 16), (16, 32), (32, 10 ** 6)):
        sel = np.flatnonzero(good & (size > s0) & (size <= s1))
        if not len(sel):
            continue
        for chunk in np.array_split(sel, max(1, len(sel) * min(s1, 64) ** 2 // 4_000_000 + 1)):
            span = int(size[chunk].max())
            oy, ox = np.mgrid[0:span, 0:span]
            ox, oy = ox.ravel(), oy.ravel()
            px = lo[chunk, 0][:, None] + ox[None]
            py = lo[chunk, 1][:, None] + oy[None]
            cx, cy = px + 0.5, py + 0.5
            A, B, C = a[chunk], b[chunk], c[chunk]
            ar = area[chunk][:, None]
            w0 = ((B[:, 0:1] - cx) * (C[:, 1:2] - cy) - (B[:, 1:2] - cy) * (C[:, 0:1] - cx)) / ar
            w1 = ((C[:, 0:1] - cx) * (A[:, 1:2] - cy) - (C[:, 1:2] - cy) * (A[:, 0:1] - cx)) / ar
            w2 = 1 - w0 - w1
            inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0) & (px <= hi[chunk, 0][:, None]) & (py <= hi[chunk, 1][:, None])
            inside &= (px >= 0) & (py >= 0) & (px < W) & (py < H)
            zc = z[chunk]
            depth = w0 * zc[:, 0:1] + w1 * zc[:, 1:2] + w2 * zc[:, 2:3]
            np.minimum.at(zbuf, (py * W + px)[inside], depth[inside])

    def to_pixel(points):
        x = np.floor((points @ u - u0) / pixel).astype(np.int64)
        y = np.floor((points @ v - v0) / pixel).astype(np.int64)
        ok = (x >= 0) & (y >= 0) & (x < W) & (y < H)
        return np.where(ok, y * W + x, -1), -(points @ d)
    return zbuf, to_pixel


def _seen(points, normals, dirs, tris):
    """(n, K) whether each point is seen from each direction: it faces that way, and nothing is
    nearer the eye at its pixel (within a tolerance that grows as the surface turns edge-on)."""
    seen = np.zeros((len(points), len(dirs)), bool)
    for k, d in enumerate(dirs):
        c = normals @ d
        facing = c > 0.05
        zbuf, to_pixel = _depth_map(tris, d)
        pix, depth = to_pixel(points)
        tan = np.sqrt(np.maximum(1 - c * c, 0)) / np.maximum(c, 0.1)
        tol = 0.4 + 1.5 * PIXEL * np.minimum(tan, 4.0)
        front = np.where(pix >= 0, depth <= zbuf[np.maximum(pix, 0)] + tol, True)
        seen[:, k] = facing & front
    return seen


# ---- building and loading ----

def build():
    V, F, fn, part = _weld()
    vn, area = _vertex_normals(V, F, fn)
    dirs = directions()
    seen = _seen(V, vn, dirs, _occluders())
    w = np.maximum(vn @ dirs.T, 0)
    open_ = (seen * w).sum(1) / np.maximum(w.sum(1), 1e-9)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE, version=VERSION, V=V, F=F, fn=fn, part=part, vn=vn, area=area,
                        dirs=dirs, seen=np.packbits(seen, axis=1), open=open_.astype(np.float32))
    load.cache_clear()
    return load()


class Map:
    def __init__(self, data):
        self.V, self.F, self.fn, self.part = data["V"], data["F"], data["fn"], data["part"]
        self.vn, self.area, self.dirs = data["vn"], data["area"], data["dirs"]
        self.seen = np.unpackbits(data["seen"], axis=1)[:, :len(self.dirs)].astype(bool)
        self.layers = {"open": data["open"]}
        self._tree = None
        self._last = None

    # ---- finding the body under a point ----

    def _samples(self, spacing=0.5):
        """Points spread over every triangle about `spacing` cm apart, each with its triangle and
        barycentric weights: the lookup's tree."""
        A, B, C = self.V[self.F[:, 0]], self.V[self.F[:, 1]], self.V[self.F[:, 2]]
        edge = np.maximum.reduce([np.linalg.norm(B - A, axis=1), np.linalg.norm(C - B, axis=1),
                                  np.linalg.norm(A - C, axis=1)])
        n = np.clip(np.ceil(edge / spacing).astype(int), 1, 60)
        faces, bary = [], []
        for k in np.unique(n):
            sel = np.flatnonzero(n == k)
            i, j = np.mgrid[0:k + 1, 0:k + 1]
            keep = i + j <= k
            b1, b2 = i[keep] / k, j[keep] / k
            b = np.stack([1 - b1 - b2, b1, b2], 1)
            faces.append(np.repeat(sel, len(b)))
            bary.append(np.tile(b, (len(sel), 1)))
        return np.concatenate(faces), np.concatenate(bary)

    def _lookup(self):
        if self._tree is None:
            f, b = self._samples()
            p = (b[:, :, None] * self.V[self.F[f]]).sum(1)
            self._tree, self._sf, self._sb = cKDTree(p), f, b
        return self._tree

    def at(self, pos, nrm=None, k=6):
        """The body's triangle (face) and barycentric weights nearest each point, preferring one
        that faces the same way as the point's normal (so a panel lying on another, or the inside
        of a thin panel, isn't mistaken for it). Also the distance (cm): far means the point
        isn't on the body (an inner part)."""
        pos = np.asarray(pos, np.float64)
        key = (pos.shape, pos[:1].tobytes(), pos[-1:].tobytes(), None if nrm is None else np.asarray(nrm)[:1].tobytes())
        if self._last is not None and self._last[0] == key:
            return self._last[1]
        tree = self._lookup()
        d, i = tree.query(pos, k=k, workers=-1)
        pick = np.zeros(len(pos), np.int64)
        if nrm is not None:
            nrm = np.asarray(nrm, np.float64)
            agree = (self.fn[self._sf[i]] * nrm[:, None, :]).sum(2) > 0.2
            first = np.argmax(agree, axis=1)
            pick = np.where(agree.any(1), first, 0)
        r = np.arange(len(pos))
        s = i[r, pick]
        out = (self._sf[s], self._sb[s], d[r, pick])
        self._last = (key, out)
        return out

    def value(self, layer, pos, nrm=None):
        """A per-vertex layer interpolated at the points."""
        face, bary, _ = self.at(pos, nrm)
        vals = self.layers[layer][self.F[face]]
        return (bary * vals).sum(1).astype(np.float32)


@functools.lru_cache(maxsize=1)
def load():
    if not CACHE.exists():
        return build()
    data = np.load(CACHE)
    if int(data["version"]) != VERSION or CACHE.stat().st_mtime < fbx.CACHE.stat().st_mtime:
        return build()
    return Map(dict(data))


if __name__ == "__main__":
    import time
    t = time.time()
    m = build()
    print(f"built in {time.time() - t:.0f} s: {len(m.V)} vertices, {len(m.F)} triangles, {len(m.dirs)} directions")
    o = m.layers["open"]
    print("open: " + ", ".join(f"{q:.0%} {np.quantile(o, q):.2f}" for q in (0.05, 0.25, 0.5, 0.75, 0.95)))
