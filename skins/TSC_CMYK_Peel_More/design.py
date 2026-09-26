"""TSC_CMYK_Peel with half the wrap gone: bigger tears, bigger flaps. The run ends in orange
rather than yellow (the user, 2026-09-25), and the lights are in the run's colours: cyan brake
lights at the front, magenta speed numbers, rear lights that go cyan > magenta > orange as the
gears climb, and rims that glow orange-hot when braking hard. The wheels are matte black, with
a line round each tyre that runs cyan > magenta > orange from the wheel's front to its back."""
import importlib.util

import numpy as np

from tool import paths, shapes

_spec = importlib.util.spec_from_file_location("cmyk_peel", paths.SKINS / "TSC_CMYK_Peel" / "design.py")
_peel = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_peel)
C, M = _peel.C, _peel.M
ORANGE = "#ff9a1a"
DARK = "#1e1f22"


BLACK = "#232528"  # the wrap's black
# the wheels (2026-09-25: the user doesn't want the stock chrome covers). All four wheels and
# tyres share one paint. Three takes were shown; the user picked "black" and asked for its line
# a little thicker, running through the colours: "gradient", this car's wheels.
WHEELS = ("black", "stripes", "magenta", "gradient")


def round_wheel(lo, hi):
    """0 at `lo` and 1 at `hi` of the way round each wheel from its front (0) to its back (1),
    over the top and under the bottom alike."""
    def f(p, n):
        zc = np.where(p[:, 2] > 30, shapes.WHEEL_Z[0], shapes.WHEEL_Z[1])
        t = np.abs(np.arctan2(p[:, 1] - shapes.WHEEL_Y, p[:, 2] - zc)) / np.pi
        return np.clip((t - lo) / (hi - lo), 0, 1)
    return shapes.Zone(f)


def wheels(s, take):
    """The wheel covers (outer ring 19-30 cm from the axle, spoked disc 9-19, hub) lose their
    stock mirror chrome; the tyres' sidewalls (28.5-34.5 cm) take stripes."""
    s.paint("wheel covers", "matte", colour=BLACK)
    if take == "black":  # all matte black, one thin magenta line on the sidewall
        s.paint("sidewall", "satin", colour=M, zone=shapes.wheel_ring(31.2, 32.0))
    elif take == "stripes":  # the run in three thin rings: cyan, magenta, orange from the tread in
        for colour, r in ((C, 33.0), (M, 31.8), (ORANGE, 30.6)):
            s.paint("sidewall", "satin", colour=colour, zone=shapes.wheel_ring(r - 0.4, r + 0.4))
    elif take == "magenta":  # the covers' outer ring in satin magenta, the rest black
        s.paint("wheel cover ring", "satin", colour=M)
    elif take == "gradient":  # the black take's line, 1.2 cm instead of 0.8, cyan > magenta > orange,
        # centred on the sidewall that shows beyond the cover (30 to 34.5 cm; the user)
        line = shapes.wheel_ring(31.7, 32.9)
        s.paint("sidewall", "satin", colour=C, zone=line)
        s.paint("sidewall", "satin", colour=M, zone=line & round_wheel(0, 0.5))
        s.paint("sidewall", "satin", colour=ORANGE, zone=line & round_wheel(0.5, 1))


def design(s, wheel_take="gradient", tip=None, hold=None):
    _peel.design(s, more=True, end=ORANGE, tip=tip, hold=hold)
    s.step("Lights", "Cyan brake lights, magenta speed numbers, rear lights by gear in the run's colours, rims that glow orange when braking hard.",
           words="You could update the cmyk one with more tailored lights if you want.", look="rear night")
    s.relight("brake lights", C)
    s.relight("speed numbers", M)
    # one colour per gear band, from the tail's corner inwards; unlit, the bars are dark (not the
    # run's colour), so each lit band shows its true colour
    s.relight("rear lights", [C, C, M, M, ORANGE])
    s.paint("rear light", "satin", colour=DARK)
    # brake heat: the rims glow orange as they heat up under hard braking; glow() tints the paint,
    # so the rims go back to the dark satin
    s.glow("rim", ORANGE, "brake heat")
    s.paint("rim", "satin", colour=DARK)
    s.step("Wheels", "Matte black covers, and a line round each tyre from cyan at the front to orange at the back.",
           words="If you can actually do a radial effect of that line that gradients the cmyk.")
    wheels(s, wheel_take)
