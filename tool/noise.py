"""Noise in 3D, for patterns drawn straight on the car's surface (no seams, no stretching).

Every function takes points p as an (n, 3) float array in cm and returns (n,) float32s. They're
plain numpy, so a whole texture's worth of points (millions) goes through in seconds, CHUNK points at a
time (`chunked`): each point's value is its own, so the chunks change nothing but the memory. Where the
computer has a graphics chip the tool uses (tool/gpu.py), the same arithmetic runs there as one kernel
(METAL, below): the same bits, in milliseconds.

    value(p, seed)          smooth value noise, 0..1, one cycle per ~1 cm
    value(p, seed, smooth=False)  the same, straight between the lattice points: faceted,
                            so a threshold of it has angular edges (torn paper, vinyl)
    fbm(p, octaves, seed)   layered noise, 0..1, the usual "natural" look
    worley(p, seed)         distance to the nearest random cell point, 0..~1 (cells ~1 cm)
    cell_id(p, seed)        the id of the nearest random cell point (for colouring cells)
Scale the points to change the size: fbm(p / 20) has features about 20 cm across.
"""

import functools

import numpy as np

from tool import gpu

CHUNK = 1 << 20  # points at a time: a whole map's 16 million at once held gigabytes of temporaries


def chunked(fn):
    """fn(p, ...), a function of each point alone, worked CHUNK points at a time."""
    @functools.wraps(fn)
    def run(p, *a, **k):
        p = np.asarray(p, np.float32)
        if len(p) <= CHUNK:
            return fn(p, *a, **k)
        out = [fn(p[i:i + CHUNK], *a, **k) for i in range(0, len(p), CHUNK)]
        return tuple(map(np.concatenate, zip(*out))) if isinstance(out[0], tuple) else np.concatenate(out)
    return run


def _seed(seed):
    return (int(seed) * 1013904223) & 0xFFFFFFFF


def _hash(ix, iy, iz, seed):
    """A pseudo-random 0..1 per integer lattice point, in 32-bit arithmetic that wraps."""
    u = np.uint32
    h = (ix.astype(u) * u(374761393) + iy.astype(u) * u(668265263)
         + iz.astype(u) * u(2147483647) + u(_seed(seed)))
    h = (h ^ (h >> u(13))) * u(1274126177)
    h = h ^ (h >> u(16))
    return (h & u(0xFFFFFF)).astype(np.float32) / 0xFFFFFF


@chunked
def value(p, seed=0, smooth=True):
    if gpu.ON:
        return _layers(p, [(1.0, 0.0, 1.0, seed)], 1.0, smooth)
    i = np.floor(p)
    f = p - i
    if smooth:
        f = f * f * (3 - 2 * f)  # smoothstep
    ix, iy, iz = (i[:, k].astype(np.int32) for k in range(3))
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


@chunked
def fbm(p, octaves=4, seed=0, gain=0.5, lacunarity=2.0):
    layers, amp, total = [], 1.0, 0.0
    for k in range(octaves):
        layers.append((lacunarity**k, k * 17.3, amp, seed + k))
        total += amp
        amp *= gain
    if gpu.ON:
        return _layers(p, layers, total, True)
    out = np.zeros(len(p), np.float32)
    for scale, shift, amp, s in layers:
        out += amp * value(p * scale + shift, s)
    return out / total


def _cells(p, seed, kind):
    """The nearest and second nearest of the random points (one per unit cell): (f1, f2), their distances; with kind
    "id", (the nearest's squared distance, its cell's 0..1 id). Each offset is taken from the point's own cell corner,
    where float32 keeps its precision."""
    if gpu.ON:
        out = {"a": ((len(p),), np.float32), "b": ((len(p),), np.float32)}
        seeds = np.uint32([_seed(seed + k) for k in range(4)])
        return tuple(gpu.run("cells", METAL, CELLS, {"p": p, "n": np.uint32([len(p), kind == "id"]), "s": seeds}, out, len(p)))
    i = np.floor(p)
    f = p - i
    i = i.astype(np.int32)
    a = np.full(len(p), 9.0, np.float32)
    b = np.full(len(p), 9.0, np.float32)
    for dz in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                cx, cy, cz = i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz
                ox = (dx + _hash(cx, cy, cz, seed)) - f[:, 0]
                oy = (dy + _hash(cx, cy, cz, seed + 1)) - f[:, 1]
                oz = (dz + _hash(cx, cy, cz, seed + 2)) - f[:, 2]
                d = (ox * ox + oy * oy) + oz * oz
                if kind == "id":
                    closer = d < a
                    b = np.where(closer, _hash(cx, cy, cz, seed + 3), b)
                    a = np.where(closer, d, a)
                    continue
                d = np.sqrt(d)
                closer = d < a
                b = np.where(closer, a, np.minimum(b, d))
                a = np.where(closer, d, a)
    return a, b


