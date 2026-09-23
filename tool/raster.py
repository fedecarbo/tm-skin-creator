"""Triangle rasteriser shared by the UV bakes and the quick preview renders.

Pixel centres sit at (col + 0.5, row + 0.5). A pixel belongs to a triangle when its centre
lies inside it. With depth, the nearest triangle wins; without, the last one drawn wins.
"""

import numpy as np


def rasterise(xy, width, height, depth=None):
    """xy: (T, 3, 2) corner positions in pixels (x = column, y = row).
    depth: optional (T, 3) per-corner depth, smaller = nearer.

    Returns tri (h, w) int32, the triangle id per pixel or -1, and bary (h, w, 3) float32,
    the barycentric weights of the corners at each covered pixel.
    """
    tri = np.full((height, width), -1, np.int32)
    bary = np.zeros((height, width, 3), np.float32)
    zbuf = np.full((height, width), np.inf, np.float32) if depth is not None else None
    lo = np.floor(xy.min(1) - 0.5).astype(np.int64)
    hi = np.ceil(xy.max(1) - 0.5).astype(np.int64)
    lo = np.maximum(lo, 0)
    hi[:, 0] = np.minimum(hi[:, 0], width - 1)
    hi[:, 1] = np.minimum(hi[:, 1], height - 1)
    a, b, c = xy[:, 0], xy[:, 1], xy[:, 2]
    area = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    for t in np.flatnonzero((np.abs(area) > 1e-12) & (hi[:, 0] >= lo[:, 0]) & (hi[:, 1] >= lo[:, 1])):
        x0, y0 = lo[t]
        x1, y1 = hi[t]
        px = np.arange(x0, x1 + 1) + 0.5
        py = np.arange(y0, y1 + 1)[:, None] + 0.5
        ax, ay = a[t]
        bx, by = b[t]
        cx, cy = c[t]
        w0 = ((bx - px) * (cy - py) - (by - py) * (cx - px)) / area[t]
        w1 = ((cx - px) * (ay - py) - (cy - py) * (ax - px)) / area[t]
        w2 = 1 - w0 - w1
        inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not inside.any():
            continue
        region = (slice(y0, y1 + 1), slice(x0, x1 + 1))
        if zbuf is not None:
            z = w0 * depth[t, 0] + w1 * depth[t, 1] + w2 * depth[t, 2]
            inside &= z < zbuf[region]
            zbuf[region][inside] = z[inside]
        tri[region][inside] = t
        bary[region][inside] = np.stack([w0, w1, w2], -1)[inside]
    return tri, bary


def interpolate(tri, bary, corner_values):
    """corner_values: (T, 3, k). Returns (h, w, k), zero where no triangle covers the pixel."""
    out = np.zeros(tri.shape + corner_values.shape[2:], np.float32)
    covered = tri >= 0
    v = corner_values[tri[covered]]  # (n, 3, k)
    out[covered] = (bary[covered][..., None] * v).sum(1)
    return out


def fill_holes(image, mask):
    """Fill every texel outside the UV islands from the nearest painted ones ("push-pull").

    Covered texels keep their value. Empty ones take the average of the covered texels in the
    smallest surrounding 2^k block, so island edges bleed outwards smoothly. That stops seams
    showing in the mips, and the flat fill compresses well. Works on power-of-two sizes.
    """
    squeeze = image.ndim == 2
    if squeeze:
        image = image[..., None]
    w = mask.astype(np.float32)[..., None]
    pyramid = [(image.astype(np.float32) * w, w)]
    while min(pyramid[-1][1].shape[:2]) > 1:
        c, n = pyramid[-1]
        h2, w2 = c.shape[0] // 2, c.shape[1] // 2
        pool = lambda a: a.reshape(h2, 2, w2, 2, a.shape[2]).sum((1, 3))
        pyramid.append((pool(c), pool(n)))
    c, n = pyramid[-1]
    filled = c / np.maximum(n, 1e-9)
    for c, n in reversed(pyramid[:-1]):
        up = np.repeat(np.repeat(filled, 2, 0), 2, 1)[: c.shape[0], : c.shape[1]]
        filled = np.where(n > 0, c / np.maximum(n, 1e-9), up)
    return filled[..., 0] if squeeze else filled
