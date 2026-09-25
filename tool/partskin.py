"""Checkpoint 3: a test skin that paints named parts, to confirm the names in the game.

    python -m tool.partskin        builds TSC_Parts (and its preview sheet)

Every colour below lands on a part by name (car/parts.json). If the right thing changes colour
in the game, the name is right. Textures the test doesn't paint stay stock.
"""

import numpy as np

from tool import bake, dds, pack, parts, paths, preview, raster
from tool.testskin import stock

NAME = "TSC_Parts"
# colour (0..1 RGB) and finish (roughness, metalness)
PLAIN, SATIN, METAL, CHROME = (0.55, 0.0), (0.35, 0.0), (0.35, 1.0), (0.05, 1.0)
COLOURS = {
    "red": (0.85, 0.05, 0.05), "blue": (0.1, 0.3, 0.9), "orange": (1.0, 0.5, 0.0), "green": (0.1, 0.7, 0.15),
    "yellow": (1.0, 0.85, 0.0), "purple": (0.5, 0.1, 0.7), "cyan": (0.0, 0.8, 0.9), "pink": (1.0, 0.3, 0.7),
    "white": (0.95, 0.95, 0.95), "black": (0.03, 0.03, 0.03), "grey": (0.45, 0.45, 0.45), "gold": (1.0, 0.75, 0.2),
    "silver": (0.85, 0.85, 0.88), "lime": (0.6, 1.0, 0.1), "brown": (0.4, 0.22, 0.08), "dark": (0.12, 0.12, 0.14),
}
# (texture set, part or assembly name, colour, finish), painted in this order: later ones win.
PAINT = [
    ("Skin", "body", "white", SATIN),
    ("Skin", "body shell", "blue", SATIN),
    ("Skin", "nose tip", "white", SATIN),
    ("Skin", "nose panel", "black", SATIN),
    ("Skin", "nose fin", "yellow", SATIN),
    ("Skin", "cockpit surround", "white", SATIN),
    ("Skin", "mirror mount", "pink", SATIN),
    ("Skin", "side skirt", "black", SATIN),
    ("Skin", "sidepod top", "green", SATIN),
    ("Skin", "sidepod inlet", "black", PLAIN),
    ("Skin", "rear flank", "purple", SATIN),
    ("Skin", "rear quarter panel", "lime", SATIN),
    ("Skin", "fuel cap", "red", METAL),
    ("Skin", "engine cover", "yellow", SATIN),
    ("Skin", "engine cover panel", "grey", SATIN),
    ("Skin", "number panel", "white", SATIN),
    ("Skin", "tail panel", "cyan", SATIN),
    ("Skin", "tail corner", "pink", SATIN),
    ("Skin", "diffuser", "dark", PLAIN),
    ("Skin", "diffuser strake", "red", SATIN),
    ("Skin", "wing pylon", "cyan", SATIN),
    ("Skin", "wheel cover ring", "gold", METAL),
    ("Skin", "wheel cover disc", "silver", METAL),
    ("Skin", "wheel cover hub", "red", SATIN),
    ("Details", "chassis", "dark", PLAIN),
    ("Details", "floor", "grey", PLAIN),
    ("Details", "front wing", "red", SATIN),
    ("Details", "front wing endplate", "yellow", SATIN),
    ("Details", "wing bracket", "silver", METAL),
    ("Details", "sidepod", "green", SATIN),
    ("Details", "airbox", "orange", SATIN),
    ("Details", "seat", "blue", PLAIN),
    ("Details", "seat belt", "yellow", PLAIN),
    ("Details", "belt buckle", "silver", CHROME),
    ("Details", "cockpit rim", "black", PLAIN),
    ("Details", "steering wheel", "red", SATIN),
    ("Details", "steering column", "silver", METAL),
    ("Details", "dashboard", "cyan", SATIN),
    ("Details", "mirror", "silver", CHROME),
    ("Details", "mirror arm", "black", PLAIN),
    ("Details", "front suspension", "white", SATIN),
    ("Details", "pushrod", "yellow", SATIN),
    ("Details", "damper", "yellow", SATIN),
    ("Details", "tie rod", "yellow", SATIN),
    ("Details", "brake line", "pink", SATIN),
    ("Details", "rear suspension", "white", SATIN),
    ("Details", "driveshaft", "yellow", SATIN),
    ("Details", "rear damper", "yellow", SATIN),
    ("Details", "hub", "black", PLAIN),
    ("Details", "brake light", "orange", SATIN),
    ("Details", "rim", "gold", METAL),
    ("Details", "brake caliper", "red", SATIN),
    ("Details", "wheel ring", "silver", METAL),
    ("Details", "exhaust", "silver", CHROME),
    ("Details", "rear bumper", "white", SATIN),
    ("Details", "rear light", "red", SATIN),
    ("Details", "rear bumper corner", "purple", SATIN),
    ("Details", "rear undertray", "dark", PLAIN),
    ("Details", "rear strake", "lime", SATIN),
    ("Details", "side vent", "cyan", SATIN),
    ("Details", "side vane", "pink", SATIN),
    ("Details", "nose plate", "red", SATIN),
    ("Details", "front bulkhead", "orange", SATIN),
    ("Details", "antenna", "yellow", SATIN),
    ("Wheels", "tread", "dark", PLAIN),
    ("Wheels", "sidewall", "silver", PLAIN),
]
SIZES = {"Skin": (4096, 4096), "Details": (4096, 4096), "Wheels": (1024, 2048)}  # the default sharpness


