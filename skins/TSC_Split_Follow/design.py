"""A colour split at the middle of the car seen from the side, following the car: magenta below, cyan
above (the user, 2026-09-30: "if I want a color split right a the middle of the car if we look at it
sideways it will do that? Magenta bottom and top to be Cyan for example").

The car is short at the nose and tall at the cockpit: halfway up its side is 31 cm at the nose, 51 cm
mid-car and 42 cm at the tail. This split runs halfway up the side all along it, as a fair arc (a
parabola fitted to the halfway points every 4 cm, within 1.4 cm of them typically), so from the side
it rises and falls with the body. Like the level split it is one rule about height, exact and
continuous over every panel, the same on both sides. Take B; TSC_Split_Level is dead level.
"""

from tool import shapes

MAGENTA, CYAN, GRAPHITE = "#d4147a", "#19b5e0", "#2a2d33"
ARC = (-0.00035718, -0.02229366, 48.7269703)   # halfway up the side (cm) as a function of z (cm)


def halfway(z):
    a, b, c = ARC
    return a * z * z + b * z + c


def design(s):
    s.clay()
    s.step("Cyan", "The body cyan, gloss.", words="top to be Cyan")
    s.paint("body", "gloss", colour=CYAN)
    s.step("The split", "Magenta below a line halfway up the side, all along the car.",
           words="a color split right a the middle of the car if we look at it sideways ... Magenta bottom")
    s.paint("body", "gloss", colour=MAGENTA, zone=shapes.field(lambda p, n: halfway(p[:, 2]) - p[:, 1]))
    s.step("The rest", "Graphite wheel covers and inner car, so the split reads.")
    s.paint(["inner", "wheel covers"], "satin", colour=GRAPHITE)
