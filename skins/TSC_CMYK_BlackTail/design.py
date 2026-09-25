"""TSC_CMYK_Peel_More with its inner car finished and its tail black (2026-09-25), the user's
idea: the tail stays black with a few tears, the speed digits in the run's orange end. Inside,
every light the game put there takes the run's colours, the turbo lights the car in them too
(magenta inside the wheels, orange-hot in the tail's openings), one line per tyre, and relief: a
quilted seat and printer's registration marks raised on the tail. TSC_CMYK_EndsInK (Claude's
idea) is the same with design(s, tail="k"): the run itself ends in black at the tip."""
import importlib.util

import numpy as np
from PIL import Image, ImageDraw

from tool import paths, shapes

_spec = importlib.util.spec_from_file_location("cmyk_more", paths.SKINS / "TSC_CMYK_Peel_More" / "design.py")
_more = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_more)
C, M, ORANGE, BLACK, DARK = _more.C, _more.M, _more.ORANGE, _more.BLACK, _more.DARK

# the game's own lights that the car still showed in its stock teal and white (found part by part,
# 2026-09-25): little lamps in the cockpit, nose and bulkhead, the strip under the floor, the vanes
# and sidepod panels, and the faint night glows on the airboxes, sidepod frames and steering
LIGHTS = ["cockpit tub", "front bulkhead", "nose inner", "floor rail", "side vane", "sidepod panel", "front wing endplate",
          "airbox", "sidepod frame", "sidepod strut", "steering column", "steering wheel", "tie rod", "exhaust"]
# the parts the game lights in the turbo pad's colour (yellow after a yellow pad: the whole inside
# of each wheel, the user didn't like it). Those in the wheels glow magenta instead (the user's
# pick; all four wheels share one paint), the rest in the run's colour where they sit
TURBO_WHEELS = ["hub", "hub bracket", "upright cover", "lower wishbone", "upper wishbone", "tie rod", "rear arm",
                "driveshaft", "damper", "pushrod"]
TURBO_REST = ["rear strake", "rear undertray", "front bulkhead", "antenna", "brake line", "wing bracket", "rear bumper corner",
              "nose inner", "exhaust"]
# inside the tail's two openings, beside the speed digits: their walls, not the frame's face
PORTS = shapes.box((-50, 20, -158), (50, 49, -120)) & ~shapes.facing((0, 0, -1), 0.7)
TAIL = ["rear diffuser", "rear bumper", "rear strake"]
# the few tears in the tail's black (the user's take): big enough to read as torn wrap, not spots
TAIL_TEARS = dict(amount=0.15, scale=18, seed=8, jag=0.1, shadow=0.4)  # one bold tear across the top band


def registration_mark(px=512):
    """A printer's registration mark: a ring with a cross through it, white on clear."""
    im = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    w = px * 0.07
    r = px * 0.3
    c = px / 2
    d.ellipse((c - r, c - r, c + r, c + r), outline=(255, 255, 255, 255), width=int(w))
    d.rectangle((c - w / 2, 0, c + w / 2, px), fill=(255, 255, 255, 255))
    d.rectangle((0, c - w / 2, px, c + w / 2), fill=(255, 255, 255, 255))
    return im


def run_zones():
    """The body's run along the car, for lights: cyan at the nose, magenta in the middle, the
    end colour at the tail."""
    return shapes.fade("z", 150, 50), shapes.fade("z", -10, -100)


def light_run(s, where, end):
    """The game's lights on these parts take the run's colour where they sit, keeping their brightness."""
    mid, back = run_zones()
    s.relight(where, C, keep_level=True)
    s.relight(where, M, zone=mid, keep_level=True)
    s.relight(where, end, zone=back, keep_level=True)


def turbo_run(s, where, end):
    """The parts the game lights in the turbo pad's colour light in the run's colours instead:
    exhaust heat, which keeps its own colour and comes on in a turbo ("ON when Turbo is enabled",
    xrayjay's table; never seen yet in the game, so these are its test)."""
    mid, back = run_zones()
    s.glow(where, C, "exhaust heat", replacing="turbo", keep_level=True)
    s.relight(where, M, zone=mid, keep_level=True)
    s.relight(where, end, zone=back, keep_level=True)


def wheels(s):
    """One line per tyre (the user): the glowing ring inside each wheel goes dark, and the tyre's
    line is a little thicker, 1.6 cm (31.5 to 33.1 cm from the axle) instead of 1.2."""
    s.no_glow("wheel ring")
    s.paint("wheel ring", "matte", colour=BLACK)
    line = shapes.wheel_ring(31.5, 33.1)
    s.paint("sidewall", "satin", colour=C, zone=line)
    s.paint("sidewall", "satin", colour=M, zone=line & _more.round_wheel(0, 0.5))
    s.paint("sidewall", "satin", colour=ORANGE, zone=line & _more.round_wheel(0.5, 1))


def design(s, tail="tears"):
    k = tail == "k"
    # the body: yours holds the wrap over the tail's last 40 cm (tears shrink away towards the
    # tip); mine runs the colour under the wrap into black at the tip (C, M, Y and K)
    _more.design(s, tip=BLACK if k else None, hold=None if k else shapes.fade("z", -110, -150))
    s.relight("speed numbers", ORANGE)
    wheels(s)
    # the inside's lights, and the turbo
    light_run(s, LIGHTS, ORANGE)
    s.relight(["hub", "brake light"], C, keep_level=True)
    s.glow(TURBO_WHEELS, M, "exhaust heat", replacing="turbo", keep_level=True)
    turbo_run(s, TURBO_REST, ORANGE)
    s.glow("rear diffuser", ORANGE, "exhaust heat", zone=PORTS)  # the openings, orange-hot in a turbo
    s.no_glow("rear bumper")  # under the deck, hidden by the body: it glowed white all the time
    # the exhaust was bare titanium, the one bright silver part inside: heat-tinted now, as real
    # titanium pipes go, straw gold at the engine through magenta-purple to blue at the tips
    s.paint("exhaust", "brushed titanium", colour="#c9a24a")
    s.paint("exhaust", "brushed titanium", colour="#9a4f9e", zone=shapes.fade("z", -115, -130))
    s.paint("exhaust", "brushed titanium", colour="#3f6fd0", zone=shapes.fade("z", -130, -145))
    # (before the tail: the pipes' trim shares a few texels with the tail's frame, and the tail
    # must win them, or they show as gold dashes along its edges)
    # the tail: black like the wrap. Yours with a few tears showing the orange under it
    under = s.keep("Details")
    s.paint(TAIL, "matte", colour=BLACK)
    if not k:
        s.peel(under, where="rear diffuser", **TAIL_TEARS)
    # the openings under the quarter panels, seen whenever the air brakes lift, were still the
    # stock grey: dark like the rest of the inside
    s.paint("airbox", "matte", colour="#1a1b1d")
    # relief: a quilted seat, and a registration mark raised at each end of the tail's top band
    s.relief("seat", "quilted", depth=0.5, scale=7, replace=True)
    s.emboss(None, "rear diffuser", at=(38, 56, -157), right=(-1, 0, 0), picture=registration_mark(), width=5.5, depth=0.15)
