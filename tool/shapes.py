"""Zones on the car, drawn in 3D with soft edges: stripes, bands, splits, fades, spots.

Every zone is a function (pos, nrm) -> weight 0..1 per point, where pos is (n, 3) in cm
(x = the car's left, y = up, z = forward) and nrm the unit normals. A weight of 1 is inside.
Edges are feathered over `soft` cm (default 0.2, about two texels), so the border never shows the texel grid,
and it never breaks at a seam because it's drawn in 3D, not on the flat texture.

    shapes.stripe(width=20)                a stripe down the middle, along the car
    shapes.stripe(width=8, at=30)          a stripe 30 cm to the left of the middle
    shapes.band(z0=-40, z1=20)             a band across the car between two lengths
    shapes.front_of(60), shapes.behind(-50), shapes.above(45), shapes.below(30)
    shapes.left(), shapes.right()
    shapes.plane(point, normal)            one side of any plane: diagonal splits
    shapes.sphere(centre, radius), shapes.box(lo, hi)
    shapes.wheel_ring(29.5, 30.5)          a ring round each wheel's axle: tyre sidewall stripes
    shapes.fade(axis="z", start=200, end=-150)  0 at start rising to 1 at end: for blends
    shapes.facing("up"), shapes.facing((1, 0, 0))  where the surface faces a direction
    shapes.grass(base=10)                  blades of grass rising up the sides; line=0.6 for ink strokes
    shapes.blob((x, 0, z), 12)             a spot that isn't quite round, seen from above (axis="x": from the side)
    shapes.region("nose")                  a named region of the body (REGIONS)
    shapes.seams(width=2)                  a line along every seam of the body panels (for tape)
    zone_a & zone_b, zone_a | zone_b, ~zone_a   combine them
Lengths: the car runs from z = -162 (tail) to 215 (nose tip); the wheels sit at z = 179 and
-120, the cockpit opening at about z = -50 .. 90, the deck behind it to z = -133. Its width is
about 175 cm over the wheels, 110 at the sidepods. Top of the body: y = 84.
"""

import numpy as np

from tool.noise import smoothstep

# 0.2 cm is about two texels at 4096² (pitch 0.09 cm): enough to hide the grid and no more. The
# first value, 1.5 cm, blurred every stripe edge over 15 texels (the user, 2026-09-24).
SOFT = 0.2


class Zone:
    def __init__(self, fn):
        self.fn = fn

    def __call__(self, pos, nrm):
        return np.clip(self.fn(pos, nrm), 0, 1).astype(np.float32)

    def __and__(self, other):
        return Zone(lambda p, n: self(p, n) * other(p, n))

    def __or__(self, other):
        return Zone(lambda p, n: 1 - (1 - self(p, n)) * (1 - other(p, n)))

    def __invert__(self):
        return Zone(lambda p, n: 1 - self(p, n))

    def __mul__(self, k):
        return Zone(lambda p, n: self(p, n) * k)


def field(fn, soft=SOFT):
    """A zone from a signed distance in cm: positive inside. The edge is feathered over `soft`."""
    return Zone(lambda p, n: smoothstep(-soft / 2, soft / 2, fn(p, n)))


def everywhere():
    return Zone(lambda p, n: np.ones(len(p), np.float32))


def stripe(width, at=0.0, axis="x", soft=SOFT):
    """A stripe of `width` cm, centred `at` cm along `axis` (x: across the car, so the stripe
    runs along its length; z: along the car, so it runs across)."""
    k = "xyz".index(axis)
    return field(lambda p, n: width / 2 - np.abs(p[:, k] - at), soft)


def band(z0, z1, soft=SOFT):
    """Everything between two lengths along the car."""
    lo, hi = min(z0, z1), max(z0, z1)
    return field(lambda p, n: np.minimum(p[:, 2] - lo, hi - p[:, 2]), soft)


def front_of(z, soft=SOFT):
    return field(lambda p, n: p[:, 2] - z, soft)


