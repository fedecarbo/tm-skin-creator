"""A roaring tiger sticker on each side and on the bonnet, on matte black with orange trim.
The tiger is made by the picture maker (tool/pictures.py): art/tiger.png keeps its prompt and seed."""


def design(s):
    s.paint("body", "matte black")
    s.paint(["nose tip", "wing pylon", "diffuser", "diffuser strake"], "gloss black")
    s.paint("wheel cover", "satin black")
    s.paint("wheel cover ring", "orange")
    s.paint("inner", "dark grey satin")
    s.paint("rim", "gunmetal")
    s.paint("brake caliper", "orange")
    s.paint("seat", "black leather")
    # the flat places on a side: the rear flank behind the sidepod (34 cm) and a thin strip
    # along the top of the front flank; the front flank itself has a deep fold (2026-09-24)
    s.decal(s.art("tiger"), "left side", width=32)
    s.decal(s.art("tiger"), "right side", width=32)
    s.decal(s.art("tiger"), "bonnet", width=42)
    s.text("TIGER", "left flank", colour="orange", font="russo", height=9, at=(35, 62, 60))
    s.text("TIGER", "right flank", colour="orange", font="russo", height=9, at=(-35, 62, 60))
