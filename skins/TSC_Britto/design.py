"""TSC_Britto: Romero Britto's pop art made of the car's own parts, its two sides unlike, as Britto paints a face's two
halves: each part its own colour and pattern, and on the right side each of the side's parts another colour or pattern
than its twin on the left; a black line on every seam between two parts; the plates the game letters plain; the inner
car's parts each a solid colour. All of it gloss, the tyres black rubber, the glass clear, every light its own colour of
the palette, and no dirt ever: it stays new."""

import numpy as np
from PIL import Image
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

from tool import fbx, parts, shapes
from tool.noise import smoothstep

RED, YELLOW, BLUE, ORANGE, GREEN, PURPLE = "#e4202d", "#ffd21f", "#1f5fd1", "#ff7f1f", "#2bb24c", "#7d3ec1"
BLACK, WHITE = "#111111", "#ffffff"
LINE = 2.0   # cm from a seam to the black line's edge: the line is twice that
GAP = 2.5    # cm: two pieces' edges this close are a seam (a sewn-on piece's gap)
CLEAR = 3.5  # cm the line keeps off the plates the game letters
LEAN = 0.47  # stripes lean forward 25 degrees

# each part of the body (the mirror mount shares the body shell's paint): its colour, its pattern and the pattern's
# colour ("plain": none)
PLAN = {
    "body shell": (BLUE, "checks", WHITE),
    "nose tip": (RED, "dots", WHITE),
    "nose panel": (YELLOW, "stripes", ORANGE),
    "wing pylon": (GREEN, "plain", None),
    "side skirt|left": (PURPLE, "dots", YELLOW),
    "side skirt|right": (YELLOW, "dots", PURPLE),
    "cockpit surround": (YELLOW, "plain", None),
    "sidepod top|left": (YELLOW, "hearts", RED),
    "sidepod top|right": (RED, "hearts", YELLOW),
    "sidepod inlet|left": (GREEN, "stripes", WHITE),
    "sidepod inlet|right": (WHITE, "stripes", GREEN),
    "rear flank|left": (ORANGE, "dots", WHITE),
    "rear flank|right": (PURPLE, "dots", WHITE),
    "rear quarter panel|left": (PURPLE, "plain", None),
    "rear quarter panel|right": (ORANGE, "plain", None),
    "fuel cap": (GREEN, "plain", None),
    "engine cover|part": (GREEN, "waves", YELLOW),
    "tail corner|left": (PURPLE, "checks", WHITE),
    "tail corner|right": (ORANGE, "checks", WHITE),
    "tail panel": (RED, "stripes", WHITE),
    "diffuser": (BLUE, "plain", None),
    "diffuser strake": (YELLOW, "plain", None),
}
PLATES = {"nose fin": BLUE, "number panel": GREEN, "engine cover panel": GREEN}  # one plain paint each, the colour round them
UNDER = ("diffuser", "diffuser strake", "wing pylon")  # under the car and behind the front wing: no line
WHEELS = {"wheel cover disc": (RED, "dots", WHITE), "wheel cover ring": (YELLOW, "plain", None),
          "wheel cover hub": (BLUE, "plain", None)}
INNER = {  # the inner car's parts seen from outside, each a solid colour
    "front wing": RED, "front wing endplate": YELLOW, "upper wishbone": BLUE, "lower wishbone": ORANGE,
    "pushrod": GREEN, "tie rod": PURPLE, "upright": YELLOW, "upright cover": RED, "rear arm": BLUE,
    "mirror": WHITE, "mirror arm": PURPLE, "sidepod frame": GREEN, "sidepod panel": RED, "sidepod strut": YELLOW,
    "side vane": BLUE, "side vent": ORANGE, "exhaust": GREEN, "rear bumper": PURPLE, "rear bumper corner": YELLOW,
    "rear strake": RED, "tail frame": BLUE, "cockpit rim": ORANGE, "seat": RED, "steering wheel": BLUE,
    "airbox": YELLOW, "wing bracket": GREEN, "brake caliper": RED, "rim": YELLOW, "hub": BLUE,
}
# the car's own lights, each its own colour, none the stock's, at full colour: the speed numbers, the gear bar along
# the tail's top (in the blue tail frame), the slots inside the front wheels, the lamps on the front wing (night only)
LIGHTS = {"speed numbers": YELLOW, "rear lights": GREEN, "brake lights": PURPLE, "front wing": YELLOW}
# the ring round each wheel and the inner car's parts that carry a light of their own (strips, lamps, the cockpit's
# glow), each lit in a colour of the palette that isn't its paint, at the stock brightness
LIT = {
    "wheel ring": ORANGE, "hub": ORANGE, "rear bumper": YELLOW, "side vane": ORANGE, "exhaust": YELLOW,
    "sidepod panel": YELLOW, "sidepod frame": YELLOW, "sidepod strut": ORANGE, "sidepod boss": YELLOW,
    "sidepod grille plate": YELLOW, "airbox": ORANGE, "tie rod": YELLOW, "steering wheel": ORANGE,
    "steering column": ORANGE, "upper wishbone": ORANGE, "front bulkhead": PURPLE, "floor rail": PURPLE,
    "cockpit tub": GREEN, "nose inner": GREEN,  # these two share their paint
}


