# Improvements to the tool

The queue of things the tool should do better. Newest at the bottom of each group. The `skin`
skill says how it's kept: during a skin, Claude fixes only what that skin needs and adds
anything else here. The user says when to work on the list. A finished item is deleted
from here, and what it taught goes under "Things we learned" in `CHECKLIST.md`.

Each item: what's wrong or missing, when and where it showed up, and an idea for the fix. A
bigger item keeps its working notes under "Improvements after the build" in `CHECKLIST.md`.

## Under way

- **Defining the parts: next, before anything else** (the user, 2026-09-26: "I think we need to
  define parts first. Can this be my next task to do before anything else?"). The user leads it,
  and may do it with another agent. What "define" covers is theirs to say: start from their
  thoughts, not from a plan of Claude's. Step by step, each agreed before it's built; the steps
  are in `CHECKLIST.md`, "Defining the parts". Done (2026-09-26): the groups on top are the
  game's maps (Body, Details, Tyres, Glass), after a day of groups by what parts are, which the
  user found over-engineered; the paint box names every part a colour also lands on; the tail's
  frame left the floor ("tail frame"); "floor edge" and "wing mounts" are parts; the Lab's UV map
  picks surfaces. Next:
  the user goes through each group's insides, and may split them. What the tool has:
  `car/parts.json`, 210 parts under 88 names in 13 assemblies in the 5 groups, made from
  `tool/naming.py` (`PY -m tool.parts`); the viewer's Parts list and the Lab's UV map tabs show
  them. Known gaps, below under "The tool": some inner names are guesses, words on the inner car.
- **The design studio, as a wizard in the Lab** (the user, 2026-09-28: "What's important is to
  actually have this as an incredible workflow that builds cars (not the typical amateur skins) but
  actually work on every single detail from start to finish"; the plan agreed the same day: "Lets
  just go with that, and see how it goes"). Three ways in: Quick (as today), the Studio, and
  Rework for a car that exists. The Studio's steps run from the brief to the release, and the
  user decides wherever there's more than one real direction. Each step has its expert's
  know-how, and an independent critic reviews the car. In the Lab it's a wizard: the build sheet
  on the left, the step waiting for the user filling the page. It takes over the Lab's remaining
  steps 9.3 to 9.6 (answers with a before and after, options on the car, Claude's checks, the
  game's screenshots). The Lab as built (the stand, its notes, the stations and their tries) stays;
  its step 9.7 is under "The tool" below. Four steps, each shown to the user before the next: W1
  the studio routine and the build sheet, W2 the experts, W3 the wizard in the Lab, W4 the test of
  Studio against Quick. Notes: `CHECKLIST.md`, "The design studio". Next: W1, piece by piece.

## The tool

- **Words on the inner car** (2026-09-25, TSC_CMYK_BlackTail): `Skin.emboss` raises lettering,
  but most inner parts share their texels with their mirror twin (74 to 99 %), so a word reads
  backwards on one side. Only marks that read the same both ways work there (the registration
  marks). Idea: list the inner parts' unshared areas big enough for a word (the tail frame's
  centre, the floor's centre plank?) and name them as spots, like `SPOTS` on the body.
- **Motifs lined up across panels** (2026-09-24, checkpoint 6). The tool can spread pictures or
  dots evenly, but not in rows that line up from panel to panel, like a regular grid. Idea: a
  `regular` switch on `Skin.scatter`, using `looks.surface_points(regular=True)`.
- **Some inner part names are guesses** (2026-09-24, checkpoint 3): side vent, side vane, nose
  sensor, airbox. Check them the first time a design paints them. Known since the air brakes
  (2026-09-25): "nose sensor" is the nose panel's lifting arms, "rear damper" the rear quarter
  panel's arm, and "airbox" the opening under each quarter panel. Known since the turning
  wheels (2026-09-25): "brake caliper" is the split ring at each wheel's centre (5 to 7 cm from
  the axle, on the outer face, under the cover's hub), and "hub" the fixed fairing inside the
  wheel, with the brake light in its slot. Renaming them means updating
  `tool/naming.py`, `skins/TSC_Stealth_CMYK/design.py`, `tool/partskin.py` and `AIRBRAKES` in
  the viewer.

- **Worn paint that reads as worn** (2026-09-26, TSC_FlagPeel_CostaRica's worn takes: "none gets
  me to think it's worn"; the Costa Rica skins were deleted on 2026-09-27, they're in the git history). `s.wear` scatters chips, scrapes and fading by noise, so they sit on
  the car like a pattern, not like damage. Real wear follows the car: paint rubbed through on
  the sharp edges and creases (convex curvature from the bake), round panel gaps and fasteners,
  where hands and walls touch; grime settles in the recesses and streaks back from the
  openings; scratches catch the light. Idea: drive the wear by the car's own shape (edges,
  recesses, contact points) and layer it (paint, primer, metal at the deepest), then test it on
  a plain one-colour car before a livery.

- **A step that covers an earlier step's paint says nothing** (2026-09-26, TSC_ChaosElegance_
  Kintsugi, deleted 2026-09-27: a borrowed inner-car helper painted the body black over the
  porcelain and gold). The
  Studio's filmstrip shows it, but only if someone looks. Idea: at the end of each step, note any
  part an earlier step painted that this step covered for the most part ("Inner car covered
  Porcelain, Mended with gold on the body shell"), as `show` notes shared paint.
- **The comparison picture's labels and views** (2026-09-26, the concept round): it numbers the
  takes 1, 2, 3 on top of Claude's A, B, C ("1 A Kintsugi"), and a fourth view asked for is left
  out without a word (the sheet is three tiles wide). Idea: letter the takes as the Lab's round
  does, and wrap extra views to a second row.

- **The fasteners have no name** (2026-09-27, TSC_CMYK_EndsInK: the user saw small cyan rings on
  the black). The little rings on the cockpit, engine cover, nose and front wing all wear one tiny
  strip of the Details map (texels 2248-2251, 2566-2607 at 4096), which the parts list counts as
  the front wing's, so they take the front wing's paint wherever they sit, and "paint also lands
  on" never says so (they're a handful of texels). The skin paints the strip by hand
  (`fasteners()` in TSC_CMYK_BlackTail's design). Idea, with the user's parts work: name them
  ("fasteners") so any design can paint them.
- **Saving the user's picture while it's open on their screen fails on Windows** (2026-09-27):
  `tool.snap --picture` stopped with "Invalid argument" while the last picture was still open;
  it worked when run again. Idea: retry the save a few times, a moment apart, as `view._write_json`
  now does for the Studio's files.
- **A finer, evenly shaped grain** (2026-09-27, TSC_CMYK_EndsInK, the user after driving it:
  "Maybe I couldve wanted a bit more finer evenly shaped grain, but looks fine to me, maybe for
  next session?"). The textured wrap (WT-07) makes its specks from noise, so they come in mixed
  shapes, and 2 mm is the smallest that holds: once the body's sheen map fills with grain, the
  zip's budget halves it to 2048² (0.18 cm texels). Finer (1 to 1.5 mm) and even (round specks of
  one size, evenly spread) needs that map at full size. Idea: draw the specks in texel space,
  one per 4x4 block from a handful of variants, so the compressed blocks repeat and zip squeezes
  them (a guess: 1.5 to 2 MB at 4096², the zip about 8.1 MB); if that's still too big, free room
  elsewhere (the suspension's blasted grain in Details_R). Check the zip first, then the game.

- **A tidy-up, from a code check** (2026-09-27, the user: "it's been forever I have refactored, so
  not sure if things need to be optimised a bit more?"). The code is in fair shape; no big
  rewrite. The two the user would feel are done (2026-09-27: a show about 35 s faster, the UV
  map's data rebuilt only when it changes; "Things we learned"). Left, most useful first:
  1. The test-skin scripts from before the paint box (`testskin.py`, `partskin.py`, `labskin.py`,
     `carbonskin.py`, 774 lines; `partskin.py` holds a copy of ~70 part names). Move `stock()`
     from `testskin` to `dds.py` first (`paintbox.py` imports it), then retire them.
  2. About 100 lines nothing calls: `dds.fix_bc1`, `pictures.mend_seams` and `art_path`,
     `noise.worley2`, `parts._tub`, `paths.VENV`, the viewer's `aim()` and `partCentres()`.
  3. Stale defaults and docs: `tool.view <name>` and plain `tool.snap <name>` read the last
     installed DDS files (old paint, or none); the viewer's bare address opens TSC_Test, which has
     no design; `paintbox.py`'s docstring names `Skin.show/build/install`, which don't exist.
  4. Designs that load another design (9 of them, chains up to 5 deep) copy the same importlib
     lines, and the Mac's container repaints a skin only when its own design changed, not one it
     borrows from. One `borrow()` helper, and `serve.py`'s `stale()` following it.
  5. The Docker image installs Playwright only because `skin.py` imports `snap.py` at the top: a
     lazy import drops it.
  6. The work folder keeps a coverage cache per `parts.json` version (0.8 GB on the Mac) and a
     250 to 285 MB `painted.npz` per skin in `build/`: prune the old coverage keys.

- **Repainting only the station that changed** (2026-09-27, the Lab's step 9.7, queued here when
  the design studio took over the Lab on 2026-09-28). Every `show` paints the whole car (90 to
  127 s for TSC_CMYK_EndsInK), even when a note changed only the tyres. Each station is one of the
  game's maps, so a change to one could repaint that map only. Only if the game files come out
  identical to a whole repaint. It makes every studio step faster. Notes: `CHECKLIST.md`, The Lab,
  step 9.

## The viewer, from the user's screenshots and videos

- **The game's cameras at speed** (2026-09-25, the user). Cam 1 and 2 and their alts are fitted
  to the user's screenshots standing still (Things we learned, "the game's lens" and "fitting a
  game camera"). In the game they
  pull back and lower as the speed rises and close in again when the car slows (the
  straight-line video; the lights test's and turbo videos show Cam 1 through whole runs, up to
  about 440 km/h). Idea: fit Cam 1 at a few speeds from those videos' frames the same way (the
  tyres and the horizon), ask for a short run in Cam 2 and the alts, and let the viewer slide
  between the poses with the pad's speed. `tool/snap.py`'s close look 9 ("driving camera") is
  still an older, narrower view.
- **The car number's lettering is a guess** (2026-09-25) until a close-up of the engine cover.
  The lights test's videos have one ("CAR 00", day at 13.2 s, night at 10.8 s).
- **The rear wings and air brakes, fine-tuning** (2026-09-25): the viewer opens both wings (up
  or down, then apart) at the video's pace, and raises the air brakes (rear quarter panels,
  nose panel, with their arms) while braking. How far the wings move, the air brakes' angles
  and how quick they are were set by eye. A short video from the side (pull away, brake hard,
  let go) would pin them. Notes under the lights improvement in `CHECKLIST.md`.
- **The page online, sharper on big screens** (2026-09-25, `tool/publish.py`): it carries
  2048² paint so a phone can hold it, so on a computer, close up, it's softer than the viewer
  here. Idea: publish the 4096² colour maps too and let the viewer take them when the screen
  is large and `renderer.capabilities.maxTextureSize` allows.
- **The page online, a lighter first visit** (2026-09-25): about 20 MB before the car shows
  (the car's shape 11 MB, the studio lighting 6 MB), slow on mobile data. Idea: the mesh in
  half floats or meshopt-compressed, and the 1K studio HDR on phones.
- **A phone on its side** (2026-09-27, the smaller-screens work): 400 px high, the name, the speed
  and the buttons leave the car about a third of the height, so the car is framed in the whole
  window and the speed and pedals sit over it. Idea: under about 500 px high, a smaller one-line
  name without the tag, and the speed beside the pedals.
- **The game's cameras on a phone** (2026-09-27): Cam 1 and Cam 2 keep the game's 16:9 picture,
  shrunk to the phone's width, so the car is small in the middle of the screen. Idea: on a tall
  screen frame the game's picture by its height and let its sides go, as the other views come closer.

## To check in the game

These need the user to drive or look, so they're tested when a skin uses them.

- **Finishes never seen in the game** (2026-09-24, checkpoint 5): candy, chrome rims, rust,
  leather, metallic flake.
- **Glows never seen to light up** (2026-09-24, checkpoint 4): exhaust heat and boost (brake
  heat and turbo lit in the lights test, 2026-09-25). TSC_CMYK_BlackTail and TSC_CMYK_EndsInK
  (2026-09-25) carry exhaust heat where the chase cameras see it: inside the tail's two openings
  (orange) and in place of every stock turbo glow (magenta inside the wheels): whichever is
  installed, a turbo pad settles it. The viewer lights it with its Turbo button, a guess.
  Still to see: a reactor boost, a red turbo pad (red, as the pad?), and whether the sidepod
  frames light with the turbo like the hubs.
- **Whether the wheel covers turn** (2026-09-25): the viewer turns them with the tyres and
  rims; the tyres are known to turn (the tyre line in the game), the covers are assumed to. A
  skin with a pattern on the covers, driven slowly past the camera, would show it.
- **How see-through the glass is** (2026-09-24, checkpoint 4): the glass file's alpha made no
  visible difference, so the tool treats glass as tint only.
- **The Lab's finishes in the game** (2026-09-27): TSC_Lab_Materials, made for this, isn't
  installed yet. Its finishes by day and at night would check the viewer's matte, satin, gloss
  and chrome against the game (the calibration car matched only the light and the glows).
- **Tyre markings** (2026-09-27, the library, `tool/tyres.py`): never in the game yet. The first
  skin with one shows whether the game takes the tyres' own relief (`Wheels_N` from a skin: raised
  letters, the tread patterns, Nadeo's lettering gone), whether the lettering reads at 2 to 2.5 cm
  from the chase cameras and in the garage, and whether the band (30.9 to 35.3 cm from the axle)
  clears the wheel covers' edge and the three dark patches of the game's own shading.
- **The upload size limit.** Zips stay under 8.5 MB until a limit shows up (2026-09-24,
  checkpoint 1); the install halves the roughness maps to fit (2026-09-25). Undocumented;
  Ubisoft said in 2022 that 9 MB "may be too big".
