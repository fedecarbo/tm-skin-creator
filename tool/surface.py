"""The body sheet: the car's outer skin flattened into a sewing pattern in true centimetres.

Every zone in tool/shapes measures through the air (a stripe 10 cm wide is 10 cm on a flat panel
and narrower on a slope), and the map's `across` and `along` are projections. The sheet is the
standard answer from geometry processing: the left half of the body (the right is its mirror), cut
at the top centreline, its panels sewn together, flattened so that 1 cm on the sheet is 1 cm on
the paint as nearly as a curved surface allows, and measured, not looked at: for every triangle the
two singular values of the flat map say how much a length stretches along and across it. Where a
piece can't lie flat (a doubly curved corner), a dart is cut from the worst spot to the nearest
edge and the piece flattened again, until the sheet meets its targets (AREA_LIMIT, ANGLE_LIMIT,
held at the 95th percentile and locally: no patch of REGION cm² over twice them) or DARTS cuts are
made.

    python -m tool.surface            build it (a few seconds) and print the pieces' table

    sheet = surface.load()
    sheet.uv_at(pos, nrm)             sheet coordinates (cm) of points on the body, NaN off it
    sheet.lines["shoulder"]           the map's lines on the sheet: lists of (n, 2) polylines
    surface.sheet_cm("Skin", w, h)    (h, w, 2) float32: every texel's place on the sheet, cached

How it's built (build):
  1. The triangles: the left half of the body (centroid x >= 0), the skin that's seen (open at
     least HIDDEN, the outlines' own rule), no wheel covers, no blades or struts standing off the
     body (BLADES), no slivers.
  2. The panels sewn (_zip): a panel whose edge lies within STITCH of another's (the sidepod's top
     0.6 cm off the shell, the tail 1.9 cm behind the rear flank) has its edge vertices put on
     the other's edge (the edge's triangle split into a fan there) and the other's on its own,
     each moved to the gap's midline, so the two share a run of edges and flatten as one, and a
     line drawn across the join carries straight over it. Only within a class: the outer skin,
     and the underside (UNDER: the skirt, cut from the shell along the skirt's crest, a fold the
     map draws; the diffuser), which stays its own piece.
  3. Pieces: triangles joined across shared edges; pieces under PIECE_MIN cm² (the rivets, the
     fin's blade) are left off. Each piece is made vertex-manifold (a pinch vertex split) for the
     libraries.
  4. Flattening (libigl 2.6.3): igl.lscm, the least-squares conformal map (Levy 2002), two
     boundary vertices pinned; then igl.arap_solve, as-rigid-as-possible (Liu 2008), ARAP_ROUNDS
     times, which keeps lengths, not only angles.
  5. Distortion per triangle: the singular values s1 >= s2 of the map's Jacobian. area: s1*s2 - 1
     (%), angle: 90 - 2*atan(s2/s1) (degrees: the most a right angle drawn on the sheet is bent on
     the car), stretch: max(s1, 1/s2) - 1 (%: the most a length changes in any direction). The
     targets: over the painted body (open >= PAINTED) the 95th percentile by area within
     AREA_LIMIT % and ANGLE_LIMIT degrees, and no connected patch of REGION cm² or more over twice
     them (a sheared corner is small next to the body, and a percentile let it through:
     2026-09-29, the user's close-up of the sidepod's rear corner).
  6. Darts: while a piece misses a target, the worst patch (by strain times area) is cut from its
     vertex deepest in the piece along the mesh's edges to the boundary, by the way of least cost
     (length / stretch: the cut follows the strain), the vertices along the cut duplicated (one
     side takes copies); the piece is flattened again. A dart that gains nothing is undone.
  7. Layout: the main piece turned so its top centreline runs left to right with the nose at
     x = 0; the other pieces turned so the car's length runs the same way and set below it in a
     row, nose to tail. Sheet coordinates in cm, y down (the SVG's way).

The sheet keeps its own mesh (Vs, Fs: the sewn, split and cut triangles; src: the map's triangle
each came from), so a texel finds its place through its own triangle's fan (uv_in), exact.
"""

import functools

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import cKDTree

from tool import carmap, paths

CACHE = paths.CACHE / "sheet.npz"
VERSION = 2
HIDDEN = carmap.HIDDEN   # open: skin under this isn't on the sheet (the outlines' rule)
PAINTED = 0.4            # open: the painted body, where the targets are held
PIECE_MIN = 300.0        # cm²: smaller loose pieces are left off the sheet
STITCH = 1.0             # cm: a gap between panels under this reads as one surface and is sewn (the sidepod's top, 0.6 cm off the shell); a wider slot (the tail, 1.9 cm) is a real opening
WELD = 0.3               # cm: a vertex this near the other panel's own vertex becomes it
RUN = 12.0               # cm: a join is sewn in runs this long, each one unsewn on its own if it strains the paint
UNSEW = 8.0              # degrees: a sewn run whose surroundings bend this much on average is unsewn (the paint would shear worse than the line would break)
SLIVER = 0.02            # cm²: a triangle under this is left out (its singular values mean nothing)
AREA_LIMIT = 5.0         # %, at the 95th percentile over the painted body
ANGLE_LIMIT = 3.0        # degrees
REGION = 50.0            # cm²: no patch this big may be over twice the limits (a 7 cm square)
ARAP_ROUNDS = 6          # igl.arap_solve rounds (the skin piece: 4.1 % after one, 3.7 % after six)
DARTS = 0                # a dart cuts the paint and breaks every line across it; the user's rule (2026-09-29): unbroken lines
                         # first, so no darts: the strain a corner keeps is measured and reported instead
