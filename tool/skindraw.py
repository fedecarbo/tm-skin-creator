"""Drawing on the car's skin: curves that are the surface's own lines, bands measured over it.

The idea (2026-09-30). A line on a car is a curve ON the surface, not a line in a picture of the
car, on a flattened pattern, or in the air near it. The surface has its own straight lines --
geodesics -- and they are smooth by construction, cannot leave the body, cannot wobble, and cross
every panel, seam and UV island without noticing. A band is then everything within n mm of such a
curve, measured over the surface, so it is the same n mm wide on the flat bonnet and round the
curve of a flank alike. Nothing here needs a camera, so nothing stops where a view turns away or
goes blind, and nothing needs a flattening, so nothing shears.

    python -m tool.skindraw --probe "nose,bonnet,tail"   the curve through those places, what it crosses
    python -m tool.skindraw --agree                      the two distance measures checked against each other

    skindraw.through(["nose", "bonnet", "tail"])          a curve through named places or (x, y, z) cm
    skindraw.band(curve, 30)                             a zone 30 mm wide on that curve, for the paint box
    skindraw.edge(place, 15)                             a line 15 mm in from the car's edge nearest a place
    skindraw.meet(curve, other)                          the curve cut where it reaches another's middle (a T)

What the exam car showed (TSC_SkinExam, 2026-10-01): 2 mm is the thinnest line the body's texture
holds whole (its texels are 0.9 mm; 1.5 and 1 mm lines go patchy), and from the game's chase cameras
3 to 4 mm reads as a line while 2 mm is faint; corners are round on the outside and whole inside;
crossings, T's (square or slanted, via meet) and a line 15 mm off the cockpit's rim all measure within
a millimetre; and a 70 mm band crosses the nose panel's raised edge.

Measured on this car, and why the primitive is what it is: the SHORTEST geodesic between two
places is not a drawing tool. Nose to tail it strays 278 mm off the centre line and kinks by 83
degrees, because the shortest way round an obstacle is round the side of it. So a curve is a chain
of geodesics through places the designer chooses: each link is the surface's own straight line, and
the route is the designer's. Add places where you want more control.

The car has a hole down the middle of its top -- the cockpit, about z = +70 to -45 -- where the
nearest up-facing skin is 8 to 28 cm out from the centre. A curve told to run down the middle
detours round it, and says so. That is the car, not the tool.
"""

import argparse

import numpy as np

from tool import paint, shapes, skinmesh
from tool.noise import smoothstep

STEP = 0.25       # cm: the curve resampled this finely for the distance (as carmap does: no beads)
NEAR = 0.15       # cm: a texel takes its offset from a ribbon point no further than this, so a
                  # texel outside the ribbon is not painted. It must be under the model's real
                  # gaps (the sidepod's top 4 mm, the inlet 14 mm, the tail 17 mm) or the band
                  # hops them, and over the ribbon's own spacing or the band comes out in pieces.
TURN = 100.0      # degrees: the band stops where the surface faces this much away from how the
                  # curve faces. Wide on purpose -- a real fold (the shoulder) turns 60 and must
                  # still take paint, and the groove where the nose panel's raised edge meets the
                  # nose turns 89 (at 75 the 70 mm nose band left three texels of its own middle
                  # bare there, 2026-10-01) -- while the far face of a thin panel turns about 180.
                  # See --agree.
SNAP = 3.0        # cm: a place further than this from the skin is refused
# Which way the surface faces where a place sits. The car has upstands and folds where two faces
# sit within millimetres of each other (the bonnet's centre fin, the sidepod's shoulder), and a
# bare (x, y, z) can land on either: a line along the bonnet's middle snapped onto the fin's side
# face and reversed 163 degrees round its top. Saying "up" settles it.
FACING = {"up": (0.0, 1.0, 0.0), "down": (0.0, -1.0, 0.0), "left": (1.0, 0.0, 0.0),
          "right": (-1.0, 0.0, 0.0), "side": None, "front": (0.0, 0.0, 1.0), "rear": (0.0, 0.0, -1.0)}


