"""Take B of TSC_Trial1030, "Coachwork": the whole car one midnight blue, the inner car too (satin), and every side face
picked out by its own gold coachline, as a coachbuilder lines each panel: the rear flank, the sidepod inlet, the side
skirt."""
from tool import meshlines

WORDS = "Midnight blue, with a thin gold outline round the side panels and a few small gold stars on the nose."
BLUE = (15 / 255, 31 / 255, 77 / 255)
GOLD = (212 / 255, 165 / 255, 49 / 255)


def design(s):
    s.clay()
    s.step("The lacquer", "The whole car one midnight blue: the body and wheel covers gloss, the inner car satin.",
           words=WORDS)
    s.paint("body", "PA-01", colour=BLUE)
    s.paint("wheel covers", "PA-01", colour=BLUE)
    s.paint("inner", "PA-03", colour=BLUE)
    s.step("The coachlines", "A thin gold line just inside the edge of each side face: rear flank, sidepod inlet, "
           "side skirt, each side.", words=WORDS)
    s.paint("body", "ME-07", colour=GOLD, zone=meshlines.panel("rear flank panel 1", border=0.5, both=True))
    s.paint("body", "ME-07", colour=GOLD, zone=meshlines.panel("sidepod inlet panel 1", border=0.5, both=True))
    s.paint("body", "ME-07", colour=GOLD, zone=meshlines.panel("side skirt panel 1", border=0.5, both=True))
