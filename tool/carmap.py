"""The car map: the body's shape worked out once from its mesh, so every design knows the car.

Before it, each design learned the car on its own (TSC_WindTunnel's smoke lines cut the body
into sections to find where its top ends; the guides' "Learned" kept repeating the same folds,
inlets and creases). The map is built from the body's mesh (Skin_01, welded into one surface), is
cached in the work folder (`python -m tool.carmap` rebuilds it, about a minute), and answers for any
point on the car. In a design, through `tool.shapes`:

    shapes.area("top")            the top, between the shoulders ("sides", "under", "front", "back")
    shapes.outside(0.4)           the outer body: spots that see at least 40 % of the open air
    shapes.across(0, 0.3)         a band the same share of the way across the top all along the car
    shapes.along(0.2, 0.4)        a band 20 % to 40 % of the way from the nose to the tail
    shapes.line("shoulder", 1.5)  a line 1.5 cm wide along one of the car's lines (LINES)
    shapes.near("opening", 3)     within 3 cm of one of them (to keep a graphic clear, use ~)

Layers (per welded vertex of the body):
    open     how much of the open air a spot sees, 0 (inside an inlet, under a panel) to 1 (the top
             of the sidepod): the cosine-weighted share of 200 directions it's seen from, with the
             inner car in the way and the wheels and glass not
    across   where a spot sits round the car's section at its length: 0 the top's middle, 1 the
             shoulder (where the top turns down into the side), 2 the lower edge (where the side
             turns under), 3 the underside's middle. The shoulder and the lower edge are found on
             each 1 cm slice's outline and smoothed along the car; between them a spot's across is
             how far out it is (over the top, seen from above), how far down (the side, seen from
             the side) or how far in (under, seen from below), so a band of across follows the
             body's own shape and nothing steps from slice to slice. The right side mirrors the left
    along    0 at the nose's tip to 1 at the tail
    facing_x, facing_y, facing_z   the smoothed normal (x: out to the car's left, y: up, z: forward)

Lines (points along the welded body's edges, and the across layer's own edges):
    fold      where the surface bends sharply (more than 35 degrees between neighbouring triangles)
    opening   an edge with nothing beyond it: the cockpit's rim, the inlets' mouths, the arches
    join      where two named panels meet, and the edges of a loose panel lying on another
    shoulder  where the top turns into the side (across = 1)
    lower     where the side turns under (across = 2)

    python -m tool.carmap            build it and print a summary
"""

import functools

import numpy as np
from scipy.ndimage import gaussian_filter1d, median_filter
from scipy.spatial import cKDTree

from tool import fbx, parts, paths

CACHE = paths.CACHE / "carmap.npz"
VERSION = 7
N_DIRS = 200
PIXEL = 1.0      # cm, the depth maps' pixel when testing what each spot sees
SLICE = 1.0      # cm between the sections
BIN = 0.4        # degrees, the sections' angular bins
FOLD = 35.0      # degrees between neighbouring triangles for a fold
NOSE_Z, TAIL_Z = 215.0, -162.0
WHEEL_COVERS = ("wheel cover disc", "wheel cover hub", "wheel cover ring")
LINES = ("fold", "opening", "join", "shoulder", "lower")


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
    names = np.array([inst["name"] for inst in P.instances])
    return V, F.astype(np.int32), fn, part, names


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


# ---- the sections: round the car from the top's middle ----

HIDDEN = 0.2  # a section's surface that sees less of the open air than this isn't part of its outline


