"""TSC_Ladybird, concept D, Silks with Anatomy's grass (the studio, 2026-09-28): the user's mix of
the concept round: "I like B the most. I do like the grass from C though". B's jockey's silks,
satin red with a few big black spots, and C's turf-green blades rising up the lower sides in place
of B's rail line and turf teeth. The spots are painted on the outer panels only and kept clear of
the sidepod inlets (on B one ran down inside an inlet: the user's note, "The spot in b also
transfers to the next object in the car, making it look weird and not properly applying pain") and
of the number panel and the engine cover panel, where the game draws the player's number and name.
Rough on purpose: flat colour, one finish, no details yet."""
from tool import shapes

WORDS = "I like B the most.  I do like the grass from C though"
NOTE = "The spot in b also transfers to the next object in the car, making it look weird and not properly applying pain."
RED, BLACK, TURF = "#D7262B", "#111111", "#3E8E3A"
# the outer panels a spot may sit on: never the inlets, the number panel or the engine cover panel
OUTER = ["body shell", "nose tip", "nose panel", "sidepod top", "engine cover|part", "rear flank"]
# big spots from above, (x, z, radius) in cm, scattered as silks' spots are. The bonnet's sits
# between the cockpit opening (z 85) and the nose fin's plate (x ±8, z 118 to 142), clear of both:
# over the plate, the upright fin stayed red, a notch in the spot, and the whole plate painted
# black made a keyhole
TOP = [(0, 178, 12), (0, 101, 11), (68, -32, 12), (-66, -38, 12), (33, -100, 11), (-33, -125, 11)]
# and one on each rear flank (y, z, radius), the flat spot behind the sidepod
SIDE = [(40, -70, 12)]


def top():
    return shapes.facing("up", 0.4, soft=0.006) & shapes.above(30)


def design(s):
    s.clay()
    s.step("Silks", "Satin red all over, big black spots over the top and on the rear flanks.", words=WORDS)
    s.paint("body", "satin", colour=RED)
    for x, z, r in TOP:
        s.paint(OUTER, "satin", colour=BLACK, zone=shapes.cylinder((x, -50, z), (x, 250, z), r) & top())
    for y, z, r in SIDE:
        s.paint(OUTER, "satin", colour=BLACK, zone=shapes.cylinder((-200, y, z), (200, y, z), r) & ~top())
    s.step("The grass", "Turf-green blades rising up the lower sides, as on concept C.", words=WORDS)
    s.paint("body", "satin", colour=TURF, zone=shapes.grass(base=6, height=(14, 30), seed=7) & ~top())
    s.step("For now", "The wheels and the inner car black: they get their own steps.")
    s.paint("wheels", "satin", colour=BLACK)
    s.paint("inner", "satin", colour=BLACK)
