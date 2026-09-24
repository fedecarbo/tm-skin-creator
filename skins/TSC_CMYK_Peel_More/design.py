"""TSC_CMYK_Peel with half the wrap gone: bigger tears, bigger flaps."""
import importlib.util

from tool import paths

_spec = importlib.util.spec_from_file_location("cmyk_peel", paths.SKINS / "TSC_CMYK_Peel" / "design.py")
_peel = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_peel)


def design(s):
    _peel.design(s, more=True)
