"""Claude's snapshots of a skin in the viewer: six views on one sheet, taken by a hidden browser.

    python -m tool.snap <name>          -> build/<name>_views.png
    python -m tool.snap <name> --size 1280x960
    python -m tool.snap <name> --close  -> build/<name>_close.png: the close looks (CLOSE)
    python -m tool.snap <name> --cams   -> build/<name>_cams.png: the game's Cam 1 and 2 and their alts,
                                             by day and at night, at 16:9 (CAMS), to set beside
                                             the game's F12 screenshots
    python -m tool.snap <name> --body   -> build/<name>_body.png: the body alone, no wheels (the car map's)
    python -m tool.snap <name> --stretches -> build/<name>_stretches.png: the car map's close looks, each
                                             stretch of the body from the nose's tip to the tail, no
                                             wheels, both sides (STRETCHES), to check its lines close up
    python -m tool.snap <name> --review -> build/<name>_review.png: the angles the other sheets miss
                                             (REVIEW), for the studio's critic (tool/critic.py)
    python -m tool.snap --page "mood.html?car=<car>" [--size 1600x1000]
                                          -> build/mood_car_<car>.png: any page of the viewer's, whole
    python -m tool.snap <name> --picture [<other> ...] [--titles ...] [--views ...]
                                             [--close-row <name> 2 5 9 [--close-row <other> 2 5 9]]
        -> build/<name>_picture.png, a row per skin from its views sheet (and a row of close
           looks), opened on the screen: the picture shown to the user

Look at the sheet before showing a skin to the user. Playwright drives the Edge installed on
the PC, and its own Chromium on the Mac (paths.launch). The GPU line it prints says which
renderer drew the pictures.
"""

import argparse
import io
import re
import time
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

from tool import fonts, paths, view

# (label, view, night, hidden meshes[, parts]). A view is a name from viewer.js's VIEWS, or
# {"dir": [x, y, z], "dist": metres, "target": [x, y, z]} for a close look. parts is an optional
# dict for viewer.showParts: {"colourBy": True, "shared": True, "hidden": [...], "only": [...],
# "highlight": [...]} with part or assembly names (or "name|side|end").
SHOTS = (("front three-quarter", "front", False, []), ("rear three-quarter", "rear", False, []),
         ("left side", "left", False, []), ("right side", "right", False, []),
         ("top", "top", False, []), ("night", "front", True, []))
# Close looks where graphics meet joins, folds and holes, and the view from the driving camera:
# the places the user zooms in on (2026-09-24). Targets in metres = the model's cm / 100.
CLOSE = (("1 bonnet", {"dir": [0.35, 0.85, 0.4], "dist": 1.4, "target": [0, 0.66, 1.17]}, False, []),
         ("2 nose", {"dir": [0.55, 0.55, 0.65], "dist": 1.3, "target": [0, 0.45, 1.9]}, False, []),
         ("3 left front flank (the fold)", {"dir": [0.9, 0.35, 0.25], "dist": 1.5, "target": [0.45, 0.5, 0.75]}, False, []),
         ("4 left sidepod", {"dir": [0.75, 0.6, 0.3], "dist": 1.6, "target": [0.7, 0.55, -0.2]}, False, []),
         ("5 left rear flank", {"dir": [0.95, 0.25, -0.2], "dist": 1.4, "target": [0.7, 0.41, -0.66]}, False, []),
         ("6 deck and tail", {"dir": [0.35, 0.75, -0.6], "dist": 1.8, "target": [0, 0.65, -1.15]}, False, []),
         ("7 right side", {"dir": [-0.85, 0.4, 0.2], "dist": 2.4, "target": [-0.55, 0.45, -0.1]}, False, []),
         ("8 front wheel", {"dir": [1, 0.2, 0.25], "dist": 1.3, "target": [0.9, 0.35, 1.79]}, False, []),
         ("9 driving camera", {"dir": [0, 0.42, -1], "dist": 4.5, "target": [0, 0.55, 0.2]}, False, []))
# The game's chase cameras standing still (viewer.js's VIEWS, fitted to the user's screenshots),
# by day and at night, at the screenshots' 16:9: what the calibration car is read through.
CAMS = tuple((f"{title} {'night' if night else 'day'}", view, night, []) for night in (False, True)
             for title, view in (("Cam 1", "cam1"), ("Cam 1 alt", "cam1alt"), ("Cam 2", "cam2"), ("Cam 2 alt", "cam2alt")))
