"""The car map's air (tool/carmap.py): how hard the oncoming air hits the body, in a warm ramp over
black, and smoke lines traced along the air's path from a rake at the nose and one along each
flank. A test car for the map, not a skin to drive (2026-09-29)."""

import numpy as np

from tool import shapes

RAMP = [(0.08, "#5a0f24"), (0.2, "#a61e22"), (0.35, "#e0521b"), (0.55, "#f7a21b"), (0.75, "#ffe9a8")]


def design(s):
    s.clay()
    s.step("Black", "The body in gloss black.", words="the car map")
    s.paint("body", "gloss", colour="#0d0e10")
    s.step("Hit", "Where the oncoming air hits the body, cool to hot.", words="the car map")
    for lo, colour in RAMP:
        s.paint("body", "satin", colour=colour, zone=shapes.hit(lo))
    s.step("Smoke", "Smoke lines along the air's path.", words="the car map")
    seeds = np.concatenate([shapes.rake(200, np.linspace(0.05, 0.95, 7)),
                            shapes.rake(150, [1.3, 1.6])])
    s.paint("body", "satin", colour="#f2f1ec", zone=shapes.streamlines(seeds, 1.4) & shapes.outside(0.2))
    s.paint(["inner", "wheel covers"], "satin", colour="#2a2d33")