def paint_set(p, tset):
    """Every part instance takes the colour of the last PAINT line naming it; then the texels
    are mixed by each instance's coverage, so a texel on the seam between two parts gets the
    two colours in proportion (anti-aliasing), and one at an island's edge keeps its own."""
    w, h = SIZES[tset]
    b = bake.bake(tset, w, h)
    chosen = {}
    for set_name, part, col, finish in PAINT:
        if set_name == tset:
            for i in p.select(part):
                chosen[i] = (COLOURS[col], finish)
    colour = np.zeros((h, w, 3), np.float32)
    rm = np.zeros((h, w, 2), np.float32)
    weight = np.zeros((h, w), np.float32)
    for i, (col, finish) in chosen.items():
        c = p.coverage(b, tset, ids=[i])
        colour += c[..., None] * np.asarray(col, np.float32)
        rm += c[..., None] * np.asarray(finish, np.float32)
        weight += c
    painted = weight > 0
    colour[painted] /= weight[painted][:, None]
    rm[painted] /= weight[painted][:, None]
    return raster.fill_holes(colour, painted), raster.fill_holes(rm, painted)


def build():
    p = parts.load()
    textures = {}
    colour, rm = paint_set(p, "Skin")
    textures |= {"Skin_B": (colour, "DXT1", {"srgb": True}), "Skin_R": (rm, "ATI2", {}),
                 "Skin_DirtMask": (stock("Skin_DirtMask"), "ATI1", {})}
    colour, rm = paint_set(p, "Details")
    textures |= {"Details_B": (colour, "DXT1", {"srgb": True}), "Details_R": (rm, "ATI2", {}),
                 "Details_I": (stock("Details_I"), "DXT5", {"codes_in_alpha": True}),
                 "Details_N": (stock("Details_N"), "ATI2", {"normal": True}),
                 "Details_DirtMask": (stock("Details_DirtMask"), "ATI1", {})}
    colour, rm = paint_set(p, "Wheels")
    textures |= {"Wheels_B": (colour, "DXT1", {"srgb": True}), "Wheels_R": (rm, "ATI2", {}),
                 "Wheels_N": (stock("Wheels_N"), "ATI2", {"normal": True}),
                 "Wheels_DirtMask": (stock("Wheels_DirtMask"), "ATI1", {})}
    out = paths.BUILD / NAME
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.dds"):
        old.unlink()
    previews = {}
    for tex_name, (image, fourcc, opts) in textures.items():
        levels = dds.write(out / f"{tex_name}.dds", image, fourcc, **opts)
        if tex_name.endswith("_B"):
            previews[tex_name.split("_")[0]] = levels[0][..., :3]
    zip_path = pack.pack(NAME, out, pack.icon("PARTS", COLOURS["red"], COLOURS["blue"]))
    sheet = paths.BUILD / f"{NAME}_preview.png"
    preview.render_sheet(previews, sheet)
    print(f"{zip_path.name}: {zip_path.stat().st_size / 1e6:.2f} MB; preview: {sheet}")
    return zip_path


if __name__ == "__main__":
    build()
