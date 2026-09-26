"""Looks: patterns drawn in 3D on the car, for the finishes in tool/finishes.py.

A look is a function look(pos, nrm, colour, finish, params) -> dict with
    "colour"     (n, 3) the painted colour per point, sRGB 0..1
    "roughness"  (n,) optional, replaces the finish's roughness where given
    "metalness"  (n,) optional
    "varnish"    (n,) optional
    "weight"     (n,) optional, 0..1: paint only this much (a pattern with holes in it)
pos is (n, 3) in cm, nrm the unit normals; colour is the finish's colour or the user's.

Geometric patterns (weaves, hexagons, checks, camo, lines) are drawn by formula from noise and
grids in 3D (triplanar: the pattern is laid on the surface from the axis it faces most, so it
never stretches and never breaks at a UV seam). Organic wear (rust, chips, leather, cast
metal) comes from photographs of real surfaces: tileable CC0 texture sets from ambientCG,
wrapped onto the car the same triplanar way (tool/textures.py).

params (all optional, per paint call): scale (cm, the pattern's size), seed, palette (a list
of colours for camo/checks/hex/splatter), line (line colour), amount (0..1, how strong the
wear is), direction ("x", "y", "z": the brush/lines direction), wrap ("uv": in the car's own
unfolding, the paint box's default on the body, so dots and grids keep their shape on every
curve; "planes": from the three axes, the default on the inner car).
"""

import numpy as np

from tool import colours, noise
from tool.noise import smoothstep

LOOKS = {}


def look(name):
    def deco(fn):
        LOOKS[name] = fn
        return fn
    return deco


def apply(finish, colour, pos, nrm, params):
    fn = LOOKS[finish.look]
    return fn(pos, nrm, np.asarray(colour, np.float32), finish, params or {})


# ---- helpers ----


def triplanar(nrm, power=4):
    """Weights (n, 3): how much each world axis's projection counts for each point."""
    w = np.abs(nrm) ** power
    return w / np.maximum(w.sum(1, keepdims=True), 1e-6)


def planar_uv(pos, axis):
    """The two coordinates across `axis` (0, 1, 2): the surface seen along that axis."""
    a, b = [k for k in range(3) if k != axis]
    return pos[:, a], pos[:, b]


TUBE_AXIS_Y = 40.0  # the body is roughly a tube around a line at this height, along z


def tube_uv(pos):
    """Coordinates wrapped round the car's length like a label round a tube: u is the arc
    length round the tube (cm), v the position along it. One projection for the whole
    cross-section, so nothing overlaps on the shoulders; only the surfaces facing forward or
    back (the nose's tip, the tail's face) smear, and those take the planar z projection."""
    x, y = pos[:, 0], pos[:, 1] - TUBE_AXIS_Y
    r = np.sqrt(x * x + y * y)
    theta = np.arctan2(x, y)
    return theta * r, pos[:, 2]


def triplanar_value(pos, nrm, fn2d, power=4, wrap="planes", uv=None):
    """Lay a 2D pattern fn2d(u, v) -> (n,) on the surface.
    wrap="uv": in the car's own unfolding (tool/uvmap.py), which has almost no stretch; `uv`
    is the (n, 2) flat position in cm the paint box passes in. The default on the body.
    wrap="planes": from each of the three axes, blended by facing; the default on the inner
    car. wrap="tube": round the car's length (kept for comparison; it stretches the flanks)."""
    if wrap == "uv" and uv is not None:
        return fn2d(uv[:, 0], uv[:, 1])
    if wrap == "tube":
        along = np.abs(nrm[:, 2])
        t = smoothstep(0.6, 0.85, along)  # 1: faces along the car: use the flat z projection
        out = np.zeros(len(pos), np.float32)
        side = t < 0.99
        if side.any():
            u, v = tube_uv(pos[side])
            out[side] += (1 - t[side]) * fn2d(u, v)
        end = t > 0.01
        if end.any():
            u, v = planar_uv(pos[end], 2)
            out[end] += t[end] * fn2d(u, v)
        return out
    w = triplanar(nrm, power)
    out = np.zeros(len(pos), np.float32)
    for axis in range(3):
        sel = w[:, axis] > 0.01
        if not sel.any():
            continue
        u, v = planar_uv(pos[sel], axis)
        out[sel] += w[sel, axis] * fn2d(u, v)
    return out


