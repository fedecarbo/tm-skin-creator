"""The car's lines as the user pins them in the Lab's lines room (viewer/lab-lines.js), kept in
car/lines.json: a few pins on the body per line (cm; x the car's left, y up, z forward, as
tool/paint.py), a name, and whether it's mirrored to the other side. Claude can't see or click;
the user can (2026-09-29: "Maybe we build a tool to build the tool").

The pins are marks, not curves. Turning sparse pins into one smooth curve on this body was tried
the same day and dropped (the user: "I think we just stick to blueprint"): a spline through pins
30 cm apart cuts through the body's bulge by centimetres and, pulled onto the skin, lands on the
wrong surface (off by up to 5 cm); a path built on the body by splitting chords and pulling their
middles wanders round openings (4 cm from its pins); the room's own preview (a spline snapped
along the pins' normals) is only a rough picture. Where a pinned line is wanted in a design, it's
drawn on the blueprints (tool/blueprint.py) through the pins' marks, and that curve is exact by
construction: a point on a view lands on the body along the line of sight.

    python -m tool.lines             every line and its pins
    lines.load(), lines.save(doc)    the file (standard library only: the viewer's server writes it, /api/lines)
"""

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


def main(args):
    doc = load()
    if not doc["lines"]:
        print(f"No lines pinned yet ({FILE}). Pin them in the Lab's lines room: lab.html?room=lines")
        return
    for L in doc["lines"]:
        print(f"{L['name']}: {len(L['points'])} pin(s), {'both sides' if L['mirror'] else 'one side'}")
        for k, p in enumerate(L["points"]):
            print(f"   pin {k + 1}: x {p[0]:7.1f}  y {p[1]:6.1f}  z {p[2]:7.1f}")


if __name__ == "__main__":
    main(sys.argv[1:])
