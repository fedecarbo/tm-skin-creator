"""The car's own lines, pinned by the user in the Lab's lines room (viewer/lab-lines.js) and kept in
car/lines.json: where the body's lines run, by a human eye. Claude can't see or click; the user can
(2026-09-29: "Maybe we build a tool to build the tool"). Each line is a few pins on the body (cm;
x the car's left, y up, z forward, as tool/paint.py), a name, and whether it's mirrored to the
other side. The curve through the pins is a centripetal Catmull-Rom spline put back on the body
and smoothed (the recipe the room draws with, so what the user sees is what gets painted),
sampled every 0.25 cm. Their clicks say where, the maths says smooth: the curve may miss a pin by
a few mm to stay smooth, and `python -m tool.lines` says by how much.

    python -m tool.lines             every line: its pins, its sides, its length, how far it strays from its pins
    lines.load(), lines.save(doc)    the file (standard library only: the viewer's server writes it, /api/lines)
    lines.fitted()                   the curves on the body: has(name), curves(name), distance(name, pos),
                                     offset(name, pos)

shapes.line, near and line_offset take a pinned line's name, before the map's own line of the same
name (tool/carmap.py): the user's eye wins over the mesh's curvature. offset > 0 is below the line
(down the body), or outboard where the line runs up and down, so shapes.line_offset("shoulder", 30,
20) is a 20 mm band 30 mm below the shoulder, on both sides when the line is mirrored."""

import json
import math
import os
import re
import sys
import tempfile
from pathlib import Path

from tool import paths

FILE = paths.REPO / "car" / "lines.json"
MAX_LINES, MAX_PINS = 200, 200
REACH = 600.0   # cm: no point of the car is further than this from its middle
SPACING = 0.25  # cm between the fitted curve's points
NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 '\-]{0,39}$")


# ---- the file ----

def _clean(doc):
    """The document checked and tidied (a plain error for the page when it isn't right)."""
    if not isinstance(doc, dict) or not isinstance(doc.get("lines"), list):
        raise ValueError("expected {\"lines\": [...]}")
    if len(doc["lines"]) > MAX_LINES:
        raise ValueError(f"more than {MAX_LINES} lines")
    out, names = [], set()
    for L in doc["lines"]:
        if not isinstance(L, dict):
            raise ValueError("a line must be an object")
        name = str(L.get("name", "")).strip()
        if not NAME.match(name):
            raise ValueError(f"not a line's name: {name!r} (letters, digits, spaces, up to 40)")
        if name.lower() in names:
            raise ValueError(f"two lines called {name!r}")
        names.add(name.lower())
        pts, nrms = L.get("points", []), L.get("normals") or []
        if not isinstance(pts, list) or len(pts) > MAX_PINS:
            raise ValueError(f"{name}: up to {MAX_PINS} pins")
        cp, cn = [], []
        for i, p in enumerate(pts):
            if not (isinstance(p, list) and len(p) == 3 and all(isinstance(v, (int, float)) and math.isfinite(v) and abs(v) <= REACH for v in p)):
                raise ValueError(f"{name}: pin {i + 1} isn't a point on the car")
            cp.append([round(float(v), 2) for v in p])
            n = nrms[i] if i < len(nrms) and isinstance(nrms[i], list) and len(nrms[i]) == 3 else [0, 1, 0]
            n = [float(v) if isinstance(v, (int, float)) and math.isfinite(v) else 0.0 for v in n]
            k = math.sqrt(sum(v * v for v in n)) or 1.0
            cn.append([round(v / k, 3) for v in n])
        out.append({"name": name, "mirror": bool(L.get("mirror", True)), "points": cp, "normals": cn})
    return {"lines": out}


def load():
    """The lines as pinned: {"lines": [{name, mirror, points, normals}]}; none yet, an empty list."""
    if not FILE.exists():
        return {"lines": []}
    with open(FILE, encoding="utf-8") as f:
        return _clean(json.load(f))