class Curve:
    """A curve lying on the skin: its points in cm, and what it crosses. `extra` is what the check
    needs to know about where it was meant to be (tool/skincheck.py): the user's pins it runs
    through, or the edge it is set in from, and how far."""

    def __init__(self, skin, pts, faces, places=None, snapped=None, name="", closed=False, extra=None):
        self.skin, self.name, self.closed = skin, name, closed
        self.extra = dict(extra or {})
        pts = np.asarray(pts, np.float64)
        faces = np.asarray(faces, np.int64)
        # Drop repeated points. Legs joined end to end share a point, and a repeat gives a zero
        # tangent, so the ribbon skipped every trace there: a ring came out a fifth painted.
        if len(pts) > 1:
            keep = np.concatenate([[True], np.linalg.norm(np.diff(pts, axis=0), axis=1) > 1e-7])
            pts, faces = pts[keep], faces[keep]
        self.pts = pts
        self.faces = faces
        self.places = places
        self.snapped = snapped                     # how far each asked-for place moved, mm
        seg = np.linalg.norm(np.diff(self.pts, axis=0), axis=1)
        self.length = float(seg.sum())
        self._turn = None

    @property
    def turn(self):
        """The turn within the surface at every point, in degrees: the crayon measure. A geodesic
        turns 0; a chain turns only where the designer put a place."""
        if self._turn is None:
            p = self.pts
            d = np.diff(p, axis=0)
            L = np.linalg.norm(d, axis=1)
            ok = L > 1e-6
            d, mid = d[ok] / L[ok, None], (p[:-1] + p[1:])[ok] / 2
            n = self.skin.fn[self.faces[:-1][ok]] if len(self.faces) == len(p) else None
            if n is None:
                f, _ = self.skin.nearest(mid)
                n = self.skin.fn[f]
            a = d[:-1] - n[:-1] * (d[:-1] * n[:-1]).sum(1)[:, None]
            b = d[1:] - n[:-1] * (d[1:] * n[:-1]).sum(1)[:, None]
            na, nb = np.linalg.norm(a, axis=1), np.linalg.norm(b, axis=1)
            good = (na > 1e-9) & (nb > 1e-9)
            c = np.zeros(len(a))
            c[good] = ((a[good] / na[good, None]) * (b[good] / nb[good, None])).sum(1)
            self._turn = np.degrees(np.arccos(np.clip(c, -1, 1)))
        return self._turn

    @property
    def parts(self):
        """The car's parts the curve runs over, in the order it meets them."""
        names, out = self.skin.part[self.faces], []
        for n in names:
            if not out or out[-1] != n:
                out.append(str(n))
        return out

    def normals(self, pts=None):
        """The way the surface faces at every point of the curve (or of `pts` along it)."""
        p = self.pts if pts is None else np.asarray(pts, np.float64)
        f, _ = self.skin.nearest(p)
        return self.skin.fn[f]

    def resample(self, step=STEP):
        """The curve as points every `step` cm, so a distance to it has no beads."""
        d = np.linalg.norm(np.diff(self.pts, axis=0), axis=1)
        s = np.concatenate([[0.0], np.cumsum(d)])
        if s[-1] < 1e-9:
            return self.pts.copy()
        t = np.arange(0.0, s[-1], step)
        return np.stack([np.interp(t, s, self.pts[:, k]) for k in range(3)], 1)

    def report(self):
        """What the curve is, in plain numbers. Read it before painting."""
        t = self.turn
        lines = [f"{self.name or 'curve'}: {self.length * 10:.0f} mm long, {len(self.pts)} points, "
                 f"turning {np.median(t):.2f} deg typical, {np.percentile(t, 95):.1f} at the 95th, {t.max():.1f} at most"]
        lines.append(f"  over: {' -> '.join(self.parts)}")
        comp = np.unique(self.skin.comp[self.faces])
        if len(comp) > 1:
            lines.append(f"  WARNING it spans {len(comp)} separate pieces of surface: a band cannot cross between them")
        if self.snapped is not None and len(self.snapped):
            worst = int(np.argmax(self.snapped))
            lines.append(f"  the places asked for moved onto the skin by {np.median(self.snapped):.0f} mm typically, "
                         f"{self.snapped[worst]:.0f} mm at most (place {worst + 1} of {len(self.snapped)})")
        bad = np.flatnonzero(t > 20.0)
        if self.places is not None and len(self.places):
            asked = np.asarray(self.places, np.float64)       # a corner at a place is the designer's own
            near = np.linalg.norm(self.pts[bad + 1][:, None] - asked[None], axis=2).min(1) < 1.5
            bad = bad[~near]
        for i in bad:
            p = self.pts[i + 1]
            lines.append(f"  a {t[i]:.0f} deg corner at (x {p[0]:.0f}, y {p[1]:.0f}, z {p[2]:.0f}) cm on the "
                         f"{self.skin.part[self.faces[i + 1]]}: it went round something. Add a place there to choose the route.")
        return "\n".join(lines)


# ---- places on the car ----

def place(skin, item):
    """One place on the skin: a name from paintbox.SPOTS, a pin's name from car/lines.json, or
    (x, y, z) in cm. Returns (face, bary, asked-for point, how far it moved in mm)."""
    from tool import paintbox
    nrm = None
    if isinstance(item, (tuple, list)) and len(item) == 4 and isinstance(item[3], str):
        word = item[3].strip().lower()
        if word not in FACING:
            raise ValueError(f"{word!r} is not a way to face: try {', '.join(FACING)}")
        item, nrm = tuple(item[:3]), FACING[word]
        if word == "side":                       # whichever flank this point is on
            nrm = (1.0 if float(item[0]) >= 0 else -1.0, 0.0, 0.0)
        nrm = np.asarray(nrm, np.float64)
    if isinstance(item, dict):                   # a pin: its place and the way the skin faces there
        want = np.asarray(item["pos"], np.float64)
        nrm = np.asarray(item["normal"], np.float64)
    elif isinstance(item, str):
        key = item.strip()
        if key not in paintbox.SPOTS:
            raise ValueError(f"no place called {key!r}: try one of {', '.join(paintbox.SPOTS)}, "
                             f"a pinned line's name (python -m tool.lines), or (x, y, z) in cm")
        spot = paintbox.SPOTS[key]
        want = np.asarray(spot["centre"], np.float64)
        nrm = np.asarray(spot["facing"], np.float64) if "facing" in spot else None
    else:
        want = np.asarray(item, np.float64)
    f, b = skin.nearest(want[None], None if nrm is None else nrm[None])
    got = skin.point(f, b)[0]
    moved = float(np.linalg.norm(got - want) * 10)
    if moved > SNAP * 10:
        raise ValueError(f"the place {item!r} is {moved:.0f} mm from the skin: too far to draw on")
    return int(f[0]), b[0], want, moved


