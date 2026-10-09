"""Bumblebee, the composition (set 1, the pick of A, "True bee"): the bee's own banding read along the car, nose to tail: black head (the nose),
a yellow collar at the front of the thorax (the nose root, over the front wheels), black thorax (the cockpit),
the abdomen's yellow at the car's fattest (the sidepods), and a yellow tail behind the deck's crease (the user's
change, 2026-10-09: 'Maybe yello').
Every edge furred. Then the surfaces: the fur's lay and its age, and the lights (its visual language: the car's language.json)."""

from dataclasses import replace

import numpy as np

from tool import finishes, meshlines, noise, shapes

Y, K, A = "#e8b61a", "#1a1612", "#8a5a1c"  # bee yellow, velvet black, wing amber
LEGS = "#0d0b09"
HONEY = "#f7a81b"  # the lights: amber, the wings' colour lit
POLLEN = "#f5dc96"  # the dust: a chalkier, paler grain than the yellow, so it shows on both colours
LIT, PRESSED = "#352a1e", "#3f3326"  # the black fur's hairs where the light catches them, and where the coat is pressed flat
GLASS = "#d8922c"  # the wings: the amber the glass is tinted with (what lies behind it darkens it)
WORDS = "Bumblebee"
HAIR = 0.24  # cm: a hair's width


def fur(zone, seed):
    """A band's edge as fur: hairs about 2 cm long lying along the car, a new one every 1.5 cm or so."""
    return shapes.noisy(zone, amount=(0.3, 0.3, 2.0), scale=(1.5, 1.5, 25.0), seed=seed)


def legs(s):
    """The bee's hard parts, the same in every take: the legs and eyes (the inner car and the wheels) in glossy
    black chitin, the feet in rubber, the wings (the glass) smoky amber."""
    s.step("The legs and wings", "The inner car and the wheels in hard glossy black; the tyres matte black rubber; "
           "the glass tinted smoky amber.", words=WORDS)
    s.paint("inner", "gloss plastic", colour=LEGS)
    s.paint("wheels", "gloss plastic", colour=LEGS)
    s.paint("tyres", "rubber")
    s.glass(GLASS, 1.0)


def design(s):
    s.clay()
    s.step("The bands", "Six bands of fur along the car: black nose, a yellow collar behind the nose, black "
           "over the cockpit, yellow over the sidepods, black over the deck, a yellow tail behind the deck's crease.",
           words=WORDS)
    s.paint("body", "suede", colour=K)
    s.paint("body", "suede", colour=Y, zone=fur(shapes.band(110, 150), 1), across=True)
    s.paint("body", "suede", colour=Y, zone=fur(shapes.band(-55, 20), 2), across=True)
    s.paint("body", "suede", colour=Y, zone=fur(shapes.behind(-128), 3), across=True)
    legs(s)
    surfaces(s)
    details(s)


def surfaces(s):
    """The surfaces pass: the fur's lay and its age, and the lights (its visual language: surfaces, ageing)."""
    yellow = fur(shapes.band(110, 150), 1) | fur(shapes.band(-55, 20), 2) | fur(shapes.behind(-128), 3)
    s.step("The fur's lay", "The nap lies nose to tail: on the yellow a grain along the car over the suede; on "
           "the black its lit hairs, thin streaks of a lighter brown-black. A worker a few weeks into summer: "
           "the coat thick and even, pressed flatter to a soft velvet sheen where it brushes the flowers (the "
           "top's front, the flanks' widest point); no wear, no dirt.", words=WORDS)
    nap = replace(finishes.get("brushed wrap"), name="fur nap", roughness=1.0, metalness=0.0, varnish=0.0, colour=None)
    s.paint("body", finish=nap, colour=Y, zone=yellow, blend=0.45, across=True, direction="z")
    pressed = replace(finishes.get("suede"), name="pressed fur", roughness=0.7)
    flowers = shapes.radial((0, 72, 105), 45) | shapes.radial((86, 45, -30), 35) | shapes.radial((-86, 45, -30), 35)
    s.paint("body", finish=pressed, colour=Y, zone=flowers & yellow, blend=0.6, across=True)
    s.paint("body", finish=pressed, colour=K, zone=flowers & ~yellow, blend=0.6, across=True)
    velvet(s, ~yellow, flowers)
    s.dirt(0)
    s.step("The lights", "Every light warm: the game's lights on the legs in honey amber, the wings' colour lit, "
           "by day and at night; nothing on the fur shines.", words=WORDS, look="rear night")
    s.relight("inner", HONEY, keep_level=True)
    s.relight("speed numbers", HONEY)
    s.relight("rear lights", HONEY)
    s.relight("brake lights", HONEY)


