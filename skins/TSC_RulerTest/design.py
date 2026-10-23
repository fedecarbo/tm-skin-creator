"""TSC_RulerTest: a throwaway test car for the road's step 16 (2026-10-22). Four things for the judge to name its ruler
on and to see the bites it couldn't: a strip beside a crisp line with a gap planted (the finding names the line it was
read against, and how far that is from the design's course); rows of dots at a course's places, one row inside the
sidepod's inlet and a dot behind the rear wheel (a check and a close look over each); the nose ring pressed over the
nose panel's step and the shoulder badge over the rear flank's groove (the bites measured, then fixed in the chart)."""
from tool import marks, meshlines, shapes

BASE, INK, GOLD, ORANGE = "#d9d6cf", "#141414", "#e0a82e", "bright orange"


def design(s):
    s.clay()
    s.step("Base", "The body pale satin, the inner car dark.", words="a pale car")
    s.paint("body", "satin", colour=BASE)
    s.paint("inner", "dark grey satin")
    s.step("Strip beside the crease", "A 1 cm strip 1 cm beside the side skirt's crease 3, both sides, with a 2 cm gap "
           "planted at z 60.", words="a thin dark line just above the skirt's lower crease")
    beside = meshlines.line("side skirt crease 3").offset(1.0)
    s.paint("body", "satin", colour=INK, zone=beside.mirrored().strip(1.0) & ~shapes.band(59, 61))  # PLANTED: the gap
    s.step("Taps", "Rows of 2 cm dots: along the sidepod inlet's crisp line (inside the inlet), along the side skirt's "
           "long crease, and one dot behind the rear wheel. Both sides.",
           words="small dark dots like pressure taps along the inlet and along the skirt")
    for name, every in (("sidepod inlet crease 1", 10), ("side skirt crease 2", 25)):
        c = meshlines.line(name)
        dots = None
        for x, y, z in c.places(every=every):
            for side in (1, -1):
                d = shapes.sphere((side * x, y, z), 1.0)
                dots = d if dots is None else dots | d
        s.paint("body", "satin", colour=INK, zone=dots, across=True)
    s.paint("body", "satin", colour=INK, zone=shapes.sphere((70, 49, -77), 1.5) | shapes.sphere((-70, 49, -77), 1.5),
            across=True)  # PLANTED: behind the rear wheel
    s.step("Nose ring", "An orange ring 25 cm across pressed onto the nose at (0, ?, 150), onto the nose fin's plate.",
           words="an orange ring on the nose, over the seam on purpose")
    s.mark("body", "satin", marks.ring(0.8), size=25, at=(0, None, 150), colour=ORANGE, across=True)
    s.step("Shoulder badge", "A gold ring 16 cm across pressed over the rear flank's rolled shoulder at z -68, where the "
           "flank's groove crosses it, both sides.", words="a gold ring badge over the shoulder, across the edge")
    shoulder = meshlines.line("rear flank roll 2", tilt=47)
    s.mark("body", "satin", marks.ring(0.82), size=16, at=shoulder.at(z=-68), colour=GOLD, across=True)
    s.step("Wheels", "Gold wheels.", words="gold wheels")
    s.paint("wheels", "gold")
