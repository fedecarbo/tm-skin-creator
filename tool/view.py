"""The 3D viewer's data: prepares what the Lab's page in viewer/ loads (tool/server.py serves it).

    python -m tool.view <name>                the skin as last shown (else its last build), serve, open
                                              the browser
    python -m tool.view <name> --no-open      same, without opening the browser

The work folder's viewer/ folder (served as /data/), all rebuildable:
  car.json, car.bin    the four meshes, in metres, with the car's wheels at y = 0, each
                       corner tagged with its part (and on Details, its speed-display
                       segment); parts.json lists the parts
  <Set>_Shared.png     the texels that several parts share (mirrored or repeated)
  <Set>_Parts.png,     the Lab's UV map: which part covers each texel, every part's
  uvmap.json           words and numbers, the room (export_uvmap)
  template/            the Lab's UV map template: the model's own lines on the maps and on the car
                       (export_template), the car a skin of its own too, skins/Template
  <name>.hdr           the lighting by day and at night, Poly Haven HDRIs (CC0), see HDRIS
  floor/               the studio floor's grain (ambientCG, CC0), see FLOOR_SETS
  stock/*.png          Nadeo's stock textures, for anything a skin leaves out
  skins/<name>/        one skin's textures, and skin.json with the URL of every slot
  skins/<name>/steps/  the Lab's car: the car at the end of each step of the design,
                       at half size, and steps.json (export_steps); studio.json names
                       the skin Claude painted last, which the Lab follows

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
import hashlib
import io
import json
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

from tool import bake, dds, fbx, finishes, parts, paths

DATA = paths.WORK / "viewer"
STOCK = DATA / "stock"
# The lighting, Poly Haven HDRIs (CC0): name -> (resolution, md5 from api.polyhaven.com/files/<name>).
# A sky for each of the four moods, like the game's (viewer.js: LOOKS).
HDRIS = {
    # the day: a bright sky with white clouds and a high sun, as the game's
    "kloofendal_48d_partly_cloudy_puresky": ("2k", "2eba3a4d7eeb23cbfbeca364c97e7980"),
    "dikhololo_night": ("1k", "4a760813214ec4d97da8e1739bb616a5"),
    "belfast_sunset_puresky": ("1k", "38890f597727936a44d17a97f7f73354"),
    "qwantani_dusk_2_puresky": ("1k", "d400530e33f683654e70b4a087b6fe8d"),
}
HDRI_URL = "https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/{res}/{name}_{res}.hdr"
# The studio floor's grain (viewer/studio.js, GRAIN, 2026-09-27): ambientCG sets (CC0), the 1K JPG
# zips (the grain is a metre a repeat), of which the viewer reads the colour and the relief,
# unpacked into DATA/floor/<asset>/.
FLOOR_SETS = ("Rubber004",)
FLOOR_MAPS = ("Color", "NormalGL")
FLOOR_URL = "https://ambientcg.com/get?file={asset}_1K-JPG.zip"
SLOTS = ("Skin_B", "Skin_RM", "Skin_Coat", "Skin_AO",
         "Details_B", "Details_RM", "Details_N", "Details_I", "Details_Code", "Details_AO",
         "Wheels_B", "Wheels_RM", "Wheels_N", "Wheels_AO",
         "Glass_T", "Glass_I", "Glass_Code", "Glass_AO")
NO_STOCK = {"Skin_Coat"}  # left out, the viewer varnishes everything, as the game does


def _stale(target, *sources, this_file=True):
    """True when target is missing or older than any source (this file counts as a source, unless
    this_file is False)."""
    if not target.exists():
        return True
    newest = max(p.stat().st_mtime for p in (*sources, *([Path(__file__)] if this_file else [])) if p.exists())
    return target.stat().st_mtime < newest


# ---- The car ----


def digit_segments(p, n_tris):
    """Per Details triangle: 0, or 1 + 7 * digit + segment on the speed display, so the viewer
    lights whole bars. Digit 0 is the hundreds, on the car's left (+x); segments
    0..6 are a..g as read from behind: top, upper right, lower right, bottom, lower left, upper
    left, middle. Each bar is three long thin pieces (its face and two bevels); the backing
    between the bars isn't long, and stays 0."""
    from tool import segment
    seg = segment.segments()
    tris = np.flatnonzero(p.tri_mask("Details", "digit display"))
    piece = seg["piece"][p.mesh_offset["Details"] + tris]
    bars = []
    for q in np.unique(piece):
        (x0, y0, _), (x1, y1, _) = seg["piece_lo"][q], seg["piece_hi"][q]
        if max(x1 - x0, y1 - y0) > 2 * min(x1 - x0, y1 - y0):
            cx, cy, _ = seg["piece_centroid"][q]
            bars.append((q, cx, cy, x1 - x0 > y1 - y0, 0 if cx > 5 else 2 if cx < -5 else 1))
    out = np.zeros(n_tris, np.float32)
    for k in range(3):
        mine = [b for b in bars if b[4] == k]
        xc = np.mean([b[1] for b in mine])
        yc = np.mean([b[2] for b in mine])
        for q, cx, cy, flat, _ in mine:
            if flat:
                s = 0 if cy > yc + 2 else 3 if cy < yc - 2 else 6
            else:  # the car's left (+x) is the reader's left
                s = (5 if cy > yc else 4) if cx > xc else (1 if cy > yc else 2)
            out[tris[piece == q]] = 1 + 7 * k + s
    return out