GAP = 6.0                # cm between the pieces on the sheet
BLADES = ("mirror mount", "wing pylon", "diffuser strake")
UNDER = ("side skirt", "diffuser")
DUCT = ("sidepod inlet",)  # the inlet's duct: its own piece, never sewn (a tube would make a handle)
PIECE_NAMES = {"body shell": "the body", "sidepod top": "the sidepod's top", "tail panel": "the tail", "tail corner": "the tail",
               "side skirt": "the skirt", "diffuser": "the diffuser", "sidepod inlet": "the inlet's duct"}


# ---- the triangles and their pieces ----

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
    a zipper along the two edges (the shorter diagonal each step), so they flatten as one sheet
    and a line drawn across the join carries straight over the gap; nothing moves, and the strip
    covers no paint (its triangles come from no triangle of the map: src -1). A vertex within
    WELD of the other panel's own vertex is welded to it first (both to their midpoint), so the
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
        for j in vtree.query_ball_point(V[v], WELD):
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


# ---- the flattening (libigl) ----

def _local(V, F):
    """Each triangle laid flat on its own: corner coordinates (T, 3, 2), and the areas."""
    A, B, C = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    e1, e2 = B - A, C - A
    x = e1 / np.maximum(np.linalg.norm(e1, axis=1, keepdims=True), 1e-12)
    nrm = np.cross(e1, e2)
    area = 0.5 * np.linalg.norm(nrm, axis=1)
    nrm = nrm / np.maximum(2 * area, 1e-12)[:, None]
    y = np.cross(nrm, x)
    P = np.zeros((len(F), 3, 2))
    P[:, 1, 0] = (e1 * x).sum(1)
    P[:, 2, 0] = (e2 * x).sum(1)
    P[:, 2, 1] = (e2 * y).sum(1)
    return P, area


def flatten(V, F, rounds=ARAP_ROUNDS):
    """One piece flattened: igl.lscm pinned at the two farthest boundary vertices, then ARAP."""
    import igl
    V, F = np.ascontiguousarray(V, np.float64), np.ascontiguousarray(F, np.int64)
    b = np.unique(_boundary(F, len(V)))
    d = np.linalg.norm(V[b] - V[b].mean(0), axis=1)
    p0 = b[int(d.argmax())]
    p1 = b[int(np.linalg.norm(V[b] - V[p0], axis=1).argmax())]
    uv, _ = igl.lscm(V, F, np.array([p0, p1], np.int64), np.array([[0.0, 0.0], [np.linalg.norm(V[p1] - V[p0]), 0.0]]))
    data = igl.ARAPData()
    igl.arap_precomputation(V, F, 2, np.array([p0], np.int32), data)  # one vertex held (the free solve is singular on some pieces)
    for _ in range(rounds):
        uv = igl.arap_solve(uv[[p0]], data, uv)
    return uv


def distortion(V, F, uv):
    """Per triangle, the singular values (s1 >= s2) of the map from the body to the sheet, and the
    triangle's area on the body."""
    P, area = _local(V, F)
    X = np.stack([P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]], 2)
    U = np.stack([uv[F[:, 1]] - uv[F[:, 0]], uv[F[:, 2]] - uv[F[:, 0]]], 2)
    ok = np.abs(np.linalg.det(X)) > 1e-9
    J = np.zeros((len(F), 2, 2))
    J[ok] = U[ok] @ np.linalg.inv(X[ok])
    s = np.linalg.svd(J, compute_uv=False)
    s[np.linalg.det(J) < 0, 1] *= -1  # a folded triangle: its small value negative
    return s[:, 0], s[:, 1], area


def measures(s1, s2):
    """area (%), angle (degrees), stretch (%) per triangle from the singular values."""
    s2c = np.maximum(s2, 1e-6)
    return (s1 * s2 - 1) * 100, 90 - 2 * np.degrees(np.arctan2(s2c, s1)), (np.maximum(s1, 1 / s2c) - 1) * 100


def percentile(v, w, q=95):
    """The q-th percentile of v weighted by w."""
    v, w = np.asarray(v, float), np.asarray(w, float)
    if not len(v):
        return np.nan
    o = np.argsort(v)
    c = np.cumsum(w[o])
    return float(v[o][min(np.searchsorted(c, q / 100 * c[-1]), len(o) - 1)])


def patches(F, n, bad, area):
    """The connected patches of `bad` triangles (joined through shared vertices): their labels
    (-1 where not bad) and each patch's area."""
    lab = np.full(len(F), -1)
    bt = np.flatnonzero(bad)
    if not len(bt):
        return lab, np.zeros(0)
    vt = coo_matrix((np.ones(3 * len(bt)), (np.repeat(np.arange(len(bt)), 3), F[bt].reshape(-1))), shape=(len(bt), n))
    lab[bt] = connected_components(vt @ vt.T, directed=False)[1]
    return lab, np.bincount(lab[bt], weights=area[bt])


