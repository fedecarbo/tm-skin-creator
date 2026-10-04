"""The car map: the body's shape worked out once from its mesh, so every design knows the car.

The map is built from the body's mesh (Skin_01, welded into one surface), is
cached in the work folder (`python -m tool.carmap` rebuilds it, about a minute), and answers for any
point on the car. In a design, through `tool.shapes`:

    shapes.area("top")            the top, between the shoulders ("sides", "under"; the body has no front or
                                  back face: car/map.md)
    shapes.outside(0.4)           the outer body: spots that see at least 40 % of the open air
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

The air (the car driving forward into still air, so the air comes at it along -z):
    hit      how hard the oncoming air hits a spot, 0..1: how squarely it faces forward, squared
             (the Newtonian rule of high-speed flow), times how much of it the car leaves in the
             open from straight ahead (the directions within 25 degrees of forward). The nose's tip,
             the sidepods' lips and the cockpit's front rim take it; the flanks, the deck and the
             tail none
    Map.flow(pos, nrm)   which way the air runs over the surface: the oncoming air laid flat on it,
             held to slide along a wall, an opening it runs into off the surface (the cockpit's
             front rim, an inlet's mouth; not a bottom edge it runs along)
    Map.streamlines(seeds)   lines traced along the flow from seed points on the body, as smoke
             would run: shapes.streamlines(seeds, width) draws them

Lines (points along the welded body's edges, and the across layer's own edges):
    fold      the body's real design edges: of the ridges of its curvature (_trace_ridges, Map.ridges:
              every crease and rounded edge, traced end to end), those that stand out 1.5 times from
              the surface round them, each fitted as one smooth curve (_folds, Map.curves)
    opening   an edge with nothing beyond it: the cockpit's rim, the inlets' mouths, the arches
    join      where two named panels meet, and the edges of a loose panel lying on another
    shoulder  where the top turns into the side (across = 1): one smooth curve per stretch, fitted by
              least squares to its evidence, the ridges' own crossings and the mesh's own edges on each
              slice (_marks, _curves), broken only at a corner or an end, absent where the body has no
              line (sec_draw)
    lower     where the side turns under (across = 2): the same, and where the body has no crease
              there (the rear flanks roll under) the line runs where each slice's skin turns to face
              the ground, one curve from the front flank's skirt to the tail

    python -m tool.carmap            build it and print a summary
    python -m tool.carmap --check    measure its lines, stretch by stretch (tool/mapcheck.py)
"""

import functools

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.spatial import cKDTree

from tool import fbx, parts, paths, progress

CACHE = paths.CACHE / "carmap.npz"
VERSION = 16
N_DIRS = 200
PIXEL = 1.0      # cm, the depth maps' pixel when testing what each spot sees
SLICE = 1.0      # cm between the sections
FOLD = 35.0      # degrees between neighbouring triangles for a fold
NOSE_Z, TAIL_Z = 215.0, -162.0
WHEEL_COVERS = ("wheel cover disc", "wheel cover hub", "wheel cover ring")
# thin blades and struts standing off the body: not part of its outline (the nose fin, upright on its
# plate, made the top end at the car's middle over z 118 to 142; the wing's pylons under the nose were
# taken for the nose's tip, and a smoke rake started on them; the diffuser's strakes under the tail
# face sideways, and read as the side going on below the arch's rim)
BLADES = ("nose fin", "mirror mount", "wing pylon", "diffuser strake")
# the low parts a smoke rake doesn't start on: the ledges and the underside's
LOW_PARTS = ("side skirt", "diffuser", "diffuser strake", "wing pylon")
LINES = ("fold", "opening", "join", "shoulder", "lower")
FRONT_CONE = 25.0  # degrees round forward from which a spot counts as open to the oncoming air


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
    the middle line, bridge (n,): the step before each point crosses a gap: 1 over hidden skin (the
    same piece of skin carries on, out of sight), 2 over nothing (the skin ends: an open edge, the
    inner car between)), or None."""
    parts = []
    for c, (p, o) in enumerate(_chains(V, F, open_, faces, z0)):
        keep = (o >= HIDDEN) & (p[:, 0] > -0.3)
        # split into runs of kept points
        idx = np.flatnonzero(keep)
        if not len(idx):
            continue
        breaks = np.flatnonzero(np.diff(idx) > 1)
        for run in np.split(idx, breaks + 1):
            q = p[run]
            if len(run) < 2 or np.linalg.norm(np.diff(q, axis=0), axis=1).sum() < 2.0:
                continue  # a stub under 2 cm: the slice cutting a seam's lip or a slot's wall, not a stretch of skin
            parts.append((q, c))
    if not parts:
        return None
    allp = np.concatenate([q for q, _ in parts])
    yc = 0.5 * (allp[:, 1].min() + allp[:, 1].max())
    ang = lambda q: np.degrees(np.arctan2(np.maximum(q[:, 0], 0), q[:, 1] - yc))  # 0 up, 180 down
    runs = []
    for q, c in parts:
        a = ang(q)
        if a[-1] < a[0]:
            q, a = q[::-1], a[::-1]
        runs.append((a.min(), a.max(), np.hypot(q[:, 0], q[:, 1] - yc).mean(), q, c))
    runs.sort(key=lambda r: r[0])
    # a stretch lying under another (inside its angles, nearer the middle) is a panel under a panel
    kept = []
    for lo, hi, rad, q, c in runs:
        if any(lo >= klo - 0.5 and hi <= khi + 0.5 and rad < krad - 0.5 for klo, khi, krad, _, _ in kept):
            continue
        kept.append((lo, hi, rad, q, c))
    pts, bridge = [], []
    for i, (_, _, _, q, c) in enumerate(kept):
        pts.append(q)
        first = 0 if i == 0 else 1 if c == kept[i - 1][4] else 2
        bridge.append(np.r_[first, np.zeros(len(q) - 1, np.int8)])
    q = np.concatenate(pts)
    bridge = np.concatenate(bridge)
    step = np.linalg.norm(np.diff(q, axis=0), axis=1)
    g = np.r_[max(q[0, 0], 0.0), max(q[0, 0], 0.0) + np.cumsum(step)]
    return q, g, bridge


def _dense(q, g, bridge, step=0.25):
    """An outline every `step` cm along its surface: points, girth, and per point the gap that
    begins after it (0 none; 1 over hidden skin; 2 over nothing: _outline), a bridged gap of 2 cm
    or more (a smaller one, a slot's edge or a seam's shadow, is crossed as surface)."""
    dq, dg, gap = [], [], []
    for i in range(len(q) - 1):
        if bridge[i + 1] and np.linalg.norm(q[i + 1] - q[i]) >= 2.0:
            gap[-1][-1] = bridge[i + 1]
            continue
        n = max(1, int(np.ceil((g[i + 1] - g[i]) / step)))
        s = np.arange(n) / n
        dq.append(q[i] + s[:, None] * (q[i + 1] - q[i]))
        dg.append(g[i] + s * (g[i + 1] - g[i]))
        gap.append(np.zeros(n, np.int8))
    dq.append(q[-1:])
    dg.append(g[-1:])
    gap.append(np.zeros(1, np.int8))
    return np.concatenate(dq), np.concatenate(dg), np.concatenate(gap)


def _angle(q, gap, sigma=4):
    """The outline's facing at each dense point, degrees: 0 up, 90 out, 180 down, negative in;
    smoothed over about 2 cm within each stretch of surface."""
    ang = np.zeros(len(q))
    for run in np.split(np.arange(len(q)), np.flatnonzero(gap > 0) + 1):
        if len(run) < 3:
            continue
        x = gaussian_filter1d(q[run, 0], sigma, mode="nearest")
        y = gaussian_filter1d(q[run, 1], sigma, mode="nearest")
        tx, ty = np.gradient(x), np.gradient(y)
        ang[run] = np.degrees(np.arctan2(-ty, tx))  # the outward normal: the tangent turned anticlockwise
    return ang


SIDE = 50.0    # degrees from facing up: the surface is a side from here, and faces the ground from 180 - SIDE
FLOOR = 25.0   # cm up from the ground: the body's lowest edges (the sill's roll, 21 to 22, the splitter under the nose, 16) are below this; the arch's front rim, 29, is not
TURN = 20.0    # degrees: the least a crease turns the surface to end the top


def _marks(q, g, gap, ang, cross, slant, at_edge, k1):
    """Along a dense outline (from the top's middle out, round and under): where the shoulder and
    the lower edge sit, each on one of the car's ridges where the outline crosses one (cross: the
    indices of the crossings; slant: per crossing, how much the ridge runs along the car there,
    |dz/ds|: under 0.5 it runs across the slices, a corner or the tail's edge, and can't be either
    line), read with the outline's facing (ang, degrees from up). Each slice is read on its own;
    _sections then repairs a slice against its neighbours (_repair).

    The shoulder: where the top ends. Where the top's own stretch of skin runs out before its facing
    passes SIDE degrees (over the sidepods' fronts and along the inlets' rims, z 30 to -9: the skin
    stops at the rim, an inner part), the shoulder is that open edge, the mesh's own, one continuous
    curve (kind 4). Otherwise the surface becomes a side where its facing first passes SIDE
    degrees and stays there 3 cm; the shoulder is the ridge up to 4 cm past that point that turns
    the surface most (its facing 2 to 6 cm after against 2 to 6 cm before, at least TURN degrees):
    the nose's crease (a 35 degree turn, though the flank below it runs at 45 degrees and only
    passes SIDE near the lip), the sidepod's outer top edge (85 degrees; the deck's soft inner
    crease before it turns the other way), the lip at the nose's tip, where there is no crease; or
    the ridge within 2 cm of that point when the turn can't be read (the inlet rim's crease, with
    the rim's lip ending in a gap 2 cm on); or, if none, the point itself (no crease there: the
    surface just curls), or, if earlier, where the top's surface ends and the outline carries on
    lower down (the sidepod's front, the inner car). The lower edge: where the side turns under:
    on the skin contiguous with the shoulder (its stretches chained through gaps over hidden skin,
    or over nothing under 4 cm: a slot), the turn where its skin comes to face the ground (turn:
    within SIDE degrees of straight down, and from there on; the sill under the sidepod's slot,
    facing out at 95 to 118 degrees, is still the side, and the body turns under at its roll), or
    the chain's end where it goes hidden facing down. There, the skin's own end at the floor on
    the mesh's boundary (kind 4: the splitter under the nose's tip), or the crest it turns under
    at (crest: a ridge crossing, kind 0, or the bend's own crest, kind 5: the lip, with the nose's
    belly under it and the skirt another piece of skin further down; the skirt's crest along the
    front flank; the sill's roll along the sidepods; the diffuser's edge at the tail corner), or
    the turn itself, with no crease (kind 2: the rear flanks). A chain ending above the floor
    still facing out, or at an opening's edge, holds no lower edge (the top's skin at the inlet's
    rim; the flank at the arch's front): the next chain down is read. If no chain qualifies, the
    first chain's end (kind 1). Returns (shoulder index, lower index, kinds, turn index): a kind
    per mark, 0 a ridge, 1 the skin's end, 2 a turn with no ridge, 3 a ridge under which the skin
    ends and the outline carries on lower down (the lip: the inner car shows below, the skirt
    further down), 4 the skin's own edge, 5 a roll's crest."""
    n = len(q)
    if n < 8:
        return n - 1, n - 1, (1, 1)
    ends = np.flatnonzero(gap > 0)  # the last point of each stretch but the last
    along = [c for c, t in zip(cross, slant) if t >= 0.5]

    def stretch_end(i):
        e = ends[ends >= i]
        return int(e[0]) if len(e) else n - 1

    def chain_end(i):
        """The end of the skin contiguous with point i: on through gaps over hidden skin, or over
        nothing under 4 cm (a slot: the sidepod's bottom edge over the sill; not the wheel
        pocket's wall 5 cm in from the nose's lip)."""
        e = stretch_end(i)
        while e < n - 1 and (gap[e] == 1 or np.linalg.norm(q[e + 1] - q[e]) < 4.0):
            e = stretch_end(e + 1)
        return e

    def mean_between(i, c0, c1):
        """The mean facing from c0 to c1 cm after point i, within its stretch."""
        j0, j1 = i + int(c0 / 0.25), min(i + int(c1 / 0.25), stretch_end(i))
        if j1 <= j0 + 3:
            return np.nan
        return ang[j0:j1 + 1].mean()

    run = 12  # 3 cm of points
    steep = np.array([abs(ang[i:i + run]).min() > SIDE and gap[i:i + run - 1].sum() == 0 for i in range(n - run)])
    drops = [int(e) for e in ends if q[min(e + 1, n - 1), 1] < q[e, 1] - 5.0]
    first = int(np.flatnonzero(steep)[0]) if steep.any() else n - 1

    def turn(c):
        after, before = mean_between(c, 2.0, 6.0), np.nan
        j0, j1 = max(c - int(6.0 / 0.25), 0), c - int(2.0 / 0.25)
        if j1 > j0 + 3 and not gap[j0:c].any():
            before = ang[j0:j1 + 1].mean()
        return after - before if np.isfinite(after) and np.isfinite(before) else np.nan

    top_end = stretch_end(0)
    if first >= top_end - 32 and at_edge(top_end) and top_end < n - 1 and gap[top_end] == 2:  # the top runs out of skin as it turns, over nothing, with skin on below: its open edge is the shoulder
        sh, sh_kind = top_end, 4
    else:
        turns = [(turn(c), c) for c in along if (c - first) * 0.25 <= 4.0]
        turns = [(t, c) for t, c in turns if np.isfinite(t) and t > TURN]
        near = [c for c in along if abs(c - first) * 0.25 <= 2.0]
        sh, sh_kind = (max(turns)[1], 0) if turns else (min(near, key=lambda c: abs(c - first)), 0) if near else (first, 2)
        later = [c for t, c in turns if sh < c <= sh + 32]  # a double crest, within 8 cm: the top ends at the outer one
        if later:
            sh = max(later)
        if drops and drops[0] < sh:
            sh, sh_kind = drops[0], 1
    # the pieces of skin from the shoulder on: its own, then the ones below (the sidepod's side
    # under the top's end at the rim, across the hidden inlet)
    chains, start = [], sh
    while start < n:
        e = chain_end(start)
        chains.append((start, e))
        start = e + 1
    def turn(c0, c1):
        """Where the chain's skin from c0 to c1 turns to face the ground: the point before it first
        passes within SIDE degrees of straight down (tilted out or in) and stays within 10 degrees
        of that for 2 cm, after which the skin never faces up again for 2 cm (under the front
        flank the belly folds back into the skirt's shelf: the body turns under at the skirt's
        crest below; skin facing sideways after the ground, the wheel pocket's wall, is a cavity's,
        not the side going on); the chain's end if it never does (the sill, hidden below)."""
        a = np.abs(ang[c0:c1 + 1])
        down = a >= 180.0 - SIDE
        for t in np.flatnonzero(down[1:] & ~down[:-1]) + 1:
            if (a[t:t + 8] >= 170.0 - SIDE).all() and (a[t:] < 60.0).sum() <= 8:
                return c0 + int(t) - 1
        return c1

    def crest(c0, c1, t):
        """The crest the skin turns under at: the last ridge crossing within 3 cm before t or 2 cm
        after it (kind 0; the lip's crease sits 2 to 3 cm above where its belly faces the ground),
        or the crest of the bend by the curvature within 2 cm, the local maximum nearest t (kind
        5, between the samples)."""
        hi = min(t + 8, c1)
        cs = [c for c in along if max(c0, sh) <= c <= hi and t - c <= 12 and (c == sh or c > sh + 2)
              and 45.0 <= np.median(ang[c:c + 5]) <= 150.0]
        if cs:
            return cs[-1], 0
        if k1 is None:
            return None, None
        lo_ = max(t - 8, c0)
        w = k1[lo_:hi + 1]
        peaks = [j for j in range(1, len(w) - 1) if w[j] >= w[j - 1] and w[j] >= w[j + 1] and w[j] >= RIDGE_END]
        if not peaks:
            return None, None
        j = min(peaks, key=lambda j: abs(lo_ + j - t))
        a, b, c = w[j - 1], w[j], w[j + 1]
        d = a - 2 * b + c
        return lo_ + j + (float(np.clip(0.5 * (a - c) / d, -0.5, 0.5)) if abs(d) > 1e-9 else 0.0), 5

    lo, lo_kind, lo_turn = chains[0][1], 1, chains[0][1]
    for c0, c1 in chains:
        t = turn(c0, c1)
        if t == c1 and not (q[c1, 1] < FLOOR or (abs(ang[c1]) >= 160.0 - SIDE and not at_edge(c1))):
            continue  # a chain ending above the floor facing out or up, or at an opening's edge (the top's skin at the inlet's rim, the flank at the arch's front)
        lo, lo_kind, lo_turn = t, 2, t
        # the skin's own end at the floor, within 2 cm of the turn: the chain's end, or a stretch's
        # end over nothing, on the mesh's boundary (within 1 cm: the diffuser plate's edge lies 2 cm
        # in from the flank's end under the arch, which tucks under it)
        edge = [i for i in range(max(t - 8, c0), min(t + 8, c1) + 1)
                if q[i, 1] < FLOOR and q[i, 0] > 1.0 and at_edge(i, 1.0) and (i == c1 or gap[i] == 2)]
        if edge:
            lo, lo_kind = edge[0], 4
            break
        c, kind = crest(c0, c1, t)
        if c is not None:
            lo, lo_kind = c, kind
            if kind == 0 and c1 < n - 1 and q[c1 + 1, 1] < q[c1, 1] - 5.0:
                lo_kind = 3
        break
    if sh_kind == 1 and at_edge(sh):
        sh_kind = 4  # the top's end is the skin's own open edge (over the sidepod's front): exact
    return sh, lo, (sh_kind, lo_kind), lo_turn


