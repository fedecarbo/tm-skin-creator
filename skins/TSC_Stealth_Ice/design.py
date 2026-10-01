"""Stealth black with one accent inside, ice blue: the sidepod grilles and rear vents glow in it,
the calipers wear it and light up when braking, the belts and brake lines wear it. The rest of
the inside is raw materials."""
from tool.skin import borrow

_cmyk = borrow("TSC_Stealth_CMYK")
ACCENT_COLOUR = "#9fd8ff"


def design(s):
    _cmyk.stealth_base(s)
    s.paint(_cmyk.ACCENT, "satin", colour=ACCENT_COLOUR)
    s.glow(["sidepod grille", "side vent"], None, "always on")
    s.glow("brake caliper", None, "brake lights")