def pinned(name):
    """A line the user pinned in the Lab's lines room (tool/lines.py), as places: its pins in the
    order they were pinned, each with the way the skin faces there. None if there's no such line."""
    from tool import lines as pins
    for ln in pins.load()["lines"]:
        if ln["name"] == name:
            return [{"pos": p, "normal": n} for p, n in zip(ln["points"], ln["normals"])]
    return None


def _expand(items):
    """Places, with a pinned line's name opened out into its pins."""
    out = []
    for it in items:
        pins = pinned(it.strip()) if isinstance(it, str) else None
        out.extend(pins if pins else [it])
    return out


def _corners(skin, items, closed=False):
    """Places as corners of the skin to run geodesics between, each place itself made a corner: its
    face split in three at the exact point. Returns a flip-geodesic solver on that surface, the
    places' corner numbers, how far each place moved onto the skin (mm), what was asked for, and
    the user's own pins among them (for the check).

    Not the nearest existing corner: the rear flank's faces are 15 to 28 mm across, so a curve run
    corner to corner passed the user's crease pins 7.6 mm off (measured on TSC_SkinExam). The solver
    takes 0.1 s to build on the whole car, so each curve gets its own."""
    import potpourri3d as pp3d
    items = _expand(items)
    pins = [it["pos"] for it in items if isinstance(it, dict)]
    if len(items) < (3 if closed else 2):
        raise ValueError(f"a {'loop' if closed else 'curve'} needs at least {3 if closed else 2} places")
    V, F = list(skin.V), [tuple(t) for t in skin.F]
    pieces = {}                                     # a face of the skin -> the faces it is split into now
    ids, snapped, asked = [], [], []
    for it in items:
        f, bary, want, moved = place(skin, it)
        bary = np.clip(bary, 0.02, 1.0)              # off the face's own edges, so no sliver
        bary /= bary.sum()
        at = (bary[:, None] * skin.V[skin.F[f]]).sum(0)
        now = pieces.get(f, [f])                     # another place may have split this face already
        face = max(now, key=lambda g: skinmesh.Skin._bary(*[np.asarray(V[F[g][c]])[None] for c in range(3)],
                                                          at[None])[0].min())
        n = len(V)
        i, j, k = F[face]
        F[face] = (i, j, n)
        F += [(j, k, n), (k, i, n)]
        pieces[f] = [g for g in now if g != face] + [face, len(F) - 2, len(F) - 1]
        V.append(at)
        snapped.append(float(np.linalg.norm(at - want) * 10))
        asked.append(want)
        ids.append(n)
    solver = pp3d.EdgeFlipGeodesicSolver(np.asarray(V, np.float64), np.asarray(F, np.int64))
    return solver, ids, np.asarray(snapped), asked, ({"pins": pins, "offset": 0.0} if pins else None)


def _legs(solver, ids):
    """The geodesic from each place to the next, end to end, and where each place falls in it."""
    legs, corners = [], []
    for a, b in zip(ids[:-1], ids[1:]):
        leg = np.asarray(solver.find_geodesic_path(int(a), int(b)), np.float64)
        if len(leg) < 2:
            raise ValueError("no way over the skin between two of the places: are they on separate pieces of the car?")
        legs.append(leg if not legs else leg[1:])
        corners.append(sum(len(x) for x in legs) - 1)
    return np.vstack(legs), corners[:-1]


def through(items, name="", smooth=0.0):
    """A curve through places on the car, passing through every one of them, each link between two
    places the surface's own straight line (a geodesic). `items` is a list of names from
    paintbox.SPOTS, pinned lines' names (the curve runs through all their pins, in order), and/or
    (x, y, z) in cm, in the order the line runs.

    Where the line changes direction at a place it has a corner there, sharp: a chevron's tip, an
    outline's corner. `smooth` (mm) rounds every corner off over that far either side of its place,
    for a line meant to flow through its places (the user's pins along a crease); the rounding
    cuts inside the corner by a fraction of a millimetre for the few degrees a flowing line turns.

    Until 2026-10-01 this pulled the whole chain tight (geometry-central's find_geodesic_path_poly
    shortens the path through all the places at once, keeping only which side of each place it
    goes), so a middle place chose the way round and was not passed through: TSC_Skin's hoop ran
    196 mm from its places, Solstice's sweep 217 mm, the user's side crease 92 mm from their pins,
    and a chevron came out a straight line. That is `taut`, kept for the cars drawn with it."""
    skin = skinmesh.load()
    solver, ids, snapped, asked, extra = _corners(skin, items)
    pts, corners = _legs(solver, ids)
    if smooth > 0 and corners:
        pts = _round_corners(skin, pts, corners, smooth / 10.0)
    f, _ = skin.nearest(pts)
    return Curve(skin, pts, f, places=asked, snapped=snapped, name=name or "a curve", extra=extra)


def taut(items, name=""):
    """The shortest line over the skin from the first place to the last, pulled taut like a string
    and kept on the same side of each place in between: the places choose the way round (which side
    of the cockpit), and are NOT passed through -- measured, up to 217 mm from them. Smooth by
    construction, with no corner anywhere. TSC_Skin, TSC_SkinMore and TSC_Solstice were drawn with
    it (it was `through` until 2026-10-01); for a line that must pass through its places, `through`."""
    skin = skinmesh.load()
    solver, ids, snapped, asked, extra = _corners(skin, items)
    pts = np.asarray(solver.find_geodesic_path_poly(ids), np.float64)
    f, _ = skin.nearest(pts)
    return Curve(skin, pts, f, places=asked, snapped=snapped, name=name or "a curve", extra=extra)


