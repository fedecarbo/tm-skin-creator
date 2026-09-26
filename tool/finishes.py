"""The library of finishes: what a surface is made of, in the user's words.

A finish is a look (a pattern drawn in 3D on the car, from tool/looks.py, or none for plain
paint), a default shine (roughness, metalness, varnish), and sometimes its own colour: carbon
is black, chrome is silver, gold is gold. A stated colour overrides the finish's own ("red
carbon" tints the weave). A stated shine overrides the default ("scratched matte olive").

    finishes.get("brushed steel")      -> Finish
    finishes.get("ME-07")              -> Finish "gold": a Lab code
    finishes.resolve("dark red carbon, glossy")
        -> (colour (r, g, b) or None, Finish with the look "carbon" and gloss shine, leftover words)

The Lab (viewer/lab.html, tool/swatches.py) shows every finish here on a ball, grouped by
`CATALOGUE`, with its code and numbers, so the user sees what the tool can do. They copy a line
like "ME-07 Gold (matte 28%, metal 100%, varnish 0%)" and paste it in the chat: the code is the
finish, exactly (`get(code)`, or the code inside a phrase: "ME-07 matte").

What the lab skins showed in the game (2026-09-24, CHECKLIST.md "Things we learned"):
  - roughness (0 mirror .. 1 matte) and metalness (0 paint .. 1 metal) work as in any PBR
    renderer, on the body, the details and the tyres alike;
  - `Skin_CoatR` is the varnish: 0 lays a glossy clear varnish over anything, 255 none. A skin
    without the file is varnished all over, so matte paint needs varnish 0 here (CoatR 255), and
    the tool always ships `Skin_CoatR`. Only the body has a varnish file.
Limits to say out loud when asked: no holographic or colour-shift paint (the game's shading
can't), and the body takes no relief, so body patterns and scratches are paint only.
"""

import re
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
    source: str = "lab"  # where its numbers come from: "lab" (set against the game), "measured", "eye"
    code: str = ""  # the Lab's code, e.g. "ME-07" (set from CATALOGUE)
    family: str = ""  # the Lab's family, e.g. "Metal"


def _f(name, r, m, v, colour=None, look=None, glow=None, about="", source="lab"):
    return Finish(name, r, m, v, colour, look, glow, about, source)


# ---- Shines: plain paint, in steps from matte to mirror. Also the "override" words. ----
SHINES = {
    "gloss": _f("gloss", 0.3, 0.0, 1.0, about="shiny paint under a clear varnish: the game's default look"),
    "satin": _f("satin", 0.5, 0.0, 0.0, about="a soft sheen, no varnish"),
    "matte": _f("matte", 0.9, 0.0, 0.0, about="flat, no shine at all"),
    "semi-gloss": _f("semi-gloss", 0.4, 0.0, 0.5, about="between satin and gloss"),
    "mirror": _f("mirror", 0.03, 1.0, 0.0, about="a perfect mirror"),
}

