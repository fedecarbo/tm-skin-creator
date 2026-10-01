"""TSC_CMYK_EndsInK with a texture in its black wrap (the user, 2026-09-27: "Can we start adding
some texture, more like for the black paint?"), take A: the wrap as carbon fibre, a fine twill
weave with a satin sheen, so the weave catches the light."""

from tool.skin import borrow

_ends = borrow("TSC_CMYK_EndsInK")
WORDS = "Can we start adding some texture, more like for the black paint?"


def carbon(s):
    s.step("The wrap's texture", "Carbon fibre: a fine twill weave in the black, with a satin sheen.", words=WORDS)
    # a 12K-size weave, a touch lighter than the wrap: the stock 0.5 cm weave in the wrap's black
    # was too fine and too dark to read beyond arm's length
    s.paint(["body", "sidepod frame"], "satin carbon", colour="#3a3d44", scale=0.8)
    s.paint("wing pylon", "satin", colour=_ends._tail.C)  # the front wing's supports stay cyan


def design(s):
    _ends.design(s, wrap=carbon)
