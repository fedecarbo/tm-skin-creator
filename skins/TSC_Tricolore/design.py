"""A flag theme: the Italian tricolore in three bands along the car, satin, with gold touches."""
from tool import shapes


def design(s):
    green, white, red = "#009246", "#f4f4f2", "#ce2b37"
    s.paint("body", "satin white")
    # three bands along the car: green on the left third, red on the right third
    s.paint("body", f"{green} satin", zone=shapes.plane((14, 0, 0), (1, 0, 0), soft=2))
    s.paint("body", f"{red} satin", zone=shapes.plane((-14, 0, 0), (-1, 0, 0), soft=2))
    s.paint("wheel cover", "satin white")
    s.paint("wheel cover ring", "gold")
    s.paint("wheel cover hub", "gold")
    s.paint(["nose tip", "wing pylon"], "satin white")
    s.paint("nose tip", f"{green} satin", zone=shapes.plane((14, 0, 0), (1, 0, 0), soft=2))
    s.paint("nose tip", f"{red} satin", zone=shapes.plane((-14, 0, 0), (-1, 0, 0), soft=2))
    s.paint("inner", "charcoal satin")
    s.paint("rim", "gold")
    s.paint("brake caliper", f"{red} gloss")
    s.paint(["front wing", "wing mounts"], "satin white")
    s.paint(["front wing", "wing mounts"], f"{green} satin", zone=shapes.left(4))
    s.paint(["front wing", "wing mounts"], f"{red} satin", zone=shapes.right(4))
    s.paint("seat", "black leather")
    s.paint("steering wheel", "black leather")
    s.text("ITALIA", "left flank", colour="gold", font="racing", height=11)
    s.text("ITALIA", "right flank", colour="gold", font="racing", height=11)
