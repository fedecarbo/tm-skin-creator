# Answers (both: atlas + ask tool), fresh agent, 2026-10-22

1. Nose end (24, 18, 149), tail end (77, 22, 17): the z-149 end is nearer the nose. The course
   `meshlines.line("side skirt crease 2")` starts at the NOSE end (c.start = (24, 18, 149), c.end = (77, 22, 17)).
   From: `ask.py line "side skirt crease 2"`; agrees with atlas_side.png legend 18 and cards_1.png card 18.

2. The course runs TAIL first (c.start is the tail end, (40, 66, -82)), so `deck.between(deck.start, deck.at(z=-60))`
   is z -82 to -60: the BACK part of the roll (22 cm of its 121, from (40, 66, -82) to (42, 66, -60)).
   From: `ask.py line "body shell roll 2"` and `ask.py stretch "body shell roll 2" tail 22`; cards_1.png card 20.

3. Panel: sidepod top panel 1 (a panel of the sidepod top; its flat room is centred exactly there, facing up).
   Part: the tool's `at` names the sidepod inlet (left), facing down and out, as the part under the point, while
   the panel belongs to the sidepod top (the inlet's own extent tops out at y 59; the point is 2 cm above it).
   So: sidepod top panel 1, on the sidepod top by its panel; `at` reports the sidepod inlet's surface under it.
   From: `ask.py at 70 61 -26`, `ask.py panel "sidepod top panel 1"`, `ask.py part "sidepod top"`.

4. Centre (64, 36, -80), facing out to the car's left and back: 37 cm of flat room there, so a 25 cm badge fits.
   (A second spot, 28 cm across, at (81, 31, -51).)
   From: `ask.py flat "rear flank"`.

5. It stops at the sidepod inlet's edge. The inlet is a piece of its own with a 1.4 cm gap to the sidepod top,
   and a line or band along it stops at the gap as a wrap would (the line itself is an "edge where the body
   ends", so there is no body beyond it to run onto).
   From: `ask.py part "sidepod inlet"`, `ask.py line "sidepod inlet edge 1"`.

6. Yes: engine cover seam 2 is the closed loop round the number panel (z -62 to -78, x -20 to 20), so a placard
   on z -74 to -62 sits on or within 3 cm of the number panel, which must be kept clear (the game letters the
   player's number there). The judge blocks it: the mark is moved or shrunk until clear, or nothing is laid, and
   show names it.
   From: `ask.py line "engine cover seam 2"`, `ask.py part "number panel"`; SKILL.md "Keep clear".

7. Two sets: the body set's wheel cover disc, wheel cover hub and wheel cover ring; and the inner car set's
   brake light, hub, rim and wheel ring. All four wheels share the one paint.
   From: `ask.py paint wheels`; SKILL.md "Wheels and tyres are their own paint".

8. side skirt crease 2, a crisp line of 146 cm, from (24, 18, 149) to (77, 22, 17).
   From: `ask.py line "side skirt crease 2"`, `ask.py list`; atlas_side.png legend 18.

9. In front of it (nearer the nose). The inlet's forward-facing surface (its opening) is at its front end,
   z 19 to about 10 (points (56, 52, 17) and (60, 52, 10) face "out to the car's left and forward"), while
   the flat room on the sidepod top is at z -26; the inlet's rear reaches of z -45 face only out, not forward.
   From: `ask.py part "sidepod inlet"`, `ask.py at 56 52 17`, `ask.py at 60 52 10`, `ask.py at 75 50 -45`.

10. Two pieces: the sidepod inlet (gap 1.4 cm to the sidepod top) and the tail panel together with the tail
    corner (one piece, gap 1.7 cm to the body shell). Every other body-set part I asked is part of the main
    skin (a band runs on across the seams), the sidepod top only sewn on 0.41 cm from the body shell.
    From: `ask.py part` for sidepod inlet, tail panel, tail corner, sidepod top, body shell, engine cover, rear
    flank, nose tip, wing pylon, side skirt, cockpit surround, diffuser, nose panel, diffuser strake, rear quarter
    panel, engine cover panel, number panel, nose fin, fuel cap, mirror mount, wheel cover disc/hub/ring.

## Commands run (all `PY ask.py ...` from the scratchpad's see/ folder)
- (no arguments: the help)
- line "side skirt crease 2"; line "body shell roll 2"; line "sidepod inlet edge 1"; line "engine cover seam 2"
- at 70 61 -26; at 56 52 17; at 60 52 10; at 75 50 -45; at 69 49 -17
- flat "rear flank"; paint wheels; find skirt; find number; list
- stretch "body shell roll 2" tail 22
- panel "sidepod top panel 1"; panel "sidepod inlet panel 1"; panel "engine cover panel 1"
- part for: sidepod inlet, sidepod top, body shell, engine cover, rear flank, nose tip, wing pylon, side skirt,
  cockpit surround, diffuser, tail panel, nose panel, tail corner, diffuser strake, rear quarter panel, engine
  cover panel, number panel, nose fin, fuel cap, wheel cover disc, wheel cover hub, wheel cover ring, mirror,
  mirror arm, mirror mount, side vane, side vent, rear bumper, rear bumper corner, front wing, front wing
  endplate, rear strake, antenna, airbox, sidepod panel, sidepod frame, sidepod boss, sidepod strut, sidepod
  grille, sidepod grille plate, nose plate, nose inner, canopy, floor, floor edge, rear undertray, wing bracket,
  tail frame, cockpit rim, nose lens
- Also read: SKILL.md, atlas_side.png, atlas_top.png, atlas_front.png, cards_1.png, cards_2.png, cards_3.png

Time: about 10 minutes for the whole quiz (started 10:23), most of it the ask tool's part sweep for question 10.
