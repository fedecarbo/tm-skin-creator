"""Rescue v2: the snow rescue car (TSC_Snow) with more detail, shaped by the car's own curvature.
Signal orange; a black lower edge that follows the side's curve, rising with the tail; block tape of
silver and orange round the car's contour, along its top line from the nose to the tail, a piece on
each panel, none on the nose's tip; silver
chevrons on the tail's deck; NO STEP on the deck and the side box's top, each side, as small boxed
placards; silver hazard stripes across the rear quarter panels; studded snow tyres; amber rear lights."""
from tool import course, levels, shapes

WORDS = "based on what you know can you design a skin or use the Rescue as a v2, to add more details"
ORANGE, AMBER = "#ff5a0f", "#ffb000"
SLANT = (0.75, 0, 1)  # the chevrons' and the hazard stripes' direction: falling back 0.75 cm per cm out from the middle
NOTES = ("Do an interval lines with DO NOT STEP text. (note 4, a line along the deck's left edge); right side "
         "too ... added more continueous do not step; Continue the do not step (note 5, round the side box's top); "
         "it should actually be NO STEP; Remove the dashes, only include certain spots for no step. (note 7)")
# Each placard's middle on the car's left (x, z; the right mirrors it) and its slant: on the deck beside
# the rear flank's seam, where the user's arrow pointed (note 10), reading along the seam (34 degrees off
# the car's length there); on the side box's top beside its inner edge, where the user drew (note 5).
SIGNS = (((63.3, -68.2), 34), ((53.0, -22.0), 0))
QUARTER = "What can we do here in this piece? (note 11, on the right rear quarter panel)"
TAPE = ("Include a tape like pattern here (note 13, a line drawn along the top of the left rear flank, which runs "
        "along the top line); picked block tape; Maybe include the tape around the car, you can be the judge on how to "
        "distribute it so that it looks like a hazard car")
BAND = "Remove this one (note 1 on the block tape's take, on the side's check band)"
SEAMS = ("I wouldn't have it continuous, just leave a bit of gap between seems. (note 15, on the seam between the side box "
         "and the rear flank); Can't see gap here (note 17, at the intake's frame); Very little gap here; Same here very "
         "little gap (notes 19 and 20, at the side box's and the tail corner's seams); In this part remove the tape. "
         "(note 22, on the nose tip)")


def design(s):
    s.clay()
    s.step("Signal orange", "The body in gloss signal orange; below the lowest side level, rising with the tail, "
           "gloss black.", words=WORDS)
    s.paint("body", "gloss", colour=ORANGE)
    s.paint("body", "gloss black", zone=levels.below("between 6") | levels.below("bottom edge"))
    s.paint("side skirt", "gloss black")  # on round the nose, under the front flank and the nose

    s.step("The tail", "Silver chevrons on the tail's deck, pointing forward.", words=WORDS)
    s.paint("tail panel", "reflective tape", zone=shapes.stripes(4, across=SLANT, edge=-132) & shapes.band(-152, -132))

    s.step("The rear quarter panels", "Silver and orange hazard stripes across the angled panels behind the "
           "cockpit, at the tail chevrons' slant.", words=QUARTER)
    s.paint("rear quarter panel", "reflective tape", zone=shapes.stripes(4, across=SLANT, edge=2.5))

    s.step("The contour tape", "Block tape, two rows of silver and orange blocks 5 cm wide, round the car's contour on "
           "its top line, as a hazard vehicle is outlined, a piece on each panel stopping 3 cm short of every edge, so "
           "6 cm of orange shows across each seam: the nose from its tip's seam back to the air intake, the side box, "
           "the rear flank and the tail corner; none on the nose's tip. The side's big check band is off.",
           words=TAPE + "; " + BAND + "; " + SEAMS)
    tape = course.around("top edge").panels(6).without("nose tip")
    s.paint("body", "reflective tape", zone=tape.mirrored().blocks(5, 2.5))

    s.step("No step", "NO STEP in black on each side, a small placard with a thin black box round the words, facing "
           "outward: on the deck beside the rear flank's seam, where the user's arrow pointed, reading along the "
           "seam; and on the side box's top beside its inner edge, where the user drew the line.",
           words=NOTES + "; NO STEP as a small placard ... Try it?: yes (note 9)")
    for (x, z), slant in SIGNS:
        s.placard("NO STEP", "body shell", at=(x, None, z), colour="black", font="teko", weight=600, height=2.6,
                  pad=0.3, frame=0.2, turn=slant)

    s.step("Wheels and inner car", "Black wheels with orange rings, studded snow tyres, the inner car and the inlets' "
           "insides dark grey, black frames round the inlets.", words=WORDS)
    s.paint("wheels", "satin black")
    s.paint("wheel cover ring", "gloss", colour=ORANGE)
    s.tyre_tread("TR-08")
    s.paint("inner", "dark grey satin")
    s.paint("sidepod inlet", "dark grey satin")
    s.paint("sidepod frame", "gloss black")

    s.step("Lights", "Orange speed numbers and wheel lights; amber rear lights (red when braking).", words=WORDS,
           look="rear night")
    s.relight("speed numbers", ORANGE)
    s.relight("rear lights", AMBER)
    s.relight("wheel ring", ORANGE, keep_level=True)
