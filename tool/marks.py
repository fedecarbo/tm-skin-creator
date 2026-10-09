"""Marks: a shape pressed onto a named panel of the body as a sticker is, whole inside its edges (Skin.mark in
tool/paintbox.py, whose docstring says how to call it). The user, 2026-10-05: "it shouldn't do mistakes in the first
place".

    s.mark("rear quarter panel", "gloss white", marks.disc(), size=12)     # each side, its roomiest spot
    spot = s.mark("body shell", "racing red", marks.star(5), size=16, at=(0, None, 117))
    s.mark("body shell", "gloss white", marks.disc(), size=0.4 * spot.size, at=spot.centre)
    s.text("7", spot, colour="black", height=0.3 * spot.size)      # on the star, upright as it is
    s.mark("body", "gloss black", marks.box(0.25), size=40, at=(0, None, 100), across=True)
    s.text("27", "rear flank", colour="black", height=20)                 # words, laid the same way
    s.placard("NO STEP", "body shell", at=(63, None, -68), height=2.6)   # words in a thin box
    s.decal(s.art("tiger"), "rear flank", width=30)                       # a picture

The shapes, each one unit wide and scaled by the mark's `size` (its width in cm):
    marks.disc()                 a disc
    marks.ring(0.6)              a ring, its hole 0.6 of its width
    marks.blob(0.1, seed=3)      a spot that isn't quite round
    marks.box(0.5, corner=0.1)   a box half as high as it's wide, its corners rounded
    marks.polygon([(x, y), ...]) any outline, x to its right and y up, in its own units
    marks.star(5, inner=0.45)    a star
    marks.Picture(rgba, ...)     a picture's opaque pixels (words, a placard, a cut-out), painted by its own pixels

A mark is drawn on the car's surface itself (tool/surface.py's chart: the surface round a point as the sticker pressed
onto it there, every distance measured along the surface, exact), so it follows the panel's curve, wraps a rolled
edge as a cut sticker does, never reaches the far side of a thin panel and never breaks where the texture is cut. Its
room is the named parts' skin round where it's wanted, without:
  - what isn't theirs: the parts' edges;
  - the model's crisp lines (tool/meshlines.py): the sticker stays on its own panel, as the chart is cut along them;
  - hidden skin: inside an inlet, under another panel (the car map's open air, judge.OUTER);
  - the panels the game letters and the nose fin's plate, and judge.CLEAR cm round them;
  - `margin` cm in from all of those.
The mark goes where it's wanted if it's whole there; else to the nearest place it is, within `reach` (then pressed on
afresh there, its own chart); else it shrinks until one exists, down to LEAST of its size; else nothing is laid. Each
of those is a note, and so is how it sits: how far the sticker is stretched under it (a share of its lengths, from
STRETCH; a flat panel and a rolled edge stretch it not at all, a doubly curved one a little) and, under words and a
placard, how far the surface turns from flat (from WORD_TURN degrees, when they read bent: the user, 2026-10-05, of
lettering along a flank's curve, "the text is big for the curvature of the surface"). `across=True` presses it on at
`at` as it is, over every edge and crisp line in its footprint (a sticker over a panel gap, as on a real car), and
says what fell in a gap or off an edge. Whether it's whole is measured as it's laid (`_missing`, a finding for the
judge, tool/judge.py): chipped where its ink found no paint though the skin is there (the sticker's surface dropped
or folded there), or kept off by its zone. Wanted at a course (tool/course.py, a stretch of one of the car's lines or of
the line the user drew), it reads along it, each letter following the line (the course's chart), anywhere along the
stretch, which is its room. Wanted on the car's middle, it stays on the middle. Its twin on the other side is its
mirror image, at the same size; words and a placard are laid there as they are, reading forward on each side. Unless
the design says where their top points, words are upright to someone standing beside the car at the side the surface
faces: on the top, their top towards the car's middle (`_outward`). `at` with a None coordinate is looked along from
outside (from above, from the panel's own side, from the nearer end); when nothing in line faces the look, the mark
goes to the nearest skin that does, and the note says so.
"""

import numpy as np
from scipy import ndimage
from scipy.signal import fftconvolve
from scipy.spatial import cKDTree

from tool import carmap, coverage, judge, receipt, shapes, uvmap
from tool.noise import smoothstep

WORD_TURN = 20.0  # degrees: words read flat on a surface turning no more than this under them (the user kept lettering
# over a flank turning 16 degrees and rejected it over 38, 2026-10-05)
STRETCH = 0.03  # the share of its lengths a sticker is stretched by from which it's said
TORN = 0.5      # stretched by this much the sticker is torn or folded over itself: counted, never painted as whole
CHIP = 0.4      # cm: a bite out of a mark's ink narrower than twice this is closed over in space, to find what's missing
CHIP_AREA = 0.25  # cm² of its ink missing where the skin is bare, from which a mark is chipped
BITE = 0.3      # cm² of its ink kept off by its zone, from which a mark is said not whole, however big it is
SIDE = 30.0   # cm from the car's middle: words on the top further out read from beside the car, nearer from its ends
LEAST = 0.4   # the smallest share of its size a mark is shrunk to
OFF = 5.0     # cm: `at` further than this from the panel is said
MIDDLE = 0.5  # cm from the car's middle: a mark wanted nearer is centred, and has no twin
WALL = 0.15   # cm: skin this near one of the model's crisp lines walls a panel's room (its roomiest spot keeps off them)
LOOK = 0.3    # how much a texel must face the look along an axis (`at` with a None) to be the skin seen there




# ---- the shapes ----

class Shape:
    """A flat shape one unit wide, centred on its middle: sd(x, y) is the distance to its edge, positive
    inside (x to its right, y up, arrays of any shape); high: its height over its width; reach: how
    far its edge gets from its middle. kind: what it is for the notes and the judge; handed: its twin
    on the other side is laid as it is, not mirrored (words read forward on both sides)."""

    kind, handed, text = "shape", False, None

    def __init__(self, sd, high=1.0, label="a shape", reach=None):
        self.sd, self.high, self.label = sd, high, label
        self.reach = float(np.hypot(0.5, high / 2)) if reach is None else reach

    def __repr__(self):
        return self.label

    def mirrored(self):
        return Shape(lambda x, y: self.sd(-x, y), self.high, self.label, self.reach)

    def footprint(self, x, y):
        """Which of the points (x, y), in its own units, it covers: what must lie on free room."""
        return self.sd(x, y) >= 0

    def paint(self, x, y, S, pitch, soft):
        """Laid S cm wide, at the points (x, y) in its own units: (each one's weight, its colours (n, 3)
        or None for one colour). pitch: the cm a texel is there."""
        return smoothstep(-soft / 2, soft / 2, self.sd(x, y) * S), None

    def said(self, S):
        """Its size at S cm wide, in words."""
        return f"{S:.1f} cm wide"

    def area(self):
        """Its area, in squares of its width."""
        r = self.reach
        o = (np.arange(600) + 0.5) / 600 * 2 * r - r
        x, y = np.meshgrid(o, o)
        return float((self.sd(x, y) >= 0).mean() * (2 * r) ** 2)


