"""TSC_Water_Lagoon: the car as a lagoon seen from the air (TSC_Water's set 1, option B).

The whole body is one depth field, cut into four flat layers of cyan with crisp edges, the way a
lagoon's water steps in colour with its depth: pale shallows over the sandbanks, turquoise, cyan,
and the deep channel. The field (depth(), in cm, higher is deeper) is minus the distance to a deep
channel that winds over the top (from a pool on the bonnet, round the cockpit on the left over the
sidepod's shoulder, back across the deck and off the tail on the right), lifted into sandbanks on the inside
of its bends (the right sidepod, the deck's left rear, the nose) and two low on the flanks, and
sunk into pools: one on the deck, wide enough to hold the number and name panels whole in the deep
colour, and a small one round the nose fin's plate, so no edge crosses either. The points are
warped by a slow 3D wave (10 cm over 60 to 140 cm) so the edges wander like a shore, never finer
than a hand's width. Each layer's edge is cut at its level by the field's slope over the surface,
so it stays 0.2 cm crisp wherever the steps come close or far apart.

The channel and the banks sit by the car map (car/map.md): the cockpit opening is x +-28 from z 85
to -48, the sidepods' tops x 55 to 86 from z 12 to -50, the number panel x +-20 at z -78 to -62,
the name panel x +-20 at z -120 to -81, the nose fin's plate x +-8 at z 118 to 142. Their heights
are the body's own top (top()). The thresholds give the layers about 20/30/30/20 of the body's
outer skin (measured on tool/skinmesh's surface).

A concept: the cyans only, in pearl; the underside, the side skirts, the sidepods' inlet ducts, the
struts under the nose, the inner car and the wheels one deep teal-navy. The tyres and glass keep
their own.
"""

import numpy as np
from scipy.spatial import cKDTree

from tool import carmap, shapes

SHALLOWS = "#9FF2E2"   # sandbank shallows
TURQUOISE = "#4FDCCF"  # the main
CYAN = "#14B2C6"       # the story's #19BCC9 a step deeper, and
DEEP = "#0A7FA6"       # the deep channel (#0B8BAE): the four steps L* 90 / 80 / 67 / 50, so each reads
GROUND = "#08303A"     # deep teal-navy: the underside, the inlets, the inner car, the wheels

# the deep channel's route seen from above, (x: the car's left, z: forward) in cm, nose to tail
ROUTE = [(0, 148), (2, 128),                  # rising from a pool round the nose fin's plate (z 118 to 142)
         (14, 102), (34, 70), (48, 35),       # bending left past the cockpit's front (z 85)
         (54, 0), (44, -35),                  # along the left sidepod's inner half (x 55 to 86)
         (8, -66), (0, -96),                  # back over the number and name panels (x +-20)
         (-14, -130), (-36, -175)]            # and off the tail's right corner
# sandbanks on the top: (x, z, radius, height), all in cm, on the inside of the channel's bends
BANKS = [(-62, 15, 40, 40),     # the right sidepod and shoulder, opposite the bend round the cockpit
         (55, -128, 30, 45),    # the deck's left rear, over the left rear wheel
         (-16, 165, 20, 20)]    # the nose's right
# sandbanks low on the flanks: (x, y, z, radius, height)
SIDE_BANKS = [(84, 32, -95, 30, 40),   # the left rear flank
              (-60, 30, 55, 30, 30)]   # the right front flank
# pools: (x, z, radius across, radius along, depth)
POOLS = [(0, -97, 34, 54, 46),   # the deck: the number and name panels whole in the deep colour
         (1, 132, 16, 26, 20)]   # the nose fin's plate, whole in the deep colour (an edge there notches)
# the slow warp: per axis, waves of (direction, wavelength cm, phase)
WARP = [[((0.8, 0.3, 0.5), 90, 0.0), ((-0.2, 0.9, 0.4), 130, 1.7), ((0.3, -0.2, 0.9), 60, 4.4)],
        [((0.1, 0.6, -0.8), 100, 2.2), ((0.7, -0.5, 0.5), 140, 0.9), ((-0.6, 0.2, 0.7), 70, 2.8)],
        [((-0.5, 0.4, 0.8), 85, 3.1), ((0.9, 0.1, -0.3), 120, 5.0), ((0.2, 0.9, 0.3), 65, 0.6)]]
WARP_CM = 10.0
# the levels (cm of depth) between shallows | turquoise | cyan | deep: about 20/30/30/20 of the skin
LEVELS = (-83.9, -37.1, -9.6)

_cache = {}


def top(x, z):
    """The body's top height (cm) at (x, z), from the car map's mesh."""
    if "top" not in _cache:
        m = carmap.load()
        up = m.vn[:, 1] > 0.3
        _cache["top"] = (cKDTree(m.V[up][:, [0, 2]]), m.V[up][:, 1])
    tree, ys = _cache["top"]
    _, i = tree.query(np.stack([np.asarray(x, float), np.asarray(z, float)], 1), k=12)
    return ys[i].max(1)


