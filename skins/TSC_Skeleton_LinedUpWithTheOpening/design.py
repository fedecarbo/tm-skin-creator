"""The levels on the clay car (tool/levels.py), the top two lines between ending in line with the
front wheel opening's upright edge, where the four below them end on it: an option for how the lines
end where the nose begins (the user, 2026-10-04)."""
import numpy as np
from tool import levels, shapes
from tool.noise import smoothstep

WORDS = "We havent defined the lines in the front part of the car btw. I guess you could give it a try"
BLACK, BLUE = "#0a0a0a", "#1d4ed8"


def along(Y, z0, z1, width=0.8):
    """A line at the height Y(z) on the outer body from z0 to z1 (levels.line's, for a curve of its own)."""
    dY = lambda z: (Y(np.asarray(z) + 0.05) - Y(np.asarray(z) - 0.05)) / 0.1
    f = levels._above_cm(Y, dY)
    z = shapes.Zone(lambda p, n: smoothstep(-0.1, 0.1, width / 2 - np.abs(f(p, n))).astype(np.float32))
    z = z & shapes.outside(0.1) & shapes.Zone(lambda p, n: smoothstep(-0.85, -0.75, n[:, 1]).astype(np.float32))
    return z & shapes.band(z0, z1)


def design(s):
    s.clay()
    cv = {c[0]: c for c in levels.curves()}
    body = sorted({i["name"] for i in s.parts.instances if i["mesh"] == "Skin"} - set(levels.WHEELS) - set(levels.OFF))
    outer = [f"{b}|part" for b in body]
    s.step("The top and the bottom", "The top line and the bottom line in black.", words=WORDS)
    for name in ("top edge", "bottom edge"):
        s.paint(outer, "matte", colour=BLACK, zone=levels.line(name))
    s.step("The levels between", "The six lines between in blue; the lower four end on the front wheel opening's edge.", words=WORDS)
    for k in (3, 4, 5, 6):
        s.paint(outer, "matte", colour=BLUE, zone=levels.line(f"between {k}"))
    s.step("The top two", "The top two lines between end in line with the opening's edge.", words=WORDS)
    for k in (1, 2):
        s.paint(outer, "matte", colour=BLUE, zone=along(cv[f"between {k}"][1], cv[f"between {k}"][3][0], END))


END = 70.0  # the front wheel opening's upright edge, z in cm (69.6 to 72.2 from 30 to 40 cm up)
