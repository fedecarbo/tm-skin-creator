"""How each graphic sits against the lines the eye sees on the car, said in words after each paint. The user,
2026-10-07, of a block tape that lay exactly on one of the model's lines yet looked placed "without any judgement on
the aesthetics": its gap to a panel line closed to nothing and its end stopped just short of another; they asked for
"the right tools to have better judgement or eyes (but obviously not restrict creativity)". It names, never forbids:
a graphic that crosses a line on purpose stays; the words only make sure it was seen.

For each graphic on the body (a zoned paint, a mark, words, a picture: Skin.zoned, Skin.marks, Skin.pictures, kept
while skin.show paints), its edge where it shows (the texels it covers last, Canvas.owner, next to ones it doesn't,
on the car within a texel or two), and each of the model's lines the eye sees (meshlines.lines: its crisp lines, the
panel lines and where the body ends; not a rounded edge's lines, nor where the map is cut) that comes within NEAR cm
of that edge, followed along the line every STEP cm:
  - beside it at an even gap (within EVEN cm over EVEN_RUN cm or more), or along it inside the graphic;
  - a gap that CLOSES: one that narrows steadily (LEVEL degrees or more, by a cm or more) to under CLOSE cm, a wedge
    of body between the graphic and the line;
  - NEARLY PARALLEL: a line the edge runs beside for PARALLEL_RUN cm or more at SLANT to LEAN degrees;
  - a NEAR MISS: an edge that comes within MISS cm of a line without reaching it (an end that stops just short);
  - a crossing (the graphic on both sides of the line), its angle, and a SHALLOW one (under LEAN degrees) named, as it
    reads as an accident; or its edge meeting the line (the graphic on one side only: an end on it).
And each graphic against each other graphic within NEAR_GRAPHIC cm (but one laid on another, a target's quarters on its
disc): beside it at an even gap, a gap that CLOSES, NEARLY PARALLEL, a NEAR MISS, or TOUCHES; else how near they come.
Each side of the car is measured; what both sides share is said once. Each thing said keeps where it is on the car and
which way the body faces there, for a close look at it (tool.snap --eye, from what show saves: save).

    python -m tool.eye <name>      paint the skin and print how its graphics sit
"""

import functools
import json
import sys

import numpy as np
from scipy.ndimage import minimum_filter1d
from scipy.spatial import cKDTree

from tool import meshlines, paths

NEAR = 5.0          # cm: a line further than this from a graphic's edge isn't its neighbour
STEP = 0.25         # cm along each line
LEAST = 8.0         # cm: shorter lines (a bolt head's ring, a lip) aren't followed
EVEN, EVEN_RUN = 0.5, 8.0     # cm: a gap within this over this length or more is even ...
LEVEL = 1.5         # degrees: ... and turning less than this
FIT = 0.3           # cm: a stretch of a gap changes straight within this
CLOSE = 2.0         # cm: a gap that narrows to under this ...
SLANT = 3.0         # degrees: ... by this or more closes; and an edge this far off a line is no longer parallel ...
LEAN = 12.0         # degrees: ... up to this: nearly parallel; a crossing under this is shallow
PARALLEL_RUN = 12.0  # cm beside a line before nearly parallel is said
MISS = 1.0          # cm: an edge this near a line without reaching it is a near miss
NEIGHBOUR = 0.6     # cm: texels further apart on the car than this aren't neighbours (the texture's islands)
ONE = 0.6           # cm: two lines this near are one to the eye (a groove, the gap round a piece set into the body)
PIECES = 6.0        # cm: a graphic of pieces (dashes, ticks, blocks) is read as one over gaps this long: a line out of
# it for no longer, and no further, runs between its pieces; the gap to it is the least within half of this
REACH = 2.5         # cm either side of a line where it goes into a graphic: the graphic beyond ONE cm on both sides
# crosses it, on one side only its edge meets it
SPAN = 5.0          # cm round a crossing (a soft window, this its spread: a hard one swings with where a tape's blocks
# fall in it): a graphic LONG times longer than wide there (a tape, a ruler) crosses at the angle it runs at; another
LONG = 2.0          # (a disc, a panel's colour) at the angle of its edge
NEAR_GRAPHIC = 15.0  # cm: another graphic further than this isn't a neighbour
TOUCH = meshlines.WALLS  # cm: graphics this near touch (no nearer gap shows); two calls of one step touching are one
# graphic to the eye
LAID = 0.9          # a graphic whose edge is this much against another's is laid on it (one graphic to the eye)
KIND = {"CLOSES": "sits", "NEARLY PARALLEL": "sits", "NEAR MISS": "sits", "SHALLOW": "sits", "TOUCHES": "over"}
# what each flag is among tool/record.py's KINDS, for the record's score


