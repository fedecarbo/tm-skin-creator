"""Marks: a shape laid on a named panel of the body, whole inside its edges (Skin.mark in
tool/paintbox.py, whose docstring says how to call it). The user, 2026-10-05: "it shouldn't do
mistakes in the first place".

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

A mark is laid in the body's own unfolding (tool/uvmap.py: each panel flat on the texture with
almost no stretch), drawn true to the car's lengths where it lands, so it follows the panel's curve
as a cut sticker does and is never drawn through the car. Its room is the named parts' skin round
where it's wanted, on one flat piece of the unfolding, without:
  - what isn't theirs: the parts' edges, the texture's seams;
  - hidden skin: inside an inlet, under another panel (the car map's open air, measure.OUTER);
  - creases and rolls: where the surface turns more than FOLD degrees within SPAN cm;
  - what faces more than BEND degrees away from where it's wanted (WORD_BEND for words and a
    placard, which read best flat: the user, 2026-10-05, of lettering along a flank's curve: "the text
    is big for the curvature of the surface");
  - the panels the game letters and the nose fin's plate, and checks.CLEAR cm round them;
  - `margin` cm in from all of those.
The mark goes where it's wanted if it's whole there; else to the nearest place it is, within `reach`;
else it shrinks until one exists, down to LEAST of its size; else nothing is laid. Each of those is
a note. Wanted at a course (tool/course.py, a stretch of one of the car's lines or of the line the
user drew), it goes at the course's middle, anywhere along it, reading along it. Wanted on the car's middle, it stays on the middle. Its twin on the other side is its mirror
image, at the same size; words and a placard are laid there as they are, reading forward on each
side. They face the free room they land on, not the texel under `at` (a lip's face, a bolt), and
unless the design says where their top points, they're upright to someone standing beside the car
at the side the surface faces: on the top, their top towards the car's middle (`_outward`).
"""

import numpy as np
from scipy import ndimage
from scipy.signal import fftconvolve
from scipy.spatial import cKDTree

from tool import carmap, coverage, measure, shapes, uvmap
from tool.noise import smoothstep

FOLD = 20.0   # degrees: a crease or a roll sharper than this, within SPAN cm, ends a mark's room
SPAN = 0.5    # cm
BEND = 30.0   # degrees: a mark's room faces within this of where it's wanted
WORD_BEND = 20.0  # degrees: the same for words and a placard, which read best flat (the user rejected lettering over
# a flank turning 38 degrees from its mean and kept lettering over 16, 2026-10-05)
SIDE = 30.0   # cm from the car's middle: words on the top further out read from beside the car, nearer from its ends
LEAST = 0.4   # the smallest share of its size a mark is shrunk to
OFF = 5.0     # cm: `at` further than this from the panel is said
MIDDLE = 0.5  # cm from the car's middle: a mark wanted nearer is centred, and has no twin


# ---- the shapes ----

