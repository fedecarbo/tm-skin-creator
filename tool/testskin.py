"""Checkpoint 1: loud test skins that show whether the game accepts our files.

    python -m tool.testskin            builds TSC_Test, TSC_Test_Sharp and TSC_Test_SkinOnly

What each one shows in game:
  body       +x side orange with "LEFT", -x side blue with "RIGHT", a white centre stripe,
             a chrome nose labelled CHROME with an arrow pointing forward, a matte engine
             cover labelled MATTE plus the test's name, and a numbered UV grid over everything
  details    yellow with a numbered grid; Nadeo's relief and glow layout kept, but the front
             lights glow cyan and the brake lights pink
  wheels     light grey with a numbered grid
  glass      Glass_D red and Glass_T green: the colour seen in game tells which file it reads
"""

import numpy as np
from PIL import Image

from tool import bake, dds, paint, pack, paths, preview, raster

ORANGE, BLUE, WHITE, INK = (1.0, 0.5, 0.0), (0.1, 0.4, 1.0), (1, 1, 1), (0.05, 0.05, 0.05)
SILVER, YELLOW, GREY = (0.85, 0.85, 0.87), (1.0, 0.85, 0.0), (0.88, 0.88, 0.88)
GLOSS, CHROME, MATTE, PLAIN = (0.25, 0.0), (0.0, 1.0), (1.0, 0.0), (0.5, 0.0)  # roughness, metalness
CYAN, PINK = (0.0, 1.0, 1.0), (1.0, 0.15, 0.8)
CODES = np.array([0, 32, 64, 96, 128, 160, 192, 224, 255])


def stock(name, size=None, resample=Image.BILINEAR):
    """Nadeo's stock texture, decoded, as float 0..1, resized to (w, h) if given."""
    a = dds.decode(paths.MODEL_SOURCE / f"{name}.dds")
    if size and (a.shape[1], a.shape[0]) != size:
        chans = [Image.fromarray(a[..., c] if a.ndim == 3 else a).resize(size, resample)
                 for c in range(a.shape[2] if a.ndim == 3 else 1)]
        a = np.stack([np.asarray(c) for c in chans], -1)
    return a.astype(np.float32) / 255


def grid_over(img, cells, strength=(0.35, 0.7)):
    h, w = img.shape[:2]
    lines, digits = paint.uv_grid(w, h, cells=cells)
    img = paint.mix(img, INK, lines * strength[0])
    return paint.mix(img, INK, digits * strength[1])


def skin_textures(size, label):
    b = bake.bake("Skin", size, size)
    pos, nrm, cov = b["position"], b["normal"], paint.covered(b)
    x, z = pos[..., 0], pos[..., 2]
    colour = np.zeros((size, size, 3), np.float32)
    colour[x > 2] = ORANGE
    colour[x < -2] = BLUE
    colour[np.abs(x) <= 2] = WHITE
    rm = np.zeros((size, size, 2), np.float32)
    rm[:] = GLOSS

    nose = cov & (z > 95) & (nrm[..., 1] > 0.35)
    cover = cov & (z < -35) & (nrm[..., 1] > 0.45)
    colour[nose] = SILVER
    rm[nose] = CHROME
    rm[cover] = MATTE

    up, fwd, top = (0, 1, 0), (0, 0, 1), (0, 1, 0)
    decals = []
    for sign, word in ((1, "LEFT"), (-1, "RIGHT")):
        img = paint.text_image(word, 240)
        decals.append(paint.project(b, img, (0, 47, -42), (0, 0, -sign), up, 26 * img.shape[1] / img.shape[0],
                                    (sign, 0, 0), where=(x * sign > 0)))
    arrow = paint.arrow_image(300, 90)
    decals.append(paint.project(b, arrow, (0, 0, 165), (-1, 0, 0), fwd, 16, top, where=nose))
    img = paint.text_image("CHROME", 200, font="bold")
    decals.append(paint.project(b, img, (0, 0, 112), (-1, 0, 0), fwd, 34, top, where=nose))
    img = paint.text_image(label, 240)
    decals.append(paint.project(b, img, (0, 0, -80), (-1, 0, 0), fwd, 60, top, where=cover))
    img = paint.text_image("MATTE", 200, font="bold")
    decals.append(paint.project(b, img, (0, 0, -125), (-1, 0, 0), fwd, 34, top, where=cover))
    ink = np.clip(sum(decals), 0, 1)
    colour = paint.mix(colour, INK, ink)
    rm[ink > 0.5] = GLOSS

    colour = grid_over(raster.fill_holes(colour, cov), 16)
    rm = raster.fill_holes(rm, cov)
    return {
        "Skin_B": (colour, "DXT1", {"srgb": True}),
        "Skin_R": (rm, "ATI2", {}),
        "Skin_CoatR": (np.zeros((16, 16, 1), np.float32), "ATI1", {}),
        "Skin_DirtMask": (stock("Skin_DirtMask"), "ATI1", {}),
    }


