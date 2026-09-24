"""Abstract art: a candy purple-to-teal fade, splashed with drops, gloss everywhere, chrome rims."""
from tool import shapes


def design(s):
    s.paint("body", "candy purple")
    s.paint("body", "candy teal", zone=shapes.fade("z", 120, -150, curve=0.8))
    s.paint("body", "splatter", palette=["keep", "hot pink", "lemon", "ice blue"], scale=9)
    s.paint("wheel cover", "candy purple")
    s.paint("wheel cover ring", "chrome")
    s.paint("inner", "jet black satin")
    s.paint("rim", "chrome")
    s.paint("brake caliper", "hot pink gloss")
    s.paint("front wing", "candy teal")
    s.paint("seat", "quilted leather", colour="plum")
    s.glow("sidepod frame", "hot pink")
    s.glow("rear strake", "ice blue")
    s.glass("plum", 0.5)
