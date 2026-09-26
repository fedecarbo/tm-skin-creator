"""The Lab's test chart (2026-09-26): every material new to the Lab on its own patch, so the
game can be read against the Lab. Ten bands down each side of the body, nose to tail, with thin
matte black gaps; the wheel covers, tyres and a few inner parts take the rest. The key is in
notes.md. When the user has driven it, each finish the game confirms gets source "game" in
tool/finishes.py."""

from tool import shapes

# the bands' edges along the car, nose (z = 215) to tail (-162), about 38 cm each
EDGES = [215, 177, 139, 102, 64, 26, -12, -49, -87, -124, -162]
GAP = 0.8  # cm either side of each edge: the black line between two patches
# (finish, colour for one without its own), nose to tail
LEFT = [("chalk", "white"), ("wet look", "racing red"), ("stainless steel", None), ("brass", None), ("rose gold", None),
        ("black chrome", None), ("bead-blasted titanium", None), ("chrome wrap", None), ("brushed wrap", None), ("muddy", "white")]
RIGHT = [("gloss carbon", None), ("plain-weave carbon", None), ("fibreglass", None), ("satin plastic", "royal blue"),
         ("soft-touch", "charcoal"), ("textured plastic", "light grey"), ("acrylic", "black"), ("sparkle plastic", "purple"),
         ("gloss wrap", "orange"), ("matte wrap", "olive")]


def design(s):
    s.paint("body", "matte black")
    for side, row in ((shapes.left(), LEFT), (shapes.right(), RIGHT)):
        for k, (finish, colour) in enumerate(row):
            s.paint("body", finish=finish, colour=colour, zone=side & shapes.band(EDGES[k + 1] + GAP, EDGES[k] - GAP))
    # the wheels (all four share one paint)
    s.paint("wheel cover disc", finish="knurled grip")
    s.paint("wheel cover ring", finish="silicone", colour="teal")
    s.paint("wheel cover hub", finish="soft rubber")
    s.paint("tyres", finish="worn rubber")
    # the inner car
    s.paint("inner", "charcoal satin")
    s.paint("seat", finish="perforated leather")
    s.paint("steering wheel", finish="suede")
    s.paint("sidepod panel", finish="denim")
    s.paint("sidepod frame", "neon blue satin")
    s.glow("sidepod frame", kind="night only")
