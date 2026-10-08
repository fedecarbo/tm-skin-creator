"""TSC_LinesTest: the road's step 4 on a test car, five lines laid anywhere on the mesh, the same design painted as
the tool was (A, the old code) and on the surface (B): a line beside a line carried on over a seam, a line beside a
bent one, a line picked across the flank through points on no line of the model's, a line drawn by hand, and a
colour's edge on a line. Scrapped after the pick."""

from tool import course, meshlines, shapes

BASE, INK, GREEN = "#d9d6cf", "#141414", "#1f8f3a"


def design(s):
    s.clay()
    s.step("The body", "The body in one pale colour, the inner car dark.")
    s.paint("body", "satin", colour=BASE)
    s.paint("inner", "matte", colour="#2a2a2e")
    s.step("The nose tape", "A block scale 4 cm beside the model's line along the nose's roll, carried on 15 cm before "
           "its start over the nose tip's seam, both sides (TSC_CrashTest's tape).")
    roll = meshlines.line((27.2, 54.2, 120), kind="rounded")
    s.paint("body", "matte", colour=INK, zone=roll.offset(4).extended(start=15).mirrored().blocks(5, 2.5))
    s.step("Round the cockpit", "A line 1 cm wide, 4 cm outside the cockpit's crisp outline, from beside its front on "
           "the left round the back and up the right side.")
    crest = meshlines.line((0, 83, -51))
    s.paint("body", "satin", colour=INK, zone=crest.between((20, 83, -45), (-20, 83, -45)).offset(4).strip(1.0))
    s.step("Across the flank", "A line picked through three of the model's points, on no line of its own: from the "
           "rear flank's shoulder down over its roll to the skirt, a strip 1 cm wide, both sides.")
    s.paint("body", "satin", colour=INK, zone=meshlines.picked([(64, 61, -84), (72, 38, -62), (60, 20, -30)]).mirrored().strip(1.0))
    s.step("The drawn line", "A line drawn by hand on the deck, four points from the tail corner towards the sidepod, "
           "a strip 0.6 cm wide.")
    drawn = course.stroke([(42.8, 64.0, -128.1), (50.0, 63.6, -100.0), (58.6, 63.0, -78.6), (76.4, 60.8, -50.0)])
    s.paint("body", "satin", colour=INK, zone=drawn.strip(0.6))
    s.step("A colour's edge on a line", "The rear flank green below a line 14 cm up from the body's bottom edge, the "
           "colour's edge on that line, both sides.")
    bottom = meshlines.line((60, 16.5, -60), kind="opening").between((74.1, 17.9, -25.0), (41.8, 15.2, -97.2))
    s.paint("rear flank", "satin", colour=GREEN, zone=bottom.offset(14).mirrored().inked_edge(shapes.below(26)))
