"""Bumblebee, the composition (set 1, the pick of A, "True bee"): the bee's own banding read along the car, nose to tail: black head (the nose),
a yellow collar at the front of the thorax (the nose root, over the front wheels), black thorax (the cockpit),
the abdomen's yellow at the car's fattest (the sidepods), and a yellow tail behind the deck's crease (the user's
change, 2026-10-09: 'Maybe yello').
Every edge furred. Then the surfaces: the fur's lay and its age, and the lights (its visual language: the car's language.json)."""

from dataclasses import replace

from tool import finishes, meshlines, noise, shapes

Y, K, A = "#e8b61a", "#1a1612", "#8a5a1c"  # bee yellow, velvet black, wing amber
LEGS = "#0d0b09"
HONEY = "#f7a81b"  # the lights: amber, the wings' colour lit
POLLEN = "#f2d27a"  # the dust
WORDS = "Bumblebee"


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
    s.glass(A, 0.8)


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
    s.step("The fur's lay", "The nap lies nose to tail: a grain along the car over the suede, in each band's "
           "own colour. A worker a few weeks into summer: the coat thick and even, pressed flatter to a soft "
           "velvet sheen where it brushes the flowers (the top's front, the flanks' widest point); no wear, "
           "no dirt.", words=WORDS)
    nap = replace(finishes.get("brushed wrap"), name="fur nap", roughness=1.0, metalness=0.0, varnish=0.0, colour=None)
    s.paint("body", finish=nap, colour=Y, zone=yellow, blend=0.45, across=True, direction="z")
    s.paint("body", finish=nap, colour=K, zone=~yellow, blend=0.45, across=True, direction="z")
    pressed = replace(finishes.get("suede"), name="pressed fur", roughness=0.7)
    flowers = shapes.radial((0, 72, 105), 45) | shapes.radial((86, 45, -30), 35) | shapes.radial((-86, 45, -30), 35)
    s.paint("body", finish=pressed, colour=Y, zone=flowers & yellow, blend=0.6, across=True)
    s.paint("body", finish=pressed, colour=K, zone=flowers & ~yellow, blend=0.6, across=True)
    s.dirt(0)
    s.step("The lights", "Every light warm: the game's lights on the legs in honey amber, the wings' colour lit, "
           "by day and at night; nothing on the fur shines.", words=WORDS, look="rear night")
    s.relight("inner", HONEY, keep_level=True)
    s.relight("speed numbers", HONEY)
    s.relight("rear lights", HONEY)
    s.relight("brake lights", HONEY)


def hairs(zone, seed):
    """A band's edge as hairs of many lengths: over the fur's teeth, finer hairs 4 mm wide reaching a centimetre
    and a half more or less, and clumps 5 cm across that reach 3 cm further or hang back; no two alike."""
    fine = shapes.noisy(fur(zone, seed), amount=(0.2, 0.2, 1.5), scale=(0.4, 0.4, 6.0), seed=seed + 10)
    return shapes.noisy(fine, amount=(0.0, 0.0, 3.0), scale=(5.0, 5.0, 30.0), seed=seed + 20)


def pollen(gather, seed, cell=0.25, grain=0.1, most=0.7):
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
    yellow = hairs(shapes.band(110, 150), 1) | hairs(shapes.band(-55, 20), 2) | hairs(shapes.behind(-128), 3)
    nap = replace(finishes.get("brushed wrap"), name="fur nap", roughness=1.0, metalness=0.0, varnish=0.0, colour=None)
    pressed = replace(finishes.get("suede"), name="pressed fur", roughness=0.7)
    flowers = shapes.radial((0, 72, 105), 45) | shapes.radial((86, 45, -30), 35) | shapes.radial((-86, 45, -30), 35)

    s.step("The hairs", "Each band's edge as hairs of many lengths: finer hairs over the fur's teeth, and clumps "
           "that reach further or hang back, so no two hairs are alike. The strip along each edge painted again, "
           "its fur, its nap and its pressed coat as before.", words=WORDS)
    strip = (shapes.band(103, 117) | shapes.band(143, 157) | shapes.band(-62, -48) | shapes.band(13, 27)
             | shapes.band(-135, -121))
    s.paint("body", "suede", colour=K, zone=strip & ~yellow, across=True)
    s.paint("body", "suede", colour=Y, zone=strip & yellow, across=True)
    s.paint("body", finish=nap, colour=Y, zone=strip & yellow, blend=0.45, across=True, direction="z")
    s.paint("body", finish=nap, colour=K, zone=strip & ~yellow, blend=0.45, across=True, direction="z")
    s.paint("body", finish=pressed, colour=Y, zone=flowers & strip & yellow, blend=0.6, across=True)
    s.paint("body", finish=pressed, colour=K, zone=flowers & strip & ~yellow, blend=0.6, across=True)

    s.step("The pollen", "A dust of pale grains, about 2 mm, no shine, where dust gathers: in the hollows the body "
           "makes (the inlets' throats and lips, under the body's edge along the lower flanks, the pocket between "
           "sidepod and rear wheel, the nose's underside, the tail's lower corners), at the foot of the groove "
           "round the cockpit and of the groove along each sidepod's top, thicker low down and thinning to nothing "
           "on the open skin; nowhere on the wings or the legs, and clear of the nose fin's plate.", words=WORDS)
    hollow = ~shapes.outside(0.6, soft=10)
    grooves = (meshlines.line("cockpit surround crease 1").band(2.5, soft=2.5)
               | meshlines.line("sidepod top crease 1").mirrored().band(3.0, soft=3.0))
    low = ~(~shapes.below(40, soft=50) * 0.6)  # 1 low down, 0.4 on top
    fin = shapes.box((-12, 55, 114), (12, 75, 147))  # the nose fin's plate and 3 cm round it
    gather = (hollow | grooves * 0.7) & low & ~fin
    s.paint("body", "chalk", colour=POLLEN, zone=pollen(gather, 4), across=True)
