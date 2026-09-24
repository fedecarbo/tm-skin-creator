"""Dots version 2: dots placed on the surface one by one, no breaks, but the spacing is uneven."""


def design(s):
    s.paint("body", "polka dots", palette=["racing red", "white"], scale=9, dot=0.5, relax=0)
    s.paint("wheel cover ring", "gloss white")
    s.paint("inner", "charcoal satin")
    s.paint("rim", "gloss white")
