"""Zones on the car, drawn in 3D with crisp edges: stripes, bands, splits, fades, spots.

Every zone is a function (pos, nrm) -> weight 0..1 per point, where pos is (n, 3) in cm
(x = the car's left, y = up, z = forward) and nrm the unit normals. A weight of 1 is inside.
Edges are feathered over `soft` cm (default 0.2, about two texels) measured along the surface, so
the border never shows the texel grid and stays as crisp on a slope as on a flat panel (a height's
edge where the side rolls under, a shape drawn from above on a flank), and it never breaks at a seam
because it's drawn in 3D, not on the flat texture.

    shapes.stripe(width=20)                a stripe down the middle, along the car
    shapes.stripe(width=8, at=30)          a stripe 30 cm to the left of the middle
    shapes.stripes(4, across=(0.75, 0, 1)) stripes 4 cm wide with 4 cm gaps, square to a direction (slanted, seen
                                           from above, mirrored side to side: hazard stripes, chevrons); `edge`
                                           where one begins; stripes(15, across="back", edge=72): 15 cm blocks
                                           along the car from z 72 back
    shapes.checks(10, across=("z", "y"))   a checkerboard, 10 cm squares, along the car and up it
    shapes.band(z0=-40, z1=20)             a band across the car between two lengths
    shapes.front_of(60), shapes.behind(-50), shapes.above(45), shapes.below(30)
    shapes.left(), shapes.right()
    shapes.plane(point, normal)            one side of any plane: diagonal splits
    shapes.sphere(centre, radius), shapes.box(lo, hi)
    shapes.radial(centre, radius)          1 at the centre fading to 0 at radius: for glows and blends
    shapes.wheel_ring(29.5, 30.5)          a ring round each wheel's axle: tyre sidewall stripes
    shapes.fade(axis="z", start=200, end=-150)  0 at start rising to 1 at end: for blends
    shapes.facing("up"), shapes.facing((1, 0, 0))  where the surface faces a direction
    shapes.grass(base=10)                  blades of grass rising up the sides; line=0.6 for ink strokes
    shapes.blob((x, 0, z), 12)             a spot that isn't quite round, seen from above (axis="x": from the side)
    shapes.region("nose")                  a named region of the body (REGIONS)
    shapes.noisy(zone, amount=6)           a zone's edge roughened: torn, ragged, hand-painted
    shapes.sides(0.5)                      the flanks: surfaces facing left or right
    shapes.polyline([points, ...], 1.5)    a line 1.5 cm wide along points on the body
  The car map's (tool/carmap.py: the body's own open air and length):
    shapes.outside(0.4)                    the outer body only: never inside an inlet or under a panel
    shapes.along(0.2, 0.4)                 a band from the nose's tip (0) to the tail (1)
  Markings along the car's own lines (tool/course.py: a strip, dashes, ticks along one of the
  model's lines, a seam, a panel's edge or the line the user drew, a band beside one) and the
  model's own panels (tool/meshlines.py) give zones like these.
    zone_a & zone_b, zone_a | zone_b, ~zone_a   combine them
Each zone keeps how the design wrote it (`label`, "behind(40)") and the zones an & joined
(`parts()`), so tool/measure.py can say which of them ends a paint where it ends.
Lengths: the car runs from z = -162 (tail) to 215 (nose tip); the wheels sit at z = 179 and
-120, the cockpit opening at about z = -50 .. 90, the deck behind it to z = -133. Its width is
about 175 cm over the wheels, 110 at the sidepods. Top of the body: y = 84.
"""

import functools

import numpy as np

from tool.noise import smoothstep

# 0.2 cm is about two texels at 4096² (pitch 0.09 cm): enough to hide the grid and no more. The
# first value, 1.5 cm, blurred every stripe edge over 15 texels (the user, 2026-09-24).
SOFT = 0.2


