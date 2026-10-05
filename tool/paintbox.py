"""The paint box: a skin is a short script of plain paint calls on named parts of the car.

    from tool.paintbox import Skin
    from tool import shapes

    def design(s):
        s.paint("body", "gloss white")                       # every body part
        s.paint("body", "racing red", zone=shapes.stripe(18))  # a stripe down the middle
        s.paint(["nose tip", "wing pylon"], "matte black")
        s.paint("inner", "dark grey satin")                   # the whole inner car
        s.paint("rim", "gunmetal")
        s.text("27", "left side", colour="black", font="russo", height=28)
        s.glow("sidepod frame", "electric blue")              # always on (inner car only)
        s.glow("brake caliper")                               # glow in the colour painted on it
        s.relight("speed numbers", "lime")                    # the stock glow, recoloured
        s.paint("sidewall", "white rubber")                   # the tyres' sides
        s.glass("smoke", 0.6)                                 # tint the glass
        s.dirt(0.5)                                           # half as dirty as stock on dirt
        under = s.keep()                                      # the paint so far, as a layer...
        s.paint("body", "matte black")                        # ... under a wrap ...
        s.peel(under, amount=0.2)                             # ... torn open (tool/peel.py)
        s.wear(under, fade=0.3, chips=0.05)                   # or aged: faded, chipped (tool/wear.py)

Words: `what` is a phrase the tool sorts into a colour, a finish and (optionally) a region:
"dark red carbon, glossy", "brushed steel", "olive camo" (see tool/colours.py, tool/finishes.py,
tool/shapes.REGIONS). Every painted area is a colour plus a finish; a finish may bring its own
colour (carbon black, chrome silver), which a stated colour overrides. Later calls paint over
earlier ones. Edges between parts and zones are anti-aliased; patterns are drawn in 3D.

`where`: a part, assembly or group name from car/parts.json, a list of them, or one of the words
"body" (the paint set without the wheel covers), "wheels" (the covers, rims, hubs and wheel
rings: their own design step, never touched by body paint), "wheel covers", "inner" (Details),
"tyres" (Wheels), "glass", "everything". The lights have plain words too (LIGHT_WORDS): "speed
numbers", "brake lights", "rear lights".
The parts list's groups are the game's maps (body, details, tyres, glass): the words above say the
same, but "body" here leaves the wheel covers out. An assembly or group leaves its glass out unless the glass is named.
Narrow a part with "|left", "|right", "|front", "|rear": "brake caliper|left|front". "floor",
"front wing" and "engine cover" name an assembly and a part in it; "|part" means the part only:
"floor|left|part". The Lab's rooms copy the phrase for any part (parts.Parts.token).

Steps (the Lab shows the car at the end of each while it's painted): a design starts with
s.clay(), the car in the Lab's neutral white clay, which stays on any part no later step paints
(in the game too): at the end, the paint box names the parts still in clay (a note, and the last
step's), since clay and white paint look alike. Then each step opens with a name, what it does and
the user's words that asked for it:
    s.clay()
    s.step("The colour run", "Satin cyan to magenta to orange along the body.",
           words="make the body ... reveal cmyk color")
    s.paint("body", "satin", colour=C) ...
    s.step("Lights", "...", look="rear night")      # a step the day's front view can't show
Paint before the first step is a step of its own ("The design" when it's the only one).

The result: Skin.textures() gives the game's textures as float arrays; tool/build.py puts them in
the viewer and builds the game's DDS files and the zip. Sets the design never touches aren't
shipped, so they keep the stock look.
"""

import functools
import hashlib
import os
import re

import numpy as np
from PIL import Image, ImageDraw

from tool import bake, colours, coverage, finishes, fonts, looks, paint, parts, paths, progress, raster, shapes
from tool.dds import stock

SIZES = {"Skin": (4096, 4096), "Details": (4096, 4096), "Wheels": (1024, 2048), "Glass": (1024, 1024)}
SET_WORDS = {"skin": "Skin", "inner": "Details", "details": "Details", "inside": "Details",
             "tyres": "Wheels", "tires": "Wheels", "glass": "Glass"}
# "body" is the paint set without the wheel covers: the wheels are their own design step and
# body paint or a scatter must never reach them (user, 2026-09-24). "wheels" is everything on
# a wheel but the tyre: the covers (Skin) and the rims, hubs and wheel rings (Details).
WHEEL_COVER_PARTS = ("wheel cover disc", "wheel cover hub", "wheel cover ring")
WHEEL_PARTS = WHEEL_COVER_PARTS + ("rim", "hub", "brake light", "wheel ring")
# the words that name a group of parts, not a part: paint on one that runs over a part painted by
# name is said (tool/checks.py)
GROUP_WORDS = frozenset(("everything", "body", "wheels", "wheel", "wheel covers", "wheel cover", *SET_WORDS))
# the lights a skin can recolour, in plain words (the lights test, 2026-09-25), for relight()
LIGHT_WORDS = {"speed numbers": "digit display", "speed digits": "digit display", "speedometer": "digit display",
               "digits": "digit display", "brake lights": "brake light", "rear lights": "rear light",
               "tail lights": "rear light", "gear lights": "rear light"}
# the rear lights' gear bands: the texture v where bands 2 to 5 start, on the bars (u < 0.5; the
# centre piece is u > 0.5). Band 1 is at the tail's corner. The viewer's rear lights use the same.
REAR_BANDS = (0.4747, 0.4903, 0.5030, 0.5157)
# a part the paint also lands on (shared texels) is named when it takes this share of its paint
SHARED_NOTE = 0.05

# Where lettering and pictures go: centre (cm), the image's right and up on the car, the side it's
# seen from, the largest sensible width (cm). Measured on the model (2026-09-24).
SPOTS = {
    "left side": dict(centre=(70, 41, -66), right=(0, 0, -1), up=(0, 1, 0), facing=(1, 0, 0), width=34, parts=("rear flank", "sidepod inlet", "side skirt", "body shell")),
    "right side": dict(centre=(-70, 41, -66), right=(0, 0, 1), up=(0, 1, 0), facing=(-1, 0, 0), width=34, parts=("rear flank", "sidepod inlet", "side skirt", "body shell")),
    "left flank": dict(centre=(35, 55, 60), right=(0, 0, -1), up=(0, 1, 0), facing=(0.8, 0.3, 0.2), width=70, parts=("body shell",)),
    "right flank": dict(centre=(-35, 55, 60), right=(0, 0, 1), up=(0, 1, 0), facing=(-0.8, 0.3, 0.2), width=70, parts=("body shell",)),
    "nose": dict(centre=(0, 50, 180), right=(-1, 0, 0), up=(0, 0, 1), facing=(0, 0.93, 0.3), width=30, parts=("nose tip",)),
    "bonnet": dict(centre=(0, 66, 117), right=(-1, 0, 0), up=(0, 0, 1), facing=(0, 0.95, 0.18), width=45, parts=("body shell",)),  # the free bonnet: z 91..142 (2026-09-24)
    "left sidepod": dict(centre=(70, 61, -20), right=(-1, 0, 0), up=(0, 0, 1), facing=(0.18, 0.97, 0), width=28, parts=("sidepod top",)),
    "right sidepod": dict(centre=(-70, 61, -20), right=(-1, 0, 0), up=(0, 0, 1), facing=(-0.18, 0.97, 0), width=28, parts=("sidepod top",)),
    "left deck": dict(centre=(38, 69, -95), right=(0, 0, -1), up=(-0.33, 0.91, 0), facing=(0.33, 0.91, -0.1), width=45, parts=("engine cover",)),
    "right deck": dict(centre=(-38, 69, -95), right=(0, 0, 1), up=(0.33, 0.91, 0), facing=(-0.33, 0.91, -0.1), width=45, parts=("engine cover",)),
    "tail": dict(centre=(0, 63, -161), right=(-1, 0, 0), up=(0, 1, 0), facing=(0, -0.23, -0.94), width=50, parts=("tail panel",)),
}


