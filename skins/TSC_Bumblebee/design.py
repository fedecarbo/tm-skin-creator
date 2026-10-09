"""Bumblebee, the composition (set 1, the pick of A, "True bee"): the bee's own banding read along the car, nose to tail: black head (the nose),
a yellow collar at the front of the thorax (the nose root, over the front wheels), black thorax (the cockpit),
the abdomen's yellow at the car's fattest (the sidepods), and a yellow tail behind the deck's crease (the user's
change, 2026-10-09: 'Maybe yello').
Every edge furred. Then the surfaces: the fur's lay and its age, and the lights (its visual language: the car's language.json)."""

from dataclasses import replace

from tool import finishes, shapes

Y, K, A = "#e8b61a", "#1a1612", "#8a5a1c"  # bee yellow, velvet black, wing amber
LEGS = "#0d0b09"
HONEY = "#f7a81b"  # the lights: amber, the wings' colour lit
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
