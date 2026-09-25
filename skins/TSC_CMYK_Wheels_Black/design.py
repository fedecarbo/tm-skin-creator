"""TSC_CMYK_Peel_More with the "black" wheels (a take, 2026-09-25): see WHEELS in its design."""
import importlib.util

from tool import paths

_spec = importlib.util.spec_from_file_location("cmyk_more", paths.SKINS / "TSC_CMYK_Peel_More" / "design.py")
_more = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_more)


def design(s):
    _more.design(s, wheel_take="black")
