"""Rescue v2: the snow rescue car (TSC_Snow) with more detail, shaped by the car's own curvature.
Signal orange; a black lower edge and a band of silver and orange checks that follow the side's
curve, rising with the tail; silver chevrons on the tail's deck; NO STEP on the deck and the side
box's top, each side, as small boxed placards; silver hazard stripes across the rear quarter panels; studded snow tyres; amber rear
lights."""
import numpy as np

from tool import levels, shapes

WORDS = "based on what you know can you design a skin or use the Rescue as a v2, to add more details"
ORANGE, AMBER = "#ff5a0f", "#ffb000"
CHECK = 15.0      # cm: a check's length along the car, twice a row's height
CHECK_FROM = 72.0  # z: a check's edge at the band's front, the body's edge there (z 69.8 to 72.2)
NOTES = ("Do an interval lines with DO NOT STEP text. (note 4, a line along the deck's left edge); right side "
         "too ... added more continueous do not step; Continue the do not step (note 5, round the side box's top); "
         "it should actually be NO STEP; Remove the dashes, only include certain spots for no step. (note 7)")
SIGN, SIGN_H = "NO STEP", 2.6  # the words and their capitals' height (cm)
# Each placard's middle on the car's left (x, z; the right mirrors it) and its slant: on the deck beside
# the rear flank's seam, where the user's arrow pointed (note 10), reading along the seam (34 degrees off
# the car's length there); on the side box's top beside its inner edge, where the user drew (note 5).
SIGNS = (((63.3, -68.2), 34), ((53.0, -22.0), 0))
PAD, FRAME = 0.3, 0.2  # cm: the room between the words and the placard's line, and the line (the user's yes, note 9)
QUARTER = "What can we do here in this piece? (note 11, on the right rear quarter panel)"


def _checks(lower=False):
    """The checks' silver blocks: the upper row's start at CHECK_FROM and every 2 CHECK behind it,
    the lower row's in the gaps between."""
    def d(p, n):
        ph = np.mod(p[:, 2] - (CHECK_FROM - CHECK / 2) + CHECK, 2 * CHECK) - CHECK
        inside = CHECK / 2 - np.abs(ph)
        return -inside if lower else inside
    return shapes.field(d)


def _skirt_top(s):
    """The bottom piece's (the side skirt's) top edge along the side, as z and y in cm, smoothed over
    12 cm. Ahead of the sidepods it rises 3 cm above the sixth level, into the band."""
    c = s.canvas("Skin")
    on = s.parts.mask(c.bake, "Skin", "side skirt").reshape(-1) & (np.abs(c.pos[:, 0]) > 5) & (np.abs(c.nrm[:, 0]) > 0.3)
    z, y = c.pos[on, 2], c.pos[on, 1]
    zs = np.arange(-160.0, 220.0, 2.0)
    top = np.array([y[(z >= a) & (z < a + 2)].max(initial=0.0) for a in zs])
    return zs + 1, np.convolve(top, np.ones(6) / 6, mode="same")


def _rows(s):
    """The body above the line between the band's two rows: midway between the fourth and fifth
    levels between, raised by half the bottom piece's rise above the band's foot (the sixth level)
    where it rises into the band, so the two rows stay even there."""
    from tool.noise import smoothstep
    Y4, Y5, Y6 = [next(c[1] for c in levels.curves() if c[0] == n) for n in ("between 4", "between 5", "between 6")]
    zs, top = _skirt_top(s)

    def mid(z):
        return (Y4(z) + Y5(z)) / 2 + np.maximum(0, np.interp(z, zs, top) - Y6(z)) / 2

    def f(p, n):
        z = p[:, 2].astype(np.float64)
        h = p[:, 1] - mid(z)
        g = np.stack([np.zeros(len(h)), np.ones(len(h)), -(mid(z + 0.5) - mid(z - 0.5))], 1)
        nn = n.astype(np.float64)
        gs = np.linalg.norm(g - (g * nn).sum(1, keepdims=True) * nn, axis=1)
        return smoothstep(-0.05, 0.05, h / np.maximum(gs, 0.05)).astype(np.float32)
    return shapes.Zone(f, label="rows")


