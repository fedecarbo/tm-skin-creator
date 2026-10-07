"""A course: a path along one of the car's own lines, and markings laid along it. The user, 2026-10-05,
drawing with the Lab's pen: "Do an interval lines with DO NOT STEP text." A marking belongs to a line
of the car (one of its own creases or rolled edges, a seam, a panel's edge) or to the line
the user drew, and the tool lays it along that line in one go: a strip, dashes, ticks, spots or words.

    course.seam("side skirt")                a seam (tool/seams.py), the left side
    course.edge("sidepod top", near=(55, 61, -40))   a panel's edge: its outline (the loop nearest `near`,
                                             else the longest), the panel on its left as it runs, seen from
                                             outside; side="left" picks the panel's instance
    meshlines.line(point), meshlines.picked(points)   the model's own lines, exact (tool/meshlines.py), as courses
    course.stroke(points)                   the line the user drew (tool.notes show_drawn prints its points):
                                             smoothed over SMOOTH cm and laid on the body
    course.points([(x, y, z), ...])          any points on the car, joined straight
    course.Courses([a, b], "the contour")    several courses marked alike: a marking is every one's, in one zone
  Shaped:
    c.between(-128, -50)                     the stretch between two lengths along the car, or two points
                                             (on a loop: from the first to the second the way it runs)
    c.then(other)                            on along another course (joined straight where they don't meet: the
                                             join shows as a step; one line whole, or one beside it, runs smooth)
    c.rounded(8)                             its corners rounded over 8 cm
    c.extended(start=3)                      carried on straight 3 cm before its start (under a frame)
    c.offset(14)                             a line beside it, 14 cm across the surface to its left all along (- its
                                             right): a band of even width along one of the model's lines
    c.mirrored()                             the same on both sides; c.reversed() the other way
    c.panels(3)                              cut at each seam between the body's panels it crosses, a piece per
                                             panel stopping 1.5 cm short of each edge it ends at (a seam, an
                                             opening's frame): a marking applied panel by panel, as tape is;
                                             .without("nose tip") leaves those panels' pieces off
    c.length, c.start, c.middle, c.end, c.at(z=-70), c.at(s=20)   points on it (cm)
    c.places(every=20)                       points every 20 cm along it, a whole gap at each end, for marks
  Markings, as zones (tool/shapes.py) for s.paint(..., zone=), measured across the surface:
    c.strip(1.0)                             a strip 1 cm wide along it, its ends square
    c.inked(0.6)                             the same drawn on the flat texture, one smooth curve per piece of it
    c.inked_edge(shapes.below(26))           a zone whose edge is moved onto the course, drawn the same way
    c.dashes(5, gap=3, width=1)              dashes 5 cm long with 3 cm gaps, a whole dash at each end
    c.dashes(2.5, width=5, slant=45)         stripes across a 5 cm strip, slanted 45 degrees: hazard tape
    c.blocks(5, 2.5)                         two rows of blocks 5 cm long and 2.5 high, alternating: block tape
    c.ticks(every=10, length=3, width=0.6, side=1)   short strokes square to it every 10 cm, to its left (+1),
                                             its right (-1) or both ways (0)
    s.text("NO STEP", "engine cover", at=c.between(-74, -62))   words (a placard, a mark) at a stretch's
                                             middle, reading along it, upright to someone beside the car
A marking lands only on skin facing within FACING of the course's own surface, never on the far side
of a thin panel. The checks (tool/checks.py) read each dash and tick as they read any small mark.
Close up where the model's flat faces are big (the nose root, the sidepods' fronts, the tail), a line
bends where it crosses a fold between two of them, as the body does: those corners are the model's,
and no way of drawing the line takes them out (measured 2026-10-06: 6 to 12 degrees with the folds at
the nose root, 1 to 5 along the surface; the texture's flat layout stretches some facets of the nose
and the rear flank by a quarter or more, so a curve drawn smooth there comes out less smooth).
"""

import numpy as np
from scipy.spatial import cKDTree

from tool import shapes
from tool.noise import smoothstep

STEP = 0.25    # cm between a course's points
SPECK = 1.0    # cm: a run of another part this short under a course is the mesh's noise, not a panel
MIDDLE = 1.0   # cm from the car's middle: a course's end there meets its mirror image
CORNER = 45.0  # degrees within 2 cm: a corner of the body a marking stops short of (the tail corner's end)
SMOOTH = 2.5   # cm: the surface's facing along a course, and a stroke's path, are averaged over this
FACING = 0.5   # a texel takes a marking when it faces within 60 degrees of the course's surface there
OFF = 3.0      # cm: a stroke's point further than this from the body is dropped
MIRROR = np.array([-1.0, 1.0, 1.0])
INK_KNOT = 8.0     # cm between the knots of the curve an inked strip follows on each piece of the flat texture
INK_REACH = 10.0   # cm either side of a course an inked edge moves the zone's edge across: all the way to the zone's own
# edge (at 4 a sliver stayed unpainted by the inlet's frame, the user, 2026-10-06: "There's a clear gap that is not
# painted here")
INK_GAP = 4        # course points (a centimetre) a run on one piece may skip and still be one run
OFFSET_KNOT = 6.0  # cm along a course between the knots of the smooth curve a line beside it is drawn as
FOLD = 45.0        # degrees from a course's own facing: past its end, where the surface has turned this far is the fold
FOLD_RUN = 3.0     # cm past a course's end an inked strip looks for the fold
INK_BLEED = 3.0    # cm: a texel near an inked edge on a piece of the texture the course doesn't cross (the sliver where
# the body turns in to an inlet's frame) takes the nearest inked texel's side within this


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


