"""TSC_Water, concept C: Wake. A powerboat's bow wave peeling off the car.

The body is deep ocean; over it, crests of cyan peel back from the nose like the bow wave a Class 1
offshore boat throws at speed: a small crest on the nose, the big bow wave sweeping round the cockpit
and back along the flanks and sidepods, and a stern wave over the deck's sides and the tail, either
side of a deep keel down the deck's middle (where the game draws the number and name). Each crest is three layers stacked like water
sheets, cyan, then bright cyan, then the brightest at its lip, and over the top they meet as
chevrons pointing forward (the wake the chase cameras see from behind). The edges rake back the
same way on both sides: a V over the top at about the wake's own angle, and down the sides they
come forward, so they climb as they run back. Wet-look gloss all over; wheels and inner car one
deep navy.
"""
import numpy as np

from tool import carmap, shapes

DEEP = "#00699A"       # deep ocean, the base
CYAN = "#00ADD9"       # cyan crest
BRIGHT = "#1FD6F2"     # bright cyan crest
BRIGHTEST = "#8CF0FA"  # the crest's lip, the thinnest layer
NAVY = "#06263A"       # wheels and the inner car
FINISH = "wet look"

WORDS = ("I want to build a car that is perfect for water maps.  In this case I want to first paint "
         "the car with layers of cyan all over the place.")

NOSE_Z = 215.0
RAKE_TOP = 2.0    # over the top, an edge runs this many cm back for each cm out from the middle (a V of ~27 degrees each side)
RAKE_SIDE = 2.0   # down the sides, this many cm forward for each cm down from the shoulder (the edges climb as they run back)
RIPPLE, RIPPLE_LEN = 2.0, 70.0   # the crest edges' broad wave (cm), kept small where the body narrows

# The wake's crests, by how far back they sit (cm from the nose's tip along the top's middle, see
# _wake): each one cyan, bright, then the brightest lip, then deep water behind it. The nose crest's
# lip stops short of the nose fin's plate (57..97 on this scale).
CRESTS = [
    (None, 20.0, 34.0, 50.0),       # the nose crest: from the tip to its lip
    (104.0, 154.0, 194.0, 214.0),   # the bow wave: over the bonnet, round the cockpit, along the sidepods
    (240.0, 290.0, 320.0, 342.0),   # the stern wave: the deck's sides, the rear flanks and the tail
]
# The keel: a deep strip down the deck's middle from the cockpit to the tail, as wide as the number
# and engine cover panels (x 20.1 each side, their own edges), so the game's number and name sit on
# deep water and the stern wave's V meets under it, as a wake fans out either side of a hull.
KEEL_X, KEEL_FROM = 20.1, -40.0


def _wake(p):
    """How far back a point sits in the wake (cm), and the scale to turn it into cm on the surface.
    Its lines are the crests' edges: a forward V over the top, coming forward down the sides."""
    m = carmap.load()
    x, y, z = np.abs(p[:, 0]), p[:, 1], p[:, 2]
    Z = m.sec["Z"]
    sh_x, sh_y = np.interp(z, Z, m.sec["sh_x"]), np.interp(z, Z, m.sec["sh_y"])   # the map's shoulder
    drop = np.maximum(0.0, sh_y - y)                       # how far below the shoulder (the sides)
    out = np.where(drop > 0, sh_x, np.minimum(x, sh_x))    # how far out from the middle (the top)
    w = (NOSE_Z - z) - RAKE_TOP * out + RAKE_SIDE * drop
    t = np.hypot(1, RAKE_TOP) * out + np.hypot(1, RAKE_SIDE) * drop   # along the edge, for its ripple
    w = w + RIPPLE * np.sin(2 * np.pi * t / RIPPLE_LEN)
    g = np.where(drop > 0, np.hypot(1, RAKE_SIDE), np.hypot(1, RAKE_TOP))
    return w, g


def _between(a, b):
    """The part of the wake between two of its lines, a crisp edge on each (a None: from the nose)."""
    def dist(p, n):
        w, g = _wake(p)
        d = (b - w) if a is None else np.minimum(w - a, b - w)
        return (d / g).astype(np.float32)
    return shapes.field(dist)


def design(s):
    s.clay()

    s.step("Deep water", "The whole body in deep ocean blue, wet-look gloss: the water the crests rise from.",
           words=WORDS)
    s.paint("body", FINISH, colour=DEEP)

    s.step("The bow wave", "Crests of cyan peel back from the nose, each a stack of cyan, bright cyan and "
           "the brightest at its lip: a small one on the nose, the big bow wave round the cockpit and back "
           "along the flanks and sidepods, and a stern wave over the deck and tail, each a V over the top; "
           "a deep keel down the deck's middle.", words=WORDS)
    skin = ~shapes.area("under") & shapes.outside(0.25)   # the outer body; underneath stays deep
    for start, bright, lip, end in CRESTS:
        s.paint("body", FINISH, colour=CYAN, zone=_between(start, bright) & skin)
        s.paint("body", FINISH, colour=BRIGHT, zone=_between(bright, lip) & skin)
        s.paint("body", FINISH, colour=BRIGHTEST, zone=_between(lip, end) & skin)
    s.paint("sidepod inlet", FINISH, colour=DEEP)          # the intakes stay deep water
    s.paint("wing pylon", FINISH, colour=DEEP)             # the struts under the nose too
    keel = shapes.field(lambda p, n: np.minimum(KEEL_X - np.abs(p[:, 0]), KEEL_FROM - p[:, 2]))
    s.paint("body", FINISH, colour=DEEP, zone=keel)

    s.step("Wheels and inner car", "The wheels and the whole inner car in one deep navy.", words=WORDS)
    s.paint("inner", FINISH, colour=NAVY)
    s.paint("wheels", FINISH, colour=NAVY)
