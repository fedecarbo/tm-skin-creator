"""TSC_CMYK_BlackTail with Claude's idea for the tail (2026-09-25): the wrap torn right to the
tail. It began as "CMYK ends in K", the colour under the wrap running into black at the tip, but
the tears there showed nothing (the user, 2026-09-27: "the cmyk gradient doesnt go through to the
far back"): the run now goes cyan, magenta, orange all the way back, and the black wrap is the K.
The orange also comes back as light (the speed digits, the rear lights' last band, the tail's
openings in a turbo). The wrap has a tiny grain in its sheen (the user, 2026-09-27)."""
import importlib.util

import numpy as np

from tool import paths

_spec = importlib.util.spec_from_file_location("cmyk_black_tail", paths.SKINS / "TSC_CMYK_BlackTail" / "design.py")
_tail = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tail)


def grain(s):
    """The user's pick over the round of textures (carbon, halftone, brushed: TSC_CMYK_Carbon ...)."""
    s.step("A fine grain", "A tiny grain in the black wrap's sheen, like textured vinyl: seen up close where the light falls. The trims plain matte.",
           words="I was just thinking tiny grain just to have a bit of texture.")
    s.paint("body", "textured wrap", colour=_tail.BLACK)
    # the trims stay plain matte, the ring round each sidepod inlet and the band round the cockpit
    # (the user's notes: "I would have these normal matte black", "Same with this")
    s.paint(["sidepod frame", "cockpit surround"], "matte", colour=_tail.BLACK)
    s.paint("wing pylon", "satin", colour=_tail.C)  # the front wing's supports stay cyan


# the suspension was matte carbon and dark satin (TSC_Stealth_CMYK's); the user: "I thing joints
# and those things shouldnt be matte?  Or I guess, matte but mettalic, so they look more
# realistic", "same with these" (2026-09-27). It shares paint only with the small patch the front
# uprights wear, which goes metal with them
SUSPENSION = ["lower wishbone", "upper wishbone", "pushrod", "tie rod", "rear arm", "damper", "rear damper", "upright",
              "hub bracket", "driveshaft"]
CARBON_ARMS = ["lower wishbone", "upper wishbone", "pushrod", "tie rod", "rear arm"]


def design(s, wrap=grain):
    _tail.design(s, tail="k", wrap=wrap)
    s.step("Metal suspension", "The wishbones, pushrods, tie rods, rear arms, dampers, uprights and driveshafts in "
           "bead-blasted titanium, a shade dark: matte, but metal.",
           words="I thing joints and those things shouldnt be matte?  Or I guess, matte but mettalic, so they look more "
                 "realistic. same with these")
    s.paint(SUSPENSION, "bead-blasted titanium", colour="#6b6d72")
    # Nadeo's relief on the arms is a carbon weave, which on metal read as woven metal: smooth
    s.relief(CARBON_ARMS, lambda pos, nrm: np.zeros(len(pos), np.float32), replace=True)
