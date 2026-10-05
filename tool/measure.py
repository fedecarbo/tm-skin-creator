"""How far each zoned paint on the body really reaches, measured on the car before anyone looks.
The user, 2026-10-02: "if the
intention is to do X, then you receive X"; a line meant to run to the back "didn't cover the rear,
as in the farthest back of the side of the car".

For each paint with a zone on the body (Skin.zoned, kept while skin.show paints), on each side,
the run: from where to where along the car the paint shows, in cm (z, with the station's name).
For a paint that runs along the car (RUN times longer than it's high: a band, a stripe, an edge):
  - each end: how far along the car the bare body goes on past it at the paint's own height (in
    three slices of it: a band's lower edge can stop before its upper one), on the outside of the
    body (shapes.outside, OUTER), followed over the surface texel to texel while it faces within 75
    degrees of the paint's end (round the corner where the side turns onto the back, not across
    the back), until the surface stops: the body's end, or an opening. An end SHORT cm or more
    short names what ends it: one of the zone's parts (shapes.Zone.parts) leaving the rest out, or
    a later call covering it (Canvas.owner). Only a reading of the car (READINGS: the map's areas,
    its open air, its lines) makes a shortfall: a length, a height, a box or a pattern ends a paint
    where the design wrote it. Past an opening the body at the paint's height can resume (behind
    the rear wheel, the farthest back of the side): the first stretch of it within FAR cm, bare, is
    said too, unless the design ends the paint there (TSC_Snow's band ends at the sidepods);
  - the gaps: stretches of GAP cm or more inside the run where the body is there at the paint's
    height and less than half of it shows the paint, with what left them out or covered them.
A line both sides share is said once; the two sides' own lines show where they differ.
Measured on the texels themselves, by their baked positions on the car, never on a picture. What
it doesn't follow: a peel or wear over the paint (they don't cover it), a paint thinner than half
(blend), and lines drawn on the skin, which follow their own course: tool/skincheck.py measures them.

    python -m tool.measure <name>      paint the skin and print its measures
"""

import json
import sys

import numpy as np
from scipy.spatial import cKDTree

from tool import carmap, coverage, paths, shapes

BIN = 0.5  # cm along the car
SHORT = 1.0  # cm: an end that stops this short of the body
GAP = 1.0  # cm: a stretch inside a run with too little of the paint showing
REACH = 40.0  # cm round an end that the body is followed
STEP = 1.0  # cm between texels that count as joined (they're 0.1 to 0.3 cm apart): a seam joins, an opening doesn't
OUTER = 0.1  # the open air a spot sees to count as the outside: an opening's insides see about 0.01, the
# flanks behind the wheels (the wheel covers shade them) 0.2 to 0.35, the sidepods nearly all of it
THIN = 0.2  # cm: the cells the joins are worked out on
EDGE = 1.5  # cm past a paint's end: the bare body whose zone parts say what ended it
FAR = 60.0  # cm past an end that the body is looked for past an opening (the rear wheel's is about 30)
OPENING = 3.0  # cm along the car with no body at a paint's height: an opening it can't follow across
ACROSS = 3.0  # cm along the car: body past an opening at a paint's height, long enough to count
RUN = 3  # a paint runs along the car when it's at least this many times longer than it's high
FACING = 0.25  # the bare body followed past an end faces within 75 degrees of the paint's end: a band
# along the side runs on round the rounded corner to where the surface faces the back
READINGS = ("area", "outside", "near", "line", "region", "sides", "facing")  # zones whose edges are the car's,
# read off its mesh: the rest (a length, a height, a box, a pattern) end a paint where the design wrote it


def _place(z):
    stations = np.array([s for s, _ in carmap.STATIONS], float)
    k = int(np.argmin(np.abs(stations - z)))
    name = carmap.STATIONS[k][1] if abs(stations[k] - z) <= 12 else None
    return f"z {z:+.0f}" + (f" ({name})" if name else "")


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
            self.outer[ask] = shapes.outside(OUTER)(self.c.pos[t], self.c.nrm[t]) > 0.5
        return k[self.outer[k] == 1]


