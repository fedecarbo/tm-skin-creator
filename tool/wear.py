"""Paint that has aged: the top coat faded, chipped, scraped along the walls, its clear coat gone.

    under = s.keep()                       # what shows through: primer, bare metal
    s.paint("body", ...)                   # the top coat (a flag, a livery), any number of colours
    s.wear(under, fade=0.3, chips=0.05, scrapes=0.5, clearcoat=0.2)

The looks in tool/looks.py ("faded", "chipped") wear one colour as it's painted; this wears the
whole coat as it stands, so a flag of several colours ages as one paint job. Drawn in 3D on the
baked positions, as the tears are (tool/peel.py), so nothing breaks at a seam, and every worn
edge is a hard one-texel cut, as the tears' are (soft edges read as blurred: the user,
2026-09-24).

- fade: how far the coat has washed out towards a pale, warm grey version of itself, in soft
  blotches about a third of a metre across, most where the sun falls (surfaces facing up).
- chips: the share of the paint chipped off in small flakes where a race car takes stones: the
  nose, faces turned forward, low down on the sides (up to a wandering line, in patches), a few
  elsewhere. Each shows `under`, with a thin dark rim where the paint breaks.
- scrapes: long scuffs along the car on its outermost sides, at the height a wall touches,
  down to `under`: the car has rubbed the barriers. 0..1, how many.
- clearcoat: the share of the upward faces where the clear coat has failed in the sun: ragged
  patches, chalky and matte, paler than the paint around them.

TSC_FlagPeel_CostaRica's worn takes, 2026-09-26 (the user: "Maybe in this concept its more on
looking worn, the flag? Instead of torn paint?"). A first try showed bare aluminium in the chips:
it mirrored the dark room and read as black specks, in a band along the sills like a pattern.
"""

import time

import numpy as np

from tool import noise, peel
from tool.noise import smoothstep


def _cut(H, idx, c):
    """Where a field H (> 0 inside) cuts through: 0..1 with a one-texel edge, and cm from the edge."""
    g, pitch = peel.gradient(H, idx, c.pos, c.w, c.w * c.h)
    sd = H / np.maximum(g, 1e-6)
    return np.clip(0.5 + sd / pitch, 0, 1), sd, pitch


def _show(c, idx, under, hole, rim=None):
    """Let `under` through where hole is 1; rim darkens it along the break."""
    for k in ("colour", "rough", "metal", "coat"):
        layer = getattr(c, k)
        if layer is None:
            continue
        u = under[k][idx]
        if k == "colour":
            if rim is not None:
                u = u * (1 - 0.45 * rim)[:, None]
            layer[idx] = layer[idx] * (1 - hole[:, None]) + u * hole[:, None]
        else:
            layer[idx] = layer[idx] * (1 - hole) + u * hole


def exposure(pos, nrm, seed=0):
    """0..1: how much stone and grit a surface takes: forward faces, the nose, low on the sides up
    to a line that wanders (so it never reads as a band), all in patches."""
    wander = 14.0 * (noise.fbm(pos / 45.0, 2, seed + 3) - 0.5)
    low = smoothstep(36.0 + wander, 16.0, pos[:, 1])
    forward = smoothstep(0.1, 0.7, nrm[:, 2])
    nose = smoothstep(120.0, 200.0, pos[:, 2]) * 0.8
    patches = smoothstep(0.3, 0.7, noise.fbm(pos / 22.0, 3, seed + 5))
    return np.maximum.reduce([forward, low, nose]) * (0.35 + 0.65 * patches)


