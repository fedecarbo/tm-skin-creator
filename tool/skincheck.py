"""A car's skin-drawn bands checked by number, on the car, over the surface.

    python -m tool.skincheck <name>              the table; a FAIL is yours to fix
    python -m tool.skincheck <name> --falsify    every curve moved 5 mm: every check must fail
    python -m tool.skincheck <name> --floor      also measured off the zone, to show what the texture costs

What it measures, and why each one. The paint is read from the texture the car actually ships
(build/<name>/painted.npz), never from the zone that drew it, and the measuring is done by walking
the surface with an exact geodesic tracer (potpourri3d / geometry-central) in ways the painting
doesn't, so the two can disagree.

  width     Every 20 mm along the curve, a geodesic is shot across it both ways and the paint
            measured where it starts and stops. This is the width ON THE CAR, so a band that looks
            right in a render but narrows over a fold fails here.
  centre    The middle of that measured band against the curve itself.
  wobble    How far the measured middle jumps from one place to the next: crayon. A straight line
            and a circle both keep theirs steady.
  holes     The band's core -- everything within its half width, less half its feather and a texel,
            of its curve -- swept by geodesic discs walked out from every 2 mm of the curve: not the
            paint's own construction (walks square to the curve, fanned at turns), so a notch the
            paint leaves at a corner shows here. Every sample must be the band's colour or a colour
            laid after it (a band crossing on top). The longest stretch of the curve with a hole is
            the BREAK. A thin line's core is its middle.
  stray     The band's colour further from its curve than its own edge (half the width, half the
            feather and a texel), within 5 cm, and nearer this curve than any other of the colour.
  joins     Where another band crosses or meets this one, or its own curve turns sharply, a walk
            across reads the other arm or band, so those places are set aside ("at a join") rather
            than judged by width. A join is judged by the holes, and a line ENDING on another band
            (a T) by the gap left between them and the spike poking out past it.
  placed    A curve run through the user's pins: how far its middle runs from each pin. A line set
            in from the car's edge (skindraw.edge): how far its middle is from that edge, straight,
            against the distance asked (a straight line is a touch short of the way over the skin).

--falsify moves every curve 5 mm along the surface and requires every band to fail. A check that
cannot fail measures nothing (CHECKLIST.md, the car map's rounds).
"""

import argparse
import json
import sys

import numpy as np
from scipy.spatial import cKDTree

from tool import paint, paths, skinmesh

STEP = 2.0        # cm along the curve between measurements
# The limits, measured. Read through the skin, the bands on TSC_Skin came out 30.0 +- 0.16,
# 40.0 +- 0.15 and 20.0 +- 0.17 mm at the 95th, their middles within 0.1 mm: a fifth of a texel.
# (An earlier version read the paint through carmap.Map.at and got +- 1.1 to 2.2 mm, which was put
# down to "the texture's grain" and the limits loosened to match. It was the lookup, not the
# texture: --floor took the zone's own measurement at 0.00 and the gap was the reading, not the
# grain. The limits are back where the numbers put them.)
WIDTH = 1.0       # mm: how far the measured width may be from the width asked for (95th percentile)
CENTRE = 0.5      # mm: how far the measured middle may be from the curve (95th percentile)
WOBBLE = 1.0      # mm: how far the painted band's middle may jump from one place to the next (95th)
HOLES = 2.0       # mm2 of the band's core allowed unpainted (a texel is 0.8 mm2)
STRAY = 1.0       # cm2 of the band's paint allowed further from its curve than its own edge
END = 0.9         # mm: the gap or the spike allowed where a line ends on another band (a texel)
PLACED = 1.0      # mm: how far a line set in from an edge may be off its distance (95th)
PINS = 3.0        # mm: how far a curve through the user's pins may run from any of them
SOFT = 0.2        # cm: the feather of a band recorded before bands said their own
SHIFT = 0.5       # cm: how far --falsify moves a curve
JOIN_TURN = 20.0  # degrees: a band crossing at more than this, or a curve turning this sharply, is a join
FACING = np.cos(np.radians(100.0))  # skindraw.TURN: the band stops where the skin turns further away


# ---- reading the paint ----