def _chevrons(width=4.0, slope=0.75, z0=-152.0, z1=-132.0):
    """Chevrons across the tail panel, pointing forward: stripes `width` cm wide (square to them),
    as many gaps between, their arms falling back `slope` cm per cm out from the middle; the panel's
    seams their ends."""
    k = np.sqrt(1 + slope * slope)
    period = 2 * width * k

    def d(p, n):
        u = p[:, 2] + slope * np.abs(p[:, 0])
        ph = np.mod(u - z1 + period / 4, period) - period / 2
        return (period / 4 - np.abs(ph)) / k
    return shapes.field(d) & shapes.band(z0, z1)


def _stripes(width=4.0, slope=0.75):
    """Hazard stripes `width` cm wide (square to them), as many gaps between, at the tail chevrons' slant
    (falling back `slope` cm per cm out from the middle), mirrored side to side."""
    k = np.sqrt(1 + slope * slope)
    period = 2 * width * k

    def d(p, n):
        ph = np.mod(p[:, 2] + slope * np.abs(p[:, 0]), period) - period / 2
        return (period / 4 - np.abs(ph)) / k
    return shapes.field(d)


def design(s):
    s.clay()
    s.step("Signal orange", "The body in gloss signal orange; below the lowest side level, rising with the tail, "
           "gloss black.", words=WORDS)
    s.paint("body", "gloss", colour=ORANGE)
    s.paint("body", "gloss black", zone=levels.below("between 6") | levels.below("bottom edge"))
    s.paint("side skirt", "gloss black")  # on round the nose, under the front flank and the nose

    s.step("The check band", "Two rows of silver and orange checks along each side between the levels, from the tail "
           "to the front wheel opening, on the body only: the bottom piece keeps its black.", words=WORDS)
    band = levels.band("between 3", "between 6")
    upper = _rows(s)
    s.paint("body", "gloss", colour=ORANGE, zone=band)
    s.paint("body", "reflective tape", zone=band & (upper & _checks() | ~upper & _checks(lower=True)))

    s.step("The tail", "Silver chevrons on the tail's deck, pointing forward.", words=WORDS)
    s.paint("tail panel", "reflective tape", zone=_chevrons())

    s.step("The rear quarter panels", "Silver and orange hazard stripes across the angled panels behind the "
           "cockpit, at the tail chevrons' slant.", words=QUARTER)
    s.paint("rear quarter panel", "reflective tape", zone=_stripes())

    s.step("No step", "NO STEP in black on each side, a small placard with a thin black box round the words, facing "
           "outward: on the deck beside the rear flank's seam, where the user's arrow pointed, reading along the "
           "seam; and on the side box's top beside its inner edge, where the user drew the line.",
           words=NOTES + "; NO STEP as a small placard ... Try it?: yes (note 9)")
    for (x, z), slant in SIGNS:
        s.placard(SIGN, "body shell", at=(x, None, z), colour="black", font="teko", weight=600, height=SIGN_H,
                  pad=PAD, frame=FRAME, turn=slant)

    s.step("Wheels and inner car", "Black wheels with orange rings, studded snow tyres, the inner car and the inlets' "
           "insides dark grey, black frames round the inlets.", words=WORDS)
    s.paint("wheels", "satin black")
    s.paint("wheel cover ring", "gloss", colour=ORANGE)
    s.tyre_tread("TR-08")
    s.paint("inner", "dark grey satin")
    s.paint("sidepod inlet", "dark grey satin")
    s.paint("sidepod frame", "gloss black")

    s.step("Lights", "Orange speed numbers and wheel lights; amber rear lights (red when braking).", words=WORDS,
           look="rear night")
    s.relight("speed numbers", ORANGE)
    s.relight("rear lights", AMBER)
    s.relight("wheel ring", ORANGE, keep_level=True)
