"""The body sheet's test car (tool/surface.py, shapes.sheet): a 10 cm checker and three bands at
fixed offsets below the shoulder, all drawn flat on the sheet and nowhere else, so the checker's
squares must come out square on every panel and the bands run parallel to the shoulder over the
body. A test car for the map, not a skin to drive (2026-09-29)."""

import numpy as np

from tool import shapes

BODY = "body"


def design(s):
    s.clay()
    s.step("Checker", "A 10 cm checker drawn on the body sheet: every square 10 cm on the paint.", words="the body sheet")
    s.paint(BODY, "satin", colour="#f4f2ec")
    checker = shapes.sheet(lambda x, y: ((np.floor(x / 100) + np.floor(y / 100)) % 2) == 0)
    s.paint(BODY, "satin", colour="#2b2f36", zone=checker)
    s.step("Offset bands", "Three bands 8 mm wide, 30, 60 and 90 mm below the shoulder over the body.", words="the body sheet")
    for d, col in ((30, "#e02020"), (60, "#1f8f3a"), (90, "#2050e0")):
        lines = [shapes.offset(l, d) for l in shapes.sheet_lines("shoulder")]
        s.paint(BODY, "satin", colour=col, zone=shapes.sheet(lines, width=8))
    s.paint(BODY, "satin", colour="#d0208e", zone=shapes.sheet_line("shoulder", 8))
    s.paint(["inner", "wheel covers"], "satin", colour="#3a3d42")
