"""The model's own lines: the edges the car's body is built from, the lines of the UV map's wireframe, each known on
the car and on the map at once: the template to design on. Read off the model's triangles alone: nothing traced from
the texture, nothing from the car map, no light or shading (the user, 2026-10-06: "doing it with the exact lines that
the model had all along"; "Your new method ... shouldnt be needing shadows anyways to design properly").

    meshlines.template("Skin")           the model's lines on one of the game's maps: its creases (crisp lines and panel
                                    lines), where the body ends, and where the map is cut while the car carries on;
                                    the Lab's UV map room draws them (view.export_template)
    meshlines.mesh("Skin")               every edge of the model's triangles on the car and on the map, with how much the
                                    body bends across it (+ outward: a rounded edge is a run of them; - inward); the
                                    template draws the mesh by it, on the maps and on the car
    meshlines.line((35, 71, 9), least=100)   the template's line nearest a point, a Course exactly through the model's
                                    points: .strip(0.6) a line on it (a panel line's groove is 0.3 to 0.4 cm wide, and
                                    the line is on one of its walls); along where the body ends a strip is half on it
    meshlines.panel((25, 80, 11))        the model's own panel under a point (bounded by its creases and the body's
                                    edges), a zone filled right up to its lines; both=True the mirror image's too;
                                    border=1.5 only a trim that far inside its edge
    meshlines.picked([(70, 60, -70), (55, 63, -100)])   the line through points clicked on the car (the Lab: Mesh
                                    and Draw on), a Course on the model: each click lands on the nearest of the model's
                                    points, where its lines cross; between two joined by an edge, that edge; on one of
                                    its lines, along it point by point; else straight across the surface
    PY -m tool.meshlines            the body's panels and its longest lines, each with a point on it and its parts
"""

import functools

import numpy as np
from scipy.sparse import coo_matrix
from scipy.spatial import cKDTree

from tool.noise import smoothstep

WELD = 1e-3   # cm: the model's points this close are one point
SHARP = 30.0  # degrees: where the model's two triangles meet at this angle or more, one of its crisp lines (a panel
# line's walls, a knife edge, an opening's lip); along a rolled edge each of its lines turns 5 to 10 degrees
SEWN = 0.15   # cm: an edge of one of the model's pieces this near another piece's is sewn to it (they meet within 0.12 mm)
CUT = 1e-4    # how far apart (the map's width is 1) an edge's two triangles may place it and still be one place
WALLS = 0.4   # cm: a line all within this of a longer one is a wall of the same panel line (a groove is two or three)


