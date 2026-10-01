# Improvements to the tool

The queue of things the tool should do better. Newest at the bottom of each group. The `skin`
skill says how it's kept: during a skin, Claude fixes only what that skin needs and adds
anything else here. The user says when to work on the list. A finished item is deleted from
here, and what it taught goes under its topic in `LEARNED.md`.

Each item: what's wrong or missing, when and where it showed up, and an idea for the fix. A
bigger item under way keeps its working notes at the end of `LEARNED.md`.

What matters most (the user, 2026-09-28: "We can always define improvements on performance, and
most importantly quality and accuracy"): quality and accuracy first (the car as the game shows it,
the design as asked), then speed.

## Under way

- **The PC's check of the tidy-up** (2026-10-01, the deep tidy-up, done on the Mac while the PC was
  away: the user asked for it as a queued task). **On the first session on the Windows PC, before
  any install or anything else:**
  1. The session's pull brings it; install the requirements if they changed
     (`PY -m pip install -r requirements.txt`).
  2. `PY -m tool.selftest --against b0ca0e8` (about 25 minutes the first time: it paints the old
     code's side once). Every texture and every DDS file must come out identical: the PC's
     processor has to agree with the Mac's, the texture encoder above all.
  3. One real `PY -m tool.skin install` of a skin already in the game (it replaces itself, e.g.
     TSC_CMYK_EndsInK), timed. Before the tidy-up its zip took 196 to 258 s to build on the PC.
  4. Write both results under "The deep tidy-up" in `LEARNED.md`, then delete this item.

  If anything differs, don't install: find and fix the difference first, and tell the user in one
  line. Never ask the user to test; they may look in the garage if they want to.
- **Drawing on the skin** (the user, 2026-09-30: "Current approaches are not working ... I cant
  figure out how ai can draw the car without making mistakes ... perfect lines that are accurate and
  continuous"). Lines are drawn ON the surface (`tool/skindraw.py`) on one mesh of the whole car
  (`tool/skinmesh.py`) and checked on the car (`tool/skincheck.py`). **The user, after the exam car
  (TSC_SkinExam, 2026-10-01): "lets stop. None of the cars make me think it's working."** The
  numbers passing hasn't convinced them by eye: ask what they'd need to see before building more,
  and don't count a check passing as the item working. Left: the nose band over the bonnet's centre
  fin; the hoop down the flanks; a break and stray-paint measure that can be trusted; a filled area
  bounded by a drawn curve; "a famous livery look: black and gold pinstripes" (the user's pick, not
  started). Working notes: `LEARNED.md`.
- **The car map: the AI understanding the car** (the user, 2026-09-29: "I actually care that the Ai
  can prperly understand how to design cars"). Built (`tool/carmap.py`; `car/map.md` and its
  pictures, read before every design): what's open, the areas split along the car's own lines,
  positions along the car, the air over it, what the chase cameras see. Its own lines are no longer
  drawn with (drawing on the skin, above). Waiting for the user's look at the lines and areas
  (`car/map/lines.jpg`, `car/map/areas.jpg`) before anything built on them is called done.
  TSC_WindTunnel waits for the user too. Left: what each game camera shows (only the chase
  cameras' view so far), the flat spots for pictures measured rather than typed (`SPOTS`), a check
  on every paint for graphics crossing a fold or an opening, and streaks combed along the flow.
  Working notes: `LEARNED.md`.
- **The car map isn't the same on the two computers** (2026-09-29, the car mapper): rebuilt fresh on
  the Mac, the map traces 66 ridges and draws 12 folds where the PC recorded 62 and 8, and `python
  -m tool.carmap --check` fails 4 stretches and 1 curve that passed on the PC. The ridge tracing
  (`carmap._trace_ridges`: seeds by a strict local maximum of k1, crests refined by a parabola,
  cuts at 1.5 cm) decides differently on tiny numeric differences between the two computers' numpy
  and BLAS. The map's areas are cut by its fitted lines, so `area("top")` can differ a little
  between the two computers (TSC_Map_Areas, TSC_WindTunnel's rakes). Idea: make the tracing's
  decisions tolerant (a seed a clear maximum by a margin, ties broken by position), or build the
  map on one computer and commit its cache's hash so the other checks it matches.
- **The design studio, now one way of working** (the user, 2026-09-28: "What's important is to
  actually have this as an incredible workflow that builds cars (not the typical amateur skins) but
  actually work on every single detail from start to finish"; then "I don't really work that
  way" to a studio of steps). Now: the car and the user's notes, sets of options in the Lab's
  timeline whenever they ask, and for a new car a short talk, three concepts, every detail with the
  guides and the critic before the game (`new-car.md`). Left: the user's word on it as they use it
  ("ill probably explore ways to make the workflow better for designing").
- **The Lab's timeline with Claude** (the user, 2026-09-28: "having the sidebar on the right as the
  ai helper ... a scrollable timeline ... the latest would be at the bottom"; they picked A of the
  mockups, a chat with two voices). Built 2026-09-28: waiting for the user's try.

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

- **Repainting only the map that changed** (2026-09-27). Every `show` paints the whole car (about a
  minute for TSC_CMYK_EndsInK on the Mac, 90 to 127 s on the PC), even when a note changed only the
  tyres. A change often touches one of the game's maps (Skin, Details, Wheels, Glass), so it could
  repaint that map only, if the game files come out identical to a whole repaint (`tool.selftest`
  says). It makes every change faster.

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
## The viewer, from the user's screenshots and videos

- **The game's cameras at speed** (2026-09-25, the user). Cam 1 and 2 and their alts are fitted
  to the user's screenshots standing still (`LEARNED.md`, "The game's cameras, lens and moods"). In
  the game they
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
  let go) would pin them (`WING` and `AIRBRAKE` in `viewer/viewer.js`).
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
