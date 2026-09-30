"""A colour split at the middle of the car seen from the side, dead level: magenta below, cyan above
(the user, 2026-09-30: "if I want a color split right a the middle of the car if we look at it
sideways it will do that? Magenta bottom and top to be Cyan for example").

One height all along the car, so from the side the split is a straight line. It is a single rule
about height -- every point of the body below 45 cm is magenta -- so it is exact and continuous over
every panel, seam and fold by construction, the same on both sides. Take A; TSC_Split_Follow is the
split that follows the car instead.
"""

from tool import shapes

MAGENTA, CYAN, GRAPHITE = "#d4147a", "#19b5e0", "#2a2d33"
LEVEL = 45.0   # cm above the ground: the side's halfway point averages 43.5 over the car's length


def design(s):
    s.clay()
    s.step("Cyan", "The body cyan, gloss.", words="top to be Cyan")
    s.paint("body", "gloss", colour=CYAN)
    s.step("The split", "Magenta below one height all along the car: a straight line from the side.",
           words="a color split right a the middle of the car if we look at it sideways ... Magenta bottom")
    s.paint("body", "gloss", colour=MAGENTA, zone=shapes.below(LEVEL))
    s.step("The rest", "Graphite wheel covers and inner car, so the split reads.")
    s.paint(["inner", "wheel covers"], "satin", colour=GRAPHITE)