# ---- The library. Values are the lab's, judged by eye from the game, except where `source`
# says otherwise: "measured" (a real metal's measured colour from Physically Based,
# physicallybased.info, CC0, then set by eye beside the rest) or "eye" (set by eye in the viewer,
# not yet seen in the game). ----
GREY = (0.5, 0.5, 0.52)
LIBRARY = {
    # paint
    "gloss": SHINES["gloss"],
    "satin": SHINES["satin"],
    "matte": SHINES["matte"],
    "semi-gloss": SHINES["semi-gloss"],
    "chalk": _f("chalk", 1.0, 0.0, 0.0, about="bone-dry and chalky, flatter than matte", source="eye"),
    "wet look": _f("wet look", 0.08, 0.0, 1.0, about="a deep, polished gloss under a thick varnish", source="eye"),
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
    "stainless steel": _f("stainless steel", 0.3, 1.0, 0.0, (0.78, 0.77, 0.75), about="bright, slightly warm steel, smooth", source="measured"),
    "brass": _f("brass", 0.3, 1.0, 0.0, (0.88, 0.72, 0.38), about="polished brass: paler and greener than gold", source="measured"),
    "rose gold": _f("rose gold", 0.3, 1.0, 0.0, (0.93, 0.62, 0.52), about="gold with a pink blush", source="eye"),
    "black chrome": _f("black chrome", 0.08, 1.0, 0.0, (0.2, 0.2, 0.22), about="a dark, smoky mirror", source="eye"),
    "bead-blasted titanium": _f("bead-blasted titanium", 0.7, 1.0, 0.0, (0.55, 0.54, 0.55), look="grain",
                                about="titanium with a fine blasted grain: soft, no sharp reflections", source="eye"),
    # composites and plastics
    "carbon": _f("carbon", 0.85, 0.0, 0.0, (0.14, 0.14, 0.16), look="carbon", about="a fine twill weave, matte by default"),
    "forged carbon": _f("forged carbon", 0.5, 0.0, 0.5, (0.12, 0.12, 0.14), look="forged", about="chopped carbon, a marbled look"),
    "kevlar": _f("kevlar", 0.6, 0.0, 0.3, (0.75, 0.6, 0.2), look="weave", about="a yellow aramid weave"),
    "gloss carbon": _f("gloss carbon", 0.25, 0.0, 1.0, (0.14, 0.14, 0.16), look="carbon",
                       about="the twill weave under a glossy varnish, as on a race car", source="eye"),
    "plain-weave carbon": _f("plain-weave carbon", 0.8, 0.0, 0.0, (0.14, 0.14, 0.16), look="plain",
                             about="a square over-and-under weave, matte", source="eye"),
    "fibreglass": _f("fibreglass", 0.35, 0.0, 0.5, (0.86, 0.86, 0.8), look="plain", about="pale glass-fibre cloth under resin", source="eye"),
    "gloss plastic": _f("gloss plastic", 0.25, 0.0, 0.0, about="shiny plastic, no varnish"),
    "matte plastic": _f("matte plastic", 0.85, 0.0, 0.0, about="dull plastic"),
    "satin plastic": _f("satin plastic", 0.5, 0.0, 0.0, about="plastic with a soft sheen", source="eye"),
    "soft-touch": _f("soft-touch", 0.8, 0.0, 0.0, about="velvety rubberised plastic, like a phone case", source="eye"),
    "textured plastic": _f("textured plastic", 0.7, 0.0, 0.0, look="grain", about="moulded plastic with a fine grain, like a dashboard", source="eye"),
    "acrylic": _f("acrylic", 0.05, 0.0, 0.0, about="glassy high-gloss plastic, no varnish needed", source="eye"),
    "sparkle plastic": _f("sparkle plastic", 0.35, 0.2, 0.0, look="flake", about="moulded plastic with metal flecks in it", source="eye"),
    "rubber": _f("rubber", 0.92, 0.0, 0.0, (0.08, 0.08, 0.08), about="matte and dark, like a tyre"),
    "soft rubber": _f("soft rubber", 0.8, 0.0, 0.0, (0.16, 0.16, 0.17), about="a softer, lighter rubber, like a grip", source="eye"),
    "silicone": _f("silicone", 0.45, 0.0, 0.0, about="smooth silicone with a gentle sheen: give it a colour", source="eye"),
    "knurled grip": _f("knurled grip", 0.85, 0.0, 0.0, (0.1, 0.1, 0.11), look="knurl",
                       about="rubber with a diamond grip pattern (painted: nothing on the body is raised)", source="eye"),
    "worn rubber": _f("worn rubber", 0.95, 0.0, 0.0, (0.12, 0.12, 0.12), look="dusty", about="dry, greyed old rubber", source="eye"),
    "vinyl": _f("vinyl", 0.45, 0.0, 0.0, about="a satin wrap, no varnish"),
    "gloss wrap": _f("gloss wrap", 0.15, 0.0, 0.0, about="a glossy vinyl wrap: shiny, no varnish", source="eye"),
    "matte wrap": _f("matte wrap", 0.8, 0.0, 0.0, about="a flat vinyl wrap", source="eye"),
    "chrome wrap": _f("chrome wrap", 0.1, 1.0, 0.0, (0.85, 0.86, 0.88), about="mirror vinyl: a little softer than real chrome", source="eye"),
    "brushed wrap": _f("brushed wrap", 0.4, 0.8, 0.0, (0.7, 0.71, 0.72), look="brushed", about="brushed-metal vinyl", source="eye"),
    "quilted leather": _f("quilted leather", 0.6, 0.0, 0.0, (0.12, 0.09, 0.08), look="texture", about="diamond-stitched leather (photo)"),
    # inside
    "leather": _f("leather", 0.65, 0.0, 0.0, (0.12, 0.09, 0.08), look="texture", about="smooth leather (photo)"),
    "cloth": _f("cloth", 0.95, 0.0, 0.0, (0.2, 0.2, 0.22), look="cloth", about="a fine fabric weave, flat"),
    "webbing": _f("webbing", 0.8, 0.0, 0.0, (0.15, 0.15, 0.17), look="webbing", about="ribbed belt strap"),
    "perforated leather": _f("perforated leather", 0.65, 0.0, 0.0, (0.12, 0.09, 0.08), look="perforated",
                             about="leather with rows of small holes, like a race seat", source="eye"),
    "suede": _f("suede", 1.0, 0.0, 0.0, (0.2, 0.2, 0.22), look="suede", about="soft napped suede or alcantara, no shine at all", source="eye"),
    "denim": _f("denim", 0.9, 0.0, 0.0, (0.2, 0.3, 0.45), look="denim", about="blue twill cotton", source="eye"),
    # wear: a look laid over the colour; the shine is what's left under the wear
    "scratched": _f("scratched", 0.55, 0.0, 0.0, look="scratched", about="fine scratches showing lighter"),
    "chipped": _f("chipped", 0.45, 0.0, 0.3, look="texture", about="paint flaked off in spots, bare metal showing (photo)"),
    "dusty": _f("dusty", 0.75, 0.0, 0.0, look="dusty", about="a film of dust, patchy"),
    "faded": _f("faded", 0.7, 0.0, 0.0, look="faded", about="sun-bleached, uneven"),
    "rusted": _f("rusted", 0.6, 0.0, 0.0, look="texture", about="rust blooming through the paint (photo)"),
    "greasy": _f("greasy", 0.6, 0.0, 0.0, look="greasy", about="dark oily smears"),
    "race-worn": _f("race-worn", 0.45, 0.0, 0.6, look="worn", about="dust, chips and scratches, lightly"),
    "muddy": _f("muddy", 0.6, 0.0, 0.0, look="muddy", about="dried mud splashed on, heavier low down", source="eye"),
    # light
    "neon": _f("neon", 0.4, 0.0, 0.0, glow="always on", about="a self-lit colour (inner car only; the body can't glow)"),
    "night glow": _f("night glow", 0.4, 0.0, 0.0, glow="night only", about="lit only at night (inner car only)"),
    "reflective tape": _f("reflective tape", 0.3, 0.75, 0.0, (0.9, 0.9, 0.88), about="bright silvery tape, no sparkle (user, 2026-09-24)"),
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
    "hide": "leather", "fabric": "cloth", "alcantara": "suede", "belt": "webbing", "belt webbing": "webbing", "strap": "webbing",
    "scratches": "scratched", "scratchy": "scratched", "chips": "chipped", "stone chipped": "chipped", "dust": "dusty",
    "bleached": "faded", "sun faded": "faded", "rust": "rusted", "rusty": "rusted", "grease": "greasy", "oily": "greasy",
    "worn": "race-worn", "raceworn": "race-worn", "race worn": "race-worn", "battle worn": "race-worn", "weathered": "race-worn", "grungy": "race-worn",
    "grunge": "race-worn", "glow": "neon", "glowing": "neon", "lit": "neon", "tape": "reflective tape",
    "camouflage": "camo", "hex": "hexagons", "honeycomb": "hexagons", "hexagon": "hexagons", "chequered": "checks",
    "checkered": "checks", "checkerboard": "checks", "chequerboard": "checks", "check": "checks", "splat": "splatter",
    "splashes": "splatter", "dots": "polka dots", "polka": "polka dots", "spots": "polka dots", "dotted": "polka dots", "paint splatter": "splatter", "pinstripe": "pinstripes", "lines": "pinstripes",
    "flake": "metallic", "metal flake": "metallic", "flakes": "metallic", "pearlescent": "pearl", "candy apple": "candy",
    # added with the Lab (2026-09-26)
    "chalky": "chalk", "dead flat": "chalk", "wet": "wet look", "high gloss": "wet look", "mirror gloss": "wet look",
    "stainless": "stainless steel", "inox": "stainless steel", "pink gold": "rose gold", "smoked chrome": "black chrome",
    "dark chrome": "black chrome", "bead blasted titanium": "bead-blasted titanium", "blasted titanium": "bead-blasted titanium",
    "sandblasted titanium": "bead-blasted titanium", "bead blasted": "bead-blasted titanium", "sandblasted": "bead-blasted titanium",
    "tyre rubber": "rubber", "tire rubber": "rubber", "grip rubber": "soft rubber", "silicon": "silicone",
    "knurled": "knurled grip", "knurling": "knurled grip", "grip": "knurled grip", "old rubber": "worn rubber", "dry rubber": "worn rubber",
    "soft touch": "soft-touch", "rubberised": "soft-touch", "rubberized": "soft-touch", "textured": "textured plastic",
    "grained plastic": "textured plastic", "glitter plastic": "sparkle plastic",
    "plain weave": "plain-weave carbon", "plain weave carbon": "plain-weave carbon", "square weave": "plain-weave carbon",
    "fiberglass": "fibreglass", "glass fibre": "fibreglass", "glass fiber": "fibreglass",
    "perforated": "perforated leather", "nubuck": "suede", "microsuede": "suede", "jeans": "denim",
    "satin wrap": "vinyl", "shiny wrap": "gloss wrap", "mirror wrap": "chrome wrap", "brushed vinyl": "brushed wrap",
    "mud": "muddy", "mud splashed": "muddy", "glow at night": "night glow", "night light": "night glow",
}