def _in_plane(pts, i, z0, fallback):
    """Where the ridge through its resampled point i crosses the plane z = z0: the point between
    the two neighbours straddling it (so a mark is the ridge's own point, not the outline's nearest
    sample, quantised to 0.25 cm); the outline's point if the ridge only touches the plane."""
    for k in range(max(i - 4, 0), min(i + 4, len(pts) - 1)):
        a, b = pts[k], pts[k + 1]
        if np.linalg.norm(b - a) < 0.6 and (a[2] - z0) * (b[2] - z0) <= 0 and a[2] != b[2]:
            t = (z0 - a[2]) / (b[2] - a[2])
            return (a + t * (b - a))[:2]
    return fallback


def _repair(raw, marks_g, kind, crossings, reach=2.0, rounds=2):
    """A run of up to three slices whose marks sit away from both flanking slices' (over `reach`
    cm) while those agree with each other takes, on each slice, the crossing nearest the flanking
    marks' mean, if one lies within reach (or, for a run of one or two slices between two on the
    same ridge, the point between the flanking marks: the ridge's crossing missing on a slice): a
    slice that read a ridge crossing its line (the deck's crease across the rear flank's shoulder),
    or missed its own, doesn't flip the line."""
    n = len(raw)
    for _ in range(rounds):
        for j in range(2):
            for L in (1, 2, 3):
                for k in range(1, n - L):
                    a, b = raw[k - 1, 2 * j:2 * j + 2], raw[k + L, 2 * j:2 * j + 2]
                    if not (np.isfinite(a).all() and np.isfinite(b).all()) or np.hypot(*(a - b)) > reach:
                        continue
                    run = [raw[i, 2 * j:2 * j + 2] for i in range(k, k + L)]
                    if any(np.hypot(*(c - a)) <= reach or np.hypot(*(c - b)) <= reach for c in run):
                        continue
                    if kind[k - 1, j] == 4 and kind[k + L, j] == 4 and all(kind[i, j] == 4 for i in range(k, k + L)):
                        continue  # marks on the skin's own edge are exact: a notch in the boundary is the body's own
                    mid = 0.5 * (a + b)
                    picks = []
                    for i in range(k, k + L):
                        if i not in crossings or not len(crossings[i][0]):
                            break
                        q, g = crossings[i]
                        d = np.hypot(*(q - mid).T)
                        if d.min() > reach:
                            break
                        picks.append((i, int(d.argmin())))
                    if len(picks) < L:
                        if L <= 2 and kind[k - 1, j] == kind[k + L, j] and kind[k - 1, j] in (0, 3, 4, 5):
                            for i in range(k, k + L):  # a ridge's crossing missing on a slice or two: between its neighbours
                                t = (i - (k - 1)) / (L + 1)
                                raw[i, 2 * j:2 * j + 2] = a + t * (b - a)
                                marks_g[i, j] = marks_g[k - 1, j] + t * (marks_g[k + L, j] - marks_g[k - 1, j])
                                kind[i, j] = kind[k - 1, j]
                        continue
                    for i, ii in picks:
                        q, g = crossings[i]
                        raw[i, 2 * j:2 * j + 2], marks_g[i, j], kind[i, j] = q[ii], g[ii], kind[k - 1, j]


def _clean(Z, raw):
    """A mark along the car: every slice's own reading, on its ridge (never blended along the car:
    a median or a smoothing put the line between two ridges, on neither); slices without a
    reading take their neighbours'."""
    good = np.isfinite(raw)
    arr = raw.copy()
    arr[~good] = np.interp(Z[~good], Z[good], raw[good])
    return arr


def _sections(V, F, part, names, open_, ridge_pts, edge_pts, k1_at=None):
    """Every slice's outline (kept for pictures, every 0.25 cm) and where its marks sit: the
    shoulder's and the lower edge's x and y (on the ridges the outline crosses: _marks; a mark on
    the skin's own edge, kind 4, moved onto the mesh's boundary itself, edge_pts, within 2 cm: the
    outline is cut where the skin stops being seen, a cm or two short of the edge and unevenly),
    each cleaned along the car, each mark's kind per slice, and where the slice's skin turns to
    face the ground (turn_x, turn_y: the lower edge where the body has no crease)."""
    body = ~np.isin(names[part], WHEEL_COVERS + BLADES)
    faces = np.flatnonzero(body)
    Z = np.arange(TAIL_Z + SLICE / 2, NOSE_Z, SLICE)
    tree = cKDTree(ridge_pts)
    tan = np.gradient(ridge_pts.astype(np.float64), axis=0)
    slant_all = np.abs(tan[:, 2]) / np.maximum(np.linalg.norm(tan, axis=1), 1e-9)
    qs, gs, starts = [], [], [0]
    raw = np.full((len(Z), 4), np.nan)  # shoulder x, y; lower x, y
    turn = np.full((len(Z), 2), np.nan)  # where the slice's skin turns to face the ground
    marks_g = np.full((len(Z), 2), np.inf)  # the slice's own shoulder and lower edge, as girth
    kind = np.full((len(Z), 2), 2, np.int8)  # 2: no outline
    crossings = {}
    for k, z0 in enumerate(Z):
        o = _outline(V, F, open_, faces, z0 + 1e-4)
        if o is not None:
            q, g, gap = _dense(*o)
            d, ri = tree.query(np.c_[q, np.full(len(q), z0)], workers=-1)
            hit = np.flatnonzero(d < 0.8)
            cross = [int(r[np.argmin(d[r])]) for r in np.split(hit, np.flatnonzero(np.diff(hit) > 1) + 1) if len(r)]
            exact = {c: _in_plane(ridge_pts, ri[c], z0, q[c]) for c in cross}
            near_z = edge_pts[np.abs(edge_pts[:, 2] - z0) < 0.5, :2]  # the boundary in the slice's own plane
            de = cKDTree(near_z).query(q, workers=-1)[0] if len(near_z) else np.full(len(q), np.inf)
            kk = k1_at(np.c_[q, np.full(len(q), z0)]) if k1_at else None
            sh, lo, kind[k], lt = _marks(q, g, gap, _angle(q, gap), cross, slant_all[ri[cross]], lambda i, tol=2.0: de[i] < tol, kk)
            turn[k] = q[lt]
            if kind[k, 1] == 5:  # a crest read on the slice: between the samples
                t = lo - int(lo)
                raw[k, 2:4] = q[int(lo)] + t * (q[min(int(lo) + 1, len(q) - 1)] - q[int(lo)])
                lo = int(round(lo))
            raw[k, 0:2] = exact.get(sh, q[sh])
            if kind[k, 1] != 5:
                raw[k, 2:4] = exact.get(lo, q[lo])
            marks_g[k] = g[sh], g[lo]
            if q[lt, 0] < 1.0:  # the turn at the car's middle: the side's skin is hidden on this slice (under the arch) and the chain ran on over hidden skin to the floor: no reading, the neighbours' stand in
                turn[k], raw[k, 2:4], marks_g[k, 1], kind[k, 1] = np.nan, np.nan, np.inf, 1
            crossings[k] = (np.array([exact[c] for c in cross]).reshape(-1, 2), g[cross])
            qs.append(q)
            gs.append(g)
        starts.append(starts[-1] + (len(qs[-1]) if o is not None else 0))
    _repair(raw, marks_g, kind, crossings)
    for L in (1, 2, 3):  # a run of up to three slices whose turns sit away from both flanking slices' while those agree: between them
        for k in range(1, len(Z) - L):
            a, b = turn[k - 1], turn[k + L]
            run = turn[k:k + L]
            if (np.isfinite(a).all() and np.isfinite(b).all() and np.hypot(*(a - b)) < 2.0
                    and all(min(np.hypot(*(c - a)), np.hypot(*(c - b))) > 2.0 for c in run)):
                for i in range(L):
                    turn[k + i] = a + (i + 1) / (L + 1) * (b - a)
    prev = [None, None]
    for k in range(len(Z) - 1, -1, -1):  # a mark on the skin's own edge: onto the mesh's boundary itself, from the nose back
        for j in range(2):
            if kind[k, j] == 4 and np.isfinite(raw[k, 2 * j]):
                near_z = edge_pts[np.abs(edge_pts[:, 2] - Z[k]) < 0.5, :2]  # in the slice's own plane
                if len(near_z):
                    d2 = np.hypot(*(near_z - raw[k, 2 * j:2 * j + 2]).T)
                    cand = np.flatnonzero(d2 < 2.5)
                    if len(cand):  # of the boundary points at hand, the one on the edge the line is already on
                        if prev[j] is not None:
                            dp = np.hypot(*(near_z[cand] - prev[j]).T)
                            i = cand[dp.argmin()] if dp.min() < 3.0 else cand[d2[cand].argmin()]
                        else:
                            i = cand[d2[cand].argmin()]
                        raw[k, 2 * j:2 * j + 2] = near_z[i]
                        prev[j] = near_z[i]
                        continue
            prev[j] = None
    marks = {name: _clean(Z, raw[:, i]) for i, name in enumerate(("sh_x", "sh_y", "lo_x", "lo_y"))}
    return dict(Z=Z, starts=np.array(starts), q=np.concatenate(qs).astype(np.float32),
                g=np.concatenate(gs).astype(np.float32), sh_g=marks_g[:, 0], lo_g=marks_g[:, 1],
                kind=kind, raw=raw, turn_x=_clean(Z, turn[:, 0]), turn_y=_clean(Z, turn[:, 1]), **marks)


