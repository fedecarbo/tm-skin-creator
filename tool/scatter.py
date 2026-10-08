"""Copies of a picture sprinkled over the body, each its own small sticker and always whole (Skin.scatter in
tool/paintbox.py, whose docstring says how to call it). Each copy is pressed onto the surface on a chart of its own
(tool/surface.py, cut along the model's crisp lines: no copy crosses one), whole on free room (tool/marks.py's sheet:
the parts' skin in the open air, off the game's panels, in the zone), and the copies are spaced along the surface: a
copy comes no nearer another than `spacing` cm measured along the car (the earlier copy's chart says how far), so two
on the two faces of a thin panel aren't neighbours and a bare patch is one along the skin. A copy that doesn't fit
where it's wanted is moved a little, turned when its turn is free, and shrunk before it's given up (TRIES); a second
pass fills any patch still bare, further than 0.75 spacings along the surface from every copy, with smaller copies."""

import os
import time

import numpy as np
from PIL import Image
from scipy.spatial import cKDTree

from tool import finishes, looks, marks

# How a copy that doesn't fit is tried again: how far it may move (in widths), how it's turned (degrees; only when
# its turn is free) and how it shrinks.
TRIES = ((0.0, 0, 1.0), (0.3, 0, 1.0), (0.3, 90, 1.0), (0.3, 45, 1.0), (0.3, -45, 1.0), (0.3, 0, 0.8), (0.3, 90, 0.65), (0.4, 0, 0.5))
BARE = 0.75  # spacings: a texel further than this along the surface from every copy is bare