# ---- The Lab's catalogue: each family's two letters, its name, and its finishes in order. A
# finish's code is its family's letters and its place: ME-07 is gold. The user points at a finish
# by its code (they copy a line from the Lab and paste it), so never reorder or remove: a new
# finish goes at the end of its family, a retired one leaves None in its place. ----
CATALOGUE = {
    "PA": ("Paint", ["gloss", "semi-gloss", "satin", "matte", "chalk", "wet look", "metallic", "pearl", "candy"]),
    "ME": ("Metal", ["chrome", "polished aluminium", "brushed steel", "brushed titanium", "stainless steel", "gunmetal",
                     "gold", "brass", "copper", "rose gold", "anodised", "black chrome", "bead-blasted titanium", "raw cast"]),
    "PL": ("Plastic", ["gloss plastic", "satin plastic", "matte plastic", "soft-touch", "textured plastic", "acrylic",
                       "sparkle plastic"]),
    "RU": ("Rubber", ["rubber", "soft rubber", "silicone", "knurled grip", "worn rubber"]),
    "CF": ("Carbon & fibre", ["carbon", "gloss carbon", "plain-weave carbon", "forged carbon", "kevlar", "fibreglass"]),
    "LF": ("Leather & fabric", ["leather", "quilted leather", "perforated leather", "suede", "cloth", "webbing", "denim"]),
    "WT": ("Wraps & tape", ["vinyl", "gloss wrap", "matte wrap", "chrome wrap", "brushed wrap", "reflective tape"]),
    "WE": ("Wear", ["scratched", "chipped", "dusty", "faded", "rusted", "greasy", "race-worn", "muddy"]),
    "PT": ("Patterns", ["camo", "hexagons", "checks", "splatter", "polka dots", "pinstripes"]),
    "LI": ("Light", ["neon", "night glow"]),
}
CODES = {}  # "ME-07" -> "gold"
for _letters, (_family, _names) in CATALOGUE.items():
    for _k, _name in enumerate(_names, 1):
        if _name is None:
            continue
        _code = f"{_letters}-{_k:02d}"
        CODES[_code] = _name
        LIBRARY[_name] = replace(LIBRARY[_name], code=_code, family=_family)
