"""The levels on the clay car (tool/levels.py), the top two lines between swept up into the top line
where the nose begins, the four below them ending on the front wheel opening's edge: an option for how
the lines end where the nose begins (the user, 2026-10-04)."""
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
    s.step("The top two", "The top two lines between sweep up into the top line where the nose begins.", words=WORDS)
    T = cv["top edge"][1]
    for k in (1, 2):
        Yk = cv[f"between {k}"][1]
        Y = lambda z, Yk=Yk: T(z) - ease(z) * (T(z) - Yk(z))
        zs = np.arange(FROM, TO, 0.25)
        end = float(zs[np.argmax(T(zs) - Y(zs) < 0.8)])  # where it touches the top line
        s.paint(outer, "matte", colour=BLUE, zone=along(Y, cv[f"between {k}"][3][0], end))


FROM, TO = 30.0, 100.0  # the sweep, z in cm: from the sidepods' front to the start of the nose


def ease(z):
    """1 behind FROM, 0 at TO, a smooth S between."""
    t = np.clip((np.asarray(z, float) - FROM) / (TO - FROM), 0, 1)
    return 1 - t * t * (3 - 2 * t)
