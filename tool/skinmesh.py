"""The skin: the car's paintable surface as one mesh, the whole car, to draw on.

Why this exists (2026-09-30, the user: "Current approaches are not working"). Four ways of
drawing have been tried and each one defines the line somewhere that isn't the car: values at the
mesh's corners (a 2 cm mesh facets every edge: crayon), the flat sheet (shears 5.6 to 8.0 % on
the sidepod's side and the rear flank), a spline through pins in the air (leaves the body by up
to 22 cm), and a view's projection (stops dead where the body turns past 53 degrees or the view
is blind, and no path can cross two views). A line on a car is none of those things: it is a
curve on the surface. So this module hands the surface over, and tool/skindraw.py draws on it.

    python -m tool.skinmesh --build     build the cache and print what it is
    python -m tool.skinmesh --spots     the named places, with the face each lands on

What it is, and why it's built this way:

* The sewn body from tool/surface.py, every piece (surface.Sheet.piece_mesh), so the panels the
  sheet welded and bridged are one surface here too. That work is already measured and trusted.
* Mirrored to the WHOLE car. The sheet holds the car's left half only and mirrors the right onto
  it, which forbids an asymmetric design and makes a band round the car impossible. Here the two
  halves are their own geometry, welded along the centre line, so a curve can run up one flank,
  over the roof and down the other.
* Pinched vertices split (surface._split_fans), because geometry-central refuses a mesh where one
  vertex sits in two boundary loops, and the mirror makes those at the centre line.
* Every face remembers the piece and the car triangle it came from, so a curve can say which
  parts of the car it crosses, and a texel can find its face through the same fan table the
  sheet uses (surface.Sheet.uv_in).

The mesh is coarse: the body shell's triangles are about 35 mm across (p95 115 mm). That is the
model's own resolution, not a choice here. A geodesic on it is exact in the mesh's own geometry;
the paint is measured per texel, never interpolated from corners, which is what keeps the crayon
out.
"""

import argparse
import functools

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

from tool import carmap, paths, surface

CACHE = paths.CACHE / "skinmesh.npz"
VERSION = 2
WELD = 0.05      # cm: two corners this near each other are the same corner (the centre line, and panels that touch)
# The model's body is coarse: its triangles are 35 mm across (127 mm at the 95th). A curve runs
# corner to corner, so a place asked for lands up to half a triangle away -- measured, 29 to 48 mm
# typically, which is more than the width of most of the lines drawn on it. Splitting every
# triangle into four, twice, puts the corners about 9 mm apart without moving the surface at all
# (every new corner sits on an edge of the old one), so a place lands where it was asked.
SUBDIVIDE = 2
CENTRE = 0.02    # cm: a corner this near x = 0 is pinned to it before mirroring, so the two halves meet exactly
REACH = 0.3      # cm: a point found by nearness must land this close to count as on the skin
# Blades: thin things standing off the body, which are surface too, so a curve would climb them.
# The nose's "fin" is NOT one of them, measured: 84 of its 94 triangles face up, and it spans x 0
# to 8 cm -- it is the raised centre panel of the bonnet, with a small upstand along it. Leaving it
# off punched an 84 mm hole in the bonnet's middle, so it stays. Its upstand is why a place on the
# centre line needs to say which way the surface faces there (skindraw.place).
OFF = ("diffuser strake", "mirror mount", "wing pylon", "wheel cover")


def _edges(F):
    """Every edge as a sorted pair, with how many triangles use it."""
    e = np.sort(np.stack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]], 1).reshape(-1, 2), axis=1)
    return np.unique(e, axis=0, return_counts=True)


def _components(V, F):
    u, _ = _edges(F)
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
        u, c = _edges(F)
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
    import collections
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


