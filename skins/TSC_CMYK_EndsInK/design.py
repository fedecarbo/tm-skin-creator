"""CMYK Ends In K, the user's car: a matte black wrap torn open in ragged
patches, a satin cyan > magenta > orange run showing through the tears from the nose to the tail
(the black wrap is the K), a tiny grain in the wrap's sheen. Inside, every light the game put
there takes the run's colours, the suspension is bead-blasted titanium, the seat quilted, and a
printer's registration mark is raised at each end of the tail. The wheels are matte black with a
line round each tyre running cyan > magenta > orange from the wheel's front to its back."""
from dataclasses import replace

import numpy as np
from PIL import Image, ImageDraw

from tool import finishes, shapes

C, M = "#00c8ff", "#ff1fa8"
ORANGE = "#ff9a1a"   # the run's end
BLACK = "#232528"    # the wrap's black
DARK = "#1e1f22"
SHADE = "#1a1b1d"

# the body's parts and the inner car's, for the black wrap's first coat
SUSPENSION_CARBON = ["lower wishbone", "upper wishbone", "pushrod", "tie rod", "rear arm", "sidepod strut"]
SUSPENSION_DARK = ["damper", "rear damper", "upright", "hub bracket", "driveshaft", "upright cover", "hub", "brake light",
                   "sidepod frame"]
# the game's own lights, stock teal and white, found part by part: little lamps in the cockpit,
# nose and bulkhead, the strip under the floor, the vanes
# and sidepod panels, and the faint night glows on the airboxes, sidepod frames and steering
LIGHTS = ["cockpit tub", "front bulkhead", "nose inner", "floor rail", "side vane", "sidepod panel", "front wing endplate",
          "airbox", "sidepod frame", "sidepod strut", "steering column", "steering wheel", "tie rod", "exhaust"]
# the parts the game lights in the turbo pad's colour: those in the wheels glow magenta (the
# user's pick; all four wheels share one paint), the rest in the run's colour where they sit
TURBO_WHEELS = ["hub", "hub bracket", "upright cover", "lower wishbone", "upper wishbone", "tie rod", "rear arm",
                "driveshaft", "damper", "pushrod"]
TURBO_REST = ["rear strake", "rear undertray", "front bulkhead", "antenna", "brake line", "wing bracket", "rear bumper corner",
              "nose inner", "exhaust"]
# inside the tail's two openings, beside the speed digits: their walls, not the frame's face
PORTS = shapes.box((-50, 20, -158), (50, 49, -120)) & ~shapes.facing((0, 0, -1), 0.7)
TAIL = ["tail frame", "rear bumper", "rear strake"]
# the colour inside takes the body's run where it sits, and the floor's edges glow at night
ACCENTS = ["sidepod grille", "sidepod panel", "seat belt", "cockpit rim", "mirror", "mirror arm", "floor edge"]
ACCENT_WORDS = ("I think these need to follow the gradient.  Not sure why it's blue. This as well need to follow the "
                "gradient.  Basically the mirror and grill would be within the magenta. Would be nice to have that also "
                "follow the gradient and make it glow at night")
# the suspension in metal: it shares paint only with the small patch the front uprights wear,
# which goes metal with them
SUSPENSION = ["lower wishbone", "upper wishbone", "pushrod", "tie rod", "rear arm", "damper", "rear damper", "upright",
              "hub bracket", "driveshaft"]
CARBON_ARMS = ["lower wishbone", "upper wishbone", "pushrod", "tie rod", "rear arm"]
# the fasteners on the cockpit, the engine cover, the nose and the front wing all wear one tiny strip
# of the inner car's paint (u, v in texels of 4096), which the parts list gives to the front wing,
# so they take its cyan wherever they sit unless painted by hand
FASTENERS = (2247, 2253, 2565, 2609)


