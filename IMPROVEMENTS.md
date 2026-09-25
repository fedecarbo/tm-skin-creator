# Improvements to the tool

The queue of things the tool should do better. Newest at the bottom of each group. The `skin`
skill says how it's kept: during a skin, Claude fixes only what that skin needs and adds
anything else here. The user says when to work on the list. A finished item is deleted
from here, and what it taught goes under "Things we learned" in `CHECKLIST.md`.

Each item: what's wrong or missing, when and where it showed up, and an idea for the fix. A
bigger item keeps its working notes under "Improvements after the build" in `CHECKLIST.md`.

## Under way

- **Define the game's cameras** (below), the user's way (2026-09-25): they set each camera by
  eye in the viewer, next to the game, press "Copy Cam N" and paste it in the chat. Claude
  squares it up behind the car and writes it into `VIEWS` in `viewer/viewer.js`. Cam 1 and Cam 2 set
  (2026-09-25); Cam 3 to come, if the game has a third that shows the car.

## The tool

- **Motifs lined up across panels** (2026-09-24, checkpoint 6). The tool can spread pictures or
  dots evenly, but not in rows that line up from panel to panel, like a regular grid. Idea: a
  `regular` switch on `Skin.scatter`, using `looks.surface_points(regular=True)`.
- **Writing on the tyres** (2026-09-24, checkpoint 5). Not built: all four tyres share one
  paint and the left and right ones aren't mirrored, so text reads backwards on one side.
  Idea: symmetric words and logos only, or no text on tyres at all.
- **Raised detail on the inner car** (2026-09-24, checkpoint 5): bolts, embossed logos, ribs,
  through `Details_N`. Not built. The body can't take relief at all.
- **Some inner part names are guesses** (2026-09-24, checkpoint 3): side vent, side vane, nose
  sensor, airbox. Check them the first time a design paints them. Known since the air brakes
  (2026-09-25): "nose sensor" is the nose panel's lifting arms, "rear damper" the rear quarter
  panel's arm, and "airbox" the opening under each quarter panel. Renaming them means updating
  `tool/naming.py`, `skins/TSC_Stealth_CMYK/design.py`, `tool/partskin.py` and `AIRBRAKES` in
  the viewer.

- **The wheel centres in `tool/parts.py` are 5.7 mm too far forward** (2026-09-25,
  TSC_CMYK_Peel_More: a tyre line wobbled in the game). `shapes.py` has the fitted ones
  (35.252; 178.314, -120.163). parts.py still uses 35.3 and 178.9, -119.6 to split the tyre
  into sidewall and tread (at 34.5 cm) and to name the cover pieces, so that split is off-centre
  by 5.7 mm: a sidewall painted unlike the tread would wobble too. Fix: use the fitted centres
  there, run `tool.parts`, and check the skins that paint "sidewall" or "tread".

## The viewer, from the user's screenshots and videos

- **Define the game's cameras** (2026-09-25, the user). The viewer's Driving menu should hold
  each of the game's cameras that show the car, each matched to the game. Now Cam 1 is matched
  to one screenshot (then moved closer at the user's wish) and Cam 2 is a guess (`VIEWS` in
  `viewer/viewer.js`; Decisions, "The game's cameras"). Needs a screenshot of each camera from
  the user, standing still and at speed: the straight-line video shows Cam 1 pulling back
  and lower as the speed rises and closing in again when the car slows, so each camera may
  follow the pad's speed. The lights test's two videos (2026-09-25, this PC) show Cam 1 through
  a whole run and a hard stop, day and night.
- **The car number's lettering is a guess** (2026-09-25) until a close-up of the engine cover.
  The lights test's videos have one ("CAR 00", day at 13.2 s, night at 10.8 s).
- **The rear wings and air brakes, fine-tuning** (2026-09-25): the viewer opens both wings (up
  or down, then apart) at the video's pace, and raises the air brakes (rear quarter panels,
  nose panel, with their arms) while braking. How far the wings move, the air brakes' angles
  and how quick they are were set by eye. A short video from the side (pull away, brake hard,
  let go) would pin them. Notes under the lights improvement in `CHECKLIST.md`.
- **A tinted rear lens should filter the braking red** (2026-09-25, TSC_Lights_Test): in the
  game, red through the cyan lens looked dark at night and teal by day; the viewer draws the
  red without the lens. Idea: multiply the braking colour by the lens's `Glass_T` tint.

## To check in the game

These need the user to drive or look, so they're tested when a skin uses them.

- **Finishes never seen in the game** (2026-09-24, checkpoint 5): candy, chrome rims, rust,
  leather, metallic flake.
- **Glows never seen to light up** (2026-09-24, checkpoint 4): turbo colour, exhaust heat,
  boost (brake heat lit in the lights test, 2026-09-25). The viewer shows them off.
  TSC_Lights_Test carries all three (sidepod frames, side vents, rear strakes): needs a track
  with turbo pads (yellow and red) and a reactor boost, with the camera behind the car.
- **How see-through the glass is** (2026-09-24, checkpoint 4): the glass file's alpha made no
  visible difference, so the tool treats glass as tint only.
- **The upload size limit.** Zips stay under 8.5 MB until a limit shows up (2026-09-24,
  checkpoint 1); the install halves the roughness maps to fit (2026-09-25). Undocumented;
  Ubisoft said in 2022 that 9 MB "may be too big".
