"""The body sheet checked on the painted texture, not only on the flattened mesh (the user's
close-up of the sidepod's rear corner, 2026-09-29: the checker sheared and the bands stepped where
two panels met, and the sheet's own figures, percentiles over the whole body, had let it through).

    python -m tool.sheetcheck TSC_Map_Sheet      the checks on that car's painted textures

Three checks, all by number, on the painted Skin texture (build/<name>/painted.npz) and every
texel's place on the sheet (surface.sheet_cm):

  continuity  every pair of texels next to each other in the texture (so next to each other on
              the car) whose sheet places differ by more than JUMP mm, and every pair of sheet
              triangles sharing an edge on the body whose sheet places differ: each such jump must
              lie on a declared seam (a dart, the cut between the outer skin and the underside at the
              skirt's crest, or an opening). Reports the undeclared ones and where they are.
  scale       per texel, from the sheet places and the body positions of its neighbours in the
              texture: the local stretch and shear of the map as painted (the singular values of
              d(sheet)/d(body)), so a sheared checker shows as a patch of texels over the limits,
              wherever it is, with its location.
  crossings   every band and named line drawn on the car (its sheet polyline) where it crosses a
              join between panels or a UV seam of the texture: the band's painted texels either side
              (found by colour), a line fitted to each side on the body, the sideways gap between the
              two and the turn between their directions. Gap over GAP mm or turn over TURN degrees
              fails, and the worst crossings are listed with their places on the car.
"""

import sys

import numpy as np
from scipy.spatial import cKDTree

from tool import bake, carmap, paths, surface

JUMP = 1.0        # mm: a sheet jump between neighbouring texels beyond this is a seam
SCALE_LIMIT = 10.0  # %: local stretch a texel patch may show (twice the sheet's target)
SHEAR_LIMIT = 6.0   # degrees
PATCH = 25.0      # cm² of texels over the limits that counts as a failure
GAP, TURN = 1.0, 2.0  # mm, degrees: a band across a crossing
SIZE = 4096


def _uv_and_pos(name):
    uv = surface.sheet_cm("Skin", SIZE, SIZE)
    b = bake.bake("Skin", SIZE, SIZE)
    return uv, b["position"], b["tri"]


def continuity(uv, pos, tri, sheet):
    """Sheet jumps between neighbouring texels (right and down neighbours, both on the body) not
    on a declared seam: their count and the worst places."""
    m = sheet.m
    on = np.isfinite(uv[..., 0]) & (tri >= 0)
    seam_pts = [s for _, s in sheet.seams]
    declared = np.concatenate(seam_pts + [m.lines["opening"].astype(np.float64), m.lines["join"].astype(np.float64)])  # a panel's edge on another is a join
    # the cut between the outer skin and the underside: the skirt's and the diffuser's edges
    pn = m.part_names[m.part]
    under = np.isin(pn, surface.UNDER)
    e = surface._edges(m.F)
    tid = np.tile(np.arange(len(m.F)), 3)
    key = e[:, 0].astype(np.int64) * len(m.V) + e[:, 1]
    _, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
    order = np.argsort(inv, kind="stable")
    starts = np.r_[0, np.cumsum(cnt)]
    two = np.flatnonzero(cnt == 2)
    ta, tb = tid[order[starts[two]]], tid[order[starts[two] + 1]]
    cut = two[under[ta] != under[tb]]
    cut_pts = 0.5 * (m.V[e[order[starts[cut]], 0]] + m.V[e[order[starts[cut]], 1]])
    declared = np.concatenate([declared, cut_pts]) if len(cut_pts) else declared
    tree = cKDTree(declared)
    out = []
    for dy, dx in ((0, 1), (1, 0)):
        a = on[:SIZE - dy, :SIZE - dx] & on[dy:, dx:]
        d3 = np.linalg.norm(pos[:SIZE - dy, :SIZE - dx] - pos[dy:, dx:], axis=-1)
        d2 = np.linalg.norm(uv[:SIZE - dy, :SIZE - dx] - uv[dy:, dx:], axis=-1)
        same = a & (d3 < 0.5)  # neighbours on the car too (not across a UV seam of the texture)
        jump = same & (d2 * 10 > JUMP + 15 * d3)  # beyond the texel's own step (with 50 % stretch allowed)
        ys, xs = np.nonzero(jump)
        if len(ys):
            p = pos[ys, xs]
            d, _ = tree.query(p, workers=-1)
            off = d > 1.0
            out.append((p[off], (d2[ys, xs][off] * 10)))
    if not out:
        return 0, np.zeros((0, 3)), np.zeros(0)
    p = np.concatenate([o[0] for o in out])
    j = np.concatenate([o[1] for o in out])
    return len(p), p, j


