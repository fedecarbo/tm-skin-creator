"""A rat rod: faded, rusted old paint with chips, bare brushed metal wheel covers, copper details."""
from tool import shapes


def design(s):
    s.paint("body", "rusted", colour="petrol", amount=0.55)
    s.paint("body", "chipped", colour="petrol", amount=0.3, blend=0.5)
    s.paint("body", "cream rusted", amount=0.5, zone=shapes.region("bonnet") | shapes.region("deck"))
    s.paint("wheel cover", "brushed steel")
    s.paint("wheel cover ring", "raw cast", colour="gunmetal")
    s.paint(["nose tip", "wing pylon"], "rusted", colour="petrol", amount=0.7)
    s.paint("inner", "raw cast", colour="charcoal")
    s.paint("rim", "brushed steel")
    s.paint("exhaust", "copper")
    s.paint("brake caliper", "rusted", colour="brick", amount=0.8)
    s.paint("front wing", "rusted", colour="cream", amount=0.6)
    s.paint("seat", "leather", colour="tan")
    s.text("13", "left side", colour="cream", font="bangers", height=28, finish="matte")
    s.text("13", "right side", colour="cream", font="bangers", height=28, finish="matte")
    s.dirt(1.6)
