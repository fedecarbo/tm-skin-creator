"""The model's own lines: the edges the car's body is built from (the lines of the UV map's wireframe). Along each of
the car's edges the modeller laid lines from end to end (on a rounded edge, a family of them across the curve, one
every few degrees of turn); a marking along an edge follows one of them exactly, from one of the model's points to
the next: straight on the UV map between the car's own points, unbroken across the texture's seams. (The user,
2026-10-06, of lines traced from the texture and smoothed: "you are basically scribbling blindly everywhere";
"There's got to be a precise solution to this".)

    meshlines.along(guide)          the model's line along a guide (course.shoulder(), course.flow(...)): of the lines
                                    within `reach` cm of it, the one where the body's shading is halfway between the two
                                    surfaces it divides (as course.shadow reads them), kept to one line and joined
                                    straight across the panels' seams; a Course through the model's points
    meshlines.along(guide).strip(0.6)    a strip along it, straight from point to point (on a body shaded smooth it shows
                                    a small corner at each point: 4 to 7 degrees on the shoulder)
    meshlines.along(guide).inked(0.6)    one smooth stroke on each piece of the UV map through where the line falls
"""

import functools

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree

WELD = 1e-3      # cm: the model's points this close are one point
SEAM = 2.0       # cm: across a seam between two of the model's pieces, a line joins the next piece's point this near
LEVEL = 0.06     # how far a point's shading may stray from the level before it costs as much again as its length
SIDEWAYS = 10.0  # cm: what stepping sideways onto the next line costs, so a line keeps to one of the model's lines
REACH = 4.0      # cm from the guide the model's lines are looked for
STRAIGHT = 0.95  # a line carries on to the guide's ends along its own edges while they turn less than this (cosine)


@functools.lru_cache(maxsize=1)
def _graph():
    """The body's (Skin) points welded, their shading normals (the corners' mean), its edges, their lengths and which
    of them join two pieces of the model across a seam."""
    from tool import fbx
    m = fbx.meshes()[fbx.MESH_OF["Skin"]]
    p0, tv, tn = m["positions"].astype(np.float64), m["tri_vertex"], m["tri_normal"].astype(np.float64)
    _, first, inv = np.unique(np.round(p0 / WELD).astype(np.int64), axis=0, return_index=True, return_inverse=True)
    P, T = p0[first], inv.ravel()[tv]
    N = np.zeros((len(P), 3))
    np.add.at(N, T.ravel(), tn.reshape(-1, 3))
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    E = np.unique(np.sort(np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), axis=1), axis=0)
    E = E[E[:, 0] != E[:, 1]]
    from scipy.sparse.csgraph import connected_components
    _, piece = connected_components(coo_matrix((np.ones(len(E)), (E[:, 0], E[:, 1])), shape=(len(P), len(P))), directed=False)
    pairs = np.array(sorted(cKDTree(P).query_pairs(SEAM)), dtype=np.int64).reshape(-1, 2)
    pairs = pairs[piece[pairs[:, 0]] != piece[pairs[:, 1]]]
    seam = np.r_[np.zeros(len(E), bool), np.ones(len(pairs), bool)]
    E = np.vstack([E, pairs])
    return P, N, E, np.linalg.norm(P[E[:, 1]] - P[E[:, 0]], axis=1), seam


def _level(c):
    """The shading halfway between the two surfaces a guide divides, each read a roll's radius off it (facing up)."""
    from tool import carmap
    m = carmap.load()
    radius = 1.0 / max(float(np.median(m.value("k1", c.pts))), 1e-3)
    side = np.cross(c.tan, c.nrm)
    faces = [float(np.median(m.value("facing_y", m.project(c.pts + sign * side * radius)[0]))) for sign in (1, -1)]
    return 0.5 * (faces[0] + faces[1])