def _resample(pts, step=STEP, closed=False):
    """Points every `step` cm along a polyline (the last point kept)."""
    pts = np.asarray(pts, np.float64)
    if closed and len(pts) > 1 and np.linalg.norm(pts[0] - pts[-1]) > 1e-6:
        pts = np.vstack([pts, pts[:1]])
    keep = np.r_[True, np.linalg.norm(np.diff(pts, axis=0), axis=1) > 1e-9]
    pts = pts[keep]
    if len(pts) < 2:
        return pts
    s = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    u = np.arange(0.0, s[-1], step)
    if s[-1] - u[-1] > step / 2:
        u = np.r_[u, s[-1]]
    else:
        u[-1] = s[-1]
    return np.stack([np.interp(u, s, pts[:, k]) for k in range(3)], 1)


def _smooth(v, cm, closed=False):
    """A running mean over `cm` along the points (the ends held)."""
    k = max(1, int(round(cm / STEP)))
    if k < 2 or len(v) < 3:
        return v
    if closed:
        pad = np.concatenate([v[-k:], v, v[:k]])
    else:
        pad = np.concatenate([np.repeat(v[:1], k, 0), v, np.repeat(v[-1:], k, 0)])
    out = np.stack([np.convolve(pad[:, c], np.ones(k) / k, mode="same") for c in range(v.shape[1])], 1)
    return out[k:k + len(v)]


def _facing(pts, closed=False):
    """The body's facing along the points: the car map's smoothed normals, averaged over SMOOTH."""
    from tool import carmap
    m = carmap.load()
    n = np.stack([m.value(f"facing_{a}", pts) for a in "xyz"], 1).astype(np.float64)
    n[:, 0] *= np.sign(pts[:, 0] + 1e-9)  # the map keeps the left's facing_x; the right faces the other way
    n = _smooth(n, SMOOTH, closed)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)


def _tangent(pts, closed=False):
    if closed:
        t = np.roll(pts, -1, 0) - np.roll(pts, 1, 0)
    else:
        t = np.gradient(pts, axis=0) if len(pts) > 1 else np.zeros_like(pts)
    return t / np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)


