"""The tool's self-test: does this code still paint every skin exactly as an earlier commit did, and which flaws does
its judge name on a car where they were planted?

    python -m tool.selftest --against <ref>             the representative set (SET), old and new
    python -m tool.selftest --against <ref> SelfTest_Tour   only the skins named
    python -m tool.selftest --against <ref> --all       every design, and the self-test's own cars
    python -m tool.selftest --against <ref> --snap      the viewer's sheets of SNAP too, pixel for pixel
    python -m tool.selftest --against <ref> --at <ref2> <ref2>'s code instead of the working tree's
    python -m tool.selftest                             this code alone: paint, encode, time
    python -m tool.selftest --profile [<skin> ...]      where one paint's time and memory go (the tour if none named)

Run it before and after any change to the tool. It first checks that every command, file and name
the instructions give still exists (tool/instructions.py, the working tree's), and its tripwires (`tripwires`): code
nothing uses (vulture: a name in tool/ that no code calls, the tool's, the designs' or the self-test's cars'; UNSEEN
are the names the standard library or a decorator calls), and the tool past its size (BUDGET: lines a commit may not
grow past without raising it here and saying why; when they shrink by more than SLACK, the budget comes down with
them). Each skin is painted
in a fresh process, from the code in the working tree and from <ref>'s code, extracted by
`git archive` into the work folder (never the repo: the PC's is in OneDrive). Per texture it compares
the painted floats, the uint8 image the viewer and install take, and the whole DDS file the game
reads; per skin, the notes and the paint's own findings (in any order), the palette, the steps and the parts left in clay. A difference is shown texel by texel, by painting
that skin again on both sides.

The self-test's own cars, painted only here and never shown in the Lab: the tour makes every paint call the user's car
doesn't, once. The planted-flaw pair lays graphics of every kind on the car's hardest spots (tape along a crisp edge and
across a seam where the map is cut, strips along a rolled edge, across where the model's short lines meet and on a
crisp line, ticks towards an opening, a band to the tail, a fill to the model's lines, discs, a ring, pictures across a
rolled edge and on a panel, words on a side, over a fold and along a curve): SelfTest_Clean as the tool lays them,
SelfTest_Flawed with the kinds of flaw the user has pointed out planted on its left side (PLANTED: what, where and how
big). Both are judged (tool/judge.py), the findings compared as the notes are; then it says which planted flaws the
judge names, and what it names on the clean car and besides on the flawed one: for a change to a check, before and
after.

The self-test's cars are compared only with commits whose paint box has every call they make. A commit's results
are kept in the work folder (selftest/<commit>/), so each side is paid for once per computer: a
minute or two a skin. The working tree's are painted afresh
every run. Both sides share the work folder's caches, so a change to what a cache
holds must change the cache's name or version, or the old side reads the new cache and agrees.

--profile paints each skin once in a fresh process under cProfile: the time to paint and to encode, the functions
that take it, the most memory the paint held and how often it waited for the disk (page-ins: swapping). The whole
profile is kept in the work folder (selftest/profile/<name>.prof).
"""

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile

from tool import instructions, paths, progress

# Together they use every part of the paint box: the user's car (peel, relief, emboss, glows, relit
# lights, a library finish, the canvas by hand) and TOUR, a test car of the self-test's own that
# makes every other call once; and the planted-flaw pair, CLEAN and FLAWED.
TOUR, CLEAN, FLAWED = "SelfTest_Tour", "SelfTest_Clean", "SelfTest_Flawed"
OWN = (TOUR, CLEAN, FLAWED)
SET = ("TSC_CMYK_EndsInK", *OWN)
SNAP = ("TSC_CMYK_EndsInK",)
HOME = paths.WORK / "selftest"
OLD = 946684800  # 2000-01-01: the old code's files predate every cache, so none rebuilds for them
# The tripwires. Names the standard library calls or reads, which no code of ours does (tool/server.py's handler and
# server, a C function's types for ctypes); tool/looks.py's @look registers each look by its name.
UNSEEN = ("do_*", "log_request", "allow_reuse_address", "directory", "restype", "argtypes")
# The tool's lines (tool/*.py, the viewer's own viewer/*.js): a commit may not grow them past this without raising it
# here and saying why in its message; when they shrink by more than SLACK, the budget comes down with them.
BUDGET = {"tool/*.py": 19350, "viewer/*.js": 4720}
SLACK = 100