@functools.lru_cache(maxsize=4)
def _edges(tset):
    """The model's edges on one of the game's maps, sorted: its triangles' welded points (T into P), and for the edges
    two triangles share (h1, h2: half-edges) and those with one (hb), where each lies on the car and on the map, and
    which are creases, cuts and sewn, how much the body bends across each (bend, degrees, + outward); each triangle's
    piece."""
    from scipy.sparse.csgraph import connected_components
    from tool import fbx
    m = fbx.meshes()[fbx.MESH_OF[tset]]
    p0, tv = m["positions"].astype(np.float64), m["tri_vertex"]
    X, UV, tn = p0[tv], m["tri_uv"].astype(np.float64), m["tri_normal"].astype(np.float64)
    fn = np.cross(X[:, 1] - X[:, 0], X[:, 2] - X[:, 0])
    fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
    fn *= np.where((fn * tn.mean(1)).sum(1) < 0, -1.0, 1.0)[:, None]  # facing out, as the shading does
    _, first, inv = np.unique(np.round(p0 / WELD).astype(np.int64), axis=0, return_index=True, return_inverse=True)
    T = inv.ravel()[tv]
    # every triangle's three edges: (triangle, its two corners), keyed by the welded points they join
    tri = np.repeat(np.arange(len(T)), 3)
    cor = np.tile(np.array([[0, 1], [1, 2], [2, 0]]), (len(T), 1))
    a, b = T[tri, cor[:, 0]], T[tri, cor[:, 1]]
    ok = a != b
    tri, cor, a, b = tri[ok], cor[ok], a[ok], b[ok]
    key = np.minimum(a, b) * (int(T.max()) + 1) + np.maximum(a, b)
    order = np.argsort(key, kind="stable")
    start = np.r_[0, np.flatnonzero(np.diff(key[order])) + 1]
    count = np.diff(np.r_[start, len(order)])

    def on(h, flip=None):
        """Half-edges h on the car and on the map, from its first corner to its second (or the other way, flip)."""
        c0, c1 = cor[h, 0], cor[h, 1]
        if flip is not None:
            c0, c1 = np.where(flip, c1, c0), np.where(flip, c0, c1)
        return np.stack([X[tri[h], c0], X[tri[h], c1]], 1), np.stack([UV[tri[h], c0], UV[tri[h], c1]], 1)

    h1, h2 = order[start[count == 2]], order[start[count == 2] + 1]
    s1, u1 = on(h1)
    s2, u2 = on(h2, flip=a[h2] != a[h1])
    cut = np.abs(u1 - u2).reshape(len(h1), -1).max(1) > CUT
    bend = np.degrees(np.arccos(np.clip((fn[tri[h1]] * fn[tri[h2]]).sum(1), -1, 1)))
    crease = bend >= SHARP
    # outward where the second triangle falls away behind the first one's face (a rounded edge), inward where it rises
    bend *= np.where(((X[tri[h2]].mean(1) - s1[:, 0]) * fn[tri[h1]]).sum(1) > 0, -1.0, 1.0)
    # the model's pieces (triangles joined edge to edge), and their edges sewn to another piece's
    n = len(T)
    _, piece = connected_components(coo_matrix((np.ones(len(h1)), (tri[h1], tri[h2])), shape=(n, n)), directed=False)
    hb = order[start[count == 1]]
    sb, ub = on(hb)
    t = np.linspace(0.0, 1.0, 5)
    ln = np.linalg.norm(sb[:, 1] - sb[:, 0], axis=1)
    k = np.maximum(2, np.ceil(ln / 0.05).astype(int))
    dense = np.concatenate([sb[i, 0] + (sb[i, 1] - sb[i, 0]) * np.linspace(0, 1, k[i])[:, None] for i in range(len(hb))])
    owner = np.repeat(piece[tri[hb]], k)
    probe = (sb[:, :1] + (sb[:, 1:] - sb[:, :1]) * t[None, :, None]).reshape(-1, 3)
    near = cKDTree(dense).query_ball_point(probe, SEWN)
    mine = np.repeat(piece[tri[hb]], len(t))
    other = np.array([any(owner[j] != p for j in js) for js, p in zip(near, mine)]).reshape(len(hb), len(t))
    sewn = other.sum(1) >= len(t) - 1
    N = np.zeros((len(first), 3))
    np.add.at(N, T.ravel(), tn.reshape(-1, 3))  # each point's normal: its corners' mean
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    return dict(T=T, P=p0[first], N=N, tri=tri, a=a, b=b, h1=h1, h2=h2, hb=hb, s1=s1, u1=u1, s2=s2, u2=u2, sb=sb, ub=ub,
                cut=cut, crease=crease, bend=bend, sewn=sewn, piece=piece)


@functools.lru_cache(maxsize=4)
def mesh(tset="Skin"):
    """Every edge of the model's triangles: on the car (n, 2, 3) cm, on the map (n, 2, 2) uv, v up, and how much the
    body bends across it (n,): the angle between its two triangles, degrees, + outward (a rounded edge is a run of
    them side by side, 5 to 10 degrees each), - inward (an indentation), 0 where the body ends. An edge where the map is
    cut is on the map twice, once on each side."""
    e = _edges(tset)
    cut = e["cut"]
    s = np.concatenate([e["s1"], e["s2"][cut], e["sb"]])
    u = np.concatenate([e["u1"], e["u2"][cut], e["ub"]])
    bend = np.concatenate([e["bend"], e["bend"][cut], np.zeros(len(e["hb"]))])
    return s.astype(np.float32), u.astype(np.float32), bend.astype(np.float32)


@functools.lru_cache(maxsize=4)
def template(tset="Skin"):
    """The model's own lines on one of the game's maps (Skin, Details, Wheels, Glass), each known on the car and on the
    map at once: {kind: (segments on the car (n, 2, 3) cm, the same on the map (n, 2, 2) uv, v up)}, read off the
    model's triangles, nothing traced:
      crease   an edge where its two triangles meet at SHARP degrees or more: the model's crisp lines (panel lines,
               knife edges, the lips round its openings)
      opening  an edge with one triangle and no other piece of the model sewn to it: where the body ends
      cut      an edge whose two triangles lie apart on the map, or a piece's edge sewn to another piece's: where the
               map is cut while the car carries on (on the map twice, once on each side)
    A crease on a cut is on the map twice too."""
    e = _edges(tset)
    crease, cut, sewn = e["crease"], e["cut"], e["sewn"]
    out = {
        "crease": (np.concatenate([e["s1"][crease], e["s2"][crease & cut]]), np.concatenate([e["u1"][crease], e["u2"][crease & cut]])),
        "opening": (e["sb"][~sewn], e["ub"][~sewn]),
        "cut": (np.concatenate([e["s1"][cut], e["s2"][cut], e["sb"][sewn]]),
                np.concatenate([e["u1"][cut], e["u2"][cut], e["ub"][sewn]])),
    }
    return {kind: (s.astype(np.float32), u.astype(np.float32)) for kind, (s, u) in out.items()}


