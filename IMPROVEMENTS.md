# Improvements to the tool

The one queue of what the tool should do better: each item dated, in two or three lines, what's wrong
and an idea for the fix. The user says when to work on it. A finished item is deleted; what it taught
goes into the code. It mustn't pile up or go stale: the session-start check (`tool/doctor.py`) says
"prune it" past 20 items or when one is older than 30 days; at a pruning each item is kept (re-dated,
still in the user's words), done, or deleted (git keeps it). Things that exist are named in backticks
and checked by the self-test; ideas are named in plain words.

## Next: intent to result

The road of 2026-10-05, in order, each step one commit under the self-test, shown on a car and scored
by `PY -m tool.record` (how many of the user's recorded flaws the tool names first: 6 of 6 today; nine
more it no longer makes).

- **E. Structure for taste, from the mesh** (2026-10-06; the user: "Sure, I can do that ... make sure to change the
  chase camera"). Built, waiting for the user's OK: the lines the tool guessed from the texture's texels are out (the
  traced lines, the shading's divide, the shoulder as a line, the edge guide); a design takes the model's own lines
  (`meshlines.line`, along a rounded edge with `kind="rounded"`, and `meshlines.picked`). TSC_EdgeLine's line is
  on the model's line along the shoulder (up to 0.6 cm further down the roll). The
  anatomy (`car/anatomy.md`) is written from the mesh: its crisp lines, its rounded edges with the lines across each
  (`meshlines.rolls`), its panels (`meshlines.panels`), its picture the Lab's template on the bare body
  (`car/map/model.jpg`); the chase camera is out of it, of show's report and of the skill. Open: the areas
  (`shapes.area`) still split on the car map's traced lines (ask the user first); the underside area's edge notched
  on the tail corners' narrow back faces.
- **Retire the guides; the mesh is the guide** (2026-10-06, the user: "I think we can retire the guides and the mesh
  somehow will be improved, but I guess that would be the new "guides""). First the Rescue car's take (its set 3: A is
  built on the guides; D, the mesh as the guide, is mine). Out then: `tool/levels.py`, `car/levels.json`,
  `car/top_lines.json`, `course.level`, `course.around`, `course.top_line`; the paint report words a height by the guides
  (`measure.py`, levels.where), the seams' heights lean on them (`seams.height`), and the self-test's tour paints with
  them: each moves to the model's own lines or plain words, the tour's paint differing where meant. Built for it:
  `Course.offset`, a line beside one of the model's lines (a band of even width, a tape beside a crease).
- **F. A picture as an entry point** (2026-10-05): a command that reads a picture the user hands over
  into the car's own words (roles per colour, placements against the anatomy, finishes; the structure,
  never the artwork), confirmed as a question in the Lab before any paint.

- **G. The model's lines, the template to design on** (2026-10-06, the user: "Im expecting some sort of blend
  between the mesh of the 3d model and the uv map, so that the ai as the ultimate uv map template to design
  accurately"; "The whole point of all of these things that we've been doing is for you to be able to see better the
  UV map that will translate into the three D model ... For you to actually produce a line on edges, around shapes, on
  curvature, or whatever"; of shading: "The shade is fine if it works for you ... If that helps you map the car's
  curvature indentations, etc"). Built, from the model's triangles alone: `meshlines.template` (creases and panel
  lines, where the body ends, where the map is cut) and `meshlines.mesh` (every edge of its triangles, with how much
  the body bends across it: outward, a rounded edge is a run of them side by side; inward, an indentation), drawn by
  `view.export_template` on the maps and on the car (the Lab's UV map room, Show, Template; the user: "I want to see
  the mesh reflected in the car"); a design picks `meshlines.line` (exactly along a template line) and
  `meshlines.panel` (filled to its lines, or a trim). The Lab's Mesh button lays the mesh over any car, and with it
  Draw picks a line by points where the mesh's lines cross (`meshlines.picked`, one smooth curve through them, the
  user's pick). The user, 2026-10-06: "Its ok, there's improvements to make but for now let's keep it that way until I
  actually start building a car". Next: their improvements, when they start a car. Not: a line from the car map's traced
  lines ("random lines ... no meaning whatsoever"), nor from a light rule alone (the 60-degree divide wandered in a
  zigzag before each inlet); a line on a panel line sits on one wall of its 0.36 cm groove, not its middle.

## The tool

- **The car map differs between the Mac and the PC** (2026-10-05): its readings (the shoulder, the
  lower edge, the ridges, the areas) differ slightly (numpy and BLAS). The guides are committed data
  now; the readings are to be checked against them (`tool/carmap.py`, `car/anatomy.md`). The checks
  (`tool/checks.py`) and a mark's room (`tool/marks.py`, the open air) read the map too and haven't run
  on the PC yet: a mark could land a texel or two apart on the two computers.
- **A mark's `at` seen along an axis** (2026-10-05, the agent's test car): `(x, None, z)` takes the panel's
  nearest texel in x and z, which can be its underside, with no note that it faces away; a shrunk mark
  that fills its room hugs the panel's edges, which no note says; placing a tight mark takes a paint per
  try. Ideas: among the texels in line, the one facing the free axis, and a note when none does; a note
  when a mark takes over 80 % of its room; a probe command for marks, as lines have one.
