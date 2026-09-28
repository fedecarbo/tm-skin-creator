"""TSC_ConceptTrial, concept C: Anatomy. The car is the ladybird itself: the nose its black
head, the seam between its wing cases a black line from nose to tail, its seven spots where they
sit on the insect, and grass rising up the lower sides. Rough on purpose: flat colour in satin
(between the boards' matte and satin, the shell's own soft sheen), the big shapes only."""

import numpy as np

from tool import shapes

RED = "#D02A21"     # between the Field guide's vermilion and the Racing colours' silks red
BLACK = "#141414"   # the ink and the black of both boards
TURF = "#3E8E3A"    # the Racing colours' turf: the grass at the root
SAGE = "#7FA25A"    # the Field guide's sage: the taller blades catching the light

# The top of the car seen from above, crisp, without the lip at the bottom that turns up again
TOP = shapes.facing("up", 0.4, soft=0.006) & shapes.above(30)
OUTER = ["body shell", "nose tip", "nose panel", "sidepod top", "engine cover|part", "rear flank"]

# The head and the shield behind it: the nose back past its fin, the rear edge bowed back in the
# middle as a ladybird's is
HEAD_BACK = 116.0


def head():
    return shapes.field(lambda p, n: p[:, 2] - (HEAD_BACK + np.minimum(0.012 * p[:, 0] ** 2, 14.0)))


# The seven spots, from above: (x, z, radius). One on the seam just behind the head, and three
# on each wing case where the seven-spot has them: a small one at the shoulder (beside the
# cockpit, where the top is only about 20 cm wide), the biggest at the widest (the sidepods) and
# one near the seam towards the tail, clear of the number and name panels (x within 20).
SPOTS = [(0, 100, 9.0)]
for side in (1, -1):
    SPOTS += [(side * 29, 39, 7.5), (side * 68, -18, 14.0), (side * 37, -102, 12.0)]


def design(s):
    s.clay()

    s.step("The shell", "Ladybird red all over the body, satin; the wheels and the inner car black, "
           "as the insect's legs and underside are.")
    s.paint("body", "satin", colour=RED)
    s.paint("wheels", "satin", colour=BLACK)
    s.paint("inner", "satin", colour=BLACK)
    s.paint(["diffuser", "diffuser strake"], "satin", colour=BLACK)

    s.step("Head and seam", "The nose black as the ladybird's head, and the seam between its wing "
           "cases a black line from the head back to the tail.")
    s.paint("body", "satin", colour=BLACK, zone=head())
    # the seam starts behind the spot that sits on it (as the insect's does) and runs back from
    # the name panel to the tail and down it: the cockpit, the number and the name hold the middle
    seam = shapes.stripe(5.0) & shapes.behind(-121)
    s.paint(["engine cover|part", "tail panel"], "satin", colour=BLACK, zone=seam)

    s.step("Spots", "The seven spots where they sit on the insect: one on the seam behind the head, "
           "three on each wing case.")
    zone = None
    for i, (x, z, r) in enumerate(SPOTS):
        b = shapes.blob((x, 0, z), r, wobble=0.08, seed=i + 1)
        zone = b if zone is None else (zone | b)
    s.paint(OUTER, "satin", colour=BLACK, zone=zone & TOP)

    s.step("Grass", "Blades of grass rising up the lower sides, from the front wheels back: tall "
           "light blades behind a dark root.")
    # The blades on everything facing the side, down to where the body turns right under (the
    # flanks lean in all the way down, so the blades go on down to there); the solid root on what
    # faces the ground and on the ledge the side skirt makes at the front: blades drawn there
    # stretch into slashes. All behind the front wheels, off the nose and the sidepod's inlet.
    under = shapes.facing("down", 0.7, soft=0.03)
    ledge = shapes.below(24) & shapes.behind(140)
    low = ~under & ~shapes.facing("up", 0.5, soft=0.03) & shapes.behind(140)
    grassy = ["body shell", "side skirt", "sidepod top", "rear flank", "tail corner"]
    s.paint(grassy, "satin", colour=SAGE,
            zone=shapes.grass(base=18, height=(16, 32), width=(5, 9), lean=0.5, every=4, seed=3) & low)
    s.paint(grassy, "satin", colour=TURF,
            zone=shapes.grass(base=16, height=(8, 18), width=(5, 9), every=3, seed=7) & low)
    s.paint(grassy, "satin", colour=TURF, zone=(under & shapes.below(34) & shapes.behind(140)) | ledge)