def _texel_of(pos, nrm, w, h):
    """The texel (column, row) each point on the body falls in, and how far the point is from the
    skin (cm). Through the skin (tool/skinmesh.py): the face under the point, the car triangle
    that face came from -- on the right half, the right triangle itself -- and that triangle's own
    UVs. A strip sewn across a join came from no car triangle and holds no paint: its points are
    off the paint (inf), not read from whatever triangle index -1 wraps round to."""
    from tool import fbx
    skin = skinmesh.load()
    pos = np.asarray(pos, np.float64)
    f, _ = skin.nearest(pos, None if nrm is None else np.asarray(nrm, np.float64))
    t = skin.src[np.maximum(f, 0)]
    m = fbx.meshes()["Skin_01"]
    corners = m["positions"][m["tri_vertex"][np.maximum(t, 0)]]
    b = np.clip(skinmesh.Skin._bary(corners[:, 0], corners[:, 1], corners[:, 2], pos), 0.0, 1.0)
    b /= np.maximum(b.sum(1, keepdims=True), 1e-12)
    uv = (b[:, :, None] * m["tri_uv"][np.maximum(t, 0)]).sum(1)
    col = np.clip((uv[:, 0] % 1.0) * w, 0, w - 1).astype(np.int64)
    row = np.clip(((1.0 - uv[:, 1]) % 1.0) * h, 0, h - 1).astype(np.int64)
    d = np.linalg.norm((b[:, :, None] * corners).sum(1) - pos, axis=1)
    return col, row, np.where((f >= 0) & (t >= 0), d, np.inf)


class Palette:
    """Every colour laid on the car, each sample sorted into the one it is nearest. The first
    version scored samples along one axis, from the paint's colour to whatever the walk ended on,
    and a real livery broke it: the three colours of a sweep 4 mm apart merged into one band 44 mm
    wide, and cream over its gold edging read as gold. Sorting into the car's own colours keeps
    neighbours apart."""

    def __init__(self, colours):
        self.all = [np.asarray(c, np.float64) * 255.0 for c in colours]
        self.rgb = np.unique(np.round(np.asarray(self.all), 3), axis=0)

    def of(self, colour):
        return int(np.argmin(np.linalg.norm(self.rgb - np.asarray(colour, np.float64) * 255.0, axis=1)))

    def sort(self, rgb):
        x = np.asarray(rgb, np.float64)
        return np.argmin(np.linalg.norm(x[:, None, :] - self.rgb[None], axis=2), axis=1)

    def after(self, order):
        """The colours laid after the paint at palette position `order`: they may cover it."""
        if order is None:
            return set()
        return {self.of(c / 255.0) for c in self.all[order + 1:]}


def _edge(rgb, dist, colour, pal):
    """How far the paint reaches along a walk, in cm: where the walk last leaves it, read to a
    fraction of a sample. The walk may start on a colour laid later (a band laid under another --
    the gold under a cream stripe, showing only as its edging); it is measured from its visible
    outer edge. Returns None if the walk never reaches the paint or never leaves it."""
    mine = pal.of(colour)
    mine_c = pal.rgb[mine]
    x = rgb.astype(np.float64)
    cls = pal.sort(x)
    on = np.flatnonzero(cls == mine)
    if not len(on):
        return None
    after = np.flatnonzero((cls != mine) & (np.arange(len(cls)) > on[0]))
    if not len(after):
        return None                    # never leaves: the car ended first
    k = int(after[0])
    # What lies beyond is where the walk SETTLES, 2 mm on (the widest feather is 2 mm), not the
    # first sample sorted as something else: half-way between black and the grey body sits nearest
    # graphite, and a 4 mm hairline read 2.8 mm with graphite taken for what lay beyond it. Not past
    # the next change of colour, though: two lines 1 mm apart would read the second as "beyond".
    settle = min(k + 10, len(cls) - 1)
    nxt = np.flatnonzero((cls[k:settle + 1] == mine))
    if len(nxt):
        settle = max(k, k + int(nxt[0]) - 1)
    beyond = pal.rgb[cls[settle]]
    span = mine_c - beyond
    n2 = float(span @ span)
    if n2 < 1.0:
        return float(dist[k])
    # The half-way point itself, looked for a few samples either side of where the sorting changed:
    # a blend half-way between two colours can sit nearer a third colour on the car (orange and
    # midnight half and half is nearer graphite), which calls the change early and read the orange
    # a quarter of a millimetre narrow on each side.
    lo, hi = max(k - 6, 0), min(k + 10, len(x))
    a = ((x[lo:hi] - beyond) @ span) / n2
    below = np.flatnonzero(a < 0.5)
    below = below[below > 0]
    if not len(below):
        return float(dist[k])
    m = int(below[0])
    frac = np.clip((a[m - 1] - 0.5) / max(a[m - 1] - a[m], 1e-9), 0.0, 1.0)
    return float(dist[lo + m - 1] + frac * (dist[lo + m] - dist[lo + m - 1]))


