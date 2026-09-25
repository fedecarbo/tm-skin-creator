# TSC_Lights_Test

Checkpoint 9's test skin (2026-09-25, Opus 5.5): which of the car's lights a skin can colour.
The user asked for their own colours on the speed numbers, the brake lights and the car number.
Each question has its own colour, so one screenshot answers it. `key.png` is what the viewer
shows; compare the game's screenshots with it.

| What | Colour in the skin | How | If it works in the game |
|---|---|---|---|
| Speed digits (rear bumper) | green | the stock glow (white, code 96) recoloured | the speed shows in green, and the unlit segments stay dark |
| Brake lights (the slotted crescent inside each front wheel) | blue | the stock glow (dim red, code 0) recoloured | dim blue at rest, flaring when braking. A report online says red may show through |
| Rear lights (the bars under the tail's lenses) | magenta glow; the car's left lens tinted cyan | the stock glow (white in the file, red in the game) recoloured, and the lens tinted | red on both sides = neither works; magenta = the glow works; cyan or blue on the left = the lens tint works too |
| Initials and number (engine cover) | yellow panel behind the initials, dark blue behind the number | plain paint | research says the game mode sets the lettering's colour (white in a normal race), so it should stay white on both |

The rest of the car is plain grey, with the stock wheels.

## What to try in the game

1. Drive in daylight with the normal chase camera. F12 screenshots from behind: going fast,
   then braking hard (the rear lights, and the brake lights inside the front wheels).
2. If the track has them: a yellow turbo pad, then a red one, a reactor boost, and cruise
   control. Screenshots from behind while each is on. Watch the speed digits (someone online
   says they change colour for these), the rings round the wheels and the front wing's lower
   edges (the game's turbo colour), and the back of the car (exhaust heat).
3. One hard stop from full speed, looking at the front wheels (brake heat, "on when braking
   hard"), then a gentle stop, to compare.
4. The same at night (a night map or night mood).
5. A close look at the engine cover, to see the lettering on the yellow and blue panels.
6. One screenshot with the game's Cam 2 (standing still is fine), for the viewer's camera menu.

## Log

- 2026-09-25: made on the Mac and checked in the viewer. Codes checked after compression: the
  digits stay exactly 96, the brake lights 0, the rear lights 96. Not yet installed.