@chunked
def worley(p, seed=0, second=False):
    """Distance to the nearest random point (one per unit cell). second=True gives the second
    nearest too: (f1, f2). f2 - f1 outlines the cells."""
    f1, f2 = _cells(p, seed, "distance")
    return (f1, f2) if second else f1


@chunked
def cell_id(p, seed=0):
    """A 0..1 random value per Voronoi cell (the cell of the nearest random point)."""
    return _cells(p, seed, "id")[1]


def smoothstep(edge0, edge1, x):
    t = np.clip((x - edge0) / (edge1 - edge0), 0, 1)
    return t * t * (3 - 2 * t)


def _layers(p, layers, total, smooth):
    """value noise's layers on the graphics chip: for each (scale, shift, amp, seed) amp * value(p * scale + shift),
    summed, over total."""
    c = [np.float32(x) for scale, shift, amp, _ in layers for x in (scale, shift, amp)] + [np.float32(total)]
    return gpu.run("layers", METAL, LAYERS, {"p": p, "n": np.uint32([len(p), len(layers), smooth]), "c": np.float32(c),
                                             "s": np.uint32([_seed(s) for *_, s in layers])},
                   {"v": ((len(p),), np.float32)}, len(p))[0]


# The numpy above, operation for operation, on the graphics chip (tool/gpu.py)
METAL = r'''
inline float lattice(int ix, int iy, int iz, uint s) {
    uint h = uint(ix) * 374761393u + uint(iy) * 668265263u + uint(iz) * 2147483647u + s;
    h = (h ^ (h >> 13)) * 1274126177u;
    h = h ^ (h >> 16);
    return float(h & 0xFFFFFFu) / 16777215.0f;
}
'''
LAYERS = r'''
if (i >= n[0]) return;
float out = 0.0f;
for (uint k = 0; k < n[1]; k++) {
    float sc = c[3 * k], sh = c[3 * k + 1];
    float3 q = float3(p[3 * i] * sc + sh, p[3 * i + 1] * sc + sh, p[3 * i + 2] * sc + sh);
    float3 fl = floor(q), f = q - fl;
    if (n[2]) f = f * f * (3.0f - 2.0f * f);
    int3 j = int3(fl);
    float x = 0.0f;
    for (int dz = 0; dz < 2; dz++) {
        float wz = dz ? f.z : 1.0f - f.z;
        for (int dy = 0; dy < 2; dy++) {
            float wy = dy ? f.y : 1.0f - f.y;
            for (int dx = 0; dx < 2; dx++) {
                float wx = dx ? f.x : 1.0f - f.x;
                x = x + wx * wy * wz * lattice(j.x + dx, j.y + dy, j.z + dz, s[k]);
            }
        }
    }
    out = out + c[3 * k + 2] * x;
}
v[i] = out / c[3 * n[1]];
'''
CELLS = r'''
if (i >= n[0]) return;
float3 q = float3(p[3 * i], p[3 * i + 1], p[3 * i + 2]), fl = floor(q), f = q - fl;
int3 j = int3(fl);
float x = 9.0f, y = 9.0f;
for (int dz = -1; dz < 2; dz++) for (int dy = -1; dy < 2; dy++) for (int dx = -1; dx < 2; dx++) {
    int cx = j.x + dx, cy = j.y + dy, cz = j.z + dz;
    float ox = (float(dx) + lattice(cx, cy, cz, s[0])) - f.x;
    float oy = (float(dy) + lattice(cx, cy, cz, s[1])) - f.y;
    float oz = (float(dz) + lattice(cx, cy, cz, s[2])) - f.z;
    float d = (ox * ox + oy * oy) + oz * oz;
    if (n[1]) {
        if (d < x) { x = d; y = lattice(cx, cy, cz, s[3]); }
        continue;
    }
    d = precise::sqrt(d);
    if (d < x) { y = x; x = d; } else y = min(y, d);
}
a[i] = x;
b[i] = y;
'''
