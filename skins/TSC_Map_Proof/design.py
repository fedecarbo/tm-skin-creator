"""TSC_Map_Proof: a livery drawn only on the body sheet (tool/surface.py), to show the car's own
lines (the user, 2026-09-29: "By the end in order to prove it you will build a car demonstrating
the curves and lines etc."). Deep petrol blue, and on it: gold pinstripes along the shoulder, the
lower edge and every real fold; a teal band and a pale one at fixed offsets below the shoulder,
which follow it over the body; four thin contour lines further down, at even steps over the
surface; three pale roundels laid across the curved panels at true size; and a decal, lettering
laid on the sheet at the sidepod's top. Everything is placed by the sheet's own millimetres
(car/sheet.json), nothing by eye. The right side is the left's mirror by construction."""

import numpy as np
from PIL import Image

from tool import shapes
from tool.paintbox import render_text

BASE = "#12283a"     # deep petrol blue
GOLD = "#d9a441"
TEAL = "#2f8f9d"
PALE = "#e8e2d0"
LINE = "#3f6f80"     # the contour lines, a shade over the base
DARK = "#1b1d21"
WORDS = "build a car demonstrating the curves and lines"


def shoulder():
    """The shoulder's longest run on the sheet (the body piece, nose to tail), in mm."""
    return max(shapes.sheet_lines("shoulder"), key=len)


def on_shoulder(x):
    """The point of the shoulder at sheet x (mm), and its downward normal."""
    l = shoulder()
    i = int(np.argmin(np.abs(l[:, 0] - x)))
    t = l[min(i + 4, len(l) - 1)] - l[max(i - 4, 0)]
    t /= np.linalg.norm(t)
    return l[i], np.array([-t[1], t[0]])


def disc(centre, r):
    cx, cy = centre
    return shapes.sheet(lambda x, y: np.hypot(x - cx, y - cy) < r)


def design(s):
    s.clay()
    s.step("Base", "Deep petrol blue satin over the whole body, the wheels and inner car dark.", words=WORDS)
    s.paint("body", "satin", colour=BASE)
    s.paint(["wheels", "inner"], "satin", colour=DARK)

    s.step("Pinstripes", "Gold pinstripes 6 mm wide along the shoulder and the lower edge, 4 mm along every real fold, "
           "each measured on the sheet so it stays that wide over the paint.", words=WORDS)
    s.paint("body", "satin", colour=GOLD, zone=shapes.sheet_line("shoulder", 6))
    s.paint("body", "satin", colour=GOLD, zone=shapes.sheet_line("lower", 6))
    s.paint("body", "satin", colour=PALE, zone=shapes.sheet_line("fold", 4))

    s.step("Bands", "A teal band 14 mm wide 25 mm below the shoulder and a pale one 6 mm wide 48 mm below it, both "
           "following the shoulder over the body; then four contour lines 3 mm wide every 25 mm further down.", words=WORDS)
    sh = shapes.sheet_lines("shoulder")
    s.paint("body", "satin", colour=TEAL, zone=shapes.sheet([shapes.offset(l, 25) for l in sh], width=14))
    s.paint("body", "satin", colour=PALE, zone=shapes.sheet([shapes.offset(l, 48) for l in sh], width=6))
    for d in (75, 100, 125, 150):
        s.paint("body", "satin", colour=LINE, zone=shapes.sheet([shapes.offset(l, d) for l in sh], width=3))

    s.step("Roundels", "Three pale roundels with a gold ring, 16 cm across, laid across the curved panels: the front "
           "flank, the sidepod's side and the rear flank, each 11 cm below the shoulder at its station.", words=WORDS)
    for x_mm in (900, 2450, 3300):
        p, n = on_shoulder(x_mm)
        c = p + 110 * n
        s.paint("body", "satin", colour=GOLD, zone=disc(c, 80))
        s.paint("body", "satin", colour=PALE, zone=disc(c, 70))
        s.paint("body", "satin", colour=BASE, zone=disc(c, 22))

    s.step("Decal", "The number 10 as a decal laid flat on the sheet on the sidepod's top, gold, 14 cm tall.", words=WORDS)
    masks, _ = render_text("10", "russo", 14.0)
    fill = masks["fill"].getchannel("A")
    img = Image.new("RGBA", fill.size, (217, 164, 65, 0))
    img.putalpha(fill)
    p, n = on_shoulder(2600)
    s.decal(img, "sheet", at=tuple(p - 95 * n), width=140, finish="satin")