def registration_mark(px=512):
    """A printer's registration mark: a ring with a cross through it, white on clear."""
    im = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    w = px * 0.07
    r = px * 0.3
    c = px / 2
    d.ellipse((c - r, c - r, c + r, c + r), outline=(255, 255, 255, 255), width=int(w))
    d.rectangle((c - w / 2, 0, c + w / 2, px), fill=(255, 255, 255, 255))
    d.rectangle((0, c - w / 2, px, c + w / 2), fill=(255, 255, 255, 255))
    return im


def round_wheel(lo, hi):
    """0 at `lo` and 1 at `hi` of the way round each wheel from its front (0) to its back (1),
    over the top and under the bottom alike."""
    def f(p, n):
        zc = np.where(p[:, 2] > 30, shapes.WHEEL_Z[0], shapes.WHEEL_Z[1])
        t = np.abs(np.arctan2(p[:, 1] - shapes.WHEEL_Y, p[:, 2] - zc)) / np.pi
        return np.clip((t - lo) / (hi - lo), 0, 1)
    return shapes.Zone(f)


def tyre_line(s, r0, r1):
    """A line round each tyre, cyan at the wheel's front, magenta over the top and bottom, orange at its back."""
    line = shapes.wheel_ring(r0, r1)
    s.paint("sidewall", "satin", colour=C, zone=line)
    s.paint("sidewall", "satin", colour=M, zone=line & round_wheel(0, 0.5))
    s.paint("sidewall", "satin", colour=ORANGE, zone=line & round_wheel(0.5, 1))


def inner_run(s, where):
    """The inner car's own run over the sidepod's length (z 36 .. -47), under the body's run that
    replaces it later on the parts the user saw."""
    s.paint(where, "satin", colour=C)
    s.paint(where, "satin", colour=M, zone=shapes.fade("z", 36, -2))
    s.paint(where, "satin", colour=ORANGE, zone=shapes.fade("z", -10, -47))


def run_zones():
    """The body's run along the car: cyan at the nose, magenta in the middle, orange at the tail."""
    return shapes.fade("z", 150, 50), shapes.fade("z", -10, -100)


def light_run(s, where):
    """The game's lights on these parts take the run's colour where they sit, keeping their brightness."""
    mid, back = run_zones()
    s.relight(where, C, keep_level=True)
    s.relight(where, M, zone=mid, keep_level=True)
    s.relight(where, ORANGE, zone=back, keep_level=True)


def paint_run(s, where):
    """Paint parts in the body's run: each takes the body's colour where it sits along the car."""
    mid, back = run_zones()
    s.paint(where, "satin", colour=C)
    s.paint(where, "satin", colour=M, zone=mid)
    s.paint(where, "satin", colour=ORANGE, zone=back)


def turbo_run(s, where):
    """The parts the game lights in the turbo pad's colour light in the run's colours instead:
    exhaust heat, which keeps its own colour and comes on in a turbo ("ON when Turbo is enabled",
    xrayjay's table; never seen yet in the game, so these are its test)."""
    mid, back = run_zones()
    s.glow(where, C, "exhaust heat", replacing="turbo", keep_level=True)
    s.relight(where, M, zone=mid, keep_level=True)
    s.relight(where, ORANGE, zone=back, keep_level=True)


def fasteners(s, what="gunmetal"):
    """Paint the fasteners' strip: one strip can't follow the run, so they're a metal, as
    fasteners are."""
    c = s.canvas("Details")
    x0, x1, y0, y1 = (round(v * c.w / 4096) for v in FASTENERS)
    idx = (np.arange(y0, y1)[:, None] * c.w + np.arange(x0, x1)[None, :]).ravel()
    f = finishes.get(what)
    c.blend(idx, np.ones(len(idx), np.float32), np.asarray(f.colour, np.float32), f.roughness, f.metalness, f.varnish)