def behind(z, soft=SOFT):
    return field(lambda p, n: z - p[:, 2], soft)


def above(y, soft=SOFT):
    return field(lambda p, n: p[:, 1] - y, soft)


def below(y, soft=SOFT):
    return field(lambda p, n: y - p[:, 1], soft)


def left(soft=SOFT):
    return field(lambda p, n: p[:, 0], soft)


def right(soft=SOFT):
    return field(lambda p, n: -p[:, 0], soft)


def plane(point, normal, soft=SOFT):
    """The side of a plane its normal points to."""
    point, normal = np.asarray(point, np.float32), np.asarray(normal, np.float32)
    normal = normal / np.linalg.norm(normal)
    return field(lambda p, n: (p - point) @ normal, soft)


def sphere(centre, radius, soft=SOFT):
    centre = np.asarray(centre, np.float32)
    return field(lambda p, n: radius - np.linalg.norm(p - centre, axis=1), soft)


def box(lo, hi, soft=SOFT):
    lo, hi = np.asarray(lo, np.float32), np.asarray(hi, np.float32)
    return field(lambda p, n: np.minimum(p - lo, hi - p).min(1), soft)


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
    return field(f, soft)


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
    return field(f, soft)


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
    return field(f, soft)


def grass(base=10.0, height=(14.0, 30.0), width=(4.0, 8.0), lean=0.4, every=3.0, line=None, seed=0, soft=SOFT):
    """Blades of grass rising up the car from `base` cm above the ground, drawn as seen from the
    side (along the car and up), so both sides show the same silhouette. A blade is `width` cm at
    its root and `height` cm tall, bending up to `lean` of its height forward or back; one every
    `every` cm on average, overlapping. Filled, with everything below `base`; or `line`: each blade
    an ink stroke that wide at its root, thinning to the tip, and nothing else. Made for the grass
    maps' cars (TSC_Ladybird's fringe, 2026-09-28): pair it with sides() to keep it off the top."""
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


# ---- Seams: the edges of the body's panels, found on the mesh ----
_SEAMS = {}


def _seam_points(spacing=0.4):
    """Points along the body mesh's edges, by kind: "border" (between two named parts), "open"
    (an edge with one triangle: the cockpit opening, wheel arches, the wing's edges) and
    "crease" (a fold between two triangles). Each kind is (points (n, 3), fold angle in degrees
    (n), the part instance ids on each side (n, 2), -1 for none). Cached per run."""
    if _SEAMS:
        return _SEAMS
    from tool import fbx, parts
    P = parts.load()
    m = fbx.meshes()["Skin_01"]
    tv, pos = m["tri_vertex"], m["positions"].astype(np.float64)
    T = len(tv)
    off = P.mesh_offset["Skin"]
    tri_part = P.tri_part[off:off + T]
    # the exporter split the mesh at every hard edge and UV seam, so weld vertices by position
    _, inv = np.unique(np.round(pos, 2), axis=0, return_inverse=True)
    wt = inv.reshape(-1)[tv]
    e = np.concatenate([wt[:, [0, 1]], wt[:, [1, 2]], wt[:, [2, 0]]])
    e.sort(1)
    ends = np.concatenate([tv[:, [0, 1]], tv[:, [1, 2]], tv[:, [2, 0]]])  # original vertex ids, for positions
    tid = np.tile(np.arange(T), 3)
    key = e[:, 0].astype(np.int64) * (int(inv.max()) + 1) + e[:, 1]
    order = np.argsort(key, kind="stable")
    key, tid, ends = key[order], tid[order], ends[order]
    _, start, cnt = np.unique(key, return_index=True, return_counts=True)
    p = pos[tv]
    n = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    kinds = {"border": [], "open": [], "crease": []}
    for s, c in zip(start, cnt):
        ts = tid[s:s + c]
        a, b = pos[ends[s, 0]], pos[ends[s, 1]]
        ids = np.unique(tri_part[ts])
        if c == 1:
            kinds["open"].append((a, b, 0.0, (int(ids[0]), -1)))
        elif len(ids) > 1:
            kinds["border"].append((a, b, 0.0, (int(ids[0]), int(ids[1]))))
        elif c == 2:
            d = np.degrees(np.arccos(np.clip(np.dot(n[ts[0]], n[ts[1]]), -1, 1)))
            kinds["crease"].append((a, b, float(d), (int(ids[0]), int(ids[0]))))
    for kind, segs in kinds.items():
        pts, ang, pp = [], [], []
        for a, b, d, ids in segs:
            k = max(2, int(np.ceil(np.linalg.norm(b - a) / spacing)) + 1)
            t = np.linspace(0, 1, k)[:, None]
            pts.append(a + (b - a) * t)
            ang.append(np.full(k, d))
            pp.append(np.tile(ids, (k, 1)))
        _SEAMS[kind] = ((np.concatenate(pts).astype(np.float32), np.concatenate(ang), np.concatenate(pp))
                        if pts else (np.zeros((0, 3), np.float32), np.zeros(0), np.zeros((0, 2), int)))
    return _SEAMS


