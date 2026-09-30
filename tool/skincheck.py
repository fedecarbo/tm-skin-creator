"""A car's skin-drawn bands checked by number, on the car, over the surface.

    python -m tool.skincheck <name>              the table; a FAIL is yours to fix
    python -m tool.skincheck <name> --falsify    every curve moved 5 mm: every check must fail

What it measures, and why each one. The paint is read from the texture the car actually ships
(build/<name>/painted.npz), never from the zone that drew it, and the measuring is done by walking
the surface with an exact geodesic tracer (potpourri3d / geometry-central) -- a different piece of
machinery from the one that painted, so the two can disagree.

  width        Every 20 mm along the curve, a geodesic is shot across it both ways and the paint
               measured where it starts and stops. This is the width ON THE CAR, not in a picture
               or on a flattening, so a band that looks right in a render but narrows over a fold
               fails here.
  centre       The middle of that measured band against the curve itself.
  unbroken     The painted texels must form ONE piece over the surface. Not "no gap longer than
               n mm" -- one piece, or the check names what cut it (a real gap in the model, an
               opening, a wheel arch), because the user's complaint was never gap size, it was
               "The lines don't follow continuously".
  smooth       How much the painted band's own middle turns within the surface, per 100 mm. The
               crayon measure: the old checks never made it, and crayon is what the user saw.

--falsify moves every curve 5 mm along the surface and requires every check to fail. A check that
cannot fail measures nothing (CHECKLIST.md, the car map's rounds).
"""

import argparse
import json
import sys

import numpy as np

from tool import paths, skinmesh

STEP = 2.0        # cm along the curve between measurements
# The limits come from the texture, not from taste. Measured with --floor: taking the same
# measurement off the zone that painted instead of off the texture gives 0.00 mm at the 95th on
# every band, so the band's geometry costs nothing and the whole of the spread is the texture's
# grain. The body's texels are 0.9 mm across (0.47 to 1.6 over the islands, tool/paint.py), and an
# edge read off a grid can be out by half a texel on each side, so a width can be out by up to
# 1.6 mm and a middle by half that before anything is wrong with the drawing. (The floor shares
# the check's own walks with the band, so it says what the texture costs, not that the walks are
# right; the walks are checked by --falsify.)
WIDTH = 2.5       # mm: how far the measured width may be from the width asked for (95th percentile)
CENTRE = 1.5      # mm: how far the measured middle may be from the curve (95th percentile)
TURN = 12.0       # degrees per 100 mm: how much the painted band's middle may turn beyond the curve's own
TONE = 70.0       # how near a texel's colour must be to the paint's, out of 255
STRAY = 1.0       # cm2 of paint allowed outside the band's own piece (a speck is a fault of its own)
SHIFT = 0.5       # cm: how far --falsify moves a curve


def _texel_of(pos, nrm, w, h):
    """The texel (column, row) each point on the body falls in, through the car's own UVs."""
    from tool import carmap, fbx
    m = carmap.load()
    t, b, d = m.at(np.asarray(pos, np.float64), None if nrm is None else np.asarray(nrm, np.float64))
    uv = (b[:, :, None] * fbx.meshes()["Skin_01"]["tri_uv"][t]).sum(1)
    col = np.clip((uv[:, 0] % 1.0) * w, 0, w - 1).astype(np.int64)
    row = np.clip(((1.0 - uv[:, 1]) % 1.0) * h, 0, h - 1).astype(np.int64)
    return col, row, d


def _edge(rgb, dist, colour, base):
    """How far the paint reaches along a walk, in cm.

    Each sample is scored 1 where it is the paint's colour and 0 where it is whatever lies beyond;
    the band's edge is feathered over shapes.SOFT (2 mm, about two texels) on purpose, so that
    score is a ramp, not a step. The reach is the AREA under that ramp, which is where the edge
    sits however noisy the ramp is -- reading off the first sample below a half instead lets one
    stray texel, picked up by the nearest-triangle lookup, call the edge early. Returns None if the
    walk never gets clear of the paint, which means the car ended before the band did."""
    c = np.asarray(colour, np.float64) * 255.0
    b = np.asarray(base, np.float64)
    span = c - b
    n2 = float(span @ span)
    if n2 < 1.0:                       # the paint and what is beyond are the same colour: unmeasurable
        return None
    alpha = np.clip(((rgb.astype(np.float64) - b) @ span) / n2, 0.0, 1.0)
    if alpha[0] < 0.5 or alpha[-1] > 0.5:
        return None                    # it does not start on the paint, or never leaves it
    return float(np.trapezoid(alpha, dist))


