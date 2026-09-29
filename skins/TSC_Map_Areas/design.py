"""The car map's areas and lines (tool/carmap.py, tool/shapes.area, shapes.line): the top white, the
sides pale blue, the underside grey; the shoulder green, the lower edge magenta, the real folds
black, openings red, joins blue. A test car for the map, not a skin to drive (2026-09-29)."""

from tool import shapes

BODY = "body"


def design(s):
    s.clay()
    s.step("Areas", "The body's areas: top, sides, underneath.", words="the car map")
    s.paint(BODY, "satin", colour="#f4f2ec", zone=shapes.area("top"))
    s.paint(BODY, "satin", colour="#9fc3e6", zone=shapes.area("sides"))
    s.paint(BODY, "satin", colour="#7d828a", zone=shapes.area("under"))
    s.step("Lines", "The car's lines drawn on it.", words="the car map")
    s.paint(BODY, "satin", colour="#1f8f3a", zone=shapes.line("shoulder", 1.6))
    s.paint(BODY, "satin", colour="#d0208e", zone=shapes.line("lower", 1.6))
    s.paint(BODY, "satin", colour="#111111", zone=shapes.line("fold", 0.6))
    s.paint(BODY, "satin", colour="#e02020", zone=shapes.line("opening", 0.8))
    s.paint(BODY, "satin", colour="#2050e0", zone=shapes.line("join", 0.6))
    s.paint(["inner", "wheel covers"], "satin", colour="#3a3d42")
