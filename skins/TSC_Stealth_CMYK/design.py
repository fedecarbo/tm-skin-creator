"""Stealth black with a cyan > magenta > yellow run inside: the sidepod frames, grilles and
belts fade through the three colours along the car (the grilles glow), the calipers and front
wing endplates are cyan, the rear vents and strakes yellow. The rest of the inside is raw
materials in black."""
from tool import shapes

MAIN = ["body shell", "cockpit surround", "nose tip", "nose panel", "sidepod top", "sidepod inlet",
        "side skirt", "rear flank", "engine cover", "tail panel", "rear quarter panel", "tail corner", "diffuser"]
ACCENT = ["sidepod grille", "side vent", "brake caliper", "seat belt", "brake line"]
C, M, Y = "#00c8ff", "#ff1fa8", "#ffe600"


def stealth_base(s, seams=True):
    s.paint("body", "matte", colour="#232528")
    if seams:
        s.paint("body", "gloss", colour="#26282b", zone=shapes.seams(1.5, parts=MAIN))
    s.paint("inner", "satin", colour="#2a2b2e")
    s.paint(["lower wishbone", "upper wishbone", "pushrod", "tie rod", "rear arm", "sidepod strut"], "carbon")
    s.paint(["damper", "rear damper", "upright", "hub bracket", "driveshaft", "upright cover", "hub", "brake light", "sidepod frame"], "satin", colour="#1e1f22")
    s.paint("exhaust", "brushed titanium")
    s.paint(["seat", "steering wheel"], "black leather")
    s.paint("dashboard", "matte", colour="#1a1b1d")
    s.paint("rim", "satin", colour="#1e1f22")


def run(s, where, end=Y):
    """The cyan > magenta > yellow run along the car, over the sidepod's length (z 36 .. -47).
    end: the colour it ends in (yellow, or another, as TSC_CMYK_Peel_More's orange)."""
    s.paint(where, "satin", colour=C)
    s.paint(where, "satin", colour=M, zone=shapes.fade("z", 36, -2))
    s.paint(where, "satin", colour=end, zone=shapes.fade("z", -10, -47))


def design(s, bold=False, seams=True, end=Y):
    stealth_base(s, seams)
    run(s, ["sidepod frame", "sidepod grille", "sidepod panel", "seat belt"], end)
    s.paint(["brake caliper", "brake line", "front wing endplate"], "satin", colour=C)
    s.paint(["side vent", "rear strake"], "satin", colour=end)
    if bold:
        s.paint(["front wing", "wing mounts"], "satin", colour=C)
        s.paint(["tail frame", "rear bumper", "rear light"], "satin", colour=end)
        run(s, ["cockpit rim", "mirror", "mirror arm"], end)
    # the plate each grille sits in goes black, to break up the run (user, 2026-09-24)
    s.paint("sidepod grille plate", "satin", colour="#1e1f22")
    s.glow(["sidepod grille", "side vent"], None, "always on")
    s.glow("brake caliper", None, "brake lights")
