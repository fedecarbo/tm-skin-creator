"""Ensign: a navy racing car with ivory panels and the roundels and stars of a squadron's insignia.
Gloss navy body; the car's own panels (the nose panel, the sidepod tops, the rear quarter panels,
the tail panel) in ivory; a navy-ivory-red roundel on each rear quarter panel and on the tail; a
red badge with an ivory star on each sidepod top; an ivory star on the bonnet; a red ring on the
nose panel; an ivory number roundel on each rear flank, a row of three red mission marks above it;
carbon skirts, diffuser and wing pylons; gunmetal wheels; ivory speed numbers, red rear lights."""
from tool import marks

WORDS = "sure test car, send an agent?"
NAVY, IVORY, RED = "#14213d", "#f2ead8", "#d7263d"


def design(s):
    s.clay()
    s.step("Navy and ivory", "The body in gloss navy; the nose panel, the sidepod tops, the rear quarter panels "
           "and the tail panel in ivory, each the car's own panel; the skirts, the diffuser and the wing pylons "
           "in carbon; the inlets' insides dark grey.", words=WORDS)
    s.paint("body", "gloss", colour=NAVY)
    for panel in ("nose panel", "sidepod top", "rear quarter panel", "tail panel"):
        s.paint(panel, "gloss", colour=IVORY)
    s.paint(["side skirt", "diffuser", "diffuser strake", "wing pylon"], "gloss carbon")
    s.paint("sidepod inlet", "dark grey satin")

    s.step("The roundels", "A navy, ivory and red roundel on each rear quarter panel, where the panel has most "
           "room, and a bigger one on the middle of the tail panel.", words=WORDS, look="rear")
    r = s.mark("rear quarter panel", "gloss", marks.disc(), size=14, colour=NAVY)
    s.mark("rear quarter panel", "gloss", marks.disc(), size=0.62 * r.size, at=r.centre, colour=IVORY)
    s.mark("rear quarter panel", "gloss", marks.disc(), size=0.30 * r.size, at=r.centre, colour=RED)
    t = s.mark("tail panel", "gloss", marks.disc(), size=22, at=(0, None, -146), colour=NAVY)
    s.mark("tail panel", "gloss", marks.disc(), size=0.62 * t.size, at=t.centre, colour=IVORY)
    s.mark("tail panel", "gloss", marks.disc(), size=0.30 * t.size, at=t.centre, colour=RED)

    s.step("Badges and stars", "A red badge with an ivory star at the back of each sidepod top; an ivory star on "
           "the bonnet behind the nose fin; a red ring on the nose panel.", words=WORDS)
    b = s.mark("sidepod top", "gloss", marks.disc(), size=14, at=(70, None, -46), colour=RED)
    s.mark("sidepod top", "gloss", marks.star(5), size=0.55 * b.size, at=b.centre, colour=IVORY)
    s.mark("body shell", "gloss", marks.star(5), size=20, at=(0, None, 112), colour=IVORY)
    s.mark("nose panel", "gloss", marks.ring(0.55), size=17, at=(0, None, 158), colour=RED)

    s.step("The flanks", "An ivory number roundel on each rear flank's waist, and a row of three red mission "
           "marks above it, the first against the sidepod's back edge, the others 11 cm apart behind it.",
           words=WORDS)
    s.mark("rear flank", "gloss", marks.disc(), size=22, colour=IVORY)
    first = s.mark("rear flank", "gloss", marks.disc(), size=5, at=(None, 56, -50), colour=RED)
    for k in (1, 2):
        s.mark("rear flank", "gloss", marks.disc(), size=5, at=(None, 56, first.centre[2] - 11 * k), colour=RED)

    s.step("Wheels and inner car", "Gunmetal wheel covers with satin black hubs; the inner car dark grey.",
           words=WORDS)
    s.paint("wheels", "gunmetal")
    s.paint("wheel cover hub", "satin black")
    s.paint("inner", "dark grey satin")
    s.glass("smoke", 0.3)

    s.step("Lights", "Ivory speed numbers; red rear lights, brake lights and wheel lights.", words=WORDS,
           look="rear night")
    s.relight("speed numbers", IVORY)
    s.relight("rear lights", "#ff2d1a")
    s.relight("brake lights", "#ff2d1a")
    s.relight("wheel ring", RED, keep_level=True)
