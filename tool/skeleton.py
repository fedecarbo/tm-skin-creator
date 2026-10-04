"""The car's skeleton: its body cut by flat planes every centimetre, from the mesh alone, with
nothing read into it (the plan's step 2, PLAN.md). The user, 2026-10-02: "a skeleton that functions
like a guide for the blind", "layer by layer, accurate throughout, like a topographic skeleton every
x cm". The car map's lines are readings of a car; these cuts are the car.

Three families of cuts through every part of the body (Skin_01, welded by position: the car map's
_weld, so a cut runs on across the texture's seams):
    section   across the car at a length z, in cm: -161 near the tail's end to 215 the nose's tip
    contour   level all round at a height y above the ground, in cm: 6 the underside to 86
    profile   along the car at a distance x from the middle, in cm, + the car's left: -107 to 107
named by their number ("the contour at 30", "the section at -120"). Each cut is polylines in cm,
chained through the mesh's shared edges; a closed one ends on its first point. Each point keeps
the part its stretch lies on (the wheel covers and the blades are cut too: parts="body" leaves them out).

Cut once and saved in car/skeleton.npz (committed, a few MB), so both computers hold the same car
and nothing about it depends on the computer's arithmetic. The cuts are plain arithmetic on the
mesh: --check cuts them again here and must agree within CHECK cm.

    python -m tool.skeleton              cut the body, save car/skeleton.npz, print a summary
    python -m tool.skeleton --check      cut it again and compare with the saved one

    sk = skeleton.load()
    sk.lines("contour", 30)              the contour at 30 cm: a list of (n, 3) arrays in cm
    sk.lines("section", range(-160, 220, 10), parts="body")
    shapes.cut("contour", range(10, 85, 5), width=0.4)   painted: a zone on the car (tool/shapes.py)
"""

import argparse
import functools
import hashlib

import numpy as np

from tool import paths

FILE = paths.REPO / "car" / "skeleton.npz"
VERSION = 1
FAMILIES = {"section": 2, "contour": 1, "profile": 0}  # the axis each family's planes stand across
EVERY = 1.0  # cm between the saved cuts
ROUND = 1e-3  # cm: the saved points' grain
CHECK = 2e-3  # cm: two cuttings of the same mesh agree within this
# the parts that stand off the body or turn with the wheels: in every cut, left out by parts="body"
APART = ("wheel cover disc", "wheel cover hub", "wheel cover ring", "nose fin", "mirror mount", "wing pylon",
         "diffuser strake")


def _mesh():
    from tool import carmap
    V, F, _, part, names = carmap._weld()
    return V, F, part, names


def _fingerprint(V, F):
    h = hashlib.sha256(np.round(V, 3).astype(np.float64).tobytes())
    h.update(F.astype(np.int64).tobytes())
    return h.hexdigest()[:16]


