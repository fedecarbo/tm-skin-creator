"""TSC_StrokesInLab: a throwaway test car for the road's step 20 (2026-10-22), the Lab showing each step's strokes. Each
kind of stroke the Lab tells apart, planted: plain strokes nothing is found on, a line the ledger knows as the tool's
(K1), a roundel across the nose fin's seam on purpose that also lands on the nose fin's plate (meant, and an accident),
a line round the rear arches a tyre hides (the eye's notes), dots a rear tyre stands in front of (an accident). Deep
green and cream."""
from tool import marks, meshlines

GREEN, CREAM = "#1f4d3a", "#efe6d0"


def design(s):
    s.clay()
    s.step("Base", "The body deep green satin, the inner car dark grey.", words="a deep green car")
    s.paint("body", "satin", colour=GREEN)
    s.paint("inner", "dark grey satin")
    s.step("Skirt line", "A 1 cm cream line 1 cm above the side skirt's lower crease, both sides.",
           words="a thin cream line along the skirt")
    s.paint("body", "satin", colour=CREAM, zone=meshlines.line("side skirt crease 3").offset(1.0).mirrored().strip(1.0))
    s.step("Nose roundel", "A cream ring 24 cm across pressed onto the nose at z 150, across the nose fin's seam.",
           words="a cream roundel on the nose, across the fin's seam")
    s.mark("body", "satin", marks.ring(0.8), size=24, at=(0, None, 150), colour=CREAM, across=True)
    s.step("Arch line", "A 1 cm cream line along the rear flank's crease round the rear wheel's arch, both sides.",
           words="a thin cream line round the rear wheel arches")
    s.paint("body", "satin", colour=CREAM, zone=meshlines.line("rear flank crease 3").mirrored().strip(1.0))
    s.step("Flank dots", "A cream dot 10 cm across on each rear flank at z -80.", words="a cream dot on each rear flank")
    s.mark("rear flank", "satin", marks.disc(), size=10, at=(64, 36, -80), colour=CREAM)
    s.step("Wheels", "Cream wheels.", words="cream wheels")
    s.paint("wheels", "satin", colour=CREAM)
