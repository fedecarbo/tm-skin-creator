"""TSC_Trial1030, from take B "Coachwork": the whole car one midnight blue, the inner car too (satin), and the side
panels picked out by a gold coachline each, as a coachbuilder lines a panel: the rear flank (the haunch behind the
sidepod) and the side skirt (the sill), each traced closed round the face the eye sees, one line where they meet."""
from tool import course, marks, meshlines

WORDS = "Midnight blue, with a thin gold outline round the side panels and a few small gold stars on the nose."
BLUE = (15 / 255, 31 / 255, 77 / 255)
GOLD = (212 / 255, 165 / 255, 49 / 255)
NIGHT = (10 / 255, 13 / 255, 24 / 255)
LINE = 0.5  # cm, every coachline (the language's DNA)


def haunch():
    """The rear flank's coachline, the left side's: up its front curve behind the sidepod, back along the deck edge's
    rounded line, down the tail corner's front, forward over the rear wheel's opening and down its front edge, then
    forward along the sill's lower rounded edge to where it began."""
    top = meshlines.line("rear flank roll 2", tilt=47).between(-48, -121)
    front = meshlines.line("body shell edge 1").between(top.start, (84, 26, -23)).reversed()
    over_wheel = meshlines.line("rear flank crease 3").between(-95, -121).reversed()
    sill = meshlines.line("rear flank roll 1", tilt=128).between(-25, -90).reversed()
    close = meshlines.line("rear flank seam 1").between(sill.end, front.start)  # up the panel's own seam
    return front.then(top).then(over_wheel).then(sill).then(close)


def skirt():
    """The side skirt's coachline, the left side's: forward along its top creases (where the sill meets the sidepod
    and the body), across its front end at the front wheel, back along its outer edge; open at the back, where the
    rear flank's line is the one line both panels share."""
    top = (meshlines.line("side skirt crease 4").reversed()
           .then(meshlines.line("side skirt crease 7").between(72, 44).reversed())
           .then(meshlines.line("side skirt crease 5").reversed()))
    outer = meshlines.line("side skirt crease 2").between(149, 38).then(meshlines.line("side skirt roll 7"))
    return top.then(outer)


def design(s):
    s.clay()
    s.step("The lacquer", "The whole car one midnight blue: the body and wheel covers gloss, the inner car satin.",
           words=WORDS)
    s.paint("body", "PA-01", colour=BLUE)
    s.paint("wheel covers", "PA-01", colour=BLUE)
    s.paint("inner", "PA-03", colour=BLUE)
    s.step("The coachlines", "A thin gold line just inside the edge of each side panel, closed round the face the "
           "eye sees: the rear flank and the side skirt, each side, one line where the two meet.", words=WORDS)
    s.paint("body", "ME-07", colour=GOLD, zone=haunch().mirrored().band(LINE, side=-1))
    s.paint("body", "ME-07", colour=GOLD, zone=skirt().mirrored().band(LINE, side=1))
    s.step("The hardware", "The hardware under and between, satin night black: the cockpit's seat, belts, wheel and "
           "dashboard, the engine bay, the exhausts, the driveshafts, the brakes, the rear dampers, the speed display.",
           words=WORDS)
    s.paint(["seat", "seat belt", "belt buckle", "steering wheel", "steering column", "dashboard", "engine bay",
             "exhaust", "driveshaft", "brake caliper", "brake line", "rear damper", "digit display"],
            "PA-03", colour=NIGHT)
    s.step("The tyres", "Black rubber with plain sidewalls, Nadeo's own tread.", words=WORDS)
    s.paint("tyres", "RU-01")
    s.tyre_tread("TR-01")
    s.step("The lights", "The car's own lights in the body's midnight blue, low, so the gold stays the coachlines' "
           "and the stars': the speed numbers, the rear lights, the front brake lights, the wheel rings.",
           words=WORDS, look="rear night")
    s.relight("speed numbers", BLUE)
    s.relight("rear lights", BLUE)
    s.relight("brake lights", BLUE)
    s.relight("wheel ring", BLUE)
    s.step("Kept new", "Fresh lacquer, polished: it takes half the stock dust on dirt.", words=WORDS)
    s.dirt(0.5)
    s.step("The stars", "A few small gold stars on the nose, like the first ones out: four five-pointed stars, each "
           "its own size (3 to 5.5 cm), loosely set over the nose panel and the nose tip, none mirrored.", words=WORDS)
    star = marks.star(5, inner=0.45)
    s.mark("nose panel", "ME-07", star, size=5.5, at=(-5, None, 167), colour=GOLD, mirror=False)
    s.mark("nose panel", "ME-07", star, size=3.5, at=(6, None, 152), colour=GOLD, mirror=False)
    s.mark("nose tip", "ME-07", star, size=4.5, at=(8, None, 190), colour=GOLD, up=(0, 0, 1), mirror=False)
    s.mark("nose tip", "ME-07", star, size=3, at=(-9, None, 200), colour=GOLD, mirror=False)
