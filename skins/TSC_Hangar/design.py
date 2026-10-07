"""TSC_Hangar: a seventies navy carrier jet, its ground crew's markings (2026-10-07), its materials and
details painted by a second agent from the car's brand book, the first test of a visual language."""

import math

import numpy as np

from tool import course, marks, meshlines, noise, shapes
from tool.noise import smoothstep

GULL = "#9a9c95"     # light gull grey, over
WHITE = "#f1f1ec"    # gloss white, under, and in the wheel wells
RED = "#c3262c"      # insignia red: the danger edges
BLACK = "#121214"
COCKPIT = "#5d6266"  # dark gull grey, the cockpit's own
# the brand book's palette
TOUCHUP = "#a4a69c"
RADOME = "#16171a"
NONSKID = "#4a4d4f"
FORMATION = "#c6df8a"
HARNESS = "#5b5a3c"
GRIME = "#5a5244"
BLUE = "#22386b"     # squadron blue
GOLD = "#f2b52a"     # squadron gold

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


# ---- the brand book's details ----

def inset(shape, border, label=None):
    """A shape `border` of its width in from its own edge, in its own frame: laid at the same size and centre
    as the shape, it leaves an even edge of it all round."""
    return marks.Shape(lambda x, y: shape.sd(x, y) - border, shape.high, label or f"{shape.label}, inset", shape.reach)


def outline(shape, width, label=None):
    """The outline of a shape, `width` of its width wide, inside its edge."""
    return marks.Shape(lambda x, y: np.minimum(shape.sd(x, y), width - shape.sd(x, y)), shape.high,
                       label or f"{shape.label}'s outline", shape.reach)


def hatch(high, corner, line, dot, dot_in):
    """An access panel's outline with a fastener at each corner, as a jet's hatches are painted: a box `high`
    of its width high, its corners rounded by `corner`, its line `line` wide, a dot `dot` across `dot_in` in
    from each corner (all in its width)."""
    box = marks.box(high, corner)
    cx, cy = 0.5 - dot_in, high / 2 - dot_in

    def sd(x, y):
        x, y = np.asarray(x), np.asarray(y)
        ring = np.minimum(box.sd(x, y), line - box.sd(x, y))
        dots = dot / 2 - np.hypot(np.abs(x) - cx, np.abs(y) - cy)
        return np.maximum(ring, dots)
    return marks.Shape(sd, high, "an access hatch", box.reach)


# the squadron's bolt: a lightning bolt from its top right down to a point at its bottom left
BOLT = marks.polygon([(0.35, 1.0), (0.75, 1.0), (0.55, 0.62), (0.75, 0.62), (0.2, 0.0), (0.38, 0.45), (0.18, 0.45)],
                     "the squadron's bolt")
# the rescue arrow, pointing up its own frame: on the top of the car that's towards the cockpit
ARROW = marks.polygon([(0.3, 0), (0.7, 0), (0.7, 0.5), (1.0, 0.5), (0.5, 1.0), (0.0, 0.5), (0.3, 0.5)], "rescue arrow")


def from_above(points, side=None, facing_up=0.3, above=0.0, soft=shapes.SOFT):
    """A zone inside an outline seen from above, (x, z) points in cm, on skin facing up: an area on the car's
    top whose edges are the model's own lines where the outline follows them. side "both": the outline is the
    left side's, mirrored to the right as well. above: only skin higher than that (cm), not what lies under it."""
    P = np.asarray(points, np.float64)
    P = P[::4]  # a point a cm along the outline: its corners round to within 0.05 cm
    lo, hi = P.min(0), P.max(0)
    W, cx, cz = float(hi[0] - lo[0]), float(lo[0] + hi[0]) / 2, float(lo[1] + hi[1]) / 2
    shape = marks.polygon(P, "an outline seen from above")
    up = shapes.facing("up", facing_up)
    bound = (lo - 1, hi + 1)

    def f(p, n):
        x = np.abs(p[:, 0]) if side == "both" else p[:, 0]
        w = np.zeros(len(p), np.float32)
        box = np.flatnonzero((x >= bound[0][0]) & (x <= bound[1][0]) & (p[:, 2] >= bound[0][1]) & (p[:, 2] <= bound[1][1])
                             & (p[:, 1] > above))
        if len(box):
            d = W * shape.sd((x[box] - cx) / W, (p[box, 2] - cz) / W)
            w[box] = smoothstep(-soft / 2, soft / 2, d)
        return w * up(p, n)
    return shapes.Zone(f, label="an outline seen from above")


