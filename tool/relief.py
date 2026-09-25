"""Relief on the inner car: raised and sunk detail, drawn as heights in 3D and turned into the
game's normal map (Details_N). The body gets no normal map in the game, so it takes no relief.

    s.relief("seat", "quilted", depth=0.5, scale=7)                  diamond quilting
    s.relief("sidepod frame", "rivets", spacing=4, inset=1.0)        rivets along its edges
    s.relief("floor plank", "ribs", scale=2.5, direction="z")        raised ribs across it
    s.emboss("CMYK", "rear diffuser|centre", at=(0, 32, -171), right=(-1, 0, 0), up=(0, 1, 0),
             height=3.5, depth=0.12)                                 raised lettering

A height is a function h(pos, nrm) -> cm, drawn on each part's own positions (a local bake, so a
shared texel gets the part's own shape). Its slope along the texture's u and v is measured in 3D:
h at the texel and a millimetre along each of the texture's directions on that triangle (dP/du,
dP/dv), so the relief is right across seams, folds and mirrored twins. The game reads the map as
OpenGL (+v up the image), which the wing domes confirmed in checkpoint 4.

Nadeo's own relief (their Details_N) stays under ours, blended, unless a call replaces it. Their
map is 2048²; ours is drawn at the Details canvas's size (4096²) and ships there when the zip has
room, else halved to 2048² (paintbox.build_zip). At 2048² a texel is about 4 mm on most parts:
keep features to 1 cm and up, with bevels of 2 mm or more.
"""

import numpy as np

from tool import fbx, noise
from tool.noise import smoothstep

EPS = 0.05  # cm: the step for measuring slopes, a quarter of a texel at 4096²
_frames = {}


def frames(texture_set="Details"):
    """Per triangle of a mesh: the unit directions of +u and +v on the surface, (T, 3) each."""
    if texture_set not in _frames:
        from tool.bake import MESH_OF
        m = fbx.meshes()[MESH_OF[texture_set]]
        p = m["positions"][m["tri_vertex"]].astype(np.float64)
        uv = m["tri_uv"].astype(np.float64)
        e1, e2 = p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]
        d1, d2 = uv[:, 1] - uv[:, 0], uv[:, 2] - uv[:, 0]
        r = d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1]
        r = np.where(np.abs(r) < 1e-12, np.inf, r)
        t = (e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) / r[:, None]
        b = (e2 * d1[:, 0:1] - e1 * d2[:, 0:1]) / r[:, None]
        unit = lambda v: (v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-12)).astype(np.float32)
        _frames[texture_set] = (unit(t), unit(b))
    return _frames[texture_set]


def slopes(h, pos, nrm, tri_u, tri_v):
    """The height function's slope (cm per cm) along +u and +v at each point: (n, 2)."""
    h0 = h(pos, nrm)
    du = (h(pos + EPS * tri_u, nrm) - h0) / EPS
    dv = (h(pos + EPS * tri_v, nrm) - h0) / EPS
    return np.stack([du, dv], 1).astype(np.float32)


def to_normal(slope):
    """Tangent-space normals (n, 2), 0..1 as the game stores them, from slopes (n, 2)."""
    n = np.concatenate([-slope, np.ones((len(slope), 1), np.float32)], 1)
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    return n[:, :2] * 0.5 + 0.5


def combine(base, detail):
    """Lay one normal map's detail over another's (both (n, 2), 0..1): "whiteout" blending,
    which keeps both slopes where they overlap."""
    a, b = base * 2 - 1, detail * 2 - 1
    az = np.sqrt(np.clip(1 - (a ** 2).sum(1), 0, 1))
    bz = np.sqrt(np.clip(1 - (b ** 2).sum(1), 0, 1))
    n = np.concatenate([a + b, (az * bz)[:, None]], 1)
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    return n[:, :2] * 0.5 + 0.5


def clean_stock(n, noise_level=0.006):
    """Nadeo's Details_N with its rounding noise set flat: within 1.5/255 of flat, three texels
    in four. It carries no shape but costs 1.5 MB in the zip; everything bigger stays."""
    dev = np.hypot(n[..., 0] - 0.5, n[..., 1] - 0.5)
    out = n.copy()
    out[dev < noise_level] = 0.5
    return out


# ---- patterns: each returns h(pos, nrm) -> cm, 0 on the part's surface, + raised ----


