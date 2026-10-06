"""A course: a path along one of the car's own lines, and markings laid along it. The user, 2026-10-05,
drawing with the Lab's pen: "Do an interval lines with DO NOT STEP text." A marking belongs to a line
of the car (a guide, a seam, a panel's edge) or to the line the user drew, and the tool lays it along
that line in one go: a strip, dashes, ticks, spots or words.

    course.level("between 3")                the level's line along the left side (side="right" the other)
    course.seam("side skirt")                a seam (tool/seams.py), the left side
    course.edge("sidepod top", near=(55, 61, -40))   a panel's edge: its outline (the loop nearest `near`,
                                             else the longest), the panel on its left as it runs, seen from
                                             outside; side="left" picks the panel's instance
    course.top_line("top 1")                 one of the top's lines (car/top_lines.json), the left half
    course.stroke(points)                    the line the user drew (tool.notes show_drawn prints its points):
                                             smoothed over SMOOTH cm and laid on the body
    course.points([(x, y, z), ...])          any points on the car, joined straight
  Shaped:
    c.between(-128, -50)                     the stretch between two lengths along the car, or two points
                                             (on a loop: from the first to the second the way it runs)
    c.then(other)                            on along another course (joined straight where they don't meet)
    c.rounded(8)                             its corners rounded over 8 cm
    c.mirrored()                             the same on both sides; c.reversed() the other way
    c.length, c.start, c.middle, c.end, c.at(z=-70), c.at(s=20)   points on it (cm)
    c.places(every=20)                       points every 20 cm along it, a whole gap at each end, for marks
  Markings, as zones (tool/shapes.py) for s.paint(..., zone=), measured across the surface:
    c.strip(1.0)                             a strip 1 cm wide along it, its ends square
    c.dashes(5, gap=3, width=1)              dashes 5 cm long with 3 cm gaps, a whole dash at each end
    c.ticks(every=10, length=3, width=0.6, side=1)   short strokes square to it every 10 cm, to its left (+1),
                                             its right (-1) or both ways (0)
    s.text("NO STEP", "engine cover", at=c.between(-74, -62))   words (a placard, a mark) at a stretch's
                                             middle, reading along it, upright to someone beside the car
A marking lands only on skin facing within FACING of the course's own surface, never on the far side
of a thin panel. The checks (tool/checks.py) read each dash and tick as they read any small mark.
"""

import numpy as np
from scipy.spatial import cKDTree

from tool import shapes
from tool.noise import smoothstep

