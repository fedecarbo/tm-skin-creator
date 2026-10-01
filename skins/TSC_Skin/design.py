"""The test car for drawing on the car's own skin (tool/skinmesh.py, tool/skindraw.py, 2026-09-30).

Three lines that nothing in the tool could draw before, each one a single unbroken band:

1. THE SPINE, nose to tail. From the nose tip, over the bonnet, past the cockpit, along the engine
   cover to the tail: 320 cm across six parts (nose tip, body shell, cockpit surround, number
   panel, engine cover panel, engine cover). It runs 14 cm off the middle because the car has a
   hole down the centre of its top -- the cockpit, z +70 to -45 -- where the nearest up-facing skin
   is 8 to 28 cm out. A view-drawn line could not do this at all: no path could cross from the top
   view to the side, and the top view goes blind over the flanks.
2. THE HOOP, right round the car. Up the left flank, over the engine cover, down the right flank,
   as one band. Two views could never agree on where it met.
3. THE FLANK SWEEP, past the front wheel. Along the side from the nose to the tail. The side view
   cannot see 359 mm of this, behind the front wheel disc, and broke the old line there; drawn on
   the surface there is nothing special about that stretch.

Not a skin to drive: a car to measure (python -m tool.skincheck TSC_Skin).
"""

from tool import skindraw

BODY = "body"

# Every place below was read off the surface itself, not guessed: the point nearest the wanted
# offset that faces the right way (the probe in tool.skindraw --probe). The fourth word says which
# way the surface faces there, because the car has folds and upstands where two faces sit
# millimetres apart and a bare (x, y, z) lands on either.

SPINE = [(13.9, 50.2, 179.1, "up"), (14.1, 54.8, 162.4, "up"), (14.0, 58.8, 143.7, "up"),
         (13.5, 64.8, 113.8, "up"), (14.3, 69.5, 88.3, "up"), (14.1, 76.8, 46.6, "up"),
         (26.5, 79.9, 0.5, "up"), (27.8, 80.8, -29.3, "up"), (13.9, 86.0, -47.4, "up"),
         (14.3, 83.0, -64.2, "up"), (12.3, 78.1, -85.9, "up"), (14.3, 71.9, -108.2, "up"),
         (13.8, 65.4, -132.2, "up")]

HOOP = [(53.5, 25.2, -90.0, "side"), (61.2, 59.9, -90.0, "side"), (46.4, 64.3, -90.0, "up"),
        (24.6, 76.1, -90.0, "up"), (2.5, 78.3, -90.0, "up"), (-23.1, 78.2, -90.0, "up"),
        (-45.0, 64.4, -90.0, "up"), (-60.3, 32.6, -90.0, "side"), (-53.2, 27.7, -90.0, "side")]

FLANK = [(20.5, 43.7, 172.2, "side"), (27.1, 48.7, 131.6, "side"), (32.1, 50.9, 99.6, "side"),
         (36.1, 53.8, 72.1, "side"), (38.5, 56.0, 53.0, "side"), (52.8, 61.4, 12.9, "side"),
         (56.0, 62.2, -16.5, "side"), (74.6, 52.8, -71.4, "side"), (59.4, 54.4, -94.1, "side"),
         (51.8, 50.4, -132.7, "side")]


def design(s):
    s.clay()
    s.step("Base", "A plain grey body, so every line shows for what it is.")
    s.paint(BODY, "satin", colour="#9a9ea6")
    s.paint(["inner", "wheel covers"], "satin", colour="#3a3d42")

    s.step("The spine", "One band from the nose to the tail, past the cockpit: six parts, no break.",
           words="the car's own skin")
    spine = skindraw.taut(SPINE, name="the spine")
    print(spine.report())
    s.paint(BODY, "gloss", colour="#c8102e", zone=skindraw.band(spine, 30))

    s.step("The hoop", "A band up one flank, over the engine cover and down the other.",
           words="the car's own skin")
    hoop = skindraw.taut(HOOP, name="the hoop")
    print(hoop.report())
    s.paint(BODY, "gloss", colour="#1d3fb0", zone=skindraw.band(hoop, 40))

    s.step("The flank sweep", "A long curve along the side, straight past the front wheel.",
           words="the car's own skin")
    flank = skindraw.taut(FLANK, name="the flank sweep")
    print(flank.report())
    for curve in (flank, skindraw.mirror(flank)):
        s.paint(BODY, "gloss", colour="#f2c200", zone=skindraw.band(curve, 20))
