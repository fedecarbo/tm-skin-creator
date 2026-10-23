# TSC_RulerTest

A throwaway test car for the road's step 16 (2026-10-22, Claude Fable 5.1): the judge names its ruler, rows of dots get a
check and a close look, and a sticker's bites at a step are measured, then fixed in the chart. Deleted on the user's OK.

## The brief (the test's words)

1. A pale car, a thin dark line 1 cm beside the side skirt's crease 3, both sides, with a 2 cm gap planted at z 60.
2. Rows of 2 cm dots: along the sidepod inlet's crisp line, along the side skirt's long crease, and one dot behind each
   rear wheel (planted).
3. An orange ring 25 cm across pressed onto the nose at (0, ?, 150), onto the nose fin's plate (the user's ring of
   2026-10-22, notched where it climbed the plate).
4. A gold ring 16 cm across pressed over the rear flank's rolled shoulder at z -68, both sides (the badge of 2026-10-08,
   "chipped off on one part of the circle").

## What the judge said before, and what it says now

- The ruler. Before: "a gap of 2.0 cm, the skin bare, on the left, z +61". Now: "...; read against the model's crisp line
  'side skirt crease 2', 0.3 cm from the design's course": the design wrote crease 3's offset, which runs 0.3 cm from
  crease 2, so that's the line every station was read against; the right side's say "mirrored to the right". A step
  where two lines meet names both.
- The rows. Before: nothing said of the dots, no close look. Now: "hidden: the rear left wheel stands in front of 1 of
  its 2 marks, seen square, z -76" (block), and a close look over every dot (looks 20 to 33), the two sides paired.
- The nose ring at z 150. Measured: along the plate's front edge (z 142, x 5 to 10 each side) the surface has two rows of
  sliver holes, rim loops 10 cm round, which the bridging never closed (a rim vertex's nearest "other" vertex was its
  own rim's next but one), so every geodesic to the plate went round the slits' ends and the sticker folded: 236
  faces torn under the ring, 194 folded, the ring notched at both crossings. Fixed in the chart: a rim loop under
  `HOLE` cm round is a hole, zipped shut across (its own rim within `OWN_RIM` edges is never a bridge's far end;
  a slit's sides bridge however they face, short of opposite): 25 faces torn, none folded; the close look shows the
  ring whole over the seam (3.6 cm² more ring than before, the close looks' own diff).
- The shoulder badge. Measured: the exact solver walks the hairline seams' slivers (0.05 cm wide, 2 cm long)
  lengthwise, so a vertex 7.7 cm from the centre read 13.8 and 130 texels round the seam crossing had no place on the
  sticker. Fixed: every distance is bounded by the way along the mesh's edges (`_relaxed`): 0 texels lost. The ring
  still jogs by about 0.3 cm at two crossings (2 and 8 o'clock in look 18) and the paint still says chipped (0.4 cm²,
  40 scattered texels): measured not to come from the step spanning nor the bridging (each switched off, the same),
  so its cause stays open, queued.

## Record

- 2026-10-22 Shown (round 1, the old code): the strip's findings without a ruler; no finding on the dots; both rings
  notched in the close looks.
- 2026-10-22 Shown (round 2, the new code): the findings above; `build/TSC_RulerTest_close_2.png` the rings and the
  first dots, `_close_3.png` the last dot. Blocks are the plantings and the nose ring on the plate, meant.