def _route(pts, n=40):
    """A Catmull-Rom curve through the route's points, n points per span."""
    P = np.asarray(pts, float)
    P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    t = np.linspace(0, 1, n, endpoint=False)[:, None]
    out = [0.5 * (2 * P[i] + (P[i + 1] - P[i - 1]) * t + (2 * P[i - 1] - 5 * P[i] + 4 * P[i + 1] - P[i + 2]) * t ** 2
                  + (3 * P[i] - P[i - 1] - 3 * P[i + 1] + P[i + 2]) * t ** 3) for i in range(1, len(P) - 2)]
    return np.vstack(out + [P[-2][None]])


def _features():
    if "channel" not in _cache:
        xz = _route(ROUTE)
        y = top(xz[:, 0], np.clip(xz[:, 1], -160, 212))
        _cache["channel"] = cKDTree(np.stack([xz[:, 0], y, xz[:, 1]], 1))
        _cache["banks"] = [np.array([x, top([x], [z])[0], z]) for x, z, _, _ in BANKS]
        _cache["pools"] = [np.array([x, top([x], [z])[0], z]) for x, z, _, _, _ in POOLS]
    return _cache


def _wave(p, d, lam, ph):
    d = np.asarray(d, float) / np.linalg.norm(d)
    return np.cos(p @ d * (2 * np.pi / lam) + ph)


def depth(p):
    """The lagoon's depth at points p (n, 3) in cm: higher is deeper."""
    p = np.asarray(p, float)
    q = p + WARP_CM * np.stack([sum(_wave(p, *w) for w in axis) / len(axis) for axis in WARP], 1)
    f = _features()
    d, _ = f["channel"].query(q, workers=-1)
    D = -d
    for (_, _, r, h), c in zip(BANKS, f["banks"]):
        D -= h * np.exp(-(np.linalg.norm(q - c, axis=1) / r) ** 2)
    for x, y, z, r, h in SIDE_BANKS:
        D -= h * np.exp(-(np.linalg.norm(q - np.array([x, y, z], float), axis=1) / r) ** 2)
    for (_, _, rx, rz, h), c in zip(POOLS, f["pools"]):
        e = ((q[:, 0] - c[0]) / rx) ** 2 + ((q[:, 1] - c[1]) / rx) ** 2 + ((q[:, 2] - c[2]) / rz) ** 2
        D += h * np.exp(-e ** 2)
    return D


def _depth_and_slope(p, n):
    """The depth and its slope over the surface (cm per cm), once per set of points."""
    key = (len(p), np.ascontiguousarray(p[:: max(1, len(p) // 97)]).tobytes())
    if _cache.get("key") != key:
        p = np.asarray(p, float)
        n = np.asarray(n, float)
        n = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
        a = np.where(np.abs(n[:, :1]) < 0.9, [[1.0, 0.0, 0.0]], [[0.0, 1.0, 0.0]])
        t1 = np.cross(n, a)
        t1 /= np.maximum(np.linalg.norm(t1, axis=1, keepdims=True), 1e-9)
        t2 = np.cross(n, t1)
        h = 0.5
        D = depth(p)
        g1 = (depth(p + h * t1) - D) / h
        g2 = (depth(p + h * t2) - D) / h
        _cache["key"], _cache["val"] = key, (D, np.maximum(np.hypot(g1, g2), 0.2))
    return _cache["val"]


def deeper_than(level):
    """The zone deeper than a level, its edge crisp: signed distance = (depth - level) / slope."""
    def dist(p, n):
        D, slope = _depth_and_slope(p, n)
        return (D - level) / slope
    return shapes.field(dist)


def design(s):
    s.clay()

    s.step("The lagoon", "The whole body as a lagoon seen from the air, in four flat layers of cyan "
           "with crisp edges: pale shallows over sandbanks, turquoise, cyan, and a deep channel winding "
           "round the cockpit and across the deck. Pearl, like the shimmer of shallow water.",
           words="I want to first paint the car with layers of cyan all over the place")
    s.paint("body", "pearl", colour=SHALLOWS)
    for colour, level in zip((TURQUOISE, CYAN, DEEP), LEVELS):
        s.paint("body", "pearl", colour=colour, zone=deeper_than(level))
    # the game's number and name panels and the nose fin's plate: whole in the deep colour
    s.paint(["number panel", "engine cover panel", "nose fin"], "pearl", colour=DEEP)

    s.step("The dark ground", "The underside, the sills, the sidepods' inlets, the struts under the "
           "nose, the inner car and the wheels in one deep teal-navy, so the cyans stand on it.")
    s.paint("body", "pearl", colour=GROUND, zone=shapes.area("under"))
    # whole parts: the inlets' ducts (by openness, ~outside, notched the flanks), the side skirt (the
    # map's under/sides split steps on its lip below the sidepod's front corner) and the struts
    # under the nose (a bright chin from straight on)
    s.paint(["sidepod inlet", "side skirt", "wing pylon"], "pearl", colour=GROUND)
    s.paint("inner", "pearl", colour=GROUND)
    s.paint("wheels", "pearl", colour=GROUND)
