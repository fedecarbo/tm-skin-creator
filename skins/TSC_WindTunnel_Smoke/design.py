"""TSC_WindTunnel_Smoke: concept B of TSC_WindTunnel's first set (2026-09-29).

The car as a 1970s wind tunnel photograph: a smoke rake in front of the nose sends a row of thin,
even smoke lines over a gloss black car. Calm and parallel where the air is laminar, parting round
the nose fin and the cockpit and fanning out over the sidepods, then breaking into a gentle wake
behind the sidepods and over the tail. One signal red line, the one that hits the car head-on,
runs down the spine from the nose to the cockpit's front.

How the lines are drawn (all in this file, measured on the car's own mesh):
- The top lines (four a side) follow the body's girth: every centimetre along the car, the section
  of the outer panels is walked from the obstacle's edge (the nose fin, the cockpit rim, the number
  and name panels) out to where the top ends (the nose's crease, the front flank's fold, the
  sidepod's and the deck's outer edge). The lines sit at even steps across that span, so they part
  round the cockpit and spread as the car widens. The span's end is a lower envelope (a running
  minimum, then smoothed), so no line runs off an edge.
- The flank lines (two a side) sit at even heights on the side-facing panels: they start at the
  rim of the opening under the front flank, pass under the sidepod inlet (the upper one 4 cm below
  its lip) and run back along the flank; the lower one ends at the rear wheel arch, the upper one
  rises over it and runs on to the tail.
- Behind the sidepods (z < -45) every line waves, the waves growing towards the tail: the wake.
- The top lines and the red one start together in a row at z 198, a little behind the nose's tip
  (the rake): run on to the tip they crowded into a white fan (the first paint). The nose fin's
  blade is thinner than a line, so it is red all over where the red line meets it.
- Lines are painted as a 1.7 cm band round a line of points on the surface (3D distance), so the
  width is the same on every curve.
"""

import functools

import numpy as np
from scipy.ndimage import gaussian_filter1d, minimum_filter1d
from scipy.spatial import cKDTree

from tool import fbx, parts, shapes
from tool.noise import smoothstep

BLACK = "#0c0d0f"   # the photograph's black, piano lacquer
SMOKE = "#efeee9"   # the smoke
RED = "#e2231a"     # the one tagged streamline
DARK = "#141518"    # wheels and inner car

WIDTH = 1.7         # cm, every line
TOP_LINES = 4       # per side, besides the red spine
WAKE_Z = -45.0      # behind the sidepods the lines start to wave
START_Z = 198.0     # the rake's row: every line starts here, a little behind the nose's tip
TAIL_Z = -162.0

# the outer panels a section walks over (the inlet, the side skirt's ledge, the pylons and the
# diffuser are never part of it, so no line can reach them)
SECTION = ("body shell", "nose tip", "nose panel", "cockpit surround", "sidepod top", "rear flank",
           "rear quarter panel", "engine cover", "tail corner", "tail panel", "fuel cap", "number panel",
           "engine cover panel")
LINE_PARTS = ["body shell", "nose tip", "nose panel", "cockpit surround", "sidepod top", "rear flank",
              "rear quarter panel", "engine cover|part", "tail corner", "tail panel", "fuel cap"]
FLANK_PARTS = ["body shell", "sidepod top", "rear flank", "tail corner"]
SPINE_PARTS = ["nose tip", "nose panel", "body shell"]


# ---- the car's sections ----

@functools.lru_cache(maxsize=1)
def _mesh():
    P = parts.load()
    m = fbx.meshes()["Skin_01"]
    tv = m["tri_vertex"]
    pos = m["positions"].astype(np.float64)
    tp = P.tri_part[P.mesh_offset["Skin"]:P.mesh_offset["Skin"] + len(tv)]
    names = np.array([inst["name"] for inst in P.instances])[tp]
    keep = np.isin(names, SECTION)
    tri = pos[tv[keep]]
    nrm = m["tri_normal"][keep].mean(1)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    names = names[keep]
    left = tri[:, :, 0].max(1) > -0.5  # the left half; the right is its mirror
    tri, nrm, names = tri[left], nrm[left], names[left]
    return tri, nrm, names, tri[:, :, 2].min(1), tri[:, :, 2].max(1)