def along(guide, level=None, reach=REACH):
    """The model's line along `guide` (a Course on either side): see the module's key. `level` (facing up, -1 to 1)
    gives the shading outright."""
    from tool import course
    right = float(np.mean(guide.pts[:, 0])) < 0
    g = course.Course(guide.pts * (course.MIRROR if right else 1), guide.name)
    level = _level(g) if level is None else float(level)
    P, N, E, L, seam = _graph()
    n = len(P)
    tree = cKDTree(g.pts)
    near = tree.query(P)[0] <= reach
    keep = near[E[:, 0]] & near[E[:, 1]]
    Ek, Lk, Sk = E[keep], L[keep], seam[keep]
    dy = (N[:, 1] - level) / LEVEL
    off = 1.0 + 0.5 * (dy[Ek[:, 0]] ** 2 + dy[Ek[:, 1]] ** 2)
    way = (P[Ek[:, 1]] - P[Ek[:, 0]]) / np.maximum(Lk[:, None], 1e-9)
    tan = g.tan[tree.query(0.5 * (P[Ek[:, 0]] + P[Ek[:, 1]]))[1]]
    sideways = np.abs((way * tan).sum(1)) < 0.5
    w = np.where(Sk, 1.5 * Lk * off, Lk * off + SIDEWAYS * sideways)
    # its ends: a start joined to the model's points near the guide's start, an end to those near its end, each at
    # the cost of how far it is from the guide's end and from the level there
    S, Z = n, n + 1

    def ends(p):
        d = np.linalg.norm(P - p, axis=1)
        idx = np.flatnonzero(near & (d < 8.0))
        return idx, d[idx] + 2.0 * np.abs(N[idx, 1] - level) / LEVEL + 1e-6

    si, sw = ends(g.pts[0])
    zi, zw = ends(g.pts[-1])
    G = coo_matrix((np.r_[w, w, sw, zw], (np.r_[Ek[:, 0], Ek[:, 1], np.full(len(si), S), zi],
                                          np.r_[Ek[:, 1], Ek[:, 0], si, np.full(len(zi), Z)])), shape=(n + 2, n + 2)).tocsr()
    dist, pred = dijkstra(G, directed=True, indices=S, return_predecessors=True)
    if not np.isfinite(dist[Z]):
        raise ValueError(f"none of the model's lines runs along {guide.name}")
    chain = [pred[Z]]
    while pred[chain[-1]] != S:
        chain.append(pred[chain[-1]])
    chain = _carried(chain[::-1], g, P, E, tree.query(P)[0] <= 2 * reach)
    out = course.points(P[chain], f"the model's line along {guide.name}")
    return course._flip(out) if right else out


def _carried(chain, g, P, E, near):
    """The chain carried on at each end along its own edges, while they run on straight (STRAIGHT) and the guide
    still lies ahead, to the guide's own ends (within twice the reach: a guide on a rounded edge's crest bends away
    from its shading line round a corner, as the shoulder does at the inlet)."""
    nbr = {}
    for a, b in E:
        nbr.setdefault(a, []).append(b)
        nbr.setdefault(b, []).append(a)
    s = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(g.pts, axis=0), axis=1))]
    tree = cKDTree(g.pts)
    for flip in (False, True):
        chain = chain[::-1] if flip else chain
        goal = s[-1] if not flip else 0.0
        while len(chain) > 1:
            a, b = chain[-2], chain[-1]
            d = (P[b] - P[a]) / max(np.linalg.norm(P[b] - P[a]), 1e-9)
            here = s[tree.query(P[b])[1]]
            if abs(goal - here) < 0.5:
                break
            best, cos = None, STRAIGHT
            for c in nbr.get(b, ()):
                if c in chain or not near[c]:
                    continue
                e = (P[c] - P[b]) / max(np.linalg.norm(P[c] - P[b]), 1e-9)
                ahead = s[tree.query(P[c])[1]]
                if e @ d > cos and abs(goal - ahead) < abs(goal - here):
                    best, cos = c, e @ d
            if best is None:
                break
            chain.append(best)
        chain = chain[::-1] if flip else chain
    return list(chain)
