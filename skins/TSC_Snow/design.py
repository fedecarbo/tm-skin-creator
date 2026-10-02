"""Rescue: a car that stands out on snow. Signal orange, a black lower edge, a silver
reflective band along each side and RESCUE on the rear flanks."""
from tool import shapes

WORDS = "I want a car that will be used for snow maps."
ORANGE = "#ff5a0f"


def design(s):
    s.clay()
    s.step("Signal orange", "The body in gloss signal orange, the lower edge in gloss black.", words=WORDS)
    s.paint("body", "gloss", colour=ORANGE)
    s.paint("body", "gloss black", zone=shapes.below(22))

    s.step("Reflective band", "A silver reflective band along each side, RESCUE on the rear flanks.", words=WORDS)
    # the map's sides miss two thin strips on the sidepod's outer face: the sideways-facing skin fills them
    flank = shapes.area("sides") | (shapes.sides(0.3) & shapes.band(z0=-50, z1=0))
    s.paint("body", "reflective tape", zone=flank & shapes.above(27) & shapes.below(36) & shapes.behind(40))
    for spot in ("left side", "right side"):
        s.text("RESCUE", spot, colour="black", font="russo", height=9, italic=0.15)

    s.step("Wheels and inner car", "Black wheels with orange rings, the inner car dark grey, black frames round the inlets.", words=WORDS)
    s.paint("wheels", "satin black")
    s.paint("wheel cover ring", "gloss", colour=ORANGE)
    s.paint("inner", "dark grey satin")
    s.paint("sidepod frame", "gloss black")

    s.step("Lights", "Orange speed numbers.", words=WORDS,
           look="night")
    s.relight("speed numbers", ORANGE)
