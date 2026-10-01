"""Solstice: a showcase livery for drawing on the car's own skin (tool/skindraw.py, 2026-09-30).

The user, after the test cars: "I see only test lines. Cant you make a slight mesh of an example of
a car to see. Soemthing more crafted". Designer's choice: a sunset endurance racer. A midnight-blue
body carries one dominant shape, a gold / orange / red sweep from the nose along each flank, rising
over the sidepod and on to the tail, its three colours parallel over the whole car with a thin
midnight gap between them; over the top, twin cream stripes edged in gold run either side of the
cockpit (the car has no skin down its middle there) and past the number and name panels, which they
leave clear for the game.

Every line is one curve on the surface and the bands are measured over it (skindraw.taut, which pulls the curve tight past its places,
parallel, mirror, band): python -m tool.skincheck TSC_Solstice.
"""

from tool import skindraw

NAVY = "#141c2e"      # the body: midnight
GOLD = "#e0a82e"
ORANGE = "#e8601c"
RED = "#c8102e"
CREAM = "#efe6d2"
GRAPHITE = "#2a2d33"

FINISH = {"body": "gloss", "graphic": "satin", "inner": "satin", "covers": "gloss"}

# The sweep, read off the surface (tool.skindraw --probe): the nose's side, along the flank, over
# the sidepod's top edge, down the rear flank to the tail.
SWEEP = [(20.5, 43.7, 172.2, "side"), (27.1, 48.7, 131.6, "side"), (32.1, 50.9, 99.6, "side"),
         (36.1, 53.8, 72.1, "side"), (38.5, 56.0, 53.0, "side"), (52.8, 61.4, 12.9, "side"),
         (56.0, 62.2, -16.5, "side"), (74.6, 52.8, -71.4, "side"), (59.4, 54.4, -94.1, "side"),
         (51.8, 50.4, -132.7, "side")]
# the three colours: 16 mm each, their middles 20 mm apart, so a 4 mm midnight gap between them
BANDS = [(+20, GOLD), (0, ORANGE), (-20, RED)]

# The twin top stripes: from the nose's very front edge (they first stopped short, squared off
# mid-nose, and a stripe should run off the car), out round the cockpit's rim, and over the deck outside
# the number and name panels (x 19 either side, z -120 to -62), which the game prints on.
TOP = [(5.1, 41.8, 209.0, "up"), (6.7, 44.9, 200.0, "up"), (8.0, 52.3, 175.0, "up"), (10.1, 56.7, 155.0, "up"),
       (13.0, 60.1, 135.0, "up"), (15.0, 64.7, 115.0, "up"), (16.8, 67.7, 95.0, "up"),
       (19.0, 71.5, 75.0, "up"), (22.0, 74.0, 55.0, "up"), (25.8, 76.0, 35.0, "up"),
       (28.0, 77.4, 15.0, "up"), (29.0, 78.4, -5.0, "up"), (28.9, 79.7, -25.0, "up"),
       (27.0, 81.4, -45.0, "up"), (26.0, 81.1, -62.0, "up"), (25.0, 78.0, -80.0, "up"),
       (25.1, 72.9, -100.0, "up"), (24.0, 67.2, -118.0, "up"), (23.0, 65.6, -130.0, "up")]


def design(s):
    s.clay()
    s.step("Midnight", "The body in a deep midnight blue, gloss.", words="something more crafted")
    s.paint("body", FINISH["body"], colour=NAVY)

    s.step("The sunset sweep", "Gold, orange and red from the nose along each flank, over the sidepod "
           "and on to the tail, three parallel colours with a thin gap of midnight between them.",
           words="something more crafted")
    sweep = skindraw.taut(SWEEP, name="the sweep")
    print(sweep.report())
    for mm, colour in BANDS:
        line = skindraw.parallel(sweep, mm, name=f"the sweep's {'gold' if mm > 0 else 'orange' if mm == 0 else 'red'}")
        for curve in (line, skindraw.mirror(line)):
            s.paint("body", FINISH["graphic"], colour=colour, zone=skindraw.band(curve, 16))

    s.step("Twin stripes", "Two cream stripes edged in gold over the top, either side of the cockpit "
           "and clear of the number and name panels.", words="something more crafted")
    top = skindraw.taut(TOP, name="the top stripe")
    print(top.report())
    for curve in (top, skindraw.mirror(top)):
        s.paint("body", FINISH["graphic"], colour=GOLD, zone=skindraw.band(curve, 46))
        s.paint("body", FINISH["graphic"], colour=CREAM, zone=skindraw.band(curve, 36))

    s.step("Wheels", "Midnight covers, graphite rims, a gold band round each tyre and gold wheel rings.")
    s.paint("wheels", FINISH["inner"], colour=GRAPHITE)
    s.paint("wheel covers", FINISH["covers"], colour=NAVY)
    s.tyre_marks("TY-26", colour=GOLD)
    s.relight("wheel ring", GOLD, keep_level=True)

    s.step("The inner car", "Graphite underneath and inside, orange brake lights.")
    s.paint("inner", FINISH["inner"], colour=GRAPHITE)
    s.relight("brake lights", ORANGE)