def wrap(s):
    """The black wrap's first coat over the whole car, the inner car in raw materials and the run."""
    s.paint("body", "matte", colour=BLACK)
    s.paint("inner", "satin", colour="#2a2b2e")
    s.paint(SUSPENSION_CARBON, "carbon")
    s.paint(SUSPENSION_DARK, "satin", colour=DARK)
    s.paint("exhaust", "brushed titanium")
    s.paint(["seat", "steering wheel"], "black leather")
    s.paint("dashboard", "matte", colour=SHADE)
    s.paint("rim", "satin", colour=DARK)
    inner_run(s, ["sidepod frame", "sidepod grille", "sidepod panel", "seat belt"])
    s.paint(["brake caliper", "brake line", "front wing endplate"], "satin", colour=C)
    s.paint(["side vent", "rear strake"], "satin", colour=ORANGE)
    s.paint(["front wing", "wing mounts"], "satin", colour=C)
    s.paint(["tail frame", "rear bumper", "rear light"], "satin", colour=ORANGE)
    inner_run(s, ["cockpit rim", "mirror", "mirror arm"])
    # the plate each grille sits in goes black, to break up the run
    s.paint("sidepod grille plate", "satin", colour=DARK)
    s.glow(["sidepod grille", "side vent"], None, "always on")
    s.glow("brake caliper", None, "brake lights")
    # the ring round each sidepod inlet in the wrap's black, so the colour comes only through
    # the tears (user); the glowing grille inside keeps its colour
    s.paint("sidepod frame", "matte", colour=BLACK)


def grain(s):
    """A tiny grain in the wrap's sheen."""
    s.step("A fine grain", "A tiny grain in the black wrap's sheen, like textured vinyl: seen up close where the light falls. The trims plain matte.",
           words="I was just thinking tiny grain just to have a bit of texture.")
    s.paint("body", "textured wrap", colour=BLACK)
    # the trims stay plain matte, the ring round each sidepod inlet and the band round the cockpit
    # (the user's notes: "I would have these normal matte black", "Same with this")
    s.paint(["sidepod frame", "cockpit surround"], "matte", colour=BLACK)
    # the rings a touch less matte (the user's note: "im ok with matte but it needs to be slightly
    # less matte"): beside the grained wrap, matte 90 % read chalky
    s.paint("sidepod frame", colour=BLACK, finish=replace(finishes.get("matte"), name="matte 70", roughness=0.7))
    s.paint("wing pylon", "satin", colour=C)  # the front wing's supports stay cyan


