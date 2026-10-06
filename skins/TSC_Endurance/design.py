"""Endurance: dark over light. The top in gloss navy, the sides in silver metallic, the change on the
car's edge (from the inlets to the tail corners, the edge guide: where the shading divides top from
side); amber in the lights."""
from tool import course, shapes

WORDS = "Endurance (the user's pick of: dark top, light sides, split on the crease)"
NAVY = "#14213d"
SILVER = "#c4c8ce"
AMBER = "#ffae00"


def design(s):
    s.clay()
    s.step("Dark over light", "The sides silver metallic, the top gloss navy, the change on the shoulder's "
           "crest; the underside dark.", words=WORDS)
    s.paint("body", "metallic", colour=SILVER)
    s.paint("sidepod inlet", "metallic", colour=SILVER)  # the inlets' ducts, one colour inside
    # from the inlet to the tail corner the navy stops on the edge guide, where the shading divides top from
    # side, drawn smooth on the flat texture, carried on under the inlet's frame and on to the fold at the tail corner; elsewhere on the shoulder
    top = course.top_line("edge").mirrored().inked_edge(shapes.area("top"), to_fold="both")
    s.paint("body", "gloss", colour=NAVY, zone=top & shapes.outside(0.4))
    s.paint("body", "satin", colour="#1b1d22", zone=shapes.area("under"))

    s.step("Wheels and inner car", "Gunmetal wheels, the inner car dark grey.", words=WORDS)
    s.paint("wheels", "gunmetal")
    s.paint("inner", "dark grey satin")

    s.step("Lights", "Amber speed numbers and wheel rings, red rear lights.", words=WORDS, look="night")
    s.relight("speed numbers", AMBER)
    s.relight("wheel ring", AMBER)
    s.relight("rear lights", "#ff1a10")
