"""Rescue v2: the snow rescue car (TSC_Snow) redrawn on the car's own lines, with more detail.
Signal orange; a black lower edge and a band of silver and orange checks that follow the side's
levels, rising with the tail; a pinstripe round the top; silver chevrons on the tail's deck; a
snowflake badge on the bonnet; RESCUE along the front flanks, a snowflake on the rear flanks; studded snow
tyres; amber rear lights."""
import numpy as np

from tool import levels, shapes

WORDS = "based on what you know can you design a skin or use the Rescue as a v2, to add more details"
ORANGE, AMBER = "#ff5a0f", "#ffb000"
CHECK = 15.0      # cm: a check's length along the car, twice a row's height
CHECK_FROM = 70.0  # z: a check's edge at the front wheel opening, where the band ends


def _checks(lower=False):
    """The checks' silver blocks: the upper row's start at CHECK_FROM and every 2 CHECK behind it,
    the lower row's in the gaps between."""
    def d(p, n):
        ph = np.mod(p[:, 2] - (CHECK_FROM - CHECK / 2) + CHECK, 2 * CHECK) - CHECK
        inside = CHECK / 2 - np.abs(ph)
        return -inside if lower else inside
    return shapes.field(d)


def _midway(upper, lower):
    """The body above the line midway between two levels (the side's levels, tool/levels.py)."""
    from tool.noise import smoothstep
    (Ya, dYa), (Yb, dYb) = [next(c[1:3] for c in levels.curves() if c[0] == n) for n in (upper, lower)]

    def f(p, n):
        z = p[:, 2].astype(np.float64)
        h = p[:, 1] - (Ya(z) + Yb(z)) / 2
        g = np.stack([np.zeros(len(h)), np.ones(len(h)), -(dYa(z) + dYb(z)) / 2], 1)
        nn = n.astype(np.float64)
        gs = np.linalg.norm(g - (g * nn).sum(1, keepdims=True) * nn, axis=1)
        return smoothstep(-0.05, 0.05, h / np.maximum(gs, 0.05)).astype(np.float32)
    return shapes.Zone(f, label=f"midway({upper!r}, {lower!r})")


def _chevrons(width=4.0, slope=0.75, z0=-152.0, z1=-132.0):
    """Chevrons across the tail panel, pointing forward: stripes `width` cm wide (square to them),
    as many gaps between, their arms falling back `slope` cm per cm out from the middle; inside the
    top's pinstripe, the panel's seams their ends."""
    k = np.sqrt(1 + slope * slope)
    period = 2 * width * k

    def d(p, n):
        u = p[:, 2] + slope * np.abs(p[:, 0])
        ph = np.mod(u - z1 + period / 4, period) - period / 2
        return (period / 4 - np.abs(ph)) / k
    return shapes.field(d) & shapes.band(z0, z1)


def _segments():
    """The snowflake's strokes, (x, z) pairs about its centre: six arms, a V on each."""
    out = []
    for i in range(6):
        a = np.pi / 2 + i * np.pi / 3
        u = np.array([np.cos(a), np.sin(a)])
        out.append((np.zeros(2), 8.0 * u))
        for at, length in ((4.0, 2.8), (6.2, 1.8)):
            for turn in (-np.pi / 4, np.pi / 4):
                b = a + turn
                out.append((at * u, at * u + length * np.array([np.cos(b), np.sin(b)])))
    return out


def _snowflake(centre, stroke=1.3, size=1.0, seen="above"):
    """A snowflake `size` times 16 cm across, its strokes `stroke` cm wide: seen from above at (x, z),
    or from the side ("left", "right") at (z, y), one arm up."""
    A = np.array([s[0] for s in _segments()], np.float32) * size
    B = np.array([s[1] for s in _segments()], np.float32) * size
    i, j = {"above": (0, 2), "left": (2, 1), "right": (2, 1)}[seen]

    def d(p, n):
        q = np.stack([p[:, i] - centre[0], p[:, j] - centre[1]], 1)
        best = np.full(len(q), np.inf, np.float32)
        for a, b in zip(A, B):
            ab = b - a
            t = np.clip(((q - a) @ ab) / (ab @ ab), 0, 1)
            best = np.minimum(best, np.linalg.norm(q - a - t[:, None] * ab, axis=1))
        return stroke / 2 - best
    return shapes.field(d) & shapes.facing({"above": "up", "left": (1, 0, 0), "right": (-1, 0, 0)}[seen], 0.5)


def _disc(centre, radius):
    """A disc seen from above at (x, z)."""
    return shapes.field(lambda p, n: radius - np.hypot(p[:, 0] - centre[0], p[:, 2] - centre[1])) & shapes.facing("up", 0.5)


def design(s):
    s.clay()
    s.step("Signal orange", "The body in gloss signal orange; below the lowest side level, rising with the tail, "
           "gloss black.", words=WORDS)
    s.paint("body", "gloss", colour=ORANGE)
    s.paint("body", "gloss black", zone=levels.below("between 6") | levels.below("bottom edge"))
    s.paint("side skirt", "gloss black")  # on round the nose, under the front flank and the nose

    s.step("The check band", "Two rows of silver and orange checks along each side between the levels, from the tail "
           "to the front wheel opening, a black pinstripe along their top.", words=WORDS)
    band = levels.band("between 3", "between 6")
    upper = _midway("between 4", "between 5")
    s.paint("body", "gloss", colour=ORANGE, zone=band)
    s.paint("body", "reflective tape", zone=band & (upper & _checks() | ~upper & _checks(lower=True)))
    s.paint("body", "gloss black", zone=levels.line("between 3", 0.6))

    s.step("The top and the tail", "A black pinstripe round the top, set in from its edge; silver chevrons on the "
           "tail's deck, pointing forward.", words=WORDS)
    s.paint("body", "gloss black", zone=levels.top_line("top 1", 0.6))
    s.paint("tail panel", "reflective tape", zone=_chevrons())

    s.step("Badges", "A black badge on the bonnet with a silver snowflake; RESCUE along the front flanks, a black "
           "snowflake on the rear flanks.", words=WORDS)
    s.paint("body", "gloss black", zone=_disc((0, 105), 11))
    s.paint("body", "reflective tape", zone=_snowflake((0, 105)))
    for spot, x in (("left flank", 35), ("right flank", -35)):  # clear of the sidepod's front and the top's pinstripe
        s.text("RESCUE", spot, colour="black", font="russo", height=8, italic=0.15, at=(x, 53, 58))
    for seen, x in (("left", 1), ("right", -1)):
        s.paint("body", "gloss black", zone=_snowflake((-66, 50), stroke=1.6, size=0.9, seen=seen) & shapes.plane((0, 0, 0), (x, 0, 0)))

    s.step("Wheels and inner car", "Black wheels with orange rings, studded snow tyres, the inner car dark grey, black "
           "frames round the inlets.", words=WORDS)
    s.paint("wheels", "satin black")
    s.paint("wheel cover ring", "gloss", colour=ORANGE)
    s.tyre_tread("TR-08")
    s.paint("inner", "dark grey satin")
    s.paint("sidepod frame", "gloss black")

    s.step("Lights", "Orange speed numbers; amber rear lights (red when braking).", words=WORDS, look="rear night")
    s.relight("speed numbers", ORANGE)
    s.relight("rear lights", AMBER)
