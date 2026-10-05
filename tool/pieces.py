"""The model's pieces: every separate panel of the body, with the gaps and overlaps between them.

    python -m tool.pieces          the table (and car/pieces.json)

`labels` gives each triangle's piece, for the checks (tool/checks.py: a graphic on two pieces).

A piece is a run of the welded body's triangles joined across shared edges (carmap._weld, the
wheel covers left out). For each: its parts, area, boundary length, the nearest other piece and
the gap to it (the smallest distance between its boundary vertices and the other's boundary
edges), how much of its boundary lies within 1 cm of another piece (sewn-tight), and the skin it
covers: the area of other pieces' triangles that face the same way within 1 cm behind it (hidden
skin, which the viewer never shows but a 3D zone paints). Also the mesh's non-manifold edges. The
user (2026-09-29): "the lines are such a mess (hidden, wobbly, not even connect)": how much is the
model, in numbers.
"""

import json

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

from tool import carmap, paths


def labels():
    """The piece each of the welded body's triangles is in (Skin_01's order, the wheel covers too)."""
    m = carmap.load()
    F, n = m.F, len(m.V)
    e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    e.sort(1)
    _, inv, cnt = np.unique(e[:, 0].astype(np.int64) * n + e[:, 1], return_inverse=True, return_counts=True)
    tid = np.tile(np.arange(len(F)), 3)
    order = np.argsort(inv, kind="stable")
    two = np.flatnonzero(cnt == 2)
    starts = np.r_[0, np.cumsum(cnt)][two]
    A = coo_matrix((np.ones(len(two)), (tid[order[starts]], tid[order[starts + 1]])), shape=(len(F), len(F)))
    return connected_components(A, directed=False)[1]


def survey():
    m = carmap.load()
    V, F, pn = m.V, m.F, m.part_names[m.part]
    keep = ~np.isin(pn, carmap.WHEEL_COVERS)
    F = F[keep]
    pn = pn[keep]
    fn = m.fn[keep]
    n = len(V)
    e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    e.sort(1)
    key = e[:, 0].astype(np.int64) * n + e[:, 1]
    u, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
    tid = np.tile(np.arange(len(F)), 3)
    order = np.argsort(inv, kind="stable")
    starts = np.r_[0, np.cumsum(cnt)]
    two = np.flatnonzero(cnt == 2)
    A = coo_matrix((np.ones(len(two)), (tid[order[starts[two]]], tid[order[starts[two] + 1]])), shape=(len(F), len(F)))
    lab = connected_components(A, directed=False)[1]
    nonmanifold = int((cnt > 2).sum())
    area = 0.5 * np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1)
    bnd = e[np.flatnonzero(cnt[inv] == 1)]
    b_lab = lab[tid[np.flatnonzero(cnt[inv] == 1)]]
    cen = V[F].mean(1)
    tree_cen = cKDTree(cen)
    pieces = []
    for k in np.unique(lab):
        sel = lab == k
        a = float(area[sel].sum())
        if a < 5:
            continue
        names, counts = np.unique(pn[sel], return_counts=True)
        mine = bnd[b_lab == k]
        blen = float(np.linalg.norm(V[mine[:, 0]] - V[mine[:, 1]], axis=1).sum()) if len(mine) else 0.0
        others = bnd[b_lab != k]
        bv = np.unique(mine)
        gap, near_share, other = np.nan, 0.0, ""
        if len(bv) and len(others):
            mid = 0.5 * (V[others[:, 0]] + V[others[:, 1]])
            d, i = cKDTree(mid).query(V[bv])
            gap = float(d.min())
            near_share = float((d < 1.0).mean())
            o = b_lab[b_lab != k][i[d.argmin()]]
            on, oc = np.unique(pn[lab == o], return_counts=True)
            other = str(on[np.argmax(oc)])
        # skin hidden behind this piece: other pieces' triangles whose centroid lies within 1 cm
        # behind one of this piece's triangles, facing the same way
        c = cen[sel]
        d, i = tree_cen.query(c, k=4)
        covered = 0.0
        for j in range(1, 4):
            t = i[:, j]
            behind = (lab[t] != k) & (d[:, j] < 1.0) & ((fn[t] * fn[sel]).sum(1) > 0.7)
            covered += float(area[t][behind].sum())
        pieces.append(dict(piece=int(k), parts=[str(x) for x in names[np.argsort(-counts)]], cm2=round(a), boundary_cm=round(blen),
                           gap_cm=None if np.isnan(gap) else round(gap, 2), boundary_within_1cm=round(near_share, 2),
                           nearest=other, hidden_skin_behind_cm2=round(covered), z=[round(float(cen[sel, 2].min())), round(float(cen[sel, 2].max()))]))
    pieces.sort(key=lambda p: -p["cm2"])
    return pieces, nonmanifold


def write():
    pieces, nonmanifold = survey()
    doc = dict(about="The body's separate pieces (tool/pieces.py): parts, area, boundary length, the gap to the nearest other piece "
                     "(cm), how much of the boundary lies within 1 cm of another piece, and the skin of other pieces hidden "
                     "within 1 cm behind it.", non_manifold_edges=nonmanifold, pieces=pieces)
    (paths.REPO / "car" / "pieces.json").write_text(json.dumps(doc, indent=1))
    return pieces, nonmanifold


if __name__ == "__main__":
    pieces, nm = write()
    print(f"{len(pieces)} pieces of 5 cm² or more; {nm} edges shared by three or more triangles")
    print(f"{'parts':40} {'cm²':>6} {'edge cm':>7} {'gap cm':>6} {'<1cm':>5} {'hidden cm²':>10}  nearest")
    for p in pieces[:40]:
        print(f"{', '.join(p['parts'])[:40]:40} {p['cm2']:6d} {p['boundary_cm']:7d} {p['gap_cm'] if p['gap_cm'] is not None else '-':>6} "
              f"{p['boundary_within_1cm']:5.2f} {p['hidden_skin_behind_cm2']:10d}  {p['nearest']}")
