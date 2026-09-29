"""TSC_WindTunnel, concept A: Flow Paint.

A test car in raw matte carbon, sprayed with fluorescent flow-visualisation paint and sent out for
a lap: the paint pools where the air meets the car (the nose's tip, the lips over each sidepod
inlet, the cockpit's front rim) and the air drags it back into fine
streaks, dense near each source and thinning to nothing, so the tail, the lower sides and the
deck's rear stay black.

How the streaks follow the air: a noise drawn round the car's long axis (an axis at Y0 cm up the
car's middle), fine across the flow (the angle round the axis) and long along it (z), so each
streak runs back at a steady angle round the body, fanning out where the body widens and closing
in where it narrows, as the air does. A density per source (1 on the source, dying away behind
it) sets how much of the noise is paint: all of it on the source, only its peaks far behind, so
the streaks taper and break up on their own, every edge crisp.
"""

import numpy as np

from tool import noise, shapes
from tool.noise import smoothstep as ss

CARBON = "#151618"  # the raw matte carbon test car, about 72 %
PAINT = "#d6f53a"   # the fluorescent flow paint, about 25 %
THIN = "#a9c62e"    # the same paint worn thin, on the faint trailing streaks

Y0 = 22.0   # the height of the axis the flow is drawn round (cm)
R0 = 50.0   # cm per radian round the axis, for the streaks' spacing
ACROSS = 1.4  # the noise's cell across the flow (at R0), cm: hair-fine
ALONG = 95.0  # ... and along it, cm: long

# the body panels the paint lands on: never the sidepod inlets, the number and name panels, the
# side skirts, the tail, the diffuser or the wing pylons
PAINTED = ["body shell", "nose tip", "nose panel", "nose fin", "cockpit surround", "sidepod top",
           "rear flank", "engine cover|part", "rear quarter panel", "tail corner"]

# the combed noise's quantiles (0, 10, ..., 100 %), measured on the body, to turn a share of paint
# into a threshold
_Q = np.array([0.176, 0.379, 0.416, 0.443, 0.467, 0.49, 0.513, 0.538, 0.567, 0.603, 0.801])
MOST = 0.88  # the pools' share: fine dark lines stay in them, as the air combs the wet paint


def _polar(p):
    """The angle round the flow's axis (0 on top, + to the car's left) and the distance from it."""
    x, y = p[:, 0], p[:, 1] - Y0
    return np.arctan2(x, y), np.hypot(x, y)


def _comb(phi, z, dash, seed=11):
    """The paint's streaky texture, about 0..1, at an angle round the axis and a length: fine
    across the flow, long along it, like a comb dragged through wet paint; the finer streaks
    shorter, all meandering a little together, staggered so they don't end in rows. `dash` (per
    point) breaks the streaks into dashes where the paint runs thin."""
    u = phi * R0 / ACROSS
    v = z / ALONG
    one = np.full_like(u, 0.5)
    u = u + 0.35 * (noise.value(np.stack([u * 0.06, v * 0.3, one + 3], 1), seed + 5) - 0.5)
    lay = lambda k, fu, fv: noise.value(np.stack([u * fu + 7.1 * k, v * fv + 0.37 * u * fu, one + k], 1), seed + k)
    return 0.58 * lay(0, 1.0, 1.0) + 0.42 * lay(1, 2.1, 1.7) + dash * (lay(2, 1.0, 6.0) - 0.5)


def combed(p):
    phi, _ = _polar(p)
    return _comb(phi, p[:, 2], 0.0)


def ragged(p, seed=23):
    """-0.5..0.5, changing every few cm round the body: a brushed edge."""
    phi, _ = _polar(p)
    u = phi * R0 / 5.0
    return noise.value(np.stack([u, p[:, 2] / 30, np.full_like(u, 0.5)], 1), seed) - 0.5


def _wake(d, pool, fall):
    """1 on a source and `pool` cm behind it, then dying away over `fall` cm; nothing ahead."""
    return np.where(d < pool, 1.0, np.exp(-np.maximum(d - pool, 0) / fall)) * ss(-1.0, 0.0, d)