def judge(F, n, s1, s2, area, painted, limits=(AREA_LIMIT, ANGLE_LIMIT)):
    """How a piece stands against the targets: (area 95 %, angle 95 %, the biggest patch (cm²)
    over twice the limits, the worst patch's triangles or None). Passes when the percentiles are
    within the limits and no patch reaches REGION."""
    a, ang, st = measures(s1, s2)
    pa, pang = percentile(np.abs(a[painted]), area[painted]), percentile(ang[painted], area[painted])
    bad = painted & ((np.abs(a) > 2 * limits[0]) | (ang > 2 * limits[1]))
    lab, sizes = patches(F, n, bad, area)
    big = float(sizes.max()) if len(sizes) else 0.0
    worst = np.flatnonzero(lab == int(np.argmax(sizes))) if len(sizes) else None
    return pa, pang, big, worst


# ---- darts ----

def _cut(F, path, n):
    """The triangles cut along a path of vertices (the last on the boundary): the triangles on one
    side of the path take new copies of its inner vertices. Returns (F', n', copies): copies[k]
    is the original of new vertex n + k."""
    F = F.copy()
    path_edges = {tuple(sorted((path[k], path[k + 1]))) for k in range(len(path) - 1)}
    copies = []
    for v in path[1:]:  # the inner vertices, and the boundary vertex at the end (its fan opens too)
        ts = np.flatnonzero((F == v).any(1))
        nb = {}
        for t in ts:
            a, b = [x for x in F[t] if x != v]
            nb.setdefault(a, []).append((t, b))
            nb.setdefault(b, []).append((t, a))
        ends = [x for x in path if x in nb and tuple(sorted((v, x))) in path_edges]
        if not ends or (len(ends) < 2 and v != path[-1]):
            continue
        side, cur = set(), ends[0]
        while True:
            opts = [(t, o) for t, o in nb[cur] if t not in side]
            if not opts:
                break
            t, o = opts[0]
            side.add(t)
            if len(ends) > 1 and (o == ends[1] or o == ends[0]):
                break
            cur = o
        if len(side) == len(ts):
            continue
        rows = np.array(sorted(side))
        F[rows] = np.where(F[rows] == v, n, F[rows])
        copies.append(v)
        n += 1
    return F, n, copies


