"""A first real design, by hand, with what checkpoint 4 taught us: TSC_Carbon.

    python -m tool.carbonskin      builds TSC_Carbon

The user's words (2026-09-24): "a fully matte car, some kind of nice black carbon look, maybe a
couple of parts where it's kind of glossy." So: a fine carbon weave in matte black over the
body (varnish 255, no gloss), gloss black on the nose tip, the cockpit surround, the rear
quarter panels and the wheel cover rings (varnish 0), the inner car dark and matte with
gunmetal rims. Tyres, glass, lights, relief and dirt stay stock. A stand-in for the paint box.
"""

import numpy as np

from tool import bake, dds, finishes, pack, parts, paths, preview, raster
from tool.testskin import stock

NAME = "TSC_Carbon"
CARBON_DARK, CARBON_LIGHT = 0.07, 0.15  # sRGB greys of the weave's two tones
GLOSS_BLACK = (0.03, 0.03, 0.035)
GLOSSY = ("nose tip", "cockpit surround", "rear quarter panel", "wheel cover ring")


def weave(pos, nrm, cell_cm=0.5):
    """A twill weave, 0..1, from 3D position: cells of stripes whose direction alternates like
    a checkerboard. Drawn on the two world axes across the surface's main axis (triplanar)."""
    out = np.zeros(pos.shape[:2], np.float32)
    w = np.abs(nrm) ** 4
    w /= np.maximum(w.sum(-1, keepdims=True), 1e-6)
    for axis in range(3):
        a, b = [k for k in range(3) if k != axis]
        u, v = pos[..., a] / cell_cm, pos[..., b] / cell_cm
        cu, cv = np.floor(u), np.floor(v)
        along_u = ((cu + cv) % 2) == 0  # this cell's stripes run along u
        phase = np.where(along_u, v, u)
        stripes = 0.5 + 0.5 * np.cos(2 * np.pi * phase * 2)
        # each cell is a thread crossing over: lighter in its middle, darker at its ends
        t = np.where(along_u, u - cu, v - cv)
        shade = 1 - 0.6 * np.abs(t - 0.5) * 2
        out += w[..., axis] * stripes * shade
    return np.clip(out, 0, 1)


def skin_textures(p):
    s = 4096
    b = bake.bake("Skin", s, s)
    pos, nrm, cov = b["position"], b["normal"], b["tri"] >= 0
    pattern = weave(pos, nrm)
    matte = finishes.get("matte")
    colour = np.zeros((s, s, 3), np.float32)
    colour[:] = (CARBON_DARK + (CARBON_LIGHT - CARBON_DARK) * pattern)[..., None]
    colour[..., 2] += 0.01  # a hint of blue in the black, as real carbon has
    rm = np.zeros((s, s, 2), np.float32)
    rm[..., 0] = matte.roughness  # flat: a weave in the roughness map costs 7 MB and shows nothing
    rm[..., 1] = matte.metalness
    coat = np.full((s, s), finishes.coat(matte), np.float32)
    gloss = finishes.get("gloss")
    for name in GLOSSY:
        m = p.mask(b, "Skin", name)
        colour[m] = GLOSS_BLACK
        rm[m] = (0.15, gloss.metalness)
        coat[m] = finishes.coat(gloss)
    return {
        "Skin_B": (raster.fill_holes(colour, cov), "DXT1", {"srgb": True}),
        "Skin_R": (raster.fill_holes(rm, cov), "ATI2", {}),
        "Skin_CoatR": (raster.fill_holes(coat, cov), "ATI1", {}),
    }


def details_textures(p):
    s = 4096
    b = bake.bake("Details", s, s)
    cov = b["tri"] >= 0
    colour = np.zeros((s, s, 3), np.float32)
    colour[:] = (0.1, 0.1, 0.11)
    rm = np.zeros((s, s, 2), np.float32)
    rm[:] = (0.8, 0.0)
    for names, col, finish in (
        (("rim", "hub"), (0.32, 0.32, 0.34), finishes.get("brushed metal")),
        (("exhaust", "wheel ring"), (0.6, 0.6, 0.62), finishes.get("polished metal")),
        (("brake caliper",), (0.05, 0.05, 0.05), finishes.get("satin")),
    ):
        for n in names:
            m = p.mask(b, "Details", n)
            colour[m] = col
            rm[m] = finishes.rm(finish)
    return {
        "Details_B": (raster.fill_holes(colour, cov), "DXT1", {"srgb": True}),
        "Details_R": (raster.fill_holes(rm, cov), "ATI2", {}),
    }


def build():
    p = parts.load()
    textures = skin_textures(p) | details_textures(p)
    out = paths.BUILD / NAME
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.dds"):
        old.unlink()
    previews = {}
    for tex_name, (image, fourcc, opts) in textures.items():
        levels = dds.write(out / f"{tex_name}.dds", image, fourcc, **opts)
        if tex_name.endswith("_B"):
            previews[tex_name.split("_")[0]] = levels[0][..., :3]
    zip_path = pack.pack(NAME, out, pack.icon("CARBON", (0.08, 0.08, 0.09), (0.03, 0.03, 0.035)))
    preview.render_sheet(previews, paths.BUILD / f"{NAME}_preview.png")
    print(f"{zip_path.name}: {zip_path.stat().st_size / 1e6:.2f} MB")
    return zip_path


if __name__ == "__main__":
    build()