def _across(skin, face, bary, direction, reach):
    """Walk the surface from a point in a direction, and return the points along the way with how
    far each is from the start, measured over the surface (cm), and whether it got all the way. An
    exact geodesic, so it crosses panels, seams and folds the way the car does."""
    d = np.asarray(direction, np.float64)
    n = np.linalg.norm(d)
    if n < 1e-9:
        return np.zeros((0, 3)), np.zeros(0), False
    path = np.asarray(skin.tracer().trace_geodesic_from_face(int(face), np.asarray(bary, np.float64),
                                                                   d / n * reach), np.float64)
    if len(path) < 2:
        return path, np.zeros(len(path)), False
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))])
    # The tracer cannot leave the surface: at an opening, an arch or the silhouette the walk simply
    # stops short. That, not any "off the body" test, is how a place cut by the car is known.
    reached = s[-1] >= reach * 0.98
    # sample it evenly so a long triangle doesn't hide the paint's edge
    t = np.arange(0.0, s[-1], 0.02)
    return np.stack([np.interp(t, s, path[:, k]) for k in range(3)], 1), t, reached


def _resample(pts, step):
    pts = np.asarray(pts, np.float64)
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    if s[-1] < 1e-9:
        return pts.copy(), s
    t = np.arange(0.0, s[-1] + 1e-9, step)
    return np.stack([np.interp(t, s, pts[:, k]) for k in range(3)], 1), t


def _tangents(pts):
    t = np.gradient(np.asarray(pts, np.float64), axis=0)
    return t / np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-12)


def _read(skin, p, img):
    """The colour on the car at points on the skin, and whether each one is on the paint."""
    h, w = img.shape[:2]
    f, _ = skin.nearest(p)
    col, row, off = _texel_of(p, skin.fn[np.maximum(f, 0)], w, h)
    return img[row, col], off < 0.3, f


# ---- the joins ----

class Others:
    """Every band on the car, to know where another one crosses, meets or runs on top of this one."""

    def __init__(self, drawn):
        self.drawn = drawn
        self.lines = []
        for d in drawn:
            pts, _ = _resample(d["points"], 0.1)
            self.lines.append((cKDTree(pts), _tangents(pts), float(d["width"]) / 20.0))

    def joins(self, me, q, tan, half):
        """Which of the points q (with the curve's tangent there) another band crosses or meets: its
        curve within both half widths and a millimetre, at more than JOIN_TURN to this one. A band
        running alongside or on top of this one (cream on gold, a tricolour's colours) is not a join:
        it is measured from its visible edge."""
        hit = np.zeros(len(q), bool)
        for j, (tree, tans, h2) in enumerate(self.lines):
            if j == me:
                continue
            d, i = tree.query(q, distance_upper_bound=half + h2 + 0.1)
            near = np.isfinite(d)
            if near.any():
                cos = np.abs((tans[np.minimum(i[near], len(tans) - 1)] * tan[near]).sum(1))
                hit[np.flatnonzero(near)[cos < np.cos(np.radians(JOIN_TURN))]] = True
        return hit


def _corners(pts, half):
    """The places along a curve where it turns sharply WITHIN the surface (a chevron's tip, an
    outline's corner). A line dipping over a step in the body (the nose panel's raised edge) turns in
    space, not on the skin, and its walks across read nothing else: it measured 4 of the nose band's
    27 places until turns were taken in the surface's own plane."""
    skin = skinmesh.load()
    p, s = _resample(pts, 0.05)
    tan = _tangents(p)
    k = 8                                           # 4 mm either side
    if len(p) <= 2 * k:
        return np.zeros(0)
    f, _ = skin.nearest(p[k:-k])
    n = skin.fn[np.maximum(f, 0)]
    a = tan[:-2 * k] - n * (tan[:-2 * k] * n).sum(1)[:, None]
    b = tan[2 * k:] - n * (tan[2 * k:] * n).sum(1)[:, None]
    a /= np.maximum(np.linalg.norm(a, axis=1, keepdims=True), 1e-12)
    b /= np.maximum(np.linalg.norm(b, axis=1, keepdims=True), 1e-12)
    turn = np.degrees(np.arccos(np.clip((a * b).sum(1), -1, 1)))
    sharp = np.flatnonzero(turn > JOIN_TURN) + k
    return s[sharp]


# ---- the measures ----

