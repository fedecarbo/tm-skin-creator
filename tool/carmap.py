"""The car map: the open air each spot of the body sees, and where along the car it is, so every design knows the car.

The map is built on the body's surface (tool/surface.py: its welded points and triangles), is cached in the work
folder (`python -m tool.carmap` rebuilds it, about a minute), and answers for any point on the car. In a design,
through `tool.shapes`:

    shapes.outside(0.4)           the outer body: spots that see at least 40 % of the open air
    shapes.along(0.2, 0.4)        a band 20 % to 40 % of the way from the nose to the tail

Layers (per welded vertex of the body):
    open     how much of the open air a spot sees, 0 (inside an inlet, under a panel) to 1 (the top
             of the sidepod): the cosine-weighted share of 200 directions it's seen from, with the
             inner car in the way and the wheels and glass not
    along    0 at the nose's tip to 1 at the tail
    facing_x, facing_y, facing_z   the model's normal (x: out to the car's left, y: up, z: forward)

Map.at, value and level find the body under any point (tool/course.py lays its lines on it).
The lines on the car are the model's own (tool/meshlines.py).

    python -m tool.carmap            build it and print a summary
    python -m tool.carmap --describe the car's axes and where a graphic stops: car/anatomy.md (read before a
                                     design; the rest of its shape the car answers, tool/meshlines.py)
"""

import functools

import numpy as np
from scipy.spatial import cKDTree

from tool import fbx, noise, parts, paths, progress, surface

VERSION = 2
CACHE = paths.CACHE / f"carmap_v{VERSION}.npz"
N_DIRS = 200
PIXEL = 1.0      # cm, the depth maps' pixel when testing what each spot sees
NOSE_Z, TAIL_Z = 215.0, -162.0
WHEEL_COVERS = ("wheel cover disc", "wheel cover hub", "wheel cover ring")


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

def _occluders(sets=("Skin", "Details")):
    """The corners of every triangle that can hide the body: the body and the inner car (sets: the meshes, by their
    texture set's name; "Wheels" the tyres)."""
    ms = fbx.meshes()
    tris = [ms[fbx.MESH_OF[k]]["positions"][ms[fbx.MESH_OF[k]]["tri_vertex"]] for k in sets]
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
    progress.detail("Rebuilding the car map")
    S = surface.load("Skin")
    vn, area = _vertex_normals(S.V, S.F, S.fn)
    dirs = directions()
    seen = _seen(S.V, vn, dirs, _occluders())
    w = np.maximum(vn @ dirs.T, 0)
    open_ = (seen * w).sum(1) / np.maximum(w.sum(1), 1e-9)
    data = dict(version=VERSION, vn=vn, area=area, open=open_.astype(np.float32))
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE, **data)
    load.cache_clear()
    return load()


def _same(a, b):
    """Whether two calls asked the same: tuples of arrays (or None, or plain values), compared whole.
    The memos once compared a shape and the first and last points, which another set can share."""
    for x, y in zip(a, b):
        if isinstance(x, np.ndarray) or isinstance(y, np.ndarray):
            if not (isinstance(x, np.ndarray) and isinstance(y, np.ndarray) and np.array_equal(x, y)):
                return False
        elif x != y:
            return False
    return True


