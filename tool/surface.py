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
                                       fills a panel line's groove to its mouth (meshlines.grooves), spans a step flat
                                       (a wall of skin, a panel of the model no wider than STEP cm, between two skins:
                                       a raised plate's edge; the raised skin is measured as if it sat level with the
                                       other, and the wall takes the sticker's edge) and bridges a gap up to BRIDGE
                                       cm between two skins facing alike, and a slit (a rim loop under HOLE cm round)
                                       however its sides face; every distance bounded by the way along the mesh's
                                       edges (_relaxed: the exact solver walks a hairline's slivers lengthwise). A
                                       Chart: .read(xy, size, lin) reads (X, Y) at texels (nan beyond the reach),
                                       .read(xy, points=) at points on the car, .stretch() how far the sticker is stretched on
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
OWN_RIM = 6      # rim edges: a rim's vertex this near another along the rim is its own rim's, never a bridge's far end
HOLE = 16.0      # cm round: a rim loop no longer than this is a hole or a slit in the skin (the nose plate's, 5 cm long), zipped
# shut across (its own rim's vertices are its far ends, all but its neighbours)
SLIT = 1.0       # cm: two rims this near are a slit's sides (the surface cut along a fold, the sides facing 90 degrees
# apart), bridged however they face, short of opposite
STEP = 1.5       # cm: a panel of the model this narrow between two skins (a raised plate's edge) is a step's wall, which
WALL = 70.0      # a sticker spans flat where the wall faces this many degrees or more from the sticker's centre
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

    def signed(self, line, reach=8.0, closed=False, crease=False, levels=(), holes=0.0, only=None):
        """cm along the surface from a line, with a side: + to its left as it runs, seen from outside, - to its right.
        The line's points go into the fine surface as a chain of its edges (_chain), the surface is cut along them (and,
        with `crease`, along the model's crisp lines: where faces meet at meshlines.SHARP degrees or more, so nothing
        crosses one), and each side's distance is exact (libigl's exact geodesics) from its own copy of the line; a
        point reached from both sides, round an open line's end, takes the nearer. An open line's cut runs one edge on
        past each end (the edge there that carries its way on best), so each side keeps its own copy of the end and the
        two sides meet only beyond it, not square to it. `levels`: the distances that will be drawn as lines (a band's
        edges, a line beside the line): where their contours bend across faces too big for them (HALF_TEXEL), those
        faces are cut finer and the distance solved again, ROUNDS times at most. `holes`: the patch's holes shorter than
        this round (a fastener's) zipped shut first (_zipped), so the distance runs straight past one. `only`: which of
        the line's points (a mask), whose stretches' own distance on its left is solved too (Field.only). A Field, read
        at texels."""
        import igl
        faces, w, on, gaps = self._chain(line, closed)
        V, F, keep, verts = self._patch(on, reach)
        V2, F2, _, parent, ids = _insert(V, F, np.searchsorted(keep, faces), w, on, chain=True)
        if holes:
            V2, F2, parent = _zipped(V2, F2, parent, holes, set(np.asarray(ids).tolist()))
        n2 = len(F2)
        # every edge of the patch: its faces and the corner it starts from in each
        slot = {}
        for g in range(n2):
            x, y, z = F2[g]
            for k, (u, v) in enumerate(((x, y), (y, z), (z, x))):
                slot.setdefault((min(u, v), max(u, v)), []).append((g, k, u))
        cuts = np.zeros((n2, 3), bool)
        left, right, mine = set(), set(), set()
        if only is not None:  # each of the chain's vertices by the line's point nearest it
            near_only = np.asarray(only, bool)[cKDTree(np.asarray(line, np.float64).reshape(-1, 3)).query(V2[ids])[1]]
        for i, (a, b) in enumerate(zip(ids[:-1], ids[1:])):
            if a == b:
                continue
            here = slot.get((min(a, b), max(a, b)), [])
            if not here:
                gaps += 1
                continue
            ours = only is not None and near_only[i] and near_only[i + 1]
            for g, k, u in here:
                cuts[g, k] = True
                (left if u == a else right).add((g, k))  # the face running a to b is on the left of a to b
                if ours and u == a:
                    mine.add((g, k))
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
        sides = (left, right, mine) if only is not None else (left, right)
        src = [np.unique([Fn[g, (k + j) % 3] for g, k in side for j in (0, 1)]).astype(np.int64) for side in sides]
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
        could, the direction through the air serves). Without the crease cut the patch's grooves are filled (_filled), its
        steps spanned (_spanned) and its gaps bridged (_bridged), and each source's way is read off the sources' distances
        from one another (_ways): the tracer's way bends where it crosses a groove the chart fills. A face reaching past
        `reach` is read whole."""
        import igl
        p = self._locate(np.asarray(centre, np.float64)[None])[2][0]
        right, up = (np.asarray(v, np.float64) for v in (right, up))
        pts = [p] + [self.carry(p, d, EPS)[-1] for d in (right, -right, up, -up)]
        f, w, on = self._locate(np.asarray(pts))
        V, F, keep, _ = self._patch(on, reach)
        V2, F2, ids, parent, _ = _insert(V, F, np.searchsorted(keep, f), w, on)
        walls, wall_parent = np.zeros((0, 3), np.int64), np.zeros(0, np.int64)
        if crease:
            Vn, Fn, back = igl.cut_mesh(V2, F2.astype(np.int64), self._sharp(F2, parent, keep))
            copies = [np.flatnonzero(np.asarray(back).reshape(-1) == i) for i in ids]
        else:
            from tool import meshlines
            fn, tri = self.fine_facing()[keep], self.model[keep // 16]
            V2, fn = _filled(V2, F2.astype(np.int64), parent, fn, meshlines.grooves(self.tset)[tri])
            Vn, Fn, parent, (walls, wall_parent) = _spanned(V2, F2.astype(np.int64), parent, fn, np.cross(right, up), int(ids[0]),
                                                             meshlines.widths(self.tset)[tri] <= STEP)
            Vn, Fn, parent = _bridged(Vn, Fn, parent, fn)
            copies = [np.array([i]) for i in ids]
        n = len(Vn)
        comp = _components(Fn, n)
        D = []
        for src in copies:
            d = np.asarray(igl.exact_geodesic(Vn, Fn, src.astype(np.int64), np.zeros(0, np.int64), np.arange(n, dtype=np.int64),
                                              np.zeros(0, np.int64))).reshape(-1)
            d[~np.isin(comp, comp[src])] = np.inf
            d[(d <= 0) & ~np.isin(np.arange(n), src)] = np.inf  # where the solve didn't go it reads 0: unreached
            D.append(_relaxed(d, Vn, Fn))
        r = D[0]
        reached = r <= reach
        reached[Fn[reached[Fn].any(1)]] = True  # a face reaching past the reach is read whole: its far corners are
        reached &= np.isfinite(r)  # within its longest edge more, inside the patch, so exact too
        eps = np.array([float(r[c].min()) if len(c) else np.inf for c in copies[1:]])
        went = np.flatnonzero((0.1 * EPS <= eps) & (eps <= 1.5 * EPS))  # it didn't go, or the surface is cut between
        # each source's way on the sticker: as sent, or pressed over every edge, as the chart has it (the tracer's way
        # bends over a groove the chart fills); then each point's place from its distances to the sources
        way = np.array([[1.0, 0.0], [-1.0, 0.0], [0.0, 1.0], [0.0, -1.0]])
        if not crease and len(went) >= 3:
            way[went] = _ways(eps[went], np.array([[D[a + 1][copies[b + 1]].min() for b in went] for a in went]), way[went])
        M, v = np.zeros((n, 2, 2)), np.zeros((n, 2))
        for k in went:
            ok = reached & np.isfinite(D[k + 1])
            M[ok] += np.outer(way[k], way[k])
            v[ok] += ((r[ok] ** 2 + eps[k] ** 2 - D[k + 1][ok] ** 2) / (2 * eps[k]))[:, None] * way[k]
        rel = Vn - p
        xy = np.c_[rel @ right, rel @ up]  # told by no source: the direction through the air serves
        for k in range(2):
            told = M[:, k, k] > 0
            xy[told, k] = v[told, k] / M[told, k, k]
        det = M[:, 0, 0] * M[:, 1, 1] - M[:, 0, 1] ** 2
        both = (M[:, 0, 1] != 0) & (det > 1e-6)
        xy[both] = np.c_[M[both, 1, 1] * v[both, 0] - M[both, 0, 1] * v[both, 1],
                         M[both, 0, 0] * v[both, 1] - M[both, 0, 1] * v[both, 0]] / det[both, None]
        rho = np.hypot(xy[:, 0], xy[:, 1])
        xy *= np.where(rho > 1e-9, r / np.maximum(rho, 1e-9), 1.0)[:, None]  # the direction theirs, the distance exact
        xy[~reached] = np.nan
        facing = np.cross(right, up)
        # the walls spanned come after the solved faces: their texels read the rims they're collapsed onto
        return Chart(self, keep, np.r_[parent, wall_parent], Vn, np.vstack([Fn, walls]), xy, np.where(reached, r, np.inf), p, right, up,
                     facing / np.linalg.norm(facing), len(Fn))

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


def _ways(eps, between, sent):
    """The ways a chart's sources lie from its centre on the sticker, as unit vectors: their places on a flat sheet from
    their distances from the centre (eps) and from one another (between), by classical scaling, turned (or mirrored) to
    sit best on the ways they were sent; the ways as sent when the places don't span the sheet."""
    d = np.r_[np.c_[0.0, eps[None]], np.c_[eps[:, None], (between + between.T) / 2]]
    k = len(d)
    J = np.eye(k) - 1.0 / k
    lam, U = np.linalg.eigh(-0.5 * J @ (d * d) @ J)
    if lam[-2] <= 1e-6 or not np.isfinite(d).all():
        return sent
    X = U[:, -2:] * np.sqrt(lam[-2:])
    X = X[1:] - X[0]
    A, _, Bt = np.linalg.svd(X.T @ (sent * eps[:, None]))
    X = X @ (A @ Bt)
    return X / np.maximum(np.linalg.norm(X, axis=1, keepdims=True), 1e-12)


def _filled(V, F, parent, fn, groove):
    """A patch's mesh with its panel lines' grooves filled to their mouths, as a sticker pressed over one spans it
    (groove: each face of the patch, whether it lies in one, meshlines.grooves): each point inside a groove lifted
    along the skin's facing at the nearest point of the groove's lips (its edges shared with the skin outside) to the
    lip's level there, so the way across is the mouth's width (0.3 cm), never down one wall and up the other, and no
    wall of it reads as a step. A face that would come out thinner than THIN keeps its points. (V, fn): each face's
    facing as filled."""
    g = groove[parent]
    inside, skin = np.zeros(len(V), bool), np.zeros(len(V), bool)
    inside[F[g]], skin[F[~g]] = True, True
    move, lips = np.flatnonzero(inside & ~skin), np.flatnonzero(inside & skin)
    if not len(move) or not len(lips):
        return V, fn
    nrm = np.zeros_like(V)  # the skin's facing at each lip point
    np.add.at(nrm, F[~g].reshape(-1), np.repeat(fn[parent[~g]], 3, axis=0))
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)
    by_lip = {}  # each lip point's lip edges
    for f in F[g]:
        for u, v in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])):
            if skin[u] and skin[v]:
                by_lip.setdefault(u, set()).add((min(u, v), max(u, v)))
                by_lip.setdefault(v, set()).add((min(u, v), max(u, v)))
    V2 = V.copy()
    for i, a in zip(move, lips[cKDTree(V[lips]).query(V[move])[1]]):
        q, n = V[a], nrm[a]  # the lips' nearest point: on an edge of the nearest lip point's, its facing between its ends'
        for u, v in by_lip.get(a, ()):
            uv = V[v] - V[u]
            s = float(np.clip((V[i] - V[u]) @ uv / max(uv @ uv, 1e-18), 0, 1))
            if np.linalg.norm(V[u] + s * uv - V[i]) < np.linalg.norm(q - V[i]):
                q, n = V[u] + s * uv, (1 - s) * nrm[u] + s * nrm[v]
        n = n / max(np.linalg.norm(n), 1e-12)
        V2[i] = V[i] + ((q - V[i]) @ n) * n

    def thin(W):
        A, B, C = (W[F[g, k]] for k in range(3))
        longest = np.max([np.linalg.norm(B - A, axis=1), np.linalg.norm(C - B, axis=1), np.linalg.norm(A - C, axis=1)], 0)
        return np.linalg.norm(np.cross(B - A, C - A), axis=1) < THIN * longest

    back = np.intersect1d(F[g][thin(V2)], move)
    V2[back] = V[back]
    if (thin(V2) & ~thin(V)).any():
        return V, fn
    A, B, C = (V2[F[g, k]] for k in range(3))
    face = np.cross(B - A, C - A)
    face /= np.maximum(np.linalg.norm(face, axis=1, keepdims=True), 1e-12)
    fn = fn.copy()
    fn[parent[g]] = face * np.where((face * fn[parent[g]]).sum(1) < 0, -1.0, 1.0)[:, None]
    return V2, fn


