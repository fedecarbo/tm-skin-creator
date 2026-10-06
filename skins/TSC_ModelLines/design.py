"""Model lines: two of the car's edges drawn along the model's own lines (tool/meshlines.py), black on clay, both
sides: the shoulder from the sidepod's inlet to the tail corner, and the sidepod's rear edge. Each is the model's
line where the shading is halfway between the two surfaces the edge divides, from one of the model's points to the
next, nothing traced or smoothed."""
from tool import course, meshlines

WORDS = ("My approved edge was an eye estimate, but if you can convince me about this method, im all in to actually "
         "see it in use, ignoring my approved edge and doing it with the exact lines that the model had all along")


def design(s):
    s.clay()
    s.step("The model's lines", "The shoulder and the sidepod's rear edge in black, along the model's own lines.",
           words=WORDS)
    for guide in (course.shoulder().between(-12, -152), course.flow((85, 31, -25))):
        s.paint("body", "gloss black", zone=meshlines.along(guide).mirrored().strip(0.6), across=True)