def export_mesh():
    """car.bin: per mesh, one vertex per triangle corner (no index), with float32 positions,
    normals, UVs and the part id of its triangle (car/parts.json); on Details also its segment of
    the speed display (digit_segments). Also parts.json and, per texture set, <Set>_Shared.png:
    the texels several parts share, for the viewer's overlay. And the Lab's rooms' data, and its template."""
    export_uvmap()
    export_template()
    out_json, out_bin = DATA / "car.json", DATA / "car.bin"
    sources = (fbx.CACHE, paths.FBX, parts.PARTS_JSON, parts.CACHE, paths.REPO / "tool" / "naming.py")
    if not _stale(out_json, *sources):
        return
    meshes = fbx.meshes()
    p = parts.load()
    lift = -min(m["positions"][:, 1].min() for m in meshes.values())  # wheels on the floor
    blob, index, offset = [], [], 0
    for name, mesh_name in fbx.MESH_OF.items():
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
        if name == "Details":
            arrays["digit"] = np.repeat(digit_segments(p, len(m["tri_vertex"])), 3)
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
    _json(out_json, {"units": "m", "lift_cm": float(lift), "meshes": index})


UVMAP_VERSION = 1  # bump when export_uvmap or _surfaces change what they write


def export_uvmap():
    """The Lab's UV map room (viewer/lab-rooms.js), from the tool's own parts and texel coverage:
      <Set>_Parts.png  per texel of the <Set>_Shared.png grid, the part that covers it most
                       (coverage.owners at the paint's size), R + 256 G = the part's id + 1
      <Set>_Surfaces.png per texel of that grid, the surface it's on, R + 256 G = its number + 1:
                       a surface is a shape of its own on the flat map (texels that touch), what
                       the Lab's UV map picks (surfaces(), below); grown 2 texels into the gaps
                       so the car lights its edges too
      uvmap.json       each map (its paint's size, the grid, its assemblies), each part in
                       words (parts.Parts: its label, whose paint it shares, the line to copy for
                       Claude) and numbers (its share of the map, dots per cm, cm2 on the car), and
                       the Lab's rooms (tool/rooms.py: the UV map, its maps, parts and camera)"""
    from tool import coverage, paintbox, rooms
    out, stamp = DATA / "uvmap.json", DATA / "uvmap.key"
    here = paths.REPO / "tool"
    # Rebuilt (23 s) when the parts, their coverage or words, or the rooms change, not after every
    # edit to paintbox.py or this file, the two most edited: of those it takes only the paint's
    # sizes, and UVMAP_VERSION for its own code.
    key = hashlib.sha1(repr((UVMAP_VERSION, paintbox.SIZES)).encode()).hexdigest()[:12]
    if (not _stale(out, parts.PARTS_JSON, here / "parts.py", here / "coverage.py", here / "rooms.py", this_file=False)
            and stamp.exists() and stamp.read_text() == key):
        return
    p = parts.load()
    maps, rows = [], []
    for tset, (gw, gh) in parts.BAKE_SIZE.items():
        pw, ph = paintbox.SIZES[tset]
        cov = coverage.load(p, tset, pw, ph)
        sx, sy = pw // gw, ph // gh
        own = cov.owners()[sy // 2::sy, sx // 2::sx] + 1
        DATA.mkdir(parents=True, exist_ok=True)
        Image.fromarray(np.stack([own & 255, own >> 8, np.zeros_like(own)], -1).astype(np.uint8), "RGB").save(DATA / f"{tset}_Parts.png")
        labels, grown, surfaces = _surfaces(own, *cov.sets(sx, sy, least=191))
        Image.fromarray(np.stack([grown & 255, grown >> 8, np.zeros_like(grown)], -1).astype(np.uint8), "RGB").save(DATA / f"{tset}_Surfaces.png")
        twins = cov.twins()
        maps.append({"set": tset, "size": [pw, ph], "grid": [gw, gh], "parts": len(cov.ids), "surfaces": surfaces,
                     "holds": list(dict.fromkeys(p.instances[i]["parent"] for i in cov.ids))})
        for i in cov.ids:
            inst = p.instances[i]
            texels, _, others = twins[i]
            rows.append({"id": i, **{k: inst[k] for k in ("name", "group", "parent", "side", "end", "mesh")},
                         "label": p.label(i), "tag": p.tag(i), "line": p.line(i, twins), "paint": p.share_words(i, twins),
                         "twins": sorted(others), "pct": round(100 * texels / (pw * ph), 2),
                         "sharp": round((texels / inst["area_cm2"]) ** 0.5, 1) if inst["area_cm2"] else 0,
                         "area": round(inst["area_cm2"])})
    assemblies = {a["name"]: a["about"] for a in json.loads(parts.PARTS_JSON.read_text())["assemblies"]}
    lab_rooms = rooms.rooms(p)
    out.write_text(json.dumps({"maps": maps, "assemblies": assemblies, "rooms": lab_rooms,
                               "parts": sorted(rows, key=lambda r: r["id"])}, indent=1))
    stamp.write_text(key)


TEMPLATE = DATA / "template"
TEMPLATE_VERSION = 4  # bump when export_template changes what it draws
TEMPLATE_KEY = {"mesh": (58, 58, 62), "outward": (255, 120, 20), "inward": (130, 80, 255), "crease": (240, 190, 0),
                "opening": (225, 45, 45), "cut": (0, 160, 230)}  # the colours of the mesh, of its edges where the body
# bends (meshlines.mesh: outward, a rounded edge; inward, an indentation) and of meshlines.template's kinds, as the
# Lab's key names them
BEND = (1.0, 12.0)  # degrees: where an edge's colour starts to turn from the mesh's to its bend's, and where it's full
TEMPLATE_LIGHT = np.array([0.35, 0.85, 0.4]) / np.linalg.norm([0.35, 0.85, 0.4])  # the shape's light: high, front left


def export_template():
    """The Lab's UV map template (viewer/lab-rooms.js, Template), from the model alone (meshlines.mesh, template):
      template/<Set>_Map.png  each map at the Lab's grid: the body's shape (clay lit from above, from the bake's
                              normals), the model's mesh (every edge of its triangles, coloured where the body bends
                              across it), its lines in their colours (TEMPLATE_KEY)
      template/<slot>.png     the car dressed in it: each map mid-grey clay, matte, with the same mesh and lines
      template/<Set>_Mesh.png the same mesh and lines alone, clear between them (colour premultiplied by its alpha):
                              what the Lab's Mesh button lays over any car's paint (viewer.js, addMesh)
      template.json           those slots' URLs, the stock for the rest, as skin.json's, and the key
    and skins/Template/skin.json, the same car as a skin the viewer opens by name (car/map/model.jpg: `PY -m tool.snap
    Template --body`)."""
    from tool import meshlines, paintbox
    stamp = TEMPLATE / "template.json"
    key = hashlib.sha1(repr((TEMPLATE_VERSION, TEMPLATE_KEY, BEND, meshlines.SHARP, meshlines.SEWN,
                             paintbox.SIZES)).encode()).hexdigest()[:12]
    if (not _stale(stamp, fbx.CACHE, paths.REPO / "tool" / "meshlines.py", this_file=False)
            and json.loads(stamp.read_text()).get("key") == key):
        _template_skin()
        return
    ensure_stock()
    TEMPLATE.mkdir(parents=True, exist_ok=True)
    car = {}
    for tset, (gw, gh) in parts.BAKE_SIZE.items():
        mesh, lines = meshlines.mesh(tset), meshlines.template(tset)
        # each picture drawn at twice its size and brought down, so its lines are smooth
        b = bake.bake(tset, gw, gh)
        lit = np.clip(b["normal"] @ TEMPLATE_LIGHT, 0, 1)
        shade = 0.35 + 0.65 * (0.5 * lit + 0.5 * (0.5 + 0.5 * b["normal"][..., 1]))
        rgb = np.where((b["tri"] >= 0)[..., None], shade[..., None] * [0.93, 0.92, 0.9] * 255, [12, 12, 14])
        img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB")
        img = _template_lines(img.resize((2 * gw, 2 * gh), Image.BILINEAR), mesh, lines, 2 * gw / 4096, 110)
        img.resize((gw, gh), Image.LANCZOS).save(TEMPLATE / f"{tset}_Map.png", compress_level=1)
        if tset != "Glass":  # the glass keeps its own tint on the car
            pw, ph = paintbox.SIZES[tset]
            clay = Image.new("RGB", (2 * pw, 2 * ph), (150, 150, 148))  # mid grey: light clay washes out under the studio's light
            car[f"{tset}_B"] = np.asarray(_template_lines(clay, mesh, lines, 2 * pw / 4096, 255).resize((pw, ph), Image.LANCZOS))
            over = _template_lines(Image.new("RGBA", (2 * pw, 2 * ph), (0, 0, 0, 0)), mesh, lines, 2 * pw / 4096, 170)
            over = np.asarray(over.resize((pw, ph), Image.LANCZOS)).astype(np.uint16)
            over[..., :3] = over[..., :3] * over[..., 3:] // 255  # premultiplied, so the GPU blends its edges cleanly
            Image.fromarray(over.astype(np.uint8), "RGBA").save(TEMPLATE / f"{tset}_Mesh.png", compress_level=1)
            matte = np.zeros((8, 8, 2), np.uint8)
            matte[..., 0] = 235
            car[f"{tset}_R"] = matte
    car["Skin_CoatR"] = np.full((8, 8, 1), 255, np.uint8)  # no varnish: the lines read under the studio's light
    own = set(_write_slots(TEMPLATE, car))
    stock = set(json.loads((STOCK / "stock.json").read_text()))
    urls = {slot: f"template/{slot}.png" if slot in own else f"stock/{slot}.png" if slot in stock and slot not in NO_STOCK
            else None for slot in SLOTS}
    _json(stamp, {"key": key, "textures": urls, "colours": {k: "#%02x%02x%02x" % c for k, c in TEMPLATE_KEY.items()},
                  "mesh": {tset: f"template/{tset}_Mesh.png" for tset in parts.BAKE_SIZE if tset != "Glass"}})
    _template_skin()


def _template_skin():
    """The template's car as a skin of its own, Template."""
    doc = json.loads((TEMPLATE / "template.json").read_text())
    _json(DATA / "skins" / "Template" / "skin.json", {"name": "Template", "textures": doc["textures"], "own": []})


def _template_lines(img, mesh, lines, scale, alpha):
    """The model's mesh (meshlines.mesh: every edge of its triangles, grey where the body is flat, turning to the bend's
    colour over BEND) and its lines (meshlines.template) drawn on a map's picture, the flat mesh at `alpha` and the
    bends opaque (over an RGB picture, blended; on an RGBA one, written as they are); widths in pixels of a 4096 map,
    times scale."""
    from PIL import ImageDraw
    w, h = img.size
    dr = ImageDraw.Draw(img, "RGBA")  # an RGB picture blends; an RGBA one takes each line's colour and alpha
    _, uv, bend = mesh
    xy = uv.astype(np.float64) * [w, -h] + [0, h]
    t = np.clip((np.abs(bend) - BEND[0]) / (BEND[1] - BEND[0]), 0, 1)
    grey = np.asarray(TEMPLATE_KEY["mesh"], np.float64)
    hue = np.where((bend > 0)[:, None], TEMPLATE_KEY["outward"], TEMPLATE_KEY["inward"])
    colour = np.rint(np.c_[grey + (hue - grey) * t[:, None], alpha + (255 - alpha) * t]).astype(int)
    width = max(1, round(2.5 * scale))
    for k in np.argsort(t, kind="stable"):  # the flat edges first, those that bend over them
        dr.line([tuple(xy[k, 0]), tuple(xy[k, 1])], fill=tuple(colour[k]), width=width)
    for kind, wide in (("cut", 6), ("opening", 6), ("crease", 4.5)):
        for p, q in lines[kind][1].astype(np.float64) * [w, -h] + [0, h]:
            dr.line([tuple(p), tuple(q)], fill=TEMPLATE_KEY[kind], width=max(2, round(wide * scale)))
    return img


SURFACE_LEAST = 16


def _surfaces(own, on, sets):
    """The flat map's surfaces: the shapes the Lab outlines on it, each a run of touching texels with
    the same part on top (own: the owners, + 1), so what's seen is what's picked (the user,
    2026-09-26: "in the 3d to select parts, but in the uv map to be able to select surfaces").
    Touching texels alone merged the body shell with the cockpit surround, and every tyre's paint
    into one. on, sets: the parts covering each texel by 3/4 (coverage.sets), twins and overlaps;
    a part counts on a surface from SURFACE_LEAST texels (a seam's texels are half each side's).
    Returns the labels (0 none, else the surface's number + 1), the same grown 2 texels into the
    gaps, and per surface {parts: ids on it, texels}."""
    from scipy import ndimage
    labels = np.zeros(own.shape, np.int32)
    n = 0
    for i, box in enumerate(ndimage.find_objects(own), start=1):
        if box is None:
            continue
        lab, k = ndimage.label(own[box] == i)
        labels[box][lab > 0] = lab[lab > 0] + n
        n += k
    if n >= 65535:
        raise ValueError(f"{n} surfaces: more than the Surfaces.png can number")
    dist, (iy, ix) = ndimage.distance_transform_edt(labels == 0, return_indices=True)
    grown = np.where(dist <= 2, labels[iy, ix], 0)
    k = (labels > 0) & (on >= 0)
    count = {}
    pairs, n_on = np.unique(np.stack([labels[k], on[k]], 1), axis=0, return_counts=True)
    for (lab, s), c in zip(pairs.tolist(), n_on.tolist()):
        for i in sets[s]:
            count[lab, i] = count.get((lab, i), 0) + c
    parts_of = [set() for _ in range(n + 1)]
    for (lab, i), c in count.items():
        if c >= SURFACE_LEAST:
            parts_of[lab].add(i)
    top = ndimage.labeled_comprehension(own, labels, np.arange(1, n + 1), np.max, np.int32, 0)
    for lab, o in enumerate(top.tolist(), start=1):  # its part on top, always
        parts_of[lab].add(o - 1)
    texels = np.bincount(labels.reshape(-1), minlength=n + 1)
    return labels, grown, [{"parts": sorted(parts_of[i]), "texels": int(texels[i])} for i in range(1, n + 1)]


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


def ensure_floor():
    for asset in FLOOR_SETS:
        folder = DATA / "floor" / asset
        wanted = [f"{asset}_1K-JPG_{m}.jpg" for m in FLOOR_MAPS]
        if all((folder / w).exists() for w in wanted):
            continue
        request = urllib.request.Request(FLOOR_URL.format(asset=asset), headers={"User-Agent": "tm-skin-creator"})
        with zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(request, timeout=180).read())) as z:
            folder.mkdir(parents=True, exist_ok=True)
            for w in wanted:
                (folder / w).write_bytes(z.read(w))


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
        code = finishes.glow_codes(a[..., 3])
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


