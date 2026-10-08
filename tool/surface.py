"""The car's surface, repaired once from its mesh: the one foundation every graphic on the car stands on, and is
measured by. Distances and lines are worked out along the surface itself, never through the air.

The model (tool/fbx.py) is a soup of triangles: its points repeated per triangle, some triangles drawn twice, so
edges with three or four faces, which no surface solver accepts. Repaired once per mesh and cached in the work
folder (`python -m tool.surface` rebuilds it and says what it did, in numbers):

    S = surface.load()                 the body (Skin); surface.load("Details") the inner car's
    S.V, S.F                           the model welded: its points that agree to WELD cm made one, and every
                                       triangle of the model over them, in the model's order (the bake's tri, the
                                       parts' tri_part)
    S.fn, S.part                       each model triangle's facing (out, as it shades) and its part
    S.RV, S.RF                         the repaired surface: one of each triangle drawn twice, and a point where
                                       more than two faces met copied per fan, so every edge has one or two faces;
                                       S.welded: each repaired vertex's welded point (copies share one)
    S.face[t], S.model[f]              a model triangle's face of the surface (a twin's: the first drawn) and back
    S.piece[f], S.pieces               the piece (faces joined edge to edge) each face is in, and how many
    S.FV, S.FF                         the fine surface: the same, every face cut into 16 (its edges halved twice),
                                       for values between the model's own points: its face j lies in face j // 16,
                                       its first vertices are RV's, the rest the midpoints
    S.distance(points, reach)          cm along the surface from a line (its points in order on the surface, every
                                       quarter centimetre or so) or from any points, per fine vertex within `reach`
                                       cm of them: exact (the points put into the fine surface as vertices of its
                                       own, then libigl's exact geodesics); inf beyond the reach and on other pieces
    S.vertex((x, y, z))                the repaired vertex nearest a point
    S.line(a, b)                       the straightest line on the surface between two vertices: (n, 3) cm (edge
                                       flips)
    S.carry(t, bary, direction, cm)    the straightest way on along the surface from a point (a model triangle and
                                       weights at its corners) in a direction, `cm` far: (n, 3) cm (the tracer)
    S.texels(size, lin)                where texels of the set's map (flat indices row * size + column; all by
                                       default) sit on the fine surface, from the bake's triangle (tool/bake.py):
                                       each one's fine face (-1 off the car) and its weights at the face's corners
    S.sample(values, size, lin)        a value per fine vertex read at those texels through their faces

The distances are exact on the surface, and within 0.05 cm between the fine surface's vertices (measured against
the line's own points); a line of the body within 8 cm costs a tenth of a second. (The heat methods and fast
marching, measured on this mesh, were off by 0.2 to 2 cm: the model's triangles are up to 24 cm long.) Nothing
crosses a gap between pieces.
"""

import functools
import time

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

from tool import bake, fbx, parts, paths

VERSION = 1
WELD = 0.01      # cm: the model's points this close are one point (a texel is 0.05 to 0.09 cm)
SNAP = 0.02      # cm: a line's point this near one of the fine surface's vertices is it; this near an edge, on it
CHUNK = 1 << 21  # texels worked on at once


def cache_file(tset):
    return paths.CACHE / f"surface_{tset}_v{VERSION}.npz"