CAM_SIZE = "1280x720"
# What the views and close looks leave out, for the studio's critic (tool/critic.py): the car straight
# on (does it make a face?), its tail low from behind (where the car behind sees it), the underside
# (from below the floor, which isn't drawn from there), and the right-hand flanks the close looks
# see only on the left (graphics and words on the other side).
REVIEW = (("front straight on", {"dir": [0, 0.18, 1], "dist": 5.0, "target": [0, 0.45, 0.2]}, False, []),
          ("rear low", {"dir": [0, 0.12, -1], "dist": 4.2, "target": [0, 0.4, -0.3]}, False, []),
          ("under the tail", {"dir": [0.3, -0.35, -1], "dist": 2.2, "target": [0, 0.2, -1.3]}, False, []),
          ("underside", {"dir": [0.3, -1, 0.2], "dist": 7.0, "target": [0, 0.2, 0.2]}, False, []),
          ("right front flank", {"dir": [-0.9, 0.35, 0.25], "dist": 1.5, "target": [-0.45, 0.5, 0.75]}, False, []),
          ("right rear flank", {"dir": [-0.95, 0.25, -0.2], "dist": 1.4, "target": [-0.7, 0.41, -0.66]}, False, []))
# The body alone, the wheels taken off (the car map's pictures, tool/carmap.py: the user, 2026-09-29,
# "you might need to hide the wheels so you see the body"): nine views, the flanks behind the wheels
# and the underside's edges included.
NO_WHEELS = {"hidden": ["wheel cover", "tyre", "rims and brakes"]}
BODY = (("front three-quarter", "front", False, [], NO_WHEELS), ("rear three-quarter", "rear", False, [], NO_WHEELS),
        ("top", "top", False, [], NO_WHEELS),
        ("left side", "left", False, [], NO_WHEELS), ("right side", "right", False, [], NO_WHEELS),
        ("front straight on", {"dir": [0, 0.18, 1], "dist": 5.0, "target": [0, 0.45, 0.2]}, False, [], NO_WHEELS),
        ("rear straight on", {"dir": [0, 0.25, -1], "dist": 4.6, "target": [0, 0.45, -0.3]}, False, [], NO_WHEELS),
        ("front three-quarter, low", {"dir": [0.8, 0.12, 0.6], "dist": 5.2, "target": [0, 0.4, 0.2]}, False, [], NO_WHEELS),
        ("underside", {"dir": [0.3, -1, 0.2], "dist": 7.0, "target": [0, 0.2, 0.2]}, False, [], NO_WHEELS))
# The car map's close looks (the user zooms in on the map's lines, so the check does too): each
# stretch of the body from the nose's tip to the tail, close, the wheels off, on both sides.
_STRETCH = (("nose's tip", [0.5, 0.5, 0.7], 0.9, [0, 0.35, 2.05]), ("nose", [0.8, 0.45, 0.4], 1.0, [0.2, 0.45, 1.6]),
            ("fin's plate and bonnet", [0.8, 0.5, 0.3], 1.1, [0.25, 0.55, 1.2]),
            ("front flank and its lip", [0.95, 0.25, 0.2], 1.1, [0.35, 0.45, 0.8]),
            ("sidepod's front and inlet", [0.7, 0.4, 0.6], 1.1, [0.65, 0.45, 0.2]),
            ("sidepod's top", [0.35, 0.9, 0.25], 1.0, [0.68, 0.6, -0.15]),
            ("sidepod", [0.95, 0.35, 0.0], 1.2, [0.8, 0.45, -0.3]), ("rear flank", [0.95, 0.3, -0.2], 1.2, [0.65, 0.4, -0.9]),
            ("deck", [0.5, 0.8, -0.3], 1.3, [0.3, 0.6, -0.9]), ("tail", [0.6, 0.4, -0.7], 1.1, [0.3, 0.5, -1.45]))
STRETCHES = tuple((f"{side} {label}", {"dir": [s * d[0], d[1], d[2]], "dist": dist, "target": [s * t[0], t[1], t[2]]},
                   False, [], NO_WHEELS)
                  for label, d, dist, t in _STRETCH for side, s in (("left", 1), ("right", -1)))
