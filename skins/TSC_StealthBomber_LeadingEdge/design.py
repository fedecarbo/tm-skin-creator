"""TSC_StealthBomber, take A, the leading edge: one swept V of tape grey over the top, seen from above, ending on
the flanks in teeth (the composition, from its visual language: language.json)."""

import math

import numpy as np

from tool import shapes

SKIN, TAPE, HOLE, GOLD = "#3f4348", "#565b61", "#1b1d20", "#c9a24a"  # the language's colours
SWEEP = math.radians(35)  # every edge 35 degrees off the car's length, or along it (the language's DNA)
T, S, C = math.tan(SWEEP), math.sin(SWEEP), math.cos(SWEEP)
WORDS = "do a stealth bomber"


def saw(u, pitch, slope):
    """A sawtooth over u: 0 at its points, rising at `slope` to the middle of each tooth; and its slope."""
    w = np.mod(u, pitch) - pitch / 2
    return slope * (pitch / 2 - np.abs(w)), -slope * np.sign(w)


def zone(fn, grad):
    """A zone from a function that's positive inside, its gradient (pos -> (n, 3)) making it a distance."""
    return shapes.field(fn, grad=lambda p, n: grad(p))


def above_teeth(y0, pitch):
    """Above a row of teeth along the car's length, their points down at y0, their sides on the sweep."""
    def g(p):
        out = np.zeros_like(p)
        out[:, 1] = 1
        out[:, 2] = -saw(p[:, 2], pitch, T)[1]
        return out
    return zone(lambda p, n: p[:, 1] - y0 - saw(p[:, 2], pitch, T)[0], g)


def base(s):
    """The skin, the openings, the gear and the glass: the same in every take."""
    s.clay()
    s.step("The skin", "Bomber grey, matte, all over; black inside every opening; the gear dark gunmetal; the canopy's "
           "gold coating.", words=WORDS)
    s.paint("body", "matte", colour=SKIN)
    s.paint("sidepod inlet", "matte", colour=HOLE)  # the intakes' insides, whole
    s.paint("inner", "matte plastic", colour=HOLE)
    s.paint("wheels", "gunmetal")
    s.paint("canopy", colour=GOLD)  # the gold coating on the canopy alone


def behind_v(apex):
    """Behind a V swept back from the middle at z apex, seen from above: a wing's leading edge."""
    def g(p):
        out = np.zeros_like(p)
        out[:, 0] = -np.sign(p[:, 0]) * C
        out[:, 2] = -S
        return out
    return zone(lambda p, n: -np.abs(p[:, 0]) * C - (p[:, 2] - apex) * S, g)


def design(s):
    base(s)
    s.step("The leading edge", "A band of tape grey 16 cm wide, swept back from just behind the nose fin at 35 degrees "
           "each side, over the cockpit and the sidepods, ending down the flanks in teeth.", words=WORDS)
    band = behind_v(110) & ~behind_v(110 - 16 / S) & above_teeth(44, 12)
    s.paint("body", "satin", colour=TAPE, zone=band)
