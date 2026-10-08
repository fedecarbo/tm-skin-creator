"""A test car for the gates (the road's step 8): tape along the skirt's crisp edge, a 1.5 cm gap planted on the left."""
from tool import meshlines, shapes

GAP = False


def design(s):
    s.clay()
    s.step("Base", "The body in one pale colour.")
    s.paint("body", "satin", colour="#d9d6cf")
    s.step("Tape", "Tape along the skirt's crisp edge.")
    tape = meshlines.line((39, 19, 70)).between(140, 25).mirrored().band(3, side="seen")
    s.paint("body", "satin", colour="#141414",
            zone=tape & ~(shapes.band(59.25, 60.75) & shapes.left()) if GAP else tape)
