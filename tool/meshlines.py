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
    meshlines.line("side skirt crease 2")   one of the model's lines by its name (named: the part it mostly runs along,
                                    its kind and its number among that part's lines of the kind, the longest first;
                                    "crease", "edge" where the body ends, "seam"), a Course exactly through the model's
                                    points: .strip(0.6) a line on it (a panel line's groove is 0.3 to 0.4 cm wide, and
                                    the line is on one of its walls); along where the body ends a strip is half on it
    meshlines.line("rear flank roll 2", tilt=47)   a rounded edge's line: a "roll" is the model's lines side by side
                                    across a rounded edge (one every 1 to 2 cm, each facing its own way); tilt, degrees
                                    from facing up, says which (the listing gives each roll's)
    meshlines.line(name, side="right")   its mirror image on the other side (the names are the left side's and the
                                    middle's; .mirrored() marks both)
    meshlines.rolls()               the body's rounded edges, each its lines side by side across it, facing up first
    meshlines.panel("tail corner panel 1")   the model's own panel by its name (bounded by its creases and the body's
                                    edges), a zone filled right up to its lines; both=True the mirror image's too;
                                    border=1.5 only a trim that far inside its edge
    meshlines.picked([(70, 60, -70), (55, 63, -100)])   the line through points clicked on the car (the Lab: Mesh
                                    and Draw on), a Course on the model, as it is: each click lands on the nearest of
                                    the model's points, where its lines cross; between two joined by an edge, that
                                    edge; on one of its lines, along it, the line's own points; else the straightest
                                    way along the surface (tool/surface.py, path)
    PY -m tool.meshlines            the body's panels, its longest lines and its rounded edges by name, each with a point
                                    on it and its parts; `at x y z` what lies within 5 cm of a point, by name
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
    """The model's lines (template's creases and openings, and its seams: where two parts meet, as the side skirt's
    top edge meets the body shell, creased there or not, and a piece's edge sewn to another piece's) joined end to
    end into lines: a list of dicts, the longest first: kind ("crease", "opening", "seam"), pts (on the car, cm, in
    order), closed (a loop), length (cm), parts (those it runs along, most first), walls (a panel line drawn as a
    groove is two or three creases WALLS apart: the shorter ones are folded into the longest, counted here;
    fold=False keeps each). A seam along a crease is in both kinds."""
    e = _edges(tset)
    names = _parts_of(tset)
    t1, t2, tb = e["tri"][e["h1"]], e["tri"][e["h2"]], e["tri"][e["hb"]]
    parting, sewn = names[t1] != names[t2], e["sewn"]
    out = []
    for kind, (a, b, tris) in (("crease", (e["a"][e["h1"]][e["crease"]], e["b"][e["h1"]][e["crease"]],
                                           np.c_[t1, t2][e["crease"]])),
                               ("opening", (e["a"][e["hb"]][~sewn], e["b"][e["hb"]][~sewn], tb[~sewn][:, None])),
                               ("seam", (np.r_[e["a"][e["h1"]][parting], e["a"][e["hb"]][sewn]],
                                         np.r_[e["b"][e["h1"]][parting], e["b"][e["hb"]][sewn]],
                                         np.vstack([np.c_[t1, t2][parting], np.c_[tb, tb][sewn]])))):
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


MIDDLE = 1.0  # cm: a line or panel whose middle lies further right than this is the right side's, named by its left twin
WORDS = {"crease": "crisp line", "opening": "edge where the body ends", "seam": "seam", "rounded": "line along a rounded edge"}
KIND_WORD = {"crease": "crease", "opening": "edge", "seam": "seam"}


def _middle(pts):
    return pts[len(pts) // 2]


@functools.lru_cache(maxsize=4)
def named(tset="Skin"):
    """Every line, rounded edge and panel of the model by its name, {name: record}: the lines of the left side and
    the middle (the right side's are their mirror images: line(..., side="right")). A line's name is the part it
    mostly runs along, its kind ("crease", "edge" where the body ends, "seam") and its number among that part's lines
    of the kind, the longest first: "side skirt crease 2". A rounded edge's is "roll": its lines side by side across
    it (rolls; one of them by its tilt, degrees from facing up): "rear flank roll 2". A panel's is "panel", by area:
    "tail corner panel 1". The record: a line's dict (lines), a roll's list of them, a panel's dict (label: its
    triangles' panel, area, at: a point on it, parts). PY -m tool.meshlines lists them."""
    out = {}
    groups = {}
    for L in lines(tset):
        m = _middle(L["pts"])
        if m[0] >= -MIDDLE:
            groups.setdefault((L["parts"][0], KIND_WORD[L["kind"]]), []).append(L)
    for g in rolls(tset):
        longest = max(g, key=lambda L: L["length"])
        if _middle(longest["pts"])[0] >= -MIDDLE:
            groups.setdefault((longest["parts"][0], "roll"), []).append(g)
    for (part, word), items in groups.items():
        if word == "roll":
            items.sort(key=lambda g: (-round(max(L["length"] for L in g), 2), -round(_middle(g[0]["pts"])[2], 1)))
        else:
            items.sort(key=lambda L: (-round(L["length"], 2), -round(_middle(L["pts"])[2], 1), round(_middle(L["pts"])[1], 1)))
        for k, item in enumerate(items, 1):
            out[f"{part} {word} {k}"] = item
    e, lab, names = _edges(tset), _panels(tset), _parts_of(tset)
    X = e["P"][e["T"]]
    area = 0.5 * np.linalg.norm(np.cross(X[:, 1] - X[:, 0], X[:, 2] - X[:, 0]), axis=1)
    A, C = np.bincount(lab, weights=area), X.mean(1)
    panels_by = {}
    for p in range(lab.max() + 1):
        mine = np.flatnonzero(lab == p)
        if not len(mine):
            continue
        mid = np.average(C[mine], axis=0, weights=area[mine])
        at = C[mine[np.argmin(np.linalg.norm(C[mine] - mid, axis=1))]]
        if mid[0] >= -MIDDLE:
            parts = _most(names[mine])
            panels_by.setdefault(parts[0], []).append(dict(label=int(p), area=float(A[p]), at=at, parts=parts))
    for part, items in panels_by.items():
        items.sort(key=lambda d: (-round(d["area"], 1), -round(d["at"][2], 1), round(d["at"][1], 1)))
        for k, d in enumerate(items, 1):
            out[f"{part} panel {k}"] = d
    return out


def _named(name, word, tset):
    """The record called `name` of the kind `word` ("line", "roll" or "panel"), or a ValueError saying what's near it."""
    import difflib
    every = named(tset)
    key = " ".join(name.strip().lower().split())
    kinds = {"line": ("crease", "edge", "seam", "roll"), "roll": ("roll",), "panel": ("panel",)}[word]
    mine = [n for n in every if n.rsplit(" ", 2)[-2] in kinds]
    if key in mine:
        return every[key]
    close = difflib.get_close_matches(key, mine, n=5, cutoff=0.5)
    part = " ".join(key.split()[:-2])
    same = [n for n in mine if n.startswith(part + " ")][:8] if part else []
    hint = f"; did you mean {', '.join(map(repr, dict.fromkeys(close + same)))}?" if close or same else ""
    raise ValueError(f"no {word} of the model called {name!r}{hint}; PY -m tool.meshlines lists them")


def _twin(L, pool):
    """A line's mirror image on the car's other side: the line of the pool whose points mirror its, or None."""
    M = L["pts"] * np.array([-1.0, 1.0, 1.0])
    mid = _middle(M)
    for K in pool:
        if abs(K["length"] - L["length"]) > 0.01 * L["length"] + 0.5 or np.linalg.norm(_middle(K["pts"]) - mid) > 2.0:
            continue
        if cKDTree(K["pts"]).query(M)[0].max() <= 1.0:
            return K
    return None


def line(name, tilt=None, side=None, tset="Skin"):
    """One of the model's lines by its name (named: "side skirt crease 2", "sidepod inlet edge 1", "body shell seam
    1"; a rounded edge's "rear flank roll 2" with `tilt`, degrees from facing up, picking the line of those side by
    side across it, when it has more than one): a Course along it, exactly through the model's points (closed round a
    loop). side="right": its mirror image on the car's other side. A name that isn't one fails, saying the near ones;
    PY -m tool.meshlines lists them all, and `at x y z` names what lies near a point."""
    from tool import course
    L = _named(name, "line", tset)
    if isinstance(L, list):  # a roll: its lines side by side across the edge
        tilts = [round(x["tilt"]) for x in L]
        if tilt is None and len(L) > 1:
            raise ValueError(f"{name!r} has {len(L)} lines side by side across it, tilted {', '.join(map(str, tilts))} degrees "
                             f"from facing up: say which, tilt=<degrees>")
        L = L[0] if tilt is None else min(L, key=lambda x: abs(x["tilt"] - tilt))
    if side == "right":
        twin = _twin(L, strips(tset) if L["kind"] == "rounded" else lines(tset))
        if twin is None:
            raise ValueError(f"{name!r} has no mirror image on the right")
        L = twin
    words = f"the model's {WORDS[L['kind']]} {name!r}" + (f" tilted {L['tilt']:.0f} degrees" if "tilt" in L else "") \
        + (" on the right" if side == "right" else "")
    k = slice(0, -1) if L["closed"] else slice(None)
    c = course.Course(L["pts"][k], words, nrm=L["nrm"][k], closed=L["closed"])
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


def panel(name, both=False, border=None, soft=None, size=4096, side=None):
    """The model's own panel by its name (named: "tail corner panel 1"; PY -m tool.meshlines lists them): every
    triangle reached from one of its own without crossing a crease, painted right up to its creases and the body's
    edges, as a zone for s.paint(..., zone=); `both`: and its mirror image's on the other side (side="right": the
    mirror image alone); `border`: only the band that many cm inside its edge (a trim round an opening, a panel's
    outline). Its edge is the model's line itself, feathered over `soft` cm (shapes.SOFT). The body (Skin)."""
    from tool import bake, course, shapes
    soft = shapes.SOFT if soft is None else soft
    e, lab = _edges("Skin"), _panels("Skin")
    d = _named(name, "panel", "Skin")
    at = np.asarray(d["at"], np.float64) * ([-1, 1, 1] if side == "right" else 1)
    label = f"the model's {{words}} {name!r}" + (" on the right" if side == "right" else "")
    pts = [at] + ([at * [-1, 1, 1]] if both else [])
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
    z = course.Course._matched(pos[idx[keep]].astype(np.float64), w[keep].astype(np.float32),
                               label=label.format(words=words) + (", both sides" if both else ""))
    z.lines, z.border = edge, border  # the judge measures the fill's edge against its lines
    return z


FLAT = 6.0        # degrees: an edge the body bends across less than this counts as more or less flat: on a panel the
# triangles' edges are only where the model was cut into triangles, and a rounded edge's own lines bend 5 to 20
FLAT_COST = 3.0   # how much further a flat edge counts for a click landing on it (less as it bends, to FLAT)
SEAM = 1.0        # cm: across a seam between the model's pieces, a point joins the nearest point of another piece
TURN = 40.0       # degrees: one of the model's lines goes on through a point along its edge turning least, if under this


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
    dicts like lines' (kind "rounded", pts, nrm, closed, length, parts), the longest first."""
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
    near, names = cKDTree(P), _parts_of(tset)
    lines = [dict(kind="rounded", pts=np.array(q), nrm=e["N"][near.query(np.array(q))[1]], closed=c,
                  length=float(np.linalg.norm(np.diff(np.array(q), axis=0), axis=1).sum()),
                  parts=_most(names[_centres(tset).query(np.array(q))[1]]))
             for q, c in out if len(q) > 1]
    return sorted(lines, key=lambda L: -L["length"])


ROLL_LENGTH = 0.15  # lines of a rounded edge are as long as one another within this share
ROLL_ENDS = 0.08    # their ends as near one another as this share of their length (3 cm at least)
ROLL_BESIDE = 6.0   # cm: every point of one within this of the other


@functools.lru_cache(maxsize=4)
def rolls(tset="Skin", least=40.0):
    """The body's rounded edges: the model's lines along them (strips) `least` cm or longer, those that run side by side
    from end to end together (a band of the model's faces rolling from one way to another, as along the rear flank's
    shoulder): a list of lists of strips' dicts, each with tilt (degrees its surface faces from up, the median along
    it), from the line facing most up; the edge with the longest line first."""
    ok = [dict(L, tilt=float(np.median(np.degrees(np.arccos(np.clip(L["nrm"][:, 1], -1, 1))))))
          for L in strips(tset) if L["length"] >= least and not L["closed"]]
    root = list(range(len(ok)))

    def find(i):
        while root[i] != i:
            root[i] = root[root[i]]
            i = root[i]
        return i
    for i, a in enumerate(ok):
        for j in range(i + 1, len(ok)):
            b = ok[j]
            if abs(a["length"] - b["length"]) > ROLL_LENGTH * max(a["length"], b["length"]):
                continue
            ea, eb, reach = a["pts"][[0, -1]], b["pts"][[0, -1]], max(3.0, ROLL_ENDS * a["length"])
            if min(np.linalg.norm(ea - eb, axis=1).max(), np.linalg.norm(ea - eb[::-1], axis=1).max()) > reach:
                continue
            if min(cKDTree(b["pts"]).query(a["pts"])[0].max(), cKDTree(a["pts"]).query(b["pts"])[0].max()) <= ROLL_BESIDE:
                root[find(i)] = find(j)
    groups = {}
    for i in range(len(ok)):
        groups.setdefault(find(i), []).append(ok[i])
    return sorted((sorted(g, key=lambda L: L["tilt"]) for g in groups.values()), key=lambda g: -max(L["length"] for L in g))


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


def _straightest(A, B, tset):
    """The straightest way along the surface from one click (snap) to another (tool/surface.py, path): on one piece of
    the surface, the shortest line near the straight one between them; across pieces that meet, the cheapest way along
    the model's edges (_between) straightened on each piece, straight across the hairline between; across pieces that
    don't meet, straight across the gap. (its points, how it went)."""
    from tool import surface
    S = surface.load(tset)
    ends = np.array([A[0], B[0]])
    piece = S.piece[S._locate(ends)[0] // 16]
    if piece[0] == piece[1]:
        return list(S.path(ends)), "straightest"
    try:
        chain = np.array(_between(A, B, tset))
    except ValueError:  # on pieces of the model that don't meet
        return [A[0], B[0]], "across"
    piece = S.piece[S._locate(chain)[0] // 16]
    ends = np.flatnonzero(np.r_[True, piece[1:] != piece[:-1], True])  # each run of one piece: its first and last point
    return list(S.path(chain[np.unique(np.r_[ends[:-1], ends[1:] - 1])])), "straightest"


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
    joined by an edge, that edge; on one of the model's lines, along it (_along); else the straightest way along the
    surface (_straightest). Its points (n, 3) cm, the model's facing at each (n, 3), where each click landed and how
    each stretch went ("edge", "line", "straightest", "across" a gap between pieces)."""
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
            got, kind = _straightest(A, B, tset)
        pts += got[1:] if pts and np.linalg.norm(got[0] - pts[-1]) < 1e-6 else got
        how.append(kind)
    if not pts:
        pts = [spots[0][0]]
    pts = np.array(pts)
    e = _edges(tset)
    nrm = e["N"][cKDTree(e["P"]).query(pts)[1]]
    return pts, nrm, spots, how


def picked(clicks, tset="Skin", closed=False):
    """The line through points clicked on the car (the Lab, with Mesh and Draw on: `PY -m tool.notes drawn` prints the
    call), a Course on the model: path's points as they are; closed, round back to the first."""
    from tool import course, surface
    pts = path(clicks, tset, closed)[0]
    if closed:
        pts = pts[:-1]
    return course.Course(pts, f"the line picked on the model from {course._said(pts[0])}", nrm=surface.load(tset).facing(pts),
                         closed=closed)


def _at(p):
    return f"({p[0]:.0f}, {p[1]:.0f}, {p[2]:.0f})"


def listing(least_line=40.0, least_area=50.0, tset="Skin"):
    """The model's named panels, lines and rounded edges (named), the left side and the middle, each with a point on it
    and its parts: {"panels": [...], "lines": [...], "rolls": [...]} of (name, size, at, parts, more)."""
    out = {"panels": [], "lines": [], "rolls": []}
    for name, rec in named(tset).items():
        word = name.rsplit(" ", 2)[-2]
        if word == "panel" and rec["area"] >= least_area:
            out["panels"].append((name, rec["area"], rec["at"], rec["parts"][:3], ""))
        elif word == "roll" and max(L["length"] for L in rec) >= least_line:
            more = ", ".join(f"{L['tilt']:.0f}" for L in rec)
            out["rolls"].append((name, max(L["length"] for L in rec), _middle(rec[0]["pts"]), rec[0]["parts"][:3], f"tilts {more}"))
        elif word in KIND_WORD.values() and rec["length"] >= least_line:
            more = (" loop" if rec["closed"] else "") + (f", a groove of {rec['walls']}" if rec["walls"] > 1 else "")
            out["lines"].append((name, rec["length"], _middle(rec["pts"]), rec["parts"][:3], more))
    for k in out:
        out[k].sort(key=lambda r: (-round(r[1]), r[0]))
    return out


def near(point, reach=5.0, tset="Skin"):
    """What of the model lies within `reach` cm of a point: [(how far, the name, a word)] for its lines and rounded
    edges, nearest first, and the name of the panel under it."""
    p = np.asarray(point, np.float64)
    found = []
    for name, rec in named(tset).items():
        word = name.rsplit(" ", 2)[-2]
        if word == "panel":
            continue
        for L in (rec if word == "roll" else [rec]):
            d = float(np.linalg.norm(L["pts"] - p, axis=1).min())
            if d <= reach:
                found.append((d, name, f"{WORDS[L['kind']]}, {L['length']:.0f} cm" + (f", tilt {L['tilt']:.0f}" if "tilt" in L else "")))
    found.sort()
    panels_named = {r["label"]: n for n, r in named(tset).items() if n.rsplit(" ", 2)[-2] == "panel"}
    under = panels_named.get(_panels(tset)[_triangle_at(p, tset)])
    if under is None:  # the right side: its twin's name
        twin = panels_named.get(_panels(tset)[_triangle_at(p * [-1, 1, 1], tset)])
        under = f"{twin} (its mirror image: side=\"right\")" if twin else None
    return found, under


def main(argv):
    """The body's named panels, lines and rounded edges, 50 cm2 or 40 cm and more, each with a point on it and its
    parts; `at x y z`: what lies within 5 cm of a point, by name."""
    if argv[:1] == ["at"]:
        p = [float(v) for v in argv[1:4]]
        found, under = near(p)
        print(f"Within 5 cm of {_at(p)}:" + ("" if found else " none of the model's lines"))
        for d, name, what in found:
            print(f"  {d:4.1f} cm  {name:<30} {what}")
        print(f"The panel under it: {under or 'none (the point is off the body)'}")
        return
    L = listing()
    print("The body's panels (meshlines.panel(name)), 50 cm2 or more, the biggest first; the right side is each one's "
          "mirror image (both=True, or side=\"right\"):")
    for name, area, at, parts, _ in L["panels"]:
        print(f"  {name:<30} {area:7.0f} cm2  at {_at(at)}  {', '.join(parts)}")
    print("Its lines (meshlines.line(name)), 40 cm or more, the longest first:")
    for name, length, at, parts, more in L["lines"]:
        print(f"  {name:<30} {length:6.0f} cm{more}  at {_at(at)}  {', '.join(parts)}")
    print("Its rounded edges (meshlines.line(name, tilt=<degrees from facing up>)), 40 cm or more: each one's lines side by "
          "side across it, by tilt:")
    for name, length, at, parts, more in L["rolls"]:
        print(f"  {name:<30} {length:6.0f} cm  {more}  at {_at(at)}  {', '.join(parts)}")


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
