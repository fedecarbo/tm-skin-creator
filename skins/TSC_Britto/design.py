"""TSC_Britto: Romero Britto's pop art made of the car's own parts, its two sides unlike, as Britto paints a face's two
halves: each part its own colour and pattern, and on the right side each of the side's parts another colour or pattern
than its twin on the left; a black stroke along every part's edges (centred on a seam, inside an edge it ends at)
and along the inner car's frames where they lie on the body; the plates the game letters on a plain panel; the inner car's parts
each a solid colour.
All of it gloss, the tyres black rubber, the glass clear, every light its own colour of the palette, and no dirt ever:
it stays new."""

import functools

import numpy as np
from PIL import Image
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

from tool import course, fbx, parts, shapes
from tool.noise import smoothstep

RED, YELLOW, BLUE, ORANGE, GREEN, PURPLE = "#e4202d", "#ffd21f", "#1f5fd1", "#ff7f1f", "#2bb24c", "#7d3ec1"
BLACK, WHITE = "#111111", "#ffffff"
LINE = 2.5   # cm: the black line's width (the language's 2.5 cm round the big sections)
GAP = 2.5    # cm: two parts' edges this close meet (a sewn-on piece's gap)
TUCKED = 0.1  # an edge seeing this much less of the open air than the one it meets is tucked under it
STUB = 15.0  # cm: an edge loop shorter than this (a fastener's hole) gets no line
TAPER = 3.0  # cm: an edge's line widens from a seam's half of LINE to the whole over this, beside the seam
CLEAR = 3.0  # cm the lines keep off the deck's plates the game letters
DECK = ("number panel", "engine cover panel")
LABEL = 28.5  # cm off the middle: the deck's plain panel, the rear quarter panels' inner edges carried on to the tail
LABEL_Z = (-84.5, -131.0)  # the quarter panels' back corners, and past the tail panel's seam
BOLTS = (0.5440, 0.4781, 0.5509, 0.4959)  # the inner car's map: the one patch every bolt shares (u, v from, to)
LEAN = 0.47  # stripes lean forward 25 degrees

# each part of the body (the mirror mount shares the body shell's paint): its colour, its pattern and the pattern's
# colour ("plain": none)
PLAN = {
    "body shell": (BLUE, "checks", WHITE),
    "nose tip": (RED, "dots", WHITE),
    "nose panel": (YELLOW, "stripes", ORANGE),
    "wing pylon": (GREEN, "plain", None),
    "side skirt|left": (PURPLE, "dots", YELLOW),
    "side skirt|right": (YELLOW, "dots", PURPLE),
    "cockpit surround": (YELLOW, "plain", None),
    "sidepod top|left": (YELLOW, "hearts", RED),
    "sidepod top|right": (RED, "hearts", YELLOW),
    "sidepod inlet|left": (RED, "stripes", WHITE),
    "sidepod inlet|right": (BLUE, "stripes", YELLOW),
    "rear flank|left": (ORANGE, "dots", WHITE),
    "rear flank|right": (PURPLE, "dots", WHITE),
    "rear quarter panel|left": (PURPLE, "small dots", YELLOW),
    "rear quarter panel|right": (ORANGE, "small dots", WHITE),
    "fuel cap": (GREEN, "plain", None),
    "engine cover|part": (GREEN, "waves", YELLOW),
    "tail corner|left": (PURPLE, "checks", WHITE),
    "tail corner|right": (ORANGE, "checks", WHITE),
    "tail panel": (RED, "stripes", WHITE),
    "diffuser": (PURPLE, "plain", None),
    "diffuser strake": (YELLOW, "plain", None),
}
PLATES = {"nose fin": BLUE, "number panel": GREEN, "engine cover panel": GREEN}  # one plain paint each, the colour round them
UNDER = ("diffuser", "diffuser strake", "wing pylon")  # under the car and behind the front wing: no line
INSIDE = ("sidepod inlet",)  # seen through the inlet's mouth, though the open air is low in there
RING = -3.0  # z where the ring round each inlet's mouth ends at the bottom (the sidepod top meets the frame at -1 to -4)
LOW = 32.0  # cm up: the foot of the sidepod, where the frame shows above the skirt
WHEELS = {"wheel cover disc": (RED, "dots", WHITE), "wheel cover ring": (YELLOW, "plain", None),
          "wheel cover hub": (BLUE, "plain", None)}