def _section(z0):
    """The outer panels cut at z0, walked from the top's centre out and down: points (n, 2) of
    (x, y), girth s (n,), whether the step after each point is a gap (an opening), and each
    point's normal's y. The body turning under (normals facing down) ends it."""
    tri, nrm, names, zmin, zmax = _mesh()
    sel = np.flatnonzero((zmin < z0) & (zmax > z0))
    if not len(sel):
        return None
    t = tri[sel]
    d = t[:, :, 2] - z0
    cs, ps = [], []
    for a, b in ((0, 1), (1, 2), (2, 0)):
        c = (d[:, a] < 0) != (d[:, b] < 0)
        s = d[:, a] / np.where(c, d[:, a] - d[:, b], 1)
        ps.append(t[:, a] + s[:, None] * (t[:, b] - t[:, a]))
        cs.append(c)
    c = np.stack(cs, 1)
    pp = np.stack(ps, 1)
    ok = c.sum(1) == 2
    first = np.argsort(~c, axis=1, kind="stable")[:, :2]
    r = np.arange(len(sel))
    p0, p1 = pp[r, first[:, 0], :2], pp[r, first[:, 1], :2]
    ny = nrm[sel, 1]
    good = ok & (ny > -0.35)
    p0, p1, ny = p0[good], p1[good], ny[good]
    if not len(p0):
        return None
    # chain the segments into polylines by their shared ends
    k0 = [tuple(v) for v in np.round(p0, 2)]
    k1 = [tuple(v) for v in np.round(p1, 2)]
    ends = {}
    for i in range(len(p0)):
        ends.setdefault(k0[i], []).append((i, 0))
        ends.setdefault(k1[i], []).append((i, 1))
    used = np.zeros(len(p0), bool)
    chains = []
    for i0 in range(len(p0)):
        if used[i0]:
            continue
        used[i0] = True
        seq, nys = [p0[i0], p1[i0]], [ny[i0], ny[i0]]
        for forward in (True, False):
            key = k1[i0] if forward else k0[i0]
            while True:
                nxt = [(j, e) for j, e in ends.get(key, ()) if not used[j]]
                if not nxt:
                    break
                j, e = nxt[0]
                used[j] = True
                far, key = (p1[j], k1[j]) if e == 0 else (p0[j], k0[j])
                if forward:
                    seq.append(far)
                    nys.append(ny[j])
                else:
                    seq.insert(0, far)
                    nys.insert(0, ny[j])
        chains.append((np.array(seq), np.array(nys)))
    # every chain resampled finely, then only the outermost surface kept in each direction from a
    # point inside the body: panels that lie on others (the nose panel on the nose tip, the rim on
    # the shell) would count twice and make the lines wander
    dense, dny = [], []
    for q, nys in chains:
        seg = np.linalg.norm(np.diff(q, axis=0), axis=1)
        for i, L in enumerate(seg):
            n = max(1, int(np.ceil(L / 0.2)))
            t = np.arange(n)[:, None] / n
            dense.append(q[i] + t * (q[i + 1] - q[i]))
            dny.append(np.full(n, nys[i + 1] if i + 1 < len(nys) else nys[i]))
        dense.append(q[-1:])
        dny.append(nys[-1:])
    dense, dny = np.concatenate(dense), np.concatenate(dny)
    centre = np.array([-1.0, min(35.0, dense[:, 1].min() - 3)])
    rel = dense - centre
    ang = np.arctan2(rel[:, 1], rel[:, 0])
    rad = np.hypot(rel[:, 0], rel[:, 1])
    bins = np.floor(ang / np.radians(0.25)).astype(np.int64)
    order = np.lexsort((-rad, -bins))  # angle descending, the outermost first in each bin
    first = np.r_[True, bins[order][1:] != bins[order][:-1]]
    keep = order[first]
    pts, nyl = dense[keep], dny[keep]
    step = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.r_[0, np.cumsum(step)]
    gap = np.r_[step > 3.0, False]
    return pts, s, gap, nyl


