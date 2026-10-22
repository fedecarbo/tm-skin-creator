# TSC_SeeControl

A test car (2026-10-22, Claude Fable 5.1): a fresh painting session painting from a written brief alone, to be
compared against measurements. No language page, no takes; not installed.

The user's words (the brief, verbatim):

> # The brief (a test car; every stroke has a measurable right place)
>
> x is out to the car's left, y up from the ground, z forward; all in cm.
>
> 1. The whole body warm white above and deep navy satin below, split by one level line 40 cm off the ground, all the
>    way round the car.
> 2. Both sidepod tops (the flat shelves either side behind the cockpit: the model's own panel there) matte black,
>    filled right up to the panel's own edges.
> 3. A bright orange band 3 cm wide along the deck's rounded shoulder: the rounded edge where the engine cover's top
>    rolls over into the flank, which passes through about (40, 62, -20) on the left. On its FRONT 40 cm only: from
>    the end nearest the cockpit (the nose end) running back 40 cm. Both sides alike.
> 4. A white disc 20 cm across with a 2 cm navy ring, on each rear flank (the big side panel behind the sidepod,
>    around (64, 36, -80) on the left), where it sits flat and whole, facing out.
> 5. The words "SEE 22" in black, 10 cm tall, on each side near the disc where they read flat, reading forward on
>    both sides.
> 6. Small white discs 4 cm across scattered evenly over the engine cover's top (the deck behind the cockpit),
>    nowhere else, none on the panels the game letters.
> 7. One orange ring 25 cm across pressed onto the nose at about (0, 58, 150), across the seam it crosses, on purpose.
> 8. Six small black dots 3 cm across, evenly spaced along the long crease that runs low along the side skirt from
>    the nose back (through about (39, 19, 70) on the left), from its nose end to its tail end. Both sides.
> 9. Gold on the wheels (covers and rims) and a thin white ring on the tyres' sidewalls. The inner car dark grey
>    satin. Nothing left in clay; the lights left as stock.

How it was read:

1. `shapes.below(40)` on "body" with `across=True`: the split crosses every body part at y 40.
2. `meshlines.panel("sidepod top panel 1", both=True)` on "sidepod top": the model's own panel, 2459 cm², to its lines.
3. The shoulder: no model line within 5 cm of (40, 62, -20) (the point is 5 cm inside the body; the surface's nearest
   point (42.8, 66.1, -20.6) tilts 37 degrees from up). The lines of that roll: body shell roll 5 (tilt 40) at 5.08 cm,
   roll 2 (tilt 33) at 5.27, roll 1 (tilt 22) at 7.1. Taken: roll 5, tilt 40, the nearest; `.band(3)` centred on it,
   from its front end (36.2, 65.5, 34.8) 40 cm back along the surface (to about (41.9, 65.9, -4.3)); `.mirrored()`.
4. A 20 cm white disc at (64, 36, -80) and a navy `marks.ring(0.8)` of the same size on its centre: the ring is the
   disc's outer 2 cm (20 cm across all told; the other reading, a ring round a 20 cm disc, would be 24).
5. "SEE 22" is 48 cm long at 10 cm tall (Russo): no flat room of that length is beside the disc (the flank's calm
   room there is 37 cm), so it's wanted behind the disc, where the flank runs flat towards the tail, and the tool
   moves or shrinks it to where it's whole and says so.
6. `s.scatter` of a white disc on "engine cover|part" (the part alone, not the game's panels), 4 cm, 10 cm apart.
7. `marks.ring(0.76)` (3 cm thick) 25 across at (0, 58, 150), `across=True`: pressed as it is over the seams in its
   footprint. Its back arc (z 137.5) reaches the nose fin's plate (z 118 to 142), which the game letters: the brief
   puts it there on purpose, so it stays, and the judge's warning is reported, not fixed.
8. Six 3 cm black discs with `across=True` (a mark on a crisp line) at s = 1.5 + k (L - 3) / 5 along side skirt
   crease 2 (146 cm, (24, 18, 149) → (39, 19, 70) → (77, 22, 17)): the first and last centred 1.5 cm in from the
   ends, so every dot is whole on the crease; mirrored by the mark.
9. "wheels" (covers, rims, hubs, wheel rings) gold; `shapes.wheel_ring(33, 34)` on "sidewall" in white rubber; "inner"
   dark grey satin; no relight, no glass tint.

The record (2026-10-22, on the Mac, Claude Fable 5.1; not installed, the PC away):

- Shown, round 1: 13 blocks. The six skirt dots laid as marks with `across=True` landed 15 to 69 % whole: side skirt
  crease 2 is the fold at the skirt's lip (the surface within 3 cm of it is a 3 cm tall strip, half of it facing down),
  so half of each sticker fell on hidden skin; the band's first station read cut by "the edge where the body ends"
  (a 1 cm notch at its front corner, the left only; no edge, crease or texture cut is within 15 cm of the start); the
  words found no room at (53, 43, -102), even at 40 %: the flank behind the disc is hidden by the rear wheel, not open
  air; the disc shrank to 18.8 cm; the nose ring 44 cm² on the nose fin's plate (meant).
- Shown, round 2: the dots as 1.5 cm spheres cut from the surface (each a 3 cm disc centred on the crease, wrapping
  the lip's fold whole, 12 to 17 cm² a pair on the texture); the band's field read from the line carried 3 cm on
  before its start and cut square at the start by a plane (no notch, no block); the disc and ring pressed as they are
  (`across=True`): both 20.0 cm at (64, 36, -80), the ring 97 % landed; the words at (76, 30, -60) laid at 10 cm:
  48 cm long, they ran over the disc (chipping it, a block), turned 26° under, and 15 % hidden by the wheel.
- Shown, round 3: the words held to the flank's lower face between the sidepod's back (z -37.5) and 1.5 cm ahead of
  the disc (z -68.5): laid at (80, 32, -54), 6.4 cm tall (64 % of 10), moved 2.7 cm, flat (no turn said), both sides
  reading forward; the scatter's seed 4 (37 copies, 8 of them smaller, spread 34 %). The judge: 1 block (the nose ring
  on the fin's plate), no warnings. Close looks: no blocks, no warnings; the discs 59 to 61 % and the ring 100 % hidden
  by the rear wheel even seen from where they face. Gate passed `--despite` the nose ring: the brief's choice.
- Open (the brief against the car): the words are 6.4 cm, not 10 (no flat open-air room 48 cm long near the disc); the
  disc and words sit in the corner the rear wheel hides from the side; the deck's spots are white on warm white (as
  asked) and don't read in the views; 8 of the 37 spots are 2.8 to 3.4 cm (the scatter's second pass).