# The tour: clay, steps, a fade, zones by facing and height, a noise pattern, a blend round a point, a torn edge, wear,
# the flanks, the car map's open air and length, a drawn line, grass, a blob, a decal, a scatter, a print,
# lettering, marks laid on a panel and across them, a band kept off a part painted by name, the
# model's lines (a band beside one, ticks along a rounded edge's, tape beside a picked line panel by
# panel, a panel's trim, dashes panel by panel but one), stripes, checks, courses (dashes along the inlet's lower rim, a
# panel edge's strip, a drawn line's placard), a camo pattern, fabric, glows, a relit light, glass, dirt, a wheel ring, tyre
# markings and a tread. Its pictures are drawn here, so it needs no stored art.
TOUR_CODE = r'''
def tour(s):
    from pathlib import Path
    from PIL import Image, ImageDraw
    from tool import course, marks, meshlines, shapes, textures
    pic = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(pic)
    d.ellipse((16, 16, 240, 240), fill=(250, 200, 30, 255), outline=(20, 20, 20, 255), width=14)
    d.polygon([(128, 50), (200, 200), (56, 200)], fill=(200, 30, 60, 255))
    tile = Path(out).with_suffix(".tile.png")
    t = Image.new("RGB", (256, 256), (30, 110, 160))
    ImageDraw.Draw(t).ellipse((64, 64, 192, 192), fill=(240, 240, 230))
    t.save(tile)
    s.clay()
    s.step("Base", "A base, a fade, a split by facing and height, a stripe, splashes and wear.")
    s.paint("body", "gloss red")
    under = s.keep()
    s.paint("body", "candy teal", zone=shapes.fade("z", 120, -150, curve=0.8))
    s.paint("body", "matte black", zone=shapes.facing("up", 0.4, soft=0.006) & shapes.above(30))
    s.paint("body", "splatter", palette=["keep", "hot pink", "lemon"], scale=9, zone=shapes.along(0.6, 0.8))
    s.paint("nose fin", "satin", colour="#e02020", zone=shapes.stripe(4))
    s.paint("body", "satin", colour="#f4f2ec", blend=0.6, zone=shapes.radial((0, 84, -60), 40))
    s.paint("body", "matte black", zone=shapes.noisy(shapes.band(150, 165), amount=3, seed=2))
    s.wear(under, fade=0.3, chips=0.08, scrapes=0.05, clearcoat=0.2)
    s.step("The map", "The flanks on the outer body, a line through points, grass and a blob.")
    s.paint("body", "satin", colour="#f4f2ec", zone=shapes.sides(0.5) & shapes.outside(0.4) & shapes.along(0.2, 0.4))
    s.paint("body", "satin", colour="#9fc3e6", zone=shapes.polyline([[(86.0, 41.6, -6.1), (86.9, 42.0, -20.0), (86.8, 42.0, -35.0)]], 1.2))
    s.paint("body", "satin", colour="#2e7d32", zone=shapes.grass(base=6, height=(18, 30), every=3.0, seed=7))
    s.paint("body", "gloss", colour="#111111", zone=shapes.blob((30, 0, 60), 9, seed=1))
    s.step("Pictures", "A decal, a scatter, a print, lettering and marks.")
    s.decal(pic, "bonnet", width=30)
    s.scatter(pic, "engine cover", size=6, seed=3)
    textures.add_file("selftest tile", tile, 20, about="the self-test's tile")
    s.paint("rear flank", "selftest tile")
    s.text("TOUR 7", "left side", colour="black", font="russo", height=10, outline="white")
    s.paint("body", "gloss", colour="#111111", zone=shapes.band(-70, -66))
    spot = s.mark("sidepod top", "gloss", marks.star(5), size=14, colour="#f4f2ec")
    s.mark("sidepod top", "gloss", marks.disc(), size=0.3 * spot.size, colour="#111111")
    s.mark("rear quarter panel", "satin", marks.box(0.5, corner=0.1), size=40, at=(30, None, -60), colour="#e0a82e", turn=20)
    s.mark("body", "satin", marks.ring(0.7), size=22, at=(0, None, 150), colour="#e8601c", across=True)
    s.step("The model's lines", "A band beside the body's bottom edge, stripes, checks, and markings along the car's lines.")
    bottom = meshlines.line((60, 16.5, -60), kind="opening").between((74.1, 17.9, -25.0), (41.8, 15.2, -97.2))
    s.paint("rear flank", "satin", colour="#1f8f3a", zone=bottom.offset(14).mirrored().inked_edge(shapes.below(26)))
    s.paint("tail panel", "satin", colour="#f4f2ec", zone=shapes.stripes(3, across=(0.75, 0, 1), edge=-132))
    s.paint("sidepod top", "satin", colour="#111111", zone=shapes.checks(6, across=("z", "x")))
    sill = meshlines.line((74, 26, 7), kind="opening").between((83.6, 26.0, -24.8), (50.9, 25.9, 39.8))  # the inlet's lower rim
    s.paint("body", "satin", colour="#111111", zone=sill.mirrored().dashes(5, gap=3, width=1))
    s.paint("rear quarter panel", "satin", colour="#e0a82e", zone=course.edge("rear quarter panel", side="left").mirrored().strip(0.8))
    s.paint("body", "satin", colour="#d0208e", zone=meshlines.line((65, 59, -85), kind="rounded").ticks(every=12, length=3, width=0.6, side=1))
    nose = meshlines.picked([(25.5, 46.7, 142.3), (35.0, 53.4, 81.3), (36.4, 52.8, 67.5)]).offset(2.5)
    s.paint("body", "satin", colour="#e0a82e", zone=course.Courses([nose], "the nose").panels(6).mirrored().blocks(5, 2.5))
    low = meshlines.line((60, 16.5, -60), kind="opening").between((80, 22, 5), (45, 17, -105))
    s.paint("body", "satin", colour="#e0a82e", zone=course.Courses([low], "the lower edge").panels(3).without("rear flank")
            .mirrored().dashes(3, gap=2, width=0.6))
    s.paint("body", "satin", colour="#f4f2ec", zone=meshlines.panel((25, 80, 11), both=True, border=1.5))
    drawn = course.stroke([(42.8, 64.0, -128.1), (50.0, 63.6, -100.0), (58.6, 63.0, -78.6), (76.4, 60.8, -50.0)])
    s.paint("body", "satin", colour="#111111", zone=drawn.strip(0.6))
    s.placard("ALONG", "body", at=drawn.between(-110, -90), height=2.6, colour="#111111", mirror=False)
    s.step("Details", "The inner car, glass, dirt, glows, a light and the tyres.")
    s.paint("inner", "camo matte", palette=["charcoal", "slate", "light grey", "jet black"], scale=26)
    s.paint("seat", "cloth", colour="charcoal")
    s.glow("rear strake", "ice blue")
    s.relight("wheel ring", "#e0a82e", keep_level=True)
    s.glass("plum", 0.5)
    s.dirt(1.3)
    s.paint("sidewall", "satin", colour="#e0a82e", zone=shapes.wheel_ring(31.8, 32.6))
    s.tyre_marks("TY-26", colour="#e0a82e")
    s.tyre_tread("TR-04")
'''
# The planted-flaw pair: graphics of every kind on the car's hardest spots, the same on both cars, laid as the tool
# lays them; on the flawed car, PLANTED's flaws on the left side. Its pictures are drawn here.
PAIR_CODE = r'''
def pair(s, flawed):
    import numpy as np
    from PIL import Image, ImageDraw
    from tool import course, marks, meshlines, shapes
    BASE, INK, GOLD, RED = "#d9d6cf", "#141414", "#e0a82e", "#c8102e"
    FLIP = np.array([-1.0, 1.0, 1.0])

    def planted(clean, left):
        # the right side as laid; on the flawed car, the left as planted
        return (clean & shapes.right()) | (left & shapes.left()) if flawed else clean

    def beside(c, cm):
        # c moved cm to its left across the surface (an array: at each of its points)
        L = np.cross(c.nrm, c.tan)
        L /= np.linalg.norm(L, axis=1, keepdims=True)
        return course.points(c.pts + np.broadcast_to(np.asarray(cm, np.float64), (len(c.pts),))[:, None] * L)

    def on(p):
        return tuple(meshlines._closest(np.asarray(p, np.float64))[1])

    def nearest(c, p):
        return tuple(c.pts[np.argmin(np.linalg.norm(c.pts - np.asarray(p, np.float64), axis=1))])

    def mirror(at):
        return tuple(None if v is None else f * v for v, f in zip(at, FLIP))

    def both(call, at, left=None, **kw):
        # a mark, words or a picture on each side; on the flawed car, the left one with `left` planted
        if not flawed:
            return call(at=at, **kw)
        call(at=mirror(at), mirror=False, **kw)
        return call(**{"at": at, "mirror": False, **kw, **(left or {})})

    def picture(px):
        pic = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        d = ImageDraw.Draw(pic)
        d.rectangle((8, 8, 248, 248), fill=(20, 20, 20, 255))
        d.ellipse((48, 48, 208, 208), fill=(224, 168, 46, 255))
        d.polygon([(128, 70), (186, 180), (70, 180)], fill=(200, 16, 46, 255))
        return pic if px == 256 else pic.resize((px, px), Image.LANCZOS)

    s.clay()
    s.step("Base", "The body in one pale colour.")
    s.paint("body", "satin", colour=BASE)

    s.step("Lines", "Tape along the skirt's crisp edge and along the body's lower edge across a seam; strips along a "
           "rolled edge, across where the model's lines meet and on a crisp line; a strip at an even gap beside a panel "
           "line.")
    skirt = meshlines.line((39, 19, 70)).between(140, 25)
    tape = skirt.mirrored().band(3, side="seen")
    hop = skirt.between(95, 101).band(3, side=-tape.side)
    s.paint("body", "satin", colour=INK, zone=planted(
        tape, (tape & ~shapes.band(59.25, 60.75) & ~shapes.band(95, 101)) | hop))
    low = meshlines.line((60, 16.5, -60), kind="opening").between((80, 22, 5), (45, 17, -105))
    tape = low.mirrored().band(3, side="seen")
    s.paint("body", "satin", colour=INK, zone=planted(tape, tape & ~shapes.band(-24.25, -25.75)))
    shoulder = meshlines.line((64, 61, -84), kind="rounded")
    front = shoulder.between(-52, -84)
    wob = front.between(-60, -76)
    s.paint("body", "satin", colour=RED, zone=planted(
        front.mirrored().strip(0.8),
        (front.strip(0.8) & ~shapes.band(-60, -76)) | beside(wob, 0.3 * np.sin(8 * np.pi * wob.s / wob.length)).strip(0.8)))
    rim = meshlines.line((14, 41, 204), kind="rounded")
    half = rim.between((0, 40, 210), rim.end)
    nose = meshlines.line((32, 55, 95), kind="rounded").between(143.8, 100)
    s.paint("body", "satin", colour=INK, zone=planted(half.then(nose).mirrored().strip(0.8),
                                                      half.then(beside(nose, 0.6)).strip(0.8)))
    side = meshlines.line((0, 70, 92)).between((36, 71, 8), (35, 74, -36))
    kink = side.between(-5, -25)
    tent = 1.2 * (1 - np.abs(kink.s - kink.length / 2) / (kink.length / 2))
    s.paint("body", "satin", colour=INK, zone=planted(
        side.mirrored().strip(0.6), (side.strip(0.6) & ~shapes.band(-5, -25)) | beside(kink, tent).strip(0.6)))
    sill = meshlines.line((74, 26, 21)).between(10, -22)
    closes = np.interp(sill.s, [0, 0.3 * sill.length, sill.length], [-2.0, -2.0, -0.3])
    s.paint("body", "satin", colour=GOLD,
            zone=planted(beside(sill, -2.0).mirrored().strip(0.6), beside(sill, closes).strip(0.6)))

    cock = meshlines.line((0, 70, 92)).between((30, 76, 33), (33, 72, 15))  # the opening 6 to 12 cm to its left
    s.paint("body", "satin", colour=INK, zone=planted(cock.mirrored().ticks(every=6, length=4, width=0.6, side=1),
                                                      cock.ticks(every=6, length=12, width=0.6, side=1)))

    s.step("Fills", "A band along the side to the tail, the tail corner's panel filled to its lines, stripes on the "
           "bonnet.")
    s.paint("body", "satin", colour=INK,
            zone=shapes.sides(0.5) & shapes.outside(0.4) & shapes.above(40) & shapes.below(44) & shapes.behind(-45))
    cover = shapes.behind(-144) & shapes.above(38) & shapes.below(46)  # the band's last 4 cm painted over, wider
    if flawed:  # on the left by the base colour: short; on the right by the same ink, which goes on to the eye
        s.paint("body", "satin", colour=BASE, zone=cover & shapes.left())
        s.paint("body", "satin", colour=INK, zone=cover & shapes.right())
    else:
        s.paint("body", "satin", colour=INK, zone=cover)
    corner = meshlines.panel((44, 64, -138), both=True)
    sliver = meshlines.panel((44, 64, -138), border=1.0) & shapes.sphere(on((45, 63.3, -128)), 7.5)
    short = shapes.Zone(lambda p, n: np.clip(corner(p, n) - sliver(p, n), 0, 1))  # 1 cm short of its line, no hairline
    short.lines = corner.lines  # a fill to the panel's lines, as the tool lays one, that falls short
    s.paint("body", "satin", colour=RED, zone=planted(corner, short))
    s.paint("body", "satin", colour=RED, zone=planted(shapes.stripe(3, at=13) | shapes.stripe(3, at=-13),
                                                      shapes.stripe(3, at=13, soft=2.5)) & shapes.band(98, 114) & shapes.above(60))

    s.step("Marks", "Discs on panels and beside a strip; pictures across a rolled edge and on the deck; words on a "
           "side, on the front flank and along a curve.")
    s.mark("sidepod top", "satin", marks.disc(), size=10, at=(76, None, -22), colour=RED)
    for where, at, size in (("rear quarter panel", (33, None, -64), 8), ("sidepod top", (70, None, -40), 8)):
        s.mark(where, "satin", marks.disc(), size=size, colour=RED, **(dict(at=mirror(at), mirror=False) if flawed else dict(at=at)))
    i = int(np.argmin(np.abs(front.pts[:, 2] + 80)))
    out = np.cross(front.nrm[i], front.tan[i])
    out /= np.linalg.norm(out)
    clear, touch = on(front.pts[i] - 6.0 * out), on(front.pts[i] - 1.0 * out)
    s.paint("body", "satin", colour=GOLD, zone=planted(shapes.sphere(clear, 2.5) | shapes.sphere(np.asarray(clear) * FLIP, 2.5),
                                                       shapes.sphere(touch, 2.5)))
    if flawed:  # off its panel: cut by the panel's edge, onto the next piece, on the lettered panel
        rq = nearest(course.edge("rear quarter panel", side="left", near=(41, 72, -64)), (41, 72, -64))
        s.paint("rear quarter panel|left", "satin", colour=RED, zone=shapes.sphere(rq, 4))
        pod = nearest(course.edge("sidepod top", side="left", near=(70, 61, -50)), (70, 61, -50))
        s.paint("body", "satin", colour=RED, zone=shapes.sphere(pod, 4))
        s.paint("body", "satin", colour=RED, zone=shapes.sphere(on((13.4, 81.7, -70)), 2.5))
    pic = picture(256)
    i = int(np.argmin(np.abs(shoulder.pts[:, 2] + 95)))
    roll, facing = on(shoulder.pts[i]), tuple(shoulder.nrm[i])
    both(lambda **k: s.decal(pic, "rear flank", width=14, across=True, **k), roll,
         left=dict(zone=shapes.facing(facing, 0.94, soft=0.01)))
    both(lambda image=pic, **k: s.decal(image, "engine cover", width=8, **k), (32, None, -105), left=dict(image=picture(16)))
    both(lambda **k: s.text("SIDE", "rear flank", colour=INK, height=5, **k), (67, 50, -75), left=dict(up=(0, -1, 0)))
    both(lambda height=5, **k: s.text("FLANK", "body shell", colour=INK, height=height, **k), on((37, 58, 68)),
         left=dict(across=True, height=8))
    s.placard("ALONG", "body shell", colour=INK, height=2.6, at=meshlines.line((40, 58, 38), kind="rounded").between(20, -40))
    s.mark("body", "satin", marks.ring(0.6), size=10, at=on((20, 66, 120)), colour=INK, across=True,
           **(dict(within=~shapes.sphere(on((25, 65, 120)), 0.5)) if flawed else {}))  # a notch bitten out of its left
'''
# The flaws planted on FLAWED's left side, each of the kinds the user has pointed out (judge.KINDS): where along the
# car it is (z, cm), and what and how big. A finding names the nearest one of its kind on its side, within NEAR cm.
PLANTED = (
    ("gap", (59, 61), "a 1.5 cm gap in the tape along the skirt's crisp edge"),
    ("line", (95, 101), "the skirt's tape on the edge's other face for 6 cm"),
    ("gap", (-24, -26), "a 1.5 cm break in the lower edge's tape at the seam where the side skirt meets the rear flank "
                        "and the map is cut"),
    ("line", (-60, -76), "the strip along the rear flank's rolled shoulder wobbling 0.3 cm either way every 4 cm"),
    ("line", (142, 146), "a 0.6 cm step in the nose's strip where the nose's rounded edge meets the body shell's"),
    ("line", (-5, -25), "a kink in the strip on the cockpit's crisp line: out 1.2 cm and back over 20 cm, bent 13 "
                       "degrees at its point"),
    ("sits", (2, -22), "the gold strip's gap to the sill's panel line closing from 2 cm to 0.3"),
    ("short", (-144, -148), "the band along the side stopping 4 cm short of the tail, painted over"),
    ("short", (-122, -132), "the tail corner's fill stopping 1 cm short of its top edge for 15 cm"),
    ("edge", (98, 114), "the bonnet's stripe feathered over 2.5 cm"),
    ("cut", (-60, -68), "a disc 8 cm wide cut by the rear quarter panel's edge"),
    ("spill", (-45, -54), "a disc 8 cm wide over the sidepod top's back edge, onto the body shell"),
    ("clear", (-67, -73), "a disc 5 cm wide on the number panel"),
    ("over", (-77, -83), "a disc 5 cm wide over the rear flank's strip"),
    ("cut", (-88, -102), "the picture across the rear flank's rolled shoulder cut where the surface turns 20 degrees from "
                         "its middle"),
    ("edge", (-101, -109), "the picture on the deck 16 pixels across its 8 cm"),
    ("upside down", (-70, -84), "SIDE hanging upside down on the rear flank"),
    ("fold", (49, 87), "FLANK laid over the front flank's turn, 42 degrees under it"),
    ("cut", (33, 15), "ticks 12 cm long from the cockpit's groove towards its opening, cut by the edge where the body ends"),
    ("cut", (115, 125), "a notch a centimetre wide bitten out of the ring on the bonnet, where the skin is bare"),
)
NEAR = 5.0  # cm along the car: a finding this near a planted flaw names it
# A kept result of the self-test's own car is the car's as it was then: its file is named by the car's code.
KEYS = {TOUR: hashlib.sha256(TOUR_CODE.encode()).hexdigest()[:10],
        CLEAN: hashlib.sha256(PAIR_CODE.encode()).hexdigest()[:10], FLAWED: hashlib.sha256(PAIR_CODE.encode()).hexdigest()[:10]}

