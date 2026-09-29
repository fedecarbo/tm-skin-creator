"""Mood boards: a studio car's directions before anything touches the car (CHECKLIST.md, "The
design studio", W1 piece 3). Each board is a colour story, the finishes as the tool paints them,
and a wall of pictures; the boards show side by side on a page, and the user picks one.

    python -m tool.mood <car>           paint the boards' balls, write the page's data, print its address
    python -m tool.mood <car> --snap    ... and photograph the page into build/mood/<car>.png

A board is skins/<car>/mood/<slug>.json, written by Claude:

    {"title": "Lacquer", "line": "the direction in a sentence",
     "colours": [{"name": "ladybird red", "hex": "#B3121B", "role": "main", "share": 60}, ...],
     "finishes": [{"phrase": "gloss", "colour": "#B3121B", "label": "deep gloss red"}, ...],
     "wall": [{"svg": "<svg ...>...</svg>", "caption": "...", "wide": true},
              {"picture": "lacquer/macro.png", "caption": "..."}, ...]}

A finish is a phrase as a design says it (a Lab code works: "PA-09"), in the colour given, painted
on a ball by the Lab's own code (swatches.paint_look) and drawn with the Lab's lighting
(viewer/balls.js), so it looks as it will on the car. The wall is drawings (SVG, drawn by Claude)
and pictures: the picture maker's (on the PC), kept in skins/<car>/mood/<slug>/, never pictures
from the web. Boards were the studio's mood step, each an option on its build sheet, until the steps
went (2026-09-28: CHECKLIST.md, "The design studio", W3): a new car's mood now lives in its concepts,
on the car. The tool stays for boards the user asks for; TSC_Ladybird's are lettered from its sheet.

Written to the viewer's data, all rebuildable: mood/<car>/boards.json and each board's balls and
pictures. The page: viewer/mood.html?car=<car>.
"""

import argparse
import json
import re
import shutil
import time

import numpy as np

from tool import colours, finishes, paths, swatches, view
from tool.sets import title_of

HEX = re.compile(r"#[0-9A-Fa-f]{6}")
ROLES = ("main", "support", "accent")


def _hex(rgb):
    return "#" + "".join(f"{int(round(v * 255)):02X}" for v in rgb)


def _brief(car):
    """The brief's "What it is", for the page's header."""
    p = paths.SKINS / car / "brief.md"
    if not p.exists():
        return ""
    text = p.read_text(encoding="utf-8")
    m = re.search(r"^## What it is\s*\n(.+?)(?:\n\s*\n|\n## |\Z)", text, re.S | re.M)
    return " ".join(m.group(1).split()) if m else ""


def _letters(car):
    """{board file: letter} from the build sheet's Mood step, for a car made with it (TSC_Ladybird)."""
    p = paths.SKINS / car / "sheet.json"
    if not p.exists():
        return {}
    steps = json.loads(p.read_text(encoding="utf-8"))["steps"]
    mood = next(s for s in steps if s["key"] == "mood")
    return {o["file"]: o["key"] for o in mood["options"] if o.get("file")}


def _colour(c, where):
    if not isinstance(c, dict) or not c.get("name"):
        raise ValueError(f"{where}: a colour needs a name")
    if c.get("hex"):
        if not HEX.fullmatch(c["hex"]):
            raise ValueError(f"{where}: {c['hex']!r} isn't a colour like #B3121B")
        hx = c["hex"].upper()
    else:
        hx = _hex(colours.get(c["name"]))
    role = c.get("role", "support")
    if role not in ROLES:
        raise ValueError(f"{where}: role {role!r} isn't one of {', '.join(ROLES)}")
    return {"name": c["name"], "hex": hx, "role": role, "share": float(c.get("share", 0))}


def _ball(f, folder, where):
    """Paint one finish on a ball; what the page needs to draw it."""
    colour, fin, leftover = finishes.resolve(f["phrase"])
    if leftover:
        print(f"  {where}: {' '.join(leftover)!r} isn't a colour or a finish: left out")
    if f.get("colour"):
        colour = colours.get(f["colour"])
    given = colour is not None
    colour = colour if given else fin.colour if fin.colour is not None else swatches.DEFAULT_COLOUR
    col, rough, metal, varnish, fin, colour = swatches.paint_look(fin, colour, {"tinted": True} if given and fin.colour is None else {})
    swatches.write_ball(folder, col, rough, metal, varnish)
    return {"label": f.get("label") or finishes.title(fin),
            "line": finishes.line(fin) if fin.code else finishes.title(fin),
            "colour": _hex(np.asarray(colour)), "glow": [float(v) for v in colour] if fin.glow else None}


