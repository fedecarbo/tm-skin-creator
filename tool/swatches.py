"""The materials page: every finish on a ball, pictured, named and grouped.

    python -m tool.swatches            build any swatches that are missing or stale, serve, open the page
    python -m tool.swatches --all      rebuild every swatch

For each finish in tool/finishes.py (and each photographed surface named in tool/textures.py)
the look is painted onto a 30 cm ball's texture with the same code that paints the car, then
viewer/swatch.html renders the ball with the car's lighting and a hidden Edge takes its picture.
viewer/materials.html shows them all. The page lives with the viewer's data:
  <work>/viewer/materials/<slug>/{B,RM,Coat}.png + swatch.json + swatch.png, and materials.json.
"""

import argparse
import hashlib
import inspect
import json
import re
import time
import webbrowser

import numpy as np
from PIL import Image

from tool import colours, finishes, looks, paths, textures, view

FOLDER = view.DATA / "materials"
RADIUS = 15.0  # cm: a 30 cm ball
SIZE = (1024, 512)  # the ball's texture, equirectangular
FAMILY = {
    "paint": ["gloss", "satin", "matte", "semi-gloss", "metallic", "pearl", "candy"],
    "metal": ["chrome", "mirror", "polished aluminium", "brushed steel", "brushed titanium", "gunmetal", "gold", "copper",
              "anodised", "raw cast"],
    "composites and plastics": ["carbon", "forged carbon", "kevlar", "gloss plastic", "matte plastic", "rubber", "vinyl"],
    "inside": ["leather", "quilted leather", "cloth", "webbing"],
    "wear": ["scratched", "chipped", "dusty", "faded", "rusted", "greasy", "race-worn"],
    "light": ["neon", "reflective tape"],
    "patterns": ["camo", "hexagons", "checks", "splatter", "polka dots", "pinstripes"],
}
# a colour for finishes that have none of their own, so the ball shows something
SHOW_COLOUR = {"anodised": "electric blue", "neon": "neon pink", "camo": None, "vinyl": "racing red"}
DEFAULT_COLOUR = (0.75, 0.12, 0.12)


