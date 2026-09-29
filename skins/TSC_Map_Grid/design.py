"""The car map's positions (tool/carmap.py, shapes.across, shapes.along): a grid that bends with the
body. Across: a line every quarter of the way from the top's middle to the shoulder (green at the
shoulder), down the side to the lower edge (magenta), and under; along: a line every tenth of the
way from the nose to the tail. A test car for the map, not a skin to drive (2026-09-29)."""

import numpy as np

from tool import shapes

BODY = "body"


def design(s):
    s.clay()
    s.step("Bands", "The top, the sides and the underside in three tones.", words="the car map")
    s.paint(BODY, "satin", colour="#f4f2ec", zone=shapes.across(0, 1))
    s.paint(BODY, "satin", colour="#bcd4ec", zone=shapes.across(1, 2))
    s.paint(BODY, "satin", colour="#8a9099", zone=shapes.across(2, 3.01))
    s.step("Grid", "Lines across the body every quarter, and along it every tenth.", words="the car map")
    for a in np.arange(0.25, 3.0, 0.25):
        if a in (1.0, 2.0):
            continue
        s.paint(BODY, "satin", colour="#2b2f36", zone=shapes.across(a - 0.012, a + 0.012))
    for a in np.arange(0.1, 1.0, 0.1):
        s.paint(BODY, "satin", colour="#2b2f36", zone=shapes.along(a - 0.0015, a + 0.0015))
    s.paint(BODY, "satin", colour="#1f8f3a", zone=shapes.line("shoulder", 1.6))
    s.paint(BODY, "satin", colour="#d0208e", zone=shapes.line("lower", 1.6))
    s.paint(["inner", "wheel covers"], "satin", colour="#3a3d42")
