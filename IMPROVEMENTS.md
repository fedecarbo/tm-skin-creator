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

- **E. Structure for taste** (2026-10-06): built, waiting for the user's OK. `car/anatomy.md`, written
  by `PY -m tool.carmap --describe` from the car's own shape and read before every design: the body's
  lines (its creases and rolled edges, each with the corners where it turns, drawn in `car/map/flow.jpg`;
  `course.flow` lays a marking along one), its flat rooms, what the chase cameras see, where a graphic
  stops. The map's numbers moved to `car/map/tables.md`. `tool.sets open` says when a take is another
  repainted. `SPOTS` stay as set: measured, the side, sidepod and deck spots lie within 10 cm of their
  panels' biggest flat room, and a word moves to room anyway; regenerating them would move TSC_Snow's
  RESCUE for nothing. Its worth shows on the user's next car.
- **F. A picture as an entry point** (2026-10-05): a command that reads a picture the user hands over
  into the car's own words (roles per colour, placements against the anatomy, finishes; the structure,
  never the artwork), confirmed as a question in the Lab before any paint.

## The tool

- **The edge the tool reads wobbles** (2026-10-06, the user on TSC_EdgeLine: "those lines are so
  wobbly"): the shoulder is the crest of where the surface bends most, which drifts about a centimetre
  against where the shading turns. `course.shadow` follows the shading (60 degrees from up, measured
  on the user's own stroke) and `Course.inked` draws a strip smooth on the flat texture; the user:
  "better". Open: the areas (`shapes.area`) split along it, drawn the same way, for TSC_Endurance.
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