def _spanned(V, F, parent, fn, facing, centre, narrow):
    """A patch's mesh with its steps spanned, as a sticker pressed over every edge spans them flat rather than running
    down and up: a wall (the faces of a panel no wider than STEP cm, `narrow` (meshlines.widths), facing WALL degrees or
    more from the sticker's facing; skin curving away over a rolled edge is none) between the centre's skin and
    another is taken out, the other skin moved onto the centre's by the step (the mean offset between the wall's two
    rims along the sticker's facing) and the rims welded, each point of the raised rim onto the other rim's own edge
    (put in as a vertex of it); a wall between two skins neither the centre's is left as it is. Faces that collapse
    go. (V, F, parent, walls): the walls spanned, collapsed onto the welded rims (a point inside a wall onto the
    nearest rim point's place), for their texels to take the sticker's edge (never solved on: faces of no area)."""
    n = len(V)
    none = (np.zeros((0, 3), np.int64), np.zeros(0, np.int64))
    wall = np.flatnonzero(narrow[parent] & (fn[parent] @ facing < np.cos(np.radians(WALL))))
    if not len(wall):
        return V, F, parent, none
    strips = _components(F[wall], n)[F[wall]].min(1)  # the walls joined edge to edge, by their lowest vertex's label
    rest = np.setdiff1d(np.arange(len(F)), wall)
    comp, edged = _components(F[rest], n), np.zeros(n, bool)
    edged[F[rest]] = True  # a wall's rims: its points on skin
    # a step parts two skins: a strip whose rims stay one skin without it (a groove's wall) is no step, and stays
    steps = [k for k in np.unique(strips) if len(np.unique(comp[[v for v in np.unique(F[wall[strips == k]]) if edged[v]]])) >= 2]
    gone = wall[np.isin(strips, steps)]
    if not len(gone):
        return V, F, parent, none
    rest = np.setdiff1d(np.arange(len(F)), gone)
    comp, edged = _components(F[rest], n), np.zeros(n, bool)
    edged[F[rest]] = True
    rim = np.unique(F[gone])
    inner, rim = rim[~edged[rim]], rim[edged[rim]]
    home = comp[centre]
    low = rim[comp[rim] == home]
    V = V.copy()
    F2, par2 = F[rest], parent[rest]
    by_edge = {}
    for g, (x, y, z) in enumerate(F2):
        for u, v in ((x, y), (y, z), (z, x)):
            by_edge.setdefault((min(u, v), max(u, v)), g)
    lows = set(low.tolist())
    segs = np.array(sorted({(min(a, b), max(a, b)) for f in F[gone] for a, b in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0]))
                            if a in lows and b in lows and a != b}), np.int64).reshape(-1, 2)  # the lower rim's own edges
    joins = []  # (the top vertex, the lower face, its weights there, the point): the top rim onto the lower rim's edges
    for k in np.unique(comp[rim]):
        if k == home:
            continue
        top = rim[comp[rim] == k]
        if not len(low) or not len(top) or not len(segs):
            continue
        d, j = cKDTree(V[low]).query(V[top], distance_upper_bound=2 * STEP)
        ok = np.isfinite(d)
        if ok.sum() < 2:
            continue
        step = float(((V[low[j[ok]]] - V[top[ok]]) @ facing).mean())  # the step's height along the sticker's facing: the
        V[comp == k] += step * facing  # raised skin moved level with the other and never sideways (a level hairline's
        # far skin moved sideways by its width would jog every graphic across it by that much)
        A, B = V[segs[:, 0]], V[segs[:, 1]]
        AB = B - A
        for t in top:
            s = np.clip(((V[t] - A) * AB).sum(1) / np.maximum((AB * AB).sum(1), 1e-18), 0, 1)
            Q = A + s[:, None] * AB
            i = int(np.argmin(np.linalg.norm(Q - V[t], axis=1)))
            if np.linalg.norm(Q[i] - V[t]) > STEP / 2:
                continue
            g = by_edge.get((int(segs[i, 0]), int(segs[i, 1])))
            if g is None:
                continue
            w = np.zeros(3)
            w[list(F2[g]).index(segs[i, 0])], w[list(F2[g]).index(segs[i, 1])] = 1 - s[i], s[i]
            joins.append((int(t), g, w, Q[i]))
    V3, F3, par3, weld = V, F2, par2, np.arange(len(V))
    if joins:
        V3, F3, ids, par3, _ = _insert(V, F2, np.array([g for _, g, _, _ in joins]), np.array([w for _, _, w, _ in joins]),
                                       np.array([q for _, _, _, q in joins]))
        weld = np.arange(len(V3))
        for (t, _, _, _), i in zip(joins, ids):
            weld[t] = i
        F3 = weld[F3]
        keep = (F3[:, 0] != F3[:, 1]) & (F3[:, 1] != F3[:, 2]) & (F3[:, 2] != F3[:, 0])
        keep &= ~np.array([_thin(*V3[f]) for f in F3])
        F3, par3 = F3[keep], par2[par3][keep]
    if len(inner) and len(rim):
        weld[inner] = weld[rim[cKDTree(V[rim]).query(V[inner])[1]]]
    return V3, F3, par3, (weld[F[gone]], parent[gone])