class Zone:
    def __init__(self, fn, label=None, factors=None):
        self.fn = fn
        self.label = label  # as a design writes it: "behind(40)"
        self.factors = factors  # the zones an & joined

    def __call__(self, pos, nrm):
        return np.clip(self.fn(pos, nrm), 0, 1).astype(np.float32)

    def parts(self):
        """The zones an & joined, each with its label; the zone itself when it isn't an &."""
        return self.factors or [self]

    def __repr__(self):
        if self.label:
            return self.label
        if self.factors:
            return " & ".join(map(repr, self.factors))
        return f"a {self.kind} drawn on the skin" if getattr(self, "kind", None) else "a zone"

    def __and__(self, other):
        return Zone(lambda p, n: self(p, n) * other(p, n), factors=self.parts() + other.parts())

    def __or__(self, other):
        return Zone(lambda p, n: 1 - (1 - self(p, n)) * (1 - other(p, n)), label=f"({self!r} | {other!r})")

    def __invert__(self):
        return Zone(lambda p, n: 1 - self(p, n), label=f"~{self!r}")

    def __mul__(self, k):
        return Zone(lambda p, n: self(p, n) * k, label=f"{self!r} * {k:g}")


# a distance that changes slower than this along the surface (cm per cm) is level with it: its edge
# there is a step, not a slope's long feather
FLAT = 0.05


def _slope(g, n):
    """How fast a distance changes along the surface: its gradient's length within the surface, at
    least FLAT."""
    g = np.asarray(g, np.float32)
    if g.ndim == 1:
        g = np.broadcast_to(g, n.shape)
    t = g - (g * n).sum(1, keepdims=True) * n
    return np.maximum(np.linalg.norm(t, axis=1), FLAT)


def field(fn, soft=SOFT, grad=None):
    """A zone from a signed distance in cm: positive inside. The edge is feathered over `soft`,
    measured along the surface when `grad` gives the distance's gradient (a direction (3,), or
    (pos, nrm) -> (n, 3)); without it, through space."""
    if grad is None:
        return Zone(lambda p, n: smoothstep(-soft / 2, soft / 2, fn(p, n)))
    return Zone(lambda p, n: smoothstep(-soft / 2, soft / 2, fn(p, n) / _slope(grad(p, n) if callable(grad) else grad, n)))


def _unit(k):
    return np.eye(3, dtype=np.float32)[k]


def stripe(width, at=0.0, axis="x", soft=SOFT):
    """A stripe of `width` cm, centred `at` cm along `axis` (x: across the car, so the stripe
    runs along its length; z: along the car, so it runs across)."""
    k = "xyz".index(axis)
    return field(lambda p, n: width / 2 - np.abs(p[:, k] - at), soft, _unit(k))


def band(z0, z1, soft=SOFT):
    """Everything between two lengths along the car."""
    lo, hi = min(z0, z1), max(z0, z1)
    return field(lambda p, n: np.minimum(p[:, 2] - lo, hi - p[:, 2]), soft, _unit(2))


def front_of(z, soft=SOFT):
    return field(lambda p, n: p[:, 2] - z, soft, _unit(2))


def behind(z, soft=SOFT):
    return field(lambda p, n: z - p[:, 2], soft, _unit(2))


def above(y, soft=SOFT):
    return field(lambda p, n: p[:, 1] - y, soft, _unit(1))


def below(y, soft=SOFT):
    return field(lambda p, n: y - p[:, 1], soft, _unit(1))


def left(soft=SOFT):
    return field(lambda p, n: p[:, 0], soft, _unit(0))


def right(soft=SOFT):
    return field(lambda p, n: -p[:, 0], soft, _unit(0))


def plane(point, normal, soft=SOFT):
    """The side of a plane its normal points to."""
    point, normal = np.asarray(point, np.float32), np.asarray(normal, np.float32)
    normal = normal / np.linalg.norm(normal)
    return field(lambda p, n: (p - point) @ normal, soft, normal)


def _radial(centre, axes=(0, 1, 2)):
    """(pos, nrm) -> the unit direction from a centre, within the given axes."""
    centre = np.asarray(centre, np.float32)

    def g(p, n):
        d = np.zeros_like(p)
        d[:, axes] = p[:, axes] - centre[list(axes)]
        return d / np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-6)
    return g