STEP = 0.25    # cm between a course's points
SMOOTH = 2.5   # cm: the surface's facing along a course, and a stroke's path, are averaged over this
FACING = 0.5   # a texel takes a marking when it faces within 60 degrees of the course's surface there
OFF = 3.0      # cm: a stroke's point further than this from the body is dropped
MIRROR = np.array([-1.0, 1.0, 1.0])


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
        self.pts = _resample(pts, STEP, closed)
        self.name, self.closed, self.mirror = name, closed, mirror
        self.s = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(self.pts, axis=0), axis=1))]
        self.tan = _tangent(self.pts, closed)
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

    def mirrored(self):
        """The same on both sides of the car."""
        return Course(self.pts, self.name, self.nrm, self.closed, True)

    def reversed(self):
        return Course(self.pts[::-1], self.name, self.nrm[::-1], self.closed, self.mirror)

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
        (s -> cm inside the marking along it, negative outside) says so."""
        P, T, N, S = self._both()
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
            inside = np.minimum(half - across, along(S[i] + a, i))
            ok = (qn * N[i]).sum(1) >= FACING
            w[box[live]] = smoothstep(-soft / 2, soft / 2, inside) * ok
            return w
        z = shapes.Zone(f, label=label)
        z.course = self
        return z

    def strip(self, width, soft=shapes.SOFT):
        """A strip `width` cm wide along the course, its ends square to it."""
        L = self.length
        along = (lambda s, i: np.full(len(s), 1e3)) if self.closed else (lambda s, i: np.minimum(s, L - s))
        return self._zone(width / 2, along, f"a strip {width:g} cm wide along {self.name}", soft)

    def dashes(self, length, gap=None, width=1.0, soft=shapes.SOFT):
        """Dashes `length` cm long with `gap` cm between (as long as a dash), `width` cm wide, the run of
        them centred on the course so a whole dash sits at each end (on a loop, spaced evenly round)."""
        gap = length if gap is None else gap
        L, period = self.length, length + gap
        if self.closed:
            n = max(1, int(round(L / period)))
            period, s0 = L / n, 0.0
            length = min(length, period)
        else:
            n = max(1, int((L + gap) // period))
            s0 = (L - (n * period - gap)) / 2

        def along(s, i):
            k = np.clip(np.floor((s - s0) / period), 0, n - 1)
            local = s - s0 - k * period
            return np.minimum(local, length - local)
        return self._zone(width / 2, along, f"dashes {length:g} cm long, {gap:g} apart, {width:g} cm wide along {self.name}", soft)

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

def _side_sign(side):
    if side not in ("left", "right"):
        raise ValueError(f"side is 'left' or 'right', not {side!r}")
    return 1.0 if side == "left" else -1.0


def level(name, side="left"):
    """The level's line along one side of the car, its longest stretch: on each slice of the body (the
    car map's, every cm) the outermost point of the open side at the level's height."""
    from tool import carmap, levels
    L = levels._find(name)
    m = carmap.load()
    Z, st, q = m.sec["Z"], m.sec["starts"], m.sec["q"]
    found = []
    for k, z in enumerate(Z):
        if not L.runs(z):
            continue
        pts = q[st[k]:st[k + 1]].astype(np.float64)
        if len(pts) < 2:
            continue
        y = float(L.Y(z))
        a, b = pts[:-1], pts[1:]
        cross = ((a[:, 1] - y) * (b[:, 1] - y) <= 0) & (np.abs(b[:, 1] - a[:, 1]) > np.abs(b[:, 0] - a[:, 0]))
        cross &= (a[:, 0] > 2) & (b[:, 0] > 2)
        if not cross.any():
            continue
        t = (y - a[cross, 1]) / np.where(np.abs(b[cross, 1] - a[cross, 1]) < 1e-9, 1e-9, b[cross, 1] - a[cross, 1])
        x = a[cross, 0] + t * (b[cross, 0] - a[cross, 0])
        found += [(float(xi), y, float(z)) for xi in x]
    if len(found) < 2:
        raise ValueError(f"{L}: no line along the {side} side")
    found = np.array(found)
    found = found[m.value("open", found) >= 0.1]  # the outer body: not an inlet's inside
    out = []
    for z in np.unique(found[:, 2]):
        at = found[found[:, 2] == z]
        out.append(at[np.argmax(at[:, 0])])
    pts = np.array(out)[::-1]  # the slices run from the tail: the course runs nose to tail
    pts = _longest_run(pts)
    c = Course(_smooth(_resample(pts), 1.0) if len(pts) > 2 else pts, f"the level {L!r} on the {side}")
    return c if side == "left" else _flip(c)


def _longest_run(pts, gap=6.0):
    """The longest stretch of points with no gap over `gap` cm."""
    d = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    cuts = np.flatnonzero(d > gap)
    starts, ends = np.r_[0, cuts + 1], np.r_[cuts + 1, len(pts)]
    k = int(np.argmax(ends - starts))
    return pts[starts[k]:ends[k]]


def _flip(c):
    return Course(c.pts * MIRROR, c.name.replace("left", "right"), c.nrm * MIRROR, c.closed, c.mirror)


def seam(name, side="left"):
    """A seam (tool/seams.py) as a course, tail to nose on one side."""
    from tool import seams
    path = np.asarray(seams.traced()[name]["path"], np.float64)
    c = Course(path, f"the seam {name!r} on the {side}")
    return c if side == "left" else _flip(c)


def top_line(name):
    """One of the top's lines (car/top_lines.json), the left half as drawn: from the tail's middle."""
    from tool import levels
    path = next((L["path"] for L in levels.top_lines() if L["name"].lower() == name.lower()), None)
    if path is None:
        raise ValueError(f"no top line called {name!r}")
    return Course(np.asarray(path, np.float64), f"the top line {name!r}")


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
