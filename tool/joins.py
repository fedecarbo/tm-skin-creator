"""Close looks at every place where two panels of the body meet: the body sheet's seams and joins,
the wheels off, both sides (the user's close-up of the sidepod's rear corner, 2026-09-29, where the
checker sheared and the bands stepped between the sidepod's top and the rear flank).

    python -m tool.joins <name> [--out <file>]   -> build/<name>_joins.png
"""

import sys

from tool import paths, snap

# (label, dir, dist, target in metres): the left side; the right is mirrored
_JOINS = (("sidepod's front panel edge", [0.75, 0.45, 0.5], 0.85, [0.6, 0.5, 0.05]),
          ("sidepod's rear corner", [0.85, 0.4, -0.35], 0.75, [0.78, 0.52, -0.5]),
          ("sidepod's rear corner, from behind", [0.5, 0.35, -0.8], 0.8, [0.75, 0.5, -0.55]),
          ("sidepod's front corner", [0.8, 0.45, 0.4], 0.8, [0.6, 0.55, 0.28]),
          ("sidepod's outer edge", [0.9, 0.45, 0.0], 0.8, [0.84, 0.55, -0.2]),
          ("tail meets the rear flank", [0.8, 0.4, -0.45], 0.8, [0.5, 0.6, -1.3]),
          ("skirt's crest at the front flank", [0.95, 0.15, 0.3], 0.8, [0.4, 0.25, 0.7]),
          ("nose's lip", [0.8, 0.2, 0.55], 0.7, [0.22, 0.45, 1.5]),
          ("deck meets the rear flank", [0.7, 0.7, -0.2], 0.9, [0.55, 0.62, -0.9]))
JOINS = tuple((f"{side} {label}", {"dir": [s * d[0], d[1], d[2]], "dist": dist, "target": [s * t[0], t[1], t[2]]},
               False, [], snap.NO_WHEELS)
              for label, d, dist, t in _JOINS for side, s in (("left", 1), ("right", -1)))


if __name__ == "__main__":
    name = sys.argv[1]
    out = paths.BUILD / (sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else f"{name}_joins.png")
    snap.snap(name, out=out, shots=JOINS, prepare=False)