class Shape:
    """A flat shape one unit wide, centred on its middle: sd(x, y) is the distance to its edge, positive
    inside (x to its right, y up, arrays of any shape); high: its height over its width; reach: how
    far its edge gets from its middle. kind: what it is for the notes and the checks; handed: its twin
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
    where it lands so it can't alias (tool/paint.py's fit_to_texels), sampled premultiplied so the
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


# ---- where a mark landed ----

class Laid:
    """Where a mark landed: centre (x, y, z in cm, on the car), size (its width in cm as laid; 0 when
    nothing was), moved (cm from where it was wanted), right, up and facing (the frame it lies in),
    twin (the same for its mirror image on the other side, or None)."""

    def __init__(self, centre, size=0.0, moved=0.0, right=(0, 0, -1), up=(0, 1, 0), facing=(1, 0, 0)):
        self.centre = tuple(round(float(v), 2) for v in centre)
        self.size, self.moved = float(size), float(moved)
        self.right, self.up, self.facing = (tuple(float(v) for v in d) for d in (right, up, facing))
        self.twin = None

    def __bool__(self):
        return self.size > 0

    def spot(self):
        """The place as Skin.text, Skin.placard and Skin.decal take one (they take the Laid itself too)."""
        return dict(centre=self.centre, up=tuple(round(v, 4) for v in self.up))


# ---- the panel on the texture ----

class _Panel:
    """The named parts on the body's texture: their texels (those they cover by half or more), each
    one's flat piece of the unfolding (island), and that piece's texel pitch in cm."""

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

    def nearest(self, at):
        """The parts' texel nearest a point (a None coordinate is looked along: of the texels in line,
        the one facing most that way), and how far off it is."""
        given = [k for k in range(3) if at[k] is not None]
        p = self.c.pos[self.texels]
        d = np.sqrt(sum((p[:, k] - at[k]) ** 2 for k in given))
        j = int(d.argmin())
        free = [k for k in range(3) if at[k] is None]
        if free:
            line = np.flatnonzero(d <= d[j] + 0.5)
            j = int(line[self.c.nrm[self.texels[line]][:, free[0]].argmax()])
        return int(self.texels[j]), float(d[j])

    def window(self, r0, r1, c0, c1):
        """A window of the texture: (r0, r1, c0, c1) clipped to it, the parts' texels in it and where."""
        r0, r1, c0, c1 = max(r0, 0), min(r1, self.c.h), max(c0, 0), min(c1, self.c.w)
        sel = (self.rows >= r0) & (self.rows < r1) & (self.cols >= c0) & (self.cols < c1)
        return (r0, r1, c0, c1), sel

    def room(self, win, sel, fold, within):
        """The free room in a window: (the texels a mark may cover, each texel's island or -1)."""
        c = self.c
        r0, r1, c0, c1 = win
        t, rr, cc = self.texels[sel], self.rows[sel] - r0, self.cols[sel] - c0
        island = np.full((r1 - r0, c1 - c0), -1, np.int32)
        island[rr, cc] = self.island[sel]
        room = np.zeros(island.shape, bool)
        if not len(t):
            return room, island
        pos, nrm = c.pos[t], c.nrm[t]
        keep = carmap.load().value("open", pos, nrm) >= measure.OUTER
        if within is not None:
            keep &= within(pos, nrm) > 0.5
        keep &= ~_by_panels(self.skin, c, t)
        room[rr[keep], cc[keep]] = True
        k = max(1, int(round(SPAN / 2 / float(np.median(self.pitch[self.island[sel]])))))
        room &= ~_creased(c.bake["normal"][r0:r1, c0:c1], c.cov[r0:r1, c0:c1], k, np.cos(np.radians(fold)))
        return room, island


def _creased(nrm, cov, k, cos_fold):
    """The texels on a crease or a roll: the surface turns by more than the fold's angle between k
    texels to one side and k to the other, along a row or a column."""
    out = np.zeros(cov.shape, bool)
    if min(cov.shape) <= 2 * k:
        return out
    a, b, mid = slice(0, -2 * k), slice(2 * k, None), slice(k, -k)
    for one, two, at in (((a, slice(None)), (b, slice(None)), (mid, slice(None))),
                         ((slice(None), a), (slice(None), b), (slice(None), mid))):
        out[at] |= cov[one] & cov[two] & ((nrm[one] * nrm[two]).sum(-1) < cos_fold)
    return out


def _by_panels(skin, c, t):
    """Which of the texels t lie on a panel the game letters or the nose fin's plate, or within
    checks.CLEAR cm of one on its face of the body."""
    from tool import checks
    cov = coverage.load(skin.parts, "Skin", c.w, c.h)
    out = np.zeros(len(t), bool)
    p = c.pos[t]
    for i, inst in enumerate(skin.parts.instances):
        if inst["name"] not in checks.PANELS or i not in cov.sparse:
            continue
        panel = cov.sparse[i][0][cov.sparse[i][1] >= 128].astype(np.int64)
        if not len(panel):
            continue
        q = c.pos[panel]
        box = np.flatnonzero(((p >= q.min(0) - checks.CLEAR) & (p <= q.max(0) + checks.CLEAR)).all(1))
        if not len(box):
            continue
        thin = q[np.unique(np.floor(q / 0.3).astype(np.int64), axis=0, return_index=True)[1]]
        d = cKDTree(thin).query(p[box], distance_upper_bound=checks.CLEAR, workers=-1)[0]
        facing = c.nrm[panel].mean(0)
        out[box[(d <= checks.CLEAR) & (c.nrm[t[box]] @ (facing / np.linalg.norm(facing)) > 0.3)]] = True
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