def tint(colour, value):
    """colour (3,) times a per-point brightness (n,) -> (n, 3)."""
    return np.clip(colour[None, :] * value[:, None], 0, 1)


def mix(a, b, t):
    t = np.asarray(t, np.float32)
    if a.ndim == 1:
        a = np.broadcast_to(a, (len(t), 3))
    if np.ndim(b) == 1:
        b = np.broadcast_to(np.asarray(b, np.float32), a.shape)
    return a * (1 - t)[:, None] + b * t[:, None]


def palette(params, colour, defaults):
    """The colours for multi-colour patterns: the user's palette, else the stated colour
    followed by defaults."""
    pal = params.get("palette")
    if pal:
        return [None if c in (None, "keep") else np.asarray(colours.get(c), np.float32) for c in pal]
    return [colour] + [np.asarray(c, np.float32) for c in defaults]


def const(n, v):
    return np.full(n, v, np.float32)


# ---- weaves ----


def _twill(u, v, cell):
    """A 2/2 twill weave in 2D, 0..1: cells of thread whose direction alternates like a board."""
    u, v = u / cell, v / cell
    cu, cv = np.floor(u), np.floor(v)
    along_u = ((cu + cv) % 2) == 0
    phase = np.where(along_u, v, u)
    stripes = 0.5 + 0.5 * np.cos(2 * np.pi * phase * 2)
    t = np.where(along_u, u - cu, v - cv)
    shade = 1 - 0.6 * np.abs(t - 0.5) * 2
    return stripes * shade


def _plain(u, v, cell):
    """A plain (over-and-under) weave in 2D, 0..1: square cells whose threads alternate
    direction, each thread rounded so it darkens at its edges."""
    u, v = u / cell, v / cell
    cu, cv = np.floor(u), np.floor(v)
    along_u = ((cu + cv) % 2) == 0
    across = np.where(along_u, v - cv, u - cu)
    return 0.25 + 0.75 * np.sin(np.pi * across)


@look("carbon")
def carbon(pos, nrm, colour, finish, params):
    cell = params.get("scale", 0.5)
    w = triplanar_value(pos, nrm, lambda u, v: _twill(u, v, cell), wrap=params.get("wrap", "planes"), uv=params.get("uv"))
    return {"colour": tint(colour, 0.5 + 0.55 * w)}


@look("weave")
def weave(pos, nrm, colour, finish, params):
    cell = params.get("scale", 0.4)
    w = triplanar_value(pos, nrm, lambda u, v: _twill(u, v, cell), wrap=params.get("wrap", "planes"), uv=params.get("uv"))
    return {"colour": tint(colour, 0.6 + 0.5 * w)}


@look("plain")
def plain(pos, nrm, colour, finish, params):
    cell = params.get("scale", 0.6)
    w = triplanar_value(pos, nrm, lambda u, v: _plain(u, v, cell), wrap=params.get("wrap", "planes"), uv=params.get("uv"))
    return {"colour": tint(colour, 0.5 + 0.55 * w)}


@look("denim")
def denim(pos, nrm, colour, finish, params):
    """A fine twill with lighter threads showing between, and the dye a little uneven."""
    cell = params.get("scale", 0.15)
    w = triplanar_value(pos, nrm, lambda u, v: _twill(u, v, cell), wrap=params.get("wrap", "planes"), uv=params.get("uv"))
    dye = noise.fbm(pos / 6, 3, params.get("seed", 0))
    col = mix(colour, np.array([0.85, 0.87, 0.9], np.float32), 0.22 * (1 - w))
    return {"colour": tint(col, 0.85 + 0.25 * dye)}


@look("forged")
def forged(pos, nrm, colour, finish, params):
    cell = params.get("scale", 1.2)
    seed = params.get("seed", 0)
    ident = noise.cell_id(pos / cell, seed)
    grain = noise.value(pos * 3, seed + 9)
    v = 0.35 + 0.8 * ident + 0.15 * (grain - 0.5)
    return {"colour": tint(colour, v), "roughness": const(len(pos), finish.roughness) + 0.15 * (ident - 0.5)}


@look("cloth")
def cloth(pos, nrm, colour, finish, params):
    cell = params.get("scale", 0.12)
    w = triplanar_value(pos, nrm, lambda u, v: 0.5 + 0.25 * np.cos(2 * np.pi * u / cell) + 0.25 * np.cos(2 * np.pi * v / cell))
    return {"colour": tint(colour, 0.85 + 0.3 * w)}


