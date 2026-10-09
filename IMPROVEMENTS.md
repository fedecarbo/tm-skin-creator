# Improvements to the tool

The one queue of what the tool should do better: each item dated, in two or three lines, what's wrong
and an idea for the fix. The user says when to work on it. A finished item is deleted; what it taught
goes into the code. It mustn't pile up or go stale: the session-start check (`tool/doctor.py`) says
"prune it" past 20 items or when one is older than 30 days; at a pruning each item is kept (re-dated,
still in the user's words), done, or deleted (git keeps it). Things that exist are named in backticks
and checked by the self-test; ideas are named in plain words.

## Next: the road

The research's order of work (`reports/Skin tool state of the art 2026.md`: its last table, the why and the
sources), one step per session (the user, 2026-10-07: "I will do the plan a session each"). A session does the
first step below and nothing past it:
- build it under the self-test, and show its worth: on a new test car made for it when it changes what a car looks
  like, never a past car (the user: "for any test to actually use new skins that could be scraped after ... unless
  it's really necessary"); in plain words and numbers when it doesn't;
- on the user's OK, remove everything it retires (the user: "I really want to make sure things that are deprecated
  to be removed"): the code, its mentions in the instructions and docstrings, its caches in the work folder, the
  test car; `git grep` finds none of the retired names;
- delete the step here (git keeps it), commit, push. A session that ends before the OK leaves its step marked
  "built, waiting for the user's OK" for the next one.

Each step names its model and effort (the user, 2026-10-07: "I don't mind using opus 5.5 or fable 5.1"): Fable 5.1
where the geometry or the design is hard and a wrong turn costs most, Opus 5.5 where the work is well bounded; xhigh
where the step reshapes what everything else stands on. Fable 5.1 sometimes reaches its limit (the user): a step
marked MUST waits for it, and a session on one that hits the limit stops at a clean point (what's done committed, the
step saying where it stands) rather than going on with another model; any other Fable step may run on its "or". The user sets them as the session starts (typing "/model fable"
or "/model opus", then "/effort xhigh" or "/effort high"); a session
running on other settings than its step's says so before it starts.

The self-test's own cars (the tour, the planted-flaw pair) are the tool's: painted by the self-test, never shown in
the Lab. The PC is away until November or December 2026 (the user, 2026-10-07): until then every step runs on the Mac, its PC
parts (step 6's run there, step 8's gate in `tool.skin install`, the PC's profile, and its graphics chip if the profile points there) wait for its return, and step 13 comes after
it.

- **Every graphic on the car's surface** (2026-10-07, the user, stopping TSC_StealthBomber: "This tool needs to be
  optimised, it cannot randomly make mistakes"; "it's really not about the tape ... anything like putting a line on an
  edge or anywhere"; "Not an external tool please ... let's stick with optimisation"). Measured: graphics are placed
  near the body, not on it (a band kept skin facing within 60 degrees of its line's facing, which flips on a rolled
  edge: gaps, until step 3; a picked line is smoothed in space and pushed back: steps), and no check measured a
  graphic where it landed. The steps:
  11. **Wear where real cars wear** (Opus 5.5, high). Curvature, occlusion and thickness baked once per car on the repaired surface
      (libigl); wear and dirt driven by them; anti-aliased part edges. Retires wear's direction, height and sun
      rules.
  12. **A narrower paint box** (Fable 5.1, xhigh; or Opus 5.5, xhigh). One verb per intent, line ids and part names as typed values that answer "did you
      mean", a short receipt from every verb, `Skin.text`, `Skin.placard`, `Skin.emboss` and `Skin.decal` merged;
      duplicate-code and error-hiding tripwires in the self-test. Retires every private way of placing things the
      foundation replaced, and the merged verbs.
  13. **Yardsticks, on the PC** (Opus 5.5, high). The game files encoded once by quicktex and texconv against the tool's own
      encoder; the viewer fitted per mood to the user's F12 screenshots (FLIP: exposure, environment strength, tone
      mapper, clearcoat), and from their videos the cameras pulling back with speed, the car number's lettering, the
      rear wings' and air brakes' angles. Retires nothing unless another encoder wins.

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
  Draw picks a line by points where the mesh's lines cross (`meshlines.picked`: along the model's lines where both
  points are on one, else the straightest way along the surface, as it is). The user, 2026-10-06: "Its ok, there's improvements to make but for now let's keep it that way until I
  actually start building a car"; "the mesh somehow will be improved". Next: their improvements, when they
  start a car. Not: a line from a light rule alone (the
  60-degree divide wandered in a zigzag before each inlet); a line on a panel line sits on one wall of its 0.36 cm
  groove, not its middle.

