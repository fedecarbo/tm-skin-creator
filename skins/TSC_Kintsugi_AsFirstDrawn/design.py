"""TSC_Kintsugi: a car pieced together from the shards of different pots and mended with gold.

The body is gold all over; ten shards of glaze are laid on it and stop short of each other, so
the gold shows between them as the mended seams. Each break is a flat cut through the whole car
(as a pot breaks), a little wavy, so a seam runs on in line over every fold, panel and gap. This
take has the breaks where they were first drawn, before any was moved for the game's panels or the nose
fin's plate: a break runs down the bonnet's middle, over the plate (the bonnet's shard lies either side
of it), and the left deck break crosses the number panel, which the game letters.
"""

import numpy as np

from tool import shapes
from tool.noise import fbm, smoothstep

WORDS = "an agent's own concept"

INDIGO = "#101a4c"    # gosu blue, the main pot
WHITE = "#efece4"     # porcelain
CELADON = "#7ea18d"
STONEWARE = "#231f1d"  # the unglazed dark clay of the inner car
LAMP = "#ffb43c"      # the lights, a warm gold

# The breaks: a point on each (cm: x the car's left, y up, z forward) and the way it faces.
BREAKS = {
    "nose": ((0, 55, 160), (0.30, 0.30, 0.90)),
    "bonnet": ((0, 66, 85), (-0.42, 0.25, 0.87)),
    "bonnet middle": ((0, 66, 120), (0.993, 0.0, -0.116)),
    "across": ((-40, 70, -52), (-0.35, 0.20, 0.92)),   # the long one, from the right sidepod's back to the left one's top
    "middle": ((3, 70, 60), (0.97, 0.0, 0.24)),
    "left": ((45, 50, 35), (0.30, 0.35, 0.89)),
    "right": ((-45, 50, 5), (-0.25, 0.40, 0.88)),
    "tail": ((0, 64, -130), (0.25, 0.30, 0.93)),
    "deck left": ((28, 75, -90), (0.90, 0.10, 0.42)),
    "deck right": ((-45, 70, -90), (-0.93, 0.20, 0.30)),
}
# How the pot broke: (a break, what lies on the side it faces, what lies behind it); a name is a shard.
TREE = ("nose", "nose",
        ("bonnet", ("bonnet middle", "bonnet", "bonnet"),
         ("across",
          ("middle", ("left", "left flank", "left pod"), ("right", "right flank", "right pod")),
          ("tail", ("deck left", "rear left", ("deck right", "rear right", "deck")), "tail"))))
SHARDS = ("nose", "bonnet", "left flank", "left pod", "right flank", "right pod", "rear left", "rear right", "deck", "tail")
WANDER = 6.0   # cm: how far a break strays from flat, in waves about 45 cm long
SEAM = 2.6     # cm of gold between two shards, wider and narrower along its way

_kept = {}


