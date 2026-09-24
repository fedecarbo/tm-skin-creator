"""Named finishes and glows, with the values the game was seen to honour (checkpoint 4).

A finish is what a surface is made of, apart from its colour: roughness, metalness and varnish.
The paint box gives every painted area a colour and a finish, and this table turns the finish
into the numbers written to the `_R` and `Skin_CoatR` textures.

What the lab skins showed in the game (2026-09-24, see CHECKLIST.md, "Things we learned"):
  - roughness (0 mirror .. 1 matte) and metalness (0 paint .. 1 metal) work as in any PBR
    renderer, on the body, the details and the tyres alike;
  - `Skin_CoatR` is the varnish: 0 lays a glossy clear varnish over anything, 255 lays none. A skin
    without the file is varnished all over. So matte paint needs varnish 255 on that area, and the
    tool always ships `Skin_CoatR`. (Only the body has a varnish file.)

    finishes.FINISHES["matte"]           -> Finish(roughness=0.9, metalness=0.0, varnish=0.0)
    finishes.rm(finish)                  -> (roughness, metalness) for a `_R` texture, 0..1
    finishes.coat(finish)                -> the `Skin_CoatR` value, 0..1 (1 - varnish)
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Finish:
    roughness: float  # 0 mirror .. 1 matte
    metalness: float  # 0 paint .. 1 metal
    varnish: float  # 0 none .. 1 a glossy clear varnish on top (body only; the game's CoatR is 1 - this)
    about: str = ""


# Plain words the user might use -> a finish. Values are the lab's, chosen by eye from the game.
FINISHES = {
    "gloss": Finish(0.3, 0.0, 1.0, "shiny paint under a clear varnish: the game's default look"),
    "satin": Finish(0.5, 0.0, 0.0, "a soft sheen, no varnish"),
    "matte": Finish(0.9, 0.0, 0.0, "flat, no shine at all"),
    "metallic": Finish(0.4, 0.5, 1.0, "metallic paint: flakes under a varnish"),
    "chrome": Finish(0.05, 1.0, 0.0, "a mirror"),
    "polished metal": Finish(0.2, 1.0, 0.0, "bright metal, reflections a little soft"),
    "brushed metal": Finish(0.55, 1.0, 0.0, "dull metal, reflections smeared"),
    "rubber": Finish(0.9, 0.0, 0.0, "matte and dark, like a tyre"),
}
ALIASES = {"glossy": "gloss", "shiny": "gloss", "flat": "matte", "mat": "matte", "metal": "polished metal",
           "mirror": "chrome", "silk": "satin", "eggshell": "satin", "pearl": "metallic"}


def get(name):
    key = name.strip().lower()
    return FINISHES[ALIASES.get(key, key)]


def rm(finish):
    """(roughness, metalness) for a `_R` texture."""
    return finish.roughness, finish.metalness


def coat(finish):
    """The `Skin_CoatR` value: 0 is a glossy varnish, 1 none."""
    return 1.0 - finish.varnish


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
