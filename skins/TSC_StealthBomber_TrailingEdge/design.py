"""TSC_StealthBomber, take C, the trailing edge: the car's back in tape grey behind a W of teeth across it, seen
from above, as a flying wing's trailing edge (the composition, from its visual language: language.json)."""

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


def behind_w(z0, pitch):
    """Behind a W across the car: teeth `pitch` wide, their points back at z0, their sides on the sweep."""
    def g(p):
        out = np.zeros_like(p)
        out[:, 0] = saw(p[:, 0], pitch, 1 / T)[1]
        out[:, 2] = -1
        return out
    return zone(lambda p, n: z0 + saw(p[:, 0], pitch, 1 / T)[0] - p[:, 2], g)


def design(s):
    base(s)
    s.step("The trailing edge", "Tape grey over the back of the car, behind a W of teeth 40 cm wide across it, the "
           "middle point just behind the cockpit, its sides 35 degrees off the length; down the flanks it ends in "
           "a level line, so the W's are the only teeth.", words=WORDS)
    s.paint("body", "satin", colour=TAPE, zone=behind_w(-52, 40) & shapes.above(55))