def _is(rgb, colour, others):
    """Is this the paint? Within TONE of it, and nearer it than any other colour drawn."""
    c = np.asarray(colour, np.float64) * 255.0
    d = np.linalg.norm(rgb.astype(np.float64) - c, axis=-1)
    near = d <= TONE
    for o in others:
        if np.allclose(o, colour):
            continue
        near &= d <= np.linalg.norm(rgb.astype(np.float64) - np.asarray(o, np.float64) * 255.0, axis=-1)
    return near


def _across(skin, face, bary, direction, reach):
    """Walk the surface from a point in a direction, and return the points along the way with how
    far each is from the start, measured over the surface (cm). An exact geodesic, so it crosses
    panels, seams and folds the way the car does."""
    d = np.asarray(direction, np.float64)
    n = np.linalg.norm(d)
    if n < 1e-9:
        return np.zeros((0, 3)), np.zeros(0)
    path = np.asarray(skin.solver("trace").trace_geodesic_from_face(int(face), np.asarray(bary, np.float64),
                                                                   d / n * reach), np.float64)
    if len(path) < 2:
        return path, np.zeros(len(path)), False
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))])
    # The tracer cannot leave the surface: at an opening, an arch or the silhouette the walk simply
    # stops short. That, not any "off the body" test, is how a place cut by the car is known.
    reached = s[-1] >= reach * 0.98
    # sample it evenly so a long triangle doesn't hide the paint's edge
    t = np.arange(0.0, s[-1], 0.02)
    return np.stack([np.interp(t, s, path[:, k]) for k in range(3)], 1), t, reached


def measure(skin, drawing, img, others, read=None):
    """One band measured across itself, every STEP cm. Returns the widths and the offsets of its
    middle, both in mm, and how many places could not be measured."""
    pts = np.asarray(drawing["points"], np.float64)
    want = float(drawing["width"])
    colour = drawing["colour"]
    h, w = img.shape[:2]
    reach = max(want / 10.0 * 2.0, 2.0)          # cm: twice the width, at least 2 cm
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    at = np.arange(STEP, max(s[-1] - STEP, STEP + 1e-6), STEP)
    widths, centres, missed = [], [], 0
    f0, b0 = skin.nearest(np.stack([np.interp(at, s, pts[:, k]) for k in range(3)], 1))
    tan = np.stack([np.interp(at + 0.25, s, pts[:, k]) - np.interp(at - 0.25, s, pts[:, k]) for k in range(3)], 1)
    for k in range(len(at)):
        if f0[k] < 0:
            missed += 1
            continue
        nrm = skin.fn[f0[k]]
        t = tan[k] - nrm * (tan[k] @ nrm)
        if np.linalg.norm(t) < 1e-9:
            missed += 1
            continue
        side = np.cross(nrm, t / np.linalg.norm(t))
        edge, cut = [], False
        for sign in (1.0, -1.0):
            p, dist, reached = _across(skin, f0[k], b0[k], side * sign, reach)
            if len(p) < 2:
                edge.append(None)
                continue
            # the walk's own normal at every step, not the curve's: across a fold the surface
            # faces somewhere else, and carmap.Map.at picks the triangle that agrees with the
            # normal it is given, so one normal for the whole walk reads the wrong side of a fold
            wf, _ = skin.nearest(p)
            col, row, off = _texel_of(p, skin.fn[np.maximum(wf, 0)], w, h)
            rgb = img[row, col] if read is None else read(p[:len(col)], skin.fn[np.maximum(wf, 0)])
            on_body = off < 1.0
            ends = float(dist[-1])
            if not on_body.all():         # the walk ran off the car (an opening, an arch, the silhouette)
                k = int(np.flatnonzero(~on_body)[0])
                rgb, dist = rgb[:k], dist[:k]
                ends = float(dist[-1]) if len(dist) else 0.0
            if len(rgb) < 3 or not reached:
                edge.append(None)
                cut = True
                continue
            hit = _edge(rgb, dist, colour, rgb[-1])     # what lies beyond is whatever the walk ends on
            if hit is None:
                # the paint never ended before the car did: this place is cut by the car, not
                # mismeasured. A band that runs along the lip of the cockpit really is narrower
                # there; saying "wrong width" would blame the tool for the car's own hole.
                edge.append(None)
                cut = True
                continue
            if ends - hit < 0.05:                       # the edge found IS the car's edge
                cut = True
            edge.append(hit)
        if cut or edge[0] is None or edge[1] is None:
            missed += 1
            continue
        widths.append((edge[0] + edge[1]) * 10.0)          # cm -> mm
        centres.append((edge[0] - edge[1]) / 2.0 * 10.0)   # positive: the band sits to one side
    return np.asarray(widths), np.asarray(centres), missed, len(at)