def antiglare():
    """The top of the nose ahead of the cockpit: from the cockpit surround's front (one of the model's lines) to
    z +114, clear of the nose fin's plate, between the nose's rolled edges (the line facing 17 degrees)."""
    groove = meshlines.line((23, 77, 33))
    front = groove.pts[(groove.pts[:, 2] > 84.5)]
    front = front[np.argsort(np.arctan2(front[:, 0], front[:, 2] - 70))]  # round the front, right to left
    roll = meshlines.line((18, 65, 108), kind="rounded").pts
    roll = roll[(roll[:, 2] > 89) & (roll[:, 2] < 115)]
    roll = roll[np.argsort(roll[:, 2])]
    left = [(x, z) for x, _, z in roll]
    right = [(-x, z) for x, _, z in roll[::-1]]
    back = [(x, z) for x, _, z in front]
    pts = back + left + right
    return from_above(pts, above=58)


def walkway_inside(inset, width, corner=2.5):
    """Inside the walkway's outline, seen from above (its middle line: the outline's line covers the edge)."""
    w = walkway(inset, width, corner)
    return from_above(w.pts[:, [0, 2]], side="both", facing_up=0.5, above=55)


def wedge(r0, r1, angle, width, soft=shapes.SOFT):
    """A short bar across each wheel, square to its rim, from r0 to r1 cm out from the axle and `width` cm wide,
    at `angle` degrees round it (0 straight forward, 90 straight up): all four wheels share their paint, so it's at
    the same place on each, as the car stands."""
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)

    def f(p, n):
        zc = np.where(p[:, 2] > 30, shapes.WHEEL_Z[0], shapes.WHEEL_Z[1])
        dz, dy = p[:, 2] - zc, p[:, 1] - shapes.WHEEL_Y
        along = dz * ca + dy * sa          # out along the bar
        across = -dz * sa + dy * ca        # across it
        d = np.minimum(np.minimum(along - r0, r1 - along), width / 2 - np.abs(across))
        return smoothstep(-soft / 2, soft / 2, d)
    return shapes.Zone(f, label=f"a bar across each wheel at {angle:g} degrees")


def hub_bolt(high, soft=shapes.SOFT):
    """The squadron's bolt on each wheel's hub cap, `high` cm tall, drawn round the axle in the wheel's own plane as
    seen from the car's left (all four covers share their paint: on the right it shows mirrored), on the cap's face."""
    W = high / BOLT.high

    def f(p, n):
        zc = np.where(p[:, 2] > 30, shapes.WHEEL_Z[0], shapes.WHEEL_Z[1])
        d = W * BOLT.sd(-(p[:, 2] - zc) / W, (p[:, 1] - shapes.WHEEL_Y) / W)
        return smoothstep(-soft / 2, soft / 2, d) * smoothstep(0.6, 0.8, np.abs(n[:, 0]))
    return shapes.Zone(f, label="the bolt on each hub cap")


def band_edge():
    """The squadron band's lower edge, one smooth line from the tail to the intake: along the line where the rear
    flank's shoulder turns down (one of the model's lines), then on at the same height along the sidepod's shoulder,
    across the seam (the sidepod top is sewn on), to the intake's frame."""
    turn = meshlines.line((66, 55, -85), kind="rounded")
    P = turn.pts if turn.pts[0, 2] < turn.pts[-1, 2] else turn.pts[::-1]  # from the tail forward
    rear = [tuple(P[i]) for i in np.linspace(0, len(P) - 1, 9).astype(int)]
    pod = [(86.5, 52.6, -40.0), (86.8, 52.5, -30.0), (86.8, 52.4, -20.0), (86.4, 52.3, -10.0)]
    return meshlines.picked(rear + pod).extended(end=4).mirrored()


