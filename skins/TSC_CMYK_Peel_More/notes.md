# TSC_CMYK_Peel_More

The second take next to TSC_CMYK_Peel (see its notes), 2026-09-24: the same wrap with about
half of it gone, bigger tears and bigger flaps.
- Shown 2026-09-24 next to TSC_CMYK_Peel: 40 % torn, 4 flaps (on both sidepods, the bonnet
  and the tail).
- Change 1: the same as TSC_CMYK_Peel's (no folds, hard edges).
- Change 2: the same as TSC_CMYK_Peel's (no seam lines, hard shadow and lit edge).
- Change 3: the same as TSC_CMYK_Peel's (a thinner shadow, even all round).
- Change 4: the same as TSC_CMYK_Peel's (sidepod frame black).
- Installed 2026-09-25 at the user's word ("install TSC_CMYK_Peel_More"): 5.85 MB, built in 169 s. Not yet seen in the game.
- Change 5 (user, 2026-09-25, Opus 5.5, after the lights test): "you could update the cmyk one
  with more tailored lights if you want". Every light in the run's colours: brake lights in the
  front wheels cyan (like the calipers), speed numbers magenta, the rear lights one colour per
  gear band (cyan, cyan, magenta, magenta, then the end colour), their bars painted dark so a
  lit band shows its true colour, and brake heat on the rims in the end colour (the rims stay
  dark satin). The rear lenses stay clear (a tint would dim the braking red). New in the paint
  box for it: a colour per gear band in `relight("rear lights", [...])`.
- Change 6 (user, same day): "Can you make the car end with orangy rather than full yellow?"
  The run ends in orange (#ff9a1a) instead of yellow, everywhere on this car: the colour under
  the wrap at the back, the inside run, the tail parts, and the lights. The other CMYK cars keep
  their yellow (`end=` on the shared designs). Shown with a picture of the rear lights through
  the gears, braking and at night.
- Installed 2026-09-25 at the user's yes ("Like it :)"): 5.82 MB, built in 169 s. Glow codes
  checked in the game file: rims 64 (orange), brake lights 0 (cyan), digits and rear lights 96.
- Change 7 (user, 2026-09-25): "I actually don't like the rims. Any ideas? I don't want them to
  be metallic", then "also maybe we can do something with the sidewalls as well? of the wheel".
  The wheel covers still had the stock mirror chrome (roughness 0.01, metal 1). Three takes
  shown as TSC_CMYK_Wheels_Black, _Stripes and _Magenta (all with matte black covers).
- Change 8 (user): "I like the magenta line actually. It would be nice to just make it slightly
  thicker but not too much. And if you can actually do a radial effect of that line that
  gradients the cmyk ... The gradient to be around I mean ... Following the ring". The black
  take, its sidewall line 1.2 cm instead of 0.8 (31.0-32.2 cm from the axle), running cyan at
  each wheel's front, magenta over the top and bottom, orange at its back (`round_wheel`).
  Wheel covers matte black like the wrap. New in the paint box: `shapes.wheel_ring`.
- Change 9 (user): "Yes perfect, just slight upwards the ring, as in a bit closer to the tread,
  so it aligns more middle". The line moved out to 31.7-32.9 cm, the middle of the sidewall
  that shows beyond the cover (30 to 34.5).
- Installed 2026-09-25: 7.44 MB, built in 178 s. The line's edges checked in `Wheels_B`: one
  to two texels, no fringes.
- Change 10 (user, from the game): "It seems that the ring is not perfectly circular, because
  when I drive I see the ring being wobbly". The wheel centres the ring was drawn round were
  5.7 mm too far forward (tool/parts.py's figures from 2026-09-23), so the line swung by half
  its width as the wheel turned. `shapes.WHEEL_Y/WHEEL_Z` now hold centres fitted to the tread,
  bead, covers and rims; the line is at 31.7-32.9 cm all the way round (measured within 0.4 mm),
  and all four tyres share the painted one's shape within 0.1 mm.
- Installed 2026-09-25 with the round ring: 7.44 MB.
- Seen in the game 2026-09-25: the user says the tyre line is round now.
- Change 11 (user, 2026-09-25, Opus 5.5): the inside finished ("the quality of the entire car"),
  then from the game: no yellow turbo glow over the inside of the wheels (magenta preferred), one
  ring per wheel with the tyre's line a bit thicker, less orange at the rear ("keep the black
  from the tip with maybe a few tears"), orange digits; and "your approach and mine". Shown as
  two takes, TSC_CMYK_BlackTail (the user's tail) and TSC_CMYK_EndsInK (Claude's): their notes
  say what changed. The pick goes into this skin, so it keeps its name in the game.
