"""Unravelled in CMYK (2026-09-26): fine pinstripes the length of the car in the CMYK car's inks on
satin dark grey, dead straight over the nose, wavering past the cockpit, folding into swirls and
loops over the tail like marbled paper. The same lines all the way; only their order is lost.

Two takes, by `look`: "rise" (this skin), each line coloured by where it runs round the car, cyan
along the top, magenta over the shoulders, yellow low on the sides; "run"
(TSC_ChaosElegance_Unravelled_CMYKRun), coloured by where it is along the car, cyan at the nose,
magenta in the middle, yellow at the tail.

From the chaos-and-elegance round (the user, 2026-09-26: "I want chaos and elegance"), concept C,
Unravelled, ivory on bottle green; the user picked it, then asked: "Can you do a cmyk as well,
lower lines yellow, to center magenta? like a gradient?, or from front to back", "and dark grey
body", "I meant is in the whole cyan magenta yellow". The ivory one and the round's other concepts
were deleted on 2026-09-27 (the user: "They are not bad, but I won't drive them"); this design
moved here from TSC_ChaosElegance_Unravelled."""

import numpy as np

from tool import noise, shapes
from tool.skin import borrow

# the game's own lamps inside the car and the parts it lights in a turbo, found part by part on
# the CMYK car (TSC_CMYK_BlackTail's lists), and the CMYK car's inks
_tail = borrow("TSC_CMYK_BlackTail")

WORDS = "I want chaos and elegance"
CMYK_WORDS = "Can you do a cmyk as well, lower lines yellow, to center magenta? like a gradient?, or from front to back"
C, M, Y = _tail.C, _tail.M, _tail._more._peel._cmyk.Y
GREY = "#2e3034"
INK = "#121614"
# the stripes: one every SPACING degrees round a line along the car (as a flag drape's, at the
# floor's height, dropping under the nose so they don't fan out there), LINE cm wide. 90 / SPACING
# is a half, so the lower sides, all at 90 degrees, fall between two lines.
AXIS_Y, NOSE_DROP = 15.0, 30.0
SPACING, LINE = 4.0, 0.6
# how far the lines are pushed about, in cm: not at all ahead of CALM (z), rising to WILD at the
# tail, in swirls about SWIRL cm across. Pushing the points rather than adding noise to the
# stripes folds the lines over into loops, like marbled paper (added noise only made them wavy)
CALM, TAIL, WILD, SWIRL = 30.0, -160.0, 45.0, 28.0


def _angle(p):
    axis = AXIS_Y - NOSE_DROP * np.clip((p[:, 2] - 140) / 60, 0, 1)
    return np.degrees(np.arctan2(p[:, 0], np.maximum(p[:, 1] - axis, 1e-3)))


def _stripe(p):
    """Which stripe a point is on (a whole number is a line's middle), the points pushed about."""
    t = np.clip((CALM - p[:, 2]) / (CALM - TAIL), 0, 1)
    push = np.stack([noise.fbm(p / SWIRL + o, 3, 7 + k) - 0.5 for k, o in enumerate((0.0, 41.3, 87.9))], 1)
    return _angle(p + 2 * WILD * (t ** 1.5)[:, None] * push) / SPACING


def pinstripes():
    """The lines as a zone, LINE cm wide wherever they wander: the distance to the nearest line
    is its offset in stripes over how fast the stripes change along the surface."""
    def dist(p, n):
        f = _stripe(p)
        e = 0.5
        g = np.stack([(_stripe(p + d) - f) / e for d in np.eye(3, dtype=np.float32) * e], 1)
        g -= (g * n).sum(1, keepdims=True) * n  # along the surface only
        off = np.abs(f - np.round(f))
        return LINE / 2 - off / np.maximum(np.linalg.norm(g, axis=1), 1e-4)
    return shapes.field(dist, soft=0.12)


def by_line(start, end):
    """0 on the lines running within `start` stripes of the top's centre line, rising to 1 on those
    `end` stripes out and beyond (the lowest on the sides are 22 out). A line keeps its colour
    through the swirls: it's the line's own, not the place's."""
    from tool.noise import smoothstep
    return shapes.Zone(lambda p, n: smoothstep(start, end, np.abs(_stripe(p))))


