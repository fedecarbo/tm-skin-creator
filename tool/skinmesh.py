"""The skin: the car's paintable surface as one mesh, the whole car, to draw on.

Why this exists (2026-09-30, the user: "Current approaches are not working"). Every way of drawing
tried before defined the line somewhere that isn't the car: values at the mesh's corners (the car
map's traced lines: a coarse mesh facets every edge, crayon), a flat sewing pattern of the skin (it
shears where the body curves), a spline through pins in the air (off the body by 22 cm), and a
view's projection (the blueprints: stops where the body turns away, and no line can cross two
views). All four are gone (2026-09-30, the user: "remove deprecated and clean up"). A line on a car
is a curve on the surface, so this module hands the surface over and tool/skindraw.py draws on it.

    python -m tool.skinmesh --build     build the cache and print what it is
    python -m tool.skinmesh --spots     the named places, with the face each lands on

How it's built (build):
  1. The triangles (_sew): the car's left half, the skin that's seen (open at least HIDDEN), no
     wheel covers, no blades standing off the body (BLADES), no slivers.
  2. Panels sewn (_bridge): a panel whose edge lies within STITCH of another's (the sidepod's top
     0.6 cm off the shell) is joined to it by a strip of new triangles, so a line crosses the join
     straight; a wider slot (the tail, 1.9 cm) is a real opening. Every join is sewn: the flat
     pattern this came from unsewed the ones that strained its flattening, which only broke lines.
     The strips cover no paint (they come from no car triangle: src -1). Only within a class: the
     outer skin, the underside (UNDER) and the inlet's duct (DUCT) stay pieces of their own.
  3. Each piece mirrored to the WHOLE car, welded on the centre line, so a curve can run up one
     flank, over the top and down the other, and an asymmetric design stays asymmetric.
  4. Doubled shell thinned (_thin), every piece wound one way and turned outwards by the car's
     own normals (_orient), pinched corners split (_split_fans): geometry-central refuses a
     surface without all three.
  5. Every triangle split into four, twice (SUBDIVIDE): the model's triangles are 35 mm across,
     and a curve runs corner to corner; 9 mm corners let a place land where it was asked.
  6. Every face remembers its piece and the car triangle it came from -- on the right half, the
     right triangle itself (_twins) -- so a curve can say which parts it crosses and a texel finds
     its face exactly (Skin.in_tri).
"""

import argparse
import collections
import functools

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

from tool import carmap, paths

CACHE = paths.CACHE / "skinmesh.npz"
VERSION = 4
HIDDEN = carmap.HIDDEN   # open: skin under this is out of sight and left off
PIECE_MIN = 300.0        # cm2: smaller loose pieces are left off
STITCH = 1.0             # cm: a gap between panels under this is one surface and is sewn; a wider slot is an opening
JOIN_WELD = 0.3          # cm: while sewing, a corner this near the other panel's own corner becomes it
RUN = 12.0               # cm: a join is sewn in runs this long
SLIVER = 0.02            # cm2: a triangle under this is left out
# Blades: thin things standing off the body, which are surface too, so a curve would climb them.
# The nose's "fin" is NOT one: 84 of its 94 triangles face up, x 0 to 8 cm; it is the bonnet's
# raised centre panel with a small upstand, and leaving it off punched an 84 mm hole in the bonnet.
BLADES = ("mirror mount", "wing pylon", "diffuser strake")
UNDER = ("side skirt", "diffuser")
DUCT = ("sidepod inlet",)  # the inlet's duct: its own piece, never sewn (a tube would make a handle)
PIECE_NAMES = {"body shell": "the body", "sidepod top": "the sidepod's top", "tail panel": "the tail", "tail corner": "the tail",
               "side skirt": "the skirt", "diffuser": "the diffuser", "sidepod inlet": "the inlet's duct"}
WELD = 0.05      # cm: two corners this near each other are the same corner (the mirror's centre line)
SUBDIVIDE = 2    # times every triangle is split into four (35 mm -> 9 mm corners)
CENTRE = 0.02    # cm: a corner this near x = 0 is pinned to it before mirroring, so the two halves meet exactly
REACH = 0.3      # cm: a point found by nearness must land this close to count as on the skin
MEND = 12.0      # cm: an edge loop shorter than this round is a flaw in the model, filled: a curve's walks
                 # stop at any edge, and a 4 cm hole by the cockpit's rear corner bites a 12 mm notch out
                 # of a line along the top. The openings round the mirror mounts and
                 # the wing pylon (13 cm and up) are real, and stay.


# ---- sewing the panels ----

def _edges(F):
    """Each triangle's three edges as sorted vertex pairs (3T, 2): the edges 01 of every triangle,
    then 12, then 20."""
    e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    e.sort(1)
    return e


