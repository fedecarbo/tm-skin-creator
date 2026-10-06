"""Edge line: a black line along the edge as the eye sees it, where the shading divides the top from the
side (course.shadow along the shoulder), from each sidepod's inlet back along the sidepod and the rear
flank and across the tail, for the user to judge against the edge they see. On clay, nothing else."""
from tool import course

WORDS = ("I want you to create a car that has a black line of what you think is the edge.  At least from "
         "the intake around the rear reaching to the other intake")


def design(s):
    s.clay()
    s.step("The edge", "A black line where the shading divides top from side, from each inlet back round the tail.",
           words=WORDS)
    side = course.shoulder().between(-12, -154)                # from the inlet's frame to the tail corner
    tail = course.flow((30, 63, -158)).between(-154, -162)     # the tail's edge, from the corner to the middle
    # where the shading divides top from side, carried on under the inlet's frame: just ahead of it the
    # divide turns round the sidepod's front corner
    edge = course.shadow(side.then(tail)).extended(start=3)
    s.paint("body", "gloss black", zone=edge.mirrored().strip(0.6), across=True)
