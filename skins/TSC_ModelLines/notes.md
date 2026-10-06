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
