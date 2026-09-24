"""The donut car with a matte body and glossy plastic donuts (the user asked whether a sticker can have its own finish, 2026-09-24). A candy car: bubblegum-pink candy paint with donuts sprinkled all over it, each donut its own
sticker (tool/pictures.py made them: art/donut_pink.png, art/donut_choc.png). Chocolate inner
car, cream wheel-cover rings, mint calipers."""


def design(s):
    s.paint("body", "matte hot pink")
    s.scatter([s.art("donut_pink"), s.art("donut_choc")], "body", size=(9, 12), spacing=14, turn="random", seed=5, finish="gloss plastic")
    s.paint(["nose tip", "wing pylon", "diffuser", "diffuser strake"], "gloss chocolate")
    s.paint("inner", "chocolate satin")
    s.paint("wheel covers", "gloss cream")
    s.paint("rim", "gloss cream")
    s.paint("brake caliper", "mint")
    s.paint("seat", "black leather")
    s.text("DONUT", "left flank", colour="cream", font="russo", height=9, at=(35, 62, 60))
    s.text("DONUT", "right flank", colour="cream", font="russo", height=9, at=(-35, 62, 60))
