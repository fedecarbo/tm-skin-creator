"""The body sheet's test car (tool/surface.py): a 10 cm checker drawn flat on the sheet (shapes.sheet),
so its squares must come out square on every panel, and three bands at fixed offsets below the
shoulder measured in 3D from the map's one smooth design line (shapes.line_offset), so they run
parallel to the shoulder and never break at a join. A test car for the map, not a skin to drive
(2026-09-29)."""

import numpy as np

from tool import shapes

BODY = "body"


def design(s):
    s.clay()
    s.step("Checker", "A 10 cm checker drawn on the body sheet: every square 10 cm on the paint.", words="the body sheet")
    s.paint(BODY, "satin", colour="#f4f2ec")
    checker = shapes.sheet(lambda x, y: ((np.floor(x / 100) + np.floor(y / 100)) % 2) == 0)
    s.paint(BODY, "satin", colour="#2b2f36", zone=checker)
    s.step("Offset bands", "Three bands 8 mm wide, 30, 60 and 90 mm below the shoulder: the distance in 3D to the map's one "
           "smooth design line, so they never break at a join.", words="the body sheet")
    for d, col in ((30, "#e02020"), (60, "#1f8f3a"), (90, "#2050e0")):
        s.paint(BODY, "satin", colour=col, zone=shapes.line_offset("shoulder", d, 8))
    s.paint(BODY, "satin", colour="#d0208e", zone=shapes.line("shoulder", 0.8))
    s.paint(["inner", "wheel covers"], "satin", colour="#3a3d42")
