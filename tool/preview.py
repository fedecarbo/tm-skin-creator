"""Quick flat-shaded renders of the car wearing a set of textures, for Claude's own checks.

This is not the viewer (checkpoint 2): orthographic views, simple lighting, no materials.
    render_sheet({"Skin": skin_rgb, "Details": ..., "Wheels": ..., "Glass": ...}, out_png)
Texture arrays are uint8 images (h, w, 3), row 0 at the top.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from tool import fbx, raster

# name -> (right axis, up axis, view direction toward the car); x = side, y = up, z = forward
VIEWS = {
    "side +x": (np.array([0, 0, -1.0]), np.array([0, 1.0, 0]), np.array([-1.0, 0, 0])),
    "side -x": (np.array([0, 0, 1.0]), np.array([0, 1.0, 0]), np.array([1.0, 0, 0])),
    "top (front up)": (np.array([-1.0, 0, 0]), np.array([0, 0, 1.0]), np.array([0, -1.0, 0])),
    "front": (np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), np.array([0, 0, -1.0])),
    "rear": (np.array([-1.0, 0, 0]), np.array([0, 1.0, 0]), np.array([0, 0, 1.0])),
    "3/4 front +x": (None, None, np.array([-0.6, -0.45, -0.66])),
}


def _basis(view):
    right, up, d = VIEWS[view]
    d = d / np.linalg.norm(d)
    if right is None:
        right = np.cross(np.array([0, 1.0, 0]), -d)
        right /= np.linalg.norm(right)
        up = np.cross(-d, right)
    return right, up, d


def render(textures, view, size=700, scale=0.6):
    right, up, d = _basis(view)
    light = -d + np.array([0.3, 0.8, 0.2])
    light /= np.linalg.norm(light)
    image = np.full((size, size, 3), 235, np.uint8)
    all_xy, all_z, all_uv, all_n, owner = [], [], [], [], []
    meshes = fbx.meshes()
    for i, (tex_name, mesh_name) in enumerate(
        [("Skin", "Skin_01"), ("Details", "Details_01"), ("Wheels", "Wheels_01"), ("Glass", "Glass_01")]
    ):
        if tex_name not in textures:
            continue
        m = meshes[mesh_name]
        p = m["positions"][m["tri_vertex"]].astype(np.float64) - np.array([0, 40.0, 27.0])
        x = p @ right / scale + size / 2
        y = size / 2 - p @ up / scale
        all_xy.append(np.stack([x, y], -1))
        all_z.append(p @ d)
        all_uv.append(m["tri_uv"])
        all_n.append(m["tri_normal"])
        owner.append(np.full(len(p), i))
    xy = np.concatenate(all_xy)
    z = np.concatenate(all_z)
    tri, bary = raster.rasterise(xy, size, size, depth=z)
    covered = tri >= 0
    uv = raster.interpolate(tri, bary, np.concatenate(all_uv))
    n = raster.interpolate(tri, bary, np.concatenate(all_n))
    n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-9)
    shade = 0.45 + 0.55 * np.abs((n * light).sum(-1))
    who = np.concatenate(owner)[np.maximum(tri, 0)]
    names = ["Skin", "Details", "Wheels", "Glass"]
    for i, tex_name in enumerate(names):
        if tex_name not in textures:
            continue
        sel = covered & (who == i)
        tex = textures[tex_name]
        th, tw = tex.shape[:2]
        u = np.clip((uv[sel, 0] % 1.0) * tw, 0, tw - 1).astype(int)
        v = np.clip((1 - uv[sel, 1] % 1.0) * th, 0, th - 1).astype(int)
        colour = tex[v, u, :3].astype(np.float32)
        image[sel] = np.clip(colour * shade[sel][:, None], 0, 255).astype(np.uint8)
    return image


def render_sheet(textures, out_path, views=None, size=700):
    views = views or list(VIEWS)
    cols = 3
    rows = (len(views) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * size, rows * size), (235, 235, 235))
    font = ImageFont.truetype("arialbd.ttf", 22)
    for k, view in enumerate(views):
        tile = Image.fromarray(render(textures, view, size))
        ImageDraw.Draw(tile).text((10, 8), view, fill=(0, 0, 0), font=font)
        sheet.paste(tile, ((k % cols) * size, (k // cols) * size))
    sheet.save(out_path)
    return out_path
