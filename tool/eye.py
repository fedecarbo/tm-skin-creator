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
  - a crossing, its angle, and a SHALLOW one (under LEAN degrees) named, as it reads as an accident.
Each side of the car is measured; a line both sides share is said once.

    python -m tool.eye <name>      paint the skin and print how its graphics sit
"""

import functools
import sys

import numpy as np
from scipy.ndimage import minimum_filter1d
from scipy.spatial import cKDTree

from tool import meshlines

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


@functools.lru_cache(maxsize=1)
def _lines():
    """The lines the eye sees, every STEP cm: points (n, 3), which line each is on, how far along it, and the lines."""
    kept = [L for L in meshlines.lines("Skin")  # the longest first
            if L["length"] >= LEAST and not L["parts"][0].startswith("wheel cover")]
    pts, ids, s = [], [], []
    for k, L in enumerate(kept):
        P = np.vstack([L["pts"], L["pts"][:1]]) if L["closed"] else L["pts"]
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
        at = np.r_[0, np.cumsum(seg)]
        t = np.arange(0, at[-1], STEP)
        pts.append(np.stack([np.interp(t, at, P[:, i]) for i in range(3)], 1))
        ids.append(np.full(len(t), k))
        s.append(t)
    P, ids, s = np.concatenate(pts), np.concatenate(ids), np.concatenate(s)
    # where two lines run within ONE cm of each other (a groove's walls, the gap round a piece set into the body),
    # the eye sees one: the longer one's
    pairs = cKDTree(P).query_pairs(ONE, output_type="ndarray")
    a, b = pairs[:, 0], pairs[:, 1]
    other = ids[a] != ids[b]
    drop = np.zeros(len(P), bool)
    drop[np.where(ids[a] > ids[b], a, b)[other]] = True
    return P[~drop], ids[~drop], s[~drop], kept


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
    """The texels a call shows on (it covered them last) and those of them on its edge, as positions on the car."""
    shown = np.flatnonzero(c.owner == op)
    if not len(shown):
        return None, None
    edge = np.zeros(len(shown), bool)
    for d in (1, -1, c.w, -c.w):
        nb = np.clip(shown + d, 0, len(c.owner) - 1)
        other = (c.owner[nb] != op) & (c.owner[nb] != -1)
        close = np.linalg.norm(c.pos[nb] - c.pos[shown], axis=1) < NEIGHBOUR
        edge |= other & close
    return c.pos[shown], c.pos[shown[edge]]


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


def _beside(g, s, p, name, key, touching):
    """What a stretch of a line outside a graphic says: beside it at an even gap, a gap that closes, nearly parallel,
    a near miss (touching: the line reaches the graphic at an end of the stretch, so it isn't one)."""
    if s[-1] - s[0] < 2.0:
        return []
    said = []
    where = lambda a, b: _span(p[a], p[b - 1])
    for a, b, th in _stretches(g, s):
        run, g1 = s[b - 1] - s[a], g[a:b]
        if run < EVEN_RUN:
            continue
        if th < LEVEL and g1.max() - g1.min() <= EVEN:
            said.append(("", f"beside {name}, an even {g1.mean():.1f} cm, {run:.0f} cm long, {where(a, b)}", key))
        elif th >= LEVEL and g1.max() - g1.min() >= 1.0 and g1.min() < CLOSE:
            said.append(("CLOSES", f"the gap to {name} CLOSES from {g1.max():.1f} to {g1.min():.1f} cm over {run:.0f} cm "
                         f"({th:.0f} degrees), {where(a, b)}", key))
        elif run >= PARALLEL_RUN and SLANT <= th < LEAN:
            said.append(("NEARLY PARALLEL", f"NEARLY PARALLEL to {name}, {th:.0f} degrees off, {g1.min():.1f} to "
                         f"{g1.max():.1f} cm from it, {where(a, b)}", key))
        else:
            said.append(("", f"beside {name}, {g1.min():.1f} to {g1.max():.1f} cm, {run:.0f} cm long, {where(a, b)}", key))
    m = int(np.argmin(g))
    if meshlines.WALLS < g[m] < MISS and not touching:
        said.append(("NEAR MISS", f"a NEAR MISS: its edge comes within {g[m]:.1f} cm of {name} without reaching it, "
                     f"at {_place(p[m])}", key))
    return said


def _crossing(g, s):
    """Degrees between a line and a graphic's edge where it crosses, from how fast the gap changes across it."""
    if len(g) < 3 or s[-1] - s[0] < 1.0:
        return 90.0
    return float(np.degrees(np.arcsin(min(1.0, abs(np.polyfit(s, g, 1)[0])))))


def _side(shown, edge, sign):
    """What one side's lines say about one graphic: a list of (flag, words, line key)."""
    P, ids, S, kept = _lines()
    keep = shown[:, 0] * sign > -0.5
    shown, edge = shown[keep], edge[edge[:, 0] * sign > -0.5]
    if len(edge) < 3:
        return []
    lo, hi = edge.min(0) - NEAR, edge.max(0) + NEAR
    box = np.flatnonzero(np.all((P >= lo) & (P <= hi), axis=1) & (P[:, 0] * sign > -0.5))
    if not len(box):
        return []
    gap = cKDTree(edge).query(P[box], distance_upper_bound=NEAR)[0]
    inside = np.isfinite(cKDTree(shown).query(P[box], distance_upper_bound=meshlines.WALLS)[0])  # in a groove's width
    said = []
    for k in np.unique(ids[box]):
        on = box[ids[box] == k]
        sel = ids[box] == k
        g, ins, s = gap[sel], inside[sel], S[on]
        order = np.argsort(s)
        g, ins, s, pts = g[order], ins[order], s[order], P[on][order]
        name, L = _name(kept[k]), kept[k]
        key = (name, L["kind"])
        for a, b in _runs(np.isfinite(g) | ins):
            if s[b - 1] - s[a] < 2.0:
                continue
            gg, ii, ss, pp = g[a:b], ins[a:b].copy(), s[a:b], pts[a:b]
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
                if raw[c0:c1].max() <= ONE:  # no deeper into it than a groove: its edge (an end) lies on the line
                    said.append(("", f"its edge meets {name} at {_place(pp[(c0 + c1) // 2])}", key))
                    continue
                for x in (c0 - 1, c1 - 1):  # where the line goes in and where it comes out
                    if x < 0 or x + 1 >= len(ii):
                        continue
                    w = slice(max(0, x - 8), min(len(ss), x + 10))
                    th = _crossing(np.where(ii[w], -raw[w], raw[w]), ss[w])
                    if th < LEAN:
                        said.append(("SHALLOW", f"crosses {name} at a SHALLOW {th:.0f} degrees at {_place(pp[x])}", key))
                    else:
                        said.append(("", f"crosses {name} at {th:.0f} degrees at {_place(pp[x])}", key))
            for c0, c1 in _runs(~ii):  # beside it, outside the graphic
                said += _beside(gg[c0:c1], ss[c0:c1], pp[c0:c1], name, key, touching=c0 > 0 or c1 < len(ii))
            for c0, c1 in _runs(ii):  # along it inside the graphic
                s1, p1 = ss[c0:c1], pp[c0:c1]
                if s1[-1] - s1[0] >= EVEN_RUN:
                    said.append(("", f"lies along {name} for {s1[-1] - s1[0]:.0f} cm, {_span(p1[0], p1[-1])}", key))
    return list(dict.fromkeys(said))


def look(skin):
    """How each graphic on the body sits: a list of {what, step, sides: {side: [(flag, words)]}}."""
    c = skin.canvases.get("Skin")
    if c is None or c.owner is None:
        return []
    out = []
    for g in _graphics(skin):
        shown, edge = _edge(c, g["op"])
        if shown is None or len(edge) < 3:
            continue
        sides = {side: _side(shown, edge, sign) for side, sign in (("left", 1), ("right", -1))}
        out.append({"what": g["what"], "step": g["step"], "label": g["label"], "sides": sides})
    return out


def words(looks):
    """The looks as lines for Claude, a graphic at a time, what it should look at first."""
    lines = []
    for x in looks:
        said = {side: [(f, w) for f, w, _ in v] for side, v in x["sides"].items() if v}
        if not said:
            continue
        lines.append(f"{x['step']}: {x['what']}" + (f", {x['label']}" if x["label"] else ""))
        both = [fw for fw in said.get("left", []) if fw in said.get("right", [])]
        rank = lambda fw: (fw[0] == "", fw[1])
        lines += [f"  both sides: {w}" for _, w in sorted(both, key=rank)]
        for side in said:
            lines += [f"  {side}: {w}" for _, w in sorted([fw for fw in said[side] if fw not in both], key=rank)]
    return lines


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    from tool import skin as skin_mod
    s = skin_mod.paintbox.Skin(sys.argv[1])
    s.measure = True
    skin_mod.load_design(sys.argv[1])(s)
    s.end_steps()
    print("\n".join(words(look(s))) or "no graphic near a line")


if __name__ == "__main__":
    main()
