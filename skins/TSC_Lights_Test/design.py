"""Checkpoint 9's test: which of the car's lights a skin can colour. Each question has its own
colour, so one screenshot answers it (the key is in notes.md). The body is plain grey so the
colours stand out."""

GREEN, BLUE, MAGENTA, CYAN = "#39ff5a", "#2a6bff", "#ff2bd9", "#19e3ff"


def design(s):
    s.paint("body", "gloss", colour="#7d8087")
    # the speed digits: the stock glow (white, always on) recoloured
    s.relight("digit display", GREEN)
    # the brake lights: the strips behind the front wheels (dim red, flaring when braking)
    s.relight("brake light", BLUE)
    # the rear lights: white in the stock file, red in the game. The glow behind both lenses
    # goes magenta, and the car's left lens is tinted cyan (the right one stays clear):
    # red on both = neither works; magenta = the glow works; cyan on the left = the glass
    # does; blue on the left = both (magenta light through cyan glass)
    s.relight("rear light", MAGENTA)
    s.paint("rear light lens|left", colour=CYAN)
    # the game's initials and number: yellow behind the initials, dark blue behind the number,
    # to see whether the lettering keeps its colour or changes with the panel
    s.paint("number panel", "gloss", colour="#ffd21f")
    s.paint("engine cover panel", "gloss", colour="#16227a")