def sphere(centre, radius, soft=SOFT):
    centre = np.asarray(centre, np.float32)
    return field(lambda p, n: radius - np.linalg.norm(p - centre, axis=1), soft, _radial(centre))


def box(lo, hi, soft=SOFT):
    lo, hi = np.asarray(lo, np.float32), np.asarray(hi, np.float32)

    def g(p, n):  # the nearest face's axis
        k = np.minimum(p - lo, hi - p).argmin(1)
        return np.eye(3, dtype=np.float32)[k]
    return field(lambda p, n: np.minimum(p - lo, hi - p).min(1), soft, g)


def _direction(across):
    """A direction across the car as a unit vector: "x", "y", "z", a word (DIRECTIONS) or a vector."""
    if isinstance(across, str):
        d = _unit("xyz".index(across)) if across in "xyz" else np.asarray(DIRECTIONS[across], np.float32)
    else:
        d = np.asarray(across, np.float32)
    return d / np.linalg.norm(d)


def _stripes(width, across, gap, edge, mirror):
    """The signed distance into stripes `width` cm wide with `gap` between, square to `across`, one
    beginning at `edge` and running the way `across` points; and its gradient. mirror: the car's
    left and right read the same (|x|), so a slanted run meets itself on the middle line."""
    d = _direction(across)
    gap = width if gap is None else gap
    period = width + gap
    flip = mirror and abs(d[0]) > 1e-6
    if np.isscalar(edge):
        u0 = float(edge) * (float(d["xyz".index(across)]) if isinstance(across, str) and across in "xyz" else float(d[2]))
    else:
        u0 = float(np.asarray(edge, np.float32) @ d)

    def q(p):
        if not flip:
            return p
        p = p.copy()
        p[:, 0] = np.abs(p[:, 0])
        return p

    def dist(p, n):
        ph = np.mod(q(p) @ d - u0, period)
        return np.where(ph <= width, np.minimum(ph, width - ph), np.maximum(width - ph, ph - period))

    def grad(p, n):
        g = np.broadcast_to(d, p.shape).copy()
        if flip:
            g[:, 0] *= np.sign(p[:, 0])
        return g
    return dist, grad


def stripes(width, across="z", gap=None, edge=0.0, mirror=True, soft=SOFT):
    """Stripes `width` cm wide with `gap` cm between (as wide as the stripes), square to a direction
    across the car: "x", "y", "z", a word ("back") or a vector ((0.75, 0, 1): slanted, seen from above);
    the car's left and right read the same, so a slanted run meets itself in a chevron on the middle
    line (mirror=False: one slant right across). One stripe begins at `edge`, a length along the car
    on the middle line (or the coordinate on the axis named) or a point, and runs the way `across`
    points. Painted on a part, they run edge to edge: hazard stripes on a panel, chevrons on the
    tail, blocks along a band."""
    dist, grad = _stripes(width, across, gap, edge, mirror)
    return field(dist, soft, grad)


def checks(size, across=("z", "y"), edge=(0.0, 0.0), mirror=True, soft=SOFT):
    """A checkerboard: squares `size` cm (or (along, across)), their rows square to the two directions
    (as stripes takes them), a square's corner at the two `edge`s."""
    size = (size, size) if np.isscalar(size) else tuple(size)
    a, b = (_stripes(size[k], across[k], size[k], edge[k], mirror) for k in range(2))

    def dist(p, n):
        da, db = a[0](p, n), b[0](p, n)
        inside = (da > 0) != (db > 0)
        return np.where(inside, 1.0, -1.0) * np.minimum(np.abs(da), np.abs(db))

    def grad(p, n):
        da, db = a[0](p, n), b[0](p, n)
        return np.where((np.abs(da) < np.abs(db))[:, None], a[1](p, n), b[1](p, n))
    return field(dist, soft, grad)


