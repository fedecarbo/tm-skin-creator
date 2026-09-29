"""The car map's lines checked by measurement, not by eye (the user, 2026-09-29: "it just doesn't
feel like it's going to be accurate mapping doing it by hand").

    python -m tool.carmap --check [-v]      the table (with -v, every slice)

The shoulder and the lower edge (tool/carmap.py) are measured on every 1 cm slice, on both sides,
and the worst value per stretch of the body (STRETCHES) is printed with pass or fail:

    ridge     cm from the line to the crest of the bend across the section (the local maximum of
              the curvature along the slice's outline nearest the line, refined by a parabola):
              "sits on the edge the eye sees", in numbers
    contrast  the crest's bend over the surface 3 to 10 cm either side of it: a real edge stands
              out from its surroundings
    shift     cm the crest moves when the normals are smoothed over 1, 2 and 4 cm instead of the
              map's SMOOTH: a real edge stays put, a soft roll wanders
    step      cm between the line's points on neighbouring slices (a step the body doesn't make)
    bend      the line's second difference per slice, cm, beyond what the ridge under it bends
              (an S the ridge itself doesn't make)
    sides     cm between the left line and the right line mirrored
    jumps     slices where the line jumps more than a step allows to another ridge, or has no point
    texture   slices where the line's path in the flat texture jumps further than the texture's
              own scale explains, within one island of the texture
    edge      cm from a mark on the skin's own edge (kind 4) to the mesh's boundary: such a line is
              the boundary itself and follows its notches (the sidepods' bottom edge steps 4 cm near
              z 2), so it is measured as a curve on the boundary, not by steps from slice to slice

A slice whose crest is weak or wanders (contrast under CONTRAST, shift over SHIFT) has no clear
edge: the map draws no line there (carmap stores it as sec_draw), and the table says "no line" for
a stretch that is mostly so, with the reason. The limits (LIMITS) come from the mesh: its triangles'
median edge is about 2 cm and the bend's noise floor is the median bend over the body, so a line
within 0.5 cm of the crest is on it as finely as the mesh can say, a crest 1.5 times its
surroundings is above the noise, and a crest that moves under 2.2 cm (one edge) with the scale is
placed as steadily as the facets allow.
"""

import numpy as np
from scipy.spatial import cKDTree

from tool import carmap, fbx

STRETCHES = ((211, 195, "the nose's tip"), (195, 145, "the nose"), (145, 118, "the fin's plate"),
             (118, 90, "the bonnet"), (90, 35, "the front flank and its lip"),
             (35, -12, "the sidepods' front and inlets"), (-12, -50, "the sidepods"),
             (-50, -122, "the rear flanks and the deck"), (-122, -162, "the tail"))
LIMITS = dict(ridge=0.6, contrast=1.5, shift=2.2, step=1.5, bend=0.25, sides=0.5, jumps=0, texture=0, edge=0.5)
SCALES = (1.0, 2.0, 4.0)
TEXELS = 4096
KINDS = {0: "ridge", 1: "skin's end", 2: "no crease", 3: "ridge, skin ends below", 4: "the skin's own edge", 5: "a roll's crest"}


def _peak(k, i0, reach, g=None):
    """The local maximum of k nearest index i0 within reach points (within the same stretch of
    surface: g, the girth, jumps across a gap), its index refined by a parabola through its
    neighbours: (index as a float, value), or (nan, nan). A crest at the stretch's very end (the
    skirt's edge, its underside hidden) counts."""
    lo, hi = max(i0 - reach, 0), min(i0 + reach, len(k) - 1)
    if g is not None:
        jumps = np.flatnonzero(np.abs(np.diff(g)) > 0.5)
        lo = max([lo] + [j + 1 for j in jumps if j + 1 <= i0])
        hi = min([hi] + [j for j in jumps if j >= i0])
    best = None
    for j in range(lo, hi + 1):
        left = k[j - 1] if j > lo else -np.inf
        right = k[j + 1] if j < hi else -np.inf
        if k[j] >= left and k[j] >= right and (best is None or abs(j - i0) < abs(best - i0)):
            best = j
    if best is None:
        return np.nan, np.nan
    if lo < best < hi:
        a, b, c = k[best - 1], k[best], k[best + 1]
        d = a - 2 * b + c
        t = 0.5 * (a - c) / d if abs(d) > 1e-9 else 0.0
        return best + np.clip(t, -0.5, 0.5), b
    return float(best), k[best]


def _k1_scales(m):
    """The bend per vertex at each of SCALES cm of smoothing."""
    out = {}
    for R in SCALES:
        ns = carmap._smooth_normals(m.V, m.F, m.fn, m.vn, m.area, R)
        out[R] = carmap._principal(carmap._curvature(m.V, m.F, ns), ns)[0].astype(np.float32)
    return out


