"""Specimen (TSC_ConceptTrial's concept A, the Field guide board, 2026-09-28): the car as a plate from
a naturalist's field guide. The ladybird is the specimen: a matte vermilion shell over the top of
the car, its rim drawn in an ink line, the seven-spot's seven ink spots on it where the plate puts
them (one at the front on the middle line, then three pairs spreading back). Below the rim the
car is the page itself, matte paper, and along the bottom the grass is drawn in ink strokes over a
wash of sage. Rough on purpose: flat colour in the board's finishes, no lettering yet (the page
below the rim is where the Latin name would go).

The shell's rim, seen from the side, is a flat superellipse: level at about 55 cm along the car's
shoulder (above the front flank's lip and the sidepod faces, so it cuts no fold), rising over the
nose (it crosses the nose's top ahead of the fin, so the nose tip is paper). Seen from above, the
shell's back end is rounded off over the tail, so the chase cameras see the drawn shell end on a
strip of paper, not a red car. Both depend on the car's shape only, so the sides match. Distances
are measured along the surface, so the ink rim is the same width wherever it crosses a curve.
"""

import numpy as np

from tool import shapes

# the board's Paper (#EDE6D3) read as white clay on the car (the first look): a shade warmer
VERMILION, INK, PAPER, SAGE = "#D2381F", "#1A1A1A", "#E8DBBF", "#7FA25A"

# the rim: ((z - ZC) / C)^K + ((YC - y) / B)^K = 1, so y = YC - B = 55 along the middle
YC, B, ZC, C, K = 95.0, 40.0, -5.0, 236.0, 4.0
# the back end seen from above: half an ellipse, x / TAIL_W and (z - TAIL_Z0) / TAIL_L, behind TAIL_Z0
# (as wide as the car there, so it leaves the edge smoothly) to z -142 on the tail panel
TAIL_Z0, TAIL_W, TAIL_L = -85.0, 80.0, 57.0
RIM_WIDTH = 2.2  # cm, the ink line of the plate's drawing

# the seven spots seen from above (x, z, radius in cm, seed), on the top's clean panels, clear of
# the cockpit, the mirror mounts, the fuel caps, the number and name panels and the nose fin
FRONT_SPOT = (0.0, 104.0, 10.0, 11)
PAIRS = [(37.0, 25.0, 8.0, 12), (61.0, -60.0, 8.0, 13), (36.0, -104.0, 10.0, 14)]
OUTER = ["body shell", "nose tip", "nose panel", "sidepod top", "engine cover|part", "rear flank"]

# every body part but the sidepod inlets, which are painted whole (the rim would cut their walls)
RIM_PARTS = ["body shell", "cockpit surround", "diffuser", "diffuser strake", "engine cover|part",
             "engine cover panel", "fuel cap", "mirror mount", "nose fin", "nose panel", "nose tip",
             "number panel", "rear flank", "rear quarter panel", "side skirt", "sidepod top",
             "tail corner", "tail panel", "wing pylon"]


def along_surface(value, grad, n):
    """A level set's distance along the surface, to first order: its value over the part of its
    gradient that lies in the surface."""
    along = grad - (grad * n).sum(1, keepdims=True) * n
    return np.clip(value / np.maximum(np.linalg.norm(along, axis=1), 1e-4), -200, 200)


def side_rim(p, n):
    """Signed distance to the rim seen from the side, in cm: positive above it."""
    y, z = p[:, 1], p[:, 2]
    u = (z - ZC) / C
    v = np.maximum(YC - y, 0.0) / B
    g = np.maximum(u ** K + v ** K, 1e-9)
    s = g ** (1 / K)  # 1 on the rim
    k = g ** (1 / K - 1)
    grad = np.stack([np.zeros_like(y), -(v ** (K - 1)) / B * k, (u ** (K - 1)) / C * k], 1)
    return along_surface(1 - s, grad, n)


