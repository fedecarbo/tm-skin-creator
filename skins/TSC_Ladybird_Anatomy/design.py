"""TSC_Ladybird, concept C, Anatomy (the studio, 2026-09-28): the two boards together: the field
guide's anatomy in the silks' bold satin. The car is the ladybird: the nose its black head, the body
its red wing cases split down the middle by the black seam (a stripe nose to tail), the seven-spot's
spots where they sit on the insect, and the grass rising up the lower sides in turf green. The
head's two pale marks read as eyes on the car, so they went (the brief: no face). Rough on
purpose: flat colour, one finish, no details yet."""
from tool import shapes

BUG = "Sure, ladybird."
GRASS = "I do wonder if the bottom is some lever of grass, that acts as the blend between the grass and the bug"
BOARDS = "c and b actually"
RED, BLACK, TURF = "#D7262B", "#111111", "#3E8E3A"
# the seven-spot's spots from above, (x, z, radius) in cm: one on the seam behind the head, three
# a side (beside the cockpit's front, on the sidepods, on the deck)
SEVEN = [(0, 128, 13), (55, 15, 14), (-55, 15, 14), (62, -52, 15), (-62, -52, 15), (28, -125, 14), (-28, -125, 14)]


def top():
    return shapes.facing("up", 0.4, soft=0.006) & shapes.above(30)


def design(s):
    s.clay()
    s.step("Wing cases", "Satin red over the body, split down the middle by a black seam, nose to tail.", words=BUG)
    s.paint("body", "satin", colour=RED)
    s.paint("body", "satin", colour=BLACK, zone=shapes.stripe(5) & top())
    s.step("The head", "The nose black, as the ladybird's head.", words=BOARDS)
    s.paint("body", "satin", colour=BLACK, zone=shapes.front_of(158))
    s.step("Seven spots", "The seven-spot's spots: one on the seam behind the head, three a side.", words=BUG)
    for x, z, r in SEVEN:
        s.paint("body", "satin", colour=BLACK, zone=shapes.cylinder((x, -50, z), (x, 250, z), r) & top())
    s.step("The grass", "Turf-green blades rising up the lower sides.", words=GRASS)
    s.paint("body", "satin", colour=TURF, zone=shapes.grass(base=6, height=(14, 30), seed=7) & ~top())
    s.step("For now", "The wheels and the inner car black: they get their own steps.")
    s.paint("wheels", "satin", colour=BLACK)
    s.paint("inner", "satin", colour=BLACK)