def disc():
    return Shape(lambda x, y: 0.5 - np.hypot(x, y), 1.0, "disc", 0.5)


def ring(inner=0.6):
    """A ring: `inner` is its hole's width over its own."""
    def sd(x, y):
        r = np.hypot(x, y)
        return np.minimum(0.5 - r, r - 0.5 * inner)
    return Shape(sd, 1.0, "ring", 0.5)


def blob(wobble=0.1, seed=0):
    """A round spot that isn't quite round: its edge wanders up to about `wobble` of its radius in a
    few slow lobes, as a ladybird's spots do (shapes.blob's outline). Each seed gives another shape."""
    rnd = np.random.default_rng(seed)
    lobes = [(n, rnd.uniform(0.3, 1.0) / n, rnd.uniform(0, 2 * np.pi)) for n in (2, 3, 4)]
    scale = wobble / sum(amp for _, amp, _ in lobes)
    r0 = 0.5 / (1 + wobble)

    def sd(x, y):
        ang = np.arctan2(y, x)
        return r0 * (1 + scale * sum(amp * np.sin(m * ang + ph) for m, amp, ph in lobes)) - np.hypot(x, y)
    return Shape(sd, 1.0, "blob", 0.5)


def box(high=1.0, corner=0.0):
    """A box `high` times as high as it's wide, its corners rounded by `corner` of its width."""
    half = np.array([0.5, high / 2])
    c = min(corner, float(half.min()))

    def sd(x, y):
        qx, qy = np.abs(x) - (half[0] - c), np.abs(y) - (half[1] - c)
        return c - (np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0))
    return Shape(sd, high, "box")


def polygon(points, label="polygon"):
    """Any closed outline: its corners (x, y) in order, in its own units; scaled to one unit wide."""
    P = np.asarray(points, np.float64)
    lo, hi = P.min(0), P.max(0)
    P = (P - (lo + hi) / 2) / (hi[0] - lo[0])
    A, E = P, np.roll(P, -1, axis=0) - P
    B = A + E
    EE = (E * E).sum(1)
    slope = E[:, 0] / np.where(E[:, 1] == 0, 1, E[:, 1])

    def sd(x, y):
        q = np.stack([np.ravel(x), np.ravel(y)], 1).astype(np.float64)
        out = np.empty(len(q))
        for i in range(0, len(q), 65536):
            p = q[i:i + 65536, None, :]
            w = p - A
            t = np.clip((w * E).sum(-1) / EE, 0, 1)
            d = np.linalg.norm(w - t[..., None] * E, axis=-1).min(1)
            cross = (A[:, 1] > p[..., 1]) != (B[:, 1] > p[..., 1])  # the edges a line to the right of the point crosses
            inside = (cross & (p[..., 0] < A[:, 0] + (p[..., 1] - A[:, 1]) * slope)).sum(1) % 2 == 1
            out[i:i + 65536] = np.where(inside, d, -d)
        return out.reshape(np.shape(x))
    return Shape(sd, float((hi[1] - lo[1]) / (hi[0] - lo[0])), label, float(np.linalg.norm(P, axis=1).max()))


def star(points=5, inner=0.45):
    """A star with that many points, the first one up; inner: how deep its notches are (their radius
    over the points')."""
    a = np.pi / 2 + np.arange(2 * points) * np.pi / points
    r = np.where(np.arange(2 * points) % 2 == 0, 1.0, inner)
    return polygon(np.stack([r * np.cos(a), r * np.sin(a)], 1), "star")


class Picture(Shape):
    """A shape cut from a picture, an RGBA float array (h, w, 4) with values 0 to 1: its opaque pixels,
    cropped to them, one unit wide. kind: "picture", "words" or "placard"; box=True: its whole rectangle
    must lie on free room (words, a placard), else its opaque pixels (a cut-out); tall: the capitals'
    height over the width, for the notes. Painted by its own pixels, filtered first to the texel pitch
    where it lands so it can't alias, sampled premultiplied so the
    fringe takes no colour from clear pixels."""

    def __init__(self, image, kind="picture", box=False, label=None, text=None, tall=None):
        img = np.asarray(image, np.float32)
        rows, cols = np.nonzero(img[..., 3] > 0.02)
        if not len(rows):
            raise ValueError("an empty picture")
        self.image = np.ascontiguousarray(img[rows.min():rows.max() + 1, cols.min():cols.max() + 1])
        self.ih, self.iw = self.image.shape[:2]
        self.kind, self.text, self.box, self.tall = kind, text, box, tall
        self.handed = kind in ("words", "placard")
        ink = self.image[..., 3] >= 0.5
        self._sd = (ndimage.distance_transform_edt(ink) - ndimage.distance_transform_edt(~ink)) / self.iw
        self._filtered = {}
        super().__init__(self._distance, self.ih / self.iw, label or kind)

    def _distance(self, x, y):
        px, py = (x + 0.5) * self.iw - 0.5, (self.high / 2 - y) * self.iw - 0.5
        sd = ndimage.map_coordinates(self._sd, [np.ravel(py), np.ravel(px)], order=1, mode="nearest").reshape(np.shape(x))
        out = np.hypot(np.maximum(np.abs(x) - 0.5, 0), np.maximum(np.abs(y) - self.high / 2, 0))
        return sd - out

    def footprint(self, x, y):
        if self.box:
            return (np.abs(x) <= 0.5) & (np.abs(y) <= self.high / 2)
        return self.sd(x, y) >= 0

    def mirrored(self):
        return Picture(self.image[:, ::-1], self.kind, self.box, self.label, self.text, self.tall)

    def area(self):
        """Its ink's area, in squares of its width (its distance field runs on past its edge where the ink fills the
        picture, so the pixels say)."""
        return float((self.image[..., 3] >= 0.5).mean()) * self.high

    def _at_pitch(self, S, pitch):
        """The picture at about a pixel per texel when it's S cm wide: (h, w, 4), premultiplied."""
        want = S / pitch
        w2 = self.iw if self.iw <= 1.25 * want else max(2, int(round(want)))
        if w2 not in self._filtered:
            from PIL import Image
            pre = self.image * self.image[..., 3:4]
            if w2 < self.iw:
                h2 = max(2, int(round(self.ih * w2 / self.iw)))
                pre = np.stack([np.asarray(Image.fromarray(np.ascontiguousarray(pre[..., k]), "F").resize((w2, h2), Image.LANCZOS), np.float32)
                                for k in range(4)], -1)
            self._filtered[w2] = np.clip(pre, 0, 1)
        return self._filtered[w2]

    def paint(self, x, y, S, pitch, soft):
        pre = self._at_pitch(S, pitch)
        ih, iw = pre.shape[:2]
        px, py = (np.ravel(x) + 0.5) * iw - 0.5, (self.high / 2 - np.ravel(y)) * iw - 0.5
        got = [ndimage.map_coordinates(pre[..., k], [py, px], order=1, mode="constant", cval=0.0) for k in range(4)]
        a = got[3]
        rgb = np.stack(got[:3], 1) / np.maximum(a, 1e-6)[:, None]
        return a.reshape(np.shape(x)).astype(np.float32), rgb.reshape(np.shape(x) + (3,)).astype(np.float32)

    def said(self, S):
        return f"{S * self.tall:.1f} cm tall" if self.tall else f"{S:.1f} cm wide"