def _unfold(c, texel, island, pitch):
    """How the texture unfolds the surface at a texel: (3, 2), the cm a step of one column and of one
    row move on the car, by least squares over its flat piece within 1.5 cm."""
    label = uvmap.islands("Skin")[0]
    k = max(6, int(round(1.5 / pitch)))
    r, col = divmod(texel, c.w)
    r0, r1, c0, c1 = max(r - k, 0), min(r + k + 1, c.h), max(col - k, 0), min(col + k + 1, c.w)
    dr, dc = np.mgrid[r0 - r:r1 - r, c0 - col:c1 - col]
    tri = c.bake["tri"][r0:r1, c0:c1]
    ok = (tri >= 0) & (label[np.maximum(tri, 0)] == island) & (dr * dr + dc * dc <= k * k)
    D = np.stack([dc[ok], dr[ok], np.ones(int(ok.sum()))], 1).astype(np.float64)
    P = c.bake["position"][r0:r1, c0:c1][ok].astype(np.float64)
    return np.linalg.lstsq(D, P, rcond=None)[0][:2].T


def _facing(panel, anchor, isl, A, radius, fold, within):
    """Where the free room within `radius` cm of a texel faces, on its flat piece: the mean of its
    normals; the texel's own where there is none. Words laid on it face this, not a lip's or a bolt's
    face under `at`."""
    c = panel.c
    pitch = float(panel.pitch[isl])
    look = int(np.ceil(radius / pitch)) + 2
    a_r, a_c = divmod(anchor, c.w)
    win, sel = panel.window(a_r - look, a_r + look + 1, a_c - look, a_c + look + 1)
    room, island = panel.room(win, sel, fold, within)
    room &= island == isl
    dr, dc = np.mgrid[win[0] - a_r:win[1] - a_r, win[2] - a_c:win[3] - a_c]
    d2 = ((A[:, 0][None, None, :] * dc[..., None] + A[:, 1][None, None, :] * dr[..., None]) ** 2).sum(-1)
    on = room & (d2 <= radius * radius)
    if not on.any():
        return c.nrm[anchor].astype(np.float64)
    n = c.bake["normal"][win[0]:win[1], win[2]:win[3]][on].astype(np.float64).mean(0)
    return n / np.linalg.norm(n)


def _pole(panel, fold, within, margin):
    """The named parts' roomiest spot: (its clear room in cm, the texel), the texel furthest from its
    room's edges; of those as far (within 2 %), the middle one of those on the car's middle, else of
    those on its left, else of the rest. None when the parts have no room."""
    c = panel.c
    best = None
    for isl in np.unique(panel.island):
        on = panel.island == isl
        win, sel = panel.window(panel.rows[on].min() - 2, panel.rows[on].max() + 3, panel.cols[on].min() - 2, panel.cols[on].max() + 3)
        room, _ = panel.room(win, sel & on, fold, within)
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
    """The named body parts' flat rooms, for car/anatomy.md: the biggest discs of free room on each part
    (as a mark's: off its creases and rolls, in the open air, clear of the game's panels) whose skin faces
    within WORD_BEND degrees of one way, `least` cm across or more, on the left side and the middle:
    {part: [(across in cm, centre, facing), ...]}, the roomiest first, at most `most`, each clear of the
    ones before. Measured on a `size`² texture."""
    from tool import paintbox
    skin = paintbox.Skin("TSC_Rooms", size=size)
    c = skin.canvas("Skin")
    ways = carmap.directions().astype(np.float32)
    flat = np.cos(np.radians(WORD_BEND))
    out = {}
    for name in names:
        panel = _Panel(skin, c, skin._ids(name, warn=False).get("Skin", []))
        if not len(panel.texels):
            continue
        win, sel = panel.window(panel.rows.min() - 2, panel.rows.max() + 3, panel.cols.min() - 2, panel.cols.max() + 3)
        room, island = panel.room(win, sel, FOLD, None)
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