INNER = {  # the inner car's parts seen from outside, each a solid colour
    "front wing": RED, "front wing endplate": YELLOW, "upper wishbone": BLUE, "lower wishbone": ORANGE,
    "pushrod": GREEN, "tie rod": PURPLE, "upright": YELLOW, "upright cover": RED, "rear arm": ORANGE,
    "mirror": RED, "mirror arm": PURPLE, "sidepod frame": GREEN, "sidepod panel": RED, "sidepod strut": YELLOW,
    "side vane": BLUE, "side vent": ORANGE, "exhaust": GREEN, "rear bumper": PURPLE, "rear bumper corner": YELLOW,
    "rear strake": RED, "tail frame": BLUE, "cockpit rim": ORANGE, "seat": RED, "steering wheel": BLUE,
    "airbox": YELLOW, "wing bracket": GREEN, "brake caliper": RED, "rim": YELLOW, "hub": PURPLE,
}
# the car's own lights, each its own colour, none the stock's, at full colour: the speed numbers, the gear bar along
# the tail's top (in the blue tail frame), the slots inside the front wheels, the lamps on the front wing (night only)
LIGHTS = {"speed numbers": YELLOW, "rear lights": GREEN, "brake lights": PURPLE, "front wing": YELLOW}
# the ring round each wheel and the inner car's parts that carry a light of their own (strips, lamps, the cockpit's
# glow), each lit in a colour of the palette that isn't its paint, at the stock brightness
LIT = {
    "wheel ring": ORANGE, "hub": ORANGE, "rear bumper": YELLOW, "side vane": ORANGE, "exhaust": YELLOW,
    "sidepod panel": YELLOW, "sidepod frame": YELLOW, "sidepod strut": ORANGE, "sidepod boss": YELLOW,
    "sidepod grille plate": YELLOW, "airbox": ORANGE, "tie rod": YELLOW, "steering wheel": ORANGE,
    "steering column": ORANGE, "upper wishbone": ORANGE, "front bulkhead": PURPLE, "floor rail": PURPLE,
    "cockpit tub": GREEN, "nose inner": GREEN,  # these two share their paint
}


@functools.cache
def skin():
    """The body's skin, a triangle drawn twice once: its triangles (welded corners), corners, part names, each
    triangle's part (an index into them) and facing."""
    P = parts.load()
    m = fbx.meshes()["Skin_01"]
    tv, pos = m["tri_vertex"], m["positions"].astype(np.float64)
    off = P.mesh_offset["Skin"]
    name = np.array([P.instances[int(i)]["name"] for i in P.tri_part[off:off + len(tv)]])
    _, weld = np.unique(np.round(pos, 2), axis=0, return_inverse=True)
    weld = weld.reshape(-1)
    V = np.zeros((weld.max() + 1, 3))
    V[weld] = pos
    tri, first = np.unique(np.sort(weld[tv], axis=1), axis=0, return_index=True)
    words, code = np.unique(name[first], return_inverse=True)
    facing = m["tri_normal"][first].mean(1)
    return tri, V, words, code, facing / (np.linalg.norm(facing, axis=1, keepdims=True) + 1e-9)


@functools.cache
def deck_points():
    """The deck's plates' edges, points every 0.2 cm: the lines keep CLEAR cm off them."""
    tri, V, words, code, _ = skin()
    e, _ = _edges(tri, np.isin(words[code], DECK))
    return _points(V, e)[0]


