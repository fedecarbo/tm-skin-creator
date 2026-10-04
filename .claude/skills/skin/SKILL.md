---
name: skin
description: Make a Trackmania car skin from the user's words and put it in their game. Design it with the paint box, show it on the car, change it until they say yes, then install it. Use for every request to make, change, compare, show, install or pick up a skin, however vague ("something with flames", "make the wheels gold", "back to the ice cream car", "install it").
argument-hint: "[what the skin should look like]"
---

# Skins from words

The user describes a skin, sees it on the car, asks for changes, says yes, and it's in the game.
Their words, if they came with the command: $ARGUMENTS
If they haven't said what they want yet, ask: **what skin would you like?**

`RULES.md` applies throughout. In short: paint it, show it, change it from their notes. A clear idea
gets one design; a loose one 2 or 3 takes as a set, each a different reading, painted one after the
other. The first picture comes within minutes of their words.

## Commands

From the repo root. `PY` is the tool's Python (`CLAUDE.md`). The Mac has no picture maker and no
game: install from the Windows PC after a push.

| Command | What it does |
|---|---|
| `PY -m tool.skin show <name>` | Paints `skins/<name>/design.py`, puts it in the viewer and the Lab, saves six views to `build/<name>_views.png`. Read every note it prints, and its measures: where each zoned paint on the body stops short of the car or leaves a gap, in cm, and why. |
| `PY -m tool.snap <name> --close` | Ten close looks → `build/<name>_close.png` (bonnet, nose, front flank fold, sidepod, rear flank, deck and tail, right side, front wheel, driving camera, tail corner). `--before`: each tile that changed since the last sheet, before beside after. |
| `PY -m tool.snap <name> --cams` | The game's chase cameras, by day and at night. |
| `PY -m tool.snap <A> [<B> <C>] --picture --titles "…" [--views front rear top] [--close-row <name> 3 4 9]` | The picture for the user, a row per take; opens on their screen. |
| `PY -m tool.swatches` (background) | Serves the Lab, http://localhost:8765/lab.html: the car, the user's notes on it, the chat beside it, the materials and the UV map. |
| `PY -m tool.skin install <name>` | Paints it, builds the game files and installs them (the PC). |
| `PY -m tool.publish` | The skins in the game on the page online (the PC, after an install). |
| `PY -m tool.skin list` / `PY -m tool.sets <car>` | Every skin / a car's sets of options. |
| `PY -m tool.pictures decal "<words>" [--style …] [-n 4]`, `tile "<words>"`, `keep <slug> <k> <skin> <name>` | The picture maker (the PC): cut-outs or seamless tiles, kept as `skins/<skin>/art/<name>.png` for `s.art("<name>")`. Ask for a few large objects; give each run its own words. |
| `PY -m tool.textures search "<surface>"`, then `add "<surface>" <Id> --scale <cm>` | A photographed surface (ambientCG, CC0) as a finish. |
| `PY -m tool.tyres [TY-01 ...]` | The tyre markings library on the car. |

## Designing

- A design is `skins/<name>/design.py`: a `design(s)` function of `paintbox.Skin` calls. Before the
  first design in a session, read the docstrings of `tool/paintbox.py` (the key), `tool/shapes.py`
  (zones) and `tool/finishes.py`. Part names are in `car/parts.json`.
- Start with `s.clay()` (any part no step paints stays clay, in the game too) and open each step
  with `s.step(name, does, words=<the user's words>)`; the Lab shows the car at the end of each.
  A change edits its step.
- Names: `TSC_<Idea>` in CamelCase. A change edits that skin unless the user wants both.
  `borrow("TSC_X")` (`tool.skin`) builds on another skin's design, only when the user names it.
- Something the box can't do: write it, in `tool/` if it's reusable. A new finish goes at the end of
  its family in `finishes.CATALOGUE`.
- Read only when a design needs it: `car/map.md` and its pictures (the body's areas, openings and
  panels, for `shapes.area`, `outside`, `along`, `near`, `streamlines`), and `tool/skindraw.py`'s
  docstring (lines, stripes, bands and rings drawn on the skin).

## What the car allows

- **Wheels and tyres are their own paint.** "body" leaves out the wheel covers; paint "wheels"
  (covers, rims, hubs, rings) and "tyres" with their own calls. All four share one paint, and the
  right tyres are the left's mirror: words read backwards there unless every letter is one of
  B C D E H I K O X 0 3 8. Tyre markings and treads come from the library: `s.tyre_marks("TY-..")`,
  `s.tyre_tread("TR-..")`.
- **Shared paint.** Most inner parts share their paint with their twin on the other side, and some
  with other parts. `show` names every part a colour also lands on: read it.