def _across(ax, y, sx, sy, lx, ly, region):
    """across from a point's place in its section (ax = |x|, y) and the section's marks: 0..1 over
    the top by how far out towards the shoulder (seen from above), 1..2 down the side by how far down
    towards the lower edge (seen from the side), 2..3 under by how far in from the lower edge (seen
    from below). Which of the three (region 0, 1, 2) by where the point sits along its slice's
    outline against the slice's own marks. Also the scale (cm per unit of across) at the point, for crisp edges."""
    s_top, s_side, s_under = np.maximum(sx, 1.0), np.maximum(sy - ly, 1.0), np.maximum(lx, 1.0)
    top = ax / s_top
    side = 1 + (sy - y) / s_side
    under = 2 + (lx - ax) / s_under
    raw = np.choose(region, [top, side, under])
    lo_, hi_ = region.astype(np.float64), region + 1.0
    across = np.clip(raw, lo_, hi_)
    scale = np.choose(region, [s_top, s_side, s_under])
    # how far (cm) a point lies outside its region's range: a bulge past the shoulder's x above it,
    # a wheel cover; a line drawn along a mark keeps off such points
    off = np.abs(raw - across) * scale
    return across, scale, off


# ---- the car's feature lines: the ridges of its curvature ----

SMOOTH = 2.5       # cm: the normals averaged over this radius before the curvature is taken, so a
                   # rounded edge reads as one crest at its middle, not as its facets
RIDGE_SEED = 0.09  # 1/cm: a ridge is traced from crests bent at least this much (the skirt's edge under the sidepods bends 0.10)
RIDGE_END = 0.05   # 1/cm: a traced ridge ends where the bend fades below this
RIDGE_STEP = 1.0   # cm along the ridge per step
RIDGE_REACH = 2.0  # cm either side of a step the crest is looked for
RIDGE_MIN = 10.0   # cm: shorter pieces are dropped (a fastener's dimple, a facet)


def _smooth_normals(V, F, fn, vn, area, R=SMOOTH):
    """Each vertex's normal as the area-weighted mean of the triangles within R cm that face its
    way (not the inside of a thin panel or the far wall of an inlet)."""
    near = cKDTree(V[F].mean(1)).query_ball_point(V, R, workers=-1)
    out = vn.copy()
    for i, c in enumerate(near):
        c = np.array(c, int)
        ok = fn[c] @ vn[i] > 0
        if ok.any():
            out[i] = (fn[c][ok] * area[c][ok][:, None]).sum(0)
    return out / np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-12)


def _curvature(V, F, ns):
    """The curvature tensor per vertex (3 x 3, in the car's own axes): per triangle, the 2 x 2 form
    that turns each edge into the change of the normal along it (Rusinkiewicz 2004, least squares
    over the three edges), summed at the corners by area. Positive where the surface is convex."""
    p, n = V[F], ns[F]
    e = np.stack([p[:, 2] - p[:, 1], p[:, 0] - p[:, 2], p[:, 1] - p[:, 0]], 1)
    dn = np.stack([n[:, 2] - n[:, 1], n[:, 0] - n[:, 2], n[:, 1] - n[:, 0]], 1)
    t = np.cross(e[:, 0], e[:, 1])
    a2 = np.linalg.norm(t, axis=1)
    t /= np.maximum(a2, 1e-12)[:, None]
    u = e[:, 0] / np.maximum(np.linalg.norm(e[:, 0], axis=1), 1e-12)[:, None]
    v = np.cross(t, u)
    eu, ev = (e * u[:, None]).sum(2), (e * v[:, None]).sum(2)
    du, dv = (dn * u[:, None]).sum(2), (dn * v[:, None]).sum(2)
    A = np.zeros((len(F), 6, 3))
    b = np.zeros((len(F), 6))
    A[:, :3, 0], A[:, :3, 1], b[:, :3] = eu, ev, du
    A[:, 3:, 1], A[:, 3:, 2], b[:, 3:] = eu, ev, dv
    x = np.linalg.solve(np.einsum("tki,tkj->tij", A, A) + 1e-9 * np.eye(3), np.einsum("tki,tk->ti", A, b)[:, :, None])[:, :, 0]
    II = np.stack([np.stack([x[:, 0], x[:, 1]], 1), np.stack([x[:, 1], x[:, 2]], 1)], 1)
    B = np.stack([u, v], 2)
    M = np.einsum("tik,tkl,tjl->tij", B, II, B)
    w = 0.5 * a2
    Mv, wv = np.zeros((len(V), 3, 3)), np.zeros(len(V))
    for k in range(3):
        np.add.at(Mv, F[:, k], M * w[:, None, None])
        np.add.at(wv, F[:, k], w)
    return Mv / np.maximum(wv, 1e-12)[:, None, None]


def _principal(M, n):
    """From curvature tensors (m, 3, 3) and normals (m, 3): the greatest curvature k1 and its
    direction e1 (across a ridge), the least k2 and its direction e2 (along it)."""
    P = np.eye(3)[None] - n[:, :, None] * n[:, None, :]
    w, vec = np.linalg.eigh(P @ M @ P)
    # the eigenvector along the normal carries nothing: the other two are the principal ones
    jn = np.abs(np.einsum("mij,mi->mj", vec, n)).argmax(1)
    r = np.arange(len(M))
    j = np.array([[a for a in range(3) if a != k] for k in jn])
    ww = w[r[:, None], j]
    hi = ww.argmax(1)
    j1, j2 = j[r, hi], j[r, 1 - hi]
    return w[r, j1], w[r, j2], vec[r, :, j1], vec[r, :, j2]


def _trace_ridges(m):
    """Every ridge of the body's curvature as one continuous curve: from each crest (a vertex bent
    at least RIDGE_SEED, the most bent within 2 cm), a step at a time along the direction of least
    curvature, pulled back onto the crest at each step (the most bent of samples RIDGE_REACH either
    way across), until the bend fades (RIDGE_END), the line leaves the body, turns sharply or runs
    onto a wheel cover or a blade. All traced at once; then, strongest first, each cut where it runs
    within 1.5 cm of one already kept, the pieces of one ridge joined end to end (_join), short
    ones dropped, and each smoothed as a curve. Returns a list of (n, 3) arrays, points RIDGE_STEP
    apart."""
    V, k1, open_ = m.V, m.layers["k1"], m.layers["open"]
    off = np.isin(m.part_names[m.part], WHEEL_COVERS + BLADES)
    off_v = np.zeros(len(V), bool)
    off_v[m.F[off]] = True
    cand = np.flatnonzero((k1 > RIDGE_SEED) & (open_ > 0.15) & ~off_v)
    near = cKDTree(V[cand]).query_ball_point(V[cand], 2.0, workers=-1)
    seeds = cand[[i for i, c in enumerate(near) if k1[cand[i]] >= k1[cand[c]].max()]]
    ts = np.arange(-RIDGE_REACH, RIDGE_REACH + 1e-6, 0.5)

    def frame(p):
        n = m.value("ns", p)
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
        c = m.value("curv", p, n)
        M = c[:, [[0, 1, 2], [1, 3, 4], [2, 4, 5]]]
        kk, _, e1, e2 = _principal(M.astype(np.float64), n)
        return kk, e1, e2, n

    def crest(q, e1, n):
        """The points pulled across, along e1, onto the ridge they're on: the nearest local maximum
        of the bend among samples RIDGE_REACH either way (never the biggest in the window: where two
        ridges converge, the nose's crease and the lip 4 cm apart, that would jump to the stronger),
        refined by a parabola through the samples round it (the bend is linear over each triangle,
        so the sample alone would jump from vertex row to vertex row). Samples off the body (past an
        open edge: the tail's top edge, the lip) don't count; a point with no ridge under it is
        left where it is, far from any crest, and the line ends there."""
        s = q[:, None, :] + ts[None, :, None] * e1[:, None, :]
        nn = np.repeat(n, len(ts), 0)
        kk = m.value("k1", s.reshape(-1, 3), nn).reshape(len(q), len(ts)).astype(np.float64)
        on = m.project(s.reshape(-1, 3), nn)[2].reshape(len(q), len(ts)) < 0.5
        kk = np.where(on, kk, -1.0)
        mid = len(ts) // 2
        top = np.full(len(q), np.inf)
        for i in range(len(q)):
            k = kk[i]
            peaks = [j for j in range(len(ts)) if on[i, j] and k[j] >= k[max(j - 1, 0)] and k[j] >= k[min(j + 1, len(ts) - 1)]]
            if not peaks:
                continue
            j = min(peaks, key=lambda j: abs(j - mid))
            w = [a for a in range(j - 2, j + 3) if 0 <= a < len(ts) and on[i, a]]
            top[i] = ts[j]
            if len(w) >= 3:
                a, b, _ = np.polyfit(ts[w], k[w], 2)
                if a < -1e-6:
                    top[i] = np.clip(-b / (2 * a), ts[j] - 0.5, ts[j] + 0.5)
        lost = ~np.isfinite(top)
        p, nn, dist = m.project(q + np.where(lost, 0.0, top)[:, None] * e1, n)
        return p, nn, np.where(lost, 9.0, dist)

    _, e1, _, n = frame(V[seeds])
    p0, n0, _ = crest(V[seeds], e1, n)
    halves = []
    for sign in (1.0, -1.0):
        p, n = p0.copy(), n0.copy()
        d = sign * frame(p)[2]
        lines = [[q.copy()] for q in p]
        alive = np.ones(len(p), bool)
        for _ in range(int(500 / RIDGE_STEP)):
            idx = np.flatnonzero(alive)
            if not len(idx):
                break
            kk, e1, e2, nn = frame(p[idx])
            e2 *= np.sign((e2 * d[idx]).sum(1, keepdims=True) + 1e-12)
            q, nq, _ = m.project(p[idx] + RIDGE_STEP * e2, nn)
            _, e1q, _, nq = frame(q)
            q, nq, dist = crest(q, e1q, nq)
            step = q - p[idx]
            moved = np.linalg.norm(step, axis=1)
            turn = (step * d[idx]).sum(1) / np.maximum(moved, 1e-9)
            face, _, _ = m.at(q, nq)
            end = (m.value("k1", q, nq) < RIDGE_END) | (dist > 1.0) | (m.value("open", q, nq) < 0.1)
            end |= (turn < 0.5) | (moved < 0.3 * RIDGE_STEP) | off[face]
            for j, k in enumerate(idx):
                if not end[j]:
                    lines[k].append(q[j].copy())
            p[idx], n[idx], d[idx] = q, nq, step / np.maximum(moved, 1e-9)[:, None]
            alive[idx[end]] = False
        halves.append(lines)
    whole = [np.array(b[::-1] + f[1:]) for b, f in zip(halves[1], halves[0])]
    strength = [m.value("k1", l).sum() for l in whole]
    kept = []
    for i in np.argsort(strength)[::-1]:
        l = whole[i]
        far = cKDTree(np.concatenate(kept)).query(l, workers=-1)[0] > 1.5 if kept else np.ones(len(l), bool)
        for run in np.split(np.arange(len(l)), np.flatnonzero(np.diff(far.astype(int)) != 0) + 1):
            if far[run[0]] and len(run) >= 4:
                kept.append(l[run])
    out = []
    for piece in _join(kept):
        if len(piece) * RIDGE_STEP >= RIDGE_MIN:
            piece = gaussian_filter1d(piece, 2.0, axis=0, mode="nearest")
            piece, _, _ = m.project(piece, m.value("ns", piece))
            out.append(piece.astype(np.float32))
    return _symmetric(out)


