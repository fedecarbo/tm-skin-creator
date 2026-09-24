"""Dots version 3: placed on the surface and then settled into even spacing, honeycomb-like, no breaks."""


def design(s):
    s.paint("body", "polka dots", palette=["racing red", "white"], scale=9, dot=0.5)
    s.paint("wheel cover ring", "gloss white")
    s.paint("inner", "charcoal satin")
    s.paint("rim", "gloss white")
