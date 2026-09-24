"""Noise in 3D, for patterns drawn straight on the car's surface (no seams, no stretching).

Every function takes points p as an (n, 3) float array in cm and returns (n,) floats. They're
plain numpy, so a whole texture's worth of points (millions) goes through in seconds.

    value(p, seed)          smooth value noise, 0..1, one cycle per ~1 cm
    fbm(p, octaves, seed)   layered noise, 0..1, the usual "natural" look
    worley(p, seed)         distance to the nearest random cell point, 0..~1 (cells ~1 cm)
    cell_id(p, seed)        the id of the nearest random cell point (for colouring cells)
Scale the points to change the size: fbm(p / 20) has features about 20 cm across.
"""

import numpy as np


def _hash(ix, iy, iz, seed):
    """A pseudo-random 0..1 per integer lattice point."""
    h = (ix.astype(np.int64) * 374761393 + iy.astype(np.int64) * 668265263
         + iz.astype(np.int64) * 2147483647 + int(seed) * 1013904223) & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFFFF).astype(np.float32) / 0xFFFFFF


def value(p, seed=0):
    p = np.asarray(p, np.float32)
    i = np.floor(p)
    f = p - i
    f = f * f * (3 - 2 * f)  # smoothstep
    ix, iy, iz = (i[:, k].astype(np.int64) for k in range(3))
    fx, fy, fz = f[:, 0], f[:, 1], f[:, 2]
    out = np.zeros(len(p), np.float32)
    for dz in (0, 1):
        wz = fz if dz else 1 - fz
        for dy in (0, 1):
            wy = fy if dy else 1 - fy
            for dx in (0, 1):
                wx = fx if dx else 1 - fx
                out += wx * wy * wz * _hash(ix + dx, iy + dy, iz + dz, seed)
    return out


def fbm(p, octaves=4, seed=0, gain=0.5, lacunarity=2.0):
    p = np.asarray(p, np.float32)
    out = np.zeros(len(p), np.float32)
    amp, total = 1.0, 0.0
    for k in range(octaves):
        out += amp * value(p * lacunarity**k + k * 17.3, seed + k)
        total += amp
        amp *= gain
    return out / total


def worley(p, seed=0, second=False):
    """Distance to the nearest random point (one per unit cell). second=True gives the second
    nearest too: (f1, f2). f2 - f1 outlines the cells."""
    p = np.asarray(p, np.float32)
    i = np.floor(p).astype(np.int64)
    f1 = np.full(len(p), 9.0, np.float32)
    f2 = np.full(len(p), 9.0, np.float32)
    for dz in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                cx, cy, cz = i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz
                px = cx + _hash(cx, cy, cz, seed)
                py = cy + _hash(cx, cy, cz, seed + 1)
                pz = cz + _hash(cx, cy, cz, seed + 2)
                d = np.sqrt((px - p[:, 0]) ** 2 + (py - p[:, 1]) ** 2 + (pz - p[:, 2]) ** 2)
                closer = d < f1
                f2 = np.where(closer, f1, np.minimum(f2, d))
                f1 = np.where(closer, d, f1)
    return (f1, f2) if second else f1


def worley2(u, v, seed=0):
    """2D Worley: distance to the nearest random point, one per unit cell, for patterns laid
    flat on the surface (the 3D one makes balls that the surface slices through)."""
    u, v = np.asarray(u, np.float32), np.asarray(v, np.float32)
    iu, iv = np.floor(u).astype(np.int64), np.floor(v).astype(np.int64)
    zero = np.zeros_like(iu)
    best = np.full(len(u), 9.0, np.float32)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            cx, cy = iu + dx, iv + dy
            px = cx + _hash(cx, cy, zero, seed)
            py = cy + _hash(cx, cy, zero, seed + 1)
            best = np.minimum(best, np.sqrt((px - u) ** 2 + (py - v) ** 2))
    return best


def cell_id(p, seed=0):
    """A 0..1 random value per Voronoi cell (the cell of the nearest random point)."""
    p = np.asarray(p, np.float32)
    i = np.floor(p).astype(np.int64)
    best = np.full(len(p), 9.0, np.float32)
    ident = np.zeros(len(p), np.float32)
    for dz in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                cx, cy, cz = i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz
                px = cx + _hash(cx, cy, cz, seed)
                py = cy + _hash(cx, cy, cz, seed + 1)
                pz = cz + _hash(cx, cy, cz, seed + 2)
                d = (px - p[:, 0]) ** 2 + (py - p[:, 1]) ** 2 + (pz - p[:, 2]) ** 2
                closer = d < best
                best = np.where(closer, d, best)
                ident = np.where(closer, _hash(cx, cy, cz, seed + 3), ident)
    return ident


def smoothstep(edge0, edge1, x):
    t = np.clip((x - edge0) / (edge1 - edge0), 0, 1)
    return t * t * (3 - 2 * t)