def _chains(V, F, open_, faces, z0):
    """The body cut at length z0: its polylines, chained through the welded mesh's shared edges, as
    lists of (points (n, 2) of x, y; each point's openness)."""
    zs = V[F[faces], 2]
    cut = faces[(zs.min(1) < z0) & (zs.max(1) > z0)]
    if len(cut) < 2:
        return []
    ends = []  # per face: the two edges it's cut on, as (vertex, vertex) keys
    for f in cut:
        a, b, c = F[f]
        es = [(i, j) for i, j in ((a, b), (b, c), (c, a)) if (V[i, 2] < z0) != (V[j, 2] < z0)]
        if len(es) == 2:
            ends.append(tuple(tuple(sorted(e)) for e in es))
    touch = {}
    for s, (e0, e1) in enumerate(ends):
        touch.setdefault(e0, []).append(s)
        touch.setdefault(e1, []).append(s)
    used = np.zeros(len(ends), bool)
    out = []
    for s0 in range(len(ends)):
        if used[s0]:
            continue
        used[s0] = True
        seq = [ends[s0][0], ends[s0][1]]
        for forward in (True, False):
            key = seq[-1] if forward else seq[0]
            while True:
                nxt = [s for s in touch.get(key, ()) if not used[s]]
                if not nxt:
                    break
                s = nxt[0]
                used[s] = True
                key = ends[s][1] if ends[s][0] == key else ends[s][0]
                if forward:
                    seq.append(key)
                else:
                    seq.insert(0, key)
        e = np.array(seq)
        a, b = V[e[:, 0]], V[e[:, 1]]
        t = (z0 - a[:, 2]) / (b[:, 2] - a[:, 2])
        p = a + t[:, None] * (b - a)
        o = open_[e[:, 0]] + t * (open_[e[:, 1]] - open_[e[:, 0]])
        out.append((p[:, :2], o))
    return out


def _outline(V, F, open_, faces, z0):
    """The left half of the body's outline at length z0, walked from the top's middle out, round the
    shoulder, down the side and under: the section's open surface (its hidden stretches, the insides
    of inlets and panels lying under others, left out), each stretch in order of where it starts
    round the section, the gaps between them bridged. Returns (points (n, 2), girth (n,) in cm from
    the middle line, bridge (n,): the step before each point crosses a gap), or None."""
    parts = []
    for p, o in _chains(V, F, open_, faces, z0):
        keep = (o >= HIDDEN) & (p[:, 0] > -0.3)
        # split into runs of kept points
        idx = np.flatnonzero(keep)
        if not len(idx):
            continue
        breaks = np.flatnonzero(np.diff(idx) > 1)
        for run in np.split(idx, breaks + 1):
            if len(run) < 2:
                continue
            q = p[run]
            parts.append(q)
    if not parts:
        return None
    allp = np.concatenate(parts)
    yc = 0.5 * (allp[:, 1].min() + allp[:, 1].max())
    ang = lambda q: np.degrees(np.arctan2(np.maximum(q[:, 0], 0), q[:, 1] - yc))  # 0 up, 180 down
    runs = []
    for q in parts:
        a = ang(q)
        if a[-1] < a[0]:
            q, a = q[::-1], a[::-1]
        runs.append((a.min(), a.max(), np.hypot(q[:, 0], q[:, 1] - yc).mean(), q))
    runs.sort(key=lambda r: r[0])
    # a stretch lying under another (inside its angles, nearer the middle) is a panel under a panel
    kept = []
    for lo, hi, rad, q in runs:
        if any(lo >= klo - 0.5 and hi <= khi + 0.5 and rad < krad - 0.5 for klo, khi, krad, _ in kept):
            continue
        kept.append((lo, hi, rad, q))
    pts, bridge = [], []
    for i, (_, _, _, q) in enumerate(kept):
        pts.append(q)
        bridge.append(np.r_[i > 0, np.zeros(len(q) - 1, bool)])
    q = np.concatenate(pts)
    bridge = np.concatenate(bridge)
    step = np.linalg.norm(np.diff(q, axis=0), axis=1)
    g = np.r_[max(q[0, 0], 0.0), max(q[0, 0], 0.0) + np.cumsum(step)]
    return q, g, bridge


