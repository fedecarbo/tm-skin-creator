"""TSC_WindTunnel: a car painted by the air, as a 1970s wind tunnel photograph (concept B, Smoke,
picked 2026-09-29; redrawn on the car map the same day, its first test).

A smoke rake in front of the car sends a row of thin, evenly spaced smoke lines across its whole width
(each starts where the air first meets the top); each is traced along the air's own flow over the
body (tool/carmap.py), so the lines part round the cockpit
and the inlets as the air does, spread over the sidepods and leave the car where its surface turns
away. Behind the sidepods they start to wave: the wake. The one line that meets the car head-on, down
its middle, is signal red, from the nose's tip to the cockpit's rim, where it stops as the air does.
"""

import numpy as np

from tool import shapes
from tool.carmap import load

BLACK = "#0c0d0f"   # the photograph's black, piano lacquer
SMOKE = "#efeee9"   # the smoke
RED = "#e2231a"     # the one tagged streamline
DARK = "#141518"    # wheels and inner car

WIDTH = 1.7         # cm, every line
RAKE_Z = 198        # the rake's row, a little behind the nose's tip
WAKE_Z = -45.0      # behind the sidepods the lines start to wave
WORDS = "sure lets try"


def wake(lines, amp=1.8, wavelength=30.0):
    """The lines behind WAKE_Z waved across the flow, growing to amp cm at the tail, each a little
    later than its neighbour so the wake rolls rather than flaps (3 cm and a bigger lag crossed
    neighbouring lines where the deck narrows)."""
    m = load()
    out = []
    for k, line in enumerate(lines):
        if len(line) < 3:
            continue
        z = line[:, 2]
        t = np.clip((WAKE_Z - z) / (WAKE_Z + 162.0), 0, 1) ** 1.4
        _, n, _ = m.project(line)
        along = np.gradient(line, axis=0)
        side = np.cross(n, along)
        side /= np.maximum(np.linalg.norm(side, axis=1, keepdims=True), 1e-9)
        shift = amp * t * np.sin(2 * np.pi * (WAKE_Z - z) / wavelength + 0.3 * k)
        moved, _, _ = m.project(line + shift[:, None] * side)
        out.append(moved)
    return out


def band(lines, width=WIDTH):
    """Lines as a zone width cm wide, the same width on every curve."""
    from scipy.spatial import cKDTree
    tree = cKDTree(np.concatenate(lines))
    return shapes.field(lambda p, n: width / 2 - np.minimum(tree.query(p.astype(np.float64), workers=-1,
                                                                        distance_upper_bound=width)[0], width))


def design(s):
    s.clay()
    s.step("Gloss black", "The whole body in deep gloss black, like piano lacquer: the photograph's black.",
           words=WORDS)
    s.paint("body", "wet look", colour=BLACK)

    s.step("Smoke lines", "A rake of thin satin white smoke lines across the car's width, each traced along the air's "
           "flow over the car, two more along each flank, waving into a wake behind the sidepods.", words=WORDS)
    top = shapes.streamlines(shapes.front_rake(np.arange(3, 84, 6)), WIDTH).lines
    flank = shapes.streamlines(shapes.rake(150, [1.35, 1.7]), WIDTH).lines
    s.paint("body", "satin", colour=SMOKE, zone=band(wake(top + flank)) & shapes.outside(0.2))

    s.step("Red streamline", "The line down the middle, which meets the car head-on, in signal red to the "
           "cockpit's rim.", words=WORDS)
    spine = shapes.streamlines(shapes.rake(RAKE_Z, [0.0]), WIDTH, both=False).lines
    s.paint(["nose tip", "nose panel", "body shell"], "satin", colour=RED, zone=band(spine))
    s.paint("nose fin", "satin", colour=RED, zone=shapes.stripe(WIDTH))

    s.step("Wheels and inner car", "The wheels and the inner car in one dark satin, out of the picture.",
           words=WORDS)
    s.paint("wheels", "satin", colour=DARK)
    s.paint("inner", "satin", colour=DARK)
