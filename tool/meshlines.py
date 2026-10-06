"""The model's own lines: the edges the car's body is built from, the lines of the UV map's wireframe, each known on
the car and on the map at once: the template to design on. Read off the model's triangles alone: nothing traced from
the texture, nothing from the car map, no light or shading (the user, 2026-10-06: "doing it with the exact lines that
the model had all along"; "Your new method ... shouldnt be needing shadows anyways to design properly").

    meshlines.template("Skin")           the model's lines on one of the game's maps: its creases (crisp lines and panel
                                    lines), where the body ends, and where the map is cut while the car carries on;
                                    the Lab's UV map room draws them (view.export_template)
    meshlines.curvature("Skin")          how much the body curves at each of the model's points, degrees a cm, + outward (a
                                    rounded edge) and - inward (an indentation), off its creases; the template tints by it
    meshlines.line((35, 71, 9), least=100)   the template's line nearest a point, a Course exactly through the model's
                                    points: .strip(0.6) a line on it (a panel line's groove is 0.3 to 0.4 cm wide, and
                                    the line is on one of its walls); along where the body ends a strip is half on it
    meshlines.panel((25, 80, 11))        the model's own panel under a point (bounded by its creases and the body's
                                    edges), a zone filled right up to its lines; both=True the mirror image's too;
                                    border=1.5 only a trim that far inside its edge
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
    which are creases, cuts and sewn; each triangle's piece."""
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
    crease = np.degrees(np.arccos(np.clip((fn[tri[h1]] * fn[tri[h2]]).sum(1), -1, 1))) >= SHARP
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
                cut=cut, crease=crease, sewn=sewn, piece=piece)


CURVE_SMOOTH = 4  # times each point's curvature is blended with its neighbours': the model's triangles are big on the
# flat panels and small on the edges, and one point's own reading is patchy


@functools.lru_cache(maxsize=4)
def curvature(tset="Skin"):
    """How much the body curves at each of the model's points (_edges' P): degrees a cm across the way it curves most,
    + outward (a rounded edge) and - inward (an indentation), from the change of the model's normals to its neighbours
    over the edges that aren't creases (a crease is a line of its own), blended CURVE_SMOOTH times with theirs."""
    e = _edges(tset)
    P, N = e["P"], e["N"]
    smooth = ~e["crease"]
    a, b = e["a"][e["h1"]][smooth], e["b"][e["h1"]][smooth]
    nbr = [[] for _ in range(len(P))]
    for u, v in zip(a, b):
        nbr[u].append(v)
        nbr[v].append(u)
    k = np.zeros(len(P))
    for v, near in enumerate(nbr):
        n = N[v]
        if len(near) < 2 or not np.linalg.norm(n) > 0.5:  # a point of degenerate triangles has no facing
            continue
        d = P[near] - P[v]
        d -= np.outer(d @ n, n)
        dn = N[near] - n
        dn -= np.outer(dn @ n, n)
        e1 = np.cross(n, [1.0, 0.0, 0.0]) if abs(n[0]) < 0.9 else np.cross(n, [0.0, 1.0, 0.0])
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(n, e1)
        S = np.linalg.lstsq(np.c_[d @ e1, d @ e2], np.c_[dn @ e1, dn @ e2], rcond=None)[0]
        w = np.linalg.eigvalsh(0.5 * (S + S.T))
        k[v] = np.degrees(w[np.argmax(np.abs(w))])
    for _ in range(CURVE_SMOOTH):
        k = np.array([0.5 * k[v] + 0.5 * k[near].mean() if near else k[v] for v, near in enumerate(nbr)])
    return k


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


@functools.lru_cache(maxsize=4)
def lines(tset="Skin"):
    """The model's lines (template's creases and openings) joined end to end into lines: a list of dicts, the longest
    first: kind ("crease", "opening"), pts (on the car, cm, in order), closed (a loop), length (cm), parts (those it runs
    along, most first), walls (a panel line drawn as a groove is two or three creases WALLS apart: the shorter ones are
    folded into the longest, counted here)."""
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
    e = _edges(tset)
    X = e["P"][e["T"]]
    tree = _centres(tset)
    _, cand = tree.query(point, k=min(24, len(X)))
    best, bd = None, np.inf
    for t in np.atleast_1d(cand):
        a, b, c = X[t]
        n = np.cross(b - a, c - a)
        n /= max(np.linalg.norm(n), 1e-12)
        q = point - ((point - a) @ n) * n
        bary = np.linalg.lstsq(np.c_[b - a, c - a], q - a, rcond=None)[0]
        u, v = np.clip(bary, 0, 1)
        if u + v > 1:
            u, v = u / (u + v), v / (u + v)
        d = np.linalg.norm(point - (a + u * (b - a) + v * (c - a)))
        if d < bd:
            best, bd = t, d
    return best


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