def _round_corners(skin, pts, at, reach):
    """Each corner of a chain (the indices `at`) rounded off over `reach` cm either side: the stretch
    replaced by a curve that leaves and rejoins the chain along it (a quadratic Bezier on the corner,
    put back on the skin a point at a time, each by the skin's face that agrees with the chain's
    own normal there, so it can't land on another face)."""
    pts = np.asarray(pts, np.float64)
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    keep_from, out = 0, []
    for k, i in enumerate(at):
        prev_c = s[at[k - 1]] if k > 0 else 0.0
        next_c = s[at[k + 1]] if k + 1 < len(at) else s[-1]
        r = min(reach, (s[i] - prev_c) * 0.45, (next_c - s[i]) * 0.45)
        if r <= 1e-3:
            continue
        i0 = int(np.searchsorted(s, s[i] - r))
        i1 = int(np.searchsorted(s, s[i] + r))
        a = np.array([np.interp(s[i] - r, s, pts[:, c]) for c in range(3)])
        b = np.array([np.interp(s[i] + r, s, pts[:, c]) for c in range(3)])
        u = np.linspace(0.0, 1.0, max(int(2 * r / 0.05), 8))[:, None]
        bez = (1 - u) ** 2 * a + 2 * u * (1 - u) * pts[i] + u ** 2 * b
        f, _ = skin.nearest(pts[i0:i1 + 1])
        nrm = skin.fn[np.maximum(f, 0)].mean(0)
        fb, bb = skin.nearest(bez, np.repeat(nrm[None], len(bez), 0))
        out.append(pts[keep_from:i0])
        out.append(skin.point(fb, bb))
        keep_from = i1
    out.append(pts[keep_from:])
    return np.vstack([o for o in out if len(o)])