def cut(V, F, part, axis, at):
    """The mesh cut by the plane coordinate `axis` = at: [(points (n, 3), parts (n,), closed)].
    A vertex on the plane counts as past it, so a cut through a vertex passes through it once."""
    past = V[:, axis] >= at
    k = past[F].sum(1)
    faces = np.flatnonzero((k > 0) & (k < 3))
    if not len(faces):
        return []
    tri = F[faces]
    nv = len(V)
    keys = []  # per face, its two cut edges as a*nv + b, a < b
    for i, j in ((0, 1), (1, 2), (2, 0)):
        a, b = tri[:, i], tri[:, j]
        crossed = past[a] != past[b]
        keys.append(np.where(crossed, np.minimum(a, b).astype(np.int64) * nv + np.maximum(a, b), -1))
    keys = np.stack(keys, 1)
    ends = np.sort(keys, 1)[:, 1:]  # the two crossed edges (the uncrossed one is -1, sorted first)
    touch = {}
    for s, (e0, e1) in enumerate(ends.tolist()):
        touch.setdefault(e0, []).append(s)
        touch.setdefault(e1, []).append(s)
    used = np.zeros(len(ends), bool)
    out = []
    for s0 in range(len(ends)):
        if used[s0]:
            continue
        used[s0] = True
        seq, segs = [int(ends[s0, 0]), int(ends[s0, 1])], [s0]
        for forward in (True, False):
            while True:
                key = seq[-1] if forward else seq[0]
                nxt = [s for s in touch[key] if not used[s]]
                if not nxt:
                    break
                s = nxt[0]
                used[s] = True
                other = int(ends[s, 1]) if ends[s, 0] == key else int(ends[s, 0])
                if forward:
                    seq.append(other)
                    segs.append(s)
                else:
                    seq.insert(0, other)
                    segs.insert(0, s)
        e = np.array(seq, np.int64)
        a, b = V[e // nv], V[e % nv]
        t = (at - a[:, axis]) / (b[:, axis] - a[:, axis])
        p = a + t[:, None] * (b - a)
        p[:, axis] = at
        seg_part = part[faces[segs]]
        out.append((p, np.r_[seg_part, seg_part[-1]], len(seq) > 2 and seq[0] == seq[-1]))
    return out


def _values(V, axis):
    lo, hi = V[:, axis].min(), V[:, axis].max()
    return np.arange(np.ceil(lo / EVERY) * EVERY, hi, EVERY)


def build():
    """Every cut of every family, as the arrays saved in FILE."""
    V, F, part, names = _mesh()
    data = dict(version=VERSION, mesh=_fingerprint(V, F), names=names.astype(str))
    for fam, axis in FAMILIES.items():
        at, starts, pts, prt, closed = [], [0], [], [], []
        for v in _values(V, axis):
            for p, q, c in cut(V, F, part, axis, v):
                at.append(v)
                pts.append(p)
                prt.append(q)
                closed.append(c)
                starts.append(starts[-1] + len(p))
        data.update({f"{fam}_at": np.array(at, np.float32), f"{fam}_starts": np.array(starts, np.int32),
                     f"{fam}_pts": (np.round(np.concatenate(pts) / ROUND) * ROUND).astype(np.float32),
                     f"{fam}_part": np.concatenate(prt).astype(np.int16), f"{fam}_closed": np.array(closed)})
    return data


class Skeleton:
    def __init__(self, data):
        self.d = data
        self.names = data["names"]

    def lines(self, family, at, parts=None):
        """The polylines of a family's cuts at `at` (a number or several, in cm, on the EVERY grid;
        one past the car's ends has none), each an (n, 3) array in cm. parts: only the stretches on
        these parts (names), or "body": all but APART."""
        if family not in FAMILIES:
            raise ValueError(f"{family!r}: a family is one of {', '.join(FAMILIES)}")
        at = np.atleast_1d(np.asarray(at, np.float64))
        want = np.round(at / EVERY).astype(np.int64)
        if np.abs(want * EVERY - at).max() > 1e-6:
            raise ValueError(f"the cuts are every {EVERY:g} cm: {at[np.abs(want * EVERY - at) > 1e-6][0]:g} isn't one")
        have = np.round(self.d[f"{family}_at"] / EVERY).astype(np.int64)
        starts, pts = self.d[f"{family}_starts"], self.d[f"{family}_pts"]
        if parts == "body":
            parts = [n for n in np.unique(self.names) if n not in APART]
        keep = None if parts is None else np.isin(self.names, list(parts))
        out = []
        for i in np.flatnonzero(np.isin(have, want)):
            p = pts[starts[i]:starts[i + 1]].astype(np.float64)
            if keep is None:
                out.append(p)
                continue
            on = np.flatnonzero(keep[self.d[f"{family}_part"][starts[i]:starts[i + 1] - 1]])  # per stretch
            for run in np.split(on, np.flatnonzero(np.diff(on) > 1) + 1):
                if len(run):
                    out.append(p[run[0]:run[-1] + 2])
        return out


@functools.lru_cache(maxsize=1)
def load():
    if not FILE.exists():
        raise SystemExit(f"{FILE.relative_to(paths.REPO)} is missing: python -m tool.skeleton cuts it")
    with np.load(FILE) as f:
        data = {k: f[k] for k in f.files}
    return Skeleton(data)


def check():
    """Cut again here and compare with the saved cuts: the same mesh, the same polylines."""
    saved = load().d
    new = build()
    if str(saved["mesh"]) != new["mesh"]:
        return [f"the mesh differs from the one cut (saved {saved['mesh']}, here {new['mesh']}): cut it again"]
    bad = []
    for fam in FAMILIES:
        for k in ("at", "starts", "part", "closed"):
            if not np.array_equal(saved[f"{fam}_{k}"], new[f"{fam}_{k}"]):
                bad.append(f"{fam}: the {k} differ")
        if not bad and saved[f"{fam}_pts"].shape == new[f"{fam}_pts"].shape:
            d = np.abs(saved[f"{fam}_pts"] - new[f"{fam}_pts"]).max()
            if d > CHECK:
                bad.append(f"{fam}: a point moved {d:.4f} cm")
    return bad


def summary(sk):
    lines = []
    for fam in FAMILIES:
        at, starts = sk.d[f"{fam}_at"], sk.d[f"{fam}_starts"]
        p = sk.d[f"{fam}_pts"].astype(np.float64)
        seg = np.linalg.norm(np.diff(p, axis=0), axis=1)
        inside = np.ones(len(seg), bool)
        inside[starts[1:-1] - 1] = False  # the step between one polyline and the next
        lines.append(f"{fam:8} {len(np.unique(at)):4} cuts, {at.min():g} to {at.max():g} cm; {len(at):5} polylines "
                     f"({sk.d[f'{fam}_closed'].sum()} closed), {len(p):7} points, {seg[inside].sum() / 100:7.0f} m of line")
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="cut again and compare with the saved cuts")
    args = ap.parse_args()
    if args.check:
        bad = check()
        print("\n".join(bad) if bad else f"the cuts agree with {FILE.name} within {CHECK} cm")
        raise SystemExit(1 if bad else 0)
    data = build()
    np.savez_compressed(FILE, **data)
    load.cache_clear()
    print(f"saved {FILE.relative_to(paths.REPO)}, {FILE.stat().st_size / 1e6:.1f} MB")
    print("\n".join(summary(load())))


if __name__ == "__main__":
    main()