@look("webbing")
def webbing(pos, nrm, colour, finish, params):
    cell = params.get("scale", 0.25)
    w = triplanar_value(pos, nrm, lambda u, v: 0.5 + 0.5 * np.cos(2 * np.pi * v / cell))
    return {"colour": tint(colour, 0.8 + 0.35 * w)}


@look("leather")
def leather(pos, nrm, colour, finish, params):
    seed = params.get("seed", 0)
    f1, f2 = noise.worley(pos / 0.35, seed, second=True)
    crease = smoothstep(0.0, 0.12, f2 - f1)  # dark lines between the grains
    big = noise.fbm(pos / 8, 3, seed + 3)
    v = (0.8 + 0.3 * crease) * (0.9 + 0.2 * big)
    return {"colour": tint(colour, v), "roughness": const(len(pos), finish.roughness) + 0.2 * (1 - crease)}


@look("suede")
def suede(pos, nrm, colour, finish, params):
    """Napped suede: soft, cloudy light and dark where the nap lies different ways."""
    seed = params.get("seed", 0)
    nap = noise.fbm(pos / 1.5, 3, seed)
    fine = noise.value(pos * 12, seed + 1)
    return {"colour": tint(colour, 0.88 + 0.18 * nap + 0.06 * (fine - 0.5))}


@look("perforated")
def perforated(pos, nrm, colour, finish, params):
    """Leather with small holes in staggered rows. scale: the rows' spacing in cm."""
    out = leather(pos, nrm, colour, finish, params)
    pitch = params.get("scale", 0.5)

    def holes(u, v):
        row = np.floor(v / pitch)
        du = ((u / pitch + 0.5 * (row % 2)) % 1) - 0.5
        dv = ((v / pitch) % 1) - 0.5
        return smoothstep(0.2, 0.13, np.sqrt(du * du + dv * dv))

    h = np.clip(triplanar_value(pos, nrm, holes, wrap=params.get("wrap", "planes"), uv=params.get("uv")), 0, 1)
    out["colour"] = mix(out["colour"], np.array([0.02, 0.02, 0.02], np.float32), 0.9 * h)
    out["roughness"] = out["roughness"] * (1 - h) + h
    return out


@look("knurl")
def knurl(pos, nrm, colour, finish, params):
    """A diamond grip pattern: two sets of grooves crossing, each diamond lit on one side (paint
    only: the body takes no relief). scale: the grooves' spacing in cm."""
    pitch = params.get("scale", 0.8)

    def diamonds(u, v):
        a, b = ((u + v) / pitch) % 1, ((u - v) / pitch) % 1
        peak = np.minimum(np.minimum(a, 1 - a), np.minimum(b, 1 - b)) * 2  # 0 in a groove, 1 on a peak
        lit = np.where(a < 0.5, 1.0, 0.75)  # the half of each diamond that faces the light
        return peak * lit

    d = triplanar_value(pos, nrm, diamonds, wrap=params.get("wrap", "planes"), uv=params.get("uv"))
    return {"colour": tint(colour, 0.35 + 1.3 * d), "roughness": const(len(pos), finish.roughness) - 0.2 * (d - 0.5)}


# ---- metals ----


def _direction(params, default="z"):
    return "xyz".index(params.get("direction", default))


@look("brushed")
def brushed(pos, nrm, colour, finish, params):
    seed = params.get("seed", 0)
    k = _direction(params)
    stretch = np.ones(3, np.float32) * 25
    stretch[k] = 0.15
    lines = noise.value(pos * stretch, seed) * 0.5 + noise.value(pos * stretch * 2.3 + 5, seed + 1) * 0.5
    v = 0.88 + 0.24 * lines
    return {"colour": tint(colour, v), "roughness": const(len(pos), finish.roughness) + 0.12 * (lines - 0.5)}


@look("flake")
def flake(pos, nrm, colour, finish, params):
    seed = params.get("seed", 0)
    size = params.get("scale", 0.08)
    h = noise.cell_id(pos / size, seed)
    sparkle = h ** 6
    v = 0.92 + 0.35 * sparkle
    return {"colour": tint(colour, v), "roughness": const(len(pos), finish.roughness) - 0.2 * sparkle}


