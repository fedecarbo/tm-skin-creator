"""A candy car: bubblegum-pink candy paint with donuts sprinkled all over it, each donut its own
sticker (tool/pictures.py made them: art/donut_pink.png, art/donut_choc.png). Chocolate inner
car, cream wheel-cover rings, mint calipers."""


def design(s):
    s.paint("body", "hot pink candy")
    s.scatter([s.art("donut_pink"), s.art("donut_choc")], "body", size=(9, 12), spacing=14, turn="random", seed=5)
    s.paint(["nose tip", "wing pylon", "diffuser", "diffuser strake"], "gloss chocolate")
    s.paint("wheel cover ring", "gloss cream")
    s.paint("inner", "chocolate satin")
    s.paint("rim", "gloss cream")
    s.paint("brake caliper", "mint")
    s.paint("seat", "black leather")
    s.text("DONUT", "left flank", colour="cream", font="russo", height=9, at=(35, 62, 60))
    s.text("DONUT", "right flank", colour="cream", font="russo", height=9, at=(-35, 62, 60))