def _bridged(V, F, parent, fn):
    """A patch's mesh with its gaps bridged, as a sticker pressed over every edge bridges them: where two skins facing
    alike (within 60 degrees) end within BRIDGE cm of each other (a raised plate's step, the hairline between two
    pieces), or a slit's two sides lie within SLIT cm facing any way but opposite (the nose plate's front edge: a
    row of sliver holes along the fold, 15 cm of them), the edges along their ends are joined by triangles, so a
    distance runs straight across instead of round. Each end's vertex takes the nearest vertex of another end (never
    one within OWN_RIM edges along its own rim, else a rim would take its own next vertex but one; a rim loop no longer
    than HOLE is a hole, zipped shut: there only the neighbours are its own; left open, every geodesic across goes
    round its ends and the sticker folds), and two vertices in a row along an end make two triangles with their two.
    The bridges' faces have no face of the patch (parent -1)."""
    edge = {}
    for g, (x, y, z) in enumerate(F):
        for u, v in ((x, y), (y, z), (z, x)):
            edge.setdefault((min(u, v), max(u, v)), []).append(g)
    rim = [(u, v, gs[0]) for (u, v), gs in edge.items() if len(gs) == 1]
    if len(rim) < 2:
        return V, F, parent
    verts = np.unique([u for u, v, _ in rim] + [v for u, v, _ in rim])
    facing, along = {}, {}
    for u, v, g in rim:
        for k, o in ((u, v), (v, u)):
            facing.setdefault(k, []).append(fn[parent[g]])
            along.setdefault(k, set()).add(o)
    nrm = np.array([np.mean(facing[k], 0) for k in verts])
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)
    loop, size = {}, {}  # each rim vertex's rim loop (the rim edges joined end to end), and each loop's length in cm
    for u, v, _ in rim:
        for k in (u, v):
            if k in loop:
                continue
            loop[k] = len(size)
            front = {k}
            while front:
                front = {o for x in front for o in along[x] if o not in loop}
                for o in front:
                    loop[o] = loop[k]
            size[loop[k]] = 0.0
        size[loop[u]] += float(np.linalg.norm(V[u] - V[v]))
    own = {}  # each rim vertex's own rim within OWN_RIM edges along it (on a hole, its neighbours only)
    for k in verts:
        seen, front = {int(k)}, {int(k)}
        for _ in range(1 if size[loop[int(k)]] <= HOLE else OWN_RIM):
            front = {o for u in front for o in along[u]} - seen
            seen |= front
        own[int(k)] = seen
    tree = cKDTree(V[verts])
    match = {}
    for i, k in enumerate(verts):
        for d, j in zip(*tree.query(V[k], k=min(8, len(verts)), distance_upper_bound=BRIDGE)):
            if not np.isfinite(d) or j == i or d < 1e-9:
                continue
            m = int(verts[j])
            alike = nrm[i] @ nrm[j]
            if m in own[int(k)] or alike < (-0.2 if d <= SLIT else 0.5):
                continue
            match[int(k)] = m
            break
    if not match:
        return V, F, parent
    F, parent = list(map(tuple, F)), list(parent)
    count = {e: len(gs) for e, gs in edge.items()}  # faces per edge: a bridge never gives an edge a third, nor makes a thin face
    for u, v, g in rim:
        if u not in match or v not in match:
            continue
        a, b = match[u], match[v]
        if min(a, b) < min(u, v):
            continue  # the other end builds this bridge
        tris = ((u, v, b),) if a == b else ((u, v, b), (u, b, a))
        if F[g][(F[g].index(u) + 1) % 3] == v:  # wound as the rim's face is, each edge one way on each side (the exact
            tris = tuple(t[::-1] for t in tris)  # solver reads nothing past a bridge wound against its skin: 0 cm)
        for tri in tris:
            if len(set(tri)) < 3 or _thin(*(V[k] for k in tri)):
                continue
            es = [(min(tri[k], tri[(k + 1) % 3]), max(tri[k], tri[(k + 1) % 3])) for k in range(3)]
            if any(count.get(e, 0) >= 2 for e in es):
                continue
            for e in es:
                count[e] = count.get(e, 0) + 1
            F.append(tri)
            parent.append(-1)
    F, parent = np.array(F, np.int64), np.array(parent)
    while (parent < 0).any():  # a bridge leaving a point where two fans of faces meet goes: no exact solve goes past one
        drop = (parent < 0) & np.isin(F, np.flatnonzero(_fans(F) > 1)).any(1)
        if not drop.any():
            break
        F, parent = F[~drop], parent[~drop]
    return V, F, parent


