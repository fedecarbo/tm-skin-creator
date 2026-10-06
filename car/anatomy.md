# The car's anatomy

Written by `python -m tool.carmap --describe` from the car's own shape (2026-10-06): how the body is built, where it's calm and where a graphic stops. Read it before a design, and follow these lines and rooms where the idea needs them, never by rule. Lengths in cm: x out to the car's left (the right mirrors it), y up from the ground, z forward (the nose's tip at 215, the tail at -162). The map in numbers (each slice, piece, opening and panel): `car/map/tables.md`.

## How the body is built

The model's own lines, read off its triangles (`tool/meshlines.py`): exact on the car and on the flat texture alike. The Lab's UV map room draws them (Template), its Mesh button lays them over any car, and `car/map/model.jpg` is the same on the bare body: the model's triangles grey, orange where the body rolls outward across them, violet where it dips in, its crisp lines yellow, red where the body ends, blue where the flat texture is cut. The left side and the middle (the right mirrors the left); every line and panel, with a point on each: `PY -m tool.meshlines`.

### Its crisp lines and edges

Panel lines, crisp folds and where the body ends, 80 cm or longer, the longest first. A marking along one: `meshlines.line(point)`, the point given.

- **a panel line, a groove of 9**, 378 cm, along the cockpit surround, at (23, 77, 33): round, z 91 to -52.
- **a crisp line**, 333 cm, along the body shell, at (0, 70, 92): (-23, 84, -51) → (-36, 73, -37) turning 48° → (-36, 71, 5) turning 29° → (-18, 77, 41) turning 25° → (-12, 70, 88) turning 63° → (0, 70, 92) turning 39° → (12, 70, 88) turning 63° → (18, 77, 41) turning 25° → (36, 71, 5) turning 29° → (36, 73, -37) turning 48° → (23, 84, -51).
- **where the body ends**, 331 cm, along the cockpit surround, at (12, 78, 40): round, z 85 to -48.
- **where the body ends**, 296 cm, along the tail corner and tail panel, at (49, 52, -152): round, z -123 to -161.
- **where the body ends**, 268 cm, along the body shell, rear flank and side skirt, at (81, 60, -49): round, z 44 to -50.
- **where the body ends**, 231 cm, along the body shell, side skirt and nose tip, at (22, 43, 75): round, z 172 to 69.
- **where the body ends**, 222 cm, along the sidepod top, at (85, 31, -32): round, z 12 to -50.
- **where the body ends**, 182 cm, along the sidepod inlet, at (75, 49, -45): round, z 19 to -51.
- **a panel line, a groove of 5**, 155 cm, along the side skirt, at (0, 18, 215): (-24, 18, 149) → (-16, 18, 205) turning 28° → (-10, 18, 214) turning 45° → (0, 18, 215) turning 17° → (10, 18, 214) turning 45° → (16, 18, 205) turning 28° → (24, 18, 149).
- **a panel line, a groove of 4**, 153 cm, along the sidepod top, at (82, 59, -49): (55, 61, 11) → (56, 63, -45) turning 45° → (61, 63, -50) turning 45° → (81, 60, -49) turning 48° → (86, 53, -46) turning 38° → (85, 30, -31) turning 54° → (83, 28, 0).
- **a crisp line**, 146 cm, along the side skirt, at (39, 19, 70): (24, 18, 149) → (39, 19, 70) turning 25° → (77, 22, 17).
- **where the body ends**, 120 cm, along the rear flank, at (52, 45, -104): round, z -94 to -140.
- **a panel line, a groove of 7**, 107 cm, along the nose tip, at (0, 49, 187): (-13, 59, 143) → (-10, 49, 184) turning 72° → (0, 49, 187) turning 28° → (10, 49, 184) turning 72° → (13, 59, 143).
- **a crisp line**, 98 cm, along the rear flank, at (51, 29, -133): (53, 24, -94) → (50, 26, -130) turning 52° → (51, 38, -137) turning 20° → (51, 49, -140) turning 107° → (54, 48, -106).
- **a panel line, a groove of 4**, 88 cm, along the side skirt, at (74, 26, 21): (44, 29, 44) → (49, 26, 42) turning 40° → (78, 26, 16) turning 40° → (84, 26, -25).
- **a panel line, a groove of 12**, 88 cm, along the rear flank, at (58, 63, -81): (77, 61, -49) → (50, 64, -94) turning 20° → (43, 64, -128).
- **a panel line, a groove of 6**, 87 cm, along the engine cover, at (0, 66, -133): (-43, 64, -128) → (43, 64, -128).
- **a crisp line**, 83 cm, along the sidepod inlet, at (69, 46, 9): (56, 56, 14) → (56, 47, 19) turning 105° → (79, 46, -1) turning 46° → (80, 46, -43).
- **where the body ends**, 80 cm, along the diffuser and diffuser strake, at (30, 24, -143): (48, 28, -141) → (42, 24, -141) turning 36° → (-30, 24, -143).

### Its rounded edges