def save(doc):
    """Keep the lines (checked), replacing the file whole. Returns them as kept."""
    doc = _clean(doc)
    FILE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=FILE.parent, prefix=".lines-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=1)
            f.write("\n")
        os.replace(tmp, FILE)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return doc


# ---- the curves on the body ----

def catmull_rom(P, spacing=SPACING):
    """A centripetal Catmull-Rom spline through the pins P (n, 3), a point every `spacing` cm, the
    ends carried straight on (viewer/lab-lines.js draws the same)."""
    import numpy as np
    P = np.asarray(P, float)
    if len(P) < 2:
        return P.copy()
    if len(P) == 2:
        n = max(2, int(math.ceil(np.linalg.norm(P[1] - P[0]) / spacing)) + 1)
        return P[0] + (P[1] - P[0]) * np.linspace(0, 1, n)[:, None]
    Q = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    for i in range(1, len(Q) - 2):
        p0, p1, p2, p3 = Q[i - 1], Q[i], Q[i + 1], Q[i + 2]
        t0 = 0.0
        t1 = t0 + math.sqrt(np.linalg.norm(p1 - p0))
        t2 = t1 + math.sqrt(np.linalg.norm(p2 - p1))
        t3 = t2 + math.sqrt(np.linalg.norm(p3 - p2))
        n = max(1, int(math.ceil(np.linalg.norm(p2 - p1) / spacing)))
        t = t1 + (t2 - t1) * np.arange(n)[:, None] / n
        lerp = lambda a, b, u: a + (b - a) * u
        A1 = lerp(p0, p1, (t - t0) / max(t1 - t0, 1e-9))
        A2 = lerp(p1, p2, (t - t1) / max(t2 - t1, 1e-9))
        A3 = lerp(p2, p3, (t - t2) / max(t3 - t2, 1e-9))
        B1 = lerp(A1, A2, (t - t0) / max(t2 - t0, 1e-9))
        B2 = lerp(A2, A3, (t - t1) / max(t3 - t1, 1e-9))
        out.append(lerp(B1, B2, (t - t1) / max(t2 - t1, 1e-9)))
    out.append(P[-1:])
    return np.vstack(out)


def _on_body(pts):
    """The spline put back on the body and smoothed, twice, then put back once more: a curve that
    lies on the skin and bends gently (carmap.Map.design_lines does the same with its blends)."""
    import numpy as np
    from scipy.ndimage import gaussian_filter1d
    from tool import carmap
    m = carmap.load()
    for _ in range(2):
        pts = m.project(pts)[0]
        pts = gaussian_filter1d(pts, 4, axis=0, mode="nearest")
    return m.project(pts)[0].astype(np.float64)


