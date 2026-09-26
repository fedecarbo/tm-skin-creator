"""Chaos and elegance, concept B (2026-09-26): black tie, and a pot of paint thrown at it. The car
dressed like a dinner suit: matte black cloth, and down each side the trousers' satin stripe, gloss
black between two fine ivory pinlines. Then one violent throw of ultramarine (an art gallery's
blue: ultramarine on black read as blood): it hits the left sidepod and flies up over the car towards
the right rear, a splash at the impact, drops and streaks thinning out along the throw. The
elegance is the tailoring; the chaos is one gesture."""
import numpy as np

from tool import noise, shapes

WORDS = "I want chaos and elegance"
CLOTH = "#101012"
IVORY = "#ece4d2"
PAINT = "#1f3cff"  # ultramarine, near Klein blue
INK = "#141416"
# the throw: where it hits (cm; x is the car's left), the way it flies
IMPACT = np.array([66.0, 58.0, 8.0])
THROW = np.array([-0.8, 0.2, -0.55])


def splash(impact=IMPACT, direction=THROW, drops=1400, reach=105.0, seed=4):
    """A throw of paint as a zone: a ragged splash round the impact, then drops that get smaller,
    sparser and more stretched along the throw the further they fly (about `reach` cm on average)."""
    u = direction / np.linalg.norm(direction)
    a = np.cross(u, (0, 1.0, 0))
    a /= np.linalg.norm(a)
    b = np.cross(u, a)
    rng = np.random.default_rng(seed)
    t = np.minimum(rng.exponential(reach, drops), 3.2 * reach)
    spread = 5 + 0.35 * t
    centres = impact + t[:, None] * u + rng.normal(0, 1, (drops, 1)) * spread[:, None] * a + rng.normal(0, 0.6, (drops, 1)) * spread[:, None] * b
    radius = 0.35 + 5.5 * np.exp(-t / (0.9 * reach)) * rng.uniform(0.25, 1, drops) ** 2
    stretch = 1 + t / 45

    def dist(p, n):
        from scipy.spatial import cKDTree
        # each drop lands on the nearest surface; one that would land more than 10 cm away missed the car
        tree = cKDTree(p)
        miss, near = tree.query(np.vstack([impact, centres]), workers=-1)
        hit, c = p[near[0]], p[near[1:]]
        keep = miss[1:] < 10
        c, rad, st = c[keep], radius[keep], stretch[keep]
        # the impact: a ragged blot about 36 cm across
        # (noise finer than a few cm made facets: value noise flattens at each lattice point)
        best = 18 * (0.7 + 0.6 * noise.fbm(p / 9, 2, seed + 1)) - np.linalg.norm(p - hit, axis=1)
        # the drops, each stretched along the throw and drawn whole over the points within its
        # reach (drawn only where it was among the nearest dozen centres, a big drop was cut
        # straight where small ones crowded it: many-sided blots)
        for j in range(len(c)):
            idx = np.asarray(tree.query_ball_point(c[j], rad[j] * 1.15 * st[j] + 0.3), np.int64)
            if not len(idx):
                continue
            d = p[idx] - c[j]
            along = d @ u
            across = d - along[:, None] * u
            wobble = 1 + 0.15 * (noise.value(p[idx] / 3 + j % 7, seed + 2) - 0.5)
            best[idx] = np.maximum(best[idx], rad[j] * wobble - np.sqrt((along / st[j]) ** 2 + (across ** 2).sum(1)))
        return best

    return shapes.field(dist, soft=0.15)


# the side stripe: along each flank at this height (cm), this tall, its pinlines this wide
STRIPE_Y, STRIPE, PIN = 38.0, 5.0, 0.5


def side_stripe(height):
    """A band `height` cm tall along both flanks, level at STRIPE_Y, on the faces that look sideways."""
    # crisp where the flank turns away: about 20 cm per unit of the normal, so the edge is a sharp line
    return shapes.field(lambda p, n: np.minimum(height / 2 - np.abs(p[:, 1] - STRIPE_Y), (np.abs(n[:, 0]) - 0.6) * 20))


def inner_car(s, dark=INK):
    """The inner car dark, as TSC_Stealth_CMYK's base without its body paint."""
    s.paint("inner", "satin", colour=dark)
    s.paint(["lower wishbone", "upper wishbone", "pushrod", "tie rod", "rear arm", "sidepod strut"], "carbon")
    s.paint(["damper", "rear damper", "upright", "hub bracket", "driveshaft", "upright cover", "hub", "brake light", "sidepod frame"],
            "satin", colour="#1e1f22")
    s.paint("exhaust", "brushed titanium")
    s.paint(["seat", "steering wheel"], "black leather")
    s.paint("dashboard", "matte", colour="#1a1b1d")


def design(s):
    s.clay()
    s.step("Black tie", "Matte black like dinner-suit cloth; down each side the trousers' satin stripe, "
           "gloss black between two fine ivory pinlines.", words=WORDS)
    s.paint("body", "matte", colour=CLOTH)
    s.paint("body", "satin", colour=IVORY, zone=side_stripe(STRIPE + 2 * PIN))
    s.paint("body", "wet look", colour=CLOTH, zone=side_stripe(STRIPE))

    s.step("The throw", "One throw of glossy ultramarine paint: it hits the left sidepod and flies over the car "
           "towards the right rear, drops and streaks thinning out along the way.", words=WORDS)
    # satin: glossy drops caught the sky as white dots from behind, the chase camera's view
    s.paint("body", "satin", colour=PAINT, zone=splash())

    s.step("Inner car", "Black inside, the grilles, calipers and belts ultramarine, a quilted black seat.", words=WORDS)
    inner_car(s)
    s.paint(["sidepod grille", "side vent", "brake caliper", "seat belt", "front wing endplate"], "satin", colour=PAINT)
    s.paint("sidepod grille plate", "satin", colour=INK)
    s.paint(["mirror", "mirror arm"], "wet look", colour=CLOTH)
    s.relief("seat", "quilted", depth=0.5, scale=7, replace=True)

    s.step("Wheels", "Gloss black covers, a thin ultramarine line round each tyre.", words=WORDS)
    s.paint("wheel covers", "wet look", colour=CLOTH)
    s.paint("rim", "satin", colour=INK)
    s.no_glow("wheel ring")
    s.paint("wheel ring", "satin", colour=INK)
    s.paint("sidewall", "satin", colour=PAINT, zone=shapes.wheel_ring(31.8, 32.6))

    s.step("Lights", "Ivory speed numbers, ultramarine rear lights and grilles glowing ultramarine at night.", words=WORDS, look="rear night")
    s.relight("speed numbers", IVORY)
    s.relight("rear lights", PAINT)
    s.relight("brake lights", PAINT)
    s.glow(["sidepod grille", "side vent"], PAINT, "night only")
