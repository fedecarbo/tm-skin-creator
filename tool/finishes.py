"""The library of finishes: what a surface is made of, in the user's words.

A finish is a look (a pattern drawn in 3D on the car, from tool/looks.py, or none for plain
paint), a default shine (roughness, metalness, varnish), and sometimes its own colour: carbon
is black, chrome is silver, gold is gold. A stated colour overrides the finish's own ("red
carbon" tints the weave). A stated shine overrides the default ("scratched matte olive").

    finishes.get("brushed steel")      -> Finish
    finishes.resolve("dark red carbon, glossy")
        -> (colour (r, g, b) or None, Finish with the look "carbon" and gloss shine, leftover words)

What the lab skins showed in the game (2026-09-24, CHECKLIST.md "Things we learned"):
  - roughness (0 mirror .. 1 matte) and metalness (0 paint .. 1 metal) work as in any PBR
    renderer, on the body, the details and the tyres alike;
  - `Skin_CoatR` is the varnish: 0 lays a glossy clear varnish over anything, 255 none. A skin
    without the file is varnished all over, so matte paint needs varnish 0 here (CoatR 255), and
    the tool always ships `Skin_CoatR`. Only the body has a varnish file.
Limits to say out loud when asked: no holographic or colour-shift paint (the game's shading
can't), and the body takes no relief, so body patterns and scratches are paint only.
"""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Finish:
    name: str
    roughness: float  # 0 mirror .. 1 matte
    metalness: float  # 0 paint .. 1 metal
    varnish: float  # 0 none .. 1 a glossy clear varnish on top (body only; the game's CoatR is 1 - this)
    colour: tuple | None = None  # the finish's own colour (sRGB 0..1), if it has one
    look: str | None = None  # a pattern in tool/looks.py
    glow: str | None = None  # a glow kind (GLOWS) the finish lights up with, on the inner car
    about: str = ""


def _f(name, r, m, v, colour=None, look=None, glow=None, about=""):
    return Finish(name, r, m, v, colour, look, glow, about)


# ---- Shines: plain paint, in steps from matte to mirror. Also the "override" words. ----
SHINES = {
    "gloss": _f("gloss", 0.3, 0.0, 1.0, about="shiny paint under a clear varnish: the game's default look"),
    "satin": _f("satin", 0.5, 0.0, 0.0, about="a soft sheen, no varnish"),
    "matte": _f("matte", 0.9, 0.0, 0.0, about="flat, no shine at all"),
    "semi-gloss": _f("semi-gloss", 0.4, 0.0, 0.5, about="between satin and gloss"),
    "mirror": _f("mirror", 0.03, 1.0, 0.0, about="a perfect mirror"),
}