# ---- the panel ----

class _Panel:
    """The named parts on the body's texture: their texels (those they cover by half or more), each one's flat piece of
    the texture (island) and that piece's texel pitch in cm (the pitch a sticker is drawn at), and which of them are
    free room: in the open air, off the panels the game letters and the nose fin's plate, and in the zone the mark must
    stay in, if any."""

    def __init__(self, skin, c, ids):
        self.skin, self.c, self.ids = skin, c, ids
        cov = coverage.load(skin.parts, "Skin", c.w, c.h)
        t = [cov.sparse[i][0][cov.sparse[i][1] >= 128] for i in ids if i in cov.sparse]
        t = np.unique(np.concatenate(t)).astype(np.int64) if t else np.zeros(0, np.int64)
        label, density, _ = uvmap.islands("Skin")
        tri = c.bake["tri"].reshape(-1)[t]
        self.texels = t[tri >= 0]
        self.island = label[tri[tri >= 0]]
        self.pitch = 1.0 / np.maximum(density * c.w, 1e-9)  # by island
        self.rows, self.cols = np.divmod(self.texels, c.w)
        self._mask = None

    def mask(self):
        """The paint box's own weights for the parts: (texels, sorted; weights)."""
        if self._mask is None:
            self._mask = self.skin._mask("Skin", self.ids, None, self.c)
        return self._mask

    def pitch_at(self, texel):
        """The cm a texel is at a texel of the panel: the median step between neighbouring texels' places on the car,
        along the rows and the columns, within 8 texels; the island's own when too few are covered there."""
        c = self.c
        r, col = divmod(int(texel), c.w)
        r0, r1, c0, c1 = max(r - 8, 0), min(r + 9, c.h), max(col - 8, 0), min(col + 9, c.w)
        P, on = c.bake["position"][r0:r1, c0:c1].astype(np.float64), c.cov[r0:r1, c0:c1]
        steps = np.r_[np.linalg.norm(P[:, 1:] - P[:, :-1], axis=-1)[on[:, 1:] & on[:, :-1]],
                      np.linalg.norm(P[1:] - P[:-1], axis=-1)[on[1:] & on[:-1]]]
        steps = steps[steps < 1.0]  # not a step across a seam
        if len(steps) < 16:
            return float(self.pitch[self.island[np.searchsorted(self.texels, texel)]])
        return float(np.median(steps))

    def free(self, t, within=None, panels=True):
        """Which of the texels t are free room: in the open air (judge.OUTER), in `within` when given, and (panels) off
        the panels the game letters and the nose fin's plate and judge.CLEAR cm round them."""
        pos, nrm = self.c.pos[t], self.c.nrm[t]
        keep = carmap.load().value("open", pos, nrm) >= judge.OUTER
        if within is not None:
            keep &= within(pos, nrm) > 0.5
        if panels:
            keep &= ~_by_panels(self.skin, self.c, t)
        return keep

    def nearest(self, at):
        """The parts' texel nearest a point, how far off it is, and a word when the point was looked along an axis (a None
        coordinate) and nothing in line faced the look: the look comes from outside (along y from above, unless the
        parts face down; along x from the texel's own side; along z from the nearer end), and of the texels in line the
        one facing it most is taken (of the skin in the open air: not the inside of the body facing up); when none
        does (LOOK), the nearest that does, within OFF cm, else the one facing it most, said."""
        given = [k for k in range(3) if at[k] is not None]
        free = [k for k in range(3) if at[k] is None]
        p = self.c.pos[self.texels]
        d = np.sqrt(sum((p[:, k] - at[k]) ** 2 for k in given)) if given else np.zeros(len(p))
        j = int(d.argmin())
        if not free:
            return int(self.texels[j]), float(d[j]), None
        k = free[0]
        nrm = self.c.nrm[self.texels]
        if k == 1:
            look = np.full(len(p), -1.0 if nrm[:, 1].mean() < -0.3 else 1.0)
        else:
            look = np.sign(p[:, k])
            look[look == 0] = 1.0
        facing = nrm[:, k] * look
        for width in (0.5, 2.0, OFF):
            line = np.flatnonzero((d <= d[j] + width) & (facing >= LOOK))
            if len(line):  # the skin seen from outside, not hidden skin facing the look from inside the body
                line = line[carmap.load().value("open", p[line], nrm[line]) >= judge.OUTER]
            if len(line):
                i = int(line[facing[line].argmax()]) if width <= 0.5 else int(line[d[line].argmin()])
                return int(self.texels[i]), float(d[i]), None
        line = np.flatnonzero(d <= d[j] + 0.5)
        i = int(line[facing[line].argmax()])
        way = {0: "from the side", 1: "from below" if look[i] < 0 else "from above", 2: "from the front" if p[i, 2] > 0 else "from the back"}[k]
        return int(self.texels[i]), float(d[i]), f"seen {way}, the skin there faces away (its underside)"

    def window(self, r0, r1, c0, c1):
        """A window of the texture: (r0, r1, c0, c1) clipped to it, the parts' texels in it and where."""
        r0, r1, c0, c1 = max(r0, 0), min(r1, self.c.h), max(c0, 0), min(c1, self.c.w)
        sel = (self.rows >= r0) & (self.rows < r1) & (self.cols >= c0) & (self.cols < c1)
        return (r0, r1, c0, c1), sel

    def room(self, win, sel, within):
        """The free room in a window of the texture, off the model's crisp lines: (bool, each cell's island or -1)."""
        r0, r1, c0, c1 = win
        t, rr, cc = self.texels[sel], self.rows[sel] - r0, self.cols[sel] - c0
        island = np.full((r1 - r0, c1 - c0), -1, np.int32)
        island[rr, cc] = self.island[sel]
        room = np.zeros(island.shape, bool)
        if len(t):
            keep = self.free(t, within) & ~_creases(self.c)[t]
            room[rr[keep], cc[keep]] = True
        return room, island