def seams(names):
    """Within LINE cm of the seams between the named parts: an edge of the body's triangles two of them share, or a
    piece's edge within GAP cm of another's (a sewn-on piece); none within CLEAR cm of the plates."""
    P = parts.load()
    m = fbx.meshes()["Skin_01"]
    tv, pos = m["tri_vertex"], m["positions"].astype(np.float64)
    off = P.mesh_offset["Skin"]
    name = np.array([P.instances[int(i)]["name"] for i in P.tri_part[off:off + len(tv)]])
    _, weld = np.unique(np.round(pos, 2), axis=0, return_inverse=True)
    weld = weld.reshape(-1)
    V = np.zeros((weld.max() + 1, 3))
    V[weld] = pos
    tri, first = np.unique(np.sort(weld[tv], axis=1), axis=0, return_index=True)  # a triangle drawn twice once
    words, code = np.unique(name[first], return_inverse=True)
    facing = m["tri_normal"][first].mean(1)
    e = np.sort(np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]]), axis=1)
    c, chosen, f = np.tile(code, 3), np.isin(np.tile(words[code], 3), names), np.tile(facing, (3, 1))
    order = np.lexsort((e[:, 1], e[:, 0]))
    e, c, chosen, f = e[order], c[order], chosen[order], f[order]
    start = np.flatnonzero(np.r_[True, (e[1:] != e[:-1]).any(1)])
    many, ours = np.diff(np.r_[start, len(e)]), np.minimum.reduceat(chosen, start)
    edge = e[start]
    shared = ours & (np.minimum.reduceat(c, start) != np.maximum.reduceat(c, start))
    open_ = ours & (many == 1)
    mid, oc = V[edge[open_]].mean(1), c[start][open_]
    near = cKDTree(mid).query(mid, k=12, distance_upper_bound=GAP)[1]
    other = np.array([(oc[[j for j in row if j < len(mid)]] != oc[i]).any() for i, row in enumerate(near)])
    keep, kf = edge[shared], f[start][shared]
    if other.any():
        keep, kf = np.vstack([keep, edge[open_][other]]), np.vstack([kf, f[start][open_][other]])
    a, b = V[keep[:, 0]], V[keep[:, 1]]
    k = np.maximum(np.ceil(np.linalg.norm(b - a, axis=1) / 0.2), 1).astype(int)
    i = np.repeat(np.arange(len(a)), k)
    pts = a[i] + (b[i] - a[i]) * np.concatenate([np.arange(n) / n for n in k])[:, None]
    nrm = kf[i] / np.linalg.norm(kf[i], axis=1, keepdims=True)
    seen = shapes.outside(0.4)(pts.astype(np.float32), nrm.astype(np.float32)) > 0.5  # none inside an inlet or under a panel
    plate = V[np.unique(tri[np.isin(words[code], list(PLATES))])]
    if len(plate):
        seen &= cKDTree(plate).query(pts, workers=-1)[0] > CLEAR + LINE
    pts = pts[seen]
    _, piece = connected_components(cKDTree(pts).sparse_distance_matrix(cKDTree(pts), 0.5), directed=False)
    pts = pts[np.bincount(piece)[piece] >= 75]  # a stretch shorter than 15 cm left after the filters goes
    tree = cKDTree(pts)
    return shapes.Zone(lambda p, n: smoothstep(-0.1, 0.1, LINE - tree.query(p, workers=-1)[0]).astype(np.float32),
                       label="the seams between the parts")


