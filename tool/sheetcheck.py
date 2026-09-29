"""The body sheet checked on the painted texture, not only on the flattened mesh (the user's
close-up of the sidepod's rear corner, 2026-09-29: the checker sheared and the bands stepped where
two panels met, and the sheet's own figures, percentiles over the whole body, had let it through).

    python -m tool.sheetcheck TSC_Map_Sheet      the checks on that car's painted textures
    python -m tool.sheetcheck TSC_Map_Sheet --falsify   three panels' paint moved 7.6 mm first: the
                                                 crossings check must fail, or it measures nothing

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
WINDOW = 1.5  # cm along the curve either side of a crossing that the band's step and turn are read over
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
    """For each band (name, colour, its sheet polylines in mm, the 3D design curve it follows,
    the curve's kind for the map, its offset and width): every place where the band crosses from
    one panel of the model to another or from one island of the texture to another (its sheet
    polyline walked in 2 mm steps and read on the car: the part and the island under each step),
    then the painted band's texels either side: the step, the difference between the two sides'
    offsets from the design curve (each side's texels' distance to the curve within WINDOW cm of
    the crossing along the curve, their median: a continuous band has the same offset on both
    sides whatever the curve does round a corner), and the turn between lines fitted to each side
    over twice that, less the turn the curve itself makes between them (a band round a corner
    bends; the excess is the kink). Returns rows (name, kind, place (3), step mm, turn deg,
    offset a, offset b, "part a | part b")."""
    from tool import uvmap
    m = sheet.m
    pn = m.part_names[m.part]
    label = uvmap.islands("Skin")[0]
    rows = []
    for name, colour, lines, curve, a_kind, target, width in bands:
        c3 = np.concatenate([curve, curve * [-1, 1, 1]])
        tg = np.concatenate([np.gradient(curve, axis=0), np.gradient(curve * [-1, 1, 1], axis=0)])
        tg /= np.maximum(np.linalg.norm(tg, axis=1, keepdims=True), 1e-9)
        ctree = cKDTree(c3)
        on = _band_texels(painted, colour) & (tri >= 0)  # every painted texel on the car, on the sheet or not
        ys, xs = np.nonzero(on)
        if not len(ys):
            continue
        keep = np.abs(m.mark_distance(pos[ys, xs], a_kind) * 10 - target) <= width / 2 + 12.0  # the band's own texels (a broken band's too, up to 12 mm off)
        ys, xs = ys[keep], xs[keep]
        if not len(ys):
            continue
        P = pos[ys, xs]
        ptree = cKDTree(P)
        tp = pn[tri[ys, xs]]
        li = label[tri[ys, xs]]
        for line in lines:
            l = np.asarray(line, np.float64) / 10
            seg = np.linalg.norm(np.diff(l, axis=0), axis=1)
            sarc = np.r_[0, np.cumsum(seg)]
            u = np.arange(0, sarc[-1], 0.2)
            walk = np.stack([np.interp(u, sarc, l[:, k]) for k in range(2)], 1)
            body = sheet.to_body(walk)
            ok = np.isfinite(body).all(1)
            if ok.sum() < 2:
                continue
            face, _, dist = m.at(body[ok])
            part_w = np.where(dist < 1.0, pn[face], "")
            isl_w = np.where(dist < 1.0, label[face], -1)
            steps = np.flatnonzero(ok)
            for j in range(1, len(steps)):
                pa, pb = part_w[j - 1], part_w[j]
                ia, ib = isl_w[j - 1], isl_w[j]
                if pa == "" or pb == "" or pa in surface.BLADES or pb in surface.BLADES or "nose fin" in (pa, pb):
                    continue  # a strut or a blade under a band is another surface, not a join of the skin
                if pa == pb and ia == ib:
                    continue
                kind = "join" if pa != pb else "UV seam"
                where0 = 0.5 * (body[steps[j - 1]] + body[steps[j]])
                for where in (where0, where0 * [-1, 1, 1]):  # the crossing on the left, and its mirror on the right
                    near = np.array(ptree.query_ball_point(where, 4.0))
                    if len(near) < 12:
                        continue
                    pts = P[near]
                    ga, gb = (tp[near] == pa, tp[near] == pb) if kind == "join" else (li[near] == ia, li[near] == ib)
                    ci = ctree.query(pts)[1]
                    c0 = ctree.query(where)[1]
                    slab = np.abs(ci - c0) * 0.25 <= WINDOW
                    wide = np.abs(ci - c0) * 0.25 <= 2 * WINDOW
                    if (ga & slab).sum() < 4 or (gb & slab).sum() < 4:
                        continue
                    offs = m.mark_distance(pts, a_kind) * 10
                    oa, ob = float(np.median(offs[ga & slab])), float(np.median(offs[gb & slab]))
                    gap = abs(oa - ob)

                    def fit(pp):
                        c = pp.mean(0)
                        vt = np.linalg.svd(pp - c, full_matrices=False)[2]
                        return c, vt[0], vt[-1]  # the centre, the band's direction, the surface's normal there
                    ca, da, na = fit(pts[ga & wide])
                    cb, db, nb = fit(pts[gb & wide])
                    if da @ db < 0:
                        db = -db
                    turn = np.degrees(np.arccos(np.clip(da @ db, -1, 1)))
                    ka, kb = int(np.median(ci[ga & wide])), int(np.median(ci[gb & wide]))
                    own = np.degrees(np.arccos(np.clip(abs(tg[ka] @ tg[kb]), -1, 1)))
                    turn = max(turn - own, 0.0)
                    if np.degrees(np.arccos(np.clip(abs(na @ nb), -1, 1))) > 20.0:
                        # the two panels face apart (a strut under the nose, a mirror's mount): the band lands
                        # on another surface there, not across a join of the skin: no step or kink to judge
                        rows.append((name, kind, where, 0.0, 0.0, oa, ob, f"{pa} | {pb}, facing apart"))
                        continue
                    rows.append((name, kind, where, gap, turn, oa, ob, f"{pa} | {pb}"))
    # one row per crossing: the same place found from both ends of a walk is kept once
    out = []
    for r in rows:
        if not any(r[0] == q[0] and np.linalg.norm(r[2] - q[2]) < 1.0 for q in out):
            out.append(r)
    return out


def bands_of(spec):
    """Bands for crossings() from (name, colour, line kind, offset mm, width mm): the band's sheet polylines
    (the design line's, offset on the sheet, to find where it crosses a join) and the design curve
    itself (3D, for the bend)."""
    from tool import shapes
    out = []
    for name, colour, kind, d, width in spec:
        k = {"shoulder": 0, "lower": 1}[kind]
        curve = np.concatenate([dense for dense, _ in surface.load().m.design_lines(k)])
        lines = [shapes.offset(l, d) if d else l for l in shapes.sheet_lines("design-" + kind)]
        out.append((name, colour, lines, curve, k + 1, d, width))
    return out


# (name, colour, the design line, offset mm, width mm)
SHEET_CAR = (("shoulder line", (0xd0, 0x20, 0x8e), "shoulder", 0, 8), ("30 mm band", (0xe0, 0x20, 0x20), "shoulder", 30, 8),
             ("60 mm band", (0x1f, 0x8f, 0x3a), "shoulder", 60, 8), ("90 mm band", (0x20, 0x50, 0xe0), "shoulder", 90, 8))
PROOF_CAR = (("shoulder pinstripe", (217, 164, 65), "shoulder", 0, 6), ("teal band", (47, 143, 157), "shoulder", 25, 14),
             ("pale band", (232, 226, 208), "shoulder", 48, 6))
FALSIFY_TEXELS = 10  # under --falsify these panels are painted 10 texels (about 9 mm) off along the texture, once per axis
FALSIFY_PARTS = ("rear flank", "nose tip", "sidepod top")  # the panels on one side of the crossings measured


def check(name, spec=None, falsify=False):
    """The three checks on a painted car. spec: the bands as (name, colour, line kind, offset mm);
    None: TSC_Map_Sheet's or TSC_Map_Proof's by the car's name. falsify: the sidepod's top's paint
    moved FALSIFY_TEXELS texels along the texture before measuring, a break the crossings check
    must catch (nothing falsified is ever cached: the check reads the painted file and writes
    nothing)."""
    sheet = surface.load()
    painted = dict(np.load(paths.BUILD / name / "painted.npz"))
    uv, pos, tri = _uv_and_pos(name)
    if falsify:
        m = sheet.m
        top = np.isin(m.part_names[m.part][np.maximum(tri, 0)], FALSIFY_PARTS) & (tri >= 0)
        honest_B = painted["Skin_B"]
        shifts = [np.where(top[..., None], np.roll(honest_B, FALSIFY_TEXELS, axis=ax), honest_B) for ax in (0, 1)]
        print(f"falsify: {', '.join(FALSIFY_PARTS)} painted {FALSIFY_TEXELS} texels off along the texture (about "
              f"{FALSIFY_TEXELS * 0.9:.1f} mm on the car), once along each axis; the crossings check must fail on each")
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
    bands = bands_of(spec or (PROOF_CAR if "Proof" in name else SHEET_CAR))
    rows = crossings(sheet, uv, pos, tri, painted, bands)
    if falsify:
        honest = rows
        broken = [crossings(sheet, uv, pos, tri, {**painted, "Skin_B": B}, bands) for B in shifts]
    worst = sorted(rows, key=lambda r: -(r[3] / GAP + r[4] / TURN))
    bad_rows = [r for r in rows if r[3] > GAP or r[4] > TURN]
    print(f"crossings: {len(rows)} places where a band crosses a join or a UV seam; {len(bad_rows)} with a gap over {GAP} mm or a turn over {TURN} deg (less the curve's own bend)")
    for nm, kind, where, gap, turn, oa, ob, sides in worst[:10]:
        corner = (" (the sidepod's rear corner)" if abs(where[2] + 50) < 8 and abs(where[0]) > 70 else
                  " (the sidepod's front panel edge)" if -20 < where[2] < 40 and abs(where[0]) > 35 and "sidepod top" in sides else "")
        print(f"    {nm:18} at a {kind:7} near ({where[0]:6.1f}, {where[1]:6.1f}, {where[2]:6.1f}): step {gap:.2f} mm "
              f"(offsets {oa:.1f} | {ob:.1f} mm, {sides}), turn {turn:.1f} deg{corner}")
    if bad_rows:
        fails.append("crossings")
    if falsify:
        # each break must show as a step over the limit that the honest paint doesn't have, at a
        # crossing on a panel that was moved
        key = lambda r: (r[0], tuple(np.round(r[2], 0)))
        base = {key(h): h[3] for h in honest}
        out = []
        for ax, rows_b in zip(("v", "u"), broken):
            grew = [abs(r[3] - base.get(key(r), 0.0)) for r in rows_b
                    if any(p in r[7] for p in FALSIFY_PARTS) and r[3] > GAP and abs(r[3] - base.get(key(r), 0.0)) >= 2.0]
            keys_b = {key(r) for r in rows_b}
            gone = [h for h in honest if key(h) not in keys_b and any(p in h[7] for p in FALSIFY_PARTS) and "facing apart" not in h[7]]
            caught = bool(grew) or bool(gone)
            print(f"falsify along {ax}: {'caught' if caught else 'NOT CAUGHT'}: " +
                  (f"{len(grew)} crossings' steps moved by up to {max(grew):.1f} mm from the honest paint's, over the limit" if grew else "no crossing's step moved by 2 mm") +
                  (f"; {len(gone)} crossings' bands no longer meet at the join at all" if gone else ""))
            out.append(caught)
        return [] if all(out) else ["falsify not caught"]
    print("the painted sheet passes" if not fails else f"FAIL: {', '.join(fails)}")
    return fails


if __name__ == "__main__":
    check(sys.argv[1], falsify="--falsify" in sys.argv)