class Canvas:
    """One texture set's layers, starting from the stock textures."""

    def __init__(self, tset, w, h):
        self.set, self.w, self.h = tset, w, h
        self.bake = bake.bake(tset, w, h)
        self.cov = self.bake["tri"] >= 0
        # a texel on an island's edge can be partly covered by a part (coverage samples 2x2)
        # while its centre misses every triangle, so the bake left it at the origin and a
        # pattern drawn there came out as a speck along the seam: it takes the nearest texel's.
        # The same nearest texels fill the gaps between islands in textures() (raster.fill_holes).
        self.near = raster.nearest(self.cov)
        self.pos = self.bake["position"].reshape(-1, 3)[self.near]
        self.nrm = self.bake["normal"].reshape(-1, 3)[self.near]
        self._uv_cm = None
        n = w * h
        b = stock(f"{tset}_B" if tset != "Glass" else "Glass_T", (w, h))
        self.colour = np.ascontiguousarray(b[..., :3].reshape(n, 3)).astype(np.float32)
        if tset == "Glass":
            self.alpha = np.ascontiguousarray(b[..., 3].reshape(n)).astype(np.float32) if b.shape[-1] > 3 else np.ones(n, np.float32)
            self.rough = self.metal = self.coat = None
        else:
            r = stock(f"{tset}_R", (w, h))
            self.rough = np.ascontiguousarray(r[..., 0].reshape(n)).astype(np.float32)
            self.metal = np.ascontiguousarray(r[..., 1].reshape(n)).astype(np.float32) if r.shape[-1] > 1 else np.zeros(n, np.float32)
            self.coat = np.zeros(n, np.float32) if tset == "Skin" else None  # CoatR 0: glossy varnish all over, as with no file
        self.touched = np.zeros(n, bool)
        self.clay = None  # texels still in the Studio's clay (Skin.clay), None when it wasn't used
        self.owner = None  # the call that covered each texel last (Skin.ops; -1 the stock), while Skin.measure
        self.named = None  # the last call that painted each texel's part whole, by its name (-1 none), while Skin.measure
        self.op = -1  # the call painting now
        self.glow_rgb = self.glow_code = None
        self.glow_touched = False
        if tset == "Details":
            i = stock("Details_I", (w, h), Image.NEAREST)
            self.glow_rgb = np.ascontiguousarray(i[..., :3].reshape(n, 3)).astype(np.float32)
            a = np.rint(i[..., 3].reshape(n) * 255)
            self.glow_code = finishes.glow_codes(a)
        # the design's relief (tool/relief.py): slopes along u and v, and how much of Nadeo's own
        # relief stays under it; None until a design asks for relief
        self.slope = self.keep_stock = None
        self.normal = None  # the tyres' normal map (n, 2), once a marking brings relief (tool/tyres.py)
        self.dirt = None  # None: ship the stock mask untouched

    @property
    def uv_cm(self):
        if self._uv_cm is None:
            from tool import uvmap
            self._uv_cm = uvmap.uv_cm(self.set, self.w, self.h).reshape(-1, 2)
        return self._uv_cm

    def blend(self, idx, m, colour, rough=None, metal=None, varnish=None):
        """Mix new values into the layers at flat indices idx, by weight m (n,)."""
        mm = m[:, None]
        self.colour[idx] = self.colour[idx] * (1 - mm) + colour * mm
        if self.rough is not None:
            if rough is not None:
                self.rough[idx] = self.rough[idx] * (1 - m) + rough * m
            if metal is not None:
                self.metal[idx] = self.metal[idx] * (1 - m) + metal * m
            if self.coat is not None and varnish is not None:
                self.coat[idx] = self.coat[idx] * (1 - m) + (1 - varnish) * m
        self.touched[idx] |= m > 0.001
        if self.clay is not None:
            self.clay[idx[m > 0.5]] = False
        if self.owner is not None:
            self.owner[idx[m > 0.5]] = self.op

    def textures(self):
        """The game's textures for this set, or {} when the design never touched it."""
        if not self.touched.any() and not self.glow_touched and self.dirt is None and self.slope is None and self.normal is None:
            return {}
        h, w = self.h, self.w
        fill = lambda image: raster.fill_holes(image, self.cov, self.near)
        out = {}
        if self.set == "Glass":
            rgba = np.concatenate([self.colour, self.alpha[:, None]], 1).reshape(h, w, 4)
            out["Glass_T"] = (fill(rgba), "DXT5", {"srgb": False})
            return out
        if self.touched.any():
            out[f"{self.set}_B"] = (fill(self.colour.reshape(h, w, 3)), "DXT1", {"srgb": True})
            rm = np.stack([self.rough, self.metal], 1).reshape(h, w, 2)
            out[f"{self.set}_R"] = (fill(rm), "ATI2", {})
            if self.coat is not None:
                out["Skin_CoatR"] = (fill(self.coat.reshape(h, w)), "ATI1", {})
        if self.glow_touched:
            rgba = np.concatenate([self.glow_rgb, dark_take_codes(self.glow_rgb, self.glow_code, w, h)[:, None].astype(np.float32) / 255],
                                  1).reshape(h, w, 4)
            out["Details_I"] = (rgba, "DXT5", {"codes_in_alpha": True})
        if self.slope is not None:
            from tool import relief
            n = relief.clean_stock(stock("Details_N", (w, h))).reshape(-1, 2)
            n = 0.5 + (n - 0.5) * self.keep_stock[:, None]
            ours = np.flatnonzero(np.abs(self.slope).max(1) > 1e-4)
            n[ours] = relief.combine(n[ours], relief.to_normal(self.slope[ours]))
            out["Details_N"] = (n.reshape(h, w, 2), "ATI2", {"normal": True})
        if self.normal is not None:
            out[f"{self.set}_N"] = (fill(self.normal.reshape(h, w, 2)), "ATI2", {"normal": True})
        if self.dirt is not None:
            out[f"{self.set}_DirtMask"] = (np.clip(stock(f"{self.set}_DirtMask") * self.dirt, 0, 1), "ATI1", {})
        return out