def measure(skin, drawing, img, pal, others=None, me=-1, read=None):
    """One band measured across itself, every STEP cm. Returns the widths and the offsets of its
    middle (mm), how many places couldn't be measured, how many places there were, the indices of
    the measured places, how many were set aside at a join, and the measured middles (cm)."""
    pts = np.asarray(drawing["points"], np.float64)
    want = float(drawing["width"])
    half = want / 20.0
    colour = drawing["colour"]
    h, w = img.shape[:2]
    reach = max(want / 10.0 * 2.0, 2.0)          # cm: twice the width, at least 2 cm
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    at = np.arange(STEP, max(s[-1] - STEP, STEP + 1e-6), STEP)
    q = np.stack([np.interp(at, s, pts[:, k]) for k in range(3)], 1)
    tan = np.stack([np.interp(at + 0.25, s, pts[:, k]) - np.interp(at - 0.25, s, pts[:, k]) for k in range(3)], 1)
    tan /= np.maximum(np.linalg.norm(tan, axis=1, keepdims=True), 1e-12)
    joined = np.zeros(len(at), bool)
    if others is not None:
        joined |= others.joins(me, q, tan, half)
    for c in _corners(pts, half):
        joined |= np.abs(at - c) < max(want / 10.0, 0.5) + 0.2
    widths, centres, missed, where, middles = [], [], 0, [], []
    f0, b0 = skin.nearest(q)
    for k in range(len(at)):
        if joined[k]:
            continue
        if f0[k] < 0:
            missed += 1
            continue
        nrm = skin.fn[f0[k]]
        t = tan[k] - nrm * (tan[k] @ nrm)
        if np.linalg.norm(t) < 1e-9:
            missed += 1
            continue
        side = np.cross(nrm, t / np.linalg.norm(t))
        edge, cut = [], False
        for sign in (1.0, -1.0):
            p, dist, reached = _across(skin, f0[k], b0[k], side * sign, reach)
            if len(p) < 2:
                edge.append(None)
                continue
            # the walk's own normal at every step, not the curve's: across a fold the surface
            # faces somewhere else, and the lookup picks the triangle that agrees with the normal
            # it is given, so one normal for the whole walk reads the wrong side of a fold
            wf, _ = skin.nearest(p)
            col, row, off = _texel_of(p, skin.fn[np.maximum(wf, 0)], w, h)
            rgb = img[row, col] if read is None else read(p[:len(col)], skin.fn[np.maximum(wf, 0)])
            on_body = off < 1.0
            ends = float(dist[-1])
            if not on_body.all():         # the walk ran off the car (an opening, an arch, the silhouette)
                # NOT `k`: that is the place along the band this loop is on, and reusing it sent
                # the other side's walk from the wrong place whenever one ran off the car
                stop = int(np.flatnonzero(~on_body)[0])
                rgb, dist = rgb[:stop], dist[:stop]
                ends = float(dist[-1]) if len(dist) else 0.0
            if len(rgb) < 3:
                edge.append(None)
                cut = True
                continue
            # A walk the car cut short still measures, if the paint ended well before the car did:
            # a line 15 mm in from the cockpit's rim walked 20 mm towards it and none was measured.
            hit = _edge(rgb, dist, colour, pal)
            if hit is not None and not reached and ends - hit < 0.25:
                hit = None
            if hit is None:
                # the paint never ended before the car did: this place is cut by the car, not
                # mismeasured. A band that runs along the lip of the cockpit really is narrower
                # there; saying "wrong width" would blame the tool for the car's own hole.
                edge.append(None)
                cut = True
                continue
            if ends - hit < 0.05:                       # the edge found IS the car's edge
                cut = True
            edge.append(hit)
        if cut or edge[0] is None or edge[1] is None:
            missed += 1
            continue
        widths.append((edge[0] + edge[1]) * 10.0)          # cm -> mm
        centres.append((edge[0] - edge[1]) / 2.0 * 10.0)   # positive: the band sits to one side
        where.append(k)
        middles.append(q[k] + side * (edge[0] - edge[1]) / 2.0)
    return (np.asarray(widths), np.asarray(centres), missed, len(at), np.asarray(where, int),
            int(joined.sum()), np.asarray(middles).reshape(-1, 3))


