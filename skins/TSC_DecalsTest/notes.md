# TSC_DecalsTest

The road's step 5 (IMPROVEMENTS.md, 2026-10-08, Claude Fable 5.1): a test car for stickers, badges and words on the
car's surface, scrapped after the pick. The same design painted twice: A with the tool as it was (the code at
2c126de: a mark laid flat in the texture's own unfolding of each panel, within a cone of one facing and off every
fold; a picture across the panels projected onto the nearest surface facing it; words at a line laid straight at its
middle; stickers projected, spaced through the air), B on the surface itself (every mark pressed onto the car on a
chart of the surface round its point, exact; words along a line following it letter by letter; stickers spaced along
the surface).

- Set 1 (Stickers and words · 2 takes): A as it was, B on the surface.
- Shown (2026-10-08, Claude Fable 5.1): set 1 open in the Lab, A (TSC_DecalsTest_AsItWas, painted from the old code's
  tree, 2c126de) and B (TSC_DecalsTest_OnTheSurface). The old code's own notes on A: the words along the nose's edge
  laid straight, "moved 7.5 cm", their twin "8.1 cm from where it was wanted"; FLANK "moved 18.4 cm, shrunk to 4.2 cm
  tall (53%)"; the placard "moved 5.1 cm, shrunk to 1.5 cm tall (58%)", off its line; 231 scattered copies through the
  air, "6 spots left bare". B: the words follow the edge letter by letter (shrunk to 3.5 cm tall to stay on the body
  shell), FLANK 7.4 cm tall over the turn ("the surface turns 21° under it"), the placard along its line, the badge
  pressed over the shoulder's roll (98 % of it on the car, stretched under 3 %), 179 copies spaced 5.8 cm or more along
  the surface, none across a crisp line. Close looks of B: the badge wraps the roll whole, the letters along the nose's
  edge sit at an even distance from it, the stickers lie whole between the sidepod top's lines.
- Pick of set 1 (user, 2026-10-08, in the Lab): B, "On the surface". Their note on B's nose: "I picked B but the surface
  on this is wrong, there's a clipping happening between the two pieces, and ignoring another piece that should have
  the outlines." Measured: the emblem crosses the 6 mm step up to the raised plate behind the nose's seam (the nose
  fin's plate); the pressed sticker ran down the step's wall, so on the plate its ring sat 0.3 to 0.5 cm back from
  where a flat badge would put it, and the halves didn't meet at the edge. A sticker laid over every edge now spans a
  step flat (`surface.Surface.chart`: the wall taken out of the solve, the raised skin measured level with the other,
  the rims welded): on the plate the ring is within 0.15 cm of flat, the rest the nose's own dome. The car repainted
  (version 4); the takes gone with the pick.
- The user (2026-10-08, in the chat): "that front nose one is wrong. The decal in theory based on your placement, would
  need to touch the three pieces to make it a full circle. At the moment its on the two pieces and it looks clipped ...
  the original one had it right, the On the surface one didn't." The third skin is the step's wall between the nose's
  top and the raised plate (two texel rows in the texture): the spanning had taken it out of the chart, so it stayed
  bare and cut the circle from the front. The wall now takes the sticker's edge; the raised rim is welded onto the lower
  rim's own edges; a strip that doesn't part two skins (a groove's wall) is no longer taken for a step. Versions 5 and 6.
- Note 3 (user, 2026-10-08, on the rear flank, the badge across the shoulder): "This decal looks chipped off on one part
  of the circle." Seen in the eye's close look at version 6: a notch about half a centimetre wide in the gold ring where a
  crisp line crosses it. Not found today; the user asked to stop ("It's taken the entire day"). Open: which of the step
  spanning or the bridging leaves it, on a chart of that spot.
