"""TSC_Water_Depth: concept A of TSC_Water, a depth chart on the car.

Five flat satin layers of cyan stacked by height, like the depth tints of a bathymetric chart:
the shallows on the car's highest ground (the cockpit's collar, the deck's crest, the bonnet's
spine), stepping down through three cyans to deep water along the sills and underneath. Each
level is a height that follows the car's length (it runs down the bonnet with the nose), placed
on the body's steep slopes, never on its flat tops, so every step is a clean edge.
"""
import numpy as np

from tool import shapes

WORDS = "paint the car with layers of cyan all over the place"

# light to dark, the shallows first: one hue, stepped in lightness (L* 86, 73, 63, 49, 32) so each
# step still reads under a bright top light, where the closer first cut of these pales melted together.
# The shallows are kept colourful (chroma 29, not 24): paler and greyer, the top read near-white, an
# ice car; darker (L* 83), it merged with the shelf from above and the layers were lost.
SHALLOWS, SHELF, CYAN, SLOPE, DEEP = "#86E5F2", "#3EC4DE", "#12A6C6", "#097DA0", "#06506E"
NAVY = "#0A2433"  # the wheels and the inner car

# Each level: its height (y, cm) along the car's length (z, cm: tail -165, nose 215). Below it
# is deeper water. They sit where the body is steep, clear of its flat tops (the sidepods' and
# the tail's at y 58 to 66, the bonnet's crest), so no edge wanders over a flat panel.
LEVELS = [
    # shallows / shelf: the whole deck crest is shallows back to z -125, so the number and name
    # panels (z -120 to -62) sit in one tint; down the bonnet it follows the crest to the nose
    (SHELF, {-165: 67.5, -110: 67.5, -40: 72, 30: 73, 60: 72, 85: 68, 110: 63.5, 140: 57,
             170: 51, 190: 42.5, 200: 40, 215: 34}),
    # shelf / cyan: above the sidepods' tops (cyan); behind them it drops below the rear
    # shoulder, so the deck's flanks are a shelf round the shallows
    (CYAN, {-165: 57, -60: 57, -50: 66.5, 30: 66.5, 60: 66, 85: 64, 110: 59, 140: 53.5,
            170: 48.5, 190: 41, 215: 32}),
    # cyan / slope: across the flanks; on the nose it runs above the lip
    (SLOPE, {-165: 50, -40: 51, 60: 51, 85: 55, 110: 53, 140: 49.5, 170: 45, 190: 35, 215: 28}),
    # slope / deep: the sills, the skirt's ledge and the wing's pylons below
    (DEEP, {-165: 31, 60: 31, 100: 34, 160: 38, 215: 38}),
]


def below(knots):
    """Everything under a level that runs along the car's length."""
    zs = sorted(knots)
    ys = [knots[z] for z in zs]
    return shapes.field(lambda p, n: np.interp(p[:, 2], zs, ys) - p[:, 1])


def design(s):
    s.clay()

    s.step("The depth chart",
           "Five flat satin layers of cyan stacked by height, pale shallows on the top down to "
           "deep water along the sills.", words=WORDS)
    s.paint("body", "satin", colour=SHALLOWS)
    for colour, knots in LEVELS:
        s.paint("body", "satin", colour=colour, zone=below(knots))
        if colour == CYAN:  # the tail, a piece of its own behind a real gap, steps down a tint
            s.paint(["tail panel", "tail corner"], "satin", colour=CYAN)

    s.step("Wheels and inner car", "The wheels and the inner car in one deep navy.", words=WORDS)
    s.paint("wheels", "satin", colour=NAVY)
    s.paint("inner", "satin", colour=NAVY)
