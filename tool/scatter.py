"""Copies of a picture sprinkled over the car, each its own small sticker and always whole
(Skin.scatter in tool/paintbox.py, whose docstring says how to call it)."""

import os
import time

import numpy as np
from PIL import Image
from scipy.spatial import cKDTree

from tool import finishes, looks, paint


def scatter(skin, image, where="body", size=8, spacing=None, turn="random", finish="gloss", zone=None, seed=None,
            min_facing=0.35, step_cm=2.5, min_landed=0.98):
    images = list(image) if isinstance(image, (list, tuple)) else [image]
    arrs = []
    for im in images:
        if isinstance(im, (str, bytes, os.PathLike)) or hasattr(im, "read"):
            im = Image.open(im)
        arrs.append(np.asarray(im.convert("RGBA"), np.float32) / 255)
    aspects = [a.shape[0] / a.shape[1] for a in arrs]
    tallest = max(aspects)
    sizes = (float(size), float(size)) if np.isscalar(size) else (float(size[0]), float(size[1]))
    spacing = spacing or sizes[1] * max(1.0, tallest) * 1.15
    rng = np.random.default_rng(skin.seed if seed is None else seed)
    fin = finishes.get(finish) if isinstance(finish, str) else finish
    z_axis = np.array([0, 0, 1.0], np.float32)
    placed = skipped = filled = 0
    t0 = time.time()
    for tset, ids in skin._ids(where).items():
        c = skin.canvas(tset)
        idx, m = skin._mask(tset, ids, zone, c)
        if not len(idx):
            continue
        pos, nrm = c.pos[idx], c.nrm[idx]
        # a coarse 3D grid over the parts' texels, so each copy only looks at its neighbourhood
        reach = sizes[1] * max(1.0, tallest) * 0.75
        cell = np.floor(pos / reach).astype(np.int64)
        cmin = cell.min(0)
        cell -= cmin
        dims = cell.max(0) + 1
        ckey = (cell[:, 0] * dims[1] + cell[:, 1]) * dims[2] + cell[:, 2]
        order = np.argsort(ckey, kind="stable")
        skeys = ckey[order]

        def neighbourhood(pt):
            pc = np.floor(pt / reach).astype(np.int64) - cmin
            sub = []
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        q = pc + (dx, dy, dz)
                        if (q < 0).any() or (q >= dims).any():
                            continue
                        k = (q[0] * dims[1] + q[1]) * dims[2] + q[2]
                        a, b = np.searchsorted(skeys, k), np.searchsorted(skeys, k, side="right")
                        if b > a:
                            sub.append(order[a:b])
            return np.concatenate(sub) if sub else None

        def frame(n, ang):
            up = z_axis - n * float(n @ z_axis)
            if np.linalg.norm(up) < 0.2:
                up = np.array([1.0, 0, 0], np.float32) - n * float(n[0])
            up /= np.linalg.norm(up)
            up = np.cos(ang) * up + np.sin(ang) * np.cross(n, up)
            return up, np.cross(up, n)

        def place(pt, kind, size_range):
            """Try to lay one copy near pt: nudged, turned and shrunk before giving up.
            Returns the centre it landed at, or None."""
            nonlocal placed
            sub = neighbourhood(pt)
            if sub is None:
                return None
            ps, ns = pos[sub], nrm[sub]
            nearest = np.argmin(((ps - pt) ** 2).sum(1))
            n = ns[nearest]
            n = n / max(np.linalg.norm(n), 1e-6)
            if turn == "random":
                ang0 = rng.uniform(0, 2 * np.pi)
            elif turn == "length":
                ang0 = 0.0
            else:
                ang0 = np.radians(float(turn))
            w_cm = rng.uniform(*size_range)
            arr = arrs[kind]
            centre = ps[nearest]
            # attempts: as is; nudged; turned (only when the turn is free); then smaller
            tries = [(0.0, 0.0, 1.0), (0.3, 0.0, 1.0), (0.3, 0.0, 1.0)]
            if turn == "random":
                tries += [(0.2, np.pi / 2, 1.0), (0.2, np.pi / 4, 1.0), (0.2, -np.pi / 4, 1.0)]
            tries += [(0.3, 0.0, 0.8), (0.3, np.pi / 2 if turn == "random" else 0.0, 0.65), (0.4, 0.0, 0.5)]
            for shift_k, dang, scale in tries:
                up, right = frame(n, ang0 + dang)
                if shift_k:
                    shift = rng.normal(0, shift_k * w_cm, 2)
                    cand = centre + shift[0] * right + shift[1] * up
                    cen = ps[np.argmin(((ps - cand) ** 2).sum(1))]
                else:
                    cen = centre
                w_try = w_cm * scale
                alpha, info = paint.project_points(ps, ns, np.ones(len(ps), bool), arr[..., 3], cen, right, up, w_try, n, min_facing)
                if info["landed"] >= min_landed and info["step_cm"] <= step_cm:
                    hit = np.flatnonzero(alpha > 0.002)
                    if not len(hit):
                        return None
                    col = np.stack([paint.project_points(ps, ns, np.ones(len(ps), bool), arr[..., k], cen, right, up, w_try, n, min_facing)[0][hit]
                                    for k in range(3)], 1)
                    gi = idx[sub[hit]]
                    mm = alpha[hit] * m[sub[hit]]
                    c.blend(gi, mm, col, np.full(len(gi), fin.roughness, np.float32), np.full(len(gi), fin.metalness, np.float32),
                            np.full(len(gi), fin.varnish, np.float32))
                    covered[sub[hit[alpha[hit] > 0.3]]] = True
                    placed += 1
                    return cen
            return None

        def kinds_for(points, done_points, done_kinds):
            """A picture per point: the one least used among the neighbours already decided
            (within 2.2 spacings, the nearer ones counting more), ties broken at random,
            so no picture bunches up."""
            if len(arrs) == 1:
                return [0] * len(points)
            all_pts = np.asarray(list(done_points) + list(points), np.float32)
            kinds = list(done_kinds) + [-1] * len(points)
            tree = cKDTree(all_pts)
            base = len(done_points)
            for i in range(len(points)):
                j = base + i
                counts = np.zeros(len(arrs))
                for q in tree.query_ball_point(all_pts[j], 2.2 * spacing):
                    if q != j and kinds[q] >= 0:
                        counts[kinds[q]] += 1 / (1 + np.linalg.norm(all_pts[q] - all_pts[j]) / spacing)
                best = np.flatnonzero(counts == counts.min())
                kinds[j] = int(rng.choice(best))
            return kinds[base:]

        covered = np.zeros(len(pos), bool)  # texels under a copy, for finding bare patches
        points = looks.surface_points(pos, spacing, seed=int(rng.integers(1 << 30)), regular=False, relax=8)
        kinds = kinds_for(points, [], [])
        centres, centre_kinds = [], []
        for pt, kind in zip(points, kinds):
            cen = place(pt, kind, sizes)
            if cen is None:
                skipped += 1
            else:
                centres.append(cen)
                centre_kinds.append(kind)
        # second pass: texels far from the outline of every copy are a bare patch; sprinkle
        # it again with smaller copies (it's bare because the full size didn't fit there)
        for _ in range(2):
            on = np.flatnonzero(covered)
            if not len(on):
                break
            sample = pos[rng.choice(len(pos), min(len(pos), 60_000), replace=False)]
            d, _ = cKDTree(pos[rng.choice(on, min(len(on), 120_000), replace=False)]).query(sample, workers=-1)
            bare = sample[d > 0.55 * spacing]  # a gap wider than one spacing
            if len(bare) < 50:
                break
            more = looks.surface_points(bare, 0.8 * spacing, seed=int(rng.integers(1 << 30)), regular=False, relax=4)
            more_kinds = kinds_for(more, centres, centre_kinds)
            small = (sizes[0] * 0.7, sizes[1] * 0.85)
            for pt, kind in zip(more, more_kinds):
                cen = place(pt, kind, small)
                if cen is not None:
                    centres.append(cen)
                    centre_kinds.append(kind)
                    filled += 1
        if skin.measure and tset == "Skin" and centres:
            skin.scattered.append({"op": skin._op, "spacing": spacing, **_spread(pos, covered, np.asarray(centres), spacing)})
    skin.notes.append(f"scatter on {where}: {placed} copies placed ({filled} of them smaller ones filling bare patches), "
                      f"{skipped} spots left bare for crossing a fold or an edge ({time.time() - t0:.0f} s)")


def _spread(pos, covered, centres, spacing):
    """How evenly the copies lie, for tool/checks.py: `uneven`, the spread of each copy's distance to
    its nearest neighbour over their mean; `bare`, the share of the surface further than 0.75
    spacings from every copy (the middle of a gap 1.5 spacings wide), and where along the car (z).
    With its own dice: the scatter's stay as they were."""
    out = {"uneven": 0.0, "bare": 0.0, "z": None}
    if len(centres) >= 8:
        d = cKDTree(centres).query(centres, k=2)[0][:, 1]
        out["uneven"] = float(d.std() / d.mean())
    on = np.flatnonzero(covered)
    if len(on):
        dice = np.random.default_rng(0)
        sample = pos[dice.choice(len(pos), min(len(pos), 60_000), replace=False)]
        d, _ = cKDTree(pos[dice.choice(on, min(len(on), 120_000), replace=False)]).query(sample, workers=-1)
        bare = sample[d > 0.75 * spacing]
        out["bare"] = len(bare) / len(sample)
        if len(bare):
            out["z"] = [round(float(bare[:, 2].max()), 1), round(float(bare[:, 2].min()), 1)]
    return out