assert set(CODES.values()) == set(LIBRARY), f"finishes missing from CATALOGUE: {set(LIBRARY) - set(CODES.values())}"
CODE_WORD = re.compile(r"\b([a-z]{2})[- ]?(\d{2})\b", re.IGNORECASE)


def title(finish):
    """The name as the Lab shows it: "Polished aluminium"."""
    return finish.name[:1].upper() + finish.name[1:]


def line(finish):
    """The line the Lab copies for the user to paste to Claude: the code, the name, the numbers."""
    return (f"{finish.code} {title(finish)} (matte {round(finish.roughness * 100)}%, metal {round(finish.metalness * 100)}%, "
            f"varnish {round(finish.varnish * 100)}%)")


def _texture_finish(key):
    """A finish for a photographed surface added by name (tool/textures.py)."""
    from tool import textures
    spec = textures.SETS.get(key)
    if spec is None:
        return None
    return _f(key, 0.45 if spec.get("metal") else 0.6, 1.0 if spec.get("metal") else 0.0, 0.0,
              (0.6, 0.6, 0.62) if spec.get("metal") else None, look="texture", about=spec.get("about", ""))


def get(name):
    code = CODE_WORD.fullmatch(name.strip())
    if code and f"{code.group(1)}-{code.group(2)}".upper() in CODES:
        return LIBRARY[CODES[f"{code.group(1)}-{code.group(2)}".upper()]]
    key = " ".join(name.strip().lower().split())
    key = ALIASES.get(key, key)
    if key in SHINES and key not in LIBRARY:
        return SHINES[key]
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
                   varnish=shine.varnish, name=f"{shine.name} {finish.name}", code="")  # no longer the Lab's own


