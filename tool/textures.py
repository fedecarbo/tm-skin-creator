"""Photographed surfaces for the wear and material finishes, wrapped onto the car in 3D.

The pictures are tileable PBR texture sets from ambientCG (https://ambientcg.com), released
under CC0 (public domain): free for any use, no credit required. Each set is downloaded once
(the 1K JPG zip, about 5 MB) into the work folder and unpacked there.

    textures.wrap("rust", pos, nrm, colour, finish, params)   -> the look dict (tool/looks.py)

    python -m tool.textures search "snake skin"     candidates from ambientCG on one sheet
    python -m tool.textures add "snake skin" Leather008 --scale 40 [--mask] [--metal]
                                                     name it: "snake skin" then works in any phrase
Added sets live in the work folder's textures/library.json and join SETS on load, so the
library grows from the user's words: search, look at the sheet, add the one that fits.

Each entry says which picture to use and how: as a colour to lay over the paint (leather,
brushed metal), or as a mask that decides where the paint gives way to rust or bare metal, with
the picture's own colour there. The picture is laid on from the axis the surface faces most
(triplanar), so it never stretches or breaks at a seam. `scale` is how many cm one repeat of
the picture covers on the car (the photos are of about a metre of surface).
"""

import argparse
import io
import json
import urllib.parse
import urllib.request
import zipfile

import numpy as np
from PIL import Image

from tool import paths
from tool.noise import smoothstep

FOLDER = paths.WORK / "textures"
URL = "https://ambientcg.com/get?file={asset}_1K-JPG.zip"

# name -> asset id, and how the picture is used
SETS = {
    "rust": {"asset": "PaintedMetal011", "mode": "mask", "scale": 90,
             "about": "white paint with rust blooming through: the rust replaces the paint where the picture is rusty"},
    "chips": {"asset": "PaintedMetal012", "mode": "mask", "scale": 70,
              "about": "white paint with dark chips: bare metal shows where the picture is dark"},
    "brushed": {"asset": "Metal009", "mode": "overlay", "scale": 60, "about": "brushed steel"},
    "cast": {"asset": "Metal052C", "mode": "overlay", "scale": 60, "about": "rough cast iron"},
    "leather": {"asset": "Leather026", "mode": "overlay", "scale": 50, "about": "smooth black leather"},
    "quilted leather": {"asset": "Leather034A", "mode": "overlay", "scale": 60, "about": "diamond-stitched leather"},
}
LIBRARY_FILE = FOLDER / "library.json"
API = "https://ambientcg.com/api/v2/full_json?type=Material&limit={n}&include=previewData,tagData&q={q}"
THUMB = "https://acg-media.struffelproductions.com/file/ambientCG-Web/media/thumbnail/128-PNG/{asset}.png"
HEADERS = {"User-Agent": "TrackmaniaSkinChallenge/1.0"}
_cache = {}


def _load_library():
    if LIBRARY_FILE.exists():
        SETS.update(json.loads(LIBRARY_FILE.read_text(encoding="utf-8")))


_load_library()


def names():
    return list(SETS)


def _get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=120).read()


