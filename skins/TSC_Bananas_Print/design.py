"""The banana print as one continuous sheet (a seamless tile from tool/pictures.py, art/bananas.png)
laid in the car's own unfolding, with the panels lined up along their seams. For comparison
with TSC_Bananas, where each banana is its own sticker and never crosses a seam."""


def design(s):
    s.print("bananas", scale=36)  # 36 cm per repeat of the tile: bananas about 8 cm long
    s.paint("body", "bananas")
    s.paint(["nose tip", "wing pylon", "diffuser", "diffuser strake"], "gloss dark brown")
    s.paint("inner", "dark brown satin")
    s.paint("wheel covers", "gloss cream")
    s.paint("rim", "gold")
    s.paint("brake caliper", "yellow")
    s.paint("seat", "black leather")
    s.text("BANANA", "left flank", colour="dark brown", font="teko", height=9, weight=600, at=(35, 62, 60))
    s.text("BANANA", "right flank", colour="dark brown", font="teko", height=9, weight=600, at=(-35, 62, 60))
