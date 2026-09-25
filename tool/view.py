"""The 3D viewer: prepares what the page in viewer/ loads, and serves it.

    python -m tool.view TSC_Test              prepare a built skin, serve, open the browser
    python -m tool.view TSC_Test --no-open    same, without opening the browser

Python's built-in web server serves two folders (ES modules don't load from file://):
  /        the repo's viewer/ folder: the page and three.js
  /data/   the work folder's viewer/ folder, all rebuildable:
             car.json, car.bin    the four meshes, in metres, with the car's wheels at y = 0, each
                                  corner tagged with its part; parts.json lists the parts
             <Set>_Shared.png     the texels that several parts share (mirrored or repeated)
             <name>.hdr           the lighting by day and at night, Poly Haven HDRIs (CC0), see HDRIS
             stock/*.png          Nadeo's stock textures, for anything a skin leaves out
             skins/<name>/        one skin's textures, and skin.json with the URL of every slot

The game's textures become PNG "slots" laid out the way three.js reads them:
  <Set>_B      base colour, sRGB
  <Set>_RM     G = roughness, B = metalness (three.js reads them there; the game's _R holds R, G)
  Skin_Coat    R = how much glossy varnish, 255 - Skin_CoatR (0 in the game's file is full gloss,
               255 none). Without the file the whole body is glossy, as in the game.
  <Set>_N      normal map, RGB, with Z rebuilt from the game's two channels
  <Set>_I      glow colour, RGB, and <Set>_Code, the glow code of each texel (the _I alpha)
  Glass_T      glass tint, RGBA
  <Set>_AO     ambient occlusion, always the stock maps: the game applies AO itself
Dirt masks aren't shown: the viewer shows a clean car.
"""

import argparse
import functools
import hashlib
import http.server
import json
import threading
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

import numpy as np
from PIL import Image

from tool import bake, dds, fbx, parts, paths

DATA = paths.WORK / "viewer"
STOCK = DATA / "stock"
# The lighting, Poly Haven HDRIs (CC0): name -> (resolution, md5 from api.polyhaven.com/files/<name>).
# The user picked this studio look on 2026-09-24: the neutral studio by day, a moonlit sky at night.
HDRIS = {
    "studio_small_09": ("2k", "b056fea247bc84b81d2e0987d44c87d8"),
    "dikhololo_night": ("1k", "4a760813214ec4d97da8e1739bb616a5"),
}
HDRI_URL = "https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/{res}/{name}_{res}.hdr"
PORT = 8765
MESHES = (("Skin", "Skin_01"), ("Details", "Details_01"), ("Wheels", "Wheels_01"), ("Glass", "Glass_01"))
CODES = np.array([0, 32, 64, 96, 128, 160, 192, 224, 255])
SLOTS = ("Skin_B", "Skin_RM", "Skin_Coat", "Skin_AO",
         "Details_B", "Details_RM", "Details_N", "Details_I", "Details_Code", "Details_AO",
         "Wheels_B", "Wheels_RM", "Wheels_N", "Wheels_AO",
         "Glass_T", "Glass_I", "Glass_Code", "Glass_AO")
NO_STOCK = {"Skin_Coat"}  # left out, the viewer varnishes everything, as the game does


def _stale(target, *sources):
    """True when target is missing or older than any source (this file counts as a source)."""
    if not target.exists():
        return True
    newest = max(p.stat().st_mtime for p in (*sources, Path(__file__)) if p.exists())
    return target.stat().st_mtime < newest


# ---- The car ----


