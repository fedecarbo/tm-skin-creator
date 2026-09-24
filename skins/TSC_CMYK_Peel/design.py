"""TSC_Stealth_CMYK_Bold with its matte black body as a wrap starting to come off: torn open in
ragged patches with hard edges and a hard shadow (a thin layer on top), satin cyan > magenta > yellow underneath, fading along the car
like the run inside. The inner car is the Bold's. TSC_CMYK_Peel_More is the same with half the
wrap gone."""
import importlib.util

from tool import paths, shapes

_spec = importlib.util.spec_from_file_location("stealth_cmyk", paths.SKINS / "TSC_Stealth_CMYK" / "design.py")
_cmyk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cmyk)
C, M, Y = _cmyk.C, _cmyk.M, _cmyk.Y


def design(s, more=False):
    # underneath: the CMY run along the whole body (satin, so the colour holds at every angle)
    s.paint("body", "satin", colour=C)
    s.paint("body", "satin", colour=M, zone=shapes.fade("z", 150, 50))
    s.paint("body", "satin", colour=Y, zone=shapes.fade("z", -10, -100))
    under = s.keep()
    # on top: the Bold car without its glossy seam lines ("the black tape", user), torn open
    _cmyk.design(s, bold=True, seams=False)
    # the ring round each sidepod inlet in the wrap's black, so the colour comes only through
    # the tears (user); the glowing grille inside keeps its colour
    s.paint("sidepod frame", "matte", colour="#232528")
    if more:
        s.peel(under, amount=0.45, scale=40, seed=11)
    else:
        s.peel(under, amount=0.2, scale=30, seed=7)
