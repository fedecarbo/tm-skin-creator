# TSC_SeeTool

A throwaway test car, painted 2026-10-22 by Claude Opus 5.5 from the user's brief alone (the paint skill as the
only guide). The user wasn't available: every decision the skill would ask them is made here and said below.

## The user's words (verbatim)

x is out to the car's left, y up from the ground, z forward; all in cm.

1. The whole body warm white above and deep navy satin below, split by one level line 40 cm off the ground, all the way round the car.
2. Both sidepod tops (the flat shelves either side behind the cockpit: the model's own panel there) matte black, filled right up to the panel's own edges.
3. A bright orange band 3 cm wide along the deck's rounded shoulder: the rounded edge where the engine cover's top rolls over into the flank, which passes through about (40, 62, -20) on the left. On its FRONT 40 cm only: from the end nearest the cockpit (the nose end) running back 40 cm. Both sides alike.
4. A white disc 20 cm across with a 2 cm navy ring, on each rear flank (the big side panel behind the sidepod, around (64, 36, -80) on the left), where it sits flat and whole, facing out.
5. The words "SEE 22" in black, 10 cm tall, on each side near the disc where they read flat, reading forward on both sides.
6. Small white discs 4 cm across scattered evenly over the engine cover's top (the deck behind the cockpit), nowhere else, none on the panels the game letters.
7. One orange ring 25 cm across pressed onto the nose at about (0, 58, 150), across the seam it crosses, on purpose.
8. Six small black dots 3 cm across, evenly spaced along the long crease that runs low along the side skirt from the nose back (through about (39, 19, 70) on the left), from its nose end to its tail end. Both sides.
9. Gold on the wheels (covers and rims) and a thin white ring on the tyres' sidewalls. The inner car dark grey satin. Nothing left in clay; the lights left as stock.

## How I read them

Every point and line below is the car's answer (`PY -m tool.meshlines`), not a guess. Decided in the user's place
(they weren't available):

1. Warm white `#efe8d8` gloss above, deep navy satin below `shapes.below(40)`, on "body" (the wheel covers are the
   wheels' own). The colour words "warm white" read as plain white in the tool, so the warm white is a hex, warm
   enough that the pure white discs (items 4 and 6) show on it.
2. `meshlines.panel("sidepod top panel 1", both=True)` matte black. The model's panel runs from the shelf down the
   sidepod's outer face to y 28, so the black goes down there too, over the navy: "filled right up to the panel's
   own edges" taken as said.
3. The rounded edge through (40, 62, -20): that point is 4.9 cm inside the body; the nearest of the model's lines is
   "body shell roll 5" (tilt 40, 1.2 cm; roll 2 is 1.9 cm, roll 1 4.5 cm). Its nose end is (36, 65, 35), beside the
   cockpit. The band is 3 cm, centred on it, from 1.5 cm to 41.5 cm along it (40 cm), both sides: started 1.5 cm in
   because at its very end the band was cut by the body's edge on the left.
4. "A white disc 20 cm across with a 2 cm navy ring": the white disc is 20 cm, the navy ring round it 2 cm, so 24 cm
   overall. At (64, 36, -80) a tyre stands in front of the flank seen square; the flank's only flat room is 36 cm
   across at (81, 37, -56), so the roundel goes there. The 40 cm split runs through it: its lower half's ring
   meets the navy body (the judge warns of it; it's the brief's own geometry).
5. "SEE 22" in teko (tall condensed): the default font is 47 cm wide at 10 cm tall and no flat room near the disc
   holds it. Teko is 26 cm wide; it sits behind the disc at (70, 50, -78), whole, 10 cm tall, reading flat (the
   surface turns under 20 degrees), above the split line, kept 1 cm off the ring.
6. The deck's top free of the game's lettered panels is two strips beside and behind them (z -88 to -123). Ten 4 cm
   pure white discs a side on a hex grid 10 cm apart, each laid whole by `s.mark` (the scatter verb made a third
   of its copies smaller than 4 cm and spread them unevenly).
7. At (0, 58, 150) the 25 cm ring lay 39 cm2 on the nose fin's plate, which the game letters. Moved 8 cm forward to
   (0, 57, 158): clear of the plate, still on the nose panel and over its seams on both sides, `across=True`.
   Ring line 2.5 cm (its hole 0.8 of it).
8. "Side skirt crease 2" (146 cm, 0.5 cm from (39, 19, 70)). Six 3 cm dots centred on it, from 1.5 cm in at its
   nose end to 1.5 cm short of its tail end, 28.6 cm apart, mirrored. Laid as 3D discs (spheres of 1.5 cm) wrapping
   the crease's fold: a pressed sticker lost up to 85 % of itself there. Black on the navy skirt: the brief's colours.
9. The inner car dark grey satin, then gold on the wheel covers and rims. The hubs stay dark grey: their paint is
   shared with the front uprights and 29 % of the floor. The light parts (brake lights, wheel rings, rear lights,
   digit display) take the inner car's dark grey like the rest (clay would otherwise stay on them); their glows are
   untouched (no relight), so they light in stock colours. A white ring 32.8 to 33.6 cm from the axle on the
   sidewalls (the visible band is 30.9 to 35.3). Glass and tyre treads stock.

## Record

- 2026-10-22 Shown (round 1): 15 blocks (dots on the crease cut, the band's end cut, the ring on the nose fin's
  plate, the words moved 24 cm onto a 63-degree turn and over the disc).
- 2026-10-22 Shown (round 2): words in teko beside the disc, ring forward, dots as 3D discs, band 1.5 cm in, hubs
  left out of the gold. 0 blocks; the deck's scattered copies uneven.
- 2026-10-22 Shown (round 3): the deck dots a hand-laid hex grid. 0 blocks.
- 2026-10-22 Shown (round 4): warmer white so the white discs show. 0 blocks, 2 warnings (the roundel over the
  split line, both sides); close looks: nothing blocks; `tool.gate` passes.
- Open (test car): not installed (no game on the Mac); a throwaway, to be deleted after the user's look.