def slug_of(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def ball():
    """Positions (cm), normals and flat (u, v) in cm for every texel of the ball's texture."""
    w, h = SIZE
    u = (np.arange(w) + 0.5) / w
    v = (np.arange(h) + 0.5) / h
    phi, theta = np.meshgrid(u * 2 * np.pi, v * np.pi)
    nrm = np.stack([-np.cos(phi) * np.sin(theta), np.cos(theta), np.sin(phi) * np.sin(theta)], -1).reshape(-1, 3).astype(np.float32)
    pos = nrm * RADIUS
    uv = np.stack([phi.reshape(-1) * RADIUS, theta.reshape(-1) * RADIUS], -1).astype(np.float32)
    return pos, nrm, uv


def paint_ball(name):
    """The ball's textures for a finish: B (h, w, 3) sRGB, roughness, metalness, varnish (h, w)."""
    fin = finishes.get(name)
    colour = fin.colour
    shown = SHOW_COLOUR.get(name, "keep")
    if shown is None:
        colour = None
    elif shown != "keep":
        colour = colours.get(shown)
    if colour is None:
        colour = DEFAULT_COLOUR
    colour = np.asarray(colour, np.float32)
    pos, nrm, uv = ball()
    n = len(pos)
    params = {"seed": 0, "wrap": "uv", "uv": uv}
    if fin.colour is None and shown not in (None, "keep"):
        params["tinted"] = True
    if name == "camo":
        params["palette"] = ["charcoal", "slate", "light grey", "jet black"]
        params["scale"] = 6
    if name == "polka dots":
        params["scale"] = 6
    if name == "checks":
        params["scale"] = 5
    if name == "splatter":
        params["scale"] = 4
    if fin.look:
        r = looks.apply(fin, colour, pos, nrm, params)
        col = r["colour"]
        rough = r.get("roughness", np.full(n, fin.roughness, np.float32))
        metal = r.get("metalness", np.full(n, fin.metalness, np.float32))
        varnish = r.get("varnish", np.full(n, fin.varnish, np.float32))
        if "weight" in r:
            wgt = r["weight"][:, None]
            col = np.broadcast_to(colour, (n, 3)) * (1 - wgt) + col * wgt
    else:
        col = np.broadcast_to(colour, (n, 3))
        rough, metal, varnish = (np.full(n, v, np.float32) for v in (fin.roughness, fin.metalness, fin.varnish))
    h, w = SIZE[1], SIZE[0]
    return (np.asarray(col).reshape(h, w, 3), np.asarray(rough).reshape(h, w), np.asarray(metal).reshape(h, w),
            np.asarray(varnish).reshape(h, w), fin, colour)


def _u8(a):
    return np.clip(np.rint(np.asarray(a, np.float32) * 255), 0, 255).astype(np.uint8)


def write_textures(name, family):
    slug = slug_of(name)
    folder = FOLDER / slug
    folder.mkdir(parents=True, exist_ok=True)
    col, rough, metal, varnish, fin, colour = paint_ball(name)
    Image.fromarray(_u8(col), "RGB").save(folder / "B.png", compress_level=1)
    rm = np.zeros(col.shape, np.uint8)
    rm[..., 0] = 255
    rm[..., 1] = _u8(rough)
    rm[..., 2] = _u8(metal)
    Image.fromarray(rm, "RGB").save(folder / "RM.png", compress_level=1)
    coat = np.zeros(col.shape, np.uint8)
    coat[..., 0] = _u8(varnish)
    Image.fromarray(coat, "RGB").save(folder / "Coat.png", compress_level=1)
    info = {"slug": slug, "name": name, "family": family, "about": fin.about,
            "glow": [float(v) for v in colour] if fin.glow else None}
    (folder / "swatch.json").write_text(json.dumps(info), encoding="utf-8")
    return info


def _stamp():
    """Changes when the code that paints finishes changes: swatches older than it are rebuilt."""
    h = hashlib.sha256()
    for mod in (finishes, looks, textures):
        h.update(inspect.getsource(mod).encode())
    h.update(inspect.getsource(paint_ball).encode())
    return h.hexdigest()[:12]


def entries():
    out = []
    listed = set()
    for family, names in FAMILY.items():
        for name in names:
            if name in finishes.LIBRARY or name in finishes.SHINES:
                out.append((name, family))
                listed.add(name)
    for name in finishes.LIBRARY:
        if name not in listed:
            out.append((name, "more"))
            listed.add(name)
    used = set(looks.TEXTURE_OF.values())  # photos that a finish above already shows
    for name in textures.SETS:
        if name not in listed and name not in used and finishes.ALIASES.get(name, name) not in listed:
            out.append((name, "photographed surfaces"))
    return out


def build(all_=False):
    view.ensure_hdri()
    stamp = _stamp()
    todo = []
    infos = []
    for name, family in entries():
        slug = slug_of(name)
        meta = FOLDER / slug / "swatch.json"
        fresh = meta.exists() and (FOLDER / slug / "swatch.png").exists() and json.loads(meta.read_text(encoding="utf-8")).get("stamp") == stamp
        if all_ or not fresh:
            t = time.time()
            info = write_textures(name, family)
            info["stamp"] = stamp
            (FOLDER / slug / "swatch.json").write_text(json.dumps(info), encoding="utf-8")
            todo.append(slug)
            print(f"  painted {name} ({time.time() - t:.0f} s)", flush=True)
        else:
            info = json.loads(meta.read_text(encoding="utf-8"))
        infos.append(info)
    if todo:
        snapshot(todo)
    for info in infos:
        info["stamp"] = int((FOLDER / info["slug"] / "swatch.png").stat().st_mtime)
    (FOLDER / "materials.json").write_text(json.dumps(infos, indent=1), encoding="utf-8")
    return infos


def snapshot(slugs, size=360):
    """Picture each ball with a hidden Edge, through viewer/swatch.html."""
    from playwright.sync_api import sync_playwright
    from tool import snap
    server = view.start_server(0)
    url = f"http://127.0.0.1:{server.server_address[1]}/swatch.html?snap=1"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True, args=snap.EDGE_ARGS)
            page = browser.new_page(viewport={"width": size, "height": size})
            page.goto(url)
            page.wait_for_function("window.swatch && (window.swatch.ready || window.swatch.error)", timeout=120_000)
            if page.evaluate("window.swatch.error"):
                raise RuntimeError(page.evaluate("window.swatch.error"))
            for slug in slugs:
                page.evaluate("(s) => swatch.show(s)", slug)
                page.screenshot(path=str(FOLDER / slug / "swatch.png"))
            browser.close()
    finally:
        server.shutdown()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()
    infos = build(args.all)
    print(f"{len(infos)} materials")
    url = f"http://localhost:{view.PORT}/materials.html"
    if args.no_open:
        return
    try:
        server = view.start_server(view.PORT)
    except OSError:
        server = None
    print(f"materials: {url}", flush=True)
    webbrowser.open(url)
    if server:
        import threading
        threading.Event().wait()


if __name__ == "__main__":
    main()