def circle(centre, radius, name=""):
    """A true circle on the car: every point `radius` mm from the centre, measured over the skin.

    Not a polygon through places. A ring built by joining places has a corner at every one of
    them -- measured, 25 degrees per 100 mm on an 11-place ring, and you could count its corners in
    the picture. Here a geodesic is walked out from the centre every degree, all the same length,
    and their ends are the circle. On a flat panel it is a circle; on a curved one it is what a
    circle IS on that surface, the way a ring of vinyl would lie."""
    skin = skinmesh.load()
    f, b, want, moved = place(skin, centre)
    r = radius / 10.0
    n = skin.fn[f]
    e1 = np.cross(n, [0.0, 0.0, 1.0])
    if np.linalg.norm(e1) < 1e-6:
        e1 = np.cross(n, [1.0, 0.0, 0.0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(n, e1)
    tracer = skin.tracer()
    pts, short = [], 0
    for a in np.radians(np.arange(0.0, 360.0, 1.0)):
        d = np.cos(a) * e1 + np.sin(a) * e2
        path = np.asarray(tracer.trace_geodesic_from_face(int(f), np.asarray(b, np.float64), d * r), np.float64)
        if len(path) < 2:
            short += 1
            continue
        walked = np.linalg.norm(np.diff(path, axis=0), axis=1).sum()
        if walked < r * 0.98:
            short += 1                               # it ran off the car before the radius
        pts.append(path[-1])
    pts = np.asarray(pts)
    pts = np.vstack([pts, pts[:1]])
    fc, _ = skin.nearest(pts)
    c = Curve(skin, pts, fc, places=[want], snapped=np.asarray([moved]),
              name=name or f"a {radius:.0f} mm circle", closed=True)
    c.short = short
    return c


def loop(items, name=""):
    """A closed curve through places on the car: a ring, an outline, anything that comes back to
    where it started. Each link is the surface's own straight line, as `through`, and the ends
    join, so the band has no cap and no seam."""
    skin = skinmesh.load()
    # Link by link, each one the shortest way between two neighbouring places, and NOT shortened
    # as a whole. Anything that shortens a closed curve pulls it tight, and a ring drawn on a panel
    # can be pulled to nothing: asked for a ring on the engine cover, find_geodesic_loop gave back
    # 98 mm with a 180 degree corner, and closing the chain and shortening that gave 18 mm. A ring
    # on a car is not the shortest loop through its places; it is the loop THROUGH them.
    solver, ids, snapped, asked, extra = _corners(skin, items, closed=True)
    pts, _ = _legs(solver, ids + ids[:1])
    f, _ = skin.nearest(pts)
    return Curve(skin, pts, f, places=asked, snapped=snapped, name=name or "a loop", closed=True, extra=extra)


def parallel(curve, mm, name=""):
    """The curve moved `mm` sideways over the skin, every point the same distance from it along the
    surface: a line exactly parallel to another however the car curves between them. Positive is
    to the curve's left as it runs, seen from outside the car (for a line run nose to tail on the
    car's left flank, that is upwards). Bands on parallels of one curve keep their gaps exact, the
    way a tricolour stripe's colours must, where offsetting in a picture or in the air would open
    and close them over every fold."""
    skin = curve.skin
    d = mm / 10.0
    pts = curve.resample(0.2)
    if abs(d) < 1e-9:
        f, _ = skin.nearest(pts)
        return Curve(skin, pts, f, name=name or curve.name, closed=curve.closed)
    f, b = skin.nearest(pts)
    tan = np.gradient(pts, axis=0)
    n = skin.fn[np.maximum(f, 0)]
    tan = tan - n * (tan * n).sum(1)[:, None]
    tan /= np.maximum(np.linalg.norm(tan, axis=1, keepdims=True), 1e-12)
    side = np.cross(n, tan) * np.sign(d)
    tracer = skin.tracer()
    out = []
    for k in range(len(pts)):
        if f[k] < 0:
            continue
        path = np.asarray(tracer.trace_geodesic_from_face(int(f[k]), b[k], side[k] * abs(d)), np.float64)
        if len(path) >= 2 and np.linalg.norm(np.diff(path, axis=0), axis=1).sum() >= abs(d) * 0.98:
            out.append(path[-1])                     # a walk cut short by the car's edge leaves a gap
    out = np.asarray(out)
    fo, _ = skin.nearest(out)
    extra = dict(curve.extra)
    if "offset" in extra:
        extra["offset"] = extra["offset"] + mm
    if "from_edge" in extra:
        extra["from_edge"] = extra["from_edge"] + mm      # an edge line runs with the edge on its right
    return Curve(skin, out, fo, name=name or f"{curve.name}, {mm:+.0f} mm", closed=curve.closed, extra=extra)


def mirror(curve, name=""):
    """The same curve on the other side of the car. The two halves of the drawing surface are their
    own geometry (skinmesh mirrors the sheet's half car), so this is a real second curve, not the
    same texels read twice: an asymmetric design stays asymmetric."""
    pts = curve.pts * [-1.0, 1.0, 1.0]
    f, _ = curve.skin.nearest(pts)
    extra = dict(curve.extra)
    for key in ("pins", "edge"):
        if key in extra:
            extra[key] = [[-p[0], p[1], p[2]] for p in extra[key]]
    if "offset" in extra:
        extra["offset"] = -extra["offset"]                # the mirror runs the other way round
    return Curve(curve.skin, pts, f, places=None, snapped=curve.snapped,
                 name=name or f"{curve.name}, mirrored", closed=curve.closed, extra=extra)


def rim(near, start=None, end=None, smooth=0.0, name=""):
    """The car's own edge nearest a place -- the cockpit's rim, an opening's lip -- as a curve run
    with the skin on its left, so parallel(rim(...), +mm) is a line set mm in from the edge. With
    `start` and `end`, only the stretch between those places, the way the edge runs.

    The edge is the model's own, corner to corner. Some are clean -- the cockpit's rim turns 9
    degrees at the 95th between neighbouring corners, and a line 15 mm in from it holds 14.6 to 14.8
    mm (straight-line; over the skin it is 15) -- and some are ragged: the cut-out by the rear wheel
    turns up to 165 degrees where hidden skin was trimmed, and a line walked off every corner of a
    zigzag is a zigzag. `smooth` (cm) blurs the edge along its length and puts it back on the skin,
    but measured on the cockpit it made a clean edge worse (snapping back jitters between faces:
    turns of 45 degrees at 1 cm), so it is off unless an edge needs it. Not tried on a ragged edge;
    the clean one measured is the cockpit's rim.

    Tried first and dropped: the line as a contour of distance from the edge by geometry-central's
    heat method. Against the straight-line distance near the cockpit's rim it was out by -18 to +22
    mm, and a distance over the skin can't be shorter than the straight line."""
    skin = skinmesh.load()
    p0 = place_point(skin, near)
    loops = skin.loops
    k = int(np.argmin([np.linalg.norm(skin.V[lp] - p0, axis=1).min() for lp in loops]))
    loop = np.asarray(loops[k])
    closed = start is None or end is None
    if not closed:
        i0 = int(np.argmin(np.linalg.norm(skin.V[loop] - place_point(skin, start), axis=1)))
        i1 = int(np.argmin(np.linalg.norm(skin.V[loop] - place_point(skin, end), axis=1)))
        loop = loop[(i0 + np.arange((i1 - i0) % len(loop) + 1)) % len(loop)]
    raw = skin.V[loop]
    ring = np.vstack([raw, raw[:1]]) if closed else raw
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(ring, axis=0), axis=1))])
    t = np.arange(0.0, s[-1], 0.2)
    pts = np.stack([np.interp(t, s, ring[:, c]) for c in range(3)], 1)
    if smooth > 0:
        from scipy.ndimage import gaussian_filter1d
        pts = gaussian_filter1d(pts, smooth / 0.2, axis=0, mode="wrap" if closed else "nearest")
    f, b = skin.nearest(pts)
    pts = skin.point(f, b)
    if closed:
        pts, f = np.vstack([pts, pts[:1]]), np.concatenate([f, f[:1]])
    return Curve(skin, pts, f, places=[p0], name=name or "the edge", closed=closed,
                 extra={"edge": [[round(float(v), 3) for v in p] for p in raw], "from_edge": 0.0})


def edge(near, mm, start=None, end=None, smooth=0.0, name=""):
    """A line `mm` in from the car's own edge nearest a place (see `rim`), every point of it walked
    exactly `mm` over the skin from the smoothed edge. Where the edge curves in towards the skin, the
    walks from either side cross; the points they leave nearer the edge than `mm` are dropped, so the
    line takes the corner as a coachline would rather than tying a knot in it."""
    edge_curve = rim(near, start, end, smooth)
    line = parallel(edge_curve, mm, name=name or f"{mm:g} mm in from the edge")
    from scipy.spatial import cKDTree
    d, _ = cKDTree(edge_curve.resample(0.05)).query(line.pts)
    keep = d >= mm / 10.0 * 0.8
    if line.closed:
        keep[-1] = keep[0]
    pts = line.pts[keep]
    if line.closed and np.linalg.norm(pts[-1] - pts[0]) > 1e-6:
        pts = np.vstack([pts, pts[:1]])
    f, _ = edge_curve.skin.nearest(pts)
    line = Curve(edge_curve.skin, pts, f, places=edge_curve.places, name=line.name, closed=line.closed,
                 extra=line.extra)
    line.dropped = int((~keep).sum())
    return line