def density(p, n):
    """How much of the surface the paint covers (0..1: pooled on the sources, dragged back) and
    where it's solid (the edge the air meets first)."""
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    ax = np.abs(x)
    phi, r = _polar(p)
    aphi = np.abs(phi)
    j = 4.0 * ragged(p)  # the pools' front edges, brushed on
    behind_cockpit = 1 - (1 - ss(20, 25, ax)) * ss(30, 40, -z)  # nothing on the headrest
    ahead = 1 - 0.4 * ss(22, 30, ax)  # the rim pools only ahead of the opening; its sides take streaks
    # each source: how far behind its front edge, its pool's depth, how far its streaks reach, its
    # solid edge's depth (0: none, its streaks start raggedly), where round the body it is, how much
    # of it pools there, and where its solid edge is
    sources = (
        (214 - z, 15, 55, 12, 1 - ss(0.82, 0.95, aphi), 1, 1),  # the nose's tip
        (92 - 0.25 * ax + j - z, 4, 50, 2.5, (1 - ss(0.66, 0.76, aphi)) * behind_cockpit, ahead, ax < 26),  # the cockpit's front rim
        (13 + j - z, 6, 48, 3, ss(0.88, 0.97, aphi) * (1 - ss(1.38, 1.48, aphi)), 1, 1),  # the lips over the inlets
    )
    # the streaks only where the surface faces out from the axis (they'd smear elsewhere), above
    # the lower sides, dying out behind the sidepods (running on down the deck's sides they read as
    # claw marks from the chase cameras, Claude's review 2026-09-29)
    radial = (n[:, 0] * x + n[:, 1] * (y - Y0)) / np.maximum(r, 1e-3)
    keep = ss(0.2, 0.5, radial) * ss(36, 40, y) * ss(-115, -70, z)
    # none where the body turns away behind (the air leaves it there; streaks on the sidepods'
    # tapering backs read as drips from the chase cameras)
    keep = keep * (1 - ss(0.12, 0.3, -n[:, 2]))
    dens = np.zeros(len(p), np.float32)
    solid = np.zeros(len(p), np.float32)
    for d, pool, fall, edge, lateral, much, solid_at in sources:
        w = _wake(d, pool, fall) * (ss(0, 8, d) if edge == 0 else 1)
        dens = np.maximum(dens, lateral * w * keep * much)
        solid = np.maximum(solid, (lateral > 0.95) * (d > -1) * (d < edge) * solid_at)
    return dens, solid


def flow(p, n):
    """Signed distance into the paint in cm: the texture over its threshold, divided by how fast
    the texture changes along the surface, so every edge is equally crisp, the streaks' tips too."""
    dens, solid = density(p, n)
    share = np.maximum(np.minimum(dens ** 0.7, MOST), solid)
    t = np.interp(1 - share, np.linspace(0, 1, 11), _Q)
    dash = 0.5 * (1 - share)  # the thinner the paint, the more its streaks break up
    phi, r = _polar(p)
    z = p[:, 2]
    c = _comb(phi, z, dash)
    h = 0.1
    across = (_comb(phi + h / np.maximum(r, 5.0), z, dash) - c) / h
    along = (_comb(phi, z + h, dash) - c) / h
    return (c - t) / np.maximum(np.hypot(across, along), 0.02)


FLOW = shapes.field(flow)
# where the paint has been dragged furthest, it's thinner and a little deeper in tone
THINNING = shapes.Zone(lambda p, n: 1 - ss(0.10, 0.30, density(p, n)[0]))

WORDS = "I want you to come up with a concept to build a car"


def design(s):
    s.clay()
    s.step("Raw carbon", "The whole body in raw matte carbon, a test car with no clear coat.", words=WORDS)
    s.paint("body", "carbon", colour=CARBON)

    s.step("Flow paint", "Fluorescent flow paint pooled on the nose's tip, the lips over the sidepod inlets, "
           "and the cockpit's front rim, dragged back by the air into fine streaks "
           "that thin out towards the tail.", words=WORDS)
    s.paint(PAINTED, "satin", colour=PAINT, zone=FLOW)
    s.paint(PAINTED, "satin", colour=THIN, zone=FLOW & THINNING)

    s.step("Wheels and inner car", "The wheels and the inner car in the same dark carbon black.", words=WORDS)
    s.paint("wheels", "satin", colour=CARBON)
    s.paint("inner", "satin", colour=CARBON)
