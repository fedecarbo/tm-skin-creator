# The car's anatomy

Written by `python -m tool.carmap --describe` from the car's own shape (2026-10-09): how the body is built, where it's calm and where a graphic stops. Read it before a design, and follow these lines and rooms where the idea needs them, never by rule. Lengths in cm: x out to the car's left (the right mirrors it), y up from the ground, z forward (the nose's tip at 215, the tail at -162).

## How the body is built

The model's own lines, read off its triangles (`tool/meshlines.py`): exact on the car and on the flat texture alike. The Lab's UV map room draws them (Template), its Mesh button lays them over any car, and `car/map/model.jpg` is the same on the bare body: the model's triangles grey, orange where the body rolls outward across them, violet where it dips in, its crisp lines yellow, red where the body ends, blue where the flat texture is cut. The left side and the middle (the right mirrors the left); every line and panel, with a point on each: `PY -m tool.meshlines`.

### Its crisp lines and edges

Panel lines, crisp folds, where the body ends and the seams between its parts, 80 cm or longer, the longest first, each by its name. A marking along one: `meshlines.line(name)` (`side="right"` its mirror image; `.mirrored()` both).

- **cockpit surround crease 1**: a panel line, a groove of 9, 378 cm, along the cockpit surround, at (23, 77, 33): round, z 91 to -52.
- **body shell crease 1**: a crisp line, 333 cm, along the body shell, at (0, 70, 92): (-23, 84, -51) → (-36, 73, -37) turning 48° → (-36, 71, 5) turning 29° → (-18, 77, 41) turning 25° → (-12, 70, 88) turning 63° → (0, 70, 92) turning 39° → (12, 70, 88) turning 63° → (18, 77, 41) turning 25° → (36, 71, 5) turning 29° → (36, 73, -37) turning 48° → (23, 84, -51).
- **cockpit surround edge 1**: where the body ends, 331 cm, along the cockpit surround, at (12, 78, 40): round, z 85 to -48.
- **tail corner edge 1**: where the body ends, 296 cm, along the tail corner and tail panel, at (49, 52, -152): round, z -123 to -161.
- **body shell edge 1**: where the body ends, 268 cm, along the body shell, rear flank and side skirt, at (81, 60, -49): round, z 44 to -50.
- **body shell edge 2**: where the body ends, 231 cm, along the body shell, side skirt and nose tip, at (22, 43, 75): round, z 172 to 69.
- **sidepod top edge 1**: where the body ends, 222 cm, along the sidepod top, at (85, 31, -32): round, z 12 to -50.
- **sidepod inlet edge 1**: where the body ends, 182 cm, along the sidepod inlet, at (75, 49, -45): round, z 19 to -51.
- **engine cover seam 1**: a seam, 161 cm, along the engine cover and engine cover panel, at (20, 79, -81): round, z -81 to -120.
- **side skirt crease 1**: a panel line, a groove of 5, 155 cm, along the side skirt, at (0, 18, 215): (-24, 18, 149) → (-16, 18, 205) turning 28° → (-10, 18, 214) turning 45° → (0, 18, 215) turning 17° → (10, 18, 214) turning 45° → (16, 18, 205) turning 28° → (24, 18, 149).
- **body shell seam 1**: a seam, 153 cm, along the body shell and cockpit surround, at (30, 74, 21): (11, 70, 89) → (18, 77, 41) turning 24° → (36, 71, 5) turning 29° → (36, 73, -37) turning 46° → (24, 83, -50).
- **sidepod top crease 1**: a panel line, a groove of 4, 153 cm, along the sidepod top, at (82, 59, -49): (55, 61, 11) → (56, 63, -45) turning 45° → (61, 63, -50) turning 45° → (81, 60, -49) turning 48° → (86, 53, -46) turning 38° → (85, 30, -31) turning 54° → (83, 28, 0).
- **side skirt crease 2**: a crisp line, 146 cm, along the side skirt, at (39, 19, 70): (24, 18, 149) → (39, 19, 70) turning 25° → (77, 22, 17).
- **rear flank edge 2**: where the body ends, 120 cm, along the rear flank, at (52, 45, -104): round, z -94 to -140.
- **engine cover seam 2**: a seam, 113 cm, along the engine cover and number panel, at (18, 83, -62): round, z -62 to -78.
- **nose tip crease 1**: a panel line, a groove of 7, 107 cm, along the nose tip, at (0, 49, 187): (-13, 59, 143) → (-10, 49, 184) turning 72° → (0, 49, 187) turning 28° → (10, 49, 184) turning 72° → (13, 59, 143).
- **nose panel seam 1**: a seam, 107 cm, along the nose panel and nose tip, at (0, 49, 187): (-13, 59, 142) → (-10, 49, 184) turning 72° → (0, 49, 187) turning 28° → (10, 49, 184) turning 72° → (13, 59, 142).
- **rear flank crease 1**: a crisp line, 98 cm, along the rear flank, at (51, 29, -133): (53, 24, -94) → (50, 26, -130) turning 52° → (51, 38, -137) turning 20° → (51, 49, -140) turning 107° → (54, 48, -106).
- **side skirt crease 4**: a panel line, a groove of 4, 88 cm, along the side skirt, at (74, 26, 21): (44, 29, 44) → (49, 26, 42) turning 40° → (78, 26, 16) turning 40° → (84, 26, -25).
- **rear flank crease 2**: a panel line, a groove of 12, 88 cm, along the rear flank, at (58, 63, -81): (77, 61, -49) → (50, 64, -94) turning 20° → (43, 64, -128).
- **engine cover crease 1**: a panel line, a groove of 6, 87 cm, along the engine cover, at (0, 66, -133): (-43, 64, -128) → (43, 64, -128).
- **sidepod inlet crease 1**: a crisp line, 83 cm, along the sidepod inlet, at (69, 46, 9): (56, 56, 14) → (56, 47, 19) turning 105° → (79, 46, -1) turning 46° → (80, 46, -43).
- **diffuser edge 1**: where the body ends, 80 cm, along the diffuser and diffuser strake, at (30, 24, -143): (48, 28, -141) → (42, 24, -141) turning 36° → (-30, 24, -143).

