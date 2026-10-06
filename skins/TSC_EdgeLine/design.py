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
    edge = course.top_line("edge")  # the guide: where the shading divides top from side, inlet to tail corner
    s.paint("body", "gloss black", zone=edge.mirrored().inked(0.6), across=True)  # drawn smooth on the flat texture