def band():
    """The squadron band: on the rear flank from the line along its top down to the band's edge; on the sidepod from
    a line beside the walkway (one with the rear flank's top line where they meet) down to the same edge, ending at
    the intake's frame."""
    flank = meshlines.panel((67, 41, -80), both=True)
    pod = meshlines.panel((76, 60, -25), both=True)
    inner = meshlines.line((56, 63, -20)).between((56.0, 61.9, -6.8), (55.9, 62.9, -44.0))
    top = inner.offset(21.5).extended(start=6, end=6).mirrored()  # the walkway's outer line is 19 cm out
    out = shapes.field(lambda p, n: np.abs(p[:, 0]) - 77.4)
    over = shapes.field(lambda p, n: p[:, 1] - np.where(p[:, 2] < -46.1, 56.7 - 0.0534 * (p[:, 2] + 123.9), 52.55))
    edge = band_edge()
    under_gold = shapes.field(lambda p, n: p[:, 1] - 52.1)  # on the sidepod the band never shows below its pinstripe
    return (flank | (pod & top.inked_edge(out) & under_gold)) & edge.inked_edge(over), edge.inked(1.0) & (flank | pod)


def grime(seed=7):
    """Where a carrier's salt and hydraulic grime collects: a trace on top, heavier low down and behind each wheel,
    in streaks drawn out backwards along the car as the air carries it; tone on tone, never a pattern."""
    def f(p, n):
        y, z, x = p[:, 1], p[:, 2], np.abs(p[:, 0])
        low = smoothstep(42, 16, y)
        behind_front = np.exp(-((z - 20) / 18) ** 2) * smoothstep(50, 70, x) * smoothstep(58, 30, y)
        behind_rear = smoothstep(-128, -150, z) * smoothstep(25, 45, x) * smoothstep(55, 25, y)
        amount = 0.03 + 0.6 * np.maximum(low, np.maximum(behind_front, behind_rear))  # a stain, never a coat
        streak = noise.fbm(p * np.array([1 / 7, 1 / 9, 1 / 45], np.float32), 4, seed)
        patch = noise.fbm(p / 14, 3, seed + 3)
        w = amount * smoothstep(0.46, 0.6, 0.6 * streak + 0.4 * patch)
        return w
    return shapes.Zone(f, label="carrier grime")


