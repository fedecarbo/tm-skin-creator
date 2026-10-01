# Improvements to the tool

The queue of things the tool should do better. Newest at the bottom of each group. The `skin`
skill says how it's kept: during a skin, Claude fixes only what that skin needs and adds
anything else here. The user says when to work on the list. A finished item is deleted
from here, and what it taught goes under "Things we learned" in `CHECKLIST.md`.

Each item: what's wrong or missing, when and where it showed up, and an idea for the fix. A
bigger item keeps its working notes under "Improvements after the build" in `CHECKLIST.md`.

What matters most (the user, 2026-09-28: "We can always define improvements on performance, and
most importantly quality and accuracy"): quality and accuracy first (the car as the game shows it,
the design as asked), then speed.

## Under way

- **Drawing on the skin** (the user, 2026-09-30: "Current approaches are not working ... I cant
  figure out how ai can draw the car without making mistakes ... perfect lines that are accurate and
  continuous"). Lines are drawn ON the surface as geodesics (`tool/skindraw.py`: `through`,
  `circle`, `loop`, `mirror`, `band`) on one mesh of the whole car (`tool/skinmesh.py`), and checked
  on the car by exact geodesics across each band (`tool/skincheck.py`, `--falsify`). Built and
  measured: widths within 0.2 mm, middles within 0.1 mm, on seventeen bands of eight kinds.
  **Left:** the nose band over the bonnet's centre fin; the hoop down the flanks; a break and
  stray-paint measure that can be trusted; a filled area bounded by a drawn curve (a split along a
  sweep, one colour each side).
  Notes: "Drawing on the car's own skin" in `CHECKLIST.md`.
  **The exam, 2026-10-01** (TSC_SkinExam, the user's pick of four test ideas, with "a famous livery
  look: black and gold pinstripes" to follow, not started): 15 of its 17 lines pass the check (the
  two that don't are the 1.5 and 1 mm pinstripes, too thin for the texture), and the earlier cars
  were re-measured, with a few spots still flagged (TSC_Skin's flank sweeps at a panel joint z -82,
  SkinMore's two middle stripes and Solstice's cream stripe at their ends). Several real faults were
  found and fixed on the way (`CHECKLIST.md`). **The user, after it: "lets stop. None of the cars
  make me think it's working."** The numbers passing hasn't convinced them by eye: ask what they'd
  need to see before building more, and don't count a check passing as the item working.
- **The car map: the AI understanding the car** (the user, 2026-09-29, after TSC_WindTunnel's
  concepts: "would it be best to focus on actually mapping the car properly, so that no matter what
  design is done, the Ai just knows?", then "I don't care about a car anymore, because I actually care
  that the Ai can prperly understand how to design cars"). Built the same day, six steps
  (`tool/carmap.py`; `car/map.md` and its pictures, read before every design): what's open, the
  areas split along the car's own lines, its lines, positions that bend with the body, the air over
  it (where it hits, its flow, smoke lines), what the chase cameras see. Tested on TSC_WindTunnel,
  whose smoke lines it now draws (403 lines of design down to 76). Left, from the plan's "later":
  what each game camera shows (only the chase cameras' view so far), the flat spots for pictures
  measured rather than typed (`SPOTS`), a check on every paint for graphics crossing a fold or an
  opening, and streaks combed along the flow. TSC_WindTunnel waits for the user. Notes:
  `CHECKLIST.md`, "The car map".
  **First, the user's review (2026-09-29):** "I don't think you did the green and the yellows and
  magenta mapping right. Some lines just looked very wobbly ... They just don't follow the lines of
  the cars and the curvature properly." Right: the shoulder and the lower edge are a threshold on
  each slice's facing (50 and 125 degrees), smoothed along the car, so on a rounded edge they sit
  wherever the threshold falls, not on the body's own crease, and they wander where the section
  changes (the sidepods' front, the nose's lip, the nose's tip); the front and back areas are a
  threshold on the facing too, so they come out as blotches. Idea: find the car's real feature lines
  from its curvature (the ridges where the surface bends most), trace each as one continuous curve
  along the car, and take the shoulder and the lower edge from those; the front and the back as
  whole faces bounded by them. **Done 2026-09-29 (the car mapper, step 7 in `CHECKLIST.md`)**, judged
  by measurement (`python -m tool.carmap --check`), not by eye (the user: "I don't think it's feasible
  to do it by eye"). After round 3 (step 9): the named lines are smooth curves fitted to the
  evidence (the shoulder from the nose to the sidepod's rear corner in one, evidence within 4.5 mm),
  the areas are cut by those curves and the mesh's own edges, only real folds are drawn (8), and the
  check measures the curves as the eye sees them (mm limits on the car and in the flat texture).
  Behind the sidepods (z -95 to -35) the body has no clear lower edge: the sides run to the skin's
  own end there. Waiting for the user's look at the lines (`car/map/lines.jpg`,
  `car/map/areas.jpg`) before anything built on the map (the rakes, the grid, the station table) is
  called done. Step 10, a flat sewing pattern of the skin to draw on, and bands drawn from the map's
  fitted lines were retired on 2026-09-30 for drawing on the car's own skin (the item above); the
  map keeps its areas, what's open, the air and the chase cameras. Notes: `CHECKLIST.md`, "The car
  map", and "Drawing on the car's own skin".
- **The car map isn't the same on the two computers** (2026-09-29, the car mapper, found while
  building the body sheet): rebuilt fresh on the Mac, the map traces 66 ridges and draws 12 folds
  where the PC recorded 62 and 8, and `python -m tool.carmap --check` fails 4 stretches (the shoulder
  over the rear flanks, ridge 0.85; the lower edge at the sidepods, a 16 cm step) and 1 curve (the
  shoulder 188 to -50: ragged 3.4 mm, texture 4.2 mm) that step 9 recorded as passing. The ridge
  tracing (`carmap._trace_ridges`: seeds by a strict local maximum of k1, crests refined by a
  parabola, cuts at 1.5 cm) decides differently on tiny numeric differences between the two
  computers' numpy and BLAS. Idea: make the tracing's decisions tolerant (a seed a clear maximum by a
  margin, ties broken by position), or build the map on one computer and commit its cache's hash so
  the other checks it matches. Not fixed. Lines are no longer drawn from the tracing (drawing on the
  skin, above), but the map's areas are still cut by its fitted lines, so `area("top")` and
  `across` can differ a little between the two computers.
- **The design studio, now one way of working** (the user, 2026-09-28: "What's important is to
  actually have this as an incredible workflow that builds cars (not the typical amateur skins) but
  actually work on every single detail from start to finish"). Built the same day in four goes: a
  studio of eleven steps, experts (the step guides, the concept designers, the critic), a wizard in
  the Lab; then, at the user's word, three steps, then none: "I don't really work that way". Now:
  the car and the user's notes, and sets of options in the Lab's timeline whenever they ask (the fresh
  layouts' A); a new car gets a short talk, three concepts as its first set, every detail with the
  guides, and the critic before the game (`new-car.md`). Notes: `CHECKLIST.md`, "The design
  studio". The test against the quick way (W4) dropped (the user, 2026-09-28): "ill probably
  explore ways to make the workflow better for designing". Left: the user's word on it as they use
  it, and whatever they explore.
- **The Lab's list as a timeline with Claude** (the user, 2026-09-28: "having the sidebar on the right
  as the ai helper ... a scrollable timeline ... the latest would be at the bottom"). The user picked
  A of the mockups, a chat with two voices. Built 2026-09-28 on the Mac, the leftovers of the earlier
  layouts cleared first: waiting for the user's try. Notes: `CHECKLIST.md`, "The Lab's timeline".

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
  `tool/naming.py`, `skins/TSC_Stealth_CMYK/design.py` and `AIRBRAKES` in
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
  porcelain and gold). Nothing
  says so: the Lab's filmstrip showed it, if someone looked, and it's gone. Idea: at the end of each step, note any
  part an earlier step painted that this step covered for the most part ("Inner car covered
  Porcelain, Mended with gold on the body shell"), as `show` notes shared paint.
- **The comparison picture's labels and views** (2026-09-26, the concept round): it numbers the
  takes 1, 2, 3 on top of Claude's A, B, C ("1 A Kintsugi"), and a fourth view asked for is left
  out without a word (the sheet is three tiles wide). Idea: letter the takes A, B, C as the Lab's
  sets do, and wrap extra views to a second row.

- **The fasteners have no name** (2026-09-27, TSC_CMYK_EndsInK: the user saw small cyan rings on
  the black). The little rings on the cockpit, engine cover, nose and front wing all wear one tiny
  strip of the Details map (texels 2248-2251, 2566-2607 at 4096), which the parts list counts as
  the front wing's, so they take the front wing's paint wherever they sit, and "paint also lands
  on" never says so (they're a handful of texels). The skin paints the strip by hand
  (`fasteners()` in TSC_CMYK_BlackTail's design). Idea: name them ("fasteners") in
  `tool/naming.py` so any design can paint them.
- **A finer, evenly shaped grain** (2026-09-27, TSC_CMYK_EndsInK, the user after driving it:
  "Maybe I couldve wanted a bit more finer evenly shaped grain, but looks fine to me, maybe for
  next session?"). The textured wrap (WT-07) makes its specks from noise, so they come in mixed
  shapes, and 2 mm is the smallest that holds: once the body's sheen map fills with grain, the
  zip's budget halves it to 2048² (0.18 cm texels). Finer (1 to 1.5 mm) and even (round specks of
  one size, evenly spread) needs that map at full size. Idea: draw the specks in texel space,
  one per 4x4 block from a handful of variants, so the compressed blocks repeat and zip squeezes
  them (a guess: 1.5 to 2 MB at 4096², the zip about 8.1 MB); if that's still too big, free room
  elsewhere (the suspension's blasted grain in Details_R). Check the zip first, then the game.

- **Repainting only the map that changed** (2026-09-27, the Lab's step 9.7, queued here when the
  design studio took over the Lab on 2026-09-28). Every `show` paints the whole car (90 to 127 s for
  TSC_CMYK_EndsInK), even when a note changed only the tyres. A change often touches one of the
  game's maps (Skin, Details, Wheels, Glass), so it could repaint that map only. Only if the game
  files come out identical to a whole repaint. It makes every change faster. Notes: `CHECKLIST.md`, The Lab,
  step 9.

- **The picture maker on the Mac** (2026-09-28, TSC_Ladybird): it runs only on the PC's graphics
  card, so a car designed on the Mac can't have new pictures made for it. Idea:
  FLUX.2 [klein] natively on the Mac (Apple M5, 16 GB) through diffusers on Metal, quantised to fit
  (its two halves are 8 GB each at full size); look up the latest release first.
- **Two tyre fonts don't paint on the Mac** (2026-09-28, TSC_Ladybird's wheels; narrowed
  2026-09-29): since the Mac runs the tool itself, `fonts.MAC` finds the Mac's own Arial, Impact,
  Verdana, Georgia and Tahoma, but the library's Bahnschrift and Consolas wordmarks are Windows-only
  and still fail there. Idea: an open font of the same look (DIN-like for Bahnschrift, a mono for
  Consolas), fetched like the Google fonts, on the Mac only; the PC keeps its own.

- **The materials, in a new way** (the user, 2026-09-28: "Ill probably add UV map and materials but
  in a different way"). Today they're in the car's menu (every finish on a ball, with its code and a
  "Copy for Claude"). The new way is the user's to describe: start from their words, then mockups.
- **The UV map, in a new way** (the same words). Today it's in the car's menu (the game's four flat
  maps, a surface picked and lit on the car, a line to copy). As above: the user's words first.

- **Real scanned materials** (the user's pick, 2026-09-29, from a search for useful tools). Poly
  Haven and ambientCG give measured scans for free (CC0): carbon, brushed metal, scratches, chipped
  paint, grime. They'd feed the textures library (`tool/textures.py`, `textures/library.json`) and
  "worn paint that reads as worn". Idea: fetch only what a finish needs, record each one's source,
  and add no new library.
- **Proven geometry libraries for the car map's accuracy** (2026-09-29, the user: "what I struggle
  is the accuracy when dealing with a 3d model and uv map ... maps the curvatures from the model into
  the uv map so the ai just knows"). The bake already gives every texel its 3D position and facing.
  The curvature, the ridges and the curves (`carmap._curvature`, `_principal`, `_trace_ridges`,
  `tool/mapcheck.py`) are our own numpy code. Give these to the car mapper after its current step,
  not during it:
  - **libigl** (Python bindings, 2.6.2 on PyPI, March 2026, MPL-2.0): tested principal curvatures
    and directions, as a second, independent measure for `--check`, or in place of ours.
  - **potpourri3d** (geometry-central's bindings, MIT): distances along the surface (the heat
    method) and the logarithmic map, which gives every texel near a point its coordinates measured
    along the body. With it, a stripe, a logo or a grid is placed by measuring on the car, so it
    wraps without stretching and lines up across the UV seams and the mirrored halves. That serves
    the positions that bend with the body, measured `SPOTS`, and "motifs lined up across panels".
  - Before adding either one: its latest release, wheels for Python 3.14 on Windows and macOS arm64,
    pinned in `requirements.txt` with the date.
  **Used, 2026-09-29 (step 10 of the car map):** both have wheels for CPython 3.14 on Windows x64 and
  macOS arm64 (libigl 2.6.3 as cp312-abi3, potpourri3d 1.4.0 as cp314), pinned in `requirements.txt`,
  installed in the Mac's venv (the PC gets them at its next session). libigl flattened the sheet
  until it was retired (2026-09-30); its `principal_curvature` is the `igl` column of `--check`'s
  curves table (the named
  lines and most folds stand out on both measures; per vertex they correlate only 0.26, and it marks
  half the welded body's vertices unfit for its quadric fit). potpourri3d now draws: since
  2026-09-30 every line on the car is a chain of its exact geodesics (`EdgeFlipGeodesicSolver`),
  and a band's width and the check across it are walked with its `GeodesicTracer` (`tool/skindraw.py`,
  `tool/skincheck.py`); its signed heat method wants curves on edges, so it isn't used.
  Looked at and left out (the same search): Substance 3D Painter (US$200 once on Steam, but it's
  painted by hand, not driven by words); Hunyuan3D-Paint and Meshy (they paint the whole mesh from
  a sentence, loosely, ignoring the map and the game's format); Recraft (vector logos and lettering,
  subscription) and Z-Image-Turbo (a free picture maker to compare with FLUX.2 klein): quality, not
  accuracy, so revisit those when quality is the focus. TypeSafe's Jev only picks from fixed
  answers, so it's no use here.

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

Only the game can settle these. Each is settled when the user drives a skin that uses it and says
or shows what they saw; never ask them to test (`CLAUDE.md`).

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
- **A glow on the body** (2026-09-29, TSC_WindTunnel: Claude said the body can't glow, the user:
  "I don't think this is true btw"). The tool lets only the inner car glow because Nadeo's list of
  skin files has a glow map (`Details_I`) for the inner car and none for the body, and the stock
  model carries `Glass_I` and `Wheels_I` but no `Skin_I`. A `Skin_I` was never tried. Idea: a test
  skin with a `Skin_I` in `Details_I`'s format (BC3, the same alpha codes): a stripe always on, a
  patch at night only, one lit with the brakes; install it on the PC and look in the garage and at
  night. If the game takes it, `Skin.glow` works on the body too (the viewer's night view as well).
- **The upload size limit.** Zips stay under 8.5 MB until a limit shows up (2026-09-24,
  checkpoint 1); the install halves the roughness maps to fit (2026-09-25). Undocumented;
  Ubisoft said in 2022 that 9 MB "may be too big".
