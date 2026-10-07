"""TSC_Hangar_Moodboard: a seventies navy carrier jet, its squadron's blue running where the air runs (2026-10-07).

The composition: the squadron's blue springs from behind each red-lipped intake, fills the sidepod's flank and the
whole rear haunch, and ends at the tail, trimmed along its top edge by a thin gold line; at the nose it answers as
the nose band, the nose panel's forward-pointing U in blue edged gold, behind a flat black radome. Between them the
airframe stays gull grey over a gloss white belly; red where something bites, black where the crew works; the ageing
follows the air back from the wheels, the intakes and the exhausts."""

import math

import numpy as np
from scipy.spatial import cKDTree

from tool import course, marks, meshlines, noise, shapes

GULL = "#9a9c95"      # light gull grey, over
FRESH = "#8f938d"     # the same grey fresh from the can: touch-ups
WHITE = "#f1f1ec"     # gloss white, under, and in the wheel wells
RED = "#c3262c"       # insignia red: danger
BLACK = "#16171a"     # working black: the crew's marks, the radar
BLUE = "#22386b"      # squadron blue
GOLD = "#f2b52a"      # squadron gold
COCKPIT = "#5d6266"   # dark gull grey, the cockpit's own
NONSKID = "#4b4e50"   # the walkways' grit
OLIVE = "#5a5a3c"     # olive webbing
GRIME = "#2f2a24"     # salt, exhaust and hydraulic fluid

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


BOLT = marks.polygon([(0.30, 1.00), (0.62, 1.00), (0.47, 0.60), (0.70, 0.60), (0.22, 0.00), (0.36, 0.44),
                      (0.14, 0.44)], "the squadron's bolt")


def walkway_edge():
    """The sidepod top's inner edge, one of the model's lines, where it runs straight back (z +7 to -39)."""
    return meshlines.line((56, 63, -20)).between((54.9, 61.4, 6.9), (55.9, 62.8, -39.0))


def walkway(inset, width, corner=2.5):
    """A walkway's outline on each sidepod's top, where the crew steps to climb in, as on a jet's wing root:
    its long sides beside the sidepod top's inner edge, `inset` and `inset + width` cm from it; its ends joined
    across."""
    edge = walkway_edge()
    a, b = edge.offset(inset), edge.offset(inset + width)
    pts = np.vstack([a.pts, b.pts[::-1]])
    return course.Course(pts, "the walkway", closed=True).rounded(corner).mirrored()


DECK_BAND = 14  # cm of the deck the blue covers inside the haunch's crease


def deck_lines(width):
    """The blue's edge on the deck, a line `width` cm inside the haunch's crease (one of the model's lines, from the
    sidepod's back corner to the tail), the line halfway, and the deck's own panel, which ends both at its back edge."""
    crease = meshlines.line((58, 63, -81))
    a = crease.offset(width)
    inward = 1 if np.abs(a.pts[:, 0]).mean() < np.abs(crease.pts[:, 0]).mean() else -1
    edge = a if inward == 1 else crease.offset(-width)
    return edge, crease.offset(inward * width / 2), meshlines.panel((-3, 75, -97))


def toward_tail(c, cm):
    """The course carried on `cm` past its end nearest the tail."""
    return c.extended(end=cm) if c.pts[-1, 2] < c.pts[0, 2] else c.extended(start=cm)


def inside_seen_from_above(outline, facing_up=0.5, soft=shapes.SOFT):
    """The area inside a closed outline lying on a top face (both sides), seen from above: a signed distance in cm
    to the outline in plan (x, z), positive inside, on surfaces facing up."""
    ring = outline.pts[:, [0, 2]].astype(np.float64)
    tree = cKDTree(ring)
    a, b = ring, np.roll(ring, -1, axis=0)

    lo, hi = ring.min(0) - 1.0, ring.max(0) + 1.0
    ax, az, bx, bz = a[None, :, 0], a[None, :, 1], b[None, :, 0], b[None, :, 1]
    run = np.where(bx == ax, 1e-9, bx - ax)

    def f(p, n):
        out = np.full(len(p), -10.0)
        q = np.stack([np.abs(p[:, 0]), p[:, 2]], 1).astype(np.float64)
        box = np.flatnonzero(np.all((q >= lo) & (q <= hi), axis=1) & (n[:, 1] >= facing_up))
        for k in range(0, len(box), 4096):
            i = box[k:k + 4096]
            d, _ = tree.query(q[i], workers=-1)
            x, z = q[i, 0:1], q[i, 1:2]
            zc = az + (x - ax) * (bz - az) / run
            inside = (((ax > x) != (bx > x)) & (zc > z)).sum(1) % 2 == 1  # even-odd crossings along +z
            out[i] = np.where(inside, d, -d)
        return out
    return shapes.field(f, soft)


