"""Checkpoint 4: the materials lab. Test skins that put every finish, the varnish, the dirt, every
glow code, the glass and the relief direction on known places, so the game can be read like a chart.

    python -m tool.labskin          builds TSC_Lab and TSC_Lab_NoCoat (the same, without Skin_CoatR)

What's where (the key the user's screenshots are read against):

  BODY (orange, plain satin everywhere not listed)
    engine deck (behind the cockpit, seen from the chase camera): a grid of 5 x 4 swatches.
      Along the car, rear to front: roughness 0, 25, 50, 75, 100 % (labelled at the outer edges).
      Across: the left outer column is plain paint (metal 0, varnish 0), the left inner column the
      same with varnish 255, the right inner column metal 100 % with varnish 0, the right outer
      column metal with varnish 255.
    flanks (the sides, from behind the rear wheel arch to the sidepod): 3 bands of metalness
      0 / 50 / 100 % at roughness 40 %, labelled M0, M50, M100.
    bonnet (in front of the cockpit): black, three bands, roughness 0 / 50 / 100 %, varnish 0 on
      the left half and 255 on the right.
    cockpit surround and nose: white. Wheel covers: gold ring, silver disc, black hub.
    dirt mask: 255 on the left half of the car, 0 on the right.
  DETAILS (dark grey, plain)
    front wing: light grey, matte, with a dome in relief either side of the centre pylon (normal
      map only). Raised domes = the game reads the map as OpenGL Y+, the way we write it; dishes
      = it doesn't.
    glows, one code per part: see GLOWS.
    dirt mask: 255 on the front wing and front suspension, 0 elsewhere.
  TYRES: sidewall in 8 sectors (numbered): roughness 0 / 33 / 67 / 100 %, sectors 1-4 plain,
    5-8 metal; tread half shiny (roughness 30 %) and half dull (90 %). Dirt 255 on the tread only.
  GLASS: canopy tinted cyan at the front and amber at the rear; alpha 255 on the left, 128 in the
    middle strip, 32 on the right. Glass_I: the side lenses glow magenta (always), the mirror
    glass white (night only).
"""

import shutil

import numpy as np
from PIL import Image
from scipy import ndimage

from tool import bake, dds, pack, paint, parts, paths, preview, raster
from tool.testskin import stock

NAME = "TSC_Lab"
VARIANTS = {"TSC_Lab": {"drop": ()}, "TSC_Lab_NoCoat": {"drop": ("Skin_CoatR",)}}

ORANGE, BLACK, WHITE, INK = (0.95, 0.42, 0.04), (0.02, 0.02, 0.02), (0.92, 0.92, 0.92), (0.05, 0.05, 0.05)
GOLD, SILVER, GREY, DARK = (1.0, 0.75, 0.2), (0.85, 0.85, 0.88), (0.6, 0.6, 0.6), (0.22, 0.22, 0.24)
STEPS = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
SKIN_SIZE, DETAILS_SIZE, WHEELS_SIZE, GLASS_SIZE = 4096, 4096, (1024, 2048), 1024
CODES = np.array([0, 32, 64, 96, 128, 160, 192, 224, 255])

# code, part, glow colour, what the game should do with it. Parts chosen because the game's
# camera can see them (checked in the viewer, 2026-09-24). Grey where Nadeo says "must be
# grayscale": the game supplies the colour.
GLOWS = [
    (0, "rear bumper corner", (1.0, 0.1, 0.1), "brake lights: on when braking"),
    (32, "sidepod frame", GREY, "energy: coloured by the game (team colour)"),
    (64, "rear bumper", (1.0, 0.45, 0.1), "brake heat: on when braking hard"),
    (96, "side vent", (1.0, 0.1, 0.9), "always on"),
    (128, "rim", (0.85, 0.92, 1.0), "front lights: vivid at night"),
    (160, "hub", GREY, "turbo colour: coloured by the game under turbo"),
    (192, "rear strake", (1.0, 0.6, 0.1), "exhaust heat: on during turbo"),
    (224, "rear undertray", GREY, "boost: coloured by the game under boost"),
    (255, "hub bracket", (1.0, 0.9, 0.2), "night only"),
]


def band(v, lo, hi, n):
    """Which of n equal bands between lo and hi holds v (clipped)."""
    return np.clip(np.floor((v - lo) / (hi - lo) * n), 0, n - 1).astype(int)


def label(b, text, centre, right, up, height_cm, where, font="bold"):
    img = paint.text_image(text, 160, font=font)
    return paint.project(b, img, centre, right, up, height_cm * img.shape[1] / img.shape[0], up_facing(right, up),
                         where=where)


