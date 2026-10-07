"""TSC_EnduranceRacer: a test car for the eye (2026-10-07), an endurance racer: one bold body colour, a stripe sweeping
along each flank with a thin pinstripe beside it, a round number disc. To be scrapped at the end of the test."""

from tool import marks, meshlines

BODY = "#1840c4"    # cobalt
STRIPE = "#f3f1ea"  # off-white
PIN = "#ff6a13"     # orange
BLACK = "#0b0b0d"


def design(s):
    s.clay()

    s.step("The colour", "The whole body in a deep cobalt, glossy; the inner car satin black.",
           words="one bold body colour")
    s.paint("body", "gloss", colour=BODY)
    s.paint("inner", "satin", colour=BLACK)

    s.step("The sweep", "An off-white stripe along each flank, beside one of the model's lines whole: it rises from low "
           "on the front flank onto the shoulder and runs back towards the deck; a thin orange pinstripe beside it.",
           words="a stripe sweeping along each flank with a thin pinstripe beside it")
    sweep = meshlines.line((46, 62, 17), kind="rounded")  # 146 cm, from (39, 30, 47) up to the shoulder and back to z -82
    # on its inner side, where the front flank has room (on its outer side the body ends 7 cm out at the inlet), both
    # stripes kept to the body shell's own panel: they start on the side skirt's panel line and end on the rear
    # quarter panel's
    shell = meshlines.panel((42.7, 64, 9.1), both=True)  # the body shell's flank, under the stripe
    # carried on 3 cm for the panel to end it on the engine cover's line (it stopped 0.6 cm short of it)
    s.paint("body", "gloss", colour=STRIPE, zone=sweep.extended(end=3).offset(4).mirrored().strip(6) & shell)
    s.paint("body", "gloss", colour=PIN, zone=sweep.offset(8.6).mirrored().strip(0.8) & shell)

    s.step("The number", "A white disc on each sidepod's flank, where it's flat, with a black number on it.",
           words="a round number disc")
    disc = s.mark("sidepod top", "gloss", marks.disc(), size=24, at=(87, 42, -24), colour=STRIPE)
    for spot in (disc, disc.twin):
        s.text("7", spot, colour=BLACK, height=0.6 * disc.size)

    s.step("The wheels", "The wheel covers in the body's cobalt, the rims and hubs black.", words="one bold body colour")
    s.paint("wheel covers", "gloss", colour=BODY)
    s.paint(["rim", "hub"], "satin", colour=BLACK)

    s.step("The lights", "The car's own lights in the pinstripe's orange.", look="rear night")
    for light in ("speed numbers", "rear lights", "brake lights"):
        s.relight(light, PIN)
