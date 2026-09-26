"""The CMYK peel with a country's flag under the wrap (2026-09-26): matte black torn open in
ragged patches, as TSC_CMYK_Peel_More, showing the flag underneath; or (wear=, the user's next
idea) the flag as the paint itself, worn (WEAR). Costa Rica's blue, white,
red (double), white, blue, draped over the car from one side to the other: red down the spine
to the nose tip, white over the shoulders, blue down the sides, so the chase camera sees the
whole flag across the car. (Stacked by height instead, so each side showed the whole flag, it
put blue down the middle from behind, Thailand's order: not shown.) The inside, the lights and
the wheels take the flag's colours. Another country is a line in FLAGS and a skin that loads
this design."""
import importlib.util

import numpy as np

from tool import paths, shapes

_spec = importlib.util.spec_from_file_location("cmyk_black_tail", paths.SKINS / "TSC_CMYK_BlackTail" / "design.py")
_tail = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tail)
_cmyk = _tail._more._peel._cmyk
BLACK, DARK = _tail.BLACK, _tail.DARK

# a flag: its stripes from the car's left side over the top to its right side, (colour, share).
# The blue is a touch lighter than the flag's navy (#002b7f) so it shows against the black wrap.
FLAGS = {
    "costa rica": dict(stripes=[("#0a3a9e", 1), ("#f4f4f2", 1), ("#ce1126", 2), ("#f4f4f2", 1), ("#0a3a9e", 1)],
                       name="Costa Rica"),
}
# the flag hangs from a line along the car: at the floor's height (cm), dropping under the nose so
# the nose's narrow tip is red all over (on the line, the stripes fanned out like a sunburst)
AXIS_Y, NOSE_DROP = 15, 30


def axis_y(p):
    return AXIS_Y - NOSE_DROP * np.clip((p[:, 2] - 140) / 60, 0, 1)


def angle(p):
    """Degrees round the car from straight up, over a line along the car at AXIS_Y: +90 down the
    left side, -90 down the right, and held there below the line."""
    return np.degrees(np.arctan2(p[:, 0], np.maximum(p[:, 1] - axis_y(p), 1e-3)))


def right_of(deg):
    """The part of the car right of the plane through that line at `deg` round (a crisp edge,
    measured in cm from the plane)."""
    def dist(p, n):
        r = np.hypot(p[:, 0], np.maximum(p[:, 1] - axis_y(p), 1e-3))
        return r * np.sin(np.radians(deg - angle(p)))
    return shapes.field(dist)


def drape(s, where, stripes, paint=True, finish="satin", keep_level=True):
    """The flag's stripes on parts, each where it falls round the car: painted, or (paint=False)
    as the colour of their lights."""
    total = sum(w for _, w in stripes)
    edge, zone = 90.0, None
    for colour, w in stripes:
        if paint:
            s.paint(where, finish, colour=colour, zone=zone)
        else:
            s.relight(where, colour, zone=zone, keep_level=keep_level)
        edge -= 180.0 * w / total
        zone = right_of(edge)


def across(s, where, stripes, half_span, finish="satin"):
    """The flag's stripes straight across a part from tip to tip, centred on the car (the front
    wing: its twins share one paint, so the stripes go by the distance from the middle)."""
    total = sum(w for _, w in stripes)
    s.paint(where, finish, colour=stripes[0][0])
    edge = 1.0
    for (colour, w), (_, prev) in zip(stripes[1:], stripes):
        edge -= 2.0 * prev / total
        if edge <= 0:  # past the middle: a symmetric flag is done
            break
        s.paint(where, finish, colour=colour, zone=shapes.stripe(2 * half_span * edge))


