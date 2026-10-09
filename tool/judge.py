"""The judge: one list of what's wrong on a painted car, measured where every graphic landed, before anyone looks
(nearly every flaw the user has pointed out was a graphic that didn't fit the car, or didn't sit where its line is;
2026-10-07: "This tool needs to be optimised, it cannot randomly make mistakes").

    python -m tool.judge <name>      paint the skin and print its verdict

`run` judges a skin painted with Skin.measure on (tool/skin.py's show): the verdict {design: the design's hash
(tool/gate.py's `design_hash`: design.py, the designs it borrows, its art), findings, seconds}, kept by show in
build/<name>/verdict.json (`save`); `words` says it for Claude, the blocks first. Each finding: {level, kind, check,
text, z, side, step}: z the stretch along the car in cm, front to back, or None; side where one side alone; the eye's
carry `at` and `nrm` too, for a close look square to the body there (tool/close.py, which adds its own findings, check
"close"). The levels (LEVELS, by kind):
  block   an accident, to fix before the car is shown as done, the tool's or the design's;
  warn    to look at close up, then fix or know why it's meant;
  note    how a graphic sits against the car's lines and the graphics round it: it names, never forbids.
The kinds are the user's kinds of flaw (KINDS). A check names an accident, never a design: a paint the design says
crosses the car's parts (`across=True`) keeps its cuts and spills unsaid, and a paint ended by a length, a height, a
box or a pattern the design wrote ends where it was written; only a reading of the car (READINGS: its open air, the way
it faces, a region) makes a shortfall.

The checks, each read off the body's texels (who painted each last, Canvas.owner; what it covered, Skin.zoned's
under; where each is on the car, the bake; its area from the map's density):
  placement  every marking along a course (a band, a strip, dashes, blocks, ticks: a zoned paint whose zone has a
             course, found inside any & and | of zones), read back station by station every STATION cm along the
             model's line it follows (the line its course lies within FOLLOW cm of over FOLLOWED of its points; else
             its own course), by its texels' distance across the surface from that line (tool/surface.py, exact):
               gap    paint expected (the zone's own `along`) and none, the skin there and bare; at an end, short;
               line   a HOP, a one-sided band on the line's other face; a STEP, an edge jumping STEP_SHARE of the
                      width between stations, or at the join of two lines it follows; a KINK, its centre turning KINK
                      degrees against the line; a WOBBLE, kinks turning each way within WOBBLE cm;
               short  its width under NARROW of the designed width where the skin beyond it is bare;
               cut    its width short where the body ends (ticks hanging off an edge), unless it follows that edge.
             Fills: a panel filled to the model's lines (meshlines.panel) or a zone's edge inked on a course
             (inked_edge): short where the painted edge sits FILL cm or more off its line.
             Marks, words and pictures (tool/marks.py, at laying, Skin.findings): cut when not whole: under WHOLE of
             the shape's area on the car (`area`, from the texels' places; kept off by its zone, fallen in a gap or
             off an edge), or chipped (the paint missing where the skin is bare).
  reach      each zoned paint with no course that runs along the car (RUN times longer than high): on each side,
             how far the bare body goes on past each end at the paint's own height (over the surface, round a
             corner, as far as the surface faces its end), SHORT cm or more; the body resuming past an opening,
             bare; and the GAPs inside its run where the body is there and less than half shows the paint. Said
             with what ends it: a zone's reading of the car, its parts, a later paint (not the same paint going
             on, nor one laid on it).
  flaws      each zoned paint's outline, followed texel to texel and across the texture's seams (`_edges`), with
             what ends it at each step: its own shape, the surface turning away, its parts, a later paint, the
             surface itself; a graphic (a mark no longer than COMPACT cm, not a line, that its own shape ends, `_marks`)
             cut for CUT cm or more by a fold, its parts' edge or the surface's end; spilled onto a second piece
             (SPILL cm²); lying across another graphic's edge, or covered by a later paint (over); a zone's edge
             soft (wider than SOFT cm; wider than BLEND it's a blend, meant); a picture with fewer than PIXELS pixels
             per cm; words over a fold (FOLD_WORDS degrees), flipped (FLIPPED) or hanging upside down (HANG); a second
             paint on, or a graphic within CLEAR cm of, the panels the game letters or the nose fin's plate (PANELS);
             a scatter spread unevenly (UNEVEN) or leaving BARE of its surface.
  the eye    how a marking, a fill or an area paint sits against the lines the eye sees (meshlines.lines: crisp
             lines, panel lines, where the body ends; not the line it lies on, nor one within ALONG cm of it) and
             against the other graphics, as notes: a gap that CLOSES, a marking's end a NEAR MISS from a line, a
             SHALLOW crossing, an edge JUST PAST a line, PART OVER a small piece's outline, TOUCHES another paint.
             The planted-flaw pair tunes what it says: whatever it names on the clean car is noise (a sliver of body
             beside a tape's far edge, a near miss along an edge, were).
"""

import functools
import hashlib
import json
import sys
import time

import numpy as np
from scipy import ndimage
from scipy.ndimage import minimum_filter1d
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

from tool import carmap, coverage, fbx, gate, paths, pieces, shapes, uvmap

# ---- the kinds and the levels ----
KINDS = {
    "short": "a paint stops before the surface it was meant to cover ends",
    "gap": "a hole inside a paint's run",
    "fold": "a picture or words over a fold or a sharp curve",
    "cut": "a shape cut off by an edge, an opening or a join, or chipped",
    "spill": "a shape running off its panel onto the next piece",
    "over": "a paint laid over, or touching, another that should stay clear",
    "clear": "paint on or round the game's own number and name panels",
    "upside down": "words upside down or mirrored",
    "line": "a line that isn't smooth or doesn't sit where it should",
    "sits": "a graphic that doesn't sit with the car's lines or the graphics round it: a gap that pinches, an end just "
            "short, a slant",
    "edge": "an edge soft, pixelated or outlined",
    "spread": "a pattern spread unevenly",
}
LEVELS = {"gap": "block", "short": "block", "line": "block", "cut": "block", "clear": "block", "upside down": "block",
          "fold": "block", "spill": "warn", "over": "warn", "edge": "warn", "spread": "warn", "sits": "note"}
READINGS = ("outside", "region", "sides", "facing")  # zones whose edges are the car's, read off its mesh: the rest
# (a length, a height, a box, a pattern) end a paint where the design wrote it
OUTER = 0.1  # the open air a spot sees not to be hidden skin: an opening's insides see about 0.01, the flanks
# behind the wheels (the wheel covers shade them) 0.2 to 0.35, the sidepods nearly all of it
SEEN = 0.4   # the open air a spot sees to be the body the eye sees from outside (shapes.outside's own default): a
# paint's reach is measured over that body, not the flank hidden behind a wheel
SAME = 0.03  # two paints this near (colour, roughness, metalness, 0..1) are one paint to the eye

# ---- placement ----
STATION = 0.5     # cm along the line a marking follows: a station each
STEP = 0.25       # cm between the points of the model's lines, and of the eye's
FOLLOW = 1.5      # cm: a course lying this near one of the model's lines follows it ...
FOLLOWED = 0.3    # ... over this share of its points or more
ON_LINE = 0.15    # cm: a course this near the model's line's points all along is the line itself (its points are STEP apart)
STEP_SHARE = 0.25  # of the marking's width: an edge jumping more than this between stations is a step ...
STEP_LEAST = 0.2  # cm ... and at least this (a texel is 0.05 to 0.09)
JOIN = 3.0        # cm: two lines a course follows in turn meet within this, so a step at their join is measured
KINK = 8.0        # degrees: the marking's centre turning this much against its line, over KINK_RUN cm each side
KINK_RUN = 2.0
WOBBLE = 12.0     # cm: kinks turning each way within this are a wobble
NARROW = 0.8      # the marking's width over its designed width, under which it's short
FILL = 0.5        # cm: a fill's edge this far off its line is off it (a panel line's groove is 0.36 wide)
TOL = 2.5         # cm beyond its designed edges that a marking's texels still count as its own (FOLLOW and a width)
END = 2           # stations left out at each end of a partial stretch of a line: the marking runs on past them
LEAST_RUN = 4.0   # cm: a shorter run along a line isn't measured
MERGE = 3.0       # cm: a marking's findings of one kind this near one another are one
ALONG = 1.0       # cm: a line this near the one a marking follows is the same line to the eye (a groove's walls)

# ---- reach ----
BIN = 0.5  # cm along the car
SHORT = 1.0  # cm: an end that stops this short of the body
GAP = 1.0  # cm: a stretch inside a run with too little of the paint showing
REACH = 40.0  # cm round an end that the body is followed
JOINED = 1.0  # cm between texels that count as joined (they're 0.1 to 0.3 cm apart): a seam joins, an opening doesn't
THIN = 0.2  # cm: the cells the joins are worked out on
EDGE = 1.5  # cm past a paint's end: the bare body whose zone parts say what ended it
FAR = 60.0  # cm past an end that the body is looked for past an opening (the rear wheel's is about 30)
OPENING = 3.0  # cm along the car with no body at a paint's height: an opening it can't follow across
ACROSS_RUN = 3.0  # cm along the car: body past an opening at a paint's height, long enough to count
RUN = 3  # a paint runs along the car when it's at least this many times longer than it's high
FACING = 0.25  # the bare body followed past an end faces within 75 degrees of the paint's end: a band
# along the side runs on round the rounded corner to where the surface faces the back
ON = 0.95  # a later paint with this share of it on a paint's zone is laid on it, a pattern: what it covers is as written

# ---- flaws ----
COMPACT = 60.0  # cm: the longest a graphic is
VOXEL = 2.5     # cm: marks nearer than this are one
CUT = 3.0       # cm of a graphic's outline
SPILL = 5.0     # cm² of a graphic on a second piece
WHOLE = 0.9     # the share of its area a laid mark must have on the car
ACROSS = 0.03   # the share of a graphic over another's paint from which it lies across its edge
CLEAR = 3.0     # cm round the panels
NEAR_PANEL = 0.10  # the share of a graphic within CLEAR cm of a panel from which it's said
SPECK = 0.3     # cm² of a graphic by a panel, or three times that of a second paint on one: less is a texel's rounding
SOFT = 2 * shapes.SOFT  # cm
BLEND = 5.0     # cm
PIXELS = 11.0   # the body's texels per cm (its texel pitch 0.089 cm at 4096², measured 2026-09-24)
FOLD_WORDS = 30.0  # degrees: the surface under words turning this much from its mean is a fold under them (the
# lettering the user rejected sat on 38)
FLIPPED = 45.0  # degrees: words laid for a surface facing this far from the one under them look flipped or sheared
HANG = -0.3     # words on a side whose top points down this much (their up's y) hang upside down
UNEVEN = 0.35   # the spread of the copies' distances to their nearest neighbour, over their mean
BARE = 0.10     # the share of a scatter's surface further than 0.75 spacings from every copy
SEAM = 1.0      # cm: the surface goes on across a seam or a panel gap no wider than this
FILL_SHARE = 0.08  # a mark's area over its length squared: under this it's a line, which may cross anything
LOOK = 200_000  # outline steps looked at per paint; a longer outline is sampled
PANELS = {"number panel": "the number panel (the game letters it)",
          "engine cover panel": "the engine cover panel (the game letters it)",
          "nose fin": "the nose fin's plate"}
NATURAL, FOLD, PART, EDGE_END, COVERED, HOLE = range(6)

# ---- the eye ----
NEAR = 5.0          # cm: a line further than this from a graphic's edge isn't its neighbour
LEAST = 8.0         # cm: shorter lines (a bolt head's ring, a lip) aren't followed
EVEN_RUN = 8.0      # cm: a gap read over this length or more ...
LEVEL = 1.5         # degrees: ... turning less than this is even, more closes or opens
FIT = 0.3           # cm: a stretch of a gap changes straight within this
CLOSE = 2.0         # cm: a gap that narrows to under this ...
SLANT = 3.0         # degrees: ... by this or more closes
LEAN = 12.0         # degrees: a crossing under this is shallow
MISS = 1.0          # cm: an edge this near a line without reaching it is a near miss ...
END_NEAR = 4.0      # cm: ... at a marking's end (within this of the course's end: a band's end is as wide as the band)
NEIGHBOUR = 0.6     # cm: texels further apart on the car than this aren't neighbours (the texture's islands)
ONE = 0.6           # cm: two lines this near are one to the eye (a groove, the gap round a piece set into the body)
PIECES = 6.0        # cm: a graphic of pieces (dashes, ticks, blocks) is read as one over gaps this long
REACH_IN = 6.0      # cm round a line where it goes into a graphic: the graphic beyond ONE cm on both sides crosses it
PAST = 3.0          # (beyond PAST on the nearer: under that its edge runs just past), on one side only its edge meets it
RING = 60.0         # cm: a closed line shorter than this is a small piece's outline (a cap, a hatch), named by what's in it
SPAN = 5.0          # cm round a crossing (a soft window, this its spread)
LONG = 2.0          # a graphic this many times longer than wide there (a tape, a ruler) crosses at the angle it runs at
NEAR_GRAPHIC = 15.0  # cm: another graphic further than this isn't a neighbour
TOUCH = 0.4         # cm: graphics this near touch (no nearer gap shows)
LAID = 0.9          # a graphic whose edge is this much against another's is laid on it (one graphic to the eye)