def seams(width=1.0, kinds=("border",), crease=60.0, parts=None, exclude=(), soft=0.3):
    """A line of `width` cm along the seams of the body: the borders between body panels
    ("border"), the free edges of panels ("open": the cockpit opening, the wings' edges) and
    sharp folds ("crease", steeper than `crease` degrees). `parts`: only seams between these
    parts (names, or assemblies); `exclude`: never these. Drawn in 3D, so it follows the panel
    gaps exactly; the edge is crisp (`soft` 0.3 cm) so a thin line stays a line."""
    from scipy.spatial import cKDTree
    from tool import parts as parts_mod
    sp = _seam_points()
    P = parts_mod.load()
    def ids_of(name):  # a part by its exact name; an assembly's name takes all its parts
        exact = [i for i, inst in enumerate(P.instances) if inst["name"] == name]
        return exact or P.select(name)
    allowed = None
    if parts is not None:
        allowed = set()
        for name in parts:
            allowed.update(ids_of(name))
    banned = set()
    for name in exclude:
        banned.update(ids_of(name))
    chosen = []
    for kind in kinds:
        pts, ang, pp = sp[kind]
        keep = ang >= crease if kind == "crease" else np.ones(len(pts), bool)
        if allowed is not None:
            keep &= np.array([all(i in allowed for i in row if i >= 0) for row in pp]) if len(pp) else keep
        if banned:
            keep &= ~np.array([any(i in banned for i in row) for row in pp]) if len(pp) else keep
        chosen.append(pts[keep])
    pts = np.concatenate(chosen) if chosen else np.zeros((0, 3), np.float32)
    if not len(pts):
        return Zone(lambda p, n: np.zeros(len(p), np.float32))
    tree = cKDTree(pts)

    def dist(p, n):
        d, _ = tree.query(p.astype(np.float32), workers=-1)
        return width / 2 - d
    return field(dist, soft)


# ---- The car map (tool/carmap.py): the body's own areas, lines and positions ----

def _map():
    from tool import carmap
    return carmap.load()


AREAS = ("top", "sides", "under", "front", "back")
FACING_EDGE = 0.7  # a surface facing forward or back more than this is the front or the back


def area(name, soft=SOFT):
    """One of the body's areas, split along the car's own lines (the car map): "top" (between the
    shoulders), "sides" (from the shoulder down to where the side turns under), "under", "front"
    (facing forward: the nose's tip, the sidepods' fronts) and "back" (facing back: the tail).
    Edges crisp, where the body itself turns."""
    if name not in AREAS:
        raise KeyError(f"no area called {name!r}; known: {', '.join(AREAS)}")

    def dist(p, n):
        m = _map()
        fwd = m.level("facing_z", FACING_EDGE, p, n)     # > 0: facing forward
        back = -m.level("facing_z", -FACING_EDGE, p, n)  # > 0: facing back
        if name == "front":
            return fwd
        if name == "back":
            return back
        a1, a2 = m.across_level(p, 1), m.across_level(p, 2)
        band = {"top": -a1, "sides": np.minimum(a1, -a2), "under": a2}[name]
        return np.minimum(band, np.minimum(-fwd, -back))
    return field(dist, soft)