def measure(m, sec=None, mirror=None):
    """Every slice's measures for both lines, on one side: a dict of arrays (n slices, 2 lines):
    x, y, kind, ridge, contrast, shift, step, bend, sides, jump, texture. sec: the sections to
    measure (the map's own by default); mirror: the other side's sections, mirrored, for sides."""
    sec = sec or m.sec
    if f"k1_{SCALES[0]}" not in m.layers:
        for R, v in _k1_scales(m).items():
            m.layers[f"k1_{R}"] = v
    Z, st, q, g = sec["Z"], sec["starts"], sec["q"], sec["g"]
    n = len(Z)
    out = {k: np.full((n, 2), np.nan) for k in ("x", "y", "ridge", "contrast", "shift", "step", "bend", "sides")}
    out["kind"] = sec["kind"].astype(int)
    out["edge"] = np.full((n, 2), np.nan)  # a mark on the skin's own edge (kind 4): cm from the mesh's boundary
    edge_tree = cKDTree(m.lines["opening"])
    out["jump"] = np.zeros((n, 2), bool)
    out["texture"] = np.zeros((n, 2), bool)
    # the bend along every outline point, at the map's scale and the check's
    zs = np.repeat(Z, np.diff(st))
    p3 = np.c_[q.astype(np.float64), zs]
    k1 = m.value("k1", p3)
    scales = {R: m.value(f"k1_{R}", p3) for R in SCALES}
    floor = float(np.median(m.layers["k1"]))  # the bend's noise floor over the body
    uv = fbx.meshes()["Skin_01"]["tri_uv"]
    ridge_tree = cKDTree(np.concatenate(m.ridges))
    ridge_bend = np.concatenate([np.r_[0, np.linalg.norm(r[2:] - 2 * r[1:-1] + r[:-2], axis=1), 0] if len(r) > 2
                                 else np.zeros(len(r)) for r in m.ridges])
    ridge_tan = np.concatenate([np.gradient(r, axis=0) if len(r) > 1 else np.zeros((1, 3)) for r in m.ridges])
    ridge_tan /= np.maximum(np.linalg.norm(ridge_tan, axis=1, keepdims=True), 1e-9)
    ridge_end = np.concatenate([np.minimum(np.arange(len(r)), np.arange(len(r))[::-1]) * carmap.RIDGE_STEP for r in m.ridges])
    ridge_id = np.concatenate([np.full(len(r), i) for i, r in enumerate(m.ridges)])
    out["across"] = np.zeros((n, 2), bool)  # the ridge runs across the slices there: no step or crest to measure
    out["ends"] = np.zeros((n, 2), bool)    # the ridge under the line ends within 8 cm (its fade-out): the line may leave it
    out["crossed"] = np.zeros((n, 2), bool)  # another ridge within 8 cm, or the ridge turns a corner: no single crest across the slice
    for j, name in enumerate(("sh", "lo")):
        # the evidence, slice by slice (the marks as read, before the curves are fitted to them)
        x, y = (sec["raw"][:, 2 * j], sec["raw"][:, 2 * j + 1]) if "raw" in sec else (sec[name + "_x"], sec[name + "_y"])
        out["x"][:, j], out["y"][:, j] = x, y
        for k in range(n):
            a, b = st[k], st[k + 1]
            if b <= a:
                out["jump"][k, j] = True
                continue
            qq, gg, kk = q[a:b], g[a:b], k1[a:b]
            d = np.hypot(qq[:, 0] - x[k], qq[:, 1] - y[k])
            i = int(d.argmin())
            # the mark's own place along the outline, between the samples
            tng = qq[min(i + 1, len(qq) - 1)] - qq[max(i - 1, 0)]
            mark_g = gg[i] + float((np.array([x[k], y[k]]) - qq[i]) @ tng) / max(float(tng @ tng), 1e-9) * float(np.linalg.norm(tng)) * 0.5
            pk, val = _peak(kk, i, 16, gg)
            if np.isfinite(pk):
                out["ridge"][k, j] = abs(np.interp(pk, np.arange(len(gg)), gg) - mark_g)
                # against the flatter side; with one side only (the skirt's edge, its underside
                # hidden; a crest beside a fillet), against the body's own noise floor
                sides_ = [kk[max(0, i - 40):max(0, i - 12)], kk[i + 12:i + 40]]
                meds = [np.median(w) for w in sides_ if len(w) >= 4]
                out["contrast"][k, j] = val / max(min(meds) if len(meds) == 2 else floor, 1e-3)
                shifts = []
                for R in SCALES:
                    pr, _ = _peak(scales[R][a:b], i, 24, gg)
                    if np.isfinite(pr):
                        shifts.append(abs(np.interp(pr, np.arange(len(gg)), gg) - np.interp(pk, np.arange(len(gg)), gg)))
                out["shift"][k, j] = max(shifts) if shifts else np.nan
        # along the car: steps, bends (beyond the ridge's own), sides, texture
        pts = np.c_[x, y, Z]
        on4 = out["kind"][:, j] == 4
        out["edge"][on4, j] = edge_tree.query(pts[on4], workers=-1)[0]
        step = np.hypot(np.diff(x), np.diff(y))
        out["step"][1:, j] = step
        bend = np.hypot(x[2:] - 2 * x[1:-1] + x[:-2], y[2:] - 2 * y[1:-1] + y[:-2])
        _, ri = ridge_tree.query(pts, workers=-1)
        # the ridge's own bend at the nodes round the crossing (a kink two nodes off counts), per
        # slice: a slanted ridge crosses the slices further apart
        own = np.max([ridge_bend[np.clip(ri[1:-1] + o, 0, len(ridge_bend) - 1)] for o in range(-2, 3)], axis=0)
        own = own / np.maximum(ridge_tan[ri[1:-1], 2] ** 2, 0.25)
        out["bend"][1:-1, j] = np.maximum(bend - own, 0)
        across = np.abs(ridge_tan[ri, 2]) < 0.7  # more than 45 degrees to the car's length
        out["across"][:, j] = across
        out["ends"][:, j] = ridge_end[ri] <= 8.0
        near = ridge_tree.query_ball_point(pts, 8.0, workers=-1)
        out["crossed"][:, j] = [any(ridge_id[c] != ridge_id[ri[k]] for c in cand) for k, cand in enumerate(near)]
        # or the ridge itself turns a corner within 5 cm (over 30 degrees between its tangents)
        lo_, hi_ = np.maximum(ri - 8, 0), np.minimum(ri + 8, len(ridge_tan) - 1)
        turn = np.degrees(np.arccos(np.clip((ridge_tan[lo_] * ridge_tan[hi_]).sum(1), -1, 1)))
        out["crossed"][:, j] |= (turn > 30.0) & (ridge_id[lo_] == ridge_id[hi_])
        for key in ("ridge", "contrast", "shift"):
            out[key][across | out["crossed"][:, j] | out["ends"][:, j], j] = np.nan
        # a step along the car allowed: the line's slope across the slices (its tangent's rise per cm of z)
        allow = np.maximum(LIMITS["step"], 1.5 * np.sqrt(np.maximum(1 - ridge_tan[ri, 2] ** 2, 0)) / np.maximum(np.abs(ridge_tan[ri, 2]), 0.3))
        out["step"][1:, j] = np.where(step <= allow[1:], np.minimum(step, LIMITS["step"]), step)
        out["jump"][1:, j] |= (step > allow[1:]) & ~out["ends"][:-1, j] & ~out["ends"][1:, j]
        if mirror is not None:
            mx, my = (mirror["raw"][:, 2 * j], mirror["raw"][:, 2 * j + 1]) if "raw" in mirror else (mirror[name + "_x"], mirror[name + "_y"])
            out["sides"][:, j] = np.hypot(x - mx, y - my)
        face, bary, _ = m.at(pts)
        t = (bary[:, :, None] * uv[face]).sum(1) * TEXELS
        A, B, C = (m.V[m.F[face, i]] for i in range(3))
        area3 = 0.5 * np.linalg.norm(np.cross(B - A, C - A), axis=1)
        u = uv[face] * TEXELS
        area2 = 0.5 * np.abs((u[:, 1, 0] - u[:, 0, 0]) * (u[:, 2, 1] - u[:, 0, 1]) - (u[:, 1, 1] - u[:, 0, 1]) * (u[:, 2, 0] - u[:, 0, 0]))
        scale = np.sqrt(area2 / np.maximum(area3, 1e-6))  # texels per cm
        dt = np.linalg.norm(np.diff(t, axis=0), axis=1)
        expect = 0.5 * (scale[1:] + scale[:-1]) * np.linalg.norm(np.diff(pts, axis=0), axis=1)
        same = np.array([len(set(m.F[face[k]]) & set(m.F[face[k + 1]])) >= 1 for k in range(n - 1)])
        out["texture"][1:, j] = same & (dt > 3 * expect + 4)
    return out