class Course:
    def __init__(self, pts, name, nrm=None, closed=False, mirror=False):
        given = np.asarray(pts, np.float64)
        self.pts = _resample(given, STEP, closed)
        self.name, self.closed, self.mirror = name, closed, mirror
        self.s = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(self.pts, axis=0), axis=1))]
        self.tan = _tangent(self.pts, closed)
        if nrm is not None and len(nrm) != len(self.pts):  # facings given for the points as they came
            nrm = np.asarray(nrm)[cKDTree(given).query(self.pts)[1]]
        self.nrm = _facing(self.pts, closed) if nrm is None else nrm

    def __repr__(self):
        return self.name

    def __len__(self):
        return len(self.pts)

    @property
    def length(self):
        return float(self.s[-1]) if len(self.s) else 0.0

    @property
    def start(self):
        return tuple(self.pts[0])

    @property
    def end(self):
        return tuple(self.pts[-1])

    @property
    def middle(self):
        return self.at(s=self.length / 2)

    def at(self, z=None, s=None):
        """A point on the course: at a length along the car (its first point nearest it), or `s` cm
        along it from its start."""
        if s is not None:
            return tuple(np.stack([np.interp(s, self.s, self.pts[:, k]) for k in range(3)]))
        return tuple(self.pts[int(np.argmin(np.abs(self.pts[:, 2] - z)))])

    def places(self, every, margin=None):
        """Points every `every` cm along the course, the run of them centred on it: half a gap before
        the first and after the last, or at least `margin` cm. For marks and words."""
        room = self.length if margin is None else self.length - 2 * margin + every
        n = max(1, int(room // every))
        s0 = (self.length - (n - 1) * every) / 2
        return [self.at(s=s0 + k * every) for k in range(n)]

    def _index(self, where):
        if np.isscalar(where):
            return int(np.argmin(np.abs(self.pts[:, 2] - where)))
        return int(np.argmin(np.linalg.norm(self.pts - np.asarray(where, np.float64), axis=1)))

    def _copy(self, pts, name, closed=False, idx=None):
        nrm = None if idx is None else self.nrm[idx]
        return Course(pts, name, nrm, closed, self.mirror)

    def between(self, a, b):
        """The stretch between two lengths along the car, or two points: on an open course in its own
        direction, on a loop from the first to the second the way the loop runs."""
        i, j = self._index(a), self._index(b)
        if self.closed:
            idx = np.arange(i, j + 1) if j >= i else np.r_[np.arange(i, len(self.pts)), np.arange(0, j + 1)]
        else:
            idx = np.arange(min(i, j), max(i, j) + 1)
        if len(idx) < 2:
            raise ValueError(f"{self.name}: nothing between {a} and {b}")
        return self._copy(self.pts[idx], f"{self.name} between {_said(a)} and {_said(b)}", idx=idx)

    def then(self, other):
        """On along another course: joined straight where their ends don't meet, the other turned round
        when its end is the nearer."""
        if np.linalg.norm(self.pts[-1] - other.pts[-1]) < np.linalg.norm(self.pts[-1] - other.pts[0]):
            other = other.reversed()
        pts = np.vstack([self.pts, other.pts])
        nrm = np.vstack([self.nrm, other.nrm])
        return Course(pts, f"{self.name}, then {other.name}", _resample_like(pts, nrm), False, self.mirror)

    def rounded(self, cm):
        """Its corners rounded over `cm`, the path laid back on the body."""
        from tool import carmap
        pts = _smooth(self.pts, cm, self.closed)
        pts, _, _ = carmap.load().project(pts, self.nrm)
        return Course(pts, f"{self.name} rounded over {cm:g} cm", None, self.closed, self.mirror)

    def extended(self, start=0.0, end=0.0):
        """Carried on straight past its ends, `start` cm before its first point and `end` cm after its last,
        laid on the body: a line that runs on under a frame (an inlet's) rather than stopping short of it."""
        from tool import carmap
        n = int(round(start / STEP)), int(round(end / STEP))
        before = self.pts[0] - self.tan[0] * STEP * np.arange(n[0], 0, -1)[:, None]
        after = self.pts[-1] + self.tan[-1] * STEP * np.arange(1, n[1] + 1)[:, None]
        pts = np.vstack([before, self.pts, after])
        pts, _, _ = carmap.load().project(pts)
        return Course(pts, f"{self.name} carried on", None, self.closed, self.mirror)

    def offset(self, cm, step=0.5):
        """A line beside the course, `cm` from it across the surface all along, to its left as it runs seen from
        outside (+) or its right (-): each point walked square to it a step at a time, laid back on the body at each,
        then one smooth curve through them all (a knot every OFFSET_KNOT cm along the course), laid on the body: where the
        course bends, the points walked on its inside crowd and cross, and the curve runs through them. A band of even
        width along one of the model's lines (the user, 2026-10-06: the mesh as the guides, "you don't need to follow
        exactly the lines"), or a tape beside a crease rather than folded over it. Not round a loop."""
        from tool import carmap, meshlines
        m = carmap.load()
        P, T, N = self.pts.copy(), self.tan.copy(), self.nrm.copy()
        n = max(1, int(np.ceil(abs(cm) / step)))
        for _ in range(n):
            L = np.cross(N, T)
            L /= np.maximum(np.linalg.norm(L, axis=1, keepdims=True), 1e-9)
            P, N, _ = m.project(P + (cm / n) * L, N)
        knots = list(np.arange(OFFSET_KNOT, self.length - OFFSET_KNOT / 2, OFFSET_KNOT))
        pts = np.stack([_lsq(self.s, P[:, k], knots)(self.s) for k in range(3)], 1)
        pts = np.array([meshlines._closest(p)[1] for p in pts])  # on the surface itself (a triangle's plane strays off it)
        return Course(pts, f"{self.name}, {abs(cm):g} cm to its {'left' if cm > 0 else 'right'}", None, False, self.mirror)

    def mirrored(self):
        """The same on both sides of the car."""
        return Course(self.pts, self.name, self.nrm, self.closed, True)

    def reversed(self):
        return Course(self.pts[::-1], self.name, self.nrm[::-1], self.closed, self.mirror)

    def panels(self, gap=3.0):
        """The course cut at each seam between the body's panels it crosses (a change of part under it;
        a run under SPECK cm is the next's): Courses, a piece per panel, each marked on its own (whole
        blocks, whole dashes) and stopping `gap` / 2 cm short of every edge it ends at: a seam, a corner of
        the body it would wrap round (the course turning more than CORNER degrees within 2 cm), or the
        course's own end (an opening, the inner car's frame round it, the lights), so `gap` cm of the body
        is bare across a seam; never at the car's middle, where it meets its mirror image. Where the course
        steps through the air from one panel to the next, that part of it isn't counted."""
        from tool import carmap
        m = carmap.load()
        f, _, off = m.at(self.pts, self.nrm)
        part = np.where(off > 0.3, -1, m.part[f])  # -1: off the body, across a step between two pieces
        k = int(round(1.0 / STEP))  # the turn over 2 cm, either side of each point
        t0, t1 = np.roll(self.tan, k, 0), np.roll(self.tan, -k, 0)
        turn = np.degrees(np.arccos(np.clip((t0 * t1).sum(1), -1, 1)))
        turn[:k], turn[-k:] = 0, 0
        part = np.where(turn > CORNER, -1, part)  # a corner of the body: an edge
        starts = np.flatnonzero(np.r_[True, part[1:] != part[:-1]])
        runs = [[a, b, part[a]] for a, b in zip(starts, np.r_[starts[1:], len(part)])]
        for r in runs:  # a speck of another part is the mesh's noise: the run it sits in
            k = runs.index(r)
            if r[2] >= 0 and self.s[r[1] - 1] - self.s[r[0]] < SPECK and 0 < k < len(runs) - 1 and runs[k - 1][2] == runs[k + 1][2]:
                r[2] = runs[k - 1][2]
        panels = []
        for a, b, p in runs:
            if panels and panels[-1][2] == p:
                panels[-1][1] = b
            else:
                panels.append([a, b, p])
        panels = [r for r in panels if r[2] >= 0]
        out = []
        middle = np.abs(self.pts[[0, -1], 0]) < MIDDLE
        for k, (a, b, p) in enumerate(panels):
            s0 = self.s[a] + (0.0 if k == 0 and middle[0] else gap / 2)
            s1 = self.s[b - 1] - (0.0 if k == len(panels) - 1 and middle[1] else gap / 2)
            idx = np.flatnonzero((self.s >= s0) & (self.s <= s1))
            if len(idx) > 1 and s1 - s0 >= max(gap, SPECK):
                piece = Course(self.pts[idx], f"{self.name}, on the {m.part_names[p]}", self.nrm[idx], False, self.mirror)
                piece.part = str(m.part_names[p])
                out.append(piece)
        return Courses(out, f"{self.name}, panel by panel")

    # ---- markings ----

    def _both(self):
        """The course's points, tangents, facings and lengths along it, with their mirror image when
        it's on both sides."""
        P, T, N, S = self.pts, self.tan, self.nrm, self.s
        if self.mirror:
            P, T, N, S = (np.vstack([P, P * MIRROR]), np.vstack([T, T * MIRROR]), np.vstack([N, N * MIRROR]), np.r_[S, S])
        return P, T, N, S

    def _zone(self, half, along, label, soft, reach=None):
        """A zone: within `half` cm across of the course (measured square to it) where `along`
        (s, b -> cm inside the marking, negative outside: s how far along the course, b how far across
        it, + to its left seen from outside) says so."""
        P, T, N, S = self._both()
        L = np.cross(N, T)  # the course's left, seen from outside; the mirror image's is its right
        tree = cKDTree(P)
        bound = (half if reach is None else reach) + soft + 1.0
        lo, hi = P.min(0) - bound, P.max(0) + bound

        def f(p, n):
            w = np.zeros(len(p), np.float32)
            box = np.flatnonzero(np.all((p >= lo) & (p <= hi), axis=1))
            if not len(box):
                return w
            q = p[box].astype(np.float64)
            d, i = tree.query(q, distance_upper_bound=bound, workers=-1)
            live = np.isfinite(d)
            if not live.any():
                return w
            i, q, qn, d = i[live], q[live], n[box][live], d[live]
            rel = q - P[i]
            a = (rel * T[i]).sum(1)
            across = np.sqrt(np.maximum(d * d - a * a, 0.0))
            b = np.copysign(across, (rel * L[i]).sum(1))
            inside = np.minimum(half - across, along(S[i] + a, b))
            ok = (qn * N[i]).sum(1) >= FACING
            w[box[live]] = smoothstep(-soft / 2, soft / 2, inside) * ok
            return w
        z = shapes.Zone(f, label=label)
        z.course = self
        return z

    def strip(self, width, soft=shapes.SOFT):
        """A strip `width` cm wide along the course, its ends square to it."""
        return self._zone(width / 2, self._ends(), f"a strip {width:g} cm wide along {self.name}", soft)

    def _inking(self, reach, size=4096):
        """Where the course runs on the flat texture (the body's, Skin): for each piece of it the course
        crosses (a run of its points whose nearest texel is on that piece), the texels of the piece within
        `reach` cm of the course (facing its way, not the far side of a thin panel) and one smooth curve
        (a knot every INK_KNOT cm) through where the course falls on it, in rows and columns: dicts of P and N
        (the texels' places on the car and facings), tex (their rows and columns), line, tan, k (each texel's nearest
        point of the line), dt (texels from it), pitch (cm per texel on the piece), first and last (whether
        the run holds the course's own start or end), start_n and end_n (the course's facing SMOOTH cm inside the run's
        ends, clear of a fold there). Both sides when the course is mirrored."""
        from tool import bake, carmap, uvmap
        b = bake.bake("Skin", size, size)
        tri, pos, nrm = b["tri"], b["position"], b["normal"]
        label, density, _ = uvmap.islands("Skin")
        for pts, N in [(self.pts, self.nrm)] + ([(self.pts * MIRROR, self.nrm * MIRROR)] if self.mirror else []):
            lo, hi = pts.min(0) - reach, pts.max(0) + reach
            rr, cc = np.nonzero((tri >= 0) & np.all((pos >= lo) & (pos <= hi), axis=-1))
            P = pos[rr, cc].astype(np.float64)
            d, i = cKDTree(pts).query(P, distance_upper_bound=reach, workers=-1)
            ok = np.isfinite(d)
            ok[ok] &= (nrm[rr[ok], cc[ok]] * N[i[ok]]).sum(1) >= FACING
            rr, cc, P = rr[ok], cc[ok], P[ok]
            isl = label[tri[rr, cc]]
            j = cKDTree(P).query(pts, workers=-1)[1]
            on, prow, pcol = isl[j], rr[j].astype(np.float64), cc[j].astype(np.float64)
            s = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
            for piece in np.unique(on):
                idx = np.flatnonzero(on == piece)
                for run in np.split(idx, np.flatnonzero(np.diff(idx) > INK_GAP) + 1):
                    if len(run) < 8:
                        continue
                    t = s[run]
                    knots = list(np.arange(t[0] + INK_KNOT, t[-1] - INK_KNOT / 2, INK_KNOT))
                    fr, fc = (_lsq(t, v[run], knots) for v in (prow, pcol))
                    line = np.stack([fr(np.arange(t[0], t[-1] + 1e-9, 0.05)), fc(np.arange(t[0], t[-1] + 1e-9, 0.05))], 1)
                    tan = np.gradient(line, axis=0)
                    tan /= np.maximum(np.linalg.norm(tan, axis=1, keepdims=True), 1e-9)
                    mine = np.flatnonzero(isl == piece)
                    tex = np.stack([rr[mine], cc[mine]], 1).astype(np.float64)
                    dt, k = cKDTree(line).query(tex, workers=-1)
                    inset = min(int(SMOOTH / STEP), len(run) - 1)
                    yield dict(P=P[mine], N=nrm[rr[mine], cc[mine]].astype(np.float64), tex=tex, line=line, tan=tan, k=k, dt=dt,
                               pitch=1.0 / max(float(density[piece]) * size, 1e-9),
                               first=run[0] == 0, last=run[-1] == len(pts) - 1,
                               start_n=N[run[inset]], end_n=N[run[-1 - inset]])

    @staticmethod
    def _matched(Pk, Wk, base=None, label=""):
        """A zone that takes the values Wk at the texels at Pk (the bake's own places, matched exactly), and
        `base`'s (or nothing) everywhere else."""
        tree = cKDTree(Pk) if len(Pk) else None
        lo, hi = (Pk.min(0) - 0.01, Pk.max(0) + 0.01) if len(Pk) else (np.zeros(3), np.zeros(3))

        def f(p, n):
            w = base(p, n) if base is not None else np.zeros(len(p), np.float32)
            if tree is None:
                return w
            box = np.flatnonzero(np.all((p >= lo) & (p <= hi), axis=1))
            if len(box):
                d, i = tree.query(p[box].astype(np.float64), distance_upper_bound=1e-3, workers=-1)
                hit = np.isfinite(d)
                w[box[hit]] = Wk[i[hit]]
            return w
        return shapes.Zone(f, label=label)

    def inked(self, width, soft=shapes.SOFT, size=4096, to_fold=None):
        """A strip `width` cm wide along the course, drawn as a skin artist draws one: on the flat texture
        (the Lab's UV map), one smooth curve on each piece of it the course crosses, so it runs smooth there
        and on the car. (strip(), measured on the car, picks up a texel or two of bend wherever the flat
        layout stretches one of the model's small flat faces differently from the next: the user, 2026-10-06,
        "I look at the uv map and the lines are wobbly".) Its width is the piece's own texels per cm, even on
        the texture; its ends square to it. The body's texture (Skin) only. A curve, not a straight line, on each
        piece: the shoulder's edge bends on the texture, and a line drawn straight there strays 0.4 to 0.8 cm off it
        on the sidepod's and the rear flank's pieces, with a 12 degree corner where they meet (measured 2026-10-06;
        the user: "The curve follow the edges better definitely").
        `to_fold` ("end", "start" or "both"): that end runs on straight, up to FOLD_RUN cm, to the fold where the
        surface turns FOLD degrees from the course's own facing, and stops along the fold rather than square (the
        user, 2026-10-06, of the edge line's end at the tail corner, half a centimetre short of the back face: "This
        area needs to properly cover the surface.  Something we can do is to mark the fold of the surface")."""
        half = width / 2
        keep_p, keep_w = [], []
        for r in self._inking(half + soft + 3.0, size):
            line, tan, keep = self._run_on(r, to_fold)
            dt, k = (r["dt"], r["k"]) if keep is None else cKDTree(line).query(r["tex"], workers=-1)
            past = ((r["tex"] - line[k]) * tan[k]).sum(1) * r["pitch"]
            inside = half - dt * r["pitch"]
            # square ends only at the course's own ends; where a run ends at a seam the next piece goes on
            if r["first"]:
                inside = np.minimum(inside, np.where(k == 0, past, np.inf))
            if r["last"]:
                inside = np.minimum(inside, np.where(k == len(line) - 1, -past, np.inf))
            w = smoothstep(-soft / 2, soft / 2, inside)
            if keep is not None:  # past an end that runs on: only up to the fold
                on = ~np.isnan(keep[k, 0])
                c = np.cos(np.radians(FOLD))
                w[on] *= smoothstep(c - 0.05, c + 0.05, (r["N"][on] * keep[k[on]]).sum(1))
            keep_p.append(r["P"][w > 0])
            keep_w.append(w[w > 0].astype(np.float32))
        z = self._matched(np.concatenate(keep_p) if keep_p else np.zeros((0, 3)),
                          np.concatenate(keep_w) if keep_w else np.zeros(0, np.float32),
                          label=f"a strip {width:g} cm wide inked along {self.name}")
        z.course = self
        return z

    @staticmethod
    def _run_on(r, to_fold, fold=True):
        """A run of _inking's line carried on straight on the texture past the course's own ends that `to_fold`
        names, to half a centimetre past the fold (without `fold`, on over it: to the piece's edge, or FOLD_RUN
        cm): the line, its tangents and, per point, the facing the surface must keep there (NaN along the course
        itself); None for keep when no end runs on."""
        line, tan = r["line"], r["tan"]
        ends = [e for e, on in (("start", r["first"]), ("end", r["last"])) if on and to_fold in (e, "both")]
        if not ends:
            return line, tan, None
        keep = np.full((len(line), 3), np.nan)
        tree, step = cKDTree(r["tex"]), 0.05 / r["pitch"]  # texels between the line's points, 0.05 cm apart
        for end in ends:
            a, ref = (0, r["start_n"]) if end == "start" else (-1, r["end_n"])
            more = line[a] + (-tan[a] if end == "start" else tan[a]) * step * np.arange(1, int(FOLD_RUN / 0.05) + 1)[:, None]
            gap, j = tree.query(more, workers=-1)
            turned = (gap > 1.5) | (((r["N"][j] @ ref) < np.cos(np.radians(FOLD))) if fold else False)
            n = min(len(more), (int(np.argmax(turned)) if turned.any() else len(more)) + 10)
            more, refs, tans = more[:n], np.repeat(ref[None], n, 0), np.repeat(tan[a][None], n, 0)
            if end == "start":
                line, tan, keep = np.vstack([more[::-1], line]), np.vstack([tans, tan]), np.vstack([refs, keep])
            else:
                line, tan, keep = np.vstack([line, more]), np.vstack([tan, tans]), np.vstack([keep, refs])
        return line, tan, keep

    def inked_edge(self, zone, reach=INK_REACH, soft=shapes.SOFT, size=4096, to_fold=None):
        """`zone` with its edge moved onto the course where it runs within `reach` cm of it, drawn on the
        flat texture as inked() is, so a colour stops on the course in one smooth curve: shapes.below(26) cut
        along a line beside the body's bottom edge (meshlines.line(...).offset(14)). On each piece of the texture
        the side of the course the zone covers more of within `reach` takes it, the other side not (within a
        centimetre and a half the zone can cover neither);
        past the course's own ends and further than `reach` from it, the zone as it is. `to_fold` as inked()'s:
        past that end the course's side still decides, up to the fold. A texel on a piece the course doesn't cross,
        within INK_BLEED cm of one it does, takes that one's side (the user, 2026-10-06, of a silver sliver where
        the body turns in to the inlet's frame: "There's a clear gap that is not painted here")."""
        keep_p, keep_w = [], []
        for r in self._inking(reach + soft, size):
            line, tan, keep = self._run_on(r, to_fold, fold=False)
            dt, k = (r["dt"], r["k"]) if keep is None else cKDTree(line).query(r["tex"], workers=-1)
            d, t = r["tex"] - line[k], tan[k]
            signed = np.sign(d[:, 0] * t[:, 1] - d[:, 1] * t[:, 0]) * dt * r["pitch"]
            near = dt * r["pitch"] <= reach
            past = (d * t).sum(1) * r["pitch"]
            if r["first"]:
                near &= ~((k == 0) & (past < 0))
            if r["last"]:
                near &= ~((k == len(line) - 1) & (past > 0))
            if not near.any():
                continue
            P, N, signed = r["P"][near], r["N"][near], signed[near]
            zv = zone(P, N)
            share = [float(zv[signed * sign > 0].mean()) if (signed * sign > 0).any() else 0.0 for sign in (1.0, -1.0)]
            if max(share) == 0.0:  # the zone isn't here: nothing to move
                continue
            side = 1.0 if share[0] >= share[1] else -1.0
            keep_p.append(P)
            keep_w.append(smoothstep(-soft / 2, soft / 2, side * signed).astype(np.float32))
        if keep_p:
            keep_p, keep_w = self._bled(np.concatenate(keep_p), np.concatenate(keep_w), reach, size)
        z = self._matched(np.concatenate(keep_p) if keep_p else np.zeros((0, 3)),
                          np.concatenate(keep_w) if keep_w else np.zeros(0, np.float32),
                          base=zone, label=f"{zone!r} with its edge inked along {self.name}")
        z.course = self
        return z

    def _bled(self, Pk, Wk, reach, size):
        """The inked texels (places Pk, values Wk) with the body's texels within `reach` of the course that they
        leave out (pieces of the texture the course doesn't cross) and within INK_BLEED cm of one of them, each
        taking its nearest one's value: lists of places and values."""
        from tool import bake
        b = bake.bake("Skin", size, size)
        tri, pos = b["tri"], b["position"]
        P = self._both()[0]
        lo, hi = P.min(0) - reach, P.max(0) + reach
        rr, cc = np.nonzero((tri >= 0) & np.all((pos >= lo) & (pos <= hi), axis=-1))
        Q = pos[rr, cc].astype(np.float64)
        Q = Q[np.isfinite(cKDTree(P).query(Q, distance_upper_bound=reach, workers=-1)[0])]
        Q = Q[~np.isfinite(cKDTree(Pk).query(Q, distance_upper_bound=1e-3, workers=-1)[0])]  # not inked already
        d, i = cKDTree(Pk).query(Q, distance_upper_bound=INK_BLEED, workers=-1)
        hit = np.isfinite(d)
        return [Pk, Q[hit]], [Wk, Wk[i[hit]]]

    def _ends(self):
        """The marking's ends, square to the course: cm inside them (a loop has none)."""
        L = self.length
        return (lambda s, b: np.full(len(s), 1e3)) if self.closed else (lambda s, b: np.minimum(s, L - s))

    def dashes(self, length, gap=None, width=1.0, slant=0.0, soft=shapes.SOFT):
        """Dashes `length` cm long with `gap` cm between (as long as a dash), `width` cm wide, the run of
        them centred on the course so a whole dash sits at each end (on a loop, spaced evenly round).
        slant: degrees the dashes' ends lean (towards the course's start on its left), so dashes as long
        as their gaps across a wide strip are hazard tape; the strip's own ends stay square."""
        gap = length if gap is None else gap
        L, period = self.length, length + gap
        if self.closed:
            n = max(1, int(round(L / period)))
            period, s0 = L / n, 0.0
            length = min(length, period)
        else:
            n = max(1, int((L + gap) // period))
            s0 = (L - (n * period - gap)) / 2
        lean, square = np.tan(np.radians(slant)), np.cos(np.radians(slant))
        ends = self._ends()

        def along(s, b):
            u = s + lean * b
            k = np.floor((u - s0) / period) if slant or self.closed else np.clip(np.floor((u - s0) / period), 0, n - 1)
            local = u - s0 - k * period
            return np.minimum(np.minimum(local, length - local) * square, ends(s, b))
        how = f", slanted {slant:g} degrees" if slant else ""
        return self._zone(width / 2, along, f"dashes {length:g} cm long, {gap:g} apart, {width:g} cm wide{how} along {self.name}",
                          soft)

    def blocks(self, length, high, rows=2, soft=shapes.SOFT):
        """Rows of blocks along the course, `length` cm long and `high` cm high, alternating from row to
        row like a chessboard (the first block at the course's start in its left row), as many rows as
        `rows` across a strip centred on it; a whole block at each end."""
        L = self.length
        n = max(1, int(round(L / length)))
        length = L / n  # whole blocks from end to end
        half = rows * high / 2
        ends = self._ends()

        def along(s, b):
            # the block a point is in or beside: past the strip's edges and ends, the one at its edge (the strip's
            # own edge and ends are drawn by the strip itself)
            u = half - b  # across from the strip's left edge
            j = np.clip(np.floor(s / length), 0, n - 1)
            r = np.clip(np.floor(u / high), 0, rows - 1)  # the row: 0 the left
            on = (j + r) % 2 == 0
            # distances to the block's sides shared with another block: only there does a block meet a gap, so a
            # gap at the strip's edge isn't painted half, a hairline round the tape
            far = np.float64(1e6)
            ds = np.minimum(np.where(j > 0, s - j * length, far), np.where(j < n - 1, (j + 1) * length - s, far))
            db = np.minimum(np.where(r > 0, u - r * high, far), np.where(r < rows - 1, (r + 1) * high - u, far))
            return np.minimum(np.where(on, 1.0, -1.0) * np.minimum(ds, db), ends(s, b))
        return self._zone(half, along, f"{rows} rows of blocks {length:.3g} by {high:g} cm along {self.name}", soft)

    def ticks(self, every, length, width=0.6, side=0, soft=shapes.SOFT):
        """Short strokes square to the course, `length` cm long and `width` wide, every `every` cm, to
        its left as it runs (side=1, seen from outside the car), its right (-1) or both ways (0)."""
        P, T, N, S = self._both()
        L = self.length
        n = max(1, int(L // every))
        s0 = (L - (n - 1) * every) / 2
        at = s0 + np.arange(n) * every
        if self.mirror:
            at = np.r_[at, at + 0.0]
        C = np.stack([np.interp(at, self.s, self.pts[:, k]) for k in range(3)], 1)
        TC = np.stack([np.interp(at, self.s, self.tan[:, k]) for k in range(3)], 1)
        NC = np.stack([np.interp(at, self.s, self.nrm[:, k]) for k in range(3)], 1)
        if self.mirror:
            h = len(C) // 2
            C[h:], TC[h:], NC[h:] = C[:h] * MIRROR, TC[:h] * MIRROR, NC[:h] * MIRROR
        D = np.cross(NC, TC)  # to the course's left, seen from outside
        D /= np.maximum(np.linalg.norm(D, axis=1, keepdims=True), 1e-9)
        if self.mirror:
            D[len(C) // 2:] *= -1  # the mirror image of a left-hand tick is a right-hand one
        tree = cKDTree(C)
        bound = length + width + soft + 1.0
        lo, hi = C.min(0) - bound, C.max(0) + bound

        def f(p, n):
            w = np.zeros(len(p), np.float32)
            box = np.flatnonzero(np.all((p >= lo) & (p <= hi), axis=1))
            if not len(box):
                return w
            q = p[box].astype(np.float64)
            d, j = tree.query(q, distance_upper_bound=bound, workers=-1)
            live = np.isfinite(d)
            if not live.any():
                return w
            j, q, qn = j[live], q[live], n[box][live]
            rel = q - C[j]
            a, b = (rel * D[j]).sum(1) * (side or 1), (rel * TC[j]).sum(1)  # a: out from the course, the tick's way
            reach = length / 2 - np.abs(a) if side == 0 else np.minimum(a, length - a)
            inside = np.minimum(width / 2 - np.abs(b), reach)
            ok = (qn * NC[j]).sum(1) >= FACING
            w[box[live]] = smoothstep(-soft / 2, soft / 2, inside) * ok
            return w
        z = shapes.Zone(f, label=f"ticks {length:g} cm long every {every:g} cm along {self.name}")
        z.course = self
        return z

    def up_at(self, point):
        """Where the top of words reading along the course points, at a point on it: upright to someone
        standing beside the car at the side the surface faces (tool/marks.py's _outward)."""
        from tool import marks
        i = self._index(point)
        t, n = self.tan[i], self.nrm[i]
        up = np.cross(n, t)
        up /= max(np.linalg.norm(up), 1e-9)
        want = np.asarray(marks._outward(n, self.pts[i]), np.float64)
        return tuple(-up if up @ want < 0 else up)


def _said(v):
    return f"z {v:+g}" if np.isscalar(v) else "(" + ", ".join(f"{float(c):.0f}" for c in v) + ")"


def _resample_like(pts, nrm):
    """Normals for `pts` resampled every STEP: the nearest given point's."""
    new = _resample(pts, STEP)
    _, i = cKDTree(pts).query(new)
    return nrm[i]


# ---- the car's lines as courses ----

class Courses:
    """Several courses marked alike: each marking is every course's, in one zone."""

    def __init__(self, courses, name):
        self.courses, self.name = list(courses), name

    def __repr__(self):
        return self.name

    def __iter__(self):
        return iter(self.courses)

    def mirrored(self):
        return Courses([c.mirrored() for c in self.courses], self.name)

    def panels(self, gap=3.0):
        return Courses([p for c in self.courses for p in c.panels(gap)], f"{self.name}, panel by panel")

    def without(self, *parts):
        """The pieces on any panel but these (by part name: Course.panels gives each piece its panel)."""
        keep = [c for c in self.courses if getattr(c, "part", None) not in parts]
        if len(keep) == len(self.courses):
            raise ValueError(f"{self.name}: no piece on {', '.join(parts)} (Course.panels names each piece's panel)")
        return Courses(keep, f"{self.name}, not on the {', '.join(parts)}")

    def _all(self, method, *a, **k):
        zones = [getattr(c, method)(*a, **k) for c in self.courses]
        fns = [z.fn for z in zones]
        label = zones[0].label.replace(self.courses[0].name, self.name) if zones else self.name
        z = shapes.Zone(lambda p, n: np.max([fn(p, n) for fn in fns], axis=0), label=label)
        z.course = self
        return z

    def strip(self, *a, **k):
        return self._all("strip", *a, **k)

    def dashes(self, *a, **k):
        return self._all("dashes", *a, **k)

    def blocks(self, *a, **k):
        return self._all("blocks", *a, **k)

    def ticks(self, *a, **k):
        return self._all("ticks", *a, **k)


def _flip(c):
    return Course(c.pts * MIRROR, c.name.replace("left", "right"), c.nrm * MIRROR, c.closed, c.mirror)


def seam(name, side="left"):
    """A seam (tool/seams.py) as a course, tail to nose on one side."""
    from tool import seams
    path = np.asarray(seams.traced()[name]["path"], np.float64)
    c = Course(path, f"the seam {name!r} on the {side}")
    return c if side == "left" else _flip(c)


def stroke(points):
    """The line the user drew with the Lab's pen: its points smoothed over SMOOTH cm, laid on the body
    (a point further than OFF cm from it is dropped)."""
    from tool import carmap
    pts = _resample(np.asarray(points, np.float64))
    pts = _smooth(pts, SMOOTH)
    on, _, far = carmap.load().project(pts)
    on = on[far <= OFF]
    if len(on) < 2:
        raise ValueError("the drawn line isn't on the body")
    return Course(on, "the line drawn")


def points(pts, name="the points given"):
    """Any points on the car, joined straight."""
    return Course(np.asarray(pts, np.float64), name)


def edge(part, side=None, near=None):
    """A panel's edge: its outline on the body's mesh, chained into loops, the panel on the course's
    left as it runs (seen from outside); the loop nearest `near` (a point), else the longest. side:
    "left" or "right" for a panel the car has on both sides."""
    from tool import fbx, parts as parts_mod
    P = parts_mod.load()
    ids = P.select(part, side=side)
    if not ids:
        raise ValueError(f"no part called {part!r} on the {side}")
    m = fbx.meshes()["Skin_01"]
    tv, pos = m["tri_vertex"], m["positions"].astype(np.float64)
    T = len(tv)
    off = P.mesh_offset["Skin"]
    mine = np.isin(P.tri_part[off:off + T], ids)
    _, inv = np.unique(np.round(pos, 2), axis=0, return_inverse=True)
    wt = inv.reshape(-1)[tv[mine]]
    tri = tv[mine]
    # the triangles' winding seen from outside: the FBX normal says which way each faces
    a, b, c = pos[tri[:, 0]], pos[tri[:, 1]], pos[tri[:, 2]]
    flip = (np.cross(b - a, c - a) * m["tri_normal"][mine].mean(1)).sum(1) < 0
    wt[flip] = wt[flip][:, [0, 2, 1]]
    e = np.concatenate([wt[:, [0, 1]], wt[:, [1, 2]], wt[:, [2, 0]]])
    key = e[:, 0].astype(np.int64) * (int(inv.max()) + 1) + e[:, 1]
    rev = e[:, 1].astype(np.int64) * (int(inv.max()) + 1) + e[:, 0]
    boundary = e[~np.isin(key, rev)]  # a directed edge whose reverse no triangle of the panel has
    nxt = {}
    for u, v in boundary:
        nxt.setdefault(int(u), []).append(int(v))
    V = np.zeros((int(inv.max()) + 1, 3))
    V[inv.reshape(-1)] = pos
    loops, used = [], set()
    for u0 in list(nxt):
        if u0 in used:
            continue
        loop, u = [u0], u0
        used.add(u0)
        while True:
            vs = [v for v in nxt.get(u, []) if v not in used]
            if not vs:
                break
            u = vs[0]
            used.add(u)
            loop.append(u)
        closed = any(v == u0 for v in nxt.get(u, []))
        if len(loop) >= 3:
            loops.append((V[loop], closed))
    if not loops:
        raise ValueError(f"{part}: no edge found")
    if near is not None:
        near = np.asarray(near, np.float64)
        pts, closed = min(loops, key=lambda lc: float(np.linalg.norm(lc[0] - near, axis=1).min()))
    else:
        pts, closed = max(loops, key=lambda lc: float(np.linalg.norm(np.diff(lc[0], axis=0), axis=1).sum()))
    tag = f" on the {side}" if side else ""
    return Course(pts, f"the edge of the {part}{tag}", None, closed)