def streaks(lo, hi, top, bottom, seed=0, amount=0.5):
    """Grime streaking back with the air: long smears along the car between lengths `hi` (where it starts, the
    heaviest) and `lo`, from height `bottom` up to `top`, fading upward and as it runs back. Weights, not a shape."""
    def f(p, n):
        w = np.zeros(len(p), np.float32)
        i = np.flatnonzero((p[:, 2] <= hi) & (p[:, 2] >= lo) & (p[:, 1] <= top) & (p[:, 1] >= bottom - 5))
        if not len(i):
            return w
        q = p[i].astype(np.float32) / np.array([3.0, 2.2, 26.0], np.float32)
        q[:, 0] = np.abs(q[:, 0])
        s = noise.fbm(q, 3, seed)
        body = np.clip((s - 0.42) * 3.0, 0, 1)
        run = np.clip((p[i, 2] - lo) / max(hi - lo, 1e-3), 0, 1)
        low = np.clip((top - p[i, 1]) / max(top - bottom, 1e-3), 0, 1)
        w[i] = amount * body * (0.35 + 0.65 * run) * low
        return w
    return shapes.Zone(f, label="grime streaking back")


def design(s):
    s.clay()

    s.step("Gull grey over white", "The body in light gull grey, semi-gloss; the side skirts, the car's belly, in "
           "gloss white, filled to the model's own lines, its masked edge running the length of the car.",
           words="light gull grey over gloss white; the airframe, over; under, and in the wells")
    s.paint("body", "semi-gloss", colour=GULL)
    belly = (meshlines.panel((42, 19, 63), both=True) | meshlines.panel((13, 20, 183), both=True)
             | meshlines.panel((2, 18, -130)))
    s.paint("body", "gloss", colour=WHITE, zone=belly)

    s.step("The squadron's blue", "From behind each intake back to the tail: the sidepod's flank below its "
           "shoulder and the whole rear haunch in squadron blue, as a navy jet wears its colours on its tail.",
           words="An invented squadron in blue and gold. Its colours can run big; marks that run where the air runs")
    haunch = meshlines.panel((67, 41, -80), both=True)
    pod = meshlines.panel((76, 60, -25), both=True) & ~shapes.facing("up", 0.6, soft=0.02)
    shoulder = meshlines.line((85, 56, -12), kind="rounded").mirrored()
    edge, middle, deck = deck_lines(DECK_BAND)
    over = toward_tail(middle, 10).mirrored().strip(DECK_BAND + 0.6) & deck
    s.paint("body", "semi-gloss", colour=BLUE, zone=haunch | over | shoulder.inked_edge(pod), across=True)

    s.step("The gold trim", "A thin gold line along the blue's edge, beside the haunch's crease on the deck and "
           "along the sidepod's shoulder, running back to the tail.", words="blue and gold where it's proud")
    trim = (toward_tail(edge, 10).mirrored().inked(1.0) & deck) | shoulder.inked(1.0)
    s.paint("body", "gloss", colour=GOLD, zone=trim, across=True)

    s.step("The radome and the nose band", "The nose's tip in flat black, its radome; behind it the nose panel's "
           "forward-pointing U in squadron blue, edged in gold, back to the nose fin's plate.",
           words="working black: the radar; its colours can run big")
    s.paint("nose tip", "matte", colour=BLACK, zone=shapes.front_of(196))
    nose = meshlines.panel((-2, 56, 162)) & shapes.front_of(146.5)
    s.paint("body", "semi-gloss", colour=BLUE, zone=nose, across=True)
    u = meshlines.line((0, 49, 187)).between((-12.4, 58, 147), (12.4, 58, 147))
    s.paint("body", "gloss", colour=GOLD, zone=u.inked(1.0), across=True)

    s.step("The intakes' red lips", "A red band round each sidepod's inlet, along where the body ends round it.",
           words="red where it's dangerous")
    lip = meshlines.line((75, 49, -45)).mirrored()
    s.paint("body", "gloss", colour=RED, zone=lip.strip(5))

    s.step("The squadron's emblem", "The emblem on each sidepod's flank, behind the intake, where a navy jet "
           "carries its squadron's badge: a gold bolt on a blue disc in a thin gold ring.",
           words="Its emblem: a gold lightning bolt on a blue disc in a thin gold ring")
    ring = s.mark("sidepod top", "gloss", marks.disc(), size=20, at=(87, 42, -24), colour=GOLD)
    s.mark("sidepod top", "gloss", marks.disc(), size=ring.size * 0.9, at=ring.centre, colour=BLUE)
    s.mark("sidepod top", "gloss", BOLT, size=ring.size * 0.36, at=ring.centre, colour=GOLD)
    ring = s.mark("tail panel", "gloss", marks.disc(), size=18, at=(0, None, -146), colour=GOLD)
    s.mark("tail panel", "gloss", marks.disc(), size=ring.size * 0.9, at=ring.centre, colour=BLUE)
    s.mark("tail panel", "gloss", BOLT, size=ring.size * 0.36, at=ring.centre, colour=GOLD, up=(0, 0, 1))

    s.step("The walkways", "Each sidepod's top, where the crew steps to climb in: non-skid grit inside a thin black "
           "outline, beside the sidepod's inner edge.", words="black where the crew works; non-skid grit")
    outline = walkway(3, 16)
    s.paint("body", "textured wrap", colour=NONSKID, zone=inside_seen_from_above(outline))
    s.paint("body", "gloss", colour=BLACK, zone=outline.strip(0.6))

    s.step("The seat's warning triangle", "The ejection seat's warning triangle, red in white, on each side of the "
           "body beside the cockpit.", words="red where it's dangerous")
    spot = s.mark("body shell", "gloss", OUTER, size=10, at=(33, 69, 34), colour=WHITE)
    s.mark("body shell", "gloss", triangle_inside(0.12), size=spot.size, at=spot.centre, colour=RED)

    s.step("Sun, salt and touch-ups", "The paint chalky where the sun hits the tops; salt and hydraulic grime "
           "streaking back low from the wheels and the intakes; fresher grey on the panels the crew opens.",
           words="Weathered, but cared for; paint touched up in fresher patches, panel by panel; grime collecting "
           "low and behind the wheels and running back with the air")
    s.wear(s.keep(), fade=0.22, chips=0.0)
    s.paint("body", "semi-gloss", colour=FRESH, zone=meshlines.panel((35, 73, -64), both=True))
    grime = (streaks(70, 150, 34, 17, seed=3) | streaks(-140, -40, 36, 15, seed=5, amount=0.45))
    s.paint("body", "satin", colour=GRIME, zone=grime, across=True)

    s.step("The wheel wells and the gear", "The inner car gloss white, as a navy jet's wheel wells and gear legs are; "
           "the dampers chrome, its oleo struts; the cockpit dark gull grey, the seat black, the belts olive webbing; "
           "the intake screens bare metal; the tail's frame and exhausts titanium, heat-stained.",
           words="a seventies navy jet; olive webbing; oleo chrome; heat-blued titanium")
    s.paint("inner", "gloss", colour=WHITE)
    s.paint(["damper", "rear damper"], "chrome")
    s.paint(["cockpit", "cockpit tub"], "matte", colour=COCKPIT)
    s.paint(["seat", "steering wheel"], "matte", colour=BLACK)
    s.paint("seat belt", "webbing", colour=OLIVE)
    s.paint("sidepod grille plate", "polished aluminium")
    s.paint(["tail frame", "exhaust", "rear bumper"], "brushed titanium")

    s.step("The wheels", "Each wheel cover gloss white, a red edge round its rim: the red edge a navy jet's gear "
           "doors carry; the rims white, the hubs polished; the tyres plain, their moulded markings only.",
           words="red danger edges round the wheels")
    s.paint("wheels", "gloss", colour=WHITE)
    s.paint("wheel covers", "gloss", colour=RED, zone=shapes.wheel_ring(26.4, 36))
    s.paint("hub", "polished aluminium")
    s.tyre_tread("TR-03")  # an aircraft tyre's: plain sidewalls, grooves round the tread

    s.step("The lights", "The wheel rings and the speed numbers in a navy jet's pale green formation lights; the rear "
           "and brake lights insignia red.", look="rear night")
    s.relight("wheel ring", "#b6f27a", keep_level=True)
    s.relight("speed numbers", "#b6f27a")
    for light in ("rear lights", "brake lights"):
        s.relight(light, RED)