def draw_mask(meas):
    """Per slice and line: whether the map draws the line there: it sits on a ridge (kind 0 or 3)
    that stands out and stays put (or runs across the slices, where that can't be measured)."""
    on = np.isin(meas["kind"], (0, 3, 5))
    clear = (meas["contrast"] >= LIMITS["contrast"]) & (meas["shift"] <= LIMITS["shift"])
    return (on & (clear | meas["across"] | meas["crossed"] | meas["ends"])) | (meas["kind"] == 4)


def mirrored_sections(m):
    """The right side's sections, mirrored onto the left."""
    flip = np.array([-1.0, 1.0, 1.0])
    return carmap._sections(m.V * flip, m.F, m.part, m.part_names, m.layers["open"], carmap._resample(m.ridges) * flip,
                            m.lines["opening"] * flip, lambda p: m.value("k1", p * flip))


CURVE_LIMITS = dict(fit95=6.0, fitmax=10.0, dropped=33.0, bends=4.0, ragged=2.0, texture=4.0)  # mm, mm, %, per metre, mm, mm
# fit95: a quarter of the mesh's median edge (2.2 cm), as the ridge limit above; a traced crest jitters by that much
# dropped: up to a third of the evidence may belong to another edge (the arch's rim against the tail corner's)
# bends: how often a curve changes the sense of its bend, per metre, where it bends tighter than 50 cm (a design
# line has very few); any curve may have two (an S and its return)
# texture: the flat map bends a straight line at every triangle's edge (the map is affine per triangle), about
# 2 mm over 4 cm on this mesh (the floor printed under the table); a line is ragged there beyond twice that


