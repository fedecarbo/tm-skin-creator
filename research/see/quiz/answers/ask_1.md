# Answers (ask tool), agent "ask_1"

Material used: `.claude/skills/paint/SKILL.md` and the question tool (`ask.py`). Coordinates in cm, x out to the car's left, y up, z forward. `ASK` below is `PY /…/scratchpad/see/ask.py`.

1. Nose end (24, 18, 149), tail end (77, 22, 17): the z-149 end is nearer the nose. `meshlines.line("side skirt crease 2")`
   runs nose first: `c.start` is the nose end, `c.end` the tail end. (146 cm, low along the side skirt.)
   From: `ASK line "side skirt crease 2"`

2. The course of `body shell roll 2` (tilt 33) starts at the TAIL end (40, 66, -82), so `between(start, at(z=-60))` is the
   back part of the roll: z -82 to -60 (about 22 cm, from (40, 66, -82) to (42, 66, -60)); the band of 3 cm sits on that
   stretch, not on the front part (which runs on to z 38).
   From: `ASK line "body shell roll 2"`; `ASK stretch "body shell roll 2" tail 22`

3. Panel: sidepod top panel 1 (2459 cm2, z 12 to -50, y 28 to 63, x 54 to 87, facing up and out), on the sidepod top (left).
   Note: the point tool names the sidepod inlet (left), facing down, as the part nearest that point (the inlet piece hangs
   1.4 cm under the sidepod top there), but the panel is the sidepod top's and its flat room is centred exactly there.
   From: `ASK at 70 61 -26`; `ASK panel "sidepod top panel 1"`; `ASK part "sidepod top"`

4. Centre (64, 36, -80), on rear flank panel 1, facing out to the car's left and back: the rear flank's flat room is 37 cm
   across there, so a 25 cm badge fits with margin. (A second, smaller room: (81, 31, -51), 28 cm across.)
   From: `ASK flat "rear flank"`

5. It stops at the sidepod inlet's edge. The sidepod inlet is a piece of its own, with a 1.4 cm gap to the sidepod top; a
   band is measured along the surface, so at the gap there is no surface to carry it on, and it stops as a wrap would.
   (`sidepod inlet edge 1` is the 182 cm closed loop where that piece's body ends.)
   From: `ASK part "sidepod inlet"`; `ASK line "sidepod inlet edge 1"`

6. Yes: `engine cover seam 2` is the 113 cm loop that bounds the number panel (z -62 to -78, x -20 to 20, on engine cover
   panel 1), so a placard on its z -74 to -62 stretch sits on, or within 3 cm of, the number panel, where the game letters
   the player's number. The judge blocks it (nothing on it or within 3 cm); `show` names it.
   From: `ASK line "engine cover seam 2"`; `ASK part "number panel"`; `ASK at 0 82 -68`; SKILL.md "Keep clear"

7. Body set: wheel cover disc, wheel cover hub, wheel cover ring. Inner-car set: hub, rim, wheel ring, and the brake light.
   From: `ASK paint wheels`

8. `side skirt crease 2`: 146 cm, nose end (24, 18, 149), tail end (77, 22, 17).
   From: `ASK line "side skirt crease 2"`; `ASK find skirt`; `ASK list`

9. In front (to your right, nearer the nose), with a caveat. The inlet piece faces out and forward at its front end
   (z 10 to 19, x 55 to 60), which is nearer the nose than the room at z -26; but the piece itself runs on back under the
   sidepod top's outer edge to z -51, below the room (y 46 to 59 against the room's y 61), so it is also beside/under it.
   The mesh has no separate hole I could name as "the opening".
   From: `ASK part "sidepod inlet"`; `ASK panel "sidepod inlet panel 1"`; `ASK at 60 52 16`; `ASK at 66 50 0`;
   `ASK at 75 48 -40`; `ASK at 62 62 -10`; `ASK line "sidepod inlet crease 1"`

10. Two: the sidepod inlet (left and right), a gap of 1.4 cm to the sidepod top; and the tail panel together with the
    tail corners (one piece), a gap of 1.7 cm to the body shell. The sidepod top is only sewn on (0.41 cm, a line runs
    across). The diffuser and diffuser strake form a skin of their own apart from the main 13 parts, but the tool gives
    no gap for them: don't know whether it is over 1 cm. Everything else is the main skin (a band runs on across seams).
    From: `ASK part "<name>"` for body shell, side skirt, rear flank, engine cover, cockpit surround, nose tip, nose panel,
    nose fin, wing pylon, tail panel, tail corner, diffuser, diffuser strake, rear quarter panel, fuel cap, sidepod top,
    sidepod inlet, number panel, engine cover panel, wheel cover disc/hub/ring

## Every command run (all as `PY ask.py …` from the repo root)

- (no arguments: the help)
- line "side skirt crease 2"; line "body shell roll 2"; at 70 61 -26
- flat "rear flank"; line "sidepod inlet edge 1"; part "sidepod inlet"
- line "engine cover seam 2"; paint wheels; find skirt; list
- stretch "body shell roll 2" tail 22; panel "engine cover panel 1"; part "number panel"; part "engine cover panel"; at 0 82 -68
- panel "sidepod top panel 1"; panel "sidepod inlet panel 1"; part "sidepod top"; flat "sidepod top"; at 70 50 10
- part: body shell, side skirt, rear flank, engine cover, cockpit surround, nose tip, nose panel, nose fin, wing pylon,
  tail panel, tail corner, diffuser, diffuser strake, rear quarter panel, fuel cap, wheel cover disc, wheel cover hub,
  wheel cover ring, front wing, front wing endplate, rear bumper, mirror, side vane
- line "body shell edge 1"; line "sidepod top edge 1"; line "sidepod inlet crease 1"; line "sidepod inlet roll 1"
- at 60 52 16; at 66 50 0; at 75 48 -40; at 80 52 -48; at 58 60 30; at 62 62 -10
  (plus one failed batch of these six where my shell passed the three numbers as one word)
- Also read: .claude/skills/paint/SKILL.md

Time: about 8 minutes of wall clock from first command to writing this file (started 10:23).