def _lanes(p, seed, sparse=0.0):
    """Each hair's reach along the car, by lane (a hair-wide column lying along the car): most 0.4 to 1.8 cm, one in
    ten to 3, tapering to half at the lane's sides so the tip is rounded; the sign says into which colour. With
    `sparse`, that share of lanes reaches 1 to 2 cm further still: the stray single hairs."""
    lanes = np.array([1 / HAIR, 1 / HAIR, 0], np.float32)
    q = p * lanes
    u = noise.cell_id(q, seed)  # which hair
    centre = 1 - 0.5 * np.clip(noise.worley(q, seed) / 0.6, 0, 1) ** 2  # 1 at the lane's middle, 0.5 at its sides
    way = np.where((u * 137.3) % 1.0 < 0.5, -1.0, 1.0)
    reach = 0.4 + 1.4 * ((u * 61.7) % 1.0) + np.where(u > 0.9, (u - 0.9) * 8.0, 0.0)
    if sparse:
        reach = reach + np.where(u > 1 - sparse, 0.8 + 1.2 * ((u * 91.1) % 1.0), 0.0)
    return way * reach * centre


def hairs(zone, seed, sparse=0.0):
    """A band's edge as a fringe of hairs lying along the car: in each hair-wide lane the edge moves along the car
    its own way (`_lanes`), each tip rounded; the lanes clump a little under a slow wander, so the fringe has no
    even pitch. sparse: the same fringe with that share of its hairs reaching further, the stray single hairs."""
    def shifted(p, n):
        q = p.copy()
        q[:, 2] += _lanes(p, seed + 30, sparse)
        return zone(q, n)
    fringe = shapes.Zone(shifted, label=f"hairs({zone!r})")
    return shapes.noisy(fringe, amount=(0.3, 0.3, 1.0), scale=(2.5, 2.5, 30.0), seed=seed)


def streaks(seed, width=0.18, length=8.0):
    """The nap's lit hairs: thin streaks along the car, about a fifth of the coat, no two alike."""
    cell = np.array([width, width, length], np.float32)
    return shapes.Zone(lambda p, n: noise.smoothstep(0.56, 0.66, noise.fbm(p / cell, 2, seed)), label="the nap's streaks")


def velvet(s, zone, flowers, seed=5):
    """The black fur's nap: its lit hairs as streaks of a lighter brown-black, a touch less matte than the coat,
    and lighter again where the coat is pressed."""
    nap = replace(finishes.get("matte"), name="velvet nap", roughness=0.85)
    pressed = replace(finishes.get("matte"), name="pressed velvet", roughness=0.7)
    lit = streaks(seed) & zone
    s.paint("body", finish=nap, colour=LIT, zone=lit & ~flowers, blend=0.5, across=True)
    s.paint("body", finish=pressed, colour=PRESSED, zone=lit & flowers, blend=0.5, across=True)


def pollen(gather, seed, cell=0.25, grain=0.1, most=0.45):
    """A dust of pollen: grains about 2 mm across (a disc round one random point in each `cell` cm cube, where the
    surface cuts it), as many as `gather` asks for (its weight, up to `most` of the cells), none where it is 0."""
    def f(p, n):
        q = p / cell
        disc = noise.smoothstep(grain + 0.03, grain - 0.03, noise.worley(q, seed) * cell)
        return disc * (noise.cell_id(q, seed + 1) < most * gather(p, n))
    return shapes.Zone(f, label=f"pollen in {gather!r}")