def holes(skin, drawing, img, pal):
    """Is the band painted all through its core? Returns the unpainted area (mm2), the longest
    stretch of the curve with a hole in it (mm), and where the worst of it is."""
    pts = np.asarray(drawing["points"], np.float64)
    half = float(drawing["width"]) / 20.0
    soft = drawing.get("soft") or SOFT
    core = half - soft / 2.0 - paint.TEXEL_CM
    line, s = _resample(pts, 0.1)                   # every mm
    if len(line) < 3:
        return 0.0, 0.0, ""
    f, b = skin.nearest(line)
    nrm = skin.fn[np.maximum(f, 0)]
    tan = _tangents(line)
    samples, station, facing = [line], [np.arange(len(line))], [nrm]
    if core > 0.03:
        tracer = skin.tracer()
        e1 = tan - nrm * (tan * nrm).sum(1)[:, None]
        e1 /= np.maximum(np.linalg.norm(e1, axis=1, keepdims=True), 1e-12)
        e2 = np.cross(nrm, e1)
        for k in range(0, len(line), 2):
            if f[k] < 0:
                continue
            for a in np.radians(np.arange(0.0, 360.0, 22.5)):
                d = np.cos(a) * e1[k] + np.sin(a) * e2[k]
                path = np.asarray(tracer.trace_geodesic_from_face(int(f[k]), b[k], d * core), np.float64)
                if len(path) < 2:
                    continue
                ps = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))])
                t = np.arange(0.05, ps[-1], 0.05)
                if not len(t):
                    continue
                samples.append(np.stack([np.interp(t, ps, path[:, c]) for c in range(3)], 1))
                station.append(np.full(len(t), k))
                facing.append(np.repeat(nrm[k][None], len(t), 0))
    q = np.vstack(samples)
    st = np.concatenate(station)
    fac = np.vstack(facing)
    rgb, on, fq = _read(skin, q, img)
    ok = on & ((skin.fn[np.maximum(fq, 0)] * fac).sum(1) >= FACING)   # where the band reaches at all
    if not drawing.get("closed"):                   # a band stops square to its curve's last cm
        head, tail = line[0], line[-1]
        dh, dt = line[0] - line[min(10, len(line) - 1)], line[-1] - line[max(-11, -len(line))]
        dh /= max(np.linalg.norm(dh), 1e-9)
        dt /= max(np.linalg.norm(dt), 1e-9)
        # two texels short of each end: the square end crosses the texels at any angle, and one up
        # to a diagonal (1.3 mm) from it is painted or not by where its centre falls (TSC_Skin's
        # spine read 45 mm2 of "holes", every one 1.0 to 1.4 mm from its end)
        ok &= ((q - head) @ dh <= -2 * paint.TEXEL_CM) & ((q - tail) @ dt <= -2 * paint.TEXEL_CM)
    mine = pal.of(drawing["colour"])
    later = pal.after(drawing.get("order"))
    cls = pal.sort(rgb)
    bad = ok & ~np.isin(cls, list({mine} | later))
    # a blend of this band and one laid over it is the other band's feathered edge, not a hole
    x = rgb.astype(np.float64)
    for c in later:
        ab = pal.rgb[c] - pal.rgb[mine]
        u = np.clip(((x - pal.rgb[mine]) @ ab) / max(ab @ ab, 1e-9), 0.0, 1.0)
        bad &= np.linalg.norm(x - (pal.rgb[mine] + u[:, None] * ab), axis=1) >= 25.0
    if not bad.any():
        return 0.0, 0.0, ""
    h, w = img.shape[:2]
    col, row, _ = _texel_of(q[bad], skin.fn[np.maximum(fq[bad], 0)], w, h)
    area = len(set(zip(col.tolist(), row.tolist()))) * (paint.TEXEL_CM * 10.0) ** 2
    gappy = np.zeros(len(line), bool)
    gappy[np.unique(st[bad])] = True
    run, worst, where = 0, 0, ""
    for k in range(len(line)):
        run = run + 1 if gappy[k] else 0
        if run > worst:
            worst, where = run, f"x {line[k, 0]:.0f}, y {line[k, 1]:.0f}, z {line[k, 2]:.0f}"
    return area, float(worst), where


def stray(skin, drawing, img, pal, drawn, bake):
    """How much of the band's colour lies off it (cm2): further from its curve than its own edge,
    within 5 cm, and nearer this curve than any other band of the same colour (its mirror, a twin
    coachline, the livery's other gold lines)."""
    mine = pal.of(drawing["colour"])
    half = float(drawing["width"]) / 20.0
    soft = drawing.get("soft") or SOFT
    edge = half + soft / 2.0 + paint.TEXEL_CM
    tri, pos, cls, rgb = bake
    pts, _ = _resample(drawing["points"], 0.05)
    here = cls == mine
    # A blend of two OTHER colours can sit nearest this one: on Solstice, orange fading into the
    # midnight gap is nearer red than either, and the red sweep read 16 cm2 "astray" all along the
    # orange's edge. A texel is this band's paint only if it is nearer this colour than any blend.
    cand = np.flatnonzero(here)
    x = rgb[cand].astype(np.float64)
    own = np.linalg.norm(x - pal.rgb[mine], axis=1)
    others = [k for k in range(len(pal.rgb)) if k != mine]
    for i, a in enumerate(others):
        for b in others[i + 1:]:
            ab = pal.rgb[b] - pal.rgb[a]
            u = np.clip(((x - pal.rgb[a]) @ ab) / max(ab @ ab, 1e-9), 0.0, 1.0)
            blend = np.linalg.norm(x - (pal.rgb[a] + u[:, None] * ab), axis=1)
            here[cand[blend < own]] = False
    d, _ = cKDTree(pts).query(pos[here], distance_upper_bound=5.0, workers=-1)
    near = np.isfinite(d)
    cand = np.flatnonzero(here)[near]
    dist = d[near]
    for other in drawn:
        if other is drawing or pal.of(other["colour"]) != mine:
            continue
        op, _ = _resample(other["points"], 0.05)
        d2, _ = cKDTree(op).query(pos[cand], workers=-1)
        dist = np.where(d2 < dist, np.inf, dist)
    off = (dist > edge) & np.isfinite(dist)
    area = float(off.sum() * paint.TEXEL_CM ** 2)
    where = ""
    if off.any():
        p = np.median(pos[cand[off]], axis=0)
        where = f"x {p[0]:.0f}, y {p[1]:.0f}, z {p[2]:.0f}"
    return area, where


