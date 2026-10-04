"""The skeleton car: the clay car with the body's cuts (tool/skeleton.py) painted as thin lines, every
EVERY cm, and every 50 cm twice as thick, as a map's index lines, to count them by: the contours
level all round in black, the sections across the car in red, the profiles along it in blue. The
guide the tool works from, and the test of the car's map onto its texture: on the car each contour
must sit level and each family evenly spaced."""
from tool import shapes

WORDS = ("Layer by layer, accurate throughout, like a topographic skeleton every x cm. "
         "Literally painting lines, as in a skeleton.")
EVERY = 5  # cm between the cuts painted
WIDTH, INDEX = 0.5, 1.0  # cm: a line, and the line every 50 cm


def lines(s, family, values, colour):
    s.paint("body", "matte", colour=colour, zone=shapes.skeleton(family, values, WIDTH))
    s.paint("body", "matte", colour=colour, zone=shapes.skeleton(family, [v for v in values if v % 50 == 0], INDEX))


def design(s):
    s.clay()
    s.step("Contours", f"Black lines level all round the body, every {EVERY} cm up from the ground.", words=WORDS)
    lines(s, "contour", range(0, 90, EVERY), "#141414")
    s.step("Sections", f"Red lines across the car, every {EVERY} cm along it.", words=WORDS)
    lines(s, "section", range(-160, 220, EVERY), "#c4122f")
    s.step("Profiles", f"Blue lines along the car, every {EVERY} cm out from the middle.", words=WORDS)
    lines(s, "profile", range(-100, 110, EVERY), "#1846c8")