def _symmetric(lines):
    """The lines made the same on both sides: the left side's (x > -1, a line across the middle
    cut there) kept, and their mirror images added for the right (the traces on the two sides
    differed by a cm or two and in where they ended; the mesh itself is mirrored to 0.2 cm)."""
    flip = np.array([-1.0, 1.0, 1.0], np.float32)
    left = []
    for l in lines:
        keep = l[:, 0] > -1.0
        for run in np.split(np.arange(len(l)), np.flatnonzero(np.diff(keep.astype(int)) != 0) + 1):
            if keep[run[0]] and len(run) * RIDGE_STEP >= RIDGE_MIN:
                left.append(l[run])
    right = [l[::-1] * flip for l in left if l[:, 0].max() > 1.0]
    return _join(left + right)


def _join(pieces, gap=4.0, agree=0.85):
    """Pieces of one ridge (traced from different seeds and cut against each other) joined end to
    end: an end within `gap` cm of another piece's end, both running the same way (cosines over
    `agree` between the last steps and the gap)."""
    pieces = [np.asarray(p, np.float64) for p in pieces]
    joined = True
    while joined:
        joined = False
        for i in range(len(pieces)):
            for j in range(len(pieces)):
                if i == j or pieces[i] is None or pieces[j] is None:
                    continue
                a, b = pieces[i], pieces[j]
                for flip in (False, True):
                    bb = b[::-1] if flip else b
                    g = bb[0] - a[-1]
                    d = np.linalg.norm(g)
                    if d > gap or d < 1e-6:
                        continue
                    da = a[-1] - a[-min(4, len(a) - 1)]
                    db = bb[min(3, len(bb) - 1)] - bb[0]
                    ok = ((da @ g) / max(np.linalg.norm(da) * d, 1e-9) > agree and
                          (db @ g) / max(np.linalg.norm(db) * d, 1e-9) > agree)
                    if ok:
                        pieces[i] = np.concatenate([a, bb])
                        pieces[j] = None
                        joined = True
                        break
                if joined:
                    break
            if joined:
                break
    return [p for p in pieces if p is not None]


def _resample(lines, spacing=0.25):
    """Points every `spacing` cm along polylines, for the distance trees."""
    out = []
    for l in lines:
        seg = np.linalg.norm(np.diff(l, axis=0), axis=1)
        s = np.r_[0, np.cumsum(seg)]
        u = np.arange(0, s[-1], spacing)
        out.append(np.stack([np.interp(u, s, l[:, k]) for k in range(3)], 1))
    return np.concatenate(out).astype(np.float32) if out else np.zeros((0, 3), np.float32)


# ---- the lines as curves: one smooth curve fitted to the evidence, not points joined up ----

KNOT = 15.0     # cm between a fitted curve's knots (more only where the evidence demands it)
FIT_MAX = 1.0   # cm: the most a curve may miss its evidence before it gets a knot there, or breaks
BRIDGE = 20     # slices of missing evidence a curve may run across, if the marks either side are close
BREAK = 3.0     # cm: a jump between neighbouring marks that is a corner or an end, not a wobble
DROP = 0.8      # cm: evidence further than this from the curve fitted to the rest is left out (a
                # second edge's points interleaved with the line's: the arch's rim against the corner's;
                # a traced ridge's crest jitters by up to 5 mm and stays in)
BLEND_GAP = 60.0   # cm: a gap between two curves of a named line no wider than this is bridged by the design line
                   # (the shoulder's 47 cm over the sidepod's front, where the measured line is a panel's edge; the lower
                   # edge's 64 cm behind the sidepods, where the body has no line, stays a break)
BLEND_KNOT = 6.0   # cm between the design line's knots
BLEND_REACH = 10.0  # cm either side of a gap that counts as the blend
BLEND_SHORT = 15.0  # cm: a gap this short is bridged whatever the ends' directions (a corner)
BLEND_TURN = 60.0   # degrees: the most the chord across a gap may turn from either curve's end for the gap to be bridged


