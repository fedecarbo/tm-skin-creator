"""TSC_CMYK_EndsInK with a texture in its black wrap (the user, 2026-09-27: "Can we start adding
some texture, more like for the black paint?"), take C: the wrap as brushed black metal vinyl,
fine lines along the car that shimmer as the light moves."""
import importlib.util

from tool import paths

_spec = importlib.util.spec_from_file_location("cmyk_ends_in_k", paths.SKINS / "TSC_CMYK_EndsInK" / "design.py")
_ends = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ends)
WORDS = "Can we start adding some texture, more like for the black paint?"


def brushed(s):
    s.step("The wrap's texture", "Brushed black metal vinyl: fine lines along the car that shimmer in the light.", words=WORDS)
    s.paint(["body", "sidepod frame"], "brushed wrap", colour="#303237", direction="z")
    s.paint("wing pylon", "satin", colour=_ends._tail.C)  # the front wing's supports stay cyan


def design(s):
    _ends.design(s, wrap=brushed)
