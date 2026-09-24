"""Cached texel coverage of every part, per texture set and size, for the paint box.

parts.Parts.coverage() rasterises a part's triangles with 2x2 samples per texel, which takes
about a second per part at 4096: painting a whole car would spend minutes on it. This stores
every part's coverage once, sparsely (most texels are 0, and most covered ones are exactly 1),
in the work folder, and rebuilds when car/parts.json changes.

    cov = coverage.load(p, "Skin", 4096, 4096)
    cov.get([id, id, ...])   -> float32 (h, w), 0..1, the union (max) of the parts' coverage
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
        flat = np.zeros(self.w * self.h, np.float32)
        for i in ids:
            if i not in self.sparse:
                continue
            idx, val = self.sparse[i]
            np.maximum.at(flat, idx, val.astype(np.float32) / 255) if False else None
            cur = flat[idx]
            flat[idx] = np.maximum(cur, val.astype(np.float32) / 255)
        return flat.reshape(self.h, self.w)


_loaded = {}


def load(p, texture_set, width, height):
    key = (texture_set, width, height)
    if key not in _loaded:
        _loaded[key] = Coverage(p, texture_set, width, height)
    return _loaded[key]