def _ragged(pts, window=17):
    """How far a dense polyline (every 0.25 cm) strays from its own course smoothed over the
    window (17 samples: 4 cm): a line the eye reads as one stroke strays under 2 mm. Returns the
    deviations (cm)."""
    if len(pts) < window:
        return np.zeros(len(pts))
    kern = np.ones(window) / window
    sm = np.stack([np.convolve(pts[:, k], kern, mode="same") for k in range(pts.shape[1])], 1)
    h = window // 2
    return np.linalg.norm(pts[h:-h] - sm[h:-h], axis=1)


def _texture_ragged(m, pts, uv):
    """The same, on the curve's path in the flat texture, in cm on the car (texels over the local
    texel scale), each island of the texture on its own and 3 cm clear of its seams (a seam is a
    jump the texture makes, and the map is stretched beside it)."""
    pts = np.asarray(pts, np.float64)
    face, bary, _ = m.at(pts)
    t = (bary[:, :, None] * uv[face]).sum(1) * TEXELS
    A, B, C = (m.V[m.F[face, i]] for i in range(3))
    area3 = 0.5 * np.linalg.norm(np.cross(B - A, C - A), axis=1)
    u = uv[face] * TEXELS
    area2 = 0.5 * np.abs((u[:, 1, 0] - u[:, 0, 0]) * (u[:, 2, 1] - u[:, 0, 1]) - (u[:, 1, 1] - u[:, 0, 1]) * (u[:, 2, 0] - u[:, 0, 0]))
    scale = np.sqrt(area2 / np.maximum(area3, 1e-6))  # texels per cm
    jump = np.r_[False, np.linalg.norm(np.diff(t, axis=0), axis=1) > 3 * 0.25 * scale[1:] + 4]
    out = []
    for seg in np.split(np.arange(len(t)), np.flatnonzero(jump)):
        seg = seg[12:-12] if len(seg) > 24 and 0 < seg[0] and seg[-1] < len(t) - 1 else seg  # 3 cm clear of a seam
        if len(seg) >= 17:
            out.append(_ragged(t[seg]) / np.maximum(scale[seg][8:-8], 1e-6))
    return np.concatenate(out) if out else np.zeros(1)


def _igl_curvature(m):
    """libigl's principal curvature over the body (the greater bend per vertex), its vertices fit for
    it in a tree, and the body's median: a second measure for the curves' contrast."""
    import igl
    pn = m.part_names[m.part]
    F = np.ascontiguousarray(m.F[~np.isin(pn, carmap.WHEEL_COVERS + carmap.BLADES)], np.int64)
    _, _, pv1, pv2, bad = igl.principal_curvature(np.ascontiguousarray(m.V, np.float64), F, 3, True)
    k = np.maximum(np.abs(pv1), np.abs(pv2))
    good = np.ones(len(m.V), bool)
    good[np.array(bad, int)] = False
    sel = np.unique(F)
    sel = sel[good[sel]]
    return k[sel], cKDTree(m.V[sel]), float(np.median(k[sel]))