# What runs in each fresh process, from the code tree it's started in. Only calls both sides have.
PRELUDE = r'''
import hashlib, json, re, sys, time
import numpy as np
from tool import dds, paintbox, skin
''' + TOUR_CODE + PAIR_CODE + r'''

def paint_car(name):
    if name not in ("SelfTest_Tour", "SelfTest_Clean", "SelfTest_Flawed"):
        return skin.paint(name)
    s = paintbox.Skin(name)
    if name == "SelfTest_Tour":
        tour(s)
    else:
        s.measure = True
        pair(s, name == "SelfTest_Flawed")
    s.end_steps()
    return s


def checked(s):
    # what the judge names on the planted-flaw pair; None on any other car
    if s.name not in ("SelfTest_Clean", "SelfTest_Flawed"):
        return None
    from tool import judge
    return [{"kind": f["kind"], "check": f["check"], "side": f["side"], "text": f["text"], "level": f["level"],
             "z": None if f["z"] is None else [round(float(v), 1) for v in f["z"]]}
            for f in judge.run(s)["findings"]]


def encoded(s, keep=False):
    # each texture as the game gets it: hashes of its floats, of the uint8 image the viewer and install take and of
    # its DDS file; with keep, the uint8 images and the DDS files themselves
    sha = lambda b: hashlib.sha256(b).hexdigest()[:20]
    textures, arrays = {}, {}
    for tex, (arr, fourcc, opts) in sorted(s.textures().items()):
        arr = np.asarray(arr)
        u8 = np.clip(np.rint(arr * 255), 0, 255).astype(np.uint8)   # as save_painted rounds
        img = u8.astype(np.float32) / 255                            # as build_zip reads it back
        blob = dds.encode(dds.build_mips(img[..., None] if img.ndim == 2 else img, **opts), fourcc)
        textures[tex] = {"shape": list(arr.shape), "dtype": str(arr.dtype), "fourcc": fourcc,
                         "float": sha(np.ascontiguousarray(arr).tobytes()), "u8": sha(u8.tobytes()), "dds": sha(blob)}
        if keep:
            arrays[tex] = u8
            arrays[tex + ".dds"] = np.frombuffer(blob, np.uint8)
    return textures, arrays
'''
CHILD = PRELUDE + r'''
name, out = sys.argv[1], sys.argv[2]
dump = sys.argv[3] if len(sys.argv) > 3 else None
t0 = time.time()
with skin.paint_slot():
    t = time.time()
    s = paint_car(name)
    painted = time.time() - t
    t = time.time()
    found = checked(s)
    looked = time.time() - t
t = time.time()
textures, arrays = encoded(s, keep=bool(dump))
if dump:
    np.savez(dump, **arrays)
record = {"palette": s.palette, "icon": s.icon_colours,
          "steps": [{"name": st["name"], "paints": st.get("paints", [])} for st in s.steps],
          "clay": s.clay_left}
notes = [re.sub(r"\(\d+ s\)", "(… s)", n) for n in s.notes]  # how long a step took isn't the paint
notes += [f["text"] for f in getattr(s, "findings", ())]  # what the paint itself knows is wrong
notes += [f"{f['kind']}: {f['text']}" for f in found or ()]  # and what the judge names on the planted-flaw pair
sha = lambda b: hashlib.sha256(b).hexdigest()[:20]
json.dump({"textures": textures, "record": sha(json.dumps(record, sort_keys=True, default=str).encode()),
           "notes": notes, "found": found,
           "seconds": {"paint": round(painted, 1), "checks": round(looked, 1), "encode": round(time.time() - t, 1),
                       "total": round(time.time() - t0, 1)}}, open(out, "w"), indent=1)
'''
# One paint profiled, in a fresh process of the working tree's: where its time goes, and its memory.
PROFILE = PRELUDE + r'''
import cProfile, os, pstats


def memory():
    # the most memory this process has held (bytes), and how often it waited for the disk (None on Windows, which
    # counts every fault)
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("faults", wintypes.DWORD), ("peak", ctypes.c_size_t)] + [
                (f"n{k}", ctypes.c_size_t) for k in range(7)]
        k32 = ctypes.WinDLL("kernel32")
        k32.GetCurrentProcess.restype = wintypes.HANDLE
        k32.K32GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        c = Counters()
        c.cb = ctypes.sizeof(c)
        if not k32.K32GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(c), c.cb):
            raise ctypes.WinError()
        return c.peak, None
    import resource
    r = resource.getrusage(resource.RUSAGE_SELF)
    return r.ru_maxrss * (1 if sys.platform == "darwin" else 1024), r.ru_majflt


name, out = sys.argv[1], sys.argv[2]
waits = memory()[1]
p = cProfile.Profile()
with skin.paint_slot():
    t = time.time()
    p.enable()
    s = paint_car(name)
    p.disable()
    painted = time.time() - t
    t = time.time()
    p.enable()
    encoded(s)
    p.disable()
    coded = time.time() - t
peak, after = memory()
p.dump_stats(out)
rows = [(f"{os.path.basename(f)}:{fn}" if f != "~" else fn, tt, ct, f.replace(os.sep, "/"))
        for (f, _, fn), (_, _, tt, ct, _) in pstats.Stats(p).stats.items()]
own = sorted(rows, key=lambda r: -r[1])[:15]
tool = sorted((r for r in rows if "/tool/" in r[3]), key=lambda r: -r[2])[:15]
json.dump({"paint": round(painted, 1), "encode": round(coded, 1), "peak": peak,
           "waits": None if after is None else after - waits,
           "own": [(n, round(tt, 1)) for n, tt, ct, f in own], "tool": [(n, round(ct, 1)) for n, tt, ct, f in tool]},
          open(out + ".json", "w"), indent=1)
'''