def _planar(fn2d, power=8):
    """A 2D pattern laid on from the axis each point faces most (the looks' "planes" wrap)."""
    def h(pos, nrm):
        w = np.abs(nrm) ** power
        w = w / np.maximum(w.sum(1, keepdims=True), 1e-6)
        out = np.zeros(len(pos), np.float32)
        for axis in range(3):
            sel = w[:, axis] > 0.01
            if sel.any():
                a, b = [k for k in range(3) if k != axis]
                out[sel] += w[sel, axis] * fn2d(pos[sel, a], pos[sel, b])
        return out
    return h


def ribs(depth=0.2, scale=2.5, width=None, bevel=0.25, direction="x", **_):
    """Straight raised ribs, `scale` cm apart, each `width` cm wide on top, across `direction`."""
    k = "xyz".index(direction)
    width = scale * 0.4 if width is None else width

    def h(pos, nrm):
        d = np.abs(((pos[:, k] / scale) % 1) - 0.5) * scale  # cm from the rib's centre line
        return depth * smoothstep(width / 2 + bevel, width / 2, d)
    return h


def _button(d, r, bevel):
    """A round head `r` cm in radius: a bevelled edge and a slight crown, 0..1."""
    return smoothstep(r, r - bevel, d) * (0.75 + 0.25 * np.sqrt(np.clip(1 - (d / r) ** 2, 0, 1)))


def studs(depth=0.25, scale=3.0, size=None, bevel=0.2, stagger=True, **_):
    """A grid of round studs, `scale` cm apart, `size` cm across (a third of the spacing)."""
    r = (scale / 3 if size is None else size) / 2

    def grid(u, v):
        row = np.floor(v / scale)
        cu = ((u / scale + (0.5 * (row % 2) if stagger else 0)) % 1 - 0.5) * scale
        cv = ((v / scale) % 1 - 0.5) * scale
        return depth * _button(np.sqrt(cu * cu + cv * cv), r, bevel)
    return _planar(grid)


def quilted(depth=0.5, scale=7.0, fullness=0.5, **_):
    """Diamond quilting: rounded pillows `scale` cm across, sunk along the stitched seams
    between them. fullness: under 1 puffs the pillows up, flatter on top."""
    def cell(u, v):
        a, b = (u + v) / scale, (u - v) / scale
        fa, fb = ((a % 1) - 0.5) * np.pi, ((b % 1) - 0.5) * np.pi  # 0 at a pillow's middle, ±pi/2 at its seams
        return depth * np.clip(np.cos(fa) * np.cos(fb), 0, 1) ** fullness
    return _planar(cell, power=4)


def hexes(depth=0.15, scale=4.0, groove=0.3, seed=0, **_):
    """A honeycomb of raised cells `scale` cm across with grooves `groove` cm wide between."""
    def h(pos, nrm):
        from tool.looks import _nearest, surface_points
        if not hasattr(h, "centres"):
            h.centres = surface_points(pos, scale * 0.92, seed, regular=True)
        d, _ = _nearest(h.centres, pos, k=2)
        gap = d[:, 1] - d[:, 0]
        return depth * smoothstep(groove * 0.5, groove * 0.5 + 0.25, gap)
    return h


def points(centres, depth=0.25, size=1.0, bevel=0.2, **_):
    """Round heads (rivets, bolt heads) `size` cm across at given 3D points."""
    from scipy.spatial import cKDTree
    tree = cKDTree(np.asarray(centres, np.float64))
    r = size / 2

    def h(pos, nrm):
        d, _ = tree.query(pos, workers=-1)
        return (depth * _button(d, r, bevel)).astype(np.float32)
    return h


def picture(alpha, centre, right, up, width, depth=0.12, bevel=0.15, reach=3.0):
    """A picture's alpha (h, w) 0..1 raised `depth` cm on the surface under it, seen along
    right x up: lettering and logos. Only surfaces within `reach` cm of the picture's plane and
    facing it take it, so nothing shows through on the far side."""
    from scipy.ndimage import gaussian_filter, map_coordinates
    centre, right, up = (np.asarray(v, np.float64) for v in (centre, right, up))
    right, up = right / np.linalg.norm(right), up / np.linalg.norm(up)
    facing = np.cross(right, up)
    ih, iw = alpha.shape
    cm_per_px = width / iw
    img = gaussian_filter(alpha.astype(np.float32), max(bevel / cm_per_px / 2, 0.5))

    def h(pos, nrm):
        rel = pos - centre
        x = rel @ right / cm_per_px + iw / 2
        y = ih / 2 - rel @ up / cm_per_px
        v = map_coordinates(img, [y, x], order=1, mode="constant", cval=0)
        ok = (np.abs(rel @ facing) < reach) & (nrm @ facing > 0.3)
        return (depth * v * ok).astype(np.float32)
    return h