def build(log=print):
    """Build the cache. Returns the dict that goes in it."""
    s = surface.load()
    m = carmap.load()
    # Each piece becomes its own whole-car surface: mirrored and welded along the centre line, but
    # never welded to another piece. The sheet already sewed what could be sewn (surface.build);
    # fusing its pieces here only twisted the surface -- the tail met the body wound the other way,
    # and 23 edges then had no consistent side, which geometry-central refuses.
    Vs, Fs, piece, src, side = [], [], [], [], []
    off = 0
    for k in range(len(s.piece_names)):
        V, F, _, sel = s.piece_mesh(k)
        csrc = s.tri[sel].astype(np.int32)
        blade = np.isin(m.part_names[m.part[csrc]], OFF)
        if blade.any():
            F, csrc = F[~blade], csrc[~blade]
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
        want = m.fn[psrc] * np.where(pside[:, None] > 0, [-1.0, 1.0, 1.0], [1.0, 1.0, 1.0])
        F = _orient(V, F, want, log=lambda msg, name=s.piece_names[k]: log(f"  {name}: {msg}"))
        F, n, origin = surface._split_fans(F, len(V))
        V = V[origin]
        for _ in range(SUBDIVIDE):
            V, F, psrc, pside = _split4(V, F, psrc, pside)
        log(f"  {str(s.piece_names[k]):18} {len(V):5d} corners {len(F):5d} triangles"
            + (f", {dropped} dropped (a doubled shell)" if dropped else "")
            + (f", {n - len(origin) + (n - len(V)) * 0} pinches split" if n > len(origin) else ""))
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
    # texels mapped, all of them on the left, and every band drawn on the right read as "no paint".
    # Each right face takes its own triangle, the twin (surface._twins, corners within 2 mm).
    twin = surface._twins(m)                        # right triangle -> its left twin
    cen = m.V[m.F].mean(1)
    right_of = np.full(len(m.F), -1, np.int64)
    rt = np.flatnonzero((twin >= 0) & (cen[:, 0] < -0.05))
    right_of[twin[rt]] = rt
    mapped = (side > 0) & (right_of[src] >= 0)
    src = np.where(mapped, right_of[src], src)
    lost = int(((side > 0) & ~mapped).sum())
    log(f"the right half: {int(mapped.sum())} faces take their own car triangle"
        + (f", {lost} have no mirror twin in the model (round the number panel) and are found by nearness" if lost else ""))

    u, c = _edges(F)
    ncomp, lab = _components(V, F)
    area = 0.5 * np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1)
    elen = np.linalg.norm(V[u[:, 1]] - V[u[:, 0]], axis=1)
    log(f"the skin: {len(V)} corners, {len(F)} triangles, {area.sum():.0f} cm2, {ncomp} piece(s) of surface, "
        f"{int((c == 1).sum())} edges on a boundary, {int((c > 2).sum())} edges with more than two faces")
    log(f"triangles {np.median(elen) * 10:.1f} mm across (median edge), {np.percentile(elen, 95) * 10:.0f} mm at the 95th; "
        f"x {V[:, 0].min():.1f} to {V[:, 0].max():.1f} cm, so both sides are here")
    assert int((c > 2).sum()) == 0, "the skin must be a surface: no edge with more than two faces"

    data = {"V": V.astype(np.float64), "F": F.astype(np.int32), "piece": piece.astype(np.int32),
            "src": src.astype(np.int32), "side": side.astype(np.int8), "comp": lab[F[:, 0]].astype(np.int32),
            "piece_names": np.array([str(x) for x in s.piece_names]), "version": np.int32(VERSION)}
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
        self._solvers = {}

    # ---- the car underneath ----

    @property
    def m(self):
        """The car map, for part names and the model's own lines."""
        if self._m is None:
            self._m = carmap.load()
        return self._m

    @functools.cached_property
    def part(self):
        """The part name of every face."""
        return self.m.part_names[self.m.part[self.src]]

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
    def area(self):
        return 0.5 * np.linalg.norm(np.cross(self.V[self.F[:, 1]] - self.V[self.F[:, 0]],
                                             self.V[self.F[:, 2]] - self.V[self.F[:, 0]]), axis=1)

    # ---- the geometry libraries (potpourri3d / geometry-central) ----

    def solver(self, kind):
        """A potpourri3d solver on this mesh, built once: "trace", "flip", "heat" or "signed"."""
        if kind not in self._solvers:
            import potpourri3d as pp3d
            make = {"trace": pp3d.GeodesicTracer, "flip": pp3d.EdgeFlipGeodesicSolver,
                    "heat": pp3d.MeshHeatMethodDistanceSolver, "signed": pp3d.MeshSignedHeatSolver,
                    "vector": pp3d.MeshVectorHeatSolver}[kind]
            self._solvers[kind] = make(self.V, self.F)
        return self._solvers[kind]

    # ---- from a place on the car to a face here ----

    def _fans(self):
        """The car triangle -> the faces here that came from it, per side, as a padded table."""
        if self._fan is None:
            key = self.src.astype(np.int64) * 2 + (self.side > 0)
            order = np.argsort(key, kind="stable")
            u, first, cnt = np.unique(key[order], return_index=True, return_counts=True)
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
        from scipy.spatial import cKDTree
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