CLAY = DATA / "clay"


def ensure_clay():
    """Modelling clay for the viewer (the Lab's lines room shows the body in it so its shape reads):
    the body and the inner car matte, no varnish, a mid grey (the Studio's near-white clay washes
    out under the studio's light: the creases vanish). The slots it covers are in
    clay.json; a page lays them over the stock ones."""
    stamp = CLAY / "clay.json"
    if not _stale(stamp):
        return
    n = 64
    colour = np.full((n, n, 3), (128, 128, 126), np.uint8)
    rm = np.zeros((n, n, 2), np.uint8)
    rm[..., 0] = 235  # roughness: matte
    rm[..., 1] = 0    # no metal
    textures = {"Skin_B": colour, "Skin_R": rm, "Skin_CoatR": np.full((n, n, 1), 255, np.uint8),
                "Details_B": colour, "Details_R": rm}
    slots = _write_slots(CLAY, textures)
    stamp.write_text(json.dumps(sorted(slots)))


def ensure_stock():
    ensure_clay()
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
        if old.name != "thumb.png":  # the gallery's picture (tool/gallery.py)
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
    _json(folder / "skin.json", {"name": name, "textures": urls, "own": sorted(own)})


# ---- The Lab's Studio: the car at the end of each step of a design (paintbox.Skin.step) ----


