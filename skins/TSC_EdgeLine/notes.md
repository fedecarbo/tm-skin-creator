# TSC_EdgeLine

The user's words (2026-10-06, Claude Opus 5.5), after TSC_Endurance's split missed the edge they see
("YOu are so way off all around the car"): "I want you to create a car that has a black line of what
you think is the edge.  At least from the intake around the rear reaching to the other intake".

Read as: a test car on clay, one black line 6 mm wide along the edge as the tool reads it off the car's
shape (two of the anatomy's lines, by `course.flow`: the sidepod's outer shoulder from behind the inlet,
then the rear flank's shoulder round the tail corner and across the tail), on both sides, meeting at the
tail's middle.
- Shown (2026-10-06): first as two of the anatomy's lines joined (an S where they met at the sidepod's
  rear corner), then as the map's shoulder (`course.shoulder`, new) from z -12 to the tail corner and the
  tail's edge across. The user: "Ok now I know you are simply not able to understand the car's geometry,
  those lines are so wobbly". Seen close up every 8 to 10 cm: the line is one smooth curve, but it drifts
  up and down the rounded shoulder by about a centimetre against where its shading turns, which reads as
  wobble. Open: whether to try the edge as the line where the shading turns halfway (asked).
- The user: "If you actually look ffrom the side, you can even see that the shadow divides the edge
  properly and your lines dont even follow", then "maybe you can figure out a shadow that will help you
  get a perfect edge to the car". Measured against their own stroke of the right rear flank's edge
  (note 2 on TSC_Endurance): it runs within 0.26 cm (median, 0.59 for 90 %) of the line where the
  surface, as the game shades it, faces 60 degrees from up; the shoulder's crest ran 1.4 cm off it.
  Built `course.shadow(guide)`: that line along a guide, midway between neighbouring texels either side
  of 60 degrees (so on the tail's sharp edge it is the crease), held to its neighbours so it never jumps
  to another panel's rim (the sidepod top's back edge, the tail corner's front edge). Repainted along
  the shoulder from z -14, across the tail's edge to the middle. Checked close up every few cm on the
  left: on the shadow's divide, smooth, no hook at the inlet, no jump at the sidepod's corner; across the
  tail's sharp edge the line wraps half onto the back face and looks thinner from above.
- Notes 1 to 3 (user, 2026-10-06, the right side): "The transition between this part has a jagged line.
  It just needs to follow straight" (the seam at the sidepod's back), "Same here." (the tail corner's
  seam), "Why is this not reaching the edge?" (it stopped 3 to 4 cm short of the inlet's frame). The
  shadow's edge is now fitted as one smooth curve (a knot every 6 cm), so it runs straight on where the
  shading steps across a seam; it starts at z -12 (just ahead the divide turns round the sidepod's front
  corner) and is carried on straight 3 cm under the frame (`Course.extended`). Checked at the three pins.
