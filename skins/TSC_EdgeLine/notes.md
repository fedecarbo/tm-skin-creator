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
- Note 4 (user, 2026-10-06, the left tail corner): "Firstly there's tiny wobbles in general.  But also,
  just make it go around straight, not make it start to ascend". Seen with a narrow lens: along the sides
  the line is smooth and even; the wobbles are at the back (a notch at the tail corner's slot, a 3 mm dip
  where the fit overshoots the corner, the line ragged along the tail's sharp edge). Across the back there
  is no bodywork at the side edge's height (60 cm up): only the deck's lip at 63 to 65 and the inner car's
  tail frame below it. Asked (question 1): climb gently round the corner, level across the frame, or stop
  at each corner.
- The user's pick (question 1): stop at each tail corner. The shadow's edge along the shoulder to z -152,
  carried on straight 5 cm to where the side ends at the tail corner (z -154); nothing across the back.
  Checked close up at both corners: straight to the end, no dip, no climb.
- The user, 2026-10-06: "I look at the uv map and the lines are wobbly, so you cant tell me they are not.
  It's getting better but sursly there has to be a way that the line rund smoothly". In the flat texture
  the strip measured on the car wandered a texel or two and thinned to 1 to 2 texels in places: the
  flat layout stretches each of the model's small faces differently. Built `Course.inked`: the strip
  drawn on the flat texture, one smooth curve per piece of it, its width even there. Measured on the
  car's own texels: width 6 to 7 texels along the rear flank (was 1 to 7). The user: "better".
- The user: "It's better, yes", then "That line should be a guide line". Stored as the guide "edge"
  (car/top_lines.json, the left side every half centimetre; `levels.write_edge()` remakes it from the
  car's shape); the test car paints it from the guide, `course.top_line("edge").mirrored().inked(0.6)`,
  the same line as approved.
- The user, 2026-10-06: "I want to continue with another agent.  I do have a hypothesis if a straighnt
  line from the uv will create the perfect line in the car". Open (next session): test it. On the flat
  texture the edge already runs nearly straight on its pieces (the rear flank's: column 1062 to 1054 over
  700 rows; the sidepod's: 291 to 274 over 330 rows); a line drawn dead straight on each piece, between
  where the edge enters and leaves it, set against the shadow's edge on the car, would show how far a
  straight line strays from the edge the user sees.
