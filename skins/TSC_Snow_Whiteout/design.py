"""Whiteout: a car that melts into the snow. Matte winter camo in snow white, pale grey,
blue-grey and charcoal; charcoal inside, matte grey wheels."""

WORDS = "I want a car that will be used for snow maps."
CAMO = ["#f2f4f5", "#c9cfd4", "#8a96a3", "#3b4048"]


def design(s):
    s.clay()
    s.step("Winter camo", "The body in matte winter camo: snow white, pale grey, blue-grey, charcoal.",
           words=WORDS)
    s.paint("body", "camo", colour=CAMO[0], palette=CAMO, scale=28)

    s.step("Wheels and inner car", "Matte grey wheels, the inner car matte charcoal.", words=WORDS)
    s.paint("wheels", "matte", colour="#8a96a3")
    s.paint("rim", "matte", colour="#3b4048")
    s.paint("inner", "matte", colour="#3b4048")
