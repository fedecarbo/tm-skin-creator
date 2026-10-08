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

Map.at, value, level and project find the body under any point (tool/course.py lays its lines on it).
The lines on the car are the model's own (tool/meshlines.py).

    python -m tool.carmap            build it and print a summary
    python -m tool.carmap --describe the car in words: car/anatomy.md (read before a design: the model's
                                     lines, tool/meshlines.py; its flat rooms, marks.rooms)
"""

import functools

import numpy as np
from scipy.spatial import cKDTree

from tool import fbx, parts, paths, progress, surface

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

    def project(self, pos, nrm=None):
        """The nearest points on the body (on their triangles' planes), their normals, and how far
        the points were from it."""
        face, _, dist = self.at(pos, nrm)
        a = self.V[self.F[face, 0]]
        n = self.fn[face]
        on = pos - ((pos - a) * n).sum(1, keepdims=True) * n
        return on, n, dist


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
        d, i = tree.query(pos, k=k, workers=-1)
        pick = np.zeros(len(pos), np.int64)
        if nrm is not None:
            agree = (self.fn[self._sf[i]] * nrm[:, None, :]).sum(2) > 0.2
            first = np.argmax(agree, axis=1)
            pick = np.where(agree.any(1), first, 0)
        r = np.arange(len(pos))
        s = i[r, pick]
        out = (self._sf[s], self._sb[s], d[r, pick])
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



# ---- the car in words, for the AI (car/anatomy.md) ----

ANATOMY_MD = paths.REPO / "car" / "anatomy.md"
STATIONS = ((212, "the nose's tip"), (190, "the nose, over the front wing"), (178, "the front wheels' axle"),
            (150, "the nose"), (130, "the nose fin's plate"), (110, "the bonnet"), (85, "the cockpit opening's front"),
            (60, "the front flank"), (30, "the front flank, the sidepods begin"), (0, "the sidepods, their inlets"),
            (-30, "the sidepods"), (-60, "the sidepods' back, the number panel"), (-90, "the deck, the engine cover panel"),
            (-120, "the rear wheels' axle"), (-140, "the tail"), (-158, "the tail's end"))
LINE_LEAST = 80.0   # cm: a line of the model's this long is in the anatomy (a rounded edge: its longest line)
PANEL_LEAST = 500.0  # cm2: a panel of the model's this big is in the anatomy
CORNER = 3.0        # cm: a line is told by its corners, where it strays this far from running straight
TURN_SAID = 15.0    # degrees: a corner that turns less isn't said
ROOM_LEAST = 12.0   # cm across: a flat room this big is in the anatomy


def _corners(p, tol):
    """The indices of a polyline's corners: where it strays more than tol cm from a straight run
    (Douglas and Peucker), its ends included."""
    a, b = p[0], p[-1]
    ab = b - a
    d = (np.linalg.norm(np.cross(p - a, ab), axis=1) / np.linalg.norm(ab) if np.linalg.norm(ab) > 1e-9
         else np.linalg.norm(p - a, axis=1))
    k = int(d.argmax())
    if len(p) < 3 or d[k] <= tol:
        return [0, len(p) - 1]
    return _corners(p[:k + 1], tol)[:-1] + [i + k for i in _corners(p[k:], tol)]


def _outside(L):
    """A line of the model's on the outer body's left half or middle: not on the wheel covers, not facing the ground."""
    return (L["parts"][0] not in WHEEL_COVERS and float(np.median(L["pts"][:, 0])) >= -0.5
            and float(np.mean(L["nrm"][:, 1] < -0.5)) < 0.5)


def _way(p):
    """A line's way in words: from its first point through the corners where it turns to its last."""
    corners = _corners(p, CORNER)
    legs = np.diff(p[corners], axis=0)
    cos = (legs[:-1] * legs[1:]).sum(1) / np.maximum(np.linalg.norm(legs[:-1], axis=1) * np.linalg.norm(legs[1:], axis=1), 1e-9)
    turns = np.degrees(np.arccos(np.clip(cos, -1, 1)))
    way = [_cm(p[corners[0]])] + [_cm(p[k]) + f" turning {t:.0f}°" for k, t in zip(corners[1:-1], turns) if t >= TURN_SAID]
    return " → ".join(way + [_cm(p[corners[-1]])])


def _model_lines():
    """The anatomy's section on the model's own lines (tool/meshlines.py): its crisp lines and edges, its rounded
    edges and its panels, the left side and the middle."""
    from tool import meshlines
    A = ["## How the body is built", "",
         "The model's own lines, read off its triangles (`tool/meshlines.py`): exact on the car and on the flat texture "
         "alike. The Lab's UV map room draws them (Template), its Mesh button lays them over any car, and "
         "`car/map/model.jpg` is the same on the bare body: the model's triangles grey, orange where the body rolls "
         "outward across them, violet where it dips in, its crisp lines yellow, red where the body ends, blue where the "
         "flat texture is cut. The left side and the middle (the right mirrors the left); every line and panel, with "
         "a point on each: `PY -m tool.meshlines`.", "",
         "### Its crisp lines and edges", "",
         f"Panel lines, crisp folds and where the body ends, {LINE_LEAST:.0f} cm or longer, the longest first. A marking "
         "along one: `meshlines.line(point)`, the point given.", ""]
    words = lambda L: ("where the body ends" if L["kind"] == "opening" else
                       f"a panel line, a groove of {L['walls']}" if L["walls"] > 1 else "a crisp line")
    for L in meshlines.lines("Skin"):
        if L["length"] < LINE_LEAST:
            break
        if not _outside(L):
            continue
        p, at = L["pts"], L["pts"][len(L["pts"]) // 2]
        run = (f"round, z {p[:, 2].max():.0f} to {p[:, 2].min():.0f}" if L["closed"] else
               _way(p if p[0, 2] >= p[-1, 2] else p[::-1]))
        A.append(f"- **{words(L)}**, {L['length']:.0f} cm, along the {_listed(L['parts'][:3])}, at {_cm(at)}: {run}.")
    A += ["", "### Its rounded edges", "",
          "Where the body rolls from facing one way to another, the model's lines run side by side across the roll, one "
          f"every 1 to 2 cm, each facing its own way (degrees from facing up). Those {LINE_LEAST:.0f} cm or longer, the "
          "longest first. A marking along one: `meshlines.line(point, kind=\"rounded\")`, the point given; along "
          "several end to end, or across: `meshlines.picked(points)`.", ""]
    for g in meshlines.rolls("Skin"):
        if max(L["length"] for L in g) < LINE_LEAST:
            break
        g = [L for L in g if _outside(L)]
        if not g:
            continue
        long = max(g, key=lambda L: L["length"])
        p = long["pts"] if long["pts"][0, 2] >= long["pts"][-1, 2] else long["pts"][::-1]
        across = "; ".join(f"{L['tilt']:.0f}° at {_cm(L['pts'][len(L['pts']) // 2])}" for L in g)
        many = f"{len(g)} lines across it, facing" if len(g) > 1 else "One line, facing"
        A.append(f"- {long['length']:.0f} cm along the {_listed(long['parts'][:3])}: {_way(p)}. {many} {across}.")
    A += ["", "### Its panels", "",
          f"The model's own panels, bounded by its crisp lines and edges, {PANEL_LEAST:.0f} cm² or more, the biggest "
          "first. A colour filling one right up to its lines: `meshlines.panel(point)`, the point given.", "",
          "| panel | cm² | a point |", "|---|---|---|"]
    twins = {}  # a panel and its mirror image, as alike as two panels are: the left one's point
    for area, at, parts in meshlines.panels("Skin", PANEL_LEAST):
        if parts[0] not in WHEEL_COVERS:
            twins.setdefault((round(area), parts[0]), []).append((area, at, parts))
    for pair in twins.values():
        area, at, parts = max(pair, key=lambda r: r[1][0])
        A.append(f"| {_listed(parts[:2])} | {area:.0f} | {_cm(at)} |")
    return A + [""]


def _cm(p):
    return "(" + ", ".join(str(round(float(v)) + 0) for v in p) + ")"


def _listed(words):
    words = list(words)
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]


def _faces(n):
    """Which way a surface faces, in words: its leading directions, the left side's."""
    ways = (("out", n[0]), ("in", -n[0]), ("up", n[1]), ("down", -n[1]), ("forward", n[2]), ("back", -n[2]))
    big = sorted((w for w in ways if w[1] >= 0.35), key=lambda w: -w[1])
    return _listed([w for w, _ in big if w != "in" and not (w in ("forward", "back") and abs(n[2]) < 0.35)] or ["out"])


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
    """car/anatomy.md, the car in one page for Claude to read before a design: every number comes from the
    model and the map, so it's redone with them."""
    import datetime
    from tool import checks, marks, pieces as pieces_mod
    m = m or load()
    names = np.array([inst["name"] for inst in parts.load().instances])
    plist, nm = pieces_mod.write()
    pname = names[m.part]
    zr = lambda name: (lambda z: f"z {z.min():.0f} to {z.max():.0f}")(m.V[m.F[pname == name]][..., 2])

    A = ["# The car's anatomy", "",
         f"Written by `python -m tool.carmap --describe` from the car's own shape ({datetime.date.today()}): how the "
         "body is built, where it's calm and where a graphic stops. Read it before a design, and "
         "follow these lines and rooms where the idea needs them, never by rule. Lengths in cm: x out to the car's "
         "left (the right mirrors it), y up from the ground, z forward (the nose's tip at 215, the tail at -162).", ""]
    A += _model_lines()
    A += ["## Where it's calm", "",
          f"The flat rooms: on each panel the biggest discs of skin that face within {marks.WORD_BEND:.0f} degrees of "
          f"one way, off its creases and clear of the game's panels, {ROOM_LEAST:.0f} cm across or more: where a "
          "badge, words or a picture lie flat (the left side; the right mirrors it).", "",
          "| panel | across, cm | centre | faces |", "|---|---|---|---|"]
    big = {n: m.area[pname == n].sum() for n in np.unique(pname)}  # the panels, the biggest first
    order = [n for n in sorted(big, key=lambda n: -big[n]) if big[n] >= 50]
    for name, found in sorted(marks.rooms([n for n in order if n not in checks.PANELS], ROOM_LEAST).items(),
                              key=lambda kv: -kv[1][0][0]):
        for across, centre, facing in found:
            if facing[1] < -0.5:
                continue  # under the car
            A.append(f"| {name} | {across:.0f} | {_cm(centre)} | {_faces(facing)} |")
    A += ["", "## Where a graphic stops", ""]
    seen, own, sewn = set(), [], []
    for q in plist[1:]:
        key = tuple(q["parts"])
        if key in seen:
            continue
        seen.add(key)
        twin = sum(tuple(o["parts"]) == key for o in plist) > 1
        what = f"the {_listed(q['parts'])}" + (" (each side)" if twin else "")
        (sewn if q["gap_cm"] is not None and q["gap_cm"] <= checks.SEAM else own).append(f"{what}, {q['gap_cm']:.2g} cm")
    cockpit = next((g for g in _opening_groups(m) if np.bincount(g["parts"]).argmax() in
                    [i for i, n in enumerate(names) if n == "cockpit surround"]), None)
    A += [f"- One skin, sewn, over most of the body: the {_listed(plist[0]['parts'])}. A band or a line runs on across "
          "the seams between them.",
          f"- Pieces of their own, a gap of more than {checks.SEAM:.0f} cm round them: {'; '.join(own)}. A line stops "
          "there, as a wrap would.",
          f"- Pieces sewn on, {checks.SEAM:.0f} cm or less from the skin: {'; '.join(sewn)}. A line may run on.",
          "- A graphic laid whole (a badge, words, a picture) stays on one piece, and off a fold."]
    if cockpit is not None:
        c = cockpit["pts"]
        A.append(f"- The cockpit leaves no skin down the top's middle from z {c[:, 2].max():.0f} to {c[:, 2].min():.0f}, "
                 f"{c[:, 0].max():.0f} cm out each side.")
    lettered = [p for p, words in checks.PANELS.items() if "letters" in words]
    A += [f"- Keep clear: {_listed(f'the {p} ({zr(p)})' for p in lettered)}, which the game letters, and "
          f"{_listed(f'{words} ({zr(p)})' for p, words in checks.PANELS.items() if p not in lettered)}: nothing on "
          f"them or within {checks.CLEAR:.0f} cm (`show` names anything there).", ""]
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
