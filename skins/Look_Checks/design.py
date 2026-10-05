"""A test car for the tool's checks (tool/checks.py), not a design: four faults planted on purpose,
each one a flaw the user once pointed out on a car, for the checks to name before anyone looks."""
from functools import reduce

from tool import levels, shapes

PALE, BLACK, RED, BLUE, ORANGE = "#e9e7e1", "#151515", "#d7262b", "#1f5fd0", "#ff7a1a"


def from_above(x, z, radius):
    """A round spot drawn from above, on the surfaces that face up."""
    return shapes.cylinder((x, -50, z), (x, 250, z), radius) & shapes.facing("up", 0.4, soft=0.006)


def design(s):
    s.clay()
    s.step("The car", "Pale grey all over, the bottom piece black.")
    s.paint("body", "gloss", colour=PALE)
    s.paint("side skirt", "gloss", colour=BLACK)
    s.paint("wheels", "satin", colour=BLACK)
    s.paint("inner", "satin", colour="#2a2b2e")

    s.step("Fault 1: a spot cut by an edge", "A red spot on the bonnet, running into the cockpit's rim.")
    s.paint("body", "gloss", colour=RED, zone=from_above(0, 79, 13))

    s.step("Fault 2: a spot on two pieces", "A blue spot on the deck's left, running on over the gap onto the "
           "tail's corner.", look="rear")
    s.paint("body", "gloss", colour=BLUE, zone=from_above(35, -130, 15))

    s.step("Fault 3: a band over the bottom piece", "An orange band along each side, painted over the bottom "
           "piece's black ahead of the sidepods.")
    s.paint("body", "gloss", colour=ORANGE, zone=levels.band("between 3", "between 6"))

    s.step("Fault 4: dots round the number panel", "Black dots round the panel where the game letters the "
           "player's number, as if it were a piece.", look="rear")
    dots = [(x, z) for x in (-21.5, 21.5) for z in (-76, -70, -64)] + [(x, z) for z in (-80.5, -59.5) for x in (-12, 0, 12)]
    s.paint("body", "gloss", colour=BLACK, zone=reduce(lambda a, b: a | b, (from_above(x, z, 0.8) for x, z in dots)))
