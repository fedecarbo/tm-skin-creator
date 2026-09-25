# TSC_Lights_Test

The lights test skin (2026-09-25, Opus 5.5): which of the car's lights a skin can colour.
The user asked for their own colours on the speed numbers, the brake lights and the car number.
Each question has its own colour, so one screenshot answers it. `key.png` is what the viewer
shows; compare the game's screenshots with it.

| What | Colour in the skin | How | If it works in the game |
|---|---|---|---|
| Speed digits (rear bumper) | green | the stock glow (white, code 96) recoloured | the speed shows in green, and the unlit segments stay dark |
| Brake lights (the slotted crescent inside each front wheel) | blue | the stock glow (dim red, code 0) recoloured | dim blue at rest, flaring when braking. A report online says red may show through |
| Rear lights (the bars under the tail's lenses) | magenta glow; the car's left lens tinted cyan | the stock glow (white in the file, red in the game) recoloured, and the lens tinted | red on both sides = neither works; magenta = the glow works; cyan or blue on the left = the lens tint works too. The viewer shows the game's red (the stock look) |
| Initials and number (engine cover) | yellow panel behind the initials, dark blue behind the number | plain paint | research says the game mode sets the lettering's colour (white in a normal race), so it should stay white on both |
| Brake heat (the wheel rims) | orange | code 64, rims painted dark | orange rims when braking hard |
| Exhaust heat (the side vents at the tail) | yellow | code 192, vents painted dark | yellow vents during a turbo |
| Turbo (the sidepod frames) | the game's colour | code 160, grey in the file, frames painted dark | the frames light up in the game's turbo colour. The stock turbo areas (the rings round the wheels) are left as they are, to compare |
| Boost (the fins under the tail) | the game's colour | code 224, grey in the file, fins painted dark | the fins light up during a reactor boost |

The rest of the car is plain grey, with the stock wheels (but for the dark rims). The earlier lab
skin had these four glows on the rear bumper, rear strakes, hubs and undertray and saw none of
them light up (checkpoint 4), so they sit on bigger, plainer spots here.

## What to try in the game

1. Drive in daylight with the normal chase camera. F12 screenshots from behind: going fast,
   then braking hard (the rear lights, and the brake lights inside the front wheels).
2. If the track has them: a yellow turbo pad, then a red one, a reactor boost, and cruise
   control. Screenshots from behind while each is on. Watch the speed digits (someone online
   says they change colour for these), the rings round the wheels and the front wing's lower
   edges (the game's turbo colour), and the back of the car (exhaust heat).
3. One hard stop from full speed, looking at the front wheels (brake heat, "on when braking
   hard"), then a gentle stop, to compare.
   Also the rear lights as a gear display (the user's observation, 2026-09-25: standing still
   only the outer ends light, each gear lights the next band, braking lights it all red):
   whether the bands fill up or move along one at a time, and
   when the small piece in the middle lights (the shift speeds are known: 100, 160, 235 and
   340 km/h). A short video from behind while accelerating from a standstill would answer both.
4. The same at night (a night map or night mood).
5. A close look at the engine cover, to see the lettering on the yellow and blue panels.
6. One screenshot with the game's Cam 2 (standing still is fine), for the viewer's camera menu.

## Log

- 2026-09-25: made on the Mac and checked in the viewer. Later the same day the four driving
  glows were added (brake heat, exhaust heat, turbo, boost), at the user's wish to test every
  state a skin can set. Codes checked after compression: the
  digits stay exactly 96, the brake lights 0, the rear lights 96. Not yet installed.
