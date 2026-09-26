"""Chaos and elegance, concept C (2026-09-26): elegance coming undone. Deep bottle green, and fine
ivory pinstripes running the length of the car, like a bespoke suit's cloth: dead straight and
evenly spaced over the nose and bonnet, starting to waver past the cockpit, and twisting into
swirls and loops over the tail. The same lines all the way; only their order is lost."""
import numpy as np

from tool import noise, shapes

WORDS = "I want chaos and elegance"
GREEN = "#0f2a20"
IVORY = "#e9dfc6"
INK = "#121614"
# the stripes: one every SPACING degrees round a line along the car (as the flag drape's, at the
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


def inner_car(s, dark=INK):
    """The inner car dark, as TSC_Stealth_CMYK's base without its body paint."""
    s.paint("inner", "satin", colour=dark)
    s.paint(["lower wishbone", "upper wishbone", "pushrod", "tie rod", "rear arm", "sidepod strut"], "carbon")
    s.paint(["damper", "rear damper", "upright", "hub bracket", "driveshaft", "upright cover", "hub", "brake light", "sidepod frame"],
            "satin", colour="#1e1f22")
    s.paint("exhaust", "brushed titanium")
    s.paint(["seat", "steering wheel"], "leather", colour="#3a2418")
    s.paint("dashboard", "matte", colour="#1a1b1d")


def design(s):
    s.clay()
    s.step("Bottle green", "The body in deep, glossy bottle green.", words=WORDS)
    s.paint("body", "gloss", colour=GREEN)  # wet look caught the sky: from behind the deck read white

    s.step("Pinstripes coming undone", "Fine ivory pinstripes the length of the car: straight and even over the nose, "
           "wavering past the cockpit, folding into swirls and loops over the tail, like marbled paper.", words=WORDS)
    s.paint("body", "gloss", colour=IVORY, zone=pinstripes())

    s.step("Inner car", "Dark inside, ivory grilles, calipers and belts, a tan leather seat.", words=WORDS)
    inner_car(s)
    s.paint(["sidepod grille", "side vent", "brake caliper", "seat belt", "front wing endplate"], "satin", colour=IVORY)
    s.paint("sidepod grille plate", "satin", colour=INK)
    s.paint(["mirror", "mirror arm"], "wet look", colour=GREEN)

    s.step("Wheels", "Bottle green covers, a thin ivory line round each tyre.", words=WORDS)
    s.paint("wheel covers", "wet look", colour=GREEN)
    s.paint("rim", "satin", colour=INK)
    s.no_glow("wheel ring")
    s.paint("wheel ring", "satin", colour=INK)
    s.paint("sidewall", "satin", colour=IVORY, zone=shapes.wheel_ring(31.8, 32.6))

    s.step("Lights", "Ivory speed numbers and rear lights, the grilles glowing ivory at night.", words=WORDS, look="rear night")
    s.relight("speed numbers", IVORY)
    s.relight("rear lights", IVORY)
    s.relight("brake lights", IVORY)
    s.glow(["sidepod grille", "side vent"], IVORY, "night only")
