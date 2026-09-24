"""Painting helpers that work on a bake (tool/bake.py): masks, projected text, UV grids.

Coordinates: x = the car's side (+x is the car's left, to be confirmed in game), y = up,
z = forward. Lengths are in cm.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONTS = {
    "bold": "C:/Windows/Fonts/arialbd.ttf",
    "impact": "C:/Windows/Fonts/impact.ttf",
    "bahnschrift": "C:/Windows/Fonts/bahnschrift.ttf",
}


def covered(bake):
    return bake["tri"] >= 0


def text_image(text, height_px, font="impact", arrow=None):
    """White-on-black text as a float mask. arrow: None, 'right' or 'up' (added after/above)."""
    f = ImageFont.truetype(FONTS[font], height_px)
    box = f.getbbox(text)
    w, h = box[2] - box[0], box[3] - box[1]
    pad = height_px // 6
    extra_w = int(height_px * 1.2) if arrow == "right" else 0
    im = Image.new("L", (w + 2 * pad + extra_w, h + 2 * pad), 0)
    d = ImageDraw.Draw(im)
    d.text((pad - box[0], pad - box[1]), text, fill=255, font=f)
    if arrow == "right":
        x0, cy = w + 2 * pad, (h + 2 * pad) / 2
        s = height_px * 0.45
        d.polygon([(x0, cy - s * 0.35), (x0 + s, cy - s * 0.35), (x0 + s, cy - s), (x0 + 2.2 * s, cy),
                   (x0 + s, cy + s), (x0 + s, cy + s * 0.35), (x0, cy + s * 0.35)], fill=255)
    return np.asarray(im, np.float32) / 255


def arrow_image(length_px, width_px):
    """An arrow pointing up (towards row 0)."""
    im = Image.new("L", (width_px, length_px), 0)
    d = ImageDraw.Draw(im)
    head = width_px
    shaft = width_px * 0.36
    cx = width_px / 2
    d.polygon([(cx, 0), (width_px, head), (cx + shaft / 2, head), (cx + shaft / 2, length_px),
               (cx - shaft / 2, length_px), (cx - shaft / 2, head), (0, head)], fill=255)
    return np.asarray(im, np.float32) / 255


def project(bake, image, centre, right, up, width_cm, facing, min_facing=0.35, where=None):
    """Project a flat image onto the car, like a decal.

    centre: 3D point (cm) where the image's centre lands. right/up: unit 3D directions of the
    image's x and y axes on the car. width_cm: the image's width on the car. facing: the
    direction the decal is seen from (towards the viewer); texels whose normal points less
    than min_facing that way are left alone. where: optional extra texel mask.
    Returns a float mask (h, w): the image's value at each texel, 0 elsewhere.
    """
    ih, iw = image.shape
    cm_per_px = width_cm / iw
    rel = bake["position"] - np.asarray(centre, np.float32)
    s = rel @ np.asarray(right, np.float32) / cm_per_px + iw / 2
    t = ih / 2 - rel @ np.asarray(up, np.float32) / cm_per_px
    ok = covered(bake) & ((bake["normal"] @ np.asarray(facing, np.float32)) >= min_facing)
    ok &= (s >= 0) & (s < iw) & (t >= 0) & (t < ih)
    if where is not None:
        ok &= where
    out = np.zeros(ok.shape, np.float32)
    out[ok] = image[t[ok].astype(int), s[ok].astype(int)]
    return out


def project_near(bake, image, centre, right, up, width_cm, facing, min_facing=0.3, cell_cm=1.5, tol_cm=10.0):
    """Like project(), but only onto the surface nearest the viewer: a decal crosses every panel
    in its footprint and never reaches the far side of the car or anything behind a panel.
    Returns (values (h, w), info): info["landed"] is the share of the image's opaque pixels that
    reached a texel, so the caller can say when part of a picture fell into a gap or off an
    edge; info["step_cm"] how far the surface under it departs from flat (a fold or a step)."""
    pos = bake["position"].reshape(-1, 3)
    nrm = bake["normal"].reshape(-1, 3)
    cov = covered(bake).reshape(-1)
    vals, info = project_points(pos, nrm, cov, image, centre, right, up, width_cm, facing, min_facing, cell_cm, tol_cm)
    return vals.reshape(bake["position"].shape[:2]), info


TEXEL_CM = 0.09  # the body's texel pitch at 4096² (median 0.089 cm, measured 2026-09-24)


def fit_to_texels(image, width_cm, texel_cm):
    """The picture filtered down to about one pixel per texel, so sampling it can't alias.
    A picture with fewer pixels than that is left alone."""
    ih, iw = image.shape
    want = width_cm / texel_cm
    if iw <= 1.25 * want:
        return image
    from PIL import Image
    w2 = max(2, int(round(want)))
    h2 = max(2, int(round(ih * w2 / iw)))
    im = Image.fromarray(np.ascontiguousarray(image, np.float32), "F").resize((w2, h2), Image.LANCZOS)
    return np.clip(np.asarray(im, np.float32), 0, 1)


def project_points(pos, nrm, cov, image, centre, right, up, width_cm, facing, min_facing=0.3, cell_cm=1.5, tol_cm=10.0,
                   texel_cm=TEXEL_CM):
    """project_near() on flat arrays of texels: pos (n, 3), nrm (n, 3), cov (n,) bool.
    Returns (values (n,), info). The depth test works per cell_cm cell of the image: a texel is
    kept if it's within tol_cm of the nearest texel in its cell or the cells around it.
    The picture is filtered to the texel pitch and sampled bilinearly (no aliasing)."""
    from scipy.ndimage import map_coordinates, maximum_filter
    image = fit_to_texels(image, width_cm, texel_cm)
    ih, iw = image.shape
    cm_per_px = width_cm / iw
    facing = np.asarray(facing, np.float32)
    facing = facing / np.linalg.norm(facing)
    rel = pos - np.asarray(centre, np.float32)
    s = rel @ np.asarray(right, np.float32) / cm_per_px + iw / 2
    t = ih / 2 - rel @ np.asarray(up, np.float32) / cm_per_px
    ok = cov & ((nrm @ facing) >= min_facing)
    ok &= (s >= 0) & (s < iw) & (t >= 0) & (t < ih)
    out = np.zeros(len(pos), np.float32)
    if not ok.any():
        return out, {"landed": 0.0, "step_cm": 0.0}
    depth = rel @ facing  # larger = nearer the viewer
    cell_px = max(1.0, cell_cm / cm_per_px)
    ncx, ncy = int(np.ceil(iw / cell_px)), int(np.ceil(ih / cell_px))
    cx = np.minimum((s[ok] / cell_px).astype(np.int64), ncx - 1)
    cy = np.minimum((t[ok] / cell_px).astype(np.int64), ncy - 1)
    near = np.full((ncy, ncx), -np.inf, np.float32)
    np.maximum.at(near, (cy, cx), depth[ok])
    # the nearest over each cell's neighbourhood, so a gap in the near surface doesn't let the
    # far side through at a cell's edge
    near = maximum_filter(near, size=3, mode="nearest")
    keep = np.zeros(len(pos), bool)
    keep[ok] = depth[ok] >= near[cy, cx] - tol_cm
    ti, si = t[keep].astype(int), s[keep].astype(int)
    # bilinear, with pixel centres at +0.5 (the picture's edge fades over half a pixel)
    out[keep] = map_coordinates(image, [t[keep] - 0.5, s[keep] - 0.5], order=1, mode="nearest")
    # how much landed, counted in half-centimetre cells (the image has more pixels than the
    # car has texels, so a pixel count would miss most of them)
    q = max(1, int(round(0.5 / cm_per_px)))
    hh, ww = max(1, ih // q), max(1, iw // q)
    hit = np.zeros((hh, ww), bool)
    hit[np.minimum(ti // q, hh - 1), np.minimum(si // q, ww - 1)] = True
    opaque = (image[:hh * q, :ww * q].reshape(hh, q, ww, q).max(axis=(1, 3))) > 0.05
    landed = float(hit[opaque].sum() / max(opaque.sum(), 1))
    # how far from flat the surface under the picture is: the depth left after the best plane
    # through the kept texels is taken out (a fold or a step shows as a big spread)
    step = 0.0
    if keep.sum() > 100:
        A = np.stack([s[keep], t[keep], np.ones(keep.sum(), np.float32)], 1)
        coef, *_ = np.linalg.lstsq(A, depth[keep], rcond=None)
        resid = depth[keep] - A @ coef
        step = float(np.percentile(resid, 97) - np.percentile(resid, 3))
    return out, {"landed": landed, "step_cm": step}


def uv_grid(width, height, cells=16, line=0.004, font_px=None):
    """Grid lines and a number in each cell, drawn flat in UV space. Returns (lines, digits)."""
    lines = Image.new("L", (width, height), 0)
    digits = Image.new("L", (width, height), 0)
    dl, dd = ImageDraw.Draw(lines), ImageDraw.Draw(digits)
    cw, ch = width / cells, height / (cells * height // width)
    rows = cells * height // width
    lw = max(2, int(width * line))
    for i in range(cells + 1):
        dl.rectangle([i * cw - lw / 2, 0, i * cw + lw / 2, height], fill=255)
    for j in range(rows + 1):
        dl.rectangle([0, j * ch - lw / 2, width, j * ch + lw / 2], fill=255)
    f = ImageFont.truetype(FONTS["bold"], font_px or int(cw * 0.28))
    for j in range(rows):
        for i in range(cells):
            dd.text((i * cw + cw / 2, j * ch + ch / 2), str(j * cells + i), fill=255, font=f, anchor="mm")
    return np.asarray(lines, np.float32) / 255, np.asarray(digits, np.float32) / 255


def mix(base, colour, mask):
    """Blend a colour into an (h, w, c) float image by a (h, w) mask."""
    m = np.clip(mask, 0, 1)[..., None]
    return base * (1 - m) + np.asarray(colour, np.float32) * m