# ---- where things are, in words ----

def _place(z):
    stations = np.array([s for s, _ in carmap.STATIONS], float)
    k = int(np.argmin(np.abs(stations - z)))
    name = carmap.STATIONS[k][1] if abs(stations[k] - z) <= 12 else None
    return f"z {z:+.0f}" + (f" ({name})" if name else "")


def _where(p):
    """Where points are, in words, and for a finding: (words, z, side)."""
    p = np.asarray(p, np.float64).reshape(-1, 3)
    z = [round(float(p[:, 2].max()), 1), round(float(p[:, 2].min()), 1)]
    left, right = bool((p[:, 0] > 2).any()), bool((p[:, 0] < -2).any())
    side = "left" if left and not right else "right" if right and not left else None
    a, b = round(z[0]) + 0.0, round(z[1]) + 0.0  # never "z -0"
    along = _place(a) if a - b < 4 else f"{_place(a)} to {_place(b)}"
    return (f"on the {side}, " if side else "") + along, z, side


def _reading(f):
    return repr(f).lstrip("~(").split("(")[0] in READINGS


def _blend(f):
    return repr(f).lstrip("~(").split("(")[0] in ("fade", "radial")


def _runs(mask):
    """(start, end) index pairs of the runs of True."""
    d = np.diff(np.r_[0, np.asarray(mask).astype(np.int8), 0])
    return list(zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)))


# ---- the car, as the checks read it ----

def _edges(c, cm2):
    """The body texture's island edges: every covered texel with an uncovered neighbour, and the
    texel the surface goes on at across the seam (the nearest within SEAM cm that faces the same way,
    on another island, or on its own a long way round: the texels along its own edge are as near),
    or -1 where the surface ends: an opening's rim, a panel's edge. (the texels, sorted; their
    partners), kept in the work folder."""
    cache = paths.CACHE / f"edges_Skin_{c.w}x{c.h}_v2.npz"
    if cache.exists() and cache.stat().st_mtime > fbx.CACHE.stat().st_mtime:
        d = np.load(cache)
        return d["edge"], d["partner"]
    cov = c.cov
    full = np.zeros_like(cov)
    full[1:-1, 1:-1] = cov[:-2, 1:-1] & cov[2:, 1:-1] & cov[1:-1, :-2] & cov[1:-1, 2:]
    edge = np.flatnonzero((cov & ~full).reshape(-1))
    pos, nrm = c.pos[edge].astype(np.float64), c.nrm[edge]
    rows, cols = np.divmod(edge, c.w)
    island = uvmap.islands("Skin")[0][c.bake["tri"].reshape(-1)[edge]]
    along = 3 * SEAM / np.sqrt(np.median(cm2[edge]))  # texels: further than any texel SEAM cm along the same edge
    tree = cKDTree(pos)
    partner = np.full(len(edge), -1, np.int64)
    for a in range(0, len(edge), 50_000):
        sl = slice(a, a + 50_000)
        _, j = tree.query(pos[sl], k=64, distance_upper_bound=SEAM, workers=-1)
        got = j < len(edge)
        j = np.minimum(j, len(edge) - 1)
        far = (np.abs(rows[j] - rows[sl, None]) > along) | (np.abs(cols[j] - cols[sl, None]) > along)
        ok = got & (far | (island[j] != island[sl, None])) & ((nrm[j] * nrm[sl, None]).sum(2) > 0.3)
        first = ok.argmax(1)
        partner[sl] = np.where(ok.any(1), edge[j[np.arange(len(first)), first]], -1)
    cache.parent.mkdir(parents=True, exist_ok=True)
    tmp = cache.with_name(cache.stem + ".tmp.npz")
    np.savez_compressed(tmp, edge=edge, partner=partner)
    tmp.replace(cache)
    return edge, partner


