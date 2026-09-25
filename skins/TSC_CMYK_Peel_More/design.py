"""TSC_CMYK_Peel with half the wrap gone: bigger tears, bigger flaps. The run ends in orange
rather than yellow (the user, 2026-09-25), and the lights are in the run's colours: cyan brake
lights at the front, magenta speed numbers, rear lights that go cyan > magenta > orange as the
gears climb, and rims that glow orange-hot when braking hard."""
import importlib.util

from tool import paths

_spec = importlib.util.spec_from_file_location("cmyk_peel", paths.SKINS / "TSC_CMYK_Peel" / "design.py")
_peel = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_peel)
C, M = _peel.C, _peel.M
ORANGE = "#ff9a1a"
DARK = "#1e1f22"


def design(s):
    _peel.design(s, more=True, end=ORANGE)
    s.relight("brake lights", C)
    s.relight("speed numbers", M)
    # one colour per gear band, from the tail's corner inwards; unlit, the bars are dark (not the
    # run's colour), so each lit band shows its true colour
    s.relight("rear lights", [C, C, M, M, ORANGE])
    s.paint("rear light", "satin", colour=DARK)
    # brake heat: the rims glow orange as they heat up under hard braking; glow() tints the paint,
    # so the rims go back to the dark satin
    s.glow("rim", ORANGE, "brake heat")
    s.paint("rim", "satin", colour=DARK)
