"""The car map, layer "open" (tool/carmap.py): how much of the open air each spot of the body sees,
in five bands. White: fully out in the open (80 % or more); pale yellow, orange, red; dark violet:
hidden (under 20 %: inside the inlets, under a panel, tucked behind the inner car). A test car for
the map, not a skin to drive (2026-09-29)."""

from tool import carmap, shapes
from tool.noise import smoothstep

BANDS = [(0.8, "#f4f2ec"), (0.6, "#f3d27a"), (0.4, "#ec8a2f"), (0.2, "#c8322a"), (-1.0, "#2a1740")]


def at_least(lo):
    return shapes.Zone(lambda p, n: smoothstep(lo - 0.01, lo + 0.01, carmap.load().value("open", p, n)))


def design(s):
    s.clay()
    s.step("Open", "The body coloured by how much of the open air each spot sees.", words="the car map")
    for lo, colour in reversed(BANDS):
        s.paint(["body", "wheel covers"], "satin", colour=colour, zone=at_least(lo))
    s.paint("inner", "satin", colour="#3a3d42")
