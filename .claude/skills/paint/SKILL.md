---
name: paint
description: The craft of painting a Trackmania car skin with the tools, for any concept that shows the car (the Lab's skin skill reads it first). The commands, how a design is written, what the car allows and what it doesn't, the checks before a car is shown. Read before painting or changing any car.
---

# Painting a car

A car is painted from the user's words, shown, then changed from what they say about it, until they say yes.
`RULES.md` applies throughout. A new car starts with its visual language, then is built in passes: read
`language.md`, beside this file. A change to a car that exists edits it.

## Commands

From the repo root (or a concept's folder: the tools are installed into the venv). `PY` is the tool's Python
(`CLAUDE.md`). The Mac has no picture maker and no game: install from the Windows PC after a push.

| Command | What it does |
|---|---|
| `PY -m tool.skin show <name>` | Paints `skins/<name>/design.py`, puts it in the viewer's data (a concept's page shows it), saves six views to `build/<name>_views.png`. Read every note it prints and the judge's verdict: what BLOCKS (a gap, a step, a kink or a wobble in a line, a band on its edge's other face, a line cut by the body's edge, a fill short of its line, a mark or a picture not whole, a paint stopping short, anything on the game's panels, words bent or upside down), what it warns of (a soft edge, a spill onto a second piece, a paint over another, a picture that will show its pixels, a scatter uneven) and the eye's notes (how a graphic sits against the lines the eye sees: a gap that CLOSES, a SLIVER, a NEAR MISS, a SHALLOW crossing, JUST PAST a line, TOUCHES another paint: the close looks look there; it names, never forbids). |
| `PY -m tool.close <name>` | After a show: close looks along every line and over every decal, square to its face, 20 pixels a cm, both sides alike → `build/<name>_close_<k>.png` (look at each). Measured too: a line's paint missing where the body shows, a shape chipped, a stretch another part hides, the right side differing from the left's mirror, and against the run before, anything that changed outside the steps the edit changed (`build/<name>_close_changed.png`, before beside after). Its findings join the verdict. About 20 s for a busy car. |
| `PY -m tool.snap <name> --cams` | The game's chase cameras, by day and at night. |
| `PY -m tool.snap <A> [<B> <C>] --picture --titles "…" [--views front rear top] [--close-row <name> 3 4 9]` | The picture for the user, a row per take (and close looks by number); opens on their screen. |
| `PY -m tool.gate <name>` | What the gates say of the car now; `--despite "<why>"` lets what blocks go, printing what to tell the user. |
| `PY -m tool.skin install <name>` | Paints it, builds the game files and installs them (the PC). |
| `PY -m tool.skin list` | Every skin, the installed ones marked. |
| `PY -m tool.pictures decal "<words>" [--style …] [-n 4]`, `tile "<words>"`, `keep <slug> <k> <skin> <name>` | The picture maker (the PC): cut-outs or seamless tiles, kept as `skins/<skin>/art/<name>.png` for `s.art("<name>")`. Ask for a few large objects; give each run its own words. |
| `PY -m tool.textures search "<surface>"`, then `add "<surface>" <Id> --scale <cm>` | A photographed surface (ambientCG, CC0) as a finish. |
| `PY -m tool.tyres [TY-01 ...]` | The tyre markings library on the car. |

## Designing

- A design is `skins/<name>/design.py`: a `design(s)` function of `paintbox.Skin` calls. Before the
  first design in a session, read `car/anatomy.md` (how the body is built, where it's calm, where a
  graphic stops) with its picture `car/map/model.jpg`, and the docstrings of
  `tool/paintbox.py` (the key), `tool/shapes.py` (zones), `tool/course.py` (markings along the car's
  lines), `tool/marks.py` (shapes on a panel) and `tool/finishes.py`. Part names are in
  `car/parts.json`.
- Start with `s.clay()` (any part no step paints stays clay, in the game too) and open each step
  with `s.step(name, does, words=<the user's words>)`; a concept's page shows the car at the end of each.
  A change edits its step.
- Names: `TSC_<Idea>` in CamelCase. A change edits that skin unless the user wants both.
  `borrow("TSC_X")` (`tool.skin`) builds on another skin's design, only when the user names it.
- Something the box can't do: write it, in `tool/` if it's reusable. A new finish goes at the end of
  its family in `finishes.CATALOGUE`.

## What the car allows

- **Wheels and tyres are their own paint.** "body" leaves out the wheel covers; paint "wheels"
  (covers, rims, hubs, rings) and "tyres" with their own calls. All four share one paint, and the
  right tyres are the left's mirror: words read backwards there unless every letter is one of
  B C D E H I K O X 0 3 8. Tyre markings and treads come from the library: `s.tyre_marks("TY-..")`,
  `s.tyre_tread("TR-..")`.
- **Shared paint.** Most inner parts share their paint with their twin on the other side, and some
  with other parts. `show` names every part a colour also lands on: read it.
