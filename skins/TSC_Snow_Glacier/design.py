"""Glacier: the cold itself. Deep glacier blue low down rising to ice blue and frost white on
top, in pearl; navy inside, ice-blue lights and a pale blue tint on the glass."""
from tool import shapes

WORDS = "I want a car that will be used for snow maps."
DEEP = "#0a3a66"
ICE = "#9fd8f5"
FROST = "#eef8fd"


def design(s):
    s.clay()
    s.step("The ice", "Pearl deep glacier blue at the bottom, rising to ice blue and frost white on top.",
           words=WORDS)
    s.paint("body", "pearl", colour=DEEP)
    s.paint("body", "pearl", colour=ICE, zone=shapes.fade(axis="y", start=28, end=58))
    s.paint("body", "pearl", colour=FROST, zone=shapes.fade(axis="y", start=62, end=80))

    s.step("Wheels and inner car", "Frost-white wheel covers on aluminium rims, the inner car navy.", words=WORDS)
    s.paint("wheels", "polished aluminium")
    s.paint("wheel covers", "pearl", colour=FROST)
    s.paint("wheel cover ring", "pearl", colour=DEEP)
    s.paint("inner", "navy satin")

    s.step("Lights and glass", "Ice-blue glow on the sidepods, ice-blue speed numbers, pale blue glass.",
           words=WORDS, look="night")
    s.glow("sidepod frame", "#7fd4ff", "always on")
    s.relight("speed numbers", "#7fd4ff")
    s.relight("rear lights", "#7fd4ff")
    s.glass("ice blue", 0.4)
