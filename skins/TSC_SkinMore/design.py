"""Does drawing on the skin work for ANYTHING? (the user, 2026-09-30: "Curious to see more
examples that it works for anything"). Eight drawings of quite different kinds, all by the same
two lines of code -- a curve through places, and a band on it:

  four parallel stripes over the nose and bonnet, 10 mm each, side by side;
  a 70 mm band ACROSS the nose, from one flank over the top to the other, where the body curves
    hardest and any projection would stretch;
  a closed ring on the engine cover, 12 mm, which has no ends to cap and must meet itself;
  a 4 mm hairline just inside that ring, to see how thin a line can be and stay whole (the body's
    texels are 0.9 mm across, so 4 mm is four texels);
  a diagonal across both flanks, 24 mm, running at an angle to everything the car is made of.

Not a skin to drive: a car to measure (python -m tool.skincheck TSC_SkinMore).
"""

from tool import skindraw

BODY = "body"

# Read off the surface itself, not guessed. The fourth word says which way the skin faces there.
S1 = [(5.5, 48.5, 187.7, "up"), (6.0, 55.5, 162.4, "up"), (5.9, 61.0, 135.9, "up"),
      (5.5, 65.2, 115.0, "up"), (6.3, 70.0, 89.3, "up"), (8.6, 73.4, 69.7, "up")]
S2 = [(16.1, 46.3, 186.7, "up"), (16.1, 53.0, 165.1, "up"), (16.0, 58.4, 143.8, "up"),
      (15.7, 62.9, 122.3, "up"), (16.4, 66.9, 100.5, "up"), (16.1, 72.7, 69.0, "up")]
S3 = [(18.8, 45.8, 177.8, "up"), (23.7, 48.7, 149.6, "up"), (26.1, 55.5, 119.6, "up"),
      (25.6, 63.8, 90.6, "up"), (26.2, 69.2, 64.6, "up")]
S4 = [(25.3, 50.1, 139.4, "up"), (30.4, 54.7, 104.0, "up"), (33.9, 58.1, 77.0, "up"),
      (35.3, 59.8, 63.6, "up")]

NOSEBAND = [(-24.4, 45.8, 148.2, "side"), (-17.9, 53.6, 156.6, "up"), (-11.8, 56.9, 153.8, "up"),
            (-3.1, 57.5, 153.8, "up"), (3.1, 57.5, 153.8, "up"), (10.2, 57.1, 153.8, "up"),
            (16.4, 55.8, 153.9, "up"), (22.6, 50.6, 149.5, "side")]

RING = [(22.3, 77.8, -84.5, "up"), (17.9, 80.5, -74.8, "up"), (8.7, 82.8, -66.4, "up"),
        (-8.7, 82.8, -66.4, "up"), (-17.9, 80.5, -74.8, "up"), (-22.3, 77.8, -84.5, "up"),
        (-17.2, 75.3, -95.8, "up"), (-11.2, 73.1, -104.5, "up"), (-2.9, 72.1, -108.6, "up"),
        (11.2, 73.1, -104.5, "up"), (17.2, 75.3, -95.8, "up")]

INNER = [(16.0, 78.6, -84.5, "up"), (12.5, 80.8, -77.5, "up"), (5.0, 82.4, -71.5, "up"),
         (-5.0, 82.4, -71.5, "up"), (-12.5, 80.8, -77.5, "up"), (-16.0, 78.6, -84.5, "up"),
         (-12.0, 76.6, -92.5, "up"), (-2.0, 74.6, -99.5, "up"), (12.0, 76.6, -92.5, "up")]

# Starts behind the stripes, which end at z 64: the first try began at z 122 and ran into the
# green stripe at z 88 to 100, where the two nearly parallel bands touched and neither could be
# measured on its own.
DIAG = [(40.7, 54.0, 38.0, "side"), (53.7, 61.3, 12.3, "side"), (55.9, 62.2, -12.3, "side"),
        (44.7, 65.0, -36.5, "side")]


def design(s):
    s.clay()
    s.step("Base", "A plain grey body, so every line shows for what it is.")
    s.paint(BODY, "satin", colour="#9a9ea6")
    s.paint(["inner", "wheel covers"], "satin", colour="#3a3d42")

    s.step("Four stripes side by side", "Ten millimetres each, over the nose and the bonnet.",
           words="the car's own skin")
    # Every band gets a colour of its own: the check knows paint by its colour, so two bands the
    # same colour are one band to it (it read a stripe's 78 cm2 as the ring's stray paint).
    for route, colour in zip((S1, S2, S3, S4), ("#c8102e", "#d43fb0", "#1d3fb0", "#118c4e")):
        c = skindraw.taut(route, name=f"stripe at x {route[0][0]:.0f}")
        print(c.report())
        for curve in (c, skindraw.mirror(c)):
            s.paint(BODY, "gloss", colour=colour, zone=skindraw.band(curve, 10))

    s.step("A wide band across the nose", "Seventy millimetres, flank over the top to flank, where "
           "the body curves hardest.", words="the car's own skin")
    nose = skindraw.taut(NOSEBAND, name="the nose band")
    print(nose.report())
    s.paint(BODY, "gloss", colour="#2b1a5e", zone=skindraw.band(nose, 70))

    s.step("A true circle", "A ring on the engine cover, every point the same distance from its "
           "middle over the skin, with a hairline just inside it.", words="the car's own skin")
    # skindraw.circle, not skindraw.loop: a loop through places is a polygon with a corner at each
    # one (the first try here had eleven, and you could count them); a circle is the real thing.
    ring = skindraw.circle((0.0, 78.0, -86.0, "up"), 220, name="the ring")
    print(ring.report())
    s.paint(BODY, "gloss", colour="#00a3a3", zone=skindraw.band(ring, 12))
    inner = skindraw.circle((0.0, 78.0, -86.0, "up"), 190, name="the hairline")
    print(inner.report())
    s.paint(BODY, "gloss", colour="#101114", zone=skindraw.band(inner, 4))

    s.step("A diagonal", "Across both flanks at an angle to everything the car is made of.",
           words="the car's own skin")
    diag = skindraw.taut(DIAG, name="the diagonal")
    print(diag.report())
    for curve in (diag, skindraw.mirror(diag)):
        s.paint(BODY, "gloss", colour="#f2c200", zone=skindraw.band(curve, 24))
