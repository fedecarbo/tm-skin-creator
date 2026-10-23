"""TSC_OutlineUV: TSC_OutlineTest with the user's idea for its outline (2026-10-23, a test, deleted after): each part's
line drawn inside it straight on its shape in the UV map, beside the tool's, to see the difference."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))  # uvline.py, beside this file: the test's own code
from uvline import outline_uv  # noqa: E402

COLOURS = ["#e4202d", "#ffd21f", "#1f5fd1", "#ff7f1f", "#2bb24c", "#7d3ec1", "#ffffff", "#19c3c3"]
BLACK = "#111111"
PARTS = ["body shell", "nose tip", "nose panel", "side skirt|left", "side skirt|right", "cockpit surround",
         "sidepod top|left", "sidepod top|right", "sidepod inlet|left", "sidepod inlet|right", "rear flank|left",
         "rear flank|right", "rear quarter panel|left", "rear quarter panel|right", "fuel cap", "engine cover|part",
         "tail corner|left", "tail corner|right", "tail panel"]
WHEELS = ["wheel cover disc", "wheel cover ring", "wheel cover hub"]


def design(s):
    s.clay()
    s.step("Plain parts", "Every part of the body a plain gloss colour of its own, the deck's plates in the engine cover's.",
           words="an outline round every part as one stroke along each part's own edge")
    for k, part in enumerate(PARTS):
        s.paint(part, "gloss", colour=COLOURS[k % len(COLOURS)])
    s.paint(["engine cover|part", "number panel", "engine cover panel"], "gloss",  # the plates a guide, not parts
            colour=COLOURS[PARTS.index("engine cover|part") % len(COLOURS)])
    for part in ("nose fin", "diffuser", "diffuser strake", "wing pylon"):
        s.paint(part, "gloss", colour="#ffffff")
    for k, part in enumerate(WHEELS):
        s.paint(part, "gloss", colour=COLOURS[(k + 2) % len(COLOURS)])
    s.step("The outline", "A black line 2.5 cm wide round every part, from one call: centred on every seam, inside "
           "every edge that meets nothing, widening gently between the two.",
           words="should it just be strokes or outlines?")
    s.paint(PARTS, "gloss", colour=BLACK, zone=outline_uv(PARTS), across=True)
    s.paint(WHEELS, "gloss", colour=BLACK, zone=outline_uv(WHEELS), across=True)
    s.paint("inner", "gloss plastic", colour="#222222")
