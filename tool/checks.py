"""The checks: what's wrong on a painted car, named before anyone looks (nearly every flaw the user has pointed out
was a graphic that didn't fit the car).

    python -m tool.checks <name>      paint the skin and print what the checks name

`run` gives every finding on a skin painted with Skin.measure on (tool/skin.py's show): each
{check, kind, text, z, side, step}, kind one of KINDS, z the stretch along the car in
cm, front to back, or None. Three sources: the paint itself (Skin.findings), the measures
(tool/measure.py: a paint that stops short or leaves a gap; a graphic's cuts speak in their place)
and the checks here, read off the body's texels: who painted each last
(Canvas.owner), what it covered (Skin.zoned's `under`), and each zoned paint's outline, followed
texel to texel and across the texture's seams (`_edges`), with what ends it at each step: its own
shape (a factor the design wrote), the surface turning away (a factor read off the car,
measure.READINGS), the parts it was aimed at, a later paint, or the surface itself.

A graphic is a mark no longer than COMPACT cm, not a line, whose own shape ends it (`_marks`: from
its middle the zone's written factors run out in every direction, or all but one line's, a shape
drawn through the car from above or from the side): a spot, a badge, a word, a picture. A band, an
area or a pattern doesn't end by itself, and the measures follow it instead. A check names an
accident, never a design: a paint the design says crosses the car's parts (`across=True`) keeps
its cuts and spills unsaid.
  cut      a graphic's outline ended for CUT cm or more by a fold, the edge of its parts, an
           opening or a panel's edge; a mark laid on a panel (tool/marks.py) with less than WHOLE
           of its shape on the car.
  spill    a graphic lying on two of the model's pieces (tool/pieces.py), SPILL cm² or more on the
           second.
  over     a graphic lying across the edge of another, or a later paint covering part of one.
  clear    a second paint on the panels the game letters or the nose fin's plate (PANELS), or a
           graphic with NEAR of itself within CLEAR cm of one.
  edge     a zone's edge feathered wider than SOFT cm (wider than BLEND it's a blend, which is
           meant), or a picture with fewer than PIXELS pixels per cm on the car.
  fold     the surface under words or a placard turning more than FOLD_WORDS degrees from its mean:
           they will look bent.
  upside down  words laid as if the surface faced one way, over a surface facing more than FLIPPED
           degrees off it (flipped or sheared), or on a side with their top pointing down (HANG).
  spread   a scatter whose copies lie unevenly (UNEVEN) or leave BARE of the surface far from any.
A picture laid across the panels on purpose (Skin.decal's across=True) keeps its cuts and spills
unsaid, as a paint does.
"""

import json
import sys

import numpy as np
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

from tool import carmap, coverage, fbx, measure, paths, pieces, shapes, uvmap

COMPACT = 60.0  # cm: the longest a graphic is
VOXEL = 2.5     # cm: marks nearer than this are one
CUT = 3.0       # cm of a graphic's outline
SPILL = 5.0     # cm² of a graphic on a second piece
ACROSS = 0.03   # the share of a graphic over another's paint from which it lies across its edge
WHOLE = 0.95    # the share of a laid mark's shape that must be on the car
CLEAR = 3.0     # cm round the panels
NEAR = 0.10     # the share of a graphic within CLEAR cm of a panel from which it's said
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
FILL = 0.08     # a mark's area over its length squared: under this it's a line, which may cross anything
LOOK = 200_000  # outline steps looked at per paint; a longer outline is sampled
PANELS = {"number panel": "the number panel (the game letters it)",
          "engine cover panel": "the engine cover panel (the game letters it)",
          "nose fin": "the nose fin's plate"}

