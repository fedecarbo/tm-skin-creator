"""TSC_Britto: Romero Britto's pop art made of the car's own parts, its two sides unlike, as Britto paints a face's two
halves: each part its own colour and pattern, and on the right side each of the side's parts another colour or pattern
than its twin on the left; a black line on every seam between two parts and wherever the body meets a coloured part of
the inner car; the plates the game letters plain; the inner car's parts each a solid colour; three small outlined marks
where they mean something (a heart by the driver's heart, a sun and a star on the rear quarter panels). All of it
gloss, the tyres black rubber, the glass clear, every light its own colour of the palette, and no dirt ever: it stays
new."""

import functools

import numpy as np
from PIL import Image
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

from tool import fbx, marks, parts, shapes
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
INSIDE = ("sidepod inlet",)  # seen through the inlet's mouth, though the open air is low in there
RING = -3.0  # z where the ring round each inlet's mouth ends at the bottom (the sidepod top meets the frame at -1 to -4)
LOW = 32.0  # cm up: the foot of the sidepod, where the frame shows above the skirt
OUTLINE = 1.2  # cm of black round a mark, 0.5 inside one (the language's DNA)
MEET = 3.0  # cm: the black line on the body where it meets a coloured part of the inner car
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
    """Within LINE cm of the seams between the named parts."""
    return near(seam_points(tuple(names)), LINE, "the seams between the parts")


@functools.cache
def seam_points(names):
    """The seams between the named parts, points every 0.2 cm: an edge of the body's triangles two of them share, or
    a piece's edge within GAP cm of another's (a sewn-on piece); none within CLEAR cm of the plates."""
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
    return pts[np.bincount(piece)[piece] >= 75]  # a stretch shorter than 15 cm left after the filters goes


def _sample(tri, V, mask, per, seed):
    """Points spread over the masked triangles, per a cm², and the triangle each lies on."""
    idx = np.flatnonzero(mask)
    T = V[tri[idx]]
    area = 0.5 * np.linalg.norm(np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]), axis=1)
    k = np.random.default_rng(seed).poisson(area * per) + 1
    r = np.repeat(np.arange(len(idx)), k)
    w = np.random.default_rng(seed + 1).dirichlet([1, 1, 1], size=len(r))
    return np.einsum("kj,kjc->kc", w, T[r]), idx[r]


def _edges(tri, mask):
    """The open edges of the masked triangles (an edge only one of them has), as points every 0.2 cm, and the
    triangle each is on."""
    idx = np.flatnonzero(mask)
    t = tri[idx]
    e = np.sort(np.concatenate([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), axis=1)
    _, inv, many = np.unique(e, axis=0, return_inverse=True, return_counts=True)
    one = many[inv.reshape(-1)] == 1
    return e[one], np.tile(idx, 3)[one]


def _points(V, e):
    a, b = V[e[:, 0]], V[e[:, 1]]
    k = np.maximum(np.ceil(np.linalg.norm(b - a, axis=1) / 0.2), 1).astype(int)
    i = np.repeat(np.arange(len(a)), k)
    return a[i] + (b[i] - a[i]) * np.concatenate([np.arange(n) / n for n in k])[:, None], i


def contacts(names, near=1.0, on=0.6):
    """Where the named body parts meet a coloured part of the inner car, on the skin the eye sees (INSIDE: all of it):
    a body part's edge within near cm of the coloured part, or the coloured part's edge lying on the body (within on
    cm of its skin, on the outer side). Points every 0.2 cm, the body part and the inner part at each."""
    P = parts.load()
    M = fbx.meshes()

    def mesh(texture, key):
        m = M[key]
        tv, pos = m["tri_vertex"], m["positions"].astype(np.float64)
        off = P.mesh_offset[texture]
        name = np.array([P.instances[int(i)]["name"] for i in P.tri_part[off:off + len(tv)]])
        _, weld = np.unique(np.round(pos, 2), axis=0, return_inverse=True)
        weld = weld.reshape(-1)
        V = np.zeros((weld.max() + 1, 3))
        V[weld] = pos
        n = m["tri_normal"].mean(1)
        return weld[tv], V, name, n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-9)

    bt, bV, bn, bnr = mesh("Skin", "Skin_01")
    dt, dV, dn, _ = mesh("Details", "Details_01")
    ours = np.isin(bn, names)
    coloured = np.isin(dn, [k for k, c in INNER.items() if c != BLACK])
    # a body part's edge beside a coloured part
    e, t = _edges(bt, np.ones(len(bt), bool))
    keep = ours[t]
    a, i = _points(bV, e[keep])
    at, an = t[keep][i], bnr[t[keep]][i]
    inner, it = _sample(dt, dV, coloured, 4, 3)
    d, j = cKDTree(inner).query(a, workers=-1)
    sel = d < near
    a, abody, ainner, an = a[sel], bn[at[sel]], dn[it[j[sel]]], an[sel]
    # a coloured part's edge lying on the body's outer skin
    e, et = _edges(dt, coloured)
    b, i = _points(dV, e)
    skin, st = _sample(bt, bV, ours, 6, 7)
    d, j = cKDTree(skin).query(b, workers=-1)
    bnrm = bnr[st[j]]
    sel = (d < on) & (np.einsum("ij,ij->i", b - skin[j], bnrm) > -0.1)
    pts, nrm = np.vstack([a, b[sel]]), np.vstack([an, bnrm[sel]])
    body, part = np.r_[abody, bn[st[j[sel]]]], np.r_[ainner, dn[et[i[sel]]]]
    seen = (shapes.outside(0.4)(pts.astype(np.float32), nrm.astype(np.float32)) > 0.5) | np.isin(body, INSIDE)
    plate = bV[np.unique(bt[np.isin(bn, list(PLATES))])]
    if len(plate):
        seen &= cKDTree(plate).query(pts, workers=-1)[0] > CLEAR + LINE
    pts, body, part = pts[seen], body[seen], part[seen]
    _, piece = connected_components(cKDTree(pts).sparse_distance_matrix(cKDTree(pts), 0.5), directed=False)
    long = np.bincount(piece)[piece] >= 50  # a stretch shorter than about 10 cm goes
    return pts[long], body[long], part[long]