Where the body rolls from facing one way to another, the model's lines run side by side across the roll, one every 1 to 2 cm, each facing its own way (degrees from facing up). Those 80 cm or longer, the longest first. A marking along one: `meshlines.line(point, kind="rounded")`, the point given; along several end to end, or across: `meshlines.picked(points)`.

- 156 cm along the nose tip: (-25, 49, 144) → (-14, 41, 204) turning 56° → (0, 40, 210) turning 48° → (14, 41, 204) turning 56° → (25, 49, 144). 2 lines across it, facing 55° at (0, 41, 210); 79° at (0, 40, 210).
- 153 cm along the side skirt: (-23, 18, 149) → (-15, 18, 205) turning 29° → (-9, 18, 213) turning 45° → (0, 18, 214) turning 17° → (9, 18, 213) turning 45° → (15, 18, 205) turning 29° → (23, 18, 149). One line, facing 24° at (0, 18, 214).
- 146 cm along the body shell and engine cover: (39, 30, 47) → (45, 58, 29) turning 30° → (46, 61, 21) turning 27° → (42, 65, -82). One line, facing 22° at (46, 62, 17).
- 140 cm along the side skirt: (23, 18, 149) → (39, 19, 69) turning 26° → (74, 21, 23). One line, facing 25° at (39, 19, 69).
- 121 cm along the body shell: (40, 58, 38) → (40, 66, -82). One line, facing 33° at (44, 65, -21).
- 116 cm along the body shell and cockpit surround: (18, 57, 142) → (26, 76, 28). 2 lines across it, facing 27° at (22, 69, 83); 40° at (23, 68, 82).
- 112 cm along the sidepod top, rear flank and body shell: (55, 62, 7) → (58, 63, -48) turning 88° → (84, 58, -48) turning 77° → (86, 33, -34). One line, facing 7° at (74, 61, -49).
- 111 cm along the body shell: (25, 49, 144) → (39, 63, 34). One line, facing 67° at (32, 55, 95).
- 111 cm along the body shell: (36, 65, 35) → (40, 67, -75). One line, facing 40° at (42, 67, -32).
- 99 cm along the side skirt: (22, 22, 82) → (74, 22, 23) turning 24° → (82, 23, 4). One line, facing 39° at (60, 22, 36).
- 95 cm along the body shell: (15, 59, 142) → (21, 75, 49). One line, facing 17° at (18, 65, 108).
- 87 cm along the rear flank and body shell: (79, 60, -50) → (52, 64, -95) turning 20° → (45, 64, -128). 7 lines across it, facing 11° at (59, 63, -82); 20° at (61, 62, -83); 32° at (63, 62, -84); 47° at (64, 61, -84); 63° at (65, 59, -85); 75° at (65, 57, -85); 85° at (66, 55, -85).
- 81 cm along the body shell: (32, 50, 95) → (40, 58, 38) turning 19° → (50, 61, 18). One line, facing 77° at (40, 58, 38).

### Its panels

The model's own panels, bounded by its crisp lines and edges, 500 cm² or more, the biggest first. A colour filling one right up to its lines: `meshlines.panel(point)`, the point given.

| panel | cm² | a point |
|---|---|---|
| body shell | 17417 | (-15, 75, 53) |
| engine cover and engine cover panel | 6454 | (-3, 75, -97) |
| rear flank | 5156 | (67, 41, -80) |
| nose tip and wing pylon | 3734 | (-3, 49, 187) |
| side skirt | 3693 | (42, 19, 63) |
| cockpit surround | 2729 | (-25, 80, 11) |
| sidepod top | 2459 | (76, 60, -25) |
| diffuser and diffuser strake | 2258 | (2, 18, -130) |
| sidepod inlet | 1887 | (69, 49, -17) |
| tail panel | 1670 | (3, 65, -152) |
| side skirt | 1195 | (13, 20, 183) |
| nose panel | 989 | (-2, 56, 162) |
| tail corner | 822 | (44, 64, -138) |
| diffuser strake | 795 | (40, 17, -124) |
| diffuser strake | 756 | (-40, 17, -124) |
| rear quarter panel | 650 | (35, 73, -64) |

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

## Where a graphic stops

- One skin, sewn, over most of the body: the body shell, rear flank, side skirt, nose tip, wing pylon, cockpit surround, engine cover, rear quarter panel, nose fin, fuel cap, nose panel, engine cover panel and number panel. A band or a line runs on across the seams between them.
- Pieces of their own, a gap of more than 1 cm round them: the tail corner and tail panel, 1.7 cm; the sidepod inlet (each side), 1.4 cm. A line stops there, as a wrap would.
- Pieces sewn on, 1 cm or less from the skin: the diffuser strake and diffuser, 0.05 cm; the sidepod top (each side), 0.41 cm; the diffuser strake, 0.04 cm; the nose fin, 0.35 cm. A line may run on.
- A graphic laid whole (a badge, words, a picture) stays on one piece, and off a fold.
- The cockpit leaves no skin down the top's middle from z 85 to -48, 28 cm out each side.
- Keep clear: the number panel (z -78 to -62) and the engine cover panel (z -120 to -81), which the game letters, and the nose fin's plate (z 118 to 142): nothing on them or within 3 cm (`show` names anything there).