# ---- The library. Values are the lab's, judged by eye from the game. ----
GREY = (0.5, 0.5, 0.52)
LIBRARY = {
    # paint
    "gloss": SHINES["gloss"],
    "satin": SHINES["satin"],
    "matte": SHINES["matte"],
    "metallic": _f("metallic", 0.35, 0.45, 1.0, look="flake", about="metallic paint: fine flakes under a varnish"),
    "pearl": _f("pearl", 0.3, 0.3, 1.0, look="pearl", about="a soft pearly sheen under a varnish (no colour shift: the game can't)"),
    "candy": _f("candy", 0.15, 0.3, 1.0, look="candy", about="deep, wet-looking colour under a thick varnish"),
    # metal
    "chrome": _f("chrome", 0.05, 1.0, 0.0, (0.9, 0.9, 0.92), about="a mirror"),
    "polished aluminium": _f("polished aluminium", 0.22, 1.0, 0.0, (0.85, 0.86, 0.88), about="bright metal, reflections a little soft"),
    "brushed steel": _f("brushed steel", 0.45, 1.0, 0.0, (0.62, 0.64, 0.66), look="texture", about="dull steel with fine brush lines (photo)"),
    "brushed titanium": _f("brushed titanium", 0.5, 1.0, 0.0, (0.5, 0.5, 0.53), look="texture", about="darker, warmer brushed metal (photo)"),
    "gunmetal": _f("gunmetal", 0.4, 1.0, 0.0, (0.28, 0.3, 0.34), about="dark grey metal"),
    "gold": _f("gold", 0.28, 1.0, 0.0, (1.0, 0.72, 0.25), about="polished gold"),
    "copper": _f("copper", 0.32, 1.0, 0.0, (0.95, 0.55, 0.35), about="polished copper"),
    "anodised": _f("anodised", 0.35, 1.0, 0.0, about="a colour on metal: give it a colour"),
    "raw cast": _f("raw cast", 0.75, 1.0, 0.0, (0.5, 0.5, 0.5), look="texture", about="rough, grainy cast iron (photo)"),
    # composites and plastics
    "carbon": _f("carbon", 0.85, 0.0, 0.0, (0.14, 0.14, 0.16), look="carbon", about="a fine twill weave, matte by default"),
    "forged carbon": _f("forged carbon", 0.5, 0.0, 0.5, (0.12, 0.12, 0.14), look="forged", about="chopped carbon, a marbled look"),
    "kevlar": _f("kevlar", 0.6, 0.0, 0.3, (0.75, 0.6, 0.2), look="weave", about="a yellow aramid weave"),
    "gloss plastic": _f("gloss plastic", 0.25, 0.0, 0.0, about="shiny plastic, no varnish"),
    "matte plastic": _f("matte plastic", 0.85, 0.0, 0.0, about="dull plastic"),
    "rubber": _f("rubber", 0.92, 0.0, 0.0, (0.08, 0.08, 0.08), about="matte and dark, like a tyre"),
    "vinyl": _f("vinyl", 0.45, 0.0, 0.0, about="a satin wrap, no varnish"),
    "quilted leather": _f("quilted leather", 0.6, 0.0, 0.0, (0.12, 0.09, 0.08), look="texture", about="diamond-stitched leather (photo)"),
    # inside
    "leather": _f("leather", 0.65, 0.0, 0.0, (0.12, 0.09, 0.08), look="texture", about="smooth leather (photo)"),
    "cloth": _f("cloth", 0.95, 0.0, 0.0, (0.2, 0.2, 0.22), look="cloth", about="a fine fabric weave, flat"),
    "webbing": _f("webbing", 0.8, 0.0, 0.0, (0.15, 0.15, 0.17), look="webbing", about="ribbed belt strap"),
    # wear: a look laid over the colour; the shine is what's left under the wear
    "scratched": _f("scratched", 0.55, 0.0, 0.0, look="scratched", about="fine scratches showing lighter"),
    "chipped": _f("chipped", 0.45, 0.0, 0.3, look="texture", about="paint flaked off in spots, bare metal showing (photo)"),
    "dusty": _f("dusty", 0.75, 0.0, 0.0, look="dusty", about="a film of dust, patchy"),
    "faded": _f("faded", 0.7, 0.0, 0.0, look="faded", about="sun-bleached, uneven"),
    "rusted": _f("rusted", 0.6, 0.0, 0.0, look="texture", about="rust blooming through the paint (photo)"),
    "greasy": _f("greasy", 0.6, 0.0, 0.0, look="greasy", about="dark oily smears"),
    "race-worn": _f("race-worn", 0.45, 0.0, 0.6, look="worn", about="dust, chips and scratches, lightly"),
    # light
    "neon": _f("neon", 0.4, 0.0, 0.0, glow="always on", about="a self-lit colour (inner car only; the body can't glow)"),
    "reflective tape": _f("reflective tape", 0.25, 0.6, 0.0, (0.88, 0.88, 0.84), look="flake", about="bright silvery tape"),
    # patterns that arrange colours (a palette); a stated colour is the first colour
    "camo": _f("camo", 0.85, 0.0, 0.0, look="camo", about="blotchy camouflage in 3 or 4 colours"),
    "hexagons": _f("hexagons", 0.3, 0.0, 1.0, look="hex", about="a honeycomb of lines"),
    "checks": _f("checks", 0.3, 0.0, 1.0, look="checks", about="a chequerboard"),
    "splatter": _f("splatter", 0.3, 0.0, 1.0, look="splatter", about="paint drops and splashes"),
    "polka dots": _f("polka dots", 0.3, 0.0, 1.0, look="dots", about="a staggered grid of round dots"),
    "pinstripes": _f("pinstripes", 0.3, 0.0, 1.0, look="lines", about="many thin parallel lines"),
}
ALIASES = {
    "glossy": "gloss", "shiny": "gloss", "shine": "gloss", "flat": "matte", "mat": "matte", "silk": "satin",
    "eggshell": "satin", "semi gloss": "semi-gloss", "semigloss": "semi-gloss",
    "metal": "polished aluminium", "polished metal": "polished aluminium", "aluminium": "polished aluminium",
    "aluminum": "polished aluminium", "polished aluminum": "polished aluminium", "brushed": "brushed steel",
    "brushed metal": "brushed steel", "brushed aluminium": "brushed steel", "steel": "brushed steel",
    "titanium": "brushed titanium", "cast": "raw cast", "cast metal": "raw cast", "anodized": "anodised",
    "carbon fibre": "carbon", "carbon fiber": "carbon", "carbon weave": "carbon", "carbonfibre": "carbon",
    "forged": "forged carbon", "aramid": "kevlar", "plastic": "gloss plastic", "vinyl wrap": "vinyl", "wrap": "vinyl",
    "hide": "leather", "fabric": "cloth", "alcantara": "cloth", "belt": "webbing", "belt webbing": "webbing", "strap": "webbing",
    "scratches": "scratched", "scratchy": "scratched", "chips": "chipped", "stone chipped": "chipped", "dust": "dusty",
    "bleached": "faded", "sun faded": "faded", "rust": "rusted", "rusty": "rusted", "grease": "greasy", "oily": "greasy",
    "worn": "race-worn", "raceworn": "race-worn", "race worn": "race-worn", "battle worn": "race-worn", "weathered": "race-worn", "grungy": "race-worn",
    "grunge": "race-worn", "glow": "neon", "glowing": "neon", "lit": "neon", "tape": "reflective tape",
    "camouflage": "camo", "hex": "hexagons", "honeycomb": "hexagons", "hexagon": "hexagons", "chequered": "checks",
    "checkered": "checks", "checkerboard": "checks", "chequerboard": "checks", "check": "checks", "splat": "splatter",
    "splashes": "splatter", "dots": "polka dots", "polka": "polka dots", "spots": "polka dots", "dotted": "polka dots", "paint splatter": "splatter", "pinstripe": "pinstripes", "lines": "pinstripes",
    "flake": "metallic", "metal flake": "metallic", "flakes": "metallic", "pearlescent": "pearl", "candy apple": "candy",
}