def _parts_of(tset):
    """Each triangle's part name, from the parts list."""
    from tool import parts
    p = parts.load()
    off = p.mesh_offset[tset]
    n = len(_edges(tset)["T"])
    names = np.array([inst["name"] for inst in p.instances])
    return names[p.tri_part[off:off + n]]


def _most(names):
    u, c = np.unique(names, return_counts=True)
    return [str(x) for x in u[np.argsort(-c)]]


@functools.lru_cache(maxsize=8)
def lines(tset="Skin", fold=True):
    """The model's lines (template's creases and openings) joined end to end into lines: a list of dicts, the longest
    first: kind ("crease", "opening"), pts (on the car, cm, in order), closed (a loop), length (cm), parts (those it runs
    along, most first), walls (a panel line drawn as a groove is two or three creases WALLS apart: the shorter ones are
    folded into the longest, counted here; fold=False keeps each)."""
    e = _edges(tset)
    names = _parts_of(tset)
    out = []
    for kind, (a, b, tris) in (("crease", (e["a"][e["h1"]][e["crease"]], e["b"][e["h1"]][e["crease"]],
                                           np.c_[e["tri"][e["h1"]], e["tri"][e["h2"]]][e["crease"]])),
                               ("opening", (e["a"][e["hb"]][~e["sewn"]], e["b"][e["hb"]][~e["sewn"]],
                                            e["tri"][e["hb"]][~e["sewn"]][:, None]))):
        nbr, by = {}, {}
        for k, (u, v) in enumerate(zip(a, b)):
            nbr.setdefault(u, []).append(v)
            nbr.setdefault(v, []).append(u)
            by[(min(u, v), max(u, v))] = k
        seen = set()

        def walk(u, v):
            path, edges = [u, v], [by[(min(u, v), max(u, v))]]
            seen.add(edges[0])
            while len(nbr[v]) == 2:
                w = nbr[v][0] if nbr[v][0] != path[-2] else nbr[v][1]
                k = by[(min(v, w), max(v, w))]
                if k in seen:
                    break
                seen.add(k)
                path.append(w)
                edges.append(k)
                v = w
            return path, edges

        found = []
        for u in nbr:  # paths between ends and branchings, then the loops left
            if len(nbr[u]) != 2:
                for v in nbr[u]:
                    if by[(min(u, v), max(u, v))] not in seen:
                        found.append(walk(u, v))
        for u in nbr:
            for v in nbr[u]:
                if by[(min(u, v), max(u, v))] not in seen:
                    found.append(walk(u, v))
        for path, edges in found:
            pts = e["P"][path]
            closed = path[0] == path[-1] and len(path) > 3
            out.append(dict(kind=kind, pts=pts, nrm=e["N"][path], closed=closed, length=float(np.linalg.norm(np.diff(pts, axis=0), axis=1).sum()),
                            parts=_most(names[tris[edges].ravel()]), walls=1))
    out.sort(key=lambda L: -L["length"])
    if not fold:
        return out
    kept = []
    for L in out:  # a groove's walls fold into its longest line
        host = next((K for K in kept if K["kind"] == L["kind"] and L["length"] <= K["length"]
                     and cKDTree(K["pts"]).query(L["pts"])[0].max() <= WALLS), None) if L["length"] < 200 else None
        if host is not None:
            host["walls"] += 1
        else:
            kept.append(L)
    return kept


def line(near, kind=None, least=3.0, tset="Skin"):
    """The model's line nearest a point (x, y, z) on the car, of `kind` ("crease" or "opening") or either, `least` cm
    long or more: a Course along it, exactly through the model's points (closed round a loop)."""
    from tool import course
    at = np.asarray(near, np.float64)
    pool = [L for L in lines(tset) if L["length"] >= least and (kind is None or L["kind"] == kind)]
    L = min(pool, key=lambda L: float(np.linalg.norm(L["pts"] - at, axis=1).min()))
    words = {"crease": "crisp line", "opening": "edge where the body ends"}[L["kind"]]
    k = slice(0, -1) if L["closed"] else slice(None)
    c = course.Course(L["pts"][k], f"the model's {words} along the {L['parts'][0]} near {course._said(at)}", nrm=L["nrm"][k],
                      closed=L["closed"])
    c.model = L
    return c


@functools.lru_cache(maxsize=4)
def _panels(tset):
    """Each triangle's panel: the model's triangles joined edge to edge wherever they don't meet at a crease."""
    from scipy.sparse.csgraph import connected_components
    e = _edges(tset)
    smooth = ~e["crease"]
    t1, t2 = e["tri"][e["h1"]][smooth], e["tri"][e["h2"]][smooth]
    n = len(e["T"])
    return connected_components(coo_matrix((np.ones(len(t1)), (t1, t2)), shape=(n, n)), directed=False)[1]


