# TSC_Endurance

The user's words (2026-10-06, Claude Opus 5.5): "any suggestions?", then, of four directions asked in
the Lab (question 15 on TSC_Skeleton), "Endurance". The direction as offered: "Endurance: dark top,
light sides, split on the crease". The first car of the anatomy (step E of the road).

Read as a clear idea, one design: the top gloss navy, the sides silver metallic, split along the
shoulder (where the top turns down into the side: the body's own crease, the anatomy's lines), the
underside dark; gunmetal wheels; amber as the one accent, in the lights.

- Shown (2026-10-06): in the Lab. Close looks checked: the split runs clean along the shoulder over the
  bonnet, the front flank's fold, round the sidepod and along the rear flank. The check's "8 cm short"
  at the tail's end is meant: the narrow lip below the tail's crease is the sides' silver. From the
  chase cameras the car reads navy (the top is 79 % of what they see); the silver shows from the side.
- Note 1 (user, 2026-10-06, on the right rear flank): "Is this deliberate.  Because this is the kind of
  things I worry that the ai thinks that the paint is straight along the edges or anywhere but in the
  actual car, they are not." Measured: the split lay on the shoulder's crest within a few mm from z -20
  to -105, but the shoulder there is a roll about 7 cm round (its curvature falls to the side's own
  about 6 cm down), so the change sat halfway round the curve. Built `shapes.area("top", wrap=6)`: the
  top's colour over the whole roll. Set 1, two takes: A on the crest, B over the shoulder. Also found:
  the inlets' ducts, inboard of the shoulder, took navy inside (blots on the duct's ceiling and inner
  wall): the sidepod inlet painted silver by name in both.
- Change (user, 2026-10-06, in the chat): "I want you to actually create the paint to stop at the
  shoulder of the car.  I want to check whether the tool can make a perfectily round edge". Picked A
  (on the crest; B and its wrap left out). Checked close up along the whole shoulder on both sides
  (17 places a side, and the tail corner's seam): the edge runs smooth on the crest from the nose to
  the tail, crosses the sidepods' rear corners and the tail corner's seam without a step; its rises
  are the shoulder's own over the rear arches.
- Note 2 (user, 2026-10-06, a line drawn on the right side from the sidepod's inlet to the rear wheel):
  "As you can see with my not so perfect line, that the tool does not know how to place the right edge of
  the car.  Can't you measure by the edge of the corner along the car?" Measured the corner a second way,
  where the shading (the bake's normals) turns halfway from the top's facing (7 degrees) to the side's
  (86 to 98): within 0.0 to 1.0 cm below the crest from z -25 to -102. The user's line runs 0.8 to 2.4 cm
  below the crest (once 0.3 above). Set 2: A on the measured corner, B `area("top", wrap=1.5)`, along
  their line.