### Its rounded edges

Where the body rolls from facing one way to another, the model's lines run side by side across the roll, one every 1 to 2 cm, each facing its own way (degrees from facing up): a roll. Those 80 cm or longer, the longest first. A marking along one of a roll's lines: `meshlines.line(name, tilt=<degrees>)`; along several end to end, or across: `meshlines.picked(points)`.

- **nose tip roll 1**: 156 cm along the nose tip: (-25, 49, 144) → (-14, 41, 204) turning 56° → (0, 40, 210) turning 48° → (14, 41, 204) turning 56° → (25, 49, 144). 2 lines across it, tilted 55° at (0, 41, 210); 79° at (0, 40, 210).
- **side skirt roll 2**: 153 cm along the side skirt: (-23, 18, 149) → (-15, 18, 205) turning 29° → (-9, 18, 213) turning 45° → (0, 18, 214) turning 17° → (9, 18, 213) turning 45° → (15, 18, 205) turning 29° → (23, 18, 149). One line, tilted 24° at (0, 18, 214).
- **body shell roll 1**: 146 cm along the body shell and engine cover: (39, 30, 47) → (45, 58, 29) turning 30° → (46, 61, 21) turning 27° → (42, 65, -82). One line, tilted 22° at (46, 62, 17).
- **side skirt roll 3**: 140 cm along the side skirt: (23, 18, 149) → (39, 19, 69) turning 26° → (74, 21, 23). One line, tilted 25° at (39, 19, 69).
- **body shell roll 2**: 121 cm along the body shell: (40, 58, 38) → (40, 66, -82). One line, tilted 33° at (44, 65, -21).
- **body shell roll 3**: 116 cm along the body shell and cockpit surround: (18, 57, 142) → (26, 76, 28). 2 lines across it, tilted 27° at (22, 69, 83); 40° at (23, 68, 82).
- **sidepod top roll 1**: 112 cm along the sidepod top, rear flank and body shell: (55, 62, 7) → (58, 63, -48) turning 88° → (84, 58, -48) turning 77° → (86, 33, -34). One line, tilted 7° at (74, 61, -49).
- **body shell roll 4**: 111 cm along the body shell: (25, 49, 144) → (39, 63, 34). One line, tilted 67° at (32, 55, 95).
- **body shell roll 5**: 111 cm along the body shell: (36, 65, 35) → (40, 67, -75). One line, tilted 40° at (42, 67, -32).
- **side skirt roll 4**: 99 cm along the side skirt: (22, 22, 82) → (74, 22, 23) turning 24° → (82, 23, 4). One line, tilted 39° at (60, 22, 36).
- **body shell roll 6**: 95 cm along the body shell: (15, 59, 142) → (21, 75, 49). One line, tilted 17° at (18, 65, 108).
- **rear flank roll 2**: 87 cm along the rear flank and body shell: (79, 60, -50) → (52, 64, -95) turning 20° → (45, 64, -128). 7 lines across it, tilted 11° at (59, 63, -82); 20° at (61, 62, -83); 32° at (63, 62, -84); 47° at (64, 61, -84); 63° at (65, 59, -85); 75° at (65, 57, -85); 85° at (66, 55, -85).
- **body shell roll 7**: 81 cm along the body shell: (32, 50, 95) → (40, 58, 38) turning 19° → (50, 61, 18). One line, tilted 77° at (40, 58, 38).