def _triangle_at(point, tset="Skin"):
    """The model's triangle nearest a point."""
    return _closest(point, tset)[0]


def _closest(point, tset="Skin"):
    """The model's triangle nearest a point, and the point on it nearest."""
    e = _edges(tset)
    X = e["P"][e["T"]]
    tree = _centres(tset)
    _, cand = tree.query(point, k=min(24, len(X)))
    best, bd, on = None, np.inf, None
    for t in np.atleast_1d(cand):
        a, b, c = X[t]
        n = np.cross(b - a, c - a)
        n /= max(np.linalg.norm(n), 1e-12)
        q = point - ((point - a) @ n) * n
        bary = np.linalg.lstsq(np.c_[b - a, c - a], q - a, rcond=None)[0]
        u, v = np.clip(bary, 0, 1)
        if u + v > 1:
            u, v = u / (u + v), v / (u + v)
        q = a + u * (b - a) + v * (c - a)
        d = np.linalg.norm(point - q)
        if d < bd:
            best, bd, on = t, d, q
    return best, on


@functools.lru_cache(maxsize=4)
def _centres(tset):
    e = _edges(tset)
    return cKDTree(e["P"][e["T"]].mean(1))


def panel(near, both=False, border=None, soft=None, size=4096):
    """The model's own panel under a point (x, y, z) on the body: every triangle reached from it without crossing a
    crease, painted right up to its creases and the body's edges, as a zone for s.paint(..., zone=); `both`: and its
    mirror image's on the other side; `border`: only the band that many cm inside its edge (a trim round an opening,
    a panel's outline). Its edge is the model's line itself, feathered over `soft` cm (shapes.SOFT). The body (Skin)."""
    from tool import bake, course, shapes
    soft = shapes.SOFT if soft is None else soft
    e, lab = _edges("Skin"), _panels("Skin")
    pts = [np.asarray(near, np.float64)] + ([np.asarray(near, np.float64) * [-1, 1, 1]] if both else [])
    sel = np.zeros(lab.max() + 1, bool)
    for p in pts:
        sel[lab[_triangle_at(p)]] = True
    # its edge: the creases with it on one side only, and the body's edges round it
    t1, t2 = e["tri"][e["h1"]], e["tri"][e["h2"]]
    rim = np.concatenate([e["s1"][sel[lab[t1]] != sel[lab[t2]]], e["sb"][sel[lab[e["tri"][e["hb"]]]]]])
    ln = np.linalg.norm(rim[:, 1] - rim[:, 0], axis=1)
    k = np.maximum(2, np.ceil(ln / 0.02).astype(int))
    edge = np.concatenate([rim[i, 0] + (rim[i, 1] - rim[i, 0]) * np.linspace(0, 1, k[i])[:, None] for i in range(len(rim))])
    b = bake.bake("Skin", size, size)
    tri, pos = b["tri"].reshape(-1), b["position"].reshape(-1, 3)
    on = tri >= 0
    inside = np.zeros(len(tri), bool)
    inside[on] = sel[lab[tri[on]]]
    lo, hi = edge.min(0) - soft, edge.max(0) + soft
    idx = np.flatnonzero(on & (inside | np.all((pos >= lo) & (pos <= hi), axis=1)))
    reach = max(soft, border or 0.0) + soft
    d = cKDTree(edge).query(pos[idx].astype(np.float64), distance_upper_bound=reach, workers=-1)[0]
    signed = np.where(inside[idx], np.minimum(d, reach), -np.minimum(d, reach))
    w = smoothstep(-soft / 2, soft / 2, signed)
    if border is not None:
        w = w * smoothstep(-soft / 2, soft / 2, border - signed)
    keep = w > 0.002
    words = "panel" if border is None else f"{border:g} cm border inside the panel"
    return course.Course._matched(pos[idx[keep]].astype(np.float64), w[keep].astype(np.float32),
                                  label=f"the model's {words} at {course._said(np.asarray(near, np.float64))}" + (", both sides" if both else ""))


FLAT = 6.0        # degrees: an edge the body bends across less than this counts as more or less flat: on a panel the
# triangles' edges are only where the model was cut into triangles, and a rounded edge's own lines bend 5 to 20
FLAT_COST = 3.0   # how much further a flat edge counts for a click landing on it (less as it bends, to FLAT)
SEAM = 1.0        # cm: across a seam between the model's pieces, a point joins the nearest point of another piece
TURN = 40.0       # degrees: one of the model's lines goes on through a point along its edge turning least, if under this
STRAIGHT = 0.5    # cm between the points of a line straight across the surface


