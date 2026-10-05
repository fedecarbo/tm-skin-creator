"""Rescue v2: the snow rescue car (TSC_Snow) with more detail, shaped by the car's own curvature.
Signal orange; a black lower edge and a band of silver and orange checks that follow the side's
curve, rising with the tail; silver chevrons on the tail's deck; NO STEP on the deck and the side
box's top, each side, as small boxed placards; the rear quarter panels in gloss black; studded snow tyres; amber rear
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
STEP_FROM, STEP_TO = -128.0, 10.5  # z: the marking's ends, where the user drew them (notes 4 and 5)
LINE = 1.0  # cm: the line the user drew, as wide as the words keep clear of it
CORNER = 1.5  # cm: the turns where the marking leaves one seam for the next, rounded over this
SIGN, SIGN_H = "NO STEP", 2.6  # the words and their capitals' height (cm)
SIGN_AT = (-70.0, -22.0)  # z: where they go along the course: the deck by the side box (the user's arrow,
# note 10, from where it was at -95 to beside the fuel cap), and the side box's top
QUARTER = "What can we do here in this piece? (note 11, on the right rear quarter panel)"
PAD, FRAME = 0.5, 0.2  # cm: the placard's box round the words (the user's yes, note 9), and its line


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


def _outlines(name, side=None):
    """A body panel's outlines, from the mesh: its open edges (the pieces are welded where the FBX splits
    them), each loop in order round it; the longest first."""
    from tool import fbx, parts
    p = parts.load()
    m = fbx.meshes()[fbx.MESH_OF["Skin"]]
    tp = p.tri_part[p.mesh_offset["Skin"]:p.mesh_offset["Skin"] + len(m["tri_vertex"])]
    V = m["positions"].astype(np.float64)
    _, weld = np.unique(np.round(V * 1000).astype(np.int64), axis=0, return_inverse=True)
    F = weld.reshape(-1)[m["tri_vertex"][np.isin(tp, list(p.select(name, side, None, exact=True)))]]
    e, k = np.unique(np.sort(np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1), axis=0, return_counts=True)
    nxt = {}
    for a, b in e[k == 1]:
        nxt.setdefault(a, []).append(b)
        nxt.setdefault(b, []).append(a)
    at = np.zeros((weld.max() + 1, 3))
    at[weld.reshape(-1)] = V
    loops, seen = [], set()
    for start in nxt:
        if start in seen or len(nxt[start]) != 2:
            continue
        loop, prev = [start], None
        while True:
            step = next((v for v in nxt[loop[-1]] if v != prev), None)
            if step is None or step == loop[0] or step in seen or len(nxt[step]) != 2:
                break
            prev = loop[-1]
            loop.append(step)
        seen.update(loop)
        if len(loop) > 2:
            loops.append(at[loop])
    return sorted(loops, key=len, reverse=True)


def _resample(P, every=0.25):
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    return np.stack([np.interp(np.arange(0, s[-1], every), s, P[:, k]) for k in range(3)], 1)


def _course():
    """The marking on the left (the right mirrors it), every 0.25 cm from its back end: the top's first
    guide line (tool/levels.py, on the rear flank's seam) forward from STEP_FROM to the side box top's
    back edge, then that panel's outline: in along its back edge, round its inner corner and forward
    along its inner edge to STEP_TO. Both are where the user drew (notes 4 and 5, within a centimetre
    or two). Its points, the length along it, and its direction."""
    top = _resample(np.asarray(next(L["path"] for L in levels.top_lines() if L["name"] == "top 1"), np.float64))
    top = top[top[:, 2] >= STEP_FROM]
    edge = _outlines("sidepod top", "left")[0]
    from scipy.spatial import cKDTree
    d, near = cKDTree(edge).query(top)
    j = int(np.argmin(np.where(np.abs(top[:, 2] + 50) < 15, d, np.inf)))  # where the guide reaches the panel
    k = int(near[j])
    way = 1 if edge[(k + 1) % len(edge), 0] < edge[k, 0] else -1  # inwards along the back edge
    run = [edge[k]]
    while not (run[-1][2] >= STEP_TO and run[-1][0] < 60):
        k = (k + way) % len(edge)
        run.append(edge[k])
    run = np.array(run)
    a, b = run[-2], run[-1]
    run[-1] = a + (b - a) * (STEP_TO - a[2]) / (b[2] - a[2])  # ends at STEP_TO
    P = _resample(np.vstack([top[:j + 1], run]))
    w = np.exp(-0.5 * (np.arange(-24, 25) * 0.25 / CORNER) ** 2)  # the turns rounded, the ends kept
    pad = np.vstack([np.repeat(P[:1], 24, 0), P, np.repeat(P[-1:], 24, 0)])
    P = np.stack([np.convolve(pad[:, c], w / w.sum(), mode="valid") for c in range(3)], 1)
    along = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    tan = np.gradient(P, axis=0)
    return P, along, tan / np.linalg.norm(tan, axis=1, keepdims=True)


def _placard():
    """NO STEP's placard: the words' ink across and high, and the box round them (PAD out), in cm."""
    from tool.paintbox import render_text
    img = render_text(SIGN, "teko", SIGN_H, weight=600)[0]["fill"]
    x0, y0, x1, y1 = img.getchannel("A").getbbox()
    return (x1 - x0) / 40 + 2 * PAD, (y1 - y0) / 40 + 2 * PAD  # render_text draws 40 px a cm, the ink centred


def _signs(s):
    """Where NO STEP goes, on both sides: beside the course where it reaches SIGN_AT (or up to 10 cm off,
    where it runs straight for the words' length, clear of the course's other stretches, of the fuel
    cap's seam and of what sits on the body: the fasteners, the inner car's pieces within a centimetre),
    on its inner side (towards the cockpit and the tail), reading along it, upright to someone at that
    side."""
    from scipy.spatial import cKDTree
    c = s.canvas("Skin")
    P, along, tan = _course()
    width, high = _placard()
    cap = cKDTree(c.pos[s.parts.mask(c.bake, "Skin", "fuel cap").reshape(-1)])
    texels = cKDTree(c.pos)
    from tool import fbx
    inner = fbx.meshes()[fbx.MESH_OF["Details"]]
    inner = cKDTree(inner["positions"][inner["tri_vertex"]].mean(1))

    def facing(at):  # the surface the words lie on there: the texels within 2.5 cm that face up, averaged
        k = texels.query_ball_point(at, 2.5)
        n = c.nrm[k][c.nrm[k][:, 1] > 0.3].astype(np.float64)
        return n.sum(0) / np.linalg.norm(n.sum(0)) if len(n) else None

    lift = LINE / 2 + 1.0 + high / 2

    def fits(u):  # the words centred u cm along: (centre, up, facing), or None where they don't fit
        i = int(np.searchsorted(along, u))
        if (tan[np.abs(along - u) <= width / 2 + 1.5] @ tan[i]).min() < np.cos(np.radians(10)):
            return None  # a turn under the words
        N = facing(P[i])  # not the nearest texel's: the side box top's edge is a little step
        if N is None:
            return None
        up = np.cross(tan[i], N)
        centre = c.pos[texels.query(P[i] + up / np.linalg.norm(up) * lift)[1]].astype(np.float64)  # on the paint
        N = facing(centre)
        if N is None:
            return None
        up = np.cross(tan[i], N)
        up /= np.linalg.norm(up)  # in the surface, on the inner side
        box = (centre + np.outer(np.linspace(-0.5, 0.5, 9), np.cross(up, N) * width)[:, None]
               + np.outer(np.linspace(-0.5, 0.5, 5), up * high)[None]).reshape(-1, 3)
        box = c.pos[texels.query(box)[1]]  # on the paint: the flat box rises off a curve
        rest = P[np.abs(along - u) > width / 2 + 4]
        if (cap.query(box)[0].min() < 1.5 or min(inner.query(box * f)[0].min() for f in ([1, 1, 1], [-1, 1, 1])) < 1.0
                or cKDTree(rest).query(box)[0].min() < 1.5):
            return None
        return centre, up, N

    spots = []
    for z in SIGN_AT:
        u0 = along[np.argmin(np.abs(P[:, 2] - z))]
        u, got = next(((u, g) for u in u0 + np.array([0, 2, -2, 4, -4, 6, -6, 8, -8, 10, -10]) if (g := fits(u))), (u0, None))
        if not got:
            continue
        centre, up, N = got
        for m in (1, -1):  # the left, then the right: its mirror, the words still reading forwards
            f = np.array([m, 1, 1])
            Nm, upm = N * f, up * f
            spots.append(dict(centre=tuple(centre * f), right=tuple(np.cross(upm, Nm)), up=tuple(upm),
                              facing=tuple(Nm), width=30))
    return spots


def _frame(spot):
    """The placard's box at a spot, FRAME cm wide, round the words: a zone."""
    centre, right, up, facing = (np.asarray(spot[k], np.float64) for k in ("centre", "right", "up", "facing"))
    width, high = _placard()

    def f(p, nrm):
        rel = p.astype(np.float64) - centre
        e = np.maximum(np.abs(rel @ right) - width / 2, np.abs(rel @ up) - high / 2)  # outside the box: > 0
        on = (np.abs(rel @ facing) < 2.5) & (nrm @ facing > 0.5)  # the surface under the box, curving away
        return np.where(on, FRAME / 2 - np.abs(e + FRAME / 2), -1.0).astype(np.float32)
    return shapes.field(f, soft=0.08)


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
    s.paint("side skirt", "gloss black", zone=band)  # ahead of the sidepods it rises into the band

    s.step("The tail", "Silver chevrons on the tail's deck, pointing forward.", words=WORDS)
    s.paint("tail panel", "reflective tape", zone=_chevrons())

    s.step("The rear quarter panels", "The angled panels behind the cockpit in gloss black, like the lower edge.",
           words=QUARTER)
    s.paint("rear quarter panel", "gloss black")

    s.step("No step", "NO STEP in black on each side, a small placard with a thin black box round the words: on the "
           "deck beside its edge, and on the side box's top beside its inner edge, where the user drew the line "
           "along them.", words=NOTES + "; NO STEP as a small placard ... Try it?: yes (note 9)")
    spots = _signs(s)
    for spot in spots:
        s.text(SIGN, spot, colour="black", font="teko", weight=600, height=SIGN_H)
        s.paint("body", "gloss black", zone=_frame(spot))

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