@functools.lru_cache(maxsize=1)
def _lines():
    """The lines the eye sees, every STEP cm: points (n, 3), the body's normal at each, which line each is on, how far
    along it, and the lines."""
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
    return P[~drop], N[~drop], ids[~drop], s[~drop], kept


def _name(L):
    what = "edge where the body ends" if L["kind"] == "opening" else "panel line" if L["walls"] > 1 else "crisp line"
    return f"the {what} along the {L['parts'][0]}"


def _place(p):
    from tool.measure import _place
    return _place(float(p[2]))


def _span(p, q):
    """From where to where along the car, front first."""
    if abs(p[2] - q[2]) <= 2:
        return _place(p)
    p, q = (p, q) if p[2] > q[2] else (q, p)
    return f"{_place(p)} to {_place(q)}"


def _graphics(skin):
    """Each graphic on the body (the wheel covers are the wheels' own design, all four one paint): its call's words,
    step and op, and what it is (the zone's or the mark's own words)."""
    covers = {i for i, inst in enumerate(skin.parts.instances) if inst["name"].startswith("wheel cover")}
    seen, out = set(), []
    for g in [*skin.zoned, *skin.marks, *skin.pictures]:
        if g["op"] in seen or (g.get("ids") and set(g["ids"]) <= covers):
            continue
        seen.add(g["op"])
        label = g["zone"].label if g.get("zone") is not None and getattr(g["zone"], "label", None) else g.get("kind", "")
        out.append({**g, "label": str(label)})
    return out


def _edge(c, op):
    """Where a call shows (the texels it covered last) and its edge there, on the car: {shown, edge: positions, nrm: the
    body's normal at each edge texel, next: the call that shows beside each}, or None."""
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
    return {"shown": c.pos[shown], "edge": c.pos[shown[edge]], "nrm": c.nrm[shown[edge]], "next": nxt[edge]}


def _runs(mask):
    """(start, end) index pairs of the runs of True."""
    d = np.diff(np.r_[0, mask.astype(np.int8), 0])
    return list(zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)))


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


def _beside(g, s, p, n, name, key, touching):
    """What a stretch of a line outside a graphic says: beside it at an even gap, a gap that closes, nearly parallel,
    a near miss (touching: the line reaches the graphic at an end of the stretch, so it isn't one). p and n: the points
    the gap is measured from and the body's normal there."""
    if s[-1] - s[0] < 2.0:
        return []
    said = []
    where = lambda a, b: _span(p[a], p[b - 1])
    for a, b, th in _stretches(g, s):
        run, g1 = s[b - 1] - s[a], g[a:b]
        if run < EVEN_RUN:
            continue
        mid, least = (a + b) // 2, a + int(np.argmin(g1))
        if th < LEVEL and g1.max() - g1.min() <= EVEN:
            said.append(("", f"beside {name}, an even {g1.mean():.1f} cm, {run:.0f} cm long, {where(a, b)}", key,
                         *_at(p[mid], n[mid], p[a:b])))
        elif th >= LEVEL and g1.max() - g1.min() >= 1.0 and g1.min() < CLOSE:
            said.append(("CLOSES", f"the gap to {name} CLOSES from {g1.max():.1f} to {g1.min():.1f} cm over {run:.0f} cm "
                         f"({th:.0f} degrees), {where(a, b)}", key, *_at(p[least], n[least], p[a:b])))
        elif run >= PARALLEL_RUN and SLANT <= th < LEAN:
            said.append(("NEARLY PARALLEL", f"NEARLY PARALLEL to {name}, {th:.0f} degrees off, {g1.min():.1f} to "
                         f"{g1.max():.1f} cm from it, {where(a, b)}", key, *_at(p[mid], n[mid], p[a:b])))
        else:
            said.append(("", f"beside {name}, {g1.min():.1f} to {g1.max():.1f} cm, {run:.0f} cm long, {where(a, b)}", key,
                         *_at(p[mid], n[mid], p[a:b])))
    m = int(np.argmin(g))
    if meshlines.WALLS < g[m] < MISS and not touching:
        said.append(("NEAR MISS", f"a NEAR MISS: its edge comes within {g[m]:.1f} cm of {name} without reaching it, "
                     f"at {_place(p[m])}", key, *_at(p[m], n[m])))
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
    """Whether a graphic lies on both sides of a stretch of line inside it (the line crosses it) rather than on one
    side (its edge meets the line): its texels within REACH cm of the stretch, beyond ONE cm on each side. p, t, n: the
    stretch's points, its direction and the body's normal there."""
    near = sorted({i for found in tree.query_ball_point(p, REACH) for i in found})
    if not near:
        return False
    q = shown[near]
    j = cKDTree(p).query(q)[1]
    across = np.einsum("ij,ij->i", q - p[j], np.cross(t[j], n[j]))
    return min((across > ONE).sum(), (across < -ONE).sum()) >= 3