def meet(curve, other, name=""):
    """The curve cut where it first reaches the middle of `other`: a line that ends ON another (a T).
    Run the curve on past the other line and this finds the crossing exactly; places snap to the
    skin's corners up to 5 mm off, so a curve aimed at another line's middle lands beside it.

    Its band then ends along the other line's middle, not square to itself: a 3 mm line meeting a
    4 mm one at 30 degrees, cut square, pokes one corner out past the far edge and leaves a gap under
    the near one. Paint the other line after it, on top, and the join is clean at any angle."""
    from scipy.spatial import cKDTree
    pts, _ = _even(curve.pts, 0.02)
    theirs, _ = _even(other.pts, 0.02)
    d, j = cKDTree(theirs).query(pts)
    close = np.flatnonzero(d < 0.1)
    if not len(close):
        raise ValueError(f"{curve.name} never reaches {other.name}: run it on past the line it meets")
    i = int(close[0])
    run = close[close - i == np.arange(len(close))]          # the first stretch within 1 mm
    i = int(run[np.argmin(d[run])])
    hit = theirs[j[i]]
    keep = np.vstack([pts[:i], hit[None]])
    f, _ = curve.skin.nearest(keep)
    out = Curve(curve.skin, keep, f, places=curve.places, snapped=curve.snapped,
                name=name or curve.name, extra=curve.extra)
    k = int(j[i])
    tan = theirs[min(k + 1, len(theirs) - 1)] - theirs[max(k - 1, 0)]
    n = curve.skin.fn[f[-1]]
    s = np.cross(n, tan)
    s /= max(np.linalg.norm(s), 1e-12)
    if (keep[0] - hit) @ s < 0:
        s = -s                                       # towards where the curve came from
    out.stop = (hit, s)
    # the curve as drawn runs on past the middle, so the band's corner on the far side of the cut
    # has paint to cut: a band stopping at the middle, square, would leave that corner short
    out.run_on = pts[i + 1:i + 1 + 100]
    out.extra = dict(out.extra, meets=other.name)
    return out


def _even(pts, step):
    """Points every `step` cm along a polyline, and how far along each is."""
    pts = np.asarray(pts, np.float64)
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    if s[-1] < 1e-9:
        return pts.copy(), s
    t = np.arange(0.0, s[-1] + 1e-9, step)
    return np.stack([np.interp(t, s, pts[:, c]) for c in range(3)], 1), t


def place_point(skin, item):
    """The point on the skin a place lands on (cm)."""
    f, b, _, _ = place(skin, item)
    return skin.point([f], [b])[0]


# ---- the paint ----

def _faces_of(pos, nrm):
    """The face on the skin under each point a zone is asked about.

    The normal matters: where two pieces of the model almost touch -- the rear flank and the tail
    corner are under a millimetre apart -- asking only for the nearest face gives whichever, and a
    band on one piece then counted as being on the other and was painted. Measured before this:
    34.6 cm2 of the flank sweep on the tail corner, a piece its curve never walked."""
    if shapes.PAINTING not in (None, "Skin"):
        return None
    skin = skinmesh.load()
    f, _ = skin.nearest(np.asarray(pos, np.float64), np.asarray(nrm, np.float64))
    return f


