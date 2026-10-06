# The car's anatomy

Written by `python -m tool.carmap --describe` from the car's own shape (2026-10-06): how the body flows, where it's calm, what the player sees and where a graphic stops. Read it before a design, and follow these lines and rooms where the idea needs them, never by rule. Lengths in cm: x out to the car's left (the right mirrors it), y up from the ground, z forward (the nose's tip at 215, the tail at -162). The map in numbers (each slice, piece, opening and panel): `car/map/tables.md`.

## How the body flows

The body's own lines: every crease and rolled edge 25 cm or longer that stands out from the skin round it and is on the outside, the longest first, each from its front end through the corners where it turns. `car/map/flow.jpg` draws each in its colour on the bare body. A marking along one: `course.flow(near)`, the line nearest a point (`tool/course.py`).

1. **red**: a crease, 230 cm, rolled over 6 cm, along the side skirt and rear flank: (31, 18, 99) → (48, 19, 53) turning 20° → (77, 21, 16) turning 29° → (82, 22, -10) turning 20° → (77, 19, -44) turning 25° → (53, 17, -80) turning 23° → (48, 17, -107).
2. **orange**: the lower edge, 196 cm, rolled over 4 cm, along the body shell and nose tip: (-1, 40, 211) → (12, 41, 207) turning 51° → (16, 42, 198) → (40, 59, 42) turning 16° → (44, 58, 30).
3. **yellow**: the shoulder, 166 cm, rolled over 7 cm, along the rear flank, tail corner and tail panel: (83, 58, -50) → (52, 63, -103) turning 25° → (46, 63, -155) turning 76° → (-1, 63, -161).
4. **green**: the shoulder, 156 cm, rolled over 9 cm, along the body shell and nose tip: (16, 44, 192) → (13, 51, 177) turning 20° → (24, 75, 42).
5. **teal**: a crease, 124 cm, rolled over 2 cm, along the side skirt: (-1, 17, 214) → (11, 18, 212) turning 52° → (16, 18, 203) turning 22° → (23, 16, 140) → (31, 18, 104).
6. **blue**: an opening's rim, 98 cm, sharp, along the sidepod top, body shell and rear flank: (55, 61, 11) → (57, 62, -47) turning 84° → (81, 60, -49) turning 64° → (86, 47, -43).
7. **violet**: the lower edge, 79 cm, rolled over 2 cm, along the rear flank and tail corner: (52, 24, -95) → (50, 23, -116) turning 19° → (50, 30, -142) turning 50° → (50, 56, -153).
8. **magenta**: an opening's rim, 50 cm, rolled over 4 cm, along the engine cover, tail panel and rear flank: (48, 63, -126) → (0, 66, -133).
9. **brown**: an opening's rim, 49 cm, rolled over 10 cm, along the sidepod top and rear flank: (84, 29, -3) → (85, 30, -27) turning 41° → (86, 44, -42).
10. **black**: an opening's rim, 43 cm, rolled over 3 cm, along the side skirt and sidepod top: (77, 26, 17) → (82, 26, 4) turning 21° → (83, 25, -24).
11. **pink**: an opening's rim, 37 cm, rolled over 2 cm, along the cockpit surround: (25, 79, 16) → (28, 81, -20).
12. **lime**: an opening's rim, 36 cm, rolled over 2 cm, along the side skirt: (48, 26, 42) → (75, 24, 20).
13. **navy**: the shoulder, 35 cm, rolled over 7 cm, along the sidepod top and sidepod inlet: (83, 58, -11) → (85, 56, -44).
14. **grey**: a crease, 30 cm, rolled over 3 cm, along the rear flank and tail corner: (52, 51, -120) → (51, 51, -148).
15. **cream**: a crease, 28 cm, rolled over 2 cm, along the side skirt: (24, 18, 147) → (27, 18, 122).
16. **olive**: an opening's rim, 27 cm, sharp, along the sidepod inlet: (58, 47, 18) → (77, 46, 2).
17. **not drawn**: an opening's rim, 27 cm, rolled over 2 cm, along the sidepod top and sidepod inlet: (58, 61, 9) → (77, 60, -7).
18. **not drawn**: a join between panels, 26 cm, rolled over 7 cm, along the cockpit surround and body shell: (12, 71, 80) → (14, 75, 57).

## Where it's calm

The flat rooms: on each panel the biggest discs of skin that face within 20 degrees of one way, off its creases and clear of the game's panels, 12 cm across or more: where a badge, words or a picture lie flat (the left side; the right mirrors it).

| panel | across, cm | centre | faces |
|---|---|---|---|
| rear flank | 37 | (64, 36, -80) | out and back |
| rear flank | 28 | (81, 31, -51) | out and back |
| tail panel | 27 | (13, 65, -147) | up |
| sidepod top | 27 | (70, 61, -36) | up |
| sidepod top | 26 | (87, 42, -24) | out |
| body shell | 24 | (33, 69, 34) | up and out |
| body shell | 22 | (10, 67, 102) | up |
| engine cover | 21 | (33, 66, -119) | up |
| engine cover | 19 | (34, 71, -97) | up and out |
| rear quarter panel | 19 | (33, 75, -62) | up and out |
| tail corner | 18 | (39, 64, -145) | up |
| nose tip | 16 | (7, 46, 194) | up |
| side skirt | 15 | (27, 20, 84) | up |
| sidepod inlet | 13 | (73, 46, -5) | up |
| cockpit surround | 12 | (31, 76, -1) | up and out |
| cockpit surround | 12 | (32, 77, -24) | up and out |
| nose panel | 12 | (6, 58, 151) | up |

## What the player sees

The chase cameras show the car from behind and above all race: the top takes 79% of what they see, the sides most of the rest; a graphic on the flanks is for the other players and the replays. By part: body shell 22%, engine cover 17%, rear flank 14%, sidepod top 9%, engine cover panel 8%, tail panel 6%, cockpit surround 6%, tail corner 5%.

## Where a graphic stops

- One skin, sewn, over most of the body: the body shell, rear flank, side skirt, nose tip, wing pylon, cockpit surround, engine cover, rear quarter panel, nose fin, fuel cap, nose panel, engine cover panel and number panel. A band or a line runs on across the seams between them.
- Pieces of their own, a gap of more than 1 cm round them: the tail corner and tail panel, 1.7 cm; the sidepod inlet (each side), 1.4 cm. A line stops there, as a wrap would.
- Pieces sewn on, 1 cm or less from the skin: the diffuser strake and diffuser, 0.05 cm; the sidepod top (each side), 0.41 cm; the diffuser strake, 0.04 cm; the nose fin, 0.35 cm. A line may run on.
- A graphic laid whole (a badge, words, a picture) stays on one piece, and off a fold.
- The cockpit leaves no skin down the top's middle from z 85 to -48, 28 cm out each side.
- Keep clear: the number panel (z -78 to -62) and the engine cover panel (z -120 to -81), which the game letters, and the nose fin's plate (z 118 to 142): nothing on them or within 3 cm (`show` names anything there).
