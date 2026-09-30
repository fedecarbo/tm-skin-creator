"""The blueprints checked on the painted texture: every line and shape drawn on a view
(shapes.view_line, view_shape: the paint box keeps them in build/<name>/painted.json, "drawn")
seen from that same view, with the drawn path over it in green, and measured.

    python -m tool.blueprintcheck TSC_Blueprint             the checks, and build/<name>_blueprint_<view>.png per view
    python -m tool.blueprintcheck TSC_Blueprint --falsify   every path moved SHIFT mm first: the check must fail,
                                                            or it measures nothing

A line: along the path every 2 mm, the painted band is looked for across the path (its colour,
within TONE of the paint's, over four widths either side) and its centre's distance from the path
read off; a point on the body with no band near it is a miss (the path over an opening or off the
outline isn't counted: the line stops there by design; nor the band's round ends, nor the body seen
at a glancing angle, under blueprint.FACING, where the drawing didn't land). A pixel is a paint's
only if its colour is within TONE of it and nearer it than any other paint drawn in the view. The line passes when the centre stays
within LIMIT mm on average and at the 95th percentile, and no run of misses on the body is longer
than BREAK mm (a break). A shape: the painted area seen from the view against the filled path:
the share of the outline's length where the paint's edge is further than LIMIT mm from it. A fill
(shapes.view_fill): the same along its strokes.

The view's picture is the texture seen through the blueprint's own hit buffer, so it shows
exactly the texels a texel-by-texel paint put there, with no lighting: what the check measures is
the paint, not a render."""

import argparse
import json
import sys

import numpy as np
from PIL import Image, ImageDraw

from tool import blueprint, paths

LIMIT = 1.5    # mm: the band's centre from the path, the mean and the 95th percentile
BREAK = 12.0   # mm: a run of misses on the body longer than this is a break in the line
TONE = 70      # the colour distance (0..255 RGB) within which a texel counts as the paint's
SHIFT = 5.0    # mm: --falsify moves every path by this much


def seen(bp, tex):
    """The texture seen from the view: (H, W, 3) uint8, white off the body."""
    tri, bary = bp.hits()
    cov = tri >= 0
    uv = (bp.UV[tri[cov]] * bary[cov][..., None].astype(np.float64)).sum(1)
    th, tw = tex.shape[:2]
    tx = np.clip((uv[:, 0] % 1) * tw, 0, tw - 1).astype(int)
    ty = np.clip((1 - uv[:, 1] % 1) * th, 0, th - 1).astype(int)
    img = np.full((bp.H, bp.W, 3), 248, np.uint8)
    img[cov] = tex[ty, tx, :3]
    return img, cov


def _shifted(path, dh, dv):
    """The path with every point moved: only absolute M/L/C/Q/T/S coordinates, as the tool's own
    designs write them (relative commands are moved as they are, the same result)."""
    out = []
    for sub in blueprint.parse_path(path):
        parts = []
        for seg in sub:
            pts = [(x + dh, y + dv) for x, y in seg[1:]]
            if not parts:
                parts.append(f"M {pts[0][0]:.1f},{pts[0][1]:.1f}")
            parts.append(seg[0] + " " + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts[1:]))
        out.append(" ".join(parts))
    return " ".join(out)


def _is(img_px, colour, others):
    """Whether pixels are this paint: within TONE of its colour, and nearer it than any other paint
    drawn in the view (a dark grey fill beside a black pinstripe isn't the pinstripe)."""
    d = np.linalg.norm(img_px.astype(float) - np.asarray(colour) * 255, axis=-1)
    on = d < TONE
    for o in others:
        on &= d <= np.linalg.norm(img_px.astype(float) - np.asarray(o) * 255, axis=-1)
    return on


def check_line(bp, img, cov, path, colour, width, others=()):
    """(deviations mm per point on the body with a band, the longest run of misses in mm, the
    number of points on the body)."""
    devs, run, longest, on_body = [], 0, 0, 0
    for sub in blueprint.sample_path(path, 2.0):
        px, py = bp.to_pixel(sub[:, 0], sub[:, 1])
        _, body_n, _ = bp.hit(sub[:, 0], sub[:, 1])
        facing = body_n @ bp.toward
        t = np.gradient(np.stack([px, py], 1), axis=0)
        t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
        nrm = np.stack([-t[:, 1], t[:, 0]], 1)
        offs = np.arange(-2 * width, 2 * width + 1)
        for k in range(len(px)):
            c, r = int(px[k]), int(py[k])
            if not (0 <= c < bp.W and 0 <= r < bp.H) or not cov[r, c]:
                run = 0
                continue
            # the ends (the band's round caps) and the body seen at a glancing angle (the band
            # wrapping over an edge shows foreshortened: its centre in the view means nothing there)
            if k * 2 < width / 2 or (len(px) - 1 - k) * 2 < width / 2 or facing[k] < blueprint.FACING:
                run = 0
                continue
            on_body += 1
            xs = np.clip(np.round(px[k] + nrm[k, 0] * offs).astype(int), 0, bp.W - 1)
            ys = np.clip(np.round(py[k] + nrm[k, 1] * offs).astype(int), 0, bp.H - 1)
            on = _is(img[ys, xs], colour, others)
            if on.sum() == 0:
                run += 2
                longest = max(longest, run)
                continue
            run = 0
            devs.append(abs(offs[on].mean()))
    return np.asarray(devs), longest, on_body


