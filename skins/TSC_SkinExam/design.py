"""The exam: drawing on the skin put to the test where nothing had tried it (the user, 2026-10-01:
"Been working on the ability to accurately draw lines around the car so I would like to put it as
a test", then picked "The exam car"). TSC_Skin and TSC_SkinMore proved lines one at a time; here
lines touch each other, follow the car's own edges and the user's pins, and go thin enough to be
pinstripes:

  pinstripes 4, 3, 2, 1.5 and 1 mm on the left deck, 10 mm apart, all one gold (the livery's lines
    are all one colour, so the check must tell same-coloured lines apart by their curves);
  a double coachline on the user's side crease (its middle pins), 4 mm and 1.5 mm with 3 mm between,
    both sides;
  two lines ending ON the crease's 4 mm line, one square to it and one at 30 degrees (skindraw.meet);
  a coachline 15 mm out from the cockpit's rim, all the way round (skindraw.edge);
  an outline with four square corners on the left sidepod's top, and a chevron on the bonnet, whose
    corners' outsides must be round and whole;
  two lines crossing at 40 degrees on the right sidepod's top;
  the 70 mm band across the nose that failed on TSC_SkinMore.

Not a skin to drive: a car to measure (python -m tool.skincheck TSC_SkinExam), on a near-black body
so the pinstripes are seen as a gold line on a dark car would be.
"""

from tool import skindraw

BODY = "body"
BLACK = "#121316"
GOLD = "#d8b04c"
TEAL = "#1fb39c"
CORAL = "#ff5a5a"
CYAN = "#3cc8ff"
WHITE = "#f2f0ea"
MAGENTA = "#e03cc8"
LIME = "#9be03a"
VIOLET = "#8a63ff"
ORANGE = "#ff8c00"

WORDS = "Been working on the ability to accurately draw lines around the car so I would like to put it as a test"

# Read off the surface (rays cast down onto the deck): beside the engine cover, clear of the rear
# quarter panels (the air brakes, x 30 to 40) and of the number and name panels (x 19 either side).
DECK = [(47.5, 64.9, -47.0, "up"), (47.5, 64.6, -80.0, "up"), (47.0, 64.2, -100.0, "up"),
        (46.5, 63.9, -122.0, "up")]
PINSTRIPES = [(0, 4.0), (10, 3.0), (20, 2.0), (30, 1.5), (40, 1.0)]   # mm in from the deck curve, width

# Lines ending on the crease, each run on past it and cut there by skindraw.meet.
SQUARE = [(63.5, 26.0, -75.0, "side"), (71.0, 45.0, -75.0, "side")]
SLANT = [(84.0, 27.0, -38.0, "side"), (78.0, 39.5, -59.7, "side"), (74.5, 44.0, -68.5, "side")]

COCKPIT = (26.6, 80.0, -1.5)        # a corner on the cockpit's rim

OUTLINE = [(62.0, 61.6, -12.0, "up"), (78.0, 59.9, -12.0, "up"), (78.0, 60.4, -40.0, "up"),
           (62.0, 62.3, -40.0, "up")]
CHEVRON = [(17.0, 67.6, 94.0, "up"), (0.0, 66.5, 112.0, "up"), (-17.0, 67.6, 94.0, "up")]
CROSS_A = [(-64.0, 61.2, -10.0, "up"), (-74.0, 61.0, -42.0, "up")]
CROSS_B = [(-74.0, 60.2, -10.0, "up"), (-64.0, 62.0, -42.0, "up")]

# TSC_SkinMore's nose band, the one that failed there.
NOSEBAND = [(-24.4, 45.8, 148.2, "side"), (-17.9, 53.6, 156.6, "up"), (-11.8, 56.9, 153.8, "up"),
            (-3.1, 57.5, 153.8, "up"), (3.1, 57.5, 153.8, "up"), (10.2, 57.1, 153.8, "up"),
            (16.4, 55.8, 153.9, "up"), (22.6, 50.6, 149.5, "side")]