def _creases(c):
    """Which texels of the body's texture lie within WALL cm of one of the model's crisp lines (tool/meshlines.py): the
    walls of a panel's room. Kept in the work folder."""
    from tool import fbx, meshlines, paths
    cache = paths.CACHE / f"creases_Skin_{c.w}x{c.h}_v1.npy"
    if cache.exists() and cache.stat().st_mtime > fbx.CACHE.stat().st_mtime:
        return np.load(cache)
    pts = []
    for L in meshlines.lines("Skin", fold=False):
        if L["kind"] != "crease":
            continue
        P = L["pts"]
        for a, b in zip(P[:-1], P[1:]):
            n = int(np.ceil(np.linalg.norm(b - a) / (WALL / 2))) + 2
            pts.append(a + (b - a) * np.linspace(0, 1, n)[:, None])
    on = np.flatnonzero(c.cov.reshape(-1))
    out = np.zeros(c.w * c.h, bool)
    if pts:
        d = cKDTree(np.vstack(pts)).query(c.pos[on], distance_upper_bound=WALL, workers=-1)[0]
        out[on[d <= WALL]] = True
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.save(cache, out)
    return out


def _by_panels(skin, c, t):
    """Which of the texels t lie on a panel the game letters or the nose fin's plate, or within
    judge.CLEAR cm of one on its face of the body."""
    cov = coverage.load(skin.parts, "Skin", c.w, c.h)
    out = np.zeros(len(t), bool)
    p = c.pos[t]
    for i, inst in enumerate(skin.parts.instances):
        if inst["name"] not in judge.PANELS or i not in cov.sparse:
            continue
        panel = cov.sparse[i][0][cov.sparse[i][1] >= 128].astype(np.int64)
        if not len(panel):
            continue
        q = c.pos[panel]
        box = np.flatnonzero(((p >= q.min(0) - judge.CLEAR) & (p <= q.max(0) + judge.CLEAR)).all(1))
        if not len(box):
            continue
        thin = q[np.unique(np.floor(q / 0.3).astype(np.int64), axis=0, return_index=True)[1]]
        d = cKDTree(thin).query(p[box], distance_upper_bound=judge.CLEAR, workers=-1)[0]
        facing = c.nrm[panel].mean(0)
        out[box[(d <= judge.CLEAR) & (c.nrm[t[box]] @ (facing / np.linalg.norm(facing)) > 0.3)]] = True
    return out


def _outward(n, at):
    """Where the top of words points on a surface facing n at `at`, upright to someone standing beside
    the car at the side it faces: the car's up on a side; on the top, away from them, towards the
    car's middle, or on the middle (within SIDE cm) towards the tail at the nose and the nose at the
    tail. Laid flat on the surface by _frame."""
    if abs(n[1]) < 0.7:
        return (0.0, 1.0, 0.0)
    v = np.array([n[0], 0.0, n[2]], np.float64)
    if np.linalg.norm(v) < 0.3:
        v = np.array([np.sign(at[0]) or 1.0, 0.0, 0.0]) if abs(at[0]) > SIDE else np.array([0.0, 0.0, np.sign(at[2]) or 1.0])
    return tuple(-v / np.linalg.norm(v))


def _frame(n, up, turn):
    """A mark's right and up on a surface facing n: `up` laid flat on it (the car's up on a side,
    forward on the top), turned `turn` degrees anticlockwise as it's looked at."""
    n = np.asarray(n, np.float64)
    n = n / np.linalg.norm(n)
    for want in ([up] if up is not None else []) + [(0, 1, 0) if abs(n[1]) < 0.7 else (0, 0, 1), (0, 0, 1), (1, 0, 0)]:
        u = np.asarray(want, np.float64)
        u = u - n * (u @ n)
        if np.linalg.norm(u) > 0.2:
            break
    u = u / np.linalg.norm(u)
    r = np.cross(u, n)
    a = np.radians(turn)
    return np.cos(a) * r + np.sin(a) * u, np.cos(a) * u - np.sin(a) * r, n


def _pole(panel, within, margin):
    """The named parts' roomiest spot: (its clear room in cm, the texel), the texel furthest from its
    room's edges; of those as far (within 2 %), the middle one of those on the car's middle, else of
    those on its left, else of the rest. None when the parts have no room. Found in the texture's own
    unfolding of each flat piece, which keeps the car's lengths within a few per cent."""
    c = panel.c
    best = None
    for isl in np.unique(panel.island):
        on = panel.island == isl
        win, sel = panel.window(panel.rows[on].min() - 2, panel.rows[on].max() + 3, panel.cols[on].min() - 2, panel.cols[on].max() + 3)
        room, _ = panel.room(win, sel & on, within)
        edt = np.where(room, ndimage.distance_transform_edt(np.pad(room, 1))[1:-1, 1:-1] * panel.pitch[isl], 0)
        if edt.max() <= margin:
            continue
        x = c.bake["position"][win[0]:win[1], win[2]:win[3], 0]
        far = edt >= 0.98 * edt.max()
        for rank, side in enumerate((np.abs(x) <= MIDDLE, x > MIDDLE, x < -MIDDLE)):
            rr, cc = np.nonzero(far & side)
            if not len(rr):
                continue
            j = int(np.argmin((rr - rr.mean()) ** 2 + (cc - cc.mean()) ** 2))
            got = (float(edt.max()), -rank, (win[0] + int(rr[j])) * c.w + win[2] + int(cc[j]))
            if best is None or got[0] > best[0] + 0.05 or (got[0] >= best[0] - 0.05 and got[1] > best[1]):
                best = got
            break
    return None if best is None else (best[0], best[2])


def rooms(names, least=12.0, most=2, size=1024):
    """The named body parts' flat rooms, for car/anatomy.md: the biggest discs of free room on each part (as a mark's:
    off the model's crisp lines, in the open air, clear of the game's panels) whose skin turns no more than WORD_TURN
    degrees from one way, so words read flat on them, `least` cm across or more, on the left side and the middle:
    {part: [(across in cm, centre, facing), ...]}, the roomiest first, at most `most`, each clear of the ones before.
    Measured on a `size`² texture, in the texture's own unfolding."""
    from tool import paintbox
    skin = paintbox.Skin("TSC_Rooms", size=size)
    c = skin.canvas("Skin")
    ways = carmap.directions().astype(np.float32)
    flat = np.cos(np.radians(WORD_TURN))
    out = {}
    for name in names:
        panel = _Panel(skin, c, skin._ids(name, warn=False).get("Skin", []))
        if not len(panel.texels):
            continue
        win, sel = panel.window(panel.rows.min() - 2, panel.rows.max() + 3, panel.cols.min() - 2, panel.cols.max() + 3)
        room, island = panel.room(win, sel, None)
        r0, r1, c0, c1 = win
        nrm, pos = c.bake["normal"][r0:r1, c0:c1], c.bake["position"][r0:r1, c0:c1]
        room &= pos[..., 0] > -MIDDLE
        found = []
        for isl in np.unique(island[room]):
            on = room & (island == isl)
            for d in ways:
                f = on & ((nrm @ d) >= flat)
                if f.sum() < 4:
                    continue
                edt = ndimage.distance_transform_edt(np.pad(f, 1))[1:-1, 1:-1] * float(panel.pitch[isl])
                k = np.unravel_index(int(edt.argmax()), edt.shape)
                found.append((2 * float(edt[k]), pos[k].astype(np.float64), nrm[k].astype(np.float64)))
        kept = []
        for across, centre, facing in sorted(found, key=lambda f: -f[0]):
            if across < least or len(kept) == most:
                break
            if all(np.linalg.norm(centre - k[1]) > k[0] / 2 + across / 2 for k in kept):
                kept.append((across, centre, facing / np.linalg.norm(facing)))
        if kept:
            out[name] = kept
    return out


