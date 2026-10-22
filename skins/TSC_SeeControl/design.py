"""TSC_SeeControl: a test car; every stroke of the brief has a measurable right place (2026-10-22)."""

from PIL import Image, ImageDraw

from tool import marks, meshlines, shapes

WHITE = "warm white"
NAVY = "deep navy"
ORANGE = "bright orange"


def white_disc(px=256):
    """A plain white disc, the picture `scatter` sprinkles."""
    im = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse((1, 1, px - 2, px - 2), fill=(244, 244, 242, 255))
    return im


def design(s):
    s.clay()

    s.step("The split", "The whole body warm white above and deep navy satin below one level line 40 cm off the "
           "ground, all the way round, across every part.",
           words="The whole body warm white above and deep navy satin below, split by one level line 40 cm off the "
                 "ground, all the way round the car.")
    s.paint("body", "gloss", colour=WHITE)
    s.paint("body", "satin", colour=NAVY, zone=shapes.below(40), across=True)

    s.step("The sidepod shelves", "Both sidepod tops matte black, the model's own panel filled right up to its lines.",
           words="Both sidepod tops (the flat shelves either side behind the cockpit: the model's own panel there) "
                 "matte black, filled right up to the panel's own edges.")
    s.paint("sidepod top", "matte black", zone=meshlines.panel("sidepod top panel 1", both=True))

    s.step("The shoulder band", "A bright orange band 3 cm wide centred on the model's line along the deck's rounded "
           "shoulder (body shell roll 5, the line tilted 40 degrees, the nearest to (40, 62, -20)), its front 40 cm "
           "only: from its front end, nearest the cockpit, back 40 cm along the surface. Both sides.",
           words="A bright orange band 3 cm wide along the deck's rounded shoulder ... On its FRONT 40 cm only: from "
                 "the end nearest the cockpit (the nose end) running back 40 cm. Both sides alike.")
    shoulder = meshlines.line("body shell roll 5", tilt=40)
    # the band's field is read from the line carried 3 cm on before its start, and the band cut square at the
    # line's own start by a plane there (each side its own), so its front end is clean where the line begins
    lead = 3.0
    carried = shoulder.extended(start=lead)
    front = carried.between(carried.start, carried.at(s=lead + 40)).mirrored()
    start, tan = [float(v) for v in shoulder.start], [float(v) for v in shoulder.tan[0]]
    flip = lambda v: (-v[0], v[1], v[2])
    from_start = (shapes.left() & shapes.plane(start, tan)) | (shapes.right() & shapes.plane(flip(start), flip(tan)))
    s.paint("body shell", "gloss", colour=ORANGE, zone=front.band(3) & from_start)

    s.step("The discs", "A white disc 20 cm across on each rear flank at (64, 36, -80), its outer 2 cm a deep navy ring.",
           words="A white disc 20 cm across with a 2 cm navy ring, on each rear flank (the big side panel behind the "
                 "sidepod, around (64, 36, -80) on the left), where it sits flat and whole, facing out.")
    disc = s.mark("rear flank", "gloss", marks.disc(), size=20, at=(64, 36, -80), colour=WHITE, across=True)
    s.mark("rear flank", "satin", marks.ring(0.8), size=20, at=disc.centre, colour=NAVY, across=True)

    s.step("The words", "SEE 22 in black capitals, 10 cm tall where they fit, on each rear flank's lower face between the "
           "sidepod's back and the disc, 1.5 cm clear of it (the flank behind the disc is hidden by the rear wheel), "
           "reading forward on both sides.",
           words='The words "SEE 22" in black, 10 cm tall, on each side near the disc where they read flat, reading '
                 "forward on both sides.")
    # the only flat face in the open air near the disc is the flank's lower face ahead of it, from the sidepod's back
    # (z -37) to the disc's edge (z -70): 10 cm words are 48 cm long, so they're held to that room and shrink to fit it
    s.decal("SEE 22", "rear flank", colour="black", height=10, at=(83, 31, -52),
            zone=shapes.behind(-37.5) & shapes.front_of(-68.5))

    s.step("The deck's spots", "White discs 4 cm across scattered evenly over the engine cover's top, 10 cm apart, "
           "off the panels the game letters.",
           words="Small white discs 4 cm across scattered evenly over the engine cover's top (the deck behind the "
                 "cockpit), nowhere else, none on the panels the game letters.")
    s.scatter(white_disc(), "engine cover|part", size=4, spacing=10, turn="length", finish="gloss", seed=4)

    s.step("The nose ring", "One bright orange ring 25 cm across, 3 cm thick, pressed onto the nose at (0, 58, 150) as "
           "it is, over every seam in its footprint.",
           words="One orange ring 25 cm across pressed onto the nose at about (0, 58, 150), across the seam it "
                 "crosses, on purpose.")
    s.mark("body", "gloss", marks.ring(0.76), size=25, at=(0, 58, 150), colour=ORANGE, across=True)

    s.step("The skirt's dots", "Six black dots 3 cm across centred on the side skirt's long crease (side skirt crease 2, the fold "
           "at the skirt's lip), evenly spaced from its nose end to its tail end, the first and last 1.5 cm in from the "
           "ends, each a sphere's cut of the surface. Both sides.",
           words="Six small black dots 3 cm across, evenly spaced along the long crease that runs low along the side "
                 "skirt from the nose back (through about (39, 19, 70) on the left), from its nose end to its tail "
                 "end. Both sides.")
    # the crease is the fold at the skirt's lip, where its top face turns under: a dot centred on it is a 3 cm disc
    # cut from the surface by a sphere (1.5 cm round the point), so it wraps the fold whole and sits exactly there
    crease = meshlines.line("side skirt crease 2")
    step = (crease.length - 3.0) / 5
    for k in range(6):
        p = tuple(float(v) for v in crease.at(s=1.5 + k * step))
        s.paint("side skirt", "matte black", zone=shapes.sphere(p, 1.5) | shapes.sphere((-p[0], p[1], p[2]), 1.5))

    s.step("Wheels, tyres and the inner car", "The wheel covers and rims gold; a thin white ring, 1 cm wide, round "
           "each tyre's sidewall 33 cm from the axle; the inner car dark grey satin. The lights as stock.",
           words="Gold on the wheels (covers and rims) and a thin white ring on the tyres' sidewalls. The inner car "
                 "dark grey satin. Nothing left in clay; the lights left as stock.")
    s.paint("inner", "dark grey satin")
    s.paint("wheels", "gold")
    s.paint("sidewall", "white rubber", zone=shapes.wheel_ring(33.0, 34.0))
