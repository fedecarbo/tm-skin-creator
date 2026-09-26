"""The ice cream truck itself: an ivory body, a pink-and-white candy-stripe awning over the deck
and the nose, mint lower body, a soft-serve cone sticker on each side and an ice lolly on the
bonnet, "ICE CREAM" on the flanks. Pink wheels with cream rings, mint brake calipers.
The pictures are from the picture maker (tool/pictures.py): art/cone.png, art/lolly.png."""
import numpy as np
from PIL import Image

from tool import shapes


def leaning(path, degrees):
    """The picture tilted, so a tall cone fits a flat patch that is wider than it is high."""
    im = Image.open(path).convert("RGBA").rotate(degrees, expand=True, resample=Image.BICUBIC)
    return im.crop(im.getchannel("A").getbbox())  # so `width` is the tilted cone's own width


def candy_stripes(period=9.0, phase=0.0):
    """Stripes across the car, each half the period wide: the awning of a real truck."""
    return shapes.field(lambda p, n: period / 4 - np.abs(((p[:, 2] - phase) % period) - period / 2))


def design(s):
    pink, mint = "hot pink", "mint"
    s.paint("body", "gloss ivory")
    s.paint(["side skirt", "diffuser", "diffuser strake"], f"gloss {mint}")
    # the awning: pink stripes on white over the deck behind the cockpit, and on the nose tip
    s.paint(["engine cover", "engine cover panel", "number panel"], "gloss white")
    s.paint(["engine cover", "engine cover panel", "number panel"], f"gloss {pink}", zone=candy_stripes(10))
    s.paint("nose tip", "gloss white")
    s.paint("nose tip", f"gloss {pink}", zone=candy_stripes(10))
    s.paint("wing pylon", "gloss white")
    # wheels: their own step
    s.paint("wheel covers", f"gloss {pink}")
    s.paint("wheel cover ring", "gloss cream")
    s.paint("rim", "gloss cream")
    s.paint(["hub", "brake light"], "gloss cream")
    s.paint("brake caliper", mint)
    s.paint("inner", "charcoal satin")
    s.paint(["front wing", "wing mounts"], "gloss ivory")
    s.paint("seat", "black leather")
    # the pictures: a cone on each rear flank, a lolly on the bonnet
    # a cone standing up is 70 cm tall at 30 wide, and the flank's flat patch is 34 cm high,
    # so the cone leans forward on both sides
    s.decal(leaning(s.art("cone"), 40), "left side", width=28)
    s.decal(leaning(s.art("cone"), -40), "right side", width=28)
    s.decal(s.art("lolly"), "bonnet", width=26)
    s.text("ICE CREAM", "left flank", colour=pink, font="bangers", height=10, outline="white", outline_width=0.08, at=(35, 62, 60))
    s.text("ICE CREAM", "right flank", colour=pink, font="bangers", height=10, outline="white", outline_width=0.08, at=(-35, 62, 60))
