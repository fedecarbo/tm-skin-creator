# Answers (both_2: atlas + ask tool)

1. Nose end (24, 18, 149), tail end (77, 22, 17). The course `meshlines.line("side skirt crease 2")` starts at the
   NOSE end (c.start = (24, 18, 149)) and ends at the tail end (77, 22, 17).
   From: `ask.py line "side skirt crease 2"` (agrees with atlas_side.png legend line 18 and cards_1.png card 18).

2. The course runs TAIL first (c.start = (40, 66, -82)), so `deck.between(deck.start, deck.at(z=-60))` is the
   22 cm from z -82 to z -60: the BACK part of the roll (the roll runs z 38 to -82), a 3 cm band wrapping it.
   From: `ask.py line "body shell roll 2"`, `ask.py stretch "body shell roll 2" tail 22`
   (atlas legend line 20: "course runs TAIL first: start z -82, end z 38").

3. Panel: sidepod top panel 1. The part under the point is the sidepod inlet (left), though the panel belongs to
   the sidepod top; the tool says the surface there faces down and out to the car's left.
   From: `ask.py at 70 61 -26` (panel also confirmed by `ask.py panel "sidepod top panel 1"`).

4. Centre (64, 36, -80), facing out to the car's left and back: a 37 cm flat room, enough for a 25 cm badge
   (the other flat room, 28 cm at (81, 31, -51), would also take it).
   From: `ask.py flat "rear flank"`.

5. It STOPS at the sidepod inlet's edge. The sidepod inlet is a piece of its own, with a gap of 1.4 cm to the
   sidepod top; a line or a band along it stops at the gap as a wrap would, so it does not run on onto the
   sidepod top or the body shell.
   From: `ask.py part "sidepod inlet"` (and `ask.py line "sidepod inlet edge 1"`: an edge where the body ends).

6. Yes: the number panel. engine cover seam 2 is the loop round the number panel (z -62 to -78, x -20 to 20), so a
   placard on its z -74..-62 stretch lies on or within 3 cm of the number panel, which the game letters with the
   player's number: KEEP CLEAR, the judge BLOCKS it (nothing on it or within 3 cm).
   From: `ask.py line "engine cover seam 2"`, `ask.py part "number panel"`, `ask.py at 0 82 -68`; SKILL.md "Keep clear".

7. Body set: wheel cover disc, wheel cover hub, wheel cover ring. Inner-car set: hub, rim, wheel ring, and the
   brake light (shared paint).
   From: `ask.py paint wheels`.

8. side skirt crease 2 (a crisp line): 146 cm, from (24, 18, 149) back to (77, 22, 17).
   From: `ask.py line "side skirt crease 2"`; atlas_side.png legend line 18 (start z 149, end z 17).

9. In front of it (nearer the nose). The inlet's forward-facing mouth is at its front end: at (60, 52, 15) the inlet
   faces out and forward, its crease turns 87 degrees at (55, 50, 19) (the mouth's front corner), and the panel
   shows in atlas_front.png (panel I inside loop 9); the flat room sits at z -26, behind that, above the inlet's
   middle. (Moderate confidence: "opening" read as the forward-facing mouth.)
   From: `ask.py at 60 52 15`, `ask.py line "sidepod inlet crease 1"`, `ask.py part "sidepod inlet"`, atlas_front.png.

10. Two: the sidepod inlet (left and right), a gap of 1.4 cm to the sidepod top; and the tail panel together with
    the tail corners (one piece), a gap of 1.7 cm to the body shell. The sidepod top is only sewn on (0.41 cm
    from the body shell: a line runs across). The diffuser and diffuser strake form a separate 2-part skin, but the
    tool gives no gap for them, so I don't know whether they count. Everything else is the main 13-part skin.
    From: `ask.py part "<name>"` for every body part (sidepod inlet, sidepod top, tail panel, tail corner, body shell,
    engine cover, engine cover panel, number panel, rear flank, nose tip, wing pylon, side skirt, cockpit surround,
    diffuser, diffuser strake, nose panel, rear quarter panel, nose fin, wheel cover disc/hub/ring).

## Commands run
- `PY ask.py` (help)
- `PY ask.py line "side skirt crease 2"`, `line "body shell roll 2"`, `line "sidepod inlet edge 1"`,
  `line "engine cover seam 2"`, `line "sidepod inlet crease 1"`
- `PY ask.py at 70 61 -26`, `at 0 82 -68`, `at 60 52 15`, `at 80 52 -45`, `at 69 49 -17`
- `PY ask.py flat "rear flank"`, `flat "sidepod top"`
- `PY ask.py paint wheels`
- `PY ask.py find skirt`, `find e`
- `PY ask.py stretch "body shell roll 2" tail 22`
- `PY ask.py panel "sidepod top panel 1"`, `panel "sidepod inlet panel 1"`, `panel "engine cover panel 1"`
- `PY ask.py part "<name>"` for: sidepod inlet, sidepod top, number panel, body shell, engine cover, engine cover panel,
  rear flank, nose tip, wing pylon, side skirt, cockpit surround, diffuser, diffuser strake, tail panel, nose panel,
  tail corner, rear quarter panel, nose fin, wheel cover disc, wheel cover hub, wheel cover ring
- Pictures looked at: atlas_side.png, atlas_top.png, atlas_front.png, cards_1.png; read SKILL.md.

## Time
About 7–8 minutes for the whole quiz (four rounds of commands, most of it the tool's own run time).