@functools.lru_cache(maxsize=4)
def _graph(tset):
    """The model's points joined by its edges: M, a sparse matrix of each edge's cost (its length, up to FLAT_COST
    times that the flatter it is), symmetric, with the pieces joined across their seams (SEAM); seam, each point's
    partner across a seam (-1: none)."""
    from scipy.sparse import csr_matrix
    e = _edges(tset)
    P = e["P"]
    u = np.r_[e["a"][e["h1"]], e["a"][e["hb"]]]
    v = np.r_[e["b"][e["h1"]], e["b"][e["hb"]]]
    bend = np.r_[np.abs(e["bend"]), np.full(len(e["hb"]), FLAT)]  # where the body ends is a line of its own
    rim = np.unique(np.r_[e["a"][e["hb"]], e["b"][e["hb"]]])
    piece = np.zeros(len(P), int)
    piece[e["T"].ravel()] = np.repeat(e["piece"], 3)
    seam = np.full(len(P), -1)
    for i, near in zip(rim, cKDTree(P[rim]).query_ball_point(P[rim], SEAM)):
        other = [rim[j] for j in near if piece[rim[j]] != piece[i]]
        if other:
            seam[i] = min(other, key=lambda j: float(np.linalg.norm(P[j] - P[i])))
    su = np.flatnonzero(seam >= 0)
    u, v, bend = np.r_[u, su].astype(np.int64), np.r_[v, seam[su]].astype(np.int64), np.r_[bend, np.full(len(su), FLAT)]
    w = np.maximum(np.linalg.norm(P[u] - P[v], axis=1) * (1 + (FLAT_COST - 1) * np.clip(1 - bend / FLAT, 0, 1)), 1e-6)
    lo, hi = np.minimum(u, v), np.maximum(u, v)
    key = lo * len(P) + hi
    order = np.lexsort((w, key))
    k = order[np.r_[True, np.diff(key[order]) != 0]]  # an edge given twice keeps its cheaper cost
    M = csr_matrix((np.r_[w[k], w[k]], (np.r_[lo[k], hi[k]], np.r_[hi[k], lo[k]])), shape=(len(P), len(P)))
    return dict(M=M, seam=seam)


CROWD = 0.5  # cm: the model's points this much nearer a click than one another are all the hand could have meant


def snap(at, tset="Skin", after=None):
    """A click on the car, on the model: the nearest of the model's points round it, where its lines cross (the user,
    2026-10-06: "I thought we were going to just have the points when two or more lines cross"); where its points
    crowd (a groove's walls, strips coming together) the nearest of those within CROWD on a line with the point
    `after` (the click before), if one is. (the point, its number, the same, 0.0), as a place on an edge from a point
    to itself."""
    e = _edges(tset)
    P, T = e["P"], e["T"]
    at = np.asarray(at, np.float64)
    near = np.unique(T[np.atleast_1d(_centres(tset).query(at, k=min(24, len(T)))[1])])
    d = np.linalg.norm(P[near] - at, axis=1)
    order = np.argsort(d)
    v = int(near[order[0]])
    if after is not None:
        mine = _lines_at(P[after], tset)
        for k in order[1:]:
            if d[k] > d[order[0]] + CROWD:
                break
            if not _lines_at(P[v], tset) & mine and _lines_at(P[near[k]], tset) & mine:
                v = int(near[k])
                break
    return P[v], v, v, 0.0


def _lines_at(p, tset):
    """The lines a stretch may run along (_clickable) that a point is on."""
    every, tree, line, _ = _clickable(tset)
    return {int(line[i]) for i in tree.query_ball_point(p, WALLS + DENSE)
            if np.linalg.norm(tree.data[i] - p) <= every[int(line[i])][1] + DENSE}