def inner_car(s, dark=INK):
    """The inner car dark, as TSC_Stealth_CMYK's base without its body paint."""
    s.paint("inner", "satin", colour=dark)
    s.paint(["lower wishbone", "upper wishbone", "pushrod", "tie rod", "rear arm", "sidepod strut"], "carbon")
    s.paint(["damper", "rear damper", "upright", "hub bracket", "driveshaft", "upright cover", "hub", "brake light", "sidepod frame"],
            "satin", colour="#1e1f22")
    s.paint("exhaust", "brushed titanium")
    s.paint(["seat", "steering wheel"], "black leather")
    s.paint("dashboard", "matte", colour="#1a1b1d")


def design(s, look="rise"):
    """look: "rise" (the lines' colours round the car) or "run" (along it)."""
    lines = pinstripes()
    s.clay()
    s.step("Dark grey", "The body in satin dark grey.", words="and dark grey body")
    s.paint("body", "satin", colour=GREY)
    undone = "straight over the nose, folding into swirls over the tail"
    if look == "rise":  # the user: "I meant is in the whole cyan magenta yellow"
        s.step("Pinstripes in CMYK", f"The pinstripes in satin inks, {undone}: each line by where it runs, cyan "
               "along the top, magenta over the shoulders, yellow low on the sides.", words=CMYK_WORDS)
        s.paint("body", "satin", colour=C, zone=lines)
        s.paint("body", "satin", colour=M, zone=lines & by_line(3, 9))
        s.paint("body", "satin", colour=Y, zone=lines & by_line(12, 18))
    else:
        s.step("Pinstripes in CMYK", f"The pinstripes in satin inks, {undone}: cyan at the nose, magenta in the "
               "middle, yellow at the tail, where the swirls are.", words=CMYK_WORDS)
        s.paint("body", "satin", colour=C, zone=lines)
        s.paint("body", "satin", colour=M, zone=lines & shapes.fade("z", 110, 10))
        s.paint("body", "satin", colour=Y, zone=lines & shapes.fade("z", -30, -130))

    # the accents in the inks: magenta and yellow as the lines rise, or by where they sit along the car
    accent = {"rise": dict(tyre=Y, rear=[Y, Y, M, M, M], lamps=M),
              "run": dict(tyre=M, rear=Y, lamps=None)}[look]
    s.step("Inner car", "Dark inside, the grilles and belts magenta, the side vents yellow, cyan calipers, "
           "a quilted black leather seat.", words=WORDS)
    inner_car(s)
    s.paint(["sidepod grille", "seat belt"], "satin", colour=M)
    s.paint("side vent", "satin", colour=Y)
    s.paint(["brake caliper", "front wing endplate"], "satin", colour=C)
    s.paint("sidepod grille plate", "satin", colour=INK)
    s.paint(["mirror", "mirror arm"], "satin", colour=GREY)
    s.relief("seat", "quilted", depth=0.5, scale=7, replace=True)

    s.step("Wheels", f"Dark grey covers, a thin {'yellow' if accent['tyre'] == Y else 'magenta'} line round each tyre.", words=WORDS)
    s.paint("wheel covers", "satin", colour=GREY)
    s.paint("rim", "satin", colour=INK)
    s.no_glow("wheel ring")
    s.paint("wheel ring", "satin", colour=INK)
    s.paint("sidewall", "satin", colour=accent["tyre"], zone=shapes.wheel_ring(31.8, 32.6))

    s.step("Lights", "Yellow speed numbers, the grilles glowing magenta at night, the lamps inside in the inks; in a "
           "turbo the wheels light magenta, not the pad's colour.", words=WORDS, look="rear night")
    s.relight("speed numbers", Y)
    s.relight("rear lights", accent["rear"])
    s.relight("brake lights", M)
    s.glow(["sidepod grille", "side vent"], M, "night only")
    # the game's own lamps inside, stock teal and white: in the inks
    if accent["lamps"]:
        s.relight(_tail.LIGHTS, accent["lamps"], keep_level=True)
        s.relight(["hub", "brake light"], accent["lamps"], keep_level=True)
    else:  # by where they sit, as the lines: the CMYK car's run
        _tail.light_run(s, _tail.LIGHTS, Y)
        s.relight(["hub", "brake light"], M, keep_level=True)
    # magenta in the wheels, as the user chose on the CMYK car; the rest as the lamps
    s.glow(_tail.TURBO_WHEELS, M, "exhaust heat", replacing="turbo", keep_level=True)
    if accent["lamps"]:
        s.glow(_tail.TURBO_REST, accent["lamps"], "exhaust heat", replacing="turbo", keep_level=True)
    else:
        _tail.turbo_run(s, _tail.TURBO_REST, Y)
    s.no_glow("rear bumper")
