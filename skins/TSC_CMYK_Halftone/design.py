"""TSC_CMYK_EndsInK with a texture in its black wrap (the user, 2026-09-27: "Can we start adding
some texture, more like for the black paint?"), take B: CMYK is print, so the wrap is printed
black on black. A halftone screen of glossy dots on the matte black, small at the nose and
growing towards the tail until they nearly touch: seen as the light moves over them."""

import numpy as np
from scipy.spatial import cKDTree

from tool import looks, shapes
from tool.skin import borrow

_ends = borrow("TSC_CMYK_EndsInK")
WORDS = "Can we start adding some texture, more like for the black paint?"


def halftone(spacing=1.8, small=0.3, big=0.9, seed=3, flat=0.97):
    """A halftone screen: dots evenly spaced on the surface, `spacing` cm apart, their diameter a
    share of the spacing growing from `small` at the nose tip to `big` at the tail. Each dot's
    size comes from its centre, so every dot is round; its edge is one texel. A dot that would
    bend over a fold, a seam or a tight curve (its normals more than about 14 degrees apart, cos <
    `flat`) is left out whole: there the highlight broke into a row of bright dashes (the sidepod
    inlet's lip at 25 degrees)."""
    def f(p, n):
        centres = looks.surface_points(p, spacing, seed)
        d, j = cKDTree(centres).query(p, workers=-1)
        share = small + (big - small) * np.clip((215 - centres[j, 2]) / 377, 0, 1)
        w = np.clip(0.5 + (share * spacing / 2 - d) / 0.09, 0, 1)
        _, at = cKDTree(p).query(centres, workers=-1)
        cos = (n * n[at][j]).sum(1)
        worst = np.ones(len(centres), np.float32)
        inside = w > 0
        np.minimum.at(worst, j[inside], cos[inside])
        return w * (worst[j] > flat)
    return shapes.Zone(f)


def dots(s):
    s.step("The wrap's texture", "A halftone print, black on black: glossy dots on the matte wrap, growing from the nose to the tail.",
           words=WORDS)
    s.paint(["body", "sidepod frame"], "gloss", colour="#1d1f22", zone=halftone())
    s.paint("wing pylon", "satin", colour=_ends._tail.C)  # the front wing's supports stay cyan


def design(s):
    _ends.design(s, wrap=dots)
