"""Fonts for lettering: the Windows fonts on this PC plus a few free Google Fonts (SIL OFL 1.1).

    fonts.font("orbitron", 300)          -> a PIL ImageFont, 300 px tall
    fonts.font("orbitron", 300, weight=900)

The Google fonts are downloaded once into the work folder from the google/fonts repository at a
pinned commit, and checked against the sha256 recorded here (2026-09-24). The OFL lets a skin
use them freely, including skins other players see. Their licence text is saved beside them.
"""

import hashlib
import urllib.request

from PIL import ImageFont

from tool import paths

FOLDER = paths.WORK / "fonts"
COMMIT = "23e54b51ddffbc7713c583748e3bd86f62b1fa4a"  # google/fonts main, 2026-09-24
URL = f"https://raw.githubusercontent.com/google/fonts/{COMMIT}/ofl/{{family}}/{{file}}"

# name -> (file, sha256) for the Google fonts; (path, None) for the Windows ones.
GOOGLE = {
    "orbitron": ("orbitron", "Orbitron[wght].ttf", "f42db2dd16e642258e35782916eceb1dcdbea06fb958d77ad71dc5963587e8fd"),
    "russo": ("russoone", "RussoOne-Regular.ttf", "bc0abcc660bd8b7ad3000ecb2898a27c58a29a50f7ec81652fa12e75148d09df"),
    "black ops": ("blackopsone", "BlackOpsOne-Regular.ttf", "282a825b5f294377387e3969f765408157dbea8da0f5d0aae68c6bc704b145b3"),
    "bangers": ("bangers", "Bangers-Regular.ttf", "4160a7311de9342674cce9160cde9fcbb30f48190397d86ff1b70b455af65824"),
    "racing": ("racingsansone", "RacingSansOne-Regular.ttf", "8b5cada83e3e4692f624f1b583a069b34e457e07a4210ceddbb1133b3383673e"),
    "teko": ("teko", "Teko[wght].ttf", "d1321889f262bbbff632e7976349853399cd097b6f382d4b19790c915c13c1ae"),
}
LICENCE = ("orbitron", "OFL.txt")
WINDOWS = {
    "impact": "impact.ttf", "bahnschrift": "bahnschrift.ttf", "arial bold": "arialbd.ttf", "arial black": "ariblk.ttf",
    "verdana bold": "verdanab.ttf", "georgia bold": "georgiab.ttf", "segoe bold": "segoeuib.ttf",
    "consolas bold": "consolab.ttf", "corbel bold": "corbelb.ttf", "tahoma bold": "tahomabd.ttf",
}
# What each looks like, for choosing from the user's words.
ABOUT = {
    "impact": "tall, heavy, condensed: the classic loud number",
    "bahnschrift": "clean German road-sign lettering",
    "arial bold": "plain and safe",
    "arial black": "very heavy plain lettering",
    "verdana bold": "wide, friendly",
    "georgia bold": "a serif, classic",
    "segoe bold": "modern, rounded",
    "consolas bold": "typewriter / code look",
    "corbel bold": "soft, modern",
    "tahoma bold": "compact sans",
    "orbitron": "square futuristic, sci-fi",
    "russo": "wide, bold, techno racing",
    "black ops": "military stencil",
    "bangers": "comic-book shout",
    "racing": "italic racing script, retro motorsport",
    "teko": "tall condensed, sporty",
}
DEFAULT = "russo"


def _fetch(family, file, sha=None):
    target = FOLDER / file
    if target.exists() and (sha is None or hashlib.sha256(target.read_bytes()).hexdigest() == sha):
        return target
    FOLDER.mkdir(parents=True, exist_ok=True)
    data = urllib.request.urlopen(URL.format(family=family, file=file), timeout=60).read()
    if sha and hashlib.sha256(data).hexdigest() != sha:
        raise ValueError(f"{file}: the download doesn't match the recorded sha256")
    target.write_bytes(data)
    return target


def path(name):
    key = name.strip().lower()
    if key in WINDOWS:
        return f"C:/Windows/Fonts/{WINDOWS[key]}"
    if key in GOOGLE:
        family, file, sha = GOOGLE[key]
        _fetch(*LICENCE)
        return str(_fetch(family, file, sha))
    raise KeyError(f"no font called {name!r}; known: {', '.join(list(WINDOWS) + list(GOOGLE))}")


def font(name, size_px, weight=None):
    f = ImageFont.truetype(path(name), size_px)
    if weight is not None:
        try:
            f.set_variation_by_axes([weight])
        except OSError:
            pass  # not a variable font
    return f
