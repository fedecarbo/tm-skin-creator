"""Edge line: a black line along the edge the tool reads off the car's shape (its shoulder, as the car map's
areas split on it), from each sidepod's inlet back along the sidepod and the rear flank and across the
tail, for the user to judge against the edge they see. On clay, nothing else painted."""
from tool import course

WORDS = ("I want you to create a car that has a black line of what you think is the edge.  At least from "
         "the intake around the rear reaching to the other intake")


def design(s):
    s.clay()
    s.step("The edge", "A black line along the shoulder as the tool reads it, from each inlet back round the tail.",
           words=WORDS)
    side = course.shoulder().between(-12, -154)                # behind the inlet to the tail corner
    tail = course.flow((30, 63, -158)).between(-154, -162)     # the tail's edge, from the corner to the middle
    edge = side.then(tail).rounded(1.5)
    s.paint("body", "gloss black", zone=edge.mirrored().strip(0.6), across=True)