def _components(F, n, cls=None):
    """Triangles joined across edges shared by exactly two of the same class: the piece label per
    triangle."""
    T = len(F)
    e = _edges(F)
    key = e[:, 0].astype(np.int64) * n + e[:, 1]
    if cls is not None:
        key = key * (cls.max() + 1) + np.tile(cls, 3)
    _, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
    tid = np.tile(np.arange(T), 3)
    order = np.argsort(inv, kind="stable")
    two = np.flatnonzero(cnt == 2)
    starts = np.r_[0, np.cumsum(cnt)]
    a, b = tid[order[starts[two]]], tid[order[starts[two] + 1]]
    A = coo_matrix((np.ones(len(a)), (a, b)), shape=(T, T))
    return connected_components(A, directed=False)[1]


def _boundary(F, n):
    """The oriented boundary edges (as the triangles wind them): (m, 2)."""
    raw = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    key = np.sort(raw, 1)
    key = key[:, 0].astype(np.int64) * n + key[:, 1]
    _, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
    return raw[cnt[inv] == 1]


def _bad_edges(F, n):
    """Per triangle: whether one of its edges is used by three triangles or twice in the same
    direction (a neighbour wound the other way)."""
    raw = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    kd = raw[:, 0].astype(np.int64) * n + raw[:, 1]
    _, inv, cnt = np.unique(kd, return_inverse=True, return_counts=True)
    e = np.sort(raw, 1)
    ke = e[:, 0].astype(np.int64) * n + e[:, 1]
    _, inv2, cnt2 = np.unique(ke, return_inverse=True, return_counts=True)
    return ((cnt[inv] > 1) | (cnt2[inv2] > 2)).reshape(3, len(F)).any(0)


def _loops(F, n):
    """Each boundary loop as an ordered list of vertices, the way the triangles wind it."""
    b = _boundary(F, n)
    nxt = {int(i): int(j) for i, j in b}
    seen, out = set(), []
    for i in nxt:
        if i in seen:
            continue
        loop, cur = [], i
        while cur in nxt and cur not in seen:
            seen.add(cur)
            loop.append(cur)
            cur = nxt[cur]
        if len(loop) >= 3:
            out.append(loop)
    return out