def up_facing(right, up):
    return tuple(np.cross(np.asarray(right, float), np.asarray(up, float)))


def skin_textures(p):
    s = SKIN_SIZE
    b = bake.bake("Skin", s, s)
    pos, nrm, cov = b["position"], b["normal"], paint.covered(b)
    x, y, z = pos[..., 0], pos[..., 1], pos[..., 2]
    colour = np.zeros((s, s, 3), np.float32)
    colour[:] = ORANGE
    rm = np.zeros((s, s, 2), np.float32)
    rm[:] = (0.45, 0.0)
    coat = np.zeros((s, s), np.float32)
    ink = np.zeros((s, s), np.float32)
    white_ink = np.zeros((s, s), np.float32)

    covers = np.zeros((s, s), bool)  # the wheel covers share one set of texels: no labels there
    for n in ("wheel cover ring", "wheel cover disc", "wheel cover hub"):
        covers |= p.mask(b, "Skin", n)

    # the flanks: metalness ladder, from the rear wheel to the front of the sidepod
    flank = cov & ~covers & (z >= -85) & (z <= 12) & (np.abs(x) > 60)
    k = band(z, -85, 12, 3)
    rm[flank] = np.stack([np.full(flank.sum(), 0.4), np.array([0.0, 0.5, 1.0])[k[flank]]], -1)
    for i in range(3):
        zc = -85 + 97 / 3 * (i + 0.5)
        for sign in (1, -1):
            ink += label(b, f"M{[0, 50, 100][i]}", (sign * 85, 46, zc), (0, 0, -sign), (0, 1, 0), 7, flank)

    # the engine deck: roughness along the car, (metal, varnish) across
    deck = cov & ~covers & (z >= -130) & (z <= 0) & (np.abs(x) <= 60) & (nrm[..., 1] > 0.3)
    k = band(z, -130, 0, 5)
    rough = STEPS[k]
    metal = np.where(x < 0, 1.0, 0.0)
    varnish = np.where(np.abs(x) < 30, 1.0, 0.0)
    rm[deck] = np.stack([rough[deck], metal[deck]], -1)
    coat[deck] = varnish[deck]
    for i in range(5):
        zc = -130 + 26 * (i + 0.5)
        for sign in (1, -1):
            ink += label(b, f"R{int(STEPS[i] * 100)}", (sign * 45, 80, zc), (-1, 0, 0), (0, 0, 1), 6, deck)

    # the bonnet: black, three roughness bands, varnish by side
    bonnet = cov & (z >= 90) & (z <= 145) & (y > 40)
    k = band(z, 90, 145, 3)
    colour[bonnet] = BLACK
    rm[bonnet] = np.stack([np.array([0.0, 0.5, 1.0])[k[bonnet]], np.zeros(bonnet.sum())], -1)
    coat[bonnet] = (x[bonnet] < 0)
    for i in range(3):
        zc = 90 + 55 / 3 * (i + 0.5)
        white_ink += label(b, str(int([0, 50, 100][i])), (0, 65, zc), (-1, 0, 0), (0, 0, 1), 5, bonnet)

    # named parts on top
    for names, col, finish in (
        (("cockpit surround",), WHITE, (0.3, 0.0)),
        (("nose tip", "nose panel", "nose fin"), WHITE, (0.2, 0.0)),
        (("wheel cover ring",), GOLD, (0.15, 1.0)),
        (("wheel cover disc",), SILVER, (0.5, 1.0)),
        (("wheel cover hub",), BLACK, (0.25, 0.0)),
    ):
        m = np.zeros((s, s), bool)
        for n in names:
            m |= p.mask(b, "Skin", n)
        colour[m] = col
        rm[m] = finish
        coat[m] = 0

    colour = paint.mix(colour, INK, ink)
    colour = paint.mix(colour, WHITE, white_ink)
    rm[(ink > 0.5) | (white_ink > 0.5)] = (0.5, 0.0)
    textures = {
        "Skin_B": (raster.fill_holes(colour, cov), "DXT1", {"srgb": True}),
        "Skin_R": (raster.fill_holes(rm, cov), "ATI2", {}),
        "Skin_CoatR": (raster.fill_holes(coat, cov), "ATI1", {}),
    }
    # dirt: left half 255, right half 0 (a 2048 bake is plenty for a mask)
    b2 = bake.bake("Skin", 2048, 2048)
    dirt = np.clip((b2["position"][..., 0] + 1) / 2, 0, 1).astype(np.float32)
    textures["Skin_DirtMask"] = (raster.fill_holes(dirt, paint.covered(b2)), "ATI1", {})
    return textures