def _halved(V, F):
    """Every face cut into four by its edges' midpoints (new vertices after V's): face i's are 4i to 4i + 3, at its
    first, second and third corner and in the middle, their corners in the face's own order."""
    e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    key = np.minimum(e[:, 0], e[:, 1]).astype(np.int64) * len(V) + np.maximum(e[:, 0], e[:, 1])
    u, inv = np.unique(key, return_inverse=True)
    mid = len(V) + inv.reshape(3, -1).T
    a, b, c = F[:, 0], F[:, 1], F[:, 2]
    mab, mbc, mca = mid[:, 0], mid[:, 1], mid[:, 2]
    NF = np.stack([np.c_[a, mab, mca], np.c_[mab, b, mbc], np.c_[mca, mbc, c], np.c_[mab, mbc, mca]], 1).reshape(-1, 3)
    return np.vstack([V, 0.5 * (V[u // len(V)] + V[u % len(V)])]), NF


def _down(f, W):
    """One cut down: the face among a face's four holding each point, and its weights there."""
    k = W.argmax(1)
    corner = W[np.arange(len(W)), k] >= 0.5
    f2 = np.where(corner, 4 * f + k, 4 * f + 3)
    W2 = np.where(corner[:, None], 2 * W - np.eye(3)[k], 1 - 2 * W[:, [2, 0, 1]])
    return f2, W2


def build(tset="Skin"):
    import igl
    m = fbx.meshes()[fbx.MESH_OF[tset]]
    pos, tv = m["positions"].astype(np.float64), m["tri_vertex"].astype(np.int64)
    _, first, inv = np.unique(np.round(pos / WELD).astype(np.int64), axis=0, return_index=True, return_inverse=True)
    V, F = pos[first], inv.reshape(-1)[tv]
    fn = m["tri_normal"].astype(np.float64).mean(1)
    fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
    P = parts.load()
    off = P.mesh_offset[tset]
    part = P.tri_part[off:off + len(F)].astype(np.int32)
    # the repaired surface: the first of each triangle drawn twice, in the model's order; then the points where
    # more than two faces meet copied, one per fan
    _, kept, group = np.unique(np.sort(F, 1), axis=0, return_index=True, return_inverse=True)
    model = np.sort(kept)
    face = np.searchsorted(model, kept[group.reshape(-1)])
    RF, welded = igl.split_nonmanifold(F[model])
    piece = np.asarray(igl.facet_components(RF)[1])
    FV, FF = _halved(*_halved(V[welded], RF))
    data = dict(version=VERSION, V=V, F=F.astype(np.int32), fn=fn, part=part, RF=RF.astype(np.int32),
                welded=welded.astype(np.int32), face=face.astype(np.int32), model=model.astype(np.int32),
                piece=piece.astype(np.int32), points=len(pos), FV=FV, FF=FF.astype(np.int32))
    f = cache_file(tset)
    f.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(f, **data)
    load.cache_clear()
    return Surface(tset, data)


@functools.lru_cache(maxsize=4)
def load(tset="Skin"):
    fbx.meshes()
    f = cache_file(tset)
    if not f.exists() or f.stat().st_mtime < fbx.CACHE.stat().st_mtime:
        return build(tset)
    return Surface(tset, dict(np.load(f)))


class Surface:
    def __init__(self, tset, d):
        self.tset = tset
        self.V, self.F, self.fn, self.part = d["V"], d["F"], d["fn"], d["part"]
        self.RF, self.welded, self.face, self.model, self.piece = d["RF"], d["welded"], d["face"], d["model"], d["piece"]
        self.FV, self.FF = d["FV"], d["FF"]
        self.RV = self.V[self.welded]
        self.points = int(d["points"])
        self.pieces = int(self.piece.max()) + 1
        self.vpiece = np.full(len(self.RV), -1, np.int64)
        self.vpiece[self.RF.reshape(-1)] = np.repeat(self.piece, 3)
        self._local, self._solvers, self._tree, self._centres = {}, {}, None, None

    # ---- the pieces and their solvers ----

    def _piece(self, p):
        """One piece as a mesh of its own: its points and faces, with their numbers on the whole surface and back."""
        if p not in self._local:
            faces = np.flatnonzero(self.piece == p)
            verts, local = np.unique(self.RF[faces], return_inverse=True)
            back = np.full(len(self.RV), -1, np.int64)
            back[verts] = np.arange(len(verts))
            fback = np.full(len(self.RF), -1, np.int64)
            fback[faces] = np.arange(len(faces))
            self._local[p] = dict(V=self.RV[verts], F=local.reshape(-1, 3), verts=verts, back=back, fback=fback)
        return self._local[p]

    def _solver(self, p, kind):
        import potpourri3d as pp3d
        if (p, kind) not in self._solvers:
            q = self._piece(p)
            make = {"flip": pp3d.EdgeFlipGeodesicSolver, "trace": pp3d.GeodesicTracer}[kind]
            self._solvers[(p, kind)] = make(q["V"], q["F"])
        return self._solvers[(p, kind)]

    def vertex(self, point):
        """The repaired vertex nearest a point in space."""
        if self._tree is None:
            self._tree = cKDTree(self.RV)
        return int(self._tree.query(np.asarray(point, np.float64))[1])

    def line(self, a, b):
        """The straightest line on the surface between two repaired vertices (edge flips): (n, 3) cm."""
        p = np.unique(self.vpiece[[a, b]])
        if len(p) != 1:
            raise ValueError("the two vertices are on different pieces of the surface")
        q = self._piece(int(p[0]))
        return np.asarray(self._solver(int(p[0]), "flip").find_geodesic_path(int(q["back"][a]), int(q["back"][b])))

    def carry(self, tri, bary, direction, cm):
        """The straightest way on along the surface from a point (a model triangle and weights at its corners) in a
        direction, `cm` far (the tracer): (n, 3) cm."""
        f = int(self.face[tri])
        p = int(self.piece[f])
        q = self._piece(p)
        d = np.asarray(direction, np.float64)
        d = d / max(np.linalg.norm(d), 1e-12) * cm
        return np.asarray(self._solver(p, "trace").trace_geodesic_from_face(int(q["fback"][f]), np.asarray(bary, np.float64), d))

    # ---- distances along the surface ----

    def _locate(self, pts):
        """Each point's fine face, its weights at the face's corners and the point on it: the nearest of the faces round it."""
        if self._centres is None:
            self._centres = cKDTree(self.FV[self.FF].mean(1))
        _, cand = self._centres.query(pts, k=24)
        A, B, C = (self.FV[self.FF[cand, k]] for k in range(3))
        e1, e2, d = B - A, C - A, pts[:, None, :] - A
        d11, d12, d22 = (e1 * e1).sum(2), (e1 * e2).sum(2), (e2 * e2).sum(2)
        r1, r2 = (e1 * d).sum(2), (e2 * d).sum(2)
        det = np.maximum(d11 * d22 - d12 * d12, 1e-18)
        u, v = np.clip((d22 * r1 - d12 * r2) / det, 0, 1), np.clip((d11 * r2 - d12 * r1) / det, 0, 1)
        s = np.maximum(u + v, 1)
        u, v = u / s, v / s
        on = A + u[..., None] * e1 + v[..., None] * e2
        best = np.linalg.norm(on - pts[:, None, :], axis=2).argmin(1)
        r = np.arange(len(pts))
        u, v = u[r, best], v[r, best]
        return cand[r, best], np.stack([1 - u - v, u, v], 1), on[r, best]

    def distance(self, points, reach=8.0):
        """cm along the surface from a line (its points in order on the surface, every quarter centimetre or so) or from
        any points, per fine vertex within `reach` cm of them: the points put into the fine surface as vertices of its
        own, the distances then exact (libigl's exact geodesics) on a patch of the surface within the reach; inf beyond
        it, and on pieces holding none of the points."""
        import igl
        pts = np.asarray(points, np.float64).reshape(-1, 3)
        f, w, on = self._locate(pts)
        longest = max(np.linalg.norm(self.FV[self.FF[:, k]] - self.FV[self.FF[:, k - 1]], axis=1).max() for k in range(3))
        near = cKDTree(on).query(self.FV, distance_upper_bound=reach + 2 * longest)[0]
        keep = np.flatnonzero(np.isfinite(near[self.FF]).any(1))
        verts, local = np.unique(self.FF[keep], return_inverse=True)
        V, F = self.FV[verts], local.reshape(-1, 3)
        V2, F2, src = _insert(V, F, np.searchsorted(keep, f), w, on)
        n = len(V2)
        g = coo_matrix((np.ones(3 * len(F2)), (F2.reshape(-1), np.roll(F2, 1, 1).reshape(-1))), shape=(n, n))
        comp = connected_components(g, directed=False)[1]
        d = np.asarray(igl.exact_geodesic(V2, F2.astype(np.int64), np.unique(src).astype(np.int64), np.zeros(0, np.int64),
                                          np.arange(n, dtype=np.int64), np.zeros(0, np.int64))).reshape(-1)[:len(V)]
        ok = np.isin(comp[:len(V)], comp[src]) & (d <= reach)
        out = np.full(len(self.FV), np.inf)
        out[verts[ok]] = d[ok]
        return out

    # ---- the texels ----

    def texels(self, size, lin=None):
        """Where texels of the set's map sit on the fine surface, from the bake's triangle (tool/bake.py): each one's
        fine face (-1 off the car) and its weights at the face's corners, (n,) and (n, 3). lin: flat texel indices,
        row * size + column; all the map's when None."""
        tri = bake.bake(self.tset, size, size)["tri"].reshape(-1)
        lin = np.arange(tri.size) if lin is None else np.asarray(lin, np.int64)
        uv = fbx.meshes()[fbx.MESH_OF[self.tset]]["tri_uv"]
        face = np.full(len(lin), -1, np.int32)
        bary = np.zeros((len(lin), 3), np.float32)
        for k in range(0, len(lin), CHUNK):
            i = lin[k:k + CHUNK]
            t = tri[i]
            on = t >= 0
            i, t = i[on], t[on]
            u = uv[t].astype(np.float64)
            x, y = u[..., 0] * size, (1 - u[..., 1]) * size  # the map's pixels, rows running down, as the bake rasterises
            px, py = (i % size) + 0.5, (i // size) + 0.5    # the texel's centre
            (ax, ay), (bx, by), (cx, cy) = (x[:, 0], y[:, 0]), (x[:, 1], y[:, 1]), (x[:, 2], y[:, 2])
            area = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
            w0 = ((bx - px) * (cy - py) - (by - py) * (cx - px)) / area
            w1 = ((cx - px) * (ay - py) - (cy - py) * (ax - px)) / area
            f, W = self.face[t].astype(np.int64), np.stack([w0, w1, 1 - w0 - w1], 1)
            f, W = _down(*_down(f, W))
            rows = np.flatnonzero(on) + k
            face[rows] = f
            bary[rows] = W
        return face, bary

    def sample(self, values, size, lin=None):
        """A value per fine vertex (n,) or (n, k), read at the texels through their faces: (m,) or (m, k), 0 off
        the car."""
        face, bary = self.texels(size, lin)
        values = np.asarray(values)
        out = np.zeros((len(face),) + values.shape[1:], values.dtype)
        on = face >= 0
        corners = values[self.FF[face[on]]]
        w = bary[on].astype(values.dtype).reshape(bary[on].shape + (1,) * (values.ndim - 1))
        out[on] = np.where(w > 0, corners * w, 0).sum(1)  # a corner out of reach (inf) weighs nothing at weight 0
        return out


def _bary(p, a, b, c):
    e1, e2, d = b - a, c - a, p - a
    d11, d12, d22, r1, r2 = e1 @ e1, e1 @ e2, e2 @ e2, e1 @ d, e2 @ d
    det = max(d11 * d22 - d12 * d12, 1e-18)
    u, v = (d22 * r1 - d12 * r2) / det, (d11 * r2 - d12 * r1) / det
    return np.array([1 - u - v, u, v])


def _insert(V, F, face, bary, pts):
    """Points put into a mesh as vertices of its own, each from its face and the point on it: the mesh with them, and
    each point's vertex. A point within SNAP of a vertex is that vertex; within SNAP of an edge, the edge is split
    there (on both its faces); else its face is cut in three. A face split keeps its corners' order."""
    V, F, alive, kids, by_edge, ids = list(V), [list(f) for f in F], [], {}, {}, []

    def key(u, v):
        return (min(u, v), max(u, v))

    def add(corners):
        F.append(list(corners))
        alive.append(True)
        f = len(F) - 1
        for k in range(3):
            by_edge.setdefault(key(corners[k], corners[(k + 1) % 3]), set()).add(f)
        return f

    def drop(f):
        alive[f] = False
        for k in range(3):
            by_edge[key(F[f][k], F[f][(k + 1) % 3])].discard(f)

    for f in range(len(F)):
        alive.append(True)
        for k in range(3):
            by_edge.setdefault(key(F[f][k], F[f][(k + 1) % 3]), set()).add(f)
    for f0, p in zip(face, pts):
        stack, found = [int(f0)], None  # the live face holding the point, among those its face was cut into
        while stack:
            f = stack.pop()
            if f in kids:
                stack += kids[f]
                continue
            w = _bary(p, *(V[k] for k in F[f]))
            if found is None or w.min() > found[1].min():
                found = (f, w)
        f, w = found
        a, b, c = F[f]
        corners = np.array([V[a], V[b], V[c]])
        off = np.linalg.norm(corners - p, axis=1)
        if off.min() <= SNAP:
            ids.append(F[f][int(off.argmin())])
            continue
        sides = np.array([np.linalg.norm(np.cross(p - corners[k], corners[(k + 1) % 3] - corners[k])) /
                          np.linalg.norm(corners[(k + 1) % 3] - corners[k]) for k in range(3)])
        V.append(p)
        ids.append(len(V) - 1)
        if sides.min() <= SNAP:  # on an edge: split it on both its faces
            k = int(sides.argmin())
            u, v = F[f][k], F[f][(k + 1) % 3]
            for g in list(by_edge[key(u, v)]):
                x, y, z = F[g]
                while z in (u, v):
                    x, y, z = y, z, x
                drop(g)
                kids[g] = [add((x, ids[-1], z)), add((ids[-1], y, z))]
        else:
            drop(f)
            kids[f] = [add((a, b, ids[-1])), add((b, c, ids[-1])), add((c, a, ids[-1]))]
    return np.array(V), np.array([F[f] for f in range(len(F)) if alive[f]]), np.array(ids)


def main():
    """The repair, its solvers and the texels, in numbers."""
    from tool import meshlines
    t = time.time()
    S = build("Skin")
    built = time.time() - t
    sizes = np.bincount(S.piece)
    print(f"The body's surface, repaired from its mesh in {built:.1f} s and cached: {S.points} points welded to {len(S.V)} "
          f"(within {WELD:g} cm), {len(S.F) - len(S.RF)} triangles drawn twice dropped ({len(S.F)} to {len(S.RF)}), "
          f"{len(S.RV) - len(S.V)} points copied where more than two faces met; {S.pieces} pieces, the biggest of "
          f"{sizes.max()} faces, {int((sizes < 50).sum())} under 50; the fine surface {len(S.FF)} faces over {len(S.FV)} points.")
    a, b = S.vertex((60, 16.5, -60)), S.vertex((60, 40, -60))  # the body's bottom edge, and up the side from it
    t = time.time()
    d = S.distance(S.RV[a], reach=40)
    took = time.time() - t
    path = S.line(a, b)
    print(f"From the bottom edge at {tuple(S.RV[a].round(1).tolist())} to {tuple(S.RV[b].round(1).tolist())} up the side: "
          f"{d[b]:.2f} cm along the surface ({took:.2f} s, within 40 cm), the straightest line between them {len(path)} points "
          f"and {np.linalg.norm(np.diff(path, axis=0), axis=1).sum():.2f} cm long, {np.linalg.norm(S.RV[a] - S.RV[b]):.2f} cm through the air.")
    c = meshlines.line((39, 19, 70))
    size = 4096
    t = time.time()
    d = S.distance(c.pts, reach=5)
    took = time.time() - t
    t = time.time()
    face, bary = S.texels(size)
    on = face >= 0
    at = S.sample(d, size)[on]
    sampled = time.time() - t
    print(f"From {c.name} ({c.length:.0f} cm, {len(c.pts)} points): the distance along the surface at {int(np.isfinite(d).sum())} "
          f"fine vertices within 5 cm in {took:.2f} s; read at every texel of the {size} map in {sampled:.1f} s: {int((at <= 3).sum())} "
          f"texels within 3 cm of it, {int((at <= 0.3).sum())} within 0.3.")
    t = time.time()
    width = np.linalg.norm(S.sample(S.FV, size)[on] - bake.bake("Skin", size, size)["position"].reshape(-1, 3)[on], axis=1)
    print(f"Every texel of the {size} map: {int(on.sum())} on the body, each on a face of the fine surface, its weights between "
          f"{bary[on].min():.3f} and {bary[on].max():.3f}; the surface's own points read through them land within {width.max():.4f} cm "
          f"of the bake's, the weld's reach ({time.time() - t:.1f} s).")
    i = len(c.pts) // 2
    t = time.time()
    f = int(S._locate(c.pts[i:i + 1])[0][0]) // 16
    way = S.carry(int(S.model[f]), _bary(c.pts[i], *S.RV[S.RF[f]]), np.cross(c.nrm[i], c.tan[i]), 10.0)
    print(f"Carried on square to it from its middle {tuple(c.pts[i].round(1).tolist())} for 10 cm: {len(way)} points, ending at "
          f"{tuple(way[-1].round(1).tolist())} ({time.time() - t:.3f} s).")


if __name__ == "__main__":
    main()