def ends(skin, drawing, img, pal, drawn):
    """A line that ends on another band (a T): across the line's end, every texel of its width, is
    there a gap between it and the band it meets, or does it poke out the far side? Returns the
    worst gap and the worst spike (mm), or None if neither end meets another band."""
    if drawing.get("closed"):
        return None
    pts = np.asarray(drawing["points"], np.float64)
    half = float(drawing["width"]) / 20.0
    mine = pal.of(drawing["colour"])
    gap = spike = None
    tracer = skin.tracer()
    for end, prev in ((pts[-1], pts[-2]), (pts[0], pts[1])):
        meets = None
        for other in drawn:
            if other is drawing:
                continue
            op, _ = _resample(other["points"], 0.05)
            dd = np.linalg.norm(op - end, axis=1)
            if dd.min() < float(other["width"]) / 20.0:
                meets = other
                break
        if meets is None:
            continue
        theirs = pal.of(meets["colour"])
        h2 = float(meets["width"]) / 20.0
        f, b = skin.nearest(end[None])
        n = skin.fn[f[0]]
        fwd = end - prev
        fwd -= n * (fwd @ n)
        fwd /= max(np.linalg.norm(fwd), 1e-12)
        side = np.cross(n, fwd)
        g = sp = 0.0
        for u in np.linspace(-(half - paint.TEXEL_CM), half - paint.TEXEL_CM, 9):
            # from a point across the line's end, back along the line and on through the other band
            if abs(u) > 1e-6:
                path = np.asarray(tracer.trace_geodesic_from_face(int(f[0]), np.asarray(_bary1(skin, f[0], end)),
                                                                  side * u), np.float64)
                start = path[-1]
            else:
                start = end
            back = start - fwd * (half + 0.4)
            line = np.stack([back + fwd * t for t in np.arange(0.0, half + 0.4 + 2 * h2 + 0.6, 0.02)])
            fl, bl = skin.nearest(line)
            line = skin.point(fl, bl)
            rgb, on, _ = _read(skin, line, img)
            cls = pal.sort(rgb)
            # a blend of the two bands' colours is where they meet, whatever colour it sits nearest:
            # half teal, half gold is nearer lime, and read as a 1 mm gap at a join that had none
            a_c, b_c = pal.rgb[mine], pal.rgb[theirs]
            ab = b_c - a_c
            u = np.clip(((rgb.astype(np.float64) - a_c) @ ab) / max(ab @ ab, 1e-9), 0.0, 1.0)
            between = np.linalg.norm(rgb.astype(np.float64) - (a_c + u[:, None] * ab), axis=1) < 25.0
            cls = np.where(between & (cls != mine) & (cls != theirs), np.where(u < 0.5, mine, theirs), cls)
            last_mine = np.flatnonzero(cls == mine)
            first_theirs = np.flatnonzero(cls == theirs)
            if not len(last_mine) or not len(first_theirs):
                continue
            a, z = int(first_theirs[0]), int(first_theirs[-1])
            before = np.flatnonzero(cls[:a] == mine)
            if len(before):
                g = max(g, (a - int(before[-1]) - 1) * 0.2)          # mm: samples are 0.2 mm apart
            beyond = np.flatnonzero(cls[z + 1:] == mine)
            if len(beyond):
                sp = max(sp, (int(beyond[-1]) + 1) * 0.2)
        gap = max(gap or 0.0, g)
        spike = max(spike or 0.0, sp)
    if gap is None:
        return None
    return gap, spike


def _bary1(skin, face, p):
    c = skin.V[skin.F[face]]
    b = np.clip(skinmesh.Skin._bary(c[0][None], c[1][None], c[2][None], p[None])[0], 0.0, 1.0)
    return b / max(b.sum(), 1e-12)


