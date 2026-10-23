"""TSC_IntentTest: a throwaway test car for the road's step 17 (2026-10-22). The user's picture of the notched ring,
again: a choice and two accidents on the same graphics, for a page to tell apart stroke by stroke. The nose ring
crosses the nose fin's plate on purpose (across=True, the step's words say so) and blocks for a third reason, its
paint within a few cm of the plate the game letters; the shoulder badge crosses the rear flank's rolled edge on purpose
and the tool chips it (the queue's 0.3 cm jog); the skirt's line is meant plain, and the judge's findings on it stay on
its own stroke."""
from tool import marks, meshlines

BASE, INK, GOLD, ORANGE = "#d9d6cf", "#141414", "#e0a82e", "bright orange"


def design(s):
    s.clay()
    s.step("Base", "The body pale satin, the inner car dark.", words="a pale car")
    s.paint("body", "satin", colour=BASE)
    s.paint("inner", "dark grey satin")
    s.step("Skirt line", "A 1 cm dark line 1 cm above the side skirt's lower crease, both sides.",
           words="a thin dark line along the skirt")
    s.paint("body", "satin", colour=INK, zone=meshlines.line("side skirt crease 3").offset(1.0).mirrored().strip(1.0))
    s.step("Nose ring", "An orange ring 25 cm across pressed onto the nose at z 150, over the nose fin's plate.",
           words="an orange ring on the nose, over the seam on purpose")
    s.mark("body", "satin", marks.ring(0.8), size=25, at=(0, None, 150), colour=ORANGE, across=True)
    s.step("Shoulder badge", "A gold ring 16 cm across pressed over the rear flank's rolled shoulder at z -68, both "
           "sides.", words="a gold ring badge over the shoulder, across the edge")
    shoulder = meshlines.line("rear flank roll 2", tilt=47)
    s.mark("body", "satin", marks.ring(0.82), size=16, at=shoulder.at(z=-68), colour=GOLD, across=True)
    s.step("Wheels", "Gold wheels.", words="gold wheels")
    s.paint("wheels", "gold")