SNAP_CHILD = r'''
import sys
from pathlib import Path
from tool import snap, view
name, folder = sys.argv[1], Path(sys.argv[2])
view.prepare(name)
for kind, shots, size, query in (("views", snap.SHOTS, (960, 720), ""), ("cams", snap.CAMS, (1280, 720), "lens=game")):
    snap.snap(name, out=folder / f"{name}_{kind}.png", size=size, shots=shots, prepare=False, query=query)
'''


def git(*args):
    return subprocess.run(["git", "-C", str(paths.REPO), *args], capture_output=True, check=True).stdout


def tree(ref):
    """<ref>'s code, extracted once into the work folder: (commit, folder)."""
    commit = git("rev-parse", "--verify", f"{ref}^{{commit}}").decode().strip()
    folder = HOME / commit[:12] / "tree"
    if not (folder / "tool").exists():
        print(f"extracting {ref} ({commit[:12]})...", flush=True)
        progress.stage("Getting the old code")
        tmp = folder.with_name("tree.tmp")
        shutil.rmtree(tmp, ignore_errors=True)
        blob = git("archive", commit, "--", "tool", "car", "viewer", "skins",
                   ":(exclude)skins/*/versions", ":(exclude)skins/*/sets")
        with tarfile.open(fileobj=io.BytesIO(blob)) as t:
            t.extractall(tmp, filter="data")
        for p in tmp.rglob("*"):
            os.utime(p, (OLD, OLD))
        tmp.rename(folder)
    return commit, folder


