"""TSC_CMYK_BlackTail with Claude's idea for the tail (2026-09-25): CMYK ends in K. The colour
under the wrap runs cyan, magenta, orange and then black at the very tip, so the tears fade into
the black towards the tail, which is clean black; the orange comes back only as light (the speed
digits, the rear lights' last band, the tail's openings in a turbo)."""
import importlib.util

from tool import paths

_spec = importlib.util.spec_from_file_location("cmyk_black_tail", paths.SKINS / "TSC_CMYK_BlackTail" / "design.py")
_tail = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tail)


def design(s):
    _tail.design(s, tail="k")
