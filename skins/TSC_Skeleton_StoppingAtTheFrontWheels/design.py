"""The guides on the clay car (tool/levels.py) with the nose's lines in pink, the nose's top line and two
shared out under it, stopping in line with the front wheels' axle before they close together: an
option for the nose's lines that don't meet at the tip (the user, 2026-10-04)."""
import numpy as np
from tool import levels, shapes
from tool.noise import smoothstep

WORDS = "I personally think that the lines shouldnt meet at the nose. As in the top ones"
BLACK, BLUE, PINK = "#0a0a0a", "#1d4ed8", "#e0115f"
# the nose's top line, where its top folds down into its side (the middle of the roll, 45 degrees),
# z and y in cm, meeting the top line at the tip
NOSE_TOP = [[36.0, 68.64], [90.0, 62.76], [150.0, 54.47], [185.0, 47.31], [206.0, 40.58]]
BACK = 28.0  # the nose's lines start in line with the intake opening's front edge


def along(Y, z0, z1, width=0.8):
    """A line at the height Y(z) on the outer body from z0 to z1 (levels.line's, for a curve of its own)."""
    dY = lambda z: (Y(np.asarray(z) + 0.05) - Y(np.asarray(z) - 0.05)) / 0.1
    f = levels._above_cm(Y, dY)
    z = shapes.Zone(lambda p, n: smoothstep(-0.1, 0.1, width / 2 - np.abs(f(p, n))).astype(np.float32))
    z = z & shapes.outside(0.1) & shapes.Zone(lambda p, n: smoothstep(-0.85, -0.75, n[:, 1]).astype(np.float32))
    return z & shapes.band(z0, z1)


def design(s):
    s.clay()
    body = sorted({i["name"] for i in s.parts.instances if i["mesh"] == "Skin"} - set(levels.WHEELS) - set(levels.OFF))
    outer = [f"{b}|part" for b in body]
    drawn = {L["name"] for L in levels.load()["levels"]}
    s.step("The guides", "The top and bottom lines in black, the lines between in blue.", words=WORDS)
    for name, *_ in levels.curves():
        s.paint(outer, "matte", colour=BLACK if name in drawn else BLUE, zone=levels.line(name))
    T = {c[0]: c for c in levels.curves()}["top edge"][1]
    F = levels.spline(NOSE_TOP)[0]
    s.step("The nose's lines", "The nose's top line and two under it, stopping in line with the front wheels.", words=WORDS)
    for t in (0.0, 1 / 3, 2 / 3):
        s.paint(outer, "matte", colour=PINK, zone=along(lambda z, t=t: F(z) - t * (F(z) - T(z)), BACK, AXLE))


AXLE = 178.0  # the front wheels' axle, z in cm
