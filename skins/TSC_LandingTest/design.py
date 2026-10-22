"""TSC_LandingTest: a throwaway test car for the road's step 15 (2026-10-22). Three strokes are planted in the wrong
place on purpose, each to be caught by `PY -m tool.skin read` before any paint: the bonnet stripe written at the
cockpit's far side, the sidepod tops' black zoned on the wrong parts, a badge behind the rear wheel."""
from tool import marks, meshlines, shapes


def design(s):
    s.clay()
    s.step("The split", "Warm white above, deep navy satin below, a level line 40 cm off the ground.",
           words="warm white above and deep navy below, split at 40 cm")
    s.paint("body", "gloss", colour="#efe8d8")
    s.paint("body", "satin", colour="#141e3c", zone=shapes.below(40))
    s.step("The bonnet stripe", "A bright orange stripe 3 cm wide across the bonnet, 10 cm in front of the cockpit "
           "opening's front (z 85), so at z 95 to 98.", words="an orange stripe across the bonnet just in front of the cockpit")
    s.paint("body", "gloss", colour="bright orange", zone=shapes.band(-98, -95))  # PLANTED: the cockpit's far side
    s.step("Sidepod tops", "Both sidepod tops matte black, filled right up to the panel's edges.",
           words="the sidepod tops matte black")
    s.paint("rear flank", "matte black", zone=meshlines.panel("sidepod top panel 1", both=True))  # PLANTED: the wrong parts
    s.step("Flank badges", "A white disc 20 cm across on each rear flank, around (64, 36, -80) on the left.",
           words="a white disc on each rear flank")
    s.mark("rear flank", "gloss", marks.disc(), size=20, at=(64, 36, -80), colour="white")  # PLANTED: behind the rear wheel
    s.step("Wheels and inner", "Gold wheels, the inner car dark grey satin.", words="gold wheels, dark grey inside")
    s.paint("inner", "dark grey satin")
    s.paint("wheels", "gold")
