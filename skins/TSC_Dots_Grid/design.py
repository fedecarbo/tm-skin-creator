"""Dots version 1: exact rows on each panel, drawn on the car's own unfolding; the rows break where panels meet."""


def design(s):
    s.paint("body", "polka dots", palette=["racing red", "white"], scale=9, dot=0.5, method="grid")
    s.paint("wheel cover ring", "gloss white")
    s.paint("inner", "charcoal satin")
    s.paint("rim", "gloss white")
