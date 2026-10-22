# Answers (ask_2: the question tool + the paint skill only)

`ask` below means `PY scratchpad/see/ask.py`.

1. Nose end (24, 18, 149), tail end (77, 22, 17): it runs z 149 (front) to z 17 (back), low near the ground.
   The course `meshlines.line("side skirt crease 2")` starts at its NOSE end (c.start = (24, 18, 149)).
   From: `ask line "side skirt crease 2"`

2. The course of `body shell roll 2` (tilt 33) runs TAIL first: c.start is the tail end (40, 66, -82). So
   `deck.between(deck.start, deck.at(z=-60)).band(3)` covers z -82 to z -60 (22 cm, from (40, 66, -82) to
   (42, 66, -60)): the BACK part of the roll, up by the engine cover, not the front.
   From: `ask line "body shell roll 2"`; `ask stretch "body shell roll 2" tail 22`

3. Panel: `sidepod top panel 1` (2459 cm2, z 12 to -50, faces up and out to the left). The part the tool names
   under that exact point is the sidepod inlet (left), facing down and out; the panel itself belongs to the sidepod
   top, and the point is the centre of the sidepod top's flat room (28 cm across, facing up).
   From: `ask at 70 61 -26`; `ask panel "sidepod top panel 1"`

4. Centre (64, 36, -80) on the rear flank (rear flank panel 1), facing out to the car's left and back: flat room
   37 cm across there, so a 25 cm badge reads flat. (Second choice: (81, 31, -51), 28 cm across.)
   From: `ask flat "rear flank"`; `ask at 64 36 -80`

5. It STOPS at the sidepod inlet's edge. The sidepod inlet is a piece of its own, with a gap of 1.4 cm to the
   sidepod top; a line or a band along it stops at the gap as a wrap would (unlike the sidepod top, which is sewn
   on 0.41 cm from the body shell, where a line runs on across the join). `sidepod inlet edge 1` is a closed loop
   (182 cm) where the body ends, round z 19 to -51.
   From: `ask part "sidepod inlet"`; `ask line "sidepod inlet edge 1"`; `ask part "sidepod top"`

6. Yes: `engine cover seam 2` is the closed seam round the NUMBER PANEL (z -62 to -78, x -20 to 20, on the deck),
   so a placard along it between z -74 and -62 sits on or within 3 cm of the number panel, where the game letters
   the player's number. KEEP CLEAR: the judge BLOCKS it (a decal is moved or shrunk until it is clear; `show`
   names anything on or round it). The engine cover panel (the name, z -81 to -120) is not touched by that stretch.
   From: `ask line "engine cover seam 2"`; `ask part "number panel"`; `ask part "engine cover panel"`; SKILL.md "Keep clear"

7. Gold lands on the body set's wheel cover disc, wheel cover hub and wheel cover ring, and on the inner car set's
   brake light, hub, rim and wheel ring (all four wheels share one paint).
   From: `ask paint wheels`; SKILL.md "Wheels and tyres are their own paint"

8. `side skirt crease 2`, 146 cm, nose end (24, 18, 149) to tail end (77, 22, 17). (The nearest other candidate,
   `side skirt roll 3`, runs z 149 to 23 and is 140 cm.)
   From: `ask list`; `ask find skirt`; `ask line "side skirt crease 2"`

9. In front of it (nearer the nose, i.e. to your right). The sidepod inlet runs z 19 (front) to -51 and faces out
   and FORWARD at its front end (at (60, 52, 17) it faces left and forward, by the inlet's edge and crease), while
   the flat room on the sidepod top is at z -26, further back. (The tool never names an "opening" as such; this
   reads the forward-facing front end at z 19 as the opening.)
   From: `ask part "sidepod inlet"`; `ask at 60 52 17`; `ask at 78 50 -45`; `ask at 70 61 -26`

10. Two: the sidepod inlet (gap 1.4 cm to the sidepod top) and the tail corner together with the tail panel (one
    piece, gap 1.7 cm to the body shell). Everything else in the body is part of the main skin (body shell, rear
    flank, side skirt, nose tip, nose panel, nose fin, wing pylon, cockpit surround, engine cover, number panel,
    engine cover panel, fuel cap, rear quarter panel; diffuser with diffuser strake), where a band runs on across
    the seams; the sidepod top is sewn on at 0.41 cm (under 1 cm, a line runs on). The wheel covers (disc, hub,
    ring) the tool only describes as sharing 100 % of their paint: no gap given, so don't know for those.
    From: `ask part "<name>"` for every body part in `ask list`'s Parts line

## Every command run

- `ask` (no arguments)
- `ask line "side skirt crease 2"`
- `ask line "body shell roll 2"`
- `ask at 70 61 -26`
- `ask flat "rear flank"`
- `ask line "sidepod inlet edge 1"`
- `ask part "sidepod inlet"`
- `ask line "engine cover seam 2"`
- `ask paint wheels`
- `ask find skirt`
- `ask list`
- `ask stretch "body shell roll 2" tail 22`
- `ask panel "sidepod top panel 1"`
- `ask panel "sidepod inlet panel 1"`
- `ask part "sidepod top"`
- `ask at 64 36 -80`
- `ask panel "engine cover panel 1"`
- `ask part "number panel"`, `ask part "engine cover panel"`, `ask part "engine cover"`, `ask part "nose fin"`
- `ask part` for: body shell, cockpit surround, rear flank, side skirt, tail corner, tail panel, nose tip, nose
  panel, wing pylon, diffuser, diffuser strake, fuel cap, rear quarter panel, wheel cover disc, wheel cover hub,
  wheel cover ring (each twice: once filtered too hard by grep, once again to read the piece/seam line)
- `ask at 60 52 17`, `ask at 78 50 -45`, `ask line "sidepod inlet crease 1"`
- `sed -n '1,400p' .claude/skills/paint/SKILL.md`

About 55 ask calls in four parallel batches; the whole quiz took roughly 7 minutes (10:23 to 10:30).
