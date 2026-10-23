# Improvements to the tool

The one queue of what the tool should do better: each item dated, in two or three lines, what's wrong
and an idea for the fix. The user says when to work on it. A finished item is deleted; what it taught
goes into the code. It mustn't pile up or go stale: the session-start check (`tool/doctor.py`) says
"prune it" past 20 items or when one is older than 30 days; at a pruning each item is kept (re-dated,
still in the user's words), done, or deleted (git keeps it). Things that exist are named in backticks
and checked by the self-test; ideas are named in plain words.

## Next: the road

One step per session: built under the self-test, its worth shown on a new test car made for it (never a past car) or
in plain words and numbers, then on the user's OK everything it retires removed and the step deleted here. Decided
2026-10-22 (the user: "there has to be a better way for AI to 'see' the car without a written essay"; "I just want
perfectly painted cars. The accuracy bit."; the evidence in `research/see/`): **the car does the seeing, never the
AI's eye**. The last step the user asked for after its four, then 13 on the PC (away until November or December
2026):

20. **The Lab shows the strokes** (in the Lab's repo; the user, 2026-10-22: "It's fine if you show it on lab"): each
    step's words beside its strokes' landings and findings, a choice and an accident told apart, the known ones marked.
    Retires nothing.
13. **Yardsticks, on the PC** (Opus 5.5, high). The game files encoded once by quicktex and texconv against the tool's
    own encoder; the camera's colours fitted first to a garage screenshot with the game's camera light on (the
    cleanest picture of a skin's colours the game gives; `viewer.lamp`), then per mood to the user's F12 screenshots
    (FLIP: exposure, environment strength, tone mapper, clearcoat), and from their videos the cameras pulling back with speed, the car number's lettering, the
    rear wings' and air brakes' angles. Retires nothing unless another encoder wins.

## The tool

- **A sticker over the sidepod top's inner edge comes out half** (2026-10-22, TSC_RingsAcross at (56, 62, -15)): the
  sidepod top is its own piece, its edge a 0.5 cm lip facing the 0.4 cm gap to the body shell, 115 degrees from the
  shell's edge across it, so the gap is neither bridged (skins facing alike) nor spanned (a wall facing 70 degrees from
  the sticker) and the shell's half never gets a place. Idea: the lip and the gap as one groove of two pieces, filled
  to its mouth as a panel line's is.
- **A plain line beside the skirt's crease blocks ten times** (2026-10-22, TSC_IntentTest, on step 16's car too): a 1 cm
  band 1 cm beside 'side skirt crease 3' gets steps of 0.3 cm read against 'side skirt roll 3' and 0.7 cm where it
  meets 'side skirt crease 2'; the close looks show it smooth. Idea: see whether the ruler line steps there, not the paint.
- **A colour name half known is taken as the half it knows** (2026-10-22, the test car's agent): `colours.get("warm
  white")`, "antique white" and "floral white" give plain white, dropping the word it doesn't know, while "deep" and
  "bright" are read. Idea: a name not known whole fails with "did you mean", as a part's name does.
- **A named spot behind the rear wheel** (2026-10-22, step 15's finding on the self-test's cars): `SPOTS` in
  `tool/paintbox.py` puts "left side" at (70, 41, -66), where 10 cm words are 42 % behind the rear wheel seen square
  (the planted-flaw pair's SIDE at (67, 50, -75) wholly); the car's `at` question says the same. Idea: the spots taken
  from the flat rooms (`marks.rooms`), which know the wheels.
- **One rounded edge named as several rolls** (2026-10-22, the test car's agent): body shell rolls 1, 2 and 5 lie side
  by side along the deck's shoulder (tilts 22, 33, 40) but are three names, their lengths too unlike for one roll, so
  "the rounded edge through (40, 62, -20)" is three answers and two agents picked different ones.
- **Where the judge and the close looks say less than they seem** (2026-10-22, the test car's agent): a finding's
  place is a station along the car's middle (a skirt dot at (28, 18, 119) "the nose fin's plate"); the close looks
  saw no change when the whole body's white changed, and wash out white on warm white under the camera light; the
  scatter, asked for 4 cm copies, made 12 of 27 smaller, and its receipt gives no places.
- **The PC's repo is inside OneDrive** (2026-10-21, the user: "why is ours on onedrive?"): Windows puts Documents under
  OneDrive by default, and the clone went there; the work folder was put outside OneDrive because of it. When the PC
  is back: clone the tools and the Lab into a plain folder (`C:\Users\fedec\Developer\`), as on the Mac, and point
  the hooks' and the doctor's notes at it. The game's own skin folder stays where the game keeps it.
- **Fur made by the tool, with a lay that follows the car** (2026-10-09, TSC_Bumblebee's surfaces pass; 2026-10-11): the
  photographed piles (fur, teddy fur, plaid fur, plush, velvet, fleece: `tool/textures.py`, the Lab's LF-08 to LF-13) lay
  their nap along each panel of the car's unfolding, fixed in the photo, so a photo's hairs can't sweep round the nose
  and tail; the suede look takes only a seed, and the brushed look, the only nap with a direction, lies along the
  world's z (one direction per call). Idea: a lay per texel (the car's long axis on the surface, the vector
  `carmap.Map.gradient` already computes per triangle; toward the nearest model line's tangent where the body faces
  the ends), passed by `paintbox.Skin` to a fur look in `tool/looks.py` (hairs of a length, clumps, dark roots) and
  to `brushed`.
- **A wash isn't a run** (2026-10-09): a paint under half weight, or zoned by `shapes.facing` or the open air, is a
  wash, but the judge read a blend 0.55 paint as one gappy run (thirty "gap" findings) and the receipt, counting only
  texels covered by half or more, says "nothing painted" for a blend under 0.5 though it lands. Idea: a wash has no
  gaps to read; the receipt counts any weight and says the blend.
- **A line on a panel line sits on one wall of its groove** (2026-10-06, from the model's lines, G): `meshlines.line`
  along a panel line lands on one wall of its 0.36 cm groove, not its middle. The user, of the mesh: "there's
  improvements to make but for now let's keep it that way until I actually start building a car".
- **The scatter's charts are the paint's slowest part** (2026-10-09, step 10's profile): 18 of the tour's 82 s under the
  profiler, five exact solves a copy on the processor (`surface.Surface.chart`), and the marks' sheet 5 s more in
  np.unique. Idea: a chart's five solves on the processor's cores at once; profile the sheet's bookkeeping.
- **A mark on both sides fitted on each alone** (2026-10-08, found by the close looks): the planted-flaw pair's clean car
  lays its deck picture (one call, both sides) with 7,505 texels on the left and 2,947 on the right, shrunk to fit on
  one side only; nothing else says so. Idea: fit it once, for both sides, and say what kept it small.
- **Names in the parts list** (2026-10-05): some inner part names are guesses (side vent, side vane,
  airbox: check them the first time a design paints them; 2026-10-07: the "antenna" is the probe under the nose,
  the "nose sensor" is hidden inside it, the "sidepod grille" is the backing of the visible "sidepod grille plate"), and the fasteners have none
  (they wear one tiny strip the list gives to the front wing; TSC_CMYK_EndsInK paints it by hand). The body's own bolt heads are four tiny parts with one paint for
  the whole car, which no zoned paint reaches: gold dots on every shard of TSC_Kintsugi, unasked.
  Renaming touches `tool/naming.py` and the viewer.
- **Pollen grains of 2 mm** (2026-10-09, TSC_Bumblebee): pale specks two texels wide on black fur; the game's colour
  compression may flatten single grains, a haze should survive.
- **Never seen in the game yet** (2026-10-05): the finishes candy, chrome rims, rust, leather,
  metallic flake, and the viewer's matte, satin, gloss and chrome against the game's; the exhaust heat
  and boost glows (TSC_CMYK_EndsInK carries exhaust heat); whether the wheel covers turn; how
  see-through the glass is (tint only, so far); tyre markings (their relief, legibility, the band
  clearing the covers); a glow on the body (Skin_I in Details_I's format, on a test skin); the upload
  size limit (zips stay under 8.5 MB until one shows up).

## Found on several cars

Kept by the judge (`tool/ledger.py`): a flaw found in one place on three cars, or let go on two, is the tool's, not
the design's. The judge says "known, queued" on it and the gate lets it pass; it's taken out when no car shows it any
more. Fixed, or found not the tool's: delete its item, and only cars judged after count it again.

- **K1: line, on 3 cars** (2026-10-22, last seen; TSC_Ledger1, TSC_Ledger2, TSC_Ledger3; at (±28, 18, 119), (±32, 19,
  91), (±56, 20, 43), (±61, 20, 38), (±68, 21, 31)): gloss #f2f0ea on body (Skirt line): a band 1 cm wide along the
  model's crisp line 'side skirt crease 3', 1 cm to its left: a step of 0.3 cm sideways, on the right, z +119 (the
  bonnet); read against the model's line along a rounded edge 'side skirt roll 3' tilted 25 degrees, 0.3 cm from the
  design's course, mirrored to the right