def pieces(skin, drawing, img, others):
    """The painted texels as pieces of surface. Returns how many pieces are the band itself, how
    much paint (cm2) lies outside the biggest, and where the biggest stray is.

    The paint is measured by the TEXELS painted, not by the area of every mesh face a texel
    touches: a face is 35 mm across and a single stray texel inside one would otherwise be
    reported as 7 cm2 of stray paint when it is a twentieth of that."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    from tool import bake, paint
    h, w = img.shape[:2]
    b = bake.bake("Skin", w, h)
    tri, pos, nrm = b["tri"].reshape(-1), b["position"].reshape(-1, 3), b["normal"].reshape(-1, 3)
    idx = np.flatnonzero(tri >= 0)
    rows, cols = np.divmod(idx, w)
    painted = _is(img[rows, cols], drawing["colour"], others)
    if painted.sum() < 10:
        return 0, 0.0, ""
    f, _ = skin.in_tri(tri[idx][painted], pos[idx][painted])
    on = f >= 0
    if not on.any():
        return 0, 0.0, ""
    f = f[on]
    per_face = np.bincount(f, minlength=len(skin.F))       # how many texels each face carries
    hit = per_face > 0
    F = skin.F
    pair = np.stack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]], 1).reshape(-1, 2)
    key = np.sort(pair, axis=1)
    order = np.lexsort((key[:, 1], key[:, 0]))
    ks, fs = key[order], order // 3
    same = np.flatnonzero((ks[:-1] == ks[1:]).all(1))
    a, bb = fs[same], fs[same + 1]
    keep = hit[a] & hit[bb]
    live = np.flatnonzero(hit)
    remap = -np.ones(len(F), np.int64)
    remap[live] = np.arange(len(live))
    A = coo_matrix((np.ones(int(keep.sum())), (remap[a[keep]], remap[bb[keep]])), shape=(len(live), len(live)))
    n, lab = connected_components(A + A.T, directed=False)
    texels = np.array([per_face[live[lab == c]].sum() for c in range(n)], np.float64)
    area = texels * paint.TEXEL_CM ** 2                    # cm2 of paint, at the body's texel pitch
    order2 = np.argsort(-area)
    total = area.sum()
    # A line's continuity is about the LINE: a speck of paint elsewhere is a different fault
    # (stray paint), and calling it "the line is in two pieces" hides both.
    real = int((area >= max(total * 0.02, 0.5)).sum())
    stray = float(total - area[order2[0]]) if n else 0.0
    where = ""
    if n > 1 and stray > 0.01:
        q = live[lab == order2[1]]
        cen = skin.V[skin.F[q]].mean(1).mean(0)
        where = f"{sorted(set(str(x) for x in skin.part[q]))[0]} at z {cen[2]:.0f}"
    return real, stray, where


def check(name, falsify=False, floor=False):
    folder = paths.BUILD / name
    meta = json.loads((folder / "painted.json").read_text())
    drawn = [d for d in meta.get("drawn", []) if d.get("kind") == "skin line"]
    if not drawn:
        print(f"{name}: nothing was drawn on the skin (tool/skindraw.py). Nothing to check.")
        return []
    img = np.load(folder / "painted.npz")["Skin_B"]
    skin = skinmesh.load()
    others = [d["colour"] for d in meta.get("drawn", [])]
    if falsify:
        for d in drawn:
            p = np.asarray(d["points"], np.float64)
            f, b = skin.nearest(p)
            nrm = skin.fn[np.maximum(f, 0)]
            tan = np.gradient(p, axis=0)
            side = np.cross(nrm, tan / np.maximum(np.linalg.norm(tan, axis=1, keepdims=True), 1e-9))
            moved = p + side * SHIFT
            f2, b2 = skin.nearest(moved)
            d["points"] = skin.point(f2, b2).tolist()   # kept on the car, just not where the paint is

    floors = []
    print(f"{'band':26} {'mm':>4} {'places':>7} {'width mm':>18} {'centre mm':>14} {'pcs':>3} {'stray':>5} {'turn/100':>9}  verdict")
    print("-" * 118)
    fails = []
    for d in drawn:
        widths, centres, missed, total = measure(skin, d, img, others)
        npieces, stray, where = pieces(skin, d, img, others)
        if floor:
            # The same measurement taken off the zone that painted, instead of off the texture:
            # what the check would read if the texture had no grain at all. The gap between the two
            # is what the body's texel pitch (0.9 mm) and the band's own feather (2 mm) cost, and
            # no band can be measured tighter than that.
            from tool import skindraw
            pts = np.asarray(d["points"], np.float64)
            f, _ = skin.nearest(pts)
            zone = skindraw.band(skindraw.Curve(skin, pts, f, name=d["name"]), float(d["width"]))

            def read(p, n, _z=zone, _c=d["colour"]):
                w = _z(p, n)[:, None]
                return (np.asarray(_c) * 255.0)[None] * w + np.array([0.0, 0.0, 0.0])[None] * (1 - w)

            fw, fc, _, _ = measure(skin, d, img, others, read=read)
            ftxt = (f"{np.percentile(np.abs(fw - float(d['width'])), 95):.2f}" if len(fw) else "-")
            floors.append(ftxt)
        want = float(d["width"])
        bad = []
        if not len(widths):
            bad.append("nothing measured")
            wtxt, ctxt = "-", "-"
        else:
            werr = np.abs(widths - want)
            cerr = np.abs(centres)
            w95, c95 = np.percentile(werr, 95), np.percentile(cerr, 95)
            wtxt = f"{np.median(widths):6.1f} +-{w95:5.2f}"
            ctxt = f"{np.median(cerr):5.2f} +-{c95:5.2f}"
            if w95 > WIDTH:
                bad.append(f"width {w95:.2f}")
            if c95 > CENTRE:
                bad.append(f"centre {c95:.2f}")
        if npieces != 1:
            bad.append(f"{npieces} pieces" if npieces else "no paint")
        if stray > STRAY:
            bad.append(f"stray {stray:.1f} cm2" + (f" on the {where}" if where else ""))
        turn = _turn(skin, d)
        if turn > TURN:
            bad.append(f"turn {turn:.0f}")
        verdict = "ok" if not bad else "FAIL " + ", ".join(bad)
        if bad:
            fails.append((d["name"], verdict))
        print(f"{d['name'][:26]:26} {want:4.0f} {len(widths):3d}/{total:<3d} {wtxt:>18} {ctxt:>14} "
              f"{npieces:3d} {stray:5.1f} {turn:9.1f}  {verdict}")
    print()
    if floors:
        print(f"the texture's own floor, the same measurement taken off the zone instead of the texture: "
              f"{', '.join(floors)} mm at the 95th. What is over that is the texture's grain, not the band.")
    print(f"limits: width and centre within {WIDTH:.1f} and {CENTRE:.1f} mm at the 95th percentile (the body's texels "
          f"are 0.9 mm across, so an edge read off them can be out by that much: see --floor), one piece of paint, "
          f"under {STRAY:.1f} cm2 of it astray, turning under {TURN:.0f} degrees per 100 mm. Widths are measured ON "
          f"the car, by exact geodesics across the band, off the texture the car ships.")
    if falsify:
        if fails:
            print(f"FALSIFY: every curve moved {SHIFT * 10:.0f} mm and {len(fails)} of {len(drawn)} bands fail, as they must.")
            return []
        print(f"FALSIFY: the check passed with every curve moved {SHIFT * 10:.0f} mm: it measures nothing.")
        return [("falsify", "the check cannot fail")]
    print("all bands pass" if not fails else f"{len(fails)} of {len(drawn)} bands FAIL")
    return fails


def _turn(skin, drawing):
    """How much the curve turns within the surface, degrees per 100 mm."""
    p = np.asarray(drawing["points"], np.float64)
    d = np.diff(p, axis=0)
    L = np.linalg.norm(d, axis=1)
    ok = L > 1e-6
    if ok.sum() < 3:
        return 0.0
    d, L = d[ok] / L[ok, None], L[ok]
    f, _ = skin.nearest((p[:-1] + p[1:])[ok] / 2)
    n = skin.fn[np.maximum(f, 0)]
    a = d[:-1] - n[:-1] * (d[:-1] * n[:-1]).sum(1)[:, None]
    b = d[1:] - n[:-1] * (d[1:] * n[:-1]).sum(1)[:, None]
    na, nb = np.linalg.norm(a, axis=1), np.linalg.norm(b, axis=1)
    good = (na > 1e-9) & (nb > 1e-9)
    ang = np.degrees(np.arccos(np.clip(((a[good] / na[good, None]) * (b[good] / nb[good, None])).sum(1), -1, 1)))
    run = L[:-1][good].sum() * 10.0
    return float(ang.sum() / max(run, 1e-9) * 100.0)


def main():
    ap = argparse.ArgumentParser(description="a car's skin-drawn bands checked by number")
    ap.add_argument("name")
    ap.add_argument("--falsify", action="store_true", help="move every curve 5 mm: every check must fail")
    ap.add_argument("--floor", action="store_true", help="also measure the zone itself, to show what the texture costs")
    a = ap.parse_args()
    sys.exit(1 if check(a.name, a.falsify, a.floor) else 0)


if __name__ == "__main__":
    main()
