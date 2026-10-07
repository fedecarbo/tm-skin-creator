# Improvements to the tool

The one queue of what the tool should do better: each item dated, in two or three lines, what's wrong
and an idea for the fix. The user says when to work on it. A finished item is deleted; what it taught
goes into the code. It mustn't pile up or go stale: the session-start check (`tool/doctor.py`) says
"prune it" past 20 items or when one is older than 30 days; at a pruning each item is kept (re-dated,
still in the user's words), done, or deleted (git keeps it). Things that exist are named in backticks
and checked by the self-test; ideas are named in plain words.

## Next: intent to result

The road of 2026-10-05, in order, each step one commit under the self-test, shown on a car and scored
by `PY -m tool.record` (how many of the user's recorded flaws the tool names first: 5 of 5 today; 40 more
can't be painted again, the tool fixed or retired what made them).

- **H. Lines that hold, on any car: first** (2026-10-07, the user, stopping TSC_StealthBomber: "Dude, what's so hard to
  follow the actual mesh you have as a guide ... It's obviously broken"; "Look at all these gaps. Mediocre"; "Is the
  tool broken?"; then "This tool needs to be optimised, it cannot randomly make mistakes"; "If rules don't work, then
  let's find another approach, if you rushed, then let's find a fix to that, either the workflow, the workload,
  anything"). Measured: a band along a line keeps only the skin facing within 60 degrees of the line's own facing at
  its nearest point, and on an edge that facing flips (the skirt's lower-edge tape: 20 flips over 30 degrees, up to
  138, straight down to outward), so the band hops between the side and the underside: the gaps; `meshlines.picked`
  smooths through the clicks and leaves the mesh where the model's short lines meet: the steps; `tool.skin show`'s
  checks named nothing all along, and no close look ran along a line. To build, one at a time, each shown on that
  car's tapes (its notes 1 to 9 are the test: every tape whole, even and on the face the user sees):
  1. A tape on one face of an edge, the face chosen by the mesh's own faces beside the edge, never by a direction.
     Built, waiting for the user's OK (2026-10-07): `Course.tape`, measured across the surface from the line through
     the map's texels, never across the line; shown on that car's tapes (its nose's kink at the seam is step 2's).
  2. One continuous line along the mesh's own edges end to end, never smoothed off the surface; a join that would
     leave the mesh is refused, not drawn.
  3. A line check: every marking along a line whole, even in width and without kinks from end to end: a failure
     that stops the work, not a note.
  4. Close looks that travel along every line a design draws, square to its visible face, with every paint.
  5. Gates instead of rules: `tool.notes done`, `tool.sets open` and the start of a pass refuse while a line check
     fails or a change has no fresh close looks, and the Stop hook (`tool/guard.py`) holds a turn that would end on
     such a car. A rule in RULES.md that a gate now enforces goes: a rule the work can break under pressure becomes a
     gate.
  6. The workload: one change, its close looks, then the reply; a pass of the routine starts only on a base the user
     has OK'd up close with no notes open; a long stage in a session of its own.

- **F. A visual language for an idea** (2026-10-07, the user: "one of the most important things before even
  designing a car is to develop sort of a visual language first, kind of like a brand book ... it shouldn't really
  indicate all the details on where to put what and how"; the car designed as a whole, not "as individual parts with
  added details"; "I'm okay if there's a level of process or steps"; "some kind of template that can be reused but
  ... the template should somehow give the freedom to explore the concept"). Built: the routine, the language then
  the car in passes (`.claude/skills/skin/language.md`), and each car's page (`PY -m tool.language <name>`, the
  layout the user picked: A, the brand book). Waiting for the user's words for a new car: its language page shown
  for their OK, then the passes on it.

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
  actually start building a car"; "the mesh somehow will be improved". Next: their improvements, when they
  start a car. Not: a line from a light rule alone (the
  60-degree divide wandered in a zigzag before each inlet); a line on a panel line sits on one wall of its 0.36 cm
  groove, not its middle.

## The tool

- **The open air may differ between the Mac and the PC** (2026-10-05): the car map's open air (`tool/carmap.py`)
  is worked out on each computer (numpy and BLAS); the checks (`tool/checks.py`) and a mark's room
  (`tool/marks.py`) read it and haven't run on the PC yet: a mark could land a texel or two apart there.
- **A mark's `at` seen along an axis** (2026-10-05, the agent's test car): `(x, None, z)` takes the panel's
  nearest texel in x and z, which can be its underside, with no note that it faces away; a shrunk mark
  that fills its room hugs the panel's edges, which no note says; placing a tight mark takes a paint per
  try. Ideas: among the texels in line, the one facing the free axis, and a note when none does; a note
  when a mark takes over 80 % of its room; a probe command for marks, as lines have one.
- **A paint covered by the same paint is said to stop short** (2026-10-06): TSC_RescueV2's black lower
  edge "stops 40 cm short" where the side skirt, painted black by name, covers it. Idea: a later call in
  the same colour and finish leaves no shortfall (`measure._why`).
- **A tick cut short by the body's edge goes unnamed** (2026-10-07): TSC_CrashTest's ruler, rising from the
  sill's line, ran into the inlet's frame about 1 cm up and showed as stubs; the checks named nothing, the close
  look found it. Idea: the checks name a tick or dash that loses most of its length to an edge.
- **The eye on the PC** (2026-10-07, the user, of the eye after its test car: "it's not perfect eye test, but Im ok
  with just moving on for now"): `eye.look` and `tool.snap --eye` have only run on the Mac. It's wordy on a ragged
  edge (the old Ladybird's grass: each blade's tip JUST PAST a line); idea: a ragged edge's flags said once.
- **A mirrored tape's carried-on end differs by side** (2026-10-07): TSC_CrashTest's nose tape (`Course.extended`,
  mirrored) runs within half a centimetre of its mirror on the other side up to z 148, then 1 to 1.6 cm apart over
  its last 8 cm on the nose tip. Idea: find whether the body or the zone isn't mirrored there.
- **Repaint only the map that changed** (2026-10-05): every `show` paints the whole car (about a
  minute) even when a note touched only the tyres. Idea: repaint that map alone, if the game files stay
  identical.
- **The Lab is empty before a new car's first paint** (2026-10-05): idea: the car in clay with a line
  on the stage until the first paint.
- **Names in the parts list** (2026-10-05): some inner part names are guesses (side vent, side vane,
  airbox: check them the first time a design paints them; 2026-10-07: the "antenna" is the probe under the nose,
  the "nose sensor" is hidden inside it, the "sidepod grille" is the backing of the visible "sidepod grille plate"), and the fasteners have none
  (they wear one tiny strip the list gives to the front wing; TSC_CMYK_EndsInK paints it by hand). The body's own bolt heads are four tiny parts with one paint for
  the whole car, which no zoned paint reaches: gold dots on every shard of TSC_Kintsugi, unasked.
  Renaming touches `tool/naming.py` and the viewer.
- **The pictures Claude looks at** (2026-10-05): the comparison picture's number takes 1, 2, 3 on top
  of A, B, C, and drops a fourth view (idea: letters, and a second row); the close looks give the right
  side one tile in ten, so a car that isn't the same on both sides goes half unseen (TSC_Kintsugi).
- **What the Mac lacks** (2026-10-05): the picture maker (it needs the PC's card; idea: FLUX.2 [klein]
  on Metal, quantised, the latest release looked up first) and two tyre fonts (Bahnschrift, Consolas;
  idea: open look-alikes).
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