@functools.lru_cache(maxsize=4)
def strips(tset="Skin"):
    """The model's lines along its rounded edges: its edges the body bends across FLAT to SHARP degrees, joined end to
    end where one goes on from another turning least (under TURN), on across the seams between its pieces: a list of
    dicts like lines' (pts, closed, length), the longest first."""
    e, g = _edges(tset), _graph(tset)
    P, seam = e["P"], g["seam"]
    k = (np.abs(e["bend"]) >= FLAT) & ~e["crease"]
    ends = np.c_[e["a"][e["h1"]][k], e["b"][e["h1"]][k]]
    root = np.arange(len(P))  # a point and its partner across a seam are one place
    for i in np.flatnonzero(seam >= 0):
        r1, r2 = root[i], root[seam[i]]
        while root[r1] != r1:
            r1 = root[r1]
        while root[r2] != r2:
            r2 = root[r2]
        root[max(r1, r2)] = min(r1, r2)
    for i in range(len(P)):
        r = i
        while root[r] != r:
            r = root[r]
        root[i] = r
    at = {}
    for j, (u, v) in enumerate(ends):
        at.setdefault(root[u], []).append((j, 0))
        at.setdefault(root[v], []).append((j, 1))
    link = {}  # (edge, its end) -> (the edge it goes on into, that one's end there)
    for here in at.values():
        pairs = []
        for x in range(len(here)):
            for y in range(x + 1, len(here)):
                (j1, s1), (j2, s2) = here[x], here[y]
                d1 = P[ends[j1, 1 - s1]] - P[ends[j1, s1]]
                d2 = P[ends[j2, 1 - s2]] - P[ends[j2, s2]]
                turn = np.degrees(np.arccos(np.clip(-d1 @ d2 / max(np.linalg.norm(d1) * np.linalg.norm(d2), 1e-12), -1, 1)))
                if turn < TURN:
                    pairs.append((turn, here[x], here[y]))
        for _, p1, p2 in sorted(pairs):
            if p1 not in link and p2 not in link:
                link[p1], link[p2] = p2, p1
    out, done = [], np.zeros(len(ends), bool)

    def walk(j, s):  # from edge j's end s across it and on: its points
        pts = [P[ends[j, s]]]
        while True:
            done[j] = True
            far = P[ends[j, 1 - s]]
            if np.linalg.norm(far - pts[-1]) > 1e-9:
                pts.append(far)
            nxt = link.get((j, 1 - s))
            if nxt is None or done[nxt[0]]:
                return pts, nxt is not None
            j, s = nxt
            if np.linalg.norm(P[ends[j, s]] - pts[-1]) > 1e-9:
                pts.append(P[ends[j, s]])

    for j in range(len(ends)):  # from each loose end, then the loops left
        for s0 in (0, 1):
            if not done[j] and (j, s0) not in link:
                pts, _ = walk(j, s0)
                out.append((pts, False))
    for j in range(len(ends)):
        if not done[j]:
            pts, _ = walk(j, 0)
            out.append((pts, True))
    lines = [dict(pts=np.array(q), closed=c, length=float(np.linalg.norm(np.diff(np.array(q), axis=0), axis=1).sum()))
             for q, c in out if len(q) > 1]
    return sorted(lines, key=lambda L: -L["length"])


DENSE = 0.1  # cm between the points a click is matched to a line by


@functools.lru_cache(maxsize=4)
def _clickable(tset):
    """Every line a stretch between two clicks may run along, and how far from it a point may be to be on it: the
    template's (lines: creases and openings, each wall of a groove its own; and each groove whole, a point on any of
    its walls WALLS away) and the rounded edges' own (strips); each line's points every DENSE cm, its own and how far
    along, in a tree."""
    every = ([(L, 0.02) for L in lines(tset, fold=False)] + [(L, WALLS) for L in lines(tset) if L["walls"] > 1]
             + [(L, 0.02) for L in strips(tset)])
    pts, line, along = [], [], []
    for k, (L, _) in enumerate(every):
        q = L["pts"]
        cum = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(q, axis=0), axis=1))]
        t = np.linspace(0.0, cum[-1], max(2, int(np.ceil(cum[-1] / DENSE)) + 1))
        pts.append(np.c_[[np.interp(t, cum, q[:, i]) for i in range(3)]].T)
        line.append(np.full(len(t), k))
        along.append(t)
    return every, cKDTree(np.concatenate(pts)), np.concatenate(line), np.concatenate(along)


def _along(pa, pb, tset):
    """The stretch between two of the model's points along one of its lines (_clickable) if both are on it, the shorter
    way round a loop, a line they're both exactly on first (a groove's wall, before the groove): its points; else
    None."""
    every, tree, line, along = _clickable(tset)
    if np.linalg.norm(pa - pb) < 1e-9:
        return [pa]
    near = {}
    for end, p in enumerate((pa, pb)):
        for i in tree.query_ball_point(p, WALLS + DENSE):
            k = int(line[i])
            d = float(np.linalg.norm(tree.data[i] - p))
            if d <= every[k][1] + DENSE and d < near.get((end, k), (np.inf,))[0]:
                near[(end, k)] = (d, float(along[i]))
    best = None
    for k in {k for end, k in near if end == 0} & {k for end, k in near if end == 1}:
        L = every[k][0]
        s0, s1 = near[(0, k)][1], near[(1, k)][1]
        q = L["pts"]
        cum = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(q, axis=0), axis=1))]
        ways = [(s0, s1)]
        if L["closed"]:
            ways.append((s0, s1 - cum[-1]) if s1 > s0 else (s0, s1 + cum[-1]))
        for lo, hi in ways:
            rank = (every[k][1], abs(hi - lo))
            if best is None or rank < best[0]:
                best = (rank, q, cum, lo, hi, L["closed"])
    if best is None:
        return None
    _, q, cum, lo, hi, closed = best
    total = cum[-1]
    laps = (-1, 0, 1) if closed else (0,)  # only a loop goes on past its end, round to its start
    marks = [lo, hi] + [x + w * total for w in laps for x in cum if min(lo, hi) < x + w * total < max(lo, hi)]
    marks = sorted(set(marks), key=lambda x: x if hi >= lo else -x)
    return [np.array([np.interp(x % total if closed else x, cum, q[:, i]) for i in range(3)]) for x in marks]