@look("grain")
def grain(pos, nrm, colour, finish, params):
    """A fine even grain, as on moulded plastic or bead-blasted metal. scale: the grain's size in cm."""
    seed = params.get("seed", 0)
    size = params.get("scale", 0.05)
    g = 0.6 * noise.value(pos / size, seed) + 0.4 * noise.value(pos / (size * 2.7) + 7, seed + 1)
    return {"colour": tint(colour, 0.93 + 0.14 * g), "roughness": const(len(pos), finish.roughness) + 0.1 * (g - 0.5)}


@look("cast")
def cast(pos, nrm, colour, finish, params):
    seed = params.get("seed", 0)
    g = noise.fbm(pos * 2, 3, seed)
    pits = smoothstep(0.62, 0.7, noise.value(pos * 4 + 3, seed + 2))
    v = (0.85 + 0.3 * g) * (1 - 0.35 * pits)
    return {"colour": tint(colour, v), "roughness": const(len(pos), finish.roughness) + 0.15 * (g - 0.5) + 0.2 * pits}


# ---- paints ----


@look("pearl")
def pearl(pos, nrm, colour, finish, params):
    seed = params.get("seed", 0)
    sheen = noise.fbm(pos / 12, 3, seed)
    fine = noise.cell_id(pos / 0.1, seed + 1) ** 8
    return {"colour": tint(colour, 0.94 + 0.12 * sheen + 0.2 * fine)}


@look("candy")
def candy(pos, nrm, colour, finish, params):
    deep = np.clip(colour, 0, 1) ** 1.35
    fine = noise.cell_id(pos / 0.1, params.get("seed", 0)) ** 8
    return {"colour": tint(deep, 0.95 + 0.25 * fine)}


# ---- wear ----


def _amount(params, default=0.5):
    return float(params.get("amount", default))


@look("scratched")
def scratched(pos, nrm, colour, finish, params):
    seed = params.get("seed", 0)
    amt = _amount(params)
    total = np.zeros(len(pos), np.float32)
    for k, (stretch, thr) in enumerate(((np.array([0.12, 30, 30]), 0.86), (np.array([30, 0.12, 30]), 0.88),
                                        (np.array([20, 20, 0.15]), 0.87))):
        s = noise.value(pos * stretch + k * 11, seed + k)
        total = np.maximum(total, smoothstep(thr - 0.02, thr + 0.02, s))
    total *= smoothstep(0.35, 0.65, noise.fbm(pos / 20, 3, seed + 7)) * 0.5 + 0.5  # patchy
    total *= amt * 1.6
    total = np.clip(total, 0, 1)
    light = np.clip(colour + (1 - colour) * 0.55, 0, 1)  # towards white, per point (colour may be (n, 3))
    out = mix(colour, light, total * 0.8)
    return {"colour": out, "roughness": const(len(pos), finish.roughness) + 0.3 * total,
            "varnish": const(len(pos), finish.varnish) * (1 - total)}


@look("chipped")
def chipped(pos, nrm, colour, finish, params):
    seed = params.get("seed", 0)
    amt = _amount(params)
    f = noise.fbm(pos / 1.2, 3, seed)
    thr = 0.68 - 0.12 * amt
    chip = smoothstep(thr - 0.02, thr + 0.02, f)
    metal = np.array([0.55, 0.55, 0.57], np.float32)
    n = len(pos)
    return {"colour": mix(colour, metal, chip), "roughness": const(n, finish.roughness) * (1 - chip) + 0.45 * chip,
            "metalness": const(n, finish.metalness) * (1 - chip) + chip, "varnish": const(n, finish.varnish) * (1 - chip)}


@look("dusty")
def dusty(pos, nrm, colour, finish, params):
    seed = params.get("seed", 0)
    amt = _amount(params)
    d = noise.fbm(pos / 9, 4, seed)
    up = smoothstep(-0.2, 0.6, nrm[:, 1])  # dust settles on top
    film = np.clip(amt * (0.35 + 0.9 * d) * (0.5 + 0.5 * up), 0, 1) * 0.6
    dust = np.array([0.72, 0.68, 0.6], np.float32)
    return {"colour": mix(colour, dust, film), "roughness": const(len(pos), finish.roughness) + 0.3 * film}


@look("faded")
def faded(pos, nrm, colour, finish, params):
    seed = params.get("seed", 0)
    amt = _amount(params)
    f = noise.fbm(pos / 30, 3, seed)
    t = np.clip(amt * (0.3 + 0.9 * f), 0, 1) * 0.7
    grey = np.array([0.6, 0.6, 0.58], np.float32) * 0.5 + colour * 0.5
    pale = mix(colour, grey, t)
    return {"colour": pale, "roughness": const(len(pos), finish.roughness) + 0.2 * t}