def emboss(height, strength=8.0):
    """Tangent-space normal (X, Y in 0..1) of a height field, OpenGL style: Y points to +v, which
    is up the image (row 0 is v = 1). A bump's upper edge gets Y > 0.5."""
    d_col = np.gradient(height, axis=1)
    d_row = np.gradient(height, axis=0)
    n = np.stack([-strength * d_col, strength * d_row, np.ones_like(height)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n[..., :2] * 0.5 + 0.5


def details_textures(p):
    s = DETAILS_SIZE
    b = bake.bake("Details", s, s)
    cov = paint.covered(b)
    colour = np.zeros((s, s, 3), np.float32)
    colour[:] = DARK
    rm = np.zeros((s, s, 2), np.float32)
    rm[:] = (0.5, 0.0)
    # the front wing: light and matte, where the relief test goes
    m = p.mask(b, "Details", "front wing")
    colour[m] = (0.75, 0.75, 0.75)
    rm[m] = (0.55, 0.0)
    # glow parts: a dark version of their glow colour, so they can be found when off
    for code, name, col, _ in GLOWS:
        m = p.mask(b, "Details", name)
        colour[m] = np.asarray(col) * 0.25
        rm[m] = (0.5, 0.0)
    textures = {
        "Details_B": (raster.fill_holes(colour, cov), "DXT1", {"srgb": True}),
        "Details_R": (raster.fill_holes(rm, cov), "ATI2", {}),
    }

    # glow, relief and dirt at 2048, the stock size
    b2 = bake.bake("Details", 2048, 2048)
    cov2 = paint.covered(b2)
    glow = np.zeros((2048, 2048, 4), np.float32)
    glow[..., 3] = 96 / 255  # black everywhere: no glow
    for code, name, col, _ in GLOWS:
        m = p.mask(b2, "Details", name)
        glow[m, :3] = col
        glow[m, 3] = code / 255
    textures["Details_I"] = (glow, "DXT5", {"codes_in_alpha": True})

    # relief: a dome on the centre of the front wing's top (the wing has only ~2.5 texels per cm,
    # too coarse for letters). A bake of the wing's own triangles gives the wing's positions
    # (Details texels are mostly shared, and the main bake's position may belong to another part).
    normal = stock("Details_N")
    wing = p.local_bake("Details", 2048, 2048, "front wing")
    wp = wing["position"]
    # The wing's centre is under the body's pylon, so the domes sit either side of it, at |x| = 45.
    top = (wing["tri"] >= 0) & (wing["normal"][..., 1] > 0.5) & (np.abs(wp[..., 0]) > 36) & (np.abs(wp[..., 0]) < 54)
    r = np.hypot(np.abs(wp[..., 0]) - 45, wp[..., 2] - 202)  # cm from the dome's centre
    h = np.where(top, 4.0 * np.clip(1 - (r / 5.0) ** 2, 0, 1), 0)  # a paraboloid 10 cm wide, 4 cm high
    cm_per_texel = float(np.median(np.linalg.norm(np.diff(wp, axis=1), axis=-1)[top[:, 1:] & top[:, :-1]]))
    n = emboss(ndimage.gaussian_filter(h, 0.7), strength=1 / cm_per_texel)
    normal[top] = n[top]
    textures["Details_N"] = (normal, "ATI2", {"normal": True})

    # dirt: the front wing and the front suspension can get dirty, nothing else
    dirt = np.zeros((2048, 2048), np.float32)
    for name in ("front wing", "front suspension"):
        dirt[p.mask(b2, "Details", name)] = 1
    textures["Details_DirtMask"] = (raster.fill_holes(dirt, cov2), "ATI1", {})
    return textures


WHEEL_Y, WHEEL_Z = parts.WHEEL_Y, parts.WHEEL_Z


def wheels_textures(p):
    w, h = WHEELS_SIZE
    b = bake.bake("Wheels", w, h)
    pos, cov = b["position"], paint.covered(b)
    x, y, z = pos[..., 0], pos[..., 1], pos[..., 2]
    zc = np.where(z > 30, WHEEL_Z[0], WHEEL_Z[1])
    theta = np.arctan2(y - WHEEL_Y, z - zc)  # angle around the axle
    radius = np.hypot(y - WHEEL_Y, z - zc)
    sidewall, tread = p.mask(b, "Wheels", "sidewall"), p.mask(b, "Wheels", "tread")
    colour = np.zeros((h, w, 3), np.float32)
    rm = np.zeros((h, w, 2), np.float32)
    sector = band(theta, -np.pi, np.pi, 8)
    colour[sidewall] = (0.72, 0.72, 0.72)
    rm[sidewall] = np.stack([np.array([0.0, 1 / 3, 2 / 3, 1.0])[sector[sidewall] % 4],
                             (sector[sidewall] >= 4).astype(np.float32)], -1)
    colour[tread] = (0.08, 0.08, 0.08)
    rm[tread] = np.stack([np.where(theta[tread] > 0, 0.3, 0.9), np.zeros(tread.sum())], -1)
    # sector numbers on the sidewalls, drawn in polar coordinates around the axle
    r_mid = float(np.median(radius[sidewall]))
    ink = np.zeros((h, w), np.float32)
    for k in range(8):
        img = paint.text_image(str(k + 1), 160, font="bold")
        ih, iw = img.shape
        height_cm = 5.0
        cm_per_px = height_cm / ih
        tc = -np.pi + (k + 0.5) * (2 * np.pi / 8)
        s_ = (np.angle(np.exp(1j * (theta - tc))) * r_mid) / cm_per_px + iw / 2
        t_ = ih / 2 - (radius - r_mid) / cm_per_px
        ok = sidewall & (s_ >= 0) & (s_ < iw) & (t_ >= 0) & (t_ < ih)
        ink[ok] = img[t_[ok].astype(int), s_[ok].astype(int)]
    colour = paint.mix(colour, INK, ink)
    rm[ink > 0.5] = (0.5, 0.0)
    dirt = tread.astype(np.float32)
    return {
        "Wheels_B": (raster.fill_holes(colour, cov), "DXT1", {"srgb": True}),
        "Wheels_R": (raster.fill_holes(rm, cov), "ATI2", {}),
        "Wheels_N": (stock("Wheels_N"), "ATI2", {"normal": True}),
        "Wheels_DirtMask": (raster.fill_holes(dirt, cov), "ATI1", {}),
    }


def glass_textures(p):
    s = GLASS_SIZE
    b = bake.bake("Glass", s, s)
    pos = b["position"]
    x, z = pos[..., 0], pos[..., 2]
    tint = stock("Glass_T")
    canopy = p.mask(b, "Glass", "canopy")
    tint[canopy & (z > 30), :3] = (0.3, 0.9, 1.0)
    tint[canopy & (z <= 30), :3] = (1.0, 0.65, 0.15)
    tint[canopy, 3] = np.where(x > 8, 1.0, np.where(x < -8, 32 / 255, 128 / 255))[canopy]
    glow = stock("Glass_I")
    glow[..., 3] = CODES[np.digitize(glow[..., 3] * 255, (CODES[1:] + CODES[:-1]) / 2)] / 255
    for name, col, code in (("side lens", (1.0, 0.1, 0.9), 96), ("mirror glass", (1.0, 1.0, 1.0), 255)):
        m = p.mask(b, "Glass", name)
        glow[m, :3] = col
        glow[m, 3] = code / 255
    return {"Glass_T": (tint, "DXT5", {}), "Glass_I": (glow, "DXT5", {"codes_in_alpha": True})}


def build():
    p = parts.load()
    textures = {}
    for fn in (skin_textures, details_textures, wheels_textures, glass_textures):
        textures |= fn(p)
    out = paths.BUILD / NAME
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.dds"):
        old.unlink()
    previews = {}
    for tex_name, (image, fourcc, opts) in textures.items():
        levels = dds.write(out / f"{tex_name}.dds", image, fourcc, **opts)
        print(f"  {tex_name}.dds  {fourcc}  {levels[0].shape[1]}x{levels[0].shape[0]}")
        if tex_name.endswith("_B") or tex_name == "Glass_T":
            previews[tex_name.split("_")[0]] = levels[0][..., :3]
    zips = []
    for name, v in VARIANTS.items():
        folder = paths.BUILD / name
        if folder != out:
            folder.mkdir(parents=True, exist_ok=True)
            for old in folder.glob("*.dds"):
                old.unlink()
            for f in out.glob("*.dds"):
                if f.stem not in v["drop"]:
                    shutil.copyfile(f, folder / f.name)
        zips.append(pack.pack(name, folder, pack.icon("LAB", ORANGE, BLACK)))
        print(f"{zips[-1].name}: {zips[-1].stat().st_size / 1e6:.2f} MB")
    sheet = paths.BUILD / f"{NAME}_preview.png"
    preview.render_sheet(previews, sheet)
    print(f"preview: {sheet}")
    return zips


if __name__ == "__main__":
    build()
