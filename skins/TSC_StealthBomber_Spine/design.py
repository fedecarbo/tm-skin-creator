"""TSC_StealthBomber, take A, the spine: the car's own central panels (the nose panel, the cockpit surround, the
engine cover, the tail panel) a step lighter in satin, the rest of it matte bomber grey (the composition, from its
visual language: language.json)."""

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
    s.step("The spine", "The car's own central panels, nose to tail, in tape grey satin, each filled whole to its "
           "lines.", words=WORDS)
    spine = (meshlines.panel((-2, 56, 162)) | meshlines.panel((-25, 80, 11), both=True)
             | meshlines.panel((-3, 75, -97)) | meshlines.panel((3, 65, -152)))
    s.paint("body", "satin", colour=TAPE, zone=spine)