def label_lines():
    """The deck's plain panel's sides: a line each side from the rear quarter panel's back corner straight back to the
    tail panel's seam, LABEL cm off the middle: the deck's skin seen from above, straight down onto it."""
    tri, V, *_ = skin()
    T = V[tri]
    up = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])[:, 1]
    out = []
    for x, side in ((LABEL, "left"), (-LABEL, "right")):
        pts = []
        for z in np.arange(LABEL_Z[0], LABEL_Z[1], -0.25):
            a, b, c = (T[:, k][:, [0, 2]] - [x, z] for k in range(3))
            d = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
            u = (a[:, 1] * c[:, 0] - a[:, 0] * c[:, 1]) / np.where(d == 0, np.inf, d)
            v = (a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]) / np.where(d == 0, np.inf, d)
            on = (u >= 0) & (v >= 0) & (u + v <= 1) & (up != 0)
            if on.any():
                y = (1 - u - v) * T[:, 0, 1] + u * T[:, 1, 1] + v * T[:, 2, 1]
                pts.append((x, float(y[on].max()), z))
        out.append(course.Course(pts, f"the deck's panel's {side} side"))
    return course.Courses(out, "the deck's panel's sides")


def exactly(pos, label):
    """The texels at these baked places of the inner car's map, and no others."""
    tree = cKDTree(pos)
    return shapes.Zone(lambda p, n: (tree.query(p, distance_upper_bound=1e-3, workers=-1)[0] < 1e-3)
                       .astype(np.float32), label=label)


@functools.cache
def bolts():
    """Every bolt of the inner car: the patch of its map they all share (BOLTS), as its texels' baked places."""
    from tool import bake
    b = bake.bake("Details", 4096, 4096)
    u0, v0, u1, v1 = BOLTS
    rows = slice(int((1 - v1) * 4096), int(np.ceil((1 - v0) * 4096)))
    cols = slice(int(u0 * 4096), int(np.ceil(u1 * 4096)))
    pos = b["position"][rows, cols].reshape(-1, 3).astype(np.float64)
    return pos[np.abs(pos).sum(1) > 0]


@functools.cache
def under_body(part, reach=25.0):
    """The triangles of an inner part the body covers (a ray out along the triangle's facing meets the body's skin
    within reach cm): their middles, facings, and which are covered."""
    M, P = fbx.meshes(), parts.load()
    m = M["Details_01"]
    tv, pos = m["tri_vertex"], m["positions"].astype(np.float64)
    off = P.mesh_offset["Details"]
    mine = np.flatnonzero([P.instances[int(i)]["name"] == part for i in P.tri_part[off:off + len(tv)]])
    C, N = pos[tv[mine]].mean(1), m["tri_normal"][mine].mean(1)
    N = N / (np.linalg.norm(N, axis=1, keepdims=True) + 1e-9)
    tri, V, *_ = skin()
    S = V[tri]
    tree = cKDTree(S.mean(1))
    hid = np.zeros(len(C), bool)
    for k, (o, d) in enumerate(zip(C + N * 0.05, N)):
        near_ = tree.query_ball_point(o + d * reach / 2, reach / 2 + 6)
        if not near_:
            continue
        a, b, c = S[near_, 0], S[near_, 1], S[near_, 2]
        e1, e2 = b - a, c - a
        h = np.cross(d, e2)
        det = (e1 * h).sum(1)
        inv = 1 / np.where(np.abs(det) > 1e-9, det, np.inf)
        w = o - a
        u, q = (w * h).sum(1) * inv, np.cross(w, e1)
        v, t = (q @ d) * inv, (e2 * q).sum(1) * inv
        hid[k] = np.any((u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0) & (t < reach))
    return C, N, hid


def covered(part, label):
    """Where the body covers an inner part (under_body): each texel by the nearest of its triangles facing its way."""
    C, N, hid = under_body(part)
    tree = cKDTree(C)

    def f(p, n):
        d, j = tree.query(p.astype(np.float64), k=4, workers=-1)
        agree = np.einsum("ikc,ic->ik", N[j], n.astype(np.float64)) > 0.3
        first = np.where(agree.any(1), agree.argmax(1), 0)
        k = np.arange(len(p))
        return (hid[j[k, first]] & (d[k, first] < 3.0)).astype(np.float32)  # a texel the part shares lies elsewhere
    return shapes.Zone(f, label=label)


