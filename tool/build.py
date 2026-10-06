"""After the paint: a painted skin put in the viewer, kept, and built into the zip the game takes.

    python -m tool.build <name>    the DDS files and the zip from the skin's last show, to see the
                                   zip's size against ZIP_BUDGET (a trial build; installing builds it
                                   itself: tool/skin.py)

The zip's files are DDS with legacy headers and full mip chains (tool/dds.py), and an icon
(tool/pack.py).
"""

import argparse
import json

import numpy as np
from PIL import Image

from tool import dds, pack, paths, progress

# uploads may fail near 9 MB (a Nadeo developer, 2022); 8.45 and 8.65 MB zips have worked
ZIP_BUDGET = 8.5e6


def export_to_viewer(skin):
    """The viewer's data, and the skin in it as painted."""
    from tool import view
    textures = {name: arr for name, (arr, fourcc, opts) in skin.textures().items()}
    view.export_mesh()
    view.ensure_hdri()
    view.ensure_floor()
    view.ensure_stock()
    view.export_skin(skin.name, textures)


def save_painted(skin):
    """Keep the painted textures (uint8) for building the zip (build_zip). Each file replaced whole, the
    textures first."""
    out = paths.BUILD / skin.name
    out.mkdir(parents=True, exist_ok=True)
    arrays, meta = {}, {}
    for name, (arr, fourcc, opts) in skin.textures().items():
        arrays[name] = np.clip(np.rint(np.asarray(arr) * 255), 0, 255).astype(np.uint8)
        meta[name] = {"fourcc": fourcc, **opts}
    np.savez(out / "painted.tmp.npz", **arrays)
    (out / "painted.tmp.npz").replace(out / "painted.npz")
    paths.write(out / "painted.json", json.dumps({"textures": meta, "icon": skin.icon_colours, "notes": skin.notes,
                                                  "palette": skin.palette}, indent=1))
    return out


def build_zip(name):
    """DDS files and the zip from build/<name>/painted.npz, its icon the skin's thumb (squared) or,
    without one, its colours and name. A zip over ZIP_BUDGET gets its normal map, then its
    roughness maps, at half size (the stock's own 2048²), the tyres' first, then the largest,
    until it fits: the relief is drawn to read at 2048² (tool/relief.py); where a design kept the
    stock look the roughness maps hold nothing finer, and a finish on a whole part keeps its edges
    (the island's). A map halved on the way that fits at full size beside the ones halved after
    it ships at full size. Colour and glow always ship at full size. Which maps to halve is
    decided from each file's size in the first zip, so the zip is written again only once."""
    out = paths.BUILD / name
    meta = json.loads((out / "painted.json").read_text())
    data = np.load(out / "painted.npz")
    for old in out.glob("*.dds"):
        old.unlink()
    thumb = paths.SKINS / name / "thumb.png"
    if thumb.exists():
        im = Image.open(thumb).convert("RGB")
        side = min(im.size)
        icon_image = im.crop(((im.width - side) // 2, (im.height - side) // 2, (im.width + side) // 2, (im.height + side) // 2)).resize((256, 256), Image.LANCZOS)
    else:
        cols = meta.get("icon") or [(0.5, 0.5, 0.5)]
        icon_image = pack.icon(name[:8], cols[0], cols[-1])
    specs = {}
    progress.stage("Game files", total=len(meta["textures"]))
    for tex_name, spec in meta["textures"].items():
        spec = dict(spec)
        fourcc = spec.pop("fourcc")
        specs[tex_name] = (fourcc, spec)
        (out / f"{tex_name}.dds").write_bytes(dds.texture(data[tex_name].astype(np.float32) / 255, fourcc, **spec))
        progress.tick()
    zip_path = pack.pack(name, out, icon_image)
    whole = pack.sizes(zip_path)  # each file's size in the zip, compressed
    packed = dict(whole)
    normals = [t for t in specs if t.endswith("_N") and data[t].shape[0] > 2048]
    rough = [t for t in specs if t.endswith("_R")]
    halves = {}  # the maps at half size: their DDS file and its shape
    while pack.size(packed) > ZIP_BUDGET and (normals or rough):
        group = normals or rough
        # the tyres' roughness first: it carries only the lettering's shine, where the body's
        # carries a grain that needs its full size (TSC_CMYK_EndsInK, 2026-09-27)
        t = max(group, key=lambda t: (t.startswith("Wheels"), packed[f"{t}.dds"]))
        group.remove(t)
        progress.detail("Making the zip small enough")
        fourcc, spec = specs[t]
        half = dds.halve(data[t].astype(np.float32) / 255)
        halves[t] = dds.texture(half, fourcc, **spec), half.shape
        packed[f"{t}.dds"] = pack.deflated(halves[t][0])
    # the last map halved made it fit; an earlier one may fit at full size beside it (the tyres'
    # roughness on TSC_CMYK_EndsInK, whose body's had to be halved too), the later ones tried first
    for t in list(halves)[-2::-1]:
        full = {**packed, f"{t}.dds": whole[f"{t}.dds"]}
        if pack.size(full) <= ZIP_BUDGET:
            packed = full
            del halves[t]
    for t, (blob, shape) in halves.items():
        (out / f"{t}.dds").write_bytes(blob)
        print(f"{t} at {shape[1]}x{shape[0]}, to keep the zip under {ZIP_BUDGET / 1e6} MB")
    if halves:
        zip_path = pack.pack(name, out, icon_image)
    if zip_path.stat().st_size > ZIP_BUDGET:
        print(f"warning: the zip is still over {ZIP_BUDGET / 1e6} MB; the upload may fail")
    return zip_path


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("name")
    args = ap.parse_args()
    zip_path = build_zip(args.name)
    print(f"{zip_path.name}: {zip_path.stat().st_size / 1e6:.2f} MB (the budget: {ZIP_BUDGET / 1e6} MB)")


if __name__ == "__main__":
    main()