def child(script, cwd, log, *args):
    """Runs a script in a fresh process with `tool` imported from cwd, its output into log. None
    when it worked, else {"error": its last line}."""
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["PYTHONHASHSEED"] = "0"
    with open(log, "w") as f:
        r = subprocess.run([sys.executable, "-B", "-c", script, *args], cwd=cwd, env=env,
                           stdout=f, stderr=subprocess.STDOUT)
    if r.returncode:
        tail = log.read_text(errors="replace").strip().splitlines()[-1:] or ["(no output)"]
        return {"error": tail[0]}
    return None


def paint(name, cwd, folder, keep):
    """One skin's results from the code at cwd, from folder if kept there already."""
    out = folder / (f"{name}-{KEYS[name]}.json" if name in OWN else f"{name}.json")
    if keep and out.exists():
        return json.loads(out.read_text())
    folder.mkdir(parents=True, exist_ok=True)
    failed = child(CHILD, cwd, out.with_suffix(".log"), name, str(out))
    if failed:
        out.unlink(missing_ok=True)
        return failed
    return json.loads(out.read_text())


def same(a, b):
    """How two results of one skin differ: (the textures that differ, other differences in words)."""
    if "error" in a or "error" in b:
        return [], [] if a.get("error") == b.get("error") else [f"error: {a.get('error')} / {b.get('error')}"]
    textures = [f"{t}: only one side has it" for t in sorted(set(a["textures"]) ^ set(b["textures"]))]
    for t in sorted(set(a["textures"]) & set(b["textures"])):
        x, y = a["textures"][t], b["textures"][t]
        bad = [k for k in ("shape", "dtype", "fourcc", "float", "u8", "dds") if x[k] != y[k]]
        if bad:
            textures.append(f"{t}: {', '.join(bad)} differ")
    other = []
    if sorted(a["notes"]) != sorted(b["notes"]):
        gone = [f"- {n}" for n in a["notes"] if n not in b["notes"]]
        new = [f"+ {n}" for n in b["notes"] if n not in a["notes"]]
        other.append("notes differ:\n      " + "\n      ".join(gone + new))
    if a["record"] != b["record"]:
        other.append("the record differs (palette, steps, clay)")
    return textures, other