def details(s):
    """The details pass (its visual language: the DNA, the three sizes, the fullness). Large: nothing beyond the
    bands, four bands and nothing else drawn. Medium: the pollen in the hollows; the nap stays along the car over
    every bend (the car's rolls run along it, as a bee's hairs lie along its body; the faces square to the car,
    the nose's front and the tail's, are too small and the nap too faint for a turn to read). Small: the bands'
    edges as hairs of many lengths."""
    fringes = lambda sparse=0.0: (hairs(shapes.band(110, 150, soft=0.4), 1, sparse)
                                  | hairs(shapes.band(-55, 20, soft=0.4), 2, sparse)
                                  | hairs(shapes.behind(-128, soft=0.4), 3, sparse))
    yellow, stray = fringes(), fringes(0.06)
    nap = replace(finishes.get("brushed wrap"), name="fur nap", roughness=1.0, metalness=0.0, varnish=0.0, colour=None)
    pressed = replace(finishes.get("suede"), name="pressed fur", roughness=0.7)
    flowers = shapes.radial((0, 72, 105), 45) | shapes.radial((86, 45, -30), 35) | shapes.radial((-86, 45, -30), 35)

    s.step("The hairs", "Each band's edge as a fringe of hairs lying along the car: hairs of many lengths, most a "
           "centimetre or two into the next colour, their tips rounded, clumped a little, and here and there a "
           "single hair reaching further, thin enough to show the other colour through it. The strip along each "
           "edge painted again, its fur, its nap and its pressed coat.", words=WORDS)
    strip = (shapes.band(103, 117) | shapes.band(143, 157) | shapes.band(-62, -48) | shapes.band(13, 27)
             | shapes.band(-135, -121))
    s.paint("body", "suede", colour=K, zone=strip & ~yellow, across=True)
    s.paint("body", "suede", colour=Y, zone=strip & yellow, across=True)
    s.paint("body", finish=nap, colour=Y, zone=strip & yellow, blend=0.45, across=True, direction="z")
    s.paint("body", finish=pressed, colour=Y, zone=flowers & strip & yellow, blend=0.6, across=True)
    s.paint("body", finish=pressed, colour=K, zone=flowers & strip & ~yellow, blend=0.6, across=True)
    velvet(s, strip & ~yellow, flowers)
    s.paint("body", "suede", colour=Y, zone=strip & stray & ~yellow, blend=0.55, across=True)
    s.paint("body", "suede", colour=K, zone=strip & yellow & ~stray, blend=0.55, across=True)

    s.step("The pollen", "A dust of pale grains, about 2 mm, no shine, lying as dust does: thickest deep in the "
           "hollows the body makes (the inlets' throats, the pocket between sidepod and rear wheel, the nose's "
           "underside, the front wing's root), thinning over a long fade to a sparse scatter on the lower flanks "
           "and to nothing on the open skin, pooled at a few places along the groove round the cockpit and the "
           "groove along each sidepod's top, uneven everywhere, thicker low down; on yellow and black alike; "
           "nowhere on the wings or the legs, and clear of the nose fin's plate.", words=WORDS)
    deep = ~shapes.outside(0.3, soft=12)  # the real hollows, fading out over 12 cm
    haze = ~shapes.outside(0.7, soft=36)  # the thin dust round them, fading out over 36 cm
    pools = shapes.Zone(lambda p, n: noise.smoothstep(0.54, 0.64, noise.fbm(p / 8.0, 3, 6)), label="pools")
    grooves = (meshlines.line("cockpit surround crease 1").band(2.5, soft=2.5)
               | meshlines.line("sidepod top crease 1").mirrored().band(3.0, soft=3.0)) & pools
    mottle = shapes.Zone(lambda p, n: 0.35 + 0.65 * noise.smoothstep(0.35, 0.65, noise.fbm(p / 5.0, 2, 7)), label="mottle")
    low = ~(~shapes.below(40, soft=50) * 0.6)  # 1 low down, 0.4 on top
    fin = shapes.box((-12, 55, 114), (12, 75, 147))  # the nose fin's plate and 3 cm round it
    gather = (deep | haze * 0.3 | grooves * 0.8) & low & ~fin & mottle
    s.paint("body", "chalk", colour=POLLEN, zone=pollen(gather, 4), across=True)