def scale(uv, pos, tri):
    """Per texel (every 4th), the local stretch (%) and shear (degrees) of the sheet as painted,
    from its right and down neighbours: returns the texels' positions, stretch, shear."""
    on = np.isfinite(uv[..., 0]) & (tri >= 0)
    s = slice(0, SIZE - 4, 4)
    c = on[s, s] & on[s, 4:SIZE:4] & on[4:SIZE:4, s]
    P0, Px, Py = pos[s, s], pos[s, 4:SIZE:4], pos[4:SIZE:4, s]
    U0, Ux, Uy = uv[s, s], uv[s, 4:SIZE:4], uv[4:SIZE:4, s]
    ex, ey = Px - P0, Py - P0
    c &= (np.linalg.norm(ex, axis=-1) < 1.0) & (np.linalg.norm(ey, axis=-1) < 1.0)  # neighbours on the car
    # not across a seam of the sheet or the car's middle (the mirror): a sheet step over three
    # times the body step is a jump, not stretch (continuity() counts those)
    c &= (np.linalg.norm(Ux - U0, axis=-1) < 3 * np.linalg.norm(ex, axis=-1) + 0.1) & (np.linalg.norm(Uy - U0, axis=-1) < 3 * np.linalg.norm(ey, axis=-1) + 0.1)
    c &= (np.sign(Px[..., 0]) == np.sign(P0[..., 0])) & (np.sign(Py[..., 0]) == np.sign(P0[..., 0]))
    ex, ey, du, dv = ex[c], ey[c], Ux[c] - U0[c], Uy[c] - U0[c]
    # the body step in the texel's own plane, then the map from it to the sheet
    x = ex / np.maximum(np.linalg.norm(ex, axis=1, keepdims=True), 1e-9)
    nrm = np.cross(ex, ey)
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
    y = np.cross(nrm, x)
    X = np.stack([np.stack([(ex * x).sum(1), (ey * x).sum(1)], 1), np.stack([(ex * y).sum(1), (ey * y).sum(1)], 1)], 1)
    U = np.stack([du, dv], 2)
    ok = np.abs(np.linalg.det(X)) > 1e-6
    J = np.zeros((len(X), 2, 2))
    J[ok] = U[ok] @ np.linalg.inv(X[ok])
    sv = np.linalg.svd(J, compute_uv=False)
    s1, s2 = sv[:, 0], np.maximum(sv[:, 1], 1e-6)
    stretch = (np.maximum(s1, 1 / s2) - 1) * 100
    shear = 90 - 2 * np.degrees(np.arctan2(s2, s1))
    return P0[c][ok], stretch[ok], shear[ok]


def _band_texels(painted, colour, tol=40):
    rgb = painted["Skin_B"].astype(int)
    return np.abs(rgb - np.asarray(colour)).max(-1) < tol