def _fit(panel, shape, size, anchor, up, turn, margin, reach, fold, within, centred, least, soft, goal=None,
         bend=BEND, facing=None):
    """Lay a shape as near a texel as it's whole: {texel (its middle), size, moved, idx, m, rgb, right, up,
    facing}, or None with no room for it. size None: the biggest that fits with its middle there.
    goal: the texel its middle goes to, within a centimetre (a twin's: its mirror image's middle),
    while its room and its frame stay those of the anchor. bend: how far its room may face from its
    facing; facing: the anchor texel's (None), or "room": the free room's round it (_facing). up:
    where its top points, or "outward" (_outward)."""
    c = panel.c
    isl = int(panel.island[np.searchsorted(panel.texels, anchor)])
    pitch = float(panel.pitch[isl])
    a_r, a_c = divmod(anchor, c.w)
    A = _unfold(c, anchor, isl, pitch)
    n0 = c.nrm[anchor]
    if facing == "room":
        n0 = _facing(panel, anchor, isl, A, (size * shape.reach if size else 10.0) + reach + margin, fold, within)
    if isinstance(up, str):
        up = _outward(n0, c.pos[anchor])
    right, up, n = _frame(n0, up, turn)
    M = np.array([[right @ A[:, 0], right @ A[:, 1]], [up @ A[:, 0], up @ A[:, 1]]])  # (columns, rows) -> the shape's x, y in cm
    pitch = float(np.sqrt(abs(np.linalg.det(M))))
    span = int(np.ceil(SPAN / pitch)) + 4
    if size is None:  # twice the clear room round the texel, the most a shape as wide could take
        look = int(np.ceil(40 / pitch))
        win, sel = panel.window(a_r - look, a_r + look + 1, a_c - look, a_c + look + 1)
        room, island = panel.room(win, sel, fold, within)
        room &= (island == isl) & ((c.bake["normal"][win[0]:win[1], win[2]:win[3]] @ n.astype(np.float32)) >= np.cos(np.radians(bend)))
        edt = ndimage.distance_transform_edt(np.pad(room, 1))[1:-1, 1:-1]
        clear = float(edt[a_r - win[0], a_c - win[2]]) * pitch - margin
        if clear <= 0.5:
            return None
        size, reach, least = 2 * clear / shape.reach, 0.0, 0.25
    half = int(np.ceil((size * shape.reach + reach + margin) / pitch)) + span
    win, sel = panel.window(a_r - half, a_r + half + 1, a_c - half, a_c + half + 1)
    r0, r1, c0, c1 = win
    room, island = panel.room(win, sel, fold, within)
    room &= (island == isl) & ((c.bake["normal"][r0:r1, c0:c1] @ n.astype(np.float32)) >= np.cos(np.radians(bend)))
    room &= ndimage.distance_transform_edt(np.pad(room, 1))[1:-1, 1:-1] * pitch >= margin
    dr, dc = np.mgrid[r0 - a_r:r1 - a_r, c0 - a_c:c1 - a_c]
    far = (M[0, 0] * dc + M[0, 1] * dr) ** 2 + (M[1, 0] * dc + M[1, 1] * dr) ** 2  # cm² from where it's wanted
    aim = far
    if goal is not None:
        gr, gc = dr - (goal // c.w - a_r), dc - (goal % c.w - a_c)
        aim = (M[0, 0] * gc + M[0, 1] * gr) ** 2 + (M[1, 0] * gc + M[1, 1] * gr) ** 2
    near = aim <= max(reach if goal is None else 1.0, 0.75 * pitch) ** 2
    if centred:
        near &= np.abs(c.bake["position"][r0:r1, c0:c1, 0]) <= max(0.3, 1.5 * pitch)
    wall = (~room).astype(np.float64)

    def foot(S, pad=0.0):
        """The kernel round a middle for the shape S wide: its points in the shape's units, k, and the
        rows and columns they are from the middle."""
        k = int(np.ceil((S * shape.reach + pad) / pitch)) + 1
        o = np.arange(-k, k + 1)
        kc, kr = np.meshgrid(o, o)
        return (M[0, 0] * kc + M[0, 1] * kr) / S, (M[1, 0] * kc + M[1, 1] * kr) / S, k, kr, kc

    def whole(S):  # the middles at which the shape, S wide, covers no texel outside the room
        x, y, k, _, _ = foot(S)
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
    jr, jc = divmod(j, room.shape[1])
    S = size * s
    x, y, k, kr, kc = foot(S, soft)
    rows, cols = r0 + jr + kr, c0 + jc + kc
    w, rgb = shape.paint(x, y, S, pitch, soft)
    on = (w > 0.002) & (rows >= 0) & (rows < c.h) & (cols >= 0) & (cols < c.w)
    texels, w = (rows[on] * c.w + cols[on]).astype(np.int64), w[on].astype(np.float32)
    idx, m = panel.mask()
    at = np.minimum(np.searchsorted(idx, texels), len(idx) - 1)
    mine = idx[at] == texels
    centre = (r0 + jr) * c.w + c0 + jc
    return {"texel": centre, "size": S, "moved": float(np.sqrt(far.reshape(-1)[j])), "idx": texels[mine],
            "m": m[at[mine]] * w[mine], "rgb": None if rgb is None else rgb[on][mine], "right": right, "up": up, "facing": n,
            "flat": float((w > 0.5).sum()) * pitch * pitch}  # cm² it covers in the unfolding, for the cut check


def through(shape, size, centre, right, up, facing, soft=shapes.SOFT):
    """A shape laid at a place as it is, over every edge in its footprint: a zone, on the surface that
    faces the same way within half its width in depth."""
    centre, right, up, facing = (np.asarray(v, np.float32) for v in (centre, right, up, facing))

    def f(p, n):
        rel = p - centre
        on = (np.abs(rel @ facing) < size / 2) & (n @ facing > 0.3)
        return np.where(on, shape.sd(rel @ right / size, rel @ up / size) * size, -1.0)
    z = shapes.field(f, soft)
    z.label = f"{shape!r} at ({', '.join(f'{v:.0f}' for v in centre)})"
    return z


# ---- Skin.mark, Skin.text, Skin.placard, Skin.decal ----

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


def _frame_at(skin, c, panel, at, up, turn):
    """A frame on the panel's texel nearest `at`: (the point on the car, right, up, facing)."""
    texel, _ = panel.nearest(at)
    n0 = c.nrm[texel]
    if isinstance(up, str):
        up = _outward(n0, c.pos[texel])
    right, upv, n = _frame(n0, up, turn)
    return c.pos[texel].astype(np.float64), right, upv, n


def project(skin, shape, where, at, up, turn, size, finish, within, min_facing=0.3):
    """A picture laid at `at` as it is, projected onto the nearest surface facing it: it crosses every
    edge in its footprint (a sticker over a panel gap, as on a real car) and never reaches the far
    side of the car or anything behind a panel. Said in a note: what fell in a gap or off an edge,
    and a fold or a step under it. Returns where it landed (Laid)."""
    from tool import finishes, paint
    name = skin.ops[skin._op]["what"]
    if at is None or size is None:
        raise ValueError("a picture laid across the panels needs `at` and its width")
    at, _ = _stroke(at, size, None)
    c = skin.canvas("Skin")
    panel = _Panel(skin, c, skin._ids(where, warn=False).get("Skin", []))
    if not len(panel.texels):
        skin.notes.append(f"{name}: pictures go on the body; nothing laid")
        return Laid([v or 0 for v in at])
    centre, right, upv, n = _frame_at(skin, c, panel, at, up, turn)
    centre = np.array([c if v is None else v for v, c in zip(at, centre)], np.float64)
    pre = shape.image * shape.image[..., 3:4]
    alpha, info = paint.project_near(c.bake, shape.image[..., 3], centre, right, upv, size, n, min_facing)
    idx = np.flatnonzero(alpha.reshape(-1) > 0.002)
    if info["landed"] < 0.97:
        skin.notes.append(f"{name}: {info['landed']:.0%} of it landed on the car; the rest falls in a gap or off an edge")
    if info["step_cm"] > 4:
        skin.notes.append(f"{name}: the surface under it has a fold or a step of {info['step_cm']:.0f} cm; it will look cut there")
    if not len(idx):
        skin.notes.append(f"{name}: nothing landed on the car")
        return Laid(centre)
    m = alpha.reshape(-1)[idx]
    if within is not None:
        m = m * within(c.pos[idx], c.nrm[idx])
    if skin.measure:
        on = idx[m > 0.5]
        skin.pictures.append({"op": skin._op, "step": skin.ops[skin._op]["step"], "what": name, "idx": on,
                              "under": c.owner[on].copy(), "pixels": shape.iw / size, "across": True})
    fin = finishes.get(finish) if isinstance(finish, str) else finish
    rgb = np.stack([paint.project_near(c.bake, pre[..., k], centre, right, upv, size, n, min_facing)[0].reshape(-1)[idx]
                    for k in range(3)], 1) / np.maximum(m, 1e-6)[:, None]
    c.blend(idx, m, np.clip(rgb, 0, 1), np.full(len(idx), fin.roughness, np.float32),
            np.full(len(idx), fin.metalness, np.float32), np.full(len(idx), fin.varnish, np.float32))
    return Laid(centre, size, 0.0, right, upv, n)


def lay(skin, where, what, shape, size, at, colour, finish, up, turn, margin, reach, fold, within, mirror, across, soft, params):
    if not isinstance(shape, Shape):
        raise TypeError("a mark's shape is one of tool/marks.py's: marks.disc(), marks.star(5), marks.polygon([...])")
    from tool import finishes
    name = skin.ops[skin._op]["what"]
    flip = np.array([-1.0, 1.0, 1.0])
    picture = isinstance(shape, Picture)
    if across and picture:
        return project(skin, shape, where, at, up, turn, size, finish, within)
    if across:
        if at is None or size is None:
            raise ValueError("a mark laid across the panels needs `at` and `size`")
        c = skin.canvas("Skin")
        panel = _Panel(skin, c, skin._ids(where, warn=False).get("Skin", []))
        if not len(panel.texels):
            skin.notes.append(f"{name}: marks go on the body; nothing laid")
            return Laid([v or 0 for v in at])
        texel, _ = panel.nearest(at)
        centre = c.pos[texel].astype(np.float64)
        right, upv, n = _frame(c.nrm[texel], up, turn)
        zone = through(shape, size, centre, right, upv, n, soft)
        laid = Laid(centre, size, 0.0, right, upv, n)
        if mirror and abs(centre[0]) > MIDDLE:
            r2, u2, n2 = _frame(n * flip, None if up is None else np.asarray(up, np.float64) * flip, -turn)
            zone = zone | through(shape.mirrored(), size, centre * flip, r2, u2, n2, soft)
            laid.twin = Laid(centre * flip, size, 0.0, r2, u2, n2)
        skin.paint(where, what, colour, finish, zone=zone, across=True, **params)
        return laid
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
    if not len(panel.texels):
        skin.notes.append(f"{name}: {'pictures' if picture else 'marks'} go on the body; nothing laid")
    if hasattr(at, "pts") and up is None:  # at a course: reading along it
        up = at.up_at(at.middle)
    at, reach = _stroke(at, size, reach)
    nowhere = Laid([v or 0 for v in at] if at is not None else (0, 0, 0))
    if not len(panel.texels):
        return nowhere
    fold = FOLD if fold is None else fold
    bend = WORD_BEND if shape.handed else BEND
    facing = "room" if picture else None
    if at is None:
        pole = _pole(panel, fold, within, margin)
        if pole is None:
            skin.notes.append(f"{name}: no free room on {_where(panel)} (the game letters it, or it's hidden); nothing laid")
            return nowhere
        anchor, off = pole[1], 0.0
    else:
        anchor, off = panel.nearest(at)
        if off > OFF:
            skin.notes.append(f"{name}: `at` is {off:.0f} cm off {_where(panel)}; laid at the nearest place on it")
    wanted = c.pos[anchor].astype(np.float64)
    centred = abs(wanted[0]) <= MIDDLE
    move = (size / 2 if size is not None else 0.0) if reach is None else reach
    if up is None and shape.handed:
        up = "outward"

    def put(got, shown):
        """Paint a fitted mark, and keep what the checks read."""
        idx, m, rgb = got["idx"], got["m"], got["rgb"]
        if skin.measure:
            on = np.sort(idx[m > 0.5])
            skin.marks.append({"op": skin._op, "step": skin.ops[skin._op]["step"], "what": name, "idx": on,
                               "under": c.owner[on].copy(), "kind": shape.kind,
                               # a picture's whole is what its texels cover flat: its ink thins where a stroke is a texel wide
                               "whole": got["flat"] if picture else shown.area() * got["size"] ** 2,
                               "text": shape.text, "pixels": shape.iw / got["size"] if picture else None, "frame": (got["right"], got["up"], got["facing"])})
        if rgb is None:
            skin._lay(c, "Skin", idx, m, fin, col, params, where)
        else:
            c.blend(idx, m, np.clip(rgb, 0, 1), np.full(len(idx), fin.roughness, np.float32),
                    np.full(len(idx), fin.metalness, np.float32), np.full(len(idx), fin.varnish, np.float32))
        return Laid(c.pos[got["texel"]], got["size"], got["moved"], got["right"], got["up"], got["facing"])

    got = _fit(panel, shape, size, anchor, up, turn, margin, move, fold, within, centred, LEAST, soft, bend=bend, facing=facing)
    if got is None:
        skin.notes.append(f"{name}: no room for it on {_where(panel)} at ({', '.join(f'{v:.0f}' for v in wanted)})"
                          + (f", even at {LEAST:.0%} of its {shape.said(size)}" if size is not None else "") + "; nothing laid")
        return nowhere
    laid = put(got, shape)
    said = []
    if at is None or size is None:
        said.append(f"laid at ({', '.join(f'{v:.0f}' for v in laid.centre)}), {shape.said(laid.size)}")
    if at is not None and laid.moved >= 0.5:
        said.append(f"moved {laid.moved:.1f} cm")
    if size is not None and laid.size < 0.99 * size:
        said.append(f"shrunk to {shape.said(laid.size)} ({laid.size / size:.0%} of its {shape.said(size).split(' cm')[0]})")
    if said:
        skin.notes.append(f"{name}: {', '.join(said)}" + (f", to stay whole on {_where(panel)}" if len(said) > (at is None or size is None) else ""))
    if mirror and abs(laid.centre[0]) > MIDDLE:
        other, off = panel.nearest(wanted * flip)
        goal, off2 = panel.nearest(np.asarray(laid.centre) * flip)
        if max(off, off2) <= 2.0:  # the named parts are on the other side too
            twin_shape = shape if shape.handed else shape.mirrored()
            up2 = up if up is None or isinstance(up, str) else np.asarray(up, np.float64) * flip
            twin = _fit(panel, twin_shape, laid.size, other, up2, -turn, margin, laid.moved + 1.5, fold, within, False,
                        0.99, soft, goal, bend=bend, facing=facing)
            if twin is None:
                twin = _fit(panel, twin_shape, laid.size, other, up2, -turn, margin, move, fold, within, False, LEAST, soft,
                            bend=bend, facing=facing)
                if twin is not None:
                    skin.notes.append(f"{name}: its twin on the other side doesn't fit as its mirror image: laid "
                                      f"{shape.said(twin['size'])}, {twin['moved']:.1f} cm from where it was wanted")
            if twin is None:
                skin.notes.append(f"{name}: no room for its twin on the other side; laid on one side only")
            else:
                laid.twin = put(twin, twin_shape)
                if abs(laid.centre[0]) < laid.size * shape.reach:
                    skin.notes.append(f"{name}: it reaches the car's middle, where its twin meets it (mirror=False for one, "
                                      f"or x = 0 in `at` for one on the middle)")
    return laid