VIEW_TILES = {"front": (0, 0), "rear": (1, 0), "left": (2, 0), "right": (0, 1), "top": (1, 1), "night": (2, 1)}


def _font(px):
    """Arial Bold, the PC's or the Mac's."""
    return fonts.font("arial bold", px)


def snap(name, out=None, size=(960, 720), shots=SHOTS, query="", prepare=True, thumb=None):
    """query: extra page settings, e.g. "exposure=1.1&coat=0.5" (TUNE in viewer.js, over each look's own).
    prepare=False: the skin is already in the viewer's data (the paint box exports it itself).
    thumb: a path to save the first view to, unlabelled, at 640x480 (the gallery's picture)."""
    if prepare:
        view.prepare(name)
    server = view.start_server(0)
    url = f"http://127.0.0.1:{server.server_address[1]}/?skin={name}&snap=1" + (f"&{query}" if query else "")
    tiles, errors = [], []
    try:
        with sync_playwright() as p:
            browser = paths.launch(p)
            page = browser.new_page(viewport={"width": size[0], "height": size[1]})
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append(str(e)))
            start = time.time()
            page.goto(url)
            page.wait_for_function("window.viewer && (window.viewer.ready || window.viewer.error)",
                                   timeout=180_000)
            if page.evaluate("window.viewer.error"):
                raise RuntimeError(page.evaluate("window.viewer.error"))
            print(f"GPU: {page.evaluate('viewer.gpu()')}; loaded in {time.time() - start:.1f} s")
            for label, view_spec, night, hidden, *rest in shots:
                page.evaluate("([v, n, h]) => viewer.show(v, n, h)", [view_spec, night, hidden])
                page.evaluate("(o) => viewer.showParts(o)", rest[0] if rest else {})
                tiles.append((label, Image.open(io.BytesIO(page.screenshot()))))
            browser.close()
    finally:
        server.shutdown()
    for e in errors:
        print(f"page error: {e}")
    return sheet(name, tiles, out, size, thumb)


def page(path, size=(1600, 1000)):
    """Any page of the viewer's, e.g. "mood.html?car=<car>", photographed whole once it says it's
    ready (window.mood or window.lab), into build/<page>.png."""
    server = view.start_server(0)
    out = paths.BUILD / (re.sub(r"[^\w-]+", "_", path.replace(".html", "")).strip("_") + ".png")
    try:
        with sync_playwright() as p:
            browser = paths.launch(p)
            pg = browser.new_page(viewport={"width": size[0], "height": size[1]})
            pg.on("pageerror", lambda e: print(f"page error: {e}"))
            pg.goto(f"http://127.0.0.1:{server.server_address[1]}/{path}")
            pg.wait_for_function('["mood", "lab"].some((k) => window[k] && (window[k].ready || window[k].error))',
                                 timeout=120_000)
            err = pg.evaluate("(window.mood || window.lab).error")
            if err:
                raise RuntimeError(err)
            out.parent.mkdir(parents=True, exist_ok=True)
            pg.screenshot(path=str(out), full_page=True)
            browser.close()
    finally:
        server.shutdown()
    print(f"page: {out}")
    return out


