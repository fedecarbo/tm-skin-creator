"""Endurance: dark over light. The top in gloss navy, the sides in silver metallic, the change on the car's edge
(from the inlets to the tail corners, the model's own line along the shoulder, picked on the mesh); amber in the
lights."""
from tool import meshlines, shapes

WORDS = "Endurance (the user's pick of: dark top, light sides, split on the crease)"
NAVY = "#14213d"
SILVER = "#c4c8ce"
AMBER = "#ffae00"
# the model's line along the shoulder, three of its lines end to end (the sidepod's, the rear flank's, the tail
# corner's): of the seven across the rear flank's rounded edge, the one facing 63 degrees from up
EDGE = [(85.33, 55.69, -11.78), (84.68, 56.55, -47.68), (84.6, 56.59, -47.83), (50.55, 60.28, -125.44),
        (50.63, 60.34, -125.58), (48.5, 59.63, -154.51)]


def design(s):
    s.clay()
    s.step("Dark over light", "The sides silver metallic, the top gloss navy, the change on the car's edge; the "
           "underside dark.", words=WORDS)
    s.paint("body", "metallic", colour=SILVER)
    s.paint("sidepod inlet", "metallic", colour=SILVER)  # the inlets' ducts, one colour inside
    # from the inlet to the tail corner the navy stops on the model's line along the shoulder, drawn smooth on the flat
    # texture, carried on under the inlet's frame and on to the fold at the tail corner; elsewhere on the shoulder
    top = meshlines.picked(EDGE).extended(start=3).mirrored().inked_edge(shapes.area("top"), to_fold="both")
    s.paint("body", "gloss", colour=NAVY, zone=top & shapes.outside(0.4))
    s.paint("body", "satin", colour="#1b1d22", zone=shapes.area("under"))

    s.step("Wheels and inner car", "Gunmetal wheels, the inner car dark grey.", words=WORDS)
    s.paint("wheels", "gunmetal")
    s.paint("inner", "dark grey satin")

    s.step("Lights", "Amber speed numbers and wheel rings, red rear lights.", words=WORDS, look="night")
    s.relight("speed numbers", AMBER)
    s.relight("wheel ring", AMBER)
    s.relight("rear lights", "#ff1a10")
