"""TSC_ChaosElegance_Unravelled in the CMYK car's inks on dark grey (2026-09-26): the pinstripes
coloured by where they are along the car, cyan at the nose, magenta in the middle, yellow at the tail.
The user, after picking Unravelled: "Can you do a cmyk as well, lower lines yellow, to center
magenta? like a gradient?, or from front to back", "and dark grey body"."""
import importlib.util

from tool import paths

_spec = importlib.util.spec_from_file_location("unravelled", paths.SKINS / "TSC_ChaosElegance_Unravelled" / "design.py")
_unravelled = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_unravelled)


def design(s):
    _unravelled.design(s, look="run")