def _bridge(V, F, lab, cls, reach, big):
    """Panels of the same class (`big`: the components large enough to be pieces) whose edges lie
    within `reach` of each other joined across the gap between them by a strip of new triangles,
    a zipper along the two edges (the shorter diagonal each step), so they are one surface and
    a line drawn across the join carries straight over the gap; nothing moves, and the strip
    covers no paint (its triangles come from no triangle of the map: src -1). A vertex within
    JOIN_WELD of the other panel's own vertex is welded to it first (both to their midpoint), so the
    strip has no slivers. Returns (V', F', src, the run each strip triangle belongs to (-1 for
    the panels' own), the runs: (panel, other panel, where))."""
    V, F = V.copy(), F.copy()
    n = len(V)
    loops = _loops(F, n)
    # each boundary edge's component and class (the triangle it belongs to)
    e = _edges(F)
    key = e[:, 0].astype(np.int64) * n + e[:, 1]
    _, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
    on = np.flatnonzero(cnt[inv] == 1)
    bnd, b_tri = e[on], on % len(F)
    keep = np.isin(lab[b_tri], big)
    bnd, b_tri = bnd[keep], b_tri[keep]
    b_lab, b_cls = lab[b_tri], cls[b_tri]
    verts = np.unique(bnd)
    v_lab = {int(v): set() for v in verts}
    v_cls = {int(v): set() for v in verts}
    for i, (x, y) in enumerate(bnd):
        for v in (int(x), int(y)):
            v_lab[v].add(b_lab[i])
            v_cls[v].add(b_cls[i])
    # welds
    vtree = cKDTree(V[verts])
    rep = np.arange(n)
    for v in verts:
        v = int(v)
        for j in vtree.query_ball_point(V[v], JOIN_WELD):
            w = int(verts[j])
            if w != v and not (v_lab[w] & v_lab[v]) and (v_cls[w] & v_cls[v]) and rep[v] == v and rep[w] == w:
                rep[v] = w
                V[w] = 0.5 * (V[v] + V[w])
                break
    # matches: each boundary vertex to the nearest boundary edge of another panel within reach
    mid = 0.5 * (V[bnd[:, 0]] + V[bnd[:, 1]])
    half = 0.5 * np.linalg.norm(V[bnd[:, 1]] - V[bnd[:, 0]], axis=1)
    tree = cKDTree(mid)
    match = {}
    for v in verts:
        v = int(v)
        if rep[v] != v:
            continue
        best = None
        for s_ in tree.query_ball_point(V[v], reach + half.max()):
            if b_lab[s_] in v_lab[v] or b_cls[s_] not in v_cls[v]:
                continue
            a, c = V[bnd[s_, 0]], V[bnd[s_, 1]]
            t = float(np.clip((V[v] - a) @ (c - a) / max((c - a) @ (c - a), 1e-9), 0, 1))
            d = float(np.linalg.norm(a + t * (c - a) - V[v]))
            if d <= reach and (best is None or d < best[0]):
                best = (d, s_, t)
        if best is not None:
            match[v] = (b_lab[best[1]], best[1], best[2])
    # runs along each loop of matched vertices toward one other panel, and the zipper strips
    new, run_of, runs = [], [], []

    def zipper(run, other):
        """The strip between a run of one panel's boundary and the other panel's edge along it."""
        mine = v_lab[run[0]]
        A = V[rep[run]]
        arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(A, axis=0), axis=1))]
        cand = set()
        for u in run:
            s_ = match[u][1]
            cand.update((int(bnd[s_, 0]), int(bnd[s_, 1])))
        atree = cKDTree(A)
        for w in verts:
            w = int(w)
            if other in v_lab[w] and not (v_lab[w] & mine) and atree.query(V[w])[0] <= reach:
                cand.add(w)
        cand = [w for w in cand if rep[w] == w and w not in run]
        if not cand:
            return
        params = []  # along the run: the arc length of the nearest run point, refined on its segment
        for w in cand:
            dd = np.linalg.norm(A - V[w], axis=1)
            i0 = int(dd.argmin())
            i1 = i0 + 1 if i0 + 1 < len(A) and (i0 == 0 or dd[i0 + 1] < dd[i0 - 1]) else max(i0 - 1, 0)
            if i1 == i0:
                i1 = 1
            seg = A[i1] - A[i0]
            t = float(np.clip((V[w] - A[i0]) @ seg / max(seg @ seg, 1e-9), 0, 1))
            params.append(arc[i0] + t * (arc[i1] - arc[i0]))
        B = [w for _, w in sorted(zip(params, cand))]
        Bp = V[B]
        Ar = [rep[u] for u in run]
        runs.append((int(min(mine)), int(other), V[Ar].mean(0)))
        i, j = 0, 0
        while i < len(Ar) - 1 or j < len(B) - 1:
            step_a = j == len(B) - 1 or (i < len(Ar) - 1 and np.linalg.norm(A[i + 1] - Bp[j]) < np.linalg.norm(A[i] - Bp[j + 1]))
            if step_a:
                new.append([Ar[i + 1], Ar[i], B[j]])
                i += 1
            else:
                new.append([B[j], B[j + 1], Ar[i]])
                j += 1
            run_of.append(len(runs) - 1)

    done = set()
    for loop in loops:
        L = len(loop)
        for start in range(L):
            v = loop[start]
            if v not in match or v in done or loop[start - 1] in match and match[loop[start - 1]][0] == match[v][0]:
                continue
            other = match[v][0]
            if other < min(v_lab[v]):
                continue  # each pair of panels is bridged once, from the lower-numbered side
            run, i = [], start
            while loop[i % L] in match and match[loop[i % L]][0] == other and len(run) < L:
                run.append(loop[i % L])
                i += 1
            done.update(run)
            if len(run) < 2:
                continue
            # a long run in pieces of RUN cm or less, cut where it turns a corner, so a join can be
            # unsewn where it strains the paint and stay sewn where it doesn't
            cur = [run[0]]
            for u0, u1, u2 in zip(run, run[1:], run[2:] + [run[-1]]):
                cur.append(u1)
                d1, d2 = V[u1] - V[u0], V[u2] - V[u1]
                turn = np.degrees(np.arccos(np.clip(d1 @ d2 / max(np.linalg.norm(d1) * np.linalg.norm(d2), 1e-9), -1, 1)))
                if np.linalg.norm(V[cur[-1]] - V[cur[0]]) >= RUN or turn > 50:
                    zipper(cur, other)
                    cur = [u1]
            if len(cur) >= 2:
                zipper(cur, other)
    F = rep[F]
    F2 = np.concatenate([F, np.array(new, np.int64).reshape(-1, 3)])
    src = np.r_[np.arange(len(F)), np.full(len(new), -1)]
    run_id = np.r_[np.full(len(F), -1), np.array(run_of, np.int64)]
    good = (F2[:, 0] != F2[:, 1]) & (F2[:, 1] != F2[:, 2]) & (F2[:, 0] != F2[:, 2])
    # a strip triangle that runs against its neighbours (the zipper crossed itself) is dropped
    keep = good & ~(_bad_edges(F2, n) & (src < 0))
    return V, F2[keep], src[keep], run_id[keep], runs


def _split_fans(F, n):
    """Vertices whose triangles form more than one fan (a pinch: two boundary loops touching)
    split, each extra fan taking a new vertex id: (F', n', origin: each vertex's original)."""
    F = F.copy()
    origin = list(range(n))
    incident = [[] for _ in range(n)]
    for t in range(len(F)):
        for v in F[t]:
            incident[v].append(t)
    for v in range(n):
        ts = incident[v]
        if len(ts) < 2:
            continue
        others = {t: set(F[t]) - {v} for t in ts}
        lab, groups = {}, 0
        for t in ts:
            if t in lab:
                continue
            stack, lab[t] = [t], groups
            while stack:
                cur = stack.pop()
                for u in ts:
                    if u not in lab and others[cur] & others[u]:
                        lab[u] = groups
                        stack.append(u)
            groups += 1
        for g in range(1, groups):
            for t in ts:
                if lab[t] == g:
                    F[t][F[t] == v] = n
            origin.append(v)
            n += 1
    return F, n, np.array(origin)


