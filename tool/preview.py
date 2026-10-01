"""The car drawn flat and coloured by part, for checking the part names (`python -m tool.parts
--review`): orthographic views, simple lighting, no materials. Not the viewer."""

import numpy as np
from PIL import Image, ImageDraw

from tool import fbx, fonts, raster

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


MESH_ORDER = ("Skin", "Details", "Wheels", "Glass")


def _project(view, size, scale, include, centre=(0, 40.0, 27.0)):
    """Rasterise the chosen meshes: returns (global triangle id per pixel or -1, shade)."""
    right, up, d = _basis(view)
    light = -d + np.array([0.3, 0.8, 0.2])
    light /= np.linalg.norm(light)
    meshes = fbx.meshes()
    xy, z, n, gid = [], [], [], []
    offset = 0
    for tex_name in MESH_ORDER:
        m = meshes[{"Skin": "Skin_01", "Details": "Details_01", "Wheels": "Wheels_01", "Glass": "Glass_01"}[tex_name]]
        count = len(m["tri_vertex"])
        if tex_name in include:
            p = m["positions"][m["tri_vertex"]].astype(np.float64) - np.asarray(centre)
            xy.append(np.stack([p @ right / scale + size / 2, size / 2 - p @ up / scale], -1))
            z.append(p @ d)
            n.append(m["tri_normal"])
            gid.append(np.arange(offset, offset + count))
        offset += count
    tri, bary = raster.rasterise(np.concatenate(xy), size, size, depth=np.concatenate(z))
    nrm = raster.interpolate(tri, bary, np.concatenate(n))
    nrm /= np.maximum(np.linalg.norm(nrm, axis=-1, keepdims=True), 1e-9)
    shade = 0.45 + 0.55 * np.abs((nrm * light).sum(-1))
    gids = np.concatenate(gid)
    return np.where(tri >= 0, gids[np.maximum(tri, 0)], -1), shade


def _palette(n, seed=7):
    import colorsys
    rng = np.random.default_rng(seed)
    hues = (np.arange(n) * 0.618034 + rng.random()) % 1
    return np.array([colorsys.hsv_to_rgb(h, 0.55 + 0.4 * rng.random(), 0.7 + 0.3 * rng.random()) for h in hues])


def render_parts_sheet(tri_part, instances, out_path, size=900):
    """Six views coloured by part name (mirrored parts share a colour), with a legend per view."""
    names = sorted(set(i["name"] for i in instances))
    colour_of_name = {n: c for n, c in zip(names, _palette(len(names)))}
    inst_colour = np.array([colour_of_name[i["name"]] for i in instances])
    shots = [("3/4 front +x", ("Skin", "Details", "Wheels", "Glass")), ("top (front up)", ("Skin", "Details", "Wheels", "Glass")),
             ("side +x", ("Skin", "Details", "Wheels", "Glass")), ("3/4 front +x", ("Details", "Wheels", "Glass")),
             ("top (front up)", ("Details", "Wheels")), ("rear", ("Details", "Wheels", "Glass"))]
    font = fonts.font("arial bold", 15)
    tiles = []
    for view, include in shots:
        gid, shade = _project(view, size, 0.5, include)
        img = np.full((size, size, 3), 235, np.uint8)
        cov = gid >= 0
        part = tri_part[np.maximum(gid, 0)]
        img[cov] = np.clip(inst_colour[part[cov]] * 255 * shade[cov][:, None], 0, 255).astype(np.uint8)
        im = Image.fromarray(img)
        d = ImageDraw.Draw(im)
        d.text((8, 6), f"{view}  ({', '.join(include)})", fill=(0, 0, 0), font=font)
        # legend: the names visible in this view, biggest first
        seen = np.bincount(part[cov], minlength=len(instances))
        by_name = {}
        for i, n in enumerate(seen):
            if n:
                by_name[instances[i]["name"]] = by_name.get(instances[i]["name"], 0) + n
        y = 28
        for n, _ in sorted(by_name.items(), key=lambda kv: -kv[1])[:40]:
            c = tuple(int(v * 255) for v in colour_of_name[n])
            d.rectangle([8, y, 22, y + 12], fill=c, outline=(0, 0, 0))
            d.text((27, y - 2), n, fill=(0, 0, 0), font=font)
            y += 16
        tiles.append(im)
    cols = 3
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * size, rows * size), (235, 235, 235))
    for k, im in enumerate(tiles):
        sheet.paste(im, ((k % cols) * size, (k // cols) * size))
    sheet.save(out_path)
    return out_path
