"""TSC_DecalsTest: the road's step 5 on a test car, stickers, badges and words on the car's hardest spots, the same
design painted as the tool was (A, the old code) and on the surface (B): a badge across the rear flank's rolled
shoulder, a picture pressed over the nose tip's seam, words along a rounded edge, words over the front flank's turn,
a disc asked for from above, a word at a side spot, a placard on a drawn line, and stickers scattered over the
sidepod tops and the deck. Scrapped after the pick."""

import numpy as np
from PIL import Image, ImageDraw

from tool import course, marks, meshlines

BASE, INK, GOLD, RED, WHITE = "#d9d6cf", "#141414", "#e0a82e", "#c8102e", "#f4f2ec"


def emblem(px=512):
    """A round emblem: a gold disc with a dark ring and a red triangle, drawn here so it needs no stored art."""
    pic = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    d = ImageDraw.Draw(pic)
    d.ellipse((16, 16, px - 16, px - 16), fill=(224, 168, 46, 255), outline=(20, 20, 20, 255), width=px // 18)
    d.polygon([(px / 2, px * 0.2), (px * 0.78, px * 0.78), (px * 0.22, px * 0.78)], fill=(200, 16, 46, 255))
    return pic


def sticker(px=256):
    """A small square sticker with a cross, for the scatter."""
    pic = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    d = ImageDraw.Draw(pic)
    d.rounded_rectangle((8, 8, px - 8, px - 8), radius=px // 8, fill=(20, 20, 20, 255))
    d.rectangle((px * 0.42, px * 0.18, px * 0.58, px * 0.82), fill=(224, 168, 46, 255))
    d.rectangle((px * 0.18, px * 0.42, px * 0.82, px * 0.58), fill=(224, 168, 46, 255))
    return pic


def design(s):
    s.clay()
    s.step("The body", "The body in one pale colour, the inner car dark.")
    s.paint("body", "satin", colour=BASE)
    s.paint("inner", "matte", colour="#2a2a2e")
    s.step("Badges across the shoulder", "A dark disc 16 cm wide with a gold ring and a red star, pressed across the rear "
           "flank's rolled shoulder on purpose, in front of the rear wheel, both sides.")
    shoulder = meshlines.line((64, 61, -84), kind="rounded")
    on = tuple(shoulder.pts[int(np.argmin(np.abs(shoulder.pts[:, 2] + 68)))])
    s.mark("body", "satin", marks.disc(), size=16, at=on, colour=INK, across=True)
    s.mark("body", "satin", marks.ring(0.82), size=16, at=on, colour=GOLD, across=True)
    s.mark("body", "satin", marks.star(5), size=9, at=on, colour=RED, across=True)
    s.step("The emblem over the nose's seam", "The emblem 22 cm wide pressed over the seam between the nose tip and the "
           "body shell, on the car's middle.")
    s.decal(emblem(), "body", width=22, at=(0, None, 150), across=True)
    s.step("Words along the nose's edge", "ALONG THE EDGE, 4 cm tall, reading along the model's line on the nose's rounded "
           "edge, each letter following it, both sides.")
    s.text("ALONG THE EDGE", "body shell", colour=INK, height=4, at=meshlines.line((27.2, 54.2, 120), kind="rounded").between(150, 90))
    s.step("Words over the flank's turn", "FLANK, 8 cm tall, where the front flank turns from the side onto the top; the "
           "note says how far the surface turns under it.")
    s.text("FLANK", "body shell", colour=INK, height=8, at=tuple(meshlines._closest(np.array([37.0, 58.0, 68.0]))[1]))
    s.step("A disc asked for from above", "A red disc 10 cm wide on the rear quarter panel at (30, ?, -60), seen from "
           "above, and a gold one on the sidepod top at (76, ?, -22).")
    s.mark("rear quarter panel", "satin", marks.disc(), size=10, at=(30, None, -60), colour=RED)
    s.mark("sidepod top", "satin", marks.disc(), size=10, at=(76, None, -22), colour=GOLD)
    s.step("A word on the side", "SEVEN, 10 cm tall, at the left side spot, white with a dark outline.")
    s.text("SEVEN", "left side", colour=WHITE, font="russo", height=10, outline=INK)
    s.step("A placard on a drawn line", "NO STEP in a thin box, 2.6 cm tall, on a line drawn across the deck from the tail "
           "corner towards the sidepod, reading along its middle stretch.")
    drawn = course.stroke([(42.8, 64.0, -128.1), (50.0, 63.6, -100.0), (58.6, 63.0, -78.6), (76.4, 60.8, -50.0)])
    s.placard("NO STEP", "body", at=drawn.between(-110, -88), height=2.6, colour=INK, mirror=False)
    s.step("Stickers", "Small stickers 5 cm wide scattered over the sidepod tops and the engine cover, spaced along the "
           "surface, none across a crisp line.")
    s.scatter(sticker(), ["sidepod top", "engine cover|part"], size=5, seed=3)