def gaps(pts, on, by, pieces=("sidepod top", "rear flank", "side skirt"), apart=3.0, strip=9.0, ledge=4.0):
    """Where the sidepod frame shows as a sliver along the side: where two of the side's pieces both meet it within
    apart cm of each other (the gap between them), and its strip above the side skirt behind the ring round the
    inlet's mouth (the ring ends at z RING at the bottom, where the sidepod top meets the frame) and the rear flank's
    foot (below LOW), up to strip cm above their edge and ledge cm in under it, under the sidepod top."""
    f = (by == "sidepod frame") & np.isin(on, pieces)
    p, o = pts[f], on[f]
    keep = np.zeros(len(p), bool)
    for piece in pieces:
        mine, other = o == piece, (o != piece)
        if mine.any() and other.any():
            keep[np.flatnonzero(mine)[cKDTree(p[other]).query(p[mine])[0] < apart]] = True
    skirt = p[((o == "side skirt") | ((o == "rear flank") & (p[:, 1] < LOW))) & (p[:, 2] < RING)]
    up, inward = np.meshgrid(np.arange(0.0, strip + 0.01, 0.5), np.arange(0.0, ledge + 0.01, 0.5))
    step = np.stack([-inward.ravel(), up.ravel(), np.zeros(up.size)], -1)  # in towards the middle, and up
    side = np.stack([np.sign(skirt[:, 0]), np.ones(len(skirt)), np.ones(len(skirt))], -1)
    curtain = skirt[:, None, :] + step[None] * side[:, None, :]
    return np.vstack([p[keep], curtain.reshape(-1, 3)])


def near(pts, width, label):
    """Within width cm of the points."""
    tree = cKDTree(pts)
    return shapes.Zone(lambda p, n: smoothstep(-0.1, 0.1, width - tree.query(p, workers=-1)[0]).astype(np.float32),
                       label=label)


def motif(inside, extent, rounded=0.0, notch=0.0, px=800):
    """A flat motif drawn by inside(x, y) (cm, y up, within extent cm of its middle) as its signed distance in cm
    (positive inside), its points rounded by `rounded` cm and its notches by `notch`, smooth between the grid's
    points."""
    from scipy.ndimage import distance_transform_edt, map_coordinates
    h = 2 * extent / px
    y, x = np.mgrid[extent - h / 2:-extent:-h, -extent + h / 2:extent:h]
    shape = inside(x, y)
    if notch:  # grown, then cut back: a notch's sharp corner filled round
        shape = distance_transform_edt(distance_transform_edt(~shape) * h <= notch) * h > notch
    core = distance_transform_edt(shape) * h > rounded  # eroded, then grown back round: no sharp points
    grid = np.where(core, distance_transform_edt(core) * h + rounded, rounded - distance_transform_edt(~core) * h)

    def sd(x, y):
        return map_coordinates(grid, [(extent - y) / h - 0.5, (x + extent) / h - 0.5], order=1, mode="nearest")
    return sd


