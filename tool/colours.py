"""Colour words -> RGB (sRGB, 0..1), and phrases like "dark metallic red" taken apart.

    colours.get("racing green")            -> (r, g, b)
    colours.parse("dark red carbon")       -> Parsed(colour=(..), finish="carbon", words=["dark"])

The user speaks in plain words, so the list is wide: the CSS names, car-paint names, and
lighteners ("light", "pale", "dark", "deep", "bright", "dull"). Unknown words are left in
`words` for the caller to sort out (a finish, a layout, a pattern).
"""

import colorsys
from dataclasses import dataclass, field

# Plain names. Tuned by eye for a car: "red" is a racing red, not pure #FF0000.
NAMES = {
    "red": "#d0121b", "racing red": "#c8102e", "ferrari red": "#d40000", "cherry": "#9b1b30", "crimson": "#b3122e",
    "scarlet": "#e0301e", "maroon": "#6b1a2a", "burgundy": "#6e1b30", "wine": "#6e1b30", "rust": "#a4501f",
    "orange": "#f26a13", "papaya": "#f7961e", "tangerine": "#f28c28", "amber": "#f5a623", "gulf orange": "#f58220",
    "yellow": "#f9d100", "lemon": "#f5e94b", "gold": "#d4a531", "mustard": "#c9a227", "sand": "#d8c59a",
    "beige": "#d9c8a9", "cream": "#f2ead3", "ivory": "#f4f0e0", "tan": "#b98d5b", "brown": "#5a3a1e",
    "chocolate": "#4a2d1b", "coffee": "#5a4632", "copper": "#b87333", "bronze": "#9c6a2d", "khaki": "#8f8a5a",
    "olive": "#5b6b2a", "army green": "#4b5a2f", "olive drab": "#6b6b3a", "green": "#0f8a3a", "racing green": "#0b4d2c",
    "british racing green": "#0b4d2c", "forest": "#1e4d2b", "emerald": "#0f9a5e", "lime": "#8fd400", "neon green": "#39ff14",
    "mint": "#8fdcc0", "teal": "#0f7f8a", "turquoise": "#1cbcc8", "cyan": "#12c8e6", "aqua": "#12c8e6", "sky blue": "#5cb3ff",
    "light blue": "#7fbfff", "baby blue": "#a9d0f5", "blue": "#0f3fbf", "royal blue": "#1b3fbf", "electric blue": "#1e60ff",
    "gulf blue": "#7ab8d9", "navy": "#0f1f4d", "midnight blue": "#0f1f4d", "cobalt": "#1f4bb5", "petrol": "#1b4b5a",
    "indigo": "#3b2a8f", "purple": "#6a1fa8", "violet": "#7b2fd1", "lavender": "#b39ddb", "lilac": "#c8a2d8",
    "magenta": "#e0189a", "fuchsia": "#e0189a", "pink": "#f25ca2", "hot pink": "#ff1f8f", "rose": "#e26d8f", "salmon": "#f08070",
    "coral": "#ff6b5b", "peach": "#f7b58a", "white": "#f4f4f2", "pearl white": "#f0efe8", "off white": "#ebe8dd", "snow": "#fafafa",
    "black": "#0a0a0c", "jet black": "#050506", "charcoal": "#2b2c30", "graphite": "#3a3c42", "anthracite": "#2f3238",
    "gunmetal": "#3c4047", "grey": "#8a8c90", "gray": "#8a8c90", "silver": "#c8cacd", "dark grey": "#4a4c50", "dark gray": "#4a4c50",
    "light grey": "#c0c2c5", "light gray": "#c0c2c5", "slate": "#5a6470", "steel": "#8c949c", "titanium": "#7a7f85",
    "aluminium": "#c9cbcd", "aluminum": "#c9cbcd", "chrome": "#dcdee0", "platinum": "#e2e2e0", "nickel": "#b5b7b5",
    "neon blue": "#2fa8ff", "neon pink": "#ff2fa8", "neon orange": "#ff7a1a", "neon yellow": "#f4ff2f",
    "ice blue": "#bfe6ff", "plum": "#6b2a5a", "brick": "#8b3a2a", "terracotta": "#b5563a", "moss": "#5e7a3a",
    "camo green": "#5a6b3a", "desert": "#c2a878", "sea green": "#2e8b6e", "smoke": "#6f7175", "bone": "#e3dccb",
}
# Modifiers: (lightness multiplier, saturation multiplier)
MODIFIERS = {
    "light": (1.35, 0.85), "pale": (1.6, 0.5), "bright": (1.1, 1.3), "vivid": (1.0, 1.4), "dark": (0.6, 1.0),
    "deep": (0.7, 1.2), "dull": (0.9, 0.6), "muted": (0.95, 0.55), "soft": (1.15, 0.7), "rich": (0.85, 1.2),
    "pastel": (1.5, 0.45), "dusty": (1.0, 0.5), "faded": (1.1, 0.5), "very": None,
}
FILLER = {"a", "an", "the", "in", "of", "and", "with", "colour", "color", "coloured", "colored", "paint", "painted"}


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def get(name):
    """A colour from a name, a hex string or an (r, g, b) tuple."""
    if isinstance(name, (tuple, list)):
        return tuple(float(v) for v in name)
    s = name.strip().lower()
    if s.startswith("#"):
        return hex_to_rgb(s)
    if s in NAMES:
        return hex_to_rgb(NAMES[s])
    parsed = parse(s)
    if parsed.colour is None:
        raise KeyError(f"no colour called {name!r}")
    return parsed.colour


def adjust(rgb, light=1.0, sat=1.0):
    h, l, s = colorsys.rgb_to_hls(*rgb)
    l = min(1.0, l * light) if light >= 1 else l * light
    s = min(1.0, s * sat)
    return colorsys.hls_to_rgb(h, l, s)


@dataclass
class Parsed:
    colour: tuple | None = None
    colour_name: str = ""
    modifiers: list = field(default_factory=list)
    words: list = field(default_factory=list)  # whatever wasn't a colour or a modifier


def parse(phrase):
    """Pick the colour out of a phrase. The longest matching name wins ("racing green" over
    "green"); modifiers before it apply to it; the other words are returned as they came."""
    words = [w for w in phrase.lower().replace("-", " ").replace(",", " ").split() if w not in FILLER]
    out = Parsed()
    i = 0
    rest = []
    pending = []
    while i < len(words):
        hit = None
        if words[i].startswith("#") and len(words[i]) == 7 and out.colour is None:
            out.colour_name = words[i]
            out.colour = hex_to_rgb(words[i])
            out.modifiers = pending
            pending = []
            i += 1
            continue
        for n in (3, 2, 1):
            cand = " ".join(words[i:i + n])
            if cand in NAMES and out.colour is None:
                hit = cand
                break
        if hit:
            out.colour_name = hit
            out.colour = hex_to_rgb(NAMES[hit])
            out.modifiers = pending
            pending = []
            i += len(hit.split())
        elif words[i] in MODIFIERS:
            if MODIFIERS[words[i]] is not None:
                pending.append(words[i])
            i += 1
        else:
            rest.extend(pending)
            pending = []
            rest.append(words[i])
            i += 1
    rest.extend(pending)
    out.words = rest
    if out.colour is not None:
        for m in out.modifiers:
            light, sat = MODIFIERS[m]
            out.colour = adjust(out.colour, light, sat)
    return out