def scatter(skin, image, where="body", size=8, spacing=None, turn="random", finish="gloss", zone=None, seed=None):
    images = list(image) if isinstance(image, (list, tuple)) else [image]
    pictures = []
    for im in images:
        if isinstance(im, (str, bytes, os.PathLike)) or hasattr(im, "read"):
            im = Image.open(im)
        pictures.append(marks.Picture(np.asarray(im.convert("RGBA"), np.float32) / 255, "picture", False, label="a copy"))
    tallest = max(p.high for p in pictures)
    sizes = (float(size), float(size)) if np.isscalar(size) else (float(size[0]), float(size[1]))
    spacing = spacing or sizes[1] * max(1.0, tallest) * 1.15
    rng = np.random.default_rng(skin.seed if seed is None else seed)
    fin = finishes.get(finish) if isinstance(finish, str) else finish
    placed = skipped = filled = 0
    inside = []  # the inner car's parts named: stickers go on the body
    t0 = time.time()
    for tset, ids in skin._ids(where).items():
        if tset != "Skin":
            inside += sorted({skin.parts.instances[i]["name"] for i in ids})
            continue
        c = skin.canvas(tset)
        panel = marks._Panel(skin, c, ids)
        if not len(panel.texels):
            continue
        free = panel.free(panel.texels, zone)
        if not free.any():
            continue
        pos = c.pos[panel.texels]
        free_texels, free_tree = panel.texels[free], cKDTree(pos[free])
        pitch = float(np.median(panel.pitch[panel.island]))
        idx, m = panel.mask()
        copies, centres, kinds = [], [], []  # each copy's (chart, its middle on the chart), its place on the car, its picture
        nearest = np.full(len(panel.texels), np.inf)  # how far each of the parts' texels is, along the surface, from the nearest copy
        covered = np.zeros(len(panel.texels), bool)

        def spaced(pt):
            """Whether a point is `spacing` or more along the surface from every copy placed."""
            if not centres:
                return True
            for j in cKDTree(centres).query_ball_point(pt, spacing):
                chart, mid = copies[j]
                xy = chart.read(chart.xy, points=pt[None])[0]
                if np.isfinite(xy).all() and np.hypot(*(xy - mid)) < spacing:
                    return False
            return True

        def place(pt, kind, size_range):
            """Try to lay one copy near pt: moved, turned and shrunk before giving up (TRIES). The place it landed, or None."""
            nonlocal placed
            texel = int(free_texels[free_tree.query(pt)[1]])
            if not spaced(c.pos[texel].astype(np.float64)):
                return None
            shape = pictures[kind]
            w_cm = float(rng.uniform(*size_range))
            ang0 = float(rng.uniform(0, 360)) if turn == "random" else (0.0 if turn == "length" else float(turn))
            reach = max(w_cm * shape.reach * 1.05 + 1.5, spacing + 1.0)
            chart, _ = marks._chart_at(c, texel, (0, 0, 1), ang0, reach, True)
            sheet = marks._Sheet(chart, panel, zone, reach, pitch)
            for move, dang, scale in TRIES:
                if dang and turn != "random":
                    continue
                got = sheet.fit(shape, w_cm * scale, *sheet.near(move * w_cm), 0.999, dang)
                if got is None:
                    continue
                X0, Y0, S = got
                cen = c.pos[sheet.t[sheet.texel_at(X0, Y0)]].astype(np.float64)
                if not spaced(cen):
                    return None
                sel, w, rgb = sheet.paint(shape, S, X0, Y0, 0.0, dang)
                keep = sheet.free[sel]
                sel, w, rgb = sel[keep], w[keep], rgb[keep]
                if not len(sel):
                    return None
                texels = sheet.t[sel]
                at = np.minimum(np.searchsorted(idx, texels), len(idx) - 1)
                mine = idx[at] == texels
                gi, mm = texels[mine], m[at[mine]] * w[mine]
                c.blend(gi, mm, np.clip(rgb[mine], 0, 1), np.full(len(gi), fin.roughness, np.float32),
                        np.full(len(gi), fin.metalness, np.float32), np.full(len(gi), fin.varnish, np.float32))
                on_panel = np.searchsorted(panel.texels, sheet.t)
                covered[on_panel[sel[w > 0.3]]] = True
                nearest[on_panel] = np.minimum(nearest[on_panel], np.hypot(sheet.xy[:, 0] - X0, sheet.xy[:, 1] - Y0))
                copies.append((chart, np.array([X0, Y0])))
                centres.append(cen)
                kinds.append(kind)
                placed += 1
                return cen
            return None

        def kinds_for(points, done_points, done_kinds):
            """A picture per point: the one least used among the neighbours already decided
            (within 2.2 spacings, the nearer ones counting more), ties broken at random,
            so no picture bunches up."""
            if len(pictures) == 1:
                return [0] * len(points)
            all_pts = np.asarray(list(done_points) + list(points), np.float64)
            out = list(done_kinds) + [-1] * len(points)
            tree = cKDTree(all_pts)
            base = len(done_points)
            for i in range(len(points)):
                j = base + i
                counts = np.zeros(len(pictures))
                for q in tree.query_ball_point(all_pts[j], 2.2 * spacing):
                    if q != j and out[q] >= 0:
                        counts[out[q]] += 1 / (1 + np.linalg.norm(all_pts[q] - all_pts[j]) / spacing)
                best = np.flatnonzero(counts == counts.min())
                out[j] = int(rng.choice(best))
            return out[base:]

        points = looks.surface_points(pos[free], spacing, seed=int(rng.integers(1 << 30)), regular=False, relax=8)
        for pt, kind in zip(points, kinds_for(points, [], [])):
            if place(pt, kind, sizes) is None:
                skipped += 1
        # second pass: the parts' skin far from every copy along the surface is a bare patch; sprinkle it again with
        # smaller copies (it's bare because the full size didn't fit there)
        for _ in range(2):
            bare = free & (nearest > BARE * spacing)
            if bare.sum() * pitch * pitch < spacing * spacing:
                break
            more = looks.surface_points(pos[bare], 0.8 * spacing, seed=int(rng.integers(1 << 30)), regular=False, relax=4)
            for pt, kind in zip(more, kinds_for(more, centres, kinds)):
                if place(pt, kind, (sizes[0] * 0.7, sizes[1] * 0.85)) is not None:
                    filled += 1
        if skin.measure and centres:
            skin.scattered.append({"op": skin._op, "spacing": spacing, **_spread(pos, covered, np.asarray(centres), spacing)})
    skin.notes.append(f"scatter on {where}: {placed} copies placed ({filled} of them smaller ones filling bare patches), "
                      f"{skipped} spots left bare for crossing a crisp line or an edge; spaced {spacing:.1f} cm or more along the "
                      f"surface ({time.time() - t0:.0f} s)" + (f"; stickers go on the body: the {', '.join(inside)} left as they are" if inside else ""))


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