def search(words, n=12, sheet=None):
    """Candidates from ambientCG for some words: [(asset id, tags)], and a contact sheet of
    their thumbnails at build/textures_<words>.png for choosing by eye."""
    data = json.loads(_get(API.format(n=n, q=urllib.parse.quote(words))))
    found = [(a["assetId"], " ".join(a.get("tags") or [])) for a in data.get("foundAssets", [])]
    if found:
        from PIL import ImageDraw
        cols = min(6, len(found))
        rows = (len(found) + cols - 1) // cols
        im = Image.new("RGB", (cols * 140, rows * 150), (30, 30, 30))
        d = ImageDraw.Draw(im)
        for k, (asset, _) in enumerate(found):
            try:
                thumb = Image.open(io.BytesIO(_get(THUMB.format(asset=asset)))).convert("RGB").resize((128, 128))
            except Exception:
                continue
            x, y = (k % cols) * 140 + 6, (k // cols) * 150 + 4
            im.paste(thumb, (x, y))
            d.text((x, y + 130), asset, fill=(255, 255, 255))
        sheet = sheet or paths.BUILD / f"textures_{words.replace(' ', '_')}.png"
        sheet.parent.mkdir(parents=True, exist_ok=True)
        im.save(sheet)
    return found, sheet


def add(name, asset, scale=60, mask=False, metal=False, about=""):
    """Name a set so it works in phrases ("snake skin seats"). mask: the picture's dark parts
    replace the paint (chips); metal: it's a metal (metalness 1)."""
    key = " ".join(name.lower().split())
    entry = {"asset": asset, "mode": "mask" if mask else "overlay", "scale": scale, "about": about or asset,
             "metal": bool(metal)}
    lib = json.loads(LIBRARY_FILE.read_text(encoding="utf-8")) if LIBRARY_FILE.exists() else {}
    lib[key] = entry
    FOLDER.mkdir(parents=True, exist_ok=True)
    LIBRARY_FILE.write_text(json.dumps(lib, indent=1), encoding="utf-8")
    SETS[key] = entry
    fetch(asset)
    return key


def fetch(asset):
    folder = FOLDER / asset
    if not (folder / "Color.jpg").exists():
        FOLDER.mkdir(parents=True, exist_ok=True)
        print(f"textures: downloading {asset} from ambientCG (CC0)...", flush=True)
        data = _get(URL.format(asset=asset))
        folder.mkdir(exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for info in z.infolist():
                name = info.filename.rsplit("/", 1)[-1]
                for kind in ("Color", "Roughness", "Metalness", "NormalGL", "Displacement"):
                    if f"_{kind}." in name:
                        (folder / (kind + name[name.rfind("."):])).write_bytes(z.read(info))
    return folder


def load(name):
    """The set as float arrays: colour (h, w, 3) sRGB, roughness (h, w) or None, metalness or None."""
    if name in _cache:
        return _cache[name]
    folder = fetch(SETS[name]["asset"])

    def read(kind):
        for ext in (".jpg", ".png"):
            f = folder / (kind + ext)
            if f.exists():
                return np.asarray(Image.open(f).convert("L" if kind != "Color" else "RGB"), np.float32) / 255
        return None
    _cache[name] = {"colour": read("Color"), "roughness": read("Roughness"), "metalness": read("Metalness")}
    return _cache[name]


def sample(image, u, v):
    """Tiled nearest sample of image (h, w[, c]) at u, v in 0..1 repeats."""
    h, w = image.shape[:2]
    x = (np.floor(u * w).astype(np.int64)) % w
    y = (np.floor(v * h).astype(np.int64)) % h
    return image[y, x]


def triplanar_sample(image, pos, nrm, scale, power=6):
    """Lay a picture on the surface from each axis, blended by facing. Returns (n[, c])."""
    w = np.abs(nrm) ** power
    w /= np.maximum(w.sum(1, keepdims=True), 1e-6)
    out = None
    for axis in range(3):
        a, b = [k for k in range(3) if k != axis]
        sel = w[:, axis] > 0.01
        if not sel.any():
            continue
        s = sample(image, pos[sel, a] / scale, pos[sel, b] / scale)
        if out is None:
            out = np.zeros((len(pos),) + s.shape[1:], np.float32)
        out[sel] += (w[sel, axis][:, None] if s.ndim > 1 else w[sel, axis]) * s
    return out


def wrap(name, pos, nrm, colour, finish, params):
    spec = SETS[name]
    tex = load(name)
    scale = params.get("scale", spec["scale"])
    amount = float(params.get("amount", 0.5))
    n = len(pos)
    colour = np.asarray(colour, np.float32)
    pic = triplanar_sample(tex["colour"], pos, nrm, scale)
    rough = triplanar_sample(tex["roughness"], pos, nrm, scale) if tex["roughness"] is not None else None
    if spec["mode"] == "overlay":
        if params.get("own colour") or not params.get("tinted") and finish.colour is None:
            col = pic  # the photograph's own colours, as when the user names a set without a colour
        else:  # the picture's brightness pattern, tinted by the colour
            lum = pic @ np.array([0.3, 0.59, 0.11], np.float32)
            mean = float(lum.mean()) or 0.5
            col = np.clip(colour[None, :] * (lum / mean)[:, None], 0, 1)
        out = {"colour": col}
        if rough is not None:
            out["roughness"] = np.clip(finish.roughness + (rough - float(rough.mean())) * 0.8, 0, 1)
        return out
    # mask mode: where the picture isn't its paint (white), the paint gives way to the picture
    lum = pic @ np.array([0.3, 0.59, 0.11], np.float32)
    if name == "rust":
        wear = smoothstep(0.05, 0.25, pic[:, 0] - pic[:, 2])  # orange: red well above blue
    else:
        wear = smoothstep(0.8, 0.6, lum)  # the dark chips (the paint in the photo is ~0.87, the chips under 0.6)
    # `amount` moves the threshold: more wear at 1, hardly any at 0
    wear = np.clip(wear * (0.3 + 1.6 * amount) + (amount - 0.5) * 0.4, 0, 1)
    col = colour[None, :] * (1 - wear)[:, None] + pic * wear[:, None]
    if name == "chips":
        metal = np.array([0.5, 0.5, 0.52], np.float32) * (0.6 + 0.8 * lum)[:, None]
        col = colour[None, :] * (1 - wear)[:, None] + metal * wear[:, None]
    out = {"colour": np.clip(col, 0, 1),
           "varnish": np.full(n, finish.varnish, np.float32) * (1 - wear)}
    if name == "rust":
        out["roughness"] = np.full(n, finish.roughness, np.float32) * (1 - wear) + 0.9 * wear
        out["metalness"] = np.full(n, finish.metalness, np.float32) * (1 - wear)
    else:
        out["roughness"] = np.full(n, finish.roughness, np.float32) * (1 - wear) + 0.45 * wear
        out["metalness"] = np.full(n, finish.metalness, np.float32) * (1 - wear) + wear
    return out


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("search")
    a.add_argument("words")
    a.add_argument("-n", type=int, default=12)
    b = sub.add_parser("add")
    b.add_argument("name")
    b.add_argument("asset")
    b.add_argument("--scale", type=float, default=60)
    b.add_argument("--mask", action="store_true")
    b.add_argument("--metal", action="store_true")
    sub.add_parser("list")
    args = ap.parse_args()
    if args.cmd == "search":
        found, sheet = search(args.words, args.n)
        for asset, tags in found:
            print(f"{asset:<24} {tags[:80]}")
        print(f"sheet: {sheet}")
    elif args.cmd == "add":
        print("added", add(args.name, args.asset, args.scale, args.mask, args.metal))
    else:
        for k, v in SETS.items():
            print(f"{k:<20} {v['asset']:<20} {v['mode']:<8} {v.get('scale')} cm  {v.get('about', '')}")


if __name__ == "__main__":
    main()
