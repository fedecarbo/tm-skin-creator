# The car map

Written by `python -m tool.carmap --describe` from the car's own mesh (2026-10-02); `tool/carmap.py` is the key. Read it, and look at its pictures (`car/map/`), when a design places shapes by the body's areas or needs exact positions. Lengths in cm: x out to the car's left (the right mirrors it), y up from the ground, z forward (the nose's tip at 215, the tail at -162).

## The pictures

The body alone, the wheels taken off, nine views each (`tool.snap <name> --body`):

- `car/map/areas.jpg`: the top white, the sides blue, underneath grey; the shoulder green, the lower edge magenta (each one smooth curve per stretch; the shoulder absent where the body has no line, the lower edge along where the skin turns to face the ground where it has no crease: `python -m tool.carmap --check`), the real folds black, openings red, joins blue.
- `car/map/lines.jpg`: every ridge of the body's curvature on clay, each in its own colour.
- `car/map/texture.jpg`: the areas car's flat texture (Skin_B), the lines on it as the game's texture holds them.
- `car/map/open.jpg`: how much of the open air each spot sees, white (all) to violet (hidden).
- `car/map/air.jpg`: where the oncoming air hits, a warm ramp over black, and smoke lines traced along its flow from a rake at the nose.

The car's 3D model in the pictures: amogusstrikesback2, CC-BY-4.0 (https://sketchfab.com/amogusstrikesback2).

## The body along its length

Where the top ends (the shoulder) and where the side turns under (the lower edge), on each slice.

| z | what's there | shoulder x, y | lower edge x, y |
|---|---|---|---|
| 212 | the nose's tip | 12, 18 | 12, 17 |
| 190 | the nose, over the front wing | 18, 42 | 18, 42 |
| 178 | the front wheels' axle | 14, 51 | 20, 44 |
| 150 | the nose | 16, 57 | 24, 46 |
| 130 | the nose fin's plate | 18, 61 | 27, 47 |
| 110 | the bonnet | 19, 64 | 30, 49 |
| 85 | the cockpit opening's front | 21, 69 | 34, 51 |
| 60 | the front flank | 22, 73 | 44, 19 |
| 30 | the front flank, the sidepods begin | 38, 65 | 69, 21 |
| 0 | the sidepods, their inlets | 70, 60 | 81, 22 |
| -30 | the sidepods | 84, 58 | 82, 22 |
| -60 | the sidepods' back, the number panel | 80, 58 | 70, 21 |
| -90 | the deck, the engine cover panel | 59, 61 | 51, 19 |
| -120 | the rear wheels' axle | 50, 62 | 50, 22 |
| -140 | the tail | 48, 62 | 50, 30 |
| -158 | the tail's end | 35, 64 | 35, 63 |

The top's half-width is the shoulder's x; the sides run from the shoulder's height down to the lower edge's. At z 70 to 208 the lower edge is the nose's and the front flank's lip, with the nose's belly rolled under it: the skin ends there and the inner car carries on below (the skirt further down is another piece); paint on "body" stops at the lip.

## Lines on the car

Lines, stripes, dashes and tape along the car's own lines (a guide, a seam, a panel's edge, a top line) or along a line drawn with the Lab's pen are courses (`tool/course.py`). The map's own lines below are fitted off the mesh to cut its areas; they are not for drawing.

## The model's pieces

