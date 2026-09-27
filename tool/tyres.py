"""Tyre markings: a library of looks for the tyres (TY-01 ...), drawn on the tyres' own map.

    s.tyre_marks("TY-01")                             a marking from the library, by code or name
    s.tyre_marks("ring soft", colour="lime", words=("OXIDE", "BOX BOX"), tread="TR-02")
    s.tyre_tread("TR-04")                             a tread from the tread library on its own
    python -m tool.tyres                              every marking on the car -> build/tyres/
    python -m tool.tyres TY-01 TY-30                  just those

How the tyres' map wraps the wheel (measured from the mesh, 2026-09-27):
  - Wheels, 1024x2048 as shipped (the stock is 512x1024). Its columns go across the tyre: the
    inner bead (u 0, 29.8 cm from the axle), the inner sidewall, the tread (u 0.2 to 0.83, 35.6 to
    36.4 cm), the outer sidewall, the outer bead (u 1). Its rows go once round: row 0 is 10 o'clock
    seen from the car's left, and the angle runs anticlockwise (seen from there) as the row grows.
  - All four tyres wear the same texels (the rear ones 10 % wider, with the same radii), and the
    right-hand ones are the left ones' mirror image. A skin can't change that: only a "3D skin"
    (a whole new car model) could, and Nadeo stopped those being shared in May 2024 (they show on
    the one PC that installed them, and crash consoles).
  - What shows: the wheel covers hide the sidewall inside 30.2 cm, the game's own shading
    (the stock Wheels_AO, which a skin can't replace) darkens three patches inside 31 cm, and
    the tread starts at 35.6. So a marking lives in BAND, 30.9 to 35.3 cm: `s` 0 to 1 across it.

So a marking is drawn as seen on the car's left, where it reads as drawn (both left tyres' outer
faces, and the right tyres' inner ones); on the right it shows mirrored. Rings, stripes, dots,
chequers and stars don't mind, and arrows round the wheel still point the way it rolls. Words read
backwards there, unless every letter looks the same upside down (FLIPPROOF: B C D E H I K O X,
0 3 8, - + = < > |): the mirror image of such a word is the same word half a turn on, with its
letters' tops toward the hub. The library's words are all flip-proof, drawn upright (a slanted
letter upside down leans the other way) and made exactly symmetric top to bottom. Any other word
works too, reading right on the side `reads` names; the paint box says so.

Relief (raised letters, grooves) goes in the tyres' normal map, Wheels_N, over Nadeo's own with
the sidewalls' lettering and the tread's grooves taken off where a marking needs it.
"""

import argparse
import functools
import math

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from tool import bake, colours, fbx, finishes, fonts, paths
from tool.shapes import WHEEL_Y, WHEEL_Z

W, H = 1024, 2048  # the tyres' map as shipped
SS_A, SS_R = 4, 2  # samples per texel round the tyre and across it
BAND = (30.9, 35.3)  # cm from the axle: where a marking shows on the sidewall (see above)
TREAD_R = 35.6  # the tread starts here
PPC = 60  # px per cm for lettering and symbols: finer than the texels (about 10 per cm round the tyre)
FLIPPROOF = frozenset("BCDEHIKOX038-+=<>| ")
# the shines a marking uses: roughness, metalness (any finish's name works too)
SHINE = {"rubber": (0.9, 0.0), "paint": (0.55, 0.0), "gloss": (0.3, 0.0), "shine": (0.32, 0.0),
         "matte": (0.95, 0.0), "metal": (0.3, 1.0), "chrome": (0.06, 1.0)}
RUBBER = "#161616"


def rad(s):
    """The distance from the axle (cm) of a point `s` across BAND (0 its inner edge, 1 its outer)."""
    return BAND[0] + s * (BAND[1] - BAND[0])


def around(n, start=0.0):
    """n clock angles evenly round the wheel, from `start` (degrees clockwise from 12 o'clock)."""
    return [start + k * 360.0 / n for k in range(n)]


def flipproof(text):
    return set(text.upper()) <= FLIPPROOF


