"""Stealth bomber: flat dark grey, glossy black panel lines along the main seams."""
from tool import shapes

MAIN = ["body shell", "cockpit surround", "nose tip", "nose panel", "sidepod top", "sidepod inlet",
        "side skirt", "rear flank", "engine cover", "tail panel", "rear quarter panel", "tail corner", "diffuser"]


def design(s):
    s.paint("body", "matte", colour="#232528")
    s.paint("body", "gloss", colour="#26282b", zone=shapes.seams(1.5, parts=MAIN))
    s.paint("inner", "satin", colour="#2a2b2e")
    s.paint("rim", "gunmetal")
    s.paint("brake caliper", "satin", colour="#232528")
    s.paint("seat", "black leather")