class Fitted:
    """The pinned lines as curves on the body, both sides where mirrored, and the distances the
    paint box needs."""

    def __init__(self, doc):
        self.doc = doc
        self.by_name = {L["name"].lower(): L for L in doc["lines"]}
        self._curves = {}
        self._trees = {}

    @property
    def names(self):
        return [L["name"] for L in self.doc["lines"]]

    def has(self, name):
        return str(name).lower() in self.by_name

    def _line(self, name):
        try:
            return self.by_name[str(name).lower()]
        except KeyError:
            known = ", ".join(self.names) or "none pinned yet"
            raise KeyError(f"no line called {name!r} has been pinned in the Lab's lines room (known: {known})") from None

    def curves(self, name):
        """The line's curves on the body: [(points (n, 3) cm every 0.25 cm, side)], the pinned side
        and, when mirrored, its mirror; a line with fewer than two pins has none."""
        import numpy as np
        key = str(name).lower()
        if key not in self._curves:
            L = self._line(name)
            out = []
            if len(L["points"]) >= 2:
                dense = _on_body(catmull_rom(L["points"]))
                side = "left" if dense[:, 0].mean() >= 0 else "right"
                out.append((dense, side))
                if L["mirror"]:
                    out.append((dense * np.array([-1.0, 1.0, 1.0]), "right" if side == "left" else "left"))
            self._curves[key] = out
        return self._curves[key]

    def _tree(self, name):
        """A KD-tree over every curve of the line, with at each point the direction across the line
        on the skin, pointing down the body (or outboard where the line runs up and down)."""
        import numpy as np
        from scipy.spatial import cKDTree
        from tool import carmap
        key = str(name).lower()
        if key not in self._trees:
            pts, B = [], []
            m = carmap.load()
            for dense, _ in self.curves(name):
                T = np.gradient(dense, axis=0)
                T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
                N = m.value("ns", dense).astype(np.float64)
                b = np.cross(N, T)
                b /= np.maximum(np.linalg.norm(b, axis=1, keepdims=True), 1e-9)
                if abs(b[:, 1].mean()) > 0.3:
                    b *= -np.sign(b[:, 1].mean())  # down the body
                else:
                    b *= np.sign((b[:, 0] * np.sign(dense[:, 0] + 1e-9)).mean() + 1e-12)  # outboard
                pts.append(dense)
                B.append(b)
            if pts:
                pts, B = np.concatenate(pts), np.concatenate(B)
                self._trees[key] = (cKDTree(pts), pts, B)
            else:
                self._trees[key] = None
        return self._trees[key]

    def distance(self, name, pos):
        """Distance (cm) from the points to the line, either side."""
        import numpy as np
        t = self._tree(name)
        pos = np.asarray(pos, np.float64)
        if t is None:
            return np.full(len(pos), 1e6, np.float32)
        return t[0].query(pos, workers=-1)[0].astype(np.float32)

    def offset(self, name, pos):
        """Signed distance (cm) from the points to the line: positive below it (down the body), or
        outboard where the line runs up and down."""
        import numpy as np
        t = self._tree(name)
        pos = np.asarray(pos, np.float64)
        if t is None:
            return np.full(len(pos), 1e6, np.float32)
        tree, pts, B = t
        d, i = tree.query(pos, workers=-1)
        sign = np.sign(((pos - pts[i]) * B[i]).sum(1) + 1e-12)
        return (sign * d).astype(np.float32)

    def strays(self, name):
        """How far the fitted curve strays from each pin (cm): the smoothing's price, for the check."""
        import numpy as np
        t = self._tree(name)
        P = np.asarray(self._line(name)["points"], np.float64)
        if t is None or not len(P):
            return np.zeros(len(P))
        return t[0].query(P, workers=-1)[0]


_fitted = None


def fitted():
    """The lines as last saved, fitted once per change of the file."""
    global _fitted
    stamp = FILE.stat().st_mtime if FILE.exists() else None
    if _fitted is None or _fitted[0] != stamp:
        _fitted = (stamp, Fitted(load()))
    return _fitted[1]


def main(args):
    f = fitted()
    if not f.names:
        print(f"No lines pinned yet ({FILE}). Pin them in the Lab's lines room: lab.html?room=lines")
        return
    import numpy as np
    for L in f.doc["lines"]:
        curves = f.curves(L["name"])
        sides = "both sides" if L["mirror"] else "one side"
        if not curves:
            print(f"{L['name']}: {len(L['points'])} pin(s), {sides}: no curve yet (two pins at least)")
            continue
        dense = curves[0][0]
        length = np.linalg.norm(np.diff(dense, axis=0), axis=1).sum()
        s = f.strays(L["name"])
        print(f"{L['name']}: {len(L['points'])} pins, {sides}, {length:.0f} cm long; the curve strays "
              f"{s.max() * 10:.1f} mm from a pin at most (mean {s.mean() * 10:.1f} mm)")
        for k, p in enumerate(L["points"]):
            print(f"   pin {k + 1}: x {p[0]:7.1f}  y {p[1]:6.1f}  z {p[2]:7.1f}   strays {s[k] * 10:4.1f} mm")


if __name__ == "__main__":
    main(sys.argv[1:])