def _side(G, sign):
    """What one side's lines say about one graphic: a list of (flag, words, line key, where, the body's normal)."""
    P, N, ids, S, kept = _lines()
    shown, edge = G["shown"], G["edge"]
    shown, edge = shown[shown[:, 0] * sign > -0.5], edge[edge[:, 0] * sign > -0.5]
    if len(edge) < 3:
        return []
    lo, hi = edge.min(0) - NEAR, edge.max(0) + NEAR
    box = np.flatnonzero(np.all((P >= lo) & (P <= hi), axis=1) & (P[:, 0] * sign > -0.5))
    if not len(box):
        return []
    gap = cKDTree(edge).query(P[box], distance_upper_bound=NEAR)[0]
    tree = cKDTree(shown)
    inside = np.isfinite(tree.query(P[box], distance_upper_bound=meshlines.WALLS)[0])  # in a groove's width
    said = []
    for k in np.unique(ids[box]):
        on = box[ids[box] == k]
        sel = ids[box] == k
        g, ins, s = gap[sel], inside[sel], S[on]
        order = np.argsort(s)
        g, ins, s, pts, nrm = g[order], ins[order], s[order], P[on][order], N[on][order]
        name, L = _name(kept[k]), kept[k]
        key = (name, L["kind"])
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
                if along[c0]:
                    continue
                mid = (c0 + c1) // 2
                if not _through(tree, shown, pp[c0:c1], tan[c0:c1], nn[c0:c1]):  # on one side only: an end on the line
                    said.append(("", f"its edge meets {name} at {_place(pp[mid])}", key, *_at(pp[mid], nn[mid])))
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
                        said.append(("SHALLOW", f"crosses {name} at a SHALLOW {th:.0f} degrees at {_place(pp[x])}", key,
                                     *_at(pp[x], nn[x])))
                    else:
                        said.append(("", f"crosses {name} at {th:.0f} degrees at {_place(pp[x])}", key, *_at(pp[x], nn[x])))
            for c0, c1 in _runs(~ii):  # beside it, outside the graphic
                said += _beside(gg[c0:c1], ss[c0:c1], pp[c0:c1], nn[c0:c1], name, key, touching=c0 > 0 or c1 < len(ii))
            for c0, c1 in _runs(ii):  # along it inside the graphic
                s1, p1 = ss[c0:c1], pp[c0:c1]
                if s1[-1] - s1[0] >= EVEN_RUN:
                    mid = (c0 + c1) // 2
                    said.append(("", f"lies along {name} for {s1[-1] - s1[0]:.0f} cm, {_span(p1[0], p1[-1])}", key,
                                 *_at(pp[mid], nn[mid], p1)))
    return _once(said)


def _once(said):
    """Each thing said once (the first place it was found)."""
    once = {}
    for x in said:
        once.setdefault(x[:3], x)
    return list(once.values())


