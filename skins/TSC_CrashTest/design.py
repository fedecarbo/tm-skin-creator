"""TSC_CrashTest: the car as the crash test dummy behind the wheel (the moodboard's B, 2026-10-07)."""

import math

from tool import marks, meshlines, shapes
from tool.shapes import WHEEL_Y, WHEEL_Z

SKIN = "#e3a21a"   # the dummy's warm yellow
BLACK = "#0a0a0c"


def quarters():
    """Two opposite quarters round each wheel's axle, above in front and below behind: the target
    a crash test camera tracks the wheel by."""
    zone = None
    for zc, end in ((WHEEL_Z[0], shapes.front_of(30)), (WHEEL_Z[1], shapes.behind(30))):
        above = shapes.plane((0, WHEEL_Y, zc), (0, 1, 0))
        ahead = shapes.plane((0, WHEEL_Y, zc), (0, 0, 1))
        q = ((above & ahead) | (~above & ~ahead)) & end
        zone = q if zone is None else zone | q
    return zone


def quartered():
    """Two opposite quarters of a disc, the rest of the target being the disc under them."""
    arc = lambda a0: [(0.5 * math.cos(a0 + k * math.pi / 32), 0.5 * math.sin(a0 + k * math.pi / 32)) for k in range(17)]
    return marks.polygon([(0, 0), *arc(0), (0, 0), *arc(math.pi)], "target")


def ruler(course, side):
    """Ticks every 3 cm, 2 long, and every 15, 4 long, to one side of a course (whose length makes them fall together)."""
    return course.ticks(3, 2, width=0.5, side=side) | course.ticks(15, 4, width=0.6, side=side)


def target(s, panel, at, size):
    """A crash test target: a black disc, two yellow quarters on it inside a black ring."""
    spot = s.mark(panel, "matte", marks.disc(), size=size, at=at, colour=BLACK)
    s.mark(panel, "soft-touch", quartered(), size=0.84 * spot.size, at=spot.centre, colour=SKIN)
    return spot


def design(s):
    s.clay()

    s.step("The dummy's skin", "The whole body in the dummy's warm yellow, soft to the touch.",
           words="i have an idea like one of those crash test cars")
    s.paint("body", "soft-touch", colour=SKIN)

    s.step("Black underneath, steel at the hinges", "The inner car matte black; the suspension arms, "
           "the car's joints, in brushed steel.", words="black targets on the head and joints, steel at the hinges")
    s.paint("inner", "matte", colour=BLACK)
    s.paint(["front suspension", "rear suspension"], "brushed steel")

    s.step("The wheels' targets", "Each wheel cover a quartered target, black and yellow, in a black ring.",
           words="black targets on the head and joints")
    s.paint("wheel covers", "soft-touch", colour=SKIN)
    s.paint("wheel covers", "matte", colour=BLACK, zone=quarters())
    s.paint(["wheel cover ring", "wheel cover hub"], "matte", colour=BLACK)
    s.paint(["rim", "hub"], "matte", colour=BLACK)

    s.step("The side targets", "A quartered target on each sidepod's flank, where a test car carries "
           "its door targets.", words="black targets on the head and joints")
    target(s, "sidepod top", (87, 42, -24), 20)

    s.step("The overhead targets", "A pair of smaller targets on the top, either side of the middle, on the nose "
           "ahead of the cockpit and on the tail: what a test's overhead camera tracks.",
           words="more refinements to the car, more focused on details")
    target(s, "body shell", (10, None, 102), 12)
    target(s, "tail panel", (13, None, -147), 14)

    s.step("The steel joint", "The car's own round fuel cap on the deck in brushed steel, as the dummy's joints are.",
           words="steel at the hinges")
    s.paint("fuel cap", "brushed steel")

    s.step("The measuring strips", "A black and yellow block scale beside each sidepod's top edge, 1.5 cm clear "
           "of it, from where the edge runs straight back to where it turns; a ruler along each sill, under the side "
           "target, every 3 cm and longer every 15, hanging from the model's line onto the strip below it.",
           words="Add them, we are testing that isnt it?")
    edge = meshlines.line((56, 63, -20))  # where the body ends round the sidepod's top: a line the eye follows
    rail = edge.between((54.9, 61.4, 6.9), (55.9, 62.8, -39.0)).offset(4).mirrored()
    s.paint("body", "matte", colour=BLACK, zone=rail.blocks(5, 2.5))
    sill = meshlines.line((74, 26, 21)).mirrored()  # 87.8 cm: the ticks every 3 and every 15 fall together
    s.paint("body", "matte", colour=BLACK, zone=ruler(sill, side=-1))

    s.step("More measuring strips", "A block scale along each rear flank, 1.5 cm clear of the line along its top, from "
           "the sidepod's back corner towards the tail; a ruler across the back of the deck, hanging forward from its "
           "line; a ruler round the nose tip's panel line, inside it, as a test car's bumper scale.",
           words="a test would be to add more block tape and measure table around the car")
    flank = meshlines.line((58, 63, -81))  # the rear flank's top, from the tail's corner to the sidepod's back
    s.paint("body", "matte", colour=BLACK,
            zone=flank.between(flank.at(s=8), flank.at(s=82)).offset(4).mirrored().blocks(5, 2.5))
    deck = meshlines.line((0, 66, -133))  # across the back of the deck; 82.5 cm, and the nose's 91.8: ticks together
    s.paint("body", "matte", colour=BLACK, zone=ruler(deck.between(deck.at(s=2), deck.at(s=84.5)), side=-1))
    nose = meshlines.line((0, 49, 187))  # round the nose tip, from z 150 (clear of the nose fin's plate) on each side
    s.paint("body", "matte", colour=BLACK, zone=ruler(nose.between(nose.at(s=7.7), nose.at(s=99.5)), side=1))

    s.step("The nose's tape", "A block scale along each side of the nose, beside the model's line along its roll, from "
           "abreast the cockpit's front (z 95) to behind the nose tip (z 143), where the user drew it.",
           words="Add tape here")
    roll = meshlines.line((27.2, 54.2, 120), kind="rounded")  # 49 cm; 4 cm beside it is within a cm of their stroke
    s.paint("body", "matte", colour=BLACK, zone=roll.offset(4).mirrored().blocks(5, 2.5))

    s.step("The lights", "The car's own lights in the dummy's yellow: the wheel rings, the speed numbers, "
           "the rear and brake lights.", look="rear night")
    s.relight("wheel ring", SKIN, keep_level=True)
    for light in ("speed numbers", "rear lights", "brake lights"):
        s.relight(light, SKIN)