def _ribbon(curve, half, soft, along=0.05, across=0.025):
    """The band's own surface, as a cloud of points each carrying how far it is from the curve
    ALONG THE SURFACE (cm, signed).

    Why not simply the distance through space, which is what the first try used: across a sharp
    fold -- the shoulder, the sidepod's edge -- the straight line through the air is shorter than
    the way over the skin, so a band set by it narrows exactly where the car bends most. Measured
    on TSC_Skin's hoop, which crosses the fold from the flank onto the engine cover: 2.96 mm out of
    40 at the 95th percentile. Here every point is reached by walking the surface with an exact
    geodesic (potpourri3d's tracer), so its offset is the real one, and the cloud is fine enough
    (0.25 mm across) that a texel takes its offset from a point nearer than a quarter of a texel.
    """
    skin = curve.skin
    pts = curve.resample(along)
    f, b = skin.nearest(pts)
    d = np.gradient(pts, axis=0)
    nrm = skin.fn[np.maximum(f, 0)]
    tan = d - nrm * (d * nrm).sum(1)[:, None]
    tan /= np.maximum(np.linalg.norm(tan, axis=1, keepdims=True), 1e-12)
    side = np.cross(nrm, tan)
    # Past the edge by the feather's outer half and a step, so the last points walked are clear of
    # the paint. A texel beyond the ribbon takes the offset of the nearest point within NEAR, and
    # with the walks stopping at 1.15 times the half width a thin line's last points sat ON its edge
    # (a 3 mm line's at 1.5 mm, half strength): every texel up to NEAR past them copied that, and a
    # 3 mm pinstripe wore a 1.6 mm half-gold fringe each side (measured 2026-10-01; the 4 mm hairline
    # that came out 0.8 mm wide was this).
    reach = max(half * 1.15, half + soft / 2.0 + 2 * across)
    out, off = [pts], [np.zeros(len(pts))]
    tracer = skin.tracer()

    def walk(k, direction, sign):
        path = np.asarray(tracer.trace_geodesic_from_face(int(f[k]), b[k], direction * reach), np.float64)
        if len(path) < 2:
            return
        s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))])
        t = np.arange(across, s[-1], across)
        if len(t):
            out.append(np.stack([np.interp(t, s, path[:, c]) for c in range(3)], 1))
            off.append(t * sign)

    for sign in (1.0, -1.0):
        for k in range(len(pts)):
            if f[k] >= 0:
                walk(k, side[k] * sign, sign)
    # Round every turn. Where the curve turns, the walks either side of the turn fan apart on its
    # outside and leave a wedge no walk reaches, a notch in the band's outer edge: at a chevron's tip
    # or an outline's corner, the whole width of the band. More walks from the turn's own point,
    # swept across the wedge, fill it the way a brush rounding a corner would. Both sides get them:
    # which side is the outside was guessed from the turn in space, and where TSC_Skin's spine hugs
    # the cockpit's rim (52 degrees in 5 mm, over the rim's rolled lip) it guessed wrong and left a
    # bite out of the band. On the inside the added walks are harmless, since a texel takes the
    # least distance its nearest ribbon points give (band).
    for k in range(len(pts) - 1):
        if f[k] < 0:
            continue
        ang = np.arccos(np.clip(side[k] @ side[k + 1], -1.0, 1.0))
        extra = int(np.ceil(ang * reach / across))
        if extra < 2:
            continue
        for i in range(1, extra):
            u = i / extra
            d = (1 - u) * side[k] + u * side[k + 1]
            d = d - nrm[k] * (d @ nrm[k])
            d /= max(np.linalg.norm(d), 1e-12)
            for sign in (1.0, -1.0):
                walk(k, d * sign, sign)
    return np.vstack(out), np.concatenate(off)


def band(curve, width, soft=shapes.SOFT, turn=TURN):
    """A zone `width` mm wide centred on a curve, measured over the car.

    The width is the real one on the skin: every texel takes its distance from the curve off a
    cloud of points walked out from it by exact geodesics, so the band is as wide over a fold as
    it is on a flat panel. Nothing is interpolated from the mesh's corners -- per-corner values on
    a 35 mm mesh are what made the old bands look like crayon -- and the cloud is finer than a
    texel, so the edge is smooth. Whether the surface faces the way the curve does is still
    checked, to keep paint off the far side of a thin panel.

    The feather is two texels at most (`soft`), and a third of the width on a thin line, but never
    under a texel: the full 2 mm feather on a pinstripe left a 1 mm line at 84 % of its colour even
    in its middle, a blur rather than a line."""
    from scipy.spatial import cKDTree
    half = width / 20.0                                # mm across -> cm from the middle
    soft = min(soft, max(paint.TEXEL_CM, width / 30.0))
    run_on = getattr(curve, "run_on", None)
    if run_on is not None and len(run_on):
        longer = np.vstack([curve.pts, run_on])
        lf, _ = curve.skin.nearest(longer)
        pts, off = _ribbon(Curve(curve.skin, longer, lf), half, soft)
    else:
        pts, off = _ribbon(curve, half, soft)
    tree = cKDTree(pts)
    face, _ = curve.skin.nearest(pts)
    ribbon_n = curve.skin.fn[np.maximum(face, 0)]      # which way the skin faces at each ribbon point
    # The band may only land on the piece of surface it walked on. Distance alone -- however
    # measured -- lets paint hop onto a piece the curve never touched but that lies near it in
    # space: measured on TSC_Skin, the spine put 97 cm2 on the tail panel and the flank sweep
    # 61 cm2 on the tail corner, both on the tail, which is its own piece across a real gap in the
    # model. Gating on the piece rather than on the faces walked leaves no holes: a face the
    # ribbon crossed but whose centre it did not fall nearest is still on the same piece.
    walked = np.zeros(int(curve.skin.comp.max()) + 1, bool)
    walked[curve.skin.comp[face[face >= 0]]] = True
    spine = curve.resample()
    spine_tree = cKDTree(spine)
    limit = np.cos(np.radians(turn))
    # The band stops at the curve's ends. Without this a texel past the end takes its offset from
    # the last ribbon point, which is small, and the band grows a cap: measured, the flank sweep
    # put 61 cm2 round onto the tail corner, a part its curve never ran over.
    # Square to the curve's last centimetre, not its last step: a geodesic arriving at its end place
    # can bend in its final millimetres, and the end cut by the last 2.5 mm alone came out slanted
    # across TSC_Skin's spine, a staircase of texels (2026-10-01).
    head, tail = spine[0], spine[-1]
    d_head, d_tail = spine[0] - spine[min(4, len(spine) - 1)], spine[-1] - spine[max(-5, -len(spine))]
    d_head /= max(np.linalg.norm(d_head), 1e-9)
    d_tail /= max(np.linalg.norm(d_tail), 1e-9)
    stop = getattr(curve, "stop", None)

    def fn(p, n, face=None):
        p = p.astype(np.float64)
        rough, _ = spine_tree.query(p, workers=-1, distance_upper_bound=half * 3)
        live = np.isfinite(rough)
        w = np.zeros(len(p), np.float32)
        if not live.any():
            return w
        d, j = tree.query(p[live], k=8, workers=-1, distance_upper_bound=NEAR)
        good = np.isfinite(d[:, 0])
        reach = np.full(int(live.sum()), np.inf)
        # How far over the skin, not through the air: the nearest ribbon point's own offset. Inside a
        # corner the walks of both arms overlap, and the nearest point can be one of the far arm's,
        # walked out past ITS edge, while the near arm puts the texel well inside the band: a chevron's
        # tip came out with dark texels inside it. A point's offset plus the way to it is never less
        # than the texel's own distance, so the least of those over the nearest few corrects it, and
        # on a plain stretch the nearest point's offset is already the least.
        jj = np.minimum(j, len(off) - 1)
        bound = np.where(np.isfinite(d), np.abs(off[jj]) + d, np.inf).min(1)
        reach[good] = np.minimum(np.abs(off[jj[good, 0]]), bound[good])
        wl = smoothstep(-soft / 2, soft / 2, half - reach)
        # The far side of a thin panel is close in space and faces the other way: keep it off. Any
        # of the nearest few ribbon points facing the texel's way will do, not only the nearest: in
        # the groove where the nose panel's raised edge meets the nose (two faces 89 degrees apart
        # within millimetres) the nearest was often on the other face, and the 70 mm nose band had
        # five unpainted texels on its own middle. Every point near the far side of a thin panel
        # faces the other way, so that stays off.
        agree = np.ones(len(wl))
        hot = wl > 0
        if hot.any():
            ok_j = np.isfinite(d[hot])
            facing = (n[live][hot][:, None, :] * ribbon_n[jj[hot]]).sum(2)
            agree[hot] = np.where(ok_j, facing, -1.0).max(1)
        ok = agree >= limit
        q = p[live]
        if not curve.closed:   # a ring has no ends: this test cut a closed ring to a fifth of itself
            ok &= (q - head) @ d_head <= 0
            if stop is None:
                ok &= (q - tail) @ d_tail <= 0
            else:              # it ends on another line: cut along that line's middle (meet)
                ok &= (q - stop[0]) @ stop[1] >= 0
        here = _faces_of(q, n[live])
        if here is not None:
            ok &= (here >= 0) & walked[curve.skin.comp[np.maximum(here, 0)]]
        w[live] = wl * ok
        return w

    z = shapes.Zone(fn)
    z.kind, z.curve, z.width, z.soft = "skin line", curve, width, soft
    return z


