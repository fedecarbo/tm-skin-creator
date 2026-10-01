"""Unravelled in CMYK, nose to tail (2026-09-26): the pinstripes coloured by where they are along the
car, cyan at the nose, magenta in the middle, yellow at the tail. The design is
TSC_ChaosElegance_Unravelled_CMYKRise's, with look "run"; its notes have the user's words."""

from tool.skin import borrow

_unravelled = borrow("TSC_ChaosElegance_Unravelled_CMYKRise")


def design(s):
    _unravelled.design(s, look="run")
