"""The tyre library's pictures: every marking (tool/tyres.py) on the car, close up on a front wheel
from each side, for the user to choose from.

    python -m tool.tyres [TY-01 ...]
        -> build/tyres/<code>_left.jpg, _right.jpg (the front wheels, the car's left and right) and
           _tread.jpg (the rear left tyre from behind),
           build/tyres/library.png (every marking, left side, on one sheet, opened on the screen)
           and build/tyres/library.json (codes, names, families, what each is)

Each marking is painted by the paint box on its own (the tyres, and the wheels a plain dark grey;
the rest of the car stock) and
shown in the viewer as TyreLib_<code>, which no gallery lists. One Edge session takes them all.
"""

import io
import json
import os
import time

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

from tool import paths, snap, tyres, view
from tool.paintbox import Skin

OUT = paths.BUILD / "tyres"
# the front wheels from each side, a little ahead and above, and the rear left tyre's tread from
# behind, as the chase cameras see it (metres; the car's left is +x)
VIEWS = {"left": {"dir": [1, 0.14, 0.18], "dist": 1.5, "target": [0.92, 0.37, 1.78]},
         "right": {"dir": [-1, 0.14, 0.18], "dist": 1.5, "target": [-0.92, 0.37, 1.78]},
         "tread": {"dir": [0.42, 0.62, -1], "dist": 1.25, "target": [0.86, 0.3, -1.3]}}
SIZE = (720, 540)


def skin_name(code):
    return f"TyreLib_{code.replace('-', '')}"


def paint(codes):
    """Paint each marking and put it in the viewer's data. Returns {code: notes}."""
    view.export_mesh()
    view.ensure_hdri()
    view.ensure_stock()
    notes = {}
    for code in codes:
        t0 = time.time()
        s = Skin(skin_name(code), size=1024)  # the body and inner car barely show: small and quick
        s.paint("wheels", "satin", colour="#2b2c30")  # plain wheels, so the tyres stand out
        s.no_glow("wheels")
        s.tyre_marks(code)
        view.export_skin(s.name, {k: arr for k, (arr, _, _) in s.textures().items()})
        notes[code] = list(dict.fromkeys(s.notes))
        print(f"{code} {tyres.library()[code]['name']}: painted in {time.time() - t0:.1f} s")
    return notes


def photograph(codes):
    server = view.start_server(0)
    port = server.server_address[1]
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True, args=snap.EDGE_ARGS)
            page = browser.new_page(viewport={"width": SIZE[0], "height": SIZE[1]})
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(f"http://127.0.0.1:{port}/?skin={skin_name(codes[0])}&snap=1")
            page.wait_for_function("window.viewer && (window.viewer.ready || window.viewer.error)", timeout=180_000)
            if page.evaluate("window.viewer.error"):
                raise RuntimeError(page.evaluate("window.viewer.error"))
            for code in codes:
                page.evaluate("(n) => viewer.load(n)", skin_name(code))
                for side, spec in VIEWS.items():
                    page.evaluate("([v]) => viewer.show(v, false, [])", [spec])
                    im = Image.open(io.BytesIO(page.screenshot())).convert("RGB")
                    im.save(OUT / f"{code}_{side}.jpg", quality=88)
            browser.close()
            for e in errors:
                print(f"page error: {e}")
    finally:
        server.shutdown()


def sheet(codes, cols=8, tile=(400, 300), strip=34):
    """Every marking from the car's left, its code and name under it, and its family."""
    lib = tyres.library()
    font, small = snap._font(18), snap._font(14)
    rows = (len(codes) + cols - 1) // cols
    out = Image.new("RGB", (cols * tile[0], rows * (tile[1] + strip)), (18, 18, 20))
    d = ImageDraw.Draw(out)
    for k, code in enumerate(codes):
        x, y = (k % cols) * tile[0], (k // cols) * (tile[1] + strip)
        out.paste(Image.open(OUT / f"{code}_left.jpg").resize(tile, Image.LANCZOS), (x, y))
        d.text((x + 8, y + tile[1] + 7), f"{code}  {lib[code]['name']}", fill=(245, 245, 245), font=font)
        fam = lib[code]["family"]
        d.text((x + tile[0] - 8 - d.textlength(fam, font=small), y + tile[1] + 10), fam, fill=(150, 150, 155), font=small)
    path = OUT / "library.png"
    out.save(path)
    return path


def page(folder, codes=None):
    """The library's page (viewer/tyres.html) in `folder`, ready to publish: index.html with the
    library's words in it, and img/<code>.jpg, each marking's three views side by side."""
    lib = tyres.library()
    codes = codes or list(lib)
    (folder / "img").mkdir(parents=True, exist_ok=True)
    for code in codes:
        strip = Image.new("RGB", (1440, 360))
        for k, side in enumerate(VIEWS):
            strip.paste(Image.open(OUT / f"{code}_{side}.jpg").resize((480, 360), Image.LANCZOS), (k * 480, 0))
        strip.save(folder / "img" / f"{code}.jpg", quality=82)
    data = [{"code": c, "name": lib[c]["name"], "family": lib[c]["family"], "about": lib[c]["about"]} for c in codes]
    html = (paths.REPO / "viewer" / "tyres.html").read_text(encoding="utf-8").replace("__DATA__", json.dumps(data))
    (folder / "index.html").write_text(html, encoding="utf-8")
    return folder / "index.html"


def make(codes, open_it=True):
    OUT.mkdir(parents=True, exist_ok=True)
    notes = paint(codes)
    photograph(codes)
    lib = tyres.library()
    doc = {"codes": [{"code": c, "name": lib[c]["name"], "family": lib[c]["family"], "about": lib[c]["about"],
                      "notes": notes.get(c, [])} for c in codes]}
    (OUT / "library.json").write_text(json.dumps(doc, indent=1), encoding="utf-8")
    path = sheet(codes)
    print(f"sheet: {path}")
    if open_it:
        os.startfile(path)
    return path