@look("rusted")
def rusted(pos, nrm, colour, finish, params):
    seed = params.get("seed", 0)
    amt = _amount(params)
    f = noise.fbm(pos / 6, 5, seed)
    thr = 0.62 - 0.2 * amt
    rust = smoothstep(thr - 0.06, thr + 0.06, f)
    tone = noise.fbm(pos / 2, 3, seed + 5)
    rust_col = mix(np.array([0.42, 0.18, 0.07], np.float32), np.array([0.7, 0.35, 0.12], np.float32), tone)
    n = len(pos)
    return {"colour": mix(colour, rust_col, rust), "roughness": const(n, finish.roughness) * (1 - rust) + 0.92 * rust,
            "metalness": const(n, finish.metalness) * (1 - rust), "varnish": const(n, finish.varnish) * (1 - rust)}


@look("greasy")
def greasy(pos, nrm, colour, finish, params):
    seed = params.get("seed", 0)
    amt = _amount(params)
    g = noise.fbm(pos / 10, 4, seed)
    smear = smoothstep(0.5, 0.72, g) * amt * 1.3
    smear = np.clip(smear, 0, 1)
    return {"colour": tint(colour, 1 - 0.4 * smear), "roughness": const(len(pos), finish.roughness) - 0.35 * smear}


@look("muddy")
def muddy(pos, nrm, colour, finish, params):
    """Dried mud splashed on, heavier low down (pos y is the height in cm), in patches and drops."""
    seed = params.get("seed", 0)
    amt = _amount(params)
    low = smoothstep(60, 10, pos[:, 1])
    splash = noise.fbm(pos / 5, 5, seed)
    thr = 0.78 - 0.5 * amt * (0.4 + 0.6 * low)
    mud = smoothstep(thr, thr + 0.06, splash)
    drops = smoothstep(0.7, 0.74, noise.value(pos / 0.7, seed + 3)) * amt
    mud = np.clip(np.maximum(mud, drops), 0, 1)
    tone = noise.fbm(pos / 2, 3, seed + 5)
    mud_col = mix(np.array([0.36, 0.24, 0.14], np.float32), np.array([0.55, 0.41, 0.28], np.float32), tone)
    n = len(pos)
    return {"colour": mix(colour, mud_col, mud), "roughness": const(n, finish.roughness) * (1 - mud) + 0.95 * mud,
            "metalness": const(n, finish.metalness) * (1 - mud), "varnish": const(n, finish.varnish) * (1 - mud)}


@look("worn")
def worn(pos, nrm, colour, finish, params):
    p = dict(params)
    amt = _amount(params, 0.4)
    a = chipped(pos, nrm, colour, finish, {**p, "amount": amt * 0.6})
    b = scratched(pos, nrm, a["colour"], finish, {**p, "amount": amt * 0.7, "seed": p.get("seed", 0) + 20})
    b["roughness"] = np.maximum(a["roughness"], b["roughness"])
    b["metalness"] = a["metalness"]
    b["varnish"] = np.minimum(a["varnish"], b["varnish"])
    c = dusty(pos, nrm, b["colour"], finish, {**p, "amount": amt * 0.5, "seed": p.get("seed", 0) + 40})
    b["colour"] = c["colour"]
    return b


# ---- patterns that arrange colours ----


@look("camo")
def camo(pos, nrm, colour, finish, params):
    seed = params.get("seed", 0)
    scale = params.get("scale", 22.0)
    pal = palette(params, colour, [(0.33, 0.38, 0.25), (0.55, 0.5, 0.35), (0.12, 0.13, 0.1)])
    a = noise.fbm(pos / scale, 4, seed)
    b = noise.fbm(pos / scale + 100, 4, seed + 1)
    out = np.broadcast_to(pal[0], (len(pos), 3)).copy()
    edge = 0.015
    if len(pal) > 1:
        out = mix(out, pal[1], smoothstep(0.5 - edge, 0.5 + edge, a))
    if len(pal) > 2:
        out = mix(out, pal[2], smoothstep(0.56 - edge, 0.56 + edge, b))
    if len(pal) > 3:
        out = mix(out, pal[3], smoothstep(0.66 - edge, 0.66 + edge, a * 0.5 + b * 0.5))
    return {"colour": out}