def build(car):
    src = paths.SKINS / car / "mood"
    files = sorted(src.glob("*.json"))
    if not files:
        raise SystemExit(f"{car} has no boards: write them as skins/{car}/mood/<name>.json")
    letters = _letters(car)
    files.sort(key=lambda p: (letters.get(f"mood/{p.name}", "~"), p.name))
    out = view.DATA / "mood" / car
    shutil.rmtree(out, ignore_errors=True)
    stamp = int(time.time())
    boards = []
    for n, spec in enumerate(files):
        b = json.loads(spec.read_text(encoding="utf-8"))
        slug = spec.stem
        where = f"{spec.name}"
        colours_ = [_colour(c, where) for c in b.get("colours", [])]
        balls = []
        for k, f in enumerate(b.get("finishes", [])):
            t = time.time()
            ball = _ball(f, out / slug / f"ball{k}", f"{where}, finish {k + 1}")
            ball.update(base=f"data/mood/{car}/{slug}/ball{k}/", stamp=stamp)
            balls.append(ball)
            print(f"  {slug}: painted {ball['label']} ({time.time() - t:.0f} s)", flush=True)
        wall = []
        for k, w in enumerate(b.get("wall", [])):
            tile = {"caption": w.get("caption", ""), "wide": bool(w.get("wide"))}
            if w.get("svg"):
                svg = w["svg"].strip()
                if not svg.startswith("<svg") or "<script" in svg.lower():
                    raise ValueError(f"{where}, wall {k + 1}: a drawing must be one <svg>, with no script")
                if "xmlns=" not in svg[:200]:  # the page shows it as a picture of its own, which needs it
                    svg = svg.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
                tile["svg"] = svg
            elif w.get("picture"):
                pic = src / w["picture"]
                if not pic.is_file():
                    raise FileNotFoundError(f"{where}, wall {k + 1}: no picture {pic}")
                dest = out / slug / "pictures" / f"{k}{pic.suffix.lower()}"
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(pic, dest)
                tile["picture"] = f"data/mood/{car}/{slug}/pictures/{dest.name}?v={stamp}"
            else:
                raise ValueError(f"{where}, wall {k + 1}: a drawing (svg) or a picture")
            wall.append(tile)
        boards.append({"key": letters.get(f"mood/{spec.name}", chr(65 + n)), "slug": slug, "title": b.get("title", slug),
                       "line": b.get("line", ""), "colours": colours_, "finishes": balls, "wall": wall})
    out.mkdir(parents=True, exist_ok=True)
    doc = {"car": car, "title": title_of(car), "brief": _brief(car), "boards": boards, "stamp": stamp}
    (out / "boards.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    return doc


def url(car):
    return f"http://localhost:{view.PORT}/mood.html?car={car}"


def snap(car, size=(1600, 1000)):
    """The page photographed whole, as tool/snap.py's pictures."""
    from playwright.sync_api import sync_playwright

    try:
        view.start_server(view.PORT)
    except OSError:
        pass  # already served
    out = paths.BUILD / "mood" / f"{car}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = paths.launch(p)
        page = browser.new_page(viewport={"width": size[0], "height": size[1]})
        page.goto(url(car))
        page.wait_for_function("window.mood && (window.mood.ready || window.mood.error)", timeout=120000)
        err = page.evaluate("window.mood.error")
        if err:
            raise RuntimeError(err)
        page.screenshot(path=str(out), full_page=True)
        browser.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("car")
    ap.add_argument("--snap", action="store_true")
    args = ap.parse_args()
    doc = build(args.car)
    print(f"{len(doc['boards'])} boards: " + ", ".join(f"{b['key']} {b['title']}" for b in doc["boards"]))
    print(f"the page: {url(args.car)}")
    if args.snap:
        print(f"photographed: {snap(args.car)}")


if __name__ == "__main__":
    main()
