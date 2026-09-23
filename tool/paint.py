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