def _texture_finish(key):
    """A finish for a photographed surface added by name (tool/textures.py)."""
    from tool import textures
    spec = textures.SETS.get(key)
    if spec is None:
        return None
    return _f(key, 0.45 if spec.get("metal") else 0.6, 1.0 if spec.get("metal") else 0.0, 0.0,
              (0.6, 0.6, 0.62) if spec.get("metal") else None, look="texture", about=spec.get("about", ""))


def get(name):
    key = " ".join(name.strip().lower().split())
    key = ALIASES.get(key, key)
    if key not in LIBRARY:
        t = _texture_finish(key)
        if t:
            return t
        raise KeyError(f"no finish called {name!r}; see finishes.LIBRARY")
    return LIBRARY[key]


def names():
    return list(LIBRARY)


def rm(finish):
    """(roughness, metalness) for a `_R` texture."""
    return finish.roughness, finish.metalness


def coat(finish):
    """The `Skin_CoatR` value: 0 is a glossy varnish, 1 none."""
    return 1.0 - finish.varnish


def with_shine(finish, shine):
    """The finish's look with another finish's shine: "scratched matte", "brushed gloss"."""
    return replace(finish, roughness=shine.roughness, metalness=shine.metalness if finish.metalness == 0 else finish.metalness,
                   varnish=shine.varnish, name=f"{shine.name} {finish.name}")


