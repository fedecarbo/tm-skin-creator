"""TSC_Map_Proof: a livery drawn only on the body sheet (tool/surface.py), to show the car's own
lines (the user, 2026-09-29: "By the end in order to prove it you will build a car demonstrating
the curves and lines etc."). Deep petrol blue, and on it: gold pinstripes along the shoulder, the
lower edge and, in pale blue, every real fold; a teal band and a pale one at fixed offsets below the shoulder,
which follow it over the body; four thin contour lines further down, at even steps over the
surface (every line and band the exact 3D distance to the map's one smooth design line, so none
breaks at a join: shapes.line, shapes.line_offset); three pale roundels laid across the curved
panels at true size and a decal, lettering on the sidepod's top, both drawn on the body sheet
(shapes.sheet, s.decal on the sheet), where true size matters. Everything is placed by the map's
own lines and the sheet's millimetres, nothing by eye. The right side is the left's mirror by
construction, the lettering flipped so it reads on both."""

import numpy as np
from PIL import Image

from tool import shapes
from tool.paintbox import render_text

BASE = "#12283a"     # deep petrol blue
GOLD = "#d9a441"
TEAL = "#2f8f9d"
PALE = "#e8e2d0"
FOLD = "#a8d8e0"     # the folds' pinstripes, a pale blue
LINE = "#3f6f80"     # the contour lines, a shade over the base
DARK = "#1b1d21"
WORDS = "build a car demonstrating the curves and lines"


def shoulder():
    """The shoulder's design line on the sheet (one curve, nose to tail, its pieces in x order), in mm."""
    pieces = sorted(shapes.sheet_lines("design-shoulder"), key=lambda l: l[:, 0].min())
    return np.concatenate(pieces)


def on_shoulder(x):
    """The point of the shoulder at sheet x (mm), and its downward normal."""
    l = shoulder()
    i = int(np.argmin(np.abs(l[:, 0] - x)))
    t = l[min(i + 4, len(l) - 1)] - l[max(i - 4, 0)]
    t /= np.linalg.norm(t)
    return l[i], np.array([-t[1], t[0]])


def roundel(size=400):
    """A roundel as a picture: a gold ring, a pale disc, a dark centre (RGBA)."""
    from PIL import ImageDraw
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, size - 1, size - 1], fill=(217, 164, 65, 255))
    d.ellipse([size * 0.0625, size * 0.0625, size * 0.9375, size * 0.9375], fill=(232, 226, 208, 255))
    d.ellipse([size * 0.3625, size * 0.3625, size * 0.6375, size * 0.6375], fill=(18, 40, 58, 255))
    return img


def design(s):
    s.clay()
    s.step("Base", "Deep petrol blue satin over the whole body, the wheels and inner car dark.", words=WORDS)
    s.paint("body", "satin", colour=BASE)
    s.paint(["wheels", "inner"], "satin", colour=DARK)

    s.step("Pinstripes", "Gold pinstripes 6 mm wide along the shoulder and the lower edge, 4 mm along every real fold, "
           "each measured on the sheet so it stays that wide over the paint.", words=WORDS)
    s.paint("body", "satin", colour=GOLD, zone=shapes.line("shoulder", 0.6))
    s.paint("body", "satin", colour=GOLD, zone=shapes.line("lower", 0.6))
    s.paint("body", "satin", colour=FOLD, zone=shapes.line("fold", 0.4))

    s.step("Bands", "A teal band 14 mm wide 25 mm below the shoulder and a pale one 6 mm wide 48 mm below it, both "
           "following the shoulder over the body; then four contour lines 3 mm wide every 25 mm further down.", words=WORDS)
    s.paint("body", "satin", colour=TEAL, zone=shapes.line_offset("shoulder", 25, 14))
    s.paint("body", "satin", colour=PALE, zone=shapes.line_offset("shoulder", 48, 6))
    for d in (75, 100, 125, 150):
        s.paint("body", "satin", colour=LINE, zone=shapes.line_offset("shoulder", d, 3))

    s.step("Roundels", "Three pale roundels with a gold ring, 16 cm across, laid on the sheet across the curved panels: the "
           "front flank, the sidepod's side and the rear flank, each 11 cm below the shoulder at its station, moved clear of "
           "any panel edge, fold or opening.", words=WORDS)
    for x_mm, d in ((900, 60), (2450, 90), (3000, 60)):  # the flank's upper half, the sidepod's side, the rear flank behind it
        p, n = on_shoulder(x_mm)
        s.decal(roundel(), "sheet", at=tuple(p + d * n), width=160, finish="satin")

    s.step("Decal", "The number 10 as a decal laid flat on the sheet on the sidepod's top, gold, 14 cm tall.", words=WORDS)
    masks, _ = render_text("10", "russo", 14.0)
    fill = masks["fill"].getchannel("A")
    img = Image.new("RGBA", fill.size, (217, 164, 65, 0))
    img.putalpha(fill)
    p, n = on_shoulder(2500)  # the sidepod's top, forward of its rear corner and off the sewn inboard edge
    s.decal(img, "sheet", at=tuple(p - 40 * n), width=140, finish="satin")
