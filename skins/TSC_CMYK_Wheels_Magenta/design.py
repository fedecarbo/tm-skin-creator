"""TSC_CMYK_Peel_More with the "magenta" wheels (a take, 2026-09-25): see WHEELS in its design."""

from tool.skin import borrow

_more = borrow("TSC_CMYK_Peel_More")


def design(s):
    _more.design(s, wheel_take="magenta")