def _lsq(t, v, knots):
    """v(t) as a cubic least-squares B-spline with interior knots `knots` (a straight polynomial
    when there are too few points for the knots)."""
    from scipy.interpolate import make_lsq_spline
    t, v = np.asarray(t, float), np.asarray(v, float)
    kept, prev = [], t[0]
    for k in knots:
        if t[0] + 1e-6 < k < t[-1] - 1e-6 and ((t >= prev) & (t < k)).any():  # a knot interval with no point makes the fit singular
            kept.append(k)
            prev = k
    knots = kept if not kept or ((t >= kept[-1]) & (t <= t[-1])).any() else kept[:-1]
    if knots and len(t) >= len(knots) + 4:
        try:
            return make_lsq_spline(t, v, np.r_[[t[0]] * 4, knots, [t[-1]] * 4], k=3)
        except ValueError:
            pass
    return np.poly1d(np.polyfit(t, v, max(1, min(3, (len(t) - 1) // 4))))  # a short run: a straight line or a gentle bend


def _fit(pts, t, knots=None):
    """One smooth curve through evidence points pts (n, 3) at parameters t (rising): each
    coordinate a cubic least-squares spline with a knot every KNOT cm (knots given, or so spaced).
    Evidence further than DROP cm from the curve fitted to the rest is left out and the curve
    refitted (up to a third of it: a second edge's points interleaved with the line's). A curve
    that then still misses a kept point by more than FIT_MAX cm gets a knot there and is
    refitted, down to a knot every 5 cm; if it still misses, the evidence has a corner: the curve
    breaks there. Returns a list of (dense points (m, 3) every 0.25 cm, residuals (n,) cm of all
    the evidence, knot count, kept (n,) whether each point was kept)."""
    t = np.asarray(t, float)
    if knots is None:
        knots = list(np.arange(t[0] + KNOT, t[-1] - KNOT / 2, KNOT))
    keep = np.ones(len(t), bool)
    while True:
        fs = [_lsq(t[keep], pts[keep, k], knots) for k in range(3)]
        res = np.linalg.norm(np.stack([f(t) for f in fs], 1) - pts, axis=1)
        far = keep & (res > DROP)
        if far.any() and (~keep).sum() + 1 <= len(t) // 3:
            keep[np.flatnonzero(far)[np.argmax(res[far])]] = False  # the worst, one at a time
            continue
        kept = np.flatnonzero(keep)
        worst = kept[int(res[kept].argmax())]
        if res[worst] <= FIT_MAX or len(t) < 8:
            break
        tw = t[worst]
        if all(abs(tw - k) > 5.0 for k in knots + [t[0], t[-1]]):
            knots = sorted(knots + [tw])
            continue
        if 4 <= worst <= len(t) - 5:  # a corner: two curves
            return _fit(pts[:worst + 1], t[:worst + 1]) + _fit(pts[worst:], t[worst:])
        break
    td = np.arange(t[0], t[-1] + 1e-9, 0.25)
    return [(np.stack([f(td) for f in fs], 1), res, len(knots), keep)]


def _runs(marks, draw):
    """The stretches of slices a curve runs over: drawn slices, a gap of up to BRIDGE slices
    bridged when the marks either side are within BREAK cm (per slice of the gap, so a 15 slice
    gap allows a 15 cm sweep: the top's edge between the lip's crease and the sidepod's front),
    broken where neighbouring marks jump BREAK cm or more (a corner, an end: the lip's crease
    giving way to the skirt's)."""
    ok = draw & np.isfinite(marks[:, 0])
    idx = np.flatnonzero(ok)
    runs, cur = [], [idx[0]] if len(idx) else []
    for i, j in zip(idx[:-1], idx[1:]):
        if j - i <= BRIDGE + 1 and np.linalg.norm(marks[j] - marks[i]) < BREAK * (j - i):
            cur.append(j)
        else:
            runs.append(cur)
            cur = [j]
    if cur:
        runs.append(cur)
    return [np.array(r) for r in runs if len(r) >= 12]  # a line is at least 12 cm long


def _curves(m, sec, edge_pts):
    """The named lines as curves: for each of the shoulder and the lower edge, the drawn marks
    (its evidence: the ridges' own crossings, the mesh's own edges) fitted run by run (_runs,
    _fit; the curve stays where it is fitted, within a millimetre of the skin its evidence lies
    on: put back on the faceted mesh it would take the facets' kinks), and the slice marks
    replaced by the curve's point there (so `across` is bounded by the curve). Where the body has
    no lower line (behind the sidepods the flank rolls under with no crease), the sides run down
    to where the slice's skin turns to face the ground. Returns the curves' data (build)."""
    Z, draw, st, q, g = sec["Z"], sec["draw"], sec["starts"], sec["q"], sec["g"]
    out = []
    for j, (kx, ky, kg) in enumerate((("sh_x", "sh_y", "sh_g"), ("lo_x", "lo_y", "lo_g"))):
        marks = np.c_[sec[kx], sec[ky], Z]
        covered = np.zeros(len(Z), bool)
        for run in _runs(marks, draw[:, j]):
            for dense, res, nk, kept in _fit(marks[run], Z[run]):
                span = int(round((dense[:, 2].max() - dense[:, 2].min()) / SLICE)) + 1
                out.append(dict(kind=j, pts=dense.astype(np.float32), res=res[kept].astype(np.float32), knots=nk,
                                gap=max(span - len(res), 0), dropped=int((~kept).sum()), contrast=0.0))
                zi = np.clip(np.rint((dense[:, 2] - Z[0]) / SLICE).astype(int), 0, len(Z) - 1)
                for k in np.unique(zi):
                    sel = zi == k
                    sec[kx][k], sec[ky][k] = dense[sel, 0].mean(), dense[sel, 1].mean()
                    covered[k] = True
        if j == 1:  # no lower line: the sides run down to where the slice's skin turns to face the ground
            for k in np.flatnonzero(~covered):
                sec[kx][k], sec[ky][k] = sec["turn_x"][k], sec["turn_y"][k]
        for k in range(len(Z)):  # the girth of the mark, for the regions round the section
            if st[k + 1] > st[k] and np.isfinite(sec[kx][k]):
                qq = q[st[k]:st[k + 1]]
                sec[kg][k] = g[st[k]:st[k + 1]][np.argmin(np.hypot(qq[:, 0] - sec[kx][k], qq[:, 1] - sec[ky][k]))]
    return out


def _ridge_contrast(m, ridge):
    """Per point of a traced ridge: its bend over the flatter side 3 to 10 cm off across it (the
    body's median bend where a side is off the body): the check's contrast, along the ridge."""
    p = ridge.astype(np.float64)
    n = m.value("ns", p).astype(np.float64)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    c = m.value("curv", p, n).astype(np.float64)
    _, _, e1, _ = _principal(c[:, [[0, 1, 2], [1, 3, 4], [2, 4, 5]]], n)
    k0 = m.value("k1", p, n)
    floor = float(np.median(m.layers["k1"]))
    sides = []
    for sign in (1.0, -1.0):
        ts = np.arange(3.0, 10.5, 1.0)
        q = p[:, None, :] + sign * ts[None, :, None] * e1[:, None, :]
        on = m.project(q.reshape(-1, 3), np.repeat(n, len(ts), 0))[2].reshape(len(p), len(ts)) < 1.0
        kk = m.value("k1", q.reshape(-1, 3), np.repeat(n, len(ts), 0)).reshape(len(p), len(ts))
        kk = np.where(on, kk, np.nan)
        med = np.nanmedian(kk, axis=1)
        sides.append(np.where(on.sum(1) >= 4, med, floor))
    return k0 / np.maximum(np.minimum(*sides), 1e-3)


def _folds(m, ridges, least=1.5, length=20.0):
    """The real design edges among the traced ridges: those whose contrast (median along them) is
    at least `least` and that run `length` cm or more, each fitted as one curve by its arc length
    (_fit) and put back on the body. Returns the curves' data (build)."""
    out = []
    for r in ridges:
        if len(r) * RIDGE_STEP < length:
            continue
        con = _ridge_contrast(m, r)
        if np.nanmedian(con) < least:
            continue
        t = np.r_[0, np.cumsum(np.linalg.norm(np.diff(r.astype(np.float64), axis=0), axis=1))]
        for dense, res, nk, kept in _fit(r.astype(np.float64), t):
            out.append(dict(kind=2, pts=dense.astype(np.float32), res=res[kept].astype(np.float32), knots=nk, gap=0,
                            dropped=int((~kept).sum()), contrast=float(np.nanmedian(con))))
    return out


def _pack(curves):
    """The curves' data as arrays for the cache."""
    return dict(curve_pts=np.concatenate([c["pts"] for c in curves]) if curves else np.zeros((0, 3), np.float32),
                curve_starts=np.r_[0, np.cumsum([len(c["pts"]) for c in curves])],
                curve_kind=np.array([c["kind"] for c in curves], np.int8),
                curve_knots=np.array([c["knots"] for c in curves], np.int16),
                curve_res=np.concatenate([c["res"] for c in curves]) if curves else np.zeros(0, np.float32),
                curve_res_starts=np.r_[0, np.cumsum([len(c["res"]) for c in curves])],
                curve_gap=np.array([c["gap"] for c in curves], np.int16),
                curve_dropped=np.array([c["dropped"] for c in curves], np.int16),
                curve_contrast=np.array([c["contrast"] for c in curves], np.float32))


# ---- the car's lines ----

def _edge_lines(V, F, fn, part, names, spacing=0.4):
    """Points along the welded body's edges, by kind: "fold" (a bend over FOLD degrees), "opening"
    (an edge with one triangle and no surface beyond it within 1 cm), "join" (between two named
    parts, or a loose panel's edge lying on another), "edge" (the openings of the body proper:
    not the wheel covers' nor the blades', for the sections)."""
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
    kinds["edge"] = kinds["opening"] & ~np.isin(names[part[t0]], WHEEL_COVERS + BLADES)
    # a wall to the air: an opening the oncoming air runs into, off the surface (the cockpit's front
    # rim, an inlet's mouth), not one it runs along (a bottom edge) or leaves behind (a back edge)
    ea, eb = V[ends[:, 0]], V[ends[:, 1]]
    n0 = fn[t0]
    con = np.cross(eb - ea, n0)
    con /= np.maximum(np.linalg.norm(con, axis=1, keepdims=True), 1e-12)
    third = cen[t0] - 0.5 * (ea + eb)
    con *= np.where((con * third).sum(1) > 0, -1.0, 1.0)[:, None]  # pointing off the triangle
    air = np.array([0.0, 0.0, -1.0])
    u0 = air - (n0 @ air)[:, None] * n0
    u0 /= np.maximum(np.linalg.norm(u0, axis=1, keepdims=True), 1e-9)
    kinds["wall"] = kinds["opening"] & ((u0 * con).sum(1) > 0.35)
    w = kinds["wall"]
    walls = dict(tri=t0[w], con=con[w], length=np.linalg.norm(eb[w] - ea[w], axis=1))
    out = {}
    for kind, sel in kinds.items():
        a, b = V[ends[sel, 0]], V[ends[sel, 1]]
        L = np.linalg.norm(b - a, axis=1)
        k = np.maximum(1, np.ceil(L / spacing).astype(int))
        rep = np.repeat(np.arange(len(k)), k + 1)
        tt = np.concatenate([np.linspace(0, 1, n + 1) for n in k]) if len(k) else np.zeros(0)
        out[kind] = (a[rep] + tt[:, None] * (b[rep] - a[rep])).astype(np.float32)
    return out, walls


# ---- the air over the surface ----

def _flow_field(V, F, walls, weight=1e4):
    """The air's flow over the body, per vertex: the potential phi whose surface gradient is closest
    to the oncoming air laid flat on each triangle (least squares, weighted by area), with the flow
    held tangent to the walls (a heavy penalty on its component across each wall edge). The oncoming
    air laid flat is itself the gradient of -z, so phi = -z plus a harmonic correction that turns the
    air round the walls smoothly and early, as potential flow does, and never merges two lines."""
    from scipy.sparse import coo_matrix, diags
    from scipy.sparse.linalg import spsolve
    A, B, C = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    n = np.cross(B - A, C - A)
    area2 = np.linalg.norm(n, axis=1)
    ok = area2 > 1e-9
    n = n / np.maximum(area2, 1e-12)[:, None]
    T = len(F)
    # the gradient of the linear function with vertex values f: sum f_i (n x e_i) / (2 area), with
    # e_i the edge opposite vertex i, anticlockwise
    rows, cols, vals = [], [], []
    for i, (p, q) in enumerate(((B, C), (C, A), (A, B))):
        g = np.cross(n, q - p) / np.maximum(area2, 1e-12)[:, None]
        for k in range(3):
            rows.append(np.arange(T) * 3 + k)
            cols.append(F[:, i])
            vals.append(np.where(ok, g[:, k], 0.0))
    G = coo_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(3 * T, len(V))).tocsr()
    air = np.array([0.0, 0.0, -1.0])
    u0 = air - (n @ air)[:, None] * n
    w = np.repeat(np.where(ok, 0.5 * area2, 0.0), 3)
    # the walls: the flow's component across each wall edge, from its triangle's gradient
    Wt, Wc, Wl = walls["tri"], walls["con"], walls["length"]
    Gx, Gy, Gz = G[0::3], G[1::3], G[2::3]
    Cw = diags(Wc[:, 0]) @ Gx[Wt] + diags(Wc[:, 1]) @ Gy[Wt] + diags(Wc[:, 2]) @ Gz[Wt]
    M = G.T @ diags(w) @ G + weight * (Cw.T @ diags(Wl) @ Cw) + 1e-6 * diags(np.ones(len(V)))
    rhs = G.T @ (w * u0.reshape(-1))
    phi = spsolve(M.tocsc(), rhs)
    flow_t = (G @ phi).reshape(T, 3)
    # per vertex: the area-weighted mean of its triangles' flow
    fv = np.zeros_like(V)
    for k in range(3):
        np.add.at(fv, F[:, k], flow_t * (0.5 * area2)[:, None])
    wsum = np.bincount(F.reshape(-1), weights=np.repeat(0.5 * area2, 3), minlength=len(V))
    return fv / np.maximum(wsum, 1e-9)[:, None], np.linalg.norm(flow_t, axis=1)


# ---- building and loading ----

def build():
    progress.detail("Rebuilding the car map")
    V, F, fn, part, names = _weld()
    vn, area = _vertex_normals(V, F, fn)
    dirs = directions()
    seen = _seen(V, vn, dirs, _occluders())
    w = np.maximum(vn @ dirs.T, 0)
    open_ = (seen * w).sum(1) / np.maximum(w.sum(1), 1e-9)
    # what the game's chase cameras see (Cam 1, Cam 2 and their alts all look from behind, 20 to 30
    # degrees above: viewer.js VIEWS), taken from one direction between them
    chase_d = np.array([0.0, 0.42, -0.91]) / np.linalg.norm([0.0, 0.42, -0.91])
    chase = _seen(V, vn, chase_d[None], _occluders())[:, 0] * np.maximum(vn @ chase_d, 0)
    cone = dirs[:, 2] > np.cos(np.radians(FRONT_CONE))
    front_open = seen[:, cone].mean(1)
    ns = _smooth_normals(V, F, fn, vn, area)
    Mv = _curvature(V, F, ns)
    k1 = _principal(Mv, ns)[0]
    data = dict(version=VERSION, V=V, F=F, fn=fn, part=part, vn=vn, area=area, dirs=dirs,
                seen=np.packbits(seen, axis=1), open=open_.astype(np.float32),
                front_open=front_open.astype(np.float32), chase=chase.astype(np.float32),
                ns=ns.astype(np.float32), k1=k1.astype(np.float32),
                curv=Mv[:, [0, 0, 0, 1, 1, 2], [0, 1, 2, 1, 2, 2]].astype(np.float32))
    ridges = _trace_ridges(Map(data))
    data["ridge_starts"] = np.r_[0, np.cumsum([len(r) for r in ridges])]
    data["ridge_pts"] = np.concatenate(ridges)
    lines, walls = _edge_lines(V, F, fn, part, names)
    lines["fold"] = _resample(ridges)
    flow_v, _ = _flow_field(V, F, walls)
    bare = Map(data)
    sec = _sections(V, F, part, names, open_, lines["fold"], lines["edge"], lambda p: bare.value("k1", p))
    data.update(flow=flow_v.astype(np.float32), **{f"sec_{k}": v for k, v in sec.items()},
                **{f"line_{k}": v for k, v in lines.items()})
    from tool import mapcheck  # the slices where a line is drawn: on a ridge that stands out and stays put
    data["sec_draw"] = mapcheck.draw_mask(mapcheck.measure(Map(data)))
    sec["draw"] = data["sec_draw"]
    named = _curves(bare, sec, lines["edge"])  # the lines as curves, from the evidence
    folds = _folds(bare, ridges)
    # a real fold that is a named line, an opening's rim or a join is drawn as that, not again as a fold
    drawn = np.concatenate([c["pts"] for c in named] + [c["pts"] * np.array([-1, 1, 1], np.float32) for c in named]
                           + [lines["opening"], lines["join"]])
    tree = cKDTree(drawn)
    folds = [c for c in folds if np.median(tree.query(c["pts"], workers=-1)[0]) > 2.0]
    curves = named + folds
    data.update(**{f"sec_{k}": v for k, v in sec.items()}, **_pack(curves))
    data["line_fold"] = _resample([c["pts"] for c in folds])
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
        self.V, self.F, self.fn, self.part = data["V"], data["F"], data["fn"], data["part"]
        self.vn, self.area, self.dirs = data["vn"], data["area"], data["dirs"]
        self.seen = np.unpackbits(data["seen"], axis=1)[:, :len(self.dirs)].astype(bool)
        self.part_names = np.array([inst["name"] for inst in parts.load().instances])
        self.sec = {k[4:]: data[k] for k in data if k.startswith("sec_")}
        self.lines = {k[5:]: data[k] for k in data if k.startswith("line_")}
        self._tree = None
        self._last = None
        self._sec_last = None
        self._grad = {}
        self._line_trees = {}
        self._slice_trees = {}
        self.layers = {"open": data["open"], "front_open": data["front_open"], "chase": data["chase"],
                       "ns": data["ns"], "curv": data["curv"], "k1": data["k1"],
                       "along": ((NOSE_Z - self.V[:, 2]) / (NOSE_Z - TAIL_Z)).astype(np.float32),
                       "facing_x": (self.vn[:, 0] * np.sign(self.V[:, 0] + 1e-9)).astype(np.float32),
                       "facing_y": self.vn[:, 1].astype(np.float32), "facing_z": self.vn[:, 2].astype(np.float32)}
        if "curve_pts" in data:  # the lines as curves (_curves, _folds): kind 0 the shoulder, 1 the lower edge, 2 a fold
            st, rs = data["curve_starts"], data["curve_res_starts"]
            self.curves = [dict(kind=int(data["curve_kind"][i]), pts=data["curve_pts"][st[i]:st[i + 1]],
                                res=data["curve_res"][rs[i]:rs[i + 1]], knots=int(data["curve_knots"][i]),
                                gap=int(data["curve_gap"][i]), dropped=int(data["curve_dropped"][i]),
                                contrast=float(data["curve_contrast"][i]))
                           for i in range(len(st) - 1)]
        if "ridge_pts" in data:  # the traced ridges, each an (n, 3) array
            st = data["ridge_starts"]
            self.ridges = [data["ridge_pts"][st[i]:st[i + 1]] for i in range(len(st) - 1)]
        if not self.sec:  # the bare map the ridges are traced on, while building
            return
        self.flow_v = data["flow"]
        st = self.sec["starts"]
        has = np.flatnonzero(st[1:] > st[:-1])
        self._fill = has[np.abs(np.arange(len(st) - 1)[:, None] - has[None]).argmin(1)]
        self.layers["across"] = self.section(self.V)[0]

    # ---- round the section ----

    def _marks_at(self, z):
        Z = self.sec["Z"]
        return [np.interp(z, Z, self.sec[k]) for k in ("sh_x", "sh_y", "lo_x", "lo_y")]

    def _region(self, pos, girths=None, with_dist=False):
        """0 top, 1 side, 2 under: where each point's nearest point on its nearest slice's outline
        sits against that slice's shoulder and lower edge (its own marks, or girths given: the
        design lines', _design_girths); with_dist: also how far that nearest outline point is
        (cm; far means the slice doesn't see the point: a blade, hidden skin)."""
        Z, st, q, g = self.sec["Z"], self.sec["starts"], self.sec["q"], self.sec["g"]
        sh_g, lo_g = girths or (self.sec["sh_g"], self.sec["lo_g"])
        k = self._fill[np.clip(np.rint((pos[:, 2] - Z[0]) / SLICE).astype(int), 0, len(Z) - 1)]
        p2 = np.stack([np.abs(pos[:, 0]), pos[:, 1]], 1)
        out = np.zeros(len(pos), int)
        dist = np.zeros(len(pos))
        for kk in np.unique(k):
            if kk not in self._slice_trees:
                self._slice_trees[kk] = cKDTree(q[st[kk]:st[kk + 1]])
            sel = np.flatnonzero(k == kk)
            dist[sel], i = self._slice_trees[kk].query(p2[sel])
            gp = g[st[kk]:st[kk + 1]][i]
            out[sel] = np.where(gp <= sh_g[kk], 0, np.where(gp <= lo_g[kk], 1, 2))  # on a mark: the area before it
        return (out, dist) if with_dist else out

    def _design_girths(self):
        """Per slice, the girth of the shoulder's and the lower edge's design line where it runs
        (the slice's own mark elsewhere): the areas are cut by the design lines, and a slice's own
        mark can sit away from them where a line bridges a stretch (round the sidepod's rear top
        corner the marks follow the panel's rounded corner inboard, the line runs straight). NaN
        where the line's point lies on no skin the slice sees (nothing within 3 cm: under the
        arch the flank's strip is hidden by the inner car on some slices)."""
        if not hasattr(self, "_girths"):
            Z, st, q, g = self.sec["Z"], self.sec["starts"], self.sec["q"], self.sec["g"]
            out = [self.sec["sh_g"].copy(), self.sec["lo_g"].copy()]
            for j in (0, 1):
                for dense, _ in self.design_lines(j):
                    zi = np.clip(np.rint((dense[:, 2] - Z[0]) / SLICE).astype(int), 0, len(Z) - 1)
                    for k in np.unique(zi):
                        if st[k + 1] > st[k]:
                            x, y = dense[zi == k, 0].mean(), dense[zi == k, 1].mean()
                            qq = q[st[k]:st[k + 1]]
                            dq = np.hypot(qq[:, 0] - x, qq[:, 1] - y)
                            out[j][k] = g[st[k]:st[k + 1]][np.argmin(dq)] if dq.min() < 3.0 else np.nan
            self._girths = tuple(out)
        return self._girths

    def section(self, pos):
        """Where points sit round the car's section: across (0 the top's middle, 1 the shoulder, 2
        the lower edge, 3 under: see _across) and the scale there (cm per unit of across)."""
        pos = np.asarray(pos, np.float64)
        if self._sec_last is not None and _same(self._sec_last[0], (pos,)):  # zones ask again for the same points
            return self._sec_last[1]
        out = tuple(v.astype(np.float32) for v in _across(np.abs(pos[:, 0]), pos[:, 1], *self._marks_at(pos[:, 2]),
                                                          self._region(pos)))
        self._sec_last = ((pos.copy(),), out)
        return out

    def design_lines(self, kind):
        """The named line (kind 0 the shoulder, 1 the lower edge) as ONE smooth curve per stretch the
        body carries it on: the map's fitted curves of that kind, nose to tail, chained, and each
        gap between two of them under BLEND_GAP cm bridged by the same C2 cubic B-spline fitted
        through both (the blend: at the sidepod's rear corner the sidepod's edge ends and the rear
        flank's crease starts 4 cm on and lower, and a band offset from each stepped there, the
        user's close-up of 2026-09-29); for the lower edge, the slices' turns (where the skin faces
        the ground: _marks) stand in where the body has no crease, so it runs from the front flank's
        skirt to the tail. A wider gap stays a break (the lower edge's hand-over from the nose's
        lip down to the skirt's crest under the front flank, where the belly's skin ends, a 25 cm
        drop between two different edges). The left
        side; a list of (points (n, 3) every 0.25 cm, blend (n,) whether the point lies in a
        blend). The measured curves (Map.curves) stay as they are for the check; the areas, `line`
        and `near` go by these."""
        if not hasattr(self, "_design"):
            self._design = {}
        if kind not in self._design:
            pieces = []
            Z, kinds, draw = self.sec["Z"], self.sec["kind"][:, kind], self.sec["draw"][:, kind]
            for c in self.curves:
                if c["kind"] != kind or len(c["pts"]) < 8:
                    continue
                p = c["pts"].astype(np.float64)
                k = np.clip(np.rint((p[:, 2] - Z[0]) / SLICE).astype(int), 0, len(Z) - 1)
                # the design line keeps the crease evidence: the shoulder over the sidepod's front
                # and inlet is the shell's own edge round the sidepod's top (kind 4), a panel gap,
                # bridged smoothly (a band offset from it wrapped round the panel's corner: the
                # user's close-up, 2026-09-29); and a curve ends at its last drawn crease (the
                # measured curve runs on round the sidepod's rear top corner, over slices with no
                # crease, to the panel's rear edge: bridged from there to the rear flank's crease
                # the line would double back on itself, and the sidepod's top go to the sides)
                keep = kinds[k] != 4 if kind == 0 else np.ones(len(p), bool)
                ok = np.flatnonzero(keep & draw[k])
                if len(ok) < 8:
                    continue
                p, keep = p[ok[0]:ok[-1] + 1], keep[ok[0]:ok[-1] + 1]
                for run in np.split(np.arange(len(p)), np.flatnonzero(np.diff(keep.astype(int)) != 0) + 1):
                    if keep[run[0]] and len(run) >= 8:
                        pieces.append((p[run], id(c)))
            pieces = sorted(pieces, key=lambda pc: -pc[0][:, 2].mean())
            pieces = [(p if p[0, 2] >= p[-1, 2] else p[::-1], c) for p, c in pieces]  # nose to tail
            if kind == 1:
                # where the body has no lower line (behind the sidepods the flank rolls under with no
                # crease) the line runs where each slice's skin turns to face the ground, along the
                # floor, and behind the last crease on up the tail corner's hem, where the side's
                # skin rolls under, to the deck's rear corner, where the turn meets the shoulder
                # and the line ends
                Z, tx, ty = self.sec["Z"], self.sec["turn_x"], self.sec["turn_y"]
                low = ty < FLOOR + 5.0
                met = np.hypot(tx - self.sec["sh_x"], ty - self.sec["sh_y"]) < 2.0
                turns = []
                for i, (p, c) in enumerate(pieces):
                    z_next = pieces[i + 1][0][0, 2] if i + 1 < len(pieces) else -np.inf
                    ks = np.flatnonzero((Z < p[-1, 2] - 0.5) & (Z > z_next + 0.5) & np.isfinite(tx))[::-1]
                    if i + 1 == len(pieces):
                        stop = np.flatnonzero(met[ks])
                        ks = ks[:stop[0]] if len(stop) else ks
                    else:
                        ks = ks[low[ks]]
                    if len(ks) >= 2:
                        turns.append((np.c_[tx[ks], ty[ks], Z[ks]], ("turn", i)))
                pieces = sorted(pieces + turns, key=lambda pc: -pc[0][:, 2].mean())
            chains, cur, last = [], [], None
            for p, c in pieces:
                # the pieces of one measured curve are one line whatever lies between them; between
                # two curves the gap decides
                if cur and c != last and not self._continues(cur[-1], p):
                    chains.append(cur)
                    cur = []
                cur.append(p)
                last = c
            if cur:
                chains.append(cur)
            out = []
            for chain in chains:
                pts = np.concatenate(chain)
                s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
                ends = np.cumsum([len(p) for p in chain])[:-1]  # where each gap begins
                knots = list(np.arange(s[0] + BLEND_KNOT, s[-1] - BLEND_KNOT / 2, BLEND_KNOT))
                for e in ends:  # no knot inside a gap: the spline spans it as one smooth piece
                    knots = [k for k in knots if not (s[e - 1] - BLEND_KNOT / 2 < k < s[e] + BLEND_KNOT / 2)]
                fs = [_lsq(s, pts[:, k], knots) for k in range(3)]
                sd = np.arange(0, s[-1], 0.25)
                dense = np.stack([f(sd) for f in fs], 1)
                blend = np.zeros(len(sd), bool)
                for e in ends:
                    blend |= (sd >= s[e - 1] - BLEND_REACH) & (sd <= s[e] + BLEND_REACH)
                if blend.any():  # a bridge lies on the skin, not through the air: put back on the body, then smoothed
                    for _ in range(2):
                        dense[blend] = self.project(dense[blend])[0]
                        dense = gaussian_filter1d(dense, 8, axis=0, mode="nearest")
                out.append((dense, blend))
            self._design[kind] = out
        return self._design[kind]

    @staticmethod
    def _continues(a, b):
        """Whether curve b carries on from curve a: their ends within BLEND_GAP, and the chord between
        them within BLEND_TURN degrees of both curves' end tangents (the sidepod's corner, the
        sweep over its front: yes; the lower edge's hand-over from the nose's lip down to the
        skirt's crest under the front flank, a 25 cm drop between two different edges: no)."""
        chord = b[0] - a[-1]
        L = np.linalg.norm(chord)
        if L > BLEND_GAP:
            return False
        if L <= BLEND_SHORT:  # a short gap is a corner or a notch: always bridged (the sidepod's rear corner)
            return True
        ta, tb = a[-1] - a[max(len(a) - 21, 0)], b[min(20, len(b) - 1)] - b[0]
        cos = min(chord @ ta / max(L * np.linalg.norm(ta), 1e-9), chord @ tb / max(L * np.linalg.norm(tb), 1e-9))
        return cos >= np.cos(np.radians(BLEND_TURN))

    def _frames(self, a):
        """The named line's design curves (a = 1 the shoulder, 2 the lower edge), both sides, with at
        each point the direction across the line pointing to the top (the shoulder: inboard and
        up) or up (the lower edge), made perpendicular to the line's run: a point's side of the
        line is the sign of its offset along it. The direction is the car's own, not read off the
        skin under the line: at an open edge the nearest skin can be a flange folded under the
        panel out of sight (the sidepod's bottom edge), whose normal would lay the direction flat
        along the flange, and flip it where the flange tilts the other way."""
        key = f"frame{int(a)}"
        if key not in self._line_trees:
            pts, B, inner = [], [], []
            for dense, _ in self.design_lines(int(a) - 1):
                for flip in (1.0, -1.0):
                    p = dense.astype(np.float64) * np.array([flip, 1.0, 1.0])
                    inner.append(np.r_[np.zeros(8, bool), np.ones(max(len(p) - 16, 0), bool), np.zeros(min(8, len(p)), bool)][:len(p)])
                    T = np.gradient(p, axis=0)
                    T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
                    want = np.c_[-np.sign(p[:, 0] + 1e-9), np.ones(len(p)), np.zeros(len(p))] if a == 1 else np.tile([0.0, 1.0, 0.0], (len(p), 1))
                    b = want - (want * T).sum(1, keepdims=True) * T
                    b /= np.maximum(np.linalg.norm(b, axis=1, keepdims=True), 1e-9)
                    pts.append(p)
                    B.append(b)
            pts = np.concatenate(pts) if pts else np.zeros((0, 3))
            self._line_trees[key] = (cKDTree(pts) if len(pts) else None, np.concatenate(B) if B else np.zeros((0, 3)), pts,
                                     np.concatenate(inner) if inner else np.zeros(0, bool))
        return self._line_trees[key]

    def across_level(self, pos, a):
        """Signed distance (cm) from the points to a named line, positive past it (further round
        from the top's middle): near the line (within 2 cm, and not at a curve's ends) the offset
        across the line's own curve in the curve's frame, so the areas are cut by the curve itself;
        further off, the distance to the curve signed by the point's region round the section,
        against the design lines' own place on its slice (_design_girths: the frame's direction
        leans along the car where the line sweeps across it, over the sidepod's front, and a
        cavity's wall a few cm off, the inlet's throat, is placed by its slice); beyond the lines'
        ends (the nose's tip, the tail's end), and where the slice sees neither the line's point
        nor the point itself (a blade, skin hidden by one), the nearest point's frame, unless the
        slice places the point before the shoulder (the top, whatever the lower line); where the
        body has no line at that length (nothing within 3 cm along the car), the distance to the
        skin's own end, the mesh's boundary, signed the same way."""
        pos = np.asarray(pos, np.float64)
        tree, B, cpts, inner = self._frames(a)
        girths = self._design_girths()
        region, dist = self._region(pos, girths, with_dist=True)
        past = region >= int(a)
        Z = self.sec["Z"]
        k = self._fill[np.clip(np.rint((pos[:, 2] - Z[0]) / SLICE).astype(int), 0, len(Z) - 1)]
        # the slice can't place the point: the line's point lies on no skin it sees, or the point
        # does (a blade: the diffuser's strakes; skin hidden between them): the frame decides,
        # unless the slice puts the point before the shoulder: that is the top whatever the lower
        # line (the deck's middle, 50 cm from any lower line, is not for the tail hem's end frame)
        blind = (~np.isfinite(girths[int(a) - 1][k]) & (region > 0)) | (dist > 3.0)
        if tree is None:
            de = self.distance("opening", pos)
            return np.where(past, de, -de).astype(np.float32)
        d, i = tree.query(pos, workers=-1)
        # the line exists at the point's length: some design curve of this kind spans its z (the
        # nearest point's own z said no for a point far from a slanted curve, and the shoulder's
        # bands then followed the skirt's edge, 2026-09-29)
        spans = [(c[:, 2].min() - 3.0, c[:, 2].max() + 3.0) for c, _ in self.design_lines(int(a) - 1)]
        on = np.zeros(len(pos), bool)
        for lo, hi in spans:
            on |= (pos[:, 2] >= lo) & (pos[:, 2] <= hi)
        # beyond the lines' first or last point along the car (the nose's tip, the tail's end: rounded
        # ends the slices cut across) the end's own frame decides, for both lines from where the
        # first of them ends
        z_nose = min(max(d[:, 2].max() for d, _ in self.design_lines(k)) for k in (0, 1))
        z_tail = max(min(d[:, 2].min() for d, _ in self.design_lines(k)) for k in (0, 1))
        beyond = (pos[:, 2] > z_nose) | (pos[:, 2] < z_tail)
        de = self.distance("opening", pos)
        out = np.where(past, 1.0, -1.0) * np.where(on, d, de)
        near = (on & (d < 2.0) & inner[i]) | beyond | (on & blind)  # not at a curve's ends, 2 cm in, where its frame says nothing beyond it
        out[near] = -((pos[near] - cpts[i[near]]) * B[i[near]]).sum(1)
        return out.astype(np.float32)

    def mark_distance(self, pos, a):
        """Distance (cm) from the points to a named line (a = 1 the shoulder, 2 the lower edge): the
        design curves (Map.design_lines), both sides; far from them where the body has no line."""
        key = f"mark{int(a)}"
        if key not in self._line_trees:
            pts = [dense.astype(np.float32) for dense, _ in self.design_lines(int(a) - 1)]
            line = np.concatenate(pts) if pts else np.zeros((0, 3), np.float32)
            self._line_trees[key] = cKDTree(np.concatenate([line, line * np.array([-1, 1, 1], np.float32)])) if len(line) else None
        tree = self._line_trees[key]
        pos = np.asarray(pos, np.float64)
        return (tree.query(pos, workers=-1)[0] if tree is not None else np.full(len(pos), 1e6)).astype(np.float32)

    # ---- the air ----

    def hit(self, pos, nrm):
        """How hard the oncoming air hits the points, 0..1 (see the module's docstring)."""
        facing = np.clip(np.asarray(nrm, np.float64)[:, 2], 0, 1)
        return (facing ** 2 * self.value("front_open", pos, nrm)).astype(np.float32)

    def _walls(self):
        if "wall" not in self._line_trees:
            self._line_trees["wall"] = cKDTree(self.lines["wall"])
        return self._line_trees["wall"]

    def flow(self, pos, nrm):
        """Unit directions the air runs over the surface at the points, from the solved flow (see
        _flow_field), laid flat on the points' own surface; zero where the air meets it head-on."""
        pos, nrm = np.asarray(pos, np.float64), np.asarray(nrm, np.float64)
        face, bary, _ = self.at(pos, nrm)
        u = (bary[:, :, None] * self.flow_v[self.F[face]]).sum(1)
        u -= (u * nrm).sum(1, keepdims=True) * nrm
        n = np.linalg.norm(u, axis=1, keepdims=True)
        return np.where(n > 0.15, u / np.maximum(n, 1e-9), 0.0)

    def project(self, pos, nrm=None):
        """The nearest points on the body (on their triangles' planes), their normals, and how far
        the points were from it."""
        face, _, dist = self.at(pos, nrm)
        a = self.V[self.F[face, 0]]
        n = self.fn[face]
        on = pos - ((pos - a) * n).sum(1, keepdims=True) * n
        return on, n, dist

    def rake(self, z, across):
        """Points on the body's outline at length z (the left side), at the given across positions
        (0 the top's middle, 1 the shoulder ...): where to start streamlines, like a smoke rake's
        nozzles. A position the outline doesn't reach there is left out."""
        Z, st, q = self.sec["Z"], self.sec["starts"], self.sec["q"]
        k = int(np.argmin(np.abs(Z - z)))
        pts = q[st[k]:st[k + 1]].astype(np.float64)
        if len(pts) < 2:
            return np.zeros((0, 3))
        p3 = np.c_[pts, np.full(len(pts), Z[k])]
        a, _, off = self.section(p3)
        out = []
        for want in np.atleast_1d(across):
            ok = off < 0.5
            j = np.flatnonzero(ok)[np.argmin(np.abs(a[ok] - want))] if ok.any() else None
            if j is not None and abs(a[j] - want) < 0.02:
                out.append(p3[j])
        return np.array(out).reshape(-1, 3)

    def front_rake(self, xs, top=True):
        """A smoke rake standing in front of the car across its width: for each x (cm, the left
        side), the first point of the body the air meets there, the most forward point of the top (or
        of the whole outline, top=False) at that x. Lines traced from them cover the car evenly, as
        the smoke lines in a wind tunnel photograph do."""
        Z, st, q = self.sec["Z"], self.sec["starts"], self.sec["q"]
        out = []
        for x in np.atleast_1d(xs):
            for k in range(len(Z) - 1, -1, -1):  # from the nose back
                pts = q[st[k]:st[k + 1]]
                if not len(pts):
                    continue
                near = np.flatnonzero(np.abs(pts[:, 0] - x) < 0.6)
                if not len(near):
                    continue
                p3 = np.c_[pts[near], np.full(len(near), Z[k])].astype(np.float64)
                a, _, off = self.section(p3)
                ok = (a < 1.0) if top else np.ones(len(a), bool)
                ok &= off < 0.5
                if top:  # the top proper, facing up, on the upper body: not a low ledge's front end (the
                    # side skirt runs forward under the nose to its tip) nor a strut
                    ok &= self.value("facing_y", p3) > 0.35
                    face, _, _ = self.at(p3)
                    ok &= ~np.isin(self.part_names[self.part[face]], LOW_PARTS)
                if ok.any():
                    j = np.flatnonzero(ok)[np.argmax(p3[ok, 1])]  # the top of the body at that x
                    out.append(p3[j] + np.array([0.0, 0.0, -1.0]))  # a centimetre in from its edge
                    break
        return np.array(out).reshape(-1, 3)

    def streamlines(self, seeds, step=0.5, length=450.0):
        """Lines traced along the flow from seed points (n, 3) on or near the body, a point every
        `step` cm, until the line runs off the body (an edge, an opening's rim), stalls (the air
        meets the surface head-on) or reaches `length` cm. Returns a list of (m, 3) arrays."""
        seeds = np.asarray(seeds, np.float64)
        p, n, _ = self.project(seeds)
        lines = [[q.copy()] for q in p]
        alive = np.ones(len(p), bool)
        for _ in range(int(length / step)):
            idx = np.flatnonzero(alive)
            if not len(idx):
                break
            u = self.flow(p[idx], n[idx])
            stall = np.linalg.norm(u, axis=1) < 0.5
            mid = p[idx] + 0.5 * step * u
            pm, nm, _ = self.project(mid, n[idx])
            u2 = self.flow(pm, nm)  # a midpoint step: steadier round bends
            nxt = p[idx] + step * np.where(np.linalg.norm(u2, axis=1, keepdims=True) > 0.5, u2, u)
            q, nq, dist = self.project(nxt, n[idx])
            # an opening's edge is a wall the line slides along, kept 0.6 cm off it
            wall, wi = self._walls().query(q, workers=-1)
            away = q - self.lines["wall"][wi]
            away -= (away * nq).sum(1, keepdims=True) * nq
            away /= np.maximum(np.linalg.norm(away, axis=1, keepdims=True), 1e-9)
            close = wall < 0.6
            if close.any():
                q[close] += (0.6 - wall[close])[:, None] * away[close]
                q[close], nq[close], dist[close] = self.project(q[close], nq[close])
            moved = np.linalg.norm(q - p[idx], axis=1)
            # where the surface turns to face back, the air leaves it (it separates)
            leaves = nq[:, 2] < -0.6
            end = stall | (dist > 1.5) | (moved < 0.1 * step) | leaves | (q[:, 2] < TAIL_Z)
            # a line that has got nowhere over its last 20 steps is stuck against a wall it met
            # head-on (the cockpit's rim dead ahead): it ends there
            back = np.array([lines[k][max(0, len(lines[k]) - 20)] for k in idx])
            full = np.array([len(lines[k]) >= 20 for k in idx])
            end |= full & (np.linalg.norm(q - back, axis=1) < 20 * step * 0.25)
            for j, k in enumerate(idx):
                if not end[j]:
                    lines[k].append(q[j].copy())
            p[idx], n[idx] = q, nq
            alive[idx[end]] = False
        return [np.array(l) for l in lines]

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


# ---- the map in words, for the AI (car/map.md) ----

MAP_MD = paths.REPO / "car" / "map.md"
STATIONS = ((212, "the nose's tip"), (190, "the nose, over the front wing"), (178, "the front wheels' axle"),
            (150, "the nose"), (130, "the nose fin's plate"), (110, "the bonnet"), (85, "the cockpit opening's front"),
            (60, "the front flank"), (30, "the front flank, the sidepods begin"), (0, "the sidepods, their inlets"),
            (-30, "the sidepods"), (-60, "the sidepods' back, the number panel"), (-90, "the deck, the engine cover panel"),
            (-120, "the rear wheels' axle"), (-140, "the tail"), (-158, "the tail's end"))


def _opening_groups(m):
    """The body's openings as loops of open edges: each group's points, the parts round it, and
    whether the oncoming air runs into it (a wall)."""
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
    wall_tree = cKDTree(m.lines["wall"])
    out = []
    for edges in groups.values():
        pts = np.array([0.5 * (V[a] + V[b]) for a, b, _ in edges])
        length = sum(np.linalg.norm(V[a] - V[b]) for a, b, _ in edges)
        if length < 30:
            continue
        parts_ = [int(m.part[t_]) for _, _, t_ in edges]
        d, _ = wall_tree.query(pts)
        out.append(dict(pts=pts, length=length, parts=parts_, wall=float(np.mean(d < 0.5))))
    return out


def describe(m=None):
    """car/map.md: the car map in words, for Claude to read before designing (the numbers all come from the map, so they're redone with it)."""
    import datetime
    m = m or load()
    P = parts.load()
    names = np.array([inst["name"] for inst in P.instances])
    Z = m.sec["Z"]
    L = ["# The car map", "",
         f"Written by `python -m tool.carmap --describe` from the car's own mesh ({datetime.date.today()}); "
         "`tool/carmap.py` is the key. Read it, and look at its pictures (`car/map/`), when a design places "
         "shapes by the body's areas or needs exact positions. Lengths in cm: x out to the car's left (the right mirrors it), y up from the ground, "
         "z forward (the nose's tip at 215, the tail at -162).", "",
         "## The pictures", "",
         "The body alone, the wheels taken off, nine views each (`tool.snap <name> --body`):", "",
         "- `car/map/areas.jpg`: the top white, the sides blue, underneath grey; the shoulder green, "
         "the lower edge magenta (each one smooth curve per stretch; the shoulder absent where the body has no line, "
         "the lower edge along where the skin turns to face the ground where it has no crease: `python -m "
         "tool.carmap --check`), the real folds black, openings red, joins blue.",
         "- `car/map/lines.jpg`: every ridge of the body's curvature on clay, each in its own colour.",
         "- `car/map/texture.jpg`: the areas car's flat texture (Skin_B), the lines on it as the game's texture holds them.",
         "- `car/map/open.jpg`: how much of the open air each spot sees, white (all) to violet "
         "(hidden).",
         "- `car/map/air.jpg`: where the oncoming air hits, a warm ramp over black, and smoke lines "
         "traced along its flow from a rake at the nose.",
         "",
         "The car's 3D model in the pictures: amogusstrikesback2, CC-BY-4.0 "
         "(https://sketchfab.com/amogusstrikesback2).", ""]
    L += ["## The body along its length", "",
          "Where the top ends (the shoulder) and where the side turns under (the lower edge), on each slice.", "",
          "| z | what's there | shoulder x, y | lower edge x, y |", "|---|---|---|---|"]
    for z, what in STATIONS:
        k = int(np.argmin(np.abs(Z - z)))
        sx, sy, lx, ly = (float(m.sec[n][k]) for n in ("sh_x", "sh_y", "lo_x", "lo_y"))
        L.append(f"| {z} | {what} | {sx:.0f}, {sy:.0f} | {lx:.0f}, {ly:.0f} |")
    high = Z[(m.sec["kind"][:, 1] == 3) & (Z > 60)]
    L += ["", "The top's half-width is the shoulder's x; the sides run from the shoulder's height down to the "
          "lower edge's." + (f" At z {high.min():.0f} to {high.max():.0f} the lower edge is the nose's and the front "
          "flank's lip, with the nose's belly rolled under it: the skin ends there and the inner car carries on below "
          "(the skirt further down is another piece); paint on \"body\" stops at the lip." if len(high) else ""), ""]
    fa_ = m.area
    outer = ~np.isin(names[m.part], WHEEL_COVERS + BLADES)
    fwd, bwd = fa_[(m.fn[:, 2] > 0.7) & outer].sum(), fa_[(m.fn[:, 2] < -0.7) & outer].sum()
    L += ["## Lines on the car", "",
          "Lines, stripes, bands, pinstripes and rings are drawn on the car's own skin (`tool/skindraw.py`): each one a "
          "curve on the surface through places you pick, its width measured over the body, exact over every fold and "
          "seam, and checked on the painted car (`python -m tool.skincheck <car>`). The map's own lines below are fitted "
          "off the mesh to cut its areas; they are not for drawing.", ""]
    from tool import pieces as pieces_mod
    plist, nm = pieces_mod.write()
    L += ["## The model's pieces", "",
          f"The body is {len(plist)} separate pieces of 5 cm² or more (triangles joined across shared edges; the wheel covers "
          f"left out), and {nm} edges are shared by three or more triangles. Each piece's parts, area, the length of its edge, "
          "the gap to the nearest other piece (the smallest distance between its edge and the other's), how much of its edge "
          "lies within 1 cm of another piece, and the skin of other pieces hidden within 1 cm behind it. Where two pieces "
          "almost touch the skin is sewn and a line carries straight over; across a real gap (the tail's 2 cm slot) a line "
          "stops, as a real wrap would, and a decal must not straddle one (`tool/pieces.py`, `car/pieces.json`).", "",
          "| parts | cm² | edge cm | gap cm | edge within 1 cm | hidden skin behind, cm² | z |", "|---|---|---|---|---|---|---|"]
    for q in plist:
        L.append(f"| {', '.join(q['parts'])} | {q['cm2']} | {q['boundary_cm']} | {q['gap_cm'] if q['gap_cm'] is not None else '-'} | "
                 f"{q['boundary_within_1cm']:.0%} | {q['hidden_skin_behind_cm2']} | {q['z'][0]} to {q['z'][1]} |")
    L += [""]
    L += ["## The front and the back", "",
          f"The body's skin has no front or back face: only {fwd:.0f} cm² of it faces within 45 degrees of straight "
          f"ahead and {bwd:.0f} cm² of straight back, in patches (the sidepods' inlet rims, the nose's wing and the "
          "tail's number panel are inner parts). The map gives no such areas; what faces the oncoming air is `shapes.hit`.", ""]
    L += ["## Openings", "", "Loops of open edges 30 cm round or more (`shapes.near(\"opening\", r)` keeps clear of them); "
          "a wall is one the oncoming air runs into, which the air turns round.", "",
          "| round | parts | x | y | z | a wall |", "|---|---|---|---|---|---|"]
    for g in sorted(_opening_groups(m), key=lambda g: -g["length"]):
        pts = g["pts"]
        if pts[:, 0].max() < -0.5:
            continue  # the right side's mirror of a left opening
        u, c = np.unique(names[g["parts"]], return_counts=True)
        top = ", ".join(u[np.argsort(-c)][:2])
        L.append(f"| {g['length']:.0f} | {top} | {pts[:, 0].min():.0f} to {pts[:, 0].max():.0f} | "
                 f"{pts[:, 1].min():.0f} to {pts[:, 1].max():.0f} | {pts[:, 2].min():.0f} to {pts[:, 2].max():.0f} | "
                 f"{'yes' if g['wall'] > 0.3 else 'partly' if g['wall'] > 0.05 else 'no'} |")
    # per part: area, where it sits, what sees it
    fa = m.area
    lay = m.layers
    vmean = lambda k: lay[k][m.F].mean(1)
    across_f, open_f, chase_f = vmean("across"), vmean("open"), vmean("chase")
    hit_f = np.clip(m.fn[:, 2], 0, 1) ** 2 * vmean("front_open")
    rows = []
    pname = names[m.part]
    for name in np.unique(pname):
        sel = pname == name
        A = fa[sel].sum()
        if A < 50:
            continue
        cen = m.V[m.F[sel]].reshape(-1, 3)
        w = fa[sel] / A
        share = [float((w * (across_f[sel] < 1)).sum()), float((w * ((across_f[sel] >= 1) & (across_f[sel] < 2))).sum()),
                 float((w * (across_f[sel] >= 2)).sum())]
        rows.append((name, "", A, share, float((w * open_f[sel]).sum()),
                     float((fa[sel] * chase_f[sel]).sum()), float((fa[sel] * hit_f[sel]).sum()), cen))
    L += ["", "## The panels", "",
          "Each body part (a pair's two sides, or the four wheels', together): its area, where it sits (its share on "
          "the top, the sides and under), how open it is, how big it looks from the chase cameras and how much of the "
          "oncoming air it takes.", "",
          "| part | cm² | top / sides / under | open | seen from behind, cm² | air, cm² | z |", "|---|---|---|---|---|---|---|"]
    for name, side, A, share, op, ch, hit, cen in sorted(rows, key=lambda r: -r[2]):
        L.append(f"| {name}{' (' + side + ')' if side and side != 'centre' else ''} | {A:.0f} | "
                 f"{share[0]:.0%} / {share[1]:.0%} / {share[2]:.0%} | {op:.0%} | {ch:.0f} | {hit:.0f} | "
                 f"{cen[:, 2].min():.0f} to {cen[:, 2].max():.0f} |")
    tot = sum(r[5] for r in rows)
    L += ["", "## What the player sees", "",
          "The player sees their own car from behind all race (the chase cameras). By how big each part looks from "
          "there:", ""]
    for name, side, A, share, op, ch, hit, cen in sorted(rows, key=lambda r: -r[5])[:8]:
        L.append(f"- {name}: {ch / tot:.0%}")
    top_seen = float((fa * chase_f * (across_f < 1)).sum() / max((fa * chase_f).sum(), 1e-9))
    L += ["", f"The top takes {top_seen:.0%} of what the chase cameras see; the sides most of the rest. A graphic "
          "on the flanks is for the other players and the replays.", ""]
    L += ["## Where the air hits", "", "By how much of the oncoming air each part takes (the Newtonian rule):", ""]
    htot = sum(r[6] for r in rows)
    for name, side, A, share, op, ch, hit, cen in sorted(rows, key=lambda r: -r[6])[:6]:
        L.append(f"- {name}: {hit / htot:.0%}")
    L += ["", "## Words for designs (tool/shapes.py)", "",
          "- `shapes.area(\"top\" | \"sides\" | \"under\")`: the body's areas, split along "
          "its own lines.",
          "- `shapes.outside(0.4)`: the outer body only (keeps paint out of the inlets, the wheel pockets, under panels).",
          "- `shapes.along(a0, a1)`: a band from the nose's tip (0) to the tail (1).",
          "- `shapes.near(kind, reach)`: near a fold, an opening, a join, the shoulder, the lower edge; `~shapes.near(...)` "
          "keeps a graphic clear. (`shapes.line(kind, width)` shows the map's own lines on its test cars.)",
          "- Lines on the car: `tool/skindraw.py`.",
          "- `shapes.hit(lo, hi)`: where the oncoming air hits, 0..1 (bands of it make a pressure map).",
          "- `shapes.streamlines(shapes.rake(z, [across ...]), width)`: smoke lines along the air's flow from a "
          "row of seeds.",
          "- Everything combines with `&`, `|`, `~` and the plain zones (`stripe`, `band`, `facing`, ...).", ""]
    MAP_MD.write_text("\n".join(L))
    return MAP_MD


if __name__ == "__main__":
    import sys
    import time
    if "--describe" in sys.argv:
        print(describe())
        raise SystemExit
    if "--check" in sys.argv:
        from tool import mapcheck
        mapcheck.check(verbose="-v" in sys.argv)  # the evidence, slice by slice
        print()
        mapcheck.curves()  # the lines as the eye sees them
        raise SystemExit
    t = time.time()
    with progress.job("Rebuilding the car map", done="The car map rebuilt"):
        m = build()
    print(f"built in {time.time() - t:.0f} s: {len(m.V)} vertices, {len(m.F)} triangles, {len(m.dirs)} directions")
    o = m.layers["open"]
    print("open: " + ", ".join(f"{q:.0%} {np.quantile(o, q):.2f}" for q in (0.05, 0.25, 0.5, 0.75, 0.95)))
    a = m.layers["across"]
    print("across: top {:.0%}, sides {:.0%}, under {:.0%} of the vertices".format(
        np.mean(a < 1), np.mean((a >= 1) & (a < 2)), np.mean(a >= 2)))
    for kind, name in enumerate(("shoulder", "lower edge", "fold")):
        cs = [c for c in m.curves if c["kind"] == kind]
        print(f"{name}: {len(cs)} curves, {sum(len(c['pts']) for c in cs) * 0.25:.0f} cm, knots {sum(c['knots'] for c in cs)}, "
              f"evidence missed by at most {max((c['res'].max() for c in cs), default=0) * 10:.1f} mm")
    for k, v in m.lines.items():
        print(f"line {k}: {len(v)} points")
    print(f"ridges: {len(m.ridges)}, {sum(len(r) for r in m.ridges) * RIDGE_STEP:.0f} cm in all; the longest:")
    for r in sorted(m.ridges, key=len)[::-1][:12]:
        print(f"  {len(r) * RIDGE_STEP:4.0f} cm, x {r[:, 0].min():5.0f}..{r[:, 0].max():5.0f}, y {r[:, 1].min():3.0f}..{r[:, 1].max():3.0f}, z {r[:, 2].min():5.0f}..{r[:, 2].max():5.0f}")
    Z = m.sec["Z"]
    for z in (200, 170, 150, 120, 100, 60, 20, -20, -60, -100, -140):
        i = int(np.argmin(np.abs(Z - z)))
        print(f"  z {z:5.0f}: shoulder at x {m.sec['sh_x'][i]:5.1f} y {m.sec['sh_y'][i]:5.1f}, lower edge at x {m.sec['lo_x'][i]:5.1f} y {m.sec['lo_y'][i]:5.1f}")
