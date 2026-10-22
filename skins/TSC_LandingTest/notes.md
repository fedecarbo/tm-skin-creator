# TSC_LandingTest

A throwaway test car for the road's step 15 (2026-10-22, Claude Fable 5.1): three strokes planted in the wrong place on
purpose, to show that `PY -m tool.skin read` catches each before any paint. Deleted on the user's OK of the step.

## The brief (the test's words)

x is out to the car's left, y up from the ground, z forward; all in cm.

1. Warm white above and deep navy satin below, split by a level line 40 cm off the ground.
2. A bright orange stripe 3 cm wide across the bonnet, 10 cm in front of the cockpit opening's front (z 85).
3. Both sidepod tops matte black, filled right up to the panel's edges.
4. A white disc 20 cm across on each rear flank, around (64, 36, -80) on the left.
5. Gold wheels, the inner car dark grey satin, nothing left in clay.

## What was planted, and what `read` said (14 s, nothing painted for anyone to see)

- The stripe written `shapes.band(-98, -95)`: the cockpit's far side. The receipt: "gloss bright orange on body: rear
  flank, engine cover, engine cover panel (body), 666 cm²; on the body: z -95 to -98 (the deck, the engine cover
  panel), y 15 to 76, x -59 to 59 (both sides), facing up". The brief said the bonnet, z 95 to 98.
- The sidepod tops' black written on "rear flank" with the sidepod top panel's zone: "matte black on rear flank: nothing
  painted: its zone reaches none of the parts named".
- The disc at (64, 36, -80): "found: gloss white disc on rear flank: hidden: the rear left wheel stands in front of 97 %
  of it, seen square" (and its twin, the rear right wheel). The sketch `build/TSC_LandingTest_landing.png` shows it
  dimmed through the tyre's outline.

## Record

- 2026-10-22 Read against the car: the three plantings caught (above). Shown as it is, wrong strokes and all, so the
  Lab's picture can be held beside the sketch.
- 2026-10-22 Shown: the judge blocks the three plantings (the disc hidden by the rear wheels, the stripe on the engine
  cover panel and the gap it cut in the navy); let through the gate as meant (`despite.json`), so the picture stands.