# the wheel centres, fitted to the tyres' tread and bead, the covers' and the rims' edges (within
# 0.2 mm, 2026-09-25). The older figures (35.3; 178.9, -119.6) were 5.7 mm too far forward, and a
# ring round them wobbled in the game as the wheel turned (the user). tool/parts.py uses these too.
WHEEL_Y, WHEEL_Z = 35.252, (178.314, -120.163)


def wheel_ring(r0, r1, soft=SOFT):
    """A ring round each wheel's axle, from r0 to r1 cm out: a stripe on the tyres' sidewalls
    (28.5 to 34.5 cm) or on the wheel covers (the cover ring 19 to 30, the disc 9 to 19). All
    four wheels share their paint, so it shows on each."""
    def f(p, n):
        zc = np.where(p[:, 2] > 30, WHEEL_Z[0], WHEEL_Z[1])
        r = np.hypot(p[:, 1] - WHEEL_Y, p[:, 2] - zc)
        return np.minimum(r - r0, r1 - r)

    def g(p, n):
        zc = np.where(p[:, 2] > 30, WHEEL_Z[0], WHEEL_Z[1])
        d = np.stack([np.zeros(len(p), np.float32), p[:, 1] - WHEEL_Y, p[:, 2] - zc], 1)
        return d / np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-6)
    return field(f, soft, g)


def cylinder(a, b, radius, soft=SOFT):
    """Within `radius` of the line from a to b."""
    a, b = np.asarray(a, np.float32), np.asarray(b, np.float32)
    d = b - a
    L = np.linalg.norm(d)
    d = d / L

    def f(p, n):
        rel = p - a
        t = np.clip(rel @ d, 0, L)
        return radius - np.linalg.norm(rel - t[:, None] * d, axis=1)

    def g(p, n):
        rel = p - a
        t = np.clip(rel @ d, 0, L)
        r = rel - t[:, None] * d
        return r / np.maximum(np.linalg.norm(r, axis=1, keepdims=True), 1e-6)
    return field(f, soft, g)


def fade(axis="z", start=200.0, end=-150.0, curve=1.0):
    """0 at `start`, rising to 1 at `end` along the axis. Use as the mix weight of a blend."""
    k = "xyz".index(axis)

    def f(p, n):
        t = np.clip((p[:, k] - start) / (end - start), 0, 1)
        return t ** curve
    return Zone(f)


def radial(centre, radius, curve=1.0):
    """1 at the centre, 0 at `radius` and beyond."""
    centre = np.asarray(centre, np.float32)
    return Zone(lambda p, n: (1 - np.clip(np.linalg.norm(p - centre, axis=1) / radius, 0, 1)) ** curve)


DIRECTIONS = {"up": (0, 1, 0), "down": (0, -1, 0), "left": (1, 0, 0), "right": (-1, 0, 0),
              "forward": (0, 0, 1), "front": (0, 0, 1), "back": (0, 0, -1), "rear": (0, 0, -1)}


def facing(direction, at_least=0.3, soft=0.25):
    """Where the surface faces a direction: 1 when the normal is within it, feathered by
    `soft` in cosine terms around `at_least`."""
    d = np.asarray(DIRECTIONS.get(direction, direction), np.float32)
    d = d / np.linalg.norm(d)
    return Zone(lambda p, n: smoothstep(at_least - soft, at_least + soft, n @ d))


def sides(at_least=0.5):
    """The flanks: surfaces facing left or right."""
    return Zone(lambda p, n: smoothstep(at_least - 0.25, at_least + 0.25, np.abs(n[:, 0])))


