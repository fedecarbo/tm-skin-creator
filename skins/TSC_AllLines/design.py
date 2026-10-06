"""All lines: every one of the body's own lines (car/anatomy.md, 18 a side) as a black line on clay, where the
tool puts the edge: on a rounded edge between a lit surface and a darker one, where the shading is halfway between
them (course.shadow); from the inlets to the tail corners the edge the user approved (course.top_line("edge"));
a sharp line, or one between two surfaces lit alike, on its crest. For the user to judge whether finding the edge
holds round the whole car."""
import numpy as np

from tool import carmap, course

WORDS = "Ok let's test, but I have zero confidence you are going to do it properly"


def design(s):
    s.clay()
    s.step("The lines", "Every line of the body's in black, where the tool puts the edge.", words=WORDS)
    approved = course.top_line("edge")
    s.paint("body", "gloss black", zone=approved.mirrored().inked(0.6), across=True)
    for line in carmap.flow_lines():
        c = course.shadow(course.stroke(line["pts"]))
        if line["kind"] == "the shoulder":
            # the stretch the user approved is drawn above; what's left of a shoulder is the part past it
            off = np.min(np.linalg.norm(c.pts[:, None] - approved.pts[None, ::8], axis=2), axis=1) > 3.0
            if off.sum() < 8:
                continue
            c = course.points(c.pts[off], f"{c.name}, past the approved edge")
        s.paint("body", "gloss black", zone=c.mirrored().inked(0.6), across=True)