class Map:
    def __init__(self, data):
        S = surface.load("Skin")
        self.V, self.F, self.fn, self.part = S.V, S.F, S.fn, S.part
        self.vn, self.area = data["vn"], data["area"]
        self.part_names = np.array([inst["name"] for inst in parts.load().instances])
        self._tree = None
        self._last = None
        self._grad = {}
        self.layers = {"open": data["open"],
                       "along": ((NOSE_Z - self.V[:, 2]) / (NOSE_Z - TAIL_Z)).astype(np.float32),
                       "facing_x": (self.vn[:, 0] * np.sign(self.V[:, 0] + 1e-9)).astype(np.float32),
                       "facing_y": self.vn[:, 1].astype(np.float32), "facing_z": self.vn[:, 2].astype(np.float32)}

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
        nrm = None if nrm is None else np.asarray(nrm, np.float64)
        asked = (pos, nrm, k)
        if self._last is not None and _same(self._last[0], asked):  # zones ask again for the same points
            return self._last[1]
        tree = self._lookup()
        s, dist = np.zeros(len(pos), np.int64), np.zeros(len(pos))
        for a in range(0, len(pos), noise.CHUNK):  # the k nearest of a whole map's points at once held gigabytes
            d, i = tree.query(pos[a:a + noise.CHUNK], k=k, workers=-1)
            pick = np.zeros(len(d), np.int64)
            if nrm is not None:
                agree = (self.fn[self._sf[i]] * nrm[a:a + noise.CHUNK, None, :]).sum(2) > 0.2
                first = np.argmax(agree, axis=1)
                pick = np.where(agree.any(1), first, 0)
            r = np.arange(len(d))
            s[a:a + noise.CHUNK], dist[a:a + noise.CHUNK] = i[r, pick], d[r, pick]
        out = (self._sf[s], self._sb[s], dist)
        self._last = ((pos.copy(), None if nrm is None else nrm.copy(), k), out)
        return out


    def value(self, layer, pos, nrm=None):
        """A per-vertex layer interpolated at the points."""
        face, bary, _ = self.at(pos, nrm)
        vals = self.layers[layer][self.F[face]]
        if vals.ndim == 3:  # a layer of vectors
            return (bary[:, :, None] * vals).sum(1).astype(np.float32)
        return (bary * vals).sum(1).astype(np.float32)


    def gradient(self, layer):
        """Per triangle: how fast a layer changes across it, per cm (to turn a level into a crisp
        edge: the distance to the level is the difference over this)."""
        if layer not in self._grad:
            f = self.layers[layer][self.F].astype(np.float64)
            A, B, C = (self.V[self.F[:, k]] for k in range(3))
            e1, e2 = B - A, C - A
            n = np.cross(e1, e2)
            a2 = np.maximum((n * n).sum(1), 1e-12)
            # the gradient of a linear function over a triangle
            g = (np.cross(n, e2) * (f[:, 1] - f[:, 0])[:, None] + np.cross(e1, n) * (f[:, 2] - f[:, 0])[:, None]) / a2[:, None]
            self._grad[layer] = np.linalg.norm(g, axis=1)
        return self._grad[layer]


    def level(self, layer, level, pos, nrm=None, floor=1e-3):
        """Signed distance (cm, along the surface) from the points to where a layer crosses a level:
        positive where the layer is above it."""
        face, bary, _ = self.at(pos, nrm)
        vals = (bary * self.layers[layer][self.F[face]]).sum(1)
        return ((vals - level) / np.maximum(self.gradient(layer)[face], floor)).astype(np.float32)



@functools.lru_cache(maxsize=1)
def load():
    """The map, built again when the surface is newer than it (the mesh changed, or the surface's code)."""
    surface.load("Skin")
    if not CACHE.exists() or CACHE.stat().st_mtime < surface.cache_file("Skin").stat().st_mtime:
        return build()
    return Map(dict(np.load(CACHE)))


# ---- the car's axes and where a graphic stops, for the AI (car/anatomy.md) ----

ANATOMY_MD = paths.REPO / "car" / "anatomy.md"
STATIONS = ((212, "the nose's tip"), (190, "the nose, over the front wing"), (178, "the front wheels' axle"),
            (150, "the nose"), (130, "the nose fin's plate"), (110, "the bonnet"), (85, "the cockpit opening's front"),
            (60, "the front flank"), (30, "the front flank, the sidepods begin"), (0, "the sidepods, their inlets"),
            (-30, "the sidepods"), (-60, "the sidepods' back, the number panel"), (-90, "the deck, the engine cover panel"),
            (-120, "the rear wheels' axle"), (-140, "the tail"), (-158, "the tail's end"))


def _listed(words):
    words = list(words)
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]