@functools.cache
def loops(keys):
    """Every edge loop of the named parts (PLAN's keys: "rear flank|left"), each a course along the car's own edge
    (course.edge: the part on its left as it runs, seen from outside), a loop under STUB cm left out: (key, course)."""
    tri, V, words, code, _ = skin()
    out = []
    for key in keys:
        part, _, side = key.partition("|")
        side = side if side in ("left", "right") else None
        p = _points(V, _edges(tri, words[code] == part)[0])[0]
        if side:
            p = p[(p[:, 0] > 0) == (side == "left")]
        _, comp = connected_components(cKDTree(p).sparse_distance_matrix(cKDTree(p), 0.3), directed=False)
        found = []
        for c in np.unique(comp):
            q = p[comp == c]
            if len(q) * 0.2 < STUB:
                continue
            loop = course.edge(part, side=side, near=q[len(q) // 2])
            if loop.length >= STUB and not any(np.allclose(loop.pts[0], o.pts[0]) for o in found):
                found.append(loop)
                out.append((key, loop))
    return out


def outline(keys, label):
    """The black outline of the named parts, LINE wide, along their every edge: each edge loop whole and unbroken, a
    band inside the part measured across the car's surface (tool/course.py), half of LINE (a seam's line is two parts'
    halves), LINE along an edge none of them meets (an opening, the inner car's frames, the body's own edges, the
    plates); and on a seam where one piece lies over another, the line centred on the edge the eye sees (the one seeing
    TUCKED more of the open air), over the tucked piece where it comes out from under (a dense line along one edge: a
    stroke, not dabs). A free edge running on from a seam widens to LINE over TAPER cm, so the line never jogs."""
    from tool import carmap
    L = loops(tuple(keys))
    P = np.vstack([c.pts for _, c in L])
    who = np.concatenate([[key] * len(c.pts) for key, c in L])
    air = np.concatenate([carmap.load().value("open", c.pts, c.nrm) for _, c in L])
    best = np.full(len(P), -1.0)
    for i, nb in enumerate(cKDTree(P).query_ball_point(P, GAP)):
        them = [j for j in nb if who[j] != who[i]]
        if them:
            best[i] = air[them].max()
    kind = np.where(best < 0, 0, np.where(air < best - TUCKED, 2, 1))  # 0 free, 1 a seam, 2 tucked under
    free, at = {}, 0
    for _, c in L:
        run = stretches(c, kind[at:at + len(c.pts)])
        for m, (j, piece, _) in enumerate(run):
            if j != 0 or len(run) == 1:
                continue
            after_seam = (m > 0 or c.closed) and run[m - 1][0] != 0
            before_seam = (m + 1 < len(run) or c.closed) and run[(m + 1) % len(run)][0] != 0
            for w, p in widened(piece, after_seam, before_seam):
                free.setdefault(w, []).append(p)
        if len(run) == 1 and run[0][0] == 0:
            free.setdefault(LINE, []).append(c)
        at += len(c.pts)
    seen = (kind == 1) & (cKDTree(P[kind == 2]).query(P, workers=-1)[0] < GAP if (kind == 2).any() else False)
    zone = course.Courses([c for _, c in L], f"the edges of {label}").band(LINE / 2, side=1)
    for w, pieces in sorted(free.items()):
        zone = zone | course.Courses(pieces, f"the free edges of {label}").band(w, side=1)
    if seen.any():
        zone = zone | near(P[seen], LINE / 2, f"the seams of {label} where one piece lies over another")
    return zone


def widened(piece, start, end, steps=6):
    """A free edge's line: LINE wide, and within TAPER cm of an end that runs on from a seam (start, end) widening
    from the seam's half of LINE in `steps` steps, each under the least step the judge sees: (width, course) each, the
    steps overlapping by a point."""
    from tool.course import STEP
    n = len(piece.pts)
    t = min(int(round(TAPER / STEP)), (n - 1) // (2 if start and end else 1))
    lo, hi = (t if start else 0), (n - 1 - t if end else n - 1)
    out = [(LINE, piece.between(piece.pts[lo], piece.pts[hi]))] if hi - lo >= 1 else []
    cut = np.linspace(0, t, steps + 1).round().astype(int)
    for k in range(steps):
        a, b = int(cut[k]), min(int(cut[k + 1]) + 1, n - 1)
        if b - a < 1:
            continue
        w = round(LINE / 2 * (1 + (k + 1) / (steps + 1)), 3)
        if start:
            out.append((w, piece.between(piece.pts[a], piece.pts[b])))
        if end:
            out.append((w, piece.between(piece.pts[n - 1 - b], piece.pts[n - 1 - a])))
    return out


def stretches(c, kind, least=1.5):
    """A course cut where its points' kind changes, a stretch under `least` cm taking the kind before it: (kind,
    piece, its points' indices) each, the pieces meeting end to end; a loop all of one kind whole."""
    from tool.course import STEP
    kind, n = kind.copy(), len(kind)

    def runs_of(kind):
        cut = np.flatnonzero(kind != np.roll(kind, 1)) if c.closed else np.flatnonzero(np.r_[True, kind[1:] != kind[:-1]])
        return cut, (np.r_[cut[1:], cut[0] + n] if c.closed else np.r_[cut[1:], n]) if len(cut) else cut

    for _ in range(3):
        cut, ends = runs_of(kind)
        short = [(a, b) for a, b in zip(cut, ends) if (b - a) * STEP < least] if len(cut) > 1 else []
        for a, b in short:
            kind[np.arange(a, b) % n] = kind[(a - 1) % n]
    cut, ends = runs_of(kind)
    if not len(cut):
        return [(int(kind[0]), c, np.arange(n))]
    out = []
    for a, b in zip(cut, ends):
        j = b % n if c.closed else min(b, n - 1)
        if j != a:
            out.append((int(kind[a]), c.between(c.pts[a], c.pts[j]), np.arange(a, b + 1) % n))
    return out


def paths(pts, least=10.0, every=1.0):
    """Points along curves (every 0.2 cm) as courses on the car: each stretch at least `least` cm long walked from
    its end, always on to the nearest point not yet passed, a point every `every` cm, cut where the walk jumps."""
    _, piece = connected_components(cKDTree(pts).sparse_distance_matrix(cKDTree(pts), 0.5), directed=False)
    out = []
    for c in np.unique(piece):
        q = pts[piece == c]
        if len(q) * 0.2 < least:
            continue
        here = int(np.argmax(np.linalg.norm(q - q.mean(0), axis=1)))
        left, walk = np.ones(len(q), bool), [here]
        left[here] = False
        while left.any():
            d = np.where(left, np.linalg.norm(q - q[here], axis=1), np.inf)
            here = int(np.argmin(d))
            left[here] = False
            walk.append(here)
        w = q[walk]
        jump = np.flatnonzero(np.linalg.norm(np.diff(w, axis=0), axis=1) > 2.0) + 1
        for seg in np.split(w, jump):
            s_ = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(seg, axis=0), axis=1))]
            if s_[-1] >= least:
                keep = np.searchsorted(s_, np.arange(0.0, s_[-1], every))
                out.append(course.points(np.vstack([seg[keep], seg[-1:]]), "an inner part's edge on the body"))
    return out