def _at(sec, g):
    """The (x, y) at girth g on a section, or None where g falls in an opening or off its ends."""
    pts, s, gap, _ = sec
    if g < s[0] or g > s[-1]:
        return None
    i = int(np.searchsorted(s, g, side="right")) - 1
    i = min(max(i, 0), len(s) - 2)
    if gap[i]:
        return None
    t = (g - s[i]) / max(s[i + 1] - s[i], 1e-9)
    return pts[i] + t * (pts[i + 1] - pts[i])


def _girth_at_x(sec, x):
    """The girth where the section's top first reaches x (flat before its first point)."""
    pts, s, _, _ = sec
    k = np.flatnonzero(pts[:, 0] >= x)
    if not len(k):
        return s[-1]
    k = k[0]
    if k == 0:
        return s[0] - (pts[0, 0] - x)
    t = (x - pts[k - 1, 0]) / max(pts[k, 0] - pts[k - 1, 0], 1e-9)
    return s[k - 1] + t * (s[k] - s[k - 1])


def _top_end(sec, z0, start):
    """Where the top ends on a section, walking out from girth `start`: ahead of the cockpit, the
    first opening (the front flank's fold) or the crease; further back, where the panels first
    stop facing up (the sidepod's and deck's outer edge, never the flare below the shoulder)."""
    pts, s, gap, ny = sec
    after = s >= start
    first_gap = np.flatnonzero(gap & after)
    end = s[first_gap[0]] if len(first_gap) else s[-1]
    if z0 < -118:
        # the tail slopes down to the back, so it hardly faces up: its top ends at its outer
        # rounding, about x 45
        return min(end, _girth_at_x(sec, 45.0))
    if z0 < 60:
        # the first run of 2 cm or more that stops facing up (a seam's odd normal isn't an edge)
        side = after & (s <= end) & (ny < 0.3) & (s > start + 2)
        idx = np.flatnonzero(side)
        if len(idx):
            breaks = np.flatnonzero(np.diff(idx) > 1)
            starts = np.r_[idx[0], idx[breaks + 1]]
            stops = np.r_[idx[breaks], idx[-1]]
            for b0, b1 in zip(starts, stops):
                if s[b1] - s[b0] >= 2.0 or b1 == len(s) - 1:
                    end = min(end, s[b0])
                    break
    return end


def _obstacle(z):
    """How far out (cm) the top lines keep from the middle: the red spine alone ahead of the nose
    fin, the fin's plate (x 8.2), the cockpit rim, the number and name panels (x 20.1), then
    closing in over the tail."""
    tri, nrm, names, zmin, zmax = _mesh()
    rim = names == "cockpit surround"
    out = np.zeros_like(z)
    for i, z0 in enumerate(z):
        if z0 > 165:
            out[i] = 0
        elif z0 > 145:
            out[i] = 9.5 * (165 - z0) / 20
        elif z0 > 100:
            out[i] = 9.5
        elif z0 > -52:
            # the cockpit opening's edge where the section cuts the rim (the rim itself runs 10 cm
            # down the slope and takes lines like the rest of the shell)
            t = tri[rim & (zmin < z0) & (zmax > z0)]
            edge = 0.0
            if len(t):
                d = t[:, :, 2] - z0
                xs = []
                for a_, b_ in ((0, 1), (1, 2), (2, 0)):
                    c = (d[:, a_] < 0) != (d[:, b_] < 0)
                    if c.any():
                        s_ = d[c, a_] / (d[c, a_] - d[c, b_])
                        xs.append(t[c, a_, 0] + s_ * (t[c, b_, 0] - t[c, a_, 0]))
                if xs:
                    edge = float(np.concatenate(xs).min())
            out[i] = max(9.5, edge + 6.0, 23.5 if z0 < -35 else 0.0)
        elif z0 > -124:
            out[i] = 23.5
        else:
            out[i] = 23.5 - 11.5 * (-124 - z0) / 38
    return gaussian_filter1d(out, 4, mode="nearest")


