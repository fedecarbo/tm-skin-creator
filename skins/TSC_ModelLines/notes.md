# TSC_ModelLines

The user's words (2026-10-06, Claude Opus 5.5), after every line of the body's traced from the texture and smoothed
got "you are basically scribbling blindly everywhere" and "There's got to be a precise solution to this", then
"There has to be a solution that enhances the way you use the uv map": "My approved edge was an eye estimate, but if
you can convince me about this method, im all in to actually see it in use, ignoring my approved edge and doing it
with the exact lines that the model had all along".

Read as: a test car on clay with two of the car's edges in black, 6 mm, both sides, drawn along the model's own lines
(the edges of its triangles, the UV map's wireframe), from one of the model's points to the next: the shoulder from
the inlet to the tail corner and the sidepod's rear edge (the one that broke into pieces on TSC_AllLines). On a
rounded edge the model has a family of lines across the curve, one every 7 degrees or so (about 8 mm apart); the one
drawn is where the shading is halfway between the two surfaces. The approved edge isn't used.
- Built (2026-10-06): `tool/meshlines.py`. The body's points welded, its edges, the pieces of the model joined across
  the panels' seams (they meet within 0.06 to 1.2 mm; joined up to 2 cm); along a guide, the cheapest path over the
  model's edges where each point's shading strays least from halfway (costed by length), stepping sideways onto the
  next line costing 10 cm, so it keeps to one line; carried on along its own edges to the guide's ends. The shoulder:
  152 cm from the inlet's frame to the tail corner, its shading 0.43 to 0.52 all along, one line on the sidepod, one
  on the rear flank and tail corner, crossing their seam with turns under 5 degrees. The sidepod's rear edge: 54 cm,
  one line. Measured first: every line of the five checked (the approved edge, the sidepod's rear edge, the nose's
  shoulder, the side skirt crease, the sidepod top's rim) runs within 1 to 2 mm of a chain of the model's edges.
- Set 1, two takes: A straight from point to point (exact; a small corner at each point, 4 to 7 degrees, visible
  behind the sidepod), B one smooth stroke on each piece of the UV map through the model's line (bends smoothly).
  Checked close up at the inlet, behind the sidepod, the tail corner and the sidepod's rear edge from behind: both
  continuous on the edges; a small step at the tail corner's seam in both.
- Notes 1 and 2 on B (user, 2026-10-06, the left rear flank): "Why is there a change in elevation of something here?"
  (behind the sidepod) and "Same here.  Why now it starts to go down" (near the tail corner). The path slipped onto
  the next model line up (facing up 0.45 to 0.68, through a diagonal of the curve's thin strips) at z -57 and back
  down at z -109: the level read off the two surfaces is 0.565, about as far from the halfway line (0.44) as from the
  one above (0.68), and a diagonal cost nothing extra. Now changing line costs as a sideways step (by the change of
  shading along an edge, seams included): the shoulder is one model line from z -12 to -154, facing up 0.43 to
  0.52, every step an edge of the model or a seam between coinciding points. Both takes repainted; checked from
  the notes' cameras: no rise, no dip.
- The user, of set 1: "I see not much difference, they both seem accurate, which one is the new method?" Both are:
  the same model line, drawn straight from point to point (A) or as one smooth stroke on the UV map through the same
  points (B). Picked B (no corners at the bends, visible only close up behind the sidepod and at the inlet's end).
- The user, 2026-10-06: "Might have to be with another agent. If this new method works, then Im expecting some sort
  of blend between the mesh of the 3d model and the uv map, so that the ai as the ultimate uv map template to design
  accurately". Open (next session): every edge of the body's along the model's lines on this car (the queue's G),
  checked close up before it's shown; then the template.
- The user, 2026-10-06 (the next session, Claude Opus 5.5): "By the way, I don't know where 18 lines come from.  But im
  interested to know if with this new mesh to uv map method will help enhance the uv map so that ai can "see" the
  geometry of the car.  I want to see it in the uv map template room as well, to check if it actually works". The
  template first, in the Lab's UV map room (Show, Template): on all four maps the body's shape shaded, the model's
  triangles, and its lines read off the triangles (creases and panel lines, where the body ends, where the map is cut
  while the car carries on); the car dressed in the same. Checked on the car from the room's camera: the panel lines
  round the cockpit, the nose plate, the engine cover and the number panel, the inlets, the fasteners' holes, all on
  the car's own. The rolled edges aren't in it: found as a shading isoline over every roll at once they broke, wobbled
  on gentle curves and looped where rolls meet. Open: the rolled edges, one at a time, as the shoulder was drawn.
- The user, 2026-10-06, of painting along the template's lines or the rolled edges first: "You choose, because this
  tool is really for you to paint accurately.  If you need to run a test feel free". Chosen: the template's lines and
  panels first (exact already, and they bound the model's own panels). A second step on this car: the cockpit
  surround filled red right up to its panel line with a black line 0.6 cm on the line itself, the nose panel blue, a
  black trim 1.5 cm inside each inlet's edge. Checked close up (the cockpit's front, side and back corner, both
  inlets, the nose panel): every fill meets its line with no gap and nothing over it, the fasteners' holes left clear,
  the trims on both sides. Measured on the texture: the black line is 0.3 cm each side of the panel line; the panel
  line is a groove 0.36 cm wide and the line sits on its inner wall, so it covers all but the groove's last half
  millimetre on the body shell's side. Shown in the Lab.
- Note 1 (user, 2026-10-06, the left sidepod's rear edge): "Where is this line coming from, I've seen it before and
  its wrong". It was the sidepod's rear edge from set 1, the model's line where the shading is halfway along the car
  map's traced line: 1.5 cm in from the sidepod panel's own edge (the template's crisp line where the panel turns
  under). Redrawn on that edge (`meshlines.line`, up the panel's back and along its foot), both sides; checked from
  the note's camera and close up on both sides: on the edge all along.
- The user, 2026-10-06, of the light-divide line and the shoulder line: "The whole point of all of these things that
  we've been doing is for you to be able to see better the UV map that will translate into the three D model. And you
  keep just creating random lines like the one that I flagged ... Either your using other methodologies, you are getting
  inspired or contaminated by other modules, or the new mesh UV map is just not working. For you to actually produce a
  line on edges, around shapes, on curvature, or whatever." Then: "Stop with the light and the shading", and: "The shade
  is fine if it works for you.  That's what im saying.  If that helps you map the car's curvature indentations, etc".
  The shoulder line (the shading rule along the car map's traced shoulder) is gone, with the method that drew it; the
  car shows only the template's lines and panels. A line where the light divides top from side all round was tried:
  clean along the nose, the sidepods, the rear flanks and the tail corners, but a zigzag before each inlet, so it isn't
  used. Built instead: the body's curvature from the mesh (`meshlines.curvature`), tinted in the template (orange
  outward, violet inward). Open (next session): the user looks at the curvature tint in the UV room; then lines on
  curvature from it, checked close up.
- The user, 2026-10-06 (the next session, Claude Opus 5.5), asked whether projecting the mesh onto the car would help:
  "I want to see the mesh reflected in the car". The template's car showed the triangles too faint to see, under a
  curvature tint over most of the body. Now the template draws the mesh itself (`meshlines.mesh`): every edge of the
  model's triangles in dark grey on plain clay, an edge the body bends across turning orange (outward) or violet
  (inward) the more it bends (full at 12 degrees), so each rounded edge shows as its bundle of the model's own lines;
  the crisp lines, openings and cuts on top as before. The tint is gone. Checked close up on the car (bonnet, nose,
  flanks, sidepod, deck and tail, wheel) and on the maps. Open: the user looks at it in the UV room (Show, Template,
  Car); then lines on curvature from a rounded edge's own lines.
- The Mesh button (any car in the Lab) and picking a line on it by clicks (Draw with Mesh on), the user's idea: "There's
  something about having them that might be also somehow useful to click on certain multiple points similar to the draw
  tool". Note 2 (user, 2026-10-06, "Got this glitch"; in the chat: "I clicked a third point and the line just went all
  crazy"): a click at a line's very end jumped to its start, a metre up the nose; fixed. Note 3 ("test"), then in the
  chat: "It just looks like sloppy work.  I just did a line and the outline is so wobbly a glitchy" and "I thought we
  were going to just have the points when two or more lines cross, that creates a point": each click lands on the
  nearest of the model's points now, marked with a small cross. Their clicks were already on its points: the wobble
  was the model's own edges, a small corner at each point and a sharp bend over the sidepod's back edge. Closed
  (question 4 in the Lab, their line from above both ways): B, "Smooth through the points", over A, straight from
  point to point. A picked line is one smooth curve through its points now, in the Lab and in paint.
- Note 4 (user, 2026-10-06, a line picked on the left rear flank, 8 points along one of its rounded edge's lines): "Draw
  a red tape here". Read as: a red tape 2 cm wide, the cockpit surround's red, exactly along the picked line
  (`meshlines.picked`, straight from point to point, as they saw it), both sides like the rest of the car. Checked close
  up from the note's camera, along it and from above, mesh off and on: crisp, even, on the line they picked; the
  checks name nothing. Shown in the Lab.
- The tape repainted smooth through the same points (the pick, B): along one of the flank's own lines its corners were
  a few degrees, so it moved under a millimetre; checked close up again, crisp and on the line.
- Note 6 (user, 2026-10-06, a line picked from the hollow behind the left front wheel's opening up to the bonnet's edge
  and forward along it, 6 points): "lets try this". Read as: the same red tape along it, both sides. Its turn at the
  bonnet's edge is 40 degrees, kept as a corner (as the Lab drew it); the rest smooth through the points. Checked close
  up from the note's camera, at the turn and on the right: even, a clean bend, on the line; the checks name nothing.
