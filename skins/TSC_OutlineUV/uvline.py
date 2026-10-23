"""The user's idea (2026-10-23), as a test: an outline drawn inside each part straight on its shape in the UV map. Each
part's texels; the distance in the map (each texel's cm, its island's scale) from its edge's texels, half the width
from an edge meeting another of the parts, the whole from one meeting none; an edge where the map is cut while the
part carries on (another island of the same part right there on the car) is no edge. Nothing measured along the
car's surface. The plates the game letters on are the engine cover's. A piece lying on the body (a fastener's ring)
takes the line of the texel beneath it."""

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

from tool import bake, course, coverage, parts as parts_mod, shapes, surface, uvmap
from tool.noise import smoothstep

N = 4096
NEAR = 0.5  # cm on the car: another part's edge texel this near an edge texel makes it a seam


def outline_uv(parts, width=2.5, soft=shapes.SOFT, merged=("number panel", "engine cover panel")):
    b = bake.bake("Skin", N, N)
    tri = b["tri"].reshape(-1)
    pos = b["position"].reshape(-1, 3).astype(np.float64)
    label, density, _ = uvmap.islands("Skin")
    pitch = np.where(tri >= 0, 1.0 / np.maximum(density[label[np.maximum(tri, 0)]] * N, 1e-9), np.inf)
    P = parts_mod.load()
    cov = coverage.load(P, "Skin", N, N)
    share = []
    for part in parts:
        ids = course._named(part)[2]
        if "engine cover" in part:
            ids = ids + [i for m in merged for i in P.select(m)]
        share.append(cov.share(ids).reshape(-1))
    share = np.stack(share)
    owner = np.where(share.max(0) >= 0.5, share.argmax(0), -1)
    owner[tri < 0] = -1
    grid = owner.reshape(N, N)
    island = np.where(tri >= 0, label[np.maximum(tri, 0)], -1).reshape(N, N)
    # every part's edge texels: an own texel with a 4-neighbour not its own (another part, another island, nothing)
    edge = np.zeros((N, N), bool)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        o = np.roll(np.roll(grid, dy, 0), dx, 1)
        i2 = np.roll(np.roll(island, dy, 0), dx, 1)
        edge |= (grid >= 0) & ((o != grid) | (i2 != island))
    E = np.flatnonzero(edge.reshape(-1))
    tree = cKDTree(pos[E])
    kind = np.zeros(len(E), np.int8)  # 0 free, 1 seam, 2 a cut in the map
    for j, nb in enumerate(tree.query_ball_point(pos[E], NEAR, workers=-1)):
        nb = E[np.asarray(nb, int)]
        other = owner[nb] != owner[E[j]]
        if (other & (owner[nb] >= 0)).any():
            kind[j] = 1
        elif ((owner[nb] == owner[E[j]]) & (island.reshape(-1)[nb] != island.reshape(-1)[E[j]])).any():
            kind[j] = 2
    weight = np.zeros(N * N, np.float32)
    for k in range(len(parts)):
        mine = np.flatnonzero(owner == k)
        if not len(mine):
            continue
        r, c = mine // N, mine % N
        pad = int(width / pitch[mine].min()) + 4
        r0, r1, c0, c1 = max(r.min() - pad, 0), min(r.max() + pad + 1, N), max(c.min() - pad, 0), min(c.max() + pad + 1, N)
        sub = lambda a: a.reshape(N, N)[r0:r1, c0:c1]
        ek = E[owner[E] == k]
        line = np.full((r1 - r0, c1 - c0), -np.inf)
        for kd, half in ((1, width / 2), (0, width)):
            src = np.zeros((r1 - r0, c1 - c0), bool)
            e = ek[kind[owner[E] == k] == kd]
            src[e // N - r0, e % N - c0] = True
            if not src.any():
                continue
            d = ndimage.distance_transform_edt(~src) * sub(pitch)
            line = np.maximum(line, half - d)
        w = smoothstep(-soft / 2, soft / 2, line).astype(np.float32)
        m = sub(owner == k)
        weight.reshape(N, N)[r0:r1, c0:c1][m] = w[m]
    # a piece lying on the body: the line of the texel beneath
    S = surface.load()
    on = np.flatnonzero(tri >= 0)
    piece = S.piece[S.face[tri[on]]]
    lies = S.lies_on()[piece] >= 0
    if lies.any():
        base = on[~lies & (owner[on] >= 0)]
        _, j = cKDTree(pos[base]).query(pos[on[lies]], workers=-1)
        weight[on[lies]] = weight[base[j]]
    lin = np.flatnonzero(weight > 0.002)
    return course.Course._matched(pos[lin], weight[lin], label="the outline drawn in the map")