def crossings(sheet, uv, pos, tri, painted, bands):
    """For each band (a colour and its sheet polylines in mm): where its polyline crosses a
    sewn join between panels or a UV seam, the painted band's texels within 3 cm either side,
    a line fitted to each, the sideways gap and the turn. Returns rows (name, place (3), gap
    mm, turn deg)."""
    m = sheet.m
    pn = m.part_names[m.part]
    rows = []
    # a join: the sheet's sewn edges (an edge whose two triangles come from different parts), a UV
    # seam: an edge whose two triangles are on different islands of the texture
    from tool import uvmap
    label = uvmap.islands("Skin")[0]
    tri_part = np.where(sheet.tri >= 0, pn[np.maximum(sheet.tri, 0)], "gap")
    e = surface._edges(sheet.Fs)
    tid = np.tile(np.arange(len(sheet.Fs)), 3)
    key = e[:, 0].astype(np.int64) * len(sheet.Vs) + e[:, 1]
    _, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
    order = np.argsort(inv, kind="stable")
    starts = np.r_[0, np.cumsum(cnt)]
    two = np.flatnonzero(cnt == 2)
    ta, tb = tid[order[starts[two]]], tid[order[starts[two] + 1]]
    is_join = tri_part[ta] != tri_part[tb]
    is_seam = (sheet.tri[ta] >= 0) & (sheet.tri[tb] >= 0) & (label[np.maximum(sheet.tri[ta], 0)] != label[np.maximum(sheet.tri[tb], 0)])
    idx = np.flatnonzero(is_join | is_seam)  # into two, ta, tb
    sel = two[idx]
    ta, tb = ta[idx], tb[idx]
    kinds = np.where(is_join[idx], "join", "UV seam")
    ea = e[order[starts[sel]]]
    A2, B2 = sheet.uv[ea[:, 0]], sheet.uv[ea[:, 1]]  # the crossing edges on the sheet (cm)
    body = np.isfinite(uv[..., 0]) & (tri >= 0)
    for name, colour, lines in bands:
        on = _band_texels(painted, colour) & body
        ys, xs = np.nonzero(on)
        if not len(ys):
            continue
        P = pos[ys, xs]
        Uv = uv[ys, xs]
        ptree = cKDTree(P)
        for line in lines:
            l = np.asarray(line, np.float64) / 10  # cm
            for i in range(len(l) - 1):
                p, q = l[i], l[i + 1]
                # segment p-q against every crossing edge
                r, s_ = q - p, B2 - A2
                den = r[0] * s_[:, 1] - r[1] * s_[:, 0]
                ok = np.abs(den) > 1e-12
                t = ((A2[:, 0] - p[0]) * s_[:, 1] - (A2[:, 1] - p[1]) * s_[:, 0]) / np.where(ok, den, 1)
                u = ((A2[:, 0] - p[0]) * r[1] - (A2[:, 1] - p[1]) * r[0]) / np.where(ok, den, 1)
                hit = ok & (t >= 0) & (t < 1) & (u >= 0) & (u <= 1)
                for k in np.flatnonzero(hit):
                    x_sheet = p + t[k] * r
                    where0 = sheet.to_body(x_sheet[None])[0]
                    if not np.isfinite(where0).all():
                        continue
                    for where in (where0, where0 * [-1, 1, 1]):  # the crossing on the left, and its mirror on the right
                        near = ptree.query_ball_point(where, 3.0)
                        if len(near) < 12:
                            continue
                        pts = P[near]
                        side_a, side_b = tri_part[ta[k]], tri_part[tb[k]]
                        tp = pn[tri[ys[near], xs[near]]]
                        if kinds[k] == "join":
                            ga, gb = tp == side_a, tp == side_b
                        else:  # a UV seam: the island of each texel
                            li = label[tri[ys[near], xs[near]]]
                            ga, gb = li == label[sheet.tri[ta[k]]], li == label[sheet.tri[tb[k]]]
                        if ga.sum() < 6 or gb.sum() < 6:
                            continue
                        # a line through each side's texels (their principal direction), in 3D
                        def fit(pp):
                            c = pp.mean(0)
                            d = np.linalg.svd(pp - c, full_matrices=False)[2][0]
                            return c, d
                        ca, da = fit(pts[ga])
                        cb, db = fit(pts[gb])
                        if da @ db < 0:
                            db = -db
                        turn = np.degrees(np.arccos(np.clip(da @ db, -1, 1)))
                        # the sideways gap: side b's centre off side a's line, measured across the band on the surface
                        off = cb - ca
                        off -= (off @ da) * da
                        gap = np.linalg.norm(off) * 10
                        rows.append((name, kinds[k], where, gap, turn))
    return rows