def runs(pts, cm):
    """Which points (every 0.2 cm along lines) lie on a stretch at least `cm` long: a shorter one reads as a dab."""
    _, piece = connected_components(cKDTree(pts).sparse_distance_matrix(cKDTree(pts), 0.5), directed=False)
    return np.bincount(piece)[piece] >= cm / 0.2


def _sample(tri, V, mask, per, seed):
    """Points spread over the masked triangles, per a cm², and the triangle each lies on."""
    idx = np.flatnonzero(mask)
    T = V[tri[idx]]
    area = 0.5 * np.linalg.norm(np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]), axis=1)
    k = np.random.default_rng(seed).poisson(area * per) + 1
    r = np.repeat(np.arange(len(idx)), k)
    w = np.random.default_rng(seed + 1).dirichlet([1, 1, 1], size=len(r))
    return np.einsum("kj,kjc->kc", w, T[r]), idx[r]


def _edges(tri, mask):
    """The open edges of the masked triangles (an edge only one of them has), as points every 0.2 cm, and the
    triangle each is on."""
    idx = np.flatnonzero(mask)
    t = tri[idx]
    e = np.sort(np.concatenate([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), axis=1)
    _, inv, many = np.unique(e, axis=0, return_inverse=True, return_counts=True)
    one = many[inv.reshape(-1)] == 1
    return e[one], np.tile(idx, 3)[one]


def _points(V, e):
    a, b = V[e[:, 0]], V[e[:, 1]]
    k = np.maximum(np.ceil(np.linalg.norm(b - a, axis=1) / 0.2), 1).astype(int)
    i = np.repeat(np.arange(len(a)), k)
    return a[i] + (b[i] - a[i]) * np.concatenate([np.arange(n) / n for n in k])[:, None], i


def contacts(names, near=1.0, on=0.6):
    """Where the named body parts meet a coloured part of the inner car, on the skin the eye sees (INSIDE: all of it):
    a body part's edge within near cm of the coloured part, or the coloured part's edge lying on the body (within on
    cm of its skin, on the outer side). Points every 0.2 cm, the body part and the inner part at each, and whether
    it's the coloured part's edge lying on the body."""
    P = parts.load()
    M = fbx.meshes()

    def mesh(texture, key):
        m = M[key]
        tv, pos = m["tri_vertex"], m["positions"].astype(np.float64)
        off = P.mesh_offset[texture]
        name = np.array([P.instances[int(i)]["name"] for i in P.tri_part[off:off + len(tv)]])
        _, weld = np.unique(np.round(pos, 2), axis=0, return_inverse=True)
        weld = weld.reshape(-1)
        V = np.zeros((weld.max() + 1, 3))
        V[weld] = pos
        n = m["tri_normal"].mean(1)
        return weld[tv], V, name, n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-9)

    bt, bV, bn, bnr = mesh("Skin", "Skin_01")
    dt, dV, dn, _ = mesh("Details", "Details_01")
    ours = np.isin(bn, names)
    coloured = np.isin(dn, [k for k, c in INNER.items() if c != BLACK])
    # a body part's edge beside a coloured part
    e, t = _edges(bt, np.ones(len(bt), bool))
    keep = ours[t]
    a, i = _points(bV, e[keep])
    at, an = t[keep][i], bnr[t[keep]][i]
    inner, it = _sample(dt, dV, coloured, 20, 3)
    d, j = cKDTree(inner).query(a, workers=-1)
    sel = d < near
    a, abody, ainner, an = a[sel], bn[at[sel]], dn[it[j[sel]]], an[sel]
    # a coloured part's edge lying on the body's outer skin
    e, et = _edges(dt, coloured)
    b, i = _points(dV, e)
    outer, st = _sample(bt, bV, ours, 40, 7)
    d, j = cKDTree(outer).query(b, workers=-1)
    bnrm = bnr[st[j]]
    sel = (d < on) & (np.einsum("ij,ij->i", b - outer[j], bnrm) > -0.1)
    pts, nrm = np.vstack([a, b[sel]]), np.vstack([an, bnrm[sel]])
    body, part = np.r_[abody, bn[st[j[sel]]]], np.r_[ainner, dn[et[i[sel]]]]
    lies = np.r_[np.zeros(len(a), bool), np.ones(sel.sum(), bool)]
    seen = (shapes.outside(0.4)(pts.astype(np.float32), nrm.astype(np.float32)) > 0.5) | np.isin(body, INSIDE)
    pts, body, part, lies = pts[seen], body[seen], part[seen], lies[seen]
    long = runs(pts, 10)  # a stretch shorter than 10 cm goes
    return pts[long], body[long], part[long], lies[long]