# The kinds of flaw the user has pointed out: a finding's kind, and a planted flaw's on the self-test's pair
KINDS = {
    "short": "a paint stops before the surface it was meant to cover ends",
    "gap": "a hole inside a paint's run",
    "fold": "a picture or words over a fold or a sharp curve",
    "cut": "a shape cut off by an edge, an opening or a join",
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

NATURAL, FOLD, PART, EDGE, COVERED, HOLE = range(6)


def _reading(f):
    return repr(f).lstrip("~(").split("(")[0] in measure.READINGS


def _blend(f):
    return repr(f).lstrip("~(").split("(")[0] in ("fade", "radial")


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
    """What the checks read off the body's texture, worked out once a paint."""

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

    def open(self, texels):
        return carmap.load().value("open", self.c.pos[texels], self.c.nrm[texels])

    def voxel(self, pos):
        return tuple(np.clip(((pos - self.lo) / VOXEL).astype(int), 0, self.dims - 1).T)

    def place(self, texels):
        """Where texels are, in words, and for a finding: (words, z, side)."""
        p = self.c.pos[texels]
        z = [round(float(p[:, 2].max()), 1), round(float(p[:, 2].min()), 1)]
        left, right = bool((p[:, 0] > 2).any()), bool((p[:, 0] < -2).any())
        side = "left" if left and not right else "right" if right and not left else None
        a, b = round(z[0]) + 0.0, round(z[1]) + 0.0  # never "z -0"
        along = measure._place(a) if a - b < 4 else f"{measure._place(a)} to {measure._place(b)}"
        return (f"on the {side}, " if side else "") + along, z, side

    def op(self, k):
        if k < 0:
            return "the stock paint"
        o = self.skin.ops[k]
        return f"{o['what']} ({o['step']})"


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
    return {"b": np.concatenate([b, e]), "kind": np.concatenate([kind, np.where(whole, EDGE, NATURAL)]),
            "detail": np.concatenate([detail, np.full(len(e), -1)]),
            "feather": np.concatenate([feather, np.full(len(e), np.nan)]),
            "length": np.sqrt(car.cm2[np.concatenate([b, e])]) * 0.8 * scale}  # 0.8: steps go round a curve by its corners


# the directions a mark's shape is followed in from its middle: to each neighbour of a cube's cell
RAYS = np.array([(x, y, z) for x in (-1, 0, 1) for y in (-1, 0, 1) for z in (-1, 0, 1) if (x, y, z) != (0, 0, 0)], np.float64)
RAYS /= np.linalg.norm(RAYS, axis=1, keepdims=True)
FAR = np.arange(COMPACT, 2 * COMPACT + 1, 5.0)  # cm from a mark's middle: past any graphic's end


def _marks(car, call, shown):
    """A zoned paint's separate marks (its texels joined within VOXEL cm): for each of `shown`'s texels
    the mark it's in, and which marks are graphics: no longer than COMPACT cm, not a line (FILL), and
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
    small = np.flatnonzero((longest > 0) & (longest <= COMPACT) & (area >= FILL * longest ** 2))
    if not written or not len(small):
        return mark, graphic
    # each small mark's middle: its texel nearest the mean of them
    count = np.maximum(np.bincount(mark, minlength=n + 1), 1)
    mean = np.stack([np.bincount(mark, weights=c.pos[shown, k], minlength=n + 1) / count for k in range(3)], 1)
    off = np.linalg.norm(c.pos[shown] - mean[mark], axis=1)
    order = np.lexsort((off, mark))
    first = order[np.unique(mark[order], return_index=True)[1]]  # one texel per mark, in the marks' order
    middle = shown[first[np.searchsorted(mark[first], small)]]
    pts = (c.pos[middle][:, None, None, :] + FAR[None, None, :, None] * RAYS[None, :, None, :]).reshape(-1, 3).astype(np.float32)
    nrm = np.repeat(c.nrm[middle], len(RAYS) * len(FAR), axis=0)
    inside = np.ones(len(pts), bool)
    for f in written:
        inside &= f(pts, nrm) > 0.5
    on = inside.reshape(len(small), len(RAYS), len(FAR)).any(2)  # the shape runs on that way
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


def _zoned(car, call, found):
    """One zoned paint's findings: its edge, and each of its graphics' cuts, spills and overlaps.
    True when the paint is graphics and next to nothing else."""
    c = car.c
    idx = call["idx"]
    still = c.owner[idx] == call["op"]
    shown = idx[still]
    if len(shown) < 20:
        return
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
            return
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
        return
    mark, graphic = _marks(car, call, shown)
    if not graphic[mark].any():
        return
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
        for code in (FOLD, PART, EDGE):
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
                EDGE: lambda: "the surface ends (an opening's rim or a panel's edge)"}[code]()
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
    return bool(car.cm2[shown[graphic[mark]]].sum() >= 0.95 * car.cm2[shown].sum())


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
    """Each picture projected onto the body (Skin.decal's across=True): pixelated; and, as it says it
    crosses edges on purpose, nothing of its pieces or what it lies across."""
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
        _pixelated(car, name, step, S, min(p["pixels"] for p in laid), found)
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


def _area(c, texels):
    """The area of texels on the car, in cm²: each one's from the texels either side of it, along its
    row and its column."""
    pos, cover = c.bake["position"].reshape(-1, 3), c.cov.reshape(-1)
    area = np.zeros(len(texels))
    ok = np.ones(len(texels), bool)
    steps = []
    for d in (1, c.w):
        a, b = np.clip(texels - d, 0, len(cover) - 1), np.clip(texels + d, 0, len(cover) - 1)
        ok &= cover[a] & cover[b]
        steps.append((pos[b].astype(np.float64) - pos[a]) / 2)
    area[ok] = np.linalg.norm(np.cross(steps[0][ok], steps[1][ok]), axis=1)
    ok &= area <= 4 * np.median(area[ok]) if ok.any() else ok  # not a step across a seam to another flat piece
    return float(area[ok].sum() * len(texels) / max(int(ok.sum()), 1))


def _laid(car, found):
    """Each mark laid on a panel (a shape, words, a placard, a picture): whole, on one piece, clear of
    another graphic's edge; a picture sharp enough; words flat and the right way up (_upright). Its
    area is measured on the car's own surface, texel by texel."""
    c = car.c
    for mark in car.skin.marks:
        name, step = car.op(mark["op"]), mark["step"]
        still = c.owner[mark["idx"]] == mark["op"]
        S, under = mark["idx"][still], mark["under"][still]
        if len(mark["idx"]) < 20:
            continue
        on = _area(c, mark["idx"])
        if on < WHOLE * mark["whole"]:
            where, z, side = car.place(mark["idx"])
            found.append({"check": "cut", "kind": "cut", "z": z, "side": side, "step": step,
                          "text": f"{name}: {on / mark['whole']:.0%} of its shape is on the car ({on:.0f} of {mark['whole']:.0f} cm²), {where}"})
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
    if cache.exists() and cache.stat().st_mtime > max(fbx.CACHE.stat().st_mtime, coverage.load(car.skin.parts, "Skin", c.w, c.h).file.stat().st_mtime):
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
    NEAR of itself on or within CLEAR cm of one."""
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
                if op != under and car.cm2[by].sum() >= max(NEAR * car.cm2[S].sum(), SPECK):
                    hits.setdefault(op, []).append(by)
        finally:
            car.mark[near] = False
        for d, sets in sorted(hits.items()):
            t = np.unique(np.concatenate(sets))
            t = t[car.open(t) >= measure.OUTER]
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
                                  f"any copy: bare patches, from {measure._place(s['z'][0])} to {measure._place(s['z'][1])}"})


def run(skin, measures=None):
    """The findings for a skin painted with Skin.measure on. measures: tool/measure.py's, when the caller has
    them."""
    found = list(skin.findings)
    measures = measure.measure(skin) if measures is None else measures
    if "Skin" in skin.canvases and skin.canvases["Skin"].owner is not None:
        car = _Car(skin)
        car.zoned_ops = {call["op"] for call in skin.zoned} | {p["op"] for p in skin.pictures + skin.marks}
        graphics = [_zoned(car, call, found) for call in skin.zoned]  # the measures' own order
        # a graphic's cuts and spills say what its run along the car would
        found += measure.findings([m for m, g in zip(measures, graphics) if not g])
        _pictures(car, found)
        _laid(car, found)
        _clear(car, found)
        _scattered(car, found)
    once = {}
    for f in found:  # a side's twin once
        f.setdefault("side", None)
        f.setdefault("z", None)
        if f["text"] in once:
            once[f["text"]]["side"] = None
        else:
            once[f["text"]] = f
    return list(once.values())


def words(found):
    """The findings as lines for Claude, by kind."""
    return [f"{f['kind']}: {f['text']}" for f in sorted(found, key=lambda f: f["kind"])]


def save(name, found):
    out = paths.BUILD / name
    out.mkdir(parents=True, exist_ok=True)
    paths.write(out / "found.json", json.dumps({"found": found}, indent=1))


def main():
    from tool import skin as skin_mod
    name = sys.argv[1]
    with skin_mod.paint_slot():
        s = skin_mod.paintbox.Skin(name)
        s.measure = True
        skin_mod.load_design(name)(s)
        s.end_steps()
    print("\n".join(words(run(s))) or "the checks name nothing")


if __name__ == "__main__":
    main()
