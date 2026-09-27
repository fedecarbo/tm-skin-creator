"""TSC_CMYK_BlackTail with Claude's idea for the tail (2026-09-25): the wrap torn right to the
tail. It began as "CMYK ends in K", the colour under the wrap running into black at the tip, but
the tears there showed nothing (the user, 2026-09-27: "the cmyk gradient doesnt go through to the
far back"): the run now goes cyan, magenta, orange all the way back, and the black wrap is the K.
The orange also comes back as light (the speed digits, the rear lights' last band, the tail's
openings in a turbo). The wrap has a tiny grain in its sheen (the user, 2026-09-27)."""
import importlib.util

from tool import paths

_spec = importlib.util.spec_from_file_location("cmyk_black_tail", paths.SKINS / "TSC_CMYK_BlackTail" / "design.py")
_tail = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tail)


def grain(s):
    """The user's pick over the round of textures (carbon, halftone, brushed: TSC_CMYK_Carbon ...)."""
    s.step("A fine grain", "A tiny grain in the black wrap's sheen, like textured vinyl: seen up close where the light falls.",
           words="I was just thinking tiny grain just to have a bit of texture.")
    s.paint(["body", "sidepod frame"], "textured wrap", colour=_tail.BLACK)
    s.paint("wing pylon", "satin", colour=_tail.C)  # the front wing's supports stay cyan


def design(s, wrap=grain):
    _tail.design(s, tail="k", wrap=wrap)
