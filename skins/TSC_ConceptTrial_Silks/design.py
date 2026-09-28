"""Silks (concept B of TSC_ConceptTrial, the Racing colours board): the ladybird as a jockey's
silks. Satin red, a few big round black spots cut crisp over the shoulders and down the sides, as a
printed silk wraps a rider; along the bottom a clean band of turf with short upright blades under a
cream rail line, like the racecourse's rail over the grass. Rough on purpose: flat colour in satin,
the big shapes only.
"""

from tool import shapes

RED = "#D7262B"     # silks red, the main colour
BLACK = "#111111"   # the spots, the wheels and the inner car
CREAM = "#F3EEDF"   # the rail line
TURF = "#3E8E3A"    # the turf band

# the outer panels a spot may land on (SKILL.md: spots on the inner panels run into whatever lies under)
OUTER = ["body shell", "nose tip", "nose panel", "sidepod top", "engine cover|part", "rear flank",
         "rear quarter panel", "tail corner"]

# the places to keep clear: the number and name panels, the nose fin's plate. The sidepod inlets
# are kept clear by leaving their part out of OUTER: the sidepod spot wraps down the sidepod's
# outer skin beside them (every texel it takes there faces out, none inside the inlet), where a box
# over the inlets cut the spot along a straight line that no edge of the car explains.
CLEAR = shapes.box((-20, 50, -122), (20, 95, -60)) | shapes.box((-9, 50, 116), (9, 80, 144))

# three big spots a side, mirrored, each round in 3D and centred on the body's shoulder, so it
# wraps from the top down the side: (x, y, z, radius)
SPOTS = [
    (36, 65, 52, 23),     # the front flank, beside the cockpit
    (70, 63, -15, 25),    # the sidepod, over its top and down its outer side, clear of the rail
    (44, 66, -95, 24),    # the deck's shoulder, over its edge; forward of the dip over the rear wheel
]

RAIL_Y = 37.0      # the cream rail line's middle, cm above the ground
TURF_TOP = 27.0    # the turf band's solid top; the blades rise above it
FRONT = 140.0      # the fringe stops behind the front wheels (under the nose the skirt is a ledge)


def design(s):
    s.clay()

    s.step("Silks red", "The whole body in satin silks red; the wheels and the inner car in one dark colour.",
           words="maybe it is something that stands out")
    s.paint("body", "satin", colour=RED)
    s.paint("wheels", "satin", colour=BLACK)
    s.paint("inner", "satin", colour=BLACK)

    s.step("The spots", "A few big round black spots, cut crisp over the shoulders and down the sides.",
           words="Sure, ladybird")
    spots = None
    for x, y, z, r in SPOTS:
        for sx in (1, -1):
            one = shapes.sphere((sx * x, y, z), r)
            spots = one if spots is None else spots | one
    s.paint(OUTER, "satin", colour=BLACK, zone=spots & ~CLEAR)

    s.step("The turf band", "A clean band of turf along the bottom with short upright blades, under a cream rail line.",
           words="maybe the bottom is some lever of grass, that acts as the blend between the grass and the bug")
    turf = shapes.grass(base=TURF_TOP, height=(5.0, 9.0), width=(2.5, 3.5), lean=0.05, every=3.2, seed=3)
    s.paint("body", "satin", colour=TURF, zone=turf & shapes.behind(FRONT))
    rail = shapes.stripe(2.4, at=RAIL_Y, axis="y") & shapes.sides(0.5)
    s.paint("body", "satin", colour=CREAM, zone=rail & shapes.behind(FRONT))