def _broken(pos, nrm):
    """Each point's shard, and how far it is over the skin from the nearest break round that shard, less
    half the seam there. A break is a plane; the distance to it over the skin is the distance through the
    air divided by how steeply the skin crosses it, so a seam keeps its width on every face."""
    key = (len(pos), float(pos[0] @ pos[-1]), float(pos[len(pos) // 2].sum()))
    if key not in _kept:
        _kept.clear()
        p = pos.astype(np.float32)
        q = p + WANDER * (np.stack([fbm(p / 45.0, 3, seed) for seed in (11, 12, 13)], 1) - 0.5)
        shard = np.zeros(len(p), np.int8)
        far = np.full(len(p), 1e3, np.float32)

        def walk(node, idx):
            if isinstance(node, str):
                shard[idx] = SHARDS.index(node)
                return
            name, front, behind = node
            point, facing = BREAKS[name]
            m = np.asarray(facing, np.float32)
            m = m / np.linalg.norm(m)
            s = (q[idx] - np.asarray(point, np.float32)) @ m
            steep = np.sqrt(np.clip(1 - (nrm[idx] @ m) ** 2, 0.12, 1))
            far[idx] = np.minimum(far[idx], np.abs(s) / steep)
            walk(front, idx[s > 0])
            walk(behind, idx[s <= 0])

        walk(TREE, np.arange(len(p)))
        seam = SEAM * (0.45 + 1.1 * fbm(p / 22.0, 2, 5))
        _kept[key] = (shard, far - seam / 2)
    return _kept[key]


def shard(name):
    """A shard, up to half a seam short of each break round it."""
    k = SHARDS.index(name)

    def weight(pos, nrm):
        which, inside = _broken(pos, nrm)
        return (which == k) * smoothstep(-shapes.SOFT / 2, shapes.SOFT / 2, inside)
    return shapes.Zone(weight, label=f"shard({name!r})")


def _bands(distance, steep, every, wide):
    off = np.abs((distance + every / 2) % every - every / 2) / np.sqrt(np.clip(steep, 0.12, 1))
    return smoothstep(-shapes.SOFT / 2, shapes.SOFT / 2, wide / 2 - off)


def hoops(every=6.0, wide=2.0, at=0.0):
    """Bands round the car, one every `every` cm along it: a banded cup's."""
    return shapes.Zone(lambda p, n: _bands(p[:, 2] - at, 1 - n[:, 2] ** 2, every, wide), label=f"hoops({every:g}, {wide:g})")


def rings(centre, every=7.0, wide=2.4):
    """Rings round a point, as on a plate (ja-no-me), one every `every` cm out from it."""
    c = np.asarray(centre, np.float32)

    def weight(p, n):
        d = p - c
        r = np.linalg.norm(d, axis=1)
        out = np.einsum("ij,ij->i", n, d) / np.maximum(r, 1e-3)
        return _bands(r, 1 - out ** 2, every, wide)
    return shapes.Zone(weight, label=f"rings({every:g}, {wide:g})")


GLAZE = {"nose": WHITE, "bonnet": INDIGO, "left flank": CELADON, "left pod": INDIGO, "right flank": INDIGO,
         "right pod": WHITE, "rear left": WHITE, "rear right": INDIGO, "deck": INDIGO, "tail": CELADON}


def design(s):
    s.clay()

    s.step("The gold", "The whole body in gold: it shows wherever no shard lies, as the mended seams.", words=WORDS)
    s.paint("body", "gold")

    s.step("The shards", "Ten shards of glazed pots laid on the gold, a seam of it left between them: "
           "deep indigo, white porcelain and celadon.", words=WORDS)
    for name in SHARDS:
        s.paint("body", "wet look", colour=GLAZE[name], zone=shard(name))

    s.step("The painted shards", "Two of the white shards come from painted pots: indigo bands round the nose, "
           "rings on the right sidepod.", words=WORDS)
    s.paint("body", "wet look", colour=INDIGO, zone=shard("nose") & hoops(6.0, 2.0, at=1.0))
    s.paint("body", "wet look", colour=INDIGO, zone=shard("right pod") & rings((-66, 61, -32), 7.0, 2.4))

    s.step("The fasteners", "The body's own bolt heads in the mender's gold (they share one paint, so they are "
           "one colour on every shard); the mirrors' mounts in the inner car's stoneware.", words=WORDS)
    s.paint(["body shell|left", "body shell|right", "cockpit surround|left", "cockpit surround|right"], "gold")
    s.paint("mirror mount", "matte", colour=STONEWARE)

    s.step("The inner car", "Everything under the body in dark unglazed stoneware; the exhausts in gold.", words=WORDS)
    s.paint("inner", "matte", colour=STONEWARE)
    s.paint("exhaust", "gold")

    s.step("Wheels and tyres", "The wheel covers as four indigo plates with gold hubs, gold rims behind them, "
           "a thin gold line round each tyre.", words=WORDS)
    s.paint("wheel covers", "wet look", colour=INDIGO)
    s.paint("wheel cover hub", "gold")
    s.paint("rim", "gold")
    s.tyre_marks("TY-68")

    s.step("Lights and glass", "Every light a warm gold; the glass a smoky amber.", words=WORDS, look="rear night")
    s.relight("speed numbers", LAMP)
    s.relight("brake lights", LAMP)
    s.relight("rear lights", LAMP)
    s.relight("wheel ring", LAMP, keep_level=True)
    s.glass("#4a3518", 0.5)