_NAMED_COLOURS = None


def _pull(phrase):
    """Take a Lab code ("ME-07"), or a finish's name that has a colour word in it ("rose gold",
    "stainless steel", "polished aluminium"), out of a phrase before its colour words are read,
    so they aren't split into a colour and a stray word: -> (Finish or None, the rest)."""
    global _NAMED_COLOURS
    from tool import colours
    code = CODE_WORD.search(phrase)
    if code and f"{code.group(1)}-{code.group(2)}".upper() in CODES:
        return LIBRARY[CODES[f"{code.group(1)}-{code.group(2)}".upper()]], phrase[:code.start()] + " " + phrase[code.end():]
    if _NAMED_COLOURS is None:  # names and aliases of 2+ words that hold a colour word, for finishes with their own colour
        _NAMED_COLOURS = {}
        for name, key in [(k, k) for k in LIBRARY] + list(ALIASES.items()):
            spaced = " ".join(name.replace("-", " ").split())
            fin = LIBRARY.get(key)
            if fin is not None and fin.colour is not None and len(spaced.split()) > 1 and colours.parse(spaced).colour is not None:
                _NAMED_COLOURS[spaced] = key
    words = phrase.lower().replace("-", " ").replace(",", " ").split()
    for n in (4, 3, 2):
        for i in range(len(words) - n + 1):
            key = _NAMED_COLOURS.get(" ".join(words[i:i + n]))
            if key:
                return LIBRARY[key], " ".join(words[:i] + words[i + n:])
    return None, phrase


def resolve(phrase, default="gloss"):
    """Sort a phrase into (colour, finish, leftover words). "dark red carbon, glossy" ->
    a dark red, the carbon finish with a gloss shine, []. Words that are neither a colour, a
    modifier, a finish nor a shine come back in the list, for the caller. A Lab code in the
    phrase is that finish: "ME-07 matte" is gold with a matte shine."""
    from tool import colours
    pre, phrase = _pull(phrase)
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
    if pre is not None:  # the code or the coloured name wins; a finish said beside it lends its shine
        if shine is None and finish is not None:
            shine = finish
        finish = pre
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
                     "seen": "the slots inside the front wheels, recoloured blue (the lights test, 2026-09-25): "
                             "dim blue all the time, flaring blue to white while braking, dim again at once"},
    "energy": {"code": 32, "keeps colour": False,
               "seen": "dim, tinted red by the game (the player's colour), on at rest"},
    "brake heat": {"code": 64, "keeps colour": True,
                   "seen": "orange rims (the lights test, 2026-09-25): dim red within a moment of braking hard, "
                           "full colour after about 1.5 s, fading about 1 s after letting go"},
    "always on": {"code": 96, "keeps colour": True,
                  "seen": "magenta as painted, day and night; the speed digits and rear lights are this code"},
    "front lights": {"code": 128, "keeps colour": True, "seen": "bright white by day and at night"},
    "turbo": {"code": 160, "keeps colour": False,
              "seen": "the hubs (stock) in the pad's colour after a yellow turbo pad (the lights test, 2026-09-25): "
                      "yellow for about 3 s, fading over the last half second; seen inside the wheels from the chase cameras"},
    "exhaust heat": {"code": 192, "keeps colour": True,
                     "seen": "not seen: the side vents that carry it in the lights test are hidden from the chase cameras"},
    "boost": {"code": 224, "keeps colour": False, "seen": "not seen"},
    "night only": {"code": 255, "keeps colour": True, "seen": "yellow as painted at night, and on a dusk map"},
}
GLOW_ALIASES = {"always": "always on", "on": "always on", "neon": "always on", "night": "night only", "at night": "night only",
                "headlights": "front lights", "lights": "front lights", "brake": "brake lights", "brakes": "brake lights",
                "team colour": "energy", "team color": "energy", "player colour": "energy"}


def glow(kind):
    key = kind.strip().lower()
    return GLOWS[GLOW_ALIASES.get(key, key)]
