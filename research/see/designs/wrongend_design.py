"""The 21 October mistake replayed: a streak meant for the FRONT of the deck's shoulder, cut from c.start, which is the tail end."""
from tool import meshlines


def design(s):
    s.clay()
    s.step("Base", "A white body.")
    s.paint("body", "gloss white")
    s.step("The streak", "A black streak along the shoulder's front stretch, from the roll's start back to z -60.")
    deck = meshlines.line("body shell roll 2", tilt=33)
    s.paint("body", "gloss black", zone=deck.between(deck.start, deck.at(z=-60)).band(3))
