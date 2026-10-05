# Improvements to the tool

The queue of what the tool should do better: each item in two or three lines, what's wrong and an
idea for the fix. The user says when to work on it. A finished item is deleted; what it taught
goes into the code.

## The harness (the plan: `PLAN.md`)

The next steps, in order, each shown and OK'd before the next (2026-10-02). A finished step is
deleted here; `PLAN.md` keeps the why.

- **3. Drawing on the car to say what you mean** (the user, 2026-10-05, after fresh eyes were
  dropped): "draw on the body to communicate something. Let's say I want a strip of something, maybe
  I can just draw on the surface where I would it and then the ai just gets the idea. Or maybe I
  want to circle something". Idea: a pen in the Lab that draws on the car's surface, kept as points
  on the body (in the measure's cm) and sent with the note; a drawn strip becomes a zone.
- **4. Rules that are checks**: a hook refuses a shell command naming the game's skin folder (the
  install command excepted); a hook won't end a session with unpushed work; `skin install`
  publishes the page online itself.
- **5. Instructions that can't rot**: the self-test checks that every command and path the
  guidance names exists.
- **6. Where we are at a cold start**: `tool.notes open` lists every skin's open items; the
  SessionStart hook prints it after the pull.
- **7. The tool measured against the record**: every change the user ever asked for, with the
  picture shown before it, as a test set; the eyes and the measures scored on it, on demand.

## Under way

- **Drawing on the skin** (`tool/skindraw.py`): paused by the user ("lets stop. None of the cars
  make me think it's working"); its foundation, the guides (step 2), is in place: it resumes when
  the user asks, for lines an idea calls for.
- **The car map** (`tool/carmap.py`, `car/map.md`): its readings (the shoulder, the lower edge,
  the ridges, the areas) differ slightly between the Mac and the PC (numpy and BLAS). Step 2 puts
  committed cuts under them; the readings are then checked against the cuts.

## The tool

- **Repaint only the map that changed**: every `show` paints the whole car (about a minute) even
  when a note touched only the tyres. Idea: repaint that map alone, if the game files stay identical.
- **The Lab is empty before a new car's first paint**: idea: the car in clay with a line on the
  stage until the first paint.
- **Words on the inner car** read backwards on one side (mirror twins share texels). Idea: name the
  inner parts' unshared areas big enough for a word as spots.
- **Motifs lined up across panels**: scatter spreads evenly but can't do rows that line up. Idea: a
  `regular` switch on `Skin.scatter`.
- **Some inner part names are guesses** (side vent, side vane, nose sensor, airbox): check them the
  first time a design paints them; renaming touches `tool/naming.py` and `AIRBRAKES` in the viewer.
- **The fasteners have no name**: they wear one tiny strip the parts list gives to the front wing
  (TSC_CMYK_EndsInK paints it by hand). Idea: name them in `tool/naming.py`.
- **Worn paint doesn't read as worn**: `s.wear` scatters by noise, like a pattern. Idea: wear driven
  by the car's shape (edges, recesses, contact points), layered paint, primer, metal.
- **A step that covers an earlier step's paint says nothing.** Idea: a note at the step's end.
- **The comparison picture's labels** number takes 1, 2, 3 on top of A, B, C, and drop a fourth
  view. Idea: letters, and a second row.
- **A finer, evenly shaped grain** (the user, on TSC_CMYK_EndsInK): 2 mm noise specks are the
  smallest that survive the zip budget. Idea: specks per 4x4 block from a few variants, so they
  compress.
- **The picture maker on the Mac**: it needs the PC's card. Idea: FLUX.2 [klein] on Metal,
  quantised; look up the latest release first.
- **Two tyre fonts don't paint on the Mac** (Bahnschrift, Consolas). Idea: open look-alikes.
- **Real scanned materials** (Poly Haven, ambientCG, CC0) for finishes and wear, fetched as needed.
- **The materials and the UV map, in a new way**: the user's to describe, after step 2 (the user,
  2026-10-02); start from their words.
- **The car map against well-made skins** (the user's idea): 11 skins the user downloaded (2026-10-04,
  `tm.rar`, unpacked into `community/`; the Mac only, git-ignored). Lay their body textures' sharp
  colour edges on the car (pinstripes from nose to tail, two-colour splits along the shoulder) and
  compare them with the map's lines and step 2's cuts; fix the map where they agree it's off, in
  pictures. For checking the map only: they never shape a design. Some use `BC5U`/`BC4U` headers,
  which `dds.read` doesn't take yet.

## The viewer

- **The game's cameras at speed**: fitted standing still; in the game they pull back with speed.
  Idea: fit Cam 1 at a few speeds from the user's videos.
- **The car number's lettering is a guess** until a close-up of the engine cover.
- **The rear wings and air brakes** move at the video's pace, their angles set by eye. A short side
  video would pin them.
- **The page online**: softer than here on big screens (2048² paint), about 20 MB before the car
  shows. Ideas: 4096² colour maps on large screens; a compressed mesh and a smaller sky on phones.
- **Phones**: on its side the car gets a third of the height; Cam 1 and 2 are small on a tall
  screen. Ideas: a one-line name under 500 px high; frame the game's picture by its height.

## To check in the game

Settled when the user drives a skin that uses it and says or shows what they saw; never ask them.

- Finishes never seen there: candy, chrome rims, rust, leather, metallic flake; the viewer's matte,
  satin, gloss and chrome against the game's.
- Glows never seen: exhaust heat (TSC_CMYK_EndsInK carries it: a turbo pad settles it) and boost.
- Whether the wheel covers turn; how see-through the glass is (tint only, so far).
- Tyre markings: never in the game yet (their relief, legibility, the band clearing the covers).
- A glow on the body: never tried (`Skin_I` in `Details_I`'s format on a test skin).
- The upload size limit: zips stay under 8.5 MB until one shows up.
