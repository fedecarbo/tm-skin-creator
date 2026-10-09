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


def area(xy, width, height, n=8):
    """How much of each pixel the triangles cover together, 0..1, (h, w) float32. A pixel no triangle's edge
    crosses counts by its centre; one an edge crosses, by n x n samples, so an edge is anti-aliased to within
    about 1/(2n) wherever it runs. Overlapping triangles count once."""
    full = np.zeros(height * width, bool)
    bits = np.zeros(height * width, np.uint64)
    offs = (np.arange(n) + 0.5) / n - 0.5
    ox, oy = (o.ravel() for o in np.meshgrid(offs, offs))
    weight = np.left_shift(np.uint64(1), np.arange(n * n, dtype=np.uint64))
    lo = np.maximum(np.floor(xy.min(1) - 0.5).astype(np.int64), 0)
    hi = np.ceil(xy.max(1) - 0.5).astype(np.int64)
    hi[:, 0] = np.minimum(hi[:, 0], width - 1)
    hi[:, 1] = np.minimum(hi[:, 1], height - 1)
    a, b, c = xy[:, 0], xy[:, 1], xy[:, 2]
    turn = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    for t in np.flatnonzero((np.abs(turn) > 1e-12) & (hi[:, 0] >= lo[:, 0]) & (hi[:, 1] >= lo[:, 1])):
        (x0, y0), (x1, y1) = lo[t], hi[t]
        px, py = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        px, py = px.ravel(), py.ravel()
        corner = xy[t]
        e, nrm = [], []
        for k in range(3):  # each edge's inward unit normal, and the pixels' centres' distance in from it
            p, q = corner[k], corner[(k + 1) % 3]
            d = (q - p) / np.linalg.norm(q - p)
            nk = np.array([-d[1], d[0]]) * np.sign(turn[t])
            nrm.append(nk)
            e.append((px - p[0]) * nk[0] + (py - p[1]) * nk[1])
        e = np.stack(e, 1)
        crossed = (np.abs(e) < 0.7072).any(1) & (e > -0.7072).all(1)  # an edge's line passes through the pixel
        rows = (py - 0.5).astype(np.int64) * width + (px - 0.5).astype(np.int64)
        full[rows[(e >= 0).all(1) & ~crossed]] = True
        if crossed.any():
            nrm = np.stack(nrm)
            at = e[crossed][:, :, None] + (nrm[:, 0, None] * ox + nrm[:, 1, None] * oy)[None]
            inside = (at >= 0).all(1)
            bits[rows[crossed]] |= (inside * weight).sum(1, dtype=np.uint64)
    out = np.bitwise_count(bits).astype(np.float32) / (n * n)
    out[full] = 1
    return out.reshape(height, width)


def coverage(xy, width, height, flags):
    """How many triangles cover each pixel centre, and the OR of their flags.

    xy as in rasterise; flags (T,) small ints. Returns count (h, w) int16 and flags (h, w) uint8.
    Used to find texels that several parts of the car share (mirrored and repeated pieces)."""
    count = np.zeros((height, width), np.int16)
    bits = np.zeros((height, width), np.uint8)
    lo = np.maximum(np.floor(xy.min(1) - 0.5).astype(np.int64), 0)
    hi = np.ceil(xy.max(1) - 0.5).astype(np.int64)
    hi[:, 0] = np.minimum(hi[:, 0], width - 1)
    hi[:, 1] = np.minimum(hi[:, 1], height - 1)
    a, b, c = xy[:, 0], xy[:, 1], xy[:, 2]
    area = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    for t in np.flatnonzero((np.abs(area) > 1e-12) & (hi[:, 0] >= lo[:, 0]) & (hi[:, 1] >= lo[:, 1])):
        x0, y0 = lo[t]
        x1, y1 = hi[t]
        px = np.arange(x0, x1 + 1) + 0.5
        py = np.arange(y0, y1 + 1)[:, None] + 0.5
        (ax, ay), (bx, by), (cx, cy) = a[t], b[t], c[t]
        w0 = ((bx - px) * (cy - py) - (by - py) * (cx - px)) / area[t]
        w1 = ((cx - px) * (ay - py) - (cy - py) * (ax - px)) / area[t]
        inside = (w0 >= 0) & (w1 >= 0) & (1 - w0 - w1 >= 0)
        region = (slice(y0, y1 + 1), slice(x0, x1 + 1))
        count[region] += inside
        bits[region] |= np.where(inside, flags[t], 0).astype(np.uint8)
    return count, bits


def interpolate(tri, bary, corner_values):
    """corner_values: (T, 3, k). Returns (h, w, k), zero where no triangle covers the pixel."""
    out = np.zeros(tri.shape + corner_values.shape[2:], np.float32)
    covered = tri >= 0
    v = corner_values[tri[covered]]  # (n, 3, k)
    out[covered] = (bary[covered][..., None] * v).sum(1)
    return out


def fill_holes(image, mask, near=None):
    """Fill every texel outside the UV islands with the colour of the nearest painted texel.

    Covered texels keep their value. Each island's edge colour spreads outwards until it meets
    the next island's, so the game's filtering and the mips never blend one island's colour into
    another's at a seam. (An average of the surrounding islands, tried first, put a fringe of
    mixed colour along every seam where two parts meet.)

    near: each texel's nearest covered texel as a flat index, when the caller has it already
    (nearest(mask); the paint box's Canvas keeps it): finding it is most of the cost, 0.9 s at 4096².
    """
    image = np.asarray(image, np.float32)
    if near is None:
        near = nearest(mask)
    return image.reshape(near.size, *image.shape[2:])[near].reshape(image.shape)


def nearest(mask):
    """Each texel's nearest texel inside mask (itself when inside), as a flat index (int32)."""
    from scipy import ndimage
    iy, ix = ndimage.distance_transform_edt(~mask, return_distances=False, return_indices=True)
    return (iy * mask.shape[1] + ix).astype(np.int32).ravel()