def _mend(V, F, src, side):
    """Fill every edge loop shorter than MEND round with a fan of triangles from its middle. They
    carry no paint (src -1, like a strip sewn across a join); they only let a walk over the skin
    carry on across a flaw in the model instead of stopping at it."""
    loops = _loops(F, len(V))
    newV, newF = [], []
    for lp in loops:
        P = V[lp]
        if np.linalg.norm(np.diff(np.vstack([P, P[:1]]), axis=0), axis=1).sum() >= MEND:
            continue
        c = len(V) + len(newV)
        newV.append(P.mean(0))
        for a, b in zip(lp, lp[1:] + lp[:1]):
            newF.append((b, a, c))              # the loop runs with the skin on its left: wind the other way
    if not newV:
        return V, F, src, side, 0
    nf = len(newF)
    cen = np.asarray(newV)[np.asarray([f[2] for f in newF]) - len(V)]
    return (np.vstack([V, newV]), np.vstack([F, newF]), np.concatenate([src, np.full(nf, -1, src.dtype)]),
            np.concatenate([side, (cen[:, 0] < 0).astype(side.dtype)]), len(newV))


def _twins(m):
    """Per triangle of the map, its mirror twin on the left (-1 without one): the triangle whose
    three corners lie within 0.2 cm of the mirrored corners, in any order (a centroid alone
    matched a long sliver to a small triangle 5 cm away, 2026-09-29)."""
    V, F = m.V, m.F
    cen = V[F].mean(1)
    left = np.flatnonzero(cen[:, 0] > -0.05)
    d, i = cKDTree(cen[left]).query(cen * [-1, 1, 1], k=3, workers=-1)
    Pm = V[F] * [-1, 1, 1]
    mirror = np.full(len(F), -1, np.int64)
    for k in range(3):
        cand = left[i[:, k]]
        Pc = V[F[cand]]
        best = np.full(len(F), np.inf)
        for perm in ((0, 1, 2), (1, 2, 0), (2, 0, 1), (0, 2, 1), (2, 1, 0), (1, 0, 2)):
            best = np.minimum(best, np.linalg.norm(Pm[:, list(perm)] - Pc, axis=2).max(1))
        take = (mirror < 0) & (best < 0.2)
        mirror[take] = cand[take]
    return mirror



# ---- the skin ----

def _edge_use(F):
    """Every edge as a sorted pair, with how many triangles use it."""
    e = np.sort(np.stack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]], 1).reshape(-1, 2), axis=1)
    return np.unique(e, axis=0, return_counts=True)


def _surface_pieces(V, F):
    u, _ = _edge_use(F)
    A = coo_matrix((np.ones(len(u)), (u[:, 0], u[:, 1])), shape=(len(V), len(V)))
    n, lab = connected_components(A + A.T, directed=False)
    return n, lab


def _split4(V, F, src, side):
    """Every triangle split into four, with new corners at the edges' middles. The surface does not
    move: a new corner sits on an edge of the old triangle, so the shape, the normals and the areas
    are what they were -- only the corners are closer together."""
    e = np.stack([np.sort(F[:, [1, 2]], 1), np.sort(F[:, [2, 0]], 1), np.sort(F[:, [0, 1]], 1)], 1)
    flat = e.reshape(-1, 2)
    uniq, inv = np.unique(flat, axis=0, return_inverse=True)
    mid = len(V) + inv.reshape(-1, 3)
    V = np.vstack([V, (V[uniq[:, 0]] + V[uniq[:, 1]]) / 2.0])
    a, b, c = F[:, 0], F[:, 1], F[:, 2]
    ma, mb, mc = mid[:, 0], mid[:, 1], mid[:, 2]     # opposite a, b, c
    F = np.concatenate([np.stack([a, mc, mb], 1), np.stack([b, ma, mc], 1),
                        np.stack([c, mb, ma], 1), np.stack([ma, mb, mc], 1)])
    return V, F, np.tile(src, 4), np.tile(side, 4)


def _thin(V, F, src, side):
    """Faces dropped until no edge has more than two of them. The model has a doubled shell here
    and there, and two faces on one edge is all a surface can have; the smallest goes first."""
    dropped = 0
    while True:
        u, c = _edge_use(F)
        bad = set(map(tuple, u[c > 2]))
        if not bad:
            return F, src, side, dropped
        area = 0.5 * np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1)
        hit = np.array([any(tuple(sorted(p)) in bad for p in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0]))) for t in F])
        worst = np.flatnonzero(hit)[np.argmin(area[hit])]
        F, src, side = np.delete(F, worst, 0), np.delete(src, worst), np.delete(side, worst)
        dropped += 1