def _zipped(V, F, parent, holes, line):
    """A patch's mesh with its holes shorter than `holes` cm round (a rim loop: a fastener's hole) zipped shut by a fan
    from their middle, wound as their rim's faces are; a loop through the `line`'s vertices, or one whose fan would
    have a face thinner than THIN (the exact solver never returns on one), is left open. The fans' faces have no face
    of the patch (parent -1)."""
    edge = {}
    for tri in F:
        for k in range(3):
            u, v = int(tri[k]), int(tri[(k + 1) % 3])
            edge.setdefault((min(u, v), max(u, v)), []).append((u, v))
    after = {}  # a rim edge's end from its start, the way its face runs
    for uses in edge.values():
        if len(uses) == 1:
            after[uses[0][0]] = uses[0][1]
    V, F, parent, seen = np.asarray(V, np.float64), [tuple(f) for f in F], list(parent), set()
    extra = []
    for u0 in list(after):
        if u0 in seen:
            continue
        loop, u = [u0], after[u0]
        seen.add(u0)
        while u != u0 and u in after and u not in seen:
            loop.append(u)
            seen.add(u)
            u = after[u]
        if u != u0 or len(loop) < 3 or line & set(loop):
            continue
        P = V[loop]
        if np.linalg.norm(P - np.roll(P, -1, 0), axis=1).sum() >= holes:
            continue
        c = P.mean(0)
        if any(_thin(V[b], V[a], c) for a, b in zip(loop, loop[1:] + loop[:1])):
            continue
        k = len(V) + len(extra)
        extra.append(c)
        for a, b in zip(loop, loop[1:] + loop[:1]):
            F.append((b, a, k))
            parent.append(-1)
    if not extra:
        return V, np.asarray(F, np.int64), np.asarray(parent)
    return np.vstack([V, extra]), np.asarray(F, np.int64), np.asarray(parent)


