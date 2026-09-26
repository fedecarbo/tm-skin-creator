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


def design(s, more=False, end=Y, tip=None, hold=None):
    """end: the colour the run ends in at the tail (yellow; TSC_CMYK_Peel_More's is orange).
    tip: a last colour it fades into at the very tail (TSC_CMYK_EndsInK's black). hold: a zone
    where the wrap holds, no tears (TSC_CMYK_BlackTail's tail)."""
    # underneath: the CMY run along the whole body (satin, so the colour holds at every angle)
    s.step("The colour run", "Satin cyan to magenta to the end colour along the body, under the wrap to come.",
           words="I wonder if you can make the body of the car as if the skin is peeling off and it reveals cmyk color.")
    s.paint("body", "satin", colour=C)
    s.paint("body", "satin", colour=M, zone=shapes.fade("z", 150, 50))
    s.paint("body", "satin", colour=end, zone=shapes.fade("z", -10, -100))
    if tip is not None:
        s.paint("body", "matte", colour=tip, zone=shapes.fade("z", -110, -150))  # matte like the wrap: the tears dissolve
    under = s.keep()
    # on top: the Bold car without its glossy seam lines ("the black tape", user), torn open
    s.step("The black wrap", "Matte black over the whole body, no seam lines; the inner car in the run's colours.",
           words="Can you remove the black tape.")
    _cmyk.design(s, bold=True, seams=False, end=end)
    # the ring round each sidepod inlet in the wrap's black, so the colour comes only through
    # the tears (user); the glowing grille inside keeps its colour
    s.paint("sidepod frame", "matte", colour="#232528")
    s.step("Torn open", f"The wrap torn off in ragged patches ({'about half' if more else 'about a fifth'}), hard edges and a thin even shadow, the run showing through.",
           words="Make the edges of the torn sharper.")
    if more:
        s.peel(under, amount=0.45, scale=40, seed=11, hold=hold)
    else:
        s.peel(under, amount=0.2, scale=30, seed=7, hold=hold)
