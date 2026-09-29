# The car map

Written by `python -m tool.carmap --describe` from the car's own mesh (2026-09-29); `tool/carmap.py` is the key. Read it, and look at its pictures (`car/map/`), before the first design in a session. Lengths in cm: x out to the car's left (the right mirrors it), y up from the ground, z forward (the nose's tip at 215, the tail at -162).

## The pictures

The body alone, the wheels taken off, nine views each (`tool.snap <name> --body`):

- `car/map/areas.jpg` (TSC_Map_Areas): the top white, the sides blue, underneath grey, facing forward yellow, facing back orange, the hidden insides violet; the shoulder green, the lower edge magenta, folds black, openings red, joins blue.
- `car/map/grid.jpg` (TSC_Map_Grid): across every quarter and along every tenth: how a band placed by them bends with the body.
- `car/map/open.jpg` (TSC_Map_Open): how much of the open air each spot sees, white (all) to violet (hidden).
- `car/map/air.jpg` (TSC_Map_Air): where the oncoming air hits, a warm ramp over black, and smoke lines traced along its flow from a rake at the nose.

The car's 3D model in the pictures: amogusstrikesback2, CC-BY-4.0 (https://sketchfab.com/amogusstrikesback2).

## The body along its length

Where the top ends (the shoulder) and where the side turns under (the lower edge), on each slice.

| z | what's there | shoulder x, y | lower edge x, y |
|---|---|---|---|
| 212 | the nose's tip | 11, 24 | 7, 18 |
| 190 | the nose, over the front wing | 16, 45 | 17, 41 |
| 178 | the front wheels' axle | 17, 48 | 19, 16 |
| 150 | the nose | 22, 51 | 24, 43 |
| 130 | the nose fin's plate | 25, 54 | 27, 47 |
| 110 | the bonnet | 28, 56 | 30, 49 |
| 85 | the cockpit opening's front | 31, 59 | 34, 51 |
| 60 | the front flank | 35, 62 | 43, 18 |
| 30 | the front flank, the sidepods begin | 43, 60 | 68, 20 |
| 0 | the sidepods, their inlets | 63, 58 | 81, 21 |
| -30 | the sidepods | 85, 57 | 82, 21 |
| -60 | the sidepods' back, the number panel | 80, 58 | 72, 23 |
| -90 | the deck, the engine cover panel | 60, 60 | 51, 19 |
| -120 | the rear wheels' axle | 50, 61 | 49, 20 |
| -140 | the tail | 49, 61 | 31, 24 |
| -158 | the tail's end | 34, 64 | 34, 63 |

The top's half-width is the shoulder's x; the sides run from the shoulder's height down to the lower edge's. Where the lower edge sits high (z 74 to 192), the body's skin ends under the nose's and the front flank's lip and the inner car carries on below: paint on "body" stops there.

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
| body shell | 17642 | 64% / 26% / 10% | 88% | 3051 | 398 | -83 to 145 |
| rear flank | 10924 | 12% / 72% / 17% | 60% | 1974 | 1 | -152 to -25 |
| wheel cover ring | 9566 | 0% / 69% / 31% | 76% | 409 | 463 | -150 to 208 |
| side skirt | 9159 | 0% / 26% / 73% | 43% | 2 | 347 | -25 to 215 |
| sidepod top | 5055 | 58% / 42% / 0% | 96% | 1208 | 21 | -50 to 12 |
| engine cover | 4411 | 100% / 0% / 0% | 95% | 2343 | 1 | -133 to -51 |
| wheel cover hub | 4087 | 0% / 76% / 24% | 37% | 0 | 96 | -130 to 188 |
| sidepod inlet | 3774 | 49% / 51% / 0% | 20% | 0 | 59 | -51 to 19 |
| wheel cover disc | 3575 | 0% / 73% / 27% | 64% | 80 | 35 | -139 to 197 |
| nose tip | 3370 | 50% / 39% / 11% | 70% | 192 | 171 | 142 to 211 |
| cockpit surround | 2818 | 100% / 0% / 0% | 98% | 811 | 24 | -53 to 91 |
| diffuser | 2117 | 0% / 1% / 99% | 93% | 72 | 0 | -145 to -109 |
| diffuser strake | 2028 | 0% / 9% / 91% | 78% | 53 | 0 | -144 to -107 |
| tail panel | 1822 | 96% / 4% / 0% | 99% | 849 | 0 | -162 to -131 |
| tail corner | 1762 | 64% / 35% / 1% | 88% | 649 | 0 | -159 to -123 |
| engine cover panel | 1621 | 100% / 0% / 0% | 100% | 1052 | 0 | -120 to -81 |
| wing pylon | 1579 | 14% / 34% / 52% | 36% | 0 | 91 | 164 to 208 |
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

The top takes 83% of what the chase cameras see; the sides most of the rest. A graphic on the flanks is for the other players and the replays.

## Where the air hits

By how much of the oncoming air each part takes (the Newtonian rule):

- wheel cover ring: 26%
- body shell: 22%
- side skirt: 20%
- nose tip: 10%
- wheel cover hub: 5%
- wing pylon: 5%

## Words for designs (tool/shapes.py)

- `shapes.area("top" | "sides" | "under" | "front" | "back")`: the body's areas, split along its own lines.
- `shapes.outside(0.4)`: the outer body only (keeps paint out of the inlets, the wheel pockets, under panels).
- `shapes.across(a0, a1)`: a band round the section (0 the top's middle, 1 the shoulder, 2 the lower edge, 3 under), the same share of the way all along the car.
- `shapes.along(a0, a1)`: a band from the nose's tip (0) to the tail (1).
- `shapes.line(kind, width)`, `shapes.near(kind, reach)`: along or near a fold, an opening, a join, the shoulder, the lower edge; `~shapes.near(...)` keeps a graphic clear.
- `shapes.hit(lo, hi)`: where the oncoming air hits, 0..1 (bands of it make a pressure map).
- `shapes.streamlines(shapes.rake(z, [across ...]), width)`: smoke lines along the air's flow from a row of seeds.
- Everything combines with `&`, `|`, `~` and the plain zones (`stripe`, `band`, `facing`, ...).
