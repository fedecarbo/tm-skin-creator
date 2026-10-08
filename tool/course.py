"""A course: a path along one of the car's own lines, and markings laid along it. The user, 2026-10-05,
drawing with the Lab's pen: "Do an interval lines with DO NOT STEP text." A marking belongs to a line
of the car (one of the model's own lines: a crease, a rolled edge's, an edge where the body ends, a seam between
two of its parts; or a panel's edge) or to the line the user drew, and the tool lays it along that line in one go:
a strip, dashes, ticks, spots or words.

    course.edge("sidepod top", near=(55, 61, -40))   a panel's edge: its outline (the loop nearest `near`,
                                             else the longest), the panel on its left as it runs, seen from
                                             outside; side="left" picks the panel's instance
    meshlines.line(point), meshlines.picked(points)   the model's own lines, exact (tool/meshlines.py), as courses
    course.stroke(points)                   the line the user drew (tool.notes show_drawn prints its points): its
                                             points on the body, joined by the straightest way along the surface
    course.points([(x, y, z), ...])          any points on the car, joined the same way
    course.Courses([a, b], "the contour")    several courses marked alike: a marking is every one's, in one zone
  Shaped (every line on the surface itself, tool/surface.py: nothing smoothed in the air and pushed back):
    c.between(-128, -50)                     the stretch between two lengths along the car, or two points
                                             (on a loop: from the first to the second the way it runs)
    c.then(other)                            on along another course, joined by the straightest way along the
                                             surface where their ends don't meet
    c.extended(start=3)                      carried on 3 cm before its start by the straightest way along the
                                             surface (under a frame, on over a seam)
    c.offset(14)                             a line beside it, 14 cm across the surface to its left all along (- its
                                             right): the line where the distance from it is 14 (never crossing
                                             itself on a bend, square to its ends); crease=True stops at a crease
    c.mirrored()                             the same on both sides; c.reversed() the other way
    c.panels(3)                              cut at each seam between the body's panels it crosses, a piece per
                                             panel stopping 1.5 cm short of each edge it ends at (a seam, an
                                             opening's frame): a marking applied panel by panel, as tape is;
                                             .without("nose tip") leaves those panels' pieces off
    c.length, c.start, c.middle, c.end, c.at(z=-70), c.at(s=20)   points on it (cm)
    c.places(every=20)                       points every 20 cm along it, a whole gap at each end, for marks
  Markings, as zones (tool/shapes.py) for s.paint(..., zone=), measured across the surface:
    c.band(4)                                a band 4 cm wide along it, centred: wrapping whatever edge it runs along
    c.band(4, side=1)                        on one face beside it, its edge on the course, 4 cm across the surface to
                                             its left as it runs seen from outside (-1 its right; "seen": the face
                                             the eye sees more of from round the car and above)
    c.band(4, side=1, crease=True)           stopping where the body creases (one of the model's crisp lines) before
                                             its width is out; c.strip(1.0) a band 1 cm wide, centred, for lines
    c.inked_edge(shapes.below(26))           a zone whose edge is moved onto the course: the side it covers more
                                             of takes it, the other not, within REACH cm of the course
    c.dashes(5, gap=3, width=1)              dashes 5 cm long with 3 cm gaps, a whole dash at each end
    c.dashes(2.5, width=5, slant=45)         stripes across a 5 cm strip, slanted 45 degrees: hazard tape
    c.blocks(5, 2.5)                         two rows of blocks 5 cm long and 2.5 high, alternating: block tape
    c.ticks(every=10, length=3, width=0.6, side=1)   short strokes square to it every 10 cm, to its left (+1),
                                             its right (-1) or both ways (0)
    s.text("NO STEP", "engine cover", at=c.between(-74, -62))   words (a placard, a mark) at a stretch's
                                             middle, reading along it, each letter following the line (c.chart:
                                             the surface laid flat along the course, X along it, Y across), upright
                                             to someone beside the car; the stretch is their room along the line
A marking's width and side are measured along the car's surface (tool/surface.py: the distance from the course exact
on each side of it), so it lies where the surface itself joins to the course, however far the body turns, and never
on the far side of a thin panel; along the course, by the course's nearest point. course.measure(zone) reads a
marking back off the body every half centimetre: its side, its reach and its gaps. The checks (tool/checks.py)
read each dash and tick as they read any small mark.
Close up where the model's flat faces are big (the nose root, the sidepods' fronts, the tail), a line
bends where it crosses a fold between two of them, as the body does: those corners are the model's,
and no way of drawing the line takes them out (measured 2026-10-06: 6 to 12 degrees with the folds at
the nose root, 1 to 5 along the surface).
"""