def gaps(pts, on, by, pieces=("sidepod top", "rear flank", "side skirt"), apart=3.0, strip=9.0, ledge=4.0):
    """Where the sidepod frame shows as a sliver along the side: where two of the side's pieces both meet it within
    apart cm of each other (the gap between them), and its strip above the side skirt behind the ring round the
    inlet's mouth (the ring ends at z RING at the bottom, where the sidepod top meets the frame) and the rear flank's
    foot (below LOW), up to strip cm above their edge and ledge cm in under it, under the sidepod top."""
    f = (by == "sidepod frame") & np.isin(on, pieces)
    p, o = pts[f], on[f]
    keep = np.zeros(len(p), bool)
    for piece in pieces:
        mine, other = o == piece, (o != piece)
        if mine.any() and other.any():
            keep[np.flatnonzero(mine)[cKDTree(p[other]).query(p[mine])[0] < apart]] = True
    skirt = p[((o == "side skirt") | ((o == "rear flank") & (p[:, 1] < LOW))) & (p[:, 2] < RING)]
    up, inward = np.meshgrid(np.arange(0.0, strip + 0.01, 0.5), np.arange(0.0, ledge + 0.01, 0.5))
    step = np.stack([-inward.ravel(), up.ravel(), np.zeros(up.size)], -1)  # in towards the middle, and up
    side = np.stack([np.sign(skirt[:, 0]), np.ones(len(skirt)), np.ones(len(skirt))], -1)
    curtain = skirt[:, None, :] + step[None] * side[:, None, :]
    return np.vstack([p[keep], curtain.reshape(-1, 3)])


