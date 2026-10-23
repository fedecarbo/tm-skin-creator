# TSC_IntentTest

A throwaway test car for the road's step 17 (2026-10-22, Claude Opus 5.5): what was meant set beside what landed,
stroke by stroke, in the viewer's data (`steps.json`), so a choice and an accident look different. The user's picture of
the notched ring of 2026-10-22 again: the crossing meant, the notch the tool's, the block for a third reason. Deleted on
the user's OK.

## The brief (the test's words)

1. A pale car, the inner car dark.
2. A thin dark line along the skirt, 1 cm above its lower crease, both sides.
3. An orange ring 25 cm across on the nose at z 150, over the nose fin's plate on purpose.
4. A gold ring badge 16 cm across over the rear flank's rolled shoulder at z -68, across the edge on purpose, both sides.
5. Gold wheels.

## What each stroke says now (`steps.json`, after the show and the close looks)

- Stroke 5, the nose ring (step "Nose ring", the user's words "an orange ring on the nose, over the seam on purpose"):
  crosses the car's parts on purpose; landed z 162 to 138 (the nose to the nose fin's plate), facing up; one finding,
  block: "39 cm² on the nose fin's plate" (the plate the game letters). The choice and the block are told apart.
- Stroke 6, the shoulder badge: crosses on purpose; landed z -60 to -75 (the sidepods' back), both sides; two findings,
  block: "chipped: 0.4 cm² ... a bite 12.1 cm wide" on the left, 0.3 on the right (the paint's own, the tool's accident:
  the queue's 0.3 cm jog).
- Stroke 4, the skirt line: meant plain; ten "line" blocks, 0.3 cm steps read against 'side skirt roll 3' and a 0.7 cm
  step where it meets crease 2; the close looks show it smooth (queued; step 16's car had the same).
- Strokes 1 to 3 and 7 (the clay, the base, the inner car, the wheels): nothing found.

## Record

- 2026-10-22 Shown (round 1): the findings above; the page for the user made from `steps.json` before anything was let
  go, so it shows the blocks as accidents.
- 2026-10-22 Shown again (round 2, its design's docstring edited): the same 13 findings; then all 13 let go with
  `tool.gate --despite` (a test car, its accidents kept on purpose), and each stroke's findings in `steps.json` now carry
  that reason (`let_go`): the gate's path checked for real.
