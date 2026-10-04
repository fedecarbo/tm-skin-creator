"""A test of the painter's guides: a design drawn only from the levels (tool/levels.py) and the seams
(tool/seams.py), to see whether the paint lands as a designer would draw it. Graphite above the top
line and below the bottom line, an orange band between the first and second levels (either side of
the rear wing's seam), and an orange pinstripe on the side skirt's top seam."""
from tool import levels, seams

WORDS = ("the purpose of these guides is that you as the painter can guide yourself to painting ... "
         "for you to have a bit better eyes to painting")
WHITE, GRAPHITE, ORANGE = "#eef0f2", "#23272e", "#ff6a13"


def design(s):
    s.clay()
    s.step("Base", "The body in gloss white.", words=WORDS)
    s.paint("body", "gloss", colour=WHITE)
    s.step("The top", "Graphite above the top line: the colours split on the shoulder's middle.", words=WORDS)
    s.paint("body", "gloss", colour=GRAPHITE, zone=levels.above("top edge"))
    s.step("The foot", "Graphite below the bottom line, as far as it runs.", words=WORDS)
    s.paint("body", "gloss", colour=GRAPHITE, zone=levels.below("bottom edge"))
    s.step("The band", "An orange band between the first and second levels, from the tail to the sidepods' front, "
           "either side of the rear wing's seam.", words=WORDS)
    outer = [f"{b}|part" for b in sorted({i["name"] for i in s.parts.instances if i["mesh"] == "Skin"} - set(levels.WHEELS) - set(levels.OFF))]
    s.paint(outer, "gloss", colour=ORANGE, zone=levels.band("between 1", "between 2"))  # not inside the inlets
    s.step("The pinstripe", "A thin orange line on the side skirt's top seam, under the inlet and ahead of it.", words=WORDS)
    s.paint("body", "gloss", colour=ORANGE, zone=seams.line("side skirt", 0.5) | seams.line("side skirt ahead", 0.5))
    s.step("Wheels", "Graphite wheel covers.", words=WORDS)
    s.paint("wheels", "satin", colour=GRAPHITE)
