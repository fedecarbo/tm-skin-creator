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

from tool import shapes, skinmesh
from tool.noise import smoothstep

STEP = 0.25       # cm: the curve resampled this finely for the distance (as carmap does: no beads)
TURN = 75.0       # degrees: the band stops where the surface faces this much away from how the
                  # curve faces. Wide on purpose -- a real fold (the shoulder) turns 60 and must
                  # still take paint -- while the far face of a panel turns about 180. See --agree.
SNAP = 3.0        # cm: a place further than this from the skin is refused
# Which way the surface faces where a place sits. The car has upstands and folds where two faces
# sit within millimetres of each other (the bonnet's centre fin, the sidepod's shoulder), and a
# bare (x, y, z) can land on either: a line along the bonnet's middle snapped onto the fin's side
# face and reversed 163 degrees round its top. Saying "up" settles it.
FACING = {"up": (0.0, 1.0, 0.0), "down": (0.0, -1.0, 0.0), "left": (1.0, 0.0, 0.0),
          "right": (-1.0, 0.0, 0.0), "side": None, "front": (0.0, 0.0, 1.0), "rear": (0.0, 0.0, -1.0)}


class Curve:
    """A curve lying on the skin: its points in cm, and what it crosses."""

    def __init__(self, skin, pts, faces, places=None, snapped=None, name=""):
        self.skin, self.name = skin, name
        self.pts = np.asarray(pts, np.float64)
        self.faces = np.asarray(faces, np.int64)
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

    def nodes(self):
        """The curve as source nodes for the surface measure: (face, [b1, b2]) per point."""
        f, b = self.skin.nearest(self.pts)
        return [(int(ff), [float(bb[1]), float(bb[2])]) for ff, bb in zip(f, b)]

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
    if isinstance(item, str):
        key = item.strip()
        if key in paintbox.SPOTS:
            spot = paintbox.SPOTS[key]
            want = np.asarray(spot["centre"], np.float64)
            nrm = np.asarray(spot["facing"], np.float64) if "facing" in spot else None
        else:
            from tool import lines as pins
            found = None
            for ln in pins.load():
                if ln["name"] == key:
                    found = np.asarray([p["pos"] for p in ln["pins"]], np.float64)
            if found is None:
                raise ValueError(f"no place called {key!r}: try one of {', '.join(paintbox.SPOTS)}, "
                                 f"a pinned line's name, or (x, y, z) in cm")
            want = found.mean(0)
    else:
        want = np.asarray(item, np.float64)
    f, b = skin.nearest(want[None], None if nrm is None else nrm[None])
    got = skin.point(f, b)[0]
    moved = float(np.linalg.norm(got - want) * 10)
    if moved > SNAP * 10:
        raise ValueError(f"the place {item!r} is {moved:.0f} mm from the skin: too far to draw on")
    return int(f[0]), b[0], want, moved


def through(items, name=""):
    """A curve through places on the car: each link the surface's own straight line. `items` is a
    list of names (paintbox.SPOTS or a pinned line) and/or (x, y, z) in cm, nose to tail or however
    you mean it to run. Two places give one straight line on the surface; add more to choose the
    route, because the shortest way between two places goes round obstacles, not over them."""
    skin = skinmesh.load()
    if len(items) < 2:
        raise ValueError("a curve needs at least two places")
    verts, snapped, asked = [], [], []
    for it in items:
        f, b, want, moved = place(skin, it)
        v = int(skin.F[f][int(np.argmax(b))])       # the geodesic chain runs corner to corner
        got = skin.V[v]
        snapped.append(float(np.linalg.norm(got - want) * 10))
        asked.append(want)
        if not verts or v != verts[-1]:
            verts.append(v)
    if len(verts) < 2:
        raise ValueError("those places all landed on the same corner of the mesh: they are too close together")
    pts = np.asarray(skin.solver("flip").find_geodesic_path_poly(verts), np.float64)
    f, _ = skin.nearest(pts)
    return Curve(skin, pts, f, places=asked, snapped=np.asarray(snapped), name=name or "a curve")


def mirror(curve, name=""):
    """The same curve on the other side of the car. The two halves of the drawing surface are their
    own geometry (skinmesh mirrors the sheet's half car), so this is a real second curve, not the
    same texels read twice: an asymmetric design stays asymmetric."""
    pts = curve.pts * [-1.0, 1.0, 1.0]
    f, _ = curve.skin.nearest(pts)
    return Curve(curve.skin, pts, f, places=None,
                 snapped=curve.snapped, name=name or f"{curve.name}, mirrored")


# ---- the paint ----

_TEXELS = {}   # canvas -> (face, bary) for its texels, worked out once


def _texel_faces(canvas, idx):
    """The face on the skin, and the weights there, of the texels the paint box is asking about."""
    key = (id(canvas), canvas.set, canvas.w, canvas.h)
    if key not in _TEXELS:
        skin = skinmesh.load()
        tri = canvas.bake["tri"].reshape(-1)[canvas.near]
        pos = canvas.pos
        f, b = skin.in_tri(tri, pos)
        _TEXELS[key] = (f, b)
    f, b = _TEXELS[key]
    return f[idx], b[idx]


def _gate_normals(curve, pts, pos, nrm):
    """Which texels the band is ALLOWED to reach: those whose surface faces the same way as the
    curve does where it passes nearest them.

    The old view-drawn band measured distance through space alone, so it painted the far face of
    any panel thinner than its half width and climbed onto a face turning away that happened to be
    near in space (the swoosh onto the sidepod's top, CHECKLIST.md:4045). Over a half width of a
    centimetre or two the real surface cannot have turned far, so the far face -- whose normal
    points the other way entirely -- is the one thing that can be told apart cheaply, per texel,
    with no solver and nothing interpolated from the mesh's corners."""
    from scipy.spatial import cKDTree
    _, j = cKDTree(pts).query(pos.astype(np.float64), workers=-1)
    return (nrm * curve.normals(pts)[np.minimum(j, len(pts) - 1)]).sum(1)


def band(curve, width, soft=shapes.SOFT, turn=TURN):
    """A zone `width` mm wide centred on a curve, measured over the car.

    The band's EDGE is the exact distance in space from the texel's own place to the curve,
    worked out per texel, so it never facets -- per-corner values on a 35 mm mesh are what made the
    old bands look like crayon. What the band may REACH is settled by whether the surface there
    faces the way the curve does, which is what keeps it off the far side of a thin panel and off
    faces turning away."""
    from scipy.spatial import cKDTree
    half = width / 20.0                                # mm across -> cm from the middle
    pts = curve.resample()
    tree = cKDTree(pts)
    limit = np.cos(np.radians(turn))

    def fn(p, n):
        d, _ = tree.query(p.astype(np.float64), workers=-1, distance_upper_bound=half * 4)
        w = smoothstep(-soft / 2, soft / 2, half - np.minimum(d, half * 4))
        live = w > 0
        if live.any():
            agree = np.zeros(len(p))
            agree[live] = _gate_normals(curve, pts, p[live], n[live])
            w = w * (agree >= limit)
        return w

    z = shapes.Zone(fn)
    z.kind, z.curve, z.width = "skin line", curve, width
    return z


def main():
    ap = argparse.ArgumentParser(description="drawing on the car's skin")
    ap.add_argument("--probe", metavar="PLACES", help="a curve through these places, comma separated")
    ap.add_argument("--agree", action="store_true", help="the two distance measures checked against each other")
    a = ap.parse_args()
    if a.probe:
        items = []
        for s in a.probe.split(","):
            s = s.strip()
            items.append(tuple(float(x) for x in s.split()) if " " in s else s)
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
