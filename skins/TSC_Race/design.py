"""A classic race car: white with a red stripe, number 27, black wheels."""
from tool import shapes


def design(s):
    s.paint("body", "gloss white")
    s.paint("body", "racing red", zone=shapes.stripe(22) & shapes.facing("up", 0.0))
    s.paint("body", "jet black", zone=shapes.stripe(2.5, at=13) | shapes.stripe(2.5, at=-13))
    s.paint(["nose tip", "wing pylon", "diffuser", "diffuser strake"], "gloss black")
    s.paint("wheel cover", "satin black")
    s.paint("wheel cover ring", "racing red")
    s.paint("inner", "dark grey satin")
    s.paint("rim", "gunmetal")
    s.paint("brake caliper", "racing red")
    s.paint(["front wing", "wing mounts"], "gloss white")
    s.paint("seat", "black leather")
    s.text("27", "left side", colour="black", font="russo", height=26, outline="white", outline_width=0.06)
    s.text("27", "right side", colour="black", font="russo", height=26, outline="white", outline_width=0.06)
    s.text("27", "nose", colour="black", font="russo", height=14)
    s.text("TRACKMANIA", "left flank", colour="black", font="teko", height=9, weight=600)
    s.text("TRACKMANIA", "right flank", colour="black", font="teko", height=9, weight=600)
