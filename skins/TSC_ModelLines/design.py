"""Model lines: lines and panels from the template alone (tool/meshlines.py: the model's own lines, read off its
triangles; nothing traced, nothing from the car map, no light or shading). On an edge: the sidepod panel's crisp edge
up its back and along its foot. Round shapes: the panel round the cockpit filled red up to its panel line with a black
line on the line, the nose panel blue, a black trim inside each inlet's edge. A red tape along the line the user picked
on the mesh (note 4) on the rear flank, smooth through its points."""
from tool import meshlines

TEST = "You choose, because this tool is really for you to paint accurately.  If you need to run a test feel free"
TAPE = "Draw a red tape here"
# note 4: the points the user clicked on the mesh (`PY -m tool.notes drawn TSC_ModelLines 4`)
PICKED = [(84.5, 55.2, -52), (82.9, 55.6, -56.4), (80.9, 55.5, -60.9), (76, 56.2, -69.1), (70.7, 56.8, -77), (65.4, 57.3, -84.8),
          (60.1, 58, -92.3), (57.1, 58.6, -97.1)]


def design(s):
    s.clay()
    s.step("On edges and round shapes", "The sidepod panel's crisp edge in black; the panel round the cockpit red up to "
           "its panel line, a black line on the line; the nose panel blue; a black trim inside each inlet's edge.", words=TEST)
    rear = meshlines.line((86, 44, -42), kind="crease", least=100).between((86, 52.4, -45.8), (83.3, 28.5, 0.2))
    s.paint("body", "gloss black", zone=rear.mirrored().strip(0.6), across=True)
    s.paint("body", "gloss red", zone=meshlines.panel((25, 79.5, 11)), across=True)
    s.paint("body", "gloss black", zone=meshlines.line((35, 71.3, 8.5), kind="crease", least=100).strip(0.6), across=True)
    s.paint("body", "gloss blue", zone=meshlines.panel((1.5, 55.6, 162.3)), across=True)
    s.paint("body", "gloss black", zone=meshlines.panel((69.4, 52.4, -18.8), both=True, border=1.5), across=True)
    s.step("A red tape", "A red tape 2 cm wide along the line picked on the mesh, smooth through its points, on the rear flank, both sides.", words=TAPE)
    s.paint("body", "gloss red", zone=meshlines.picked(PICKED).mirrored().strip(2.0), across=True)
