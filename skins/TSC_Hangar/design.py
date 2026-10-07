"""TSC_Hangar: a seventies navy carrier jet, its ground crew's markings (the moodboard's B, 2026-10-07)."""

import math

import numpy as np

from tool import course, marks, meshlines, shapes

GULL = "#9a9c95"     # light gull grey, over
WHITE = "#f1f1ec"    # gloss white, under, and in the wheel wells
RED = "#c3262c"      # insignia red: the danger edges
BLACK = "#121214"
COCKPIT = "#5d6266"  # dark gull grey, the cockpit's own

H = math.sqrt(3) / 2
OUTER = marks.polygon([(0, 0), (1, 0), (0.5, H)], "warning triangle")


def triangle_inside(border):
    """The warning triangle's red, `border` of its width in from the outer one's edges: drawn in the outer
    triangle's own frame, so the two laid at one size and centre nest evenly."""
    cy = H / 3 - H / 2  # the incentre, in the outer's frame (its middle at 0, 0)
    r = H / 3           # the inradius
    k = (r - border) / r

    def sd(x, y):
        return k * OUTER.sd(np.asarray(x) / k, (np.asarray(y) - cy) / k + cy)
    return marks.Shape(sd, OUTER.high, "warning triangle's red", OUTER.reach)


CHEVRON = marks.polygon([(0, 0.6), (0.55, 1.2), (1.0, 1.2), (0.45, 0.6), (1.0, 0), (0.55, 0)], "chevron")


def chevrons():
    """Two chevrons side by side, pointing to their left: forward on the car's left side seen from outside (and
    on the right, mirrored): an intake's danger marking, pointing into it."""
    k, c = 0.45, 0.275

    def sd(x, y):
        x, y = np.asarray(x), np.asarray(y)
        return k * np.maximum(CHEVRON.sd((x + c) / k, y / k), CHEVRON.sd((x - c) / k, y / k))
    return marks.Shape(sd, CHEVRON.high * k, "intake danger chevrons", float(np.hypot(0.5, CHEVRON.high * k / 2)))


def walkway(inset, width, corner=2.5):
    """A walkway's outline on each sidepod's top, where the crew steps to climb in, as on a jet's wing root:
    its long sides beside the sidepod top's inner edge (one of the model's lines), `inset` and `inset + width` cm
    from it, from where the edge runs straight back (z +7) to where it turns (z -39); its ends joined across."""
    edge = meshlines.line((56, 63, -20)).between((54.9, 61.4, 6.9), (55.9, 62.8, -39.0))
    a, b = edge.offset(inset), edge.offset(inset + width)
    pts = np.vstack([a.pts, b.pts[::-1]])
    return course.Course(pts, "the walkway", closed=True).rounded(corner).mirrored()


def design(s):
    s.clay()

    s.step("Gull grey over white", "The body in light gull grey, semi-gloss; the side skirts, the car's belly, in "
           "gloss white, filled to the model's own lines.", words="hangar; light gull grey over gloss white")
    s.paint("body", "semi-gloss", colour=GULL)
    belly = (meshlines.panel((42, 19, 63), both=True) | meshlines.panel((13, 20, 183), both=True)
             | meshlines.panel((2, 18, -130)))
    s.paint("body", "gloss", colour=WHITE, zone=belly)

    s.step("The wheel wells and the gear", "The inner car gloss white, as a navy jet's wheel wells and gear legs are; "
           "the dampers chrome, its oleo struts; the cockpit dark gull grey, the seat black; the exhausts burnt "
           "titanium.", words="a seventies navy jet")
    s.paint("inner", "gloss", colour=WHITE)
    s.paint(["damper", "rear damper"], "chrome")
    s.paint("cockpit", "matte", colour=COCKPIT)
    s.paint(["seat", "steering wheel"], "matte", colour=BLACK)
    s.paint("exhaust", "brushed titanium")

    s.step("The wheels", "Each wheel cover gloss white, a red edge round its rim: the red edge a navy jet's gear "
           "doors carry; the rims white, the hubs polished.", words="red danger edges round the intakes and the wheels")
    s.paint("wheels", "gloss", colour=WHITE)
    s.paint("wheel covers", "gloss", colour=RED, zone=shapes.wheel_ring(26.4, 36))  # out over the cover's rim (29.3 cm) and its lip
    s.paint("hub", "polished aluminium")

    s.step("The intakes' red lips", "A red band round each sidepod's inlet, along where the body ends round it.",
           words="red danger edges round the intakes")
    lip = meshlines.line((75, 49, -45)).mirrored()
    s.paint("body", "gloss", colour=RED, zone=lip.strip(5))

    s.step("The intakes' chevrons", "A pair of red chevrons behind each intake, pointing into it: its danger "
           "marking.", words="chevrons warn around the air intakes")
    s.mark("sidepod top", "gloss", chevrons(), size=12, at=(87, 42, -24), colour=RED)

    s.step("The walkways", "A thin black outline on each sidepod's top, where the crew steps to climb in, its long "
           "sides beside the sidepod's inner edge.", words="black lines where the crew may walk")
    s.paint("body", "gloss", colour=BLACK, zone=walkway(3, 16).strip(0.6))

    s.step("The seat's warning triangle", "The ejection seat's warning triangle, red in white, on each side of the "
           "body beside the cockpit.", words="the seat's warning triangle")
    spot = s.mark("body shell", "gloss", OUTER, size=10, at=(33, 69, 34), colour=WHITE)
    s.mark("body shell", "gloss", triangle_inside(0.12), size=spot.size, at=spot.centre, colour=RED)

    s.step("The lights", "The wheel rings and the speed numbers in a navy jet's pale green formation lights; the rear "
           "and brake lights insignia red.", look="rear night")
    s.relight("wheel ring", "#b6f27a", keep_level=True)
    s.relight("speed numbers", "#b6f27a")
    for light in ("rear lights", "brake lights"):
        s.relight(light, RED)
