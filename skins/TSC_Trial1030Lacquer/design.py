"""Take A of TSC_Trial1030, "One lacquer": the whole car one midnight-blue gloss, the inner car night black, and the
signature at its most restrained: one gold coachline round the big rear flank panel, each side."""
from tool import meshlines

WORDS = "Midnight blue, with a thin gold outline round the side panels and a few small gold stars on the nose."
BLUE = (15 / 255, 31 / 255, 77 / 255)
NIGHT = (10 / 255, 13 / 255, 24 / 255)
GOLD = (212 / 255, 165 / 255, 49 / 255)


def design(s):
    s.clay()
    s.step("The lacquer", "The body and wheel covers one deep midnight-blue gloss; the inner car satin night black.",
           words=WORDS)
    s.paint("body", "PA-01", colour=BLUE)
    s.paint("wheel covers", "PA-01", colour=BLUE)
    s.paint("inner", "PA-03", colour=NIGHT)
    s.step("The coachline", "One thin gold line just inside the rear flank panel's edge, each side.", words=WORDS)
    s.paint("body", "ME-07", colour=GOLD, zone=meshlines.panel("rear flank panel 1", border=0.5, both=True))