def _straight(A, B, tset):
    """The way from one click (snap) to another straight across the surface: the straight line between them brought
    onto the model every STRAIGHT cm; None where it would leave the surface (across an opening, round a corner)."""
    pa, pb = A[0], B[0]
    n = max(2, int(np.ceil(np.linalg.norm(pb - pa) / STRAIGHT)) + 1)
    out = [pa]
    for t in np.linspace(0, 1, n)[1:-1]:
        q = pa + t * (pb - pa)
        on = _closest(q, tset)[1]
        if np.linalg.norm(on - q) > max(1.0, 0.1 * np.linalg.norm(pb - pa)):
            return None
        out.append(on)
    out.append(pb)
    if max(np.linalg.norm(np.diff(np.array(out), axis=0), axis=1)) > 4 * STRAIGHT:  # it jumped: an opening in between
        return None
    return out


def _between(A, B, tset):
    """The cheapest way along the model's edges from one click (snap) to another: its points."""
    from scipy.sparse.csgraph import dijkstra
    P, M = _edges(tset)["P"], _graph(tset)["M"]
    (pa, a0, a1, f), (pb, b0, b1, g) = A, B
    if {a0, a1} == {b0, b1}:
        return [pa, pb]

    def ends(u, v, t):  # the click's way to each end of its edge
        n = float(np.linalg.norm(P[v] - P[u]))
        per = M[u, v] / n if n > 1e-9 and M[u, v] else 1.0
        return [(u, t * n * per), (v, (1 - t) * n * per)]

    starts, stops = ends(a0, a1, f), ends(b0, b1, g)
    D, pred = dijkstra(M, directed=False, indices=[s for s, _ in starts], return_predecessors=True)
    cost, i, q = min((c0 + D[i, q] + c1, i, q) for i, (_, c0) in enumerate(starts) for q, c1 in stops)
    if not np.isfinite(cost):
        raise ValueError("no way along the model between two of the clicks: they're on pieces that don't meet")
    chain = [q]
    while chain[-1] != starts[i][0]:
        chain.append(int(pred[i, chain[-1]]))
    pts = [pa] + [P[k] for k in chain[::-1]] + [pb]
    return [p for k, p in enumerate(pts) if k == 0 or np.linalg.norm(p - pts[k - 1]) > 1e-6]


def path(clicks, tset="Skin", closed=False):
    """The line through points clicked on the car, each landed on the nearest of the model's points (snap): between two
    joined by an edge, that edge; on one of the model's lines, along it (_along); else straight across the surface
    (_straight); where that leaves the surface, the cheapest way along the model's edges (_between). Its points (n, 3)
    cm, the model's facing at each (n, 3), where each click landed and how each stretch went ("edge", "line",
    "straight", "edges", "across" a gap between pieces)."""
    spots = []
    for c in clicks:
        spots.append(snap(c, tset, after=spots[-1][1] if spots else None))
    if len(spots) > 1:  # the first by the second, as each other by the one before
        spots[0] = snap(clicks[0], tset, after=spots[1][1])
    if closed and len(spots) > 2:
        spots.append(spots[0])
    M = _graph(tset)["M"]
    pts, how = [], []
    for A, B in zip(spots, spots[1:]):
        if A[1] == B[1]:  # the same point twice
            continue
        if M[A[1], B[1]] and _graph(tset)["seam"][A[1]] != B[1]:  # joined by one of the model's edges
            got, kind = [A[0], B[0]], "edge"
        else:
            got, kind = _along(A[0], B[0], tset), "line"
        if got is None:
            got, kind = _straight(A, B, tset), "straight"
        if got is None:
            try:
                got, kind = _between(A, B, tset), "edges"
            except ValueError:  # on pieces of the model that don't meet: straight across the gap
                got, kind = [A[0], B[0]], "across"
        pts += got[1:] if pts and np.linalg.norm(got[0] - pts[-1]) < 1e-6 else got
        how.append(kind)
    if not pts:
        pts = [spots[0][0]]
    pts = np.array(pts)
    e = _edges(tset)
    nrm = e["N"][cKDTree(e["P"]).query(pts)[1]]
    return pts, nrm, spots, how