def _wake(z, k, amp, wavelength=30.0):
    """A wave growing from nothing at WAKE_Z to amp at the tail; each line's phase a little later
    than its neighbour's, so the wake rolls across the car rather than flapping in step."""
    t = np.clip((WAKE_Z - z) / (WAKE_Z - TAIL_Z), 0, 1)
    return amp * t ** 1.4 * np.sin(2 * np.pi * (WAKE_Z - z) / wavelength + 0.55 * k)


@functools.lru_cache(maxsize=1)
def top_lines():
    """The top lines' points, (n, 3) per line, the left side's; the right mirrors them."""
    Z = np.arange(START_Z, TAIL_Z, -1.0)
    secs = [_section(z0) for z0 in Z]
    xo = _obstacle(Z)
    # each section's own girth at the obstacle's edge (its start moves where the fin or the cockpit
    # begins, so this is never smoothed), and the top's width from there: that is smoothed, as a
    # lower envelope, so the lines never run off an edge
    a = np.array([_girth_at_x(sec, x) if sec else 0.0 for sec, x in zip(secs, xo)])
    span = np.array([_top_end(sec, z0, ai) - ai if sec else np.nan for sec, z0, ai in zip(secs, Z, a)])
    span = np.where(np.isnan(span), np.nanmin(span), span)
    low = minimum_filter1d(span, 5, mode="nearest")
    span = gaussian_filter1d(minimum_filter1d(span, 25, mode="nearest"), 7, mode="nearest")
    span = np.maximum(np.minimum(span, low), 4.0)
    lines = []
    for k in range(1, TOP_LINES + 1):
        g = a + span * k / (TOP_LINES + 0.6) + _wake(Z, k, 3.2)
        raw = [(_at(sec, gk) if sec else None) for sec, gk in zip(secs, g)]
        lines.append(_smooth(raw, secs, Z))
    return lines


def _smooth(raw, secs, Z, sigma=2.5, jump=4.0):
    """A line's (x, y) per section smoothed along the car, in unbroken runs, and put back on
    each section's surface: calm, with no ripple from the mesh."""
    out = [None] * len(raw)
    runs, cur = [], []
    for i, p in enumerate(raw):
        if p is not None and cur and np.linalg.norm(p - raw[cur[-1]]) > jump:
            runs.append(cur)
            cur = []
        if p is None:
            if cur:
                runs.append(cur)
            cur = []
        else:
            cur.append(i)
    if cur:
        runs.append(cur)
    for run in runs:
        xy = np.array([raw[i] for i in run])
        if len(run) > 3:
            xy = gaussian_filter1d(xy, sigma, axis=0, mode="nearest")
        for i, p in zip(run, xy):
            q = secs[i][0]
            a, b = q[:-1], q[1:]
            ab = b - a
            t = np.clip(((p - a) * ab).sum(1) / np.maximum((ab * ab).sum(1), 1e-9), 0, 1)
            near = a + t[:, None] * ab
            j = int(np.argmin(((near - p) ** 2).sum(1)))
            out[i] = np.array([near[j, 0], near[j, 1], Z[i]])
    return out


