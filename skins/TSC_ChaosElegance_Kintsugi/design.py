"""Chaos and elegance, concept A (2026-09-26): kintsugi. The car as porcelain that shattered and
was mended with gold: gloss white, a few long cracks running across the whole car, and fine
hairlines branching off them where it took the hits. The inner car black with gold, the wheel
covers porcelain on gold rims. The chaos is the break; the elegance is the repair."""
import numpy as np

from tool import noise, shapes

WORDS = "I want chaos and elegance"
PORCELAIN = "#f1eee8"
GOLD = "ME-07"  # the Lab's gold
WARM = "#ffcf6b"  # gold, as light
INK = "#141416"


def cracks(scale, width, seed, warp=0.4, patchy=None):
    """A crack network: the borders of 3D cells about `scale` cm across, bent by noise so they
    wander, `width` cm wide on average (thicker and thinner along each crack). patchy: (size cm,
    share) keeps them only in patches covering about that share of the car."""
    def dist(p, n):
        bend = np.stack([noise.fbm(p / (scale * 0.8) + o, 3, seed + k) - 0.5 for k, o in enumerate((0.0, 31.7, 73.1))], 1)
        f1, f2 = noise.worley(p / scale + warp * 2 * bend, seed, second=True)
        gap = (f2 - f1) * scale / 2  # about the distance to the cells' border, in cm
        w = width * (0.35 + 1.3 * noise.fbm(p / 20, 2, seed + 9))
        d = w / 2 - gap
        if patchy:
            size, share = patchy
            d = np.where(noise.fbm(p / size, 3, seed + 21) > 1 - share, d, -1.0)
        return d
    return shapes.field(dist, soft=0.12)


def inner_car(s, dark=INK):
    """The inner car dark, as TSC_Stealth_CMYK's base without its body paint: carbon arms, satin
    uprights and dampers, brushed titanium exhaust, a black leather seat."""
    s.paint("inner", "satin", colour=dark)
    s.paint(["lower wishbone", "upper wishbone", "pushrod", "tie rod", "rear arm", "sidepod strut"], "carbon")
    s.paint(["damper", "rear damper", "upright", "hub bracket", "driveshaft", "upright cover", "hub", "brake light", "sidepod frame"],
            "satin", colour="#1e1f22")
    s.paint("exhaust", "brushed titanium")
    s.paint(["seat", "steering wheel"], "black leather")
    s.paint("dashboard", "matte", colour="#1a1b1d")


def design(s):
    s.clay()
    s.step("Porcelain", "The body in gloss porcelain white, deep and wet-looking.", words=WORDS)
    s.paint("body", "wet look", colour=PORCELAIN)

    s.step("Mended with gold", "A few long cracks run across the whole car, with fine hairlines branching off "
           "where it took the hits, all filled with polished gold.", words=WORDS)
    s.paint("body", GOLD, zone=cracks(55, 0.9, seed=3))
    s.paint("body", GOLD, zone=cracks(16, 0.35, seed=5, patchy=(70, 0.35)))

    s.step("Inner car", "Black inside, the grilles, calipers and belts in gold, a quilted black seat.", words=WORDS)
    inner_car(s)
    s.paint(["sidepod grille", "side vent", "brake caliper", "seat belt", "belt buckle", "front wing endplate"], GOLD)
    s.paint("sidepod grille plate", "satin", colour=INK)
    s.paint(["mirror", "mirror arm"], "wet look", colour=PORCELAIN)
    s.relief("seat", "quilted", depth=0.5, scale=7, replace=True)

    s.step("Wheels", "Porcelain covers on gold rims, a thin gold line round each tyre.", words=WORDS)
    s.paint("wheel covers", "wet look", colour=PORCELAIN)
    s.paint("rim", GOLD)
    s.no_glow("wheel ring")
    s.paint("wheel ring", "satin", colour=INK)
    s.paint("sidewall", GOLD, zone=shapes.wheel_ring(31.8, 32.6))

    s.step("Lights", "Speed numbers, rear lights and the grilles' glow in warm gold.", words=WORDS, look="rear night")
    s.relight("speed numbers", WARM)
    s.relight("rear lights", WARM)
    s.relight("brake lights", WARM)
    s.glow(["sidepod grille", "side vent"], WARM, "night only")
