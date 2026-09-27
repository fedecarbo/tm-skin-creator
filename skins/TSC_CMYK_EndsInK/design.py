"""TSC_CMYK_BlackTail with Claude's idea for the tail (2026-09-25): the wrap torn right to the
tail. It began as "CMYK ends in K", the colour under the wrap running into black at the tip, but
the tears there showed nothing (the user, 2026-09-27: "the cmyk gradient doesnt go through to the
far back"): the run now goes cyan, magenta, orange all the way back, and the black wrap is the K.
The orange also comes back as light (the speed digits, the rear lights' last band, the tail's
openings in a turbo)."""
import importlib.util

from tool import paths

_spec = importlib.util.spec_from_file_location("cmyk_black_tail", paths.SKINS / "TSC_CMYK_BlackTail" / "design.py")
_tail = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tail)


def design(s):
    _tail.design(s, tail="k")
