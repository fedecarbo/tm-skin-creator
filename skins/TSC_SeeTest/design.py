"""TSC_SeeTest: a test car whose every stroke has a measurable right place (the brief in notes.md)."""
from tool import marks, meshlines, shapes

# The deck's lattice: rows 6 cm apart, columns 12 cm apart and staggered, kept to the points where a whole 4 cm disc
# sits on the engine cover alone (off the game's two panels and their 3 cm, inside its rolled edge), the left side.
DECK = [(38, -86), (35, -92), (41, -92), (38, -98), (44, -98), (41, -104), (38, -110), (35, -116), (32, -122),
        (38, -122)]


def design(s):
    s.clay()

    s.step("The split", "Warm white above, deep navy satin below, one level line 40 cm off the ground.",
           words="warm white above and deep navy satin below, split by one level line 40 cm off the ground")
    s.paint("body", "ivory")
    s.paint("body", "deep navy satin", zone=shapes.below(40))

    s.step("Sidepod tops", "The model's own sidepod top panel, matte black to its edges, both sides.",
           words="Both sidepod tops ... matte black, filled right up to the panel's own edges")
    s.paint("sidepod top", "matte black", zone=meshlines.panel("sidepod top panel 1", both=True))

    s.step("Shoulder band", "Orange, 3 cm, on the deck's rounded shoulder (body shell roll 2), its front 40 cm.",
           words="A bright orange band 3 cm wide along the deck's rounded shoulder ... its FRONT 40 cm only")
    shoulder = meshlines.line("body shell roll 2", tilt=33).reversed()  # nose first: start (40, 58, 38)
    front = shoulder.between(shoulder.start, shoulder.at(s=40))
    s.paint("body shell", "bright orange", zone=front.mirrored().band(3))

    s.step("Flank discs", "A white disc 20 cm with a 2 cm navy ring on each rear flank, SEE 22 beside it.",
           words="A white disc 20 cm across with a 2 cm navy ring, on each rear flank ... The words \"SEE 22\" in black, 10 cm tall")
    s.mark("rear flank", "white", marks.disc(), size=20, at=(64, 36, -77))  # 3 cm forward of (64, 36, -80): whole at 20
    s.mark("rear flank", "navy", marks.ring(0.8), size=20, at=(64, 36, -77))
    s.decal("SEE 22", "rear flank", colour="black", height=10, at=(80, 31, -54), font="teko", spacing=-0.3)

    s.step("Deck spots", "Small white discs 4 cm, evenly over the engine cover's top, off the game's panels.",
           words="Small white discs 4 cm across scattered evenly over the engine cover's top, nowhere else")
    for x, z in DECK:
        s.mark("engine cover|part", "white", marks.disc(), size=4, at=(x, None, z), reach=0.5)

    s.step("Nose ring", "One orange ring 25 cm on the nose at (0, 58, 150), across the seam on purpose.",
           words="One orange ring 25 cm across pressed onto the nose at about (0, 58, 150), across the seam it crosses")
    s.mark("body", "bright orange", marks.ring(0.76), size=25, at=(0, 58, 150), across=True)

    s.step("Skirt dots", "Six black dots 3 cm along side skirt crease 2, nose end to tail end, both sides.",
           words="Six small black dots 3 cm across, evenly spaced along the long crease that runs low along the side skirt")
    skirt = meshlines.line("side skirt crease 2")  # nose first; the crease is the skirt's rolled lower lip
    dots = None
    for k in range(6):
        p = skirt.at(s=skirt.length * (k + 0.5) / 6)
        for sx in (1, -1):  # the left point and its mirror image
            dot = shapes.sphere((float(p[0]) * sx, float(p[1]), float(p[2])), 1.5)  # a 3 cm dot wrapping the lip
            dots = dot if dots is None else (dots | dot)
    s.paint("side skirt", "black", zone=dots)

    s.step("Wheels, tyres, inner", "Gold wheels, a thin white ring on the sidewalls, the inner car dark grey satin.",
           words="Gold on the wheels (covers and rims) and a thin white ring on the tyres' sidewalls. The inner car dark grey satin")
    s.paint("inner", "dark grey satin")
    s.paint("wheels", "gold")
    s.tyre_marks("TY-65")