@functools.lru_cache(maxsize=2)
def geometry(w=W, h=H):
    """Where the map's rows and columns sit on the tyre. Per row: the clock angle (degrees clockwise
    from 12 o'clock, seen from the car's left; unwrapped, so it falls as the row grows). Per column:
    the distance from the axle and across the tyre (cm, + to its outside, on the front tyre's scale),
    and the columns of each face."""
    p = fbx.meshes()["Wheels_01"]["positions"]
    front = p[:, 2] > 30
    ax = np.abs(p[:, 0])
    plane = {k: ((ax[s].min() + ax[s].max()) / 2, (ax[s].max() - ax[s].min()) / 2) for k, s in ((True, front), (False, ~front))}
    pos = bake.bake("Wheels", w, h)["position"]
    fr = pos[..., 2] > 30
    dy, dz = pos[..., 1] - WHEEL_Y, pos[..., 2] - np.where(fr, WHEEL_Z[0], WHEEL_Z[1])
    r = np.median(np.hypot(dy, dz), 0)
    mid = np.where(fr, plane[True][0], plane[False][0])
    half = np.where(fr, plane[True][1], plane[False][1])
    across = np.median((np.abs(pos[..., 0]) - mid) / half, 0) * plane[True][1]
    clock = np.degrees(np.unwrap(np.arctan2(-dz[:, w // 2], dy[:, w // 2])))
    cols = np.arange(w)
    step = np.hypot(np.gradient(r), np.gradient(across))  # cm per column along the surface
    return {"clock": clock, "r": r, "across": across, "step": step, "w": w, "h": h,
            "outer": cols[(across > 0) & (r < TREAD_R)], "inner": cols[(across < 0) & (r < TREAD_R)],
            "tread": cols[r >= TREAD_R]}


def _rows_clock(g, sub):
    """The clock angle at `sub` samples per row, (h * sub,)."""
    h = g["h"]
    at = (np.arange(h)[:, None] + (np.arange(sub) + 0.5) / sub - 0.5).ravel()
    idx = np.concatenate([[-1], np.arange(h), [h]])
    c = g["clock"]
    return np.interp(at, idx, np.concatenate([[c[-1] + 360], c, [c[0] - 360]]))


def _cols_value(g, cols, key, sub):
    at = (cols[:, None] + (np.arange(sub) + 0.5) / sub - 0.5).ravel()
    return np.interp(at, np.arange(g["w"]), g[key])


def _finish(finish):
    if isinstance(finish, (tuple, list)):
        return float(finish[0]), float(finish[1])
    if finish in SHINE:
        return SHINE[finish]
    f = finishes.get(finish)
    return f.roughness, f.metalness


def _colour(c):
    return np.asarray(colours.get(c), np.float32)


def _edge(x, lo, hi, aa):
    """0..1: inside [lo, hi], anti-aliased over `aa`."""
    return np.clip(np.minimum(x - lo, hi - x) / aa + 0.5, 0, 1).astype(np.float32)


def _arcs(a, arcs, aa):
    """0..1 per clock angle: inside any of the arcs (start, end), each clockwise from start."""
    cov = np.zeros(len(a), np.float32)
    for a0, a1 in arcs:
        span = (a1 - a0) % 360 or 360
        t = (a - a0) % 360
        d = np.where(t <= span, np.minimum(t, span - t), -np.minimum(t - span, 360 - t))
        cov = np.maximum(cov, np.clip(d / aa + 0.5, 0, 1))
    return cov


class _Grid:
    """One face of the tyre (or its tread), sampled finer than the texels: premultiplied paint
    over whatever is under it, a height (cm, for relief) and how deep in a groove (0..1)."""

    def __init__(self, clock, x, mirrored=False):
        self.a = -clock if mirrored else clock  # drawn as seen from the right: the left's mirror
        self.x = x.astype(np.float32)
        self.mirrored = mirrored
        self.da = float(np.abs(np.diff(clock[:2]))[0])  # degrees between samples round the tyre
        self.dx = float(np.median(np.abs(np.diff(x)))) or 0.02
        n = (len(clock), len(x))
        self.rgb = np.zeros(n + (3,), np.float32)
        self.alpha = np.zeros(n, np.float32)
        self.rough = np.zeros(n, np.float32)
        self.metal = np.zeros(n, np.float32)
        self.height = np.zeros(n, np.float32)
        self.groove = np.zeros(n, np.float32)

    def rows_near(self, a0, half):
        """The rows within `half` degrees of clock angle a0, and their signed angle from it."""
        d = (self.a - a0 + 180) % 360 - 180
        rows = np.flatnonzero(np.abs(d) < half)
        return rows, d[rows]

    def paint(self, rows, cov, rgb, rough, metal):
        k = cov[..., None]
        self.rgb[rows] = np.asarray(rgb, np.float32) * k + self.rgb[rows] * (1 - k)
        self.alpha[rows] = cov + self.alpha[rows] * (1 - cov)
        self.rough[rows] = rough * cov + self.rough[rows] * (1 - cov)
        self.metal[rows] = metal * cov + self.metal[rows] * (1 - cov)

    def lift(self, rows, cov, height):
        self.height[rows] = height * cov + self.height[rows] * (1 - cov)

    def texels(self, sub_a, sub_x):
        """Averaged back to texels: (colour, alpha, rough, metal, height, groove), each (h, cols[, 3])."""
        A, C = self.alpha.shape
        m = lambda v: v.reshape(A // sub_a, sub_a, C // sub_x, sub_x, *v.shape[2:]).mean((1, 3))
        alpha = m(self.alpha)
        safe = np.maximum(alpha, 1e-6)
        return (m(self.rgb) / safe[..., None], alpha, m(self.rough) / safe, m(self.metal) / safe,
                m(self.height), m(self.groove))


# ---- lettering and symbols, as masks in cm (PPC px per cm), centred on the image ----


def word_mask(text, height, font="russo", weight=None, spacing=0.0, outline=0.0):
    """A word as a fill mask and an outline mask (float 0..1, same size), its cap height `height` cm
    tall, centred on its cap line's middle. A flip-proof word is made exactly symmetric top to
    bottom (its bottom half mirrored up), so that upside down it is the same word."""
    cap = max(int(round(height * PPC)), 4)
    f = fonts.font(font, cap * 2, weight)
    hb = f.getbbox("H")
    f = fonts.font(font, int(cap * 2 * cap / max(hb[3] - hb[1], 1)), weight)
    hb = f.getbbox("H")
    sp = spacing * PPC
    widths = [f.getlength(ch) for ch in text]
    tw = int(math.ceil(sum(widths) + sp * max(len(text) - 1, 0)))
    ol = int(math.ceil(outline * height * PPC))
    pad = cap // 3 + ol + 2
    img = Image.new("L", (tw + 2 * pad, cap + 2 * pad), 0)
    d = ImageDraw.Draw(img)
    x = pad
    for ch, wch in zip(text, widths):
        d.text((x, pad - hb[1]), ch, fill=255, font=f)
        x += wch + sp
    fill = np.asarray(img, np.float32) / 255
    if flipproof(text):  # the padding is the same above and below, so the cap line's middle is the image's
        half = fill.shape[0] // 2
        fill[:half] = fill[::-1][:half]
    ring = np.zeros_like(fill)
    if ol:
        dist = ndimage.distance_transform_edt(fill < 0.5)
        ring = np.clip(ol + 0.5 - dist, 0, 1).astype(np.float32)
    return fill, ring


def shape_mask(kind, size):
    """A symbol `size` cm across, pointing up (outward from the hub) unless it says otherwise: dot,
    ring, square, diamond, triangle, chevron, arrow (pointing along the reading direction), star,
    bolt, flag (a chequer), wing, plus, bar."""
    n = max(int(round(size * PPC)), 4)
    ss = 4
    im = Image.new("L", (n * ss, n * ss), 0)
    d = ImageDraw.Draw(im)
    N = n * ss
    P = lambda pts: [(x * N, (1 - y) * N) for x, y in pts]  # unit square, y up
    if kind == "dot":
        d.ellipse([0, 0, N - 1, N - 1], fill=255)
    elif kind == "ring":
        d.ellipse([0, 0, N - 1, N - 1], fill=255)
        d.ellipse([N * 0.22, N * 0.22, N * 0.78, N * 0.78], fill=0)
    elif kind == "square":
        d.rectangle([N * 0.1, N * 0.1, N * 0.9, N * 0.9], fill=255)
    elif kind == "diamond":
        d.polygon(P([(0.5, 0), (1, 0.5), (0.5, 1), (0, 0.5)]), fill=255)
    elif kind == "triangle":
        d.polygon(P([(0.05, 0.1), (0.95, 0.1), (0.5, 0.9)]), fill=255)
    elif kind == "chevron":
        d.polygon(P([(0, 0.15), (0.5, 0.65), (1, 0.15), (1, 0.45), (0.5, 0.95), (0, 0.45)]), fill=255)
    elif kind == "arrow":
        d.polygon(P([(0, 0.38), (0.55, 0.38), (0.55, 0.15), (1, 0.5), (0.55, 0.85), (0.55, 0.62), (0, 0.62)]), fill=255)
    elif kind == "star":
        pts = [(0.5 + 0.5 * math.sin(math.radians(k * 36)) * (1 if k % 2 == 0 else 0.42),
                0.47 + 0.5 * math.cos(math.radians(k * 36)) * (1 if k % 2 == 0 else 0.42)) for k in range(10)]
        d.polygon(P(pts), fill=255)
    elif kind == "bolt":
        d.polygon(P([(0.7, 1), (0.12, 0.42), (0.46, 0.42), (0.3, 0), (0.88, 0.6), (0.54, 0.6)]), fill=255)
    elif kind == "flag":
        for i in range(4):
            for j in range(4):
                if (i + j) % 2 == 0:
                    d.rectangle([i * N / 4, j * N / 4, (i + 1) * N / 4 - 1, (j + 1) * N / 4 - 1], fill=255)
    elif kind == "wing":  # a pair of swept wings either side of a round badge, twice as wide as tall
        for sgn in (-1, 1):
            X = lambda x: 0.5 + sgn * x
            d.polygon(P([(X(0.1), 0.62), (X(0.5), 0.7), (X(0.42), 0.6), (X(0.47), 0.58), (X(0.36), 0.5),
                         (X(0.41), 0.47), (X(0.28), 0.4), (X(0.1), 0.38)]), fill=255)
        d.ellipse([N * 0.37, N * 0.37, N * 0.63, N * 0.63], fill=255)
        d.ellipse([N * 0.43, N * 0.43, N * 0.57, N * 0.57], fill=0)
    elif kind == "plus":
        d.rectangle([N * 0.38, 0, N * 0.62, N - 1], fill=255)
        d.rectangle([0, N * 0.38, N - 1, N * 0.62], fill=255)
    elif kind == "bar":
        d.rectangle([0, N * 0.3, N - 1, N * 0.7], fill=255)
    else:
        raise KeyError(f"no symbol called {kind!r}")
    return np.asarray(im.resize((n, n), Image.LANCZOS), np.float32) / 255


def span(kind, what, o):
    """How long a piece of row() is along the sidewall, in cm: its ink, not its padding."""
    if kind == "text":
        m = word_mask(what.upper(), o["height"], o.get("font", "russo"), o.get("weight"), o.get("spacing", 0.0))[0]
    else:
        m = shape_mask(what, o["size"])
    ink = np.flatnonzero(m.max(0) > 0.1)
    return (ink[-1] - ink[0] + 1) / PPC if len(ink) else 0.0


def half_angle(text, height, s=0.5, font="russo", weight=None, spacing=0.0):
    """Half the angle a word covers round the wheel, in degrees."""
    return math.degrees(span("text", text, {"height": height, "font": font, "weight": weight, "spacing": spacing}) / 2 / rad(s))


def _sample(mask, px, py):
    return ndimage.map_coordinates(mask, [py, px], order=1, mode="constant", cval=0.0).astype(np.float32)


# ---- a marking being drawn ----


class Art:
    """A marking: calls on the sidewalls (seen from the car's left; `s` across BAND, angles
    clockwise from 12 o'clock) and on the tread (`t` cm across it from its middle, + to the
    outside). Replayed on each face of the tyre when it's laid on the map (apply)."""

    def __init__(self):
        self.side, self.tread_ops = [], []
        self.tread_kind = None  # a tread pattern replacing Nadeo's grooves (tread())
        self.words = []  # every word written, to check it's flip-proof
        self.notes = []

    # -- sidewalls --

    def band(self, s0, s1, colour, finish="paint", arcs=None, lift=0.0):
        """A ring round the sidewall from s0 to s1 (or arcs of it: [(start, end), ...] clockwise)."""
        r0, r1 = rad(s0), rad(s1)
        rgb, (ro, me) = _colour(colour), _finish(finish)

        def op(g):
            cr = _edge(g.x, r0, r1, g.dx)
            if arcs is None:
                rows, cov = slice(None), np.broadcast_to(cr, g.alpha.shape)
            else:
                ca = _arcs(g.a, arcs, g.da)
                rows = np.flatnonzero(ca > 0)
                cov = ca[rows, None] * cr[None]
            g.paint(rows, cov, rgb, ro, me)
            if lift:
                g.lift(rows, cov, lift)
        self.side.append(op)
        return self

    def run(self, s0, s1, colours_, finish="paint"):
        """A ring whose colour runs round the wheel through `colours_` and back to the first."""
        r0, r1 = rad(s0), rad(s1)
        cols = np.array([_colour(c) for c in colours_] + [_colour(colours_[0])])
        ro, me = _finish(finish)

        def op(g):
            t = (g.a % 360) / 360 * (len(cols) - 1)
            k = np.minimum(t.astype(int), len(cols) - 2)
            f = (t - k)[:, None]
            rgb = cols[k] * (1 - f) + cols[k + 1] * f
            cr = _edge(g.x, r0, r1, g.dx)
            g.paint(slice(None), np.broadcast_to(cr, g.alpha.shape), rgb[:, None, :], ro, me)
        self.side.append(op)
        return self

    def segments(self, s0, s1, colours_, n, finish="paint", gap=0.0):
        """A ring cut into n pieces round the wheel, in turn in each colour; gap: degrees between."""
        step = 360 / n
        for k in range(n):
            self.band(s0, s1, colours_[k % len(colours_)], finish, arcs=[(k * step + gap / 2, (k + 1) * step - gap / 2)])
        return self

    def checks(self, s0, s1, n, rows=2, colours_=("#f4f4f2", "#0a0a0c"), finish="paint"):
        """A chequered band: n squares round the wheel, `rows` across."""
        r0, r1 = rad(s0), rad(s1)
        c = [_colour(v) for v in colours_]
        ro, me = _finish(finish)

        def op(g):
            i = np.floor((g.a % 360) / 360 * n).astype(int)
            j = np.clip(np.floor((g.x - r0) / (r1 - r0) * rows).astype(int), 0, rows - 1)
            odd = (i[:, None] + j[None]) % 2 == 1
            rgb = np.where(odd[..., None], c[1], c[0])
            cr = _edge(g.x, r0, r1, g.dx)
            g.paint(slice(None), np.broadcast_to(cr, g.alpha.shape), rgb, ro, me)
        self.side.append(op)
        return self

    def rays(self, s0, s1, n, width, colour, finish="paint", slant=0.0):
        """n stripes across the band, each `width` degrees wide, leaning `slant` degrees from s0 to s1."""
        r0, r1 = rad(s0), rad(s1)
        rgb, (ro, me) = _colour(colour), _finish(finish)

        def op(g):
            lean = slant * (g.x - r0) / (r1 - r0)  # (C,)
            t = ((g.a[:, None] - lean[None]) % (360 / n)) - width / 2
            cov = np.clip(np.minimum(t + width / 2, width / 2 - t) / g.da + 0.5, 0, 1) * _edge(g.x, r0, r1, g.dx)[None]
            cov = cov * (np.abs(t) <= width / 2 + g.da)
            g.paint(slice(None), cov.astype(np.float32), rgb, ro, me)
        self.side.append(op)
        return self

    def place(self, layers, size, s, at, inward=False, finish="paint", lift=0.0, rolling=False):
        """Lay masks along the sidewall, centred at `s` across the band and at each clock angle of
        `at`. layers: [(mask, colour)] drawn in order, all one size (w, h) in cm; up is outward
        (inward=True: toward the hub, so it reads upright at 6 o'clock). rolling: the mask's right
        points the way the wheel rolls (anticlockwise seen from the left) wherever it's seen."""
        w_cm, h_cm = size
        rm = rad(s)
        ro, me = _finish(finish)
        rgbs = [_colour(c) for _, c in layers]
        union = np.maximum.reduce([m for m, _ in layers])
        bump = ndimage.gaussian_filter(union, 0.05 * PPC) if lift else None  # a 0.5 mm bevel
        half = math.degrees((math.hypot(w_cm, h_cm) / 2 + 0.2) / (rm - h_cm / 2 - 0.2))

        def op(g):
            # the mask's right runs clockwise (seen as drawn); a rolling one's runs the way the
            # wheel rolls, anticlockwise seen from the left (the mirror of that seen from the right)
            sx = (-1.0 if rolling and not g.mirrored else 1.0) * (-1.0 if inward else 1.0)
            sy = -1.0 if inward else 1.0
            for a0 in at:
                rows, d = g.rows_near(a0, half)
                if not len(rows):
                    continue
                shape = (len(rows), len(g.x))
                px = np.broadcast_to(((np.radians(d) * rm * sx)[:, None] + w_cm / 2) * PPC - 0.5, shape)
                py = np.broadcast_to((h_cm / 2 - (g.x - rm)[None] * sy) * PPC - 0.5, shape)
                for (mask, _), rgb in zip(layers, rgbs):
                    cov = _sample(mask, px, py)
                    keep = cov.max(1) > 0
                    if keep.any():
                        g.paint(rows[keep], cov[keep], rgb, ro, me)
                if lift:
                    cov = _sample(bump, px, py)
                    keep = cov.max(1) > 0
                    g.lift(rows[keep], cov[keep], lift)
        self.side.append(op)
        return self

    def text(self, text, s, height, at, colour="white", font="russo", weight=None, spacing=0.0,
             outline=None, outline_width=0.12, inward=False, finish="paint", lift=0.0):
        """Words along the sidewall (see place()); height: the capitals' height in cm."""
        text = text.upper()
        self.words.append(text)
        fill, ring = word_mask(text, height, font, weight, spacing, outline_width if outline else 0.0)
        size = (fill.shape[1] / PPC, fill.shape[0] / PPC)
        layers = ([(ring, outline)] if outline else []) + [(fill, colour)]
        return self.place(layers, size, s, at, inward, finish, lift)

    def row(self, items, s, at, gap=0.5, inward=False):
        """Pieces side by side along the sidewall, centred together at each angle of `at`: items are
        ("text", words, {options}) or ("symbol", kind, {options}), each with its height or size;
        gap: cm between them."""
        rm = rad(s)
        widths = [span(kind, what, o) for kind, what, o in items]
        x = -(sum(widths) + gap * (len(items) - 1)) / 2
        for (kind, what, o), w in zip(items, widths):
            off = math.degrees((x + w / 2) / rm) * (-1 if inward else 1)
            angles = [a + off for a in at]
            o = dict(o)
            if kind == "text":
                self.text(what, s, o.pop("height"), angles, inward=inward, **o)
            else:
                self.symbol(what, s, o.pop("size"), angles, **o)
            x += w + gap
        return self

    def symbol(self, kind, s, size, at, colour="white", finish="paint", lift=0.0, turn=0, rolling=False, outline=None):
        """A symbol (shape_mask) at each angle of `at`; turn: quarter turns anticlockwise; outline:
        a colour for a border round it."""
        m = np.pad(np.rot90(shape_mask(kind, size), turn), 8)
        layers = [(m, colour)]
        if outline:
            dist = ndimage.distance_transform_edt(m < 0.5)
            layers = [(np.clip(0.12 * size * PPC + 0.5 - dist, 0, 1).astype(np.float32), outline), (m, colour)]
        return self.place(layers, (m.shape[1] / PPC, m.shape[0] / PPC), s, at, finish=finish, lift=lift, rolling=rolling)

    def wrinkles(self, s0, s1, n, depth=0.06):
        """Relief only: n soft ribs across the band (a drag slick's wrinkle wall)."""
        r0, r1 = rad(s0), rad(s1)

        def op(g):
            wave = 0.5 + 0.5 * np.cos(np.radians(g.a) * n)
            cov = np.broadcast_to(_edge(g.x, r0, r1, 0.3), g.alpha.shape)
            g.lift(slice(None), cov, (wave[:, None] * depth).astype(np.float32))
        self.side.append(op)
        return self

    # -- tread --

    def tread_paint(self, colour, finish="rubber", t0=None, t1=None, arcs=None):
        """Paint the tread, or a line round it from t0 to t1 cm across (+ outward)."""
        rgb, (ro, me) = _colour(colour), _finish(finish)

        def op(g):
            cx = np.ones(len(g.x), np.float32) if t0 is None else _edge(g.x, t0, t1, g.dx)
            if arcs is None:
                rows, cov = slice(None), np.broadcast_to(cx, g.alpha.shape)
            else:
                ca = _arcs(g.a, arcs, g.da)
                rows = np.flatnonzero(ca > 0)
                cov = ca[rows, None] * cx[None]
            g.paint(rows, cov, rgb, ro, me)
        self.tread_ops.append(op)
        return self

    def tread(self, name):
        """A tread from the tread library (TREAD_LIBRARY: "TR-04" or its name, "wet"), or one of
        TREADS by its key ("rain"), or "slick"."""
        key = str(name).strip().lower()
        if key in TREADS or key == "slick":
            return self.tread_grooves(key)
        tread_find(name)[1]["fn"](self)
        return self

    def tread_grooves(self, kind, colour=None, **p):
        """A tread pattern in place of Nadeo's (TREADS): its grooves as relief, and a little darker."""
        self.tread_kind = kind
        if kind == "slick":
            return self
        fn = TREADS[kind]

        def op(g):
            y = np.radians(g.a % 360) * 36.3  # cm round the tread
            depth = fn(y[:, None], g.x[None], **p)  # 0 on top .. 1 at a groove's floor, (A, C)
            g.lift(slice(None), np.ones_like(depth), (-depth * p.get("deep", 0.25)).astype(np.float32))
            g.groove = np.maximum(g.groove, depth)
            if colour is not None:
                g.paint(slice(None), depth.astype(np.float32), _colour(colour), *SHINE["paint"])
        self.tread_ops.append(op)
        return self

    def studs(self, colour="#b8bcc2", spacing=4.0, size=0.45):
        """Metal studs over the tread (a snow tyre's)."""
        rgb, (ro, me) = _colour(colour), SHINE["metal"]

        def op(g):
            y = np.radians(g.a % 360) * 36.3
            yy = (y[:, None] % spacing) - spacing / 2
            row = np.floor(y / spacing).astype(int)[:, None]
            xx = ((g.x[None] + (row % 2) * spacing / 2) % spacing) - spacing / 2
            d = np.hypot(xx, yy)
            cov = np.clip((size / 2 - d) / 0.04 + 0.5, 0, 1).astype(np.float32)
            g.paint(slice(None), cov, rgb, ro, me)
            g.lift(slice(None), cov, 0.08)
        self.tread_ops.append(op)
        return self


# ---- tread patterns: depth 0 (the tread's top) .. 1 (a groove's floor), from y (cm round the
# tyre) and t (cm across it, + outward). Symmetric about the middle, so the right tyres (the left's
# mirror) show the same; a directional one points the way the wheel rolls on both sides. ----


def _groove(d, width, soft=0.08):
    """1 inside a groove `width` cm wide at distance d from its middle, with sloped walls."""
    return np.clip((width / 2 - np.abs(d)) / soft + 0.5, 0, 1)


def _t_grooved(y, t, positions=(-7.5, -2.5, 2.5, 7.5), width=1.2, **_):
    out = np.zeros(np.broadcast(y, t).shape, np.float32)
    for c in positions:
        out = np.maximum(out, _groove(t - c + 0 * y, width))
    return out


def _t_rain(y, t, pitch=11.0, width=0.75, sweep=0.45, **_):
    """Full wets: a groove round the middle and grooves sweeping back from it to the shoulders."""
    main = _groove(t + 0 * y, 1.1)
    v = (y + sweep * np.abs(t) ** 1.25) % pitch
    side = _groove(v - pitch / 2, width) * (np.abs(t) > 1.2)
    return np.maximum(main, side).astype(np.float32)


def _t_inter(y, t, pitch=6.0, width=0.45, sweep=0.35, **_):
    v = (y + sweep * np.abs(t) ** 1.2) % pitch
    side = _groove(v - pitch / 2, width) * (np.abs(t) > 3.0) * (np.abs(t) < 12.5)
    return np.maximum(side, _groove(np.abs(t) - 3.0 + 0 * y, 0.5)).astype(np.float32)


def _t_blocks(y, t, bw=3.2, bl=3.6, gap=0.9, **_):
    """Gravel: staggered blocks."""
    col = np.floor(t / bw + 0.5)
    yy = (y + (col % 2) * bl / 2) % bl
    tt = (t / bw + 0.5) % 1 * bw
    across = _groove(yy, gap) + _groove(yy - bl, gap)
    along = _groove(tt + 0 * yy, gap) + _groove(tt - bw + 0 * yy, gap)
    return np.maximum(across, along).clip(0, 1).astype(np.float32)


def _t_snow(y, t, **p):
    return _t_blocks(y, t, bw=2.4, bl=2.6, gap=0.7)


def _t_mud(y, t, pitch=7.0, **_):
    """Mud: chunky lugs in a V, deep gaps between."""
    v = (y + 0.55 * np.abs(t)) % pitch
    lug = _groove(v - pitch * 0.3, pitch * 0.45, 0.15)
    return (1 - lug).astype(np.float32)


def _t_asphalt(y, t, **_):
    """Rally asphalt: nearly slick, two grooves round it and a few short cuts."""
    ring = np.maximum(_groove(t - 5.5 + 0 * y, 0.9), _groove(t + 5.5 + 0 * y, 0.9))
    cut = _groove((y % 14.0) - 7.0, 0.5) * (np.abs(np.abs(t) - 9.5) < 2.5)
    return np.maximum(ring, cut).astype(np.float32)


def _t_ribs(y, t, n=7, width=0.55, span=12.0, **_):
    """Ribs round the tyre: a vintage or a skinny front tyre's."""
    out = np.zeros(np.broadcast(y, t).shape, np.float32)
    for k in range(n):
        out = np.maximum(out, _groove(t - (-span + 2 * span * (k + 0.5) / n) + 0 * y, width))
    return out


def _t_diamond(y, t, pitch=3.0, width=0.35, **_):
    """Diamonds: two sets of diagonal grooves (a 1920s balloon tyre's)."""
    a = _groove(((y + t) % pitch) - pitch / 2, width)
    b = _groove(((y - t) % pitch) - pitch / 2, width)
    return (np.maximum(a, b) * (np.abs(t) < 12.0)).astype(np.float32)


def _t_semislick(y, t, pitch=5.0, **_):
    """Drift: a slick middle, blocks at the shoulders and one channel round each side."""
    ring = np.maximum(_groove(t - 7.0 + 0 * y, 1.0), _groove(t + 7.0 + 0 * y, 1.0))
    cut = _groove((y % pitch) - pitch / 2, 0.8) * (np.abs(t) > 8.5)
    return np.maximum(ring, cut).astype(np.float32)


def _t_lugs(y, t, pitch=4.6, size=1.5, **_):
    """Round lugs standing proud (a monster-truck toy's)."""
    row = np.floor(y / pitch)
    yy = (y % pitch) - pitch / 2
    tt = ((t + (row % 2) * pitch / 2) % pitch) - pitch / 2
    return (1 - np.clip((size - np.hypot(yy, tt)) / 0.15 + 0.5, 0, 1)).astype(np.float32)


TREADS = {"grooved": _t_grooved, "rain": _t_rain, "inter": _t_inter, "gravel": _t_blocks, "snow": _t_snow,
          "mud": _t_mud, "asphalt": _t_asphalt, "ribs": _t_ribs, "diamond": _t_diamond, "semi-slick": _t_semislick,
          "lugs": _t_lugs}


def _tr(kind, studs=False, **p):
    def fn(t):
        if kind != "stock":
            t.tread_grooves(kind, **p)
        if studs:
            t.studs()
    fn.depth = 0 if kind in ("stock", "slick") else p.get("deep", 0.25)
    return fn


# The tread library: the Lab's "Treads" (tool/swatches.py), a tread on its own for s.tyre_tread(),
# or any marking's tread= ("ring soft" on "TR-02"). Codes as the finishes': never reorder or remove,
# a new one goes at the end.
TREAD_LIBRARY = [
    ("Nadeo's own", "the car's own tread, as it comes: grooves like a road tyre's", _tr("stock")),
    ("slick", "no grooves at all: a dry racing tyre (the game still shades faint lines where Nadeo's grooves were)", _tr("slick")),
    ("grooved", "four grooves round the tread: Formula 1's dry tyres from 1998 to 2008", _tr("grooved")),
    ("wet", "a deep wet tread: a groove round the middle and grooves swept back to the shoulders", _tr("rain")),
    ("intermediate", "a shallow wet tread: finer swept grooves, a slick middle", _tr("inter")),
    ("rally asphalt", "nearly slick: two grooves round it and a few short cuts", _tr("asphalt")),
    ("gravel blocks", "chunky staggered blocks, for loose ground", _tr("gravel")),
    ("snow studs", "narrow blocks and metal studs, for ice", _tr("snow", studs=True)),
    ("mud lugs", "big lugs in a V with deep gaps between", _tr("mud", deep=0.35)),
    ("semi-slick", "a slick middle, a channel each side and blocks at the shoulders: a drift tyre's", _tr("semi-slick")),
    ("ribbed", "ribs round the tread: a vintage or a skinny front tyre's", _tr("ribs")),
    ("vintage diamond", "diamonds of crossed grooves: a 1920s balloon tyre's", _tr("diamond")),
    ("round lugs", "round lugs standing proud: a toy monster truck's", _tr("lugs", deep=0.4)),
]


def tread_library():
    """{code: entry}: TR-01, TR-02, ..."""
    return {f"TR-{k:02d}": {"name": n, "about": a, "fn": fn} for k, (n, a, fn) in enumerate(TREAD_LIBRARY, 1)}


def tread_find(name):
    key = " ".join(str(name).strip().lower().replace("-", " ").split())
    for code, e in tread_library().items():
        if key in (code.lower().replace("-", " "), code.lower().replace("-", ""), e["name"].lower().replace("-", " ")):
            return code, e
    raise KeyError(f"no tread called {name!r}; see tool/tyres.py (TREAD_LIBRARY)")


# ---- laying a marking on the tyres' map ----


def _stock_normal(w, h):
    from tool.testskin import stock
    return stock("Wheels_N", (w, h)).reshape(-1, 2)


def _flatten_rows(values, cols, w, h):
    """Each of `cols` set to its median round the tyre: what's the same all round stays (the
    sidewall's profile), what isn't goes (Nadeo's lettering, the tread's grooves)."""
    v = values.reshape(h, w, *values.shape[1:])
    v[:, cols] = np.median(v[:, cols], axis=0, keepdims=True)
    return v.reshape(values.shape)


def apply(canvas, art, reads="left"):
    """Lay a marking (Art) on the paint box's Wheels canvas: its paint on the colour, roughness and
    metalness, its relief on the canvas's normal map (canvas.normal, made here from Nadeo's)."""
    g = geometry(canvas.w, canvas.h)
    w, h = canvas.w, canvas.h
    sides = np.concatenate([g["outer"], g["inner"]])
    # the sidewalls start plain: Nadeo's lettering and marks off, in colour and relief (once, so a
    # second marking lands on the first)
    if canvas.normal is None:
        canvas.normal = _stock_normal(w, h).astype(np.float32)
        for layer in (canvas.colour, canvas.rough, canvas.normal):
            _flatten_rows(layer, sides, w, h)
    if art.tread_kind:
        for layer in (canvas.colour, canvas.rough):
            _flatten_rows(layer, g["tread"], w, h)
        canvas.normal.reshape(h, w, 2)[:, g["tread"]] = 0.5
    canvas.touched.reshape(h, w)[:, np.concatenate([sides, g["tread"]])] = True
    height = np.zeros((h, w), np.float32)
    groove = np.zeros((h, w), np.float32)
    faces = [(g["outer"], art.side, "r", SS_A, SS_R), (g["inner"], art.side, "r", SS_A, SS_R),
             (g["tread"], art.tread_ops, "across", 2, 2)]
    for cols, ops, key, sa, sx in faces:
        if not ops:
            continue
        grid = _Grid(_rows_clock(g, sa), _cols_value(g, cols, key, sx), mirrored=(reads == "right" and key == "r"))
        for op in ops:
            op(grid)
        rgb, alpha, rough, metal, hh, gr = grid.texels(sa, sx)
        idx = (np.arange(h)[:, None] * w + cols[None]).ravel()
        a = alpha.ravel()
        canvas.blend(idx, a, rgb.reshape(-1, 3), rough.ravel(), metal.ravel())
        height[:, cols] = hh
        groove[:, cols] = gr
    if groove.any():  # a groove's floor a little darker (Nadeo's grooves are too)
        k = (1 - 0.35 * groove.ravel())[:, None]
        canvas.colour *= k
    if np.abs(height).max() > 1e-5:
        from tool import relief
        du = np.gradient(height, axis=1) / np.maximum(g["step"], 1e-3)[None]
        dv_cm = 2 * np.pi * g["r"] / h
        dv = (np.roll(height, 1, 0) - np.roll(height, -1, 0)) / 2 / dv_cm[None]  # +v is up the image
        slope = np.stack([du, dv], -1).reshape(-1, 2).astype(np.float32)
        ours = np.flatnonzero(np.abs(slope).max(1) > 1e-4)
        canvas.normal[ours] = relief.combine(canvas.normal[ours], relief.to_normal(slope[ours]))
    notes = list(art.notes)
    for word in dict.fromkeys(art.words):
        if not flipproof(word):
            notes.append(f"tyre lettering {word!r} reads backwards on the car's {'right' if reads == 'left' else 'left'}: "
                         "only B C D E H I K O X 0 3 8 read both ways")
    return notes


# ---- the library ----
# Layouts after real tyres (research, 2026-09-27: CHECKLIST.md, "Tyre markings"), rebuilt in our
# own words and shapes: no maker's name or logo. The words are all flip-proof: MAKER is the maker's
# name on every marking; the model's name changes with the family.

MAKER = "OXIDE"
RED, YELLOW, WHITE, GREEN, BLUE = "#e4002b", "#ffd100", "#f2f2f2", "#3dae2b", "#0072ce"
PINK, PURPLE, ICE, ORANGE, SILVER = "#f49ac1", "#7d2f8f", "#8fd8f8", "#f58025", "#a7aaad"
CREAM, GOLD, DARK = "#eeebe3", "#c9a04b", "#0a0a0c"
BIG = "arial black"  # heavy, wide capitals: the classic tyre maker's letters


def _ring(t, colour, words=(MAKER, "BOX BOX"), letters=None, arcs=True, heavy=False, low=False,
          chequer=False, brackets=False, tread=None):
    """Formula 1 since 2011: four wordmarks at 12, 3, 6 and 9 o'clock, the maker's and the model's in
    turn, in the compound's colour, and twin arcs between them, so the colour reads as a ring when
    the wheel turns."""
    letters = letters or colour
    caps = (2.8, 2.3) if low else (2.4, 2.0)
    for k, a in enumerate(around(4)):
        t.text(words[k % 2], 0.5, caps[k % 2], [a], colour=letters)
    if chequer:
        for a in (0, 180):
            t.symbol("flag", 0.5, 1.3, [a + half_angle(words[0], caps[0]) + 3.5], colour=WHITE)
    if arcs:
        spans = []
        for k, a in enumerate(around(4)):
            lo = a + half_angle(words[k % 2], caps[k % 2]) + (7 if chequer and k % 2 == 0 else 4)
            hi = a + 90 - half_angle(words[(k + 1) % 2], caps[(k + 1) % 2]) - 4
            spans.append((lo, hi))
        if low:
            t.band(-0.02, 0.14, colour, arcs=spans)
            t.band(0.86, 1.0, colour, arcs=spans)
        else:
            w = 0.15 if heavy else 0.1
            t.band(0.04, 0.04 + w, colour, arcs=spans)
            t.band(0.96 - w, 0.96, colour, arcs=spans)
        if brackets:
            for lo, hi in spans:
                t.band(0.04, 0.96, colour, arcs=[(lo, lo + 1.3), (hi - 1.3, hi)])
    if tread:
        t.tread(tread)


def _marks(t, colour, words=(MAKER, "CHECK"), cap=2.2, font="russo", model=True, s=0.5, lift=0.0,
           finish="paint", outline=None, tread=None):
    """The maker's wordmark at 12 and 6 o'clock and the model's at 3 and 9."""
    t.text(words[0], s, cap, [0, 180], colour=colour, font=font, lift=lift, finish=finish, outline=outline)
    if model and len(words) > 1:
        t.text(words[1], s, cap * 0.75, [90, 270], colour=colour, font=font, lift=lift, finish=finish, outline=outline)
    if tread:
        t.tread(tread)


def _grooved(t, colour=WHITE, words=(MAKER, "CHECK"), line=None, line_at=2.5):
    """1998 to 2008: grooved dries, white wordmarks; the softer one with a line in a groove."""
    _marks(t, colour, words, cap=2.0, font="arial bold")
    t.tread_grooves("grooved")
    if line:
        t.tread_paint(line, "paint", line_at - 0.5, line_at + 0.5)


def _wet_line(t, line, words=(MAKER, "CHECK")):
    _marks(t, WHITE, words, cap=2.0, font="arial bold")
    t.tread_grooves("rain")
    t.tread_paint(line, "paint", -0.45, 0.45)


def _winged(t, colour, words=("OXI", "DE", "EXCEED"), cap=2.3):
    """The classic American maker's layout: its name split by a winged emblem, twice round, and the
    model's name between."""
    t.row([("text", words[0], {"height": cap, "colour": colour, "font": BIG}),
           ("symbol", "wing", {"size": cap * 2.3, "colour": colour}),
           ("text", words[1], {"height": cap, "colour": colour, "font": BIG})], 0.5, [0, 180], gap=0.25)
    t.text(words[2], 0.5, cap * 0.7, [90, 270], colour=colour, font=BIG)


def _seventies(t, colour=WHITE, words=(MAKER,)):
    """1970s slicks: big plain white capitals, painted on, matte."""
    t.text(words[0], 0.52, 3.3, [0, 180], colour=colour, font="impact", finish="matte", spacing=0.14)
    t.tread_grooves("slick")


def _stripe(t, colour, s0, s1, words=(MAKER, "CODEX"), letters=WHITE, cap=1.8, s=0.36, tread=None):
    """A painted band round the sidewall, the wordmarks inside it."""
    t.band(s0, s1, colour)
    if words:
        _marks(t, letters, words, cap=cap, s=s)
    if tread:
        t.tread(tread)


def _stock(t, colour, words=(MAKER, "HEX 8"), tread=None):
    """American stock cars: bold wide capitals twice round, glossy paint."""
    _marks(t, colour, words, cap=2.6, font=BIG, finish="gloss")
    if tread:
        t.tread(tread)


def _sticker(t, words=(MAKER, "HEX 8")):
    """A new tyre with its data label still on: the wordmarks, and a white label with bars."""
    _stock(t, YELLOW, words)
    for a in (45, 225):  # the label: about 9 cm long, a barcode and a line of numbers
        t.band(0.04, 0.96, WHITE, "matte", arcs=[(a - 8, a + 8)])
        for k in range(26):
            x = a - 6.5 + k * 0.5
            t.band(0.34, 0.8, DARK, "matte", arcs=[(x, x + (0.3 if k % 3 else 0.14))])
        t.text("0308 3E", 0.18, 0.6, [a], colour=DARK, font="consolas bold")


def _junior(t, colour=RED, words=(MAKER, "C3")):
    """The feeder series' ring: smaller, with the series' tag."""
    for k, a in enumerate(around(4)):
        t.text(words[k % 2], 0.5, 1.9, [a], colour=colour)
    t.band(0.08, 0.2, colour, arcs=[(a + 20, a + 70) for a in around(4)])


def _electric(t, words=(MAKER, "E-CODE")):
    """An all-weather electric racer's: treaded, orange and blue graphics, orange in the grooves."""
    _marks(t, WHITE, words, cap=1.8, font="orbitron", s=0.5)
    for a in around(4, 45):
        t.band(0.08, 0.28, ORANGE, arcs=[(a - 22, a + 22)])
        t.band(0.72, 0.9, "#1e60ff", arcs=[(a - 16, a + 16)])
    t.tread_grooves("inter", colour=ORANGE)


def _endurance(t, colour, words=(MAKER, "ECHO"), tread=None):
    """Endurance prototypes since 2024: the maker's wordmark in the compound's colour, a tab of it
    either side, the model in white."""
    cap = 2.4
    t.text(words[0], 0.5, cap, [0, 180], colour=colour)
    t.text(words[1], 0.5, 1.8, [90, 270], colour=WHITE)
    h = half_angle(words[0], cap) + 3
    for a in (0, 180):
        t.band(0.18, 0.82, colour, arcs=[(a - h - 2.2, a - h), (a + h, a + h + 2.2)])
    if tread:
        t.tread(tread)


def _dot(t, colour=RED, words=(MAKER, "ECHO")):
    """Before 2024: a black tyre, white wordmarks, one small coloured dot."""
    _marks(t, WHITE, words, cap=2.0)
    h = half_angle(words[0], 2.0) + 3.5
    t.symbol("dot", 0.5, 1.4, [h, 180 + h], colour=colour)


def _moto(t, colour, words=(MAKER, "BIKE"), tread=None):
    """Bikes: a thin stripe round the edge, small white wordmarks."""
    t.band(0.86, 0.95, colour)
    _marks(t, WHITE, words, cap=1.8, s=0.42)
    if tread:
        t.tread(tread)


def _war(t, colour, words=(MAKER,), cap=3.3, bar=True):
    """A tyre war's loud wordmark, huge, twice round, with an accent bar under it."""
    t.text(words[0], 0.56, cap, [0, 180], colour=colour, font=BIG)
    if bar:
        h = half_angle(words[0], cap, 0.56, BIG)
        t.band(0.02, 0.1, colour, arcs=[(a - h, a + h) for a in (0, 180)])


def _rally(t, mark, tread, words=(MAKER, "HEX"), studs=False):
    """Rally: white wordmarks, a band in the surface's colour, the tread for it."""
    _marks(t, WHITE, words, cap=2.0, s=0.45)
    if mark:
        t.band(0.84, 0.96, mark, arcs=[(a + 22, a + 68) for a in around(4)])
    t.tread_grooves(tread, deep=0.35 if tread == "mud" else 0.25)
    if studs:
        t.studs()


def _drift(t, colour=WHITE, words=(MAKER,)):
    """Drift: big raised sticker letters top and bottom, a semi-slick tread."""
    t.text(words[0], 0.52, 3.1, [0, 180], colour=colour, font="russo", lift=0.08, spacing=0.12)
    t.tread_grooves("semi-slick")


def _smoke(t, colour="#ff2d95", words=(MAKER, "BOX BOX")):
    """Coloured-smoke drift tyres: neon lettering and a stripe (bright paint; tyres can't glow)."""
    _marks(t, colour, words, cap=2.2, font="russo")
    t.band(0.9, 0.98, colour)
    t.tread_grooves("semi-slick")


def _drag(t, colour=WHITE, words=(MAKER, "HD 38 X 08")):
    """Drag slicks: giant lettering, a line of small print under it, wrinkles near the rim."""
    t.text(words[0], 0.62, 3.2, [0, 180], colour=colour, font=BIG)
    t.text(words[1], 0.14, 0.7, [0, 180], colour=colour, font="arial bold")
    t.wrinkles(-0.1, 0.05, 90)
    t.tread_grooves("slick")


def _skinny(t, words=(MAKER, "DECK 3")):
    """A skinny front: thin lettering, a ribbed tread."""
    _marks(t, WHITE, words, cap=1.2, font="arial bold")
    t.tread_grooves("ribs", n=5, span=11.0)


def _kart(t, colour=YELLOW, words=(MAKER, "C3")):
    """Karting: the wordmark and a label box in the compound's colour."""
    t.text(words[0], 0.5, 2.2, [0, 180], colour=WHITE, font="bahnschrift")
    t.symbol("square", 0.5, 3.2, [90, 270], colour=colour)
    t.text(words[1], 0.5, 1.5, [90, 270], colour=DARK, font=BIG)


def _rwl(t, colour=WHITE, words=(MAKER, "CODEX 3"), outline=False, finish="rubber", stripe=None):
    """Raised letters, as on 1970s muscle cars: the maker's twice round, the model's between.
    outline: white outlines on black letters."""
    s = 0.62 if stripe else 0.5
    if outline:
        _marks(t, RUBBER, words, cap=1.9 if stripe else 2.3, font=BIG, s=s, lift=0.09, finish="rubber", outline=colour)
    else:
        _marks(t, colour, words, cap=1.9 if stripe else 2.3, font=BIG, s=s, lift=0.09, finish=finish)
    if stripe:
        t.band(0.1, 0.2, stripe)


def _stealth(t, words=(MAKER, "CODEX 3")):
    """Black on black: satin raised letters on matte rubber."""
    t.band(-0.2, 1.1, RUBBER, "matte")
    _marks(t, "#1f1f22", words, cap=2.3, font=BIG, lift=0.1, finish="satin")


def _whitewall(t, s0, s1, colour=CREAM, pin=None, tread=None):
    t.band(s0, s1, colour, "rubber")
    if pin:
        t.band(s1 + 0.04, s1 + 0.09, pin)
    if tread:
        t.tread(tread)


def _lines(t, bands, tread=None):
    for s0, s1, colour in bands:
        t.band(s0, s1, colour)
    if tread:
        t.tread(tread)


def _balloon(t, words=(MAKER, "DECO")):
    """A 1920s balloon tyre: cream sidewalls, raised serif letters, a diamond tread."""
    t.band(-0.3, 1.2, "#e6dcc3", "rubber")
    _marks(t, "#8a7a5c", words, cap=2.2, font="georgia bold", lift=0.09, finish="rubber")
    t.tread_grooves("diamond")


def _white_1910(t):
    """The first tyres were white all over: natural rubber, before carbon black."""
    t.band(-0.3, 1.2, "#e9e4d6", "rubber")
    t.tread_paint("#e2dccb", "rubber")
    t.tread_grooves("ribs", n=6, span=12.0)


def _shine(t):
    """Tyre shine: glossy black all over."""
    t.band(-0.3, 1.2, RUBBER, "shine")
    t.tread_paint(RUBBER, "shine")


def _info(t, words=(MAKER, "HD 308-38 X 08")):
    """What a road tyre's sidewall carries, moulded black on black: the name, the size, the date
    code in its oval, wear markers at the shoulder and arrows the way it rolls."""
    ink = "#1b1b1d"
    _marks(t, ink, words[:1], cap=2.2, font=BIG, lift=0.09, finish="rubber", model=False)
    t.text(words[1], 0.2, 0.55, [90, 270], colour=ink, font="arial bold", lift=0.06, finish="rubber")
    t.symbol("ring", 0.62, 1.4, [135, 315], colour=ink, finish="rubber", lift=0.06)
    t.text("3808", 0.62, 0.45, [135, 315], colour=ink, font="arial bold", lift=0.06, finish="rubber")
    t.symbol("triangle", 0.93, 0.6, around(6, 30), colour=ink, finish="rubber", lift=0.06)
    t.symbol("arrow", 0.45, 1.3, around(4, 45), colour=ink, finish="rubber", lift=0.06, rolling=True)


def _arrows(t, colour=YELLOW, words=(MAKER,)):
    """Arrows the way the wheel rolls, painted: they point forward on both sides of the car."""
    t.symbol("arrow", 0.5, 2.6, around(8, 22.5), colour=colour, rolling=True)
    t.text(words[0], 0.5, 2.0, around(4), colour=WHITE)


def _toy(t, colour="#ff2020"):
    """A toy car's tyre: glossy black plastic and a thin bright line near the rim."""
    t.band(-0.3, 1.2, "#101012", "gloss")
    t.tread_paint("#101012", "gloss")
    t.band(0.06, 0.15, colour, "gloss")
    t.tread_grooves("slick")


def _neon(t, colour="#12e6ff", words=(MAKER, "BOX BOX")):
    """Bright rings and lettering in one neon colour (bright paint: tyres can't glow)."""
    t.band(0.06, 0.16, colour)
    t.band(0.84, 0.94, colour)
    _marks(t, colour, words, cap=2.1, font="orbitron")


def _chequer(t, colours_=(WHITE, DARK)):
    t.checks(0.08, 0.92, 96, 2, colours_)


def _cyber(t, colour="#5b2a86", seam="#ff3df0"):
    """A coloured slick: the whole tyre in one colour, a bright seam round the tread's middle."""
    t.band(-0.3, 1.2, colour, "satin")
    t.tread_paint(colour, "satin")
    t.tread_paint(seam, "paint", -0.35, 0.35)
    t.band(0.9, 0.96, seam)
    t.tread_grooves("slick")


def _monster(t, colour="#ff6a13"):
    """A toy monster truck's: orange all over, round lugs."""
    t.band(-0.3, 1.2, colour, "satin")
    t.tread_paint(colour, "satin")
    t.tread_grooves("lugs", deep=0.4)


def _emblems(t, kind="star", colour=WHITE, n=8, size=3.9):
    t.symbol(kind, 0.5, size, around(n), colour=colour)


def _rainbow(t):
    cols = ["#e4002b", "#f58025", "#ffd100", "#3dae2b", "#12c8e6", "#1b3fbf", "#7d2f8f"]
    for k, c in enumerate(cols):
        t.band(0.04 + k * 0.13, 0.04 + (k + 1) * 0.13, c)


def _candy(t, colour="#e4002b", base=WHITE):
    t.band(0.06, 0.94, base)
    t.rays(0.06, 0.94, 30, 5.5, colour, slant=7.0)


def _colour_run(t, colours_=("#12c8e6", "#e0189a", "#f9d100")):
    """A ring whose colour runs round the wheel (the CMYK cars' cyan, magenta and yellow)."""
    t.run(0.3, 0.7, colours_)


def _whole(t, colour="#9b1b30", finish="satin"):
    """The whole tyre in one colour."""
    t.band(-0.3, 1.2, colour, finish)
    t.tread_paint(colour, finish)


def _tread_only(t, kind, **p):
    """Only the tread's pattern; the sidewalls plain."""
    t.tread_grooves(kind, **p)


def _catalogue():
    E = lambda name, family, about, fn, **d: {"name": name, "family": family, "about": about, "fn": fn, "defaults": d}
    F1, OLD, US, SEAT, END, BIKE, RALLY, DD, ROAD, FUN, TREAD = (
        "Formula 1", "Formula 1, before 2011", "American racing", "Other single-seaters", "Endurance",
        "Bikes and touring cars", "Rally", "Drift, drag and karts", "Road and show", "Fun", "Treads")
    return [
        # the Formula 1 ring
        E("ring soft", F1, "red ring: the soft of the three since 2019", _ring, colour=RED),
        E("ring medium", F1, "yellow ring", _ring, colour=YELLOW),
        E("ring hard", F1, "white ring", _ring, colour=WHITE),
        E("ring intermediate", F1, "green ring and the shallow wet tread", _ring, colour=GREEN, tread="inter"),
        E("ring wet", F1, "blue ring and the deep wet tread", _ring, colour=BLUE, tread="rain"),
        E("ring hypersoft", F1, "pink ring (2018)", _ring, colour=PINK),
        E("ring ultrasoft", F1, "purple ring (2016 to 2018)", _ring, colour=PURPLE),
        E("ring supersoft", F1, "red ring with heavier arcs (2011 to 2018)", _ring, colour=RED, heavy=True),
        E("ring ice", F1, "ice-blue ring: the hard of 2018", _ring, colour=ICE),
        E("ring superhard", F1, "orange ring (2018)", _ring, colour=ORANGE),
        E("ring silver", F1, "silver ring: the hard of 2011", _ring, colour=SILVER),
        E("ring orange wet", F1, "orange ring and the deep wet tread (2011)", _ring, colour=ORANGE, tread="rain"),
        E("letters only", F1, "red wordmarks, no arcs: the test tyres' look", _ring, colour=RED, arcs=False),
        E("ring brackets", F1, "red ring whose arcs end in short bars", _ring, colour=RED, brackets=True),
        E("low-profile ring", F1, "the 18-inch look since 2022: bigger letters, wider arcs", _ring, colour=RED, low=True),
        E("chequer ring", F1, "red ring with a small chequered flag by each maker's name", _ring, colour=RED, chequer=True),
        # before the ring
        E("grooved dry", OLD, "four grooves round the tread, white wordmarks (1998 to 2008)", _grooved),
        E("grooved option", OLD, "the same, with a white line painted in a groove: the softer one", _grooved, line=WHITE),
        E("extreme wet line", OLD, "the deep wet tread with a white line round its middle", _wet_line, line=WHITE),
        E("green wet line", OLD, "the deep wet tread with a green line round its middle", _wet_line, line=GREEN),
        E("green edge slick", OLD, "a slick with a green band at the sidewall's edge (2009 to 2010)", _stripe,
          colour=GREEN, s0=0.84, s1=0.95, words=(MAKER, "CHECK"), cap=2.0, s=0.45, tread="slick"),
        E("classic white", OLD, "the 1980s American maker's look: its name split by a winged emblem", _winged, colour=WHITE),
        E("classic yellow", OLD, "the same in yellow, as from 1993", _winged, colour="#ffd200"),
        E("seventies slick", OLD, "big plain white painted capitals on a slick", _seventies),
        # America
        E("indy primary", US, "black, white wordmarks", _marks, colour=WHITE, words=(MAKER, "CODEX"), cap=2.2, font=BIG),
        E("indy alternate", US, "a red band round the sidewall: the softer one, seen from the stands", _stripe,
          colour="#d2232a", s0=0.66, s1=0.9),
        E("indy green", US, "a green band: the tyre made from plants", _stripe, colour="#2e9e3e", s0=0.66, s1=0.9),
        E("indy rain", US, "grey wordmarks and deep grooves", _marks, colour="#9a9ca0", words=(MAKER, "CODEX"), cap=2.2,
          font=BIG, tread="rain"),
        E("stock car yellow", US, "bold yellow capitals, glossy, twice round", _stock, colour="#ffd200"),
        E("stock car red", US, "the same in red: the option tyre", _stock, colour="#d0121b"),
        E("stock car wet", US, "white capitals and a treaded wet tyre", _stock, colour=WHITE, tread="inter"),
        E("sticker tyre", US, "yellow capitals and the white data label a new tyre still carries", _sticker),
        # other single-seaters
        E("junior ring", SEAT, "a smaller ring and the series' tag", _junior),
        E("electric all-weather", SEAT, "treaded, orange and blue graphics, orange in the grooves", _electric),
        # endurance
        E("endurance soft", END, "white wordmark with a tab either side", _endurance, colour=WHITE),
        E("endurance medium", END, "yellow wordmark and tabs", _endurance, colour=YELLOW),
        E("endurance hard", END, "red wordmark and tabs: red is the hard one here", _endurance, colour=RED),
        E("endurance wet", END, "light-blue wordmark and tabs, a wet tread", _endurance, colour="#6cc4ee", tread="rain"),
        E("endurance dot", END, "black tyre, white wordmarks, one small red dot", _dot),
        E("prototype yellow", END, "yellow wordmarks: the dry tyre", _marks, colour=YELLOW, words=(MAKER, "ECHO"), cap=2.3),
        E("prototype blue", END, "blue wordmarks and tabs, a shallow wet tread", _endurance, colour="#2a7fff", tread="inter"),
        # bikes and touring cars
        E("moto white stripe", BIKE, "a thin white stripe round the edge: the soft one", _moto, colour=WHITE),
        E("moto yellow stripe", BIKE, "a thin yellow stripe: the hard one", _moto, colour=YELLOW),
        E("moto rain", BIKE, "a dark-blue stripe and a wet tread", _moto, colour="#1b3fbf", tread="rain"),
        E("touring option", BIKE, "an oversized yellow wordmark twice round", _war, colour=YELLOW, cap=2.7, bar=False),
        E("tyre war", BIKE, "a huge wordmark twice round, an accent bar under it", _war, colour=RED),
        # rally
        E("rally asphalt", RALLY, "nearly slick, two grooves, an orange band", _rally, mark=ORANGE, tread="asphalt"),
        E("rally gravel", RALLY, "chunky blocks and a yellow band", _rally, mark=YELLOW, tread="gravel"),
        E("rally snow", RALLY, "narrow blocks, metal studs and a blue band", _rally, mark="#1e60ff", tread="snow",
          words=(MAKER, "ICE"), studs=True),
        E("rally mud", RALLY, "deep lugs, no colour", _rally, mark=None, tread="mud"),
        # drift, drag and karts
        E("drift white", DD, "big raised white letters top and bottom, a semi-slick", _drift),
        E("drift colour", DD, "the same in red (any colour)", _drift, colour="#e4002b"),
        E("smoke neon", DD, "neon pink letters and stripe (bright paint, it doesn't glow)", _smoke),
        E("drag slick", DD, "giant white letters, small print, wrinkles near the rim", _drag),
        E("skinny front", DD, "thin letters and a ribbed tread", _skinny),
        E("kart yellow", DD, "the wordmark and a yellow label box: the soft one", _kart),
        E("kart red", DD, "the same with a red box", _kart, colour="#e4002b"),
        # road and show
        E("raised white letters", ROAD, "white raised capitals, as on 1970s muscle cars", _rwl),
        E("outlined white letters", ROAD, "black raised capitals outlined in white", _rwl, outline=True),
        E("raised red letters", ROAD, "the raised capitals in red", _rwl, colour="#c8102e"),
        E("stealth letters", ROAD, "black on black: satin raised letters on matte rubber", _stealth),
        E("whitewall 1930s", ROAD, "a wide whitewall, nearly the whole sidewall", _whitewall, s0=0.0, s1=0.92),
        E("whitewall 1950s", ROAD, "a whitewall half the sidewall wide", _whitewall, s0=0.18, s1=0.68),
        E("whitewall 1960s", ROAD, "a narrow whitewall", _whitewall, s0=0.36, s1=0.55),
        E("floating stripe", ROAD, "one white stripe floating in the middle", _whitewall, s0=0.5, s1=0.62, colour=WHITE),
        E("triple white", ROAD, "three thin white stripes", _lines,
          bands=[(0.28, 0.34, WHITE), (0.44, 0.5, WHITE), (0.6, 0.66, WHITE)]),
        E("redline", ROAD, "a thin red line (the 1960s muscle car's)", _lines, bands=[(0.6, 0.69, "#c8102e")]),
        E("goldline", ROAD, "a thin gold line", _lines, bands=[(0.6, 0.69, GOLD)]),
        E("blueline raised letters", ROAD, "a blue stripe under raised white letters", _rwl, stripe="#2a5db0"),
        E("red and white pair", ROAD, "two thin stripes, red and white", _lines,
          bands=[(0.46, 0.53, "#c8102e"), (0.6, 0.67, WHITE)]),
        E("gold-pinned whitewall", ROAD, "a narrow whitewall and a thin gold line", _whitewall, s0=0.3, s1=0.56, pin=GOLD),
        E("balloon vintage", ROAD, "1920s: cream sidewalls, raised serif letters, a diamond tread", _balloon),
        E("hot rod", ROAD, "a wide whitewall and a ribbed tread", _whitewall, s0=0.05, s1=0.78, tread="ribs"),
        E("tyre shine", ROAD, "plain black with a wet-look gloss", _shine),
        E("road tyre markings", ROAD, "moulded black on black: name, size, date code, wear markers, arrows", _info),
        # fun
        E("rolling arrows", FUN, "yellow arrows the way it rolls (forward on both sides)", _arrows),
        E("toy redline", FUN, "a toy car's glossy tyre with a thin red line", _toy),
        E("neon ring", FUN, "bright cyan rings and letters (paint, it doesn't glow)", _neon),
        E("chequered sidewall", FUN, "a chequered band all round", _chequer),
        E("cyber slick", FUN, "a purple slick with a pink seam", _cyber),
        E("orange monster", FUN, "an orange tyre with round lugs", _monster),
        E("stars", FUN, "eight white stars", _emblems),
        E("rainbow", FUN, "seven rings, red to violet", _rainbow),
        E("candy stripe", FUN, "red stripes on white, leaning, like a barber's pole", _candy),
        E("colour run", FUN, "a ring running cyan to magenta to yellow round the wheel", _colour_run),
        E("lightning", FUN, "eight yellow lightning bolts", _emblems, kind="bolt", colour="#ffd100"),
        E("crimson tyre", FUN, "the whole tyre crimson", _whole),
        E("white 1910", FUN, "white all over, as tyres were before carbon black", _white_1910),
        # treads on their own, the sidewalls plain
        E("slick", TREAD, "no grooves at all", _tread_only, kind="slick"),
        E("grooved", TREAD, "four grooves round the tread", _tread_only, kind="grooved"),
        E("wet", TREAD, "a deep wet tread", _tread_only, kind="rain"),
        E("intermediate", TREAD, "a shallow wet tread", _tread_only, kind="inter"),
        E("gravel blocks", TREAD, "rally gravel blocks", _tread_only, kind="gravel"),
        E("ribbed", TREAD, "ribs round the tread", _tread_only, kind="ribs"),
        E("semi-slick", TREAD, "a slick middle, blocks at the shoulders", _tread_only, kind="semi-slick"),
    ]


def library():
    """{code: entry} in the catalogue's order: TY-01, TY-02, ... Never reorder or remove: the user
    names a marking by its code. A new one goes at the end; a retired one leaves None."""
    return {f"TY-{k:02d}": e for k, e in enumerate(_catalogue(), 1) if e is not None}


def find(name):
    lib = library()
    key = " ".join(str(name).strip().lower().replace("-", " ").split())
    for code, e in lib.items():
        if key in (code.lower().replace("-", " "), code.lower().replace("-", ""), e["name"].replace("-", " ")):
            return code, e
    raise KeyError(f"no tyre marking called {name!r}; see tool/tyres.py (library)")


def draw(name, **options):
    """The Art for a library marking. options (colour, words, ...) reach its layout where it takes
    them; the others are noted and left out."""
    import inspect
    code, e = find(name)
    art = Art()
    takes = inspect.signature(e["fn"]).parameters
    kw = {**e["defaults"], **{k: v for k, v in options.items() if k in takes}}
    if isinstance(kw.get("words"), str):  # one word: the maker's; the model's stays
        default = e["defaults"].get("words") or takes["words"].default
        kw["words"] = (kw["words"],) + tuple(default[1:])
    for k in options:
        if k not in takes:
            art.notes.append(f"{code} {e['name']}: takes no {k}")
    e["fn"](art, **kw)
    return code, e, art


def main():
    ap = argparse.ArgumentParser(description="The tyre markings library, on the car")
    ap.add_argument("codes", nargs="*")
    args = ap.parse_args()
    from tool import tyresheet
    tyresheet.make(args.codes or list(library()))


if __name__ == "__main__":
    main()