def design(s):
    # underneath: the run along the whole body (satin, so the colour holds at every angle)
    s.step("The colour run", "Satin cyan to magenta to the end colour along the body, under the wrap to come.",
           words="I wonder if you can make the body of the car as if the skin is peeling off and it reveals cmyk color.")
    s.paint("body", "satin", colour=C)
    s.paint("body", "satin", colour=M, zone=shapes.fade("z", 150, 50))
    s.paint("body", "satin", colour=ORANGE, zone=shapes.fade("z", -10, -100))
    under = s.keep()
    # on top: the black wrap, torn open
    s.step("The black wrap", "Matte black over the whole body; the inner car in the run's colours.",
           words="Can you remove the black tape.")
    wrap(s)
    grain(s)
    s.step("Torn open", "The wrap torn off in ragged patches (about half), hard edges and a thin even shadow, the run showing through.",
           words="Make the edges of the torn sharper.")
    s.peel(under, amount=0.45, scale=40, seed=11, hold=None)

    s.step("Lights", "Cyan brake lights, magenta speed numbers, rear lights by gear in the run's colours, rims that glow orange when braking hard.",
           words="You could update the cmyk one with more tailored lights if you want.", look="rear night")
    s.relight("brake lights", C)
    s.relight("speed numbers", M)
    # one colour per gear band, from the tail's corner inwards; unlit, the bars are dark (not the
    # run's colour), so each lit band shows its true colour
    s.relight("rear lights", [C, C, M, M, ORANGE])
    s.paint("rear light", "satin", colour=DARK)
    # brake heat: the rims glow orange as they heat up under hard braking; glow() tints the paint,
    # so the rims go back to the dark satin
    s.glow("rim", ORANGE, "brake heat")
    s.paint("rim", "satin", colour=DARK)

    s.step("Wheels", "Matte black covers, and a line round each tyre from cyan at the front to orange at the back.",
           words="If you can actually do a radial effect of that line that gradients the cmyk.")
    # the wheel covers matte black over the stock mirror chrome
    s.paint("wheel covers", "matte", colour=BLACK)
    tyre_line(s, 31.7, 32.9)
    s.relight("speed numbers", ORANGE)
    # one line per tyre (the user): the glowing ring inside each wheel goes dark, and the tyre's
    # line a little thicker, 1.6 cm (31.5 to 33.1 cm from the axle)
    s.no_glow("wheel ring")
    s.paint("wheel ring", "matte", colour=BLACK)
    tyre_line(s, 31.5, 33.1)
    # the inside's lights, and the turbo
    light_run(s, LIGHTS)
    s.relight(["hub", "brake light"], C, keep_level=True)
    s.glow(TURBO_WHEELS, M, "exhaust heat", replacing="turbo", keep_level=True)
    turbo_run(s, TURBO_REST)
    s.glow("tail frame", ORANGE, "exhaust heat", zone=PORTS)  # the openings, orange-hot in a turbo
    s.no_glow("rear bumper")  # under the deck, hidden by the body: stock, it glows white all the time
    # the exhaust heat-tinted, as real
    # titanium pipes go, straw gold at the engine through magenta-purple to blue at the tips
    s.paint("exhaust", "brushed titanium", colour="#c9a24a")
    s.paint("exhaust", "brushed titanium", colour="#9a4f9e", zone=shapes.fade("z", -115, -130))
    s.paint("exhaust", "brushed titanium", colour="#3f6fd0", zone=shapes.fade("z", -130, -145))
    # (before the tail: the pipes' trim shares a few texels with the tail's frame, and the tail
    # must win them, or they show as gold dashes along its edges)
    s.paint(TAIL, "matte", colour=BLACK)
    # the openings under the quarter panels, seen whenever the air brakes lift: dark like the rest
    # of the inside
    s.paint("airbox", "matte", colour=SHADE)
    # relief: a quilted seat, and a registration mark raised at each end of the tail's top band
    s.relief("seat", "quilted", depth=0.5, scale=7, replace=True)
    s.emboss(None, "tail frame", at=(38, 56, -157), right=(-1, 0, 0), picture=registration_mark(), width=5.5, depth=0.15)

    s.step("In the body's run", "The mirrors, sidepod grilles, cockpit rim, belts and the floor's edges in the body's colour "
           "where they sit; the floor's edges glow at night.", words=ACCENT_WORDS, look="night")
    paint_run(s, ACCENTS)
    # the cockpit rim and sidepod panels share a small patch of paint with many inner parts (all of
    # the front uprights'): the uprights go dark, or they'd take the run's pink
    s.paint("upright", "matte", colour=SHADE)
    s.glow("sidepod grille", None, "always on")  # the grilles glow in the run's colours
    s.glow("floor edge", None, "night only")
    fasteners(s)

    s.step("Metal suspension", "The wishbones, pushrods, tie rods, rear arms, dampers, uprights and driveshafts in "
           "bead-blasted titanium, a shade dark: matte, but metal.",
           words="I thing joints and those things shouldnt be matte?  Or I guess, matte but mettalic, so they look more "
                 "realistic. same with these")
    s.paint(SUSPENSION, "bead-blasted titanium", colour="#6b6d72")
    # Nadeo's relief on the arms is a carbon weave, which on metal read as woven metal: smooth
    s.relief(CARBON_ARMS, lambda pos, nrm: np.zeros(len(pos), np.float32), replace=True)