def layer(sd, grow, label):
    """The motif grown by `grow` cm (its outline round it), as a mark's shape one unit wide (tool/marks.py), and its
    width in cm: an outline and its fill share their middle, so the fill laid at the outline's centre sits in it."""
    span = np.linspace(-20, 20, 801)
    x, y = np.meshgrid(span, span)
    inside = sd(x, y) + grow > 0
    xs, ys = x[inside], y[inside]
    lo, hi = np.array([xs.min(), ys.min()]), np.array([xs.max(), ys.max()])
    c, w = (lo + hi) / 2, hi[0] - lo[0]
    return marks.Shape(lambda u, v: (sd(c[0] + np.asarray(u) * w, c[1] + np.asarray(v) * w) + grow) / w,
                       (hi[1] - lo[1]) / w, label), w


def heart_motif(width):
    """A rounded heart `width` cm wide."""
    k = width / 2.28
    return motif(lambda x, y: ((x / k) ** 2 + (y / k) ** 2 - 1) ** 3 - (x / k) ** 2 * (y / k) ** 3 <= 0,
                 width * 0.7 + 3, rounded=0.3, notch=1.0)


def star_motif(width, points=5, inner=0.42):
    """A star `width` cm across its points, its tips rounded."""
    a = np.pi / 2 + np.arange(2 * points) * np.pi / points
    r = np.where(np.arange(2 * points) % 2 == 0, 1.0, inner) * width / 2
    P = np.stack([r * np.cos(a), r * np.sin(a)], -1)

    def inside(x, y):
        out = np.zeros(x.shape, bool)
        for (x0, y0), (x1, y1) in zip(P, np.roll(P, -1, 0)):
            cross = (y0 > y) != (y1 > y)
            out ^= cross & (x < x0 + (y - y0) * (x1 - x0) / np.where(y1 == y0, 1, y1 - y0))
        return out
    return motif(inside, width * 0.6 + 3, rounded=0.4)


def outlined(s, where, sd, colour, at, within):
    """A motif laid on a part as a sticker in its colour with OUTLINE cm of black round it, one side only: the black
    first, the colour on it at its middle (shrunk with it when it had to shrink to fit)."""
    edge, w = layer(sd, OUTLINE, "an outline")
    spot = s.mark(where, "gloss", edge, size=w, at=at, colour=BLACK, mirror=False, within=within)
    fill, wf = layer(sd, 0.0, "a mark")
    s.mark(where, "gloss", fill, size=wf * spot.size / w, at=spot.centre, colour=colour, mirror=False)


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

    s.step("The outline round the inner car", "A black line on the body wherever it meets a coloured part of the "
           "inner car: round the green frame of each sidepod's inlet (on the yellow and red sidepod tops, the checks, "
           "the skirts and inside the inlets), along the blue tail frame and the purple bumper at the back, round "
           "the mirrors' feet; and the green frame black where it shows only as a sliver along the side (in the "
           "gaps between the sidepod top, the rear flank and the side skirt). Two colours never touch.",
           words="each part of something with for example red and circles, then another part with another color")
    pts, on, by = contacts(list(dict.fromkeys(p.split("|")[0] for p in body)))
    s.paint(body, "gloss", colour=BLACK, zone=near(pts, MEET, "where the body meets the coloured inner car"),
            across=True)
    s.paint("sidepod frame", "gloss plastic", colour=BLACK,
            zone=near(gaps(pts, on, by), 2.0, "the frame where it shows as a sliver along the side"))

    s.step("Small marks", "A few small marks of Britto's world, each outlined in black, where they mean something: a "
           "red heart on the cockpit's left beside the driver's heart; a sun, yellow round orange, on the left rear "
           "quarter panel by the fuel cap; a green star on the right one. The two sides unlike, as everywhere.",
           words="each part of something with for example red and circles, then another part with another color with "
                 "some different shapes")
    names = tuple(dict.fromkeys(p.split("|")[0] for p in body))
    clear = ~near(seam_points(names), LINE + 1.0, "the black lines") & ~near(pts, MEET + 1.0, "the black lines")
    outlined(s, "cockpit surround", heart_motif(5.2), RED, (31, None, 6), clear)
    sun = 7.5  # the sun's yellow, across
    spot = s.mark("rear quarter panel", "gloss", marks.disc(), size=sun + 2 * OUTLINE, at=(33, None, -60),
                  colour=BLACK, mirror=False, within=clear)
    k = spot.size / (sun + 2 * OUTLINE)  # shrunk to fit, the rest with it
    for size, colour in ((sun, YELLOW), (3.0 + 1.0, BLACK), (3.0, ORANGE)):
        s.mark("rear quarter panel", "gloss", marks.disc(), size=size * k, at=spot.centre, colour=colour, mirror=False)
    outlined(s, "rear quarter panel", star_motif(9.5), GREEN, (-33, None, -60), clear)

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