def dark_take_codes(rgb, code, w, h, reach=3):
    """The glow codes, with every unlit texel within `reach` texels of a glow taking that glow's
    code. The game and the viewer blend the glow colour between texels but read the code of the
    nearest one, so an unlit texel of another code beside a glow lit the glow's colour on its
    own terms along the edge: a dashed line of always-on orange round
    a turbo-lit opening. An unlit texel shows nothing whatever its code."""
    from scipy.ndimage import distance_transform_edt
    lit = (rgb.max(1) > 0.004).reshape(h, w)
    d, (iy, ix) = distance_transform_edt(~lit, return_distances=True, return_indices=True)
    fix = (~lit & (d <= reach)).reshape(-1)
    out = code.copy()
    out[fix] = code[(iy * w + ix).reshape(-1)[fix]]
    return out


def _op(describe):
    """A call that lays paint on the body, named for tool/measure.py: while Skin.measure is on,
    each body texel keeps the call that covered it last (Canvas.owner), so a paint cut short by a
    later one can say which. A call inside another (text, through decal) takes the outer one's name."""
    def wrap(method):
        @functools.wraps(method)
        def run(self, *args, **kw):
            if self._op_open:
                return method(self, *args, **kw)
            self.ops.append({"what": describe(*args, **kw), "step": self.steps[-1]["name"] if self.steps else "The design"})
            self._op, self._op_open = len(self.ops) - 1, True
            try:
                return method(self, *args, **kw)
            finally:
                self._op_open = False
        return run
    return wrap


def _where(where):
    return where if isinstance(where, str) else ", ".join(where)