def check(name, bands=None):
    """The three checks on a painted car. bands: [(name, colour (r, g, b) 0..255, polylines mm)];
    None: TSC_Map_Sheet's."""
    sheet = surface.load()
    painted = dict(np.load(paths.BUILD / name / "painted.npz"))
    uv, pos, tri = _uv_and_pos(name)
    fails = []
    n, p, j = continuity(uv, pos, tri, sheet)
    print(f"continuity: {n} texel pairs next to each other on the car jump on the sheet off any declared seam" +
          (f"; the worst at ({p[np.argmax(j)][0]:.0f}, {p[np.argmax(j)][1]:.0f}, {p[np.argmax(j)][2]:.0f}) by {j.max():.0f} mm" if n else ""))
    if n:
        fails.append("continuity")
        for q, jj in sorted(zip(p, j), key=lambda x: -x[1])[:6]:
            print(f"    ({q[0]:6.1f}, {q[1]:6.1f}, {q[2]:6.1f}): {jj:.0f} mm")
    P0, stretch, shear = scale(uv, pos, tri)
    bad = (stretch > SCALE_LIMIT) | (shear > SHEAR_LIMIT)
    cm2 = bad.sum() * 16 * (0.09 ** 2)  # every 4th texel each way, a texel about 0.9 mm
    print(f"scale: on the painted texture the map stretches {np.percentile(stretch, 95):.1f} % and shears {np.percentile(shear, 95):.1f} deg (95 % of texels), "
          f"{np.percentile(stretch, 99):.1f} % and {np.percentile(shear, 99):.1f} deg (99 %); over {SCALE_LIMIT} % or {SHEAR_LIMIT} deg: about {cm2:.0f} cm²")
    if bad.any():
        # the worst patches: cluster the bad texels
        bp = P0[bad]
        tree = cKDTree(bp)
        from scipy.sparse import coo_matrix
        from scipy.sparse.csgraph import connected_components
        pairs = tree.query_pairs(2.0, output_type="ndarray")
        lab = connected_components(coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(len(bp), len(bp))), directed=False)[1]
        sizes = np.bincount(lab) * 16 * 0.09 ** 2
        for c in np.argsort(sizes)[::-1][:5]:
            if sizes[c] < 2:
                break
            q = bp[lab == c].mean(0)
            print(f"    a patch of {sizes[c]:.0f} cm² at ({q[0]:.0f}, {q[1]:.0f}, {q[2]:.0f}), stretch up to {stretch[bad][lab == c].max():.0f} %, shear up to {shear[bad][lab == c].max():.0f} deg")
        if sizes.max() >= PATCH:
            fails.append("scale")
    if bands is None:
        from tool import shapes
        sh = shapes.sheet_lines("shoulder")
        bands = [("shoulder line", (0xd0, 0x20, 0x8e), sh)] + [(f"{d} mm band", col, [shapes.offset(l, d) for l in sh])
                                                            for d, col in ((30, (0xe0, 0x20, 0x20)), (60, (0x1f, 0x8f, 0x3a)), (90, (0x20, 0x50, 0xe0)))]
    rows = crossings(sheet, uv, pos, tri, painted, bands)
    worst = sorted(rows, key=lambda r: -(r[3] / GAP + r[4] / TURN))
    bad_rows = [r for r in rows if r[3] > GAP or r[4] > TURN]
    print(f"crossings: {len(rows)} places where a band crosses a join or a UV seam; {len(bad_rows)} with a gap over {GAP} mm or a turn over {TURN} deg")
    for nm, kind, where, gap, turn in worst[:8]:
        print(f"    {nm:14} at a {kind:7} near ({where[0]:6.1f}, {where[1]:6.1f}, {where[2]:6.1f}): gap {gap:.2f} mm, turn {turn:.1f} deg")
    if bad_rows:
        fails.append("crossings")
    print("the painted sheet passes" if not fails else f"FAIL: {', '.join(fails)}")
    return fails


if __name__ == "__main__":
    check(sys.argv[1])
