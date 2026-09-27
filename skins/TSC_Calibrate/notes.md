# TSC_Calibrate

The calibration car (2026-09-27, Opus 5.5, made on the Mac). The user's words: "a car that will
help you calibrate the moods? Something I can do later with my pc" (on the list the night
before), then "I put in queue the calibration of the Moods in the game, and maybe you can compare
the 4 moods that trackmania has. I am not in my pc but maybe you can create the calibration car?"

How it was read: a test chart, not a skin to drive for looks. The viewer's day and night were set
by taste; this car lets the game's screenshots set them. Every patch is a known colour where the
game's chase cameras see it standing still (Cam 1 and 2 from behind, Cam 3 over the cockpit: the
viewer's poses are fitted to the user's screenshots of those three). The greys and colours are
the ColorChecker Classic's (sRGB), the photographer's standard chart. The rest of the car is one
flat mid grey, the photographer's grey card. The game's own lamps are off except the ones listed.

## The key

From behind, as the chase cameras see it, the car's left is on the picture's left.

- **The tail's flat top (the grey scale), matte**, the car's left to right: the left tail corner
  pure black `#000000`; then Black `#343434`, Neutral 3.5 `#555555`, Neutral 5 `#7a7a79`,
  Neutral 6.5 `#a0a0a0`, Neutral 8 `#c8c8c8`, White `#f3f3f2`; the right tail corner pure white
  `#ffffff`.
- **The deck either side of the engine cover's panel (the colours), matte**, from the middle
  out: on the car's left red `#af363c`, green `#469449`, blue `#383d96`; on its right cyan
  `#0885a1`, magenta `#bb5695`, yellow `#e7c71f`.
- **Beside the cockpit (the finishes)**, both sides alike, from the middle out, with thin black
  lines between: Neutral 5 in PA-04 matte, PA-03 satin, PA-01 gloss (the varnish), then ME-01
  chrome (its own silver). The rear quarter panels (the air brakes) and the sidepod tops, z -88
  to 12 cm.
- **The glow row, across the back just under the tail's top**, both sides alike, from the middle
  out, every patch light blue `#00b4ff` on black paint (so any light there is the glow): always
  on, night only, front lights, brake lights, energy (the game gives energy its own colour: red
  for this player). Unlit, a patch is a black rectangle.
- **Other lights, light blue `#00b4ff`:** the speed numbers, the rear lights, the brake lights
  (the slots inside the front wheels), and the cockpit's lamps (the row of slashes along the
  canopy's front edge, seen from Cam 3, always on).
- **Steering wheel:** White `#f3f3f2`, matte (Cam 3's white).
- **Everything else:** Neutral 5 `#7a7a79` matte: the body, the wheel covers, the inner car. The
  tyres are stock.

## What to do in the game (the PC)

All four moods on one small map in the editor, so the car stands on the same spot facing the
same way each time: the sun comes from a different side in each mood, and official maps can't
give that. Twelve screenshots in all. (From a lookup on 2026-09-27; the steps haven't been tried
in the game yet, so if a menu has another name, go by what the game shows.)

1. Claude installs it (`tool.skin install TSC_Calibrate`). In the game: Garage → My Skins →
   Upload skin, pick TSC_Calibrate.
2. Create → Map Editor (newer builds say Track Editor) → Create a map → Mouse and Keyboard →
   Advanced → **Sunrise** (the game may call it Morning). If the editor skips these choices, its
   quick start is on (Settings, Map Editor Quick Start): the mood is set there, or use step 5's
   light settings.
3. Put down one flat road piece out in the open.
4. Light settings on the bottom bar (or Map Options → Edit Light Settings): compute the shadows
   (Default or High, the same for all four moods). Without it the light isn't the map's real
   light.
5. Press Enter (test), click the road to put the car down, and don't touch the throttle.
6. Press 1, wait about 3 seconds (the game's exposure settles, slowest at night), F12. Then 2,
   then 3. A camera key pressed twice gives that camera's second view: take the first.
7. Esc back to the editor, Light settings → the next mood → compute the shadows again → Enter,
   the car on the same spot, facing the same way → 1, 2, 3. In order: Sunrise, Day, Sunset,
   Night.
8. Keep the same graphics settings throughout, as for the earlier Cam 1, 2, 3 screenshots.

Worth knowing: a free account can test in the editor; only playing a saved map from Local needs
Club. TSC_Lab_Materials can come on the same drive (its finishes by day and at night).

## What the viewer shows

`tool.snap TSC_Calibrate --cams` (on the Mac `node docker/snap.mjs TSC_Calibrate --cams`, with
`--size 2560x1440` for the screenshots' size): Cam 1, 2 and 3 by day and at night, as the viewer's
looks stood when the car was made (`LOOKS` in `viewer/viewer.js`: day exposure 1.2, env 1.25,
key 1.1; night env 4.4, key 0.44, exposure 0.9, glows x1.8).

## Record

- Made 2026-09-27 on the Mac and checked in the viewer: the six views, the close looks and the
  three chase cameras by day and at night. Every patch is where Cam 1 and 2 see it; Cam 3 sees
  the cockpit, the white wheel and the lamps. Not installed yet: install it on the Windows PC with
  `tool.skin install TSC_Calibrate`.