- **A paint covered by the same paint is said to stop short** (2026-10-06): TSC_RescueV2's black lower
  edge "stops 40 cm short" where the side skirt, painted black by name, covers it. Idea: a later call in
  the same colour and finish leaves no shortfall (`measure._why`).
- **Repaint only the map that changed** (2026-10-05): every `show` paints the whole car (about a
  minute) even when a note touched only the tyres. Idea: repaint that map alone, if the game files stay
  identical.
- **The Lab is empty before a new car's first paint** (2026-10-05): idea: the car in clay with a line
  on the stage until the first paint.
- **Words on the inner car** read backwards on one side (2026-10-05): mirror twins share texels. Idea:
  name the inner parts' unshared areas big enough for a word as spots.
- **Motifs lined up across panels** (2026-10-05): scatter spreads evenly but can't do rows that line
  up. Idea: a regular switch on `Skin.scatter`.
- **Names in the parts list** (2026-10-05): some inner part names are guesses (side vent, side vane,
  nose sensor, airbox: check them the first time a design paints them), and the fasteners have none
  (they wear one tiny strip the list gives to the front wing; TSC_CMYK_EndsInK paints it by hand). The body's own bolt heads are four tiny parts with one paint for
  the whole car, which no zoned paint reaches: gold dots on every shard of TSC_Kintsugi, unasked.
  Renaming touches `tool/naming.py` and the viewer.
- **Worn paint doesn't read as worn** (2026-10-05): `s.wear` scatters by noise, like a pattern. Idea:
  wear driven by the car's shape (edges, recesses, contact points), layered paint, primer, metal, with
  real scanned materials (Poly Haven, ambientCG, CC0) for finishes and wear, fetched as needed.
- **The pictures Claude looks at** (2026-10-05): the comparison picture's number takes 1, 2, 3 on top
  of A, B, C, and drops a fourth view (idea: letters, and a second row); the close looks give the right
  side one tile in ten, so a car that isn't the same on both sides goes half unseen (TSC_Kintsugi).
- **A finer, evenly shaped grain** (2026-10-05, the user, on TSC_CMYK_EndsInK): 2 mm noise specks are
  the smallest that survive the zip budget. Idea: specks per 4x4 block from a few variants, so they
  compress.
- **What the Mac lacks** (2026-10-05): the picture maker (it needs the PC's card; idea: FLUX.2 [klein]
  on Metal, quantised, the latest release looked up first) and two tyre fonts (Bahnschrift, Consolas;
  idea: open look-alikes).
- **The materials and the UV map, in a new way** (2026-10-05): the user's to describe (2026-10-02);
  start from their words.
- **The car map against well-made skins** (2026-10-05, the user's idea): 11 skins the user downloaded
  (2026-10-04; the Mac only, git-ignored). Lay their body textures' sharp colour edges on the car and
  compare them with the guides; fix the map where they agree it's off, in pictures. For checking only:
  they never shape a design. Some use BC5U and BC4U headers, which `dds.read` doesn't take yet.

## The viewer

- **The viewer against the game** (2026-10-05): the game's cameras pull back with speed (fitted
  standing still; fit Cam 1 at a few speeds from the user's videos); the car number's lettering is a
  guess until a close-up of the engine cover; the rear wings and air brakes move at the video's pace,
  their angles set by eye (a short side video would pin them).

## To check in the game

Settled when the user drives a skin that uses it and says or shows what they saw; never ask them.

- **Never seen in the game yet** (2026-10-05): the finishes candy, chrome rims, rust, leather,
  metallic flake, and the viewer's matte, satin, gloss and chrome against the game's; the exhaust heat
  and boost glows (TSC_CMYK_EndsInK carries exhaust heat); whether the wheel covers turn; how
  see-through the glass is (tint only, so far); tyre markings (their relief, legibility, the band
  clearing the covers); a glow on the body (Skin_I in Details_I's format, on a test skin); the upload
  size limit (zips stay under 8.5 MB until one shows up).
