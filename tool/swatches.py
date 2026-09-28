"""The Lab's materials: every finish the tool knows, painted on a ball, with its code and numbers.

    python -m tool.swatches            paint any balls that are missing or stale, serve, open the Lab
    python -m tool.swatches --all      repaint every ball
    python -m tool.swatches --no-open  just paint (docker/serve.py does this on the Mac)
    python -m tool.swatches --no-tab   paint and serve, no tab opened (a restart after a server
                                       change, with the Lab already open)

The Lab (viewer/lab.html) shows only what this writes, and this writes only what the tool has:
each finish in tool/finishes.py, in `CATALOGUE` order, each photographed surface named in
tool/textures.py that no finish uses yet, and each tread in tool/tyres.py's TREAD_LIBRARY (the
user, 2026-09-27: "In the material library, can we add a tread library as well?"). So the Lab is the tool's own list: a finish added to
the tool shows up here, and one missing here is missing from the tool (the user, 2026-09-26).

Each ball is painted with the same code that paints the car (looks.apply on a 30 cm ball's
texture). A tread goes on a tyre instead of a ball: the car's own tyre shape (tyre.json, its
cross-section from the mesh) turned on a lathe, wearing the tyres' map as the paint box paints it
(with Nadeo's shading, which the game adds), turned so the lathe can read it. The page draws the balls itself with the viewer's lighting (viewer/lab.js), so this
needs no browser and runs on the Mac too. Written to the viewer's data:
  <work>/viewer/materials/<slug>/{B,RM,Coat}.png + swatch.json, and materials.json (the list);
  a tread's folder has {B,RM,N,AO}.png, and tyre.json is the tyre's shape.
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

from tool import colours, finishes, looks, paths, textures, tyres, view

FOLDER = view.DATA / "materials"
RADIUS = 15.0  # cm: a 30 cm ball
SIZE = (1024, 512)  # the ball's texture, equirectangular
# a colour for finishes that have none of their own, so the ball shows something
SHOW_COLOUR = {"anodised": "electric blue", "neon": "neon pink", "night glow": "neon blue", "camo": None, "vinyl": "racing red"}
DEFAULT_COLOUR = (0.75, 0.12, 0.12)
PHOTOS = "Photographed"  # the family for surfaces added with tool.textures that no finish uses yet
TREADS = "Treads"  # the tread library (tool/tyres.py), each on a tyre
TYRE_POINTS = 129  # the tyre's cross-section, evenly across its map (u 0 to 1)


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
    params = {}
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
    return paint_look(fin, colour, params)


def paint_look(fin, colour, params=None):
    """A finish in a colour on the ball, painted as looks.apply paints the car: B (h, w, 3) sRGB,
    roughness, metalness, varnish (h, w), the finish and the colour. The Lab's balls, and the mood
    boards' (tool/mood.py)."""
    colour = np.asarray(colour, np.float32)
    pos, nrm, uv = ball()
    n = len(pos)
    params = {"seed": 0, "wrap": "uv", "uv": uv, **(params or {})}
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


def _hex(rgb):
    return "#" + "".join(f"{v:02X}" for v in _u8(np.asarray(rgb, np.float32)))


def describe(name, family):
    """What the Lab says about a finish: its code, numbers, colour, where it works, the line to copy."""
    fin = finishes.get(name)
    photo = family == PHOTOS
    return {
        "slug": slug_of(name), "code": fin.code, "name": finishes.title(fin), "family": family, "about": fin.about,
        "matte": round(fin.roughness * 100), "metal": round(fin.metalness * 100), "varnish": round(fin.varnish * 100),
        "colour": _hex(fin.colour) if fin.colour is not None else None,
        "works_on": "Inner car only (it glows)" if fin.glow else "Body · Inner car · Wheels",
        "source": "photo" if photo else fin.source,
        "line": finishes.line(fin) if fin.code else f"The photographed surface “{name}” (matte {round(fin.roughness * 100)}%, "
                                                      f"metal {round(fin.metalness * 100)}%)",
    }


