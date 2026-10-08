# A new car: its visual language, then the car in passes

The user, 2026-10-07: "develop sort of a visual language first, kind of like a brand book", one that "shouldn't
really indicate all the details on where to put what and how", and a car designed as a whole. A change to a car
that exists skips all of this.

What makes a car feel thought of everywhere: one idea and one signature move; a shared DNA, so the smallest mark is
made from the same rules as the biggest; colours with jobs, the accent rare; surfaces as design; something at each
of three distances (far, the chase camera, close up), as much as the concept wants; and the whole car worked at once,
split by layer and size, never by part.

## 1. The language (this session, with the user)

Write `skins/<name>/language.json` from the user's words (and any picture they bring), each heading answered fresh
for this car (`tool/language.py`'s docstring has the keys): the idea and its world; what it is and isn't; the
signature, how it behaves on a body (how it starts, follows the form, ends); the DNA; the colours, each one's job
and share, how two meet; the surfaces, how they age; what lives large, medium and small, and how full the car gets;
what it never does. Draw the signature, the DNA and each size flat, in its colours. It says how, never where: no
list of items to place. Take the idea's feeling, materials and behaviour from its source, and its lines and shapes
from the car's own form (its panels, creases and edges): the source's own geometry laid on the car reads too
literal (the user, 2026-10-07, of a bomber's planform on the car: "it just doesn't go well with the aesthetics of
the car"). `PY -m tool.language <name>` checks it and opens its page; the user changes
it until it's right. It changes later too: when a pass finds the language missing something, the language changes
(and its page), not only the car.

## 2. The composition (this session): three takes, the user picks

A set (`tool.sets new <car> "Composition · 3 takes"`, an option each), each a different reading of the same
language: the big colour areas and the signature on the whole car, base finishes only, no details. Start each
with `s.clay()`. Large shapes cross pieces and end where the car's flow ends, never at a seam. Paint each, look at
its views, open the set. After the pick, write in the record what each big shape is for: the next passes build on
it.

## 3 to 5. Fresh agents, one job each

Start each with the Agent tool. Its brief: the car's name, this file's section for its pass, and to read
`language.json`, the record (`notes.md`) and `design.py` first, then the skin skill's Designing section. Each adds
its own steps (`s.step`), paints with `tool.skin show`, ends on a car `PY -m tool.gate <name>` passes (no pass
starts before), and with a line in the record: what it added and why.

3. **Surfaces**: every part's finish, from the language's surfaces (the inner car, the wheels, the tyres, the
   glass, the lights by day and night), and the texture layer: how it ages, or stays new on purpose.
4. **Details**: large, then medium, then small, each made from the DNA and built off the composition's shapes, as
   many as the language's fullness asks; a quiet area is a choice. Large and medium cross pieces; only small marks
   stay on one. `tool.close <name>` after each size.
5. **Art direction**, by an agent that made none of it: the whole car against the language, from `tool.close
   <name>`'s sheets, `tool.snap <name> --cams` and the views. It changes nothing; it lists what reads as a sticker, is cut where it
   shouldn't be, doesn't belong to the language, or is missing at a size, with where. A fresh agent fixes the
   list, then the art director looks once more.

## 6. The finished car

In the Lab, as for any car (the skin skill's Before showing and Showing). In the reply, the time each pass took.
