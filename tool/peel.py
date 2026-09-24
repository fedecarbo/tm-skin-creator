"""A wrap torn off the body: the top paint ripped open to show the paint underneath.

    under = s.keep()                       # the body's paint so far: the layer underneath
    s.paint("body", "matte black")         # the wrap on top
    s.peel(under, amount=0.2)              # torn open

Tears are drawn in 3D (noise on the baked positions, stretched along the car as if the wind
tore them), so they cross panel seams without a break. Their outline is faceted noise: straight
runs and sharp corners, no blobs or loose specks. The edge is a hard cut, anti-aliased over one
texel: the field is divided by its gradient, measured on the texel grid, which gives the
distance to the border.

The wrap reads as a thin layer on top through a narrow shadow just inside every tear's edge,
the same width all round (a light from straight above), hard-edged: a solid band with a
one-texel edge, no fade. The same all round so it reads from every camera.

The user, 2026-09-24, in turn: a soft shadow (a fade over a centimetre) and a grey bevel all
round made the edges look soft; strips of wrap folded back over it looked flat, not 3D; then
"a bit of 3D so it looks like a slight layer on top, just crispier" gave a hard shadow cast by
a light from ahead, with a lit hairline on the far edges; then "shorten the shadow" and make its
angle "more neutral, because when the camera is on the rear it doesn't look 3D": this.
"""

import time

import numpy as np
from scipy.spatial import cKDTree

from tool import noise


def facets(p, seed, octaves=2):
    """Faceted noise, 0..1: straight between lattice points, so added to a smooth field it
    gives a torn edge of straight runs and sharp corners, not blobs."""
    out, amp, total = np.zeros(len(p), np.float32), 1.0, 0.0
    for k in range(octaves):
        out += amp * noise.value(p * 2.3 ** k + 5.1 * k, seed + k, smooth=False)
        total += amp
        amp *= 0.45
    return out / total


def tears(p, amount, scale, seed, stretch=0.5, jag=0.07):
    """The tear field at points p (> 0 torn), its zero level set so `amount` of them are torn."""
    warp = np.stack([noise.value(p / (scale * 1.3) + 31.7 * k, seed + 10 + k) for k in range(3)], 1) - 0.5
    q = p + warp * scale * 0.5
    q[:, 2] *= stretch  # longer along the car
    f = noise.fbm(q / scale, 2, seed) + jag * (facets(p / 4, seed + 5, 3) - 0.5)
    return f - float(np.quantile(f, 1 - amount))


def gradient(F, idx, P, w, n):
    """The size of F's gradient per cm at texels idx, from the texel grid (neighbours more
    than 0.6 cm apart are across an island border and ignored), and the texel pitch in cm."""
    full = np.full(n, np.nan, np.float32)
    full[idx] = F
    g2 = np.zeros(len(idx), np.float32)
    pitch = np.full(len(idx), 9.0, np.float32)
    for step in (1, w):
        side = []
        for sgn in (-1, 1):
            j = np.clip(idx + sgn * step, 0, n - 1)
            Fj = full[j]
            d = np.linalg.norm(P[j] - P[idx], axis=1)
            ok = np.isfinite(Fj) & (d > 1e-4) & (d < 0.6)
            side.append((Fj, d, ok))
            pitch = np.where(ok, np.minimum(pitch, d), pitch)
        (Fa, da, oka), (Fb, db, okb) = side
        deriv = np.zeros(len(idx), np.float32)
        both = oka & okb
        deriv[both] = (Fb[both] - Fa[both]) / (da[both] + db[both])
        a_only = oka & ~okb
        deriv[a_only] = (F[a_only] - Fa[a_only]) / da[a_only]
        b_only = okb & ~oka
        deriv[b_only] = (Fb[b_only] - F[b_only]) / db[b_only]
        g2 += deriv ** 2
    pitch[pitch > 8] = 0.09
    return np.sqrt(g2), pitch


def peel(skin, under, where="body", amount=0.2, scale=30.0, stretch=0.5, jag=0.07, seed=0,
         keep_off=("number panel", "engine cover panel"), shadow=0.25, shadow_dark=0.5):
    """Tear the paint on `where` (Skin set) open to show `under` (from Skin.keep()).
    amount: the share torn open; scale: the tears' size in cm; stretch < 1 draws them out
    along the car; jag: how ragged their outline is. keep_off: parts never torn (the game
    draws the number and the name there); tears thin out as they near them, so none is cut
    straight along their border. shadow: the width in cm of the hard shadow inside every
    tear's edge (0 for none); shadow_dark: how much it darkens the paint underneath.
    Returns the torn weight per texel (for checks)."""
    t0 = time.time()
    c = skin.canvas("Skin")
    ids = skin._ids(where).get("Skin", [])
    idx, m = skin._mask("Skin", ids, None, c)
    pos = c.pos[idx]
    H = tears(pos, amount, scale, seed, stretch, jag)
    off = [i for i, inst in enumerate(skin.parts.instances) if inst["mesh"] == "Skin" and inst["name"] in keep_off]
    if off:
        from tool import coverage
        locked = coverage.load(skin.parts, "Skin", c.w, c.h).get(off).reshape(-1)[idx]
        margin = 12.0
        d, _ = cKDTree(pos[locked > 0.5][::3]).query(pos, distance_upper_bound=margin, workers=-1)
        H = H - 0.35 * (1 - np.minimum(d, margin) / margin) ** 2
        H = np.where(locked > 0.5, np.minimum(H, -0.01), H)
    g, pitch = gradient(H, idx, c.pos, c.w, c.w * c.h)
    sd = H / np.maximum(g, 1e-6)  # cm from the edge, + inside a tear
    hole = np.clip(0.5 + sd / pitch, 0, 1)  # a one-texel ramp across the edge
    shade = np.clip(0.5 + (shadow - sd) / pitch, 0, 1) * hole if shadow > 0 else np.zeros_like(hole)
    for k in ("colour", "rough", "metal", "coat"):
        layer = getattr(c, k)
        h = hole[:, None] if k == "colour" else hole
        u = under[k][idx]
        if k == "colour":
            u = u * (1 - shadow_dark * shade)[:, None]
        layer[idx] = layer[idx] * (1 - h) + u * h
    c.touched[idx] = True
    torn = float((hole * m).sum() / max(m.sum(), 1))
    skin.notes.append(f"peel on {where}: {torn:.0%} of it torn open ({time.time() - t0:.0f} s)")
    out = np.zeros(c.w * c.h, np.float32)
    out[idx] = hole
    return out
