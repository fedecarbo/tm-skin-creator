"""Stealth black with one accent inside, magenta: the sidepod grilles and rear vents glow in it,
the calipers wear it and light up when braking, the belts and brake lines wear it. The rest of
the inside is raw materials."""
import importlib.util
from tool import paths

_spec = importlib.util.spec_from_file_location("stealth_cmyk", paths.SKINS / "TSC_Stealth_CMYK" / "design.py")
_cmyk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cmyk)
ACCENT_COLOUR = "#ff1fa8"


def design(s):
    _cmyk.stealth_base(s)
    s.paint(_cmyk.ACCENT, "satin", colour=ACCENT_COLOUR)
    s.glow(["sidepod grille", "side vent"], None, "always on")
    s.glow("brake caliper", None, "brake lights")
