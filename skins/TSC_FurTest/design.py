"""The pile library's test car (the tool's, 2026-10-11, the user: "an actual fur texture library"): each of the six
photographed piles on its own stretch of the body, in the photo's own colours, to be judged close up on the car."""

from tool import shapes

WORDS = "an actual fur texture library"


def design(s):
    s.clay()
    s.step("The piles", "Six photographed piles along the car, each in its own colours: animal fur on the nose, "
           "teddy fur over the front wheels, velvet over the cockpit, plush on the two sidepod tops (each piece whole, "
           "its own seam the edge), fleece over the deck, plaid fur on the tail.", words=WORDS)
    s.paint("body", "fur")
    s.paint("body", "teddy fur", zone=shapes.band(40, 110), across=True)
    s.paint("body", "velvet", zone=shapes.band(-55, 40), across=True)
    s.paint("sidepod top", "plush")
    s.paint("body", "fleece", zone=shapes.band(-135, -55), across=True)
    s.paint("body", "plaid fur", zone=shapes.behind(-135), across=True)
    s.step("The rest", "The inner car and the wheels in gloss black plastic, the tyres rubber: nothing to distract "
           "from the piles.", words=WORDS)
    s.paint("inner", "gloss plastic", colour="#141414")
    s.paint("wheels", "gloss plastic", colour="#141414")
    s.paint("tyres", "rubber")