def start_steps(name):
    """A design is about to be painted: clear its old frames, and point the Lab's car at it."""
    import shutil
    ensure_stock()
    shutil.rmtree(DATA / "skins" / name / "steps", ignore_errors=True)
    _json(DATA / "studio.json", {"skin": name, "stamp": time.time()})


def save_frame(name, k, slot, image, digest):
    """One slot's picture for step k; returns its URL, which changes with the picture."""
    folder = DATA / "skins" / name / "steps" / str(k)
    folder.mkdir(parents=True, exist_ok=True)
    image.save(folder / f"{slot}.png", compress_level=1)
    return f"skins/{name}/steps/{k}/{slot}.png?v={digest}"


def frame_urls(own):
    """A frame's URL for every slot: its own pictures ({slot: url}), else the stock ones (as skin.json)."""
    stock = set(json.loads((STOCK / "stock.json").read_text())) if (STOCK / "stock.json").exists() else set()
    return {slot: own.get(slot) or (f"stock/{slot}.png" if slot in stock and slot not in NO_STOCK else None) for slot in SLOTS}


def export_steps(name, steps, painting, clay=None):
    """steps.json: each step's name, what it does, the user's words, what it paints, how to look
    at it, the line to copy for Claude, and the URL of every slot of its frame (its own pictures,
    else the stock ones, as skin.json); a step still being painted has none yet. clay: when the
    design is done, the parts still in clay, [(instance id, name)] (Skin.still_clay; None for a
    design that didn't start from clay)."""
    n = len(steps)
    out = []
    for k, st in enumerate(steps):
        title = ("The start" if n > 1 else "The design") if st.get("implicit") else st["name"]
        urls = frame_urls(st["textures"]) if "textures" in st else None
        out.append({"name": title, "does": st["does"], "words": st["words"], "look": st["look"], "paints": st["paints"],
                    "line": f"{name}, step {k} of {n - 1}: {title}", "frame": st.get("frame"), "textures": urls})
    doc = {"name": name, "stamp": time.time(), "painting": painting, "steps": out}
    if clay is not None:
        doc["clay"] = [{"id": i, "name": n} for i, n in clay]
    _json(DATA / "skins" / name / "steps.json", doc)


def _json(path, doc):
    """A JSON file the pages read, written whole (paths.write)."""
    paths.write(path, json.dumps(doc, indent=1))


def skin_from_build(name):
    """Show a built skin (build/<name>/*.dds): the top level of each file in its zip."""
    folder = paths.BUILD / name
    files = sorted(folder.glob("*.dds"))
    if not files:
        raise FileNotFoundError(f"No built skin called {name} in {paths.BUILD}")
    export_skin(name, {f.stem: dds.decode(f) for f in files})


def prepare(name):
    """Everything the viewer loads, and the skin: as `tool.skin show` last put it there (the paint
    box exports it itself), else from its last build, a skin made before the paint box."""
    export_mesh()
    ensure_hdri()
    ensure_floor()
    ensure_stock()
    if not (DATA / "skins" / name / "skin.json").exists():
        skin_from_build(name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()
    prepare(args.name)
    from tool import server
    server.serve(f"?skin={urllib.parse.quote(args.name)}", "viewer", open_tab=not args.no_open)


if __name__ == "__main__":
    main()
