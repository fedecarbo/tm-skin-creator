"""TSC_Stealth_CMYK, bolder: the run also on the cockpit rim and mirrors, the front wing cyan,
the tail frame and bumper yellow."""
import importlib.util
from tool import paths

_spec = importlib.util.spec_from_file_location("stealth_cmyk", paths.SKINS / "TSC_Stealth_CMYK" / "design.py")
_cmyk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cmyk)


def design(s):
    _cmyk.design(s, bold=True)