def _orient(V, F, want, log=print):
    """Every face wound the same way round its piece of surface, and each piece turned to face
    outwards. The sheet's pieces don't agree with each other (the tail's winding is the body's
    reversed), and geometry-central refuses a mesh where one edge is used twice the same way.
    `want` (m, 3) is the way each face should face -- the car's own normal -- which settles which
    way round a whole piece goes."""
    F = F.copy()
    # faces that share an edge, as a graph
    pair = np.stack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]], 1).reshape(-1, 2)
    key = np.sort(pair, axis=1)
    order = np.lexsort((key[:, 1], key[:, 0]))
    ks, fs = key[order], order // 3
    same = np.flatnonzero((ks[:-1] == ks[1:]).all(1))
    a, b = fs[same], fs[same + 1]
    # the two faces agree if they traverse the shared edge in opposite directions
    flipped = (pair[order][same] == pair[order][same + 1]).all(1)
    A = coo_matrix((np.ones(len(a)), (a, b)), shape=(len(F), len(F)))
    A = (A + A.T).tocsr()
    ncomp, lab = connected_components(A, directed=False)
    # walk each piece, flipping what disagrees
    flip = np.zeros(len(F), bool)
    seen = np.zeros(len(F), bool)
    disagree = collections.defaultdict(list)
    for i in range(len(a)):
        disagree[a[i]].append((b[i], flipped[i]))
        disagree[b[i]].append((a[i], flipped[i]))
    clash = 0
    for start in range(len(F)):
        if seen[start]:
            continue
        seen[start] = True
        stack = [start]
        while stack:
            cur = stack.pop()
            for nxt, needs in disagree.get(cur, ()):
                want_flip = flip[cur] ^ needs
                if not seen[nxt]:
                    seen[nxt] = True
                    flip[nxt] = want_flip
                    stack.append(nxt)
                elif flip[nxt] != want_flip:
                    clash += 1
    if clash:
        log(f"{clash} edges could not be made to agree (the surface twists on itself there): left as they are")
    # each piece the right way out, by the car's own normals
    for c in range(ncomp):
        q = np.flatnonzero(lab == c)
        n = np.cross(V[F[q, 1]] - V[F[q, 0]], V[F[q, 2]] - V[F[q, 0]])
        n[flip[q]] *= -1.0
        nn = np.linalg.norm(n, axis=1, keepdims=True)
        agree = ((n / np.maximum(nn, 1e-12)) * want[q]).sum(1)
        if np.average(agree, weights=nn[:, 0]) < 0:
            flip[q] = ~flip[q]
    F[flip] = F[flip][:, ::-1]
    log(f"{int(flip.sum())} faces turned round so every piece of surface is wound one way and faces outwards "
        f"({ncomp} piece(s))")
    return F


def _sew(m, log=print):
    """The car's left half as sewn pieces of surface: a list of (name, V, F, src), src the car
    triangle each face came from (-1 for a strip sewn across a join)."""
    V, F, pn = m.V, m.F, m.part_names[m.part]
    cen = V[F].mean(1)
    open_t = m.layers["open"][F].mean(1)
    A, B, C = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    tri_area = 0.5 * np.linalg.norm(np.cross(B - A, C - A), axis=1)
    keep = ~np.isin(pn, carmap.WHEEL_COVERS + BLADES) & (cen[:, 0] > -0.05) & (open_t >= HIDDEN) & (tri_area > SLIVER)
    tris = np.flatnonzero(keep)
    Fk = F[tris].copy()
    flip = (np.cross(V[Fk[:, 1]] - V[Fk[:, 0]], V[Fk[:, 2]] - V[Fk[:, 0]]) * m.fn[tris]).sum(1) < 0
    Fk[flip] = Fk[flip][:, [0, 2, 1]]  # anticlockwise seen from outside
    cls = np.isin(pn[tris], UNDER).astype(int) + 2 * np.isin(pn[tris], DUCT).astype(int)
    Fk, n, origin = _split_fans(Fk, len(V))  # every pinch split first, so the boundary loops are simple
    V = V[origin]
    lab = _components(Fk, len(V), cls)
    big = np.flatnonzero(np.bincount(lab, weights=tri_area[tris]) >= PIECE_MIN)
    Vz, Fz, src, _, runs = _bridge(V, Fk, lab, cls, STITCH, big)
    log(f"sewn: {(src < 0).sum()} strip triangles bridge {len(runs)} joins between panels")
    tris_z, cls_z = np.where(src < 0, -1, tris[np.maximum(src, 0)]), cls[np.maximum(src, 0)]
    lab_z = _components(Fz, len(Vz), cls_z)
    Az, Bz, Cz = Vz[Fz[:, 0]], Vz[Fz[:, 1]], Vz[Fz[:, 2]]
    parea = np.bincount(lab_z, weights=0.5 * np.linalg.norm(np.cross(Bz - Az, Cz - Az), axis=1))
    pieces = []
    for p in [int(p) for p in np.argsort(parea)[::-1] if parea[p] >= PIECE_MIN]:
        sel = np.flatnonzero(lab_z == p)
        names, counts = np.unique(pn[tris_z[sel][tris_z[sel] >= 0]], return_counts=True)
        name = PIECE_NAMES.get(names[np.argmax(counts)], names[np.argmax(counts)])
        vids, inv = np.unique(Fz[sel], return_inverse=True)
        Fl, _, origin0 = _split_fans(inv.reshape(-1, 3), len(vids))
        pieces.append((name, Vz[vids[origin0]], Fl, tris_z[sel].astype(np.int32)))
    return pieces


