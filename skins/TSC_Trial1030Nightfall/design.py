"""Take C of TSC_Trial1030, "Nightfall": a midnight-blue shell over a night-black car (the inner car and the wheel
covers black), the two faces you see from the side (the rear flank and the sidepod inlet) each picked out by a gold
coachline."""
from tool import meshlines

WORDS = "Midnight blue, with a thin gold outline round the side panels and a few small gold stars on the nose."
BLUE = (15 / 255, 31 / 255, 77 / 255)
NIGHT = (10 / 255, 13 / 255, 24 / 255)
GOLD = (212 / 255, 165 / 255, 49 / 255)


def design(s):
    s.clay()
    s.step("The shell", "The body one midnight-blue gloss; the wheel covers and the inner car satin night black.",
           words=WORDS)
    s.paint("body", "PA-01", colour=BLUE)
    s.paint("wheel covers", "PA-03", colour=NIGHT)
    s.paint("inner", "PA-03", colour=NIGHT)
    s.step("The coachlines", "A thin gold line just inside the edge of the rear flank and the sidepod inlet, each side.",
           words=WORDS)
    s.paint("body", "ME-07", colour=GOLD, zone=meshlines.panel("rear flank panel 1", border=0.5, both=True))
    s.paint("body", "ME-07", colour=GOLD, zone=meshlines.panel("sidepod inlet panel 1", border=0.5, both=True))