def export_mesh():
    """car.bin: per mesh, one vertex per triangle corner (no index), with float32 positions,
    normals, UVs and the part id of its triangle (car/parts.json). Also parts.json and, per
    texture set, <Set>_Shared.png: the texels several parts share, for the viewer's overlay."""
    out_json, out_bin = DATA / "car.json", DATA / "car.bin"
    sources = (fbx.CACHE, paths.FBX, parts.PARTS_JSON, parts.CACHE, paths.REPO / "tool" / "naming.py")
    if not _stale(out_json, *sources):
        return
    meshes = fbx.meshes()
    p = parts.load()
    lift = -min(m["positions"][:, 1].min() for m in meshes.values())  # wheels on the floor
    blob, index, offset = [], [], 0
    for name, mesh_name in MESHES:
        m = meshes[mesh_name]
        corners = m["tri_vertex"].reshape(-1)
        off = p.mesh_offset[name]
        part = np.repeat(p.tri_part[off:off + len(m["tri_vertex"])], 3)
        arrays = {
            "position": ((m["positions"][corners] + [0, lift, 0]) * 0.01).astype(np.float32),
            "normal": m["tri_normal"].reshape(-1, 3).astype(np.float32),
            "uv": m["tri_uv"].reshape(-1, 2).astype(np.float32),
            "part": part.astype(np.float32),
        }
        entry = {"name": name, "vertices": len(corners)}
        for field, a in arrays.items():
            entry[field] = offset
            blob.append(a.tobytes())
            offset += a.nbytes
        index.append(entry)
    DATA.mkdir(parents=True, exist_ok=True)
    out_bin.write_bytes(b"".join(blob))
    (DATA / "parts.json").write_text(parts.PARTS_JSON.read_text())
    for tset, (w, h) in parts.BAKE_SIZE.items():
        b = bake.bake(tset, w, h)
        shared = ((b["tri"] >= 0) & (b["count"] > 1)).astype(np.uint8) * 255
        Image.fromarray(shared, "L").save(DATA / f"{tset}_Shared.png", compress_level=1)
    out_json.write_text(json.dumps({"units": "m", "lift_cm": float(lift), "meshes": index}, indent=1))


def ensure_hdri():
    DATA.mkdir(parents=True, exist_ok=True)
    for name, (res, md5) in HDRIS.items():
        target = DATA / f"{name}.hdr"
        if target.exists():
            continue
        url = HDRI_URL.format(name=name, res=res)
        data = urllib.request.urlopen(url, timeout=120).read()
        if hashlib.md5(data).hexdigest() != md5:
            raise ValueError(f"{url}: unexpected md5")
        target.write_bytes(data)


# ---- Textures ----


def _u8(a):
    if a.dtype == np.uint8:
        return a
    return np.clip(np.rint(np.asarray(a, np.float64) * 255), 0, 255).astype(np.uint8)


def _channels(a):
    return a if a.ndim == 3 else a[..., None]


def convert(tex_name, image):
    """One game texture (decoded uint8, or float 0..1) -> {slot: PIL image}. Unshown ones -> {}."""
    a = _channels(_u8(image))
    h, w = a.shape[:2]
    tset, kind = tex_name.split("_", 1)
    if kind == "B":
        return {tex_name: Image.fromarray(np.ascontiguousarray(a[..., :3]), "RGB")}
    if kind == "R":  # ATI2: roughness, metalness. Stock Wheels_R is ATI1: roughness only.
        rm = np.zeros((h, w, 3), np.uint8)
        rm[..., 0] = 255
        rm[..., 1] = a[..., 0]
        rm[..., 2] = a[..., 1] if a.shape[2] > 1 else 0
        return {f"{tset}_RM": Image.fromarray(rm, "RGB")}
    if kind == "CoatR":
        coat = np.zeros((h, w, 3), np.uint8)
        coat[..., 0] = 255 - a[..., 0]  # three.js reads the clear-coat amount from R
        return {"Skin_Coat": Image.fromarray(coat, "RGB")}
    if kind == "N":
        xy = a[..., :2].astype(np.float64) / 255 * 2 - 1
        z = np.sqrt(np.clip(1 - (xy**2).sum(-1, keepdims=True), 0, 1))
        return {tex_name: Image.fromarray(_u8(np.concatenate([xy, z], -1) * 0.5 + 0.5), "RGB")}
    if kind == "I":
        code = CODES[np.digitize(a[..., 3], (CODES[1:] + CODES[:-1]) / 2)].astype(np.uint8)
        return {tex_name: Image.fromarray(np.ascontiguousarray(a[..., :3]), "RGB"),
                f"{tset}_Code": Image.fromarray(code, "L")}
    if tex_name == "Glass_T":
        return {tex_name: Image.fromarray(np.ascontiguousarray(a[..., :4]), "RGBA")}
    if kind == "AO":
        return {tex_name: Image.fromarray(np.ascontiguousarray(a[..., 0]), "L")}
    return {}  # dirt masks, Glass_D (the game reads Glass_T), Wheels_I (stock is empty)