## The tool

- **The scatter's charts are the paint's slowest part** (2026-10-09, step 10's profile): 18 of the tour's 82 s under the
  profiler, five exact solves a copy on the processor (`surface.Surface.chart`), and the marks' sheet 5 s more in
  np.unique. Idea: a chart's five solves on the processor's cores at once; profile the sheet's bookkeeping.
- **Decals chipped where a crisp line crosses them** (2026-10-08, the user, giving step 5 its OK: "certain decals where
  chipped or slightly clipped"; their note on the test car's badge across the rear shoulder: "This decal looks chipped
  off on one part of the circle"): a notch about half a centimetre wide in the ring where a crisp line crosses it, left
  by `surface.Surface.chart`'s step spanning or its bridging at the sidepod top's hairline; find which on a chart of that
  spot (the test car TSC_DecalsTest is in git at 3fac0d5). Step 6's judge names a decal not whole; a 5 cm disc on the
  body across=True near z -84 (TSC_CloseTest, in git at 6ec0595) has a 0.6 cm² notch on both sides that only the close looks name.
- **A mark on both sides fitted on each alone** (2026-10-08, found by the close looks): the planted-flaw pair's clean car
  lays its deck picture (one call, both sides) with 7,505 texels on the left and 2,947 on the right, shrunk to fit on
  one side only; nothing else says so. Idea: fit it once, for both sides, and say what kept it small.
- **The open air may differ between the Mac and the PC** (2026-10-05): the car map's open air (`tool/carmap.py`)
  is worked out on each computer (numpy and BLAS); the judge (`tool/judge.py`) and a mark's room
  (`tool/marks.py`) read it and haven't run on the PC yet: a mark could land a texel or two apart there.
- **The Lab is empty before a new car's first paint** (2026-10-05): idea: the car in clay with a line
  on the stage until the first paint.
- **Names in the parts list** (2026-10-05): some inner part names are guesses (side vent, side vane,
  airbox: check them the first time a design paints them; 2026-10-07: the "antenna" is the probe under the nose,
  the "nose sensor" is hidden inside it, the "sidepod grille" is the backing of the visible "sidepod grille plate"), and the fasteners have none
  (they wear one tiny strip the list gives to the front wing; TSC_CMYK_EndsInK paints it by hand). The body's own bolt heads are four tiny parts with one paint for
  the whole car, which no zoned paint reaches: gold dots on every shard of TSC_Kintsugi, unasked.
  Renaming touches `tool/naming.py` and the viewer.
- **What the Mac lacks** (2026-10-05): the picture maker (it needs the PC's card; idea: FLUX.2 [klein]
  on Metal, quantised, the latest release looked up first) and two tyre fonts (Bahnschrift, Consolas;
  idea: open look-alikes).

## To check in the game

Settled when the user drives a skin that uses it and says or shows what they saw; never ask them.

- **Never seen in the game yet** (2026-10-05): the finishes candy, chrome rims, rust, leather,
  metallic flake, and the viewer's matte, satin, gloss and chrome against the game's; the exhaust heat
  and boost glows (TSC_CMYK_EndsInK carries exhaust heat); whether the wheel covers turn; how
  see-through the glass is (tint only, so far); tyre markings (their relief, legibility, the band
  clearing the covers); a glow on the body (Skin_I in Details_I's format, on a test skin); the upload
  size limit (zips stay under 8.5 MB until one shows up).