def main():
    ap = argparse.ArgumentParser(description="drawing on the car's skin")
    ap.add_argument("--probe", metavar="PLACES", help='a curve through these places, comma separated: '
                    'names ("bonnet", a pinned line) or "x y z [facing]" in cm')
    ap.add_argument("--agree", action="store_true", help="the two distance measures checked against each other")
    a = ap.parse_args()
    if a.probe:
        items = []
        for s in a.probe.split(","):
            words = s.split()
            try:                                     # "x y z" in cm, perhaps with a facing word
                nums = tuple(float(x) for x in words[:3])
                items.append(nums + tuple(words[3:4]) if len(words) > 3 else nums)
            except ValueError:                       # a name: a spot or a pinned line
                items.append(s.strip())
        print(through(items, name=a.probe).report())
    if a.agree:
        agree()


def agree():
    """What the gate does, by number: a band drawn along the bonnet's middle, then every texel the
    distance alone would paint, and which of them the gate throws out and why."""
    import time
    from tool import bake, skinmesh
    skin = skinmesh.load()
    c = through([(0.0, 62.0, 140.0, "up"), (0.0, 65.0, 120.0, "up"), (0.0, 70.0, 95.0, "up")],
                name="a line along the bonnet's middle")
    print(c.report())
    b = bake.bake("Skin", 2048, 2048)
    pos, nrm = b["position"].reshape(-1, 3), b["normal"].reshape(-1, 3)
    cov = b["tri"].reshape(-1) >= 0
    idx = np.flatnonzero(cov)
    pos, nrm = pos[idx], nrm[idx]
    t = time.time()
    z = band(c, 30)
    w = z(pos, nrm)
    print(f"\na 30 mm band over {len(idx)} texels in {time.time() - t:.1f}s")
    # what the distance alone would have painted
    from scipy.spatial import cKDTree
    pts = c.resample()
    d, j = cKDTree(pts).query(pos, workers=-1)
    near = d <= 30 / 20.0
    agree_v = (nrm * c.normals(pts)[np.minimum(j, len(pts) - 1)]).sum(1)
    thrown = near & (agree_v < np.cos(np.radians(TURN)))
    print(f"  within 15 mm in space: {int(near.sum())} texels")
    print(f"  of those, the gate throws out {int(thrown.sum())} ({100 * thrown.mean() / max(near.mean(), 1e-9):.1f} %)")
    if thrown.any():
        f, _ = skin.in_tri(b["tri"].reshape(-1)[idx][thrown], pos[thrown])
        on = f >= 0
        names, cnt = np.unique(skin.part[f[on]], return_counts=True)
        for n, k in sorted(zip(names, cnt), key=lambda x: -x[1])[:6]:
            print(f"     {k:6d} on the {n}")
        print(f"     they face the curve at {np.percentile(agree_v[thrown], [5, 50, 95]).round(2)} (cos), "
              f"i.e. {np.degrees(np.arccos(np.clip(np.percentile(agree_v[thrown], 50), -1, 1))):.0f} deg away typically")
    print(f"\n  painted in the end: {int((w > 0.5).sum())} texels, {100 * (w > 0.5).sum() / len(idx):.2f} % of the skin")


if __name__ == "__main__":
    main()
