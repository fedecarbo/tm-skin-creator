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

Words: `what` is a phrase the tool sorts into a colour, a finish and (optionally) a region:
"dark red carbon, glossy", "brushed steel", "olive camo" (see tool/colours.py, tool/finishes.py,
tool/shapes.REGIONS). Every painted area is a colour plus a finish; a finish may bring its own
colour (carbon black, chrome silver), which a stated colour overrides. Later calls paint over
earlier ones. Edges between parts and zones are anti-aliased; patterns are drawn in 3D.

`where`: a part or assembly name from car/parts.json, a list of them, or one of the words
"body" (the paint set without the wheel covers), "wheels" (the covers, rims, hubs and wheel
rings: their own design step, never touched by body paint), "wheel covers", "inner" (Details),
"tyres" (Wheels), "glass", "everything". The lights have plain words too (LIGHT_WORDS): "speed
numbers", "brake lights", "rear lights".
Narrow a part with "|left", "|right", "|front", "|rear": "brake caliper|left|front".

The result: Skin.textures() gives the game's textures as float arrays; show() puts them in the
viewer and takes Claude's snapshot sheet; build() writes the DDS files and the zip; install()
puts it in the game. Sets the design never touches aren't shipped, so they keep the stock look.
"""

import json
import os
import re
import time

import numpy as np
from PIL import Image, ImageDraw

from tool import bake, colours, coverage, dds, finishes, fonts, looks, pack, paint, parts, paths, raster, shapes
from tool.testskin import stock

SIZES = {"Skin": (4096, 4096), "Details": (4096, 4096), "Wheels": (1024, 2048), "Glass": (1024, 1024)}
# uploads may fail near 9 MB (a Nadeo developer, 2022); 8.45 and 8.65 MB zips have worked
ZIP_BUDGET = 8.5e6
SET_WORDS = {"skin": "Skin", "inner": "Details", "details": "Details", "inside": "Details",
             "tyres": "Wheels", "tires": "Wheels", "glass": "Glass"}
# "body" is the paint set without the wheel covers: the wheels are their own design step and
# body paint or a scatter must never reach them (user, 2026-09-24). "wheels" is everything on
# a wheel but the tyre: the covers (Skin) and the rims, hubs and wheel rings (Details).
WHEEL_COVER_PARTS = ("wheel cover disc", "wheel cover hub", "wheel cover ring")
WHEEL_PARTS = WHEEL_COVER_PARTS + ("rim", "hub", "brake light", "wheel ring")
GLOW_CODES = np.array([0, 32, 64, 96, 128, 160, 192, 224, 255])
# the lights a skin can recolour, in plain words (the lights test, 2026-09-25), for relight()
LIGHT_WORDS = {"speed numbers": "digit display", "speed digits": "digit display", "speedometer": "digit display",
               "digits": "digit display", "brake lights": "brake light", "rear lights": "rear light",
               "tail lights": "rear light", "gear lights": "rear light"}
# the rear lights' gear bands: the texture v where bands 2 to 5 start, on the bars (u < 0.5; the
# centre piece is u > 0.5). Band 1 is at the tail's corner. The viewer's rear lights use the same.
REAR_BANDS = (0.4747, 0.4903, 0.5030, 0.5157)

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
        # pattern drawn there came out as a speck along the seam: it takes the nearest texel's
        from scipy.ndimage import distance_transform_edt
        near = distance_transform_edt(~self.cov, return_distances=False, return_indices=True)
        self.pos = self.bake["position"][near[0], near[1]].reshape(-1, 3)
        self.nrm = self.bake["normal"][near[0], near[1]].reshape(-1, 3)
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
        self.glow_rgb = self.glow_code = None
        self.glow_touched = False
        if tset == "Details":
            i = stock("Details_I", (w, h), Image.NEAREST)
            self.glow_rgb = np.ascontiguousarray(i[..., :3].reshape(n, 3)).astype(np.float32)
            a = np.rint(i[..., 3].reshape(n) * 255)
            self.glow_code = GLOW_CODES[np.digitize(a, (GLOW_CODES[1:] + GLOW_CODES[:-1]) / 2)].astype(np.uint8)
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

    def textures(self):
        """The game's textures for this set, or {} when the design never touched it."""
        if not self.touched.any() and not self.glow_touched and self.dirt is None:
            return {}
        h, w = self.h, self.w
        cov = self.cov
        out = {}
        if self.set == "Glass":
            rgba = np.concatenate([self.colour, self.alpha[:, None]], 1).reshape(h, w, 4)
            out["Glass_T"] = (raster.fill_holes(rgba, cov), "DXT5", {"srgb": False})
            return out
        if self.touched.any():
            out[f"{self.set}_B"] = (raster.fill_holes(self.colour.reshape(h, w, 3), cov), "DXT1", {"srgb": True})
            rm = np.stack([self.rough, self.metal], 1).reshape(h, w, 2)
            out[f"{self.set}_R"] = (raster.fill_holes(rm, cov), "ATI2", {})
            if self.coat is not None:
                out["Skin_CoatR"] = (raster.fill_holes(self.coat.reshape(h, w), cov), "ATI1", {})
        if self.glow_touched:
            rgba = np.concatenate([self.glow_rgb, self.glow_code[:, None].astype(np.float32) / 255], 1).reshape(h, w, 4)
            out["Details_I"] = (rgba, "DXT5", {"codes_in_alpha": True})
        if self.dirt is not None:
            out[f"{self.set}_DirtMask"] = (np.clip(stock(f"{self.set}_DirtMask") * self.dirt, 0, 1), "ATI1", {})
        return out


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

    # ---- selecting ----

    def canvas(self, tset):
        if tset not in self.canvases:
            w, h = self.sizes[tset]
            self.canvases[tset] = Canvas(tset, w, h)
        return self.canvases[tset]

    def _ids(self, where):
        """(texture set, instance ids) pairs for a `where`."""
        names = [where] if isinstance(where, str) else list(where)
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
            ids = self.parts.select(bits[0], side=side, end=end)
            for i in ids:
                out.setdefault(self.parts.instances[i]["mesh"], set()).add(i)
            self._warn_shared(bits[0], ids)
        return {tset: sorted(ids) for tset, ids in out.items()}

    def _warn_shared(self, name, ids):
        chosen = set(ids)
        for i in ids:
            inst = self.parts.instances[i]
            if inst["shared"] > 0.5:
                twins = [j for j, o in enumerate(self.parts.instances) if o["name"] == inst["name"] and j != i]
                if twins and not chosen.issuperset(twins):
                    self.notes.append(f"{name}: its texels are shared with its twin(s), so the paint lands on all of them")
                    return

    def _mask(self, tset, ids, zone, canvas):
        cov = coverage.load(self.parts, tset, canvas.w, canvas.h).get(ids).reshape(-1)
        idx = np.flatnonzero(cov > 0.002)
        m = cov[idx]
        if zone is not None:
            m = m * zone(canvas.pos[idx], canvas.nrm[idx])
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
        t0 = time.time()
        for tset, ids in targets.items():
            c = self.canvas(tset)
            idx, m = self._mask(tset, ids, zone, c)
            if not len(idx):
                continue
            m = m * blend
            pos, nrm = c.pos[idx], c.nrm[idx]
            if fin.look:
                # flat patterns on the body are drawn in the car's own unfolding (tool/uvmap.py),
                # which has almost no stretch (user, 2026-09-24: projections distorted the dots);
                # the inner car's unfolding is in many small pieces, so it uses the three planes
                extra = {"wrap": "uv" if tset == "Skin" else "planes"}
                if extra["wrap"] == "uv":
                    extra["uv"] = c.uv_cm[idx]
                r = looks.apply(fin, col, pos, nrm, {**extra, **params})
                colour_v = r["colour"]
                rough = r.get("roughness", np.full(len(idx), fin.roughness, np.float32))
                metal = r.get("metalness", np.full(len(idx), fin.metalness, np.float32))
                varnish = r.get("varnish", np.full(len(idx), fin.varnish, np.float32))
                if "weight" in r:
                    m = m * r["weight"]
            else:
                colour_v = np.broadcast_to(col, (len(idx), 3))
                rough = np.full(len(idx), fin.roughness, np.float32)
                metal = np.full(len(idx), fin.metalness, np.float32)
                varnish = np.full(len(idx), fin.varnish, np.float32)
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

    def blend_paint(self, where, what_a, what_b, zone, **params):
        """Two paints blended by a zone's weight: 0 gives the first, 1 the second. For fades:
        s.blend_paint("body", "candy purple", "teal", shapes.fade("z", 200, -150))."""
        self.paint(where, what_a, **params)
        self.paint(where, what_b, zone=zone, **params)
        return self

    def keep(self, tset="Skin"):
        """A copy of a texture set's paint so far: the layer a peel reveals (tool/peel.py)."""
        c = self.canvas(tset)
        return {k: None if getattr(c, k) is None else getattr(c, k).copy() for k in ("colour", "rough", "metal", "coat")}

    def peel(self, under, where="body", **params):
        """Tear the body's paint open, as a wrap ripped off, to show `under` (from keep())
        (tool/peel.py has the parameters)."""
        from tool import peel
        peel.peel(self, under, where, **params)
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

    def glow(self, where, colour=None, kind="always on", zone=None):
        """Make inner-car parts glow: kind is one of finishes.GLOWS ("always on", "night only",
        "brake lights", "front lights", "energy", ...). The body can't glow. colour None: the
        parts glow in whatever colour is already painted on them (so a fade can glow)."""
        col = None if colour is None else np.asarray(colours.get(colour), np.float32)
        targets = self._ids(where)
        for tset, ids in targets.items():
            if tset != "Details":
                self.notes.append(f"glow on {where}: only the inner car (Details) can glow; skipped {tset}")
                continue
            c = self.canvas(tset)
            idx, m = self._mask(tset, ids, zone, c)
            if col is None:
                self._glow(c, idx, m, c.colour[idx], kind)
                continue
            self._glow(c, idx, m, col, kind)
            # the lit colour also goes in the base colour, so it reads the same by day
            c.blend(idx, m, np.broadcast_to(col, (len(idx), 3)), np.full(len(idx), 0.4, np.float32), np.zeros(len(idx), np.float32), np.zeros(len(idx), np.float32))
        return self

    def relight(self, where, colour):
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
        braking, red) takes the last."""
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
            c.glow_rgb[idx] = col * (level / level.max())[:, None]
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

    def tyres(self, what="black rubber", **params):
        return self.paint("tyres", what, **params)

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

    def _spot(self, where, at=None):
        if isinstance(where, dict):
            spec = dict(where)
        else:
            spec = dict(SPOTS[where.strip().lower()])
        if at is not None:
            spec["centre"] = at
        return spec

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
        if info["landed"] < 0.97:
            self.notes.append(f"decal at {where}: {info['landed']:.0%} of the picture landed on the car; the rest falls in a gap or off an edge")
        if info["step_cm"] > 4:
            self.notes.append(f"decal at {where}: the surface under the picture has a fold or step of {info['step_cm']:.0f} cm; "
                              "it will look cut there. Try a smaller picture or another spot")
        flat = alpha.reshape(-1)
        idx = np.flatnonzero(flat > 0.002)
        if not len(idx):
            self.notes.append(f"decal at {where}: nothing landed on the car")
            return self
        m = flat[idx]
        if zone is not None:
            m = m * zone(c.pos[idx], c.nrm[idx])
        fin = finishes.get(finish) if isinstance(finish, str) else finish
        if rgb is not None:
            col = np.broadcast_to(np.asarray(colours.get(rgb), np.float32), (len(idx), 3))
        else:
            col = np.stack([paint.project_near(b, arr[..., k], spec["centre"], spec["right"], spec["up"], width, spec["facing"], min_facing)[0].reshape(-1)[idx]
                            for k in range(3)], 1)
        c.blend(idx, m, col, np.full(len(idx), fin.roughness, np.float32), np.full(len(idx), fin.metalness, np.float32),
                np.full(len(idx), fin.varnish, np.float32))
        return self

    def scatter(self, image, where="body", size=8, spacing=None, turn="random", finish="gloss", zone=None, seed=None,
                min_facing=0.35, step_cm=2.5, min_landed=0.98):
        """Sprinkle copies of a picture (a cut-out, RGBA, or a path; or a list of them, mixed) over parts, each laid flat
        on the surface as its own small sticker and always whole: a copy that would cross a fold
        or run off a panel's edge is left out, so nothing is ever cut (user, 2026-09-24). size:
        the copy's width in cm, or (smallest, largest); spacing: the least distance between
        copies in cm (default: a little more than the largest size, so they never overlap);
        turn: "random", "length" (along the car) or an angle in degrees from the car's length.
        The spread is even (user, 2026-09-24: the first version bunched up and left bare
        patches): each copy takes the picture least used among its neighbours, a copy that
        doesn't fit is nudged, turned and shrunk before it's given up, and a second pass fills
        any patch still bare with smaller copies."""
        from scipy.spatial import cKDTree
        images = list(image) if isinstance(image, (list, tuple)) else [image]
        arrs = []
        for im in images:
            if isinstance(im, (str, bytes, os.PathLike)) or hasattr(im, "read"):
                im = Image.open(im)
            arrs.append(np.asarray(im.convert("RGBA"), np.float32) / 255)
        aspects = [a.shape[0] / a.shape[1] for a in arrs]
        tallest = max(aspects)
        sizes = (float(size), float(size)) if np.isscalar(size) else (float(size[0]), float(size[1]))
        spacing = spacing or sizes[1] * max(1.0, tallest) * 1.15
        rng = np.random.default_rng(self.seed if seed is None else seed)
        fin = finishes.get(finish) if isinstance(finish, str) else finish
        z_axis = np.array([0, 0, 1.0], np.float32)
        placed = skipped = filled = 0
        t0 = time.time()
        for tset, ids in self._ids(where).items():
            c = self.canvas(tset)
            idx, m = self._mask(tset, ids, zone, c)
            if not len(idx):
                continue
            pos, nrm = c.pos[idx], c.nrm[idx]
            # a coarse 3D grid over the parts' texels, so each copy only looks at its neighbourhood
            reach = sizes[1] * max(1.0, tallest) * 0.75
            cell = np.floor(pos / reach).astype(np.int64)
            cmin = cell.min(0)
            cell -= cmin
            dims = cell.max(0) + 1
            ckey = (cell[:, 0] * dims[1] + cell[:, 1]) * dims[2] + cell[:, 2]
            order = np.argsort(ckey, kind="stable")
            skeys = ckey[order]

            def neighbourhood(pt):
                pc = np.floor(pt / reach).astype(np.int64) - cmin
                sub = []
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        for dz in (-1, 0, 1):
                            q = pc + (dx, dy, dz)
                            if (q < 0).any() or (q >= dims).any():
                                continue
                            k = (q[0] * dims[1] + q[1]) * dims[2] + q[2]
                            a, b = np.searchsorted(skeys, k), np.searchsorted(skeys, k, side="right")
                            if b > a:
                                sub.append(order[a:b])
                return np.concatenate(sub) if sub else None

            def frame(n, ang):
                up = z_axis - n * float(n @ z_axis)
                if np.linalg.norm(up) < 0.2:
                    up = np.array([1.0, 0, 0], np.float32) - n * float(n[0])
                up /= np.linalg.norm(up)
                up = np.cos(ang) * up + np.sin(ang) * np.cross(n, up)
                return up, np.cross(up, n)

            def place(pt, kind, size_range):
                """Try to lay one copy near pt: nudged, turned and shrunk before giving up.
                Returns the centre it landed at, or None."""
                nonlocal placed
                sub = neighbourhood(pt)
                if sub is None:
                    return None
                ps, ns = pos[sub], nrm[sub]
                nearest = np.argmin(((ps - pt) ** 2).sum(1))
                n = ns[nearest]
                n = n / max(np.linalg.norm(n), 1e-6)
                if turn == "random":
                    ang0 = rng.uniform(0, 2 * np.pi)
                elif turn == "length":
                    ang0 = 0.0
                else:
                    ang0 = np.radians(float(turn))
                w_cm = rng.uniform(*size_range)
                arr = arrs[kind]
                centre = ps[nearest]
                # attempts: as is; nudged; turned (only when the turn is free); then smaller
                tries = [(0.0, 0.0, 1.0), (0.3, 0.0, 1.0), (0.3, 0.0, 1.0)]
                if turn == "random":
                    tries += [(0.2, np.pi / 2, 1.0), (0.2, np.pi / 4, 1.0), (0.2, -np.pi / 4, 1.0)]
                tries += [(0.3, 0.0, 0.8), (0.3, np.pi / 2 if turn == "random" else 0.0, 0.65), (0.4, 0.0, 0.5)]
                for shift_k, dang, scale in tries:
                    up, right = frame(n, ang0 + dang)
                    if shift_k:
                        shift = rng.normal(0, shift_k * w_cm, 2)
                        cand = centre + shift[0] * right + shift[1] * up
                        cen = ps[np.argmin(((ps - cand) ** 2).sum(1))]
                    else:
                        cen = centre
                    w_try = w_cm * scale
                    alpha, info = paint.project_points(ps, ns, np.ones(len(ps), bool), arr[..., 3], cen, right, up, w_try, n, min_facing)
                    if info["landed"] >= min_landed and info["step_cm"] <= step_cm:
                        hit = np.flatnonzero(alpha > 0.002)
                        if not len(hit):
                            return None
                        col = np.stack([paint.project_points(ps, ns, np.ones(len(ps), bool), arr[..., k], cen, right, up, w_try, n, min_facing)[0][hit]
                                        for k in range(3)], 1)
                        gi = idx[sub[hit]]
                        mm = alpha[hit] * m[sub[hit]]
                        c.blend(gi, mm, col, np.full(len(gi), fin.roughness, np.float32), np.full(len(gi), fin.metalness, np.float32),
                                np.full(len(gi), fin.varnish, np.float32))
                        covered[sub[hit[alpha[hit] > 0.3]]] = True
                        placed += 1
                        return cen
                return None

            def kinds_for(points, done_points, done_kinds):
                """A picture per point: the one least used among the neighbours already decided
                (within 2.2 spacings, the nearer ones counting more), ties broken at random,
                so no picture bunches up."""
                if len(arrs) == 1:
                    return [0] * len(points)
                all_pts = np.asarray(list(done_points) + list(points), np.float32)
                kinds = list(done_kinds) + [-1] * len(points)
                tree = cKDTree(all_pts)
                base = len(done_points)
                for i in range(len(points)):
                    j = base + i
                    counts = np.zeros(len(arrs))
                    for q in tree.query_ball_point(all_pts[j], 2.2 * spacing):
                        if q != j and kinds[q] >= 0:
                            counts[kinds[q]] += 1 / (1 + np.linalg.norm(all_pts[q] - all_pts[j]) / spacing)
                    best = np.flatnonzero(counts == counts.min())
                    kinds[j] = int(rng.choice(best))
                return kinds[base:]

            covered = np.zeros(len(pos), bool)  # texels under a copy, for finding bare patches
            points = looks.surface_points(pos, spacing, seed=int(rng.integers(1 << 30)), regular=False, relax=8)
            kinds = kinds_for(points, [], [])
            centres, centre_kinds = [], []
            for pt, kind in zip(points, kinds):
                cen = place(pt, kind, sizes)
                if cen is None:
                    skipped += 1
                else:
                    centres.append(cen)
                    centre_kinds.append(kind)
            # second pass: texels far from the outline of every copy are a bare patch; sprinkle
            # it again with smaller copies (it's bare because the full size didn't fit there)
            for _ in range(2):
                on = np.flatnonzero(covered)
                if not len(on):
                    break
                sample = pos[rng.choice(len(pos), min(len(pos), 60_000), replace=False)]
                d, _ = cKDTree(pos[rng.choice(on, min(len(on), 120_000), replace=False)]).query(sample, workers=-1)
                bare = sample[d > 0.55 * spacing]  # a gap wider than one spacing
                if len(bare) < 50:
                    break
                more = looks.surface_points(bare, 0.8 * spacing, seed=int(rng.integers(1 << 30)), regular=False, relax=4)
                more_kinds = kinds_for(more, centres, centre_kinds)
                small = (sizes[0] * 0.7, sizes[1] * 0.85)
                for pt, kind in zip(more, more_kinds):
                    cen = place(pt, kind, small)
                    if cen is not None:
                        centres.append(cen)
                        centre_kinds.append(kind)
                        filled += 1
        self.notes.append(f"scatter on {where}: {placed} copies placed ({filled} of them smaller ones filling bare patches), "
                          f"{skipped} spots left bare for crossing a fold or an edge ({time.time() - t0:.0f} s)")
        return self

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
        out = {}
        for c in self.canvases.values():
            out |= c.textures()
        return out

    def summary(self):
        lines = [f"{self.name}: {', '.join(sorted(self.textures()))}"]
        lines += [f"  note: {n}" for n in dict.fromkeys(self.notes)]
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


# ---- building ----


def export_to_viewer(skin):
    from tool import view
    textures = {name: arr for name, (arr, fourcc, opts) in skin.textures().items()}
    view.export_mesh()
    view.ensure_hdri()
    view.ensure_stock()
    view.export_skin(skin.name, textures)


def save_painted(skin):
    """Keep the painted textures (uint8) so installing needn't paint again."""
    out = paths.BUILD / skin.name
    out.mkdir(parents=True, exist_ok=True)
    arrays, meta = {}, {}
    for name, (arr, fourcc, opts) in skin.textures().items():
        arrays[name] = np.clip(np.rint(np.asarray(arr) * 255), 0, 255).astype(np.uint8)
        meta[name] = {"fourcc": fourcc, **opts}
    np.savez(out / "painted.npz", **arrays)
    (out / "painted.json").write_text(json.dumps({"textures": meta, "icon": skin.icon_colours, "notes": skin.notes}, indent=1))
    return out


