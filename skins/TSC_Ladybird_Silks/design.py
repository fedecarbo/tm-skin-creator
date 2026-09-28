"""TSC_Ladybird, concept B, Silks (the studio, 2026-09-28): the Racing colours board on the car. The
ladybird as a jockey's silks, "red, black spots": satin red all over, a few big black spots over the
top and down the sides, cut crisp, and along each side a cream rail line with flat, sharp blades of
turf under it. Rough on purpose: flat colour, one finish, no details yet."""
from tool import shapes

BUG = "Sure, ladybird."
GRASS = "I do wonder if the bottom is some lever of grass, that acts as the blend between the grass and the bug"
BOARDS = "c and b actually"
RED, BLACK, CREAM, TURF = "#D7262B", "#111111", "#F3EEDF", "#3E8E3A"
# big spots from above, (x, z, radius) in cm, scattered as silks' spots are, on the flat top
TOP = [(0, 175, 13), (0, 110, 15), (58, 20, 16), (-50, -15, 17), (70, -60, 15), (-20, -75, 18), (35, -130, 16), (-40, -140, 13)]
# and on the sides (y, z, radius), both sides alike
SIDE = [(42, 95, 11), (46, -5, 13), (40, -105, 12)]


def top():
    return shapes.facing("up", 0.4, soft=0.006) & shapes.above(30)


def design(s):
    s.clay()
    s.step("Silks", "Satin red all over, big black spots over the top and down the sides.", words=BUG)
    s.paint("body", "satin", colour=RED)
    for x, z, r in TOP:
        s.paint("body", "satin", colour=BLACK, zone=shapes.cylinder((x, -50, z), (x, 250, z), r) & top())
    for y, z, r in SIDE:
        s.paint("body", "satin", colour=BLACK, zone=shapes.cylinder((-200, y, z), (200, y, z), r) & ~top())
    s.step("Rail and turf", "A cream rail line along each side, flat sharp blades of turf rising under it.", words=GRASS)
    s.paint("body", "satin", colour=TURF, zone=shapes.grass(base=14, height=(8, 17), width=(6, 10), lean=0.12, every=4.5, seed=5) & ~top())
    s.paint("body", "satin", colour=CREAM, zone=shapes.stripe(2.5, at=32, axis="y") & ~top())
    s.step("For now", "The wheels and the inner car black: they get their own steps.", words=BOARDS)
    s.paint("wheels", "satin", colour=BLACK)
    s.paint("inner", "satin", colour=BLACK)
