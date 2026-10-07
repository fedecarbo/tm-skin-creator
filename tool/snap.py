"""Claude's snapshots of a skin in the viewer: six views on one sheet, taken by a hidden browser.

    python -m tool.snap <name>          -> build/<name>_views.png
    python -m tool.snap <name> --size 1280x960
    python -m tool.snap <name> --close  -> build/<name>_close.png: the close looks (CLOSE)
    python -m tool.snap <name> --eye    -> build/<name>_eye.png: a close look at each spot the eye names on the
                                             last show (tool/eye.py: where a graphic crosses or meets a line,
                                             and whatever it flags), the model's mesh drawn on the paint
    python -m tool.snap <name> --before [close|views|...]  -> build/<name>_<kind>_compare.png, opened:
                                             each tile that changed since the sheet before, before
                                             beside after, the change outlined (a sheet's last one is
                                             kept as <name>_<kind>_before.png)
    python -m tool.snap <name> --cams   -> build/<name>_cams.png: the game's Cam 1 and 2 and their alts,
                                             by day and at night, at 16:9 (CAMS), to set beside
                                             the game's F12 screenshots
    python -m tool.snap <name> --body   -> build/<name>_body.png: the body alone, no wheels, nine views
    python -m tool.snap --page "lab.html?room=uv" [--size 1600x1000]
                                          -> build/lab_room_uv.png: any page of the viewer's, whole
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
import json
import re
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

from tool import fonts, paths, progress, server, view

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
         ("9 driving camera", {"dir": [0, 0.42, -1], "dist": 4.5, "target": [0, 0.55, 0.2]}, False, []),
         # the farthest back of the side, behind the rear wheel, where the side turns onto the back (the
         # user, 2026-10-02: a line that "didn't cover the rear, as in the farthest back of the side")
         ("10 left tail corner", {"dir": [0.6, 0.25, -0.9], "dist": 1.2, "target": [0.48, 0.33, -1.45]}, False, []))
# The game's chase cameras standing still (viewer.js's VIEWS, fitted to the user's screenshots),
# by day and at night, at the screenshots' 16:9: what the calibration car is read through.
CAMS = tuple((f"{title} {'night' if night else 'day'}", view, night, []) for night in (False, True)
             for title, view in (("Cam 1", "cam1"), ("Cam 1 alt", "cam1alt"), ("Cam 2", "cam2"), ("Cam 2 alt", "cam2alt")))
CAM_SIZE = "1280x720"
# The body alone, the wheels taken off (car/map/model.jpg; the user, 2026-09-29, "you might need to
# hide the wheels so you see the body"): nine views, the flanks behind the wheels and the underside's
# edges included.
NO_WHEELS = {"hidden": ["wheel cover", "tyre", "rims and brakes"]}
BODY = (("front three-quarter", "front", False, [], NO_WHEELS), ("rear three-quarter", "rear", False, [], NO_WHEELS),
        ("top", "top", False, [], NO_WHEELS),
        ("left side", "left", False, [], NO_WHEELS), ("right side", "right", False, [], NO_WHEELS),
        ("front straight on", {"dir": [0, 0.18, 1], "dist": 5.0, "target": [0, 0.45, 0.2]}, False, [], NO_WHEELS),
        ("rear straight on", {"dir": [0, 0.25, -1], "dist": 4.6, "target": [0, 0.45, -0.3]}, False, [], NO_WHEELS),
        ("front three-quarter, low", {"dir": [0.8, 0.12, 0.6], "dist": 5.2, "target": [0, 0.4, 0.2]}, False, [], NO_WHEELS),
        ("underside", {"dir": [0.3, -1, 0.2], "dist": 7.0, "target": [0, 0.2, 0.2]}, False, [], NO_WHEELS))
VIEW_TILES = {"front": (0, 0), "rear": (1, 0), "left": (2, 0), "right": (0, 1), "top": (1, 1), "night": (2, 1)}
EYE_DIST = 0.8   # metres from a spot the eye names: about 50 cm of the car across
EYE_APART = 10   # cm: spots nearer than this (or a spot's mirror on the other side) share a look
EYE_MOST = 12    # looks at most, what the eye flags first


def _font(px):
    """Arial Bold, the PC's or the Mac's."""
    return fonts.font("arial bold", px)


def snap(name, out=None, size=(960, 720), shots=SHOTS, query="", prepare=True, thumb=None, mesh=False):
    """query: extra page settings, e.g. "exposure=1.1&coat=0.5" (TUNE in viewer.js, over each look's own).
    prepare=False: the skin is already in the viewer's data (the paint box exports it itself).
    thumb: a path to save the first view to, unlabelled, at 640x480 (the gallery's picture).
    mesh: the model's mesh drawn over the paint (view.export_template's, viewer.mesh)."""
    if prepare:
        view.prepare(name)
    if mesh:
        view.export_template()
        query = "&".join(q for q in (query, "mesh=1") if q)
    httpd = server.start(0)
    url = f"http://127.0.0.1:{httpd.server_address[1]}/?skin={name}&snap=1" + (f"&{query}" if query else "")
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
            if mesh and not page.evaluate("viewer.mesh(true)"):
                raise RuntimeError("no mesh to draw: view.export_template")
            print(f"GPU: {page.evaluate('viewer.gpu()')}; loaded in {time.time() - start:.1f} s")
            progress.stage("Taking pictures", total=len(shots))
            for label, view_spec, night, hidden, *rest in shots:
                page.evaluate("([v, n, h]) => viewer.show(v, n, h)", [view_spec, night, hidden])
                page.evaluate("(o) => viewer.showParts(o)", rest[0] if rest else {})
                tiles.append((label, Image.open(io.BytesIO(page.screenshot()))))
                progress.tick()
            browser.close()
    finally:
        httpd.shutdown()
    for e in errors:
        print(f"page error: {e}")
    return sheet(name, tiles, out, size, thumb)


def page(path, size=(1600, 1000)):
    """Any page of the viewer's, e.g. "lab.html?room=uv", photographed whole once it says it's
    ready (window.lab), into build/<page>.png."""
    httpd = server.start(0)
    out = paths.BUILD / (re.sub(r"[^\w-]+", "_", path.replace(".html", "")).strip("_") + ".png")
    try:
        with sync_playwright() as p:
            browser = paths.launch(p)
            pg = browser.new_page(viewport={"width": size[0], "height": size[1]})
            pg.on("pageerror", lambda e: print(f"page error: {e}"))
            pg.goto(f"http://127.0.0.1:{httpd.server_address[1]}/{path}")
            pg.wait_for_function("window.lab && (window.lab.ready || window.lab.error)", timeout=120_000)
            err = pg.evaluate("window.lab.error")
            if err:
                raise RuntimeError(err)
            out.parent.mkdir(parents=True, exist_ok=True)
            pg.screenshot(path=str(out), full_page=True)
            browser.close()
    finally:
        httpd.shutdown()
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
    if out.exists():  # the sheet before, for before and after at the same cameras (compare)
        out.replace(out.with_name(f"{out.stem}_before{out.suffix}"))
    sheet.save(out)
    print(f"sheet: {out}")
    return out


KINDS = {"views": SHOTS, "close": CLOSE, "cams": CAMS, "body": BODY}


def eye_shots(name):
    """A close look at each spot the eye named on the last show (build/<name>/eye.json): what it flags first, then
    where a graphic crosses or meets a line; the camera square to the body there. Prints what each look is for."""
    looks = json.loads((paths.BUILD / name / "eye.json").read_text())["looks"]
    found = [(x, side, f) for x in looks for side, said in x["sides"].items() for f in said
             if f["flag"] or f["words"].startswith(("crosses", "its edge meets"))]
    found.sort(key=lambda t: (not t[2]["flag"], t[1] != "left"))
    taken, shots = [], []
    for x, side, f in found:
        if len(shots) == EYE_MOST:
            break
        at = np.array(f["at"])
        if any(min(np.linalg.norm(at - p), np.linalg.norm(at * [-1, 1, 1] - p)) < EYE_APART for p in taken):
            continue
        taken.append(at)
        d = np.array(f["nrm"], float)
        d[1] = max(d[1], 0.15)  # never from under the floor
        k = len(shots) + 1
        print(f"  {k}: {x['n']}. {x['step']}, {side}: {f['words']}")
        shots.append((f"{k} {x['step']}, {side}: {f['flag'] or ('meets' if 'meets' in f['words'] else 'crosses')}",
                      {"dir": (d / np.linalg.norm(d)).round(3).tolist(), "dist": EYE_DIST, "target": (at / 100).tolist()},
                      False, []))
    return shots


def changed(ta, tb):
    """Where tile tb differs from ta, as a box, the change outlined in both; None if it doesn't.
    Noise of a few levels, and specks, don't count."""
    from PIL import ImageChops, ImageFilter
    diff = ImageChops.difference(ta, tb).convert("L").point(lambda v: 255 if v > 12 else 0)
    where = diff.filter(ImageFilter.MinFilter(5)).getbbox()  # specks go
    if where is not None:
        x0, y0, x1, y1 = where
        for t in (ta, tb):
            ImageDraw.Draw(t).rectangle((x0 - 12, y0 - 12, x1 + 12, y1 + 12), outline=(232, 255, 71), width=4)
    return where


def compare(name, kind="close", open_it=True):
    """Each tile of a sheet that changed since the sheet before it: before beside after, the change
    outlined in both (changed)."""
    new, old = paths.BUILD / f"{name}_{kind}.png", paths.BUILD / f"{name}_{kind}_before.png"
    if not old.exists():
        raise SystemExit(f"no earlier {kind} sheet of {name}: take one, change the design, take another")
    a, b = Image.open(old).convert("RGB"), Image.open(new).convert("RGB")
    if a.size != b.size:
        raise SystemExit(f"{old.name} and {new.name} differ in size: the cameras changed in between")
    shots = KINDS[kind]
    w, h = a.width // 3, a.height // ((len(shots) + 2) // 3)
    rows = []
    for k, shot in enumerate(shots):
        box = ((k % 3) * w, (k // 3) * h, (k % 3 + 1) * w, (k // 3 + 1) * h)
        ta, tb = a.crop(box), b.crop(box)
        if changed(ta, tb):
            rows.append((shot[0], ta, tb))
    if not rows:
        print(f"{name}: no {kind} tile changed")
        return None
    band = 60
    out = Image.new("RGB", (2 * w, len(rows) * (h + band)), (24, 24, 26))
    font = _font(34)
    for i, (label, ta, tb) in enumerate(rows):
        y = i * (h + band)
        d = ImageDraw.Draw(out)
        d.text((16, y + 12), f"{label}: before", fill=(235, 235, 235), font=font)
        d.text((w + 16, y + 12), "after", fill=(235, 235, 235), font=font)
        out.paste(ta, (0, y + band))
        out.paste(tb, (w, y + band))
    path = paths.BUILD / f"{name}_{kind}_compare.png"
    png = io.BytesIO()
    out.save(png, "PNG")
    paths.write(path, png.getvalue())
    print(f"changed: {', '.join(r[0] for r in rows)}\ncompare: {path}")
    if open_it:
        paths.open_file(path)
    return path


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
    png = io.BytesIO()
    out.save(png, "PNG")
    paths.write(path, png.getvalue())  # the last one may still be open on the user's screen
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
    ap.add_argument("--eye", action="store_true", help="a close look at each spot the eye names, the mesh drawn")
    ap.add_argument("--cams", action="store_true", help="the game's Cam 1 and 2 and their alts, day and night, at 16:9")
    ap.add_argument("--body", action="store_true", help="the body alone, no wheels, nine views")
    ap.add_argument("--picture", action="store_true", help="put the snapped sheets together for the user")
    ap.add_argument("--titles", nargs="*", help="a short title per skin, in plain words")
    ap.add_argument("--views", nargs="*", default=["front", "rear", "top"], choices=list(VIEW_TILES))
    ap.add_argument("--close-row", nargs="+", action="append", metavar="NAME N",
                    help="a skin, then numbers from its close sheet (again for another skin)")
    ap.add_argument("--page", metavar="PAGE", help='any page of the viewer\'s, whole, e.g. "lab.html" (no name)')
    ap.add_argument("--before", nargs="?", const="close", choices=list(KINDS),
                    help="the tiles that changed since the sheet before, before beside after")
    args = ap.parse_args()
    if args.page:
        page(args.page, tuple(int(v) for v in (args.size or "1600x1000").split("x")))
        return
    if not args.name:
        ap.error("the skin's name")
    if args.before:
        compare(args.name, args.before)
        return
    if args.eye:
        shots = eye_shots(args.name)
        if not shots:
            print("the eye names no spot to look at")
            return
        with progress.job(f"Photographing {progress.title_of(args.name)}: where the eye looked", skin=args.name,
                          done="Photographed"):
            snap(args.name, out=paths.BUILD / f"{args.name}_eye.png", shots=shots, prepare=False, mesh=True)
        return
    shots, kind = ((CLOSE, "close") if args.close else (CAMS, "cams") if args.cams
                   else (BODY, "body") if args.body else (SHOTS, "views"))
    if args.picture:
        close = [(row[0], row[1:]) for row in args.close_row or []]
        picture([args.name] + args.more, args.titles, args.views, close)
        return
    w, h = (int(v) for v in (args.size or (CAM_SIZE if args.cams else "960x720")).split("x"))
    what = {"close": "close looks", "cams": "the game's cameras", "body": "the body"}
    with progress.job(f"Photographing {progress.title_of(args.name)}" + (f": {what[kind]}" if kind in what else ""),
                      skin=args.name, done="Photographed"):
        if args.close or args.cams or args.body:
            snap(args.name, out=paths.BUILD / f"{args.name}_{kind}.png", size=(w, h), shots=shots, prepare=False,
                 query="lens=game" if args.cams else "")  # the game's wide lens, to set beside its screenshots
        else:
            snap(args.name, size=(w, h))


if __name__ == "__main__":
    main()
