"""TSC_Bumblebee, take A, "True bee": the bee's own banding read along the car, nose to tail: black head (the nose),
a yellow collar at the front of the thorax (the nose root, over the front wheels), black thorax (the cockpit),
the abdomen's yellow at the car's fattest (the sidepods), black, and the white tail behind the deck's crease.
Every edge furred. Base finishes only (its visual language: ../TSC_Bumblebee/language.json)."""

from tool import shapes

Y, K, W, A = "#e8b61a", "#1a1612", "#f1ebdc", "#8a5a1c"  # bee yellow, velvet black, tail white, wing amber
LEGS = "#0d0b09"
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
           "over the cockpit, yellow over the sidepods, black over the deck, the white tail behind the deck's crease.",
           words=WORDS)
    s.paint("body", "suede", colour=K)
    s.paint("body", "suede", colour=Y, zone=fur(shapes.band(110, 150), 1), across=True)
    s.paint("body", "suede", colour=Y, zone=fur(shapes.band(-55, 20), 2), across=True)
    s.paint("body", "suede", colour=W, zone=fur(shapes.behind(-128), 3), across=True)
    legs(s)