def _turned(a):
    """The tyres' map (rows round the tyre, columns across it) turned for the Lab's lathe: across
    it bottom (the inner bead) to top, round it left to right."""
    return np.ascontiguousarray(np.swapaxes(a, 0, 1)[::-1])


def _half(a):
    im = Image.fromarray(_u8(a) if a.dtype != np.uint8 else a)
    return np.asarray(im.resize((im.width // 2, im.height // 2), Image.LANCZOS))


def write_tyre():
    """tyre.json: the tyre's cross-section, (radius, across) in tyre radii at TYRE_POINTS points
    evenly across its map, which a lathe turns into the Lab's tyre."""
    g = tyres.geometry()
    u = np.linspace(0, 1, TYRE_POINTS)
    col = np.clip(u * g["w"] - 0.5, 0, g["w"] - 1)
    r, across = np.interp(col, np.arange(g["w"]), g["r"]), np.interp(col, np.arange(g["w"]), g["across"])
    scale = float(r.max())
    FOLDER.mkdir(parents=True, exist_ok=True)
    (FOLDER / "tyre.json").write_text(json.dumps({"points": [[round(float(a) / scale, 5), round(float(b) / scale, 5)]
                                                             for a, b in zip(r, across)]}), encoding="utf-8")


def describe_tread(code):
    e = tyres.tread_library()[code]
    depth = e["fn"].depth
    sub = "Nadeo's grooves" if e["name"] == "Nadeo's own" else f"Grooves {depth * 10:.1f} mm" if depth else "No grooves"
    return {"slug": slug_of(f"tread {e['name']}"), "code": code, "name": e["name"][:1].upper() + e["name"][1:],
            "family": TREADS, "about": e["about"], "matte": 90, "metal": 0, "varnish": 0, "colour": None,
            "works_on": "The tyres' tread, all four", "source": "tread", "shape": "tyre", "maps": ["B", "RM", "N", "AO"],
            "sub": sub, "line": f"{code} {e['name'][:1].upper() + e['name'][1:]} tread ({e['about']})"}


def write_tread(code):
    """A tread's maps for the Lab's tyre, painted by the paint box as on the car."""
    from tool.paintbox import Skin
    from tool.testskin import stock
    info = describe_tread(code)
    folder = FOLDER / info["slug"]
    folder.mkdir(parents=True, exist_ok=True)
    sk = Skin("LabTread")
    sk.tyre_tread(code)
    tex = {k: arr for k, (arr, _, _) in sk.textures().items()}
    Image.fromarray(_half(_turned(tex["Wheels_B"])), "RGB").save(folder / "B.png", compress_level=1)
    r = _half(_turned(tex["Wheels_R"]))
    rm = np.zeros(r.shape[:2] + (3,), np.uint8)
    rm[..., 0], rm[..., 1], rm[..., 2] = 255, r[..., 0], r[..., 1]
    Image.fromarray(rm, "RGB").save(folder / "RM.png", compress_level=1)
    n = _turned(tex["Wheels_N"]).astype(np.float32)
    x, y = 1 - n[..., 1], n[..., 0]  # round the tyre is the lathe's u (the map's -v), across it its v (the map's u)
    x, y = x * 2 - 1, y * 2 - 1
    z = np.sqrt(np.clip(1 - x * x - y * y, 0, 1))
    Image.fromarray(_half(np.stack([x, y, z], -1) * 0.5 + 0.5), "RGB").save(folder / "N.png", compress_level=1)
    ao = _turned(stock("Wheels_AO")[..., 0] if stock("Wheels_AO").ndim == 3 else stock("Wheels_AO"))
    Image.fromarray(_u8(ao), "L").convert("RGB").save(folder / "AO.png", compress_level=1)
    (folder / "swatch.json").write_text(json.dumps(info), encoding="utf-8")
    return info


def write_textures(name, family):
    folder = FOLDER / slug_of(name)
    col, rough, metal, varnish, fin, colour = paint_ball(name)
    write_ball(folder, col, rough, metal, varnish)
    info = {**describe(name, family), "glow": [float(v) for v in colour] if fin.glow else None}
    (folder / "swatch.json").write_text(json.dumps(info), encoding="utf-8")
    return info


def write_ball(folder, col, rough, metal, varnish):
    """A ball's B, RM and Coat.png, as viewer/balls.js reads them."""
    folder.mkdir(parents=True, exist_ok=True)
    Image.fromarray(_u8(col), "RGB").save(folder / "B.png", compress_level=1)
    rm = np.zeros(col.shape, np.uint8)
    rm[..., 0] = 255
    rm[..., 1] = _u8(rough)
    rm[..., 2] = _u8(metal)
    Image.fromarray(rm, "RGB").save(folder / "RM.png", compress_level=1)
    coat = np.zeros(col.shape, np.uint8)
    coat[..., 0] = _u8(varnish)
    Image.fromarray(coat, "RGB").save(folder / "Coat.png", compress_level=1)


def _stamp(treads=False):
    """Changes when the code that paints finishes (or treads) changes: swatches older than it are
    repainted."""
    h = hashlib.sha256()
    for mod in (tyres,) if treads else (finishes, looks, textures):
        h.update(inspect.getsource(mod).encode())
    for fn in (describe_tread, write_tread, _turned) if treads else (paint_ball, paint_look, write_ball, describe):
        h.update(inspect.getsource(fn).encode())
    return h.hexdigest()[:12]


def entries():
    """(name, family) for every finish in the Lab's order, then photographed surfaces no finish uses."""
    out = [(name, family) for family, names in ((f, n) for f, n in finishes.CATALOGUE.values()) for name in names if name]
    listed = {name for name, _ in out}
    used = set(looks.TEXTURE_OF.values())  # photos that a finish above already shows
    for name in textures.SETS:
        if name not in listed and name not in used and finishes.ALIASES.get(name, name) not in listed:
            out.append((name, PHOTOS))
    out += [(code, TREADS) for code in tyres.tread_library()]
    return out


def build(all_=False):
    view.ensure_hdri()
    stamps = {False: _stamp(), True: _stamp(treads=True)}
    infos = []
    write_tyre()
    for name, family in entries():
        stamp = stamps[family == TREADS]
        slug = describe_tread(name)["slug"] if family == TREADS else slug_of(name)
        meta = FOLDER / slug / "swatch.json"
        fresh = meta.exists() and (FOLDER / slug / "B.png").exists() and json.loads(meta.read_text(encoding="utf-8")).get("stamp") == stamp
        if all_ or not fresh:
            t = time.time()
            info = write_tread(name) if family == TREADS else write_textures(name, family)
            info["stamp"] = stamp
            meta.write_text(json.dumps(info), encoding="utf-8")
            print(f"  painted {name} ({time.time() - t:.0f} s)", flush=True)
        else:
            info = json.loads(meta.read_text(encoding="utf-8"))
        infos.append(info)
    (FOLDER / "materials.json").write_text(json.dumps(infos, indent=1), encoding="utf-8")
    return infos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--no-open", action="store_true")
    ap.add_argument("--no-tab", action="store_true")
    args = ap.parse_args()
    infos = build(args.all)
    print(f"{len(infos)} materials")
    view.export_mesh()  # the car, and the Lab's rooms' data (view.export_uvmap)
    url = f"http://localhost:{view.PORT}/lab.html"
    if args.no_open:
        return
    try:
        server = view.start_server(view.PORT)
    except OSError:
        server = None
    print(f"the Lab: {url}", flush=True)
    if not args.no_tab:
        webbrowser.open(url)
    if server:
        import threading
        threading.Event().wait()


if __name__ == "__main__":
    main()