class Skin:
    def __init__(self, name, seed=0, size=None):
        if not re.fullmatch(r"[A-Za-z0-9_\-]+", name):
            raise ValueError("a skin's name can only have letters, digits, _ and -")
        self.name = name
        self.seed = seed
        self.sizes = dict(SIZES)
        if size:
            self.sizes["Skin"] = self.sizes["Details"] = (size, size)
        self.parts = parts.load()
        self.canvases = {}
        self.notes = []  # what the tool decided, for the record
        self.icon_colours = []
        self.drawn = []  # the lines drawn on the car's skin (tool/skindraw.py), for tool/skincheck.py
        self.palette = []  # every colour laid on the car, so a check can tell a band's paint from the rest
        self.steps = []  # the design's steps (step()), for the Studio
        self.clay_left = None  # the parts still in clay when the design is done (end_steps)
        self.frames = False  # skin.show sets it: write the car at the end of each step for the Studio
        self._frame_slots = {}  # slot -> (digest, url) of the last frame's picture of it
        self._frame_sets = {}  # texture set -> its slots in the last frame, in order
        self._touched = set()  # the texture sets reached (Skin.canvas) since the last frame
        self._twin_cache = {}  # texture set -> coverage twins, for _warn_shared
        self._final = None  # the finished textures, built once when the design is done (end_steps)
        self.measure = False  # skin.show sets it: keep what tool/measure.py reads (the calls, who covered what)
        self.ops = []  # every call that laid paint: {what, step}
        self.zoned = []  # each zoned paint on the body: {op, step, what, where, zone, ids, group (where names a group
        # of parts), idx (the texels it covers), under (the call each of them showed before)}
        self.pictures = []  # each picture laid on the body, while measuring: {op, step, what, idx, under, pixels (per cm)}
        self.scattered = []  # each scatter on the body, while measuring (tool/scatter.py)
        self.findings = []  # what's wrong on the car, as the paint itself knows it (tool/checks.py adds the rest)
        self._op, self._op_open = -1, False

    # ---- steps: the Lab draws the car at the end of each ----

    def step(self, name, does, words=None, look=None):
        """Start a step of the design. name: a few words ("The colour run"); does: what it
        paints, in plain words; words: the user's own words that asked for it; look: how the
        Studio shows it when the day's front view can't: "rear", "night", "rear night"."""
        self._end_step()
        self.steps.append({"name": name, "does": does, "words": words or "", "look": look or "", "paints": []})
        progress.detail(f"Step {len(self.steps)}: {name}")
        if self.frames:  # the Studio shows it as being painted
            from tool import view
            view.export_steps(self.name, self.steps, painting=True)
        return self

    @_op(lambda: "the clay")
    def clay(self):
        """The first step of a design made in the Studio: the body, wheel covers and inner car in
        the Studio's clay, a neutral white (the user's pick, 2026-09-26). What no later step
        paints stays clay, in the game too. The tyres and glass keep their own."""
        self.step("Clay", "The car before any paint: all but the tyres and glass in the Studio's clay.")
        for where in ("body", "wheel covers", "inner"):
            self.paint(where, "clay")
            for tset, ids in self._ids(where).items():  # what later paint must cover
                c = self.canvas(tset)
                if c.clay is None:
                    c.clay = np.zeros(c.w * c.h, bool)
                idx, m = self._mask(tset, ids, None, c)
                c.clay[idx[m > 0.5]] = True
        return self

    def still_clay(self, least=0.2, texels=100):
        """The parts no step painted: [(instance id, part name)] for each part with at least
        `least` of its texels (and `texels` of them) still in clay. None for a design that didn't
        start from clay. Clay is a neutral white, so a part left in it passes for white paint
        and a white part looks forgotten."""
        found = None
        for tset, c in self.canvases.items():
            if c.clay is None:
                continue
            found = found or []
            cov = coverage.load(self.parts, tset, c.w, c.h)
            for i in cov.ids:
                idx, val = cov.sparse.get(i, ((), ()))
                if not len(idx):
                    continue
                inside = idx[val >= 128]
                left = int(c.clay[inside].sum())
                if left >= texels and left >= least * len(inside):
                    found.append((i, self.parts.instances[i]["name"]))
        return found

    def end_steps(self):
        """The design is done: the parts still in clay noted, the last step's frame, and the
        Studio's list marked finished."""
        self.clay_left = self.still_clay()
        if self.clay_left:
            self.notes.append("still clay (no step paints them): " + ", ".join(dict.fromkeys(n for _, n in self.clay_left)))
        # nothing paints after this: the last frame, summary(), the viewer and save_painted all
        # take these rather than each building them again (15 to 25 s a show)
        self._final = self.textures()
        self._end_step(done=True)

    def _end_step(self, done=False):
        """The car as it is now becomes the open step's frame: its pictures in the viewer's data at
        half size (only the ones that changed), and the Lab's list rewritten. A texture set no paint
        reached since the last frame keeps its pictures without being built again."""
        if not self.frames or not self.steps:
            return
        from tool import view
        k = len(self.steps) - 1
        if "textures" not in self.steps[k]:
            for tset, c in self.canvases.items():
                if tset not in self._touched and tset in self._frame_sets:
                    continue
                textures = ({t: v for t, v in self._final.items() if t.startswith(f"{tset}_")} if self._final is not None
                            else c.textures())
                self._frame_sets[tset] = []
                for tex_name, (arr, _, _) in textures.items():
                    for slot, im in view.convert(tex_name, arr).items():
                        if im.width >= 2048:
                            im = im.resize((im.width // 2, im.height // 2), Image.NEAREST if slot.endswith("_Code") else Image.LANCZOS)
                        digest = hashlib.sha1(im.tobytes()).hexdigest()[:12]
                        if self._frame_slots.get(slot, ("",))[0] != digest:
                            url = view.save_frame(self.name, k, slot, im, digest)
                            self._frame_slots[slot] = (digest, url)
                        self._frame_sets[tset].append(slot)
            self._touched.clear()
            own = {slot: self._frame_slots[slot][1] for tset in self.canvases for slot in self._frame_sets.get(tset, ())}
            self.steps[k]["textures"] = own
            self.steps[k]["frame"] = hashlib.sha1(repr(sorted(self._frame_slots.items())).encode()).hexdigest()[:12]
        view.export_steps(self.name, self.steps, painting=not done, clay=self.clay_left if done else None)

    # ---- selecting ----

    def _open_step(self):
        if not self.steps:  # paint before the first step is a step of its own
            self.steps.append({"name": "The design", "does": "", "words": "", "look": "", "paints": [], "implicit": True})
        return self.steps[-1]

    def canvas(self, tset):
        """A texture set's layers, made when first painted. Everything that paints reaches them here,
        which is how a step's frame knows which sets changed."""
        self._open_step()
        self._touched.add(tset)
        if tset not in self.canvases:
            w, h = self.sizes[tset]
            self.canvases[tset] = Canvas(tset, w, h)
            if self.measure and tset == "Skin":
                self.canvases[tset].owner = np.full(w * h, -1, np.int16)
                self.canvases[tset].named = np.full(w * h, -1, np.int16)
        c = self.canvases[tset]
        c.op = self._op
        return c

    def _ids(self, where):
        """(texture set, instance ids) pairs for a `where`."""
        names = [where] if isinstance(where, str) else list(where)
        paints = self._open_step()["paints"]  # what the open step paints, for the Studio
        paints += [n for n in names if n not in paints]
        out = {}
        for item in names:
            key = item.strip().lower()
            if key == "everything":
                for tset in ("Skin", "Details", "Wheels"):
                    out.setdefault(tset, set()).update(i for i, inst in enumerate(self.parts.instances) if inst["mesh"] == tset)
                continue
            if key in SET_WORDS:
                tset = SET_WORDS[key]
                out.setdefault(tset, set()).update(i for i, inst in enumerate(self.parts.instances) if inst["mesh"] == tset)
                continue
            if key == "body":
                out.setdefault("Skin", set()).update(i for i, inst in enumerate(self.parts.instances)
                                                     if inst["mesh"] == "Skin" and inst["name"] not in WHEEL_COVER_PARTS)
                continue
            if key in ("wheels", "wheel", "wheel covers", "wheel cover"):
                group = WHEEL_PARTS if key.startswith("wheels") or key == "wheel" else WHEEL_COVER_PARTS
                for name in group:
                    for i in self.parts.select(name):
                        out.setdefault(self.parts.instances[i]["mesh"], set()).add(i)
                continue
            bits = [b.strip() for b in key.split("|")]
            bits[0] = LIGHT_WORDS.get(bits[0], bits[0])
            side = next((b for b in bits[1:] if b in ("left", "right", "centre")), None)
            end = next((b for b in bits[1:] if b in ("front", "rear")), None)
            ids = self.parts.select(bits[0], side=side, end=end, exact="part" in bits[1:])
            # an assembly or group tints its glass only when the glass is named: painting the tail
            # must not darken the rear lights' lenses (the glass joined the assemblies, 2026-09-26)
            ids = [i for i in ids if self.parts.instances[i]["mesh"] != "Glass" or self.parts.instances[i]["name"] == bits[0]]
            for i in ids:
                out.setdefault(self.parts.instances[i]["mesh"], set()).add(i)
            self._warn_shared(bits[0], ids)
            self._warn_reach(bits[0], ids)
        return {tset: sorted(ids) for tset, ids in out.items()}

    def _warn_shared(self, name, ids):
        """Note the parts the paint also lands on, because they use the same texels: a mirror
        twin, the four wheels, or another part (half of each front wing wears the floor's paint,
        2026-09-26). Names each part that isn't chosen and would take SHARED_NOTE of its paint
        or more, with how much: "floor: its paint also lands on front wing (left, right: 47 %)"."""
        chosen = set(ids)
        hit = {}
        for tset in {self.parts.instances[i]["mesh"] for i in ids}:
            twins = self._twins(tset)
            for j, (texels, _, others) in twins.items():
                if j in chosen or not texels:
                    continue
                n = sum(c for i, c in others.items() if i in chosen)
                if n >= SHARED_NOTE * texels:
                    hit[j] = n / texels
        if not hit:
            return
        by_name = {}
        for j in sorted(hit, key=lambda j: (-hit[j], j)):
            by_name.setdefault(self.parts.instances[j]["name"], []).append(j)
        by_name = {k: sorted(js) for k, js in by_name.items()}  # the names by share, their sides in order
        much =lambda x: "all of it" if x >= 0.95 else f"{round(x * 100)} %"
        who = []
        for pname, js in by_name.items():
            if max(hit[j] for j in js) - min(hit[j] for j in js) < 0.03:  # twins: one share for all
                tags = ", ".join(t for t in (self.parts.tag(j) for j in js) if t)
                who.append(f"{pname} ({tags + ': ' if tags else ''}{much(hit[js[0]])})")
            else:
                who.append(f"{pname} ({', '.join(f'{self.parts.tag(j) or 'centre'} {much(hit[j])}' for j in js)})")
        self.notes.append(f"{name}: its paint also lands on {', '.join(who)}")

    def _twins(self, tset):
        if tset not in self._twin_cache:
            w, h = self.sizes[tset]
            self._twin_cache[tset] = coverage.load(self.parts, tset, w, h).twins()
        return self._twin_cache[tset]

    def _warn_reach(self, name, ids):
        """Note when a name reaches further than it seems: an assembly that shares its name with
        one of its parts ("front wing" is the wing, its endplates and lenses), or one whose parts are in
        more than one texture set."""
        chosen = [self.parts.instances[i] for i in ids]
        if not {o["name"] for o in chosen} - {name}:
            return  # a part, or "|part"
        ambiguous = any(o["name"] == name for o in self.parts.instances)
        if not ambiguous and len({o["mesh"] for o in chosen}) < 2:
            return  # an assembly's own name, all in one set: what it says
        words = {"Skin": "body", "Details": "inner car", "Wheels": "tyres", "Glass": "glass"}
        by_set = {}
        for i in ids:
            inst = self.parts.instances[i]
            if inst["name"] != name:
                by_set.setdefault(inst["mesh"], []).append(inst["name"])
        also = "; ".join(f"{', '.join(dict.fromkeys(names))} ({words[s]})" for s, names in by_set.items())
        hint = f"; '{name}|part' is the {name} alone" if any(self.parts.instances[i]["name"] == name for i in ids) else ""
        self.notes.append(f"{name}: the whole assembly, so it also paints {also}{hint}")

    def _mask(self, tset, ids, zone, canvas):
        cov = coverage.load(self.parts, tset, canvas.w, canvas.h).share(ids).reshape(-1)
        idx = np.flatnonzero(cov > 0.002)
        m = cov[idx]
        if zone is not None:
            shapes.PAINTING = tset
            try:
                m = m * zone(canvas.pos[idx], canvas.nrm[idx])
            finally:
                shapes.PAINTING = None
            keep = m > 0.002
            idx, m = idx[keep], m[keep]
        return idx, m

    # ---- painting ----

    def _resolve(self, what, colour, finish, default_finish, params=None):
        col, fin = None, None
        leftover = []
        if what:
            col, fin, leftover = finishes.resolve(what, default=default_finish)
        if colour is not None:
            col = np.asarray(colours.get(colour), np.float32)
        if finish is not None:
            fin = finishes.get(finish) if isinstance(finish, str) else finish
        if fin is None:
            fin = finishes.get(default_finish)
        if col is not None and params is not None:
            params["tinted"] = True  # the user named a colour: a photographed surface takes it as a tint
        if col is None:
            col = fin.colour
            if col is None and params and params.get("palette"):
                first = params["palette"][0]
                col = (0.5, 0.5, 0.5) if first in (None, "keep") else colours.get(first)
            if col is None and fin.look == "texture":
                col = (0.5, 0.5, 0.5)  # the photograph's own colours are used
            if col is None:
                raise ValueError(f"{what!r}: no colour given and the finish {fin.name!r} has none of its own")
        return np.asarray(col, np.float32), fin, leftover

    @_op(lambda where, what=None, colour=None, finish=None, *a, **k:
         f"{' '.join(x for x in (what or finish, colour) if isinstance(x, str)) or 'paint'} on {_where(where)}")
    def paint(self, where, what=None, colour=None, finish=None, zone=None, blend=1.0, **params):
        """Paint parts with a colour and a finish. `what` is a phrase; `colour` and `finish`
        override it. `zone` limits it (tool/shapes.py); leftover words that name a region
        ("nose", "sides") do too. `blend` < 1 paints it thinly. params reach the pattern:
        scale, seed, palette, line, amount, direction, texture."""
        targets = self._ids(where)
        default_finish = "rubber" if list(targets) == ["Wheels"] else "gloss"
        params = {"seed": self.seed, **params}
        col, fin, leftover = self._resolve(what, colour, finish, default_finish, params)
        for word in list(leftover):
            if word in shapes.REGIONS:
                zone = shapes.region(word) if zone is None else (zone & shapes.region(word))
                leftover.remove(word)
        if leftover:
            self.notes.append(f"{what!r}: didn't understand {' '.join(leftover)!r}")
        self.palette.append([float(v) for v in col])   # every colour laid on the car, for the checks
        if getattr(zone, "curve", None) is not None:  # drawn on the car's skin: kept for tool/skincheck.py
            curve = zone.curve
            self.drawn.append({"kind": zone.kind, "width": getattr(zone, "width", None), "name": curve.name,
                               "points": [[round(float(v), 4) for v in p] for p in curve.pts],
                               "colour": [float(v) for v in col], "closed": bool(curve.closed),
                               "soft": getattr(zone, "soft", None),
                               "order": len(self.palette) - 1,   # colours laid after it may cover it
                               "where": where if isinstance(where, str) else list(where),
                               **getattr(curve, "extra", {})})
        for tset, ids in targets.items():
            c = self.canvas(tset)
            idx, m = self._mask(tset, ids, zone, c)
            if not len(idx):
                continue
            m = m * blend
            if self.measure and tset == "Skin":
                on = idx[m > 0.5]
                group = all(n.strip().lower() in GROUP_WORDS for n in ([where] if isinstance(where, str) else where))
                if zone is not None:
                    self.zoned.append({"op": self._op, "step": self.ops[self._op]["step"], "what": self.ops[self._op]["what"],
                                       "where": where, "zone": zone, "ids": ids, "group": group, "idx": on,
                                       "under": c.owner[on].copy()})
                elif not group:
                    c.named[on] = self._op
            extra = {}
            if fin.look:
                # flat patterns on the body are drawn in the car's own unfolding (tool/uvmap.py),
                # which has almost no stretch (user, 2026-09-24: projections distorted the dots);
                # the inner car's unfolding is in many small pieces, so it uses the three planes
                extra = {"wrap": "uv" if tset == "Skin" else "planes"}
                if extra["wrap"] == "uv":
                    extra["uv"] = c.uv_cm[idx]
            colour_v, rough, metal, varnish, weight = looks.lay(fin, col, c.pos[idx], c.nrm[idx], {**extra, **params})
            if weight is not None:
                m = m * weight
            if tset == "Glass":
                c.colour[idx] = c.colour[idx] * (1 - m[:, None]) + colour_v * m[:, None]
                c.touched[idx] = True
            else:
                c.blend(idx, m, colour_v, rough, metal, varnish)
            if fin.glow and tset == "Details":
                self._glow(c, idx, m, col, fin.glow)
            elif fin.glow:
                self.notes.append(f"{fin.name} on {where}: only the inner car can glow; painted it bright instead")
        if len(self.icon_colours) < 2 and "Skin" in targets:
            self.icon_colours.append(tuple(float(v) for v in col))
        return self

    def keep(self, tset="Skin"):
        """A copy of a texture set's paint so far: the layer a peel reveals (tool/peel.py)."""
        c = self.canvas(tset)
        kept = {k: None if getattr(c, k) is None else getattr(c, k).copy() for k in ("colour", "rough", "metal", "coat", "clay")}
        return {**kept, "set": tset}

    def peel(self, under, where="body", **params):
        """Tear the paint open, as a wrap ripped off, to show `under` (from keep()): on the
        body, or on inner parts with an `under` kept from "Details" (tool/peel.py has the
        parameters)."""
        from tool import peel
        peel.peel(self, under, where, **params)
        return self

    def wear(self, under, where="body", **params):
        """Age the paint as it stands: faded by the sun, chipped down to `under` (from keep())
        where stones hit (tool/wear.py has the parameters)."""
        from tool import wear
        wear.wear(self, under, where, **params)
        return self

    def _glow(self, c, idx, m, col, kind):
        """col: one colour (3,), or a colour per texel (n, 3)."""
        g = finishes.glow(kind)
        rgb = np.asarray(col, np.float32)
        if rgb.ndim == 1:
            rgb = np.broadcast_to(rgb, (len(idx), 3))
        if not g["keeps colour"]:
            rgb = np.repeat(rgb.mean(1, keepdims=True), 3, 1)
        on = m > 0.5
        c.glow_rgb[idx[on]] = rgb[on]
        c.glow_code[idx[on]] = g["code"]
        c.glow_touched = True

    def glow(self, where, colour=None, kind="always on", zone=None, replacing=None, keep_level=False):
        """Make inner-car parts glow: kind is one of finishes.GLOWS ("always on", "night only",
        "brake lights", "front lights", "energy", ...). The body can't glow. colour None: the
        parts glow in whatever colour is already painted on them (so a fade can glow).
        replacing: only where the parts carry that kind of glow now (a stock one), swapped for
        this one: s.glow("hub", "magenta", "exhaust heat", replacing="turbo"). keep_level: each
        texel keeps the brightness it glowed with (relight's), and the paint is left alone."""
        col = None if colour is None else np.asarray(colours.get(colour), np.float32)
        targets = self._ids(where)
        for tset, ids in targets.items():
            if tset != "Details":
                self.notes.append(f"glow on {where}: only the inner car (Details) can glow; skipped {tset}")
                continue
            c = self.canvas(tset)
            idx, m = self._mask(tset, ids, zone, c)
            if replacing is not None:
                keep = c.glow_code[idx] == finishes.glow(replacing)["code"]
                idx, m = idx[keep], m[keep]
            if keep_level and col is not None:
                level = c.glow_rgb[idx].max(1)
                self._glow(c, idx, m, col / max(float(col.max()), 1e-6) * level[:, None], kind)
                continue
            if col is None:
                self._glow(c, idx, m, c.colour[idx], kind)
                continue
            self._glow(c, idx, m, col, kind)
            # the lit colour also goes in the base colour, so it reads the same by day
            c.blend(idx, m, np.broadcast_to(col, (len(idx), 3)), np.full(len(idx), 0.4, np.float32), np.zeros(len(idx), np.float32), np.zeros(len(idx), np.float32))
        return self

    def relight(self, where, colour, zone=None, keep_level=False):
        """Give the stock glow on parts a new colour. Each texel keeps its kind of glow and its
        brightness, so the pattern stays: the speed digits' segments with their dark backing, the
        brake lights' slots. The brightest texel takes the full colour. The
        paint is left as it is (a painted digit would show "888" by day). Glows whose colour
        the game supplies (energy, turbo, boost) stay grey.

        In the game (the lights test, 2026-09-25): "speed numbers" show only the lit segments, in
        this colour, braking or not. "brake lights" (the slots inside the front wheels) glow dimly
        and flare towards white while braking. "rear lights" fill up band by band with the gear
        in this colour and turn fully red while braking, whatever the colour. A tinted rear lens
        (glass) filters them, the braking red too: red through a blue or green lens looks dark.

        For "rear lights", colour may be a list of five, one per gear band from the tail's corner
        inwards: gear 1 lights the first, gear 5 all five. The centre piece (lit only when
        braking, red) takes the last.

        zone: recolour only where a zone says, blending by its weight, so a fade works as with
        paint: relight(parts, "cyan"), then relight(parts, "magenta", zone=shapes.fade(...)).
        keep_level: keep each texel's stock brightness and change only its hue (for faint lights,
        such as the night-only glows), rather than raising the brightest to the full colour."""
        bands = isinstance(colour, list)
        if bands and LIGHT_WORDS.get(where, where).split("|")[0] != "rear light":
            raise ValueError(f"relight {where}: a colour per gear band is for the rear lights only")
        cols = np.asarray([colours.get(c) for c in (colour if bands else [colour])], np.float32)
        own = [g["code"] for g in finishes.GLOWS.values() if g["keeps colour"]]
        for tset, ids in self._ids(where).items():
            if tset != "Details":
                self.notes.append(f"relight {where}: only the inner car (Details) glows; skipped {tset}")
                continue
            c = self.canvas(tset)
            idx, m = self._mask(tset, ids, None, c)
            idx = idx[(m > 0.5) & np.isin(c.glow_code[idx], own)]
            level = c.glow_rgb[idx].max(1)
            if not len(idx) or level.max() < 0.05:
                self.notes.append(f"relight {where}: no stock glow there to recolour")
                continue
            col = cols[0]
            if bands:
                rows, us = np.divmod(idx, c.w)
                band = np.searchsorted(REAR_BANDS, 1 - (rows + 0.5) / c.h, side="right")
                band[(us + 0.5) / c.w >= 0.5] = len(cols) - 1
                col = cols[np.minimum(band, len(cols) - 1)]
            if keep_level:
                new = col / np.maximum(np.max(col, axis=-1, keepdims=True), 1e-6) * level[:, None]
            else:
                new = col * (level / level.max())[:, None]
            if zone is not None:
                w = zone(c.pos[idx], c.nrm[idx])[:, None]
                new = c.glow_rgb[idx] * (1 - w) + new * w
            c.glow_rgb[idx] = new
            c.glow_touched = True
        return self

    def no_glow(self, where):
        """Switch the stock glow off on parts (paint them dark)."""
        for tset, ids in self._ids(where).items():
            if tset != "Details":
                continue
            c = self.canvas(tset)
            idx, m = self._mask(tset, ids, None, c)
            on = m > 0.5
            c.glow_rgb[idx[on]] = 0
            c.glow_touched = True
        return self

    def glass(self, colour, strength=1.0):
        """Tint the glass. strength 1 is the full colour, less keeps some of the stock tint."""
        c = self.canvas("Glass")
        col = np.asarray(colours.get(colour), np.float32)
        idx = np.flatnonzero(c.cov.reshape(-1))
        c.colour[idx] = c.colour[idx] * (1 - strength) + col * strength
        c.touched[idx] = True
        return self

    def dirt(self, amount, where="body"):
        """How dirty the car gets on dirt: 1 is the stock amount, 0 never dirty, 2 twice."""
        for tset in self._ids(where):
            if tset != "Glass":
                self.canvas(tset).dirt = float(amount)
        return self

    def tyre_marks(self, marking, reads="left", **options):
        """A tyre marking from the library (tool/tyres.py): "TY-07" or its name ("ring soft"), on
        all four tyres' sidewalls and tread, over the tyres' paint so far. options reach its layout
        where it takes them: colour="lime", words=("OXIDE", "BOX BOX"). The right-hand tyres show it
        mirrored: words read right on the side `reads` names, and on both when every letter is the
        same upside down (the library's are)."""
        from tool import tyres
        code, entry, art = tyres.draw(marking, **options)
        self._open_step()["paints"].append(f"tyres: {code} {entry['name']}")
        self.notes += tyres.apply(self.canvas("Wheels"), art, reads)
        return self

    def tyre_tread(self, tread):
        """A tread from the tread library (tool/tyres.py; the Lab's Treads): "TR-04" or its name
        ("wet"), on all four tyres in place of Nadeo's grooves. The sidewalls go plain (Nadeo's
        lettering off), as under any marking."""
        from tool import tyres
        code, entry = tyres.tread_find(tread)
        art = tyres.Art()
        entry["fn"](art)
        self._open_step()["paints"].append(f"tyres: {code} {entry['name']} tread")
        self.notes += tyres.apply(self.canvas("Wheels"), art)
        return self

    # ---- relief (the inner car only: the game's normal map, tool/relief.py) ----

    def _relief(self, where, make_h, zone=None, replace=False, what="relief"):
        """Lay a height function on inner-car parts. make_h(tris_xyz, pos, nrm) -> h(pos, nrm)
        in cm, given the parts' triangles and surface (for patterns that follow their edges or
        sit on given points)."""
        from scipy.ndimage import distance_transform_edt
        from tool import relief
        t_u, t_v = relief.frames("Details")
        for tset, ids in self._ids(where).items():
            if tset != "Details":
                self.notes.append(f"{what} on {where}: only the inner car takes relief; skipped {tset}")
                continue
            c = self.canvas(tset)
            idx, m = self._mask(tset, ids, zone, c)
            if not len(idx):
                continue
            # the parts' own positions (a shared texel's main-bake position may be another part's)
            lb = self.parts.local_bake(tset, c.w, c.h, ids=ids)
            hit = lb["tri"] >= 0
            near = distance_transform_edt(~hit, return_distances=False, return_indices=True)
            flat = near[0].reshape(-1)[idx] * c.w + near[1].reshape(-1)[idx]
            pos = lb["position"].reshape(-1, 3)[flat].astype(np.float32)
            nrm = lb["normal"].reshape(-1, 3)[flat]
            tris = np.flatnonzero(self.parts.tri_mask(tset, None, ids=ids))
            tri = tris[lb["tri"].reshape(-1)[flat]]
            mesh = self.parts._meshes["Details_01"]
            h = make_h(mesh["positions"][mesh["tri_vertex"][tris]], pos, nrm)
            s = relief.slopes(h, pos, nrm, t_u[tri], t_v[tri])
            if c.slope is None:
                c.slope = np.zeros((c.w * c.h, 2), np.float32)
                c.keep_stock = np.ones(c.w * c.h, np.float32)
            c.slope[idx] += s * m[:, None]
            if replace:
                c.keep_stock[idx] *= 1 - m
        return self

    def relief(self, where, pattern, depth=0.2, zone=None, replace=False, **params):
        """Raised (depth > 0, cm) or sunk detail on inner-car parts, in the game's normal map.
        pattern: "ribs" (scale apart, width, direction), "studs" (scale apart, size), "quilted"
        (scale: the diamonds), "hex" (scale, groove), "rivets" (size; at `points`, a list of
        (x, y, z) in cm, or along `line` = (from, to) every `spacing` cm, moved onto the parts'
        surface; else along the parts' open edges, `inset` cm in, where they aren't tucked
        under another part), or a function h(pos, nrm) -> cm. replace: a new surface, so
        Nadeo's own relief there goes; otherwise ours is laid over theirs. Features under 1 cm
        blur away when the map ships at 2048² (tool/relief.py)."""
        from tool import relief
        if callable(pattern):
            make = lambda tris, pos, nrm: pattern
        elif pattern == "rivets":
            def make(tris, pos, nrm):
                if "points" in params or "line" in params:
                    pts = params.get("points") or relief.line_points(*params["line"], params.get("spacing", 4.0))
                    pts = relief.snap(pts, pos)
                else:
                    pts = relief.edge_points(tris, params.get("spacing", 4.0), params.get("inset", 1.0), params.get("min_loop"))
                if not len(pts):
                    self.notes.append(f"rivets on {where}: no edge long enough for them")
                return relief.points(pts if len(pts) else np.zeros((1, 3)) + 1e6, depth, params.get("size", 1.0), params.get("bevel", 0.2))
        else:
            h = relief.PATTERNS[pattern](depth=depth, **params)
            make = lambda tris, pos, nrm: h
        return self._relief(where, make, zone, replace, what=f"relief {pattern!r}")

    def emboss(self, text, where, at, right, height=4.0, depth=0.12, font=None, weight=None, spacing=0,
               bevel=0.15, zone=None, picture=None, width=None, mirror=True):
        """Raised (depth > 0) or sunk lettering on inner-car parts, `height` cm tall, centred on
        the parts' surface nearest `at` (cm), laid flat there and read along `right`. picture: a
        PIL image or path instead of text, `width` cm wide (its alpha is raised). mirror: its
        mirror image on the car's other side too. Most inner parts share their texels with their
        mirror twin, which shows it there anyway (backwards, for words): use centre parts for
        words, or marks that read the same both ways."""
        from tool import relief
        if picture is not None:
            im = Image.open(picture) if not isinstance(picture, Image.Image) else picture
            alpha = np.asarray(im.convert("RGBA"), np.float32)[..., 3] / 255
            w_cm = width or 10.0
        else:
            img, w_cm = render_text(text, font or fonts.DEFAULT, height, weight=weight, spacing=spacing)
            alpha = np.asarray(img["fill"], np.float32)[..., 3] / 255
        def make(tris, pos, nrm):
            k = int(np.argmin(np.linalg.norm(pos - np.asarray(at, np.float32), axis=1)))
            f = nrm[k] / np.linalg.norm(nrm[k])
            r = np.asarray(right, np.float64)
            r = r - f * (r @ f)
            h = relief.picture(alpha, pos[k], r, np.cross(f, r), w_cm, depth, bevel)
            return relief.mirrored(h) if mirror else h
        return self._relief(where, make, zone, what=f"emboss {text or 'a picture'!r}")

    # ---- lettering and pictures ----

    def art(self, name):
        """A kept picture of this skin's: skins/<skin>/art/<name>.png (tool/pictures.py)."""
        p = paths.SKINS / self.name / "art" / f"{name}.png"
        if not p.exists():
            raise FileNotFoundError(f"no picture {name!r} for {self.name}: make one with `python -m tool.pictures`")
        return p

    def print(self, name, scale=30, picture=None, wrap="uv"):
        """Make a kept tile usable as a finish: after s.print("bananas", scale=25),
        s.paint("body", "bananas") lays it on with 25 cm per repeat. wrap: "facing" (one
        continuous projection per side of the car, so neighbouring panels line up; it
        changes only at the shoulders), "uv" (the car's unfolding, no stretch, but every panel
        starts the pattern afresh) or "planes" (blended projections)."""
        from tool import textures
        textures.add_file(name, self.art(picture or name), scale, about=f"{self.name}'s print {name}", wrap=wrap)
        return self

    def _found(self, kind, text, c=None, texels=None, check="picture"):
        """Something wrong on the car (tool/checks.py; kind is one of tool/record.py's KINDS): what, and
        the stretch along the car it's on, front to back in cm, from the texels it's about."""
        z = c.pos[texels, 2] if c is not None and texels is not None and len(texels) else None
        self.findings.append({"check": check, "kind": kind, "text": text,
                              "z": None if z is None else [round(float(z.max()), 1), round(float(z.min()), 1)],
                              "step": self.steps[-1]["name"] if self.steps else None})

    def _spot(self, where, at=None):
        if isinstance(where, dict):
            spec = dict(where)
        else:
            spec = dict(SPOTS[where.strip().lower()])
        if at is not None:
            spec["centre"] = at
        return spec

    @_op(lambda image, where, *a, **k: f"a picture at {_where(where) if not isinstance(where, dict) else 'a spot'}")
    def decal(self, image, where, width=None, at=None, finish="gloss", zone=None, min_facing=0.3, rgb=None):
        """Lay a picture (PIL RGBA, or a path) on the body at a spot (SPOTS, or a dict with
        centre, right, up, facing). width in cm. rgb: paint every opaque pixel this colour
        instead of the picture's own (for one-colour lettering)."""
        if isinstance(image, (str, bytes, os.PathLike)) or hasattr(image, "read"):
            image = Image.open(image)
        image = image.convert("RGBA")
        spec = self._spot(where, at)
        width = width or spec["width"]
        arr = np.asarray(image, np.float32) / 255
        c = self.canvas("Skin")
        b = c.bake
        # onto the nearest surface only: the decal crosses every panel in its footprint (a
        # sticker over a panel gap, as on a real car) and never reaches the far side
        alpha, info = paint.project_near(b, arr[..., 3], spec["centre"], spec["right"], spec["up"], width, spec["facing"], min_facing)
        flat = alpha.reshape(-1)
        idx = np.flatnonzero(flat > 0.002)
        if info["landed"] < 0.97:
            self._found("cut", f"decal at {where}: {info['landed']:.0%} of the picture landed on the car; the rest falls in a gap or off an edge", c, idx)
        if info["step_cm"] > 4:
            self._found("fold", f"decal at {where}: the surface under the picture has a fold or step of {info['step_cm']:.0f} cm; "
                        "it will look cut there. Try a smaller picture or another spot", c, idx)
        if not len(idx):
            self.notes.append(f"decal at {where}: nothing landed on the car")
            return self
        m = flat[idx]
        if zone is not None:
            m = m * zone(c.pos[idx], c.nrm[idx])
        if self.measure:
            on = idx[m > 0.5]
            self.pictures.append({"op": self._op, "step": self.ops[self._op]["step"], "what": self.ops[self._op]["what"],
                                  "idx": on, "under": c.owner[on].copy(), "pixels": image.width / width})
        fin = finishes.get(finish) if isinstance(finish, str) else finish
        if rgb is not None:
            col = np.broadcast_to(np.asarray(colours.get(rgb), np.float32), (len(idx), 3))
        else:
            col = np.stack([paint.project_near(b, arr[..., k], spec["centre"], spec["right"], spec["up"], width, spec["facing"], min_facing)[0].reshape(-1)[idx]
                            for k in range(3)], 1)
        c.blend(idx, m, col, np.full(len(idx), fin.roughness, np.float32), np.full(len(idx), fin.metalness, np.float32),
                np.full(len(idx), fin.varnish, np.float32))
        return self

    @_op(lambda image, where="body", *a, **k: f"copies of a picture on {_where(where)}")
    def scatter(self, image, where="body", size=8, spacing=None, turn="random", finish="gloss", zone=None, seed=None,
                min_facing=0.35, step_cm=2.5, min_landed=0.98):
        """Sprinkle copies of a picture (a cut-out, RGBA, or a path; or a list of them, mixed) over parts, each laid flat
        on the surface as its own small sticker and always whole: a copy that would cross a fold
        or run off a panel's edge is left out, so nothing is ever cut (user, 2026-09-24). size:
        the copy's width in cm, or (smallest, largest); spacing: the least distance between
        copies in cm (default: a little more than the largest size, so they never overlap);
        turn: "random", "length" (along the car) or an angle in degrees from the car's length.
        The spread is even: each copy takes the picture least used among its neighbours, a copy that
        doesn't fit is nudged, turned and shrunk before it's given up, and a second pass fills
        any patch still bare with smaller copies."""
        from tool import scatter
        scatter.scatter(self, image, where, size, spacing, turn, finish, zone, seed, min_facing, step_cm, min_landed)
        return self

    @_op(lambda text, where, *a, **k: f"the text {text!r}")
    def text(self, text, where, colour="white", font=None, height=20, at=None, finish="gloss", outline=None,
             outline_width=0.08, weight=None, italic=0.0, spacing=0, zone=None):
        """Write on the body. height in cm; outline: a colour for a border, outline_width as a
        share of the height; italic: a slant (0.2 is a racing lean); spacing: extra letter
        spacing in cm."""
        img, w_cm = render_text(text, font or fonts.DEFAULT, height, outline, outline_width, weight, italic, spacing)
        limit = self._spot(where, at)["width"]
        if w_cm > limit:  # too wide for the spot: shrink it to fit, and say so
            height = height * limit / w_cm
            img, w_cm = render_text(text, font or fonts.DEFAULT, height, outline, outline_width, weight, italic, spacing)
            self.notes.append(f"text {text!r} at {where}: shrunk to {height:.0f} cm tall to fit the spot's {limit} cm")
        col = colours.get(colour)
        if outline:
            self.decal(img["outline"], where, w_cm, at, finish, zone, rgb=outline)
        self.decal(img["fill"], where, w_cm, at, finish, zone, rgb=col)
        return self

    # ---- output ----

    def textures(self):
        if self._final is not None:
            return self._final
        out = {}
        for c in self.canvases.values():
            out |= c.textures()
        return out

    def summary(self, found=True):
        """What was painted and the notes, for Claude: the parts whose paint lands on the same others
        (a small patch serves many inner parts) named together, once. found: the paint's own findings
        too (a picture over a fold), where no check follows to say them."""
        lines = [f"{self.name}: {', '.join(sorted(self.textures()))}"]
        shared, said = {}, []
        for n in dict.fromkeys(self.notes + [f["text"] for f in self.findings if found]):
            name, sep, tail = n.partition(": its paint also lands on ")
            if sep:
                if tail not in shared:
                    said.append(tail)
                shared.setdefault(tail, []).append(name)
            else:
                said.append(n)
        for n in said:
            if n in shared:
                names = shared[n]
                who = names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"
                n = f"{who}: {'its' if len(names) == 1 else 'their'} paint also lands on {n}"
            lines.append(f"  note: {n}")
        return "\n".join(lines)


# ---- lettering ----


def render_text(text, font_name, height_cm, outline=None, outline_width=0.08, weight=None, italic=0.0, spacing=0):
    """Text as two float masks ("fill" and "outline", PIL "L" images), and its width in cm.
    Drawn at 40 px per cm so a 20 cm letter is 800 px tall: sharper than the car's texels."""
    px_per_cm = 40
    size = int(height_cm * px_per_cm)
    f = fonts.font(font_name, size, weight)
    # size the cap height, not the em box: measure "H"
    hb = f.getbbox("H")
    cap = hb[3] - hb[1]
    f = fonts.font(font_name, int(size * size / max(cap, 1)), weight)
    box = f.getbbox(text)
    stroke = int(outline_width * size) if outline else 0
    sp = int(spacing * px_per_cm)
    tw = box[2] - box[0] + sp * max(len(text) - 1, 0)
    th = box[3] - box[1]
    pad = stroke + size // 4 + int(abs(italic) * th)
    W, H = tw + 2 * pad, th + 2 * pad
    fill = Image.new("L", (W, H), 0)
    outl = Image.new("L", (W, H), 0)
    x = pad - box[0]
    for ch in text:
        for im, sw in ((outl, stroke), (fill, 0)):
            if im is outl and not outline:
                continue
            ImageDraw.Draw(im).text((x, pad - box[1]), ch, fill=255, font=f, stroke_width=sw, stroke_fill=255)
        x += f.getlength(ch) + sp
    if italic:
        shear = (1, -italic, 0, 0, 1, 0)
        fill = fill.transform(fill.size, Image.AFFINE, shear, resample=Image.BILINEAR)
        outl = outl.transform(outl.size, Image.AFFINE, shear, resample=Image.BILINEAR)
    to_rgba = lambda im: Image.merge("RGBA", (im, im, im, im))
    return {"fill": to_rgba(fill), "outline": to_rgba(outl)}, W / px_per_cm
