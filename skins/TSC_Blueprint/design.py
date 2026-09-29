"""The blueprints' test car (tool/blueprint.py, 2026-09-29): everything on it is drawn flat on a
view and landed on the body. A 20 mm line through the user's own pins for the side crease (the Lab's
lines room), from the left view and again from the right; a
30 mm swoosh from the nose's flank up to the sidepod's top edge, drawn on no line the body has; a
chevron filled on the bonnet from the top view. A test car for the blueprints, not a skin to drive."""

from tool import shapes

BODY = "body"
# (z, y) mm on the side views: through the pinned side crease, (-1456, 390) ... (-386, 395)
SIDE = "M -1500,388 C -1100,394 -700,397 -386,395"
SWOOSH = "M 1850,330 C 1400,340 1000,560 250,600"
# (x, z) mm on the top view: an arrow head on the bonnet, pointing at the nose
CHEVRON = "M 0,1380 L 290,960 L 150,930 L 0,1180 L -150,930 L -290,960 Z"


def design(s):
    s.clay()
    s.step("Base", "A warm white body.")
    s.paint(BODY, "satin", colour="#e9e6de")
    s.step("The pinned line", "A 20 mm line through the user's side crease pins, drawn on the left and right views and "
           "landed on the body.", words="the blueprints")
    for view in ("left", "right"):
        s.paint(BODY, "satin", colour="#d81e5b", zone=shapes.view_line(view, SIDE, 20))
    s.step("The swoosh", "A 30 mm sweep from the nose's flank up to the sidepod's top edge, on no line the body has.",
           words="the blueprints")
    for view in ("left", "right"):
        s.paint(BODY, "satin", colour="#1e5bd8", zone=shapes.view_line(view, SWOOSH, 30))
    s.step("The chevron", "An arrow head filled on the bonnet, drawn from above.", words="the blueprints")
    s.paint(BODY, "satin", colour="#202329", zone=shapes.view_shape("top", CHEVRON))
    s.paint(["inner", "wheel covers"], "satin", colour="#3a3d42")