def _marks(q, g, bridge):
    """Along an outline: the girth where the top turns down into the side (the shoulder) and where
    the side turns under (the lower edge), read from the outline's own direction smoothed over about
    2 cm, over its surface only (never a bridged gap).

    The shoulder: the first turn past 50 degrees from facing up that lasts 2 cm (a seam's lip doesn't),
    or where the top's surface ends and the outline carries on lower down (the body stops there and
    the inner car takes over), whichever comes first. The lower edge: where the side turns under for
    good, the first turn past 125 degrees after which the outline faces out for less than 6 cm more
    (so a lip's underside, with the flank carrying on below it, isn't taken)."""
    grid = np.arange(g[0], g[-1], 0.25)
    if len(grid) < 8:
        return g[-1], g[-1]
    x = gaussian_filter1d(np.interp(grid, g, q[:, 0]), 4)
    y = gaussian_filter1d(np.interp(grid, g, q[:, 1]), 4)
    tx, ty = np.gradient(x), np.gradient(y)
    nx, ny = -ty, tx  # walking out and down from the top, the outward normal is the tangent turned anticlockwise
    ang = np.degrees(np.arctan2(nx, ny))  # 0 up, 90 out, 180 down; negative: facing in
    # grid points within 1.5 cm of a bridged gap aren't surface
    near_gap = np.zeros(len(grid), bool)
    drops = []
    for i in np.flatnonzero(bridge):
        near_gap |= (grid > g[i - 1] - 1.5) & (grid < g[i] + 1.5)
        if q[i, 1] < q[i - 1, 1] - 5.0:
            drops.append(g[i - 1])
    run = int(2.0 / 0.25)

    def runs(cond, start):
        cond = cond & ~near_gap
        return [grid[i] for i in np.flatnonzero(cond & (grid >= start)) if cond[i:i + run].all()]

    turns = runs(ang > 50.0, g[0])
    shoulder = min([c for c in (turns[:1] + drops[:1])] or [g[-1]])
    side = (ang > 50.0) & (ang < 125.0) & ~near_gap
    lower = g[-1]
    for c in runs(ang > 125.0, shoulder):
        if side[grid > c].sum() * 0.25 < 6.0:
            lower = c
            break
    return shoulder, max(lower, shoulder + 0.5)


def _clean(Z, raw, window=7, jump=4.0, sigma=1.0):
    """A mark along the car: a slice's reading kept unless it strays more than `jump` cm from its
    neighbours' median (a seam's lip, a panel's edge), which takes its place; then lightly smoothed.
    Slices without a reading take their neighbours'."""
    good = np.isfinite(raw)
    arr = raw.copy()
    arr[~good] = np.interp(Z[~good], Z[good], raw[good])
    med = median_filter(arr, window, mode="nearest")
    arr = np.where(np.abs(arr - med) > jump, med, arr)
    return gaussian_filter1d(arr, sigma, mode="nearest")


def _sections(V, F, part, names, open_):
    """Every slice's outline (kept for pictures) and where its marks sit: the shoulder's and the
    lower edge's x and y, and the section's middle height, each cleaned along the car so the marks
    run as smooth lines from the nose to the tail."""
    body = ~np.isin(names[part], WHEEL_COVERS)
    faces = np.flatnonzero(body)
    Z = np.arange(TAIL_Z + SLICE / 2, NOSE_Z, SLICE)
    qs, starts = [], [0]
    raw = np.full((len(Z), 5), np.nan)  # shoulder x, y; lower x, y; the middle height
    for k, z0 in enumerate(Z):
        o = _outline(V, F, open_, faces, z0 + 1e-4)
        if o is not None:
            q, g, bridge = o
            sh, lo = _marks(q, g, bridge)
            at = lambda gg: np.array([np.interp(gg, g, q[:, 0]), np.interp(gg, g, q[:, 1])])
            # a mark in a bridged gap sits at the end of the surface before it
            i_sh = min(np.searchsorted(g, sh, side="right") - 1, len(g) - 1)
            i_lo = min(np.searchsorted(g, lo, side="right") - 1, len(g) - 1)
            raw[k, 0:2] = q[i_sh] if bridge[min(i_sh + 1, len(g) - 1)] and g[i_sh] < sh else at(sh)
            raw[k, 2:4] = q[i_lo] if bridge[min(i_lo + 1, len(g) - 1)] and g[i_lo] < lo else at(lo)
            raw[k, 4] = 0.5 * (q[:, 1].min() + q[:, 1].max())
            qs.append(q)
        starts.append(starts[-1] + (len(qs[-1]) if o is not None else 0))
    marks = {name: _clean(Z, raw[:, i]) for i, name in enumerate(("sh_x", "sh_y", "lo_x", "lo_y", "mid_y"))}
    marks["mid_y"] = _clean(Z, raw[:, 4], window=15, jump=3.0, sigma=4.0)
    return dict(Z=Z, starts=np.array(starts), q=np.concatenate(qs).astype(np.float32), **marks)