- **Shapes** (a spot, a badge, a roundel, a star) go on a named panel with `s.mark`: pressed onto its
  surface as a sticker is (it follows the panel's curve and wraps a rolled edge; every distance is
  measured along the surface), whole inside its edges, on its own panel (not across one of the
  model's crisp lines) and clear of the game's panels, moved or shrunk until they are. Read its
  notes: moved, shrunk, nothing laid, how it sits (stretched where the surface curves two ways; the
  turn under words). `across=True` presses it on as it is, over every edge and crisp line in its
  footprint, as a sticker over a panel gap. A shape or a stripe meant to cross parts says
  `across=True`; without it a zoned paint on "body" leaves a part painted by its name.
- **Keep clear** of the number panel and the engine cover panel on the deck, where the game letters
  the player's number and name, and of the nose fin's plate: they aren't pieces. `show` names
  anything on them or round them.
- **Words and pictures** are one verb, `s.decal`, laid as shapes are: words (`height=` the capitals'), words in
  a thin box as a small sign (`box=True`, near a point or the line the user drew) or a picture (`width=`), on a
  named panel (both sides, words reading forward on each) or at a named spot (`SPOTS` in `tool/paintbox.py`, one
  side): whole, upright to someone standing beside the car, moved or shrunk until they fit; the receipt says when
  the surface turns more than 20 degrees under words (they read bent: smaller words, or a flatter panel). On an
  inner-car part, `depth=` raises them in its relief instead. Objects: `s.scatter` (whole copies, spaced along the
  surface). A continuous texture: a tile through `s.print`.
- **Every call returns a receipt**, and `show` prints each as the paint goes: what it painted and how much, where a
  mark landed, what it refused, what it found wrong. A part's name or a line's name that isn't one stops the paint
  at once with "did you mean": fix the name, never guess round it.
- **A marking along one of the car's lines** (one of the model's lines: a crease, an edge where the body
  ends, a seam between two of its pieces, a rounded edge's; or a panel's edge) or along
  the line the user drew is a course (`tool/course.py`): a strip, dashes, ticks, spots at its
  places, words reading along it (`at=` a stretch of it, each letter following the line; the
  stretch is their room, on the panel named), in one paint. The user's line comes from the concept that showed
  them the car (the Lab prints its points for `course.stroke`, or for a line picked on the mesh its
  `meshlines.picked(...)` call: exact, use it as it is). 3 mm or more to be seen
  while driving (2 mm is the thinnest that holds). A line through points of your own is
  `course.points(...)`: the straightest way along the surface from each to the next, corners at the
  points. The cockpit leaves no skin down the top's
  middle from z +70 to -45. The model's own crisp lines and panels (the template) are exact and
  named (`car/anatomy.md`; `PY -m tool.meshlines` lists every name, `at x y z` names what lies near a point):
  `meshlines.line("side skirt crease 2")` a course along one (a rounded edge's `("rear flank roll 2", tilt=47)`,
  the tilt picking its line), `meshlines.panel("tail corner panel 1")` a zone filling one right up to its lines
  (`border=` a trim); the names are the left side's, `.mirrored()` or `both=True` for both sides, `side="right"`
  for the right alone;
  `.band(cm, side="seen")` a band of even width on one face beside one, its edge on the line, measured
  along the surface (`.band(cm)` centred, wrapping the edge; `crease=True` stopping at the body's next
  crease); `.offset(cm)` a line beside one, `.extended(start=cm)` one carried on along the surface
  (over a seam, under a frame), `.then(other)` one joined to another.
- **Edges are crisp** (a zone's edge is 0.2 cm). Paint can't fake big 3D shapes; a painted shadow
  must be even all round. Fine grain goes in the sheen, not the colour (compression flattens it).
- **Glows light the inner car only**: `s.glow(part, colour, kind)`: always on, night only, front
  lights, brake lights, brake heat, turbo. Exhaust heat and boost were never seen to light up.
- **The car's own lights take any colour**: `s.relight("speed numbers" | "brake lights" | "rear
  lights" | "wheel ring", colour)` (`keep_level=True` for a faint one, the wheel ring). Braking turns the rear lights red whatever their colour, and a
  tinted rear lens filters that red. `s.glass(colour, strength)` only tints, lights behind it too.
- **Can't be done** (say so if asked): holographic or colour-shift paint, relief on the body, the
  player's number and name or their colour, the turbo colour, the tyres' mapping.

## Before showing

1. Fix what the judge blocks, look at what it warns of, then look at the six views. For a set's
   takes, that's enough.
2. A design shown alone, or a pick: `tool.close <name>`; fix what it blocks, and look at every
   sheet: nothing cut, sunk, stretched or soft, the two sides alike, nothing changed that the edit
   didn't mean.

The gates hold you to both (`tool/gate.py`): a pass's agent, `install` and a concept's own commands (a note
handled, a set opened) refuse a car the judge hasn't passed as it is, and a turn is held once with what's wrong.
What's meant, or still there after about three rounds: `PY -m tool.gate <name> --despite "<why, in plain
words>"`, then tell the user what it printed.
3. The whole car: every visible part serves the idea, the lights at night (none left in a stock
   colour), no paint left from an earlier version, no part left in clay by accident (`show` names
   them). Fix and look again.

## The record

`skins/<name>/notes.md`: the user's words verbatim, the date and the model, how you read them,
then a line per event (`Shown`, `Change <n> (user): "…"`, `Installed`, and `Open (…): …` for
anything left to do, its first word turned to `Closed` once it's done). A cold session must be
able to pick up the skin from it and `design.py`. On the user's yes: `tool.skin install <name>` on the PC; in the
game, Garage → My Skins → pick `<name>`, no restart needed. Their screenshots (F12) are in
`C:\Program Files (x86)\Steam\userdata\53610290\760\remote\2225070\screenshots\`; look only at ones taken after
the install.