def sheet(name, tiles, out=None, size=(960, 720), thumb=None):
    """The sheet of labelled views, from (label, picture) pairs; thumb as snap()'s."""
    out = out or paths.BUILD / f"{name}_views.png"
    if thumb and tiles:
        Path(thumb).parent.mkdir(parents=True, exist_ok=True)
        tiles[0][1].convert("RGB").resize((640, 480), Image.LANCZOS).save(thumb)
    cols = 3
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * size[0], rows * size[1]))
    font = _font(24)
    for k, (label, tile) in enumerate(tiles):
        d = ImageDraw.Draw(tile)
        d.text((14, 10), label, fill=(255, 255, 255), font=font, stroke_width=3, stroke_fill=(0, 0, 0))
        sheet.paste(tile.convert("RGB"), ((k % cols) * size[0], (k // cols) * size[1]))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(f"sheet: {out}")
    return out


def _tile(sheet, k):
    """The k-th view (0-based) of a 3-column sheet."""
    im = Image.open(sheet)
    w = im.width // 3
    h = w * 3 // 4
    return im.crop(((k % 3) * w, (k // 3) * h, (k % 3 + 1) * w, (k // 3 + 1) * h))


def picture(names, titles=None, views=("front", "rear", "top"), close=None, open_it=True):
    """The picture for the user: a titled row per skin (views from its views sheet) and, with
    close = (name, [numbers from its close sheet]) or a list of them (one per take), rows of close
    looks. Opens it on the screen."""
    titles = list(titles or [])
    rows = []
    for k, name in enumerate(names):
        title = f"{k + 1}  {titles[k] if k < len(titles) else name}" if len(names) > 1 else (titles[0] if titles else name)
        c, r = zip(*(VIEW_TILES[v] for v in views))
        rows.append((title, [_tile(paths.BUILD / f"{name}_views.png", r[i] * 3 + c[i]) for i in range(len(views))]))
    for name, numbers in ([close] if close and isinstance(close[0], str) else close or []):
        label = titles[names.index(name)] if name in names and names.index(name) < len(titles) else name
        if len(names) > 1 and name in names:
            label = f"{names.index(name) + 1}  {label}"
        tiles = [_tile(paths.BUILD / f"{name}_close.png", int(n) - 1) for n in numbers]
        for i in range(0, len(tiles), 3):
            rows.append((f"Up close: {label}" if i == 0 else "", tiles[i:i + 3]))
    tw, th = rows[0][1][0].size
    band = 70
    out = Image.new("RGB", (3 * tw, len(rows) * (th + band)), (24, 24, 26))
    font = _font(40)
    for i, (title, tiles) in enumerate(rows):
        y = i * (th + band)
        ImageDraw.Draw(out).text((20, y + 14), title, fill=(235, 235, 235), font=font)
        for j, t in enumerate(tiles):
            out.paste(t.convert("RGB").resize((tw, th)), (j * tw, y + band))
    path = paths.BUILD / f"{names[0]}_picture.png"
    out.save(path)
    print(f"picture: {path}")
    if open_it:
        paths.open_file(path)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", nargs="?")
    ap.add_argument("more", nargs="*", help="with --picture: the other takes, in order")
    ap.add_argument("--size", help="each picture's size (960x720; 1280x720 with --cams)")
    ap.add_argument("--close", action="store_true", help="the close looks instead of the six views")
    ap.add_argument("--cams", action="store_true", help="the game's Cam 1 and 2 and their alts, day and night, at 16:9")
    ap.add_argument("--review", action="store_true", help="the angles the other sheets miss, for the critic")
    ap.add_argument("--body", action="store_true", help="the body alone, no wheels, nine views (the car map's pictures)")
    ap.add_argument("--stretches", action="store_true", help="the car map's close looks: each stretch of the body, no wheels, both sides")
    ap.add_argument("--picture", action="store_true", help="put the snapped sheets together for the user")
    ap.add_argument("--titles", nargs="*", help="a short title per skin, in plain words")
    ap.add_argument("--views", nargs="*", default=["front", "rear", "top"], choices=list(VIEW_TILES))
    ap.add_argument("--close-row", nargs="+", action="append", metavar="NAME N",
                    help="a skin, then numbers from its close sheet (again for another skin)")
    ap.add_argument("--page", metavar="PAGE", help='any page of the viewer\'s, whole, e.g. "lab.html" (no name)')
    args = ap.parse_args()
    if args.page:
        page(args.page, tuple(int(v) for v in (args.size or "1600x1000").split("x")))
        return
    if not args.name:
        ap.error("the skin's name")
    shots, kind = ((CLOSE, "close") if args.close else (CAMS, "cams") if args.cams else (REVIEW, "review") if args.review
                   else (BODY, "body") if args.body else (STRETCHES, "stretches") if args.stretches else (SHOTS, "views"))
    if args.picture:
        close = [(row[0], row[1:]) for row in args.close_row or []]
        picture([args.name] + args.more, args.titles, args.views, close)
        return
    w, h = (int(v) for v in (args.size or (CAM_SIZE if args.cams else "960x720")).split("x"))
    if args.close or args.cams or args.review or args.body or args.stretches:
        snap(args.name, out=paths.BUILD / f"{args.name}_{kind}.png", size=(w, h), shots=shots, prepare=False,
             query="lens=game" if args.cams else "")  # the game's wide lens, to set beside its screenshots
    else:
        snap(args.name, size=(w, h))


if __name__ == "__main__":
    main()