def _between(A, B, name, sign):
    """What one side says about a graphic against another: beside it at an even gap, a gap that closes, nearly
    parallel, a near miss, touching, or how near they come; nothing when they're further apart than NEAR_GRAPHIC, or
    touch within one step. A list of (flag, words, key, where, the body's normal, the stretch along the car)."""
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
    if d[m] <= TOUCH:
        if A["step"] == B["step"]:
            return []
        on = np.flatnonzero(d <= TOUCH)
        q = ea[on]
        long = np.ptp((q - q.mean(0)) @ np.linalg.svd(q - q.mean(0), full_matrices=False)[2][0]) if len(q) > 1 else 0
        c = on[np.argmin(np.linalg.norm(q - q.mean(0), axis=1))]
        hi, lo = q[np.argmax(q[:, 2])], q[np.argmin(q[:, 2])]
        return [("TOUCHES", f"TOUCHES {name} over {max(long, 0.1):.1f} cm, {_span(hi, lo)}", key, *_at(ea[c], na[c], q))]
    said = []
    near = d <= NEAR
    if near.sum() >= 3:  # beside it: the gap along the edge facing it, in order along its main direction
        q, gq, nq = ea[near], d[near], na[near]
        along = (q - q.mean(0)) @ np.linalg.svd(q - q.mean(0), full_matrices=False)[2][0]
        k = ((along - along.min()) / STEP).astype(int)
        g = np.full(k.max() + 1, NEAR)
        np.minimum.at(g, k, gq)
        order = np.lexsort((gq, k))
        bins, first = np.unique(k[order], return_index=True)
        pick = np.full(len(g), -1)
        pick[bins] = order[first]  # each bin's point: its nearest; an empty bin takes the one before's
        pick = pick[np.maximum.accumulate(np.where(pick >= 0, np.arange(len(g)), 0))]
        said += _beside(g, np.arange(len(g)) * STEP, q[pick], nq[pick], name, key, touching=True)
    if MISS > d[m] > TOUCH:
        said.append(("NEAR MISS", f"a NEAR MISS: its edge comes within {d[m]:.1f} cm of {name} without touching it, at "
                     f"{_place(ea[m])}", key, *_at(ea[m], na[m])))
    if not said:
        gap = f"{d[m]:.1f}" if d[m] < NEAR else f"{d[m]:.0f}"
        said.append(("", f"{gap} cm from {name} at its nearest, {_place(ea[m])}", key, *_at(ea[m], na[m])))
    return said


def look(skin):
    """How each graphic on the body sits, numbered from 1: a list of {n, what, step, label, sides: {side: [{flag, words,
    at, nrm, z}]}} (where, which way the body faces there, the stretch along the car), each graphic against the lines,
    then against the graphics after it."""
    c = skin.canvases.get("Skin")
    if c is None or c.owner is None:
        return []
    gs = []
    for g in _graphics(skin):
        e = _edge(c, g["op"])
        if e is not None and len(e["edge"]) >= 3:
            gs.append({**g, **e})
    # one laid on another (its edge all against it: a target's quarters on its disc) is part of it to the eye
    laid = {B["op"] for B in gs for A in gs if A is not B and np.mean(B["next"] == A["op"]) >= LAID}
    out = []
    for n, A in enumerate(gs, 1):
        sides = {}
        for side, sign in (("left", 1), ("right", -1)):
            said = _side(A, sign)
            for m, B in enumerate(gs[n:], n + 1):
                if A["op"] not in laid and B["op"] not in laid:
                    said += _between(A, B, f"graphic {m} ({B['step']})", sign)
            sides[side] = [{"flag": f, "words": w, "at": at, "nrm": nrm, "z": z} for f, w, _, at, nrm, z in said]
        out.append({"n": n, "what": A["what"], "step": A["step"], "label": A["label"], "sides": sides})
    return out


def words(looks):
    """The looks as lines for Claude, a graphic at a time, what it should look at first."""
    lines = []
    for x in looks:
        said = {side: [(f["flag"], f["words"]) for f in v] for side, v in x["sides"].items() if v}
        if not said:
            continue
        lines.append(f"{x['n']}. {x['step']}: {x['what']}" + (f", {x['label']}" if x["label"] else ""))
        both = [fw for fw in said.get("left", []) if fw in said.get("right", [])]
        rank = lambda fw: (fw[0] == "", fw[1])
        lines += [f"  both sides: {w}" for _, w in sorted(both, key=rank)]
        for side in said:
            lines += [f"  {side}: {w}" for _, w in sorted([fw for fw in said[side] if fw not in both], key=rank)]
    return lines


def findings(looks):
    """What the eye flags, as tool/checks.py's findings ({check, kind, text, z, side, step}), for the record's score:
    what both sides say, once."""
    out = {}
    for x in looks:
        for side, said in x["sides"].items():
            for f in said:
                if f["flag"]:
                    text = f"{x['n']}. {x['step']}: {f['words']}"
                    if text in out:
                        out[text]["side"] = None
                    else:
                        out[text] = {"check": "eye", "kind": KIND[f["flag"]], "z": list(f["z"]), "side": side,
                                     "step": x["step"], "text": text}
    return list(out.values())


def save(name, looks):
    out = paths.BUILD / name
    out.mkdir(parents=True, exist_ok=True)
    paths.write(out / "eye.json", json.dumps({"looks": looks}, indent=1))


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    from tool import skin as skin_mod
    with skin_mod.paint_slot():
        s = skin_mod.paintbox.Skin(sys.argv[1])
        s.measure = True
        skin_mod.load_design(sys.argv[1])(s)
        s.end_steps()
    looks = look(s)
    save(sys.argv[1], looks)
    print("\n".join(words(looks)) or "no graphic near a line")


if __name__ == "__main__":
    main()