def edge_points(tris_xyz, spacing=4.0, inset=1.0, min_loop=None):
    """Points `inset` cm in from the open edges of a set of triangles, evenly `spacing` cm apart
    round each edge loop: where rivets go on a panel. tris_xyz: (T, 3, 3) corner positions.
    Loops shorter than `min_loop` cm (small holes; default three spacings) get none."""
    min_loop = 3 * spacing if min_loop is None else min_loop
    t = tris_xyz.astype(np.float64)
    # corners that sit on the same spot are one vertex (the mesh repeats them at UV seams)
    _, vid = np.unique(np.round(t.reshape(-1, 3), 2), axis=0, return_inverse=True)
    vid = vid.reshape(-1, 3)
    edges = np.concatenate([vid[:, [0, 1]], vid[:, [1, 2]], vid[:, [2, 0]]], 0)
    tri_of = np.tile(np.arange(len(t)), 3)
    key = np.sort(edges, 1)
    _, inv, counts = np.unique(key, axis=0, return_inverse=True, return_counts=True)
    border = counts[inv.reshape(-1)] == 1
    edges, tri_of = edges[border], tri_of[border]
    corner = t.reshape(-1, 3)
    where = {}  # vertex id -> a corner position
    for k, v in enumerate(vid.reshape(-1)):
        where.setdefault(int(v), corner[k])
    nxt = {}
    for k, (a, b) in enumerate(edges):
        nxt.setdefault(int(a), []).append(k)
    used = np.zeros(len(edges), bool)
    out = []
    for start in range(len(edges)):
        if used[start]:
            continue
        loop, k = [], start
        while k is not None and not used[k]:
            used[k] = True
            loop.append(k)
            cands = [j for j in nxt.get(int(edges[k][1]), []) if not used[j]]
            k = cands[0] if cands else None
        a = np.array([where[int(edges[j][0])] for j in loop])
        b = np.array([where[int(edges[j][1])] for j in loop])
        seg = np.linalg.norm(b - a, axis=1)
        total = seg.sum()
        if total < min_loop:
            continue
        # the inward direction of each edge: in its triangle's plane, towards the third corner
        tri = t[tri_of[loop]]
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        along = (b - a) / np.maximum(seg[:, None], 1e-9)
        inward = np.cross(n, along)
        inward /= np.maximum(np.linalg.norm(inward, axis=1, keepdims=True), 1e-9)
        flip = ((tri.mean(1) - a) * inward).sum(1) < 0
        inward[flip] *= -1
        count = max(int(round(total / spacing)), 1)
        s = (np.arange(count) + 0.5) * total / count
        cum = np.concatenate([[0], np.cumsum(seg)])
        e = np.clip(np.searchsorted(cum, s, side="right") - 1, 0, len(loop) - 1)
        f = ((s - cum[e]) / np.maximum(seg[e], 1e-9))[:, None]
        out.append(a[e] + (b[e] - a[e]) * f + inward[e] * inset)
    return np.concatenate(out) if out else np.zeros((0, 3))


def mirrored(h):
    """A height function and its mirror image across the car's centre (x = 0), for detail on
    parts that share their texels with a mirror twin: each texel shows the right one."""
    flip = np.array([-1, 1, 1], np.float32)
    return lambda pos, nrm: np.maximum(h(pos, nrm), h(pos * flip, nrm * flip))


def line_points(a, b, spacing):
    """Points evenly spaced from a to b (3D, cm), about `spacing` cm apart, ends included."""
    a, b = np.asarray(a, np.float64), np.asarray(b, np.float64)
    n = max(int(round(np.linalg.norm(b - a) / spacing)), 1)
    return a + (b - a) * np.linspace(0, 1, n + 1)[:, None]


def snap(points, pos):
    """Each point moved to the nearest of the surface positions `pos`."""
    from scipy.spatial import cKDTree
    _, k = cKDTree(pos).query(np.asarray(points, np.float64))
    return pos[k]


PATTERNS = {"ribs": ribs, "studs": studs, "quilted": quilted, "hex": hexes}