def flag_colours(flag):
    """The flag's colours by role: the outer stripe, the next, the centre."""
    st = FLAGS[flag]["stripes"]
    return st[0][0], st[1][0], st[len(st) // 2][0]


# the flag worn rather than torn (the user, 2026-09-26: "the black is too much of a colour do be
# on top of the flag", then "Maybe in this concept its more on looking worn, the flag? Instead of
# torn paint?"): the flag is the paint, over light grey primer, aged (tool/wear.py). "race"
# (TSC_FlagPeel_CostaRica_RaceWorn): stone chips where a race car takes hits, scrapes along the
# sides from the walls, the colours a little faded. "sun" (_SunFaded): washed out by years of
# sun, the clear coat failed in chalky patches on top, a few chips.
WEAR = {"race": dict(fade=0.15, chips=0.06, scrapes=0.6), "sun": dict(fade=0.7, clearcoat=0.08, chips=0.02)}
PRIMER = "#c9c9c4"
WORN_WORDS = "Maybe in this concept its more on looking worn, the flag? Instead of torn paint?"


def inner_car(s, stripes, match):
    """The inner car dark, its accents in the flag's colours; the parts beside the wrap match it."""
    outer, second, centre = stripes[0][0], stripes[1][0], stripes[len(stripes) // 2][0]
    _cmyk.stealth_base(s, seams=False)
    s.paint(["sidepod frame", "mirror", "mirror arm"], match[0], colour=match[1])  # in a flag's colour, the mirrors read as scraps of it
    s.paint(["sidepod grille", "seat belt", "side vent"], "satin", colour=centre)
    s.paint("sidepod panel", "satin", colour=second)
    s.paint("sidepod grille plate", "satin", colour=DARK)
    s.paint(["brake caliper", "brake line", "front wing endplate"], "satin", colour=outer)
    s.paint("cockpit rim", "satin", colour=centre)  # in white, its corners inside the cockpit read as leftover clay
    # the front wing (its plane only, 51 cm each side of the middle): the flag across it
    across(s, "front wing|part", stripes, 51)
    s.glow(["sidepod grille", "side vent"], None, "always on")
    s.glow("brake caliper", None, "brake lights")


def design(s, flag="costa rica", wear=None):
    """wear None: the black wrap torn open over the flag. "race" or "sun": the flag worn (WEAR)."""
    stripes = FLAGS[flag]["stripes"]
    outer, second, centre = flag_colours(flag)
    match = ("matte", BLACK) if wear is None else ("carbon", None)  # the sidepods' inlet rings, the mirrors, the tail
    flag_does = (f"{FLAGS[flag]['name']}'s flag in satin, draped over the body from side to side: "
                 "red down the spine, white over the shoulders, blue down the sides.")
    flag_words = "instead of cmyk, we could do country flags, for example Costa Rica"
    s.clay()
    if wear is None:
        s.step("The flag", flag_does, words=flag_words)
        drape(s, "body", stripes)
        under = s.keep()
        s.step("The black wrap", "Matte black over the whole body, no seam lines. The inner car dark, its accents in the flag's colours.",
               words="Give me another proposition for cmyk tearing concept")
        inner_car(s, stripes, match)
        s.step("Torn open", "The wrap torn off in ragged patches (about half), hard edges and a thin even shadow, the flag showing through.",
               words="cmyk tearing concept")
        s.peel(under, amount=0.45, scale=40, seed=11)
    else:
        s.step("Primer", "The body in light grey primer, the inner car dark with its accents in the flag's colours: "
               "what shows where the paint wears through.", words=WORN_WORDS)
        inner_car(s, stripes, match)
        s.paint("body", "matte", colour=PRIMER)
        under = s.keep()
        s.step("The flag", flag_does, words=flag_words)
        drape(s, "body", stripes)
        s.step("Worn", {"race": "Stone chips down to the primer on the nose, the faces turned forward and low on the sides, "
                                "scrapes along the sides from the walls, the colours a little sun-faded.",
                        "sun": "The flag washed out by years of sun, palest on top, the clear coat gone chalky in patches; "
                               "a few chips."}[wear],
               words=WORN_WORDS)
        s.wear(under, **WEAR[wear])

    s.step("Lights", "Blue brake lights, white speed numbers, rear lights through the flag as the gears climb "
           "(blue, white, red), rims that glow red when braking hard; the inside's lamps in the flag's colours.",
           look="rear night")
    s.relight("brake lights", outer)
    s.relight("speed numbers", second)
    s.relight("rear lights", [outer, outer, second, second, centre])
    s.paint("rear light", "satin", colour=DARK)
    s.glow("rim", centre, "brake heat")
    s.paint("rim", "satin", colour=DARK)
    drape(s, _tail.LIGHTS, stripes, paint=False)
    s.relight(["hub", "brake light"], outer, keep_level=True)
    # the turbo: the game lights the inside of each wheel in the pad's colour; here exhaust heat,
    # which keeps its own (red), as on the CMYK car
    s.glow(_tail.TURBO_WHEELS, centre, "exhaust heat", replacing="turbo", keep_level=True)
    s.glow(_tail.TURBO_REST, outer, "exhaust heat", replacing="turbo", keep_level=True)
    s.glow("rear diffuser", centre, "exhaust heat", zone=_tail.PORTS)
    s.no_glow("rear bumper")

    s.step("Inside", f"The exhaust heat-tinted, the tail in {'the wrap' if wear is None else 'bare carbon'}, a quilted seat.",
           words="what matters is the quality of the entire car")  # the user on the CMYK car, 2026-09-25
    s.paint("exhaust", "brushed titanium", colour="#c9a24a")
    s.paint("exhaust", "brushed titanium", colour="#9a4f9e", zone=shapes.fade("z", -115, -130))
    s.paint("exhaust", "brushed titanium", colour="#3f6fd0", zone=shapes.fade("z", -130, -145))
    s.paint(_tail.TAIL, match[0], colour=match[1])
    s.paint("airbox", "matte", colour="#1a1b1d")
    s.relief("seat", "quilted", depth=0.5, scale=7, replace=True)

    s.step("Wheels", "Matte black covers, and a red line round each tyre.")
    s.paint("wheel covers", "matte", colour=BLACK)
    s.no_glow("wheel ring")
    s.paint("wheel ring", "matte", colour=BLACK)
    s.paint("sidewall", "satin", colour=centre, zone=shapes.wheel_ring(31.5, 33.1))
