"""Bananas over a cream body, each one its own small sticker laid flat on the panel, never
crossing a seam (tool/pictures.py made the banana: art/banana.png keeps its prompt and seed).
Brown inner car, gold rims."""


def design(s):
    s.paint("body", "gloss cream")
    s.scatter(s.art("banana"), "body", size=(7, 10), spacing=11, turn="random", seed=3)
    s.paint(["nose tip", "wing pylon", "diffuser", "diffuser strake"], "gloss dark brown")
    s.paint("inner", "dark brown satin")
    s.paint("rim", "gold")
    s.paint("brake caliper", "yellow")
    s.paint("seat", "black leather")
    s.text("BANANA", "left flank", colour="dark brown", font="teko", height=9, weight=600, at=(35, 62, 60))
    s.text("BANANA", "right flank", colour="dark brown", font="teko", height=9, weight=600, at=(-35, 62, 60))
