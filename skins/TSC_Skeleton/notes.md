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
- Closed further down, "I think it's fine" (user, 2026-10-04, end of session): "I realised the car is not simmetrical. Is that a car issue
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
- The user: "I think the bottom line need to follow the shoulder (surface curvature) going to the
  front. Maybe that helps." (And of a point that moved: "I keep moving without wanting, just ignore
  it": the bottom's front end had been dragged to z 41, 77 cm and went into c820c67; replaced.)
  Measured from the shading: the middle of the turn under (45 degrees from straight down) runs at
  about 20.7 cm along the sidepod and falls to 17 by the front wheel; the level bottom ran 1 to 5 cm
  above it there. The bottom from the strake forward refitted to it (within 0.28 cm on average,
  stray slices at the inlet's frame set aside), bending only where it did before. Seen low it runs
  where the side rolls under all the way and ends on that edge by the front wheel opening. The cost:
  the side skirt's top seam under the inlet runs level while the turn under falls, so the lines near
  it drift 2.3 cm over its length (1.5 before); the rear wing's unchanged.
- Where the session stopped (2026-10-04): the test of the guides, TSC_GuideTest, is in the Lab with
  the question "does the paint land the way a designer would draw it?" (its question 1), unanswered.
  Open: the user's verdict on it (then delete TSC_GuideTest, git keeps it); the side skirt's seam
  under the inlet runs level while the bottom (on the turn under) falls, so the levels near it drift
  2.3 cm over its length; the car looking lopsided somewhere (the user was to show where: never seen
  yet); "side level" not saving (likely the stray clicks or an old copy of the room, both fixed: ask
  if it happens again).
- The user (next session, 2026-10-04): "We havent defined the lines in the front part of the car btw".
  Seen: the top line runs along the nose's lip (its widest point, where it tucks under), so the whole
  nose sits above it with no levels; the six between and the bottom end in a straight cut at z 82,
  and the test car's band stops dead there. Open, after the verdict on TSC_GuideTest.
- The user, of TSC_GuideTest: "I think it's looking accurate". The guides hold for painting; the test
  car goes (git keeps it). Next: the front's lines.
- The user: "My theory for the bottom is that considering the back part is fine, it should keep on
  following the sholder of the surface (when it starts folding). I think it's quite clear to follow
  that for the front for the bottom level it seems". Measured: the side skirt runs on from the
  sidepods under the nose to the tip and round its front, its edge a bevel about 1.6 cm tall; its
  45-degree point jumps 0.85 cm where the mesh's corners change (z 120), so the bottom follows the
  middle of the turn under (halfway from facing out to facing 60 degrees down): 20.3 cm by the
  sidepods, 16.9 at z 87, then 16.85 to 16.7 to the tip. The bottom's points behind z 50 kept
  (moved 0.01 cm at most), four new ones ahead (z 82 to 216): within 0.21 cm of the edge (0.04 on
  average), no bend changing direction, round the tip joining both sides. The levels between end
  where they did (the sidepods' front), so their spacing holds; the lowest moved 0.23 cm at most
  (z 50 to 82, where the bottom had run 0.3 under the edge). Checked close up in red, both sides,
  low and from above (no stray line on the skirt's top), and round the tip. Shown in the levels room.
- The user, of the bottom to the tip: "Seems alright to me". Next: the levels between at the front.
- The user: "I maybe think it's a little under the fold? Maybe we need it right at the fold? Im
  assuming it doesn't matter if it follows the shape either way correct?" (Yes: the crest and the
  middle of its turn run parallel within 0.4 cm.) Measured: along the sidepods the body turns under
  in a broad roll (6 cm tall) and the bottom keeps to its middle (unchanged); from z 40 forward the
  lower edge is a blade (the skirt, its top facing up) and the line had run on its bevel, 1.1 cm
  under the crest. The bottom from z 10 forward now runs on the crest (where the edge faces straight
  out): three points (z 50, 110, 216), within 0.39 cm of it from z 40 (0.03 on average), round the
  tip at 17.5; behind z 10 it moved 0.12 cm at most (at z -12). The levels between moved with it at
  the front flank (the lowest up to 0.93 cm, z 10 to 82; under 0.1 behind z 10), and drift less
  against the side skirt's seams: 2.46 to 1.98 cm under the inlet, 1.44 to 1.20 ahead of it. Tried
  and not kept: the levels between carried on to the tip (only the lowest found any body there, a U
  on the skirt's top round the tip). Checked close up in red: the blend at the sidepods' front, the
  skirt both sides, round the tip. Shown in the levels room.
- The user: "Yes, front is perfect. I wonder if we move a little up the part where the intake is, you
  see the fold is a bit above?"
  Measured: under the intake (the side skirt, z -26 to 30) a flat face just under the seam, facing
  15 to 25 degrees down, bends into the turn under at a crease (between 30 and 35 degrees, the
  sharpest bend) at 22 to 22.4 cm; the bottom ran about 1 cm under it. Behind the intake the crease
  spreads into the broad roll, ahead it becomes the blade's crest. Refitted the whole bottom at once
  from z -50 forward (kept as it was behind, the crease from z -26 to 30, the crest from z 40):
  within 0.23 cm of the crease (0.07 on average), the crest now within 0.14 (was 0.39), behind z -50
  moved 0.08 at most, no new bend. The cost: the lowest levels follow it up under the intake and
  drift more against the side skirt's seam (2.43 cm over its length, was 1.98; ahead of it 1.32, was
  1.20); the rear wing's unchanged (0.62). Checked close up in red, both sides, a little above and
  below and along. Shown in the levels room.
- The user, of the bottom under the intake: "Seems accurate". Open: the levels between at the front
  (they end in a straight cut at z 82, where the nose begins); the side skirt's seam drift (2.43 cm);
  the car looking lopsided somewhere (the user to show where).
- The user, asked how the six lines between should end where the nose begins: "I guess you could
  give it a try". Measured: the lower four end on the front wheel opening's upright edge (z 69.6 to
  72.2 from 30 to 40 cm up, curving forward at its foot into the skirt and at its top into the
  nose's underside); only the top two run past it onto the nose's underside and were cut at z 82.
  Shown as set 2 in the Lab: A, the top two end in line with the opening's edge (z 70); B, they sweep
  up (a smooth S from z 30 to 100) and stop where they touch the top line (z 82 and 88). Tried and
  not kept: B running on along the top line (it tinted it blue). Checked close up, both sides.
- Picked A (user, in the Lab, 2026-10-04), with a screenshot of the right side ahead of the intake:
  "A. But also, you see there's a marking seam between the body shell and the side skirt. I think
  the lines should follow that curvature no?" A built into the guides (OPENING: a level between
  that passes over the opening's upright edge ends in line with it, z 70), and TSC_Skeleton's design
  is now the guides on the clay car. Measured: both side skirt seams run level (25.8 cm under the
  intake, 29.5 ahead, a 3.7 cm step between at the intake's front corner) while the top and the
  bottom fall about 4 cm towards the nose, so every line between fell across them (2.4 cm against
  the seam under the intake, 1.3 ahead). Now from the intake forward each line takes the seams'
  direction (one straight line through each, -0.44 cm per metre) by the square of how far down
  towards them it sits, growing in from z -45 to -25: the nearest runs within 0.33 cm of parallel
  to the seam under the intake and 0.35 ahead, the spacing narrows evenly (5.0 to about 4.3 cm at the
  front), no new bend, nothing moves behind z -45. Tried and not kept: following each seam's own
  traced shape (the lines copied its 1 to 2 mm ripples). The six lines now end in a near column on
  the opening's edge (z 70 to 74). Checked close up from the screenshot's angle, both sides, under
  the intake and where the lean grows in; the room draws the paint's lines exactly. Shown in the
  levels room and on the skeleton car.
- The user: "I guess that looks good. Obviously there's more of a gap in the front for the bottom and
  the next blue line, but I guess it's supposed to be like that?" Yes: the lowest line runs level
  with the seam while the bottom falls with the skirt's fold (the skirt is 4 cm from its top seam to
  its fold under the intake, 11 ahead of it), so the gap opens from 4.6 cm under the intake to 8.1
  where the lines end. Kept.
- The user, of the seam: "Considering the seam we are following. So Im assuming it's accurate" (yes:
  traced within 0.05 cm of the mesh's edge, the nearest line within 0.33 of parallel). Of the car
  looking lopsided, asked for a screenshot: "I think it's fine". Closed. Still without lines: the
  nose's own side above the top line (from the cockpit to the tip).
- The user, asked whether to define the nose's lines next: "Sure". Read as the side's way: the nose's
  own top line where its top folds down into its side (the middle of the roll, 45 degrees, as the top
  line along the sidepods), the top line (the nose's lower edge) its bottom, lines shared evenly
  between, closing at the tip. Measured: the fold runs 68.6 cm at z 36 (where the sidepods begin), 63
  at the cockpit's front, 48 by the front wheels, and meets the top line at the tip (z 206); the
  wedge is 13 cm tall by the cockpit. Fitted with four points and the tip: within 0.34 cm (0.08 on
  average), bending one way only (five points bent one way then the other by the nose fin). Two lines
  between. They start in line with the intake opening's front edge (z 28, where the body's skin at the
  top line's height begins; behind it the area above the top line is the sidepod's broad top). Checked
  close up: the tip from both sides and above, the start, the nose fin. Shown in the viewer as a trial
  (Look_Nose, in pink), before it goes into the levels room.
- The user, of the trial: "I don;t know, I personally think that the lines shouldnt meet at the nose",
  then "As in the top ones" (the nose's lines). Shown as set 3 in the Lab: A, round the nose (three
  lines each keeping its height above the top line, a third of the nose's side apart where it begins,
  12.9 cm, going round over the nose in a U at z 146, 175 and 196); B, the nose's top line and two
  shared out under it, stopping in line with the front wheels' axle (z 178). Checked close up: the
  tip, the start, both sides, from ahead and from the driving camera.
- Picked A, round the nose (user, in the Lab, 2026-10-04). Built into the guides: `nose` lines above
  the top line (3; the room's second − and +, "On the nose, above the top"), each a share of the
  nose's side where it begins (12.9 cm at z 36, from the top line to where the nose's top folds down)
  above the top line, from z 28 (in line with the intake opening's front edge) to the tip, going
  round over the nose in a U at z 146, 175 and 196. In blue with the other lines; the room's side view
  stops each where it goes over the nose's top. The room draws the paint's lines exactly (0.0000 cm).
  TSC_Skeleton's design is the guides again. Self-test: every car identical.
- The user: "they look ok. its hard to know if im heading the right direction. Not sure if the example
  skins help with some guidance". Measured on the eleven example skins in the work folder (local, never
  pushed; overlays Look_Guides_*, the guides in thin magenta), per 4 cm slice the strongest colour change
  near each line: on the nose every one runs parallel to the top line at a height of its own (spread
  within 1 to 2 cm along the nose): F2002 and the two RBS3 on it, Peach and Melon 1.8 under, Red Bull
  4.8 above (the lowest nose line, 4.3), Envision 6.2, Citroen 8.2 (the middle one, 8.6), Jaguar and
  Nissan 7.8: the nose's lines as picked (round the nose) follow them, converging ones would cross
  them. Along the sidepods each splits the top from the side on the shoulder at a height of its own:
  Red Bull on the top line (0.2 cm, 70% within 1), Envision and Jaguar 3 to 5 above, Peach and Melon 2
  to 3 under. The bottom under the nose: Red Bull and RBS3 pinstripes on it (within 1 cm along 70 to
  100%), the others 1 to 2 cm above. None paints along the levels between: their sides are one colour
  with logos and diagonals. Shown: Red Bull and Peach with the guides, in the viewer.
- The user, of the example skins against the guides: "Seems ok to me": the direction holds (the
  guides as they are: the top and the bottom where designers split and pinstripe, the nose's lines
  round the nose, the levels between for measuring). The overlays are gone from the work folder.
- The user: "I am wondering looking at the redbull one, the bottom red strip, maybe I have the bottom
  line in the back wrong?" Measured on Red Bull's Skin_B: the red strip runs level at 21.7 to 22.3 cm
  (its middle) from z -102 (where the rear's lower piece begins) to the intake, then on the bottom
  line to the tip; the bottom (the middle of the sidepod's roll under, 45 degrees) dips under it,
  2.8 cm at z -90, joining it by z -30. The two RBS3 (the same painter) put theirs 2 to 3 cm above
  too; Nissan splits its colours 4 to 5 above; the others paint nothing there. The body has no fold
  there: the side rolls under over 6 to 10 cm, the strip crosses its upper part. Shown as set 4 in
  the Lab, the bottom in pink: A, as it is; B, on the diffuser strake's seam to its end (20.6 cm at
  z -110.5), then straight to the crease under the intake (22.06 at z -22): within 0.1 of the seam,
  two bends as before; C, down the seam, then level at the crease's height (22.0 to 22.1) from z -108,
  leaving the seam 1.5 cm above its end, like Red Bull's strip. Each fitted to its shape (within 0.1
  cm), ahead of z -22 unchanged. Checked close up from the side and low from both quarters: smooth.
- The user: "between b and c which do you recommend? considering the rest of the lines above might
  need to be readjusted". Measured: the levels between follow on their own (the three highest move
  under 0.2 cm with B, 0.3 with C; the lowest 1.5 and 2.3); the rear wing's and the side skirt's seams
  keep their nearest lines as before; the spacing is more even than A's in both (C a touch more).
  B keeps the bottom on the diffuser strake's seam (drift 0.19 cm, A 0.40), C parts from it (1.63).
  Recommended B. The user: "b then lets see". Picked B (straight from the seam): the bottom's points
  at z -110, -88 and -50 replaced by -116, -104 and -32 in the guides; TSC_Skeleton's design is the
  plain guides again. The room draws the paint's lines exactly (0.0 cm). Checked close up from the
  side and low from both quarters. Self-test: every car identical.
- The user, of the bottom along the back: "looks good". The Red Bull overlay is gone from the work folder.
- The user: "How about defining the top ones" (the lines above the top line, which only the nose
  has). Measured on the cross-sections: down the middle runs a raised spine (the nose, the cockpit
  surround, the engine cover) with a sloping side 14 to 15 cm tall from z 20 to -60 (its foot 7 to 8
  cm above the top line, 64 to 66 cm), shrinking to 4 cm by z -100 as the engine cover falls to the
  tail's deck; either side of it the sidepods' tops, flat shelves between its foot and the top line.
  Trial (Look_TopLines, in the work folder, in pink): the nose's three lines carried back along the
  spine's sides at the same heights above its foot (4.3, 8.6, 12.9 cm), rising onto it over z 50 to
  20 (above the sidepods' front, where the foot climbs 7 cm), and going round the engine cover's back
  in U's (z about -62, -83, -100), as they go round the nose: three rings round the spine. The
  sidepods' tops and the tail's deck are flat (no height to follow) and stay without lines for now.
  Checked close up: the U's from above and the side, the sweep from the side and high, the cockpit's
  side, the mirror mount (untouched). Shown in the viewer.
- The user, of the trial: "The back ones should follow the top shape of the car, if that makes sense".
  Read as: not turning across the engine cover, but on to the tail, riding its top down. Trial 2
  (Look_TopLines again): from the cockpit's back (z -30 to -55, a smooth hand-over) each line keeps
  where it is seen from above (30.6, 34.8, 38.9 cm from the middle, clear of the number and name
  panels), so it rides down the engine cover's back with the top and runs along the tail's deck to
  the tail's end; ahead of the hand-over unchanged (heights above the spine's foot, round the nose).
  Checked close up: the hand-over from the side and above, the engine cover's back from the side and
  high behind, the tail's end from behind and above. Shown in the viewer.
- The user: "I was actually thinking on looking the the black line, the next line would offset from
  that. and so on. So it basically forms the shape of the top car. You sse the rear flank seam from
  the top, that might help you with how the first red guide would go, but of course following the
  offset from the tail and so on." Measured from above: the seam inside the black line at the back
  (the body shell's and the engine cover's outer edge against the rear flank, z -52 to -124) runs a
  steady 6.2 cm in from it (5.8 to 6.7). Trial 3 (Look_TopLines): three rings, the black line seen
  from above set in by 6.3, 12.6 and 18.9 cm, all round: along the sidepods, round their front corner
  and across their front, along the nose and round its tip in U's (the third a long one, back by the
  nose fin), across the tail. Made from the top seen from above (where the body stands above the
  black line, the cockpit filled in), its distance from the black line smoothed over 6 cm so the
  rings bend smoothly at the corners and close round at the nose. The first runs on the seam (within
  a cm at its ends). The nose's lines give way to them in the trial. Checked close up: the seam
  (with and without the rings), the tail corner, the sidepod's front corner, the nose root, the
  cockpit's front, the nose tip from above and the side. Shown in the viewer.
- The user: "So the back is getting better but the front not at all. you know the nose pannel has a
  seam on the front. I think that should follow that curve. If you want you can just have one red
  line so we can define that one first". The nose panel (on the nose's top, z 142 to 186.5, x within
  12.4) has its seam round its front and along its sides, 9 to 13 cm in from the black line seen from
  above (the rear flank's seam 6.3). Trial 4 (Look_TopLines): one line, its own curve seen from above:
  6.3 cm in from the black line across the tail, on the rear flank's seam and along the sidepods;
  flaring in over the sidepods' front (z -12 to 30, where the black line flares) to 12.3 cm in,
  parallel to the black line along the nose; easing onto the panel's sides (z 118 to 146) and round
  its front on its seam. Tried first and not shown: 6.3 in up to z 60 and then drifting across the
  nose to the panel (an 80 cm diagonal tied to nothing on the car). Checked close up: the panel from
  above and the front quarter, onto the panel from the side, along the nose from above, the flare,
  the tail. Shown in the viewer.
- The user: "Sorry, I should have been more clear, the first red line, should be between the nose
  panel seam and the black line if that makes sense". Trial 5 (Look_TopLines): the line 6.3 cm in
  from the black line all round (on the rear flank's seam), and from the nose panel's back on (z 135
  to 165, easing in) halfway between the black line and the panel's seam, its sides and its front:
  6.3 to 4.7 cm in along the panel's sides (it narrows less than the nose), round the front in a U at
  z 196 (the panel's front 186.5, the tip 210), a corner of 12.9 cm radius at the tightest, one gentle
  bend along the nose. Tried and not kept: easing in from z 100 (a 0.7 cm bulge at z 120 where the
  panel's side carried back runs wider). Checked close up: the panel from above and the front quarter,
  the side, along the nose, the flare, the tail. Shown in the viewer.
- The user: "But you are for some reason making it more round. Consider as in the corner just have a
  bigger or smaller corner radius, not a full circle at the front, same when you go around the car.
  The red line should have an offset inside with a consistant distance from the black if that makes
  sense". (The roundness came from smoothing the distance over 6 cm.) Trial 6 (Look_TopLines): the
  black line seen from above set in by exactly 6.3 cm all round (6.33 to 6.44 over 90% of it), a
  corner that would come out sharper than 3 cm radius given 3 cm: flat across the nose's front (z
  204) and across the tail (z -155) with rounded corners, the sidepods' corners rounded. Where the
  nose meets the sidepods (z 0 to 40) the black line swings twice seen from above, and the exact
  set-in waved with it: smoothed over 12 cm there into one S (5.1 to 7.5 cm in there, the only place
  it strays). Tried and not kept: bridging the dip (no change: it is a swing, not a notch). Checked
  close up: the nose tip from above and the front quarter, the nose root from above and the side,
  the sidepod's corner, the tail. Shown in the viewer.
- The user: "Front is better but it needs to be closer to the black line. The back is fine, it's just
  the front sides are too separated from the black if that makes sense". Measured along the surface
  (not from above): the 6.3 cm set-in from above was 6.3 to 6.8 cm along the surface at the back but
  10 to 14 along the nose's sides, which are steep where the black line runs. Trial 7
  (Look_TopLines): the set-in from above that keeps the back's distance along the surface (6.7 cm),
  evened out along the car over 25 cm (an exact one followed every step and edge of the nose's skin
  and notched at the sidepod's front corner: not shown), placed as before with 3 cm corners and the
  nose root's S. From above: 6.2 to 6.6 at the back, 5.7 at the sidepods' front, 1.7 to 4.2 along
  the nose, 3.0 across its front; along the surface 6.1 to 6.6 at the back and along the nose's
  front half, 8 by the nose root and 7.4 at the tip's corners (the evening out). Checked close up:
  the nose from the side and high, the nose root, the tip, the sidepod's front corner, from above.
  Shown in the viewer.
- The user: "Now it looks distorted, expecialy front half. So in essence when you look at it from the
  side, the front half should be lower, closer to the black", then "If there are example skins that
  might help you, go ahead and check". Measured from the side: the line 6.3 cm in from above sits 2.3
  to 2.9 cm above the black line at the back, 11 to 12 along the nose. Trial 8 (Look_TopLines): at the
  back as before (6.3 in from above, on the rear flank's seam), from the nose root on a level 2.6 cm
  above the black line (as the blue ones follow it below), handing over at z 15 to 45 (handing over
  at the sidepods' sides instead took it down the sidepods' front face with the black line, broken by
  the inlet: not shown). The example skins (local, never pushed), the first strong colour change in
  from the black line: at the back 1.1 to 2.7 cm above it (about 2.3), 1.2 to 8.2 in from above
  (about 5.5), as the line; on the nose 5.2 to 10.7 above (about 7), 1.8 to 9.2 in, parallel to the
  black line from the side (Peach: none found). Also painted: Look_TopLines_High, the nose's part 7 cm
  above (over the nose's top in a U short of the tip). Both checked from the side, high side and front
  quarter. Asked in the Lab (question 8) which height, both open in the viewer.
- The user: "A lot better, but I feel you can stretch the nose a bit more so that it's between the seam
  of the front of the nose panel and the black line" (read as the higher one, 7 cm above, whose turn
  at the tip was at the panel's front). The nose's top stands 7 cm above the black line at z 184 and
  4 at z 198 (halfway from the panel's front, 186.5, to the black line's tip, 210). Look_TopLines_High
  now comes down from 7 to 4 cm above over z 150 to 198 (eased), so it turns over the nose's top at
  z 198: from the front flat with corners, from above a shallow point in the middle (the nose's top
  is 2 mm higher there). Checked: the nose from the side and high, the tip from the front quarter,
  above and the front, the whole side. Question 8 settled in the chat.
- The user: "Yes but I think you could stretch it a bit further so that the red line on the nose it's
  not so above. Also there the intake is, that red line when doing the curve, looka bit wobbly".
  Measured on the paint: by the intake the line rose across the sidepods' front, overshot to 7.9 cm
  above the black line at z 32 and settled to 7 at z 47 (the hand-over between the set-in from above,
  climbing the nose's side there, and the nose's level). Trial 9 (Look_TopLines_High): from the
  sidepods' sides forward one level above the black line whose height is a single monotone curve: 2.5
  cm along the sidepods (the back's own, handing over at z -30 to -16), rising across the sidepods'
  front to 5.6 by z 16, 5.6 along the nose, easing to 3.0 at z 203 so it turns there (stretched from
  198). Tried and not kept: 4.5 along the nose (between 4 and 5 cm above it crosses a lip on the
  sidepod top's front edge twice, by the intake: a split line). Checked: by the intake from the side,
  high side, high front, above, high rear and low front; the nose from the side and high; the tip.
- The user: "It's better. But a little sharp curves where the intake is. All lines should feel like you
  are using the pen tool in illustrator to make things smooth". Measured on the paint: the tightest
  bends 7.5 cm radius at the sidepods' outer front corner (z -17), 6 to 8 halfway across their front
  (z 2), 17 to 20 at the nose root. Trial 10 (Look_TopLines_High): from z -45 to 95 the line is one
  curve in space (the painted path smoothed over 8 cm of its length at the corner, 12 cm from the
  intake on, easing out over 15 cm behind and 30 cm ahead, where the line is nearly straight), painted
  onto the skin beneath it (each point measured across the curve within the skin); the back and the
  nose beyond as before. From above the curve bends no tighter than 22 cm at the corner and 39 cm
  from the intake on; it leaves the old path by 2.2 cm at most (the corner, now rounder). Tried and
  not kept: smoothing seen from above only (the nose root's steep side turned it into height
  wobbles); smoothing from z -75 (the line drifted off the rear flank's seam); rejoining the nose's
  line by z 50 (a step). Checked: the corner, by the intake from the side and high front, from above,
  the front quarter, the whole side.
- The user, of the smoothed line: "Works for now". Built into the guides: car/top_lines.json holds the
  top's lines, each a path in space (the left half, tail's middle to nose's middle, a point every cm,
  taken from the approved paint), and levels.top_line(name) paints one on the skin beneath it (across
  the path within the skin). "top 1" is this line; the skeleton paints it in pink, in place of the
  nose's lines (set to 0 in the room: the top's lines take their place). The skeleton's line lies
  within 0.03 cm of the approved one (0.24 for 99% of it). The trials are gone from the work folder.
  Self-test: every car identical.
- Next (the user will pick it up in a new session): the second top line, set in from the first the same
  way. What the user asked of the first, to keep for the next: the same distance from the black line
  all round, judged from the side on the steep nose (there in height above it, not from above);
  corners just get a radius, never a full round; every line pen-tool smooth (no tight bends where
  the car has them: draw over them); at the front between the nose panel's seam and the black line;
  at the back on the rear flank's seam. How the first was made (the scripts were scratch): set in
  from above at the back (the top's outline from above, its distance field, the level at 6.3 cm,
  sharp corners given 3 cm), a level above the top line with a smooth monotone height from the
  sidepods forward (2.5, 5.6 along the nose, 3.0 at z 203 for the turn), the stretch from z -45 to 95
  smoothed as one curve in space (8 cm at the corner, 12 on), then its painted path saved as
  "top 1". Example skins: their first change in from the black line sits about 2.3 cm above it at
  the back, about 7 on the nose.
- The user (2026-10-05, a screenshot from above of the cockpit and both sidepods' front corners, the
  first top line's turns circled): "Is there a way to make these corners (circled in black) a bit
  sharper, rather than too round.", then "In a way each line should somehow feel paralell to the black
  line if that makes sense". Measured from above: the top's outline (the skin above the black line, the
  cockpit filled in) turns in a crisp corner at the sidepod's front (x 84.4, z -11) and runs straight
  across the sidepod's front to the nose root; the black line itself has no stretch there (the inlet
  takes the front face). The first top line keeps 6.2 to 6.9 cm in from that outline along the side and
  across the front, but its turn (21 cm radius at the tightest, z -30 to -5) cut the corner, up to 9.0
  cm in. Trial (Look_TopCorner, in the work folder): from z -36 to -3.4, straight along the side, a turn
  of 8 cm radius at the tightest (the bend eased in and out over 13.5 cm), straight across the
  sidepod's front to where the line already ran straight, heights from the skin: 6.3 to 7.2 cm in from
  the outline all through the turn; it moves 2.0 cm at most (at the corner), the rest unchanged. Checked
  from above on both sides, high front, high side and high behind, beside the line as it was. Shown in
  the viewer.
- The user (a screenshot of the right side's front quarter at the inlet, the turn where the line comes
  across the sidepod's front onto the nose circled): "I would say this one also needs to have a tighter
  radius no?" Measured: from above that turn spread over z -3 to 40 (43 degrees); on the sidepod's top
  the line holds its height (61.6 to 61.9 cm) and so follows the top at that height, which curves gently
  into the nose's root. Tried and not shown: a corner further in (x 41, z 15, radius 10 to 20, as at the
  first turn), which climbed the nose's root (up to 63.8 cm: a 2 to 3 cm rise and fall from the side).
  Trial (Look_TopCorner2, on top of the first): straight across the sidepod's front to z 9, a turn of
  8 cm radius at the tightest (28 degrees), back on the line at z 22, where it runs onto the nose;
  heights within 0.35 cm of the line's; it moves 1.6 cm at most from above; the nose root's own gentle
  turn beyond (z 22 to 40) kept. Checked from the user's angle on both sides, from above, the side, high
  front and high behind, beside the first trial. Shown in the viewer.
- The user (a view from above of the right side's nose root, the line they want drawn in black: on
  straight across the sidepod's front, a sharp turn, then straight along the nose): "Cant you make it
  like this: Obviously my hands are not precise but hopefulyl you get the point". Trial
  (Look_TopCorner3, on top of the first trial): from z -3, straight across the sidepod's front (parallel
  to its edge) to z 11, a turn of 8 cm radius at the tightest (43 degrees, at x 44, z 14), straight along
  the nose to z 50 (in line with the line's run there), then the line as it was. Turning in further
  takes it up the nose's root: from the side it rises 1.1 cm above the line as it was (to 62.95 cm at
  z 15) and comes back down by z 40; the heights smoothed over 10 cm and settled onto the skin (on the
  steep side by moving across, not down), so from the side it is one gentle rise and fall. Checked from
  the user's angle, above, the side, the front quarter, high behind, along the nose, beside the second
  trial. Shown in the viewer.
- The user (a low view of the nose's side, a magenta line sketched under the line, nearer the black line
  towards the tip): "In the front you could ease a little with the climbing, see the magenta I sketched.
  If you look from the side (from the shadow), the line could keep following the surface curvature if
  that makes sense". Measured on the model's smooth normals: along the nose the line (5.6 cm above the
  black line) sat where the skin is tilted 29 to 31 degrees as far as the cockpit's front, and climbed
  onto the top towards the tip (35 degrees at z 110, 40 at z 150, 52 at z 190): the nose's side shrinks
  under a fixed height. The magenta matches the line where the skin keeps 31 degrees (within about 0.3
  cm at z 170), which comes down to 0.5 cm above the black line round the tip (the two lines would
  merge). Trial (Look_TopCorner4, on top of the third): from z 60 on, the line's height above the black
  line follows the 31-degree line (smoothed: 5.6 at z 60, 5.1 at 100, 4.1 at 140, 2.5 at 180), never
  closer than 2.0 cm, so round the tip it runs 2 cm from the black line and turns over the nose's top at
  z 205.6 (was 201); eased in over z 55 to 70 (within 0.003 cm of the line at the join). Checked from the
  user's angle, the side, the tip from above, the front quarter and straight on, high along the nose,
  beside the third trial. Shown in the viewer.
- The user, of the fourth trial: "Yes, perfect. and make sure this part has a smooth transition. It's a
  bit jagged" (a view from above of the right side's turn onto the nose). Measured: the turn came in
  two jerks (5 degrees per cm, a pause, again) and the run along the nose's root swayed 2 to 5 degrees
  either way: laid point by point onto the model's big flat faces there (each 8 to 14 degrees steeper
  than the last, z 17 to 37). Redrawn (Look_TopCorner5): from above the straight diagonal, one even
  8 cm turn, a straight run fitted to the line just after it (-13 degrees), easing into the nose by
  z 66; the run smoothed as a curve in space (over 4 cm) instead of laid on face by face, so it floats
  at most 4.3 mm off the skin (1.1 on average) and the paint lands beneath it; its heading eases from
  -13 to -7 degrees and its height falls evenly. Checked from the user's angle, the left from above, high
  front, high side, high behind and low along, beside the fourth trial.
- Built into the guides: "top 1" in car/top_lines.json is the fifth trial's line (both corners, the
  turn onto the nose, the nose at one tilt of the skin, 2 cm from the black line round the tip, ending
  on the nose's middle). TSC_Skeleton repainted; TSC_RescueV2's pinstripe follows it. Self-test: the
  self-test's cars identical. The trials are gone from the work folder.
- The second top line (the user: "Sure", 2026-10-05). Measured first: along the nose the nose panel's
  side seam stands three times the first line's height above the black line (12.4 cm at z 143 against
  3 x 4.1; 9.9 at z 164 against 9.6; 7.0 at z 180 against 7.5), so lines at twice and three times are
  evenly spaced up to the panel's seam. Trial (Look_TopLine2, in the work folder): behind the nose the
  first line set in by 6.3 cm seen from above (the tail, the deck, the sidepods, round their front
  corners, across their fronts; its bends no tighter than 3 cm: 3.1 at the tail's corner, where the
  first's 5.7 would have folded); from z 25 to 45 handing over to twice the first line's height above
  the black line (12 at the cockpit's front, 11.2 at z 60, 8.3 at z 140, 5.0 at z 180), which keeps
  it 4 cm from the black line round the tip and turns it over the nose's top at z 196.5 (the panel's
  front 186.5, the first line's turn 205.6); smoothed in space over the hand-over; within 2.8 mm of
  the skin. Checked from above, the deck and tail high behind, the sidepod's corner, the nose root high
  front, the nose from the side, the tip from the front quarter and above, the cockpit's side, the rear
  three-quarter. Shown in the viewer.
- The user, of the second line: "it somehow feels like every line should end it the tip of the nose
  following the should (the shadow line we talked a while back)? ... maybe all lead to following the
  curved edge (shoulder or whatever its called) ending going around the tip of the nose? Any thoughts,
  would that be more reasonable?" Measured: along the nose the second line already keeps one tilt of
  the skin (42 to 44 degrees from z 40 to 180: the nose's shoulder); only past z 185 it held 4 cm
  above the black line, climbed off the shoulder and crossed the top at z 196.5. Every tilt runs down
  into the black line at the tip, so the lines can follow it there only as loops nested closer than
  along the nose. Recommended: follow the shoulder down, the lines bunching at the tip. Second trial
  (Look_TopLine2b): from z 150 the second line hands over to the shoulder's line (twice the first's own
  shading line, before its floor), never nearer the first than 1.5 cm; it crosses the top at z 199.2.
  Asked in the Lab (question on TSC_Skeleton), both trials open.
- The user: "Dont see the changes" (B against A: under 1% of the picture differs). Third trial
  (Look_TopLine2c): the second line follows the shoulder down and runs into the first line by z 203
  (its gap closing from 1.5 cm at z 190), so the two go round the tip as one; its paint stops at its end.
  Question 9 settled; asked B or C in the Lab (question 10).
- The user: "I meanti as in both lines meeting the black line so they all meet at the nose". Measured:
  the nose's middle stands 7.7 cm above the black line at z 180, 3.4 at z 200, 0.7 at its front (z
  210.8); the first line's shading line already runs at about a third of that near the tip, the
  shoulder (the second line) at about two thirds. Fourth trial (Look_TopLinesMeet), both lines: along
  the nose the first line's shading line (31 degrees) and twice it, as before; from z 185 to 200 handing
  over to a third and two thirds of the nose's own height above the black line, which brings both down
  into the black line at the front of the tip (z 210.7, the middle); the first line no longer keeps
  2 cm off it. Eased in from z 144 (within 0.01 cm of the lines as they were). Checked from the low
  side, the tip close from the front quarter, from above and straight on, the nose high, the front
  three-quarter. Question 10 settled; shown in the Lab.
- The user, of both lines meeting the black line at the tip: "Yes, that's it." Then (a view from above,
  a magenta line from the tail's middle across, turning forward and running straight along the
  cockpit's side to the second line at the nose root): "for the second red line, im actually thinking
  if we actually make it follow the in between curvature of the car. So it still ends in the nose like
  you have it ... similar to the first one when it comes to the front half, but it's more on the cockpit
  starting curvature". Measured: the raised middle (the engine cover, the cockpit's surround) rises off
  the flat top at about 45 degrees; the crease at its foot (the most concave point across, slice by slice)
  runs 36 cm from the middle at z -120, 40 at -85, 43.5 along the cockpit, 41 at z 20, fading into the
  nose's side by z 30; across the back it runs where the engine cover's back slope meets the tail deck
  (z -129.5 in the middle, -127 at 28 cm out), rounding into the side. Fifth trial (Look_TopLineCrease):
  the second line on that crease (smoothed over 3 cm, heights from the skin, the corner about 12 cm),
  handing over at z 15 to 40 to the nose stretch (twice the first line's shading line, two thirds of the
  nose's height at the tip); with the first line meeting the tip. Within 2.2 mm of the skin; 3 cm from
  the first line at the nose root, where both turn. From the side the hand-over climbs 3.5 cm (the
  crease 7 to 8 cm above the black line, the shoulder on the nose 11 to 12). Checked from above, the back
  high behind, along the cockpit, onto the nose, the back corner, the rear three-quarter, the nose root
  from above (both sides), the side and high behind. Shown in the Lab.
- The user, of the crease trial (a view from above, the back corners circled in blue, the nose root in
  green): "the blue circles I drew, those corners should be smooth corner radius. And the drawn green
  cricles, that's where I said the second line should meet with the first line. So that they all run
  through the shoulder of the cars nose", then "if you need to slightly make the first line a bit further
  to reach the cockpit curvature, feel free. So both lines meet perfectly". Measured: the crease along
  the cockpit is nearly straight (43.65 cm out at z 0, drifting in 0.027 cm per cm), and the first line's
  turn onto the nose already lands on it (43.35 against 43.16 at z 18), crossing it at a 9.5 degree
  angle; so the first line stays as it is. Sixth trial (Look_TopLines8): the second line on the crease,
  its back corners one eased turn of 12 cm radius (from the back crease at 8 cm out to the side crease
  at z -75); along the cockpit on the crease's straight line; from z 8 to 24 one bend (no tighter than
  45 cm) into the first line's course, ending on it (0.07 mm) in its direction; its paint stops at its
  end. Ahead of the join only the first line runs on, to the tip. Tried and not kept: the second line
  easing into the first over z 8 to 35 (side by side for 15 cm, a taper); the first line's turn redrawn
  onto the crease (an S after it); a bend ending at z 18 (it bulged out first). Checked from above on both
  sides, high front, high behind, the back corners. Shown in the Lab.
- The user, of the sixth trial: "feels about right". Built into the guides: car/top_lines.json holds
  "top 1" (the first line meeting the top line at the tip) and "top 2" (the second, on the crease,
  ending on the first at the nose root); levels.top_line stops a line that ends away from the middle at
  its end. TSC_Skeleton repainted (its join the trial's exactly), TSC_RescueV2's pinstripe follows the
  first line into the tip. Self-test: the self-test's cars identical. The trials are gone from the work
  folder.
- Step D of the road (2026-10-06, Claude Opus 5.5; the user: "next"): the guides' lines drawn in the flat
  texture. Measured first: the texture's flat layout stretches some facets of the nose and the rear flank
  by a quarter or more, so a line drawn smooth in it comes out less smooth there. Drawn smooth instead in
  the car's own flattening (the facets along each line unfolded exactly; each line within 1.5 mm of
  itself) and painted as a second take: close up at the nose root and the tail it looked the same as
  this car, with one small new notch on the first top line. The corners that show close up there are
  the model's own folds between its big flat faces (the first top line bends 6 to 12 degrees with them at
  the nose root, 1 to 5 along the surface), and any line crossing them bends with them, in the game too.
  Not shown to the user; the take and its code are gone. Open: the user's OK to drop the step.
- Asked in the Lab (question 11) whether to drop step D, retire the line-drawing tool and go on to E. The
  user, in the chat: "Oh wait. I do like the drawing tool, I actually find it very useful. I would
  actually make refinments to the drawing tool rather than removing it". Asked which they meant (the
  lines room's tool was meant): "Oh ok! Yes. That "The lines" tool didn't help at all. You can retire
  that". The drawing tool they like is the Lab's pen; it stays. Step D dropped; the lines room, its pins
  and the line tool behind it retired. Open: the pen's refinements, in the user's words.
- The user, of the levels room: "Even the levels room was meant to define the levels, but I don't even
  know if its actually necessary? My intentions to that tool was to sort of provide guidance for the AI
  to understand how the car kind of flows but I don't want to add more complexity". Recommended keeping
  the guides and retiring the room (question 12). The user: "Yeah, but what's important is that the AI
  doesn't only exclusively use those guides ... what I expect for the AI is to just follow the flow of
  the car. Without needing guides. Like if I ask the AI to build a car, it doesn't need to use one of the
  guides". The levels room retired; the guides (car/levels.json, car/top_lines.json) stay, optional; a
  design follows the car's own flow (RULES.md), and step E reads it from the car's shape.
