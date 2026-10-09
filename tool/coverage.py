"""Cached texel coverage of every part, per texture set and size, for the paint box.

parts.Parts.coverage() rasterises a part's triangles with 2x2 samples per texel, which takes
about a second per part at 4096: painting a whole car would spend minutes on it. This stores
every part's coverage once, sparsely (most texels are 0, and most covered ones are exactly 1),
in the work folder as plain arrays mapped from the disk (bake.save, bake.load), with which parts share
paint (twins), and builds it again when anything it's made from changes: car/parts.json, the code that
cuts and rasterises the parts, the mesh. Building a new one keeps only the one before it (which the
self-test's earlier commit may still read).

    cov = coverage.load(p, "Skin", 4096, 4096)
    cov.get([id, id, ...])   -> float32 (h, w), 0..1, the parts' coverage added up (clipped to 1)
    cov.share([id, ...])     -> the parts' share of what covers each texel: 1 on an island's edge
                                that only they reach, where get() gives the part inside the island
    cov.owners()             -> int32 (h, w), the part that covers each texel most, -1 for none
    cov.twins()              -> which parts share texels with which (the Lab's rooms, their UV map tab)
"""

import hashlib
import json
import shutil

import numpy as np

from tool import bake, fbx, parts, paths

MADE_FROM = ("parts.py", "raster.py", "segment.py", "coverage.py")


def _key():
    """What the coverage is made from (parts' cuts live in parts.py), so that a change to any of it
    makes a new file rather than reading an old one."""
    h = hashlib.sha256(parts.PARTS_JSON.read_bytes())
    for name in MADE_FROM:
        h.update((paths.REPO / "tool" / name).read_bytes())
    h.update(str(fbx.CACHE.stat().st_mtime_ns if fbx.CACHE.exists() else 0).encode())
    return h.hexdigest()[:16]


