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
- The user (2026-10-04, next session): "im really struggling to get this skeleton right, and if I cant
  get it right. I think AI wont be able to map the car properly". Where each spot of paint sits is
  measured exactly; what failed is lines traced off the model's facets. Proposed: the user draws
  only the top and bottom lines, and the levels between blend from one to the other (smooth by
  construction). Asked what they'd need to see before building it.
- The user: "I would need to see, because sometimes you suggest a 'better' approach, and then you
  fail", and "the purpose of the skeleton is to help you at the end of the day, if it doesn't then
  it's no point doing them". Built and checked before showing: the levels room takes a top (the top
  edge) and a bottom (new: the body's lower edge, from the tail's end to the sidepods' front, 38 cm at
  the tail, 19.5 to 22 along the side, 18.5 at the front), and shares levels out evenly between them
  (5 to start, the room's − and +). The bottom and the levels between run only as far as the bottom:
  held level they ran on along the floor's blade and round the front wing. Found on the way: the side
  tucks under along the sidepods (15 to 40 degrees down from 34 cm to its foot) and the paint had
  skipped anything over 15 degrees down, so the lower levels faded and the bottom didn't show; now only
  the real undersides (over 50 degrees down) are skipped, the top edge unchanged. The levels stay off
  the inlets' roofs and the struts under the nose. The room's live lines had sat 1.2 cm under the
  paint since it was built (the viewer raises the car to put the tyres on the floor); now on it, and
  shown only for the level picked and what changed since the last paint. Checked close up on both
  sides, every stretch, and from low down. Shown in the levels room.
- The user (screenshot of the right side between the rear wheel and the inlet, from a little above):
  "with the help of the shadows, you can actually see that the line is not fully defined properly,
  the line falls below the curved surface and in another part if falls above the curved surface".
  Measured from the shading (the smooth normals): the shoulder's curve, from 65 to 25 degrees, is only
  3.3 to 3.7 cm tall there; the user's top line ran from 0.5 cm under its middle by the wheel to 0.9
  over it by the inlet, and the line of the session before 0.5 to 1.8 cm under it all along. Left and
  right measure identical. The top line's points from the tail to the inlet refitted to the middle of
  the curve (45 degrees): six points, within 0.18 cm of it all along (0.05 on average), bending one way
  then the other only where the shoulder does (behind the wheel); the user's points from the inlet
  forward kept. Checked close up straight into the shoulder every 20 cm, old beside new: the new line
  keeps the middle of the turn all along; the inlets and the tail unchanged. Shown in the levels room.
- The user: "Can you remove the ones I added because it's hard to see." Removed "level 2" (the only
  one saved; "side level" never was). The room now re-reads the levels when the user comes back to the
  page, so an open or old copy never saves over a change made from here.
- The user: "Feels more accurate, yes. Would be nice if the bottom one would follow seamlessly the
  crease of the diffuser strake when you look at it on the side", then "if you look at the tail corner
  as well, that could help with the other blue lines". The crease (the rear flank's lower edge over
  the strake, z -141.5 to -110.5, 28.2 to 20.6 cm) ran 0.4 to 0.8 cm above the bottom line; the tail
  corner's edge from the side climbs from (-142, 28.5) to (-154.5, 58.5). The bottom refitted through
  both, the angle between them rounded: within 0.24 cm of the crease and 0.19 of the corner, one way of
  bending from the tail to -68, unchanged ahead (within 0.15). The levels between now sweep up the tail
  corner and gather into the top of it, a fan. Tried and not kept: the crease alone (the levels between
  wrapped round the corner as before). Checked close up at the gathering, the turn and the crease, both
  sides. Shown in the levels room.
