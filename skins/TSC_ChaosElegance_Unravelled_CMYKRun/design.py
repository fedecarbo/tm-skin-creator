"""Unravelled in CMYK, nose to tail (2026-09-26): the pinstripes coloured by where they are along the
car, cyan at the nose, magenta in the middle, yellow at the tail. The design is
TSC_ChaosElegance_Unravelled_CMYKRise's, with look "run"; its notes have the user's words."""
import importlib.util

from tool import paths

_spec = importlib.util.spec_from_file_location("unravelled_cmyk", paths.SKINS / "TSC_ChaosElegance_Unravelled_CMYKRise" / "design.py")
_unravelled = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_unravelled)


def design(s):
    _unravelled.design(s, look="run")