def _write_slots(folder, textures):
    """textures: {game texture name: array}. Writes one PNG per slot; returns the slots written."""
    folder.mkdir(parents=True, exist_ok=True)
    written = []
    for tex_name, image in textures.items():
        for slot, im in convert(tex_name, image).items():
            im.save(folder / f"{slot}.png", compress_level=1)
            written.append(slot)
    return written


def ensure_stock():
    stamp = STOCK / "stock.json"
    sources = sorted(paths.MODEL_SOURCE.glob("*.dds"))
    if not _stale(stamp, *sources):
        return
    textures = {f.stem: dds.decode(f) for f in sources if f.stem != "Wheels_I"}
    slots = _write_slots(STOCK, textures)
    stamp.write_text(json.dumps(sorted(slots)))


def export_skin(name, textures):
    """Show a skin in the viewer. textures: {game texture name ("Skin_B", ...): array in the game's
    layout, uint8 or float 0..1}. Anything left out shows the stock texture, as in the game."""
    folder = DATA / "skins" / name
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*.png"):
        old.unlink()
    own = set(_write_slots(folder, textures))
    stock = set(json.loads((STOCK / "stock.json").read_text()))
    urls = {}
    for slot in SLOTS:
        if slot in own:
            urls[slot] = f"skins/{name}/{slot}.png"
        elif slot in stock and slot not in NO_STOCK:
            urls[slot] = f"stock/{slot}.png"
        else:
            urls[slot] = None
    (folder / "skin.json").write_text(json.dumps({"name": name, "textures": urls, "own": sorted(own)}, indent=1))


def skin_from_build(name):
    """Show a built skin (build/<name>/*.dds): the top level of each file in its zip."""
    folder = paths.BUILD / name
    files = sorted(folder.glob("*.dds"))
    if not files:
        raise FileNotFoundError(f"No built skin called {name} in {paths.BUILD}")
    export_skin(name, {f.stem: dds.decode(f) for f in files})


def prepare(name):
    export_mesh()
    ensure_hdri()
    ensure_stock()
    skin_from_build(name)


# ---- Serving ----


class Handler(http.server.SimpleHTTPRequestHandler):
    # Windows can map .js to text/plain in the registry, and browsers refuse modules served that way.
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".js": "text/javascript", ".json": "application/json", ".html": "text/html",
                      ".png": "image/png", ".bin": "application/octet-stream", ".hdr": "application/octet-stream",
                      ".ttf": "font/ttf"}

    def translate_path(self, path):
        path = urllib.parse.urlsplit(path).path
        if path.startswith("/data/"):
            self.directory, path = str(DATA), path[len("/data"):]
        else:
            self.directory = str(paths.REPO / "viewer")
        return super().translate_path(path)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass


def start_server(port=PORT):
    """Serve in a background thread. port 0 picks a free one. Returns the server."""
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()
    prepare(args.name)
    url = f"http://localhost:{args.port}/?skin={urllib.parse.quote(args.name)}"
    try:
        server = start_server(args.port)
    except OSError:
        server = None  # a viewer is already serving on this port; it reads the same folders
    print(f"viewer: {url}", flush=True)
    if not args.no_open:
        webbrowser.open(url)
    if server:
        threading.Event().wait()


if __name__ == "__main__":
    main()
