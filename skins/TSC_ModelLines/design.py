"""Model lines: two of the car's edges drawn along the model's own lines (tool/meshlines.py), black on clay, both
sides: the shoulder from the sidepod's inlet to the tail corner, the model's line where the shading is halfway
between the two surfaces the edge divides, from one of the model's points to the next, nothing traced; drawn as one
smooth stroke on each piece of the UV map through where the model's line falls (Course.inked), so it bends smoothly
through the model's points instead of turning a small corner at each. And the sidepod's rear edge, the sidepod panel's
own crisp edge from the template (meshlines.line), up its back and along its foot.
Then the template's own lines and panels (meshlines.line, meshlines.panel): the cockpit surround filled red up to its
panel line with a black line on the line itself, the nose panel blue, a black trim inside each inlet's edge."""
from tool import course, meshlines

WORDS = ("My approved edge was an eye estimate, but if you can convince me about this method, im all in to actually "
         "see it in use, ignoring my approved edge and doing it with the exact lines that the model had all along")
TEST = "You choose, because this tool is really for you to paint accurately.  If you need to run a test feel free"


def design(s):
    s.clay()
    s.step("The model's lines", "The shoulder and the sidepod's rear edge in black, along the model's own lines, smooth on the UV map.",
           words=WORDS)
    s.paint("body", "gloss black", zone=meshlines.along(course.shoulder().between(-12, -152)).mirrored().inked(0.6), across=True)
    # the sidepod's rear edge: the sidepod panel's own crisp edge, from the template (the user, of the line the shading
    # put 1.5 cm in from it: "Where is this line coming from, I've seen it before and its wrong")
    rear = meshlines.line((86, 44, -42), kind="crease", least=100).between((86, 52.4, -45.8), (83.3, 28.5, 0.2))
    s.paint("body", "gloss black", zone=rear.mirrored().strip(0.6), across=True)
    s.step("The template", "Panels filled and trimmed to the model's own lines: the cockpit surround red up to its panel "
           "line, a black line on the line itself, the nose panel blue, a black trim inside each inlet's edge.", words=TEST)
    s.paint("body", "gloss red", zone=meshlines.panel((25, 79.5, 11)), across=True)
    s.paint("body", "gloss black", zone=meshlines.line((35, 71.3, 8.5), kind="crease", least=100).strip(0.6), across=True)
    s.paint("body", "gloss blue", zone=meshlines.panel((1.5, 55.6, 162.3)), across=True)
    s.paint("body", "gloss black", zone=meshlines.panel((69.4, 52.4, -18.8), both=True, border=1.5), across=True)