class Coverage:
    def __init__(self, p, texture_set, width, height):
        self.p, self.set, self.w, self.h = p, texture_set, width, height
        self.ids = [i for i, inst in enumerate(p.instances) if inst["mesh"] == texture_set]
        self.folder = paths.CACHE / f"coverage_{texture_set}_{width}x{height}_{_key()}"
        self._all = None
        self._twins = None
        if not self._load():
            self._build()

    def _load(self):
        if not (self.folder / "twins.npy").exists():
            return False
        d = bake.load(self.folder)
        start = d["start"].tolist()
        self.sparse = {i: (d["idx"][a:b], d["val"][a:b]) for i, a, b in zip(d["part"].tolist(), start, start[1:])}
        self._twins = {int(i): (t, s, {int(j): c for j, c in o.items()})
                       for i, (t, s, o) in json.loads(bytes(d["twins"]).decode()).items()}
        return True

    def _build(self):
        print(f"coverage: rasterising {len(self.ids)} parts of {self.set} at {self.w}x{self.h} (once per size)...", flush=True)
        b = bake.bake(self.set, self.w, self.h)
        self.sparse = {}
        for i in self.ids:
            c = self.p.coverage(b, self.set, ids=[i])
            idx = np.flatnonzero(c > 0).astype(np.uint32)
            self.sparse[i] = (idx, np.rint(c.reshape(-1)[idx] * 255).astype(np.uint8))
        self._twins = self._find_twins()
        sizes = [len(idx) for idx, _ in self.sparse.values()]
        bake.save(self.folder, {"part": np.array(list(self.sparse), np.int32), "start": np.r_[0, np.cumsum(sizes)],
                                "idx": np.concatenate([idx for idx, _ in self.sparse.values()]),
                                "val": np.concatenate([val for _, val in self.sparse.values()]),
                                "twins": np.frombuffer(json.dumps(self._twins).encode(), np.uint8)})
        self._load()  # mapped from the disk, as the next paint reads it
        kin = [f for f in self.folder.parent.glob(f"coverage_{self.set}_{self.w}x{self.h}_*") if f.is_dir() and "." not in f.name]
        for old in sorted(kin, key=lambda f: f.stat().st_mtime)[:-2]:
            shutil.rmtree(old, ignore_errors=True)

    def get(self, ids):
        """The parts' coverage added up and clipped to 1. Added, not the largest: where two
        parts meet, each covers part of the seam texel, and painting both must cover it fully
        (the largest leaves the stock paint showing through as a dotted line along every seam). Shared texels (twins) just clip to 1."""
        flat = np.zeros(self.w * self.h, np.float32)
        for i in ids:
            if i not in self.sparse:
                continue
            idx, val = self.sparse[i]
            flat[idx] += val.astype(np.float32) / 255
        return np.minimum(flat, 1).reshape(self.h, self.w)

    def share(self, ids):
        """The parts' share of each texel's covered area, 0..1: what paint on them should weigh.
        On an island's edge a texel is partly outside every triangle; get() gives the part
        inside, so a second coat over a first would leave the first showing there at a quarter or so,
        a dashed line along every edge. Only where another part shares the texel does the paint mix."""
        if self._all is None:
            self._all = self.get(self.ids).reshape(-1)
        mine = self.get(ids).reshape(-1)
        return np.minimum(mine / np.maximum(self._all, 1e-6), 1).reshape(self.h, self.w)

    def owners(self):
        """Per texel, the part that covers it most, -1 where none covers half of it. Where
        several cover it fully (a shared texel), the lowest id wins: centre before left before
        right, so a mirrored texel names the left twin."""
        best = np.full(self.w * self.h, 128, np.uint8)
        out = np.full(self.w * self.h, -1, np.int32)
        for i in sorted(self.sparse, reverse=True):
            idx, val = self.sparse[i]
            win = val >= best[idx]
            out[idx[win]] = i
            best[idx[win]] = val[win]
        return out.reshape(self.h, self.w)

    def sets(self, sx, sy, least=128):
        """Per texel of a coarser grid (one texel in sx by sy, from each cell's middle, as the
        Lab's maps sample owners()), the parts covering it by `least`/255 or more: (index (h, w), -1 for
        none, and the list of id tuples it points into). The Lab's surfaces are made from these
        (view._surfaces): each names only the parts on its own texels, not every part its parts
        share any paint with (the user, 2026-09-26: "I can't select that surface because it
        selects almost all details surfaces")."""
        gw, gh = self.w // sx, self.h // sy
        cells, who = [], []
        for i, (t, v) in self.sparse.items():
            y, x = np.divmod(t[v >= least].astype(np.int64), self.w)
            keep = (y % sy == sy // 2) & (x % sx == sx // 2)
            cells.append((y[keep] // sy) * gw + x[keep] // sx)
            who.append(np.full(int(keep.sum()), i, np.int32))
        cells, who = np.concatenate(cells), np.concatenate(who)
        order = np.lexsort((who, cells))
        cells, who = cells[order], who[order]
        start = np.flatnonzero(np.r_[True, cells[1:] != cells[:-1]])
        size = np.diff(np.r_[start, len(cells)])
        rows = np.full((len(start), size.max()), -1, np.int32)  # each cell's parts, padded
        at = np.arange(len(cells)) - np.repeat(start, size)
        rows[np.repeat(np.arange(len(start)), size), at] = who
        uniq, inv = np.unique(rows, axis=0, return_inverse=True)
        index = np.full(gw * gh, -1, np.int32)
        index[cells[start]] = inv.reshape(-1)
        return index.reshape(gh, gw), [tuple(int(i) for i in r if i >= 0) for r in uniq]

    def twins(self):
        """Which parts share paint: {id: (texels, shared, {other id: texels both use})}. Counts
        texels a part covers by three quarters or more, so where two parts meet on one island,
        the texel they split counts for neither. texels: the part's; shared: how many of those
        another part uses too; the pairs are those sharing at least 64 texels. Not always
        mirror twins with one name: the front wing and the floor share most of theirs. Worked out
        once, with the coverage."""
        return self._twins

    def _find_twins(self, least=64):
        idx, who = [], []
        for i, (t, v) in self.sparse.items():
            t = t[v >= 191]
            idx.append(t)
            who.append(np.full(len(t), i, np.int32))
        idx, who = np.concatenate(idx), np.concatenate(who)
        order = np.lexsort((who, idx))
        idx, who = idx[order], who[order]
        texels = np.bincount(who, minlength=len(self.p.instances))
        on_shared = np.zeros(len(idx), bool)
        pairs = {}
        for k in range(1, 64):  # the k-th part after this one on the same texel
            same = np.flatnonzero(idx[k:] == idx[:-k])
            if not len(same):
                break
            on_shared[same] = on_shared[same + k] = True
            keys, n = np.unique(who[same].astype(np.int64) * 65536 + who[same + k], return_counts=True)
            for key, c in zip(keys.tolist(), n.tolist()):
                if c >= least:
                    a, b = divmod(key, 65536)
                    pairs.setdefault(a, {})[b] = c
                    pairs.setdefault(b, {})[a] = c
        shared = np.bincount(who[on_shared], minlength=len(self.p.instances))
        return {i: (int(texels[i]), int(shared[i]), pairs.get(i, {})) for i in self.ids}


_loaded = {}


def load(p, texture_set, width, height):
    key = (texture_set, width, height)
    if key not in _loaded:
        _loaded[key] = Coverage(p, texture_set, width, height)
    return _loaded[key]
