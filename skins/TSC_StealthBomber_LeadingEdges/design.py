"""TSC_StealthBomber, take B, the leading edges: tape grey bands along the car's own leading edges (the nose's
rounded front, the crease ahead of the cockpit, the swept edges of the skirts, the intakes' lips), each ending where
its line ends (the composition, from its visual language: language.json)."""

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
    s.step("The leading edges", "Tape grey satin, 4 cm wide, along the car's own leading edges: round the nose's "
           "front, along the crease ahead of the cockpit, along the skirts' swept edges and round the intakes' lips.",
           words=WORDS)
    nose = meshlines.line((0, 40, 210), kind="rounded").strip(4)
    crest = meshlines.line((0, 70, 92)).strip(4)
    skirts = meshlines.line((39, 19, 70)).mirrored().strip(4)
    s.paint("body", "satin", colour=TAPE, zone=nose | crest | skirts)
    lips = meshlines.line((75, 49, -45)).mirrored().strip(4)
    s.paint("body", "satin", colour=TAPE, zone=lips, across=True)
