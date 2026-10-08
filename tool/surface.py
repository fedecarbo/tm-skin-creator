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
                                       at texels of the set's map (nan beyond the reach), .contour(cm) the line
                                       where it is `cm` (a line beside the line), .gaps how many of the line's
                                       links couldn't be cut (0)
    S.path(points)                     the straightest way along the surface through points, in order: between
                                       each two, the shortest line on the surface near the straight one (edge
                                       flips); from one piece to another, straight across the gap: (n, 3) cm
    S.carry(point, direction, cm)      the straightest way on along the surface from a point in a direction, `cm`
                                       far (the tracer), across a hairline between pieces, stopping where the body
                                       ends: (n, 3) cm
    S.facing(points)                   the surface's facing at points (outward)
    S.chart(centre, right, up, reach, crease)   the surface round a point as a sticker pressed onto it there: for the fine
                                       surface within `reach` cm along the surface of the centre, each vertex's place
                                       on the sticker, X along `right` and Y along `up` (cm), exact: its distance from
                                       the centre by exact geodesics (the centre put in as a vertex), its direction by
                                       the law of cosines against four more sources EPS cm away along the surface,
                                       before and behind it along right and along up (the tracer's); with crease, the
                                       patch cut along the model's crisp lines first, so the sticker stays on the
                                       centre's own panel; without, it folds over them as a pressed sticker does,
                                       spans a step flat (a wall of skin thinner than STEP cm between two skins, a
                                       raised plate's edge: the raised skin is measured as if it sat level with the
                                       other) and bridges a gap up to BRIDGE cm between two skins facing alike. A
                                       Chart: .at(size, lin) reads (X, Y) at texels (nan beyond the reach), .read(xy,
                                       points=) at points on the car, .stretch() how far the sticker is stretched on
                                       each face (0.05: its lengths grow or shrink 5 %; inf where it folds over itself)
    S.texels(size, lin)                where texels of the set's map (flat indices row * size + column; all by
                                       default) sit on the fine surface, from the bake's triangle (tool/bake.py):
                                       each one's fine face (-1 off the car) and its weights at the face's corners
    S.sample(values, size, lin)        a value per fine vertex read at those texels through their faces

