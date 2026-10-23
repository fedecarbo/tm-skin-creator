"""TSC_Ledger2: a throwaway test car for the road's step 18 (2026-10-22), one of three different cars that share two
plain strokes a real design might write (a thin line along the skirt, a ring badge over the rear flank's shoulder), for
the ledger to find the tool's accidents on them car after car. White over navy, split level 40 cm off the ground."""
from tool import marks, meshlines, shapes

WHITE = "#f2f0ea"


def design(s):
    s.clay()
    s.step("Two tones", "White gloss above, deep navy satin below, split level 40 cm off the ground all round.",
           words="white over navy")
    s.paint("body", "gloss", colour=WHITE)
    s.paint("body", "deep navy satin", zone=shapes.below(40))
    s.paint("inner", "dark grey satin")
    s.step("Skirt line", "A 1 cm white line 1 cm above the side skirt's lower crease, both sides.",
           words="a thin white line along the skirt")
    s.paint("body", "gloss", colour=WHITE, zone=meshlines.line("side skirt crease 3").offset(1.0).mirrored().strip(1.0))
    s.step("Shoulder badge", "A navy ring 16 cm across pressed over the rear flank's rolled shoulder at z -68, both "
           "sides.", words="a navy ring badge over the shoulder, across the edge")
    shoulder = meshlines.line("rear flank roll 2", tilt=47)
    s.mark("body", "deep navy satin", marks.ring(0.82), size=16, at=shoulder.at(z=-68), across=True)
    s.step("Wheels", "Gold wheels.", words="gold wheels")
    s.paint("wheels", "gold")