def blob(centre, radius, axis="y", wobble=0.1, seed=0, soft=SOFT):
    """A round spot that isn't quite round, projected along `axis` (y: seen from above; x: from the
    side): its edge wanders up to about `wobble` of its radius in a few slow lobes, as a ladybird's
    spots do (the user, 2026-09-28: "lady bug spots are not perfect circles, more like a blob close
    to being a circle"). Each seed gives another shape. centre is (x, y, z) in cm; the coordinate
    along `axis` is ignored."""
    k = "xyz".index(axis)
    a, b = [i for i in range(3) if i != k]
    c = np.asarray(centre, np.float32)
    rnd = np.random.default_rng(seed)
    lobes = [(n, rnd.uniform(0.3, 1.0) / n, rnd.uniform(0, 2 * np.pi)) for n in (2, 3, 4)]
    scale = wobble / sum(amp for _, amp, _ in lobes)

    def f(p, n):
        du, dv = p[:, a] - c[a], p[:, b] - c[b]
        ang = np.arctan2(dv, du)
        edge = radius * (1 + scale * sum(amp * np.sin(m * ang + ph) for m, amp, ph in lobes))
        return edge - np.hypot(du, dv)
    return field(f, soft, _radial(c, (a, b)))


def grass(base=10.0, height=(14.0, 30.0), width=(4.0, 8.0), lean=0.4, every=3.0, line=None, seed=0, soft=SOFT):
    """Blades of grass rising up the car from `base` cm above the ground, drawn as seen from the
    side (along the car and up), so both sides show the same silhouette. A blade is `width` cm at
    its root and `height` cm tall, bending up to `lean` of its height forward or back; one every
    `every` cm on average, overlapping. Filled, with everything below `base`; or `line`: each blade
    an ink stroke that wide at its root, thinning to the tip, and nothing else. Pair it with sides()
    to keep it off the top."""
    rnd = np.random.default_rng(seed)
    zs = np.arange(-190.0, 235.0, every)
    k = len(zs)
    zs = zs + rnd.uniform(-every / 2, every / 2, k)
    hs = rnd.uniform(*height, k)
    ws = rnd.uniform(*width, k)
    leans = rnd.uniform(-lean, lean, k) * hs
    top = base + max(height)

    def dist(p, n):
        y, z = p[:, 1], p[:, 2]
        d = np.full(len(p), -1e3, np.float32) if line else (base - y).astype(np.float32)
        near = np.nonzero((y > base - 1) & (y < top + 1))[0]
        near = near[np.argsort(z[near])]
        zn = z[near]
        for zi, h, w, le in zip(zs, hs, ws, leans):
            reach = w + abs(le) + 1
            a, b = np.searchsorted(zn, (zi - reach, zi + reach))
            if a == b:
                continue
            idx = near[a:b]
            u = (y[idx] - base) / h
            off = np.abs(z[idx] - (zi + le * np.clip(u, 0, 1) ** 1.6))  # bending more toward the tip
            half = (line / 2) * (1 - 0.7 * u) if line else (w / 2) * (1 - u)
            di = np.where((u >= 0) & (u <= 1), half - off, -1e3)
            d[idx] = np.maximum(d[idx], di)
        return d
    return field(dist, soft)


def noisy(zone, amount=6.0, scale=15.0, seed=0):
    """Roughen a zone's edge with noise: the border wanders by about `amount` cm, in wobbles
    about `scale` cm long. For torn, ragged or hand-painted looks."""
    from tool import noise

    def f(p, n):
        w = zone(p, n)
        shift = (noise.fbm(p / scale, 3, seed) - 0.5) * 2 * amount
        # push the weight by the noise: 0.5 stays a border, inside/outside move by the shift
        return np.clip(w + shift / (2 * SOFT) * 0.5, 0, 1)
    return Zone(f)


# Named regions of the body, in plain words. Measured on the model (2026-09-24).
REGIONS = {
    "nose": lambda: front_of(120, 4),
    "bonnet": lambda: band(40, 145, 4) & facing("up", 0.2),
    "cockpit": lambda: band(-55, 40, 4) & facing("up", 0.2),
    "deck": lambda: band(-135, -55, 4) & facing("up", 0.2),
    "tail": lambda: behind(-135, 4),
    "sides": lambda: sides(0.55),
    "top": lambda: facing("up", 0.35),
    "front half": lambda: front_of(25, 4),
    "rear half": lambda: behind(25, 4),
    "left": lambda: left(),
    "right": lambda: right(),
    "lower": lambda: below(35, 4),
    "upper": lambda: above(35, 4),
}