# ---- the sticker's sheet ----

def _surface():
    from tool import surface
    return surface.load()


def _chart_at(c, texel, up, turn, reach, crease):
    """A chart (tool/surface.py) centred on a texel: its frame from the surface's facing there, `up` laid flat on it (a
    word, "outward": _outward) and turned; (the chart, the up it was given, as a vector)."""
    S = _surface()
    p = c.pos[texel].astype(np.float64)
    n0 = S.facing(p[None])[0]
    if isinstance(up, str):
        up = _outward(n0, p)
    right, upv, _ = _frame(n0, up, turn)
    return S.chart(p, right, upv, reach, crease), up


class _Sheet:
    """A chart's surroundings as a flat sheet of square cells, `pitch` cm each (the panel's texel pitch), to try a shape
    on: the panel's texels on the chart with their places (t, xy), which of them are free room (free), and the sheet:
    on, the cells with skin (each texel marks the cell it falls in and the next one towards it, so the sheet has no
    holes between texels), room, those free (a cell any unfree texel reaches isn't), cell, a texel of each cell (for
    its place on the car), xpos, the car's x there. k: cells from the centre to the sheet's edge, the centre at (k, k)."""

    def __init__(self, chart, panel, within, reach, pitch, panels=True):
        c = panel.c
        self.chart, self.panel, self.pitch, self.reach = chart, panel, pitch, reach
        box = np.flatnonzero(np.linalg.norm(c.pos[panel.texels] - chart.centre.astype(np.float32), axis=1) <= reach + 1.0)
        t = panel.texels[box]
        g, wt = chart.faces_at(c.w, t)
        xy = chart.read(chart.xy, faces=(g, wt))
        ok = np.isfinite(xy).all(1) & (np.abs(xy) <= reach).all(1)
        self.t, self.xy, self.stretch = t[ok], xy[ok], chart.stretch()[np.maximum(g[ok], 0)]
        self.lost = t[~ok]  # the panel's texels round the centre with no place on the sticker (_missing)
        self.free = panel.free(self.t, within, panels)
        k = self.k = int(np.ceil(reach / pitch)) + 2
        n = 2 * k + 1
        gxy = self.xy / pitch + k
        i0 = np.clip(np.floor(gxy).astype(np.int64), 0, n - 1)  # (m, 2): the column (X) and the row (Y)
        step = np.where(gxy - i0 >= 0.5, 1, -1)
        on, blocked = np.zeros((n, n), bool), np.zeros((n, n), bool)
        for dx in (0, 1):
            for dy in (0, 1):
                col = np.clip(i0[:, 0] + dx * step[:, 0], 0, n - 1)
                row = np.clip(i0[:, 1] + dy * step[:, 1], 0, n - 1)
                on[row, col] = True
                blocked[row[~self.free], col[~self.free]] = True
        self.on, self.room = on, on & ~blocked
        self.cell = np.full((n, n), -1, np.int64)
        self.cell[i0[:, 1], i0[:, 0]] = np.arange(len(self.t))
        self.xpos = np.zeros((n, n), np.float32)
        self.xpos[i0[:, 1], i0[:, 0]] = c.pos[self.t, 0]

    def erode(self, margin):
        """The room kept `margin` cm in from its edges."""
        if margin > 0:
            self.room &= ndimage.distance_transform_edt(np.pad(self.room, 1))[1:-1, 1:-1] * self.pitch >= margin

    def clear(self):
        """The clear room round the centre, in cm: how far the nearest cell outside the room is."""
        return float(ndimage.distance_transform_edt(np.pad(self.room, 1))[1:-1, 1:-1][self.k, self.k]) * self.pitch

    def near(self, reach, goal=(0.0, 0.0), along=False, centred=False):
        """The cells a shape's middle may go to, and how far each is from the goal (cm², for the nearest): within `reach`
        cm of the goal on the sheet (at least the cell itself), on the centre's own line (along: words along a course
        stay on it), on the car's middle (centred), and a cell with a texel of its own."""
        o = (np.arange(2 * self.k + 1) - self.k) * self.pitch
        dx, dy = o[None, :] - goal[0], o[:, None] - goal[1]
        aim = dx * dx + dy * dy
        near = (aim <= max(reach, 0.75 * self.pitch) ** 2) & (self.cell >= 0)
        if along:
            near &= np.abs(dy) <= 0.75 * self.pitch
        if centred:
            near &= np.abs(self.xpos) <= max(0.3, 1.5 * self.pitch)
        return near, aim

    def _foot(self, shape, S, pad, turn):
        """The kernel round a middle for the shape S cm wide, turned `turn` degrees: its points in the shape's own units,
        and k, its half width in cells."""
        k = int(np.ceil((S * shape.reach + pad) / self.pitch)) + 1
        o = np.arange(-k, k + 1) * self.pitch / S
        x, y = np.meshgrid(o, o)
        return (*_turned(x, y, turn), k)

    def fit(self, shape, size, near, aim, least, turn=0.0):
        """The place nearest the goal, among `near`, where the shape `size` cm wide (turned `turn` degrees on the sheet)
        covers no cell outside the room; shrunk by halves down to `least` of its size when there's none: (X, Y, size),
        or None."""
        wall = (~self.room).astype(np.float64)

        def whole(S):
            x, y, k = self._foot(shape, S, 0.0, turn)
            K = shape.footprint(x, y).astype(np.float64)
            return (fftconvolve(np.pad(wall, k, constant_values=1.0), K[::-1, ::-1], mode="valid") < 0.5) & near

        ok, s = whole(size), 1.0
        if not ok.any():
            ok, s = whole(size * least), least
            if not ok.any():
                return None
            hi = 1.0
            for _ in range(7):
                mid = (s + hi) / 2
                got = whole(size * mid)
                if got.any():
                    ok, s = got, mid
                else:
                    hi = mid
        j = int(np.where(ok, aim, np.inf).argmin())
        jr, jc = divmod(j, ok.shape[1])
        return (jc - self.k) * self.pitch, (jr - self.k) * self.pitch, size * s

    def paint(self, shape, S, X0, Y0, soft, turn=0.0):
        """The shape S cm wide with its middle at (X0, Y0) on the sheet, turned `turn` degrees, over the sheet's texels:
        (which (indices into t), their weights, their colours (n, 3) or None)."""
        x, y = _turned((self.xy[:, 0] - X0) / S, (self.xy[:, 1] - Y0) / S, turn)
        sel = np.flatnonzero(x * x + y * y <= (shape.reach + (soft + self.pitch) / S) ** 2)
        w, rgb = shape.paint(x[sel], y[sel], S, self.pitch, soft)
        on = w > 0.002
        return sel[on], w[on].astype(np.float32), None if rgb is None else rgb[on]

    def texel_at(self, X, Y):
        """The texel nearest a place on the sheet, as an index into t."""
        return int(np.argmin(np.hypot(self.xy[:, 0] - X, self.xy[:, 1] - Y)))


