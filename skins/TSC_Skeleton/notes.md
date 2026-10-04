# TSC_Skeleton

Not a design of the user's: the tool's skeleton car, the plan's step 2 (PLAN.md). The user's words
it serves (2026-10-02): "A skeleton that functions like a guide for the blind." "Layer by layer,
accurate throughout, like a topographic skeleton every x cm", and "literally painting lines, as in
a skeleton."

Read as: the clay car with the body's cuts (tool/skeleton.py, car/skeleton.npz) painted as thin
lines: contours level all round in black, sections across the car in red, profiles along it in
blue, every 50 cm twice as thick to count them by. Made 2026-10-04 by Claude Opus 5.5.

- Shown (2026-10-04): two spacings as set 1 in the Lab, every 10 cm and every 5 cm.
- Picked B, every 5 cm (user, in the Lab, 2026-10-04). Close looks checked: the lines run unbroken
  across the panels' joins, the contours level and every family evenly spaced.
- The user (2026-10-04), after the looks in the viewer (the 70° line, the steepness rings, the level
  lines): "You're just not mapping things properly, evey line you do are just so distorted and
  disformed. The reality when it comes to this car is that you wouldnt add horisontal outlines that
  are exactly 90 degrees. The cars top has a curvature, and that's why Peach for example does not do
  90 degrees, because it follows the slope of the model, but either way, i have a feeling you just
  don't know how to tace a car because the lines you make are so imperfect". Measured: the model's
  faces on the top are 5 to 6 cm long (up to 24), meeting at 6° (often 20°) in the curve; every line
  was computed face by face, so it bends at each edge. Open: one line traced as a single smooth
  stroke (Peach's seam, the edge between two pieces of the skin, carried over the nose in its flow),
  shown in the viewer, before anything more is built on the skeleton.
- The user: "cant you just trace peach's from the uv map?" Measured: Peach's line is painted inside
  one piece of the texture and follows no face edges (22%): the artist drew one smooth curve in the
  flat texture, which stays smooth on the car. Traced the same way (its edge texels, one smoothing
  spline per piece of the texture it crosses, three a side, within 0.3 texels of Peach's edge;
  painted 0.8 cm wide in texture space): smooth, unbroken across the joins. Shown in the viewer
  (Look_PeachLine, a look in the work folder; Peach's texture stays local). Waiting for the user's
  verdict before anything is built on it.
- The user: the lines must go all the way round and connect at the nose; "cover only the top" must
  follow the shape, not split it flat. Then: "if you look at the car body side (no wheels), the car
  top is curved, and same with the bottom. That for me is the car's 'line'. so that for me is the
  guide to having the levels." Shown in the viewer: the top's edge all round (where the surface,
  judged over 5 cm, is 70° steep, traced from above and smoothed into one closed curve; it dips at
  each sidepod's front, where the body rolls over more gently) and the top covered by it. Tried and
  not shown: levels between the profile's top and bottom taken as each slice's highest and lowest
  points (the cockpit's hoop, the inlets and the nose's underside make them jump, and every level
  waves). Asked the user to pin the top line and the rocker line in the lines room.
- The user (screenshot of the sidepod's front): "You're asking me and you just don't notice how the
  line is distorted in plain site." The top's edge traced from the shape rippled (the 70° line
  follows every bump: an S at each sidepod's front, waves along the side), and Claude had explained
  the S away as the car's form. Redone the designer's way: the edge's height along the car smoothed
  into one gentle curve (nothing shorter than about a metre left: 61 cm at the tail, 56 along the
  sidepods, 59 by the cockpit, 43 at the nose tip), then the line wherever the outer body is at that
  height, all round. Checked close up at the user's framing: one smooth stroke along the sidepod,
  across its front, over the rear wheel, round the nose tip; at the back it runs along the rim
  where the body's skin ends. Shown in the viewer (Look_TopEdge, Look_TopCovered).
- The user: "a bit more smooth but there has to be a way where the top surface is somewhat less S
  curve in the back. following the surface corner of the curve". The line held a set height and slid
  1.5 to 2.5 cm down the side where the corner rises (the rear widening into the sidepods). Now its
  height comes from the corner itself on every slice (the middle of the roll from top to side, 60°
  steep), smoothed the same way: 61 cm at the tail, 57 along the sidepods, 60 across the sidepod's
  front and the cockpit's sides, 41 round the nose tip (the slices from 13 to 35 cm forward read the
  floor and are left out; the tip's last cm come from the outline seen from above). Checked close up
  from high behind, at the sidepod's front and round the nose tip. Shown in the viewer.
- The user asked for a tool to place the line themselves from the side: built, the Lab's levels room
  (lab.html?room=levels, tool/levels.py, car/levels.json): drag points on a side view, the line on the
  3D car follows live, "Show it on the car" paints it (14 s). Starts from the top's edge above.
- Open (user, 2026-10-04, end of session): "I realised the car is not simmetrical. Is that a car issue
  or actually the tool is not making things simmetrial." Measured: the body model is symmetric (98% of
  its points sit on their mirror image, 0.00 cm); only a small one-sided feature on top, z -80 to -40,
  y 63 to 65 (probably the fuel cap). So what looks lopsided comes from the tool or the viewer: next
  session, ask where they saw it (a screenshot), then find it.