def design(s):
    s.clay()

    s.step("Gull grey over white", "The body in light gull grey, semi-gloss; the side skirts, the car's belly, in "
           "gloss white, filled to the model's own lines.", words="hangar; light gull grey over gloss white")
    s.paint("body", "semi-gloss", colour=GULL)
    belly = (meshlines.panel((42, 19, 63), both=True) | meshlines.panel((13, 20, 183), both=True)
             | meshlines.panel((2, 18, -130)))
    s.paint("body", "gloss", colour=WHITE, zone=belly)

    s.step("Touch-up panels", "A few whole panels in a fresher touch-up grey, satin against the old semi-gloss, one "
           "side more than the other: the right sidepod, the cockpit's surround and the left rear quarter panel (its "
           "badge put back on after).",
           words="Touch-up panels: corrosion touch-ups in a fresher grey on a few whole panels, one side more than the "
                 "other: tone on tone, never flat")
    touched = meshlines.panel((-76, 60, -25)) | meshlines.panel((-25, 80, 11)) | meshlines.panel((35, 73, -64))
    s.paint("body", "satin", colour=TOUCHUP, zone=touched)

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
    s.mark("sidepod top", "gloss", chevrons(), size=12, at=(87, 44, -18), colour=RED)

    s.step("The walkways", "A thin black outline on each sidepod's top, where the crew steps to climb in, its long "
           "sides beside the sidepod's inner edge; inside it the walkway's dark non-skid grip.",
           words="black lines where the crew may walk; Non-skid inside the walkway: the walkway's rough dark grip, so "
                 "boots don't slip on a wet deck")
    s.paint("body", "textured wrap", colour=NONSKID, zone=walkway_inside(3, 16))
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

    # ---- the brand book, area by area ----

    s.step("The nose", "The radar's cone flat black, the nose tip as its own object; a flat dark anti-glare panel ahead "
           "of the cockpit; a pale green formation-light strip on each side of the nose; the air-data probe under the "
           "nose's tip bare metal, its tip red, and the sensor inside the nose bare metal; the radar bay's access door, "
           "an outline with a fastener at each corner.",
           words="Black radome: the radar's cone is flat black on a seventies navy jet. Anti-glare panel: a flat dark "
                 "panel ahead of the cockpit, so the sun doesn't dazzle the pilot. Formation-light strips: the pale "
                 "green strips a wingman flies on at night. Pitot probe: bare metal, its tip red. Avionics hatch: the "
                 "radar bay's access door")
    s.paint(["nose tip", "nose panel"], "matte", colour=RADOME)
    s.paint("body", "matte", colour=RADOME, zone=antiglare())
    strip = meshlines.line((30, 50, 117)).between((31.6, 51.0, 104.0), (28.5, 48.7, 124.0)).offset(3.25).mirrored()
    s.paint("body", "matte", colour=FORMATION, zone=strip.strip(2.5))
    s.paint(["antenna", "nose sensor"], "polished aluminium")  # the probe pointing forward under the nose's tip
    s.paint("antenna", "gloss", colour=RED, zone=shapes.front_of(204.0))
    s.mark("body shell", "gloss", hatch(0.55, 0.08, 0.4 / 12, 0.5 / 12, 1.0 / 12), size=12, at=(23, 57, 134), colour=BLACK)

    s.step("The cockpit", "The rescue arrow each side, yellow on a red edge, pointing at the opening; the seat's "
           "yellow-and-black firing handle; the harness in olive webbing, its buckles bare metal.",
           words="Rescue arrow: the arrow a rescuer follows to the canopy release. Firing handle: the seat's "
                 "yellow-and-black striped pull handle. Olive harness, polished buckles")
    arrow = s.mark("cockpit surround", "gloss", ARROW, size=5, at=(31, 76, -4), up=(-1, 0, 0), colour=RED)
    s.mark("cockpit surround", "gloss", inset(ARROW, 0.09), size=arrow.size, at=arrow.centre, up=(-1, 0, 0), colour=GOLD)
    handle = shapes.box((-3, 17, 27), (3, 27, 37))
    s.paint("seat", "gloss", colour=GOLD, zone=handle)
    s.paint("seat", "gloss", colour=BLACK, zone=handle & shapes.stripes(0.8, across=(0, 0.6, 0.8)))
    s.paint("seat belt", "webbing", colour=HARNESS)
    s.paint("belt buckle", "polished aluminium")

    s.step("The squadron", "The squadron's blue band along each rear flank's shoulder and on over the sidepod's into "
           "the intake, as the air runs, its lower edge a gold pinstripe; its emblem on each rear quarter panel, a gold bolt on a blue disc in a thin gold "
           "ring; the bolt alone, gold, on each wheel's hub.",
           words="Squadron band: the squadron's blue along each rear flank, its lower edge a gold pinstripe: the colour "
                 "you see from the chase camera; it lost its fluidity stopping at the sidepod (the user, 2026-10-07: "
                 "\"It lost it's fluidity in the design\"). Squadron emblem, where the chase camera sees it. The bolt on the hubs")
    blue, pinstripe = band()
    s.paint("body", "gloss", colour=BLUE, zone=blue)
    s.paint("body", "gloss", colour=GOLD, zone=pinstripe)
    badge = s.mark("rear quarter panel", "gloss", marks.disc(), size=14, at=(33, 75, -63.5), colour=BLUE)
    s.mark("rear quarter panel", "gloss", marks.ring(0.86), size=badge.size, at=badge.centre, colour=GOLD)
    s.mark("rear quarter panel", "gloss", BOLT, size=badge.size * 0.62 / BOLT.high, at=badge.centre, colour=GOLD)
    s.paint("wheel cover hub", "gloss", colour=GOLD, zone=hub_bolt(5.0))

    s.step("The sidepods", "Two kick-in steps up each sidepod's flank to the walkway, behind the intake's chevrons.",
           words="Kick-in steps: two footholds up the sidepod's side to the walkway")
    step_box = outline(marks.box(0.75, 0.1), 0.35 / 4, "a kick-in step")
    s.mark("sidepod top", "gloss", step_box, size=4, at=(86.3, 38, -33), colour=BLACK)
    s.mark("sidepod top", "gloss", step_box, size=4, at=(86.2, 46, -37.5), colour=BLACK)

    s.step("The deck and tail", "The panels round the exhausts in burnt titanium, fading into the grey ahead of them; "
           "the arresting hook in black and white bands under the tail; the fuel cap bare metal in a red ring; the "
           "engine bay's access door on each rear flank.",
           words="Heat-stained tail: the one soft colour change. Arresting hook: the carrier's signature. Refuelling "
                 "point. Engine access hatch", look="rear")
    heat = shapes.fade("z", start=-122, end=-140, curve=0.8)
    s.paint(["tail corner", "tail panel"], "brushed titanium", zone=heat)
    hook = shapes.stripe(12, at=0) & shapes.band(-143.5, -112)  # stowed, short of the diffuser's edge
    s.paint("diffuser", "gloss", colour=WHITE, zone=hook)
    s.paint("diffuser", "gloss", colour=BLACK, zone=hook & shapes.stripes(5, across="z"))
    s.paint("fuel cap", "polished aluminium")
    cap = (51.0, 63.8, -71.6)
    s.paint("body", "gloss", colour=RED, zone=shapes.sphere(cap, 6.4) & ~shapes.sphere(cap, 4.5))  # right up to the cap, which keeps its metal
    s.mark("rear flank", "gloss", hatch(0.55, 0.06, 0.4 / 20, 0.5 / 20, 1.0 / 20), size=20, at=(64, 36, -80),
           colour=BLACK)

    s.step("The wheels and gear", "A white slip mark across each tyre and its cover's red rim; the brakes dark "
           "heat-worn metal.", words="Tyre slip marks: to see if the tyre has crept. Brakes: dark heat-worn metal")
    s.paint("wheel covers", "gloss", colour=WHITE, zone=wedge(24, 36, 70, 2.0))
    s.paint("sidewall", "rubber", colour=WHITE, zone=wedge(28, 34.6, 70, 2.0))
    s.paint("brake caliper", "gunmetal")

    s.step("The inner car", "The front wing's leading edge polished, as a jet's wing edges are; the intakes' wire "
           "screens dull steel against the white.",
           words="Bare-metal leading edge. Intake screens: the intakes' wire screens in dull steel")
    edge = shapes.Zone(lambda p, n: smoothstep(-0.1, 0.1, p[:, 2] - (213.4 - 0.136 * np.abs(p[:, 0]))))
    s.paint("front wing", "polished aluminium", zone=edge)
    s.paint(["sidepod grille", "sidepod grille plate"], "brushed steel", colour="#6b6e71")

    s.step("The stencils", "A few small stencils in the squadron's stencil type, as a jet carries them: NO STEP behind "
           "each walkway, DANGER under each intake's chevrons, RESCUE by each rescue arrow.",
           words="Sure (to small words): NO STEP just outside the walkway; DANGER beside the intake's chevrons; RESCUE "
                 "beside the rescue arrow")
    s.text("NO STEP", "sidepod top", colour=BLACK, font="black ops", height=2, at=(67, 62.6, -44.5), up=(0, 0, 1))
    s.text("DANGER", "sidepod top", colour=RED, font="black ops", height=2.5, at=(87, 36, -18))
    s.text("RESCUE", "cockpit surround", colour=RED, font="black ops", height=2, at=(32, 77, -14))

    s.step("Carrier grime", "Salt and hydraulic grime, a trace on top, heavier low down and behind each wheel, "
           "streaked back along the car.", words="Carrier grime: salt and hydraulic grime, faint on top, heavier low "
                                                  "and behind the wheels")
    s.paint("body", "greasy", colour=GRIME, zone=grime(), blend=0.75, across=True)