def resolve(phrase, default="gloss"):
    """Sort a phrase into (colour, finish, leftover words). "dark red carbon, glossy" ->
    a dark red, the carbon finish with a gloss shine, []. Words that are neither a colour, a
    modifier, a finish nor a shine come back in the list, for the caller."""
    from tool import colours
    parsed = colours.parse(phrase)
    words = parsed.words
    finish = None
    shine = None
    i = 0
    leftover = []
    while i < len(words):
        hit = None
        for n in (3, 2, 1):
            cand = " ".join(words[i:i + n])
            key = ALIASES.get(cand, cand)
            if key in LIBRARY or _texture_finish(key):
                if key not in LIBRARY:
                    LIBRARY[key] = _texture_finish(key)
                hit = (n, key)
                break
        if hit is None:
            leftover.append(words[i])
            i += 1
            continue
        n, key = hit
        i += n
        if key in SHINES or key in ("mirror",):
            if finish is None or finish.look is None:
                finish = finish if finish and finish.look else None
                shine = LIBRARY[key] if key in LIBRARY else SHINES[key]
            else:
                shine = SHINES[key]
        elif finish is None:
            finish = LIBRARY[key]
        else:  # two looks: keep the first as the look, treat the second as a shine hint
            shine = LIBRARY[key]
    colour = parsed.colour
    # a metal named as a colour ("gold", "chrome", "copper") is the metal, unless a finish was said
    metal_key = ALIASES.get(parsed.colour_name, parsed.colour_name)
    if finish is None and metal_key in LIBRARY:
        finish = LIBRARY[metal_key]
        if finish.colour:
            colour = finish.colour
            for m in parsed.modifiers:
                colour = colours.adjust(colour, *colours.MODIFIERS[m])
    if finish is None:
        finish = shine or get(default)
    elif shine is not None:
        finish = with_shine(finish, shine)
    return colour, finish, leftover


# The Details_I alpha codes (CLAUDE.md), as the lab put them on named parts, and what the game
# did with them in the user's screenshots (2026-09-24). `keeps colour`: the texel's RGB shows
# as painted; otherwise the game tints it and the RGB should be grey.
GLOWS = {
    "brake lights": {"code": 0, "keeps colour": True,
                     "seen": "the stock strips behind the front wheels (checkpoint 1): dim all the time, "
                             "flaring to near white when braking; the lab's part was hidden from the camera"},
    "energy": {"code": 32, "keeps colour": False,
               "seen": "dim, tinted red by the game (the player's colour), on at rest"},
    "brake heat": {"code": 64, "keeps colour": True, "seen": "not seen to light up (braking from 133 km/h)"},
    "always on": {"code": 96, "keeps colour": True, "seen": "magenta as painted, day and night"},
    "front lights": {"code": 128, "keeps colour": True, "seen": "bright white by day and at night"},
    "turbo": {"code": 160, "keeps colour": False, "seen": "not seen (the hubs are hidden by the wheel covers)"},
    "exhaust heat": {"code": 192, "keeps colour": True, "seen": "not seen to light up on turbo pads"},
    "boost": {"code": 224, "keeps colour": False, "seen": "not seen"},
    "night only": {"code": 255, "keeps colour": True, "seen": "yellow as painted at night, and on a dusk map"},
}
GLOW_ALIASES = {"always": "always on", "on": "always on", "neon": "always on", "night": "night only", "at night": "night only",
                "headlights": "front lights", "lights": "front lights", "brake": "brake lights", "brakes": "brake lights",
                "team colour": "energy", "team color": "energy", "player colour": "energy"}


def glow(kind):
    key = kind.strip().lower()
    return GLOWS[GLOW_ALIASES.get(key, key)]
