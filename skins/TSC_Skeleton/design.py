"""The skeleton car: the painter's guides on the clay car (tool/levels.py), as the levels room draws
them: the top line and the bottom line in black, the levels between in blue, and the top's lines
over the top in pink."""
from tool import levels

WORDS = ("the purpose of these guides is that you as the painter can guide yourself to painting ... "
         "for you to have a bit better eyes to painting")
BLACK, BLUE, PINK = "#0a0a0a", "#1d4ed8", "#e0115f"


def design(s):
    s.clay()
    body = sorted({i["name"] for i in s.parts.instances if i["mesh"] == "Skin"} - set(levels.WHEELS) - set(levels.OFF))
    outer = [f"{b}|part" for b in body]
    drawn = {L["name"] for L in levels.load()["levels"]}
    s.step("The top and the bottom", "The top line and the bottom line in black.", words=WORDS)
    for name, *_ in levels.curves():
        if name in drawn:
            s.paint(outer, "matte", colour=BLACK, zone=levels.line(name))
    s.step("The lines between", "The levels between in blue.", words=WORDS)
    for name, *_ in levels.curves():
        if name not in drawn:
            s.paint(outer, "matte", colour=BLUE, zone=levels.line(name))
    s.step("The lines over the top", "The top's lines in pink.", words=WORDS)
    for L in levels.top_lines():
        s.paint(outer, "matte", colour=PINK, zone=levels.top_line(L["name"]))