def build(log=print):
    """Build the cache. Returns the dict that goes in it."""
    m = carmap.load()
    # Each piece becomes its own whole-car surface: mirrored and welded along the centre line, but
    # never welded to another piece -- fusing pieces twisted the surface (the tail met the body
    # wound the other way, and 23 edges had no consistent side, which geometry-central refuses).
    pieces = _sew(m, log)
    names = [p[0] for p in pieces]
    Vs, Fs, piece, src, side = [], [], [], [], []
    off = 0
    for k, (name, V, F, csrc) in enumerate(pieces):
        V = V.copy()
        V[np.abs(V[:, 0]) < CENTRE, 0] = 0.0     # pin the centre line so the two halves meet exactly
        n0 = len(V)
        V = np.vstack([V, V * [-1.0, 1.0, 1.0]])
        F = np.vstack([F, F[:, ::-1] + n0])      # the mirror's winding flips, so its faces still face out
        psrc = np.tile(csrc, 2)
        pside = np.concatenate([np.zeros(len(csrc), np.int8), np.ones(len(csrc), np.int8)])
        key = np.round(V / WELD).astype(np.int64)
        _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
        V, F = V[first], inv[F].astype(np.int64)
        keep = (F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 2] != F[:, 0])
        F, psrc, pside = F[keep], psrc[keep], pside[keep]
        F, psrc, pside, dropped = _thin(V, F, psrc, pside)
        # the way each face should face: the car's own normal, mirrored on the mirrored half; a strip
        # sewn across a join has no car triangle and says nothing (its piece decides)
        want = np.where(psrc[:, None] >= 0, m.fn[np.maximum(psrc, 0)], 0.0)
        want = want * np.where(pside[:, None] > 0, [-1.0, 1.0, 1.0], [1.0, 1.0, 1.0])
        F = _orient(V, F, want, log=lambda msg, name=name: log(f"  {name}: {msg}"))
        F, n, origin = _split_fans(F, len(V))
        V = V[origin]
        V, F, psrc, pside, mended = _mend(V, F, psrc, pside)
        for _ in range(SUBDIVIDE):
            V, F, psrc, pside = _split4(V, F, psrc, pside)
        log(f"  {name:18} {len(V):6d} corners {len(F):6d} triangles" + (f", {dropped} dropped (a doubled shell)" if dropped else "")
            + (f", {mended} small hole(s) filled" if mended else ""))
        Vs.append(V)
        Fs.append(F + off)
        piece.append(np.full(len(F), k, np.int32))
        src.append(psrc)
        side.append(pside)
        off += len(V)
    V, F = np.vstack(Vs), np.vstack(Fs)
    piece, src, side = np.concatenate(piece), np.concatenate(src), np.concatenate(side)

    # The right half is the left one mirrored, so its faces came out remembering the LEFT car
    # triangle they were copied from. But a texel on the car's right belongs to the RIGHT triangle,
    # the left one's mirror twin, and could never find its face: measured, only 38 % of the skin's
    # texels mapped, all of them on the left. Each right face takes its own triangle, the twin.
    twin = _twins(m)                                # right triangle -> its left twin
    cen = m.V[m.F].mean(1)
    right_of = np.full(len(m.F), -1, np.int64)
    rt = np.flatnonzero((twin >= 0) & (cen[:, 0] < -0.05))
    right_of[twin[rt]] = rt
    mapped = (side > 0) & (src >= 0) & (right_of[np.maximum(src, 0)] >= 0)
    src = np.where(mapped, right_of[np.maximum(src, 0)], src)
    lost = int(((side > 0) & (src >= 0) & ~mapped).sum())
    log(f"the right half: {int(mapped.sum())} faces take their own car triangle"
        + (f", {lost} have no mirror twin in the model (round the number panel) and are found by nearness" if lost else ""))

    u, c = _edge_use(F)
    ncomp, lab = _surface_pieces(V, F)
    area = 0.5 * np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1)
    elen = np.linalg.norm(V[u[:, 1]] - V[u[:, 0]], axis=1)
    log(f"the skin: {len(V)} corners, {len(F)} triangles, {area.sum():.0f} cm2, {ncomp} piece(s) of surface, "
        f"{int((c == 1).sum())} edges on a boundary, {int((c > 2).sum())} edges with more than two faces")
    log(f"triangles {np.median(elen) * 10:.1f} mm across (median edge), {np.percentile(elen, 95) * 10:.0f} mm at the 95th; "
        f"x {V[:, 0].min():.1f} to {V[:, 0].max():.1f} cm, so both sides are here")
    assert int((c > 2).sum()) == 0, "the skin must be a surface: no edge with more than two faces"

    data = {"V": V.astype(np.float64), "F": F.astype(np.int32), "piece": piece.astype(np.int32),
            "src": src.astype(np.int32), "side": side.astype(np.int8), "comp": lab[F[:, 0]].astype(np.int32),
            "piece_names": np.array(names), "version": np.int32(VERSION)}
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE, **data)
    return data


