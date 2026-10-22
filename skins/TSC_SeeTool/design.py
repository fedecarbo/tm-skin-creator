"""TSC_SeeTool: a throwaway test car, from the user's nine-point brief (notes.md)."""
from tool import marks, meshlines, shapes

WARM_WHITE = "#efe8d8"      # "warm white" (the colour word alone reads as plain white): warm enough that the
WHITE = "#ffffff"           # pure white discs on it are seen
NAVY = "deep navy"

# The deck's free top beside and behind the game's lettered panels, a hex grid 10 cm apart (seen from above, the
# left side's; each mark's twin is the right's). Measured with s.mark one by one: each lands whole at 4 cm; (43, -114)
# shrank against the deck's edge and is left out.
DECK_DOTS = [(28, -88), (38, -88), (48, -88), (33, -96.7), (43, -96.7), (28, -105.3), (38, -105.3), (33, -114),
             (28, -122.6), (38, -122.6)]


def design(s):
    s.clay()

    s.step("Two tones", "Warm white above, deep navy satin below, split level 40 cm off the ground all round.",
           words="The whole body warm white above and deep navy satin below, split by one level line 40 cm off "
                 "the ground, all the way round the car.")
    s.paint("body", "gloss", colour=WARM_WHITE)
    s.paint("body", "deep navy satin", zone=shapes.below(40))

    s.step("Sidepod tops", "Each sidepod top's own panel matte black, to its edges.",
           words="Both sidepod tops (the flat shelves either side behind the cockpit: the model's own panel there) "
                 "matte black, filled right up to the panel's own edges.")
    s.paint("body", "matte black", zone=meshlines.panel("sidepod top panel 1", both=True))

    s.step("Shoulder band", "A bright orange band 3 cm wide on the front 40 cm of the deck's rounded shoulder, "
           "each side.",
           words="A bright orange band 3 cm wide along the deck's rounded shoulder ... On its FRONT 40 cm only: "
                 "from the end nearest the cockpit (the nose end) running back 40 cm. Both sides alike.")
    shoulder = meshlines.line("body shell roll 5")
    front = shoulder.between(shoulder.at(s=1.5), shoulder.at(s=41.5))   # 1.5 cm in: whole at its nose end
    s.paint("body", "bright orange", zone=front.mirrored().band(3))

    s.step("Roundels and words", "A white disc 20 cm across in a 2 cm navy ring on each rear flank's flat room, "
           "and SEE 22 in black beside it.",
           words="A white disc 20 cm across with a 2 cm navy ring, on each rear flank ... where it sits flat and "
                 "whole, facing out. The words \"SEE 22\" in black, 10 cm tall, on each side near the disc where "
                 "they read flat, reading forward on both sides.")
    ring = s.mark("rear flank", NAVY, marks.disc(), size=24, at=(81, 37, -56))
    s.mark("rear flank", "gloss", marks.disc(), size=20, at=ring.centre, colour=WHITE)
    s.decal("SEE 22", "rear flank", colour="black", height=10, font="teko", at=(72, 48, -76),
            zone=~shapes.sphere(tuple(ring.centre), 13))

    s.step("Deck dots", "Small white discs 4 cm across spread evenly over the engine cover's top, clear of the "
           "game's panels.",
           words="Small white discs 4 cm across scattered evenly over the engine cover's top (the deck behind the "
                 "cockpit), nowhere else, none on the panels the game letters.")
    for x, z in DECK_DOTS:
        s.mark("engine cover|part", "gloss", marks.disc(), size=4, at=(x, None, z), reach=3, colour=WHITE)

    s.step("Nose ring", "An orange ring 25 cm across pressed onto the nose, over the seam it crosses.",
           words="One orange ring 25 cm across pressed onto the nose at about (0, 58, 150), across the seam it "
                 "crosses, on purpose.")
    s.mark("body", "bright orange", marks.ring(0.8), size=25, at=(0, None, 159), across=True)

    s.step("Skirt dots", "Six black dots 3 cm across along the side skirt's long crease, nose end to tail end, "
           "each side.",
           words="Six small black dots 3 cm across, evenly spaced along the long crease that runs low along the "
                 "side skirt from the nose back ... from its nose end to its tail end. Both sides.")
    crease = meshlines.line("side skirt crease 2")
    dots = None
    for k in range(6):
        x, y, z = crease.at(s=1.5 + k * (crease.length - 3) / 5)
        for side in (1, -1):
            d = shapes.sphere((side * x, y, z), 1.5)
            dots = d if dots is None else dots | d
    s.paint("body", "gloss black", zone=dots, across=True)

    s.step("Inner car, wheels, tyres", "The inner car dark grey satin, the wheels gold, a thin white ring on the "
           "tyres' sidewalls; the lights keep their stock glow.",
           words="Gold on the wheels (covers and rims) and a thin white ring on the tyres' sidewalls. The inner "
                 "car dark grey satin. Nothing left in clay; the lights left as stock.")
    s.paint("inner", "dark grey satin")
    s.paint(["wheel covers", "rim"], "gold")
    s.paint("sidewall", "white rubber", zone=shapes.wheel_ring(32.8, 33.6))
