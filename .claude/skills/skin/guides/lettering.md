# Lettering: the typography and badges designer's guide

Read on the studio's car (`studio.md`, 3) when the work reaches the lettering: words, numbers and badges, their typeface and place.
It grows with every car: at the end of the step, add what the car taught under "Learned", dated,
with the car's name.

## What good looks like

- **Every word earns its place.** A number, a name, a mark that says something about the car.
  Lettering added to fill space makes the car look like a sponsor sheet. None is a real answer.
- **A hierarchy:** one big thing (a number, a name), then small marks. Two big words compete.
- **The typeface is the car's voice:** condensed and sporty, wide techno, a retro racing script, a
  naturalist's serif. Match it to the car's mood, not to habit.
- **Legibility at distance:** a heavy enough stroke, open letters, strong contrast with the ground
  it sits on; an outline or a panel (a roundel, a plate) when the ground is busy.
- **Placement follows the body:** on flat areas, level with the car's lines or raked with them,
  never across a fold. A number the right way up only from behind reads as another sign from the
  front.

## On this car

- The places (`SPOTS` in `tool/paintbox.py`): "left side"/"right side" on the rear flank (34 cm
  wide), "bonnet" (45 cm), "left flank"/"right flank" the front flank's top strip (lettering only:
  the flank has a deep fold), the sidepods (28 cm), the deck (45 cm), the tail (50 cm), the nose
  (30 cm). Never the number and name panels: the game letters the player's number and name there,
  in white, over the paint.
- `s.text(text, spot, colour=, font=, height=, outline=, italic=, spacing=)`; too wide for its spot,
  it's shrunk and noted; `show` says when a picture crosses a fold or runs off an edge. The fonts
  and what each looks like: `fonts.ABOUT` (`tool/fonts.py`); a new Google font at google/fonts'
  latest commit, its sha256 recorded. On the body a texel is about 1 mm: 4 cm letters are crisp.
- Mirrored surfaces: the inner parts and the tyres share paint with their other side, so a word
  reads backwards there (the tyres' flip-proof letters in `SKILL.md`). The body's two sides are
  lettered separately and read right on each.

## Check before showing

- Both sides and the front; close rows where the lettering sits.
- Where it meets the car's own pieces (the flank's small fin, a panel line).
- Say what reads only close up.

## Learned

- 2026-09-28, TSC_Ladybird: the Latin name ran under the front flank's small black fin (moved
  4 cm down); a 7 on the black nose read as an L from the front and, between the head's white
  marks, risked a face; the user chose none ("c").