def detail(name, old_cwd, new_cwd):
    """Paints the skin again on both sides and says how far each texture is from the other."""
    import numpy as np
    tmp = HOME / "detail"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    for side, cwd in (("old", old_cwd), ("new", new_cwd)):
        failed = child(CHILD, cwd, tmp / f"{side}.log", name, str(tmp / f"{side}.json"), str(tmp / f"{side}.npz"))
        if failed:
            print(f"    {side}: {failed['error']}")
            return
    a, b = np.load(tmp / "old.npz"), np.load(tmp / "new.npz")
    for t in sorted(set(a.files) & set(b.files)):
        x, y = a[t], b[t]
        if x.shape != y.shape:
            print(f"    {t}: {x.shape} / {y.shape}")
        elif not np.array_equal(x, y):
            d = np.abs(x.astype(np.int16) - y.astype(np.int16))
            what = "bytes" if t.endswith(".dds") else "values"
            print(f"    {t}: {int((d > 0).sum())} {what} differ, by up to {int(d.max())}")
    shutil.rmtree(tmp, ignore_errors=True)


def snapshots(names, old_cwd, new_cwd, commit):
    """The viewer's sheets (views, close looks, the game's cameras) from both sides' viewer code,
    over the same skin data, compared pixel for pixel."""
    from PIL import Image, ImageChops
    ok = True
    for name in names:
        folders = {"old": HOME / commit[:12] / "snap", "new": HOME / "live" / "snap"}
        for side, cwd in (("old", old_cwd), ("new", new_cwd)):
            folders[side].mkdir(parents=True, exist_ok=True)
            failed = child(SNAP_CHILD, cwd, folders[side] / f"{name}.log", name, str(folders[side]))
            if failed:
                print(f"  {name} ({side}): {failed['error']}")
                ok = False
        for kind in ("views", "close", "cams"):
            a, b = (folders[s] / f"{name}_{kind}.png" for s in ("old", "new"))
            if not (a.exists() and b.exists()):
                continue
            ia, ib = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
            if ia.size != ib.size:  # a difference compares only the part the two share
                print(f"  {name} {kind}: the sizes differ, {ia.width}x{ia.height} / {ib.width}x{ib.height}")
                ok = False
                continue
            box = ImageChops.difference(ia, ib).getbbox()
            print(f"  {name} {kind}: {'identical' if box is None else f'differs within {box}'}")
            ok &= box is None
    return ok


