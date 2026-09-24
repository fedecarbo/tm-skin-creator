"""The sweet counter: a pastel mint body with ice creams sprinkled all over it, each one its own
sticker (cones, lollies and three-scoop cones), a pink-and-white candy-stripe nose, pink wheels.
The pictures are from the picture maker (tool/pictures.py): art/cone.png, art/lolly.png, art/scoops.png."""
import numpy as np

from tool import shapes


def candy_stripes(period=9.0, phase=0.0):
    return shapes.field(lambda p, n: period / 4 - np.abs(((p[:, 2] - phase) % period) - period / 2))


def design(s):
    pink = "hot pink"
    s.paint("body", "gloss mint")
    s.scatter([s.art("cone"), s.art("lolly"), s.art("scoops")], "body", size=(9, 12), spacing=18, turn="random", seed=7)
    s.paint("nose tip", "gloss white")
    s.paint("nose tip", f"gloss {pink}", zone=candy_stripes(10))
    s.paint(["wing pylon", "diffuser", "diffuser strake"], f"gloss {pink}")
    s.paint("wheel covers", f"gloss {pink}")
    s.paint("wheel cover ring", "gloss cream")
    s.paint("rim", "gloss cream")
    s.paint("hub", "gloss cream")
    s.paint("brake caliper", pink)
    s.paint("inner", "charcoal satin")
    s.paint("front wing", "gloss mint")
    s.paint("seat", "black leather")
    s.text("ICE CREAM", "left flank", colour="white", font="bangers", height=10, outline=pink, outline_width=0.08, at=(35, 62, 60))
    s.text("ICE CREAM", "right flank", colour="white", font="bangers", height=10, outline=pink, outline_width=0.08, at=(-35, 62, 60))