def near(pts, width, label):
    """Within width cm of the points."""
    tree = cKDTree(pts)
    return shapes.Zone(lambda p, n: smoothstep(-0.1, 0.1, width - tree.query(p, workers=-1)[0]).astype(np.float32),
                       label=label)


def waves(width=4.0, every=10.0, rise=2.5, length=24.0):
    """Wavy stripes across the car, waving up the sides and across the top."""
    def f(p, n):
        u = p[:, 2] + rise * np.sin(2 * np.pi * (p[:, 1] + np.abs(p[:, 0])) / length)
        return smoothstep(-0.1, 0.1, width / 2 - np.abs((u / every) % 1 - 0.5) * every).astype(np.float32)
    return shapes.Zone(f, label="waves")


def heart(colour, px=192):
    """A heart, the colour on clear."""
    y, x = np.mgrid[1.25:-1.15:px * 3j, -1.3:1.3:px * 3j]
    inside = ((x * x + y * y - 1) ** 3 - x * x * y ** 3 <= 0).reshape(px, 3, px, 3).mean((1, 3))
    rgba = np.zeros((px, px, 4), np.uint8)
    rgba[..., :3] = [int(colour[k:k + 2], 16) for k in (1, 3, 5)]
    rgba[..., 3] = np.round(inside * 255)
    return Image.fromarray(rgba, "RGBA")


def lay(s, part, colour, pattern, other):
    """A part in its colour and pattern."""
    if pattern in ("dots", "small dots"):
        s.paint(part, "polka dots", palette=[colour, other], scale=10 if pattern == "dots" else 6)
    elif pattern == "checks":
        s.paint(part, "checks", palette=[colour, other], scale=8)
    else:
        s.paint(part, "gloss", colour=colour)
    if pattern == "stripes":
        s.paint(part, "gloss", colour=other, zone=shapes.stripes(4, across=(0, -LEAN, 1)))
    elif pattern == "waves":
        s.paint(part, "gloss", colour=other, zone=waves())
    elif pattern == "hearts":
        s.scatter(heart(other), where=part, size=6, spacing=11, turn="length")


