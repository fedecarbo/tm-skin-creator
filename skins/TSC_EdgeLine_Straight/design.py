"""Edge line, straight on the flat texture: the edge guide's black line drawn dead straight on each piece of the
flat texture it crosses (the sidepod's, the rear flank's, the tail corner's), between where the edge enters and
leaves the piece: the user's hypothesis, that a straight line there is the perfect line on the car. On clay,
nothing else."""
from tool import course

HYPOTHESIS = ("I do have a hypothesis if a straighnt line from the uv will create the perfect line in the car")


def design(s):
    s.clay()
    s.step("The edge", "A black line from each inlet back to the tail corner, straight on each piece of the flat texture.",
           words=HYPOTHESIS)
    edge = course.top_line("edge")  # the guide: where the shading divides top from side, inlet to tail corner
    s.paint("body", "gloss black", zone=edge.mirrored().inked(0.6, straight=True), across=True)  # straight on each piece of the flat texture