CORNER = 35.0  # degrees: where a line turns this much at one point it keeps the corner; a smooth one rounds the rest
SMOOTH_STEP = 0.25  # cm between the points of a smooth line


def smooth(pts, tset="Skin", closed=False):
    """A line through the model's points made one smooth curve through the same points (between them a centripetal
    Catmull-Rom curve, which never loops or overshoots), its corners of CORNER degrees or more kept, laid back on the
    surface: (n, 3) cm."""
    q = [np.asarray(pts[0], np.float64)]
    for p in pts[1:]:
        if np.linalg.norm(p - q[-1]) > 0.3 or p is pts[-1]:
            q.append(np.asarray(p, np.float64))
    q = np.array(q)
    if len(q) < 3:
        return q
    d = np.diff(q, axis=0)
    d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-12)
    turn = np.degrees(np.arccos(np.clip((d[1:] * d[:-1]).sum(1), -1, 1)))
    cuts = [0] + [i + 1 for i in np.flatnonzero(turn >= CORNER)] + [len(q) - 1]
    out = [q[0]]
    for a, b in zip(cuts, cuts[1:]):
        Q = q[a:b + 1]
        if len(Q) < 3:
            out.append(Q[-1])
            continue
        Q = np.r_[[2 * Q[0] - Q[1]], Q, [2 * Q[-1] - Q[-2]]]
        for i in range(1, len(Q) - 2):
            P0, P1, P2, P3 = Q[i - 1], Q[i], Q[i + 1], Q[i + 2]
            t1 = np.linalg.norm(P1 - P0) ** 0.5 + 1e-9
            t2 = t1 + np.linalg.norm(P2 - P1) ** 0.5 + 1e-9
            t3 = t2 + np.linalg.norm(P3 - P2) ** 0.5 + 1e-9
            n = max(1, int(np.ceil(np.linalg.norm(P2 - P1) / SMOOTH_STEP)))
            for t in np.linspace(t1, t2, n + 1)[1:]:
                A1 = (t1 - t) / t1 * P0 + t / t1 * P1
                A2 = (t2 - t) / (t2 - t1) * P1 + (t - t1) / (t2 - t1) * P2
                A3 = (t3 - t) / (t3 - t2) * P2 + (t - t2) / (t3 - t2) * P3
                B1 = (t2 - t) / t2 * A1 + t / t2 * A2
                B2 = (t3 - t) / (t3 - t1) * A2 + (t - t1) / (t3 - t1) * A3
                out.append((t2 - t) / (t2 - t1) * B1 + (t - t1) / (t2 - t1) * B2)
    return np.array([_closest(p, tset)[1] for p in out])


def picked(clicks, tset="Skin", closed=False):
    """The line through points clicked on the car (the Lab, with Mesh and Draw on: `PY -m tool.notes drawn` prints the
    call), a Course on the model (path): closed, round back to the first."""
    from tool import course
    pts, nrm, _, _ = path(clicks, tset, closed)
    if closed:
        pts, nrm = pts[:-1], nrm[:-1]
    return course.Course(pts, f"the line picked on the model from {course._said(pts[0])}", nrm=nrm, closed=closed)


def main():
    """The body's panels, the biggest first, and its longest lines: a point on each to pick it by, and its parts."""
    e, lab, names = _edges("Skin"), _panels("Skin"), _parts_of("Skin")
    X = e["P"][e["T"]]
    area = 0.5 * np.linalg.norm(np.cross(X[:, 1] - X[:, 0], X[:, 2] - X[:, 0]), axis=1)
    A = np.bincount(lab, weights=area)
    C = X.mean(1)
    print("The body's panels (meshlines.panel(point)), 50 cm2 or more, the biggest first:")
    for p in np.argsort(-A):
        if A[p] < 50:
            break
        mine = np.flatnonzero(lab == p)
        mid = np.average(C[mine], axis=0, weights=area[mine])
        at = C[mine[np.argmin(np.linalg.norm(C[mine] - mid, axis=1))]]  # a triangle of its own near its middle
        print(f"  {A[p]:7.0f} cm2  at ({at[0]:.0f}, {at[1]:.0f}, {at[2]:.0f})  {', '.join(_most(names[mine])[:3])}")
    print("Its lines (meshlines.line(point)), 40 cm or more, the longest first:")
    for L in lines("Skin"):
        if L["length"] < 40:
            break
        at = L["pts"][len(L["pts"]) // 2]
        groove = f", a groove of {L['walls']}" if L["walls"] > 1 else ""
        print(f"  {L['kind']:7s} {L['length']:6.0f} cm{' loop' if L['closed'] else ''}  at ({at[0]:.0f}, {at[1]:.0f}, {at[2]:.0f})"
              f"  {', '.join(L['parts'][:3])}{groove}")


if __name__ == "__main__":
    main()