def design(s):
    s.clay()

    s.step("Every part its own", "Each part of the body its own colour and pattern, the two sides unlike: on the "
           "left the side skirt purple with yellow dots, the sidepod yellow with red hearts, the rear flank orange "
           "with white dots; on the right the side skirt yellow with purple dots, the sidepod red with yellow hearts, "
           "the rear flank purple with white dots, the inlet red with white stripes on the left, blue with yellow on "
           "the right; the small rear quarter panels in small dots, purple with yellow on the left, orange with white "
           "on the right; the body shell blue with white checks, the engine cover green with yellow waves, and down "
           "its middle a plain green panel holding the plates the game letters, like a label.",
           words="I want you to actually paint each part differently ... e.g tail panel is one, fuel cap, etc; "
                 "Maybe for smaller parts, do dotted?")
    for part, plan in PLAN.items():
        lay(s, part, *plan)
    for part, colour in PLATES.items():
        s.paint(part, "gloss", colour=colour)
    s.paint("engine cover|part", "gloss", colour=GREEN,
            zone=shapes.Zone(lambda p, n: (np.abs(p[:, 0]) < LABEL).astype(np.float32), label="the deck's plain panel"))

    s.step("The black outline", "A black stroke 2.5 cm wide along every edge of every part, as Britto outlines "
           "everything: centred on the seam where two parts meet, inside the part where it ends (round the nose fin, "
           "the openings, the inner car's frames), widening gently where an edge runs on from a seam; the deck's "
           "plain panel framed by two more, carrying the rear quarter panels' inner edges back to the tail; clear "
           "of the deck's plates the game letters.",
           words="This needs a black line to close the fin; I think in general lines are too thick; Like why dabs "
                 "anyways? should it just be strokes or outlines?")
    body = [p for p in PLAN if p.split("|")[0] not in UNDER]
    clear = ~near(deck_points(), CLEAR, "the deck's plates")
    s.paint(body, "gloss", colour=BLACK, zone=outline(body, "the body's parts") & clear, across=True)
    s.paint("engine cover|part", "gloss", colour=BLACK, zone=label_lines().band(LINE))

    s.step("Wheels and the inner car", "The wheel covers red with white dots in a yellow ring, a black stroke along "
           "their edges; every part of the inner car a solid colour of its own (at the back the tail frame blue, "
           "the rear arms orange, the hubs and the diffuser purple), the rest of it and every bolt black.",
           words="primary and secondary colors")
    for part, plan in WHEELS.items():
        lay(s, part, *plan)
    s.paint(list(WHEELS), "gloss", colour=BLACK, zone=outline(list(WHEELS), "the wheel covers"), across=True)
    s.paint("inner", "gloss plastic", colour=BLACK)
    for part, colour in INNER.items():
        s.paint(part, "gloss plastic", colour=colour)

    s.step("The outline round the inner car", "A black stroke on the body along the edge of every coloured part of "
           "the inner car that lies on it: round the green frame of each sidepod's inlet, the bumper and tail frame "
           "at the back, the mirrors' feet, on each part beside it; and "
           "the green frame black where it shows only as a sliver along the side (in the gaps between the sidepod "
           "top, the rear flank and the side skirt) and wherever the body covers it, seen only through its cracks. "
           "Two colours never touch.",
           words="each part of something with for example red and circles, then another part with another color")
    names = list(dict.fromkeys(p.split("|")[0] for p in body))
    pts, on, by, lies = contacts(names)
    for part in np.unique(on[lies]):  # each part from its own stretch of the frame's edge: none runs on onto the next
        strokes = paths(pts[lies & (on == part)])
        if strokes:  # centred on the frame's edge, half under the frame: LINE cm of it seen
            s.paint([p for p in body if p.split("|")[0] == part], "gloss", colour=BLACK,
                    zone=course.Courses(strokes, f"the inner car's edge on the {part}").band(2 * LINE) & clear,
                    across=True)
    s.paint("sidepod frame", "gloss plastic", colour=BLACK,
            zone=near(gaps(pts, on, by), 2.0, "the frame where it shows as a sliver along the side")
            | covered("sidepod frame", "the frame under the body, seen only through its cracks"))
    s.paint("inner", "gloss plastic", colour=BLACK, zone=exactly(bolts(), "every bolt"))

    s.step("Tyres and glass", "The tyres plain black rubber, the black line round the whole car; the glass clear, "
           "so the red seat and the blue steering wheel show through the canopy.",
           words="I want you to actually paint each part differently")
    s.paint("tyres", "rubber", colour=BLACK)
    s.glass(WHITE, 0.9)

    s.step("The lights", "Every light its own colour of the palette, none the stock's: the speed numbers yellow, the "
           "gear bar along the tail green, the slots inside the front wheels purple, the front wing's lamps sun "
           "yellow at night, the ring round each wheel orange; "
           "each inner part's own lamps and strips in a colour that isn't its paint.",
           words="I want you to actually paint each part differently", look="rear night")
    for part, colour in LIGHTS.items():
        s.relight(part, colour)
    for part, colour in LIT.items():
        s.relight(part, colour, keep_level=True)

    s.step("Stays new", "A freshly varnished canvas: no dirt, no wear, no fading, even on a dirt road.",
           words="How about we design a car like that")
    s.dirt(0, "everything")