def build_zip(name, icon_image=None):
    """DDS files and the zip from build/<name>/painted.npz. A zip over ZIP_BUDGET gets its
    roughness maps at half size (the stock's own 2048²), largest first, until it fits: where a
    design kept the stock look they hold nothing finer, and a finish on a whole part keeps its
    edges (the island's)."""
    out = paths.BUILD / name
    meta = json.loads((out / "painted.json").read_text())
    data = np.load(out / "painted.npz")
    for old in out.glob("*.dds"):
        old.unlink()
    specs = {}
    for tex_name, spec in meta["textures"].items():
        spec = dict(spec)
        specs[tex_name] = (spec.pop("fourcc"), spec)
        dds.write(out / f"{tex_name}.dds", data[tex_name].astype(np.float32) / 255, specs[tex_name][0], **spec)
    if icon_image is None:
        cols = meta.get("icon") or [(0.5, 0.5, 0.5)]
        icon_image = pack.icon(name[:8], cols[0], cols[-1])
    zip_path = pack.pack(name, out, icon_image)
    rough = [t for t in specs if t.endswith("_R")]
    while zip_path.stat().st_size > ZIP_BUDGET and rough:
        sizes = pack.sizes(zip_path)
        t = max(rough, key=lambda t: sizes.get(f"{t}.dds", 0))
        rough.remove(t)
        fourcc, spec = specs[t]
        half = dds.halve(data[t].astype(np.float32) / 255)
        dds.write(out / f"{t}.dds", half, fourcc, **spec)
        zip_path = pack.pack(name, out, icon_image)
        print(f"{t} at {half.shape[1]}x{half.shape[0]}, to keep the zip under {ZIP_BUDGET / 1e6} MB")
    if zip_path.stat().st_size > ZIP_BUDGET:
        print(f"warning: the zip is still over {ZIP_BUDGET / 1e6} MB; the upload may fail")
    return zip_path