def _dense(pts, step=0.25, jump=4.0):
    """A line's points every `step` cm, broken where a point is missing or the next one jumps."""
    out = []
    for p, q in zip(pts[:-1], pts[1:]):
        if p is None or q is None:
            continue
        d = float(np.linalg.norm(q - p))
        if d > jump:
            continue
        n = max(2, int(np.ceil(d / step)) + 1)
        t = np.linspace(0, 1, n)[:, None]
        out.append(p + t * (q - p))
    return np.concatenate(out) if out else np.zeros((0, 3))


def _band(points, width=WIDTH):
    """Within width/2 of any of the points (both sides of the car)."""
    both = np.concatenate([points, points * np.array([-1.0, 1.0, 1.0])])
    tree = cKDTree(both)

    def dist(p, n):
        d, _ = tree.query(p.astype(np.float64), workers=-1, distance_upper_bound=width)
        return width / 2 - np.minimum(d, width)
    return shapes.field(dist, 0.2)


def top_zone():
    return _band(np.concatenate([_dense(line) for line in top_lines()]))


# ---- the flank lines: even heights on the side-facing panels ----

def _flank_y(j, z):
    if j == 0:  # the upper one: under the inlet, then rising over the rear wheel arch
        return 41.0 + 14.0 * smoothstep(-55.0, -102.0, z) + _wake(z, 5, 2.4, 32.0)
    return 33.0 + _wake(z, 6, 1.6, 32.0)  # the lower one, to the arch


def flank_zone():
    def dist(p, n):
        best = np.full(len(p), -1e3, np.float32)
        z, y = p[:, 2].astype(np.float64), p[:, 1].astype(np.float64)
        for j in (0, 1):
            h = 0.05
            F = y - _flank_y(j, z)
            dF = (_flank_y(j, z + h) - _flank_y(j, z - h)) / (2 * h)
            g = np.stack([np.zeros_like(z), np.ones_like(z), -dF], 1)
            gt = g - (g * n).sum(1, keepdims=True) * n
            dist_cm = np.abs(F) / np.maximum(np.linalg.norm(gt, axis=1), 0.2)
            best = np.maximum(best, (WIDTH / 2 - dist_cm).astype(np.float32))
        return best
    # outward only: never the inside of a panel seen through an opening
    side = shapes.Zone(lambda p, n: smoothstep(0.42, 0.52, n[:, 0] * np.sign(p[:, 0])))
    return shapes.field(dist, 0.2) & side & shapes.behind(78, 0.2)


def spine_zone():
    """The red streamline: the car's middle from the nose's tip to the cockpit's front."""
    return shapes.stripe(WIDTH) & shapes.band(93, START_Z) & shapes.facing("up", 0.3, 0.05)


def blade_zone():
    """The nose fin's blade (1.2 cm thin, narrower than the line) stands on the red line: all of it red."""
    return shapes.stripe(WIDTH) & shapes.band(93, START_Z)


def design(s):
    s.clay()
    s.step("Gloss black", "The whole body in deep gloss black, like piano lacquer: the photograph's black.",
           words="sure lets try")
    s.paint("body", "wet look", colour=BLACK)

    s.step("Smoke lines", "A row of thin, even satin white smoke lines from the nose's tip over the whole "
           "car: parting round the fin and the cockpit, spreading over the sidepods, two more along each "
           "flank under the inlets, all breaking into a gentle wake behind the sidepods.", words="sure lets try")
    s.paint(LINE_PARTS, "satin", colour=SMOKE, zone=top_zone())
    s.paint(FLANK_PARTS, "satin", colour=SMOKE, zone=flank_zone())

    s.step("Red streamline", "One signal red line down the spine, from the nose's tip to the cockpit's front.",
           words="sure lets try")
    s.paint(SPINE_PARTS, "satin", colour=RED, zone=spine_zone())
    s.paint("nose fin", "satin", colour=RED, zone=blade_zone())

    s.step("Wheels and inner car", "The wheels and the inner car in one dark satin, out of the picture.",
           words="sure lets try")
    s.paint("wheels", "satin", colour=DARK)
    s.paint("inner", "satin", colour=DARK)
