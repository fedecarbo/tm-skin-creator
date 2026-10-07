"""TSC_StealthBomber: a stealth bomber's darkness, finishes and quiet, every line from the car's own form (its visual
language: language.json). The composition, set 2's B: matte bomber grey, and tape grey bands along the car's own
leading edges (round the nose and on along the body's edge over the side openings, all round the cockpit's outline,
along the skirts' swept edges, round the intakes' lips), each ending where its line ends."""

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
           "front and on back along the body's edge over the side openings, all round the cockpit's outline, "
           "along the skirts' swept edges and round the intakes' lips.",
           words=WORDS)
    # one smooth line: over the right side opening along the body's crisp edge (the user traced it), easing up onto
    # the nose's rounded edge, round the nose where it shows, and back down onto the left's crisp edge: no step
    rim = meshlines.line((0, 40, 210), kind="rounded")  # round the nose, its right end first
    side = meshlines.line((25.9, 47.3, 139.8))  # the crisp edge over the left side opening
    back = [(36.3, 52.8, 69), (35.4, 53.0, 75), (33.4, 51.4, 89)] + [tuple(side.at(z=z)) for z in (110, 124)]
    front = [tuple(rim.at(s=k * rim.length / 12)) for k in range(13)]
    nose = meshlines.picked([(-x, y, z) for x, y, z in back] + front + back[::-1]).strip(4)
    crest = meshlines.line((0, 83, -51)).strip(4)  # the whole outline round the cockpit, closed behind it
    skirts = meshlines.line((39, 19, 70)).mirrored().strip(4)
    s.paint("body", "satin", colour=TAPE, zone=nose | crest | skirts)
    lips = meshlines.line((75, 49, -45)).mirrored().strip(4)
    s.paint("body", "satin", colour=TAPE, zone=lips, across=True)