def _across(ax, y, sx, sy, lx, ly, my):
    """across from a point's place in its section (ax = |x|, y) and the section's marks: 0..1 over
    the top by how far out towards the shoulder (seen from above), 1..2 down the side by how far down
    towards the lower edge (seen from the side), 2..3 under by how far in from the lower edge (seen
    from below). Which of the three by the point's angle round the section's middle against the
    marks'. Also the scale (cm per unit of across) at the point, for crisp edges."""
    ang = np.arctan2(ax, y - my)
    a_sh = np.arctan2(sx, sy - my)
    a_lo = np.arctan2(lx, ly - my)
    s_top, s_side, s_under = np.maximum(sx, 1.0), np.maximum(sy - ly, 1.0), np.maximum(lx, 1.0)
    top = ax / s_top
    side = 1 + (sy - y) / s_side
    under = 2 + (lx - ax) / s_under
    region = np.where(ang < a_sh, 0, np.where(ang < a_lo, 1, 2))
    raw = np.choose(region, [top, side, under])
    lo_, hi_ = region.astype(np.float64), region + 1.0
    across = np.clip(raw, lo_, hi_)
    scale = np.choose(region, [s_top, s_side, s_under])
    # how far (cm) a point lies outside its region's range: a bulge past the shoulder's x above it,
    # a wheel cover; a line drawn along a mark keeps off such points
    off = np.abs(raw - across) * scale
    return across, scale, off


# ---- the car's lines ----

def _edge_lines(V, F, fn, part, spacing=0.4):
    """Points along the welded body's edges, by kind: "fold" (a bend over FOLD degrees), "opening"
    (an edge with one triangle and no surface beyond it within 1 cm), "join" (between two named
    parts, or a loose panel's edge lying on another)."""
    e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    tid = np.tile(np.arange(len(F)), 3)
    e.sort(1)
    key = e[:, 0].astype(np.int64) * len(V) + e[:, 1]
    order = np.argsort(key, kind="stable")
    key, tid, e = key[order], tid[order], e[order]
    _, start, cnt = np.unique(key, return_index=True, return_counts=True)
    ends = e[start]
    t0 = tid[start]
    t1 = np.where(cnt >= 2, tid[np.minimum(start + 1, len(tid) - 1)], -1)
    ang = np.where(t1 >= 0, np.degrees(np.arccos(np.clip((fn[t0] * fn[np.maximum(t1, 0)]).sum(1), -1, 1))), 0)
    kinds = {}
    kinds["fold"] = (cnt == 2) & (ang > FOLD) & (part[t0] == part[np.maximum(t1, 0)])
    kinds["join"] = (cnt >= 2) & (part[t0] != part[np.maximum(t1, 0)])
    single = cnt == 1
    # a single edge with another surface just beyond it (a loose panel on the shell) is a join
    mid = 0.5 * (V[ends[:, 0]] + V[ends[:, 1]])
    cen = V[F].mean(1)
    tree = cKDTree(cen)
    lying = np.zeros(len(ends), bool)
    idx = np.flatnonzero(single)
    near = tree.query_ball_point(mid[idx], 1.2, workers=-1)
    for j, (i, cand) in enumerate(zip(idx, near)):
        lying[i] = any(abs(fn[c] @ fn[t0[i]]) > 0.8 and part[c] != part[t0[i]] for c in cand)
    kinds["join"] |= single & lying
    kinds["opening"] = single & ~lying
    out = {}
    for kind, sel in kinds.items():
        a, b = V[ends[sel, 0]], V[ends[sel, 1]]
        L = np.linalg.norm(b - a, axis=1)
        k = np.maximum(1, np.ceil(L / spacing).astype(int))
        rep = np.repeat(np.arange(len(k)), k + 1)
        tt = np.concatenate([np.linspace(0, 1, n + 1) for n in k]) if len(k) else np.zeros(0)
        out[kind] = (a[rep] + tt[:, None] * (b[rep] - a[rep])).astype(np.float32)
    return out


# ---- building and loading ----