def tail_end(p, n):
    """Signed distance to the shell's rounded back end seen from above: positive inside."""
    x, z = p[:, 0], p[:, 2]
    behind = z < TAIL_Z0
    u = np.where(behind, (z - TAIL_Z0) / TAIL_L, 0.0)
    w = x / TAIL_W
    s = np.maximum(np.sqrt(u * u + w * w), 1e-6)
    grad = np.stack([w / TAIL_W / s, np.zeros_like(x), u / TAIL_L / s], 1)
    d = along_surface(1 - s, grad, n)
    return np.where(behind, d, 200.0)


def rim(p, n):
    """Signed distance to the shell's whole rim along the surface, in cm: positive on the shell."""
    return np.minimum(side_rim(p, n), tail_end(p, n))


def mirrored(zone):
    """The same zone on the car's other side, drawn as its mirror image."""
    flip = np.array([-1.0, 1.0, 1.0], np.float32)
    return shapes.Zone(lambda p, n: zone(p * flip, n * flip))


def side_facing(least=0.65):
    """Surfaces facing left or right, cut crisply: the blades stop where the body turns under."""
    return shapes.Zone(lambda p, n: np.clip((np.abs(n[:, 0]) - least) / 0.03, 0, 1))


def wash_line(p, n):
    """The top of the sage wash: about 24 cm up, wandering a little like a watercolour's edge."""
    z = p[:, 2]
    return 24.0 + 1.2 * np.sin(z / 11.0 + 0.5) + 0.7 * np.sin(z / 4.3 + 1.7) - p[:, 1]


def design(s):
    s.clay()

    s.step("The page", "The whole body in matte paper: the page of the field guide the ladybird is drawn on.",
           words="I obviously don't want to fall in the cliche camoufaldge skin though")
    s.paint("body", "matte", colour=PAPER)

    s.step("The shell", "A matte vermilion shell over the top, from the nose back to the tail, "
           "its rim drawn in an ink line along the shoulder and round its back end over the tail.",
           words="maybe it is something that stands out")
    s.paint("body", "matte", colour=VERMILION, zone=shapes.field(rim))
    s.paint("sidepod inlet", "matte", colour=INK)  # the rim crosses its walls: the opening in ink
    s.paint(RIM_PARTS, "chalk", colour=INK, zone=shapes.field(lambda p, n: RIM_WIDTH / 2 - np.abs(rim(p, n))))

    s.step("The seven spots", "The seven-spot's ink spots on the shell, seen from above as on the plate: "
           "one at the front on the middle line, three pairs spreading back.",
           words="Sure, ladybird.")
    top = shapes.facing("up", 0.4, soft=0.006) & shapes.above(30)
    x, z, r, seed = FRONT_SPOT
    spots = shapes.blob((x, 0, z), r, wobble=0.08, seed=seed)
    for x, z, r, seed in PAIRS:
        one = shapes.blob((x, 0, z), r, wobble=0.08, seed=seed)
        spots = spots | one | mirrored(one)
    s.paint(OUTER, "chalk", colour=INK, zone=spots & top)

    s.step("The grass", "Along the bottom, grass drawn in ink strokes rising from a wash of sage, "
           "on the paper below the rim.",
           words="I do wonder if the bottom is some lever of grass, that acts as the blend between the grass and the bug or something")
    # not on the ledges facing up: the side skirt's top under the front flank came out a green
    # stripe seen from above (the second look); its face below stays a thin ground line
    wash = shapes.field(wash_line) & shapes.behind(140) & ~shapes.facing("up", 0.6, soft=0.05)
    s.paint("body", "matte", colour=SAGE, zone=wash)
    blades = shapes.grass(base=18.0, height=(12.0, 30.0), lean=0.45, every=2.6, line=1.6, seed=7)
    below_rim = shapes.field(lambda p, n: -rim(p, n) - 4.0)
    s.paint("body", "chalk", colour=INK, zone=blades & side_facing() & below_rim & shapes.behind(10))
    # the blades stop at the sidepods' front: ahead, the front flank's lower half sits back under a
    # lip over the skirt, where they broke into dashes (the first look)

    s.step("Wheels and inner car", "The wheels, the inner car and the diffuser under the tail in ink.")
    s.paint("wheels", "matte", colour=INK)
    s.paint("inner", "matte", colour=INK)
    s.paint(["diffuser", "diffuser strake"], "matte", colour=INK)
