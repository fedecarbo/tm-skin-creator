"""TSC_StealthBomber, take C, the sheen: one grey all over, the car's own outer panels (the sidepod tops, the rear
flanks, the side skirts, the rear quarter panels, the tail corners) in satin and the rest matte, so its form shows
only as the light moves (the composition, from its visual language: language.json)."""

from tool import meshlines

SKIN, TAPE, HOLE, GOLD = "#3f4348", "#565b61", "#1b1d20", "#c9a24a"  # the language's colours
WORDS = "do a stealth bomber"


def base(s):
    """The skin, the openings, the gear and the canopy: the same in every take."""
    s.clay()
    s.step("The skin", "Bomber grey, matte, all over; black inside the intakes and the inner car; the gear dark "
           "gunmetal; the canopy's gold coating.", words=WORDS)
    s.paint("body", "matte", colour=SKIN)
    s.paint("sidepod inlet", "matte", colour=HOLE)  # the intakes' insides, whole
    s.paint("inner", "matte plastic", colour=HOLE)
    s.paint("wheels", "gunmetal")
    s.paint("canopy", colour=GOLD)  # the gold coating on the canopy alone


def design(s):
    base(s)
    s.step("The sheen", "The car's own outer panels in satin, the same bomber grey: they show only as the light "
           "moves across them.", words=WORDS)
    outer = meshlines.panel((76, 60, -25), both=True)
    for at in ((67, 41, -80), (42, 19, 63), (35, 73, -64), (44, 64, -138)):
        outer = outer | meshlines.panel(at, both=True)
    s.paint("body", "satin", colour=SKIN, zone=outer)
