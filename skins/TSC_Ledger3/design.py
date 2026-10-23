"""TSC_Ledger3: a throwaway test car for the road's step 18 (2026-10-22), the third of three different cars that share
two plain strokes a real design might write (a thin line along the skirt, a ring badge over the rear flank's shoulder):
the ledger queues the tool's accidents on them here. Racing green and cream, with one mistake of its own, kept: a cream
ring pressed over the nose fin's plate, which the game letters (the judge must still block it: it's this design's)."""
from tool import marks, meshlines

GREEN, CREAM = "#1f4d36", "#efe6cf"


def design(s):
    s.clay()
    s.step("Base", "The body racing green satin, the inner car dark grey.", words="a racing green car")
    s.paint("body", "satin", colour=GREEN)
    s.paint("inner", "dark grey satin")
    s.step("Skirt line", "A 1 cm cream line 1 cm above the side skirt's lower crease, both sides.",
           words="a thin cream line along the skirt")
    s.paint("body", "satin", colour=CREAM, zone=meshlines.line("side skirt crease 3").offset(1.0).mirrored().strip(1.0))
    s.step("Shoulder badge", "A cream ring 16 cm across pressed over the rear flank's rolled shoulder at z -68, both "
           "sides.", words="a cream ring badge over the shoulder, across the edge")
    shoulder = meshlines.line("rear flank roll 2", tilt=47)
    s.mark("body", "satin", marks.ring(0.82), size=16, at=shoulder.at(z=-68), colour=CREAM, across=True)
    s.step("Nose ring", "A cream ring 25 cm across pressed onto the nose at z 150, over the nose fin's plate.",
           words="a cream ring on the nose")
    s.mark("body", "satin", marks.ring(0.8), size=25, at=(0, None, 150), colour=CREAM, across=True)
    s.step("Wheels", "Cream wheels.", words="cream wheels")
    s.paint("wheels", "satin", colour=CREAM)
