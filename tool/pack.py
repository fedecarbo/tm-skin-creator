"""Build a skin zip: the DDS textures at its root plus an Icon.tga. No spaces in the name."""

import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from tool import paint

ICON_SIZE = 256


def icon(label, left, right):
    """A square icon: two colour halves and a label. Colours are 0..1 RGB."""
    im = Image.new("RGB", (ICON_SIZE, ICON_SIZE))
    d = ImageDraw.Draw(im)
    to255 = lambda c: tuple(int(v * 255) for v in c)
    d.rectangle([0, 0, ICON_SIZE // 2, ICON_SIZE], fill=to255(left))
    d.rectangle([ICON_SIZE // 2, 0, ICON_SIZE, ICON_SIZE], fill=to255(right))
    f = ImageFont.truetype(paint.FONTS["impact"], 46)
    d.text((ICON_SIZE / 2, ICON_SIZE / 2), label, fill=(255, 255, 255), font=f, anchor="mm",
           stroke_width=4, stroke_fill=(0, 0, 0))
    return im


def pack(name, folder, icon_image):
    if " " in name:
        raise ValueError("skin names can't contain spaces")
    icon_image.save(folder / "Icon.tga")
    zip_path = folder.parent / f"{name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in sorted(folder.glob("*.dds")) + [folder / "Icon.tga"]:
            z.write(f, f.name)
    return zip_path
