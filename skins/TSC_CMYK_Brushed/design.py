"""TSC_CMYK_EndsInK with a texture in its black wrap (the user, 2026-09-27: "Can we start adding
some texture, more like for the black paint?"), take C: the wrap as brushed black metal vinyl,
fine lines along the car that shimmer as the light moves."""

from tool.skin import borrow

_ends = borrow("TSC_CMYK_EndsInK")
WORDS = "Can we start adding some texture, more like for the black paint?"


def brushed(s):
    s.step("The wrap's texture", "Brushed black metal vinyl: fine lines along the car that shimmer in the light.", words=WORDS)
    s.paint(["body", "sidepod frame"], "brushed wrap", colour="#303237", direction="z")
    s.paint("wing pylon", "satin", colour=_ends._tail.C)  # the front wing's supports stay cyan


def design(s):
    _ends.design(s, wrap=brushed)
