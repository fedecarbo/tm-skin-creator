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
AI's eye**. Four steps, then 13 on the PC (away until November or December 2026):

14. **The car answers, and the traps come out.** Built, waiting for the user's OK (2026-10-22): `PY -m tool.meshlines`
    answers questions from the mesh (a line's ends and course, a panel, a part with its piece and gap, a point by the
    skin the eye sees, a where-word, flat rooms); every course from `meshlines.line` runs nose first; `marks.rooms` seen
    square with the wheels in place; `car/anatomy.md` only the axes and where a graphic stops. Shown on TSC_SeeTool,
    painted by a fresh agent from the skill alone, beside TSC_SeeControl and TSC_SeeTest (the same brief). On the OK: the
    three test cars deleted, and this step.
15. **The landing in every receipt.** What `research/see/dryrun.py` prints, printed by `tool.skin show` as the paint
    goes: each call's stretch of the car (z, y, x), the parts under it, its area, and a sketch of every call's texels
    on the side and top views; and a way to stop before the textures, the judge and the views, so a design is read
    against the car in 12 s (a simple car) to a minute (a busy one) before anything is shown. The test: a design with
    strokes planted in the wrong place (a stretch by z landing on a line's far side, a zone on the wrong parts, a
    badge behind a wheel), each caught before a paint. Retires nothing; it replaces repaints (the control car of
    2026-10-22 took three paints, the test car one).
16. **The judge names its ruler and the bites it can't see.** Every placement finding names the line it read against;
    a row of marks at a course's places and dots zoned by `shapes.sphere` get a check and a close look; a sticker's bite
    where `surface.Surface.chart` spans a step onto a raised plate (the nose ring of 2026-10-22, notched where it
    climbs the nose fin's plate; the chipped decals of 2026-10-08) measured first, then fixed in the chart. Retires
    the three queue items below that name these.
17. **Intent beside landing.** Each step's `words=`, each call's landing and the judge's findings on it, written to the
    viewer's data for a concept to show stroke by stroke, so a choice and an accident look different to the user (their
    picture of the notched ring, 2026-10-22: the crossing meant, the notch the tool's, the block for a third reason).
    Retires nothing.
13. **Yardsticks, on the PC** (Opus 5.5, high). The game files encoded once by quicktex and texconv against the tool's
    own encoder; the camera's colours fitted first to a garage screenshot with the game's camera light on (the
    cleanest picture of a skin's colours the game gives; `viewer.lamp`), then per mood to the user's F12 screenshots
    (FLIP: exposure, environment strength, tone mapper, clearcoat), and from their videos the cameras pulling back with speed, the car number's lettering, the
    rear wings' and air brakes' angles. Retires nothing unless another encoder wins.

## The tool

- **A colour name half known is taken as the half it knows** (2026-10-22, the test car's agent): `colours.get("warm
  white")`, "antique white" and "floral white" give plain white, dropping the word it doesn't know, while "deep" and
  "bright" are read. Idea: a name not known whole fails with "did you mean", as a part's name does.
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
- **Decals chipped where a crisp line crosses them** (2026-10-08, the user, giving step 5 its OK: "certain decals where
  chipped or slightly clipped"; their note on the test car's badge across the rear shoulder: "This decal looks chipped
  off on one part of the circle"): a notch about half a centimetre wide in the ring where a crisp line crosses it, left
  by `surface.Surface.chart`'s step spanning or its bridging at the sidepod top's hairline; find which on a chart of that
  spot (the test car TSC_DecalsTest is in git at 3fac0d5). Step 6's judge names a decal not whole; a 5 cm disc on the
  body across=True near z -84 (TSC_CloseTest, in git at 6ec0595) has a 0.6 cm² notch on both sides that only the close looks name.
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
- **The judge doesn't name the line it read a marking against** (2026-10-21, the test car's agent): "cut short by the
  edge where the body ends" was measured against the model line nearest the streak, 7 cm from the course the design
  followed, so the finding pointed at the wrong edge. Idea: every placement finding names the line it read against.
- **Rows of dots get no check and no close look** (2026-10-21, the test car's agent): a paint zoned by
  `shapes.sphere` at a course's places (pressure taps) is skipped by the judge and the close looks, so a row painted
  inside a sidepod went unnamed. Idea: a row of marks at a course's places is a graphic, measured and looked at.
- **Never seen in the game yet** (2026-10-05): the finishes candy, chrome rims, rust, leather,
  metallic flake, and the viewer's matte, satin, gloss and chrome against the game's; the exhaust heat
  and boost glows (TSC_CMYK_EndsInK carries exhaust heat); whether the wheel covers turn; how
  see-through the glass is (tint only, so far); tyre markings (their relief, legibility, the band
  clearing the covers); a glow on the body (Skin_I in Details_I's format, on a test skin); the upload
  size limit (zips stay under 8.5 MB until one shows up).