def _beyond(end_pts, bare_pts):
    """The bare texels joined to the paint's end over the surface (texel to texel, STEP cm apart at
    most): what lies on past the end, round a corner too."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    if not len(bare_pts) or not len(end_pts):
        return np.zeros(0, int)
    end_pts = _thin(end_pts)
    bare_cell, bare_back = np.unique(_cells(bare_pts), return_inverse=True)
    bare_one = np.zeros(len(bare_cell), int)
    bare_one[bare_back.ravel()] = np.arange(len(bare_pts))  # a texel for each cell
    pts = np.concatenate([end_pts, bare_pts[bare_one]]).astype(np.float64)
    pairs = cKDTree(pts).query_pairs(STEP, output_type="ndarray")
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


def _why(skin, call, texels, aimed):
    """What leaves these texels without the paint: (words, as_written). aimed: a flag per texel,
    the zone reached it."""
    c = skin.canvases["Skin"]
    mine = aimed[texels]
    if mine.mean() >= 0.5:  # the zone reached them: a later call covers them
        owners = c.owner[texels[mine]]
        owners = owners[owners != call["op"]]
        if len(owners):
            op = int(np.bincount(owners - owners.min()).argmax() + owners.min())
            return f"covered by {skin.ops[op]['what']} ({skin.ops[op]['step']})", False
        return "covered", False
    pos, nrm = c.pos[texels], c.nrm[texels]
    out = [f for f in call["zone"].parts() if (f(pos, nrm) < 0.5).mean() >= 0.5]
    if not out:
        return "left out by the zone as a whole", False
    written = not any(repr(f).lstrip("~(").split("(")[0] in READINGS for f in out)
    return ("ends where " if written else "left out by ") + " & ".join(map(repr, out)), written


def _side(skin, call, body, shown, showing, aimed, sign):
    """One side's run, ends and gaps. showing: a flag per texel, the paint shows there; aimed: the
    zone reached it."""
    c = skin.canvases["Skin"]
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
            # the end, OPENING cm or more with none of it, then ACROSS cm or more of it
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
                if long >= ACROSS and long > (worst.get("across") or {}).get("long", 0):
                    inside = (on >= r0 * BIN) & (on < r1 * BIN)
                    worst["across"] = {"from": zend + d * r0 * BIN, "to": zend + d * r1 * BIN, "long": long,
                                       "height": [a, b], "texels": far[inside]}
                break
        if worst["short"] >= SHORT:
            worst["why"], worst["as_written"] = _why(skin, call, body.texels[worst["edge"]], aimed)
        worst.pop("edge", None)
        if worst.get("across"):
            x = worst["across"]
            x["why"], x["as_written"] = _why(skin, call, body.texels[x.pop("texels")], aimed)
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
        why, written = _why(skin, call, body.texels[hole], aimed)
        out["gaps"].append({"from": (b0 + g1) * BIN, "to": (b0 + g0) * BIN, "why": why, "as_written": written})
    return out


def measure(skin):
    """The measures of every zoned paint on the body: a list of {what, step, zone, sides}."""
    if "Skin" not in skin.canvases or not skin.zoned or skin.canvases["Skin"].owner is None:
        return []
    c = skin.canvases["Skin"]
    cov = coverage.load(skin.parts, "Skin", c.w, c.h)
    bodies, out = {}, []
    shapes.PAINTING = "Skin"
    try:
        for call in skin.zoned:
            if getattr(call["zone"], "curve", None) is not None:
                continue  # a line drawn on the skin: tool/skincheck.py
            key = tuple(call["ids"])
            if key not in bodies:
                bodies[key] = _Body(c, np.flatnonzero(cov.share(call["ids"]).reshape(-1) > 0.5))
            idx = call["idx"]
            shown = idx[c.owner[idx] == call["op"]]
            showing = np.zeros(c.w * c.h, bool)
            showing[shown] = True
            aimed = np.zeros(c.w * c.h, bool)
            aimed[idx] = True
            sides = {side: _side(skin, call, bodies[key], shown, showing, aimed, sign) for side, sign in (("left", 1), ("right", -1))}
            out.append({"what": call["what"], "step": call["step"], "zone": repr(call["zone"]), "sides": sides})
    finally:
        shapes.PAINTING = None
    return out


def words(measures):
    """The measures as lines for Claude, a paint at a time: its run per side, then what stops short.
    A line both sides share is said once."""
    lines = []
    for m in measures:
        sides = {k: v for k, v in m["sides"].items() if v}
        if not sides:
            continue
        said = {}
        for side, s in sides.items():
            said[side] = [f"from {_place(s['front'])} to {_place(s['rear'])}"]
            for end, e in s["ends"].items():
                x = e.get("across")
                if x and not x["as_written"]:
                    up = f"{x['height'][0]:.0f} to {x['height'][1]:.0f} cm up"
                    said[side].append(f"{end} end STOPS SHORT past an opening: at {up} the body goes on, BARE, from "
                                      f"{_place(x['from'])} to {_place(x['to'])}; {x['why']}")
                if e["short"] < SHORT or e["as_written"]:
                    continue
                at = f"{e['height'][0]:.0f} to {e['height'][1]:.0f} cm up"
                much = f"{e['short']:.0f} cm" if e["short"] < REACH - BIN else f"{REACH:.0f} cm or more"
                said[side].append(f"{end} end STOPS {much} SHORT: at {at} the bare body goes on to "
                                  f"{_place(e['body'])}; {e['why']}")
            said[side] += [f"GAP of {g['from'] - g['to']:.0f} cm from {_place(g['from'])} to {_place(g['to'])}: {g['why']}"
                           for g in s["gaps"] if not g["as_written"]]
        lines.append(f"{m['step']}: {m['what']}, zone {m['zone']}")
        if len(sides) == 1:
            lines.append(f"  only on the {next(iter(sides))} side")
        both = [x for x in said.get("left", []) if x in said.get("right", [])]
        lines += [f"  both sides: {x}" for x in both]
        for side in sides:
            lines += [f"  {side}: {x}" for x in said[side] if x not in both]
    return lines


def findings(measures):
    """What the measures say is wrong, as tool/checks.py's findings: an end that stops short, a gap."""
    found = []
    for m in measures:
        for side, r in m["sides"].items():
            if not r:
                continue
            said = {"check": "measure", "side": side, "step": m["step"]}
            for end, e in r["ends"].items():
                x = e.get("across")
                if x and not x["as_written"]:
                    found.append({**said, "kind": "short", "z": [x["from"], x["to"]],
                                  "text": f"{m['step']}: {m['what']}, {end} end, bare past an opening"})
                if e["short"] >= SHORT and not e["as_written"]:
                    found.append({**said, "kind": "short", "z": [r[end], e["body"]],
                                  "text": f"{m['step']}: {m['what']}, {end} end {e['short']:.0f} cm short"})
            found += [{**said, "kind": "gap", "z": [g["from"], g["to"]],
                       "text": f"{m['step']}: {m['what']}, a gap of {g['from'] - g['to']:.0f} cm"}
                      for g in r["gaps"] if not g["as_written"]]
    return found


def save(name, measures):
    out = paths.BUILD / name
    out.mkdir(parents=True, exist_ok=True)
    paths.write(out / "measured.json", json.dumps(measures, indent=1))


def main():
    from tool import skin as skin_mod
    name = sys.argv[1]
    with skin_mod.paint_slot():
        s = skin_mod.paintbox.Skin(name)
        s.measure = True
        skin_mod.load_design(name)(s)
    found = measure(s)
    print("\n".join(words(found)) or "nothing zoned on the body")


if __name__ == "__main__":
    main()