def tripwires():
    """What the tripwires catch, a line each: code nothing uses, and code past its budget; then the line counts."""
    import vulture
    v = vulture.Vulture(ignore_names=list(UNSEEN), ignore_decorators=["@look"])
    v.scavenge([paths.REPO / "tool", *sorted(paths.SKINS.glob("*/design.py"))])
    cars = CHILD + PROFILE
    v.scan(cars, filename="cars")
    caught = []
    for item in v.get_unused_code(min_confidence=60):
        if item.filename.is_absolute():
            where = f"{item.filename.relative_to(paths.REPO).as_posix()}:{item.first_lineno}"
        else:
            where = f"tool/selftest.py, the cars' code, at {cars.splitlines()[item.first_lineno - 1].strip()!r}"
        caught.append(f"{where}: {item.message}: delete it, or use it")
    counts = []
    for pattern, budget in BUDGET.items():
        n = sum(len(f.read_text(encoding="utf-8").splitlines()) for f in paths.REPO.glob(pattern))
        counts.append(f"{pattern} {n} lines of {budget}")
        if n > budget:
            caught.append(f"{pattern}: {n} lines, {n - budget} past its budget: make room, or raise BUDGET and say why "
                          "in the commit")
        elif n < budget - SLACK:
            caught.append(f"{pattern}: {n} lines, {budget - n} under its budget: lower BUDGET to {n}")
    return caught, counts


def _same(f, g):
    """Two findings of one kind in one place (their ends within a cm), one side's and both sides' alike."""
    if f["kind"] != g["kind"] or (f["side"] and g["side"] and f["side"] != g["side"]):
        return False
    if f["z"] is None or g["z"] is None:
        return f["z"] == g["z"]
    return all(abs(x - y) <= 1.0 for x, y in zip(sorted(f["z"]), sorted(g["z"])))


def _gap(f, flaw):
    """How far along the car a finding is from a planted flaw (cm), None when it can't name it: another kind or side, or
    further than NEAR."""
    kind, where, _ = flaw
    if f["kind"] != kind or f["side"] not in (None, "left"):
        return None
    if f["z"] is None:
        return NEAR
    (a0, a1), (b0, b1) = sorted(f["z"]), sorted(where)
    gap = max(b0 - a1, a0 - b1, 0.0)
    return gap if gap <= NEAR else None


def score(clean, flawed):
    """What the checks name on the planted-flaw pair: (how many of PLANTED, the lines to print). A finding the clean
    car has too doesn't name a planted flaw."""
    named, rest = {}, []
    for f in flawed:
        if any(_same(f, g) for g in clean):
            continue
        near = [(gap, k) for k, flaw in enumerate(PLANTED) if (gap := _gap(f, flaw)) is not None]
        if near:
            named.setdefault(min(near)[1], set()).add(f"{f['check']}, {f['level']}" if f.get("level") else f["check"])
        else:
            rest.append(f)
    lines = [f"  {'named ' if k in named else 'missed'} {kind:<11} z {where[0]:+g} to {where[1]:+g}: {what}"
             + (f" ({', '.join(sorted(named[k]))})" if k in named else "") for k, (kind, where, what) in enumerate(PLANTED)]
    kinds = lambda fs: ", ".join(f"{k} {sum(f['kind'] == k for f in fs)}" for k in sorted({f["kind"] for f in fs}))
    lines.append(f"  on {CLEAN}, where nothing was planted: {len(clean)}" + (f" ({kinds(clean)})" if clean else ""))
    lines.append(f"  on {FLAWED}, besides: {len(rest)}" + (f" ({kinds(rest)})" if rest else ""))
    return len(named), lines


def _swap():
    """The swap in use on the Mac (sysctl), in words; None elsewhere."""
    if sys.platform != "darwin":
        return None
    out = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True, text=True).stdout
    used = re.search(r"used = ([\d.]+)M", out)
    return f"{float(used.group(1)) / 1024:.1f} GB" if used else None