- **Keep clear** of the number panel (x ±19, z -78 to -62) and the engine cover panel (x ±19,
  z -120 to -82), where the game letters the player's number and name, and the nose fin's plate
  (x ±8, z 118 to 142).
- **Pictures** go on the flat spots (`SPOTS` in `tool/paintbox.py`): the rear flanks and the bonnet;
  the front flank's top strip takes lettering only. `show` reports a decal that crosses a fold.
  Objects: `s.scatter` (whole copies). A continuous texture: a tile through `s.print`.
- **Lines** are drawn on the skin (`tool/skindraw.py`): probe a route first (`PY -m tool.skindraw
  --probe "place, place"`), 3 mm or more to be seen while driving (2 mm is the thinnest that holds),
  and `PY -m tool.skincheck <name>` after painting. The cockpit leaves no skin down the top's middle
  from z +70 to -45.
- **Edges are crisp** (a zone's edge is 0.2 cm). Paint can't fake big 3D shapes; a painted shadow
  must be even all round. Fine grain goes in the sheen, not the colour (compression flattens it).
- **Glows light the inner car only**: `s.glow(part, colour, kind)`: always on, night only, front
  lights, brake lights, brake heat, turbo. Exhaust heat and boost were never seen to light up.
- **The car's own lights take any colour**: `s.relight("speed numbers" | "brake lights" | "rear
  lights" | "wheel ring", colour)` (`keep_level=True` for a faint one, the wheel ring). Braking turns the rear lights red whatever their colour, and a
  tinted rear lens filters that red. `s.glass(colour, strength)` only tints, lights behind it too.
- **Can't be done** (say so if asked): holographic or colour-shift paint, relief on the body, the
  player's number and name or their colour, the turbo colour, the tyres' mapping.

## The Lab: notes, sets and questions

- **Notes on the car**: the user clicks the car and writes, or writes in the box under the chat.
  Notes arrive with their next message (a hook prints them) or at once while you wait (`PY -m
  tool.notes wait` in the background). Each has the skin, its number, the part clicked as a `where`
  phrase, their words and a picture of what they saw: look at it. Act on it in that skin, then
  `PY -m tool.notes done <skin> <n> --say "<what changed, a sentence>"`. `tool.notes say <car> "…"`
  for anything else.
- **Lines copied from the Lab** (`ME-07 Gold (…)`, `floor|left|part (…)`): the code is that finish,
  the phrase before the bracket that part.
- **Sets of options** (painted takes): `tool.sets new <car> "<what>" --words "<their words>"`,
  `tool.sets option <car> <n> "<Title>"` for each (a copy of the design to change), paint each and
  look at its views, then `tool.sets open <car> <n>` with a line (`tool.notes say`). The pick:
  `tool.sets pick <car> <n> <letter> "<what>"` (the others go), then `show <car>` and its close
  looks. "None of these" or a mix in their words: change an option, then pick it, or `tool.sets drop`.
- **Questions** (anything else to pick or confirm): `PY -m tool.notes ask <car> "<question>"
  --choice "<label>" [--colour "#rrggbb"] [--picture <png>] --choice … [--several]`, or `--yes` for
  yes or no. Ask the same in one bold line in the reply. Answered in the chat instead: `tool.notes
  settle <car> <k> "<what was decided>"`.
- After a set or a question, start `PY -m tool.notes wait` in the background and end the turn: the
  answer arrives as a note.

## Before showing

1. Fix what show's measures say STOPS SHORT or GAP, then look at the six views. For a set's takes, that's enough.
2. A design shown alone, or a pick: `tool.snap <name> --close`, and look where graphics meet a
   join, fold, hole or edge: nothing cut, sunk, stretched or soft.
3. The whole car: every visible part serves the idea, the lights at night, no paint left from an
   earlier version, no part left in clay by accident (`show` names them). Fix and look again.

## Showing and installing

- The picture (`tool.snap … --picture`) and the Lab. Reply in a few sentences: what the car looks
  like and what you checked close up, then one bold question.
- On their yes: `tool.skin install <name>` on the PC, then `tool.publish`. In the game: Garage → My
  Skins → pick `<name>`, no restart needed.
- Screenshots (F12) are in
  `C:\Program Files (x86)\Steam\userdata\53610290\760\remote\2225070\screenshots\`; look only at
  ones taken after the install.

## The record and the improvement list

- `skins/<name>/notes.md`: the user's words verbatim, the date and the model, how you read them,
  then a line per event (`Shown`, `Change <n> (user): "…"`, `Installed`). A cold session must be able
  to pick up the skin from it and `design.py`.
- `IMPROVEMENTS.md` is the queue of what the tool should do better. During a skin fix only what
  the skin needs; put anything else on the list in two or three lines and tell the user in one.
  Work on the list when they ask; a finished item is deleted.
