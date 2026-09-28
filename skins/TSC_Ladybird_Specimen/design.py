"""TSC_Ladybird, concept A, Specimen (the studio, 2026-09-28): the Field guide board on the car. The
top of the car is the ladybird's matte vermilion shell with seven ink spots, placed as on the
seven-spot; the sides are the paper of a naturalist's plate, with the grass drawn up them in ink
lines over a wash of sage. Rough on purpose: flat colour, one finish, no details yet."""
from tool import shapes

BUG = "Sure, ladybird."
GRASS = "I do wonder if the bottom is some lever of grass, that acts as the blend between the grass and the bug"
BOARDS = "c and b actually"
VERM, INK, PAPER, SAGE = "#D2381F", "#1A1A1A", "#EDE6D3", "#7FA25A"
# the seven-spot's spots from above, (x, z, radius) in cm, on the flat top (a map of the car from
# above, 2026-09-28): one on the nose behind the head, three a side (beside the cockpit's front,
# on the sidepods, on the deck)
SEVEN = [(0, 135, 11), (55, 15, 12), (-55, 15, 12), (62, -50, 13), (-62, -50, 13), (28, -125, 12), (-28, -125, 12)]


def shell():
    """The top of the car, as a ladybird's shell is seen from above: where the body faces up,
    edged crisp (a small `soft` in the normal's terms is a narrow edge in cm), not the lip at the
    bottom that turns up again."""
    return shapes.facing("up", 0.4, soft=0.006) & shapes.above(30)


def spot(x, z, r):
    """A round spot as seen from above, on the shell."""
    return shapes.cylinder((x, -50, z), (x, 250, z), r) & shell()


def design(s):
    s.clay()
    s.step("Paper", "The body in matte paper cream, the plate the ladybird is drawn on.", words=BOARDS)
    s.paint("body", "matte", colour=PAPER)
    s.step("The shell", "Matte vermilion over the top of the car, seven ink spots, the nose tip in ink.", words=BUG)
    s.paint("body", "matte", colour=VERM, zone=shell())
    for x, z, r in SEVEN:
        s.paint("body", "matte", colour=INK, zone=spot(x, z, r))
    s.paint("body", "matte", colour=INK, zone=shapes.front_of(170) & shell())
    s.step("The grass", "A wash of sage low on the sides, and grass drawn up them in ink.", words=GRASS)
    s.paint("body", "matte", colour=SAGE, zone=shapes.below(18) & ~shell())
    s.paint("body", "matte", colour=INK, zone=shapes.grass(base=4, height=(18, 40), line=1.3, every=1.3, lean=0.5, seed=3) & ~shell())
    s.step("For now", "The wheels and the inner car in ink: they get their own steps.")
    s.paint("wheels", "matte", colour=INK)
    s.paint("inner", "matte", colour=INK)