def waves(width=4.0, every=10.0, rise=2.5, length=24.0):
    """Wavy stripes across the car, waving up the sides and across the top."""
    def f(p, n):
        u = p[:, 2] + rise * np.sin(2 * np.pi * (p[:, 1] + np.abs(p[:, 0])) / length)
        return smoothstep(-0.1, 0.1, width / 2 - np.abs((u / every) % 1 - 0.5) * every).astype(np.float32)
    return shapes.Zone(f, label="waves")


def heart(colour, px=192):
    """A heart, the colour on clear."""
    y, x = np.mgrid[1.25:-1.15:px * 3j, -1.3:1.3:px * 3j]
    inside = ((x * x + y * y - 1) ** 3 - x * x * y ** 3 <= 0).reshape(px, 3, px, 3).mean((1, 3))
    rgba = np.zeros((px, px, 4), np.uint8)
    rgba[..., :3] = [int(colour[k:k + 2], 16) for k in (1, 3, 5)]
    rgba[..., 3] = np.round(inside * 255)
    return Image.fromarray(rgba, "RGBA")


def lay(s, part, colour, pattern, other):
    """A part in its colour and pattern."""
    if pattern == "dots":
        s.paint(part, "polka dots", palette=[colour, other], scale=10)
    elif pattern == "checks":
        s.paint(part, "checks", palette=[colour, other], scale=8)
    else:
        s.paint(part, "gloss", colour=colour)
    if pattern == "stripes":
        s.paint(part, "gloss", colour=other, zone=shapes.stripes(4, across=(0, -LEAN, 1)))
    elif pattern == "waves":
        s.paint(part, "gloss", colour=other, zone=waves())
    elif pattern == "hearts":
        s.scatter(heart(other), where=part, size=6, spacing=11, turn="length")


def design(s):
    s.clay()

    s.step("Every part its own", "Each part of the body its own colour and pattern, the two sides unlike: on the "
           "left the side skirt purple with yellow dots, the sidepod yellow with red hearts, the rear flank orange "
           "with white dots; on the right the side skirt yellow with purple dots, the sidepod red with yellow hearts, "
           "the rear flank purple with white dots; the body shell blue with white checks, the engine cover green "
           "with yellow waves; the plates the game letters plain.",
           words="I want you to actually paint each part differently ... e.g tail panel is one, fuel cap, etc")
    for part, plan in PLAN.items():
        lay(s, part, *plan)
    for part, colour in PLATES.items():
        s.paint(part, "gloss", colour=colour)

    s.step("The black outline", "A black line on every seam between two parts, as Britto outlines everything.",
           words="each part of something with for example red and circles, then another part with another color")
    body = [p for p in PLAN if p.split("|")[0] not in UNDER]
    s.paint(body, "gloss", colour=BLACK, zone=seams([p.split("|")[0] for p in body]), across=True)

    s.step("Wheels and the inner car", "The wheel covers red with white dots in a yellow ring, a black line between; "
           "every part of the inner car a solid colour of its own, the rest of it black.",
           words="primary and secondary colors")
    for part, plan in WHEELS.items():
        lay(s, part, *plan)
    s.paint(list(WHEELS), "gloss", colour=BLACK, zone=seams(list(WHEELS)), across=True)
    s.paint("inner", "gloss plastic", colour=BLACK)
    for part, colour in INNER.items():
        s.paint(part, "gloss plastic", colour=colour)

    s.step("Tyres and glass", "The tyres plain black rubber, the black line round the whole car; the glass clear, "
           "so the red seat and the blue steering wheel show through the canopy.",
           words="I want you to actually paint each part differently")
    s.paint("tyres", "rubber", colour=BLACK)
    s.glass(WHITE, 0.9)

    s.step("The lights", "Every light its own colour of the palette, none the stock's: the speed numbers yellow, the "
           "gear bar along the tail green, the slots inside the front wheels purple, the front wing's lamps sun "
           "yellow at night, the ring round each wheel orange; "
           "each inner part's own lamps and strips in a colour that isn't its paint.",
           words="I want you to actually paint each part differently", look="rear night")
    for part, colour in LIGHTS.items():
        s.relight(part, colour)
    for part, colour in LIT.items():
        s.relight(part, colour, keep_level=True)

    s.step("Stays new", "A freshly varnished canvas: no dirt, no wear, no fading, even on a dirt road.",
           words="How about we design a car like that")
    s.dirt(0, "everything")
