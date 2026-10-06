"""Model lines: lines and panels from the template alone (tool/meshlines.py: the model's own lines, read off its
triangles; nothing traced, nothing from the car map, no light or shading). On an edge: the sidepod panel's crisp edge
up its back and along its foot. Round shapes: the panel round the cockpit filled red up to its panel line with a black
line on the line, the nose panel blue, a black trim inside each inlet's edge."""
from tool import meshlines

TEST = "You choose, because this tool is really for you to paint accurately.  If you need to run a test feel free"


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
