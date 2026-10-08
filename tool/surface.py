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
    S.distance(points, reach)          cm along the surface from any points, per fine vertex within `reach` cm of
                                       them: exact (the points put into the fine surface as vertices of its own,
                                       then libigl's exact geodesics); inf beyond the reach and on other pieces
    S.signed(line, reach, closed, crease)   cm along the surface from a line (its points in order on the surface,
                                       every quarter centimetre or so), with a side: + to the line's left as it
                                       runs, seen from outside, - to its right, exact on each side (the line put in
                                       as a chain of the fine surface's edges, the surface cut along it, each side
                                       measured from its own copy of the line); with crease, cut along the model's
                                       crisp lines too, so nothing crosses one. A Field: .at(size, lin) reads it
                                       at texels of the set's map (nan beyond the reach), .gaps how many of the
                                       line's links couldn't be cut (0)
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
the line's own points); a line of the body within 8 cm costs a tenth of a second from any points, and half a second
to two with a side (the chain and the cut; a line's point landing beside its piece, on a sewn-on part, is put back
on it). (The heat methods and fast marching, measured on this mesh, were off by 0.2 to 2 cm: the model's triangles
are up to 24 cm long.) Nothing crosses a gap between pieces.
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
THIN = 1e-6      # cm: a face thinner than this isn't made (three points in a line): the point takes the nearest corner
JOIN = 12        # how many times a link of a line is halved to find the face it crosses, at most
STRAY = 0.5      # cm: a line's point landing on another piece this near the line's own piece is put back on it


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
        self._local, self._solvers, self._trees, self._near, self._longest, self._facing = {}, {}, {}, None, None, None

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
        if self._near is None:
            self._near = cKDTree(self.RV)
        return int(self._near.query(np.asarray(point, np.float64))[1])

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

    def _locate(self, pts, piece=None):
        """Each point's fine face, its weights at the face's corners and the point on it: the nearest point of the
        surface (or of one piece of it), exactly (libigl's tree over the fine faces), and never a face it isn't in."""
        import igl
        if piece not in self._trees:
            faces = np.arange(len(self.FF)) if piece is None else np.flatnonzero(self.piece[np.arange(len(self.FF)) // 16] == piece)
            tree = igl.AABB()
            tree.init(self.FV, self.FF[faces].astype(np.int64))
            self._trees[piece] = (tree, faces)
        tree, faces = self._trees[piece]
        pts = np.ascontiguousarray(pts, np.float64).reshape(-1, 3)
        _, f, on = tree.squared_distance(self.FV, self.FF[faces].astype(np.int64), pts)
        f = faces[f]
        A, B, C = (self.FV[self.FF[f, k]] for k in range(3))
        e1, e2, d = B - A, C - A, on - A
        d11, d12, d22 = (e1 * e1).sum(1), (e1 * e2).sum(1), (e2 * e2).sum(1)
        r1, r2 = (e1 * d).sum(1), (e2 * d).sum(1)
        det = np.maximum(d11 * d22 - d12 * d12, 1e-18)
        u, v = np.clip((d22 * r1 - d12 * r2) / det, 0, 1), np.clip((d11 * r2 - d12 * r1) / det, 0, 1)
        s = np.maximum(u + v, 1)
        u, v = u / s, v / s
        return f, np.stack([1 - u - v, u, v], 1), on

    def _patch(self, on, reach):
        """The fine faces within `reach` of points on the surface as a mesh of their own: V, F, and each face's and
        vertex's number on the whole surface."""
        if self._longest is None:
            self._longest = max(np.linalg.norm(self.FV[self.FF[:, k]] - self.FV[self.FF[:, k - 1]], axis=1).max() for k in range(3))
        near = cKDTree(on).query(self.FV, distance_upper_bound=reach + 2 * self._longest)[0]
        keep = np.flatnonzero(np.isfinite(near[self.FF]).any(1))
        verts, local = np.unique(self.FF[keep], return_inverse=True)
        return self.FV[verts], local.reshape(-1, 3), keep, verts

    def distance(self, points, reach=8.0):
        """cm along the surface from any points, per fine vertex within `reach` cm of them: the points put into the fine
        surface as vertices of its own, the distances then exact (libigl's exact geodesics) on a patch of the surface
        within the reach; inf beyond it, and on pieces holding none of the points."""
        import igl
        pts = np.asarray(points, np.float64).reshape(-1, 3)
        f, w, on = self._locate(pts)
        V, F, keep, verts = self._patch(on, reach)
        V2, F2, src, _, _ = _insert(V, F, np.searchsorted(keep, f), w, on)
        n = len(V2)
        comp = _components(F2, n)
        d = np.asarray(igl.exact_geodesic(V2, F2.astype(np.int64), np.unique(src).astype(np.int64), np.zeros(0, np.int64),
                                          np.arange(n, dtype=np.int64), np.zeros(0, np.int64))).reshape(-1)[:len(V)]
        ok = np.isin(comp[:len(V)], comp[src]) & (d <= reach)
        out = np.full(len(self.FV), np.inf)
        out[verts[ok]] = d[ok]
        return out

    def _chain(self, pts, closed):
        """A line's points on the fine surface (the piece most of them are on: a point landing on another piece within
        STRAY cm of it is put back), each joined to the next across one face or one edge: where two in a row sit in
        faces sharing no edge, the point where their link crosses the edge between them is added, or its midway,
        again and again (JOIN times at most; past four, through the one corner the faces share). (faces, weights,
        points), and how many links stayed unjoined."""
        pts = np.asarray(pts, np.float64).reshape(-1, 3)
        if closed and len(pts) > 1:
            pts = np.vstack([pts, pts[:1]])
        f, w, on = self._locate(pts)
        piece = int(np.bincount(self.piece[f // 16]).argmax())
        stray = np.flatnonzero(self.piece[f // 16] != piece)
        if len(stray):
            f2, w2, on2 = self._locate(pts[stray], piece)
            back = stray[np.linalg.norm(on2 - pts[stray], axis=1) <= STRAY]
            sel = np.isin(stray, back)
            f[back], w[back], on[back] = f2[sel], w2[sel], on2[sel]
        out, gaps = [(int(f[0]), w[0], on[0])], 0

        def inside(point, face):
            A, B, C = self.FV[self.FF[face]]
            n = np.cross(B - A, C - A)
            if abs((point - A) @ n) > SNAP * max(np.linalg.norm(n), 1e-18):
                return None
            bw = _bary(point, A, B, C)
            return bw if bw.min() >= -1e-6 else None

        def join(a, b, depth):
            nonlocal gaps
            fa, fb = a[0], b[0]
            if fa == fb:
                out.append(b)
                return
            bw = inside(b[2], fa)
            if bw is not None:  # on an edge or a corner of a's face: in it too
                out.append((fa, np.clip(bw, 0, 1), b[2]))
                return
            shared = np.intersect1d(self.FF[fa], self.FF[fb])
            if len(shared) == 2:
                u, v = self.FV[shared[0]], self.FV[shared[1]]
                x = _crossing(a[2], b[2], u, v)
                A, B, C = self.FV[self.FF[fa]]
                out.append((fa, np.clip(_bary(x, A, B, C), 0, 1), x))
                out.append(b)
                return
            if len(shared) == 1 and depth >= 4:
                corner = self.FV[shared[0]]
                A, B, C = self.FV[self.FF[fa]]
                out.append((fa, np.clip(_bary(corner, A, B, C), 0, 1), corner))
                out.append(b)
                return
            if depth >= JOIN:
                gaps += 1
                out.append(b)
                return
            mid = 0.5 * (a[2] + b[2])
            fm, wm, om = self._locate(mid[None], piece)
            m = (int(fm[0]), wm[0], om[0])
            join(a, m, depth + 1)
            join(m, b, depth + 1)

        for k in range(1, len(on)):
            join(out[-1], (int(f[k]), w[k], on[k]), 0)
        faces = np.array([o[0] for o in out])
        return faces, np.array([o[1] for o in out]), np.array([o[2] for o in out]), gaps

    def signed(self, line, reach=8.0, closed=False, crease=False):
        """cm along the surface from a line, with a side: + to its left as it runs, seen from outside, - to its right.
        The line's points go into the fine surface as a chain of its edges (_chain), the surface is cut along them (and,
        with `crease`, along the model's crisp lines: where faces meet at meshlines.SHARP degrees or more, so nothing
        crosses one), and each side's distance is exact (libigl's exact geodesics) from its own copy of the line; a
        point reached from both sides, round an open line's end, takes the nearer. A Field, read at texels."""
        import igl
        faces, w, on, gaps = self._chain(line, closed)
        V, F, keep, verts = self._patch(on, reach)
        V2, F2, _, parent, ids = _insert(V, F, np.searchsorted(keep, faces), w, on, chain=True)
        n2 = len(F2)
        # every edge of the patch: its faces and the corner it starts from in each
        slot = {}
        for g in range(n2):
            x, y, z = F2[g]
            for k, (u, v) in enumerate(((x, y), (y, z), (z, x))):
                slot.setdefault((min(u, v), max(u, v)), []).append((g, k, u))
        cuts = np.zeros((n2, 3), bool)
        left, right = set(), set()
        for a, b in zip(ids[:-1], ids[1:]):
            if a == b:
                continue
            here = slot.get((min(a, b), max(a, b)), [])
            if not here:
                gaps += 1
                continue
            for g, k, u in here:
                cuts[g, k] = True
                (left if u == a else right).add((g, k))  # the face running a to b is on the left of a to b
        if crease:
            from tool import meshlines
            fn = self.fine_facing()[keep]
            cos = np.cos(np.radians(meshlines.SHARP))
            for (u, v), here in slot.items():
                if len(here) == 2 and fn[parent[here[0][0]]] @ fn[parent[here[1][0]]] <= cos:
                    for g, k, _ in here:
                        cuts[g, k] = True
        Vn, Fn, _ = igl.cut_mesh(V2, F2.astype(np.int64), cuts)
        n = len(Vn)
        comp = _components(Fn, n)
        d = []
        for side in (left, right):
            src = np.unique([Fn[g, (k + j) % 3] for g, k in side for j in (0, 1)]).astype(np.int64)
            if not len(src):
                d.append(np.full(n, np.inf))
                continue
            dist = np.asarray(igl.exact_geodesic(Vn, Fn, src, np.zeros(0, np.int64), np.arange(n, dtype=np.int64),
                                                 np.zeros(0, np.int64))).reshape(-1)
            dist[~np.isin(comp, comp[src])] = np.inf
            d.append(dist)
        return Field(self, keep, parent, Vn, Fn, np.stack(d, 1), gaps)

    def fine_facing(self):
        """Each fine face's facing, outward (its winding's, as the model's)."""
        if self._facing is None:
            A, B, C = (self.FV[self.FF[:, k]] for k in range(3))
            n = np.cross(B - A, C - A)
            n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
            n *= np.where((n * self.fn[self.model[np.arange(len(self.FF)) // 16]]).sum(1) < 0, -1.0, 1.0)[:, None]
            self._facing = n
        return self._facing

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


def _to_segment(p, a, b):
    """How far a point is from the segment ab (its ends included)."""
    ab = b - a
    t = np.clip((p - a) @ ab / max(ab @ ab, 1e-18), 0.0, 1.0)
    return float(np.linalg.norm(p - (a + t * ab)))


def _bary(p, a, b, c):
    e1, e2, d = b - a, c - a, p - a
    d11, d12, d22, r1, r2 = e1 @ e1, e1 @ e2, e2 @ e2, e1 @ d, e2 @ d
    det = max(d11 * d22 - d12 * d12, 1e-18)
    u, v = (d22 * r1 - d12 * r2) / det, (d11 * r2 - d12 * r1) / det
    return np.array([1 - u - v, u, v])


def _crossing(p, q, u, v):
    """Where the link pq crosses the edge uv: the point of the edge nearest the link."""
    d1, d2, r = q - p, v - u, p - u
    a, b, c, d, e = d1 @ d1, d1 @ d2, d2 @ d2, d1 @ r, d2 @ r
    den = a * c - b * b
    t = np.clip((a * e - b * d) / den, 0, 1) if den > 1e-18 else 0.5  # along the edge
    s = np.clip((b * t - d) / max(a, 1e-18), 0, 1)                   # along the link, nearest that
    t = np.clip((b * s + e) / max(c, 1e-18), 0, 1)
    return u + t * d2


def _nearest_on(p, a, b, c):
    """The point of the triangle abc nearest p."""
    best, near = None, np.inf
    for u, v in ((a, b), (b, c), (c, a)):
        uv = v - u
        t = np.clip((p - u) @ uv / max(uv @ uv, 1e-18), 0.0, 1.0)
        q = u + t * uv
        d = np.linalg.norm(p - q)
        if d < near:
            best, near = q, d
    return best


def _thin(a, b, c):
    """Whether a triangle is thinner than THIN: its smallest height."""
    e = max(np.linalg.norm(b - a), np.linalg.norm(c - b), np.linalg.norm(a - c))
    return np.linalg.norm(np.cross(b - a, c - a)) / max(e, 1e-18) < THIN


def _components(F, n):
    g = coo_matrix((np.ones(3 * len(F)), (F.reshape(-1), np.roll(F, 1, 1).reshape(-1))), shape=(n, n))
    return connected_components(g, directed=False)[1]


def _insert(V, F, face, bary, pts, chain=False):
    """Points put into a mesh as vertices of its own, each from its face and the point on it: the mesh with them, each
    point's vertex, each face's parent (the face of F it was cut from) and the chain of vertices the points make
    (with the crossings walked between them). A point within SNAP of a vertex is that
    vertex; within SNAP of an edge (the edge itself, not its line carried on), the edge is split there (on both its
    faces); else its face is cut in three. A split that would make a face thinner than THIN (three points in a line,
    beside the model's needle-thin faces: the exact solver never returns on a face of no area) isn't made: the point
    takes the nearest corner. A face split keeps its corners' order. With `chain`, each point is joined to the one
    before by edges: where their link crosses the faces between them (the pieces of one face, in one plane), the
    crossings are put in too, so the chain is a chain of the mesh's edges and the mesh can be cut along it."""
    V, F, alive, kids, by_edge, by_vertex, ids = list(V), [list(f) for f in F], [], {}, {}, {}, []
    parent = list(range(len(F)))

    def key(u, v):
        return (min(u, v), max(u, v))

    def add(corners, of):
        F.append(list(corners))
        alive.append(True)
        parent.append(of)
        f = len(F) - 1
        for k in range(3):
            by_edge.setdefault(key(corners[k], corners[(k + 1) % 3]), set()).add(f)
            by_vertex.setdefault(corners[k], set()).add(f)
        return f

    def drop(f):
        alive[f] = False
        for k in range(3):
            by_edge[key(F[f][k], F[f][(k + 1) % 3])].discard(f)
            by_vertex[F[f][k]].discard(f)

    def split_edge(u, v, p):
        """The edge uv split at p on each of its faces: p's vertex, or None when a face would come out thin."""
        plan = []
        for g in list(by_edge[key(u, v)]):
            x, y, z = F[g]
            while z in (u, v):
                x, y, z = y, z, x
            plan.append((g, x, y, z))
        if any(_thin(V[x], p, V[z]) or _thin(p, V[y], V[z]) for _, x, y, z in plan):
            return None
        V.append(p)
        new = len(V) - 1
        for g, x, y, z in plan:
            drop(g)
            kids[g] = [add((x, new, z), parent[g]), add((new, y, z), parent[g])]
        return new

    def link(a, b):
        """Edges from a to b across the faces their link crosses, a crossing put on each edge in the way: the vertices
        walked, a to b (b missing when the way was lost)."""
        walked = [a]
        for _ in range(64):
            if a == b or key(a, b) in by_edge:
                return walked + [b]
            P, Q = np.asarray(V[a]), np.asarray(V[b])
            hit = None
            for g in list(by_vertex.get(a, ())):
                x, y, z = F[g]
                while x != a:
                    x, y, z = y, z, x
                U, W = np.asarray(V[y]) - P, np.asarray(V[z]) - P
                st = np.linalg.lstsq(np.stack([U, W], 1), Q - P, rcond=None)[0]
                if st[0] >= -1e-9 and st[1] >= -1e-9 and st.sum() > 1e-9:
                    hit = (y, z, float(st.sum()))
                    break
            if hit is None or hit[2] <= 1 + 1e-9:
                return walked
            y, z, reach = hit
            x = P + (Q - P) / reach
            off = [np.linalg.norm(x - np.asarray(V[y])), np.linalg.norm(x - np.asarray(V[z]))]
            new = None if min(off) <= SNAP else split_edge(y, z, x)
            a = new if new is not None else (y if off[0] <= off[1] else z)
            walked.append(a)
        return walked

    for f in range(len(F)):
        alive.append(True)
        for k in range(3):
            by_edge.setdefault(key(F[f][k], F[f][(k + 1) % 3]), set()).add(f)
            by_vertex.setdefault(F[f][k], set()).add(f)
    path = []  # the chain: each point's vertex, and the vertices walked between it and the one before
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
        if w.min() < -1e-9:  # outside every face it could be in (rounding): onto the nearest one's edge
            p = _nearest_on(p, *corners)
        off = np.linalg.norm(corners - p, axis=1)
        if off.min() <= SNAP:
            ids.append(F[f][int(off.argmin())])
        else:
            sides = np.array([_to_segment(p, corners[k], corners[(k + 1) % 3]) for k in range(3)])
            if sides.min() <= SNAP:  # on an edge: split it on both its faces
                k = int(sides.argmin())
                new = split_edge(F[f][k], F[f][(k + 1) % 3], p)
                ids.append(F[f][int(off.argmin())] if new is None else new)
            elif _thin(V[a], V[b], p) or _thin(V[b], V[c], p) or _thin(V[c], V[a], p):
                ids.append(F[f][int(off.argmin())])
            else:
                V.append(p)
                ids.append(len(V) - 1)
                drop(f)
                kids[f] = [add((a, b, ids[-1]), parent[f]), add((b, c, ids[-1]), parent[f]), add((c, a, ids[-1]), parent[f])]
        if chain and len(ids) > 1:
            path += link(ids[-2], ids[-1])[1:]
        else:
            path.append(ids[-1])
    live = [f for f in range(len(F)) if alive[f]]
    return np.array(V), np.array([F[f] for f in live]), np.array(ids), np.array([parent[f] for f in live]), np.array(path)


class Field:
    """The distance from each side of a line over a patch of the fine surface, on the mesh the line was cut into: read
    at texels of the set's map as one signed distance. keep: the patch's faces on the whole surface; parent: each cut
    face's face of the patch; Vn, Fn: the cut mesh; value: (n, 2) per vertex of it, from the line's left and from its
    right (inf where unreached). Each side is read on its own and the nearer takes the texel: a signed value read
    across a face would fake a zero wherever the two sides meet round an open line's end."""

    def __init__(self, S, keep, parent, Vn, Fn, value, gaps):
        self.S, self.keep, self.Vn, self.Fn, self.value, self.gaps = S, keep, Vn, Fn, value, gaps
        order = np.argsort(parent, kind="stable")
        starts = np.r_[0, np.flatnonzero(np.diff(parent[order])) + 1]
        self.kids = {int(parent[order[a]]): order[a:b] for a, b in zip(starts, np.r_[starts[1:], len(order)])}

    def at(self, size, lin=None):
        """The signed distance at texels of the set's map (flat indices; all by default): + to the line's left, - to its
        right; nan off the patch or beyond its reach."""
        face, bary = self.S.texels(size, lin)
        out = np.full((len(face), 2), np.inf)
        j = np.searchsorted(self.keep, face)
        j = np.minimum(j, len(self.keep) - 1)
        on = (face >= 0) & (self.keep[j] == face)
        if not on.any():
            return np.full(len(face), np.nan)
        rows, j = np.flatnonzero(on), j[on]
        P = (self.S.FV[self.S.FF[face[on]]] * bary[on][..., None]).sum(1)
        single = np.array([len(self.kids[int(k)]) == 1 for k in j])
        # a face kept whole: its corners' values at the texel's weights (its corners stay in order)
        g = np.array([self.kids[int(k)][0] for k in j[single]], dtype=np.int64)
        if len(g):
            out[rows[single]] = _read(self.value[self.Fn[g]], bary[on][single].astype(np.float64))
        # a face the line cut: the piece the texel is in, by its weights there
        for k in np.unique(j[~single]):
            mine = np.flatnonzero(j == k)
            gs = self.kids[int(k)]
            A, B, C = (self.Vn[self.Fn[gs, c]] for c in range(3))
            best, bw = None, None
            for gi, (a, b, c) in enumerate(zip(A, B, C)):
                w = np.array([_bary(p, a, b, c) for p in P[mine]])
                m = w.min(1)
                if best is None:
                    best, bw, bm = np.full(len(mine), gi), w, m
                else:
                    better = m > bm
                    best[better], bw[better], bm[better] = gi, w[better], m[better]
            wt = np.clip(bw, 0, None)
            out[rows[mine]] = _read(self.value[self.Fn[gs[best]]], wt / np.maximum(wt.sum(1, keepdims=True), 1e-12))
        value = np.where(out[:, 0] <= out[:, 1], out[:, 0], -out[:, 1])
        value[np.isinf(out).all(1)] = np.nan
        return value


def _read(corners, wt):
    """Corner values (m, 3, 2) at weights (m, 3): a corner out of reach (inf) counts only at weight 0."""
    wt = wt[..., None]
    with np.errstate(invalid="ignore"):  # inf times 0 at a corner out of reach, which the weight then drops
        return np.where(wt > 0, corners * wt, 0.0).sum(1)


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
    field = S.signed(c.pts, reach=5)
    took = time.time() - t
    t = time.time()
    face, bary = S.texels(size)
    on = face >= 0
    at = field.at(size)[on]
    sampled = time.time() - t
    print(f"From {c.name} ({c.length:.0f} cm, {len(c.pts)} points): the signed distance along the surface, exact on each side "
          f"({field.gaps} links uncut), in {took:.2f} s; read at every texel of the {size} map in {sampled:.1f} s: "
          f"{int((np.abs(at) <= 3).sum())} texels within 3 cm of it, {int(((at > 0) & (at <= 3)).sum())} on its left, "
          f"{int((np.abs(at) <= 0.3).sum())} within 0.3.")
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