class Skin:
    """The car's paintable surface, one mesh, the whole car."""

    def __init__(self, data):
        self.V, self.F = data["V"], data["F"].astype(np.int64)
        self.piece, self.src, self.side, self.comp = data["piece"], data["src"], data["side"], data["comp"]
        self.piece_names = list(data["piece_names"])
        self._m = None
        self._fan = None
        self._tracer = None

    # ---- the car underneath ----

    @property
    def m(self):
        """The car map, for part names."""
        if self._m is None:
            self._m = carmap.load()
        return self._m

    @functools.cached_property
    def part(self):
        """The part name of every face ("a join" for a strip sewn across one)."""
        names = self.m.part_names[self.m.part[np.maximum(self.src, 0)]].astype(object)
        names[self.src < 0] = "a join"
        return names

    @functools.cached_property
    def fn(self):
        n = np.cross(self.V[self.F[:, 1]] - self.V[self.F[:, 0]], self.V[self.F[:, 2]] - self.V[self.F[:, 0]])
        return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)

    @functools.cached_property
    def vn(self):
        n = np.zeros_like(self.V)
        for k in range(3):
            np.add.at(n, self.F[:, k], self.fn)
        return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)

    @functools.cached_property
    def loops(self):
        """The skin's edges -- the cockpit's rim, every opening's lip, the body's lower edge -- each
        as a loop of corners, run with the skin on its left (seen from outside)."""
        return _loops(self.F, len(self.V))

    @functools.cached_property
    def area(self):
        return 0.5 * np.linalg.norm(np.cross(self.V[self.F[:, 1]] - self.V[self.F[:, 0]],
                                             self.V[self.F[:, 2]] - self.V[self.F[:, 0]]), axis=1)

    # ---- the geometry libraries (potpourri3d / geometry-central) ----

    def tracer(self):
        """potpourri3d's geodesic tracer on this mesh, built once: it walks straight on the surface
        from a point in a direction."""
        if self._tracer is None:
            import potpourri3d as pp3d
            self._tracer = pp3d.GeodesicTracer(self.V, self.F)
        return self._tracer

    # ---- from a place on the car to a face here ----

    def _fans(self):
        """The car triangle -> the faces here that came from it, per side, as a padded table."""
        if self._fan is None:
            own = np.flatnonzero(self.src >= 0)             # strips sewn across joins carry no paint
            key = self.src[own].astype(np.int64) * 2 + (self.side[own] > 0)
            order = own[np.argsort(key, kind="stable")]
            key = np.sort(key, kind="stable")
            u, first, cnt = np.unique(key, return_index=True, return_counts=True)
            table = np.full((len(self.m.F) * 2, int(cnt.max())), -1, np.int64)
            for k in range(int(cnt.max())):
                has = cnt > k
                table[u[has], k] = order[first[has] + k]
            self._fan = table
        return self._fan

    @staticmethod
    def _bary(A, B, C, pos):
        e1, e2, d = B - A, C - A, pos - A
        d11, d12, d22 = (e1 * e1).sum(-1), (e1 * e2).sum(-1), (e2 * e2).sum(-1)
        dd1, dd2 = (d * e1).sum(-1), (d * e2).sum(-1)
        det = np.maximum(d11 * d22 - d12 * d12, 1e-12)
        b1 = (d22 * dd1 - d12 * dd2) / det
        b2 = (d11 * dd2 - d12 * dd1) / det
        return np.stack([1 - b1 - b2, b1, b2], -1)

    def in_tri(self, tri, pos):
        """For points known to sit on the car's triangles `tri` (the bake's own ids), the face here
        they fall on and their weights there: (face (n,) or -1, bary (n, 3)). The side is taken
        from the point itself, so the car's right lands on the mirrored half."""
        tri, pos = np.asarray(tri, np.int64), np.asarray(pos, np.float64)
        key = tri * 2 + (pos[:, 0] < 0)
        fan = self._fans()[np.clip(key, 0, len(self._fans()) - 1)]
        out = np.full(len(tri), -1, np.int64)
        bary = np.zeros((len(tri), 3))
        best = np.full(len(tri), -np.inf)
        for k in range(fan.shape[1]):
            f = fan[:, k]
            on = (f >= 0) & (tri >= 0)
            if not on.any():
                continue
            c = self.V[self.F[f[on]]]
            b = self._bary(c[:, 0], c[:, 1], c[:, 2], pos[on])
            score = b.min(1)                       # 0 or more: inside. The least negative wins.
            better = np.zeros(len(tri), bool)
            better[on] = score > best[on]
            best[better] = score[better[on]]
            out[better] = f[better]
            bary[better] = np.clip(b[better[on]], 0.0, 1.0)
        bary /= np.maximum(bary.sum(1, keepdims=True), 1e-12)
        # A point whose triangle has no face here is found by nearness -- but only if it then lands
        # ON the skin. The few right triangles with no mirror twin do; a texel on the inner car or a
        # wheel cover is not on the skin at all, and without this test was dragged onto the nearest
        # face up to 48 cm away.
        miss = (out < 0) & (tri >= 0)
        if miss.any():
            f2, b2 = self.nearest(pos[miss])
            close = np.linalg.norm(self.point(f2, b2) - pos[miss], axis=1) < REACH
            m_idx = np.flatnonzero(miss)[close]
            out[m_idx], bary[m_idx] = f2[close], b2[close]
        return out, bary

    def nearest(self, pos, nrm=None, k=12):
        """The face nearest any points (n, 3), preferring one facing the same way: (face, bary).
        For points that aren't already known to sit on a car triangle."""
        if not hasattr(self, "_ctree"):
            self._cen = self.V[self.F].mean(1)
            self._ctree = cKDTree(self._cen)
        pos = np.asarray(pos, np.float64)
        _, idx = self._ctree.query(pos, k=min(k, len(self.F)), workers=-1)
        idx = np.atleast_2d(idx)
        best = np.full(len(pos), np.inf)
        out = np.full(len(pos), -1, np.int64)
        bary = np.zeros((len(pos), 3))
        for j in range(idx.shape[1]):
            f = idx[:, j]
            c = self.V[self.F[f]]
            b = np.clip(self._bary(c[:, 0], c[:, 1], c[:, 2], pos), 0.0, 1.0)
            b /= np.maximum(b.sum(1, keepdims=True), 1e-12)
            p = (b[:, :, None] * c).sum(1)
            d = np.linalg.norm(p - pos, axis=1)
            if nrm is not None:
                d = d + 5.0 * np.maximum(0.0, 0.3 - (self.fn[f] * np.asarray(nrm)).sum(1))  # cm: facing the other way costs
            take = d < best
            best[take], out[take], bary[take] = d[take], f[take], b[take]
        return out, bary

    def point(self, face, bary):
        """The 3D place (cm) of a face and its weights."""
        return (np.asarray(bary)[..., None] * self.V[self.F[np.asarray(face)]]).sum(-2)


