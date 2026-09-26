"""TSC_FlagPeel_CostaRica worn instead of torn (2026-09-26): the flag is the paint, over primer,
washed out by years of sun, the clear coat failed in chalky
patches on top, a few chips. The user: "Maybe in this concept its more on looking worn, the
flag? Instead of torn paint?"
"""
import importlib.util

from tool import paths

_spec = importlib.util.spec_from_file_location("flag_peel", paths.SKINS / "TSC_FlagPeel_CostaRica" / "design.py")
_flag = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_flag)


def design(s):
    _flag.design(s, "costa rica", wear="sun")