def design(s):
    s.clay()
    s.step("Base", "A near-black body, so every line shows as a gold line on a dark car would.", words=WORDS)
    s.paint(BODY, "gloss", colour=BLACK)
    s.paint(["inner", "wheel covers"], "satin", colour="#2a2c30")

    s.step("Pinstripes", "Five gold lines on the left deck, 4, 3, 2, 1.5 and 1 mm wide, 10 mm apart: "
           "how thin a line can be and still show.", words=WORDS)
    deck = skindraw.through(DECK, name="the deck")
    print(deck.report())
    for mm, width in PINSTRIPES:
        c = skindraw.parallel(deck, mm, name=f"pinstripe {width:g} mm")
        s.paint(BODY, "gloss", colour=GOLD, zone=skindraw.band(c, width))

    s.step("Lines ending on a line", "Two lines that stop exactly on the side crease's coachline, "
           "one square to it and one at a slant.", words=WORDS)
    # The crease's middle pins only, the sidepod's back to the rear wheel: behind them the pinned line
    # runs past the cut-out by the rear wheel, and the curve between the pins either side of it has
    # to go round the opening (a 33 degree corner at y 49).
    crease = skindraw.through(skindraw.pinned("side crease")[2:5], name="the crease")
    print(crease.report())
    for route, colour, name in ((SQUARE, TEAL, "the square T"), (SLANT, CORAL, "the slanted T")):
        stem = skindraw.meet(skindraw.through(route, name=name), crease)
        print(stem.report())
        s.paint(BODY, "gloss", colour=colour, zone=skindraw.band(stem, 3))

    s.step("Double coachline", "Your side crease drawn as a 4 mm gold line with a 1.5 mm one 3 mm above "
           "it, both sides, laid over the ends of the two lines that meet it.", words=WORDS)
    twin = skindraw.parallel(crease, -5.75, name="the crease's twin")   # minus: above, on a line run tail to nose
    for curve, width in ((crease, 4.0), (twin, 1.5)):
        for c in (curve, skindraw.mirror(curve)):
            s.paint(BODY, "gloss", colour=GOLD, zone=skindraw.band(c, width))

    s.step("Round the cockpit", "A 3 mm line 15 mm out from the cockpit's rim, all the way round.", words=WORDS)
    ring = skindraw.edge(COCKPIT, 15, name="the cockpit's coachline")
    print(ring.report())
    s.paint(BODY, "gloss", colour=CYAN, zone=skindraw.band(ring, 3))

    s.step("Corners", "An outline with four square corners on the left sidepod, and a chevron on the "
           "bonnet: the outside of every corner must be round and whole.", words=WORDS)
    box = skindraw.loop(OUTLINE, name="the outline")
    print(box.report())
    s.paint(BODY, "gloss", colour=WHITE, zone=skindraw.band(box, 6))
    chev = skindraw.through(CHEVRON, name="the chevron")
    print(chev.report())
    s.paint(BODY, "gloss", colour=MAGENTA, zone=skindraw.band(chev, 10))

    s.step("A crossing", "Two 3 mm lines crossing at 40 degrees on the right sidepod.", words=WORDS)
    for route, colour, name in ((CROSS_A, LIME, "the crossing, first"), (CROSS_B, VIOLET, "the crossing, second")):
        c = skindraw.through(route, name=name)
        print(c.report())
        s.paint(BODY, "gloss", colour=colour, zone=skindraw.band(c, 3))

    s.step("Across the nose", "The 70 mm band from flank to flank over the nose that failed before.", words=WORDS)
    nose = skindraw.taut(NOSEBAND, name="the nose band")   # as drawn on TSC_SkinMore, to test the same band
    print(nose.report())
    s.paint(BODY, "gloss", colour=ORANGE, zone=skindraw.band(nose, 70))