@look("checks")
def checks(pos, nrm, colour, finish, params):
    cell = params.get("scale", 10.0)
    pal = palette(params, colour, [(0.04, 0.04, 0.05)])
    k = _direction(params, "x")  # the board is laid in the plane across this axis by default: use triplanar

    def board(u, v):
        return ((np.floor(u / cell) + np.floor(v / cell)) % 2)
    t = triplanar_value(pos, nrm, board, power=8, wrap=params.get("wrap", "planes"), uv=params.get("uv"))
    t = smoothstep(0.45, 0.55, t)
    return {"colour": mix(pal[0], pal[1], t)}


# ---- Patterns made of separate things placed on the surface: dots, splashes, cells ----
# Drawing these flat on the car's panels clips them at every panel edge (user, 2026-09-24).
# Instead, each element is centred on a point of the surface itself, spaced evenly, and drawn
# by 3D distance from that point: whole everywhere, bending over a fold like a sticker.


def surface_points(pos, spacing, seed=0, regular=True, relax=15):
    """Evenly spaced points on the painted surface, at least `spacing` cm apart (Poisson-disc
    thinning of candidate texels). regular=True takes candidates nearest a 3D lattice first,
    so the result reads as a grid where the surface is flat; False gives a hand-placed look."""
    from scipy.spatial import cKDTree
    rng = np.random.default_rng(seed)
    n = len(pos)
    want = max(int(n * 9 / max(spacing, 0.5) ** 2 / 125 * 2), 2000)  # ~2 candidates per (spacing/3)^2 at 4096
    want = min(want, n, 400_000)
    cand = pos[rng.choice(n, want, replace=False)]
    if regular:
        off = rng.uniform(0, spacing, 3)
        lattice = np.abs(((cand + off) / spacing + 0.5) % 1 - 0.5).max(1)  # distance to the lattice, in cells
        order = np.argsort(lattice + rng.uniform(0, 0.02, want))
    else:
        order = rng.permutation(want)
    cand = cand[order]
    tree = cKDTree(cand)
    pairs = tree.query_pairs(spacing, output_type="ndarray")
    # greedy: in order, accept a candidate unless an earlier accepted one is within spacing
    blocked = np.zeros(want, bool)
    lo, hi = np.minimum(pairs[:, 0], pairs[:, 1]), np.maximum(pairs[:, 0], pairs[:, 1])
    order2 = np.argsort(lo)
    lo, hi = lo[order2], hi[order2]
    starts = np.searchsorted(lo, np.arange(want + 1))
    accepted = []
    for i in range(want):
        if blocked[i]:
            continue
        accepted.append(i)
        blocked[hi[starts[i]:starts[i + 1]]] = True
    points = cand[accepted]
    # settle: each point moves to the middle of the surface nearest to it, then back onto the
    # surface (Lloyd relaxation), so the spacing evens out into a honeycomb-like arrangement
    # instead of a jittered one (the user found the first result messy, 2026-09-24)
    for _ in range(int(relax)):
        _, owner = cKDTree(points).query(cand, workers=-1)
        sums = np.zeros_like(points)
        np.add.at(sums, owner, cand)
        counts = np.bincount(owner, minlength=len(points))[:, None]
        centroid = np.where(counts > 0, sums / np.maximum(counts, 1), points)
        _, back = tree.query(centroid, workers=-1)  # snap to the nearest candidate on the surface
        points = cand[back]
    return points


def _nearest(points, pos, k=1):
    from scipy.spatial import cKDTree
    return cKDTree(points).query(pos, k=k, workers=-1)


@look("dots")
def dots(pos, nrm, colour, finish, params):
    """Polka dots placed on the surface. scale: the spacing in cm; "dot": the dot's diameter as
    a share of the spacing (0.5); regular=False for a scattered, hand-placed look."""
    spacing = params.get("scale", 8.0)
    r = params.get("dot", 0.5) * spacing / 2
    pal = palette(params, colour, [(0.97, 0.97, 0.95)])
    keep = pal[0] is None
    if params.get("method", "surface") == "grid":
        # the flat grid in the car's unfolding: exact rows on each panel, broken at panel edges
        stagger = params.get("stagger", True)

        def grid(u, v):
            row = np.floor(v / spacing)
            cu = (u / spacing + (0.5 * (row % 2) if stagger else 0)) % 1 - 0.5
            cv = v / spacing % 1 - 0.5
            return smoothstep(r / spacing + 0.02, r / spacing - 0.02, np.sqrt(cu * cu + cv * cv))
        dot = triplanar_value(pos, nrm, grid, power=8, wrap=params.get("wrap", "planes"), uv=params.get("uv"))
    else:
        centres = surface_points(pos, spacing, params.get("seed", 0), params.get("regular", True), params.get("relax", 15))
        d, _ = _nearest(centres, pos)
        dot = smoothstep(r + 0.08, r - 0.08, d)
    out = mix(pal[0] if not keep else colour, pal[1], dot)
    return {"colour": out, "weight": dot} if keep else {"colour": out}


