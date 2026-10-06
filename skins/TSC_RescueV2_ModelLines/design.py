"""Rescue v2: the snow rescue car (TSC_Snow) with more detail, on the model's own lines.
Signal orange; black on the car's bottom piece and, on the rear flanks, up to the model's line where the side
turns under, rising round the rear wheel's arch; block tape of silver and orange round the car's contour, on
the model's lines along the nose's lower crease and the shoulder from the sidepods to the tail, a piece on
each panel, none on the nose's tip; silver
chevrons on the tail's deck; NO STEP on the deck and the side box's top, each side, as small boxed
placards; silver hazard stripes across the rear quarter panels; studded snow tyres; amber rear lights."""
from tool import course, meshlines, shapes

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
WITHOUT = "not sure what guides you mean but show me a version without the guides and using the new approach tool"
# The model's own lines (picked on the mesh, tool/meshlines.py), the left side: the tape's, along the nose's lower crease
# from behind the nose tip's seam to where it meets the curve rising in front of the air intake, on straight across the
# surface to the intake's crisp front edge, and along the shoulder (the line facing 47 degrees from up across its rounded
# edge) from the sidepod's front to the tail corner's end; the black's, from the rear flank's front edge where the bottom
# piece's top meets it (note 1: a step there), straight across the surface to the line along the top of the rear flank's
# lower curve, where the side turns under, then along it and up round the front of the rear wheel's arch
NOSE = [(25.5, 46.7, 142.3), (35.0, 53.4, 81.3), (36.4, 52.8, 67.5), (38.9, 54.7, 48.4), (41.5, 55.0, 35.7),
        (47.9, 54.3, 28.2)]
SHOULDER = [(84.4, 57.0, -11.6), (83.7, 57.9, -48.3), (83.6, 57.9, -48.4), (49.6, 61.5, -126.1), (49.7, 61.6, -126.2),
            (47.6, 60.9, -155.1)]
UNDER = [(83.64, 25.97, -24.85), (83.0, 24.0, -38.0), (51.0, 19.0, -91.0), (52.0, 21.0, -94.0), (50.0, 26.0, -130.0)]
SEAMS = ("I wouldn't have it continuous, just leave a bit of gap between seems. (note 15, on the seam between the side box "
         "and the rear flank); Can't see gap here (note 17, at the intake's frame); Very little gap here; Same here very "
         "little gap (notes 19 and 20, at the side box's and the tail corner's seams); In this part remove the tape. "
         "(note 22, on the nose tip)")


def design(s):
    s.clay()
    s.step("Signal orange", "The body in gloss signal orange; gloss black on the bottom piece and, on the rear flanks, "
           "up to the model's line where the side turns under, rising round the rear wheel's arch.", words=WORDS + "; " + WITHOUT)
    s.paint("body", "gloss", colour=ORANGE)
    s.paint("rear flank", "gloss black", zone=meshlines.picked(UNDER).mirrored().inked_edge(shapes.below(26)))
    s.paint("side skirt", "gloss black")  # on round the nose, under the front flank and the nose

    s.step("The tail", "Silver chevrons on the tail's deck, pointing forward.", words=WORDS)
    s.paint("tail panel", "reflective tape", zone=shapes.stripes(4, across=SLANT, edge=-132) & shapes.band(-152, -132))

    s.step("The rear quarter panels", "Silver and orange hazard stripes across the angled panels behind the "
           "cockpit, at the tail chevrons' slant.", words=QUARTER)
    s.paint("rear quarter panel", "reflective tape", zone=shapes.stripes(4, across=SLANT, edge=2.5))

    s.step("The contour tape", "Block tape, two rows of silver and orange blocks 5 cm wide, round the car's contour on "
           "the model's own lines, as a hazard vehicle is outlined, a piece on each panel stopping 3 cm short of every edge, so "
           "6 cm of orange shows across each seam: the nose from its tip's seam back to the air intake, the side box, "
           "the rear flank and the tail corner; none on the nose's tip. The side's big check band is off.",
           words=TAPE + "; " + BAND + "; " + SEAMS + "; " + WITHOUT)
    tape = course.Courses([meshlines.picked(NOSE), meshlines.picked(SHOULDER)], "the car's contour").panels(6)
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