- The user: "No, you ruined it. I meant to say is that the bottom line, should seamlessly meet the
  seem of the bottom piece. ignore the other lines. they where fine initially how you had it. Ill
  explain the other line, but for now it was the bottom one". The tail corner climb undone: the bottom
  line is the first one again, moved onto the seam over the diffuser strake (within 0.24 cm of it from
  the side) and within 0.54 cm of itself behind it and 0.2 ahead; the levels between as they were (the
  lowest moves at most 0.76 cm, by the strake). Measured on the paint, both sides: the line had run
  0.4 to 1.1 cm under the seam, now within 0.27 of it. The user will explain what they meant about
  the tail corner and the other lines.
- The user: "Yes perfct." Then: "you see the rear wing seam from the side, it lies close to the
  second and third. While Im not expecting either to be exact because these are guides, I do expect
  that the lines follow the same curvature". Measured: the rear wing's lower seam from the side runs
  parallel to the top line, 8.5 cm under it (52.8 to 53.3 cm, z -152 to -126); shared evenly, every
  level took its share of the bottom's climb at the tail, and the second and third lines (the top
  first) tilted 1.6 and 3.2 cm against the seam over its length. The bottom's shape now fades out
  towards the top (s of the way down: s times the typical gap below the top, plus s² times how much
  the gap there differs): 0.2 and 1.0 cm; the lower levels still follow the bottom, the tightest gap
  2.2 cm at the tail's end. Checked at the tail side-on and from behind; the room's lines match the
  paint's within 0.005 cm. Shown in the levels room.
- The user: "BTW ... more looking front there are seams between pieces, like the one between body
  shell and side skirt." Measured: that seam runs level at 29.5 cm from the inlet's frame to the front
  wheel opening (the side skirt's top edge runs level at 26 cm under the inlet); the two lowest
  levels either side of it fell about 1 cm towards the front over its length, following the bottom.
  Proposed: the car's seams as guides for the levels near them; asked whether the lines should share
  a seam's curve or one sit on it. The user: "Actually, let's first do 6 lines as guides instead of 5,
  I think that helps a little." Six between (the user's own edits in the room kept: a point on the
  top at z 6.6, the bottom's front end at 81.5, 18.8); the fifth now runs on the front seam (29.3 at
  z 60), the second and third either side of the rear wing's (56.4 and 51.5 against 53). Checked
  every stretch, both sides. The seams as guides still open.
- The user: "I didnt want to edit by the way, I just couldnt undo". Both edits taken back (the top
  and the bottom as before them; six between kept). Found: a single click on the side view added a
  point, a click on a point with the slightest wobble moved it, and after turning the car the
  keyboard's undo went to the car, not the room. Now a point is added with a double-click, a point
  moves only once the pointer has moved a few pixels, and the room's keys work from the car too.
- The user, on what the guides are for: "the purpose of these guides is that you as the painter can
  guide yourself to painting. ... Im not expecting that paint should only be in the guides
  themselves, but for you to have a bit better "eyes" to paininting. I guess my goal is that the uv
  map is a uv map +, something digitally perfect for you."
- The user: "Sure" (the seams, then a quick test paint with the guides). The seams along the side
  traced from the mesh as named lines (tool/seams.py: the rear wing's lower seam, the strake's, the
  side skirt's top edge under the inlet and ahead of it, each within 0.05 cm of its edge), drawn in
  the levels room in orange, paintable along. Tried and not kept: pulling the levels near a seam to
  keep their distance from it (a pull per seam faded past its ends, then one smooth correction per
  level): both bent the levels into S-shapes round the inlet's front corner, where two level seams
  sit 3.5 cm apart in height while the top and the bottom fall towards the nose. Kept instead: the
  bottom runs level at the front (21.9 to 21.6 cm from z 40 to 82, it fell to 18.5), so the levels
  near the side skirt's seams run alongside them (they drift 0.5 to 0.9 cm over a seam's length,
  1.4 to 1.6 before; at the rear wing 0.07 and 0.6), shaped by the top and the bottom alone. Checked:
  every stretch, the low looks, the bottom's front end; the room's lines match the paint's.
