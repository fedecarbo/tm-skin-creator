"""The Lab's UV map room's data (viewer/lab-rooms.js), from the tool's own parts and texel coverage, into the work
folder's viewer data (tool/view.py's DATA): built when the Lab's server starts (tool/swatches.py).

  <Set>_Parts.png     per texel of the <Set>_Shared.png grid, the part that covers it most (coverage.owners at the
                      paint's size), R + 256 G = the part's id + 1
  <Set>_Surfaces.png  per texel of that grid, the surface it's on, R + 256 G = its number + 1: a surface is a shape
                      of its own on the flat map (texels that touch), what the Lab's UV map picks (_surfaces);
                      grown 2 texels into the gaps so the car lights its edges too
  uvmap.json          each map (its paint's size, the grid, its assemblies), each part in words (parts.Parts: its
                      label, whose paint it shares, the line to copy for Claude) and numbers (its share of the map,
                      dots per cm, cm2 on the car), and the Lab's rooms (tool/rooms.py: the UV map, its maps, parts
                      and camera)
"""

import hashlib
import json

import numpy as np
from PIL import Image

from tool import parts, paths, view
from tool.view import DATA, _stale

UVMAP_VERSION = 1  # bump when export_uvmap or _surfaces change what they write


def export_uvmap():
    """The room's files (above), rebuilt when the parts, their coverage or words, or the rooms change."""
    from tool import coverage, paintbox, rooms
    out, stamp = DATA / "uvmap.json", DATA / "uvmap.key"
    here = paths.REPO / "tool"
    # Rebuilt (23 s) when those change, not after every edit to paintbox.py or this file, the two most
    # edited: of those it takes only the paint's sizes, and UVMAP_VERSION for its own code.
    key = hashlib.sha1(repr((UVMAP_VERSION, paintbox.SIZES)).encode()).hexdigest()[:12]
    if (not _stale(out, parts.PARTS_JSON, here / "parts.py", here / "coverage.py", here / "rooms.py", this_file=False)
            and stamp.exists() and stamp.read_text() == key):
        return
    p = parts.load()
    maps, rows = [], []
    for tset, (gw, gh) in parts.BAKE_SIZE.items():
        pw, ph = paintbox.SIZES[tset]
        cov = coverage.load(p, tset, pw, ph)
        sx, sy = pw // gw, ph // gh
        own = cov.owners()[sy // 2::sy, sx // 2::sx] + 1
        DATA.mkdir(parents=True, exist_ok=True)
        Image.fromarray(np.stack([own & 255, own >> 8, np.zeros_like(own)], -1).astype(np.uint8), "RGB").save(DATA / f"{tset}_Parts.png")
        labels, grown, surfaces = _surfaces(own, *cov.sets(sx, sy, least=191))
        Image.fromarray(np.stack([grown & 255, grown >> 8, np.zeros_like(grown)], -1).astype(np.uint8), "RGB").save(DATA / f"{tset}_Surfaces.png")
        twins = cov.twins()
        maps.append({"set": tset, "size": [pw, ph], "grid": [gw, gh], "parts": len(cov.ids), "surfaces": surfaces,
                     "holds": list(dict.fromkeys(p.instances[i]["parent"] for i in cov.ids))})
        for i in cov.ids:
            inst = p.instances[i]
            texels, _, others = twins[i]
            rows.append({"id": i, **{k: inst[k] for k in ("name", "group", "parent", "side", "end", "mesh")},
                         "label": p.label(i), "tag": p.tag(i), "line": p.line(i, twins), "paint": p.share_words(i, twins),
                         "twins": sorted(others), "pct": round(100 * texels / (pw * ph), 2),
                         "sharp": round((texels / inst["area_cm2"]) ** 0.5, 1) if inst["area_cm2"] else 0,
                         "area": round(inst["area_cm2"])})
    assemblies = {a["name"]: a["about"] for a in json.loads(parts.PARTS_JSON.read_text())["assemblies"]}
    lab_rooms = rooms.rooms(p)
    out.write_text(json.dumps({"maps": maps, "assemblies": assemblies, "rooms": lab_rooms,
                               "parts": sorted(rows, key=lambda r: r["id"])}, indent=1))
    stamp.write_text(key)


SURFACE_LEAST = 16


def _surfaces(own, on, sets):
    """The flat map's surfaces: the shapes the Lab outlines on it, each a run of touching texels with
    the same part on top (own: the owners, + 1), so what's seen is what's picked (the user,
    2026-09-26: "in the 3d to select parts, but in the uv map to be able to select surfaces").
    Touching texels alone merged the body shell with the cockpit surround, and every tyre's paint
    into one. on, sets: the parts covering each texel by 3/4 (coverage.sets), twins and overlaps;
    a part counts on a surface from SURFACE_LEAST texels (a seam's texels are half each side's).
    Returns the labels (0 none, else the surface's number + 1), the same grown 2 texels into the
    gaps, and per surface {parts: ids on it, texels}."""
    from scipy import ndimage
    labels = np.zeros(own.shape, np.int32)
    n = 0
    for i, box in enumerate(ndimage.find_objects(own), start=1):
        if box is None:
            continue
        lab, k = ndimage.label(own[box] == i)
        labels[box][lab > 0] = lab[lab > 0] + n
        n += k
    if n >= 65535:
        raise ValueError(f"{n} surfaces: more than the Surfaces.png can number")
    dist, (iy, ix) = ndimage.distance_transform_edt(labels == 0, return_indices=True)
    grown = np.where(dist <= 2, labels[iy, ix], 0)
    k = (labels > 0) & (on >= 0)
    count = {}
    pairs, n_on = np.unique(np.stack([labels[k], on[k]], 1), axis=0, return_counts=True)
    for (lab, s), c in zip(pairs.tolist(), n_on.tolist()):
        for i in sets[s]:
            count[lab, i] = count.get((lab, i), 0) + c
    parts_of = [set() for _ in range(n + 1)]
    for (lab, i), c in count.items():
        if c >= SURFACE_LEAST:
            parts_of[lab].add(i)
    top = ndimage.labeled_comprehension(own, labels, np.arange(1, n + 1), np.max, np.int32, 0)
    for lab, o in enumerate(top.tolist(), start=1):  # its part on top, always
        parts_of[lab].add(o - 1)
    texels = np.bincount(labels.reshape(-1), minlength=n + 1)
    return labels, grown, [{"parts": sorted(parts_of[i]), "texels": int(texels[i])} for i in range(1, n + 1)]