import functools

import numpy as np
from scipy.spatial import cKDTree

from tool import shapes
from tool.noise import smoothstep

STEP = 0.25    # cm between a course's points
SPECK = 1.0    # cm: a run of another part this short under a course is the mesh's noise, not a panel
MIDDLE = 1.0   # cm from the car's middle: a course's end there meets its mirror image
CORNER = 45.0  # degrees within 2 cm: a corner of the body a marking stops short of (the tail corner's end)
OFF = 3.0      # cm: a stroke's point further than this from the body is dropped
MIRROR = np.array([-1.0, 1.0, 1.0])
REACH = 10.0   # cm either side of a course an inked edge moves the zone's edge across: all the way to the zone's own
# edge (at 4 a sliver stayed unpainted by the inlet's frame, the user, 2026-10-06: "There's a clear gap that is not
# painted here")


@functools.lru_cache(maxsize=1)
def _seen_by_facing():
    """How far a face faces the eye from round the car and above, by how far it faces up: (its facing up, -1 to 1;
    the mean over the directions above the ground of how squarely it faces each)."""
    from tool import carmap
    up = carmap.directions()
    up = up[up[:, 1] > 0]
    c = np.linspace(-1, 1, 81)
    n = np.stack([np.sqrt(1 - c * c), c, np.zeros_like(c)], 1)
    return c, np.maximum(n @ up.T, 0).mean(1)


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
        self.nrm = _surface().facing(self.pts) if nrm is None else nrm
        self._fields = {}

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
        """On along another course, the other turned round when its end is the nearer: where their ends don't meet,
        joined by the straightest way along the surface."""
        if np.linalg.norm(self.pts[-1] - other.pts[-1]) < np.linalg.norm(self.pts[-1] - other.pts[0]):
            other = other.reversed()
        join = _surface().path([self.pts[-1], other.pts[0]])[1:-1] if np.linalg.norm(self.pts[-1] - other.pts[0]) > STEP else np.zeros((0, 3))
        return Course(np.vstack([self.pts, join, other.pts]), f"{self.name}, then {other.name}", None, False, self.mirror)

    def extended(self, start=0.0, end=0.0):
        """Carried on past its ends by the straightest way along the surface, `start` cm before its first point and
        `end` cm after its last: a line that runs on under a frame (an inlet's) or on over a seam rather than stopping
        short of it; where the body ends, it stops."""
        S = _surface()
        before = S.carry(self.pts[0], -self.tan[0], start)[:0:-1] if start > 0 else np.zeros((0, 3))
        after = S.carry(self.pts[-1], self.tan[-1], end)[1:] if end > 0 else np.zeros((0, 3))
        return Course(np.vstack([before, self.pts, after]), f"{self.name} carried on", None, self.closed, self.mirror)

    def offset(self, cm, crease=False):
        """A line beside the course, `cm` from it across the surface all along, to its left as it runs seen from
        outside (+) or its right (-): the line where the distance along the surface from the course is `cm`
        (tool/surface.py, Field.contour), which never crosses itself where the course bends; square to the course's
        ends, round a loop a loop; with `crease`, going no further than the body's next crease. Where it reaches an
        opening or runs off the course's piece it comes in pieces, joined in order along the course. A band of even
        width along one of the model's lines, or a tape beside a crease rather than folded over it."""
        pieces = self._signed(abs(cm) + 1.0, crease, levels=(cm,)).contour(cm)
        tree, runs = cKDTree(self.pts), []
        for pts, closed in pieces:
            _, i = tree.query(pts)
            al = self.s[i] + ((pts - self.pts[i]) * self.tan[i]).sum(1)
            if self.closed:
                runs.append((float(np.median(al)), pts, closed))
                continue
            if al[-1] < al[0]:
                pts, al = pts[::-1], al[::-1]
            pts = _clip(pts, al, 0.0, self.length)
            if len(pts) > 1:
                runs.append((float(al[(al >= 0) & (al <= self.length)].min()), pts, False))
        if not runs:
            raise ValueError(f"{self.name}: no line {abs(cm):g} cm beside it")
        runs.sort(key=lambda r: r[0])
        many = f", in {len(runs)} pieces" if len(runs) > 1 else ""
        return Course(np.vstack([r[1] for r in runs]), f"{self.name}, {abs(cm):g} cm to its {'left' if cm > 0 else 'right'}{many}",
                      None, len(runs) == 1 and runs[0][2], self.mirror)

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

    def _signed(self, reach, crease=False, mirrored=False, levels=()):
        """The signed distance along the surface from the course (or its mirror image) within `reach` cm, kept on the
        course: a Field (tool/surface.py); `levels`, the distances drawn as lines, which it reads finely."""
        key = (round(reach, 3), crease, mirrored, tuple(levels))
        if key not in self._fields:
            P = self.pts * MIRROR if mirrored else self.pts
            self._fields[key] = _surface().signed(P, reach=reach, closed=self.closed, crease=crease, levels=levels)
        return self._fields[key]

    def _across(self, reach, crease=False, size=4096, levels=()):
        """The signed distance along the surface from the course, read at the body's texels within `reach` cm of it
        (tool/surface.py: exact on each side; + to the course's left as it runs, seen from outside): one dict per copy
        (the course; its mirror image when it's on both sides, `mirrored`): the texels' flat indices on the map (lin),
        their places (pos), the distance at each (d), and the copy's points and tangents (P, T). Kept on the course."""
        from tool import bake
        key = (round(reach, 3), crease, size, tuple(levels))
        if key not in self._fields:
            b = bake.bake("Skin", size, size)
            tri, pos = b["tri"].reshape(-1), b["position"].reshape(-1, 3)
            copies = [(self.pts, self.tan, False)] + ([(self.pts * MIRROR, self.tan * MIRROR, True)] if self.mirror else [])
            out = []
            for P, T, mirrored in copies:
                field = self._signed(reach + 1.0, crease, mirrored, levels)
                lo, hi = P.min(0) - reach - 1, P.max(0) + reach + 1
                lin = np.flatnonzero((tri >= 0) & np.all((pos >= lo) & (pos <= hi), axis=1))
                d = field.at(size, lin)
                ok = np.isfinite(d) & (np.abs(d) <= reach)
                out.append(dict(lin=lin[ok], pos=pos[lin[ok]].astype(np.float64), d=d[ok], P=P, T=T, mirrored=mirrored))
            self._fields[key] = out
        return self._fields[key]

    def _zone(self, lo, hi, along, label, soft, crease=False):
        """A zone: the texels whose distance across the surface from the course, b (+ to its left seen from outside),
        lies between `lo` and `hi` cm (for the mirror image, between -hi and -lo: the mirror image of the marking)
        where `along` (s, b -> cm inside the marking, negative outside: s how far along the course, by its nearest
        point) says so."""
        from tool import bake
        reach = max(abs(lo), abs(hi)) + soft + 1.0
        lins, ws = [], []
        for c in self._across(reach, crease, levels=tuple(v for v in (lo, hi) if v)):  # its edges, read finely
            L, H = (-hi, -lo) if c["mirrored"] else (lo, hi)
            _, i = cKDTree(c["P"]).query(c["pos"], workers=-1)
            a = ((c["pos"] - c["P"][i]) * c["T"][i]).sum(1)
            inside = np.minimum(np.minimum(c["d"] - L, H - c["d"]), along(self.s[i] + a, c["d"]))
            w = smoothstep(-soft / 2, soft / 2, inside).astype(np.float32)
            on = w > 0.002
            lins.append(c["lin"][on])
            ws.append(w[on])
        lin = np.concatenate(lins) if lins else np.zeros(0, np.int64)
        w = np.concatenate(ws) if ws else np.zeros(0, np.float32)
        order = np.lexsort((-w, lin))  # a texel both copies reach takes the higher weight
        first = np.r_[True, np.diff(lin[order]) != 0] if len(lin) else np.zeros(0, bool)
        lin, w = lin[order][first], w[order][first]
        pos = bake.bake("Skin", 4096, 4096)["position"].reshape(-1, 3)[lin].astype(np.float64)
        z = self._matched(pos, w, label=label)
        z.course = self
        return z

    def band(self, width, side=0, crease=False, soft=shapes.SOFT):
        """A band `width` cm wide along the course, measured along the surface: centred on it (side=0), wrapping whatever
        edge it runs along; or on one face beside it, its edge on the course and its other `width` cm across the surface
        from it, to its left as it runs seen from outside (side=1), its right (-1), or the face the eye sees more of from
        round the car and above ("seen": its faces up to the width, by how much open air they see and how far they face
        up). With `crease`, it stops where the body creases (one of the model's crisp lines) before its width is out.
        Its ends square to the course."""
        if side == "seen":
            side = self._seen_side(width, crease)
        lo, hi = {0: (-width / 2, width / 2), 1: (0.0, width), -1: (-width, 0.0)}[side]
        how = "" if side == 0 else f" on the {'left' if side > 0 else 'right'} of"
        z = self._zone(lo, hi, self._ends(), f"a band {width:g} cm wide{how or ' along'} {self.name}{', to the crease' if crease else ''}",
                       soft, crease)
        z.side = side
        return z

    def _seen_side(self, width, crease):
        """The side of the course the eye sees more of: its texels within the width, by how much open air each sees
        and how far it faces up (round the car and above), by their area."""
        from tool import bake, carmap, uvmap
        b = bake.bake("Skin", 4096, 4096)
        nrm = b["normal"].reshape(-1, 3)
        label, density, _ = uvmap.islands("Skin")
        tri = b["tri"].reshape(-1)
        seen = {1: 0.0, -1: 0.0}
        for c in self._across(width + 1.0, crease):
            Nq = nrm[c["lin"]].astype(np.float64)
            weight = np.interp(Nq[:, 1], *_seen_by_facing()) * carmap.load().value("open", c["pos"], Nq)
            pitch = 1.0 / np.maximum(density[label[tri[c["lin"]]]] * 4096, 1e-9)
            for s in (1, -1):
                on = (s * c["d"] * (-1 if c["mirrored"] else 1) > 0) & (np.abs(c["d"]) <= width)
                seen[s] += float((weight[on] * pitch[on] ** 2).sum())
        return 1 if seen[1] >= seen[-1] else -1

    def strip(self, width, soft=shapes.SOFT):
        """A strip `width` cm wide along the course, centred on it, its ends square to it."""
        return self.band(width, soft=soft)

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

    def inked(self, width, soft=shapes.SOFT):
        """A strip `width` cm wide along the course: strip()."""
        return self.strip(width, soft)

    def inked_edge(self, zone, reach=REACH, soft=shapes.SOFT):
        """`zone` with its edge moved onto the course where it runs within `reach` cm of it, so a colour stops on the
        course itself: shapes.below(26) cut along a line beside the body's bottom edge (meshlines.line(...).offset(14)).
        On each side of the car, the side of the course the zone covers more of within `reach` takes it, the other
        not, the edge measured along the surface; past the course's own ends and further than `reach` from it, the
        zone as it is."""
        from tool import bake
        nrm = bake.bake("Skin", 4096, 4096)["normal"].reshape(-1, 3)
        keep_p, keep_w = [], []
        for c in self._across(reach):
            _, i = cKDTree(c["P"]).query(c["pos"], workers=-1)
            s = self.s[i] + ((c["pos"] - c["P"][i]) * c["T"][i]).sum(1)
            near = self.closed | ((s >= 0) & (s <= self.length))
            if not near.any():
                continue
            P, d = c["pos"][near], c["d"][near]
            zv = zone(P, nrm[c["lin"][near]].astype(np.float64))
            share = [float(zv[d * sign > 0].mean()) if (d * sign > 0).any() else 0.0 for sign in (1.0, -1.0)]
            if max(share) == 0.0:  # the zone isn't here: nothing to move
                continue
            side = 1.0 if share[0] >= share[1] else -1.0
            keep_p.append(P)
            keep_w.append(smoothstep(-soft / 2, soft / 2, side * d).astype(np.float32))
        z = self._matched(np.concatenate(keep_p) if keep_p else np.zeros((0, 3)),
                          np.concatenate(keep_w) if keep_w else np.zeros(0, np.float32),
                          base=zone, label=f"{zone!r} with its edge on {self.name}")
        z.course = self
        return z

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
        return self._zone(-width / 2, width / 2, along, f"dashes {length:g} cm long, {gap:g} apart, {width:g} cm wide{how} along {self.name}",
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
        return self._zone(-half, half, along, f"{rows} rows of blocks {length:.3g} by {high:g} cm along {self.name}", soft)

    def ticks(self, every, length, width=0.6, side=0, soft=shapes.SOFT):
        """Short strokes square to the course, `length` cm long and `width` wide, every `every` cm, to
        its left as it runs (side=1, seen from outside), its right (-1) or both ways (0)."""
        L = self.length
        n = max(1, int(L // every))
        s0 = (L - (n - 1) * every) / 2
        lo, hi = {1: (0.0, length), -1: (-length, 0.0), 0: (-length / 2, length / 2)}[side]

        def along(s, b):
            k = np.clip(np.round((s - s0) / every), 0, n - 1)
            return width / 2 - np.abs(s - (s0 + k * every))
        return self._zone(lo, hi, along, f"ticks {length:g} cm long every {every:g} cm along {self.name}", soft)

    def _left(self, i, mirrored=False):
        t, n = (self.tan[i] * MIRROR, self.nrm[i] * MIRROR) if mirrored else (self.tan[i], self.nrm[i])
        up = np.cross(n, t)
        return up / max(np.linalg.norm(up), 1e-9)

    def _turned(self, i, mirrored=False):
        """Whether words reading along the course at its point i are upright with their top to the course's right
        (then they read the other way along it), for someone beside the car (tool/marks.py's _outward)."""
        from tool import marks
        n, p = (self.nrm[i] * MIRROR, self.pts[i] * MIRROR) if mirrored else (self.nrm[i], self.pts[i])
        return bool(self._left(i, mirrored) @ np.asarray(marks._outward(n, p), np.float64) < 0)

    def chart(self, s0, across, mirrored=False):
        """The surface laid flat along the course, for words and patterns reading along it (tool/marks.py): a Chart
        (tool/surface.py) whose X runs along the course from the point s0 cm along it and whose Y runs across it,
        the distance across the surface (exact on each side), within `across` cm of it; a texel's X is its nearest
        point's length along the course. Words are upright to someone beside the car (_turned): where their top points
        to the course's right, the sheet is turned over (X the other way along it, Y to its right). The frame at s0:
        right the way the words read, up where their top points, facing the surface's. mirrored: the course's mirror
        image's."""
        from tool import surface
        field = self._signed(across + 1.0, False, mirrored)
        P, T = (self.pts * MIRROR, self.tan * MIRROR) if mirrored else (self.pts, self.tan)
        _, i = cKDTree(P).query(field.Vn, workers=-1)
        s = self.s[i] + ((field.Vn - P[i]) * T[i]).sum(1)
        v = field.value
        d = np.where(v[:, 0] <= v[:, 1], v[:, 0], -v[:, 1])
        d[np.isinf(v).all(1)] = np.nan
        i0 = int(np.argmin(np.abs(self.s - s0)))
        sign = -1.0 if self._turned(i0, mirrored) else 1.0
        xy = np.stack([sign * (s - s0), sign * d], 1)
        xy[~np.isfinite(d) | (np.abs(d) > across) | (s < 0) | (s > self.length)] = np.nan
        n = self.nrm[i0] * MIRROR if mirrored else self.nrm[i0]
        return surface.Chart(field.S, field.keep, field.parent, field.Vn, field.Fn, xy, np.where(np.isfinite(d), np.abs(d), np.inf),
                             P[i0], sign * T[i0], sign * self._left(i0, mirrored), n)


def _said(v):
    return f"z {v:+g}" if np.isscalar(v) else "(" + ", ".join(f"{float(c):.0f}" for c in v) + ")"


def _surface():
    from tool import surface
    return surface.load()


def _clip(pts, al, lo, hi):
    """The run of a polyline where `al` (a value per point) lies between lo and hi, its ends put where it crosses
    them (al taken as running straight from point to point)."""
    inside = np.flatnonzero((al >= lo) & (al <= hi))
    if not len(inside):
        return pts[:0]
    a, b = int(inside[0]), int(inside[-1])
    out = [pts[a:b + 1]]
    if a > 0:  # the point before is outside: where the way in crosses the bound
        bound = lo if al[a - 1] < lo else hi
        out.insert(0, (pts[a] + (al[a] - bound) / (al[a] - al[a - 1]) * (pts[a - 1] - pts[a]))[None])
    if b < len(pts) - 1:
        bound = lo if al[b + 1] < lo else hi
        out.append((pts[b] + (al[b] - bound) / (al[b] - al[b + 1]) * (pts[b + 1] - pts[b]))[None])
    return np.vstack(out)


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

    def band(self, *a, **k):
        return self._all("band", *a, **k)

    def dashes(self, *a, **k):
        return self._all("dashes", *a, **k)

    def blocks(self, *a, **k):
        return self._all("blocks", *a, **k)

    def ticks(self, *a, **k):
        return self._all("ticks", *a, **k)


def measure(zone, every=0.5, size=4096):
    """A marking read back off the body along its course (zone.course), station by station every `every` cm: on each
    copy of the course (its mirror image too), per station the side its texels lie on (+ the course's left, - its
    right; 0 both, when the lesser side holds a quarter or more), how far across the surface they reach from the
    course (the marking's far edge, cm) and how many there are. {copy: [(side, reach, count), ...]} and its words: the
    side flips (left to right or back), the reach's range and the empty stations."""
    from tool import bake
    courses = list(zone.course) if isinstance(zone.course, Courses) else [zone.course]
    b = bake.bake("Skin", size, size)
    nrm = b["normal"].reshape(-1, 3)
    out, words = {}, []
    for c in courses:
        for k, copy in enumerate(c._across(8.0, size=size)):
            w = zone(copy["pos"], nrm[copy["lin"]])
            on = w >= 0.5
            _, i = cKDTree(copy["P"]).query(copy["pos"][on], workers=-1)
            s = c.s[i] + ((copy["pos"][on] - copy["P"][i]) * copy["T"][i]).sum(1)
            n = max(1, int(round(c.length / every)))  # the last station takes the course's tail
            st = np.clip(np.floor(s / every).astype(int), 0, n - 1)
            d = copy["d"][on]
            rows = []
            for j in range(n):
                mine = st == j
                if not mine.any():
                    rows.append((0, 0.0, 0))
                    continue
                left = int((d[mine] > 0).sum())
                side = 0 if min(left, mine.sum() - left) * 4 >= mine.sum() else (1 if left * 2 >= mine.sum() else -1)
                here = d[mine] if side == 0 else d[mine][np.sign(d[mine]) == side]
                rows.append((side, float(np.abs(here).max()) if len(here) else 0.0, int(mine.sum())))
            name = f"{c.name}{' (mirror image)' if copy['mirrored'] else ''}"
            out[name] = rows
            sides = [r[0] for r in rows if r[2] and r[0]]
            flips = int(sum(1 for a, b in zip(sides[:-1], sides[1:]) if a != b))
            reach = [r[1] for r in rows if r[2]]
            empty = sum(1 for r in rows if not r[2])
            words.append(f"{name}: {len(rows)} stations every {every:g} cm, {flips} side flip{'s' if flips != 1 else ''}, "
                         f"reaching {min(reach):.2f} to {max(reach):.2f} cm across the surface, {empty} empty")
    return out, words


def stroke(pts):
    """The line the user drew with the Lab's pen: its points on the body (one further than OFF cm from it is
    dropped), joined by the straightest way along the surface between them, as they are."""
    pts = np.asarray(pts, np.float64).reshape(-1, 3)
    on = _surface()._locate(pts)[2]
    on = on[np.linalg.norm(on - pts, axis=1) <= OFF]
    if len(on) < 2:
        raise ValueError("the drawn line isn't on the body")
    return points(on, "the line drawn")


def points(pts, name="the points given"):
    """Any points on the car, each brought onto the surface and joined to the next by the straightest way along it
    (tool/surface.py, path)."""
    return Course(_surface().path(np.asarray(pts, np.float64)), name)


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