def curves(m=None):
    """The lines as the eye sees them: every fitted curve (the shoulder, the lower edge, the real
    folds), how far its evidence lies from it (95th percentile and the most, mm), how fair it is
    (its tightest bend as a radius, and how often per metre its bend changes sense: a design line
    has very few), and how ragged it is at the 1 to 2 cm scale on the car and in the flat texture
    (mm from its own course smoothed over 4 cm). The areas' boundaries are these curves and the
    mesh's own edges, nothing else."""
    m = m or carmap.load()
    uv = fbx.meshes()["Skin_01"]["tri_uv"]
    igl_k1, igl_tree, igl_med = _igl_curvature(m)
    rows, fails, floors = [], [], []
    hdr = f"{'line':11} {'z':>14} {'cm':>4} {'knots':>5} {'evid':>5} {'fit95':>6} {'fitmax':>6} {'radius':>6} {'bends/m':>7} {'ragged':>6} {'texture':>7} {'igl':>5}  verdict"
    print(hdr)
    print("-" * len(hdr))
    for c in m.curves:
        p = c["pts"].astype(np.float64)
        name = ("shoulder", "lower", "fold")[c["kind"]]
        length = len(p) * 0.25
        # the bend along the curve, and its sense: the sign of the turn in the plane of the local motion
        d1 = np.gradient(p, 0.25, axis=0)
        d2 = np.gradient(d1, 0.25, axis=0)
        sp = np.linalg.norm(d1, axis=1)
        curv = np.linalg.norm(np.cross(d1, d2), axis=1) / np.maximum(sp ** 3, 1e-9)
        n0 = np.cross(d1[len(p) // 2], d2[len(p) // 2]) if len(p) > 2 else np.array([0, 0, 1.0])
        sense = np.sign(np.cross(d1, d2) @ (n0 / max(np.linalg.norm(n0), 1e-9)))
        sense = sense[np.abs(curv) > 0.02]  # bending gentler than a 50 cm radius has no sense to change
        changes = int((np.diff(sense) != 0).sum())
        bends = changes / max(length / 100.0, 0.05)
        radius = 1.0 / max(np.quantile(curv, 0.98), 1e-6)
        fit95, fitmax = float(np.quantile(c["res"], 0.95)) * 10, float(c["res"].max()) * 10
        dropped = 100.0 * c["dropped"] / max(len(c["res"]) + c["dropped"], 1)
        rag = float(_ragged(p).max()) * 10
        tx = _texture_ragged(m, p, uv)
        tex = float(tx.max()) * 10
        floors.append(float(np.median(tx)) * 10)
        bad = [k for k, v in (("fit95", fit95), ("fitmax", fitmax), ("dropped", dropped), ("ragged", rag), ("texture", tex)) if v > CURVE_LIMITS[k]]
        if changes > max(2, CURVE_LIMITS["bends"] * length / 100.0):
            bad.append("bends")
        note = f" ({c['gap']} slices without evidence)" if c.get("gap") else ""
        note += f" ({c['dropped']} points left out)" if c.get("dropped") else ""
        note += f" (contrast {c['contrast']:.1f})" if c["kind"] == 2 else ""
        verdict = ("FAIL " + " ".join(bad) if bad else "ok") + note
        if bad:
            fails.append((name, verdict))
        igl_c = float(np.median(igl_k1[igl_tree.query(p)[1]]) / igl_med)  # the crest's contrast by libigl's own curvature
        print(f"{name:11} {p[:, 2].max():6.0f} to {p[:, 2].min():4.0f} {length:4.0f} {c['knots']:5d} {len(c['res']):5d} {fit95:6.1f} {fitmax:6.1f} "
              f"{min(radius, 999):6.0f} {bends:7.1f} {rag:6.1f} {tex:7.1f} {igl_c:5.1f}  {verdict}")
    print()
    print("igl: the crest's bend over the body's median by libigl's principal_curvature (2.6.3, a quadric fit over three rings), an "
          "independent measure of the map's own (carmap._curvature): a named line or fold that stands out on both is a real edge; "
          "libigl marks half the welded body's vertices unfit for its fit (loose panels, thin pieces), which are left out")
    print("limits: " + ", ".join(f"{k} {v}" for k, v in CURVE_LIMITS.items()) + " (mm, mm, %, per metre, mm, mm); "
          f"the texture's own floor, the median over the curves: {np.median(floors):.1f} mm")
    print("the areas' boundaries: the top and the sides meet on the shoulder's curves, the sides and the underside on the "
          "lower edge's curves or, where the body has no lower line, on the skin's own end (the mesh's boundary); nothing else")
    print("all curves pass" if not fails else f"{len(fails)} curves fail")
    return fails


# ---- the body sheet (tool/surface.py), all by number ----

SHEET_LIMITS = dict(area=5.0, angle=3.0, stripe=1.0, offset=1.0, symmetry=0.5, seam=1.0, logmap=2.0)
# area %, angle deg (the sheet's own targets, at the 95th percentile over the painted body);
# stripe: a 20 mm stripe drawn on the sheet at any angle measures 20 +- this on the paint (mm, 95th percentile);
# offset: a line drawn 30 mm below the shoulder is 30 +- this from it along the surface, by an exact geodesic
# (potpourri3d's tracer on the piece's mesh), mm at the 95th percentile; symmetry: the right side mirrored
# lies within this of the left (mm, 95th); seam: a dart's two sides agree in length within this (mm);
# logmap: round a decal's spot, the sheet's coordinates agree with the log map (potpourri3d's vector heat
# method, an independent measure over the surface) within this (mm, 95th percentile, 10 cm round)


def sheet(s=None):
    """The body sheet checked: distortion per piece and per area, the stripe round trip, the
    offsets from the shoulder by exact geodesics, the symmetry, the seams, and a decal's spot
    against the log map. Prints the table and returns the failures."""
    import potpourri3d as pp3d
    from tool import surface
    s = s or surface.load()
    m = s.m
    lim = SHEET_LIMITS
    fails = []
    a, ang, st = surface.measures(s.s1, s.s2)
    V3 = s.corners
    area = 0.5 * np.linalg.norm(np.cross(V3[:, 1] - V3[:, 0], V3[:, 2] - V3[:, 0]), axis=1)
    print(f"{'piece / area':28} {'cm²':>6} {'area%':>6} {'angle':>6} {'stretch%':>8}  verdict")
    print("-" * 72)
    from tool import sheetmap
    labels = sheetmap._area_labels(s)
    for k, name in enumerate(s.piece_names):
        for j, aname in ((None, ""), (0, "top"), (1, "sides"), (2, "under")):
            sel = (s.piece == k) & s.painted & ((labels == j) if j is not None else True)
            if area[sel].sum() < 50:
                continue
            pa, pang, pst = (surface.percentile(np.abs(a[sel]), area[sel]), surface.percentile(ang[sel], area[sel]),
                             surface.percentile(st[sel], area[sel]))
            bad = [x for x, v in (("area", pa), ("angle", pang)) if v > lim[x]]
            label = name if j is None else f"  {aname}"
            verdict = "ok" if not bad else "FAIL " + " ".join(bad)
            if bad and j is None:
                fails.append((name, bad))
            print(f"{label:28} {area[sel].sum():6.0f} {pa:6.1f} {pang:6.1f} {pst:8.1f}  {verdict}")
    # the stripe round trip: a 20 mm stripe across each painted triangle at 12 angles, its width on the paint
    P, _ = surface._local(s.Vs, s.Fs)
    X = np.stack([P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]], 2)
    U = np.stack([s.corner_uv[:, 1] - s.corner_uv[:, 0], s.corner_uv[:, 2] - s.corner_uv[:, 0]], 2)
    ok = np.abs(np.linalg.det(X)) > 1e-9
    J = np.zeros((len(s.tri), 2, 2))
    J[ok] = U[ok] @ np.linalg.inv(X[ok])
    worst = np.zeros(len(s.tri))
    for th in np.arange(0, np.pi, np.pi / 12):
        n = np.array([np.cos(th), np.sin(th)])
        g = np.linalg.norm(np.einsum("tji,j->ti", J, n), axis=1)  # |J^T n|: the stripe's sheet width over its paint width
        worst = np.maximum(worst, np.abs(20 / np.maximum(g, 1e-6) - 20))
    sel = s.painted & (area > 0.5)
    stripe95, stripemax = surface.percentile(worst[sel], area[sel]), float(worst[sel].max())
    print()
    print(f"stripe: a 20 mm stripe on the sheet, at 12 angles, is off by {stripe95:.2f} mm on the paint (95 % of the painted body), {stripemax:.1f} mm at most")
    if stripe95 > lim["stripe"]:
        fails.append(("stripe", stripe95))
    # offsets from the shoulder by exact geodesics on the piece's mesh (potpourri3d)
    devs = []
    for k in range(len(s.piece_names)):
        Vp, Fp, uvp, sel_k = s.piece_mesh(k)
        tracer = pp3d.GeodesicTracer(Vp, Fp)
        for line in s.lines["shoulder"]:
            t_line, _ = s.at(line[::4])
            if not (t_line >= 0).any() or np.median(s.piece[np.maximum(t_line, 0)]) != k:
                continue
            for i in range(4, len(line) - 4, 8):
                q = line[i]
                tng = line[i + 4] - line[i - 4]
                tng /= max(np.linalg.norm(tng), 1e-9)
                nrm2 = np.array([-tng[1], tng[0]])  # down the sheet, onto the flank
                t, bary = s.at(q[None])
                if t[0] < 0 or s.piece[t[0]] != k:
                    continue
                f = int(np.flatnonzero(sel_k == t[0])[0])
                Jt = J[t[0]]
                if abs(np.linalg.det(Jt)) < 1e-9:
                    continue
                d2 = np.linalg.solve(Jt, nrm2)  # the sheet direction in the triangle's own flat frame
                A, B, C = Vp[Fp[f]]
                x = (B - A) / np.linalg.norm(B - A)
                nn = np.cross(B - A, C - A)
                nn /= np.linalg.norm(nn)
                d3 = d2[0] * x + d2[1] * np.cross(nn, x)
                d3 = d3 / np.linalg.norm(d3) * 3.0
                path = np.asarray(tracer.trace_geodesic_from_face(f, bary[0], d3))
                if len(path) < 2:
                    continue
                end = s.uv_at(path[-1:] , m.value("ns", path[-1:]))[0]
                if not np.isfinite(end).all():
                    continue
                dist = np.min(np.linalg.norm(line - end, axis=1))
                devs.append(abs(dist * 10 - 30))
    devs = np.array(devs)
    off95, offmax = (np.percentile(devs, 95), devs.max()) if len(devs) else (np.nan, np.nan)
    print(f"offset: 30 mm below the shoulder on the sheet is 30 mm along the surface within {off95:.2f} mm (95 % of {len(devs)} places), {offmax:.1f} mm at most (exact geodesics)")
    if not len(devs) or off95 > lim["offset"]:
        fails.append(("offset", off95))
    # symmetry: the right side mirrored against the left surface
    pn = m.part_names[m.part]
    body = ~np.isin(pn, carmap.WHEEL_COVERS + surface.BLADES)
    cen = m.V[m.F].mean(1)
    right = np.flatnonzero(body & (cen[:, 0] < -0.05))
    rv = np.unique(m.F[right])
    mirrored = m.V[rv] * [-1, 1, 1]
    _, _, dist = m.at(mirrored)
    sym95, symmax = np.percentile(dist, 95) * 10, dist.max() * 10
    unmirrored = right[surface._twins(m)[right] < 0]
    print(f"symmetry: the right side's vertices mirrored lie within {sym95:.2f} mm of the left surface (95 %), {symmax:.1f} mm at most; "
          f"{len(unmirrored)} right triangles have no mirror twin in the model's triangulation ({', '.join(np.unique(pn[unmirrored]))}) and go by their corners' mirror vertices")
    if sym95 > lim["symmetry"]:
        fails.append(("symmetry", sym95))
    # seams: a dart's two sides agree in length with each other and with the body
    worst_seam = 0.0
    for k, pts3 in s.seams:
        sides = s._seam_sides(pts3)
        L3 = np.linalg.norm(np.diff(pts3.astype(np.float64), axis=0), axis=1).sum()
        for side in sides:
            L2 = np.linalg.norm(np.diff(side, axis=0), axis=1).sum()
            worst_seam = max(worst_seam, abs(L2 - L3) * 10)
        gap = np.linalg.norm(sides[0][-1] - sides[1][-1]) * 10 if len(sides) == 2 else 0.0
        print(f"seam on {s.piece_names[k]}: {L3:.1f} cm long, its two sides {len(sides)}, lengths within {worst_seam:.2f} mm of the body, open {gap:.1f} mm at the edge")
    if not s.seams:
        print("seams: none (no piece needed a dart)")
    if worst_seam > lim["seam"]:
        fails.append(("seam", worst_seam))
    # a decal's spot: the sheet against the log map round a point on the left flank
    Vp, Fp, uvp, sel_k = s.piece_mesh(0)
    spot = np.array([35.0, 55.0, 60.0])
    src = int(np.argmin(np.linalg.norm(Vp - spot, axis=1)))
    lm = np.asarray(pp3d.MeshVectorHeatSolver(Vp, Fp).compute_log_map(src))
    near = np.flatnonzero((np.linalg.norm(lm, axis=1) < 10.0) & (np.linalg.norm(Vp - Vp[src], axis=1) < 12.0))  # the log map is sound near its source only
    A2, B2 = lm[near], uvp[near] - uvp[src]
    # the best rotation (and flip) between the two frames, then the residual
    best = None
    for flip in (1.0, -1.0):
        Bf = B2 * [1.0, flip]
        Hm = A2.T @ Bf
        Uu, _, Vt = np.linalg.svd(Hm)
        R = (Uu @ Vt).T
        res = np.linalg.norm(A2 @ R.T - Bf, axis=1) * 10
        if best is None or np.percentile(res, 95) < best[0]:
            best = (np.percentile(res, 95), res.max())
    print(f"log map: round the left flank's spot, {len(near)} vertices within 10 cm, the sheet's coordinates agree with the log map within {best[0]:.2f} mm (95 %), {best[1]:.1f} mm at most")
    if best[0] > lim["logmap"]:
        fails.append(("logmap", best[0]))
    print()
    print("limits: " + ", ".join(f"{k} {v}" for k, v in lim.items()) + " (%, deg, mm, mm, mm, mm, mm)")
    print("the sheet passes" if not fails else f"{len(fails)} sheet checks fail: " + ", ".join(f[0] for f in fails))
    return fails


def check(m=None, verbose=False):
    m = m or carmap.load()
    right = mirrored_sections(m)
    left = measure(m, m.sec, right)
    rght = measure(m, right, m.sec)
    both = draw_mask(left) & draw_mask(rght)  # sides: only where both sides draw the line
    for meas in (left, rght):
        meas["sides"][~both] = np.nan
    Z = m.sec["Z"]
    rows, fails = [], []
    hdr = f"{'line':9} {'side':5} {'stretch':32} {'ridge':>6} {'contr':>6} {'shift':>6} {'step':>6} {'bend':>6} {'sides':>6} {'edge':>5} {'jumps':>5} {'tex':>4}  verdict"
    print(hdr)
    print("-" * len(hdr))
    for j, line in enumerate(("shoulder", "lower")):
        for side, meas in (("left", left), ("right", rght)):
            for z1, z0, what in STRETCHES:
                sel = (Z <= z1) & (Z > z0)
                kind = meas["kind"][sel, j]
                drawn = draw_mask(meas)[:, j] & sel
                on = drawn  # the worst values over the slices where the line is drawn
                w = lambda key, s=on, f=np.nanmax: (float(f(meas[key][s, j])) if s.any() and np.isfinite(meas[key][s, j]).any() else np.nan)
                crest = on & np.isin(meas["kind"][:, j], (0, 3, 5))  # a mesh edge (kind 4) has no crest to judge
                ridge, contrast, shift = w("ridge", crest), w("contrast", crest, np.nanmin), w("shift", crest)
                # a step where the line's kind changes is the car's own (the top's end at the sidepod's front)
                change = np.r_[False, meas["kind"][1:, j] != meas["kind"][:-1, j]] | meas["ends"][:, j]
                change = change | np.r_[change[1:], False] | np.r_[False, change[:-1]]  # and the slices either side
                same_kind = drawn & ~change & ~meas["across"][:, j]  # over the drawn slices
                # a mesh edge (kind 4) is measured against the boundary (edge), not by steps and bends
                not4 = same_kind & (meas["kind"][:, j] != 4)
                step, bend, sides = w("step", not4), w("bend", not4), w("sides", on & ~meas["across"][:, j] & ~meas["crossed"][:, j])
                edge = w("edge", sel & (meas["kind"][:, j] == 4))
                jumps = int((meas["jump"][:, j] & not4).sum())
                ends = int((meas["ends"][:, j] & sel).sum())
                tex = int((meas["texture"][:, j] & same_kind).sum())
                reasons = [f"{n}: {KINDS[int(u)]}" for u, n in zip(*np.unique(kind[kind != 0], return_counts=True))]
                weak = int((~drawn & sel & np.isin(meas["kind"][:, j], (0, 3, 5))).sum())
                if weak:
                    reasons.append(f"{weak}: weak or wandering crest")
                bad = [k for k, v in (("ridge", ridge), ("shift", shift), ("step", step), ("bend", bend), ("sides", sides), ("edge", edge)) if np.isfinite(v) and v > LIMITS[k]]
                if np.isfinite(contrast) and contrast < LIMITS["contrast"]:
                    bad.append("contrast")
                if jumps > LIMITS["jumps"]:
                    bad.append("jumps")
                if tex > LIMITS["texture"]:
                    bad.append("texture")
                if drawn.sum() < sel.sum() / 2:
                    why = ", ".join(reasons) if reasons else "weak or wandering crest"
                    verdict = f"no line ({drawn.sum()}/{sel.sum()} slices drawn: {why})"
                    if bad and drawn.any():
                        verdict += "; FAIL " + " ".join(bad)
                        fails.append((line, side, what, bad))
                elif bad:
                    verdict = "FAIL " + " ".join(bad) + (f" ({', '.join(reasons)})" if reasons else "")
                    fails.append((line, side, what, bad))
                else:
                    verdict = "ok" + (f" ({', '.join(reasons)})" if reasons else "")
                if ends:
                    verdict += f" [{ends} slices at a ridge's end]"
                fmt = lambda v: f"{v:6.2f}" if np.isfinite(v) else "     -"
                print(f"{line:9} {side:5} {what:32} {fmt(ridge)} {fmt(contrast)} {fmt(shift)} {fmt(step)} {fmt(bend)} {fmt(sides)} {fmt(edge)[1:]} {jumps:5d} {tex:4d}  {verdict}")
                if verbose:
                    for k in np.flatnonzero(sel):
                        v = {key: meas[key][k, j] for key in ("x", "y", "ridge", "contrast", "shift", "step", "bend", "sides")}
                        print(f"    z {Z[k]:6.1f} ({v['x']:5.1f},{v['y']:5.1f}) {KINDS[int(meas['kind'][k, j])]:10} "
                              f"ridge {v['ridge']:5.2f} contr {v['contrast']:5.2f} shift {v['shift']:5.2f} step {v['step']:5.2f} "
                              f"bend {v['bend']:5.2f} sides {v['sides']:5.2f}{' JUMP' if meas['jump'][k, j] else ''}{' TEX' if meas['texture'][k, j] else ''}"
                              f"{' across' if meas['across'][k, j] else ''}{' end' if meas['ends'][k, j] else ''}{' crossed' if meas['crossed'][k, j] else ''}")
    print()
    print(f"limits: " + ", ".join(f"{k} {v}" for k, v in LIMITS.items()))
    print("all stretches pass" if not fails else f"{len(fails)} stretches fail")
    return fails


if __name__ == "__main__":
    import sys
    check(verbose="-v" in sys.argv)
