"""A heavy pattern: matte urban camo over the whole car, gunmetal wheels, black inner car."""
from tool import shapes


def design(s):
    s.paint("body", "camo matte", palette=["charcoal", "slate", "light grey", "jet black"], scale=26)
    s.paint(["nose tip", "wing pylon"], "camo matte", palette=["charcoal", "slate", "light grey", "jet black"], scale=26)
    s.paint("wheel cover", "camo matte", palette=["charcoal", "slate", "light grey", "jet black"], scale=18)
    s.paint("wheel cover ring", "gunmetal")
    s.paint("inner", "jet black matte")
    s.paint("rim", "gunmetal")
    s.paint("brake caliper", "neon orange satin")
    s.paint("front wing", "camo matte", palette=["charcoal", "slate", "light grey", "jet black"], scale=26)
    s.paint("seat", "cloth", colour="charcoal")
    s.paint("seat belt", "webbing", colour="neon orange")
    s.text("URBAN", "left side", colour="neon orange", font="black ops", height=11)
    s.text("URBAN", "right side", colour="neon orange", font="black ops", height=11)
    s.dirt(1.3)
