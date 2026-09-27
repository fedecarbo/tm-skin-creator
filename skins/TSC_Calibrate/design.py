"""The calibration car (2026-09-27): a test chart to set the viewer's day and night against the
game's four moods. Nothing on it is for looks. Every patch is a known colour where the game's
chase cameras (Cam 1 and 2 from behind, Cam 3 over the cockpit) see it standing still, so an F12
screenshot and the viewer's render of the same camera can be set side by side (`tool.snap
--cams`). The key is in notes.md.

The greys and colours are the ColorChecker Classic's (sRGB), the photographer's standard chart."""

from tool import shapes

WORDS = ("a car that will help you calibrate the moods? Something I can do later with my pc; "
         "maybe you can compare the 4 moods that trackmania has")

# the ColorChecker's neutral row, black to white, and pure black and white beyond it
GREYS = ["#343434", "#555555", "#7a7a79", "#a0a0a0", "#c8c8c8", "#f3f3f2"]
PURE_BLACK, PURE_WHITE = "#000000", "#ffffff"
CARD = GREYS[2]  # neutral 5, the grey card: the rest of the car
# the ColorChecker's primaries and secondaries: on the car's left red, green, blue; on its right
# cyan, magenta, yellow, from the middle outwards
LEFT_COLOURS = ["#af363c", "#469449", "#383d96"]
RIGHT_COLOURS = ["#0885a1", "#bb5695", "#e7c71f"]
# one colour for every glow, so the kinds compare with each other
GLOW = "#00b4ff"
LINE = "#000000"  # the thin lines between patches of one colour


def columns(edges, gap=0.0):
    """Zones between successive |x| edges (cm from the middle), on both sides: mirrored, as the
    inner car's shared paint is anyway. gap: cm left out either side of each edge."""
    return [shapes.Zone(lambda p, n, a=a, b=b: _between(abs_x(p), a + gap, b - gap)) for a, b in zip(edges, edges[1:])]


def abs_x(p):
    return abs(p[:, 0])


def _between(v, a, b, soft=0.2):
    import numpy as np
    return np.clip(0.5 + np.minimum(v - a, b - v) / soft, 0, 1)


def x_band(a, b):
    """Between x = a and x = b (cm, the car's left is +x)."""
    return shapes.Zone(lambda p, n: _between(p[:, 0], min(a, b), max(a, b)))


def design(s):
    s.clay()
    s.step("Grey card", "The whole car in one flat mid grey, the photographer's grey card, and the "
           "game's own lamps off, but for the speed numbers, rear lights and brake lights.", words=WORDS)
    s.paint(["body", "wheel covers", "inner"], "matte", colour=CARD)
    s.no_glow(STOCK_GLOWS)

    s.step("Grey scale", "Across the flat top of the tail, black on the car's left to white on its "
           "right: the chart's six greys, pure black and pure white on the corners beyond.", words=WORDS, look="rear")
    edges = [31.2, 20.8, 10.4, 0, -10.4, -20.8, -31.2]  # the tail panel's width, left to right
    for grey, a, b in zip(GREYS, edges, edges[1:]):
        s.paint("tail panel", "matte", colour=grey, zone=x_band(a, b))
    s.paint("tail corner|left", "matte", colour=PURE_BLACK)
    s.paint("tail corner|right", "matte", colour=PURE_WHITE)

    s.step("Colours", "The deck either side of the number: red, green and blue on the car's left, "
           "cyan, magenta and yellow on its right, from the middle out.", words=WORDS, look="rear")
    deck = [20.5, 29.5, 38.5, 47.5]
    beside = shapes.band(-129, -86)  # beside the engine cover's panel, square to the grey scale
    for colours, side in ((LEFT_COLOURS, shapes.left()), (RIGHT_COLOURS, shapes.right())):
        for colour, zone in zip(colours, columns(deck)):
            s.paint("engine cover|part", "matte", colour=colour, zone=zone & side & beside)

    s.step("Finishes", "The same grey four ways beside the cockpit, both sides alike, from the middle "
           "out: flat, satin, gloss and chrome, with thin black lines between.", words=WORDS, look="rear")
    band = shapes.band(-88, 12)
    ring = [20.5, 37, 53, 69, 88]
    s.paint(FINISH_PARTS, "matte", colour=LINE, zone=band & columns([20.5, 88])[0])
    for finish, zone in zip(["matte", "satin", "gloss", "chrome"], columns(ring, gap=0.7)):
        s.paint(FINISH_PARTS, finish, colour=None if finish == "chrome" else CARD, zone=band & zone)

    s.step("Glows", "A row across the back under the tail, both sides alike, from the middle out: "
           "always on, night only, front lights, brake lights and the game's energy glow, all in one "
           "light blue on black; the speed numbers, rear lights, brake lights and the cockpit's lamps "
           "in it too, and a white steering wheel.", words=WORDS, look="rear night")
    row = shapes.facing((0, 0, -1), at_least=0.5) & shapes.above(48)
    for kind, zone in zip(GLOW_KINDS, columns([0, 10, 20, 30, 40, 51], gap=0.6)):
        s.paint("tail frame", "matte", colour=PURE_BLACK, zone=row & zone)
        s.glow("tail frame", GLOW, kind, zone=row & zone)
        s.paint("tail frame", "matte", colour=PURE_BLACK, zone=row & zone)  # glow() tints the paint too
    s.paint("digit display", "matte", colour="#0d0d0d")  # dark behind the numbers, as stock
    s.relight(["speed numbers", "rear lights", "brake lights"], GLOW)
    s.glow("cockpit tub", GLOW, "always on", replacing="always on", keep_level=True)
    s.paint("steering wheel", "matte", colour=GREYS[-1])


FINISH_PARTS = ["rear quarter panel", "sidepod top", "body shell"]
# the glow row, from the middle out
GLOW_KINDS = ["always on", "night only", "front lights", "brake lights", "energy"]

# every inner part with a stock glow (the stock Details_I, 2026-09-27), but for the three relit above
STOCK_GLOWS = ["airbox", "antenna", "brake caliper", "brake line", "damper", "driveshaft", "exhaust", "floor rail",
               "front bulkhead", "front wing", "front wing endplate", "hub", "hub bracket", "lower wishbone", "nose inner",
               "pushrod", "rear arm", "rear bumper", "rear bumper corner", "rear strake", "rear undertray", "rim",
               "side vane", "side vent", "sidepod boss", "sidepod frame", "sidepod grille", "sidepod grille plate",
               "sidepod panel", "sidepod strut", "steering column", "steering wheel", "tail frame", "tie rod",
               "upper wishbone", "upright cover", "wheel ring", "wing bracket"]
