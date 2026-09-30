"""The blueprints' test car (tool/blueprint.py, 2026-09-30), made the way a livery designer works on
a side view: a few strokes cut the body into areas and each area takes a colour (the user: "those
artists that have a side view of a car and do strokes of lines to separate colours"). Two sweeps
along the side, A high and B low: white above A, red between them, dark below B, the strokes
themselves pinstriped; from above, two strokes along the nose with a red spine between them. Every
stroke and fill is drawn flat on a view and landed on the body (shapes.view_line, view_fill), the
same on the left and the right. A test car for the blueprints, not a skin to drive."""

from tool import shapes

BODY = "body"
# (z, y) mm on the side views, kept on what the side owns (python -m tool.blueprint --probe)
A = "M 2200,395 C 1700,450 900,575 500,600 C 100,625 -300,560 -700,560 S -1300,560 -1550,530"  # the high sweep, from beyond the nose tip
B = "M 850,240 C 300,330 -200,320 -600,330 S -900,370 -1000,330 S -1050,220 -1060,140"       # the low sweep, off the body at the front, down to the sill at the rear (the sill runs under the arch)
RED = [(500, 450), (-500, 480)]      # spots between A and B (the sidepod's front and its flank)
DARK = [(-500, 260)]                 # a spot below B (the sidepod's skirt)
# (x, z) mm on the top view: two strokes along the nose, the spine between them
S1, S2 = "M 140,2150 L 140,300", "M -140,2150 L -140,300"
SPINE = [(0, 1000), (0, 1800)]


def design(s):
    s.clay()
    s.step("Base", "A warm white body.")
    s.paint(BODY, "satin", colour="#e9e6de")
    s.step("The red band", "Red between the two sweeps, filled from spots on the side views like a paint bucket.",
           words="the blueprints")
    for view in ("left", "right"):
        for at in RED:
            s.paint(BODY, "satin", colour="#c8102e", zone=shapes.view_fill(view, at, [A, B]))
    s.step("The dark skirt", "Dark below the low sweep.", words="the blueprints")
    for view in ("left", "right"):
        for at in DARK:
            s.paint(BODY, "satin", colour="#202329", zone=shapes.view_fill(view, at, [A, B]))
    s.step("The pinstripes", "The two sweeps themselves, 6 and 4 mm black lines.", words="the blueprints")
    for view in ("left", "right"):
        s.paint(BODY, "gloss", colour="#101114", zone=shapes.view_line(view, A, 6))
        s.paint(BODY, "gloss", colour="#101114", zone=shapes.view_line(view, B, 4))
    s.step("The spine", "A red spine down the nose between two strokes, from above.", words="the blueprints")
    for at in SPINE:
        s.paint(BODY, "satin", colour="#c8102e", zone=shapes.view_fill("top", at, [S1, S2]))
    for stroke in (S1, S2):
        s.paint(BODY, "gloss", colour="#101114", zone=shapes.view_line("top", stroke, 5))
    s.paint(["inner", "wheel covers"], "satin", colour="#3a3d42")