def profile(names):
    """One paint of each skin profiled: where its time goes, the most memory it held, how often it waited for the disk."""
    folder = HOME / "profile"
    folder.mkdir(parents=True, exist_ok=True)
    for name in names:
        out = folder / f"{name}.prof"
        before = _swap()
        failed = child(PROFILE, paths.REPO, out.with_suffix(".log"), name, str(out))
        if failed:
            print(f"{name}: FAILED {failed['error']}")
            continue
        r = json.loads(out.with_suffix(".prof.json").read_text())
        waits = "" if r["waits"] is None else f", waited for the disk {r['waits']} times"
        print(f"{name}: painted in {r['paint']:.0f} s, encoded in {r['encode']:.0f} s, profiled (slower than a plain paint); "
              f"held at most {r['peak'] / 2 ** 30:.1f} GB{waits}" + (f"; swap {before} before, {_swap()} after" if before else ""))
        print("  the most time spent in:")
        print("\n".join(f"    {s:>6.1f} s  {n}" for n, s in r["own"]))
        print("  the tool's functions, with all they call:")
        print("\n".join(f"    {s:>6.1f} s  {n}" for n, s in r["tool"]))
        print(f"  the whole profile: {out}")


def designs():
    return sorted(p.parent.name for p in paths.SKINS.glob("*/design.py"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("skins", nargs="*", help="the skins to test (the representative set if none)")
    ap.add_argument("--against", metavar="REF", help="the commit to compare with")
    ap.add_argument("--at", metavar="REF", help="test this commit's code instead of the working tree's")
    ap.add_argument("--all", action="store_true", help="every design")
    ap.add_argument("--snap", action="store_true", help="the viewer's sheets too, pixel for pixel")
    ap.add_argument("--profile", action="store_true", help="where one paint's time and memory go (the tour if none named)")
    args = ap.parse_args()
    if args.profile:
        with progress.job("Profiling a paint", done="Profiled"):
            return profile(args.skins or [TOUR])
    names = args.skins or (designs() + list(OWN) if args.all else list(SET))
    with progress.job("Checking the tool", done="Every car painted exactly as before" if args.against else "Painted and timed"):
        run(args, names)


def run(args, names):
    differing = []
    if not args.at:
        counts, missing = instructions.check()
        print(instructions.line(counts, missing), flush=True)
        if missing:
            differing.append("instructions")
        caught, counts = tripwires()
        print("tripwires: " + ("nothing unused; " if not caught else "") + "; ".join(counts), flush=True)
        print("\n".join(f"  {c}" for c in caught))
        if caught:
            differing.append("tripwires")
    old_cwd = commit = None
    if args.against:
        commit, old_cwd = tree(args.against)
    new_cwd, live, fresh = paths.REPO, HOME / "live", True
    if args.at:
        at, new_cwd = tree(args.at)
        live, fresh = HOME / at[:12], False
    print(f"{len(names)} skins" + (f" at {args.at}" if args.at else "")
          + (f", against {args.against} ({commit[:12]})" if commit else ""), flush=True)
    progress.stage("Cars checked", total=len(names))
    results = {}
    for name in names:
        progress.detail(f"{progress.title_of(name)}: painted with the new code")
        new = paint(name, new_cwd, live, keep=not fresh)
        if "error" in new:
            print(f"{name:<40} new: FAILED {new['error']}", flush=True)
            differing.append(name)
            progress.tick()
            continue
        results[name] = {"new": new}
        line = f"{name:<40} paint {new['seconds']['paint']:>5.1f} s  encode {new['seconds']['encode']:>5.1f} s"
        if commit:
            if not (old_cwd / "skins" / name / "design.py").exists() and name not in OWN:
                print(f"{line}  (new since {args.against})", flush=True)
                progress.tick()
                continue
            progress.detail(f"{progress.title_of(name)}: painted with the old code")
            old = paint(name, old_cwd, HOME / commit[:12], keep=True)
            if name in OWN and "error" in old:  # the car makes a call that commit's paint box doesn't have
                print(f"{line}  (not at {args.against}: {old['error']})", flush=True)
                progress.tick()
                continue
            results[name]["old"] = old
            textures, other = same(old, new)
            if "seconds" in old:
                line += f"   was {old['seconds']['paint']:>5.1f} s / {old['seconds']['encode']:>5.1f} s"
            print(f"{line}  {'DIFFERENT' if textures or other else 'identical'}", flush=True)
            for d in textures + other:
                print(f"    {d}")
            if textures or other:
                differing.append(name)
            if textures:
                progress.detail(f"{progress.title_of(name)}: finding the differences")
                detail(name, old_cwd, new_cwd)
        else:
            print(line, flush=True)
        progress.tick()
    if CLEAN in results and FLAWED in results:
        caught, lines = score(results[CLEAN]["new"]["found"], results[FLAWED]["new"]["found"])
        was = [results[n].get("old", {}).get("found") for n in (CLEAN, FLAWED)]
        was = f" (at {args.against}: {score(*was)[0]})" if None not in was else ""
        print(f"\nThe checks name {caught} of the {len(PLANTED)} flaws planted on {FLAWED}{was}:")
        print("\n".join(lines), flush=True)
    if args.snap and commit:
        print("snapshots:", flush=True)
        progress.stage("Comparing the pictures")
        if not snapshots(SNAP, old_cwd, new_cwd, commit):
            differing.append("snapshots")
    if commit:
        print("\nall identical" if not differing else f"\ndifferent: {', '.join(differing)}")
    if differing:
        progress.result(f"Different: {', '.join(progress.title_of(n) for n in differing)}", failed=True)
    sys.exit(1 if differing else 0)


if __name__ == "__main__":
    main()