@look("splatter")
def splatter(pos, nrm, colour, finish, params):
    """Drops placed on the surface, of varied size, in the palette's colours after the first."""
    seed = params.get("seed", 0)
    scale = params.get("scale", 6.0)
    pal = palette(params, colour, [(0.95, 0.2, 0.6), (0.1, 0.8, 0.9), (1.0, 0.85, 0.1)])
    keep = pal[0] is None
    out = np.broadcast_to(pal[0] if not keep else colour, (len(pos), 3)).copy()
    weight = np.zeros(len(pos), np.float32)
    rng = np.random.default_rng(seed)
    for k, c in enumerate(pal[1:]):
        centres = surface_points(pos, scale * 1.6, seed + 7 * k, regular=False)
        radius = rng.uniform(0.25, 0.7, len(centres)) * scale
        d, j = _nearest(centres, pos)
        edge = 0.15 * radius[j] * (noise.value(pos * 1.5 + k * 3, seed + k) - 0.5)  # a wobbly rim
        drop = smoothstep(0.1, -0.1, d - radius[j] + edge)
        out = mix(out, c, drop)
        weight = np.maximum(weight, drop)
    return {"colour": out, "weight": weight} if keep else {"colour": out}


@look("hex")
def hexagons(pos, nrm, colour, finish, params):
    """A honeycomb of cells grown round evenly spaced surface points: the lines are where two
    cells meet. scale: the cell size in cm; "line": the line width in cm; "line colour"."""
    cell = params.get("scale", 4.0)
    width = params.get("line", 0.35)
    line_col = np.asarray(colours.get(params["line colour"]), np.float32) if "line colour" in params         else np.clip(colour * 0.35, 0, 1)
    centres = surface_points(pos, cell * 0.92, params.get("seed", 0), regular=True)
    d, _ = _nearest(centres, pos, k=2)
    gap = d[:, 1] - d[:, 0]  # 0 on the border between two cells
    t = smoothstep(width + 0.06, width - 0.06, gap)
    return {"colour": mix(colour, line_col, t)}


@look("lines")
def lines(pos, nrm, colour, finish, params):
    spacing = params.get("scale", 3.0)
    width = params.get("line", 0.6)
    k = _direction(params, "x")
    line_col = np.asarray(colours.get(params["line colour"]), np.float32) if "line colour" in params else np.clip(colour * 0.3, 0, 1)
    d = np.abs(((pos[:, k] / spacing) % 1) - 0.5) * spacing
    t = smoothstep(width / 2 + 0.05, width / 2 - 0.05, d)
    return {"colour": mix(colour, line_col, t)}


@look("texture")
def texture(pos, nrm, colour, finish, params):
    """A photographed surface (tool/textures.py) wrapped on in 3D. params: texture (the set's
    name), scale (cm the picture covers), tint (multiply the picture by the colour)."""
    from tool import textures
    name = params.get("texture")
    if not name:
        base = finish.name
        for shine in ("gloss ", "satin ", "matte ", "semi-gloss ", "mirror "):  # a shine override's prefix
            if base.startswith(shine):
                base = base[len(shine):]
        name = TEXTURE_OF.get(base) or (base if base in textures.SETS else TEXTURE_OF[base.split(" ")[-1]])
    return textures.wrap(name, pos, nrm, colour, finish, params)


# which photographed surface each finish uses by default (finish name, or its last word after a shine override)
TEXTURE_OF = {"rusted": "rust", "chipped": "chips", "leather": "leather", "quilted leather": "quilted leather",
              "raw cast": "cast", "cast": "cast", "brushed steel": "brushed", "brushed titanium": "brushed",
              "steel": "brushed", "titanium": "brushed"}