The body is 9 separate pieces of 5 cm² or more (triangles joined across shared edges; the wheel covers left out), and 156 edges are shared by three or more triangles. Each piece's parts, area, the length of its edge, the gap to the nearest other piece (the smallest distance between its edge and the other's), how much of its edge lies within 1 cm of another piece, and the skin of other pieces hidden within 1 cm behind it. Where two pieces almost touch the skin is sewn and a line carries straight over; across a real gap (the tail's 2 cm slot) a line stops, as a real wrap would, and a decal must not straddle one (`tool/pieces.py`, `car/pieces.json`).

| parts | cm² | edge cm | gap cm | edge within 1 cm | hidden skin behind, cm² | z |
|---|---|---|---|---|---|---|
| body shell, rear flank, side skirt, nose tip, wing pylon, cockpit surround, engine cover, rear quarter panel, nose fin, fuel cap, nose panel, engine cover panel, number panel | 55054 | 2876 | 0.13 | 6% | 160 | -152 to 215 |
| tail corner, tail panel | 3585 | 296 | 1.74 | 0% | 104 | -162 to -123 |
| diffuser strake, diffuser | 3279 | 235 | 0.05 | 15% | 80 | -145 to -107 |
| sidepod top | 2528 | 222 | 0.41 | 19% | 35 | -50 to 12 |
| sidepod top | 2528 | 222 | 0.41 | 19% | 35 | -50 to 12 |
| sidepod inlet | 1887 | 182 | 1.39 | 0% | 0 | -46 to 19 |
| sidepod inlet | 1887 | 182 | 1.39 | 0% | 0 | -46 to 19 |
| diffuser strake | 866 | 113 | 0.04 | 24% | 78 | -143 to -107 |
| nose fin | 23 | 14 | 0.35 | 83% | 0 | 125 to 131 |

## The front and the back

The body's skin has no front or back face: only 411 cm² of it faces within 45 degrees of straight ahead and 872 cm² of straight back, in patches (the sidepods' inlet rims, the nose's wing and the tail's number panel are inner parts). The map gives no such areas; what faces the oncoming air is `shapes.hit`.

## Openings

Loops of open edges 30 cm round or more (`shapes.near("opening", r)` keeps clear of them); a wall is one the oncoming air runs into, which the air turns round.

| round | parts | x | y | z | a wall |
|---|---|---|---|---|---|
| 1030 | rear flank, side skirt | -74 to 74 | 14 to 64 | -151 to 213 | partly |
| 331 | cockpit surround | -28 to 28 | 71 to 86 | -48 to 85 | partly |
| 296 | tail corner, tail panel | -52 to 52 | 52 to 65 | -161 to -123 | no |
| 268 | body shell, rear flank | 44 to 86 | 26 to 63 | -50 to 44 | yes |
| 235 | diffuser, diffuser strake | -31 to 50 | 14 to 28 | -145 to -107 | no |
| 231 | body shell, side skirt | 11 to 23 | 20 to 44 | 69 to 172 | partly |
| 222 | sidepod top | 55 to 86 | 28 to 62 | -50 to 12 | no |
| 185 | wheel cover ring | 105 to 105 | 6 to 65 | -149 to -91 | yes |
| 185 | wheel cover ring | 102 to 102 | 6 to 65 | 149 to 208 | yes |
| 182 | sidepod inlet | 55 to 82 | 46 to 59 | -51 to 19 | yes |
| 135 | wheel cover ring | 93 to 95 | 14 to 55 | 158 to 199 | partly |
| 135 | wheel cover ring | 96 to 98 | 14 to 55 | -141 to -100 | partly |
| 120 | rear flank | 49 to 52 | 23 to 49 | -140 to -95 | no |
| 115 | wheel cover disc | 97 to 97 | 17 to 54 | -138 to -102 | yes |
| 115 | wheel cover disc | 94 to 94 | 17 to 54 | 160 to 197 | yes |
| 70 | wing pylon, side skirt | -10 to 10 | 20 to 37 | 192 to 201 | yes |
| 36 | wheel cover hub | 102 to 102 | 29 to 42 | -119 to -114 | yes |
| 36 | wheel cover hub | 99 to 99 | 29 to 42 | 179 to 185 | yes |
| 36 | wheel cover hub | 99 to 99 | 29 to 42 | 172 to 177 | yes |
| 36 | wheel cover hub | 102 to 102 | 29 to 42 | -127 to -121 | yes |
| 32 | wing pylon | 11 to 13 | 32 to 38 | 179 to 192 | no |

## The panels

Each body part (a pair's two sides, or the four wheels', together): its area, where it sits (its share on the top, the sides and under), how open it is, how big it looks from the chase cameras and how much of the oncoming air it takes.

