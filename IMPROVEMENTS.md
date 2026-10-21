# Improvements to the tool

The one queue of what the tool should do better: each item dated, in two or three lines, what's wrong
and an idea for the fix. The user says when to work on it. A finished item is deleted; what it taught
goes into the code. It mustn't pile up or go stale: the session-start check (`tool/doctor.py`) says
"prune it" past 20 items or when one is older than 30 days; at a pruning each item is kept (re-dated,
still in the user's words), done, or deleted (git keeps it). Things that exist are named in backticks
and checked by the self-test; ideas are named in plain words.

## Next: the road

The research's order of work (`research/Skin tool state of the art 2026.md`), one step per session (the user,
2026-10-07: "I will do the plan a session each"): built under the self-test, its worth shown on a new test car made for
it (never a past car) or in plain words and numbers, then on the user's OK everything it retires removed (code,
mentions, caches, the test car; `git grep` finds none of the retired names), the step deleted here, commit, push. A
step names its model and effort; the user sets them as the session starts. One step is left, and it waits for the PC
(away until November or December 2026):

13. **Yardsticks, on the PC** (Opus 5.5, high). The game files encoded once by quicktex and texconv against the tool's
    own encoder; the camera's colours fitted first to a garage screenshot with the game's camera light on (the
    cleanest picture of a skin's colours the game gives; `viewer.lamp`), then per mood to the user's F12 screenshots
    (FLIP: exposure, environment strength, tone mapper, clearcoat), and from their videos the cameras pulling back with speed, the car number's lettering, the
    rear wings' and air brakes' angles. Retires nothing unless another encoder wins.

## The tool

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
- **Never seen in the game yet** (2026-10-05): the finishes candy, chrome rims, rust, leather,
  metallic flake, and the viewer's matte, satin, gloss and chrome against the game's; the exhaust heat
  and boost glows (TSC_CMYK_EndsInK carries exhaust heat); whether the wheel covers turn; how
  see-through the glass is (tint only, so far); tyre markings (their relief, legibility, the band
  clearing the covers); a glow on the body (Skin_I in Details_I's format, on a test skin); the upload
  size limit (zips stay under 8.5 MB until one shows up).
