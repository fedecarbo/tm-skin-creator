"""Rescue v2: the snow rescue car (TSC_Snow) with more detail, shaped by the car's own curvature.
Signal orange; a black lower edge and a band of silver and orange checks that follow the side's
curve, rising with the tail; silver chevrons on the tail's deck; NO STEP on the deck and the side
box's top, each side, as small boxed placards; silver hazard stripes across the rear quarter panels;
studded snow tyres; amber rear lights."""
from tool import levels, seams, shapes

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


def design(s):
    s.clay()
    s.step("Signal orange", "The body in gloss signal orange; below the lowest side level, rising with the tail, "
           "gloss black.", words=WORDS)
    s.paint("body", "gloss", colour=ORANGE)
    s.paint("body", "gloss black", zone=levels.below("between 6") | levels.below("bottom edge"))
    s.paint("side skirt", "gloss black")  # on round the nose, under the front flank and the nose

    s.step("The check band", "Two rows of silver and orange checks along each side between the levels, from the tail "
           "to the front wheel opening, on the body only: the bottom piece keeps its black.", words=WORDS)
    band = levels.band("between 3", "between 6")
    # the band's foot: the sixth level, or the bottom piece's top edge where it rises above it ahead of
    # the sidepods; the rows split halfway, so they stay even there
    foot = levels.higher("between 6", seams.height("side skirt ahead"))
    upper = levels.above(levels.split("between 3", levels.smoothed(foot, 12)))
    blocks = shapes.stripes(15, across="back", edge=72)  # 15 cm blocks along the car, whole from the body's front edge
    s.paint("body", "gloss", colour=ORANGE, zone=band)
    s.paint("body", "reflective tape", zone=band & (upper & blocks | ~upper & ~blocks))

    s.step("The tail", "Silver chevrons on the tail's deck, pointing forward.", words=WORDS)
    s.paint("tail panel", "reflective tape", zone=shapes.stripes(4, across=SLANT, edge=-132) & shapes.band(-152, -132))

    s.step("The rear quarter panels", "Silver and orange hazard stripes across the angled panels behind the "
           "cockpit, at the tail chevrons' slant.", words=QUARTER)
    s.paint("rear quarter panel", "reflective tape", zone=shapes.stripes(4, across=SLANT, edge=2.5))

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
