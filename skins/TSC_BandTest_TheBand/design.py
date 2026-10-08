"""TSC_BandTest, take B: the same four tapes laid with the band measured along the car's surface (tool/course.py's
band: its width and side from the distance along the surface), and in orange what only the band does."""
from tool import meshlines

BODY, INNER, TAPE, EXTRA = "#d9d6cf", "#1b1d20", "#3a3d42", "#e0742e"
WORDS = "the road, step 3: bands along a line, the tape beside the band, the eye picks"


def lines():
    """Four of the car's own lines, the kinds the tapes failed on: the skirts' crisp edges, the body's lower edge back
    to the rear wheels, the cockpit's outline and the intakes' lips."""
    skirt = meshlines.line((39, 19, 70)).mirrored()
    low = meshlines.line((60, 16.5, -60), kind="opening").between((80, 22, 5), (45, 17, -105)).mirrored()
    crest = meshlines.line((0, 83, -51))
    lips = meshlines.line((75, 49, -45)).mirrored()
    return skirt, low, crest, lips


def base(s):
    s.clay()
    s.step("The body", "One pale satin over the body, the inner car dark, the wheels gunmetal.", words=WORDS)
    s.paint("body", "satin", colour=BODY)
    s.paint("inner", "matte plastic", colour=INNER)
    s.paint("wheels", "gunmetal")


def design(s):
    base(s)
    s.step("The bands", "Dark grey, 4 cm wide, on the face the eye sees beside four of the car's own lines: the "
           "skirts' crisp edges, the lower edge back to the rear wheels, the cockpit's outline, the intakes' lips. "
           "Laid with the band, measured along the car's surface.", words=WORDS)
    skirt, low, crest, lips = lines()
    for c in (skirt, low, crest):
        s.paint("body", "satin", colour=TAPE, zone=c.band(4, side="seen"))
    s.paint("body", "satin", colour=TAPE, zone=lips.band(4, side="seen"), across=True)
    s.step("What only the band does", "In orange: a 3 cm band wrapping the rear flank's rolled shoulder, both sides, "
           "and a 6 cm band inside the sidepod top's outline that stops at the top's crease instead of running over it.",
           words=WORDS)
    s.paint("body", "satin", colour=EXTRA, zone=meshlines.line((64, 61, -84), kind="rounded").between(-57, -84).mirrored().band(3))
    s.paint("body", "satin", colour=EXTRA, zone=meshlines.line((82, 59, -49)).mirrored().band(6, side=1, crease=True))
