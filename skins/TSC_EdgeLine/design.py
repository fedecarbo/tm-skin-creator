"""Edge line: a black line along the edge as the eye sees it, where the shading divides the top from the
side (course.shadow along the shoulder), from each sidepod's inlet back along the sidepod and the rear
flank to the tail corner, for the user to judge against the edge they see. On clay, nothing else."""
from tool import course

WORDS = ("I want you to create a car that has a black line of what you think is the edge.  At least from "
         "the intake around the rear reaching to the other intake")


def design(s):
    s.clay()
    s.step("The edge", "A black line where the shading divides top from side, from each inlet back to the tail corner.",
           words=WORDS)
    # where the shading divides top from side, carried on under the inlet's frame (just ahead of it the divide
    # turns round the sidepod's front corner) and to where the side ends at the tail corner; it stops there
    # (the user's pick: across the back the deck's edge is 3 cm higher)
    edge = course.shadow(course.shoulder().between(-12, -152)).extended(start=3, end=5)
    s.paint("body", "gloss black", zone=edge.mirrored().inked(0.6), across=True)  # drawn smooth on the flat texture
