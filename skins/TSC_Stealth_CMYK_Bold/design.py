"""TSC_Stealth_CMYK, bolder: the run also on the cockpit rim and mirrors, the front wing cyan,
the tail frame and bumper yellow."""
from tool.skin import borrow

_cmyk = borrow("TSC_Stealth_CMYK")


def design(s):
    _cmyk.design(s, bold=True)