def check_shape(bp, img, cov, path, colour, others=(), allow=0.0):
    """The share of the outline (every 2 mm, on the body) where the paint's edge is further than
    LIMIT mm (plus `allow`: half the width of a line drawn on the same stroke) from it: across
    the outline, the paint should start within that of the path."""
    bad, total = 0, 0
    offs = np.arange(-10 - int(allow), 11 + int(allow))
    for sub in blueprint.sample_path(path, 2.0):
        px, py = bp.to_pixel(sub[:, 0], sub[:, 1])
        t = np.gradient(np.stack([px, py], 1), axis=0)
        t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
        nrm = np.stack([-t[:, 1], t[:, 0]], 1)
        for k in range(len(px)):
            c, r = int(px[k]), int(py[k])
            if not (0 <= c < bp.W and 0 <= r < bp.H) or not cov[r, c]:
                continue
            xs = np.clip(np.round(px[k] + nrm[k, 0] * offs).astype(int), 0, bp.W - 1)
            ys = np.clip(np.round(py[k] + nrm[k, 1] * offs).astype(int), 0, bp.H - 1)
            on = _is(img[ys, xs], colour, others)
            if on.all() or not on.any():
                continue  # inside a painted area or outside it: the edge isn't here (the far side of a wrapped shape)
            edge = np.flatnonzero(np.diff(on.astype(int)) != 0)
            total += 1
            if np.abs(offs[edge] + 0.5).min() > LIMIT + allow:
                bad += 1
    return bad, total


def run(name, falsify=False):
    out = paths.BUILD / name
    meta = json.loads((out / "painted.json").read_text())
    drawn = meta.get("drawn", [])
    if not drawn:
        print(f"{name}: nothing was drawn on the blueprints (shapes.view_line, view_shape)")
        return True
    tex = np.load(out / "painted.npz")["Skin_B"]
    ok = True
    by_view = {}
    for d in drawn:
        by_view.setdefault(d["view"], []).append(d)
    for view, items in by_view.items():
        bp = blueprint.load(view)
        img, cov = seen(bp, tex)
        pic = Image.fromarray(img)
        draw = ImageDraw.Draw(pic)
        colours = [tuple(x["colour"]) for x in items]
        for d in items:
            others = [c for c in colours if c != tuple(d["colour"])]
            path = _shifted(d["path"], SHIFT, 0) if falsify else d["path"]
            for sub in blueprint.sample_path(path, 1.0):
                px, py = bp.to_pixel(sub[:, 0], sub[:, 1])
                draw.line(list(zip(px.tolist(), py.tolist())), fill=(0, 230, 0), width=1)
            if d["kind"] == "line":
                devs, longest, on_body = check_line(bp, img, cov, path, d["colour"], d["width"] or 10, others)
                if not len(devs):
                    print(f"  {view}: a {d['width']:.0f} mm line paints nothing on the body: FAIL")
                    ok = False
                    continue
                limit = max(LIMIT, (d["width"] or 10) / 10)  # a wide band on a curved flank projects a little lopsided
                passed = devs.mean() <= limit and np.percentile(devs, 95) <= limit and longest <= BREAK
                ok &= passed
                print(f"  {view}: a {d['width']:.0f} mm line, {on_body} points on the body: the band's centre "
                      f"{devs.mean():.2f} mm from the path on average, {np.percentile(devs, 95):.2f} at the 95th, "
                      f"{devs.max():.1f} at worst; the longest break {longest:.0f} mm: {'pass' if passed else 'FAIL'}")
            else:
                if not path.strip():  # a fill with no strokes: bounded by the body alone, nothing to measure against
                    print(f"  {view}: a fill bounded by the body alone: nothing to measure")
                    continue
                strokes = d.get("strokes") or [d["path"]]
                bad = total = 0
                for stroke in strokes:
                    # a line drawn on the same stroke covers the fill's edge by half its width
                    allow = max([x["width"] / 2 for x in items if x["kind"] == "line" and x["path"] == stroke and x["width"]] or [0.0])
                    b, t = check_shape(bp, img, cov, _shifted(stroke, SHIFT, 0) if falsify else stroke, d["colour"], others, allow)
                    bad, total = bad + b, total + t
                passed = total > 0 and bad / total <= 0.05
                ok &= passed
                what = "a filled shape" if d["kind"] == "shape" else f"a fill at ({d['at'][0]:.0f}, {d['at'][1]:.0f})"
                print(f"  {view}: {what}, {total} points of outline on the body: the paint's edge is off by more "
                      f"than {LIMIT} mm at {bad} ({100 * bad / max(total, 1):.1f} %): {'pass' if passed else 'FAIL'}")
        pic.save(paths.BUILD / f"{name}_blueprint_{view}{'_falsified' if falsify else ''}.png")
    print(f"pictures: {paths.BUILD}/{name}_blueprint_<view>.png")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--falsify", action="store_true")
    args = ap.parse_args()
    if args.falsify:
        print(f"every path moved {SHIFT} mm: the check must fail")
        if run(args.name, falsify=True):
            print("FALSIFY: the check passed anyway: it measures nothing")
            sys.exit(1)
        print("the check failed as it must")
        return
    sys.exit(0 if run(args.name) else 1)


if __name__ == "__main__":
    main()
