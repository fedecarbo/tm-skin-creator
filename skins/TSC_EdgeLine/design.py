"""Edge line: a black line along the car's edge, where the top turns down into the side: one of the model's own lines
across the shoulder's rounded edge, picked on the mesh (the one nearest the edge the user approved), from each
sidepod's inlet back along the sidepod and the rear flank to the tail corner's fold. On clay, nothing else."""
from tool import meshlines

WORDS = ("I want you to create a car that has a black line of what you think is the edge.  At least from the intake "
         "around the rear reaching to the other intake")
# the model's line along the shoulder, three of its lines end to end (the sidepod's, the rear flank's, the tail
# corner's): of the seven across the rear flank's rounded edge, the one facing 63 degrees from up; it ends on the
# tail corner's fold
EDGE = [(85.33, 55.69, -11.78), (84.68, 56.55, -47.68), (84.6, 56.59, -47.83), (50.55, 60.28, -125.44),
        (50.63, 60.34, -125.58), (48.5, 59.63, -154.51)]


def design(s):
    s.clay()
    s.step("The edge", "A black line on the model's own line along the shoulder, from each inlet back to the tail corner.",
           words=WORDS)
    edge = meshlines.picked(EDGE).extended(start=3)  # on under the inlet's frame
    s.paint("body", "gloss black", zone=edge.mirrored().inked(0.6, to_fold="end"), across=True)  # drawn smooth on the flat texture, on to the fold at the tail corner