def placed(drawing, middles):
    """Where the line was meant to be: the user's pins it runs through, or the edge it is set in
    from. Returns (text, error mm, limit) or None."""
    if "pins" in drawing and drawing["pins"]:
        # each pin where it lands on the skin: the pins are clicked on the viewer's car, 1 to 5 mm off
        # the drawing surface, and the curve runs through the skin under them
        skin = skinmesh.load()
        f, b = skin.nearest(np.asarray(drawing["pins"], np.float64))
        pts, _ = _resample(drawing["points"], 0.01)
        d, _ = cKDTree(pts).query(skin.point(f, b))
        off = np.abs(d * 10.0 - abs(float(drawing.get("offset", 0.0))))
        return f"pins {np.max(off):.1f}", float(np.max(off)), PINS
    if "edge" in drawing and drawing.get("from_edge") and len(middles):
        e = np.asarray(drawing["edge"], np.float64)
        closed = not drawing.get("closed") is False and np.linalg.norm(e[0] - e[-1]) < 3.0
        A = e if closed else e[:-1]
        B = np.roll(e, -1, 0) if closed else e[1:]
        AB = B - A
        t = np.clip(((middles[:, None] - A[None]) * AB[None]).sum(-1) / np.maximum((AB * AB).sum(-1), 1e-12)[None], 0, 1)
        d = np.linalg.norm(middles[:, None] - (A[None] + t[..., None] * AB[None]), axis=-1).min(1) * 10.0
        err = np.abs(d - float(drawing["from_edge"]))
        e95 = float(np.percentile(err, 95))
        return f"edge {np.median(d):.1f}+-{e95:.1f}", e95, PLACED
    return None