### Its panels

The model's own panels, bounded by its crisp lines and edges, 500 cm² or more, the biggest first, each by its name (the left side's and the middle's; the right side mirrors them). A colour filling one right up to its lines: `meshlines.panel(name)` (`both=True` its mirror image too).

| panel | parts | cm² | a point |
|---|---|---|---|
| body shell panel 1 | body shell | 17417 | (-15, 75, 53) |
| engine cover panel 1 | engine cover and engine cover panel | 6454 | (-3, 75, -97) |
| rear flank panel 1 | rear flank | 5156 | (67, 41, -80) |
| nose tip panel 1 | nose tip and wing pylon | 3734 | (-3, 49, 187) |
| side skirt panel 1 | side skirt | 3693 | (42, 19, 63) |
| cockpit surround panel 1 | cockpit surround | 2729 | (-25, 80, 11) |
| sidepod top panel 1 | sidepod top | 2459 | (76, 60, -25) |
| diffuser panel 1 | diffuser and diffuser strake | 2258 | (2, 18, -130) |
| sidepod inlet panel 1 | sidepod inlet | 1887 | (69, 49, -17) |
| tail panel panel 1 | tail panel | 1670 | (3, 65, -152) |
| side skirt panel 2 | side skirt | 1195 | (13, 20, 183) |
| nose panel panel 1 | nose panel | 989 | (-2, 56, 162) |
| tail corner panel 1 | tail corner | 822 | (44, 64, -138) |
| diffuser strake panel 1 | diffuser strake | 795 | (40, 17, -124) |
| rear quarter panel panel 1 | rear quarter panel | 650 | (35, 73, -64) |

## Where it's calm

The flat rooms: on each panel the biggest discs of skin whose surface turns no more than 20 degrees from one way, off the model's crisp lines and clear of the game's panels, 12 cm across or more: where words read flat, and a badge or a picture sits with no stretch to speak of (the left side; the right mirrors it). A sticker wraps a rolled edge as well as it lies on a flat panel; only where the surface curves two ways is it stretched, and the note says by how much.

| panel | across, cm | centre | faces |
|---|---|---|---|
| rear flank | 37 | (64, 36, -80) | out and back |
| rear flank | 28 | (81, 31, -51) | out and back |
| sidepod top | 28 | (70, 61, -26) | up |
| sidepod top | 24 | (87, 41, -25) | out |
| tail panel | 27 | (13, 65, -147) | up |
| body shell | 24 | (33, 69, 34) | up and out |
| body shell | 22 | (10, 67, 102) | up |
| engine cover | 21 | (33, 66, -119) | up |
| engine cover | 19 | (34, 71, -97) | up and out |
| rear quarter panel | 19 | (33, 76, -60) | up and out |
| tail corner | 18 | (39, 64, -148) | up |
| nose tip | 16 | (7, 46, 194) | up |
| side skirt | 15 | (27, 20, 84) | up |
| cockpit surround | 13 | (31, 76, 4) | up and out |
| cockpit surround | 12 | (32, 77, -28) | up and out |
| sidepod inlet | 13 | (73, 46, -4) | up |
| nose panel | 12 | (6, 58, 151) | up |

## Where a graphic stops

- One skin, sewn, over most of the body: the body shell, rear flank, side skirt, nose tip, wing pylon, cockpit surround, engine cover, rear quarter panel, nose fin, fuel cap, nose panel, engine cover panel and number panel. A band or a line runs on across the seams between them.
- Pieces of their own, a gap of more than 1 cm round them: the tail corner and tail panel, 1.7 cm; the sidepod inlet (each side), 1.4 cm. A line stops there, as a wrap would.
- Pieces sewn on, 1 cm or less from the skin: the diffuser strake and diffuser, 0.05 cm; the sidepod top (each side), 0.41 cm; the diffuser strake, 0.04 cm; the nose fin, 0.35 cm. A line may run on.
- A graphic laid whole (a badge, words, a picture) stays on one piece, and off a fold.
- The cockpit leaves no skin down the top's middle from z 85 to -48, 28 cm out each side.
- Keep clear: the number panel (z -78 to -62) and the engine cover panel (z -120 to -81), which the game letters, and the nose fin's plate (z 118 to 142): nothing on them or within 3 cm (`show` names anything there).