def region(name):
    key = name.strip().lower()
    if key not in REGIONS:
        raise KeyError(f"no region called {name!r}; known: {', '.join(REGIONS)}")
    return REGIONS[key]()


# ---- The car map (tool/carmap.py): the body's own open air and positions ----

def _map():
    from tool import carmap
    return carmap.load()


def outside(at_least=0.4, soft=SOFT):
    """The outer body: spots that see at least this share of the open air (the car map's "open"),
    so a graphic keeps off the insides of the inlets, the wheel pockets and the underside's recesses."""
    return field(lambda p, n: _map().level("open", at_least, p, n), soft)


def along(a0, a1, soft=SOFT):
    """A band across the car from a0 to a1 of the way from the nose's tip (0) to the tail (1)."""
    return field(lambda p, n: np.minimum(_map().level("along", a0, p, n), -_map().level("along", a1, p, n)), soft)


def _spaced(lines, spacing=0.25):
    """Points every `spacing` cm along polylines, for the distance trees."""
    out = []
    for l in lines:
        seg = np.linalg.norm(np.diff(l, axis=0), axis=1)
        s = np.r_[0, np.cumsum(seg)]
        u = np.arange(0, s[-1], spacing)
        out.append(np.stack([np.interp(u, s, l[:, k]) for k in range(3)], 1))
    return np.concatenate(out).astype(np.float32) if out else np.zeros((0, 3), np.float32)


def polyline(lines, width=1.5, soft=SOFT, spacing=0.25):
    """Lines `width` cm wide along polylines on the body: one (n, 3) array of points in cm, or a
    list of them (a line the user drew, say). spacing: cm between the points the distance is taken
    to (a quarter of the width or less: no beads)."""
    from scipy.spatial import cKDTree
    lines = [np.asarray(l, np.float64) for l in lines] if isinstance(lines, (list, tuple)) else [np.asarray(lines, np.float64)]
    pts = _spaced([l for l in lines if len(l) > 1], spacing)
    tree = cKDTree(pts) if len(pts) else None

    def dist(p, n):
        if tree is None:
            return np.full(len(p), -1.0, np.float32)
        d, _ = tree.query(p.astype(np.float64), workers=-1, distance_upper_bound=width * 2)
        return (width / 2 - np.minimum(d, width * 2)).astype(np.float32)

    def grad(p, n):
        if tree is None:
            return np.broadcast_to(_unit(1), p.shape)
        d, i = tree.query(p.astype(np.float64), workers=-1, distance_upper_bound=width * 2)
        r = p - pts[np.minimum(i, len(pts) - 1)]
        return (r / np.maximum(np.linalg.norm(r, axis=1, keepdims=True), 1e-6)).astype(np.float32)
    return field(dist, soft, grad)


def _word(v):
    if isinstance(v, (bool, np.bool_)) or v is None:
        return repr(v)
    if isinstance(v, (int, float, np.integer, np.floating)):
        return f"{float(v):g}"
    if isinstance(v, (list, tuple, np.ndarray)):
        return f"[{', '.join(map(_word, v))}]" if len(v) <= 4 else "[...]"
    return repr(v)


def _named(fn):
    """A zone's maker that labels what it makes the way the design wrote it: behind(40)."""
    @functools.wraps(fn)
    def make(*args, **kw):
        z = fn(*args, **kw)
        if isinstance(z, Zone) and z.label is None:
            z.label = f"{fn.__name__}({', '.join([*map(_word, args), *(f'{k}={_word(v)}' for k, v in kw.items())])})"
        return z
    return make


for _maker in ("stripe", "stripes", "checks", "band", "front_of", "behind", "above", "below", "left", "right", "plane",
               "sphere", "box", "wheel_ring", "cylinder", "fade", "radial", "facing", "sides", "blob", "grass", "noisy",
               "region", "outside", "along", "polyline"):
    globals()[_maker] = _named(globals()[_maker])