def _fans(F):
    """How many fans of faces meet at each point of a mesh whose edges have one or two faces: the faces round it joined
    by the edges through it (two or more: a bowtie, which libigl's exact solver doesn't go past, reading 0 beyond)."""
    m, top = len(F), int(F.max()) + 1
    corner = np.arange(3 * m).reshape(m, 3)
    u, v = F.reshape(-1), np.roll(F, -1, 1).reshape(-1)
    cu, cv = corner.reshape(-1), np.roll(corner, -1, 1).reshape(-1)
    key = np.minimum(u, v) * top + np.maximum(u, v)
    order = np.argsort(key, kind="stable")
    pair = np.flatnonzero(key[order][1:] == key[order][:-1])
    a, b = order[pair], order[pair + 1]  # an edge's two faces: their corners at each end joined
    straight = u[a] == u[b]
    i = np.r_[cu[a], cv[a]]
    j = np.r_[np.where(straight, cu[b], cv[b]), np.where(straight, cv[b], cu[b])]
    lab = connected_components(coo_matrix((np.ones(len(i)), (i, j)), shape=(3 * m, 3 * m)), directed=False)[1]
    return np.bincount(np.unique(np.c_[F.reshape(-1), lab], axis=0)[:, 0], minlength=top)


def _relaxed(d, V, F):
    """Distances from a source, no longer than the way along the mesh's edges from a nearer vertex (a few rounds of
    relaxing over every edge): the exact solver walks a hairline's slivers lengthwise (a distance across one grows by
    its length, and a vertex 8 cm away reads 14), and a way along the edges, on the surface itself, is never shorter
    than the true one, so the shorter of the two is the nearer the truth."""
    E = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    L = np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1)
    for _ in range(2 * ROUNDS):
        before = d.copy()
        np.minimum.at(d, E[:, 1], d[E[:, 0]] + L)
        np.minimum.at(d, E[:, 0], d[E[:, 1]] + L)
        if np.array_equal(before, d):
            break
    return d


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
        self.value, self.gaps = value[:, :2], gaps
        self.only = value[:, 2] if value.shape[1] > 2 else None  # from the stretches `only` named, on the left

    def at_only(self, size, lin=None):
        """The distance on the line's left from the stretches `only` named (signed), at texels: inf where unreached."""
        g, wt = self.faces_at(size, lin)
        out = np.full(len(g), np.inf)
        on = g >= 0
        out[on] = _read(self.only[self.Fn[g[on]]][..., None], wt[on])[:, 0]
        return out

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

    def __init__(self, S, keep, parent, Vn, Fn, xy, r, centre, right, up, facing, solved=None):
        super().__init__(S, keep, parent, Vn, Fn)
        self.xy, self.r = xy, r
        self.centre, self.right, self.up, self.facing = (np.asarray(v, np.float64) for v in (centre, right, up, facing))
        self.solved = len(Fn) if solved is None else solved  # the faces from here on are steps' walls, collapsed
        self._stretch = None

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
            out[self.solved:] = 0.0  # a step's wall takes the sticker's edge: no stretch to speak of
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
    path = S.path([a, b])
    walked = time.time() - t
    print(f"From the bottom edge at {tuple(a.round(1).tolist())} to {tuple(b.round(1).tolist())} up the side: the "
          f"straightest line between them {len(path)} points and {np.linalg.norm(np.diff(path, axis=0), axis=1).sum():.2f} "
          f"cm long ({walked:.3f} s), {np.linalg.norm(a - b):.2f} cm through the air.")
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