def details_textures(size):
    colour = grid_over(np.full((size, size, 3), YELLOW, np.float32), 16)
    rm = np.zeros((size, size, 2), np.float32)
    rm[:] = PLAIN
    glow = stock("Details_I", (size, size), resample=Image.NEAREST)
    code = CODES[np.digitize(glow[..., 3] * 255, (CODES[1:] + CODES[:-1]) / 2)]
    glow[..., 3] = code / 255
    glow[code == 128, :3] = CYAN
    glow[code == 0, :3] = PINK
    return {
        "Details_B": (colour, "DXT1", {"srgb": True}),
        "Details_R": (rm, "ATI2", {}),
        "Details_I": (glow, "DXT5", {"codes_in_alpha": True}),
        "Details_N": (stock("Details_N"), "ATI2", {"normal": True}),
        "Details_DirtMask": (stock("Details_DirtMask"), "ATI1", {}),
    }


def wheels_textures(w, h):
    colour = grid_over(np.full((h, w, 3), GREY, np.float32), 8)
    rm = np.zeros((h, w, 2), np.float32)
    rm[:] = PLAIN
    return {
        "Wheels_B": (colour, "DXT1", {"srgb": True}),
        "Wheels_R": (rm, "ATI2", {}),
        "Wheels_N": (stock("Wheels_N"), "ATI2", {"normal": True}),
        "Wheels_DirtMask": (stock("Wheels_DirtMask"), "ATI1", {}),
    }


def glass_textures(size):
    tint = stock("Glass_T", (size, size))
    tint[..., :3] = (0.0, 1.0, 0.0)
    return {
        "Glass_D": (np.full((size, size, 3), (1.0, 0.1, 0.1), np.float32), "DXT1", {"srgb": True}),
        "Glass_T": (tint, "DXT5", {}),
    }


# scale: sharpness of the painted textures. The dirt masks and normal maps are Nadeo's, kept at
# their own size: they're most of a zip's weight. only: keep just these textures.
VARIANTS = {
    "TSC_Test": {"scale": 1, "label": "TEST 2K", "sets": ("Skin", "Details", "Wheels", "Glass")},
    "TSC_Test_Sharp": {"scale": 2, "label": "TEST 4K", "sets": ("Skin", "Details", "Wheels", "Glass")},
    "TSC_Test_SkinOnly": {"scale": 1, "label": "SKIN ONLY", "sets": ("Skin",), "only": ("Skin_B", "Skin_R")},
}


def build(name):
    v = VARIANTS[name]
    s = v["scale"]
    textures = {}
    if "Skin" in v["sets"]:
        textures |= skin_textures(2048 * s, v["label"])
    if "Details" in v["sets"]:
        textures |= details_textures(2048 * s)
    if "Wheels" in v["sets"]:
        textures |= wheels_textures(512 * s, 1024 * s)
    if "Glass" in v["sets"]:
        textures |= glass_textures(1024)
    if "only" in v:
        textures = {k: t for k, t in textures.items() if k in v["only"]}
    out = paths.BUILD / name
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.dds"):
        old.unlink()
    previews = {}
    for tex_name, (image, fourcc, opts) in textures.items():
        levels = dds.write(out / f"{tex_name}.dds", image, fourcc, **opts)
        _, written = dds.read(out / f"{tex_name}.dds")
        errors = []
        for (w, h, data), src in zip(written, levels):
            got = dds.decode_level(fourcc, w, h, data).astype(int)
            want = src.astype(int)
            want = want[..., : got.shape[-1]] if got.ndim == 3 else want[..., 0]
            errors.append(np.abs(got - want))
        print(f"  {tex_name}.dds  {fourcc}  {levels[0].shape[1]}x{levels[0].shape[0]}  {len(levels)} mips  "
              f"decode error: mean {errors[0].mean():.2f}, worst {max(e.max() for e in errors)} (of 255)")
        if tex_name.endswith("_B") or tex_name == "Glass_D":
            previews[tex_name.split("_")[0]] = levels[0][..., :3]
    zip_path = pack.pack(name, out, pack.icon(v["label"], ORANGE, BLUE))
    print(f"  {zip_path.name}: {zip_path.stat().st_size / 1e6:.2f} MB")
    return zip_path, previews


def main():
    for name in VARIANTS:
        print(name)
        _, previews = build(name)
        if name == "TSC_Test":
            sheet = paths.BUILD / "TSC_Test_preview.png"
            preview.render_sheet(previews, sheet)
            print(f"  preview: {sheet}")


if __name__ == "__main__":
    main()