def outside(at_least=0.4, soft=SOFT):
    """The outer body: spots that see at least this share of the open air (the car map's "open"),
    so a graphic keeps off the insides of the inlets, the wheel pockets and the underside's recesses."""
    return field(lambda p, n: _map().level("open", at_least, p, n), soft)


def across(a0, a1, soft=SOFT):
    """A band round the body's section, the same share of the way across it all along the car (the
    car map's "across": 0 the top's middle, 1 the shoulder, 2 the lower edge, 3 the underside's
    middle), so it follows the body's shape. On both sides."""
    return field(lambda p, n: np.minimum(_map().across_level(p, a0), -_map().across_level(p, a1)), soft)


def along(a0, a1, soft=SOFT):
    """A band across the car from a0 to a1 of the way from the nose's tip (0) to the tail (1)."""
    return field(lambda p, n: np.minimum(_map().level("along", a0, p, n), -_map().level("along", a1, p, n)), soft)


def near(kind, reach, soft=SOFT):
    """Within `reach` cm of one of the car's lines (the car map's LINES: "fold", "opening", "join",
    "shoulder", "lower"). ~near(...) keeps a graphic clear of them."""
    def dist(p, n):
        m = _map()
        if kind == "shoulder":
            d = m.mark_distance(p, 1)
        elif kind == "lower":
            d = m.mark_distance(p, 2)
        else:
            d = m.distance(kind, p)
        return reach - d
    return field(dist, soft)


def line(kind, width=1.0, soft=SOFT):
    """A line `width` cm wide drawn along one of the car's lines (see near)."""
    return near(kind, width / 2, soft)


def hit(lo, hi=1.01, soft=SOFT):
    """Where the oncoming air hits the body between two strengths (the car map's hit, 0..1): the
    nose's tip and the lips round the openings take the most. Bands of it make a pressure map."""
    def dist(p, n):
        h = _map().hit(p, n)
        # the edge made crisp by how fast hit changes, which follows the facing: about 1/25 per cm
        return np.minimum(h - lo, hi - h) * 25.0
    return field(dist, soft)


def streamlines(seeds, width=1.5, step=0.5, length=450.0, soft=SOFT, both=True):
    """Lines `width` cm wide along the air's path over the body (the car map's streamlines), traced
    from seed points (x, y, z) in cm on the body: a smoke rake's row at the nose, say. both: the
    seeds mirrored onto the other side too. The traced lines are kept on the zone as .lines."""
    from scipy.spatial import cKDTree
    seeds = np.asarray(seeds, np.float64)
    if both:
        seeds = np.concatenate([seeds, seeds[np.abs(seeds[:, 0]) > 0.3] * np.array([-1.0, 1.0, 1.0])])
    lines = _map().streamlines(seeds, step, length)
    pts = np.concatenate([l for l in lines if len(l) > 1]) if lines else np.zeros((0, 3))
    tree = cKDTree(pts) if len(pts) else None

    def dist(p, n):
        if tree is None:
            return np.full(len(p), -1.0, np.float32)
        d, _ = tree.query(p.astype(np.float64), workers=-1, distance_upper_bound=width * 2)
        return (width / 2 - np.minimum(d, width * 2)).astype(np.float32)
    z = field(dist, soft)
    z.lines = lines
    return z


def rake(z, across):
    """Seed points on the body at length z, at across positions (see across): the smoke rake's row
    for streamlines. shapes.streamlines(shapes.rake(198, np.linspace(0.1, 0.9, 5)), 1.5)."""
    return _map().rake(z, across)