The distances are exact on the surface, and within 0.05 cm between the fine surface's vertices (measured against
the line's own points); a line of the body within 8 cm costs a tenth of a second from any points, and half a second
to two with a side (the chain and the cut; a line's point landing beside its piece, on a sewn-on part, is put back
on it); a path or a line carried on, milliseconds; a chart (five solves) a quarter of a second to one. A chart's
places are worked out at the surface's own vertices, where every distance is exact, and read between them by their
faces: checked against rays the tracer shoots from the centre, within 0.01 cm on flat panels, the rear flank's rolled
shoulder and the nose's roll alike (2026-10-08; a distance read between vertices would be off by up to 1.7 cm near
the centre, where it is a cone over a 6 cm face). (The heat methods and fast marching, measured on this mesh, were
off by 0.2 to 2 cm: the model's triangles are up to 24 cm long.) The body's skin is one piece (the body shell, the
flanks, the skirts, the nose tip and the rest sewn with shared points); the sidepod tops, the tail's corners, the
diffuser and the nose fin are pieces of their own, a hair apart from it (0.05 to 0.35 cm).
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
HOP = 0.4        # cm: a line carried on hops a gap this wide between pieces (they're 0.05 to 0.35 apart)
BRIDGE = 1.5     # cm: a sticker pressed over every edge bridges a gap this wide between two skins facing alike
STEP = 1.5       # cm: a wall of skin this thin between two skins (a raised plate's edge) is a step a sticker spans flat
WALL = 70.0      # degrees: skin facing this far from the sticker's centre is a wall, where it's thin
SPECK = 0.5      # cm: a piece of a contour shorter than this is the solver's noise, not a line
EPS = 0.5        # cm: how far a chart's four more sources sit from its centre along the surface
HALF_TEXEL = 0.05  # cm: a contour's vertex this far off the straight line between its neighbours, where the surface
# is flat, means the faces there are too big for the bend: a distance is read straight across a face, so a line
# beside a bent line comes out as a polygon on big faces. Those faces are cut finer and the distance solved again
FINEST = 0.2     # cm: a face with no edge longer than this isn't cut finer
ROUNDS = 4       # how many times at most


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
        self._local, self._solvers, self._trees, self._longest, self._facing = {}, {}, {}, None, None
        self._maps = {}  # per map size: the bake's triangle per texel and the mesh's UVs, kept (the bake is 500 MB unpacked)

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

    def _tracer(self, p):
        import potpourri3d as pp3d
        if p not in self._solvers:
            q = self._piece(p)
            self._solvers[p] = pp3d.GeodesicTracer(q["V"], q["F"])
        return self._solvers[p]

    def _on(self, points):
        """Points brought onto the surface: each one's repaired face, its weights at the face's corners and the point
        on it."""
        f, _, on = self._locate(points)
        f = f // 16
        return f, np.array([_bary(p, *self.RV[self.RF[c]]) for p, c in zip(on, f)]), on

    def path(self, points):
        """The straightest way along the surface through points, in order: each two in a row joined by the shortest
        line on the surface near the straight one between them (the points put into their piece as vertices of its
        own, then edge flips), one pair at a time, so the line passes through every point; from one piece to another,
        straight across the gap. (n, 3) cm, the points themselves among them."""
        import potpourri3d as pp3d
        f, w, on = self._on(np.asarray(points, np.float64).reshape(-1, 3))
        piece = self.piece[f]
        out, k = [on[0]], 0
        while k < len(on) - 1:
            j = k
            while j + 1 < len(on) and piece[j + 1] == piece[k]:
                j += 1
            if j == k:  # the next point is on another piece: across the gap
                out.append(on[k + 1])
                k += 1
                continue
            q = self._piece(int(piece[k]))
            V2, F2, ids, _, _ = _insert(q["V"], q["F"], q["fback"][f[k:j + 1]], w[k:j + 1], on[k:j + 1])
            solver = pp3d.EdgeFlipGeodesicSolver(V2, F2)
            for a, b in zip(ids[:-1], ids[1:]):
                if a != b:
                    out.extend(np.asarray(solver.find_geodesic_path(int(a), int(b)))[1:])
            k = j
        return np.array(out)

    def carry(self, point, direction, cm):
        """The straightest way on along the surface from a point in a direction (its part along the surface), `cm`
        far (the tracer): (n, 3) cm, the point first. Across a gap between pieces up to HOP cm wide it carries on;
        where the body ends it stops."""
        pt, d, left, out = np.asarray(point, np.float64), np.asarray(direction, np.float64), float(cm), []
        for _ in range(8):
            f, w, on = self._on(pt[None])
            f, p = int(f[0]), int(self.piece[f[0]])
            A, B, C = self.RV[self.RF[f]]
            n = np.cross(B - A, C - A)
            n /= max(np.linalg.norm(n), 1e-12)
            d = d - (d @ n) * n
            if np.linalg.norm(d) < 1e-9 or left <= 0.01:
                break
            way = np.asarray(self._tracer(p).trace_geodesic_from_face(int(self._piece(p)["fback"][f]), w[0], d / np.linalg.norm(d) * left))
            out.extend(way if not out else way[1:])
            left -= float(np.linalg.norm(np.diff(way, axis=0), axis=1).sum())
            if left <= 0.01 or len(way) < 2:
                break
            d = way[-1] - way[-2]  # stopped short: the body ends here, or another piece begins a hair on
            d /= max(np.linalg.norm(d), 1e-12)
            probe = way[-1] + d * HOP
            f2, _, on2 = self._locate(probe[None])
            if self.piece[int(f2[0]) // 16] == p or np.linalg.norm(on2[0] - probe) > HOP:
                break
            pt = on2[0]
        return np.array(out if out else [pt])

    def facing(self, points):
        """The surface's facing at points (their faces', outward): (n, 3)."""
        return self.fine_facing()[self._locate(points)[0]]

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

    def signed(self, line, reach=8.0, closed=False, crease=False, levels=()):
        """cm along the surface from a line, with a side: + to its left as it runs, seen from outside, - to its right.
        The line's points go into the fine surface as a chain of its edges (_chain), the surface is cut along them (and,
        with `crease`, along the model's crisp lines: where faces meet at meshlines.SHARP degrees or more, so nothing
        crosses one), and each side's distance is exact (libigl's exact geodesics) from its own copy of the line; a
        point reached from both sides, round an open line's end, takes the nearer. An open line's cut runs one edge on
        past each end (the edge there that carries its way on best), so each side keeps its own copy of the end and the
        two sides meet only beyond it, not square to it. `levels`: the distances that will be drawn as lines (a band's
        edges, a line beside the line): where their contours bend across faces too big for them (HALF_TEXEL), those
        faces are cut finer and the distance solved again, ROUNDS times at most. A Field, read at texels."""
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
        if not closed and ids[0] != ids[-1]:
            chain = set(zip(np.minimum(ids[:-1], ids[1:]), np.maximum(ids[:-1], ids[1:])))
            for end, prev in ((ids[0], ids[1]), (ids[-1], ids[-2])):
                way = V2[end] - V2[prev]
                best = None
                for (u, v) in slot:
                    if end in (u, v) and (u, v) not in chain:
                        d = V2[v if u == end else u] - V2[end]
                        score = way @ d / max(np.linalg.norm(d), 1e-12)
                        if best is None or score > best[0]:
                            best = (score, (u, v))
                if best is not None:
                    for g, k, _ in slot[best[1]]:
                        cuts[g, k] = True
        if crease:
            cuts |= self._sharp(F2, parent, keep)
        Vn, Fn, _ = igl.cut_mesh(V2, F2.astype(np.int64), cuts)
        src = [np.unique([Fn[g, (k + j) % 3] for g, k in side for j in (0, 1)]).astype(np.int64) for side in (left, right)]
        field = Field(self, keep, parent, Vn, Fn, _solve(Vn, Fn, src), gaps)
        for _ in range(ROUNDS):
            coarse = field.too_coarse(levels)
            if not coarse:
                break
            Vn, Fn, parent, src = _finer(Vn, Fn, parent, coarse, src)
            field = Field(self, keep, parent, Vn, Fn, _solve(Vn, Fn, src), gaps)
        return field

    def _sharp(self, F2, parent, keep):
        """The edges of a patch's mesh along the model's crisp lines (its faces meeting at meshlines.SHARP degrees or more),
        as igl.cut_mesh takes them: (faces, 3) bool, the edge from each corner to the next."""
        from tool import meshlines
        fn = self.fine_facing()[keep]
        cos = np.cos(np.radians(meshlines.SHARP))
        slot = {}
        for g in range(len(F2)):
            x, y, z = F2[g]
            for k, (u, v) in enumerate(((x, y), (y, z), (z, x))):
                slot.setdefault((min(u, v), max(u, v)), []).append((g, k))
        cuts = np.zeros((len(F2), 3), bool)
        for here in slot.values():
            if len(here) == 2 and fn[parent[here[0][0]]] @ fn[parent[here[1][0]]] <= cos:
                for g, k in here:
                    cuts[g, k] = True
        return cuts

    def chart(self, centre, right, up, reach=12.0, crease=False):
        """The surface round a point as a sticker pressed onto it there (a Chart; the key above says how): right and up in
        the surface's tangent plane at the centre, the sticker's X and Y. The distance from the centre is exact; the
        direction comes from the law of cosines against the four sources EPS cm away (each pair's two agree on a flat
        panel; a source that couldn't go, where the body ends or across a cut, leaves the other to tell; where neither
        could, the direction through the air serves). Without the crease cut the patch's steps are spanned (_spanned) and
        its gaps bridged (_bridged)."""
        import igl
        p = self._locate(np.asarray(centre, np.float64)[None])[2][0]
        right, up = (np.asarray(v, np.float64) for v in (right, up))
        pts = [p] + [self.carry(p, d, EPS)[-1] for d in (right, -right, up, -up)]
        f, w, on = self._locate(np.asarray(pts))
        V, F, keep, _ = self._patch(on, reach)
        V2, F2, ids, parent, _ = _insert(V, F, np.searchsorted(keep, f), w, on)
        if crease:
            Vn, Fn, back = igl.cut_mesh(V2, F2.astype(np.int64), self._sharp(F2, parent, keep))
            copies = [np.flatnonzero(np.asarray(back).reshape(-1) == i) for i in ids]
        else:
            fn = self.fine_facing()[keep]
            Vn, Fn, parent = _spanned(V2, F2.astype(np.int64), parent, fn, np.cross(right, up), int(ids[0]))
            Vn, Fn, parent = _bridged(Vn, Fn, parent, fn)
            copies = [np.array([i]) for i in ids]
        n = len(Vn)
        comp = _components(Fn, n)
        D = []
        for src in copies:
            d = np.asarray(igl.exact_geodesic(Vn, Fn, src.astype(np.int64), np.zeros(0, np.int64), np.arange(n, dtype=np.int64),
                                              np.zeros(0, np.int64))).reshape(-1)
            d[~np.isin(comp, comp[src])] = np.inf
            D.append(d)
        r = D[0]
        reached = r <= reach
        xy = np.zeros((n, 2))
        rel = Vn - p
        for k, (axis, plus, minus) in enumerate(((right, 1, 2), (up, 3, 4))):
            got, count = np.zeros(n), np.zeros(n)
            for src, sign in ((plus, 1.0), (minus, -1.0)):
                eps = float(r[copies[src]].min()) if len(copies[src]) else np.inf
                if not 0.1 * EPS <= eps <= 1.5 * EPS:  # it didn't go, or the surface is cut between
                    continue
                ok = reached & np.isfinite(D[src])
                got[ok] += sign * (r[ok] ** 2 + eps ** 2 - D[src][ok] ** 2) / (2 * eps)
                count[ok] += 1
            xy[:, k] = np.where(count > 0, got / np.maximum(count, 1), rel @ axis)
        rho = np.hypot(xy[:, 0], xy[:, 1])
        xy *= np.where(rho > 1e-9, r / np.maximum(rho, 1e-9), 1.0)[:, None]  # the direction theirs, the distance exact
        xy[~reached] = np.nan
        facing = np.cross(right, up)
        return Chart(self, keep, parent, Vn, Fn, xy, np.where(reached, r, np.inf), p, right, up, facing / np.linalg.norm(facing))

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
        if size not in self._maps:
            self._maps[size] = (bake.bake(self.tset, size, size)["tri"].reshape(-1), fbx.meshes()[fbx.MESH_OF[self.tset]]["tri_uv"])
        tri, uv = self._maps[size]
        lin = np.arange(tri.size) if lin is None else np.asarray(lin, np.int64)
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


def _spanned(V, F, parent, fn, facing, centre):
    """A patch's mesh with its steps spanned, as a sticker pressed over every edge spans them flat rather than running
    down and up: a wall (faces facing WALL degrees or more from the sticker's facing) thinner than STEP cm (twice its
    area over its perimeter) between the centre's skin and another is taken out, the other skin moved onto the
    centre's by the step (the mean offset between the wall's two rims) and the rims welded; a wall between two skins
    neither the centre's is left as it is. Faces that collapse go."""
    n = len(V)
    wall = np.flatnonzero(fn[np.maximum(parent, 0)] @ facing < np.cos(np.radians(WALL)))
    if not len(wall):
        return V, F, parent
    strips = _components(F[wall], n)[F[wall]].min(1)  # the walls joined edge to edge, by their lowest vertex's label
    A, B, C = (V[F[wall, k]] for k in range(3))
    area = 0.5 * np.linalg.norm(np.cross(B - A, C - A), axis=1)
    per = np.linalg.norm(B - A, axis=1) + np.linalg.norm(C - B, axis=1) + np.linalg.norm(A - C, axis=1)
    thin = set()
    for s in np.unique(strips):
        mine = strips == s
        if 2 * area[mine].sum() / max(per[mine].sum() / 2, 1e-9) <= STEP:  # each inner edge counted twice: half the perimeter
            thin.add(s)
    gone = wall[np.isin(strips, list(thin))]
    if not len(gone):
        return V, F, parent
    rest = np.setdiff1d(np.arange(len(F)), gone)
    comp = _components(F[rest], n)
    rim = np.unique(F[gone])
    home = comp[centre]
    V = V.copy()
    weld = np.arange(n)
    for k in np.unique(comp[rim]):
        if k == home:
            continue
        top = rim[comp[rim] == k]
        low = rim[comp[rim] == home]
        if not len(low) or not len(top):
            continue
        d, j = cKDTree(V[low]).query(V[top], distance_upper_bound=2 * STEP)
        ok = np.isfinite(d)
        if ok.sum() < 2:
            continue
        shift = (V[low[j[ok]]] - V[top[ok]]).mean(0)
        V[comp == k] += shift
        d, j = cKDTree(V[low]).query(V[top], distance_upper_bound=0.3)
        weld[top[np.isfinite(d)]] = low[j[np.isfinite(d)]]
    F2 = weld[F[rest]]
    keep = (F2[:, 0] != F2[:, 1]) & (F2[:, 1] != F2[:, 2]) & (F2[:, 2] != F2[:, 0])
    keep &= ~np.array([_thin(*V[f]) for f in F2])
    return V, F2[keep], parent[rest][keep]


def _bridged(V, F, parent, fn):
    """A patch's mesh with its gaps bridged, as a sticker pressed over every edge bridges them: where two skins facing
    alike (within 60 degrees) end within BRIDGE cm of each other (a raised plate's step, the hairline between two
    pieces), the edges along their ends are joined by triangles, so a distance runs straight across instead of round.
    Each end's vertex takes the nearest vertex of another end (never one it shares an edge with), and two vertices in
    a row along an end make two triangles with their two. The bridges' faces have no face of the patch (parent -1)."""
    edge = {}
    for g, (x, y, z) in enumerate(F):
        for u, v in ((x, y), (y, z), (z, x)):
            edge.setdefault((min(u, v), max(u, v)), []).append(g)
    rim = [(u, v, gs[0]) for (u, v), gs in edge.items() if len(gs) == 1]
    if len(rim) < 2:
        return V, F, parent
    verts = np.unique([u for u, v, _ in rim] + [v for u, v, _ in rim])
    facing = {}
    for u, v, g in rim:
        for k in (u, v):
            facing.setdefault(k, []).append(fn[parent[g]])
    nrm = np.array([np.mean(facing[k], 0) for k in verts])
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)
    tree = cKDTree(V[verts])
    linked = set(edge)
    match = {}
    for i, k in enumerate(verts):
        for d, j in zip(*tree.query(V[k], k=min(8, len(verts)), distance_upper_bound=BRIDGE)):
            if not np.isfinite(d) or j == i or d < 1e-9:
                continue
            m = int(verts[j])
            if (min(k, m), max(k, m)) in linked or nrm[i] @ nrm[j] < 0.5:
                continue
            match[int(k)] = m
            break
    if not match:
        return V, F, parent
    F, parent = list(map(tuple, F)), list(parent)
    count = {e: len(gs) for e, gs in edge.items()}  # faces per edge: a bridge never gives an edge a third, nor makes a thin face
    for u, v, _ in rim:
        if u not in match or v not in match:
            continue
        a, b = match[u], match[v]
        if min(a, b) < min(u, v):
            continue  # the other end builds this bridge
        for tri in (((u, v, b),) if a == b else ((u, v, b), (u, b, a))):
            if len(set(tri)) < 3 or _thin(*(V[k] for k in tri)):
                continue
            es = [(min(tri[k], tri[(k + 1) % 3]), max(tri[k], tri[(k + 1) % 3])) for k in range(3)]
            if any(count.get(e, 0) >= 2 for e in es):
                continue
            for e in es:
                count[e] = count.get(e, 0) + 1
            F.append(tri)
            parent.append(-1)
    return V, np.array(F, np.int64), np.array(parent)


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


def _bary_many(P, a, b, c):
    """_bary for points P (m, 3) in one triangle: (m, 3)."""
    e1, e2, d = b - a, c - a, P - a
    d11, d12, d22 = e1 @ e1, e1 @ e2, e2 @ e2
    r1, r2 = d @ e1, d @ e2
    det = max(d11 * d22 - d12 * d12, 1e-18)
    u, v = (d22 * r1 - d12 * r2) / det, (d11 * r2 - d12 * r1) / det
    return np.stack([1 - u - v, u, v], 1)


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


def _solve(Vn, Fn, src):
    """The exact distance (libigl) over a mesh from each side's sources (vertices): (n, 2), inf where a side doesn't
    reach (no sources, or another component)."""
    import igl
    n = len(Vn)
    comp = _components(Fn, n)
    d = []
    for s in src:
        if not len(s):
            d.append(np.full(n, np.inf))
            continue
        dist = np.asarray(igl.exact_geodesic(Vn, Fn, s, np.zeros(0, np.int64), np.arange(n, dtype=np.int64),
                                             np.zeros(0, np.int64))).reshape(-1)
        dist[~np.isin(comp, comp[s])] = np.inf
        d.append(dist)
    return np.stack(d, 1)


def _finer(V, F, parent, faces, src):
    """Faces cut into four by their edges' midpoints, their neighbours cut to match (a neighbour sharing two or three
    cut edges is cut into four too; one sharing one, into two through its midpoint), so the mesh stays whole; each
    new face keeps its face's parent, and the midpoint of an edge between two of one side's sources is a source too
    (the line's own edges). (V, F, parent, src)."""
    V, F, parent = list(map(np.asarray, V)), [list(f) for f in F], list(parent)
    red = set(int(f) for f in faces)
    by_edge = {}
    for g, (x, y, z) in enumerate(F):
        for u, v in ((x, y), (y, z), (z, x)):
            by_edge.setdefault((min(u, v), max(u, v)), []).append(g)
    cut = set()
    while True:  # an edge of a red face is cut; a face with two cut edges goes red, until nothing changes
        for g in red:
            x, y, z = F[g]
            cut.update((min(u, v), max(u, v)) for u, v in ((x, y), (y, z), (z, x)))
        more = {g for e in cut for g in by_edge[e] if g not in red
                and sum((min(u, v), max(u, v)) in cut for u, v in ((F[g][0], F[g][1]), (F[g][1], F[g][2]), (F[g][2], F[g][0]))) >= 2}
        if not more:
            break
        red |= more
    sides = [set(s.tolist()) for s in src]
    mid = {}
    for u, v in cut:
        V.append(0.5 * (V[u] + V[v]))
        mid[(u, v)] = len(V) - 1
        for s in sides:
            if u in s and v in s:
                s.add(len(V) - 1)
    out, par = [], []
    for g, (x, y, z) in enumerate(F):
        m = [mid.get((min(u, v), max(u, v))) for u, v in ((x, y), (y, z), (z, x))]
        if g in red:
            kids = [(x, m[0], m[2]), (m[0], y, m[1]), (m[2], m[1], z), (m[0], m[1], m[2])]
        elif any(k is not None for k in m):
            k = next(i for i in range(3) if m[i] is not None)
            a, b, c = [(x, y, z), (y, z, x), (z, x, y)][k]  # the cut edge ab, the corner c across from it
            kids = [(a, m[k], c), (m[k], b, c)]
        else:
            kids = [(x, y, z)]
        out.extend(kids)
        par.extend([parent[g]] * len(kids))
    return np.array(V), np.array(out), np.array(par), [np.array(sorted(s), np.int64) for s in sides]


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


class _Patch:
    """A patch of the fine surface as a mesh of its own, with points put in and maybe cut or cut finer (Vn, Fn; keep: the
    patch's faces on the whole surface; parent: each face's face of the patch), and values per vertex of it read at
    texels of the set's map, or at points on the car, through their faces."""

    def __init__(self, S, keep, parent, Vn, Fn):
        self.S, self.keep, self.parent, self.Vn, self.Fn = S, keep, parent, Vn, Fn
        order = np.argsort(parent, kind="stable")
        starts = np.r_[0, np.flatnonzero(np.diff(parent[order])) + 1]
        self.kids = {int(parent[order[a]]): order[a:b] for a, b in zip(starts, np.r_[starts[1:], len(order)])}

    def _faces(self, face, bary):
        """For points given by their fine face and weights there: each one's face of the mesh (-1 off the patch) and its
        weights at that face's corners. A face kept whole keeps its corners in order; one cut, the piece the point is
        in, by its weights there."""
        g, wt = np.full(len(face), -1, np.int64), np.zeros((len(face), 3))
        j = np.searchsorted(self.keep, face)
        j = np.minimum(j, len(self.keep) - 1)
        on = (face >= 0) & (self.keep[j] == face)
        on[on] = [int(k) in self.kids for k in j[on]]  # a face of the patch taken out (a step's wall) is off it
        if not on.any():
            return g, wt
        rows, j = np.flatnonzero(on), j[on]
        P = (self.S.FV[self.S.FF[face[on]]] * bary[on][..., None]).sum(1)
        single = np.array([len(self.kids[int(k)]) == 1 for k in j])
        g[rows[single]] = [self.kids[int(k)][0] for k in j[single]]
        wt[rows[single]] = bary[on][single]
        for k in np.unique(j[~single]):
            mine = np.flatnonzero(j == k)
            best = bw = bm = None
            for gi in self.kids[int(k)]:
                w = _bary_many(P[mine], *(self.Vn[self.Fn[gi, c]] for c in range(3)))
                m = w.min(1)
                if best is None:
                    best, bw, bm = np.full(len(mine), gi), w, m
                else:
                    better = m > bm
                    best[better], bw[better], bm[better] = gi, w[better], m[better]
            w = np.clip(bw, 0, None)
            g[rows[mine]], wt[rows[mine]] = best, w / np.maximum(w.sum(1, keepdims=True), 1e-12)
        return g, wt

    def faces_at(self, size, lin=None):
        """Each texel's face of the mesh and its weights there (_faces), for texels of the set's map (all by default)."""
        return self._faces(*self.S.texels(size, lin))

    def read(self, value, size=None, lin=None, points=None, faces=None):
        """A value per vertex of the mesh, (n,) or (n, k), read at texels of the set's map (size, lin), at points on
        the car, or at faces and weights found already (faces_at's): nan off the patch, or at a face with a corner
        the value doesn't reach (not finite)."""
        if faces is not None:
            g, wt = faces
        elif points is not None:
            g, wt = self._faces(*self.S._locate(np.asarray(points, np.float64).reshape(-1, 3))[:2])
        else:
            g, wt = self.faces_at(size, lin)
        value = np.asarray(value, np.float64)
        out = np.full((len(g),) + value.shape[1:], np.nan)
        on = np.flatnonzero(g >= 0)
        corners = value[self.Fn[g[on]]]
        w = wt[on].reshape((len(on), 3) + (1,) * (value.ndim - 1))
        ok = np.isfinite(corners).reshape(len(on), -1).all(1)
        out[on[ok]] = (corners * w).sum(1)[ok]
        return out


class Field(_Patch):
    """The distance from each side of a line over a patch of the fine surface, on the mesh the line was cut into: read
    at texels of the set's map as one signed distance. value: (n, 2) per vertex, from the line's left and from its
    right (inf where unreached). Each side is read on its own and the nearer takes the texel: a signed value read
    across a face would fake a zero wherever the two sides meet round an open line's end."""

    def __init__(self, S, keep, parent, Vn, Fn, value, gaps):
        super().__init__(S, keep, parent, Vn, Fn)
        self.value, self.gaps = value, gaps

    def at(self, size, lin=None):
        """The signed distance at texels of the set's map (flat indices; all by default): + to the line's left, - to its
        right; nan off the patch or beyond its reach."""
        g, wt = self.faces_at(size, lin)
        out = np.full((len(g), 2), np.inf)
        on = g >= 0
        out[on] = _read(self.value[self.Fn[g[on]]], wt[on])
        value = np.where(out[:, 0] <= out[:, 1], out[:, 0], -out[:, 1])
        value[np.isinf(out).all(1)] = np.nan
        return value

    def contour(self, level):
        """The line where the signed distance is `level` cm (+ on the line's left, - on its right): a line beside the
        line, which never crosses itself where the line bends, as pieces, each (n, 3) cm along the surface with whether
        it closes, in no order (round an open line's ends the pieces run on, a quarter circle, to where the two sides
        meet). Read on the cut mesh's own faces, on the level's side only (a face reached from both sides, beyond
        an end, would cross the level where the sign jumps); a piece under SPECK cm is left out."""
        return [(pts, closed) for pts, closed, _ in self._contour(level)]

    def too_coarse(self, levels):
        """The faces too big for the lines these levels draw across them: where a contour's vertex sits more than
        HALF_TEXEL off the straight line between its neighbours while the surface there is flat (the two faces
        coplanar), the two faces, unless no edge of either is longer than FINEST."""
        out = set()
        for level in levels:
            for pts, _, faces in self._contour(level):
                if len(pts) < 3:
                    continue
                A, B, C = (self.Vn[self.Fn[faces, k]] for k in range(3))
                n = np.cross(B - A, C - A)
                n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
                flat = (n[1:] * n[:-1]).sum(1) > 0.9998  # under a degree between the chord's face and the next
                big = np.maximum.reduce([np.linalg.norm(B - A, axis=1), np.linalg.norm(C - B, axis=1), np.linalg.norm(A - C, axis=1)]) > FINEST
                p0, p1, p2 = pts[:-2], pts[1:-1], pts[2:]
                chord = p2 - p0
                t = np.clip(((p1 - p0) * chord).sum(1) / np.maximum((chord * chord).sum(1), 1e-12), 0, 1)
                off = np.linalg.norm(p1 - p0 - t[:, None] * chord, axis=1)
                for k in np.flatnonzero((off > HALF_TEXEL) & flat):
                    out.update(int(faces[j]) for j in (k, k + 1) if big[j])
        return out

    def _contour(self, level):
        """contour's pieces, each with the cut face each of its segments crosses: (pts, closed, faces)."""
        Vn, Fn, d = self.Vn, self.Fn, self.value
        v = np.where(d[:, 0] <= d[:, 1], d[:, 0], -d[:, 1])
        v[np.isinf(d).all(1)] = np.nan
        own = np.isfinite(v[Fn]).all(1) & (np.sign(v[Fn]) == np.sign(level)).all(1)
        faces = np.flatnonzero(own)
        F, s = Fn[own], v[Fn[own]] - level
        pos = s > 0
        cross = pos.any(1) & ~pos.all(1)
        F, s, pos, faces = F[cross], s[cross], pos[cross], faces[cross]
        segs, of = [], []  # per crossed face: its two crossings, (the edge crossed, the point), and the face
        for f in range(len(F)):
            got = []
            for k in range(3):
                i, j = int(F[f, k]), int(F[f, (k + 1) % 3])
                if pos[f, k] != pos[f, (k + 1) % 3]:
                    t = s[f, k] / (s[f, k] - s[f, (k + 1) % 3])
                    got.append(((min(i, j), max(i, j)), Vn[i] + t * (Vn[j] - Vn[i])))
            if len(got) == 2:
                segs.append(got)
                of.append(int(faces[f]))
        nbr, where = {}, {}
        for n, (a, b) in enumerate(segs):
            nbr.setdefault(a[0], []).append(n)
            nbr.setdefault(b[0], []).append(n)
            where[a[0]], where[b[0]] = a[1], b[1]
        seen, out = set(), []

        def walk(n, key):  # out of segment n through the edge `key`, on while the way goes on: the edges and segments
            chain, used = [key], []
            while True:
                seen.add(n)
                used.append(n)
                a, b = segs[n]
                key = b[0] if a[0] == key else a[0]
                chain.append(key)
                on = [m for m in nbr[key] if m != n and m not in seen]
                if not on:
                    return chain, used
                n = on[0]

        for n in range(len(segs)):
            if n in seen:
                continue
            a, b = segs[n]
            loose = [e for e in (a[0], b[0]) if len(nbr[e]) == 1]
            if loose:
                chain, used = walk(n, loose[0])
            else:  # started midway: both ways from here, unless the first comes back round
                chain, used = walk(n, a[0])
                if chain[0] != chain[-1]:
                    back, more = walk(n, b[0])
                    chain, used = back[::-1] + chain[2:], more[::-1] + used[1:]
            pts = np.array([where[k] for k in chain])
            if np.linalg.norm(np.diff(pts, axis=0), axis=1).sum() >= SPECK:
                out.append((pts, not loose and chain[0] == chain[-1], np.array([of[m] for m in used])))
        return out


class Chart(_Patch):
    """A flat map of the surface round a point, as a sticker pressed onto the car there (Surface.chart; a course's, laid
    along it, Course.chart in tool/course.py): xy, each vertex's place on the sticker (X along right, Y along up, cm;
    nan where it doesn't reach), r its distance from the centre along the surface, and the centre's frame (centre,
    right, up, facing)."""

    def __init__(self, S, keep, parent, Vn, Fn, xy, r, centre, right, up, facing):
        super().__init__(S, keep, parent, Vn, Fn)
        self.xy, self.r = xy, r
        self.centre, self.right, self.up, self.facing = (np.asarray(v, np.float64) for v in (centre, right, up, facing))
        self._stretch = None

    def at(self, size, lin=None):
        """(X, Y) at texels of the set's map (flat indices; all by default): (m, 2), nan where the chart doesn't reach."""
        return self.read(self.xy, size, lin)

    def stretch(self):
        """Per face of the mesh: how far the sticker is stretched there, the most its lengths grow or shrink as a share
        of themselves (0.05: 5 %; 0 flat); inf where the map folds over itself."""
        if self._stretch is None:
            A, B, C = (self.Vn[self.Fn[:, k]] for k in range(3))
            a, b, c = (self.xy[self.Fn[:, k]] for k in range(3))
            E = np.stack([B - A, C - A], 2)  # a step on the car for each of the face's two edges
            e = np.stack([b - a, c - a], 2)  # the same step on the sticker
            det = e[:, 0, 0] * e[:, 1, 1] - e[:, 0, 1] * e[:, 1, 0]
            ok = np.isfinite(det) & (np.abs(det) > 1e-9)
            inv = np.zeros_like(e)
            inv[ok, 0, 0], inv[ok, 1, 1] = e[ok, 1, 1] / det[ok], e[ok, 0, 0] / det[ok]
            inv[ok, 0, 1], inv[ok, 1, 0] = -e[ok, 0, 1] / det[ok], -e[ok, 1, 0] / det[ok]
            s = np.linalg.svd(E[ok] @ inv[ok], compute_uv=False)  # how a step on the sticker comes out on the car, most and least
            out = np.full(len(self.Fn), np.inf)
            out[ok] = np.maximum(np.maximum(s[:, 0] - 1, 1 - s[:, 1]), 0)
            self._stretch = out
        return self._stretch


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
    a, b = np.array([60.0, 16.5, -60.0]), np.array([60.0, 40.0, -60.0])  # the body's bottom edge, and up the side from it
    t = time.time()
    d = S.distance(a, reach=40)
    took = time.time() - t
    t = time.time()
    path = S.path([a, b])
    walked = time.time() - t
    j = S._locate(b[None])[0][0]
    print(f"From the bottom edge at {tuple(a.round(1).tolist())} to {tuple(b.round(1).tolist())} up the side: "
          f"{d[S.FF[j]].min():.2f} cm along the surface ({took:.2f} s, within 40 cm), the straightest "
          f"line between them {len(path)} points and {np.linalg.norm(np.diff(path, axis=0), axis=1).sum():.2f} cm long "
          f"({walked:.3f} s), {np.linalg.norm(a - b):.2f} cm through the air.")
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
    way = S.carry(c.pts[i], np.cross(c.nrm[i], c.tan[i]), 10.0)
    carried = time.time() - t
    t = time.time()
    beside = field.contour(3.0)
    print(f"Carried on square to it from its middle {tuple(c.pts[i].round(1).tolist())} for 10 cm: {len(way)} points, ending at "
          f"{tuple(way[-1].round(1).tolist())} ({carried:.3f} s). The line 3 cm to its left: {len(beside)} piece(s), "
          f"{sum(np.linalg.norm(np.diff(p, axis=0), axis=1).sum() for p, _ in beside):.1f} cm ({time.time() - t:.3f} s).")


if __name__ == "__main__":
    main()