def _turned(x, y, turn):
    """Points on the sheet in the frame of a shape turned `turn` degrees anticlockwise on it."""
    if not turn:
        return x, y
    ca, sa = np.cos(np.radians(turn)), np.sin(np.radians(turn))
    return ca * x + sa * y, ca * y - sa * x


def _sits(sheet, sel, w):
    """How a shape painted on a sheet sits: the stretch under its ink (its 90th percentile, a share), the share of its
    ink where the sticker is torn or folded (TORN), and the surface's turn under it (degrees from the chart's facing,
    its 99th percentile)."""
    ink = sel[w > 0.5]
    if not len(ink):
        return 0.0, 0.0, 0.0
    st = sheet.stretch[ink]
    torn = ~np.isfinite(st) | (st >= TORN)
    stretch = float(np.percentile(st[~torn], 90)) if (~torn).any() else float("inf")
    nrm = sheet.panel.c.nrm[sheet.t[ink]].astype(np.float64)
    turn = float(np.percentile(np.degrees(np.arccos(np.clip(nrm @ sheet.chart.facing, -1, 1))), 99))
    return stretch, float(torn.mean()), turn


def _missing(sheet, sel, w, within):
    """What of a laid shape's ink found no paint: (chipped: (cm², how wide, where) or None; kept off: {why: cm²}).
    Kept off: the sheet's texels inside the ink that aren't free room (its zone; hidden skin and the game's panels,
    which a sticker pressed over every edge covers as it is). Chipped: the panel's texels round the centre with no
    place on the sticker (the chart dropped or folded there) that lie inside the painted ink in space (within CHIP cm
    of the painted texels all round: a closing), facing as the sticker does, free and bare."""
    c, panel, pitch = sheet.panel.c, sheet.panel, sheet.pitch
    ink = w > 0.5
    off = sel[ink & ~sheet.free[sel]]
    kept = {}
    if len(off):
        t = sheet.t[off]
        pos, nrm = c.pos[t], c.nrm[t]
        hidden = carmap.load().value("open", pos, nrm) < judge.OUTER
        zoned = np.zeros(len(t), bool) if within is None else within(pos, nrm) <= 0.5
        for why, m in (("hidden skin", hidden), ("its zone", zoned & ~hidden), ("the game's panels", ~hidden & ~zoned)):
            if m.any():
                kept[why] = float(m.sum()) * pitch * pitch
    painted = sheet.t[sel[ink & sheet.free[sel]]]
    lost = sheet.lost
    if len(painted) < 20 or not len(lost):
        return None, kept
    P = c.pos[painted].astype(np.float64)
    L = c.pos[lost].astype(np.float64)
    near = np.all((L >= P.min(0) - CHIP) & (L <= P.max(0) + CHIP), axis=1)
    lost, L = lost[near], L[near]
    if len(lost):
        keep = (c.nrm[lost] @ sheet.chart.facing > 0.3) & panel.free(lost, within, False)
        lost, L = lost[keep], L[keep]
    if not len(lost):
        return None, kept
    V = max(0.15, pitch)
    lo = P.min(0) - 2 * CHIP
    dims = np.ceil((P.max(0) + 2 * CHIP - lo) / V).astype(int) + 1
    grid = np.zeros(dims, bool)
    grid[tuple(((P - lo) / V).astype(int).T)] = True
    r = CHIP / V
    dilated = ndimage.distance_transform_edt(~grid) <= r
    closed = ndimage.distance_transform_edt(dilated) > r
    hit = (closed & ~grid)[tuple(np.clip(((L - lo) / V).astype(int), 0, dims - 1).T)]
    if hit.sum() * pitch * pitch < CHIP_AREA:
        return None, kept
    Q = L[hit]
    return (float(hit.sum()) * pitch * pitch, float(np.ptp(Q, axis=0).max()) if len(Q) > 1 else pitch, Q), kept


def _laid(sheet, shape, S, X0, Y0, soft, moved, within=None):
    """A shape painted on a sheet, as `put` takes it: {texel (its middle), size, moved, idx, m, rgb, right, up, facing,
    flat (cm² its ink covers), stretch, torn, turn, landed (the share of its footprint that found free skin), chips and
    kept (_missing)}."""
    c, panel = sheet.panel.c, sheet.panel
    sel, w, rgb = sheet.paint(shape, S, X0, Y0, soft)
    chips, kept = _missing(sheet, sel, w, within)
    if within is not None:
        w = w * within(c.pos[sheet.t[sel]], c.nrm[sheet.t[sel]]).astype(np.float32)
    keep = sheet.free[sel] & (w > 0.002)
    sel, w, rgb = sel[keep], w[keep], None if rgb is None else rgb[keep]
    stretch, torn, turn = _sits(sheet, sel, w)
    texels = sheet.t[sel]
    idx, m = panel.mask()
    at = np.minimum(np.searchsorted(idx, texels), len(idx) - 1)
    mine = idx[at] == texels
    ink = judge.area(c, texels[w > 0.5]) if (w > 0.5).any() else 0.0  # cm² its ink covers, from the texels' places
    return {"texel": int(sheet.t[sheet.texel_at(X0, Y0)]), "size": S, "moved": moved, "idx": texels[mine], "m": m[at[mine]] * w[mine],
            "rgb": None if rgb is None else rgb[mine], "right": sheet.chart.right, "up": sheet.chart.up, "facing": sheet.chart.facing,
            "flat": ink, "stretch": stretch, "torn": torn, "turn": turn, "landed": ink / max(shape.area() * S * S, 1e-9),
            "chips": chips, "kept": kept}