| part | cm² | top / sides / under | open | seen from behind, cm² | air, cm² | z |
|---|---|---|---|---|---|---|
| body shell | 17642 | 48% / 41% / 10% | 88% | 3051 | 398 | -83 to 145 |
| rear flank | 10924 | 11% / 72% / 17% | 60% | 1974 | 1 | -152 to -25 |
| wheel cover ring | 9566 | 0% / 51% / 49% | 76% | 409 | 463 | -150 to 208 |
| side skirt | 9159 | 0% / 23% / 77% | 43% | 2 | 347 | -25 to 215 |
| sidepod top | 5055 | 56% / 44% / 0% | 96% | 1208 | 21 | -50 to 12 |
| engine cover | 4411 | 100% / 0% / 0% | 95% | 2343 | 1 | -133 to -51 |
| wheel cover hub | 4087 | 0% / 50% / 50% | 37% | 0 | 96 | -130 to 188 |
| sidepod inlet | 3774 | 50% / 50% / 0% | 20% | 0 | 59 | -51 to 19 |
| wheel cover disc | 3575 | 0% / 57% / 43% | 64% | 80 | 35 | -139 to 197 |
| nose tip | 3370 | 36% / 34% / 29% | 70% | 192 | 171 | 142 to 211 |
| cockpit surround | 2818 | 100% / 0% / 0% | 98% | 811 | 24 | -53 to 91 |
| diffuser | 2117 | 0% / 1% / 99% | 93% | 72 | 0 | -145 to -109 |
| diffuser strake | 2028 | 0% / 0% / 100% | 78% | 53 | 0 | -144 to -107 |
| tail panel | 1822 | 95% / 5% / 1% | 99% | 849 | 0 | -162 to -131 |
| tail corner | 1762 | 59% / 40% / 1% | 88% | 649 | 0 | -159 to -123 |
| engine cover panel | 1621 | 100% / 0% / 0% | 100% | 1052 | 0 | -120 to -81 |
| wing pylon | 1579 | 10% / 7% / 83% | 36% | 0 | 91 | 164 to 208 |
| rear quarter panel | 1347 | 100% / 0% / 0% | 94% | 491 | 0 | -85 to -42 |
| nose panel | 1017 | 100% / 0% / 0% | 99% | 179 | 50 | 142 to 187 |
| number panel | 655 | 100% / 0% / 0% | 100% | 391 | 0 | -78 to -62 |
| nose fin | 471 | 100% / 0% / 0% | 87% | 89 | 14 | 118 to 142 |
| fuel cap | 79 | 100% / 0% / 0% | 95% | 33 | 0 | -77 to -67 |

## What the player sees

The player sees their own car from behind all race (the chase cameras). By how big each part looks from there:

- body shell: 22%
- engine cover: 17%
- rear flank: 14%
- sidepod top: 9%
- engine cover panel: 8%
- tail panel: 6%
- cockpit surround: 6%
- tail corner: 5%

The top takes 79% of what the chase cameras see; the sides most of the rest. A graphic on the flanks is for the other players and the replays.

## Where the air hits

By how much of the oncoming air each part takes (the Newtonian rule):

- wheel cover ring: 26%
- body shell: 22%
- side skirt: 20%
- nose tip: 10%
- wheel cover hub: 5%
- wing pylon: 5%

## Words for designs (tool/shapes.py)

- `shapes.area("top" | "sides" | "under")`: the body's areas, split along its own lines.
- `shapes.outside(0.4)`: the outer body only (keeps paint out of the inlets, the wheel pockets, under panels).
- `shapes.along(a0, a1)`: a band from the nose's tip (0) to the tail (1).
- `shapes.near(kind, reach)`: near a fold, an opening, a join, the shoulder, the lower edge; `~shapes.near(...)` keeps a graphic clear. (`shapes.line(kind, width)` shows the map's own lines on its test cars.)
- Lines on the car: `tool/course.py`.
- `shapes.hit(lo, hi)`: where the oncoming air hits, 0..1 (bands of it make a pressure map).
- `shapes.streamlines(shapes.rake(z, [across ...]), width)`: smoke lines along the air's flow from a row of seeds.
- Everything combines with `&`, `|`, `~` and the plain zones (`stripe`, `band`, `facing`, ...).