def build():
    V, F, fn, part, names = _weld()
    vn, area = _vertex_normals(V, F, fn)
    dirs = directions()
    seen = _seen(V, vn, dirs, _occluders())
    w = np.maximum(vn @ dirs.T, 0)
    open_ = (seen * w).sum(1) / np.maximum(w.sum(1), 1e-9)
    sec = _sections(V, F, part, names, open_)
    lines = _edge_lines(V, F, fn, part)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE, version=VERSION, V=V, F=F, fn=fn, part=part, vn=vn, area=area,
                        dirs=dirs, seen=np.packbits(seen, axis=1), open=open_.astype(np.float32),
                        **{f"sec_{k}": v for k, v in sec.items()},
                        **{f"line_{k}": v for k, v in lines.items()})
    load.cache_clear()
    return load()


class Map:
    def __init__(self, data):
        self.V, self.F, self.fn, self.part = data["V"], data["F"], data["fn"], data["part"]
        self.vn, self.area, self.dirs = data["vn"], data["area"], data["dirs"]
        self.seen = np.unpackbits(data["seen"], axis=1)[:, :len(self.dirs)].astype(bool)
        self.sec = {k[4:]: data[k] for k in data if k.startswith("sec_")}
        self.lines = {k[5:]: data[k] for k in data if k.startswith("line_")}
        self._tree = None
        self._last = None
        self._sec_last = None
        self._grad = {}
        self._line_trees = {}
        across, _, _ = self.section(self.V)
        self.layers = {"open": data["open"], "across": across,
                       "along": ((NOSE_Z - self.V[:, 2]) / (NOSE_Z - TAIL_Z)).astype(np.float32),
                       "facing_x": (self.vn[:, 0] * np.sign(self.V[:, 0] + 1e-9)).astype(np.float32),
                       "facing_y": self.vn[:, 1].astype(np.float32), "facing_z": self.vn[:, 2].astype(np.float32)}

    # ---- round the section ----

    def _marks_at(self, z):
        Z = self.sec["Z"]
        return [np.interp(z, Z, self.sec[k]) for k in ("sh_x", "sh_y", "lo_x", "lo_y", "mid_y")]

    def section(self, pos):
        """Where points sit round the car's section: across (0 the top's middle, 1 the shoulder, 2
        the lower edge, 3 under: see _across) and the scale there (cm per unit of across)."""
        pos = np.asarray(pos, np.float64)
        key = (pos.shape, pos[:1].tobytes(), pos[-1:].tobytes())
        if self._sec_last is not None and self._sec_last[0] == key:
            return self._sec_last[1]
        out = tuple(v.astype(np.float32) for v in _across(np.abs(pos[:, 0]), pos[:, 1], *self._marks_at(pos[:, 2])))
        self._sec_last = (key, out)
        return out

    def across_level(self, pos, a):
        """Signed distance (cm, roughly, round the section) from the points to where across = a:
        positive past it (further round from the top's middle)."""
        across, scale, _ = self.section(pos)
        return ((across - a) * scale).astype(np.float32)

    def mark_distance(self, pos, a):
        """Distance (cm) from the points to a mark (across = 1, the shoulder; 2, the lower edge),
        counting how far a point lies outside its region's range, so a bulge isn't on the line."""
        across, scale, off = self.section(pos)
        return np.hypot((across - a) * scale, off).astype(np.float32)

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

    def distance(self, kind, pos):
        """Distance (cm) from the points to the nearest of one of the car's lines (fold, opening, join);
        the right side's copy of each line comes from the model itself."""
        if kind not in self._line_trees:
            self._line_trees[kind] = cKDTree(self.lines[kind])
        d, _ = self._line_trees[kind].query(np.asarray(pos, np.float64), workers=-1)
        return d.astype(np.float32)


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
    a = m.layers["across"]
    print("across: top {:.0%}, sides {:.0%}, under {:.0%} of the vertices".format(
        np.mean(a < 1), np.mean((a >= 1) & (a < 2)), np.mean(a >= 2)))
    for k, v in m.lines.items():
        print(f"line {k}: {len(v)} points")
    Z = m.sec["Z"]
    for z in (200, 170, 150, 120, 100, 60, 20, -20, -60, -100, -140):
        i = int(np.argmin(np.abs(Z - z)))
        print(f"  z {z:5.0f}: shoulder at x {m.sec['sh_x'][i]:5.1f} y {m.sec['sh_y'][i]:5.1f}, lower edge at x {m.sec['lo_x'][i]:5.1f} y {m.sec['lo_y'][i]:5.1f}")
