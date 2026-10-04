"""The skeleton car: the painter's guides on the clay car (tool/levels.py), as the levels room draws
them: the top line and the bottom line in black, the levels between in blue."""
from tool import levels

WORDS = ("the purpose of these guides is that you as the painter can guide yourself to painting ... "
         "for you to have a bit better eyes to painting")
BLACK, BLUE = "#0a0a0a", "#1d4ed8"


def design(s):
    s.clay()
    body = sorted({i["name"] for i in s.parts.instances if i["mesh"] == "Skin"} - set(levels.WHEELS) - set(levels.OFF))
    outer = [f"{b}|part" for b in body]
    drawn = {L["name"] for L in levels.load()["levels"]}
    s.step("The top and the bottom", "The top line and the bottom line in black.", words=WORDS)
    for name, *_ in levels.curves():
        if name in drawn:
            s.paint(outer, "matte", colour=BLACK, zone=levels.line(name))
    s.step("The levels between", "The levels between in blue, ending on the front wheel opening's edge or in line with it.",
           words=WORDS)
    for name, *_ in levels.curves():
        if name not in drawn:
            s.paint(outer, "matte", colour=BLUE, zone=levels.line(name))