def _fit(c, panel, shape, size, anchor, up, turn, margin, reach, within, centred, least, soft):
    """Lay a shape as near a texel as it's whole (the key above), on its own panel (the chart cut along the model's crisp
    lines): _laid's dict, or None with no room for it. size None: the biggest that fits with its middle there. up:
    where its top points on the car, or "outward" (_outward). A shape that moves is pressed on afresh where it goes,
    on its own chart there, and shrunk if the surface there asks it."""
    pitch = panel.pitch_at(anchor)
    span = (size * shape.reach if size else 40.0) + reach + margin + soft + 1.5
    chart, up = _chart_at(c, anchor, up, turn, span, True)
    sheet = _Sheet(chart, panel, within, span, pitch)
    sheet.erode(margin)
    if size is None:  # twice the clear room round the texel, the most a shape as wide could take
        clear = sheet.clear()
        if clear <= 0.5:
            return None
        size, reach, least = 2 * clear / shape.reach, 0.0, 0.25
    near, aim = sheet.near(reach, centred=centred)
    got = sheet.fit(shape, size, near, aim, least)
    if got is None:
        return None
    X0, Y0, S = got
    moved = float(np.hypot(X0, Y0))
    if moved > 0.75 * pitch:
        there = int(sheet.t[sheet.texel_at(X0, Y0)])
        span = S * shape.reach + margin + soft + 1.5
        chart2, _ = _chart_at(c, there, up, turn, span, True)
        sheet2 = _Sheet(chart2, panel, within, span, pitch)
        sheet2.erode(margin)
        got = sheet2.fit(shape, S, *sheet2.near(0.0), least)
        if got is not None:
            sheet, (X0, Y0, S) = sheet2, got
    return _laid(sheet, shape, S, X0, Y0, soft, moved)


def _fit_along(c, panel, shape, size, course, margin, reach, within, least, soft, mirrored):
    """Lay a shape along a course, reading along it (the course's chart, tool/course.py): at the stretch's middle, or
    the nearest place along the stretch where it's whole within `reach` cm, shrunk down to `least` when there's
    none: _laid's dict, or None."""
    s0 = course.length / 2
    centre = course.at(s=s0)
    anchor = panel.nearest(centre)[0]
    pitch = panel.pitch_at(anchor)
    across = size * shape.high / 2 + margin + soft + 1.5
    span = course.length / 2 + size * shape.reach + 2.0
    chart = course.chart(s0, across, mirrored)
    sheet = _Sheet(chart, panel, within, span, pitch)
    sheet.erode(margin)
    got = sheet.fit(shape, size, *sheet.near(reach, along=True), least)
    if got is None:
        return None
    X0, Y0, S = got
    return _laid(sheet, shape, S, X0, Y0, soft, abs(X0))


def _press(c, panel, shape, size, anchor, up, turn, within, soft):
    """A shape pressed onto the car at a texel as it is, over every edge and crisp line in its footprint, onto the
    skin in the open air there: _laid's dict (moved 0; landed says what found skin)."""
    pitch = panel.pitch_at(anchor)
    span = size * shape.reach + soft + 1.5
    chart, _ = _chart_at(c, anchor, up, turn, span, False)
    sheet = _Sheet(chart, panel, within, span, pitch, panels=False)
    return _laid(sheet, shape, size, 0.0, 0.0, soft, 0.0, within)


# ---- Skin.mark and Skin.decal ----

def _where(panel):
    names = list(dict.fromkeys(panel.skin.parts.instances[i]["name"] for i in panel.ids))
    return "the " + (names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1])


def _stroke(at, size, reach):
    """`at` as a point: the points of a line the user drew become its middle, and the mark may go
    anywhere along it; a course (tool/course.py) its middle point. (a point, reach)."""
    if hasattr(at, "pts"):
        if reach is None:
            reach = at.length / 2 + (size or 0.0) / 2
        return at.middle, reach
    if at is None or np.isscalar(at[0]) or at[0] is None:
        return at, reach
    P = np.asarray(at, np.float64)
    mid = P.mean(0)
    if reach is None:
        reach = float(np.linalg.norm(P - mid, axis=1).max()) + (size or 0.0) / 2
    return tuple(mid), reach


def _how(got, shape):
    """How a laid shape sits, in words: its stretch (from STRETCH), where it's torn, the turn under words (from
    WORD_TURN); [] when it sits flat."""
    said = []
    if got["torn"] >= 0.01:
        said.append(f"{got['torn']:.0%} of it where the sticker would tear or fold over itself")
    elif got["stretch"] >= STRETCH:
        said.append(f"stretched {got['stretch']:.0%} under it (the surface curves two ways)")
    if shape.handed and got["turn"] > WORD_TURN:
        said.append(f"the surface turns {got['turn']:.0f}° under it, more than {WORD_TURN:.0f}: it will read bent")
    return said


