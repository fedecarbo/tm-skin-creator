"""The guides on the clay car (tool/levels.py) with the bottom line in pink: on the seam over the
diffuser strake to its end, then straight to the crease under the intake (the user, 2026-10-04,
of Red Bull's red strip along the back)."""
import numpy as np
from tool import levels, shapes
from tool.noise import smoothstep

WORDS = "looking at the redbull one, the bottom red strip, maybe I have the bottom line in the back wrong?"
BLACK, BLUE, PINK = "#0a0a0a", "#1d4ed8", "#e0115f"
BOTTOM = [[-162.0, 38.0], [-148.0, 30.6], [-137.0, 26.6], [-124.0, 22.8], [-116.0, 21.11], [-104.0, 20.69], [-32.0, 21.9],
          [-22.0, 22.06], [8.0, 21.71], [40.0, 19.52], [110.0, 17.85], [216.0, 17.41]]  # z and y in cm


def along(Y, dY, span, width=0.8):
    """A line at the height Y(z) on the outer body (levels.line's, for a curve of its own)."""
    f = levels._above_cm(Y, dY)
    z = shapes.Zone(lambda p, n: smoothstep(-0.1, 0.1, width / 2 - np.abs(f(p, n))).astype(np.float32))
    z = z & shapes.outside(0.1) & shapes.Zone(lambda p, n: smoothstep(-0.85, -0.75, n[:, 1]).astype(np.float32))
    return z & shapes.band(*span) if span else z


def design(s):
    s.clay()
    body = sorted({i["name"] for i in s.parts.instances if i["mesh"] == "Skin"} - set(levels.WHEELS) - set(levels.OFF))
    outer = [f"{b}|part" for b in body]
    doc = levels.load()
    for L in doc["levels"]:
        if L.get("role") == "bottom":
            L["points"] = BOTTOM
    s.step("The guides", "The top line in black, the bottom line in pink, the lines between in blue.", words=WORDS)
    for name, Y, dY, span in levels.curves(doc):
        colour = BLACK if name == "top edge" else PINK if name == "bottom edge" else BLUE
        s.paint(outer, "matte", colour=colour, zone=along(Y, dY, span))