def check(name, falsify=False, floor=False):
    folder = paths.BUILD / name
    meta = json.loads((folder / "painted.json").read_text())
    drawn = [d for d in meta.get("drawn", []) if d.get("kind") == "skin line"]
    if not drawn:
        print(f"{name}: nothing was drawn on the skin (tool/skindraw.py). Nothing to check.")
        return []
    img = np.load(folder / "painted.npz")["Skin_B"]
    skin = skinmesh.load()
    # Every colour on the car, not only the drawn ones: a dark band otherwise counts the dark
    # background as its own paint (the nose band's dark purple matched 2.68 M texels).
    pal = Palette(meta.get("palette") or [d["colour"] for d in meta.get("drawn", [])])
    if falsify:
        for d in drawn:
            p = np.asarray(d["points"], np.float64)
            f, b = skin.nearest(p)
            nrm = skin.fn[np.maximum(f, 0)]
            tan = np.gradient(p, axis=0)
            side = np.cross(nrm, tan / np.maximum(np.linalg.norm(tan, axis=1, keepdims=True), 1e-9))
            moved = p + side * SHIFT
            f2, b2 = skin.nearest(moved)
            d["points"] = skin.point(f2, b2).tolist()   # kept on the car, just not where the paint is
    from tool import bake as bakes
    h, w = img.shape[:2]
    bk = bakes.bake("Skin", w, h)
    tri = bk["tri"].reshape(-1)
    idx = np.flatnonzero(tri >= 0)
    rows, cols = np.divmod(idx, w)
    baked = (tri[idx], bk["position"].reshape(-1, 3)[idx], pal.sort(img[rows, cols]), img[rows, cols])
    others = Others(drawn)

    floors = []
    print(f"{'band':26} {'mm':>4} {'places':>9} {'width mm':>14} {'centre mm':>13} {'wobble':>6} "
          f"{'holes':>6} {'break':>5} {'stray':>5} {'end':>9} {'placed':>14}  verdict")
    print("-" * 140)
    fails = []
    for me, d in enumerate(drawn):
        widths, centres, missed, total, w_at, joined, middles = measure(skin, d, img, pal, others, me)
        hole, brk, hwhere = holes(skin, d, img, pal)
        st, swhere = stray(skin, d, img, pal, drawn, baked)
        end = ends(skin, d, img, pal, drawn)
        place = placed(d, middles)
        if floor:
            # The same measurement taken off the zone that painted, instead of off the texture:
            # what the check would read if the texture had no grain at all.
            from tool import skindraw
            pts = np.asarray(d["points"], np.float64)
            f, _ = skin.nearest(pts)
            zone = skindraw.band(skindraw.Curve(skin, pts, f, name=d["name"]), float(d["width"]))

            def read(p, n, _z=zone, _c=d["colour"]):
                wz = _z(p, n)[:, None]
                return (np.asarray(_c) * 255.0)[None] * wz + np.array([0.0, 0.0, 0.0])[None] * (1 - wz)

            fw = measure(skin, d, img, pal, others, me, read=read)[0]
            floors.append(f"{np.percentile(np.abs(fw - float(d['width'])), 95):.2f}" if len(fw) else "-")
        want = float(d["width"])
        bad = []
        if not len(widths):
            bad.append("nothing measured")
            wtxt, ctxt = "-", "-"
        else:
            werr = np.abs(widths - want)
            cerr = np.abs(centres)
            w95, c95 = np.percentile(werr, 95), np.percentile(cerr, 95)
            wtxt = f"{np.median(widths):5.1f} +-{w95:4.2f}"
            ctxt = f"{np.median(cerr):4.2f} +-{c95:4.2f}"
            if w95 > WIDTH:
                bad.append(f"width {w95:.2f}")
            if c95 > CENTRE:
                bad.append(f"centre {c95:.2f}")
        # Crayon is a middle that JUMPS: a straight line and a circle both keep theirs steady, one
        # turning not at all and the other the same amount everywhere. So the measure is how much the
        # painted band's middle moves from one place to the next -- on the paint, not on the curve,
        # because the curve is what was asked for and the paint is what the user sees. (The first
        # version measured how much the curve turned, and failed a true circle for being round.)
        wob = 0.0
        if len(centres) > 3:
            nextdoor = np.diff(w_at) == 1                 # only places side by side along the band
            jumps = np.abs(np.diff(centres))[nextdoor]
            wob = float(np.percentile(jumps, 95)) if len(jumps) else 0.0
        if wob > WOBBLE:
            bad.append(f"wobble {wob:.1f}")
        if hole > HOLES:
            bad.append(f"holes {hole:.0f} mm2 (break {brk:.0f} mm at {hwhere})")
        if st > STRAY:
            bad.append(f"stray {st:.1f} cm2 at {swhere}")
        etxt = "-"
        if end is not None:
            etxt = f"{end[0]:.1f}/{end[1]:.1f}"
            if end[0] > END:
                bad.append(f"gap {end[0]:.1f} mm where it ends on another band")
            if end[1] > END:
                bad.append(f"spike {end[1]:.1f} mm past the band it ends on")
        ptxt = "-"
        if place is not None:
            ptxt, perr, plim = place
            if perr > plim:
                bad.append(f"placed {ptxt} mm")
        verdict = "ok" if not bad else "FAIL " + ", ".join(bad)
        if bad:
            fails.append((d["name"], verdict))
        jtxt = f"+{joined}j" if joined else ""
        print(f"{d['name'][:26]:26} {want:4.1f} {len(widths):3d}/{total:<3d}{jtxt:>3} {wtxt:>14} {ctxt:>13} {wob:6.1f} "
              f"{hole:6.1f} {brk:5.0f} {st:5.1f} {etxt:>9} {ptxt:>14}  {verdict}")
    print()
    if floors:
        print(f"the texture's own floor, the same measurement taken off the zone instead of the texture: "
              f"{', '.join(floors)} mm at the 95th. What is over that is the texture's grain, not the band.")
    print(f"limits: width and centre within {WIDTH:.1f} and {CENTRE:.1f} mm at the 95th percentile, the middle jumping under "
          f"{WOBBLE:.1f} mm from one place to the next, under {HOLES:.0f} mm2 of the core unpainted, under {STRAY:.1f} cm2 "
          f"astray, a line ending on another band within {END:.1f} mm of it and not past it, a line set in from an edge "
          f"within {PLACED:.1f} mm of its distance, a curve through pins within {PINS:.0f} mm of each. Measured ON the car, "
          f"by exact geodesics, off the texture the car ships. Places +nj are at a join (another band, a sharp turn) "
          f"and judged by the holes and the end instead of by width.")
    if falsify:
        if len(fails) == len(drawn):
            print(f"FALSIFY: every curve moved {SHIFT * 10:.0f} mm and all {len(drawn)} bands fail, as they must.")
            return []
        passed = [d["name"] for d in drawn if d["name"] not in {n for n, _ in fails}]
        print(f"FALSIFY: with every curve moved {SHIFT * 10:.0f} mm, {len(passed)} of {len(drawn)} bands still pass: "
              f"{', '.join(passed)}. The check can't see them.")
        return [("falsify", "the check passed a moved band")]
    print("all bands pass" if not fails else f"{len(fails)} of {len(drawn)} bands FAIL")
    return fails


def main():
    ap = argparse.ArgumentParser(description="a car's skin-drawn bands checked by number")
    ap.add_argument("name")
    ap.add_argument("--falsify", action="store_true", help="move every curve 5 mm: every check must fail")
    ap.add_argument("--floor", action="store_true", help="also measure the zone itself, to show what the texture costs")
    a = ap.parse_args()
    sys.exit(1 if check(a.name, a.falsify, a.floor) else 0)


if __name__ == "__main__":
    main()