@functools.lru_cache(maxsize=1)
def load():
    if not CACHE.exists() or int(np.load(CACHE)["version"]) != VERSION:
        build()
    d = dict(np.load(CACHE))
    if int(d["version"]) != VERSION:
        d = build()
    return Skin(d)


def reload():
    load.cache_clear()
    return load()


def main():
    ap = argparse.ArgumentParser(description="the car's paintable surface as one mesh")
    ap.add_argument("--build", action="store_true", help="rebuild the cache")
    ap.add_argument("--spots", action="store_true", help="the named places and the face each lands on")
    a = ap.parse_args()
    if a.build or not CACHE.exists():
        build()
    sk = load()
    print(f"\n{len(sk.V)} corners, {len(sk.F)} triangles, {sk.area.sum():.0f} cm2, "
          f"{len(set(sk.comp.tolist()))} piece(s) of surface")
    print(f"{'piece':22} {'triangles':>9} {'cm2':>8}")
    for k, name in enumerate(sk.piece_names):
        q = sk.piece == k
        if q.any():
            print(f"{name:22} {int(q.sum()):9d} {sk.area[q].sum():8.0f}")
    print(f"\nthe parts on it ({len(set(sk.part.tolist()))}):")
    names, cnt = np.unique(sk.part, return_counts=True)
    for n, c in sorted(zip(names, cnt), key=lambda x: -x[1]):
        print(f"   {n:26} {c:5d} triangles {sk.area[sk.part == n].sum():8.0f} cm2")
    if a.spots:
        from tool import paintbox
        print(f"\n{'spot':16} {'asked for (cm)':26} {'landed on':26} {'off by':>8}")
        for name, spot in paintbox.SPOTS.items():
            c = np.asarray(spot["centre"], np.float64)[None]
            f, b = sk.nearest(c, np.asarray(spot["facing"], np.float64)[None] if "facing" in spot else None)
            p = sk.point(f, b)[0]
            print(f"{name:16} {str(c[0].round(1)):26} {str(p.round(1)):26} {np.linalg.norm(p - c[0]) * 10:7.1f} mm  {sk.part[f[0]]}")


if __name__ == "__main__":
    main()
