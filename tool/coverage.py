"""Cached texel coverage of every part, per texture set and size, for the paint box.

parts.Parts.coverage() rasterises a part's triangles with 2x2 samples per texel, which takes
about a second per part at 4096: painting a whole car would spend minutes on it. This stores
every part's coverage once, sparsely (most texels are 0, and most covered ones are exactly 1),
in the work folder, and rebuilds when car/parts.json changes.

    cov = coverage.load(p, "Skin", 4096, 4096)
    cov.get([id, id, ...])   -> float32 (h, w), 0..1, the parts' coverage added up (clipped to 1)
    cov.share([id, ...])     -> the parts' share of what covers each texel: 1 on an island's edge
                                that only they reach, where get() gives the part inside the island
    cov.owners()             -> int32 (h, w), the part that covers each texel most, -1 for none
    cov.twins()              -> which parts share texels with which (the Lab's rooms, their UV map tab)
"""

import hashlib

import numpy as np

from tool import bake, parts, paths


def _key():
    return hashlib.sha256(parts.PARTS_JSON.read_bytes()).hexdigest()[:16]


class Coverage:
    def __init__(self, p, texture_set, width, height):
        self.p, self.set, self.w, self.h = p, texture_set, width, height
        self.ids = [i for i, inst in enumerate(p.instances) if inst["mesh"] == texture_set]
        self.file = paths.CACHE / f"coverage_{texture_set}_{width}x{height}_{_key()}.npz"
        self.sparse = self._load() or self._build()
        self._all = None

    def _load(self):
        if not self.file.exists():
            return None
        d = np.load(self.file)
        return {i: (d[f"idx_{i}"], d[f"val_{i}"]) for i in self.ids if f"idx_{i}" in d.files}

    def _build(self):
        print(f"coverage: rasterising {len(self.ids)} parts of {self.set} at {self.w}x{self.h} (once per size)...", flush=True)
        b = bake.bake(self.set, self.w, self.h)
        out = {}
        for i in self.ids:
            c = self.p.coverage(b, self.set, ids=[i])
            idx = np.flatnonzero(c > 0).astype(np.uint32)
            out[i] = (idx, np.rint(c.reshape(-1)[idx] * 255).astype(np.uint8))
        self.file.parent.mkdir(parents=True, exist_ok=True)
        arrays = {}
        for i, (idx, val) in out.items():
            arrays[f"idx_{i}"] = idx
            arrays[f"val_{i}"] = val
        np.savez_compressed(self.file, **arrays)
        return out

    def get(self, ids):
        """The parts' coverage added up and clipped to 1. Added, not the largest: where two
        parts meet, each covers part of the seam texel, and painting both must cover it fully
        (the largest left the stock paint showing through as a dotted line along every seam;
        found on TSC_Seams_Black, 2026-09-24). Shared texels (twins) just clip to 1."""
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
        inside, so a second coat over a first left the first showing there at a quarter or so,
        a dashed line along every edge (black over orange on TSC_CMYK_BlackTail's tail,
        2026-09-25). Only where another part shares the texel does the paint mix."""
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

    def twins(self, least=64):
        """Which parts share paint: {id: (texels, shared, {other id: texels both use})}. Counts
        texels a part covers by three quarters or more, so where two parts meet on one island,
        the texel they split counts for neither. texels: the part's; shared: how many of those
        another part uses too; the pairs are those sharing at least `least` texels. Not always
        mirror twins with one name: the front wing and the floor share most of theirs."""
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