def _dart(V, F, s1, s2, area, painted, worst, strip=None):
    """The path of a dart through the worst patch: from its vertex deepest inside the piece,
    along the mesh's edges to the boundary, the way of least cost with cost = length / stretch
    (the cut follows the strain), and a tenth of that through the strips sewn across the gaps
    between panels (a cut there reopens the gap, a real opening, rather than the paint). Returns
    the vertices from the patch's heart out to the edge, or None."""
    n = len(V)
    a, ang, st = measures(s1, s2)
    region = np.unique(F[worst])
    vst = np.zeros(n)
    np.maximum.at(vst, F.reshape(-1), np.repeat(st, 3))
    e = _edges(F)
    L = np.linalg.norm(V[e[:, 0]] - V[e[:, 1]], axis=1)
    cost = L / np.maximum(0.5 * (vst[e[:, 0]] + vst[e[:, 1]]), 0.1)
    if strip is not None and strip.any():
        in_strip = np.zeros(n, bool)
        in_strip[F[strip].reshape(-1)] = True
        cost = np.where(in_strip[e[:, 0]] & in_strip[e[:, 1]], cost * 0.1, cost)
    G = coo_matrix((np.r_[cost, cost], (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()
    bv = np.unique(_boundary(F, n))
    d, pred, _ = dijkstra(G, indices=bv, return_predecessors=True, min_only=True)
    region = region[np.isfinite(d[region]) & ~np.isin(region, bv)]
    if not len(region):
        return None
    path = [int(region[np.argmax(d[region])])]
    while pred[path[-1]] >= 0:
        path.append(int(pred[path[-1]]))
    return path if len(path) > 2 else None


def flatten_piece(V, F, painted=None, limits=(AREA_LIMIT, ANGLE_LIMIT), darts=DARTS, log=print, strip=None):
    """One piece flattened, darts cut until the targets hold (or `darts` cuts). Returns (F', V',
    uv, origin, seams, (s1, s2, area)): F' over the vertices V' (the originals, then the cut
    copies, origin[i] the original of each), seams the darts as lists of original vertex ids."""
    V, F = np.asarray(V, np.float64), np.asarray(F, np.int64)
    origin = np.arange(len(V))
    painted = np.ones(len(F), bool) if painted is None else painted
    seams, last = [], None
    for round_ in range(darts + 1):
        uv = flatten(V, F)
        s1, s2, area = distortion(V, F, uv)
        pa, pang, big, worst = judge(F, len(V), s1, s2, area, painted, limits)
        log(f"    round {round_}: area 95 % {pa:.1f} %, angle 95 % {pang:.1f} deg, the biggest patch over twice "
            f"the limits {big:.0f} cm², folded {(s2 < 0).sum()}")
        if last is not None and pa > last[0][0] - 0.1 and pang > last[0][1] - 0.1 and big > last[0][2] - 2.0:
            F, V, uv, origin, (s1, s2, area) = last[1]  # the dart gained nothing: undone, and no more
            seams.pop()
            log("      the dart gained nothing: undone")
            break
        if (pa <= limits[0] and pang <= limits[1] and big < REGION) or round_ == darts or worst is None:
            break
        path = _dart(V, F, s1, s2, area, painted, worst, strip)
        if path is None:
            break
        F2, n2, copies = _cut(F, path, len(V))
        if not copies:
            break
        last = ((pa, pang, big), (F, V, uv, origin, (s1, s2, area)))
        V = np.concatenate([V, V[copies]])
        origin = np.concatenate([origin, origin[copies]])
        F = F2
        seams.append([int(origin[v]) for v in path])
        log(f"      dart {len(seams)}: {len(path)} vertices, from ({V[path[0]][0]:.0f}, {V[path[0]][1]:.0f}, {V[path[0]][2]:.0f}) out to the edge")
    return F, V, uv, origin, seams, (s1, s2, area)


# ---- the sheet ----

def _turn(uv, d):
    """uv turned so that direction d runs along +x."""
    d = d / max(np.linalg.norm(d), 1e-9)
    return uv @ np.array([[d[0], -d[1]], [d[1], d[0]]])


def _orient(V, F, uv, main, log=print):
    """A piece turned and flipped so that it is seen from outside with the nose at the left (the
    main piece by its top centreline, laid level; the others by the way z falls across them). Seen
    so, with y down as the sheet has it, the triangles wind clockwise; on the main piece the top
    centreline then lies along the upper edge and the flank hangs below it."""
    top = np.flatnonzero((np.abs(V[:, 0]) < 0.05) & (V[:, 1] > 40)) if main else np.zeros(0, int)
    if len(top) >= 8:
        p = uv[top]
        d = np.linalg.eigh(np.cov((p - p.mean(0)).T))[1][:, 1]
        if (uv[top][V[top, 2].argmax()] - p.mean(0)) @ d > 0:
            d = -d
    else:  # the least-squares gradient of z over the piece: the nose lies against it
        d = -np.linalg.lstsq(np.c_[uv, np.ones(len(uv))], V[:, 2], rcond=None)[0][:2]
    uv = _turn(uv, d)
    A, B, C = uv[F[:, 0]], uv[F[:, 1]], uv[F[:, 2]]
    if ((B - A)[:, 0] * (C - A)[:, 1] - (B - A)[:, 1] * (C - A)[:, 0]).sum() > 0:
        uv = uv * [1.0, -1.0]
    if len(top) >= 8 and uv[top, 1].mean() > np.median(uv[:, 1]):
        log("    the main piece's top centreline came out below its flank")
    return uv - uv.min(0)


def build(log=print):
    m = carmap.load()
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
    Vz, Fz_all, src_all, run_all, runs = _bridge(V, Fk, lab, cls, STITCH, big)
    log(f"sewn: {(src_all < 0).sum()} strip triangles bridge {len(runs)} joins between panels")
    dropped, best = set(), None
    while True:
        keep = ~np.isin(run_all, list(dropped)) | (run_all < 0)
        Fz, src, run_id = Fz_all[keep], src_all[keep], run_all[keep]
        tris_z, cls_z = np.where(src < 0, -1, tris[np.maximum(src, 0)]), cls[np.maximum(src, 0)]
        lab_z = _components(Fz, len(Vz), cls_z)
        Az, Bz, Cz = Vz[Fz[:, 0]], Vz[Fz[:, 1]], Vz[Fz[:, 2]]
        area_z = 0.5 * np.linalg.norm(np.cross(Bz - Az, Cz - Az), axis=1)
        parea = np.bincount(lab_z, weights=area_z)
        order = [int(p) for p in np.argsort(parea)[::-1] if parea[p] >= PIECE_MIN]
        pieces = []
        for k, p in enumerate(order):
            sel = np.flatnonzero(lab_z == p)
            names, counts = np.unique(pn[tris_z[sel][tris_z[sel] >= 0]], return_counts=True)
            name = PIECE_NAMES.get(names[np.argmax(counts)], names[np.argmax(counts)])
            vids, inv = np.unique(Fz[sel], return_inverse=True)
            Fl, n, origin0 = _split_fans(inv.reshape(-1, 3), len(vids))
            Vl = Vz[vids[origin0]]
            painted = (tris_z[sel] >= 0) & (open_t[np.maximum(tris_z[sel], 0)] >= PAINTED)
            log(f"piece {k}: {name} ({', '.join(names)}), {len(sel)} triangles, {parea[p]:.0f} cm², {n - len(vids)} pinch vertices split")
            F2, V2, uv, origin, seams, (s1, s2, area) = flatten_piece(Vl, Fl, painted, log=log, strip=tris_z[sel] < 0)
            uv = _orient(V2, F2, uv, k == 0, log)
            pieces.append(dict(name=name, src=tris_z[sel], F=F2, V=V2, uv=uv, seams=[V2[q] for q in seams], s1=s1, s2=s2, painted=painted,
                               run=run_id[sel]))
            if k == 0:
                verdict = judge(F2, len(V2), s1, s2, area, painted)[:3]
        pa, pang, big = verdict
        log(f"  the body with {len(runs) - len(dropped)} of {len(runs)} joins sewn: area 95 % {pa:.1f} %, angle 95 % {pang:.1f} deg, the biggest patch {big:.0f} cm²")
        if best is not None and not (pa < best[0][0] - 0.1 or pang < best[0][1] - 0.1 or big < best[0][2] - 2.0):
            log("  unsewing that join gained nothing: sewn again")
            pieces, dropped = best[1], best[2]
            break
        best = (verdict, pieces, set(dropped))
        if pa <= AREA_LIMIT and pang <= ANGLE_LIMIT and big < REGION:
            break
        # the body misses its targets: unsew every join whose surroundings strain (the paint within
        # 6 cm bent over UNSEW degrees on average); those joins stay open, at the model's own gaps
        main = pieces[0]
        present = [int(r) for r in np.unique(main["run"]) if r >= 0]
        ang_ = measures(main["s1"], main["s2"])[1]
        cen = main["V"][main["F"]].mean(1)
        loose = []
        for r in present:
            near = cKDTree(cen[main["run"] == r]).query(cen)[0] < 6.0
            v = float(np.mean(ang_[near & main["painted"]])) if (near & main["painted"]).any() else 0.0
            if v > UNSEW:
                loose.append((v, r))
        if not loose:
            break
        for v, r in sorted(loose)[::-1]:
            dropped.add(r)
            where = runs[r][2]
            log(f"  unsewn: the join at ({where[0]:.0f}, {where[1]:.0f}, {where[2]:.0f}): the paint round it bent {v:.1f} deg")
    for p in pieces:
        p.pop("run")
    open_joins = np.array([runs[r][2] for r in sorted(dropped)]).reshape(-1, 3)
    main = pieces[0]
    y0 = main["uv"][:, 1].max() + GAP
    x = 0.0
    for p in sorted(pieces[1:], key=lambda p: -p["V"][:, 2].mean()):
        p["uv"] = p["uv"] + [x, y0]
        x += p["uv"][:, 0].max() - p["uv"][:, 0].min() + GAP
    offs = np.r_[0, np.cumsum([len(p["V"]) for p in pieces])]
    data = dict(version=VERSION, piece_names=np.array([p["name"] for p in pieces]),
                Vs=np.concatenate([p["V"] for p in pieces]),
                Fs=np.concatenate([p["F"] + offs[k] for k, p in enumerate(pieces)]),
                uv=np.concatenate([p["uv"] for p in pieces]).astype(np.float32),
                src=np.concatenate([p["src"] for p in pieces]),
                piece=np.concatenate([np.full(len(p["src"]), k) for k, p in enumerate(pieces)]),
                s1=np.concatenate([p["s1"] for p in pieces]).astype(np.float32),
                s2=np.concatenate([p["s2"] for p in pieces]).astype(np.float32),
                painted=np.concatenate([p["painted"] for p in pieces]),
                seam_pts=np.concatenate([s for p in pieces for s in p["seams"]] or [np.zeros((0, 3))]).astype(np.float32),
                seam_starts=np.r_[0, np.cumsum([len(s) for p in pieces for s in p["seams"]])].astype(np.int64),
                seam_piece=np.array([k for k, p in enumerate(pieces) for s in p["seams"]], np.int64),
                open_joins=open_joins)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE, **data)
    load.cache_clear()
    return load()


class Sheet:
    def __init__(self, data):
        self.m = carmap.load()
        self.piece_names = list(data["piece_names"])
        self.Vs, self.Fs, self.uv = data["Vs"], data["Fs"], data["uv"].astype(np.float64)
        self.tri, self.piece = data["src"], data["piece"]  # the map's triangle each sheet triangle came from
        self.s1, self.s2, self.painted = data["s1"], data["s2"], data["painted"]
        st = data["seam_starts"]
        self.seams = [(int(data["seam_piece"][i]), data["seam_pts"][st[i]:st[i + 1]]) for i in range(len(st) - 1)]
        self.open_joins = data["open_joins"]  # joins between panels left unsewn (sewing them strained the paint), (k, 3)
        self.corner_uv = self.uv[self.Fs]         # (T, 3, 2)
        self.corners = self.Vs[self.Fs]           # (T, 3, 3) on the body
        # the map's triangle -> its sheet triangles (a fan where a panel was sewn), as a padded table
        real = np.flatnonzero(self.tri >= 0)
        order = real[np.argsort(self.tri[real], kind="stable")]
        u, first, cnt = np.unique(self.tri[order], return_index=True, return_counts=True)
        self._fan = np.full((len(self.m.F), int(cnt.max())), -1, np.int64)
        for k in range(int(cnt.max())):
            has = cnt > k
            self._fan[u[has], k] = order[first[has] + k]
        self._tree = None
        self._lines = None
        self._last = None

    @property
    def size(self):
        """The sheet's extent (cm): (width, height)."""
        return tuple(self.uv.max(0))

    def top_y(self, x):
        """The top centreline's y on the sheet at sheet x (cm): the body piece's corners on the
        car's middle line, interpolated (the line runs nearly level, but not exactly)."""
        if not hasattr(self, "_top"):
            on = (self.piece[:, None] == 0) & (np.abs(self.corners[:, :, 0]) < 0.05) & (self.corners[:, :, 1] > 40)
            p = np.unique(np.round(self.corner_uv[on], 4), axis=0)
            self._top = p[np.argsort(p[:, 0])]
        return np.interp(np.asarray(x, np.float64), self._top[:, 0], self._top[:, 1])

    def piece_mesh(self, k):
        """Piece k as its own mesh: (V (n, 3) on the body, F (m, 3), uv (n, 2), the sheet
        triangle index per face). A dart's two sides are apart, and the mesh is manifold, as the
        geometry libraries need."""
        sel = np.flatnonzero(self.piece == k)
        vids, inv = np.unique(self.Fs[sel], return_inverse=True)
        return self.Vs[vids], inv.reshape(-1, 3), self.uv[vids], sel

    # ---- from the body to the sheet ----

    @staticmethod
    def _bary(A, B, C, pos):
        e1, e2, d = B - A, C - A, pos - A
        d11, d12, d22 = (e1 * e1).sum(-1), (e1 * e2).sum(-1), (e2 * e2).sum(-1)
        dd1, dd2 = (d * e1).sum(-1), (d * e2).sum(-1)
        det = np.maximum(d11 * d22 - d12 * d12, 1e-12)
        b1 = (d22 * dd1 - d12 * dd2) / det
        b2 = (d11 * dd2 - d12 * dd1) / det
        return np.stack([1 - b1 - b2, b1, b2], -1)

    def uv_in(self, t, pos):
        """Sheet coordinates of points pos (n, 3) known to lie on the map's triangles t (n,): the
        sheet triangle of that triangle's fan the point falls in (or nearest), its weights there,
        then the corners' sheet places. NaN where the triangle isn't on the sheet."""
        pos = np.asarray(pos, np.float64)
        fan = self._fan[t]                                    # (n, K)
        out = np.full((len(t), 2), np.nan)
        best = np.full(len(t), -np.inf)
        for k in range(fan.shape[1]):
            f = fan[:, k]
            on = f >= 0
            if not on.any():
                continue
            c = self.corners[f[on]]
            b = self._bary(c[:, 0], c[:, 1], c[:, 2], pos[on])
            score = b.min(1)
            better = np.zeros(len(t), bool)
            better[on] = score > best[on]
            best[better] = score[better[on]]
            bb = b[better[on]]  # unclamped: a point just outside its triangle (a mirror twin 2 mm off) extends the map affinely
            out[better] = (bb[:, :, None] * self.corner_uv[f[better]]).sum(1)
        return out

    def _lookup(self):
        if self._tree is None:
            f, b = self.m._samples()
            on = self._fan[f, 0] >= 0
            f, b = f[on], b[on]
            p = (b[:, :, None] * self.m.V[self.m.F[f]]).sum(1)
            self._tree, self._sf = cKDTree(p), f
        return self._tree

    def uv_at(self, pos, nrm=None, reach=1.5):
        """Sheet coordinates of any points (n, 3) on or near the body: the nearest sheet triangle
        facing their way (the right side mirrored onto the left), within `reach` cm; NaN beyond."""
        pos = np.asarray(pos, np.float64)
        key = (pos.shape, pos[:1].tobytes(), pos[-1:].tobytes())
        if self._last is not None and self._last[0] == key:
            return self._last[1]
        flip = np.where(pos[:, 0] < 0, -1.0, 1.0)
        p = pos * np.c_[flip, np.ones(len(pos)), np.ones(len(pos))]
        tree = self._lookup()
        d, i = tree.query(p, k=6, workers=-1)
        pick = np.zeros(len(p), np.int64)
        if nrm is not None:
            n = np.asarray(nrm, np.float64) * np.c_[flip, np.ones(len(pos)), np.ones(len(pos))]
            agree = (self.m.fn[self._sf[i]] * n[:, None, :]).sum(2) > 0.2
            pick = np.where(agree.any(1), np.argmax(agree, axis=1), 0)
        r = np.arange(len(p))
        t = self._sf[i[r, pick]]
        a, nn = self.m.V[self.m.F[t, 0]], self.m.fn[t]
        q = p - ((p - a) * nn).sum(1, keepdims=True) * nn
        out = self.uv_in(t, q)
        out[d[r, pick] > reach] = np.nan
        self._last = (key, out)
        return out

    # ---- from the sheet to the body ----

    def _sheet_tree(self):
        if not hasattr(self, "_stree"):
            self._stree = cKDTree(self.corner_uv.mean(1))
        return self._stree

    def at(self, uv, k=12):
        """The sheet's triangle under points uv (n, 2) and the points' barycentric weights in it
        (the nearest triangle's when none holds the point; -1 when none is within 3 cm)."""
        uv = np.asarray(uv, np.float64)
        d, i = self._sheet_tree().query(uv, k=k, workers=-1)
        C = self.corner_uv[i]
        A, B, Cc = C[:, :, 0], C[:, :, 1], C[:, :, 2]
        det = (B[..., 0] - A[..., 0]) * (Cc[..., 1] - A[..., 1]) - (B[..., 1] - A[..., 1]) * (Cc[..., 0] - A[..., 0])
        det = np.where(np.abs(det) < 1e-12, 1e-12, det)
        P = uv[:, None, :]
        w1 = ((P[..., 0] - A[..., 0]) * (Cc[..., 1] - A[..., 1]) - (P[..., 1] - A[..., 1]) * (Cc[..., 0] - A[..., 0])) / det
        w2 = ((B[..., 0] - A[..., 0]) * (P[..., 1] - A[..., 1]) - (B[..., 1] - A[..., 1]) * (P[..., 0] - A[..., 0])) / det
        w0 = 1 - w1 - w2
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        pick = np.where(inside.any(1), np.argmax(inside, 1), 0)
        r = np.arange(len(uv))
        bary = np.clip(np.stack([w0[r, pick], w1[r, pick], w2[r, pick]], 1), 0, 1)
        bary /= np.maximum(bary.sum(1, keepdims=True), 1e-9)
        t = np.where(d[r, pick] > 3.0, -1, i[r, pick])
        return t, bary

    def to_body(self, uv):
        """Points on the body (n, 3), on the left side, under sheet points uv; NaN off the sheet."""
        t, bary = self.at(uv)
        out = np.full((len(t), 3), np.nan)
        on = t >= 0
        out[on] = (bary[on][:, :, None] * self.corners[t[on]]).sum(1)
        return out

    # ---- the map's lines on the sheet ----

    @property
    def lines(self):
        """The map's lines as sheet polylines (cm): shoulder, lower, fold (the fitted curves, the
        left side), opening, join (the mesh's own edges), seam (the darts, both sides), outline
        (each piece's boundary), each a list of (n, 2) arrays."""
        if self._lines is None:
            self._lines = {}
            for name, kind in (("shoulder", 0), ("lower", 1), ("fold", 2)):
                self._lines[name] = [q for c in self.m.curves if c["kind"] == kind for q in self._on_sheet(c["pts"].astype(np.float64))]
            for name in ("opening", "join"):
                pts = self.m.lines[name].astype(np.float64)
                self._lines[name] = self._chains(pts[pts[:, 0] > -0.05])
            self._lines["seam"] = [q for _, s in self.seams for q in self._seam_sides(s)]
            self._lines["outline"] = self._outlines()
        return self._lines

    def _on_sheet(self, pts):
        """A dense 3D polyline as sheet polylines, split where it leaves the sheet or jumps (a seam,
        another piece)."""
        uv = self.uv_at(pts, self.m.value("ns", pts))
        out, cur = [], []
        for k in range(len(uv)):
            if not np.isfinite(uv[k]).all() or (cur and np.linalg.norm(uv[k] - cur[-1]) > 1.0):  # a jump: a seam, another piece
                if len(cur) >= 16:  # 4 cm or more
                    out.append(np.array(cur))
                cur = []
            if np.isfinite(uv[k]).all():
                cur.append(uv[k])
        if len(cur) >= 16:
            out.append(np.array(cur))
        return out

    def _chains(self, pts):
        """Edge points (0.4 cm apart, unordered) as sheet polylines: chained by nearness on the sheet."""
        uv = self.uv_at(pts, self.m.value("ns", pts))
        uv = uv[np.isfinite(uv).all(1)]
        if not len(uv):
            return []
        tree = cKDTree(uv)
        used = np.zeros(len(uv), bool)
        out = []
        for s in range(len(uv)):
            if used[s]:
                continue
            chain = [s]
            used[s] = True
            for direction in (0, 1):
                cur = chain[-1] if direction == 0 else chain[0]
                while True:
                    cand = [c for c in tree.query_ball_point(uv[cur], 0.7) if not used[c]]
                    if not cand:
                        break
                    nxt = min(cand, key=lambda c: np.linalg.norm(uv[c] - uv[cur]))
                    used[nxt] = True
                    chain.append(nxt) if direction == 0 else chain.insert(0, nxt)
                    cur = nxt
            if len(chain) >= 6:
                out.append(uv[chain])
        return out

    def _seam_sides(self, pts3):
        """A dart's two sides on the sheet: the sheet places of the vertex copies along the seam,
        each copy put on the side of the seam's own line it lies on."""
        tree = cKDTree(self.Vs)
        copies = [np.unique(np.round(self.uv[tree.query_ball_point(p, 1e-3)], 4), axis=0) for p in pts3]
        pts = [c.mean(0) for c in copies]
        if len(pts) < 2:
            return []
        d = pts[-1] - pts[0]  # the seam's line, from the tip to the edge
        sides = [[], []]
        for c, q in zip(copies, pts):
            if len(c) == 1:
                sides[0].append(c[0])
                sides[1].append(c[0])
                continue
            cross = [(x - q)[0] * d[1] - (x - q)[1] * d[0] for x in c]
            order = np.argsort(cross)
            sides[0].append(c[order[0]])
            sides[1].append(c[order[-1]])
        return [np.array(s) for s in sides]

    def _outlines(self):
        """Each piece's boundary on the sheet as closed polylines."""
        out = []
        for k in range(len(self.piece_names)):
            V, F, uv, _ = self.piece_mesh(k)
            b = _boundary(F, len(V))
            nxt = {}
            for i, j in b:
                nxt.setdefault(int(i), []).append(int(j))
            seen = set()
            for i, _ in b:
                if int(i) in seen:
                    continue
                loop, cur = [int(i)], int(i)
                while True:
                    seen.add(cur)
                    cand = [j for j in nxt.get(cur, []) if j not in seen]
                    if not cand:
                        break
                    cur = cand[0]
                    loop.append(cur)
                if len(loop) >= 3:
                    out.append(uv[loop + ([loop[0]] if nxt.get(cur) and loop[0] in nxt[cur] else [])])
        return out


@functools.lru_cache(maxsize=1)
def load():
    if not CACHE.exists() or CACHE.stat().st_mtime < carmap.CACHE.stat().st_mtime:
        return build()
    data = np.load(CACHE)
    if int(data["version"]) != VERSION:
        return build()
    return Sheet(dict(data))


# ---- every texel's place on the sheet ----

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


def sheet_cm(texture_set, width, height):
    """(h, w, 2) float32: each texel's sheet coordinates (cm), NaN off the sheet (the wheel covers,
    the inner car, hidden skin). Left texels through their own triangle, right texels through the
    mirrored one (the mesh's triangulation is mirrored but for a few triangles round the number
    panel, which go by the nearest); cached next to the bake."""
    from tool import bake
    if texture_set != "Skin":
        return np.full((height, width, 2), np.nan, np.float32)
    cache = paths.CACHE / f"sheet_{texture_set}_{width}x{height}.npy"
    sheet = load()
    if cache.exists() and cache.stat().st_mtime > CACHE.stat().st_mtime:
        return np.load(cache)
    b = bake.bake(texture_set, width, height)
    tri, pos, nrm = b["tri"].reshape(-1), b["position"].reshape(-1, 3).astype(np.float64), b["normal"].reshape(-1, 3).astype(np.float64)
    m = sheet.m
    out = np.full((height * width, 2), np.nan, np.float32)
    cov = np.flatnonzero(tri >= 0)
    t = tri[cov]
    p = pos[cov]
    flip = np.where(p[:, 0] < -0.05, -1.0, 1.0)
    mirror = _twins(m)
    tt = np.where(flip < 0, mirror[t], t)
    pm = p * np.c_[flip, np.ones(len(p)), np.ones(len(p))]
    ok = (tt >= 0) & (sheet._fan[np.maximum(tt, 0), 0] >= 0)
    out[cov[ok]] = sheet.uv_in(tt[ok], pm[ok])
    # the rest by the nearest sheet triangle facing their way: only skin the sheet would hold (not a
    # wheel cover, a blade or hidden skin): a loose piece too small for the sheet (a rivet on the
    # surround, the fin's blade), a right triangle without a mirror twin
    pn = m.part_names[m.part]
    open_t = m.layers["open"][m.F].mean(1)
    fine = ~np.isin(pn, carmap.WHEEL_COVERS + BLADES) & (open_t >= HIDDEN)
    rest = cov[~ok & fine[t]]
    if len(rest):
        out[rest] = sheet.uv_at(pos[rest], nrm[rest])
    # a right triangle without a mirror twin (the model triangulates the number panel's surround
    # differently on the two sides) goes by its corners' mirror vertices, which do exist, so its
    # texels agree with their neighbours' where the shell is doubled and the nearest lookup could
    # take either layer
    twinless = np.flatnonzero(~ok & fine[t] & (flip < 0) & (tri[cov] >= 0))
    if len(twinless):
        vt = cKDTree(sheet.Vs)
        corner_uv = np.full((len(m.V), 2), np.nan)
        rv = np.unique(m.F[t[twinless]])
        for v in rv:
            hits = vt.query_ball_point(m.V[v] * [-1, 1, 1], 0.15)
            hits = [h for h in hits if (sheet.piece[np.flatnonzero((sheet.Fs == h).any(1))[:1]] == 0).all()] if hits else []
            if hits:
                corner_uv[v] = sheet.uv[hits].mean(0)
        c = corner_uv[m.F[t[twinless]]]  # (n, 3, 2)
        good = np.isfinite(c).all((1, 2))
        if good.any():
            tt_ = t[twinless][good]
            A_, B_, C_ = m.V[m.F[tt_, 0]], m.V[m.F[tt_, 1]], m.V[m.F[tt_, 2]]
            bary = Sheet._bary(A_, B_, C_, p[twinless][good])
            out[cov[twinless][good]] = (bary[:, :, None] * c[good]).sum(1)
    out = out.reshape(height, width, 2)
    np.save(cache, out)
    return out


if __name__ == "__main__":
    import time
    t0 = time.time()
    s = build()
    print(f"built in {time.time() - t0:.0f} s: {len(s.piece_names)} pieces, {len(s.Fs)} triangles, {len(s.seams)} darts, sheet {s.size[0]:.0f} x {s.size[1]:.0f} cm")
    a, ang, st = measures(s.s1, s.s2)
    ar = 0.5 * np.linalg.norm(np.cross(s.corners[:, 1] - s.corners[:, 0], s.corners[:, 2] - s.corners[:, 0]), axis=1)
    for k, name in enumerate(s.piece_names):
        sel = (s.piece == k) & s.painted
        pa, pang, big, _ = judge(s.Fs, len(s.Vs), s.s1, s.s2, ar, sel)
        print(f"  {name:20} painted {ar[sel].sum():6.0f} cm²: area 95 % {pa:4.1f} %, angle 95 % {pang:4.1f} deg, "
              f"stretch 95 % {percentile(st[sel], ar[sel]):4.1f} %, the biggest patch over twice the limits {big:.0f} cm²")