def wear(skin, under, where="body", fade=0.3, chips=0.05, scrapes=0.0, clearcoat=0.0, chip_size=1.6, seed=0):
    t0 = time.time()
    tset = under.get("set", "Skin")
    c = skin.canvas(tset)
    idx, m = skin._mask(tset, skin._ids(where).get(tset, []), None, c)
    pos, nrm = c.pos[idx], c.nrm[idx]
    up = smoothstep(-0.1, 0.8, nrm[:, 1])
    said = [f"faded up to {fade:.0%}"]

    def pale(col, t):
        grey = col.mean(1, keepdims=True)
        target = 0.55 * (0.6 * col + 0.4 * grey) + 0.45 * np.array([0.88, 0.85, 0.8], np.float32)
        return col * (1 - t[:, None]) + target * t[:, None]

    if fade > 0:
        blotch = noise.fbm(pos / 60.0, 3, seed + 31)
        t = np.clip(fade * (0.35 + 0.9 * blotch) * (0.35 + 0.65 * up), 0, 0.85)
        c.colour[idx] = pale(c.colour[idx], t)
        c.rough[idx] = np.clip(c.rough[idx] + 0.25 * t, 0, 1)
    if clearcoat > 0:  # a few big ragged patches on the highest upward faces, chalky and matte
        # (at a fifth of the faces, 20 cm across, they read as camouflage: 2026-09-26)
        high = up * smoothstep(50.0, 72.0, pos[:, 1])
        f = noise.fbm(pos / 34.0, 3, seed + 41) + 0.12 * (peel.facets(pos / 5.0, seed + 43, 2) - 0.5) + 0.45 * (high - 1)
        hole, sd, pitch = _cut(f - float(np.quantile(f, 1 - clearcoat)), idx, c)
        lift = np.clip(0.5 + (0.12 - sd) / pitch, 0, 1) * hole  # the lifting edge, 1.2 mm, lighter
        chalk = 0.35 + 0.25 * noise.fbm(pos / 0.9, 2, seed + 45)  # mottled, not flat
        col = pale(c.colour[idx], chalk * hole)
        c.colour[idx] = np.clip(col + 0.2 * lift[:, None], 0, 1)
        c.rough[idx] = c.rough[idx] * (1 - hole) + 0.95 * hole
        if c.coat is not None:
            c.coat[idx] = c.coat[idx] * (1 - hole) + hole  # no varnish left
        said.append(f"{float((hole * m).sum() / max(m.sum(), 1)):.0%} clear coat gone")
    if scrapes > 0:  # long scuffs along the car where the walls touch: the outermost sides, 20-55 cm up
        side = smoothstep(0.55, 0.85, np.abs(nrm[:, 0])) * smoothstep(55.0, 72.0, np.abs(pos[:, 0]))
        band = smoothstep(18.0, 26.0, pos[:, 1]) * smoothstep(58.0, 48.0, pos[:, 1])
        where_hit = smoothstep(0.62 - 0.25 * scrapes, 0.7 - 0.25 * scrapes, noise.fbm(pos / 50.0, 2, seed + 51))
        streak = noise.fbm(pos * np.array([0.0, 1.1, 0.03], np.float32), 3, seed + 53)
        gate = smoothstep(0.3, 0.6, side * band * where_hit)
        H = streak - (0.63 - 0.08 * scrapes) - 0.6 * (1 - gate)
        hole, sd, pitch = _cut(H, idx, c)
        _show(c, idx, under, hole)
        said.append(f"{float((hole * m).sum() / max(m.sum(), 1)):.1%} scraped")
    if chips > 0:
        e = exposure(pos, nrm, seed)
        f = noise.fbm(pos / chip_size, 3, seed + 7) + 0.12 * (peel.facets(pos / (chip_size * 0.6), seed + 9, 2) - 0.5)
        f = f + 0.35 * (e - 1)  # only a few where nothing hits
        hole, sd, pitch = _cut(f - float(np.quantile(f, 1 - chips)), idx, c)
        rim = np.clip(0.5 + (0.06 - sd) / pitch, 0, 1) * hole  # the broken paint's edge, 0.6 mm
        _show(c, idx, under, hole, rim)
        said.append(f"{float((hole * m).sum() / max(m.sum(), 1)):.1%} chipped")
    c.touched[idx] = True
    skin.notes.append(f"wear on {where}: {', '.join(said)} ({time.time() - t0:.0f} s)")