class _Car:
    """What the judge reads off the body's texture, worked out once a paint."""

    def __init__(self, skin):
        self.skin = skin
        c = self.c = skin.canvases["Skin"]
        self.n = c.w * c.h
        self.cover = c.cov.reshape(-1)
        self.part = coverage.load(skin.parts, "Skin", c.w, c.h).owners().reshape(-1)
        self.names = [inst["name"] for inst in skin.parts.instances]
        tri = c.bake["tri"].reshape(-1)
        label, density, _ = uvmap.islands("Skin")
        per_cm = density[label[np.maximum(tri, 0)]] * c.w  # texels per cm
        self.cm2 = np.where((tri >= 0) & (per_cm > 0), 1.0 / np.maximum(per_cm, 1e-9) ** 2, 0).astype(np.float32)
        self.piece = np.where(tri >= 0, pieces.labels()[np.maximum(tri, 0)], -1)
        self.mark = np.zeros(self.n, bool)  # scratch: the texels of the paint being looked at
        self.edge, self.partner = _edges(c, self.cm2)
        self.lo = np.array([-110.0, -10.0, -180.0])
        self.dims = np.ceil(np.array([220.0, 120.0, 410.0]) / VOXEL).astype(int)
        self.blends = set()  # the calls whose zone is a blend: they make no edge
        self.graphics = []  # each graphic found: (its call, its texels)
        self.zoned_ops = {call["op"] for call in skin.zoned} | {p["op"] for p in skin.pictures + skin.marks}
        self.bodies = {}  # the parts a paint was aimed at -> their body (reach)
        self.paints = {}  # a call -> its paint (colour, roughness, metalness), to tell the same paint going on
        self.followed = {}  # a call -> the points of the lines its markings follow (the eye leaves them out)
        self.looks = []  # every graphic, for the close looks along and over it (tool/close.py): `graphics`

    def open(self, texels):
        return carmap.load().value("open", self.c.pos[texels], self.c.nrm[texels])

    def voxel(self, pos):
        return tuple(np.clip(((pos - self.lo) / VOXEL).astype(int), 0, self.dims - 1).T)

    def place(self, texels):
        return _where(self.c.pos[texels])

    def op(self, k):
        if k < 0:
            return "the stock paint"
        o = self.skin.ops[k]
        return f"{o['what']} ({o['step']})"

    def paint_of(self, op):
        """A call's paint as it shows: the median colour, roughness and metalness of the texels it covers last."""
        if op not in self.paints:
            c = self.c
            on = np.flatnonzero(c.owner == op)
            if not len(on):
                self.paints[op] = None
            else:
                on = on[:: max(1, len(on) // 20000)]
                self.paints[op] = np.r_[np.median(c.colour[on], 0), np.median(c.rough[on]), np.median(c.metal[on])]
        return self.paints[op]

    def same_paint(self, a, b):
        pa, pb = self.paint_of(a), self.paint_of(b)
        return pa is not None and pb is not None and float(np.abs(pa - pb).max()) <= SAME


# ---- reach: how far each zoned paint goes along the car ----

class _Body:
    """The texels of the parts a paint was aimed at, and which of them are on the outer body,
    asked only where a measure needs them (the open-air lookup is the slow part)."""

    def __init__(self, c, texels):
        pos = c.pos[texels]
        order = np.argsort(pos[:, 2], kind="stable")  # by length along the car, for windows
        self.c, self.texels, self.pos = c, texels[order], pos[order]
        self.outer = np.full(len(texels), -1, np.int8)

    def near(self, sign, z0, z1, y0, y1):
        """Indices (into texels) on a side, outer, within z0..z1 and y0..y1."""
        i0, i1 = np.searchsorted(self.pos[:, 2], [z0, z1], side="left")
        p = self.pos[i0:i1]
        k = i0 + np.flatnonzero((p[:, 0] * sign > 0) & (p[:, 1] >= y0) & (p[:, 1] <= y1))
        ask = k[self.outer[k] < 0]
        if len(ask):
            t = self.texels[ask]
            self.outer[ask] = shapes.outside(SEEN)(self.c.pos[t], self.c.nrm[t]) > 0.5
        return k[self.outer[k] == 1]


def _beyond(end_pts, bare_pts):
    """The bare texels joined to the paint's end over the surface (texel to texel, JOINED cm apart at
    most): what lies on past the end, round a corner too."""
    if not len(bare_pts) or not len(end_pts):
        return np.zeros(0, int)
    end_pts = _thin(end_pts)
    bare_cell, bare_back = np.unique(_cells(bare_pts), return_inverse=True)
    bare_one = np.zeros(len(bare_cell), int)
    bare_one[bare_back.ravel()] = np.arange(len(bare_pts))  # a texel for each cell
    pts = np.concatenate([end_pts, bare_pts[bare_one]]).astype(np.float64)
    pairs = cKDTree(pts).query_pairs(JOINED, output_type="ndarray")
    n = len(pts)
    graph = coo_matrix((np.ones(len(pairs), np.int8), (pairs[:, 0], pairs[:, 1])), shape=(n, n))
    _, label = connected_components(graph, directed=False)
    joined_cells = np.isin(label[len(end_pts):], np.unique(label[:len(end_pts)]))
    return np.flatnonzero(joined_cells[bare_back.ravel()])  # every texel in a joined cell


def _cells(pts):
    """Each point's THIN-cm cell as one number (the car fits in 2**20 cells a side)."""
    c = np.floor(pts / THIN).astype(np.int64) + (1 << 19)
    return (c[:, 0] << 40) | (c[:, 1] << 20) | c[:, 2]


def _thin(pts):
    """One point per THIN-cm cell: the texels are far denser than the joins need."""
    return pts[np.unique(_cells(pts), return_index=True)[1]]


def _why(car, call, texels, aimed):
    """What leaves these texels without the paint: (words, as_written). aimed: a flag per texel,
    the zone reached it."""
    skin, c = car.skin, car.c
    mine = aimed[texels]
    if mine.mean() >= 0.5:  # the zone reached them: a later call covers them
        owners = c.owner[texels[mine]]
        owners = owners[owners != call["op"]]
        if len(owners):
            op = int(np.bincount(owners - owners.min()).argmax() + owners.min())
            said = car.op(op)
            if car.same_paint(call["op"], op):  # the same paint goes on: nothing stops to the eye
                return f"under the same paint, {said}", True
            # a pattern laid on the paint (checks on a band, stripes on a tape) lies wholly within it
            on = [z for z in skin.zoned if z["op"] == op]
            if on and len(on[0]["idx"]) and aimed[on[0]["idx"]].mean() >= ON:
                return f"under {said}, laid on it", True
            return f"covered by {said}", False
        return "covered", False
    pos, nrm = c.pos[texels], c.nrm[texels]
    out = [f for f in call["zone"].parts() if (f(pos, nrm) < 0.5).mean() >= 0.5]
    if not out:
        return "left out by the zone as a whole", False
    written = not any(_reading(f) for f in out)
    return ("ends where " if written else "left out by ") + " & ".join(map(repr, out)), written


def _reach_side(car, call, body, shown, showing, aimed, sign):
    """One side's run, ends and gaps. showing: a flag per texel, the paint shows there; aimed: the
    zone reached it."""
    c = car.c
    p = c.pos[shown]
    keep = p[:, 0] * sign > 0
    shown, p = shown[keep], p[keep]
    if len(shown) < 30:
        return None
    z, y = p[:, 2], p[:, 1]
    out = {"front": float(z.max()), "rear": float(z.min()), "ends": {}, "gaps": []}
    # the paint's height along the run, a bin at a time, filled across the bins it misses
    zb = np.floor(z / BIN).astype(int)
    b0, b1 = int(zb.min()), int(zb.max())
    order = np.argsort(zb, kind="stable")
    bins, starts = np.unique(zb[order], return_index=True)
    lo_b = np.minimum.reduceat(y[order], starts)
    hi_b = np.maximum.reduceat(y[order], starts)
    # each end, in up to three slices of the paint's usual height: a band's lower edge can stop
    # before its upper one
    lo_y, hi_y = float(np.median(lo_b)), float(np.median(hi_b))
    if out["front"] - out["rear"] < RUN * (hi_y - lo_y):
        return out  # a patch, not a run along the car: its extent says it all
    cuts = np.linspace(lo_y, hi_y, 2 if hi_y - lo_y < 1.5 else 4)
    for end, d in (("front", 1), ("rear", -1)):
        worst = {"short": 0.0, "body": out[end]}
        for a, b in zip(cuts[:-1], cuts[1:]):
            slice_ = (y >= a) & (y <= b)
            if slice_.sum() < 10:
                continue
            zend = float(z[slice_].max() if d > 0 else z[slice_].min())
            tip = slice_ & (np.abs(z - zend) <= 1.5)
            k = body.near(sign, zend - REACH, zend + REACH, a, b)
            k = k[~showing[body.texels[k]]]
            facing = c.nrm[shown[tip]].mean(0)
            facing /= max(float(np.linalg.norm(facing)), 1e-6)
            k = k[c.nrm[body.texels[k]] @ facing >= FACING]  # the side, not the back it turns into
            joined = _beyond(p[tip], body.pos[k])
            along = (body.pos[k[joined], 2] - zend) * d  # how far on along the car
            if len(along) and along.max() > worst["short"]:
                # what ends the paint is what leaves out the bare texels right at its edge
                gap, _ = cKDTree(p[tip]).query(body.pos[k[joined]], distance_upper_bound=EDGE * 2, workers=-1)
                edge = joined[gap <= EDGE] if (gap <= EDGE).any() else joined
                worst = {"short": float(along.max()), "body": zend + d * float(along.max()), "height": [a, b],
                         "edge": k[edge], "across": worst.get("across")}
            # the body at the paint's height resuming past an opening (the rear wheel's), bare: past
            # the end, OPENING cm or more with none of it, then ACROSS_RUN cm or more of it
            far = body.near(sign, zend - FAR, zend + FAR, a, b)
            far = far[~showing[body.texels[far]]]
            far = far[c.nrm[body.texels[far]] @ facing >= FACING]
            on = (body.pos[far, 2] - zend) * d
            far, on = far[on > 0], on[on > 0]
            has = np.bincount(np.floor(on / BIN).astype(int)) >= 4 if len(on) else np.zeros(0, bool)
            runs = np.flatnonzero(np.diff(np.concatenate([[0], has.astype(int), [0]])))  # starts, ends of runs
            for r0, r1 in zip(runs[::2], runs[1::2]):
                if r0 * BIN < OPENING or r0 > 0 and has[:r0].any() and (r0 - np.flatnonzero(has[:r0])[-1] - 1) * BIN < OPENING:
                    continue  # no opening before it: joined to the end, or a speck
                long = (r1 - r0) * BIN
                if long >= ACROSS_RUN and long > (worst.get("across") or {}).get("long", 0):
                    inside = (on >= r0 * BIN) & (on < r1 * BIN)
                    worst["across"] = {"from": zend + d * r0 * BIN, "to": zend + d * r1 * BIN, "long": long,
                                       "height": [a, b], "texels": far[inside]}
                break
        if worst["short"] >= SHORT:
            worst["why"], worst["as_written"] = _why(car, call, body.texels[worst["edge"]], aimed)
        worst.pop("edge", None)
        if worst.get("across"):
            x = worst["across"]
            x["why"], x["as_written"] = _why(car, call, body.texels[x.pop("texels")], aimed)
        else:
            worst.pop("across", None)
        out["ends"][end] = worst
    # the gaps
    every = np.arange(b0, b1 + 1)
    lo = np.interp(every, bins, lo_b)
    hi = np.interp(every, bins, hi_b)
    pad = (hi - lo) * 0.1
    lo, hi = lo + pad, hi - pad
    k = body.near(sign, b0 * BIN, (b1 + 1) * BIN, float(lo.min()), float(hi.max()))
    bp = body.pos[k]
    kb = np.clip(np.floor(bp[:, 2] / BIN).astype(int) - b0, 0, len(every) - 1)
    inside = (bp[:, 1] >= lo[kb]) & (bp[:, 1] <= hi[kb])
    k, kb = k[inside], kb[inside]
    there = np.bincount(kb, minlength=len(every))
    on = showing[body.texels[k]]
    seen = np.bincount(kb[on], minlength=len(every))
    gap = (there >= 4) & (seen < 0.5 * there)
    edges = np.flatnonzero(np.diff(np.concatenate([[0], gap.astype(int), [0]])))
    for g0, g1 in zip(edges[::2], edges[1::2]):
        if (g1 - g0) * BIN < GAP:
            continue
        hole = k[(kb >= g0) & (kb < g1) & ~on]
        why, written = _why(car, call, body.texels[hole], aimed)
        out["gaps"].append({"from": (b0 + g1) * BIN, "to": (b0 + g0) * BIN, "why": why, "as_written": written})
    return out


def _reach(car, call, found):
    """A zoned paint's findings along the car: an end that stops short, the body bare past an opening, a gap."""
    skin, c = car.skin, car.c
    key = tuple(call["ids"])
    if key not in car.bodies:
        cov = coverage.load(skin.parts, "Skin", c.w, c.h)
        car.bodies[key] = _Body(c, np.flatnonzero(cov.share(call["ids"]).reshape(-1) > 0.5))
    idx = call["idx"]
    shown = idx[c.owner[idx] == call["op"]]
    showing = np.zeros(c.w * c.h, bool)
    showing[shown] = True
    aimed = np.zeros(c.w * c.h, bool)
    aimed[idx] = True
    name = car.op(call["op"])
    for side, sign in (("left", 1), ("right", -1)):
        r = _reach_side(car, call, car.bodies[key], shown, showing, aimed, sign)
        if not r:
            continue
        said = {"check": "reach", "side": side, "step": call["step"]}
        for end, e in r["ends"].items():
            x = e.get("across")
            if x and not x["as_written"]:
                up = f"{x['height'][0]:.0f} to {x['height'][1]:.0f} cm up"
                found.append({**said, "kind": "short", "z": [x["from"], x["to"]],
                              "text": f"{name}: its {end} end stops short past an opening: at {up} the body goes on, bare, "
                                      f"from {_place(x['from'])} to {_place(x['to'])}; {x['why']}"})
            if e["short"] >= SHORT and not e["as_written"]:
                at = f"{e['height'][0]:.0f} to {e['height'][1]:.0f} cm up"
                much = f"{e['short']:.0f} cm" if e["short"] < REACH - BIN else f"{REACH:.0f} cm or more"
                found.append({**said, "kind": "short", "z": [r[end], e["body"]],
                              "text": f"{name}: its {end} end stops {much} short: at {at} the bare body goes on to "
                                      f"{_place(e['body'])}; {e['why']}"})
        found += [{**said, "kind": "gap", "z": [g["from"], g["to"]],
                   "text": f"{name}: a gap of {g['from'] - g['to']:.0f} cm from {_place(g['from'])} to {_place(g['to'])}: {g['why']}"}
                  for g in r["gaps"] if not g["as_written"]]


# ---- flaws: each zoned paint's outline and graphics ----

def _inverse_smoothstep(w):
    """x in 0..1 for w = 3x² - 2x³ (tool/noise.py's smoothstep): a zone's weight linearised back to
    where it sits across its feather."""
    return 0.5 - np.sin(np.arcsin(np.clip(1 - 2 * w, -1, 1)) / 3)


def _feather(car, factors, B):
    """How wide a zone's own edge is at texels B, in cm: the zone's weight (its factors' product) over
    each texel's four neighbours on the texture, linearised through the feather's own curve, gives how
    fast it changes per cm across the texture whichever way the edge runs (a step across a slanted
    edge alone reads it twice too wide); the feather is one over that."""
    c = car.c
    pitch = np.sqrt(np.maximum(car.cm2[B], 1e-6))
    pts = np.clip(np.stack([B, B - 1, B + 1, B - c.w, B + c.w]), 0, car.n - 1)
    flat = pts.reshape(-1)
    w = np.ones(len(flat), np.float32)
    for f in factors:
        w *= f(c.pos[flat], c.nrm[flat])
    x = _inverse_smoothstep(w).reshape(5, -1)
    near = car.cover[pts] & (np.linalg.norm(c.pos[pts] - c.pos[pts[0]][None], axis=2) <= 3 * pitch)
    grad2 = np.zeros(len(B))
    for lo, hi in ((1, 2), (3, 4)):
        d = np.maximum(np.where(near[lo], np.abs(x[0] - x[lo]), 0), np.where(near[hi], np.abs(x[hi] - x[0]), 0))
        grad2 += (d / pitch) ** 2
    return 1 / np.sqrt(np.maximum(grad2, 1e-4))


def _outline(car, call, shown):
    """A zoned paint's outline, a step for each texel edge between a texel showing it and one that
    doesn't (across the texture's seams too): the texel inside (b), what ends the paint there
    (kind; detail: the zone's factor, the part beyond, the later call), how wide the zone's own edge
    is there (feather, cm; nan where it isn't the zone's) and the step's length (cm)."""
    c, mark = car.c, car.mark
    S = shown[car.cover[shown]]
    factors = call["zone"].parts()
    reading = np.array([_reading(f) for f in factors])
    mark[S] = True
    try:
        bs, ts, ends = [], [], []
        for d in (1, -1, c.w, -c.w):
            n = S + d
            ok = (n >= 0) & (n < car.n)
            n = np.where(ok, n, S)
            out = ok & ~mark[n]
            b, n = S[out], n[out]
            cov = car.cover[n]
            bs.append(b[cov])
            ts.append(n[cov])
            e = np.unique(b[~cov])  # at an island's edge: the surface goes on across a seam, or ends
            k = np.minimum(np.searchsorted(car.edge, e), len(car.edge) - 1)
            p = np.where(car.edge[k] == e, car.partner[k], -1)
            on = (p >= 0) & ~mark[np.maximum(p, 0)]
            bs.append(e[on])
            ts.append(p[on])
            ends.append(e[p < 0])
    finally:
        mark[S] = False
    b, t = np.concatenate(bs), np.concatenate(ts)
    e = np.unique(np.concatenate(ends))
    scale = 1.0
    if len(b) + len(e) > LOOK:
        rng = np.random.default_rng(0)
        scale = (len(b) + len(e)) / LOOK
        b, t = (x[rng.choice(len(b), int(len(b) / scale), replace=False)] for x in (b, t)) if len(b) else (b, t)
        e = e[rng.choice(len(e), int(len(e) / scale), replace=False)] if len(e) else e
    every = np.concatenate([t, b, e])
    vals = np.stack([f(c.pos[every], c.nrm[every]) for f in factors]) if len(every) else np.zeros((len(factors), 0), np.float32)
    vt, ve = vals[:, :len(t)], vals[:, len(t) + len(b):]
    written_low = (vt[~reading] < 0.5).any(0) if (~reading).any() else np.zeros(len(t), bool)
    reading_low = (vt[reading] < 0.5).any(0) if reading.any() else np.zeros(len(t), bool)
    aimed = np.zeros(len(car.names) + 1, bool)  # the last slot: no part
    aimed[list(call["ids"])] = True
    in_ids = aimed[car.part[t]]
    kind = np.full(len(t), HOLE)
    detail = np.full(len(t), -1)
    lowest = np.where(reading[:, None], np.inf, vt).argmin(0) if (~reading).any() else np.zeros(len(t), int)
    turned = np.where(reading[:, None], vt, np.inf).argmin(0) if reading.any() else np.zeros(len(t), int)
    later = c.owner[t] > call["op"]
    for code, where, what in ((COVERED, ~written_low & ~reading_low & in_ids & later, c.owner[t]),
                              (PART, ~written_low & ~reading_low & ~in_ids, car.part[t]),
                              (FOLD, ~written_low & reading_low, turned), (NATURAL, written_low, lowest)):
        kind[where], detail[where] = code, what[where]
    feather = np.full(len(t), np.nan)
    own = (kind == NATURAL) | (kind == FOLD)
    if own.any():
        feather[own] = _feather(car, factors, b[own])
    # where the surface ends: cut there if the zone's own shape is still whole (well inside its edge)
    whole = (ve[~reading] >= 0.999).all(0) if (~reading).any() else np.ones(len(e), bool)
    return {"b": np.concatenate([b, e]), "kind": np.concatenate([kind, np.where(whole, EDGE_END, NATURAL)]),
            "detail": np.concatenate([detail, np.full(len(e), -1)]),
            "feather": np.concatenate([feather, np.full(len(e), np.nan)]),
            "length": np.sqrt(car.cm2[np.concatenate([b, e])]) * 0.8 * scale}  # 0.8: steps go round a curve by its corners


# the directions a mark's shape is followed in from its middle: to each neighbour of a cube's cell
RAYS = np.array([(x, y, z) for x in (-1, 0, 1) for y in (-1, 0, 1) for z in (-1, 0, 1) if (x, y, z) != (0, 0, 0)], np.float64)
RAYS /= np.linalg.norm(RAYS, axis=1, keepdims=True)
FAR_OUT = np.arange(COMPACT, 2 * COMPACT + 1, 5.0)  # cm from a mark's middle: past any graphic's end


def _marks(car, call, shown):
    """A zoned paint's separate marks (its texels joined within VOXEL cm): for each of `shown`'s texels
    the mark it's in, and which marks are graphics: no longer than COMPACT cm, not a line (FILL_SHARE), and
    ended by the zone's own shape: from the mark's middle, its written factors are out from COMPACT cm on in every
    direction, or in all but one line's (a spot drawn through the car from above runs on up and
    down). A band runs on along itself, a pattern comes back, an area's zone has no end of its own."""
    c = car.c
    grid = np.zeros(car.dims, bool)
    at = car.voxel(c.pos[shown])
    grid[at] = True
    lab, n = ndimage.label(grid, structure=np.ones((3, 3, 3), bool))
    mark = lab[at]
    graphic = np.zeros(n + 1, bool)
    written = [f for f in call["zone"].parts() if not _reading(f)]
    longest = np.array([0.0] + [max(s.stop - s.start for s in box) * VOXEL for box in ndimage.find_objects(lab)])
    area = np.bincount(mark, weights=car.cm2[shown], minlength=n + 1)
    small = np.flatnonzero((longest > 0) & (longest <= COMPACT) & (area >= FILL_SHARE * longest ** 2))
    if not written or not len(small):
        return mark, graphic
    # each small mark's middle: its texel nearest the mean of them
    count = np.maximum(np.bincount(mark, minlength=n + 1), 1)
    mean = np.stack([np.bincount(mark, weights=c.pos[shown, k], minlength=n + 1) / count for k in range(3)], 1)
    off = np.linalg.norm(c.pos[shown] - mean[mark], axis=1)
    order = np.lexsort((off, mark))
    first = order[np.unique(mark[order], return_index=True)[1]]  # one texel per mark, in the marks' order
    middle = shown[first[np.searchsorted(mark[first], small)]]
    pts = (c.pos[middle][:, None, None, :] + FAR_OUT[None, None, :, None] * RAYS[None, :, None, :]).reshape(-1, 3).astype(np.float32)
    nrm = np.repeat(c.nrm[middle], len(RAYS) * len(FAR_OUT), axis=0)
    inside = np.ones(len(pts), bool)
    for f in written:
        inside &= f(pts, nrm) > 0.5
    on = inside.reshape(len(small), len(RAYS), len(FAR_OUT)).any(2)  # the shape runs on that way
    for k, runs in zip(small, on):
        d = RAYS[runs]
        graphic[k] = not len(d) or bool((np.abs(d @ d[0]) > 0.99).all())
    # one shape in several marks (a spot drawn from above, on a panel and on what lies under it): the
    # zone's shape holds all the way from one's middle to the other's
    keep = graphic[small]
    ids, mids = small[keep], c.pos[middle[keep]].astype(np.float64)
    pairs = cKDTree(mids).query_pairs(COMPACT, output_type="ndarray") if len(ids) > 1 else np.zeros((0, 2), int)
    if len(pairs):
        t = np.linspace(0, 1, 11)[1:-1]
        a, b = mids[pairs[:, 0]], mids[pairs[:, 1]]
        seg = (a[:, None, :] + t[None, :, None] * (b - a)[:, None, :]).reshape(-1, 3).astype(np.float32)
        nrm = np.repeat(c.nrm[middle[keep]][pairs[:, 0]], len(t), axis=0)
        inside = np.ones(len(seg), bool)
        for f in written:
            inside &= f(seg, nrm) > 0.5
        one = pairs[inside.reshape(len(pairs), len(t)).all(1)]
        group = connected_components(coo_matrix((np.ones(len(one)), (one[:, 0], one[:, 1])), shape=(len(ids), len(ids))),
                                     directed=False)[1]
        same = np.arange(n + 1)
        same[ids] = ids[np.unique(group, return_index=True)[1]][group]  # each group takes its first mark's number
        mark = same[mark]
    return mark, graphic


def _lengths(o, sel):
    return float(o["length"][sel].sum())


def _zoned(car, call, found, marking):
    """One zoned paint's findings: its edge, and each of its graphics' cuts, spills and overlaps (a marking along a
    course is measured by the placement check instead: its texels are one graphic). (True when the paint is graphics
    and next to nothing else, its outline)."""
    c = car.c
    idx = call["idx"]
    still = c.owner[idx] == call["op"]
    shown = idx[still]
    if len(shown) < 20:
        return False, None
    name = car.op(call["op"])
    o = _outline(car, call, shown)
    # the edge: soft, or a blend
    own = np.isfinite(o["feather"])
    if own.any():
        order = np.argsort(o["feather"][own])
        cum = np.cumsum(o["length"][own][order])
        median = float(o["feather"][own][order][np.searchsorted(cum, cum[-1] / 2)])
        if median >= BLEND or any(_blend(f) for f in call["zone"].parts()):
            car.blends.add(call["op"])
            return False, o
        soft = own & (o["feather"] > SOFT)
        if _lengths(o, soft) >= 10 and _lengths(o, soft) >= 0.25 * cum[-1]:
            f = call["zone"].parts()
            k = np.bincount(o["detail"][soft], minlength=len(f)).argmax()
            wide = float(np.median(o["feather"][soft]))
            where, z, side = car.place(o["b"][soft])
            found.append({"check": "edge", "kind": "edge", "z": z, "side": side, "step": call["step"],
                          "text": f"{name}: {_lengths(o, soft):.0f} cm of its edge is soft, about {wide:.1f} cm wide "
                                  f"(a crisp edge is {shapes.SOFT} cm), where {f[k]!r} ends it, {where}"})
    elif any(_blend(f) for f in call["zone"].parts()):
        car.blends.add(call["op"])
        return False, o
    if marking:
        car.graphics.append((call["op"], shown))
        return False, o
    mark, graphic = _marks(car, call, shown)
    if not graphic[mark].any():
        return False, o
    at = mark[np.searchsorted(shown, o["b"])] if len(o["b"]) else np.zeros(0, int)
    under = call["under"][still]
    cuts, covers, across = {}, {}, {}
    for k in np.flatnonzero(graphic):
        S = shown[mark == k]
        if not len(S):
            continue
        car.graphics.append((call["op"], S))
        if call["across"]:  # the design's own crossing: nothing to say
            continue
        mine = at == k
        # cut: by a fold, by the edge of its parts, by the surface's end
        hard = {}
        for code in (FOLD, PART, EDGE_END):
            sel = mine & (o["kind"] == code)
            for d in np.unique(o["detail"][sel]):
                hard[(code, int(d))] = sel & (o["detail"] == d)
        if sum(_lengths(o, sel) for sel in hard.values()) >= CUT:
            cuts[k] = {key: sel for key, sel in hard.items() if _lengths(o, sel) >= 0.5}
        # over: a later paint covers part of it
        sel = mine & (o["kind"] == COVERED)
        for d in np.unique(o["detail"][sel]):
            if _lengths(o, sel & (o["detail"] == d)) >= CUT:
                covers.setdefault(int(d), []).append(sel & (o["detail"] == d))
        _spill(car, name, call["step"], S, found)
        _across(car, call["op"], S, under[mark == k], across)

    def why(code, d):
        return {FOLD: lambda: f"the surface turns away ({call['zone'].parts()[d]!r})",
                PART: lambda: f"its parts end and its shape goes on, onto the {car.names[d] if d >= 0 else 'next part'}",
                EDGE_END: lambda: "the surface ends (an opening's rim or a panel's edge)"}[code]()
    if len(cuts) > 4:  # dots, a row of marks: said together, by what cuts them
        by = {}
        for hard in cuts.values():
            for key, sel in hard.items():
                by[key] = by.get(key, False) | sel
        cuts = {None: by}
    for k, hard in cuts.items():
        sel = np.logical_or.reduce(list(hard.values()))
        said = "; ".join(f"{_lengths(o, x):.0f} cm where {why(*key)}" for key, x in sorted(hard.items(), key=lambda kv: -_lengths(o, kv[1])))
        where, z, side = car.place(o["b"][sel])
        found.append({"check": "cut", "kind": "cut", "z": z, "side": side, "step": call["step"],
                      "text": f"{name}: {'several of its marks are ' if k is None else ''}cut along its outline: {said}, {where}"})
    for d, sels in sorted(covers.items()):
        if _sits_on(car, d, call["op"]):
            continue
        sel = np.logical_or.reduce(sels)
        where, z, side = car.place(o["b"][sel])
        found.append({"check": "over", "kind": "over", "z": z, "side": side, "step": car.skin.ops[d]["step"],
                      "text": f"{car.op(d)} covers part of {name}: {_lengths(o, sel):.0f} cm of its outline, {where}"})
    _say_across(car, name, call["step"], across, found)
    return bool(car.cm2[shown[graphic[mark]]].sum() >= 0.95 * car.cm2[shown].sum()), o


def _spill(car, name, step, S, found):
    """A graphic on two of the body's pieces."""
    on = np.bincount(car.piece[S] + 1, weights=car.cm2[S])
    big = np.flatnonzero(on >= max(SPILL, 0.01 * on.sum())) - 1
    if len(big) < 2:
        return
    parts = []
    for p in big:
        t = S[car.piece[S] == p]
        names, counts = np.unique(car.part[t], return_counts=True)
        parts.append(f"{car.cm2[t].sum():.0f} cm² on the {car.names[names[counts.argmax()]]}")
    where, z, side = car.place(S)
    found.append({"check": "spill", "kind": "spill", "z": z, "side": side, "step": step,
                  "text": f"{name}: lies on {len(big)} separate pieces of the body ({', '.join(parts)}), {where}"})


def _across(car, op, S, under, across):
    """A graphic's texels by the call each showed before: over two paints, one of them a zoned paint's
    or a picture's, it lies across an edge: that one's, or the smaller's when both are."""
    keep = under != op  # a word's fill on its own outline
    S, under = S[keep], under[keep]
    if not len(S):
        return
    area = np.bincount(under + 1, weights=car.cm2[S])
    whole = area.sum()
    big = np.flatnonzero((area >= ACROSS * whole) & (area >= 2.0)) - 1
    edged = [int(d) for d in big if d in car.zoned_ops and d not in car.blends]
    if len(big) < 2 or not edged:
        return
    most = int(big[area[big + 1].argmax()])
    for d in [d for d in edged if d != most] or edged:
        across.setdefault(d, []).append((S[under == d], area[d + 1] / whole))


def _say_across(car, name, step, across, found):
    for d, hits in sorted(across.items()):
        t = np.concatenate([h[0] for h in hits])
        where, z, side = car.place(t)
        share = max(h[1] for h in hits)
        found.append({"check": "over", "kind": "over", "z": z, "side": side, "step": step,
                      "text": f"{name} lies across the edge of {car.op(d)}: {share:.0%} of it over that paint, {where}"})


def _sits_on(car, later, op):
    """A later call's paint lies wholly on a call's: a mark painted on a badge, not across its edge."""
    for call in car.skin.zoned + car.skin.pictures + car.skin.marks:
        if call["op"] == later and len(call["under"]):
            return float((call["under"] == op).mean()) >= 1 - ACROSS
    return False


def _pictures(car, found):
    """Each picture or mark pressed onto the body over every edge (across=True): pixelated; words bent or flipped;
    and, as it says it crosses edges on purpose, nothing of its pieces or what it lies across."""
    c = car.c
    by_op = {}
    for p in car.skin.pictures:
        by_op.setdefault(p["op"], []).append(p)
    for op, laid in by_op.items():
        name, step = car.op(op), laid[0]["step"]
        idx = np.concatenate([p["idx"] for p in laid])
        under = np.concatenate([p["under"] for p in laid])
        idx, first = np.unique(idx, return_index=True)
        under = under[first]
        still = c.owner[idx] == op
        S, under = idx[still], under[still]
        if len(S) < 20:
            continue
        car.graphics.append((op, S))
        if laid[0].get("kind", "picture") != "shape":
            _pixelated(car, name, step, S, min(p["pixels"] for p in laid), found)
        for p in laid:
            if p.get("kind") in ("words", "placard"):
                mine = np.isin(p["idx"], S)
                if mine.sum() >= 20:
                    _upright(car, name, step, p, p["idx"][mine], found)
        if any(p.get("across") for p in laid):
            continue
        _spill(car, name, step, S, found)
        across = {}
        _across(car, op, S, under, across)
        _say_across(car, name, step, across, found)


def _pixelated(car, name, step, S, pixels, found):
    if pixels < PIXELS:
        where, z, side = car.place(S)
        found.append({"check": "edge", "kind": "edge", "z": z, "side": side, "step": step,
                      "text": f"{name}: {pixels:.0f} of the picture's pixels per cm on the car, fewer than the car's own "
                              f"{PIXELS:.0f}: it will show its pixels, {where}"})


def _upright(car, name, step, mark, S, found):
    """Words or a placard laid flat on the body: the surface under them turning (a fold), facing
    elsewhere than they were laid for (flipped or sheared), or their top pointing down on a side
    (hanging). Read off the texels' own normals; the frame is the one they were laid in."""
    c = car.c
    nrm = c.nrm[S].astype(np.float64)
    mean = nrm.mean(0)
    mean /= np.linalg.norm(mean)
    turn = float(np.percentile(np.degrees(np.arccos(np.clip(nrm @ mean, -1, 1))), 99))
    where, z, side = car.place(S)
    if turn > FOLD_WORDS:
        found.append({"check": "fold", "kind": "fold", "z": z, "side": side, "step": step,
                      "text": f"{name}: the surface under it turns {turn:.0f}° away from flat: it will look bent, {where}"})
    right, up, facing = (np.asarray(v, np.float64) for v in mark["frame"])
    off = float(np.degrees(np.arccos(np.clip(mean @ facing / np.linalg.norm(facing), -1, 1))))
    if off > FLIPPED:
        found.append({"check": "upside down", "kind": "upside down", "z": z, "side": side, "step": step,
                      "text": f"{name}: laid as if the surface faced one way, but under it the surface faces {off:.0f}° away: "
                              f"it will look flipped or sheared, {where}"})
    elif abs(mean[1]) < 0.7 and up[1] < HANG:
        found.append({"check": "upside down", "kind": "upside down", "z": z, "side": side, "step": step,
                      "text": f"{name}: its top points down: it hangs upside down, {where}"})


def area(c, texels):
    """The area of texels on the car, in cm²: each one's from the texels either side of it, along its
    row and its column."""
    pos, cover = c.bake["position"].reshape(-1, 3), c.cov.reshape(-1)
    out = np.zeros(len(texels))
    ok = np.ones(len(texels), bool)
    steps = []
    for d in (1, c.w):
        a, b = np.clip(texels - d, 0, len(cover) - 1), np.clip(texels + d, 0, len(cover) - 1)
        ok &= cover[a] & cover[b]
        steps.append((pos[b].astype(np.float64) - pos[a]) / 2)
    out[ok] = np.linalg.norm(np.cross(steps[0][ok], steps[1][ok]), axis=1)
    ok &= out <= 4 * np.median(out[ok]) if ok.any() else ok  # not a step across a seam to another flat piece
    return float(out[ok].sum() * len(texels) / max(int(ok.sum()), 1))


def _laid(car, found):
    """Each mark laid on a panel (a shape, words, a placard, a picture): on one piece, clear of
    another graphic's edge; a picture sharp enough; words flat and the right way up (_upright). Whether it's whole
    was measured as it was laid (tool/marks.py: Skin.findings)."""
    c = car.c
    for mark in car.skin.marks:
        name, step = car.op(mark["op"]), mark["step"]
        still = c.owner[mark["idx"]] == mark["op"]
        S, under = mark["idx"][still], mark["under"][still]
        if len(S) < 20:
            continue
        car.graphics.append((mark["op"], S))
        kind = mark.get("kind", "shape")
        if kind != "shape":
            _pixelated(car, name, step, S, mark["pixels"], found)
        if kind in ("words", "placard"):
            _upright(car, name, step, mark, S, found)
        _spill(car, name, step, S, found)
        across = {}
        _across(car, mark["op"], S, under, across)
        _say_across(car, name, step, across, found)


def _panels(car):
    """Each of PANELS on the body texture: its own texels, and those within CLEAR cm of it on its face
    of the body (not what lies under it). Kept in the work folder."""
    c = car.c
    cache = paths.CACHE / f"panels_Skin_{c.w}x{c.h}_v1.npz"
    if cache.exists() and cache.stat().st_mtime > max(fbx.CACHE.stat().st_mtime, coverage.load(car.skin.parts, "Skin", c.w, c.h).folder.stat().st_mtime):
        d = np.load(cache)
        return {part: (d[f"{part} on"], d[f"{part} near"]) for part in PANELS if f"{part} on" in d.files}
    out = {}
    for part in PANELS:
        ids = [i for i, n in enumerate(car.names) if n == part]
        panel = np.flatnonzero(np.isin(car.part, ids) & car.cover)
        if not len(panel):
            continue
        p = c.pos[panel]
        lo, hi = p.min(0) - CLEAR, p.max(0) + CLEAR
        box = np.flatnonzero(((c.pos >= lo) & (c.pos <= hi)).all(1) & car.cover)
        thin = p[np.unique(np.floor(p / 0.3).astype(np.int64), axis=0, return_index=True)[1]]
        near = box[cKDTree(thin).query(c.pos[box], distance_upper_bound=CLEAR, workers=-1)[0] <= CLEAR]
        facing = c.nrm[panel].mean(0)
        out[part] = (panel, near[c.nrm[near] @ (facing / np.linalg.norm(facing)) > 0.3])
    cache.parent.mkdir(parents=True, exist_ok=True)
    tmp = cache.with_name(cache.stem + ".tmp.npz")
    np.savez_compressed(tmp, **{f"{part} {k}": v for part, pair in out.items() for k, v in zip(("on", "near"), pair)})
    tmp.replace(cache)
    return out


def _clear(car, found):
    """The panels the game letters, and the nose fin's plate: a second paint on one, or a graphic with
    NEAR_PANEL of itself on or within CLEAR cm of one."""
    c = car.c
    for part, (panel, near) in _panels(car).items():
        words = PANELS[part]
        hits = {}  # call -> its texels by the panel
        owner = c.owner[panel]
        area = np.bincount(owner + 1, weights=car.cm2[panel])
        under = int(area.argmax()) - 1
        for d in np.flatnonzero(area >= 3 * SPECK) - 1:
            if d != under and d not in car.blends:
                hits[int(d)] = [panel[owner == d]]
        car.mark[near] = True
        try:
            for op, S in car.graphics:
                by = S[car.mark[S]]
                if op != under and car.cm2[by].sum() >= max(NEAR_PANEL * car.cm2[S].sum(), SPECK):
                    hits.setdefault(op, []).append(by)
        finally:
            car.mark[near] = False
        for d, sets in sorted(hits.items()):
            t = np.unique(np.concatenate(sets))
            t = t[car.open(t) >= OUTER]
            if car.cm2[t].sum() < SPECK:
                continue
            on = float(car.cm2[t[np.isin(t, panel)]].sum())
            where, z, side = car.place(t)
            how = f"{on:.0f} cm² on" if on >= 3 * SPECK else f"{car.cm2[t].sum():.0f} cm² within {CLEAR:g} cm of"
            found.append({"check": "clear", "kind": "clear", "z": z, "side": side, "step": car.skin.ops[d]["step"],
                          "text": f"{car.op(d)}: {how} {words}, {where}"})


def _scattered(car, found):
    for s in car.skin.scattered:
        name = car.op(s["op"])
        if s["uneven"] > UNEVEN:
            found.append({"check": "spread", "kind": "spread", "z": None, "side": None, "step": car.skin.ops[s["op"]]["step"],
                          "text": f"{name}: the copies lie unevenly: their distances to the nearest copy vary by "
                                  f"{s['uneven']:.0%} of the mean (even is under {UNEVEN:.0%})"})
        if s["bare"] > BARE:
            found.append({"check": "spread", "kind": "spread", "z": s["z"], "side": None, "step": car.skin.ops[s["op"]]["step"],
                          "text": f"{name}: {s['bare']:.0%} of its surface is further than {0.75 * s['spacing']:.0f} cm from "
                                  f"any copy: bare patches, from {_place(s['z'][0])} to {_place(s['z'][1])}"})


# ---- placement: markings along the car's lines ----

def _pieces(zone, seen=None):
    """The markings laid along a course inside a zone, through any & and | of zones: each with its course, lo, hi
    and along (tool/course.py's _zone)."""
    seen = set() if seen is None else seen
    if id(zone) in seen:
        return []
    seen.add(id(zone))
    if getattr(zone, "pieces", None):
        return [p for z in zone.pieces for p in _pieces(z, seen)]
    if getattr(zone, "along", None) is not None:
        return [zone]
    out = []
    for f in list(zone.factors or []) + list(getattr(zone, "either", ())):
        out += _pieces(f, seen)
    return out


def _fill_lines(zone, seen=None):
    """The fills inside a zone: each zone with lines (meshlines.panel) or an edge inked on a course (inked_edge):
    [(zone, its lines' points, what they are)]."""
    seen = set() if seen is None else seen
    if id(zone) in seen:
        return []
    seen.add(id(zone))
    if getattr(zone, "lines", None) is not None:
        return [(zone, np.asarray(zone.lines, np.float64), "its lines")]
    if getattr(zone, "inked", False):
        return [(zone, zone.course.pts, zone.course.name)]
    out = []
    for f in list(zone.factors or []) + list(getattr(zone, "either", ())):
        out += _fill_lines(f, seen)
    return out


@functools.lru_cache(maxsize=1)
def _model():
    """The model's lines a marking can follow (crisp lines, panel lines, where the body ends, seams, the lines along
    its rounded edges), every STEP cm: points, which line each is on, the lines, and a tree of the points."""
    from tool import meshlines
    kept = [L for L in meshlines.lines("Skin") + meshlines.strips("Skin") if L["length"] >= 3.0]
    pts, ids = [], []
    for k, L in enumerate(kept):
        P = np.vstack([L["pts"], L["pts"][:1]]) if L["closed"] else L["pts"]
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
        at = np.r_[0, np.cumsum(seg)]
        t = np.arange(0, at[-1], STEP)
        pts.append(np.stack([np.interp(t, at, P[:, i]) for i in range(3)], 1))
        ids.append(np.full(len(t), k))
    P = np.concatenate(pts)
    return P, np.concatenate(ids), kept, cKDTree(P)


def _followed(c):
    """Which of the model's lines a course follows, point by point: the line's index (one within FOLLOW cm over
    FOLLOWED of the course's points or more), or -1; a break under LEAST_RUN cm inside a run is the run's."""
    P, ids, kept, tree = _model()
    d, j = tree.query(c.pts, workers=-1)
    line = np.where(d <= FOLLOW, ids[j], -1)
    counts = np.bincount(line[line >= 0], minlength=len(kept)) if (line >= 0).any() else np.zeros(len(kept), int)
    keep = np.flatnonzero(counts >= FOLLOWED * len(c.pts))
    line[~np.isin(line, keep)] = -1
    runs = _run_values(line)
    for k in range(1, len(runs) - 1):  # a short break between two runs of one line
        v, a, b = runs[k]
        if runs[k - 1][0] == runs[k + 1][0] >= 0 and v != runs[k - 1][0] and c.s[b - 1] - c.s[a] < LEAST_RUN:
            runs[k] = (runs[k - 1][0], a, b)
    merged = []
    for v, a, b in runs:
        if merged and merged[-1][0] == v:
            merged[-1] = (v, merged[-1][1], b)
        else:
            merged.append((v, a, b))
    return line, merged, kept


def _run_values(v):
    """[(value, start, end)] for the runs of equal values."""
    v = np.asarray(v)
    starts = np.r_[0, np.flatnonzero(v[1:] != v[:-1]) + 1]
    ends = np.r_[starts[1:], len(v)]
    return [(int(v[a]), int(a), int(b)) for a, b in zip(starts, ends)]


def _stretch(L, c, a, b):
    """A model line's stretch alongside a course's run from its point a to its point b, as a Course the course's way,
    on both sides when the course is (on a loop, the shorter way round)."""
    from tool import course
    k = slice(0, -1) if L["closed"] else slice(None)
    R = course.Course(L["pts"][k], "the line", nrm=L["nrm"][k], closed=L["closed"], mirror=c.mirror)
    pa, pb = c.pts[a], c.pts[b - 1]
    S = R.between(tuple(pa), tuple(pb))
    if L["closed"]:
        other = R.between(tuple(pb), tuple(pa)).reversed()
        if other.length < S.length:
            S = other
    if (S.pts[-1] - S.pts[0]) @ (pb - pa) < 0:
        S = S.reversed()
    S.mirror = c.mirror
    return S


def _stations(car, call, z, c, R, mark, reached, ends, span=None):
    """A marking read back along a reference course R (the model's line it follows, or the course itself), a station
    every STATION cm over `span` (s0, s1 along R; all of it by default): per copy of R (the course; its mirror image),
    arrays over the stations: expected (paint meant there), n (its texels on its own face), lo and hi (its edges
    across the surface, cm), other (its texels on the line's other face), skin (the body's texels in its designed
    width), bare (of those, neither painted nor covered later), beyond_lo and beyond_hi (the body goes on past its
    painted edges within its designed width, bare), nrm (the body's facing), pos (R's point), and the designed edges
    (lo_e, hi_e). ends: whether the span holds the course's own start and end (else its first and last END stations
    are left out: the marking runs on past them)."""
    lo, hi = z.lo, z.hi
    reach = max(abs(lo), abs(hi)) + TOL + 1.0
    cached = [k for k, v in c._fields.items() if R is c and isinstance(v, list) and not k[1]]
    # the course's own read-back, solved while painting (its reach a centimetre past the marking: a texel further out
    # than that reads as missing, which is a finding too), else solved here
    copies = c._fields[max(cached, key=lambda k: k[0])] if cached else R._across(reach)
    s0, s1 = (0.0, R.length) if span is None else span
    n = max(1, int(np.ceil((s1 - s0) / STATION)))
    centres = np.minimum(s0 + (np.arange(n) + 0.5) * STATION, s1)
    Rpts = np.stack([np.interp(centres, R.s, R.pts[:, k]) for k in range(3)], 1)
    _, ci = cKDTree(c.pts).query(Rpts, workers=-1)  # each station's point on the course
    sc = c.s[ci]
    nrm_all = car.c.bake["normal"].reshape(-1, 3)
    out = []
    for copy in copies:
        lo_e, hi_e = (-hi, -lo) if copy["mirrored"] else (lo, hi)
        W = hi_e - lo_e
        b_mid = (lo_e + hi_e) / 2
        sign = float(np.sign(lo_e + hi_e)) if lo_e * hi_e == 0 else 0.0  # one-sided: the face it's meant on
        offs = np.linspace(-STATION / 2, STATION / 2, 5)
        along = z.along(np.repeat(sc, 5) + np.tile(offs, n), np.full(5 * n, b_mid)).reshape(n, 5)
        expected = (along > 0).any(1)  # paint meant anywhere in the station (a tick is one station wide)
        if not ends[0]:
            expected[:END] = False
        if not ends[1]:
            expected[n - END:] = False
        P, T = copy["P"], copy["T"]
        _, i = cKDTree(P).query(copy["pos"], workers=-1)
        s = R.s[i] + ((copy["pos"] - P[i]) * T[i]).sum(1)
        st = np.floor((s - s0) / STATION).astype(int)
        inside = (st >= 0) & (st < n)
        st, d, lin = st[inside], copy["d"][inside], copy["lin"][inside]
        own = mark[lin]
        got = reached[lin]
        within = (d >= lo_e - TOL) & (d <= hi_e + TOL)
        if sign:
            within &= np.sign(d) * sign >= 0  # its own face
        designed = (d >= lo_e) & (d <= hi_e)
        mine = own & within
        count = np.bincount(st[mine], minlength=n)
        lo_j = np.full(n, np.nan)
        hi_j = np.full(n, np.nan)
        order = np.lexsort((d[mine], st[mine]))  # by station, then by distance: each station's 3rd and 97th percentile
        sm, dm = st[mine][order], d[mine][order]
        starts = np.r_[0, np.flatnonzero(sm[1:] != sm[:-1]) + 1]
        for j, a, b in zip(sm[starts], starts, np.r_[starts[1:], len(sm)]):
            if b - a >= 3:
                lo_j[j], hi_j[j] = dm[a + int(0.03 * (b - a - 1))], dm[a + int(round(0.97 * (b - a - 1)))]
        other = (np.bincount(st[own & (np.sign(d) == -sign) & (np.abs(d) > 0.3) & (np.abs(d) <= W + TOL)], minlength=n)
                 if sign else np.zeros(n, int))
        skin = np.bincount(st[designed], minlength=n)
        bare = np.bincount(st[designed & ~own & ~got], minlength=n)
        skin_lo, skin_hi = np.full(n, np.inf), np.full(n, -np.inf)  # how far the body goes within the designed width
        np.minimum.at(skin_lo, st[designed], d[designed])
        np.maximum.at(skin_hi, st[designed], d[designed])
        # the body on past the painted edges, within the designed width, bare
        has = np.isfinite(lo_j)
        sel = designed & ~own & ~got & has[st]
        beyond_lo = np.bincount(st[sel & (d < lo_j[st] - 0.15)], minlength=n)
        beyond_hi = np.bincount(st[sel & (d > hi_j[st] + 0.15)], minlength=n)
        nrm = np.zeros((n, 3))
        for k in range(3):
            nrm[:, k] = np.bincount(st[mine], weights=nrm_all[lin[mine], k], minlength=n)
        nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
        flip = np.array([-1.0, 1.0, 1.0]) if copy["mirrored"] else 1.0
        pos, facing = Rpts * flip, R.nrm[np.clip(np.searchsorted(R.s, centres), 0, len(R.s) - 1)] * flip
        out.append(dict(expected=expected, n=count, lo=lo_j, hi=hi_j, other=other, skin=skin, bare=bare,
                        skin_lo=skin_lo, skin_hi=skin_hi, beyond_lo=beyond_lo, beyond_hi=beyond_hi, nrm=nrm, pos=pos,
                        facing=facing, lo_e=lo_e, hi_e=hi_e, W=W, sign=sign, mirrored=copy["mirrored"], ends=ends))
    return out


def _marking(car, call, z, found):
    """One marking's findings along the line it follows (or its own course): gaps, hops, steps, kinks, wobbles, its
    width short where the skin is bare, cut where the body ends. Keeps the lines it lies on for the eye."""
    c = z.course
    if c.length < LEAST_RUN:
        return []
    name, label = car.op(call["op"]), z.label
    idx = call["idx"]
    mark = np.zeros(car.n, bool)
    mark[idx[car.c.owner[idx] == call["op"]]] = True
    reached = np.zeros(car.n, bool)
    reached[idx] = True
    line, runs, kept = _followed(c)
    refs = []  # (the reference course, the line's kind or None, the run, the span along the reference)
    for v, a, b in runs:
        if c.s[b - 1] - c.s[a] < LEAST_RUN:
            continue
        if v < 0:
            refs.append((c, None, (a, b), (float(c.s[a]), float(c.s[b - 1]))))
            continue
        R = _stretch(kept[v], c, a, b)
        d = cKDTree(R.pts).query(c.pts[a:b], workers=-1)[0]
        if d.max() <= ON_LINE:  # the course is the line itself: read while painting
            refs.append((c, kept[v]["kind"], (a, b), (float(c.s[a]), float(c.s[b - 1]))))
        else:
            refs.append((R, kept[v]["kind"], (a, b), None))
        if d.max() <= 0.3:  # the eye leaves out the lines the course lies on, and their walls
            car.followed.setdefault(call["op"], []).append(R.pts)
    mine, stretches = [], {}
    for R, kind, (a, b), span in refs:
        for st in _stations(car, call, z, c, R, mark, reached, (a == 0, b == len(c.pts)), span):
            _station_findings(name, label, call, st, kind, mine)
            painted = np.linalg.norm(st["nrm"], axis=1, keepdims=True) > 0.5  # the face its paint is on, else the line's
            car.looks.append({"kind": "line", "op": call["op"], "what": f"{name}: {label}", "step": call["step"],
                              "pos": st["pos"].round(2).tolist(),
                              "facing": np.where(painted, st["nrm"], st["facing"]).round(3).tolist(),
                              "expected": st["expected"].tolist(), "lo": float(st["lo_e"]), "hi": float(st["hi_e"])})
            stretches.setdefault(st["mirrored"], []).append((st, kind, a, b))
    # a step at the join of two lines the course follows in turn: the marking's centre jumps from one to the next
    for runs_ in stretches.values():
        for (s1, k1, a1, b1), (s2, k2, a2, b2) in zip(runs_[:-1], runs_[1:]):
            if k1 is None or k2 is None or float(c.s[a2] - c.s[b1 - 1]) > JOIN:
                continue
            full1 = np.flatnonzero(np.isfinite(s1["lo"]) & (s1["hi"] - s1["lo"] >= NARROW * s1["W"]))
            full2 = np.flatnonzero(np.isfinite(s2["lo"]) & (s2["hi"] - s2["lo"] >= NARROW * s2["W"]))
            if not len(full1) or not len(full2):
                continue
            c1 = (s1["lo"][full1[-1]] + s1["hi"][full1[-1]]) / 2 - (s1["lo_e"] + s1["hi_e"]) / 2
            c2 = (s2["lo"][full2[0]] + s2["hi"][full2[0]]) / 2 - (s2["lo_e"] + s2["hi_e"]) / 2
            jump = abs(c2 - c1)
            if jump > max(STEP_SHARE * s1["W"], STEP_LEAST):
                where, zz, side = _where(np.vstack([s1["pos"][full1[-1]], s2["pos"][full2[0]]]))
                mine.append({"check": "placement", "kind": "line", "z": zz, "side": side, "step": call["step"],
                             "text": f"{name}: {label}: a step of {jump:.1f} cm sideways where the two lines it follows meet, {where}"})
    return mine


def _merged(mine):
    """One marking's findings, those of one kind and side within MERGE cm of one another said once: the longest's
    words (a wobble over its kinks), over all their stretch."""
    out = []
    for f in sorted(mine, key=lambda f: (f["kind"], f["side"] or "", -f["z"][0])):
        last = out[-1] if out else None
        if last and last["kind"] == f["kind"] and last["side"] == f["side"] and last["z"][1] - f["z"][0] <= MERGE:
            rank = lambda g: ("wobbles" in g["text"], g["z"][0] - g["z"][1])
            keep = last if rank(last) >= rank(f) else f
            keep["z"] = [max(last["z"][0], f["z"][0]), min(last["z"][1], f["z"][1])]
            out[-1] = keep
        else:
            out.append(f)
    return out


def _station_findings(name, label, call, st, kind, found):
    """The findings along one copy of one reference: runs of stations with the same fault, each said once. kind: the
    reference line's (None: the course itself)."""
    n, W = len(st["n"]), st["W"]
    exp, cnt = st["expected"], st["n"]
    step = max(STEP_SHARE * W, STEP_LEAST)
    said = {"check": "placement", "step": call["step"]}

    def say(kind_, sel, text):
        where, zz, side = _where(st["pos"][sel])
        found.append({**said, "kind": kind_, "z": zz, "side": side, "text": f"{name}: {label}: {text}, {where}"})

    has = np.isfinite(st["lo"])
    width = np.where(has, st["hi"] - st["lo"], 0.0)
    full = has & (width >= NARROW * W)
    bare = (st["bare"] >= np.maximum(3, 0.5 * st["skin"])) | (st["beyond_lo"] >= 3) | (st["beyond_hi"] >= 3)
    first, last = (np.flatnonzero(exp)[[0, -1]] if exp.any() else (0, -1))
    # gaps: paint expected and none, or under half its width, the skin there and bare
    gap = exp & (~has | (width < 0.5 * W)) & (st["other"] < 3) & bare
    for a, b in _runs(gap):
        L = (b - a) * STATION
        if L < 1.0:
            continue
        if (a == first and st["ends"][0]) or (b - 1 == last and st["ends"][1]):
            say("short", slice(a, b), f"stops {L:.1f} cm short of its end, the skin bare")
        else:
            say("gap", slice(a, b), f"a gap of {L:.1f} cm, the skin bare")
    # hops: a one-sided band on the line's other face
    hop = exp & (st["other"] >= 3) & (cnt < st["other"])
    for a, b in _runs(hop):
        say("line", slice(a, b), f"on the line's other face for {(b - a) * STATION:.1f} cm")
    # its width short where the skin beyond its edge is bare; cut where the body ends (not along that edge)
    narrow = exp & has & ~full & (width >= 0.5 * W)
    for a, b in _runs(narrow & bare):
        if (b - a) * STATION < 2.0:
            continue
        w = float(np.median(width[a:b]))
        say("short", slice(a, b), f"{w:.1f} of its {W:.1f} cm wide, the skin bare beyond it, over {(b - a) * STATION:.1f} cm")
    if kind != "opening":  # the body ends inside its designed width, and the paint reaches the body's end
        ended = exp & has & ~bare & ((st["skin_hi"] < st["hi_e"] - 1.0) | (st["skin_lo"] > st["lo_e"] + 1.0))
        for a, b in _runs(ended):
            w = float(np.median(width[a:b]))
            if W - w >= 1.0:
                say("cut", slice(a, b), f"cut short by the edge where the body ends: {w:.1f} of its {W:.1f} cm across")
    # steps: an edge jumping between neighbouring full stations
    both = full[:-1] & full[1:]
    jump = np.zeros(n - 1)
    jump[both] = np.maximum(np.abs(np.diff(st["lo"]))[both], np.abs(np.diff(st["hi"]))[both])
    for j in np.flatnonzero(jump > step):
        say("line", slice(j, j + 2), f"a step of {jump[j]:.1f} cm sideways")
    # kinks and wobbles: the centre's turning against the line, over KINK_RUN cm each side
    if kind is None:
        return
    # the line the eye follows: a one-sided band's edge on the line, a centred strip's middle
    track = st["lo"] if st["sign"] > 0 else st["hi"] if st["sign"] < 0 else (st["lo"] + st["hi"]) / 2
    centre = np.where(full, track, np.nan)
    k = int(round(KINK_RUN / STATION))
    kinks = []
    for j in range(k, n - k):
        if np.isnan(centre[j - k]) or np.isnan(centre[j]) or np.isnan(centre[j + k]):
            continue
        before = np.degrees(np.arctan2(centre[j] - centre[j - k], k * STATION))
        after = np.degrees(np.arctan2(centre[j + k] - centre[j], k * STATION))
        if abs(after - before) >= KINK:
            kinks.append((j, after - before))
    picked = []  # the sharpest of each cluster within a centimetre
    for j, turn in kinks:
        if picked and j - picked[-1][0] <= k // 2:
            if abs(turn) > abs(picked[-1][1]):
                picked[-1] = (j, turn)
        else:
            picked.append((j, turn))
    i = 0
    while i < len(picked):
        j0 = i
        while (j0 + 1 < len(picked) and (picked[j0 + 1][0] - picked[j0][0]) * STATION <= WOBBLE / 2
               and np.sign(picked[j0 + 1][1]) != np.sign(picked[j0][1])):
            j0 += 1
        if j0 - i >= 2:  # three kinks turning each way: a wobble
            a, b = picked[i][0], picked[j0][0]
            amp = float(np.nanmax(centre[a - k:b + k + 1]) - np.nanmin(centre[a - k:b + k + 1])) / 2
            period = 2 * (b - a) * STATION / (j0 - i)
            say("line", slice(a, b + 1), f"wobbles {amp:.1f} cm either way about every {period:.0f} cm over {(b - a) * STATION:.0f} cm")
        else:
            for j, turn in picked[i:j0 + 1]:
                say("line", slice(j, j + 1), f"a kink of {abs(turn):.0f} degrees against the line")
        i = j0 + 1


def _fills(car, call, o, fills, found):
    """A fill's painted edge against the lines it was filled to: where it sits FILL cm or more off them."""
    if o is None:
        return
    name = car.op(call["op"])
    own = o["kind"] == NATURAL
    if not own.any():
        return
    b = o["b"][own]
    pos = car.c.pos[b].astype(np.float64)
    length = o["length"][own]
    for z, lines, what in fills:
        car.followed.setdefault(call["op"], []).append(lines)
        d = cKDTree(lines).query(pos, distance_upper_bound=3.0 * FILL + 3.0, workers=-1)[0]
        near = np.isfinite(d)
        if near.sum() < 10:
            continue
        off = near & (d > FILL)
        zb = np.floor(pos[:, 2] / 2.0).astype(int)
        z0 = zb.min()
        off_len = np.bincount(zb[off] - z0, weights=length[off], minlength=int(zb.max() - z0 + 1))
        for a, c_ in _runs(off_len >= 1.5):
            sel = off & (zb - z0 >= a) & (zb - z0 < c_)
            if c_ - a < 2 or not sel.any() or length[sel].sum() < 3.0:
                continue
            where, zz, side = _where(pos[sel])
            found.append({"check": "placement", "kind": "short", "z": zz, "side": side, "step": call["step"],
                          "text": f"{name}: its edge sits {np.median(d[sel]):.1f} cm inside {what} over {length[sel].sum():.0f} cm, {where}"})


# ---- the eye: how a graphic sits against the lines the eye sees ----

@functools.lru_cache(maxsize=1)
def _lines():
    """The lines the eye sees, every STEP cm: points (n, 3), the body's normal at each, which line each is on, how far
    along it, and the lines."""
    from tool import meshlines
    kept = [L for L in meshlines.lines("Skin")  # the longest first
            if L["length"] >= LEAST and not L["parts"][0].startswith("wheel cover")]
    pts, nrm, ids, s = [], [], [], []
    for k, L in enumerate(kept):
        P, N = (np.vstack([L[x], L[x][:1]]) if L["closed"] else L[x] for x in ("pts", "nrm"))
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
        at = np.r_[0, np.cumsum(seg)]
        t = np.arange(0, at[-1], STEP)
        pts.append(np.stack([np.interp(t, at, P[:, i]) for i in range(3)], 1))
        n = np.stack([np.interp(t, at, N[:, i]) for i in range(3)], 1)
        nrm.append(n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9))
        ids.append(np.full(len(t), k))
        s.append(t)
    P, N, ids, s = np.concatenate(pts), np.concatenate(nrm), np.concatenate(ids), np.concatenate(s)
    # where two lines run within ONE cm of each other (a groove's walls, the gap round a piece set into the body),
    # the eye sees one: the longer one's
    pairs = cKDTree(P).query_pairs(ONE, output_type="ndarray")
    a, b = pairs[:, 0], pairs[:, 1]
    other = ids[a] != ids[b]
    drop = np.zeros(len(P), bool)
    drop[np.where(ids[a] > ids[b], a, b)[other]] = True
    e = meshlines._edges("Skin")
    centres, names = e["P"][e["T"]].mean(1), meshlines._parts_of("Skin")
    for L in kept:  # a small ring: the part inside it, where it isn't the ring's own
        if L["closed"] and L["length"] < RING:
            mid = L["pts"].mean(0)
            r = np.linalg.norm(L["pts"] - mid, axis=1).mean()
            inner = names[np.linalg.norm(centres - mid, axis=1) < 0.7 * r]
            inner = [x for x in meshlines._most(inner) if x != L["parts"][0]]
            L["inside"] = inner[0] if inner else None
    return P[~drop], N[~drop], ids[~drop], s[~drop], kept


def _name(L):
    if L.get("inside"):
        return f"the outline round the {L['inside']}"
    what = "edge where the body ends" if L["kind"] == "opening" else "panel line" if L["walls"] > 1 else "crisp line"
    return f"the {what} along the {L['parts'][0]}"


def _span(p, q):
    """From where to where along the car, front first."""
    if abs(p[2] - q[2]) <= 2:
        return _place(float(p[2]))
    p, q = (p, q) if p[2] > q[2] else (q, p)
    return f"{_place(float(p[2]))} to {_place(float(q[2]))}"


def _edge(c, op):
    """Where a call shows (the texels it covered last) and its edge there, on the car: {shown, edge: positions, nrm: the
    body's normal at each edge texel, next: the call that shows beside each, paint}, or None."""
    shown = np.flatnonzero(c.owner == op)
    if not len(shown):
        return None
    edge, nxt = np.zeros(len(shown), bool), np.full(len(shown), -1)
    for d in (1, -1, c.w, -c.w):
        nb = np.clip(shown + d, 0, len(c.owner) - 1)
        other = (c.owner[nb] != op) & (c.owner[nb] != -1)
        close = np.linalg.norm(c.pos[nb] - c.pos[shown], axis=1) < NEIGHBOUR
        nxt = np.where(other & close & ~edge, c.owner[nb], nxt)
        edge |= other & close
    paint = np.r_[np.median(c.colour[shown], 0), np.median(c.rough[shown]), np.median(c.metal[shown])]
    return {"shown": c.pos[shown], "edge": c.pos[shown[edge]], "nrm": c.nrm[shown[edge]], "next": nxt[edge], "paint": paint}


def _angle(g, s):
    """Degrees the edge turns away from the line over a stretch, from how the gap changes along it."""
    if len(g) < 3 or s[-1] - s[0] < 1.0:
        return 0.0
    k = np.polyfit(s, g, 1)[0]
    return float(np.degrees(np.arctan(abs(k))))


def _stretches(g, s):
    """The gap split into stretches each well fit by a straight change along the line (within FIT cm), greedily from
    its start: (i, j, degrees the edge turns from the line over it). The gap at NEAR (the line too far) is no stretch."""
    out, i, n = [], 0, len(g)
    while i < n - 2:
        if g[i] >= NEAR:
            i += 1
            continue
        j = i + 2
        while j < n and g[j] < NEAR:
            k = min(n, j + 4)
            if np.any(g[j:k] >= NEAR):
                break
            fit = np.polyval(np.polyfit(s[i:k], g[i:k], 1), s[i:k])
            if np.abs(fit - g[i:k]).max() > FIT:
                break
            j = k
        out.append((i, j, _angle(g[i:j], s[i:j])))
        i = j
    return out


def _at(p, n, span=None):
    """Where a thing said is on the car, which way the body faces there (for a close look at it), and the stretch along
    the car it's about (span: its points; else that point)."""
    z = (p[2], p[2]) if span is None else (span[:, 2].min(), span[:, 2].max())
    return (tuple(round(float(v), 1) for v in p), tuple(round(float(v), 3) for v in n),
            tuple(round(float(v), 1) for v in z))


def _beside(g, s, p, n, name, key, touching, ends):
    """What a stretch of a line outside a graphic says: a gap that closes; a near miss at one of the graphic's ends
    (touching: the line reaches the graphic at an end of the stretch, so it isn't one). p and n: the points the gap is
    measured from and the body's normal there; ends: the graphic's end points, or None for one without ends."""
    if s[-1] - s[0] < 2.0:
        return []
    said = []
    where = lambda a, b: _span(p[a], p[b - 1])
    for a, b, th in _stretches(g, s):
        run, g1 = s[b - 1] - s[a], g[a:b]
        if run < EVEN_RUN:
            continue
        least = a + int(np.argmin(g1))
        if th >= LEVEL and g1.max() - g1.min() >= 1.0 and g1.min() < CLOSE:
            said.append(("CLOSES", f"the gap to {name} CLOSES from {g1.max():.1f} to {g1.min():.1f} cm over {run:.0f} cm "
                         f"({th:.0f} degrees), {where(a, b)}", key, *_at(p[least], n[least], p[a:b])))
    m = int(np.argmin(g))
    at_end = ends is not None and len(ends) and np.linalg.norm(ends - p[m], axis=1).min() <= END_NEAR
    if TOUCH < g[m] < MISS and not touching and at_end:
        said.append(("NEAR MISS", f"a NEAR MISS: its end comes within {g[m]:.1f} cm of {name} without reaching it, "
                     f"at {_place(float(p[m][2]))}", key, *_at(p[m], n[m])))
    return said


def _crossing(g, s):
    """Degrees between a line and a graphic's edge where it crosses, from how fast the gap changes across it (the gap
    signed: minus the depth inside the graphic)."""
    if len(g) < 3 or s[-1] - s[0] < 1.0:
        return 90.0
    return float(np.degrees(np.arcsin(min(1.0, abs(np.polyfit(s, g, 1)[0])))))


def _runs_at(tree, shown, p, t):
    """Degrees between a line (at p, along t) and a graphic that runs across it (its texels round p, LONG times longer
    than wide: a tape, a ruler), or None (a disc, a panel's colour: its edge says)."""
    q = shown[tree.query_ball_point(p, 3 * SPAN)]
    if len(q) < 10:
        return None
    w = np.exp(-np.sum((q - p) ** 2, axis=1) / (2 * SPAN * SPAN))
    m = w @ q / w.sum()
    ev, axes = np.linalg.eigh(((q - m) * w[:, None]).T @ (q - m) / w.sum())
    if ev[2] < LONG * LONG * ev[1]:
        return None
    return float(np.degrees(np.arccos(min(1.0, abs(float(axes[:, 2] @ t))))))


def _through(tree, shown, p, t, n):
    """How far a graphic reaches past a stretch of line inside it, on the side it reaches least (its texels within
    REACH_IN cm of the stretch, across the line): under ONE cm it lies on one side only (its edge meets the line),
    REACH_IN or so it crosses. p, t, n: the stretch's points, its direction and the body's normal there."""
    near = sorted({i for found in tree.query_ball_point(p, REACH_IN) for i in found})
    if not near:
        return 0.0
    q = shown[near]
    j = cKDTree(p).query(q)[1]
    across = np.sort(np.einsum("ij,ij->i", q - p[j], np.cross(t[j], n[j])))
    if len(across) < 6:
        return 0.0
    return float(max(0.0, min(across[-3], -across[2])))  # the third furthest each way: a stray texel isn't a reach


def _eye_side(G, sign, skip, ends):
    """What one side's lines say about one graphic: a list of (flag, words, line key, where, the body's normal, z).
    skip: the lines' points the graphic follows (its own line, and its walls), left out."""
    P, N, ids, S, kept = _lines()
    shown, edge = G["shown"], G["edge"]
    shown, edge = shown[shown[:, 0] * sign > -0.5], edge[edge[:, 0] * sign > -0.5]
    if len(edge) < 3:
        return []
    lo, hi = edge.min(0) - NEAR, edge.max(0) + NEAR
    box = np.flatnonzero(np.all((P >= lo) & (P <= hi), axis=1) & (P[:, 0] * sign > -0.5) & ~skip)
    if not len(box):
        return []
    gap = cKDTree(edge).query(P[box], distance_upper_bound=NEAR)[0]
    tree = cKDTree(shown)
    inside = np.isfinite(tree.query(P[box], distance_upper_bound=TOUCH)[0])  # in a groove's width
    said = []
    for k in np.unique(ids[box]):
        on = box[ids[box] == k]
        sel = ids[box] == k
        g, ins, s = gap[sel], inside[sel], S[on]
        order = np.argsort(s)
        g, ins, s, pts, nrm = g[order], ins[order], s[order], P[on][order], N[on][order]
        name, L = _name(kept[k]), kept[k]
        key = (name, L["kind"])
        overs = []  # where the graphic's edge runs just past this line: (how far, where, the normal)
        if L.get("inside") is not None and ins.any():  # a small piece's outline: the graphic over all of it, or some
            share = ins.sum() / max(1, np.sum(ids == k))
            mid = len(pts) // 2
            if share < 0.95:
                said.append(("PART OVER", f"lies PART OVER {name}, {share:.0%} of its outline, at {_place(float(pts[mid][2]))}", key,
                             *_at(pts[mid], nrm[mid], pts)))
            continue
        for a, b in _runs(np.isfinite(g) | ins):
            if s[b - 1] - s[a] < 2.0:
                continue
            gg, ii, ss, pp, nn = g[a:b], ins[a:b].copy(), s[a:b], pts[a:b], nrm[a:b]
            tan = np.gradient(pp, axis=0)
            tan /= np.maximum(np.linalg.norm(tan, axis=1, keepdims=True), 1e-9)
            raw = np.where(np.isfinite(gg), gg, NEAR)  # the gap as measured (inside: to the edge), for a crossing
            gg = minimum_filter1d(raw, int(PIECES / STEP) + 1, mode="nearest")
            for c0, c1 in _runs(~ii):  # a line through a graphic of pieces (dashes, ticks, blocks) runs along it
                if 0 < c0 and c1 < len(ii) and ss[c1 - 1] - ss[c0] <= PIECES and gg[c0:c1].max() <= PIECES:
                    ii[c0:c1] = True
            # crossings: where the line goes into the graphic or out of it, but for the ends of a stretch it lies along
            along = np.zeros(len(ii), bool)
            for c0, c1 in _runs(ii):
                along[c0:c1] = ss[c1 - 1] - ss[c0] >= EVEN_RUN
            for c0, c1 in _runs(ii):
                if along[c0] or L["kind"] == "opening":
                    continue
                mid = (c0 + c1) // 2
                past = _through(tree, shown, pp[c0:c1], tan[c0:c1], nn[c0:c1])
                if past <= ONE:  # on one side only: an end on the line
                    continue
                if past < PAST:  # said once a line, below
                    overs.append((past, pp[mid], nn[mid]))
                    continue
                chord = pp[min(len(pp) - 1, mid + 8)] - pp[max(0, mid - 8)]  # the line's way over 4 cm, not a facet's
                th = _runs_at(tree, shown, pp[mid], chord / max(np.linalg.norm(chord), 1e-9))
                half = max(1, min(10, (c1 - c0) // 2))  # into the graphic no further than its middle
                for x, w in (((mid, None),) if th is not None else  # a tape across it: once
                             ((c0 - 1, slice(max(0, c0 - 8), c0 + half)), (c1, slice(c1 - half, c1 + 8)))):  # in, out
                    if x < 0 or x >= len(ii):
                        continue
                    if w is not None:
                        sg = np.where(ii[w], -raw[w], raw[w])
                        known = np.abs(sg) < NEAR  # a gap past NEAR is no gap measured
                        th = _crossing(sg[known], ss[w][known])
                    if th < LEAN:
                        said.append(("SHALLOW", f"crosses {name} at a SHALLOW {th:.0f} degrees at {_place(float(pp[x][2]))}", key,
                                     *_at(pp[x], nn[x])))
            for c0, c1 in _runs(~ii):  # beside it, outside the graphic
                said += _beside(gg[c0:c1], ss[c0:c1], pp[c0:c1], nn[c0:c1], name, key, c0 > 0 or c1 < len(ii), ends)
        if overs:
            most, at, n = max(overs, key=lambda o: o[0])
            where = np.array([o[1] for o in overs])
            places = (f"at {len(overs)} places, {_span(where[np.argmax(where[:, 2])], where[np.argmin(where[:, 2])])}"
                      if len(overs) > 1 else f"at {_place(float(at[2]))}")
            said.append(("JUST PAST", f"its edge runs JUST PAST {name}, {most:.1f} cm over it, {places}", key,
                         *_at(at, n, where)))
    once = {}
    for x in said:
        once.setdefault(x[:3], x)
    return list(once.values())


def _between(A, B, name, sign):
    """What one side says about a graphic against another: touching it (no nearer gap shows), in another paint."""
    a, b = (A["edge"][:, 0] * sign > -0.5), (B["edge"][:, 0] * sign > -0.5)
    ea, eb = A["edge"][a], B["edge"][b]
    if len(ea) < 3 or len(eb) < 3:
        return []
    if np.any(ea.min(0) - NEAR_GRAPHIC > eb.max(0)) or np.any(eb.min(0) - NEAR_GRAPHIC > ea.max(0)):
        return []
    d = cKDTree(eb).query(ea, distance_upper_bound=NEAR_GRAPHIC)[0]
    if not np.isfinite(d).any():
        return []
    key, na = (name, "graphic"), A["nrm"][a]
    m = int(np.argmin(d))
    if d[m] > TOUCH or np.abs(A["paint"] - B["paint"]).max() <= SAME:
        return []
    on = np.flatnonzero(d <= TOUCH)
    q = ea[on]
    long = np.ptp((q - q.mean(0)) @ np.linalg.svd(q - q.mean(0), full_matrices=False)[2][0]) if len(q) > 1 else 0
    c = on[np.argmin(np.linalg.norm(q - q.mean(0), axis=1))]
    hi, lo = q[np.argmax(q[:, 2])], q[np.argmin(q[:, 2])]
    return [("TOUCHES", f"TOUCHES {name} over {max(long, 0.1):.1f} cm, {_span(hi, lo)}", key, *_at(ea[c], na[c], q))]


def _eye(car, calls, found):
    """How each marking, fill and area paint sits against the lines the eye sees (not the ones it follows) and the
    other graphics, as notes with where to look."""
    c = car.c
    P = _lines()[0]
    gs = []
    for call in calls:
        e = _edge(c, call["op"])
        if e is not None and len(e["edge"]) >= 3:
            own = car.followed.get(call["op"], [])
            skip = np.zeros(len(P), bool)
            if own:
                skip = cKDTree(np.vstack(own)).query(P, distance_upper_bound=ALONG, workers=-1)[0] <= ALONG
            ends = [cc.pts[[0, -1]] * f for z in _pieces(call["zone"]) if not (cc := z.course).closed
                    for f in ([1.0, np.array([-1.0, 1.0, 1.0])] if cc.mirror else [1.0])]
            gs.append({**call, **e, "skip": skip, "ends": np.vstack(ends) if ends else None, "n": len(gs) + 1})
    laid = {B["op"] for B in gs for A in gs if A is not B and np.mean(B["next"] == A["op"]) >= LAID}
    out = {}
    for A in gs:
        name = car.op(A["op"])
        for side, sign in (("left", 1), ("right", -1)):
            said = _eye_side(A, sign, A["skip"], A["ends"])
            for B in gs[A["n"]:]:
                if A["op"] not in laid and B["op"] not in laid:
                    said += _between(A, B, car.op(B["op"]), sign)
            for flag, words_, _, at, nrm, z in said:
                text = f"{name}: {words_}"
                if text in out:
                    out[text]["side"] = None
                else:
                    out[text] = {"check": "eye", "kind": "over" if flag == "TOUCHES" else "sits", "z": list(z), "side": side,
                                 "step": A["step"], "text": text, "at": list(at), "nrm": list(nrm)}
    found += list(out.values())


# ---- what the close looks travel along and look over (tool/close.py) ----

def _look_edges(car, call, fills):
    """A fill's lines, for the close looks along its edge: each line a station every STATION cm, the surface's facing."""
    from tool import surface
    for _, lines, what in fills:
        breaks = np.flatnonzero(np.linalg.norm(np.diff(lines, axis=0), axis=1) > 2.0) + 1
        for P in np.split(lines, breaks):
            seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
            at = np.r_[0, np.cumsum(seg)]
            if len(P) < 2 or at[-1] < LEAST_RUN:
                continue
            t = np.arange(STATION / 2, at[-1], STATION)
            pos = np.stack([np.interp(t, at, P[:, i]) for i in range(3)], 1)
            car.looks.append({"kind": "edge", "op": call["op"], "what": f"{car.op(call['op'])}: its edge on {what}",
                              "step": call["step"], "pos": pos.round(2).tolist(),
                              "facing": surface.load().facing(pos).round(3).tolist()})


def _look_marks(car):
    """Each mark, words and picture, for a close look over it: its middle, the way it faces, how far it reaches."""
    c = car.c
    for rec in car.skin.marks + car.skin.pictures:
        if not len(rec["idx"]):
            continue
        pos = c.pos[rec["idx"]].astype(np.float64)
        middle = pos[np.argmin(np.linalg.norm(pos - pos.mean(0), axis=1))]
        facing = np.asarray(rec["frame"][2], np.float64)
        some = rec["idx"][:: max(1, len(rec["idx"]) // 300)]  # its texels' places, to see what hides it
        car.looks.append({"kind": "mark", "op": rec["op"], "what": rec["what"], "step": rec["step"], "shape": rec["kind"],
                          "at": middle.round(2).tolist(), "facing": (facing / np.linalg.norm(facing)).round(3).tolist(),
                          "reach": round(float(np.linalg.norm(pos - middle, axis=1).max()), 1),
                          "pts": c.pos[some].round(2).tolist(), "nrm": c.nrm[some].round(3).tolist()})


# ---- the verdict ----

def run(skin):
    """The verdict on a skin painted with Skin.measure on: {design, findings, seconds}."""
    t0 = time.time()
    found = [dict(f) for f in skin.findings]
    if "Skin" in skin.canvases and skin.canvases["Skin"].owner is not None:
        car = _Car(skin)
        plain = []
        for call in skin.zoned:
            pieces_ = _pieces(call["zone"])
            fills = _fill_lines(call["zone"])
            graphic, o = _zoned(car, call, found, bool(pieces_))
            mine = []
            for z in pieces_:
                mine += _marking(car, call, z, found) or []
            found += _merged(mine)
            if fills:
                _fills(car, call, o, fills, found)
                _look_edges(car, call, fills)
            if not graphic and not pieces_ and not fills and call["op"] not in car.blends:
                _reach(car, call, found)
            if not graphic and call["op"] not in car.blends:
                plain.append(call)
        _pictures(car, found)
        _laid(car, found)
        _clear(car, found)
        _scattered(car, found)
        _eye(car, plain, found)
        _look_marks(car)
    once = {}
    for f in found:  # a side's twin once
        f.setdefault("side", None)
        f.setdefault("z", None)
        f["level"] = "note" if f["check"] == "eye" else LEVELS[f["kind"]]
        if f["text"] in once:
            once[f["text"]]["side"] = None
        else:
            once[f["text"]] = f
    rank = {"block": 0, "warn": 1, "note": 2}
    findings = sorted(once.values(), key=lambda f: (rank[f["level"]], -(f["z"][0] if f["z"] else -1e9), f["text"]))
    return {"design": gate.design_hash(skin.name), "findings": findings, "seconds": round(time.time() - t0, 1),
            "graphics": car.looks if "Skin" in skin.canvases and skin.canvases["Skin"].owner is not None else []}


def words(verdict):
    """The verdict as lines for Claude: the blocks first, then the warnings, then the eye's notes."""
    return [f"{f['level'].upper() if f['level'] == 'block' else f['level']}: {f['kind']}: {f['text']}" for f in verdict["findings"]]


def step_hashes(name):
    """Each step's hash, from its code in design.py (its s.step(...) to the next, as parsed: comments and spacing
    don't count) and the code of the design's own functions and names it uses: an edit changes the hashes of the steps
    it edits, and no other's (tool/close.py's diff of the close looks)."""
    import ast
    tree = ast.parse((paths.SKINS / name / "design.py").read_text())
    own = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            own[node.name] = node
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                for n in ast.walk(t):
                    if isinstance(n, ast.Name):
                        own[n.id] = node
    body = own["design"].body if isinstance(own.get("design"), ast.FunctionDef) else []
    steps, now = {}, "The design"
    for stmt in body:
        for n in ast.walk(stmt):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "step" and n.args
                    and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str)):
                now = n.args[0].value
        steps.setdefault(now, []).append(stmt)
    out = {}
    for step, stmts in steps.items():
        used, todo = set(), [n.id for s_ in stmts for n in ast.walk(s_) if isinstance(n, ast.Name)]
        while todo:
            k = todo.pop()
            if k in own and k != "design" and k not in used:
                used.add(k)
                todo += [n.id for n in ast.walk(own[k]) if isinstance(n, ast.Name)]
        code = [ast.unparse(s_) for s_ in stmts] + [ast.unparse(own[k]) for k in sorted(used)]
        out[step] = hashlib.sha256("\n".join(code).encode()).hexdigest()[:16]
    return out


def save(name, verdict, skin=None):
    """The verdict in build/<name>/verdict.json; with the skin painted, what its close looks read (tool/close.py):
    graphics.json (the graphics, each call's step and paint, each step's hash) and owner.npy (the call that covered each texel of
    the body's map last)."""
    out = paths.BUILD / name
    out.mkdir(parents=True, exist_ok=True)
    graphics = verdict.pop("graphics", [])
    if skin is not None and skin.canvases.get("Skin") is not None and skin.canvases["Skin"].owner is not None:
        c = skin.canvases["Skin"]
        np.save(out / "owner.tmp.npy", c.owner.reshape(c.h, c.w).astype(np.int16))
        (out / "owner.tmp.npy").replace(out / "owner.npy")
        steps = step_hashes(name) if (paths.SKINS / name / "design.py").exists() else {}
        paths.write(out / "graphics.json", json.dumps({"design": verdict["design"], "steps": steps,
                                                       "ops": [o["step"] for o in skin.ops],
                                                       "paints": [o["what"] for o in skin.ops], "graphics": graphics}))
    paths.write(out / "verdict.json", json.dumps(verdict, indent=1))


def main():
    from tool import skin as skin_mod
    name = sys.argv[1]
    with skin_mod.paint_slot():
        s = skin_mod.paintbox.Skin(name)
        s.measure = True
        skin_mod.load_design(name)(s)
        s.end_steps()
    verdict = run(s)
    save(name, verdict, s)
    print("\n".join(words(verdict)) or "the judge names nothing")
    print(f"judged in {verdict['seconds']} s")


if __name__ == "__main__":
    main()