def _opening_groups(m):
    """The body's openings as loops of open edges, 30 cm round or more: each group's points and the
    parts round it."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    F, V = m.F, m.V
    e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    tid = np.tile(np.arange(len(F)), 3)
    s = np.sort(e, 1)
    key = s[:, 0].astype(np.int64) * len(V) + s[:, 1]
    u, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
    single = cnt[inv] == 1
    se, st = s[single], tid[single]
    g = coo_matrix((np.ones(len(se)), (se[:, 0], se[:, 1])), shape=(len(V), len(V)))
    _, lab = connected_components(g, directed=False)
    groups = {}
    for (a, b), t_ in zip(se, st):
        groups.setdefault(lab[a], []).append((a, b, t_))
    out = []
    for edges in groups.values():
        pts = np.array([0.5 * (V[a] + V[b]) for a, b, _ in edges])
        length = sum(np.linalg.norm(V[a] - V[b]) for a, b, _ in edges)
        if length < 30:
            continue
        out.append(dict(pts=pts, length=length, parts=[int(m.part[t_]) for _, _, t_ in edges]))
    return out


def describe(m=None):
    """car/anatomy.md, the car's axes and where a graphic stops, one page for Claude to read before a design: every
    number comes from the model and the map, so it's redone with them. Everything else about the car's shape it answers
    itself (PY -m tool.meshlines)."""
    import datetime
    from tool import judge, pieces as pieces_mod
    m = m or load()
    names = np.array([inst["name"] for inst in parts.load().instances])
    plist, nm = pieces_mod.write()
    pname = names[m.part]
    zr = lambda name: (lambda z: f"z {z.min():.0f} to {z.max():.0f}")(m.V[m.F[pname == name]][..., 2])

    A = ["# The car", "",
         f"Written by `python -m tool.carmap --describe` from the car's own shape ({datetime.date.today()}). Lengths in cm: x "
         "out to the car's left (the right mirrors it), y up from the ground, z forward (the nose's tip at 215, the tail at "
         "-162). Along the car: " + "; ".join(f"{z} {words}" for z, words in STATIONS) + ". Everything else about its "
         "shape the car answers, exact from its mesh: `PY -m tool.meshlines` and its questions.", "",
         "## Where a graphic stops", ""]
    seen, own, sewn = set(), [], []
    for q in plist[1:]:
        key = tuple(q["parts"])
        if key in seen:
            continue
        seen.add(key)
        twin = sum(tuple(o["parts"]) == key for o in plist) > 1
        what = f"the {_listed(q['parts'])}" + (" (each side)" if twin else "")
        (sewn if q["gap_cm"] is not None and q["gap_cm"] <= judge.SEAM else own).append(f"{what}, {q['gap_cm']:.2g} cm")
    cockpit = next((g for g in _opening_groups(m) if np.bincount(g["parts"]).argmax() in
                    [i for i, n in enumerate(names) if n == "cockpit surround"]), None)
    A += [f"- One skin, sewn, over most of the body: the {_listed(plist[0]['parts'])}. A band or a line runs on across "
          "the seams between them.",
          f"- Pieces of their own, a gap of more than {judge.SEAM:.0f} cm round them: {'; '.join(own)}. A line stops "
          "there, as a wrap would.",
          f"- Pieces sewn on, {judge.SEAM:.0f} cm or less from the skin: {'; '.join(sewn)}. A line may run on.",
          "- A graphic laid whole (a badge, words, a picture) stays on one piece, and off a fold."]
    if cockpit is not None:
        c = cockpit["pts"]
        A.append(f"- The cockpit leaves no skin down the top's middle from z {c[:, 2].max():.0f} to {c[:, 2].min():.0f}, "
                 f"{c[:, 0].max():.0f} cm out each side.")
    A += [f"- {_listed(f'the {p} ({zr(p)})' for p in judge.LETTERED).capitalize()}: where the game letters the player's "
          "number and name, on top of the paint; a guide, not parts: paint runs on across them, an outline round the "
          "part they lie in leaves them in it.",
          f"- Keep clear: {_listed(f'{words} ({zr(p)})' for p, words in judge.PANELS.items() if p not in judge.LETTERED)}: "
          f"nothing on it or within {judge.CLEAR:.0f} cm (`show` names anything there).", ""]
    ANATOMY_MD.write_text("\n".join(A))
    return ANATOMY_MD


if __name__ == "__main__":
    import sys
    import time
    if "--describe" in sys.argv:
        print(describe())
        raise SystemExit
    t = time.time()
    with progress.job("Rebuilding the car map", done="The car map rebuilt"):
        m = build()
    print(f"built in {time.time() - t:.0f} s: {len(m.V)} vertices, {len(m.F)} triangles")
    o = m.layers["open"]
    print("open: " + ", ".join(f"{q:.0%} {np.quantile(o, q):.2f}" for q in (0.05, 0.25, 0.5, 0.75, 0.95)))