def lay(skin, where, what, shape, size, at, colour, finish, up, turn, margin, reach, within, mirror, across, soft, params):
    if not isinstance(shape, Shape):
        raise TypeError("a mark's shape is one of tool/marks.py's: marks.disc(), marks.star(5), marks.polygon([...])")
    from tool import finishes
    name = skin.ops[skin._op]["what"]
    flip = np.array([-1.0, 1.0, 1.0])
    picture = isinstance(shape, Picture)
    targets = skin._ids(where, warn=False)
    if picture:
        fin, col = finishes.get(finish or "gloss") if isinstance(finish, str) else finish, None
    else:
        params = {"seed": skin.seed, **params}
        col, fin, leftover = skin._resolve(what, colour, finish, "gloss", params)
        if leftover:
            skin.notes.append(f"{what!r}: didn't understand {' '.join(leftover)!r}")
        skin.palette.append([float(v) for v in col])
    c = skin.canvas("Skin")
    panel = _Panel(skin, c, targets.get("Skin", []))
    course = at if hasattr(at, "pts") else None
    at, reach = _stroke(at, size, reach)
    rec = skin.receipt  # the verb's receipt: where the mark lands (tool/receipt.py)
    nowhere = rec.landed([v or 0 for v in at] if at is not None else (0, 0, 0))
    if not len(panel.texels):
        skin.notes.append(f"{name}: {'pictures' if picture else 'marks'} go on the body; nothing laid")
        return nowhere
    if up is None and shape.handed:
        up = "outward"

    def put(got, shown, place=None):
        """Paint a fitted shape, keep what the judge reads, and say when it isn't whole (a finding): where it landed,
        on `place` (the verb's receipt) or a place of its own (a twin's)."""
        idx, m, rgb = got["idx"], got["m"], got["rgb"]
        step = skin.ops[skin._op]["step"]
        if got["chips"]:
            area, wide, Q = got["chips"]
            where_, z, side = judge._where(Q)
            skin.findings.append({"check": "whole", "kind": "cut", "z": z, "side": side, "step": step,
                                  "text": f"{name}: chipped: {area:.1f} cm² of it missing where the skin is bare, a bite "
                                          f"{wide:.1f} cm wide, {where_}"})
        on = idx[m > 0.5]
        expected = shown.area() * got["size"] ** 2
        share = judge.area(c, on) / expected if len(on) and expected > 0 else 0.0
        kept = {k: v for k, v in got["kept"].items() if k == "its zone" or not across}
        if share < judge.WHOLE or sum(kept.values()) >= BITE:
            why = ", ".join(f"{a:.1f} cm² kept off by {k}" for k, a in sorted(kept.items(), key=lambda kv: -kv[1]))
            where_, z, side = judge._where(c.pos[on]) if len(on) else ("", None, None)
            skin.findings.append({"check": "whole", "kind": "cut", "z": z, "side": side, "step": step,
                                  "text": f"{name}: not whole: {share:.0%} of its {expected:.0f} cm² is on the car"
                                          f"{' (' + why + ')' if why else ''}, {where_}"})
        if skin.measure:
            on = np.sort(idx[m > 0.5])
            rec = {"op": skin._op, "step": skin.ops[skin._op]["step"], "what": name, "idx": on, "under": c.owner[on].copy(),
                   "kind": shape.kind, "whole": got["flat"] if picture else shown.area() * got["size"] ** 2, "text": shape.text,
                   # a picture's whole is what its ink covers: it thins where a stroke is a texel wide
                   "pixels": shape.iw / got["size"] if picture else np.inf, "frame": (got["right"], got["up"], got["facing"]),
                   "stretch": got["stretch"], "turn": got["turn"]}
            if across:
                skin.pictures.append({**rec, "across": True})
            else:
                skin.marks.append(rec)
        if rgb is None:
            skin._lay(c, "Skin", idx, m, fin, col, params, where)
        else:
            c.blend(idx, m, np.clip(rgb, 0, 1), np.full(len(idx), fin.roughness, np.float32),
                    np.full(len(idx), fin.metalness, np.float32), np.full(len(idx), fin.varnish, np.float32))
        place = receipt.Receipt(name, step) if place is None else place
        return place.landed(c.pos[got["texel"]], got["size"], got["moved"], got["right"], got["up"], got["facing"], got["stretch"],
                            got["turn"], shown.said(got["size"]))

    def place(point):
        """The panel's texel for a point wanted, with its notes."""
        texel, off, seen = panel.nearest(point)
        if seen:
            skin.notes.append(f"{name}: `at` {seen}; laid on the nearest skin facing the look, {off:.0f} cm away")
        elif off > OFF:
            skin.notes.append(f"{name}: `at` is {off:.0f} cm off {_where(panel)}; laid at the nearest place on it")
        return texel

    if across:
        if at is None or size is None:
            raise ValueError("a mark laid across the panels needs `at` and its width")
        anchor = place(at)
        got = _press(c, panel, shape, size, anchor, up, turn, within, soft)
        if not len(got["idx"]):
            skin.notes.append(f"{name}: nothing landed on the car")
            return nowhere
        laid = put(got, shape, rec)
        said = _how(got, shape)
        if got["landed"] < 0.97:
            said.insert(0, f"{got['landed']:.0%} of it landed on the car; the rest falls in a gap or off an edge")
        if said:
            skin.notes.append(f"{name}: {'; '.join(said)}")
        if mirror and abs(laid.centre[0]) > MIDDLE:
            other, off, _ = panel.nearest(np.asarray(laid.centre) * flip)
            if off <= 2.0:
                up2 = up if up is None or isinstance(up, str) else np.asarray(up, np.float64) * flip
                twin = _press(c, panel, shape if shape.handed else shape.mirrored(), size, other, up2, -turn, within, soft)
                if len(twin["idx"]):
                    laid.twin = put(twin, shape)
        return laid

    if course is not None:
        got = _fit_along(c, panel, shape, size, course, margin, reach, within, LEAST, soft, False)
    else:
        if at is None:
            pole = _pole(panel, within, margin)
            if pole is None:
                skin.notes.append(f"{name}: no free room on {_where(panel)} (the game letters it, or it's hidden); nothing laid")
                return nowhere
            anchor = pole[1]
        else:
            anchor = place(at)
        wanted = c.pos[anchor].astype(np.float64)
        centred = abs(wanted[0]) <= MIDDLE
        move = (size / 2 if size is not None else 0.0) if reach is None else reach
        got = _fit(c, panel, shape, size, anchor, up, turn, margin, move, within, centred, LEAST, soft)
    if got is None:
        if course is not None:
            under = skin._part_at(course.middle)
            where_ = f"along {course.name} on {_where(panel)}" + (f" (the line runs over the {under})" if under not in _where(panel) else "")
        else:
            where_ = f"on {_where(panel)} at ({', '.join(f'{v:.0f}' for v in wanted)})"
        skin.notes.append(f"{name}: no room for it {where_}" + (f", even at {LEAST:.0%} of its {shape.said(size)}" if size is not None else "")
                          + "; nothing laid")
        return nowhere
    laid = put(got, shape, rec)
    said = []
    if at is None or size is None:
        said.append(f"laid at ({', '.join(f'{v:.0f}' for v in laid.centre)}), {shape.said(laid.size)}")
    if at is not None and laid.moved >= 0.5:
        said.append(f"moved {laid.moved:.1f} cm" + (" along the line" if course is not None else ""))
    if size is not None and laid.size < 0.99 * size:
        said.append(f"shrunk to {shape.said(laid.size)} ({laid.size / size:.0%} of its {shape.said(size).split(' cm')[0]})")
    if said:
        skin.notes.append(f"{name}: {', '.join(said)}" + (f", to stay whole on {_where(panel)}" if len(said) > (at is None or size is None) else ""))
    how = _how(got, shape)
    if how:
        skin.notes.append(f"{name}: {'; '.join(how)}")
    if mirror and abs(laid.centre[0]) > MIDDLE:
        twin_shape = shape if shape.handed else shape.mirrored()
        up2 = up if up is None or isinstance(up, str) else np.asarray(up, np.float64) * flip
        if course is not None:
            other, off, _ = panel.nearest(np.asarray(laid.centre) * flip)
            twin = _fit_along(c, panel, twin_shape, laid.size, course, margin, reach, within, 0.99, soft, True) if off <= 2.0 else None
            if twin is None and off <= 2.0:
                twin = _fit_along(c, panel, twin_shape, laid.size, course, margin, reach, within, LEAST, soft, True)
        else:
            other, off, _ = panel.nearest(np.asarray(laid.centre) * flip)
            twin = None
            if off <= 2.0:  # the named parts are on the other side too: its mirror image's place, within a centimetre
                twin = _fit(c, panel, twin_shape, laid.size, other, up2, -turn, margin, 1.0, within, False, 0.99, soft)
                if twin is None:
                    other, _, _ = panel.nearest(wanted * flip)
                    twin = _fit(c, panel, twin_shape, laid.size, other, up2, -turn, margin, move, within, False, LEAST, soft)
        if off > 2.0:
            return laid
        if twin is None:
            skin.notes.append(f"{name}: no room for its twin on the other side; laid on one side only")
        else:
            if twin["size"] < 0.99 * laid.size or twin["moved"] > 1.5:
                skin.notes.append(f"{name}: its twin on the other side doesn't fit as its mirror image: laid "
                                  f"{shape.said(twin['size'])}, {twin['moved']:.1f} cm from where it was wanted")
            laid.twin = put(twin, twin_shape)
            if abs(laid.centre[0]) < laid.size * shape.reach:
                skin.notes.append(f"{name}: it reaches the car's middle, where its twin meets it (mirror=False for one, "
                                  f"or x = 0 in `at` for one on the middle)")
    return laid
