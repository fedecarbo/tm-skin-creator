"""Claude's snapshots of a skin in the viewer: six views on one sheet, taken by a hidden Edge.

    python -m tool.snap TSC_Test          -> build/TSC_Test_views.png
    python -m tool.snap TSC_Test --size 1280x960
    python -m tool.snap TSC_Test --close  -> build/TSC_Test_close.png: the close looks (CLOSE)
    python -m tool.snap TSC_Test --picture [TSC_Other ...] [--titles ...] [--views ...]
                                             [--close-row TSC_Test 2 5 9]
        -> build/TSC_Test_picture.png, a row per skin from its views sheet (and a row of close
           looks), opened on the screen: the picture shown to the user

Look at the sheet before showing a skin to the user. Playwright drives the Edge installed on
this PC (no browser download). The GPU line it prints says which renderer drew the pictures.
"""

import argparse
import io
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

from tool import paths, view

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
VIEW_TILES = {"front": (0, 0), "rear": (1, 0), "left": (2, 0), "right": (0, 1), "top": (1, 1), "night": (2, 1)}
EDGE_ARGS = ["--use-angle=d3d11", "--enable-gpu", "--ignore-gpu-blocklist"]


def snap(name, out=None, size=(960, 720), shots=SHOTS, query="", prepare=True, thumb=None):
    """query: extra page settings, e.g. "exposure=0.9&coat=0.5" (TUNE in viewer.js).
    prepare=False: the skin is already in the viewer's data (the paint box exports it itself).
    thumb: a path to save the first view to, unlabelled, at 640x480 (the gallery's picture)."""
    if prepare:
        view.prepare(name)
    server = view.start_server(0)
    url = f"http://127.0.0.1:{server.server_address[1]}/?skin={name}&snap=1" + (f"&{query}" if query else "")
    tiles, errors = [], []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True, args=EDGE_ARGS)
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
    out = out or paths.BUILD / f"{name}_views.png"
    if thumb and tiles:
        Path(thumb).parent.mkdir(parents=True, exist_ok=True)
        tiles[0][1].convert("RGB").resize((640, 480), Image.LANCZOS).save(thumb)
    cols = 3
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * size[0], rows * size[1]))
    font = ImageFont.truetype("arialbd.ttf", 24)
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
    close = (name, [numbers from its close sheet]), rows of close looks. Opens it on the screen."""
    titles = list(titles or [])
    rows = []
    for k, name in enumerate(names):
        title = f"{k + 1}  {titles[k] if k < len(titles) else name}" if len(names) > 1 else (titles[0] if titles else name)
        c, r = zip(*(VIEW_TILES[v] for v in views))
        rows.append((title, [_tile(paths.BUILD / f"{name}_views.png", r[i] * 3 + c[i]) for i in range(len(views))]))
    if close:
        name, numbers = close
        label = titles[names.index(name)] if name in names and names.index(name) < len(titles) else name
        tiles = [_tile(paths.BUILD / f"{name}_close.png", int(n) - 1) for n in numbers]
        for i in range(0, len(tiles), 3):
            rows.append((f"Up close: {label}" if i == 0 else "", tiles[i:i + 3]))
    tw, th = rows[0][1][0].size
    band = 70
    out = Image.new("RGB", (3 * tw, len(rows) * (th + band)), (24, 24, 26))
    font = ImageFont.truetype("arialbd.ttf", 40)
    for i, (title, tiles) in enumerate(rows):
        y = i * (th + band)
        ImageDraw.Draw(out).text((20, y + 14), title, fill=(235, 235, 235), font=font)
        for j, t in enumerate(tiles):
            out.paste(t.convert("RGB").resize((tw, th)), (j * tw, y + band))
    path = paths.BUILD / f"{names[0]}_picture.png"
    out.save(path)
    print(f"picture: {path}")
    if open_it:
        import os
        os.startfile(path)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("more", nargs="*", help="with --picture: the other takes, in order")
    ap.add_argument("--size", default="960x720")
    ap.add_argument("--close", action="store_true", help="the close looks instead of the six views")
    ap.add_argument("--picture", action="store_true", help="put the snapped sheets together for the user")
    ap.add_argument("--titles", nargs="*", help="a short title per skin, in plain words")
    ap.add_argument("--views", nargs="*", default=["front", "rear", "top"], choices=list(VIEW_TILES))
    ap.add_argument("--close-row", nargs="+", metavar="NAME N", help="a skin, then numbers from its close sheet")
    args = ap.parse_args()
    if args.picture:
        close = (args.close_row[0], args.close_row[1:]) if args.close_row else None
        picture([args.name] + args.more, args.titles, args.views, close)
        return
    w, h = (int(v) for v in args.size.split("x"))
    if args.close:
        snap(args.name, out=paths.BUILD / f"{args.name}_close.png", size=(w, h), shots=CLOSE, prepare=False)
    else:
        snap(args.name, size=(w, h))


if __name__ == "__main__":
    main()
