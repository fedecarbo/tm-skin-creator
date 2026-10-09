"""TSC_Bumblebee, take C, "Chevron": the bands swept into the car's own V. The body's long crease ahead of the
cockpit runs as a V, from the top's middle back to each shoulder; each band's edge follows that V across the top
and then drops straight down the flank where the V reaches the shoulder. Black nose ahead of the V, a deep yellow
V behind it, black, the white tail behind the deck's crease. Every edge furred. Base finishes only (its visual
language: ../TSC_Bumblebee/language.json)."""

import math

from tool import shapes

Y, K, W, A = "#e8b61a", "#1a1612", "#f1ebdc", "#8a5a1c"  # bee yellow, velvet black, tail white, wing amber
LEGS = "#0d0b09"
WORDS = "Bumblebee"
SWEEP = (36.0, 87.0)  # the crease's V: 36 cm out for 87 cm back, from (0, 70, 92) to (36, 71, 5)
SHOULDER = 36.0  # where the V meets the shoulder and the edge drops down the flank


def behind_v(z0):
    """Everything behind a V whose point is at z0 on the car's middle, swept like the body's crease; past the
    shoulders the edge runs straight down the flank at the V's depth there."""
    dx, dz = SWEEP
    n = math.hypot(dx, dz)
    left = shapes.plane((0, 0, z0), (-dz / n, 0, -dx / n))  # behind the V's left arm (x > 0)
    right = shapes.plane((0, 0, z0), (dz / n, 0, -dx / n))  # behind its right arm (x < 0)
    middle = shapes.box((-SHOULDER, -999, -999), (SHOULDER, 999, 999))
    flanks = ~middle & shapes.behind(z0 - SHOULDER * dz / dx)
    return (middle & left & right) | flanks


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
    s.step("The bands", "Bands of fur swept into the body's own V: a black nose ahead of the crease's V, yellow in a "
           "deep V behind it, black behind that, the white tail behind the deck's crease.", words=WORDS)
    s.paint("body", "suede", colour=K)
    s.paint("body", "suede", colour=Y, zone=fur(behind_v(92) & ~behind_v(22), 1), across=True)
    s.paint("body", "suede", colour=W, zone=fur(shapes.behind(-128), 3), across=True)
    legs(s)
