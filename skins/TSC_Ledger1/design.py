"""TSC_Ledger1: a throwaway test car for the road's step 18 (2026-10-22), one of three different cars that share two
plain strokes a real design might write (a thin line along the skirt, a ring badge over the rear flank's shoulder), for
the ledger to find the tool's accidents on them car after car. Graphite and orange, the sidepod tops orange."""
from tool import marks, meshlines

BASE, ORANGE = "#2b2d30", "#ff7a1a"


def design(s):
    s.clay()
    s.step("Base", "The body graphite satin, the inner car dark grey.", words="a graphite car")
    s.paint("body", "satin", colour=BASE)
    s.paint("inner", "dark grey satin")
    s.step("Sidepod tops", "Each sidepod top's own panel orange, to its edges.", words="orange sidepod tops")
    s.paint("body", "satin", colour=ORANGE, zone=meshlines.panel("sidepod top panel 1", both=True))
    s.step("Skirt line", "A 1 cm orange line 1 cm above the side skirt's lower crease, both sides.",
           words="a thin orange line along the skirt")
    s.paint("body", "satin", colour=ORANGE, zone=meshlines.line("side skirt crease 3").offset(1.0).mirrored().strip(1.0))
    s.step("Shoulder badge", "An orange ring 16 cm across pressed over the rear flank's rolled shoulder at z -68, both "
           "sides.", words="an orange ring badge over the shoulder, across the edge")
    shoulder = meshlines.line("rear flank roll 2", tilt=47)
    s.mark("body", "satin", marks.ring(0.82), size=16, at=shoulder.at(z=-68), colour=ORANGE, across=True)
    s.step("Wheels", "Dark grey wheels.", words="dark wheels")
    s.paint("wheels", "dark grey satin")
